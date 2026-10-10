"""Offline tests of the exact filter used by the bootstrap Ansible tasks."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / 'ansible/roles/zabbix_server'
spec = importlib.util.spec_from_file_location(
    'bootstrap_filter', ROLE / 'filter_plugins/bootstrap_diagnostic.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sanitize = module.FilterModule().filters()['zabbix_bootstrap_diagnostic']
SECRET = 'secret-canary-never-display'


class DiagnosticTests(unittest.TestCase):
    def check_result(self, payload, rc=0):
        result = sanitize({'stdout': json.dumps(payload), 'rc': rc,
                           'stderr': SECRET, 'stdin': SECRET})
        self.assertNotIn(SECRET, json.dumps(result))
        self.assertEqual(set(result), {'failed', 'changed', 'stage', 'code'})
        return result

    def test_success_and_idempotent_repeat(self):
        for changed in (True, False):
            result = self.check_result({'failed': False, 'changed': changed,
                                       'warnings': [{'message': SECRET}], 'token': SECRET})
            self.assertFalse(result['failed'])
            self.assertIs(result['changed'], changed)

    def test_verified_failure_even_with_zero_exit_status(self):
        for rc in (0, 1):
            result = self.check_result({'failed': True, 'changed': False,
                                       'stage': 'password_update', 'code': 'RPC_ERROR',
                                       'message': SECRET}, rc)
            self.assertEqual(result, {'failed': True, 'changed': False,
                                      'stage': 'password_update', 'code': 'RPC_ERROR'})

    def test_invalid_json_never_displays_raw_output(self):
        for stdout in ('', SECRET, '{"password": "' + SECRET, 'null', '[]'):
            result = sanitize({'stdout': stdout, 'rc': 1, 'stderr': SECRET})
            self.assertEqual(result['code'], 'DIAGNOSTIC_UNAVAILABLE')
            self.assertTrue(result['failed'])
            self.assertFalse(result['changed'])
            self.assertNotIn(SECRET, json.dumps(result))

    def test_closed_values_and_strict_boolean_types(self):
        valid = {'failed': True, 'changed': False, 'stage': 'input', 'code': 'INVALID_JSON'}
        for field, values in {
            'failed': [None, 0, 1, 'false', SECRET],
            'changed': [None, 0, 1, 'true', True, SECRET],
            'stage': [None, [], {}, SECRET],
            'code': [None, [], {}, SECRET],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    result = self.check_result(dict(valid, **{field: value}))
                    self.assertTrue(result['failed'])
                    self.assertFalse(result['changed'])
                    self.assertEqual(result['code'], 'DIAGNOSTIC_UNAVAILABLE')
        for field in valid:
            payload = dict(valid)
            del payload[field]
            self.assertEqual(self.check_result(payload)['code'], 'DIAGNOSTIC_UNAVAILABLE')

    def test_nonzero_exit_status_cannot_be_success(self):
        result = self.check_result({'failed': False, 'changed': True}, rc=2)
        self.assertTrue(result['failed'])
        self.assertFalse(result['changed'])

    def test_success_rejects_untrusted_diagnostics(self):
        for field in ('stage', 'code'):
            result = self.check_result({'failed': False, 'changed': False, field: SECRET})
            self.assertTrue(result['failed'])

    def test_missing_command_result_fails_closed(self):
        for value in ({}, None, {'stdout': '{}'}, {'stdout': '{}', 'rc': True}):
            self.assertTrue(sanitize(value)['failed'])

    def test_ansible_tasks_only_publish_sanitized_fields(self):
        tasks = (ROLE / 'tasks/main.yml').read_text()
        command, remaining = tasks.split('- name: Secure the initial administrator', 1)[1].split(
            '- name: Validate and sanitize', 1)
        self.assertIn('no_log: true', command)
        self.assertIn('failed_when: false', command)
        self.assertIn('changed_when: (zabbix_admin_result | zabbix_bootstrap_diagnostic).changed', command)
        sanitizer, failure = remaining.split('- name: Stop before publishing', 1)
        self.assertIn('no_log: true', sanitizer)
        self.assertIn('zabbix_admin_result | zabbix_bootstrap_diagnostic', sanitizer)
        self.assertIn('ansible.builtin.fail:', failure)
        self.assertIn('msg: "stage={{ zabbix_admin_diagnostic.stage }} code={{ zabbix_admin_diagnostic.code }}"', failure)
        self.assertIn('- zabbix_admin_diagnostic.failed', failure)
        self.assertNotIn('zabbix_admin_result', failure)
        self.assertEqual(command.count('when: not ansible_check_mode'), 1)
        self.assertIn('when: not ansible_check_mode', sanitizer)
        self.assertIn('- not ansible_check_mode', failure)


if __name__ == '__main__':
    unittest.main()
