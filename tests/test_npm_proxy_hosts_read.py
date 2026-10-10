"""Adapter tests with fake HTTP responses; real sockets are forbidden."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / 'ansible/roles/npm_proxy_hosts'
spec = importlib.util.spec_from_file_location('npm_read', ROLE / 'library/npm_proxy_hosts_read.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
spec = importlib.util.spec_from_file_location('npm_compare', ROLE / 'filter_plugins/proxy_hosts.py')
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


class Response(io.BytesIO):
    def __init__(self, body, status=200, headers=None):
        super().__init__(body)
        self.status = status
        self.headers = {'Content-Type': 'application/json', **(headers or {})}


class FakeOpener:
    def __init__(self, response=None, error=None):
        self.response, self.error = response, error
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


class ReadTests(unittest.TestCase):
    def setUp(self):
        self.hosts = json.loads((ROOT / 'tests/fixtures/npm/proxy_hosts.json').read_text())
        self.settings = dict(url='https://npm.example.test/api/nginx/proxy-hosts',
                             token='fake-test-token', contract_verified=True)

    def read(self, body=None, status=200, headers=None, error=None):
        if body is None:
            body = json.dumps(self.hosts).encode()
        self.opener = FakeOpener(Response(body, status, headers), error)
        with patch('socket.socket', side_effect=AssertionError('Real network forbidden')):
            return adapter.read_snapshot(**self.settings, opener=self.opener)

    def test_get_bearer_and_existing_comparison(self):
        snapshot = self.read()
        request, timeout = self.opener.calls[0]
        self.assertEqual(request.get_method(), 'GET')
        self.assertIsNone(request.data)
        self.assertEqual(request.get_header('Authorization'), 'Bearer fake-test-token')
        self.assertEqual(timeout, 30)
        self.assertNotIn('advanced_config', snapshot[1])
        services = json.loads((ROOT / 'ansible/inventories/production/group_vars/all/services.yml').read_text())['infrastructure_services']
        report = comparison.npm_proxy_hosts_compare(services, snapshot)
        self.assertEqual({row['service'] for row in report['matching']}, {'forgejo', 'zabbix'})

    def test_successful_empty_response_is_distinct_from_failure(self):
        self.assertEqual(self.read(b'[]'), [])

    def test_multi_domain_order_and_websocket_are_preserved(self):
        self.hosts[0]['domain_names'].reverse()
        self.hosts[0]['allow_websocket_upgrade'] = True
        snapshot = self.read()
        self.assertEqual(snapshot[0]['domain_names'], self.hosts[0]['domain_names'])
        self.assertIs(snapshot[0]['allow_websocket_upgrade'], True)

    def test_every_required_field_is_validated(self):
        for field in adapter.FIELDS:
            host = dict(self.hosts[0])
            del host[field]
            with self.subTest(field=field), self.assertRaisesRegex(adapter.ReadError, '^INVALID_RESPONSE$'):
                self.read(json.dumps([host]).encode())

    def test_malformed_domains_and_optional_tls_fields(self):
        for field, value in [('domain_names', ['git. home.lab']),
                             ('domain_names', ['git.home.lab\n']),
                             ('certificate_id', True), ('certificate_id', -1),
                             ('certificate_id', '0'), ('ssl_forced', 0),
                             ('ssl_forced', 'false')]:
            with self.subTest(field=field, value=value), self.assertRaisesRegex(adapter.ReadError, '^INVALID_RESPONSE$'):
                self.read(json.dumps([dict(self.hosts[0], **{field: value})]).encode())

    def test_owner_filtered_list_and_equal_total_do_not_prove_completeness(self):
        self.hosts = self.hosts[:1]
        snapshot = self.read(headers={'X-Total-Count': '1'})
        report = comparison.npm_proxy_hosts_compare({}, snapshot)
        self.assertEqual(report['snapshot_visibility']['completeness'], 'unverified')

    def test_http_authorization_and_server_errors(self):
        for code, diagnostic in [(401, 'AUTHORIZATION_FAILED'), (403, 'AUTHORIZATION_FAILED'),
                                 (404, 'HTTP_ERROR'), (500, 'HTTP_ERROR'), (302, 'REDIRECT_REJECTED')]:
            error = HTTPError(self.settings['url'], code, 'fake-secret-server-message', {}, None)
            with self.subTest(code=code), self.assertRaisesRegex(adapter.ReadError, '^' + diagnostic + '$'):
                self.read(error=error)
        for status in (401, 403, 500, 204):
            with self.subTest(status=status), self.assertRaises(adapter.ReadError):
                self.read(status=status)

    def test_connection_timeout_and_tls_errors_are_sanitized(self):
        for error in (URLError('fake-secret'), TimeoutError('fake-secret'), OSError('fake-secret')):
            with self.subTest(error=type(error).__name__), self.assertRaisesRegex(adapter.ReadError, '^CONNECTION_FAILED$'):
                self.read(error=error)

    def test_invalid_json_encoding_and_duplicate_keys(self):
        for body in (b'<html>login</html>', b'', b'\xff', b'[{"id":1,"id":2}]',
                     b'[NaN]', b'[Infinity]', b'[-Infinity]'):
            with self.subTest(body=body), self.assertRaisesRegex(adapter.ReadError, '^INVALID_RESPONSE$'):
                self.read(body)

    def test_unknown_wrapper_and_wrong_fields_never_become_empty(self):
        payloads = [None, {}, {'data': self.hosts}, {'error': 'fake-secret'}, [None], [{}]]
        for field, value in [('id', True), ('forward_port', '8080'), ('enabled', 1),
                             ('allow_websocket_upgrade', None), ('domain_names', []),
                             ('domain_names', [12]), ('forward_scheme', 'tcp')]:
            payloads.append([dict(self.hosts[0], **{field: value})])
        payloads.append([self.hosts[0], self.hosts[0]])
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(adapter.ReadError):
                self.read(json.dumps(payload).encode())

    def test_content_type_pagination_and_incomplete_list(self):
        for headers, diagnostic in [({'Content-Type': 'text/html'}, 'INVALID_CONTENT_TYPE'),
                                    ({'Link': '<fake>; rel=next'}, 'PAGINATION_NOT_SUPPORTED'),
                                    ({'X-Next-Page': '2'}, 'PAGINATION_NOT_SUPPORTED'),
                                    ({'Content-Range': '0-2/20'}, 'PAGINATION_NOT_SUPPORTED'),
                                    ({'X-Total-Count': '4'}, 'INCOMPLETE_RESPONSE'),
                                    ({'X-Total-Count': 'bad'}, 'INCOMPLETE_RESPONSE')]:
            with self.subTest(headers=headers), self.assertRaisesRegex(adapter.ReadError, diagnostic):
                self.read(headers=headers)
        self.assertEqual(len(self.read(headers={'X-Total-Count': '3'})), 3)

    def test_response_size_limit(self):
        with patch.object(adapter, 'MAX_BYTES', 3), self.assertRaisesRegex(adapter.ReadError, 'RESPONSE_TOO_LARGE'):
            self.read(b'[  ]')

    def test_contract_guard_and_settings_reject_before_any_request(self):
        cases = [('contract_verified', False), ('token', ''), ('token', 'fake\nsecret'),
                 ('url', 'http://192.168.55.23:81/api/nginx/proxy-hosts'),
                 ('url', 'https://user:password@npm.example.test/api/hosts'),
                 ('url', 'https://npm.example.test/api/hosts?token=fake-secret'),
                 ('url', 'https://npm.example.test/api/hosts#fragment'),
                 ('url', 'https://npm.example.test/api/nginx/streams'),
                 ('url', 'https://npm.example.test/api/hosts\n'),
                 ('url', 'file:///etc/passwd'), ('timeout', 0)]
        for field, value in cases:
            with self.subTest(field=field), self.assertRaises(adapter.ReadError):
                adapter.read_snapshot(**dict(self.settings, **{field: value}), opener=FakeOpener())

    def test_loopback_tunnel_allowed(self):
        self.settings['url'] = 'http://127.0.0.1:18081/api/nginx/proxy-hosts'
        self.assertEqual(len(self.read()), 3)

    def test_redirects_never_forward_credentials(self):
        with self.assertRaisesRegex(adapter.ReadError, 'REDIRECT_REJECTED'):
            adapter.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.example.test')

    def test_default_transport_disables_proxies_and_uses_verified_tls(self):
        opener = FakeOpener(Response(b'[]'))
        with patch.object(adapter, 'build_opener', return_value=opener) as factory:
            self.assertEqual(adapter.read_snapshot(**self.settings), [])
        handlers = factory.call_args.args
        self.assertEqual(handlers[0].proxies, {})
        self.assertIsInstance(handlers[1], adapter.NoRedirect)
        self.assertTrue(handlers[2]._context.check_hostname)

    def test_module_host_guard_check_mode_and_safe_error_output(self):
        class Finished(BaseException):
            pass

        class FakeModule:
            params = dict(self.settings, timeout=30)
            check_mode = False

            def exit_json(fake, **result):
                fake.result = result
                raise Finished()

            def fail_json(fake, **result):
                fake.result = result
                raise Finished()

        fake = FakeModule()
        basic = types.ModuleType('ansible.module_utils.basic')
        basic.AnsibleModule = lambda **kwargs: fake
        modules = {'ansible': types.ModuleType('ansible'),
                   'ansible.module_utils': types.ModuleType('ansible.module_utils'),
                   'ansible.module_utils.basic': basic}
        with patch.dict(sys.modules, modules), patch.object(adapter, 'read_snapshot') as read:
            with patch.object(adapter.socket, 'gethostname', return_value='development'), self.assertRaises(Finished):
                adapter.main()
            self.assertEqual(fake.result['code'], 'EXECUTION_HOST_MUST_BE_IZA')
            read.assert_not_called()
            fake.check_mode = True
            with patch.object(adapter.socket, 'gethostname', return_value='iza'), self.assertRaises(Finished):
                adapter.main()
            self.assertTrue(fake.result['skipped'])
            read.assert_not_called()
            fake.check_mode = False
            read.side_effect = RuntimeError('fake-secret-error')
            with patch.object(adapter.socket, 'gethostname', return_value='iza'), self.assertRaises(Finished):
                adapter.main()
            self.assertEqual(fake.result['code'], 'UNEXPECTED_ERROR')
            self.assertIs(fake.result['changed'], False)
            self.assertNotIn('fake-secret', json.dumps(fake.result))
            read.side_effect = None
            read.return_value = []
            with patch.object(adapter.socket, 'gethostname', return_value='iza'), self.assertRaises(Finished):
                adapter.main()
            self.assertEqual(fake.result['snapshot'], [])
            self.assertEqual(fake.result['snapshot_scope'], 'token_visible')
            self.assertEqual(fake.result['completeness'], 'unverified')


if __name__ == '__main__':
    unittest.main()
