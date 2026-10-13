"""Pure offline contract tests: every HTTP call is replaced by a fake API."""
import copy
import importlib.util
import unittest
from unittest.mock import patch
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


registration = load('registration', 'ansible/roles/zabbix_registration/files/register.py')
bootstrap = load('bootstrap', 'ansible/roles/zabbix_server/files/bootstrap_admin.py')
access = load('access', 'ansible/roles/zabbix_local_access/files/access.py')


class FakeZabbix:
    def __init__(self):
        self.hosts = []
        self.writes = []
        self.groups = [{'name': 'Homelab/Linux', 'groupid': '1'}, {'name': 'Homelab/Proxmox', 'groupid': '2'}]

    def __call__(self, method, params):
        if method == 'template.get':
            templates = [{'host': 'Linux by Zabbix agent active', 'templateid': '10'},
                         {'host': 'Proxmox VE by HTTP', 'templateid': '11', 'macros': [{'macro': name} for name in ['{$PVE.URL.HOST}', '{$PVE.URL.PORT}', '{$PVE.TOKEN.ID}', '{$PVE.TOKEN.SECRET}']]}]
            return [t for t in templates if t['host'] in params['filter']['host']]
        if method == 'host.get':
            # Zabbix 7.0 never returns write-only PSK fields or secret macro values.
            hosts = copy.deepcopy(self.hosts)
            for h in hosts:
                h.pop('tls_psk', None)
                h.pop('tls_psk_identity', None)
                for macro in h.get('macros', []):
                    if str(macro.get('type')) == '1':
                        macro.pop('value', None)
            return hosts
        if method == 'hostgroup.get':
            return self.groups
        self.writes.append((method, copy.deepcopy(params)))
        if method == 'host.create':
            h = copy.deepcopy(params)
            h['hostid'] = str(len(self.hosts) + 100)
            h['hostgroups'] = h.pop('groups')
            h['parentTemplates'] = h.pop('templates')
            h['interfaces'][0]['interfaceid'] = '99'
            for index, macro in enumerate(h['macros']):
                macro['hostmacroid'] = str(index + 1)
            self.hosts.append(h)
        elif method == 'host.update':
            h = next(h for h in self.hosts if h['hostid'] == params['hostid'])
            h.update(params)
            h['hostgroups'] = h.pop('groups')
            h['parentTemplates'] = h.pop('templates')
        elif method == 'usermacro.update':
            for h in self.hosts:
                for macro in h['macros']:
                    if macro['hostmacroid'] == params['hostmacroid']:
                        macro.update(params)
        elif method == 'usermacro.create':
            h = next(h for h in self.hosts if h['hostid'] == params['hostid'])
            h['macros'].append(dict(params, hostmacroid=str(len(h['macros']) + 1)))
        elif method == 'hostinterface.update':
            self.hosts[0]['interfaces'][0].update(params)
        return {}


class DeploymentTests(unittest.TestCase):
    def test_host_create_repeat_rotation_and_preservation(self):
        api = FakeZabbix()
        hosts = [dict(name='dom', ip='192.168.55.3', psk='ab' * 32)]
        tokens = {'dom': dict(id='monitor@pve!zabbix', secret='test-only')}
        self.assertTrue(registration.reconcile(api, hosts, tokens))
        api.writes.clear()
        self.assertFalse(registration.reconcile(api, hosts, tokens))
        self.assertEqual(api.writes, [])
        api.hosts[0]['hostgroups'].append({'groupid': 'external'})
        api.hosts[0]['parentTemplates'].append({'templateid': 'external'})
        api.hosts[0]['tags'].append({'tag': 'external', 'value': 'keep'})
        api.hosts[0]['macros'].append({'macro': '{$UNRELATED.SECRET}', 'value': 'MASKED', 'type': '1', 'hostmacroid': '1000'})
        hosts[0]['psk'] = 'cd' * 32
        self.assertTrue(registration.reconcile(api, hosts, tokens))
        self.assertIn({'groupid': 'external'}, api.hosts[0]['hostgroups'])
        self.assertIn({'templateid': 'external'}, api.hosts[0]['parentTemplates'])
        self.assertIn({'tag': 'external', 'value': 'keep'}, api.hosts[0]['tags'])
        self.assertFalse(registration.reconcile(api, hosts, tokens))
        self.assertEqual(api.hosts[0]['macros'][-1]['value'], 'MASKED')
        self.assertTrue(all('macros' not in params for method, params in api.writes if method == 'host.update'))

    def test_unowned_host_rejected_before_writes(self):
        api = FakeZabbix()
        api.hosts = [{'host': 'dom', 'tags': []}]
        with self.assertRaises(ValueError):
            registration.reconcile(api, [dict(name='dom', ip='192.168.55.3', psk='ab' * 32)], {})
        self.assertEqual(api.writes, [])

    def test_dns_repeat_conflict_and_add(self):
        records = [{'name': access.DOMAIN, 'type': 'A', 'rData': {'ipAddress': '192.168.55.23'}}]
        calls = []
        def fake(url, *args, **kwargs):
            calls.append(url)
            return {'status': 'ok', 'response': {'zone': {'type': 'Primary'}, 'records': records}}
        self.assertFalse(access.dns({'token': 'test-only'}, fake))
        self.assertEqual(len(calls), 1)
        records.append(copy.deepcopy(records[0]))
        with self.assertRaises(ValueError):
            access.dns({'token': 'test-only'}, fake)
        records.clear()
        self.assertTrue(access.dns({'token': 'test-only'}, fake))
        self.assertIn('zones/records/add', calls[-1])
        self.assertIn('overwrite=false', calls[-1])

    def test_proxy_create_repeat_and_ownership(self):
        hosts, writes = [], []
        def fake(url, data=None, token=None, method=None):
            if url.endswith('/tokens'):
                return {'token': 'test-only'}
            if method == 'POST':
                writes.append(data)
                hosts.append(dict(data, id=1, enabled=True))
                return {}
            return copy.deepcopy(hosts)
        settings = dict(identity='test', password='test-only', server_ip='192.168.55.250')
        self.assertTrue(access.npm(settings, fake))
        self.assertIn('deny all;', writes[0]['advanced_config'])
        self.assertEqual(writes[0]['certificate_id'], 0)
        self.assertFalse(access.npm(settings, fake))
        self.assertEqual(len(writes), 1)
        hosts[0]['advanced_config'] = ''
        with self.assertRaises(ValueError):
            access.npm(settings, fake)

    def test_administrator_bootstrap_repeat_and_approval(self):
        state = {'password': 'zabbix'}
        writes = []
        def fake(request, timeout):
            body = __import__('json').loads(request.data)
            method, params = body['method'], body['params']
            if method == 'user.login':
                result = {'result': 'session'} if params['password'] == state['password'] else {'error': {}}
            elif method == 'user.get':
                result = {'result': [{'userid': '1'}]}
            elif method == 'user.update':
                state['password'] = params['passwd']
                writes.append(method)
                result = {'result': {'userids': ['1']}}
            else:
                result = {'result': True}
            return io.BytesIO(__import__('json').dumps(result).encode())
        settings = {'password': 'test-only-password' * 2, 'allow_initial_password': False}
        with patch.object(bootstrap, 'urlopen', fake):
            with self.assertRaises(ValueError):
                bootstrap.main(settings)
            self.assertEqual(writes, [])
            settings['allow_initial_password'] = True
            self.assertTrue(bootstrap.main(settings))
            self.assertFalse(bootstrap.main(settings))
            self.assertEqual(len(writes), 1)

    def test_bootstrap_rejects_ambiguous_admin_and_api_errors(self):
        for users, update in [([], {'result': {}}),
                              ([{'userid': '1'}, {'userid': '2'}], {'result': {}}),
                              ([{'userid': '1'}], {'error': {}})]:
            calls = []
            def fake(request, timeout):
                body = __import__('json').loads(request.data)
                method = body['method']
                calls.append(method)
                if method == 'user.login':
                    result = {'error': {}} if len(calls) == 1 else {'result': 'session'}
                elif method == 'user.get':
                    result = {'result': users}
                elif method == 'user.update':
                    result = update
                else:
                    result = {'result': True}
                return io.BytesIO(__import__('json').dumps(result).encode())
            with self.subTest(users=users, update=update), patch.object(bootstrap, 'urlopen', fake):
                with self.assertRaises(ValueError):
                    bootstrap.main({'password': 'test-only-password' * 2, 'allow_initial_password': True})
                self.assertEqual(calls[-1], 'user.logout')
                if len(users) != 1:
                    self.assertNotIn('user.update', calls)

    def test_all_sixteen_hosts_repeat_without_duplicate_hosts(self):
        api = FakeZabbix()
        names = ['dom', 'dtcode', 'iza', 'dns01', 'home01', 'forgejo01', 'npm01',
                 'tailscale-router', 'mysql01', 'bao01', 'qdrant01', 'langfuse01',
                 'grafana01', 'cloudflare01', 'webui01', 'zabbix01']
        hosts = [dict(name=name, ip='192.168.55.' + str(index + 40), psk='ab' * 32)
                 for index, name in enumerate(names)]
        tokens = {name: dict(id='monitor@pve!zabbix', secret='test-only') for name in ['dom', 'dtcode']}
        self.assertTrue(registration.reconcile(api, hosts, tokens))
        self.assertEqual(len(api.hosts), 16)
        self.assertFalse(registration.reconcile(api, hosts, tokens))
        self.assertEqual(len(api.hosts), 16)

    def test_api_tag_fields_do_not_break_ownership_or_idempotency(self):
        api = FakeZabbix()
        hosts = [dict(name='zabbix01', ip='192.168.55.29', psk='ab' * 32)]
        self.assertTrue(registration.reconcile(api, hosts, {}))
        # Zabbix 7.0 returns read-only tag fields that must not be compared or sent back.
        for tag in api.hosts[0]['tags']:
            tag['automatic'] = '0'
        api.writes.clear()
        self.assertFalse(registration.reconcile(api, hosts, {}))
        hosts[0]['psk'] = 'cd' * 32
        self.assertTrue(registration.reconcile(api, hosts, {}))
        updates = [params for method, params in api.writes if method == 'host.update']
        self.assertTrue(all(set(tag) == {'tag', 'value'} for tag in updates[0]['tags']))

    def test_pilot_then_full_registration(self):
        names = ['dom', 'dtcode', 'iza', 'dns01', 'home01', 'forgejo01', 'npm01',
                 'tailscale-router', 'mysql01', 'bao01', 'qdrant01', 'langfuse01',
                 'grafana01', 'cloudflare01', 'webui01', 'zabbix01']
        hosts = [dict(name=name, ip='192.168.55.' + str(index + 40), psk='ab' * 32)
                 for index, name in enumerate(names)]
        tokens = {name: dict(id='monitor@pve!zabbix', secret='test-only') for name in ['dom', 'dtcode']}
        pilot = dict(mode='pilot', hosts=hosts[-1:], proxmox={})
        full = dict(mode='full', hosts=hosts, proxmox=tokens)
        registration.validate(pilot)
        registration.validate(full)
        for invalid in [dict(pilot, hosts=hosts[:1]), dict(pilot, proxmox=tokens),
                        dict(full, hosts=hosts[:-1]), dict(full, mode='other')]:
            with self.assertRaises(ValueError):
                registration.validate(invalid)
        api = FakeZabbix()
        self.assertTrue(registration.reconcile(api, pilot['hosts'], {}))
        self.assertTrue(registration.reconcile(api, hosts, tokens))
        self.assertEqual(len(api.hosts), 16)
        self.assertFalse(registration.reconcile(api, hosts, tokens))

    def test_full_mode_without_proxmox_tokens_keeps_existing_integration(self):
        names = ['dom', 'dtcode', 'iza', 'dns01', 'home01', 'forgejo01', 'npm01',
                 'tailscale-router', 'mysql01', 'bao01', 'qdrant01', 'langfuse01',
                 'grafana01', 'cloudflare01', 'webui01', 'zabbix01']
        hosts = [dict(name=name, ip='192.168.55.' + str(index + 40), psk='ab' * 32)
                 for index, name in enumerate(names)]
        registration.validate(dict(mode='full', hosts=hosts, proxmox={}))
        with self.assertRaises(ValueError):
            registration.validate(dict(mode='full', hosts=hosts, proxmox={'iza': {}}))
        api = FakeZabbix()
        tokens = {'dom': dict(id='monitor@pve!zabbix', secret='test-only')}
        self.assertTrue(registration.reconcile(api, hosts[:1], tokens))
        # Without tokens: all hosts get the Linux template, nothing Proxmox-related is removed.
        self.assertTrue(registration.reconcile(api, hosts, {}))
        self.assertFalse(registration.reconcile(api, hosts, {}))
        self.assertEqual(len(api.hosts), 16)
        dom = api.hosts[0]
        self.assertEqual({t['templateid'] for t in dom['parentTemplates']}, {'10', '11'})
        self.assertEqual(len(dom['macros']), 4)
        self.assertTrue(all({'templateid': '10'} in h['parentTemplates'] for h in api.hosts))
        self.assertTrue(all(h['tls_connect'] == 2 for h in api.hosts))

    def run_main(self, fake_urlopen, secret):
        settings = dict(mode='pilot', password=secret, proxmox={},
                        hosts=[dict(name='zabbix01', ip='192.168.55.29', psk='ab' * 32)])
        stderr = io.StringIO()
        with patch.object(registration, 'urlopen', fake_urlopen), \
             patch('sys.stdin', io.StringIO(__import__('json').dumps(settings))), \
             patch('sys.stderr', stderr), self.assertRaises(SystemExit) as raised:
            registration.main()
        return str(raised.exception.code), stderr.getvalue()

    def test_reconcile_error_survives_logout_failure_without_secrets(self):
        secret = 'test-only-secret-' + 'ab' * 32
        calls = []
        def fake(request, timeout):
            method = __import__('json').loads(request.data)['method']
            calls.append(method)
            if method == 'user.login':
                return io.BytesIO(b'{"result": "session"}')
            if method == 'template.get':
                # Raw API error data must never be echoed.
                body = {'error': {'code': -32602, 'data': secret}}
                return io.BytesIO(__import__('json').dumps(body).encode())
            raise registration.URLError('logout unavailable')
        message, warnings = self.run_main(fake, secret)
        self.assertEqual(message, 'Registration failed: stage=reconcile step=templates operation=template.get '
                                  'category=api_error exception=APIError code=-32602')
        self.assertEqual(calls[-1], 'user.logout')
        self.assertIn('stage=logout', warnings)
        self.assertNotIn(secret, message + warnings)
        self.assertNotIn('ab' * 32, message + warnings)

    def test_connection_error_reports_login_operation_and_type(self):
        def fake(request, timeout):
            raise registration.URLError('connection refused')
        message, _ = self.run_main(fake, 'test-only-password')
        self.assertEqual(message, 'Registration failed: stage=login step=none operation=user.login '
                                  'category=connection exception=URLError')

    def test_missing_response_field_reports_key_and_step(self):
        api = FakeZabbix()
        hosts = [dict(name='zabbix01', ip='192.168.55.29', psk='ab' * 32)]
        registration.reconcile(api, hosts, {})
        del api.hosts[0]['parentTemplates']
        with self.assertRaises(KeyError) as raised:
            registration.reconcile(api, hosts, {})
        self.assertEqual(registration.describe(raised.exception, 'reconcile', 'hostgroup.get'),
                         'Registration failed: stage=reconcile step=compare:zabbix01 operation=hostgroup.get '
                         'category=unexpected_response exception=KeyError key=parentTemplates')

    def test_all_new_python_sources_compile_without_execution(self):
        for directory in ['zabbix_server', 'zabbix_registration', 'zabbix_local_access']:
            for path in (ROOT / 'ansible/roles' / directory).rglob('*.py'):
                compile(path.read_text(), str(path), 'exec')

    def test_optional_yaml_validation(self):
        try:
            import yaml
        except ImportError:
            self.skipTest('PyYAML unavailable locally')
        paths = list((ROOT / 'ansible/roles').glob('zabbix*/**/*.yml'))
        paths += list((ROOT / 'ansible/playbooks').glob('zabbix*.yml'))
        paths += [ROOT / 'ansible/tasks/zabbix-controller-guard.yml',
                  ROOT / 'ansible/inventories/production/hosts.yml']
        for path in paths:
            yaml.safe_load(path.read_text())


if __name__ == '__main__':
    unittest.main()
