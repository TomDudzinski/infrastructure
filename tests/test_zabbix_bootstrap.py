"""Offline bootstrap diagnostics: every HTTP request is intercepted."""
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'bootstrap_diagnostics', ROOT / 'ansible/roles/zabbix_server/files/bootstrap_admin.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
SECRET = 'credential-canary-never-log'
SETTINGS = {'password': SECRET, 'allow_initial_password': True}


class BootstrapTests(unittest.TestCase):
    def execute(self, responses, settings=None):
        calls = []
        responses = iter(responses)

        def fake(request, timeout):
            calls.append(json.loads(request.data)['method'])
            value = next(responses)
            if isinstance(value, Exception):
                raise value
            return io.BytesIO(value if isinstance(value, bytes) else json.dumps(value).encode())

        with patch.object(bootstrap, 'urlopen', fake):
            result = bootstrap.run(SETTINGS if settings is None else settings)
        self.assertNotIn(SECRET, json.dumps(result))
        return result, calls

    def prefix(self):
        return [{'error': {'data': SECRET}}, {'result': SECRET},
                {'result': [{'userid': '1'}]}, {'result': {'userids': ['1']}}]

    def test_each_stage_sanitizes_protocol_and_transport_failures(self):
        failures = [({'error': {'message': SECRET, 'data': SECRET}}, 'RPC_ERROR'),
                    ({}, 'MISSING_RESULT'), (b'not-json-' + SECRET.encode(), 'INVALID_JSON'),
                    ([], 'INVALID_RESPONSE'),
                    (HTTPError('http://localhost/' + SECRET, 403, SECRET, {}, None), 'HTTP_ERROR'),
                    (URLError(SECRET), 'TRANSPORT_ERROR'),
                    (RuntimeError(SECRET), 'UNEXPECTED_ERROR')]
        for stage, index in [('target_login', 0), ('initial_login', 1),
                             ('user_read', 2), ('password_update', 3), ('logout', 4)]:
            for failure, code in failures:
                with self.subTest(stage=stage, code=code):
                    responses = self.prefix()[:index] + [failure]
                    if index in (2, 3):
                        responses.append({'result': True})
                    settings = dict(SETTINGS, allow_initial_password=False) if index == 0 else SETTINGS
                    result, calls = self.execute(responses, settings)
                    if stage == 'logout':
                        self.assertFalse(result['failed'])
                        self.assertTrue(result['changed'])
                        self.assertEqual(result['warnings'], [{'stage': stage, 'code': code}])
                    else:
                        self.assertTrue(result['failed'])
                        self.assertEqual(result['stage'], stage)
                        expected = 'INITIAL_PASSWORD_NOT_APPROVED' if index == 0 and code == 'RPC_ERROR' else code
                        self.assertEqual(result['code'], expected)
                    if index == 0:
                        self.assertEqual(calls, ['user.login'])

    def test_cleanup_preserves_primary_error(self):
        result, calls = self.execute(self.prefix()[:2] + [
            {'error': {'data': SECRET}}, URLError(SECRET)])
        self.assertEqual((result['stage'], result['code']), ('user_read', 'RPC_ERROR'))
        self.assertEqual(result['warnings'], [{'stage': 'logout', 'code': 'TRANSPORT_ERROR'}])
        self.assertEqual(calls[-1], 'user.logout')

    def test_confirmed_update_then_repeat_with_logout_failure(self):
        result, calls = self.execute(self.prefix() + [{'error': {'data': SECRET}}])
        self.assertTrue(result['changed'])
        self.assertFalse(result['failed'])
        self.assertEqual(calls.count('user.update'), 1)
        result, calls = self.execute([{'result': SECRET}, URLError(SECRET)])
        self.assertFalse(result['changed'])
        self.assertFalse(result['failed'])
        self.assertEqual(calls, ['user.login', 'user.logout'])
        self.assertEqual(result['warnings'][0]['stage'], 'logout')

    def test_update_requires_matching_userid_confirmation(self):
        for value in ({}, None, True, {'userids': []}, {'userids': ['2']}):
            with self.subTest(value=value):
                result, _ = self.execute(self.prefix()[:3] + [{'result': value}, {'result': True}])
                self.assertEqual(result['code'], 'UPDATE_NOT_CONFIRMED')
                self.assertTrue(result['failed'])

    def test_update_sends_password_used_for_initial_login(self):
        for response, expected_code in [
                ({'result': {'userids': ['1']}}, None),
                ({'result': {'userids': ['2']}}, 'UPDATE_NOT_CONFIRMED'),
                ({'error': {'data': SECRET}}, 'RPC_ERROR')]:
            with self.subTest(code=expected_code):
                requests = []
                responses = iter(self.prefix()[:3] + [response, {'result': True}])

                def fake(request, timeout):
                    requests.append(json.loads(request.data))
                    return io.BytesIO(json.dumps(next(responses)).encode())

                stdout, stderr = io.StringIO(), io.StringIO()
                with patch.object(bootstrap, 'urlopen', fake), \
                        patch.object(bootstrap.sys, 'stdin', io.StringIO(json.dumps(SETTINGS))), \
                        patch.object(bootstrap.sys, 'stdout', stdout), \
                        patch.object(bootstrap.sys, 'stderr', stderr):
                    status = bootstrap.cli()
                initial_login = requests[1]['params']
                update = requests[3]['params']
                self.assertEqual(requests[1]['method'], 'user.login')
                self.assertEqual(requests[3]['method'], 'user.update')
                self.assertEqual(initial_login['password'], 'zabbix')
                self.assertEqual(update, {'userid': '1', 'passwd': SECRET,
                                          'current_passwd': initial_login['password']})
                self.assertEqual(requests[-1]['method'], 'user.logout')
                result = json.loads(stdout.getvalue())
                self.assertEqual(status, 1 if expected_code else 0)
                self.assertEqual(result['failed'], expected_code is not None)
                self.assertEqual(result['changed'], expected_code is None)
                if expected_code:
                    self.assertEqual((result['stage'], result['code']),
                                     ('password_update', expected_code))
                for secret in (SECRET, initial_login['password']):
                    self.assertNotIn(secret, stdout.getvalue() + stderr.getvalue())
                self.assertEqual(stderr.getvalue(), '')

    def test_invalid_tokens_and_user_shapes(self):
        for token in ('', None, {}, True):
            result, calls = self.execute([{'result': token}])
            self.assertEqual(result['code'], 'INVALID_TOKEN')
            self.assertEqual(calls, ['user.login'])
        for users in (None, {}, [], [{}], [{'userid': SECRET}], [{'userid': '1'}, {'userid': '2'}]):
            result, calls = self.execute(self.prefix()[:2] + [{'result': users}, {'result': True}])
            self.assertEqual(result['code'], 'INVALID_ADMIN_RESULT')
            self.assertNotIn('user.update', calls)

    def test_cli_exit_status_and_no_secret_output(self):
        for payload, outcome, expected_status in [(SECRET, None, 1),
                                                   (json.dumps(SETTINGS), {'error': {'data': SECRET}}, 1),
                                                   (json.dumps(SETTINGS), {'result': SECRET}, 0)]:
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(bootstrap.sys, 'stdin', io.StringIO(payload)), \
                    patch.object(bootstrap.sys, 'stdout', stdout), \
                    patch.object(bootstrap.sys, 'stderr', stderr), \
                    patch.object(bootstrap, 'urlopen', return_value=io.BytesIO(json.dumps(outcome).encode())):
                status = bootstrap.cli()
            self.assertEqual(status, expected_status)
            self.assertNotIn(SECRET, stdout.getvalue() + stderr.getvalue())
            self.assertEqual(json.loads(stdout.getvalue())['failed'], bool(expected_status))
            self.assertEqual(stderr.getvalue(), '')

    def test_no_log_remains_enabled(self):
        tasks = (ROOT / 'ansible/roles/zabbix_server/tasks/main.yml').read_text()
        task = tasks.split('- name: Secure the initial administrator', 1)[1]
        self.assertIn('no_log: true', task)
        self.assertIn('diff: false', task)


if __name__ == '__main__':
    unittest.main()
