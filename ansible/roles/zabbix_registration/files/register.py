"""Reconcile only owned Zabbix 7.0 hosts. Input secrets exclusively on stdin."""
import hashlib
import ipaddress
import json
import re
import sys
from urllib.request import Request, urlopen


class API:
    def __init__(self, url, token):
        self.url, self.token = url, token

    def __call__(self, method, params):
        body = json.dumps(dict(jsonrpc='2.0', method=method, params=params, id=1)).encode()
        request = Request(self.url, body, {'Content-Type': 'application/json-rpc',
                                          **({'Authorization': 'Bearer ' + self.token} if self.token else {})})
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
        if 'error' in result:
            raise RuntimeError('Zabbix API rejected ' + method)
        return result['result']


OWNER_TAG = {'tag': 'managed-by', 'value': 'infrastructure-zabbix'}


def plain_tags(tags):
    # Zabbix 7.0 adds read-only fields such as 'automatic'; compare and send only tag/value.
    return [{'tag': t['tag'], 'value': t.get('value', '')} for t in tags if str(t.get('automatic', '0')) == '0']


def reconcile(api, hosts, proxmox):
    # Read all prerequisites before the first mutation.
    names = ['Linux by Zabbix agent active']
    if proxmox:
        names.append('Proxmox VE by HTTP')
    templates = api('template.get', {'output': ['templateid', 'host'], 'selectMacros': 'extend', 'filter': {'host': names}})
    ids = {x['host']: x['templateid'] for x in templates}
    if set(ids) != set(names):
        raise ValueError('Required stock templates are missing')
    if proxmox:
        pve_template = next(t for t in templates if t['host'] == 'Proxmox VE by HTTP')
        expected = {'{$PVE.URL.HOST}', '{$PVE.URL.PORT}', '{$PVE.TOKEN.ID}', '{$PVE.TOKEN.SECRET}'}
        if not expected <= {m['macro'] for m in pve_template['macros']}:
            raise ValueError('Installed Proxmox template macro contract differs')
    current = api('host.get', {'output': ['hostid', 'host', 'tls_connect', 'tls_accept', 'tls_psk_identity'],
                              'filter': {'host': [h['name'] for h in hosts]},
                              'selectHostGroups': ['groupid'], 'selectParentTemplates': ['templateid'],
                              'selectInterfaces': ['interfaceid', 'type', 'main', 'useip', 'ip', 'dns', 'port'],
                              'selectTags': 'extend', 'selectMacros': 'extend'})
    existing = {h['host']: h for h in current}
    for h in current:
        if OWNER_TAG not in plain_tags(h['tags']):
            raise ValueError('Existing unowned host needs explicit adoption: ' + h['host'])
    group_names = ['Homelab/Linux', 'Homelab/Proxmox']
    groups = api('hostgroup.get', {'output': ['groupid', 'name'], 'filter': {'name': group_names}})
    group_ids = {g['name']: g['groupid'] for g in groups}
    changed = False
    for name in group_names:
        if name not in group_ids:
            group_ids[name] = api('hostgroup.create', {'name': name})['groupids'][0]
            changed = True
    for host in hosts:
        name, ip, psk = host['name'], host['ip'], host['psk']
        old = existing.get(name)
        desired_groups = {group_ids['Homelab/Linux']}
        desired_templates = {ids['Linux by Zabbix agent active']}
        macros = []
        fingerprint_input = psk
        if name in proxmox:
            desired_groups.add(group_ids['Homelab/Proxmox'])
            desired_templates.add(ids['Proxmox VE by HTTP'])
            credentials = proxmox[name]
            macros = [{'macro': '{$PVE.URL.HOST}', 'value': ip},
                      {'macro': '{$PVE.URL.PORT}', 'value': '8006'},
                      {'macro': '{$PVE.TOKEN.ID}', 'value': credentials['id']},
                      {'macro': '{$PVE.TOKEN.SECRET}', 'value': credentials['secret'], 'type': '1'}]
            fingerprint_input += json.dumps(credentials, sort_keys=True)
        digest = hashlib.sha256(fingerprint_input.encode()).hexdigest()
        tags = [OWNER_TAG, {'tag': 'credentials-sha256', 'value': digest}]
        interface = dict(type=1, main=1, useip=1, ip=ip, dns='', port='10050')
        payload = dict(host=name, groups=[{'groupid': x} for x in sorted(desired_groups)],
                       templates=[{'templateid': x} for x in sorted(desired_templates)],
                       tls_connect=2, tls_accept=2, tls_psk_identity='homelab-' + name,
                       tls_psk=psk, tags=tags)
        if not old:
            payload.update(interfaces=[interface], macros=macros)
            api('host.create', payload)
            changed = True
            continue
        old_groups = {g['groupid'] for g in old['hostgroups']}
        old_templates = {t['templateid'] for t in old['parentTemplates']}
        interfaces = [i for i in old['interfaces'] if str(i['type']) == '1' and str(i['main']) == '1']
        if len(interfaces) != 1:
            raise ValueError('Expected exactly one main agent interface: ' + name)
        actual = interfaces[0]
        interface_changed = any(str(actual[k]) != str(v) for k, v in interface.items())
        old_tags = plain_tags(old['tags'])
        credentials_changed = tags[1] not in old_tags
        macro_values = {m['macro']: m['value'] for m in old['macros']}
        macro_changed = any(m['macro'] not in macro_values or (m.get('type') != '1' and macro_values[m['macro']] != m['value']) for m in macros)
        tls_changed = (str(old['tls_connect']) != '2' or str(old['tls_accept']) != '2'
                       or old['tls_psk_identity'] != 'homelab-' + name)
        if credentials_changed or macro_changed or tls_changed or not desired_groups <= old_groups or not desired_templates <= old_templates:
            payload.pop('host')
            payload['hostid'] = old['hostid']
            payload['groups'] = [{'groupid': x} for x in sorted(old_groups | desired_groups)]
            payload['templates'] = [{'templateid': x} for x in sorted(old_templates | desired_templates)]
            payload['tags'] = [t for t in old_tags if t['tag'] not in ('managed-by', 'credentials-sha256')] + tags
            if macros and (credentials_changed or macro_changed):
                # Never send unrelated masked secret macros back to the API.
                old_macros = {m['macro']: m for m in old['macros']}
                for macro in macros:
                    previous = old_macros.get(macro['macro'])
                    if previous:
                        api('usermacro.update', dict(macro, hostmacroid=previous['hostmacroid']))
                    else:
                        api('usermacro.create', dict(macro, hostid=old['hostid']))
            api('host.update', payload)
            changed = True
        if interface_changed:
            api('hostinterface.update', dict(interface, interfaceid=actual['interfaceid']))
            changed = True
    return changed


def validate(settings):
    hosts = settings['hosts']
    mode = settings.get('mode')
    if mode == 'pilot':
        if len(hosts) != 1 or hosts[0]['name'] != 'zabbix01':
            raise ValueError('Pilot mode allows only zabbix01')
        if settings.get('proxmox') != {}:
            raise ValueError('Pilot mode must not include Proxmox credentials')
    elif mode == 'full':
        if len(hosts) != 15 or len({h['name'] for h in hosts}) != 15 or len({h['ip'] for h in hosts}) != 15:
            raise ValueError('Exactly 15 unique hosts and addresses are required')
        if set(settings['proxmox']) != {'dom', 'dtcode'}:
            raise ValueError('Read-only Proxmox credentials for both hosts are required')
    else:
        raise ValueError('Registration mode must be pilot or full')
    for h in hosts:
        if ipaddress.ip_address(h['ip']) not in ipaddress.ip_network('192.168.55.0/24') or h['ip'] in ('192.168.55.0', '192.168.55.255'):
            raise ValueError('Host outside LAN: ' + h['name'])
        if not re.fullmatch(r'(?:[0-9a-fA-F]{2}){16,256}', h['psk']):
            raise ValueError('Invalid PSK: ' + h['name'])


def main():
    settings = json.load(sys.stdin)
    validate(settings)
    api = API('http://127.0.0.1:8080/api_jsonrpc.php', None)
    api.token = api('user.login', {'username': 'Admin', 'password': settings['password']})
    try:
        print(json.dumps({'changed': reconcile(api, settings['hosts'], settings['proxmox'])}))
    finally:
        api('user.logout', [])


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError) as error:
        # Messages are built from host names and API method names only, never from secrets.
        sys.exit('Registration failed: ' + str(error))
    except Exception:
        sys.exit('Registration failed; no credentials logged. Review API/template compatibility and ownership.')
