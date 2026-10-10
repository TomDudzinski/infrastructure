"""Offline validation and ownership regression tests for the service catalogue."""
import ast
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validate_services', ROOT / 'scripts/validate_services.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.data = validator.load_catalogue()
        self.services = self.data['infrastructure_services']

    def test_repository_catalogue_and_initial_scope(self):
        validator.validate_catalogue(self.data)
        self.assertEqual(set(self.services), {'homepage', 'npm', 'technitium_dns',
                                             'open_webui', 'vscode', 'jupyter',
                                             'forgejo', 'openbao', 'zabbix', 'dom', 'dtcode'})
        self.assertTrue(all(s['npm_enabled'] is False for s in self.services.values()))
        for service in self.services.values():
            self.assertTrue((ROOT / service['source']).is_file())

    def test_user_confirmed_npm_domains(self):
        expected = {
            'homepage': 'home.home.lab',
            'npm': 'proxy.home.lab',
            'technitium_dns': 'dns.home.lab',
            'open_webui': 'chat.home.lab',
            'vscode': 'vsc.home.lab',
            'jupyter': 'jupyter.home.lab',
            'forgejo': 'git.home.lab',
            'openbao': 'bao01.home.lab',
            'zabbix': 'zabbix.home.lab',
            'dom': 'pve-dom.home.lab',
            'dtcode': 'pve-dtcode.home.lab',
        }
        self.assertEqual({key: service['domain'] for key, service in self.services.items()}, expected)

    def test_api_confirmed_upstreams(self):
        expected = {
            'homepage': ('192.168.55.20', 3000),
            'open_webui': ('192.168.55.7', 3000),
            'vscode': ('192.168.55.7', 8443),
            'jupyter': ('192.168.55.7', 8888),
        }
        for key, endpoint in expected.items():
            with self.subTest(service=key):
                service = self.services[key]
                self.assertEqual((service['ip'], service['port']), endpoint)
                self.assertEqual(service['protocol'], 'http')
                self.assertIs(service['websocket'], True)
                self.assertIs(service['npm_enabled'], False)

    def test_duplicate_domains_case_and_trailing_dot(self):
        self.services['npm']['domain'] = 'GIT.HOME.LAB.'
        with self.assertRaisesRegex(ValueError, 'duplicate domain'):
            validator.validate_catalogue(self.data)

    def test_proxmox_panels_use_user_supplied_endpoints(self):
        for host, ip in [('dom', '192.168.55.3'), ('dtcode', '192.168.55.6')]:
            with self.subTest(host=host):
                service = self.services[host]
                self.assertEqual(service['host'], host)
                self.assertEqual(service['ip'], ip)
                self.assertEqual(service['domain'], f'pve-{host}.home.lab')
                self.assertEqual(service['port'], 8006)
                self.assertEqual(service['protocol'], 'https')
                self.assertIs(service['npm_enabled'], False)
                self.assertIs(service['websocket'], True)
        self.assertNotIn('tdcode', self.services)
        self.assertNotIn('tdcode', {s['host'] for s in self.services.values()})

    def test_websocket_optional_boolean_and_unknown_fields(self):
        # Existing services do not need a schema migration.
        self.services['homepage'].pop('websocket')
        validator.validate_catalogue(self.data)
        for value in (True, False):
            self.services['homepage']['websocket'] = value
            validator.validate_catalogue(self.data)
        for value in ('true', 'false', 0, 1, None, [], {}):
            self.services['dom']['websocket'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'websocket must be boolean'):
                validator.validate_catalogue(self.data)
        self.services['dom']['websocket'] = True
        self.services['dom']['websockets'] = True
        with self.assertRaisesRegex(ValueError, 'unexpected or missing fields'):
            validator.validate_catalogue(self.data)

    def test_proxmox_domains_participate_in_uniqueness_validation(self):
        self.services['npm']['domain'] = 'PVE-DTCODE.HOME.LAB.'
        with self.assertRaisesRegex(ValueError, 'duplicate domain'):
            validator.validate_catalogue(self.data)

    def test_invalid_values(self):
        cases = {'domain': ['', 'bad_name.home.lab', '-bad.home.lab', 'https://git.home.lab'],
                 'ip': ['192.168.55.999', 'host.home.lab', 123, '192.168.55.7/24'],
                 'port': [0, -1, 65536, True, '81', 81.5],
                 'protocol': ['tcp', 'HTTP', '', 123],
                 'npm_enabled': ['false', 0, None]}
        for field, values in cases.items():
            for value in values:
                data = copy.deepcopy(self.data)
                data['infrastructure_services']['npm'][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    validator.validate_catalogue(data)

    def test_valid_boundaries_and_ipv6(self):
        for port in (1, 65535):
            self.services['npm'].update(port=port, ip='2001:db8::1', protocol='https')
            validator.validate_catalogue(self.data)

    def test_unknown_values_allowed_only_while_disabled(self):
        for field in ('domain', 'ip', 'port', 'protocol'):
            data = copy.deepcopy(self.data)
            service = data['infrastructure_services']['forgejo']
            service[field] = None
            validator.validate_catalogue(data)
            service['npm_enabled'] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'complete endpoint'):
                validator.validate_catalogue(data)

    def test_missing_or_malformed_structure(self):
        for data in ([], {}, {'infrastructure_services': []}, {'infrastructure_services': {}},
                     {'infrastructure_services': {'npm': {}}}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                validator.validate_catalogue(data)

    def test_duplicate_yaml_subset_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'services.yml'
            path.write_text('{"infrastructure_services": {"npm": {}, "npm": {}}}')
            with self.assertRaisesRegex(ValueError, 'Duplicate key'):
                validator.load_catalogue(path)

    def test_grafana_excluded(self):
        self.services['grafana'] = copy.deepcopy(self.services['npm'])
        with self.assertRaisesRegex(ValueError, 'Grafana'):
            validator.validate_catalogue(self.data)

    def test_zabbix_endpoint_matches_existing_owner_without_executing_it(self):
        tree = ast.parse((ROOT / 'ansible/roles/zabbix_local_access/files/access.py').read_text())
        domain = next(ast.literal_eval(node.value) for node in tree.body
                      if isinstance(node, ast.Assign) and any(
                          isinstance(target, ast.Name) and target.id == 'DOMAIN' for target in node.targets))
        desired = next(node.value for node in ast.walk(tree)
                       if isinstance(node, ast.Assign) and any(
                           isinstance(target, ast.Name) and target.id == 'desired' for target in node.targets))
        fields = {keyword.arg: keyword.value for keyword in desired.keywords}
        service = self.services['zabbix']
        self.assertEqual(service['domain'], domain)
        self.assertEqual(service['protocol'], ast.literal_eval(fields['forward_scheme']))
        self.assertEqual(service['port'], ast.literal_eval(fields['forward_port']))
        shared = (ROOT / 'ansible/inventories/production/group_vars/all/zabbix.yml').read_text()
        self.assertIn('zabbix_server_ip: ' + service['ip'], shared)
        self.assertEqual(set(self.data), {'infrastructure_services'})
        service['npm_enabled'] = True
        with self.assertRaisesRegex(ValueError, 'zabbix_local_access'):
            validator.validate_catalogue(self.data)


if __name__ == '__main__':
    unittest.main()
