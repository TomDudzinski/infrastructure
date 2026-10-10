"""Narrow, idempotent local DNS/NPM integration; never replace whole zones."""
import json
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DOMAIN = 'zabbix.home.lab'
MARKER = '# Managed by infrastructure: zabbix.home.lab'
ACL = MARKER + '\nallow 192.168.55.0/24;\ndeny all;\n'


def request(url, data=None, token=None, method=None):
    headers = {}
    if data is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data).encode()
    if token:
        headers['Authorization'] = 'Bearer ' + token
    with urlopen(Request(url, data, headers, method=method), timeout=30) as response:
        return json.load(response)


def dns(settings, call=request):
    def api(path, **params):
        result = call('http://127.0.0.1:5380/api/' + path + '?' + urlencode(dict(token=settings['token'], **params)))
        if result.get('status') != 'ok':
            raise ValueError('Technitium API failure')
        return result.get('response', {})
    result = api('zones/records/get', domain='home.lab', listZone='true')
    # Never create/replace the existing zone or overwrite ambiguous records.
    if result.get('zone', {}).get('type') != 'Primary':
        raise ValueError('Require existing primary home.lab zone')
    records = [r for r in result['records'] if r['name'].rstrip('.') == DOMAIN]
    if any(r['type'] in ('CNAME', 'AAAA') for r in records):
        raise ValueError('Conflicting CNAME or unapproved IPv6 record requires review')
    records = [r for r in records if r['type'] == 'A']
    if len(records) > 1:
        raise ValueError('Multiple A records require review')
    if records and records[0]['rData']['ipAddress'] == '192.168.55.23' and not records[0].get('disabled', False):
        return False
    if records:
        api('zones/records/update', domain=DOMAIN, type='A', ipAddress=records[0]['rData']['ipAddress'],
            newDomain=DOMAIN, newIpAddress='192.168.55.23', ttl=300, disable='false')
    else:
        api('zones/records/add', domain=DOMAIN, type='A', ipAddress='192.168.55.23', ttl=300, overwrite='false')
    return True


def npm(settings, call=request):
    base = 'http://127.0.0.1:81/api'
    token = call(base + '/tokens', {'identity': settings['identity'], 'secret': settings['password']})['token']
    hosts = call(base + '/nginx/proxy-hosts', token=token)
    matches = [h for h in hosts if DOMAIN in h['domain_names']]
    if len(matches) > 1:
        raise ValueError('Duplicate proxy host requires review')
    if matches and (matches[0]['domain_names'] != [DOMAIN] or MARKER not in matches[0].get('advanced_config', '')):
        raise ValueError('Existing unowned proxy host requires review')
    desired = dict(domain_names=[DOMAIN], forward_scheme='http', forward_host=settings['server_ip'],
                   forward_port=8080, access_list_id=0, certificate_id=0, ssl_forced=False,
                   caching_enabled=False, block_exploits=True, allow_websocket_upgrade=False,
                   http2_support=False, hsts_enabled=False, hsts_subdomains=False,
                   advanced_config=ACL, locations=[], meta={'letsencrypt_agree': False, 'dns_challenge': False})
    if not matches:
        call(base + '/nginx/proxy-hosts', desired, token, 'POST')
        return True
    old = matches[0]
    comparable = {k: v for k, v in desired.items() if k != 'meta'}
    if all(old.get(k) == v for k, v in comparable.items()) and old.get('enabled', True):
        return False
    desired['meta'] = old.get('meta', desired['meta'])
    call(base + '/nginx/proxy-hosts/' + str(old['id']), desired, token, 'PUT')
    if not old.get('enabled', True):
        call(base + '/nginx/proxy-hosts/' + str(old['id']) + '/enable', {}, token, 'POST')
    return True


if __name__ == '__main__':
    try:
        settings = json.load(sys.stdin)
        action = {'dns': dns, 'npm': npm}[settings['action']]
        print(json.dumps({'changed': action(settings)}))
    except Exception:
        sys.exit('Local DNS/NPM integration failed. Review installed API version and existing records; no credentials logged.')
