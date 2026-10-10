"""Offline regressions: fake psql/gzip only, no database or network access."""
import os
import configparser
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / 'ansible/roles/zabbix_server'


class ServerTests(unittest.TestCase):
    def test_pid_matches_reported_systemd_unit(self):
        # Contract supplied in the incident report: Type=forking and this PIDFile.
        config = (ROLE / 'templates/zabbix_server.conf.j2').read_text()
        pid_files = [line.split('=', 1)[1].strip() for line in config.splitlines()
                     if line.startswith('PidFile=')]
        self.assertEqual(pid_files, ['/run/zabbix/zabbix_server.pid'])

    @unittest.skipUnless(os.environ.get('ZABBIX_SERVER_DEB'),
                         'set ZABBIX_SERVER_DEB to inspect a local package offline')
    def test_local_package_pid_and_runtime_directory(self):
        package = Path(os.environ['ZABBIX_SERVER_DEB']).resolve()
        version = subprocess.check_output(
            ['dpkg-deb', '-f', str(package), 'Version'], text=True).strip()
        self.assertEqual(version, '1:7.0.31-1+ubuntu24.04')
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(['dpkg-deb', '-x', str(package), directory], check=True)
            root = Path(directory)
            units = list(root.rglob('zabbix-server.service'))
            self.assertEqual(len(units), 1)
            unit = configparser.ConfigParser(interpolation=None, strict=False)
            unit.read(units[0])
            service = unit['Service']
            self.assertEqual(service['Type'], 'forking')
            config = (ROLE / 'templates/zabbix_server.conf.j2').read_text()
            self.assertIn('\nPidFile=' + service['PIDFile'] + '\n', config)
            self.assertEqual(service['PIDFile'], '/run/zabbix/zabbix_server.pid')
            if service.get('RuntimeDirectory') == 'zabbix':
                self.assertEqual(service['User'], 'zabbix')
                self.assertEqual(service.get('Group', service['User']), 'zabbix')
                self.assertEqual(int(service.get('RuntimeDirectoryMode', '0755'), 8), 0o755)
            else:
                entries = []
                for path in root.rglob('*.conf'):
                    if path.parent.name == 'tmpfiles.d':
                        entries.extend(line.split() for line in path.read_text().splitlines()
                                       if line.strip() and not line.lstrip().startswith('#'))
                runtime = [entry for entry in entries
                           if len(entry) >= 5 and entry[1] in ('/run/zabbix', '/var/run/zabbix')]
                self.assertEqual(len(runtime), 1)
                self.assertEqual(runtime[0][0], 'd')
                self.assertEqual(int(runtime[0][2], 8), 0o755)
                self.assertEqual(runtime[0][3:5], ['zabbix', 'zabbix'])

    def run_schema(self, tables='0', fail='', gzip_fail=False):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / 'psql').write_text('''#!/bin/bash
printf '%s\\n' "$*" >> "$CALLS"
case "$*" in
  *count*) echo "$TABLES"; [ "$FAIL" != count ] ;;
  *dbversion*) [ "$FAIL" != existing ] ;;
  *--single-transaction*) [ "$FAIL" != import ] ;;
  *) exit 99 ;;
esac
''')
            (work / 'gzip').write_text('#!/bin/bash\n[ "$GZIP_FAIL" != yes ] || exit 1\nprintf "CREATE TABLE test(id int);"\n')
            for name in ('psql', 'gzip'):
                (work / name).chmod(0o700)
            calls = work / 'calls'
            env = dict(os.environ, PATH=str(work) + ':' + os.defpath,
                       CALLS=str(calls), TABLES=tables, FAIL=fail,
                       GZIP_FAIL='yes' if gzip_fail else 'no', TMPDIR=str(work))
            result = subprocess.run(['bash', str(ROLE / 'files/import_schema.sh'), '/fake/schema.gz'],
                                    env=env, capture_output=True, text=True)
            self.assertFalse(list(work.glob('tmp.*')), 'temporary schema must be removed')
            return result, calls.read_text()

    def test_empty_database_import_and_repeat(self):
        result, calls = self.run_schema()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('SCHEMA_IMPORTED', result.stdout)
        self.assertIn('--single-transaction -v ON_ERROR_STOP=1', calls)
        result, calls = self.run_schema(tables='200')
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('SCHEMA_IMPORTED', result.stdout)
        self.assertNotIn('--single-transaction', calls)
        self.assertIn('dbversion', calls)

    def test_failures_never_report_success(self):
        for kwargs in ({'fail': 'count'}, {'fail': 'import'}, {'gzip_fail': True},
                       {'tables': '2', 'fail': 'existing'}):
            with self.subTest(**kwargs):
                result, calls = self.run_schema(**kwargs)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('SCHEMA_IMPORTED', result.stdout)
                if kwargs.get('fail') == 'count' or kwargs.get('gzip_fail'):
                    self.assertNotIn('--single-transaction', calls)

    def test_pinned_configuration_and_service_safety(self):
        config = (ROOT / 'ansible/inventories/production/group_vars/zabbix_servers.yml').read_text()
        self.assertIn('1:7.0.31-1+ubuntu24.04', config)
        self.assertIn('zabbix-release_7.0-5%2Bubuntu24.04_all.deb', config)
        self.assertIn('sha256:4f206504c2bc1cff36edf762e2274d0686b0e796b772533c95d04bbe265654de', config)
        tasks = (ROLE / 'tasks/main.yml').read_text()
        self.assertNotIn('zabbix-nginx-conf', tasks)
        self.assertEqual(tasks.count('policy_rc_d: 101'), 2)
        self.assertIn('selection: hold', tasks)
        self.assertIn('no_password_changes:', tasks)
        self.assertIn('become_user: postgres', tasks)
        self.assertIn('path: /etc/nginx/sites-enabled/default\n    state: absent', tasks)
        self.assertLess(tasks.index('Disable the default nginx'), tasks.index('Enable services'))
        nginx = (ROLE / 'templates/nginx.conf.j2').read_text()
        self.assertIn('listen 127.0.0.1:8080;', nginx)
        self.assertIn('allow 192.168.55.23;', nginx)
        self.assertIn('deny all;', nginx)
        self.assertIn('try_files $uri =404;', nginx)
        self.assertIn('fastcgi_pass unix:/run/php/php8.3-fpm.sock;', nginx)
        handlers = (ROLE / 'handlers/main.yml').read_text()
        self.assertIn('php-fpm8.3 -t', handlers)
        self.assertIn('nginx -t', handlers)


if __name__ == '__main__':
    unittest.main()
