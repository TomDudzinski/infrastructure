"""Pure snapshot comparison; no network, filesystem writes or reconciliation."""
import ipaddress
import re


def domain_name(value, wildcard=False):
    if not isinstance(value, str):
        raise ValueError('Invalid domain in comparison input')
    value = value.lower().rstrip('.')
    suffix = value[2:] if wildcard and value.startswith('*.') else value
    if len(value) > 253 or '.' not in suffix or any(
        not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label)
        for label in suffix.split('.')
    ):
        raise ValueError('Invalid domain in comparison input')
    return value


def overlaps(pattern, domain):
    return pattern == domain or (pattern.startswith('*.') and domain.endswith(pattern[1:]))


def address(value):
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return value.lower().rstrip('.')


def npm_proxy_hosts_compare(services, snapshot):
    if not isinstance(services, dict) or not isinstance(snapshot, list):
        raise ValueError('Expected a service mapping and an explicit NPM host list')
    report = {status: [] for status in ('matching', 'missing', 'conflict', 'unmanaged')}
    # Neither a valid array nor a matching total proves visibility of all owners.
    # Offline snapshots also have no independently verified visibility evidence.
    report['snapshot_visibility'] = dict(scope='provided_snapshot', completeness='unverified',
                                         warning='owner_permissions_may_limit_visibility')
    hosts, ids = [], set()
    for raw in snapshot:
        if not isinstance(raw, dict) or type(raw.get('id')) is not int or raw['id'] <= 0:
            raise ValueError('NPM hosts require positive integer IDs')
        if raw['id'] in ids:
            raise ValueError('Duplicate NPM host ID')
        ids.add(raw['id'])
        domains = raw.get('domain_names')
        if not isinstance(domains, list) or not domains:
            raise ValueError('NPM hosts require a nonempty domain_names list')
        if (raw.get('forward_scheme') not in ('http', 'https')
                or not isinstance(raw.get('forward_host'), str) or not raw['forward_host'].strip()
                or type(raw.get('forward_port')) is not int or not 1 <= raw['forward_port'] <= 65535
                or type(raw.get('enabled')) is not bool
                or type(raw.get('allow_websocket_upgrade')) is not bool):
            raise ValueError('Invalid NPM routing fields')
        hosts.append(dict(id=raw['id'], domains=[domain_name(d, True) for d in domains],
                          protocol=raw['forward_scheme'], ip=raw['forward_host'],
                          port=raw['forward_port'], enabled=raw['enabled'],
                          websocket=raw['allow_websocket_upgrade']))
    # Expose only routing fields from the validated snapshot, without changing
    # the normalized hosts used by the comparison below.
    report['observed_endpoints'] = [
        dict(proxy_host_id=raw['id'], domains=list(raw['domain_names']),
             protocol=raw['forward_scheme'], host=raw['forward_host'],
             port=raw['forward_port'], enabled=raw['enabled'],
             websocket=raw['allow_websocket_upgrade'])
        for raw in snapshot
    ]
    catalogue = {}
    for key, service in services.items():
        if not isinstance(service, dict) or type(service.get('npm_enabled')) is not bool:
            raise ValueError('Invalid catalogue service or npm_enabled flag')
        if service.get('domain') is not None:
            domain = domain_name(service['domain'])
            catalogue.setdefault(domain, []).append(key)
        if service.get('protocol') not in (None, 'http', 'https'):
            raise ValueError('Invalid catalogue protocol')
        if service.get('ip') is not None:
            if not isinstance(service['ip'], str):
                raise ValueError('Invalid catalogue IP')
            ipaddress.ip_address(service['ip'])
        port = service.get('port')
        # Ansible may wrap integers in metadata-carrying subclasses; bool is
        # also an int subclass, but must never be accepted as a port.
        if port is not None and (isinstance(port, bool) or not isinstance(port, int)
                                 or not 1 <= port <= 65535):
            raise ValueError('Invalid catalogue port')
        if 'websocket' in service and type(service['websocket']) is not bool:
            raise ValueError('Invalid catalogue websocket flag')
    for key, service in services.items():
        entry = dict(service=key, domain=service.get('domain'), npm_enabled=service['npm_enabled'],
                     owner='zabbix_local_access' if key == 'zabbix' else 'unassigned')
        if service.get('domain') is None:
            report['unmanaged'].append(dict(entry, reason='unknown_catalogue_domain', proxy_host_ids=[]))
            continue
        domain = domain_name(service['domain'])
        matches = [h for h in hosts if any(overlaps(d, domain) for d in h['domains'])]
        entry['proxy_host_ids'] = sorted(h['id'] for h in matches)
        reasons = []
        if len(catalogue[domain]) > 1:
            reasons.append('duplicate_catalogue_domain')
        if len(matches) > 1:
            reasons.append('multiple_proxy_hosts')
        for host in matches:
            if any(d.startswith('*.') and overlaps(d, domain) for d in host['domains']):
                reasons.append('wildcard_overlap')
            if len(host['domains']) != len(set(host['domains'])):
                reasons.append('duplicate_proxy_domain')
            if not host['enabled']:
                reasons.append('proxy_host_disabled')
            for field in ('ip', 'port', 'protocol', 'websocket'):
                if field not in service or service[field] is None:
                    if field != 'websocket':
                        reasons.append('incomplete_catalogue_endpoint')
                elif (address(host[field]) != address(service[field]) if field == 'ip'
                      else host[field] != service[field]):
                    reasons.append(field + '_mismatch')
        if reasons:
            report['conflict'].append(dict(entry, reasons=sorted(set(reasons))))
        elif not matches:
            report['missing'].append(dict(entry, reason='no_visible_proxy_host'))
        else:
            report['matching'].append(entry)
    for host in hosts:
        unknown = [d for d in host['domains'] if d not in catalogue]
        if unknown:
            report['unmanaged'].append(dict(proxy_host_id=host['id'], domains=unknown,
                                            reason='domains_outside_catalogue'))
    # Duplicate unknown domains are conflicts too, without implying adoption.
    unknown_domains = {d for host in hosts for d in host['domains'] if d not in catalogue}
    for domain in sorted(unknown_domains):
        occurrences = [host['id'] for host in hosts for d in host['domains'] if d == domain]
        if len(occurrences) > 1:
            report['conflict'].append(dict(domain=domain, proxy_host_ids=sorted(set(occurrences)),
                                            reasons=['duplicate_unmanaged_domain']))
    return report


class FilterModule:
    def filters(self):
        return {'npm_proxy_hosts_compare': npm_proxy_hosts_compare}
