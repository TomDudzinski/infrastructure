"""Reconcile only owned Zabbix 7.0 hosts. Input secrets exclusively on stdin."""
import hashlib
import ipaddress
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class CheckFailed(ValueError):
    """Expected precondition failure; messages contain only host names and fixed text."""


class APIError(RuntimeError):
    """Zabbix JSON-RPC error; keeps only the method and numeric error code."""

    def __init__(self, method, code):
        super().__init__('Zabbix API rejected ' + method)
        self.code = code


class API:
    def __init__(self, url, token):
        self.url, self.token = url, token
        self.method = None

    def __call__(self, method, params):
        self.method = method
        body = json.dumps(dict(jsonrpc='2.0', method=method, params=params, id=1)).encode()
        request = Request(self.url, body, {'Content-Type': 'application/json-rpc',
                                          **({'Authorization': 'Bearer ' + self.token} if self.token else {})})
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
        if 'error' in result:
            # Never expose error 'data': it may echo request parameters.
            raise APIError(method, result['error'].get('code') if isinstance(result['error'], dict) else None)
        return result['result']


# Last reconcile step, reported on failure; contains only fixed names and host names.
progress = {'step': 'none'}

OWNER_TAG = {'tag': 'managed-by', 'value': 'infrastructure-zabbix'}


def plain_tags(tags):
    # Zabbix 7.0 adds read-only fields such as 'automatic'; compare and send only tag/value.
    return [{'tag': t['tag'], 'value': t.get('value', '')} for t in tags if str(t.get('automatic', '0')) == '0']


def reconcile(api, hosts, proxmox):
    # Read all prerequisites before the first mutation.
    progress['step'] = 'templates'
    names = ['Linux by Zabbix agent active']
    if proxmox:
        names.append('Proxmox VE by HTTP')
    templates = api('template.get', {'output': ['templateid', 'host'], 'selectMacros': 'extend', 'filter': {'host': names}})
    ids = {x['host']: x['templateid'] for x in templates}
    if set(ids) != set(names):
        raise CheckFailed('Required stock templates are missing')
    if proxmox:
        pve_template = next(t for t in templates if t['host'] == 'Proxmox VE by HTTP')
        expected = {'{$PVE.URL.HOST}', '{$PVE.URL.PORT}', '{$PVE.TOKEN.ID}', '{$PVE.TOKEN.SECRET}'}
        if not expected <= {m['macro'] for m in pve_template['macros']}:
            raise CheckFailed('Installed Proxmox template macro contract differs')
    progress['step'] = 'hosts'
    # tls_psk_identity and tls_psk are write-only in Zabbix 7.0 and never returned by host.get.
    current = api('host.get', {'output': ['hostid', 'host', 'tls_connect', 'tls_accept'],
                              'filter': {'host': [h['name'] for h in hosts]},
                              'selectHostGroups': ['groupid'], 'selectParentTemplates': ['templateid'],
                              'selectInterfaces': ['interfaceid', 'type', 'main', 'useip', 'ip', 'dns', 'port'],
                              'selectTags': 'extend', 'selectMacros': 'extend'})
    existing = {h['host']: h for h in current}
    for h in current:
        if OWNER_TAG not in plain_tags(h['tags']):
            raise CheckFailed('Existing unowned host needs explicit adoption: ' + h['host'])
    progress['step'] = 'groups'
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
        progress['step'] = 'prepare:' + name
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
        progress['step'] = 'compare:' + name
        old_groups = {g['groupid'] for g in old['hostgroups']}
        old_templates = {t['templateid'] for t in old['parentTemplates']}
        interfaces = [i for i in old['interfaces'] if str(i['type']) == '1' and str(i['main']) == '1']
        if len(interfaces) != 1:
            raise CheckFailed('Expected exactly one main agent interface: ' + name)
        actual = interfaces[0]
        interface_changed = any(str(actual[k]) != str(v) for k, v in interface.items())
        old_tags = plain_tags(old['tags'])
        credentials_changed = tags[1] not in old_tags
        # Secret macro values are write-only and absent from host.get; they are never compared.
        macro_values = {m['macro']: m.get('value') for m in old['macros']}
        macro_changed = any(m['macro'] not in macro_values or (m.get('type') != '1' and macro_values[m['macro']] != m['value']) for m in macros)
        # The PSK identity cannot be read back; host.update below always sends it with the PSK.
        tls_changed = str(old['tls_connect']) != '2' or str(old['tls_accept']) != '2'
        if credentials_changed or macro_changed or tls_changed or not desired_groups <= old_groups or not desired_templates <= old_templates:
            progress['step'] = 'update:' + name
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
            raise CheckFailed('Pilot mode allows only zabbix01')
        if settings.get('proxmox') != {}:
            raise CheckFailed('Pilot mode must not include Proxmox credentials')
    elif mode == 'full':
        if len(hosts) != 15 or len({h['name'] for h in hosts}) != 15 or len({h['ip'] for h in hosts}) != 15:
            raise CheckFailed('Exactly 15 unique hosts and addresses are required')
        if set(settings['proxmox']) != {'dom', 'dtcode'}:
            raise CheckFailed('Read-only Proxmox credentials for both hosts are required')
    else:
        raise CheckFailed('Registration mode must be pilot or full')
    for h in hosts:
        if ipaddress.ip_address(h['ip']) not in ipaddress.ip_network('192.168.55.0/24') or h['ip'] in ('192.168.55.0', '192.168.55.255'):
            raise CheckFailed('Host outside LAN: ' + h['name'])
        if not re.fullmatch(r'(?:[0-9a-fA-F]{2}){16,256}', h['psk']):
            raise CheckFailed('Invalid PSK: ' + h['name'])


def describe(error, stage, method):
    """Build a one-line diagnostic without exception text from untrusted sources."""
    if isinstance(error, CheckFailed):
        category, detail = 'precondition', str(error)
    elif isinstance(error, APIError):
        category, detail = 'api_error', 'code=' + str(error.code)
    elif isinstance(error, HTTPError):
        category, detail = 'http_error', 'status=' + str(error.code)
    elif isinstance(error, (URLError, OSError)):
        category, detail = 'connection', ''
    elif isinstance(error, ValueError):
        category, detail = 'invalid_data', ''
    elif isinstance(error, KeyError):
        key = error.args[0] if error.args else None
        # Only report keys that look like field or host names, never arbitrary data.
        safe = isinstance(key, str) and re.fullmatch(r'[A-Za-z0-9_.\-]{1,64}', key)
        category, detail = 'unexpected_response', 'key=' + (key if safe else 'unreported')
    elif isinstance(error, (TypeError, IndexError, StopIteration)):
        category, detail = 'unexpected_response', ''
    else:
        category, detail = 'internal', ''
    parts = ['Registration failed:', 'stage=' + stage, 'step=' + progress['step'],
             'operation=' + (method or 'none'),
             'category=' + category, 'exception=' + type(error).__name__]
    return ' '.join(parts + ([detail] if detail else []))


def logout(api):
    # Best effort: a logout failure must never replace the registration result.
    try:
        api('user.logout', [])
    except Exception as error:
        print(describe(error, 'logout', 'user.logout').replace('failed', 'warning', 1), file=sys.stderr)


def main():
    stage, api = 'input', None
    progress['step'] = 'none'
    try:
        settings = json.load(sys.stdin)
        stage = 'validate'
        validate(settings)
        stage = 'login'
        api = API('http://127.0.0.1:8080/api_jsonrpc.php', None)
        api.token = api('user.login', {'username': 'Admin', 'password': settings['password']})
        stage = 'reconcile'
        changed = reconcile(api, settings['hosts'], settings['proxmox'])
    except Exception as error:
        # Capture the failing operation before logout overwrites it.
        method = api.method if api else None
        if stage == 'reconcile':
            logout(api)
        sys.exit(describe(error, stage, method))
    logout(api)
    print(json.dumps({'changed': changed}))


if __name__ == '__main__':
    main()
