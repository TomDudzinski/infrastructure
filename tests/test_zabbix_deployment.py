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
            return [{'host': 'Linux by Zabbix agent active', 'templateid': '10'},
                    {'host': 'Proxmox VE by HTTP', 'templateid': '11', 'macros': [{'macro': name} for name in ['{$PVE.URL.HOST}', '{$PVE.URL.PORT}', '{$PVE.TOKEN.ID}', '{$PVE.TOKEN.SECRET}']]}]
        if method == 'host.get':
            return copy.deepcopy(self.hosts)
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

    def test_all_fifteen_hosts_repeat_without_duplicate_hosts(self):
        api = FakeZabbix()
        names = ['dom', 'dtcode', 'iza', 'dns01', 'home01', 'forgejo01', 'npm01',
                 'tailscale-router', 'mysql01', 'bao01', 'qdrant01', 'langfuse01',
                 'grafana01', 'cloudflare01', 'zabbix01']
        hosts = [dict(name=name, ip='192.168.55.' + str(index + 40), psk='ab' * 32)
                 for index, name in enumerate(names)]
        tokens = {name: dict(id='monitor@pve!zabbix', secret='test-only') for name in ['dom', 'dtcode']}
        self.assertTrue(registration.reconcile(api, hosts, tokens))
        self.assertEqual(len(api.hosts), 15)
        self.assertFalse(registration.reconcile(api, hosts, tokens))
        self.assertEqual(len(api.hosts), 15)

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
