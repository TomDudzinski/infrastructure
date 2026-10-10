"""Read-only comparison tests using synthetic NPM data, never a live API."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / 'ansible/roles/npm_proxy_hosts'
spec = importlib.util.spec_from_file_location('proxy_hosts', ROLE / 'filter_plugins/proxy_hosts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProxyHostsTests(unittest.TestCase):
    def setUp(self):
        self.services = json.loads((ROOT / 'ansible/inventories/production/group_vars/all/services.yml').read_text())['infrastructure_services']
        self.hosts = json.loads((ROOT / 'tests/fixtures/npm/proxy_hosts.json').read_text())

    def compare(self):
        # Accidental future network use fails immediately.
        with patch('socket.socket', side_effect=AssertionError('Network forbidden')), patch(
            'urllib.request.urlopen', side_effect=AssertionError('API forbidden')
        ):
            return module.npm_proxy_hosts_compare(self.services, self.hosts)

    def conflict(self, service):
        return next(row for row in self.compare()['conflict'] if row['service'] == service)

    def test_fixture_disabled_catalogue_and_external_zabbix(self):
        report = self.compare()
        self.assertEqual(set(report), {'matching', 'missing', 'conflict', 'unmanaged', 'snapshot_visibility'})
        self.assertEqual({row['service'] for row in report['matching']}, {'forgejo', 'zabbix'})
        self.assertTrue(all(row['npm_enabled'] is False for row in report['matching']))
        zabbix = next(row for row in report['matching'] if row['service'] == 'zabbix')
        self.assertEqual(zabbix['owner'], 'zabbix_local_access')
        self.assertEqual(zabbix['proxy_host_ids'], [20])
        self.assertEqual(report['conflict'], [])
        self.assertEqual({row['service'] for row in report['missing']}, {'openbao', 'dom', 'dtcode'})
        self.assertIn({'proxy_host_id': 10, 'domains': ['forgejo-alias.home.lab'],
                       'reason': 'domains_outside_catalogue'}, report['unmanaged'])
        self.assertIn({'proxy_host_id': 30, 'domains': ['grafana.tdcode.pl'],
                       'reason': 'domains_outside_catalogue'}, report['unmanaged'])

    def test_no_input_mutation_or_raw_config_disclosure(self):
        before = copy.deepcopy((self.services, self.hosts))
        self.hosts[1]['token'] = 'test-secret-do-not-report'
        report = self.compare()
        self.hosts[1].pop('token')
        self.assertEqual((self.services, self.hosts), before)
        self.assertNotIn('test-secret', json.dumps(report))
        self.assertNotIn('advanced_config', json.dumps(report))

    def test_multi_domain_host_with_two_catalogue_services(self):
        self.services['alias'] = dict(self.services['forgejo'], domain='forgejo-alias.home.lab')
        report = self.compare()
        matches = {row['service']: row for row in report['matching']}
        self.assertEqual(matches['alias']['proxy_host_ids'], [10])
        self.assertEqual(matches['forgejo']['proxy_host_ids'], [10])

    def test_catalogue_domain_in_second_position_and_normalization(self):
        self.hosts[0]['domain_names'] = ['forgejo-alias.home.lab', 'GIT.HOME.LAB.']
        self.assertIn('forgejo', {row['service'] for row in self.compare()['matching']})

    def test_duplicate_hosts_including_existing_zabbix_route(self):
        self.hosts.append(dict(self.hosts[1], id=21, domain_names=['other.home.lab', 'ZABBIX.HOME.LAB.']))
        row = self.conflict('zabbix')
        self.assertIn('multiple_proxy_hosts', row['reasons'])
        self.assertEqual(row['proxy_host_ids'], [20, 21])
        self.assertEqual(row['owner'], 'zabbix_local_access')

    def test_duplicate_catalogue_domain_conflicts_for_both_services(self):
        self.services['alias'] = dict(self.services['forgejo'], domain='GIT.HOME.LAB.')
        for key in ('forgejo', 'alias'):
            self.assertIn('duplicate_catalogue_domain', self.conflict(key)['reasons'])

    def test_wrong_zabbix_target_disabled_proxy_and_websocket(self):
        cases = [('forward_host', '192.168.55.250', 'ip_mismatch'),
                 ('forward_port', 80, 'port_mismatch'),
                 ('forward_scheme', 'https', 'protocol_mismatch'),
                 ('enabled', False, 'proxy_host_disabled')]
        original = copy.deepcopy(self.hosts[1])
        for field, value, reason in cases:
            self.hosts[1] = dict(original, **{field: value})
            with self.subTest(field=field):
                self.assertIn(reason, self.conflict('zabbix')['reasons'])
        self.hosts[1] = original
        self.services['zabbix']['websocket'] = True
        self.assertIn('websocket_mismatch', self.conflict('zabbix')['reasons'])

    def test_wildcard_overlap_is_never_matching(self):
        self.hosts.append(dict(self.hosts[0], id=40, domain_names=['*.home.lab']))
        for key in ('forgejo', 'zabbix', 'dom', 'dtcode'):
            self.assertIn('wildcard_overlap', self.conflict(key)['reasons'])

    def test_duplicate_domains_within_one_proxy_host(self):
        self.hosts[0]['domain_names'].append('GIT.HOME.LAB.')
        self.assertIn('duplicate_proxy_domain', self.conflict('forgejo')['reasons'])

    def test_duplicate_domains_outside_catalogue_still_report_conflict(self):
        self.hosts.append(dict(self.hosts[2], id=31, domain_names=['GRAFANA.TDCODE.PL.']))
        self.assertIn({'domain': 'grafana.tdcode.pl', 'proxy_host_ids': [30, 31],
                       'reasons': ['duplicate_unmanaged_domain']}, self.compare()['conflict'])

    def test_incomplete_catalogue_does_not_claim_matching(self):
        self.services['forgejo']['protocol'] = None
        self.assertIn('incomplete_catalogue_endpoint', self.conflict('forgejo')['reasons'])
        self.assertIn('homepage', {row.get('service') for row in self.compare()['unmanaged']})

    def test_empty_snapshot_is_explicit_missing_not_deletion(self):
        self.hosts = []
        report = self.compare()
        self.assertEqual(len(report['missing']), 5)
        self.assertEqual(report['matching'], [])
        self.assertNotIn('delete', json.dumps(report))
        self.assertEqual(report['snapshot_visibility']['completeness'], 'unverified')
        self.assertTrue(all(row['reason'] == 'no_visible_proxy_host' for row in report['missing']))

    def test_owner_filtered_snapshot_does_not_claim_completeness(self):
        self.hosts = self.hosts[:1]
        report = self.compare()
        self.assertEqual(report['snapshot_visibility']['warning'],
                         'owner_permissions_may_limit_visibility')
        self.assertEqual(report['snapshot_visibility']['completeness'], 'unverified')
        self.assertIn('zabbix', {row['service'] for row in report['missing']})

    def test_websocket_mapping_true_false_and_unspecified(self):
        for desired, actual in ((True, True), (False, False), (True, False), (False, True)):
            with self.subTest(desired=desired, actual=actual):
                self.services['forgejo']['websocket'] = desired
                self.hosts[0]['allow_websocket_upgrade'] = actual
                report = self.compare()
                if desired == actual:
                    self.assertIn('forgejo', {row['service'] for row in report['matching']})
                else:
                    self.assertIn('websocket_mismatch', self.conflict('forgejo')['reasons'])
        self.services['forgejo'].pop('websocket')
        self.assertIn('forgejo', {row['service'] for row in self.compare()['matching']})

    def test_invalid_snapshot_rejected_not_replaced_by_empty_list(self):
        for invalid in (None, {}, [{'id': 1}], [self.hosts[0], self.hosts[0]]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                module.npm_proxy_hosts_compare(self.services, invalid)
        for field, value in [('domain_names', 'git.home.lab'), ('domain_names', []),
                             ('forward_port', True), ('enabled', 'false')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                module.npm_proxy_hosts_compare(self.services, [dict(self.hosts[0], **{field: value})])

    def test_filter_registration_and_role_has_only_controller_operations(self):
        self.assertIs(module.FilterModule().filters()['npm_proxy_hosts_compare'], module.npm_proxy_hosts_compare)
        tasks = (ROLE / 'tasks/main.yml').read_text()
        operations = [line.strip().split(':')[0] for line in tasks.splitlines() if 'ansible.builtin.' in line]
        self.assertEqual(operations, ['ansible.builtin.include_tasks', 'ansible.builtin.assert', 'ansible.builtin.set_fact', 'ansible.builtin.debug'])
        self.assertIn('changed_when: false', tasks)

    def test_zabbix_fixture_preserves_existing_role_marker_and_acl(self):
        tree = ast.parse((ROOT / 'ansible/roles/zabbix_local_access/files/access.py').read_text())
        marker = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'MARKER' for t in n.targets))
        self.assertEqual(self.hosts[1]['advanced_config'], marker + '\nallow 192.168.55.0/24;\ndeny all;\n')
        self.assertEqual(self.hosts[1]['certificate_id'], 0)
        self.assertIs(self.hosts[1]['ssl_forced'], False)


if __name__ == '__main__':
    unittest.main()
