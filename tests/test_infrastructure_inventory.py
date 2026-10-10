import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('inventory', ROOT / 'scripts/infrastructure_inventory.py')
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.data = inventory.read(ROOT / 'tests/fixtures/infrastructure/linux.json')

    def test_baseline_is_static_not_confirmed(self):
        data = inventory.read(ROOT / 'docs/infrastructure/data/baseline-2026-10-10.json')
        self.assertEqual(len(data['records']), 19)
        self.assertTrue(all(row['status'] == 'unverified' for row in data['records']))

    def test_report_history_and_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory.report(self.data, None, directory)
            before = {path.name: path.read_bytes() for path in Path(directory).glob('*.md')}
            inventory.report(self.data, None, directory)
            self.assertEqual(before, {path.name: path.read_bytes() for path in Path(directory).glob('*.md')})
            self.assertEqual(len(list((Path(directory) / 'history').glob('*.json'))), 1)
            self.assertIn('confirmed', (Path(directory) / 'INVENTORY.md').read_text())

    def test_changes_and_missing_are_not_deletion(self):
        new = copy.deepcopy(self.data)
        new['records'][0]['cores'] = 16
        new['records'][0]['status'] = 'planned'
        new['records'].append(dict(id='host/dom', kind='host', name='dom', host='dom', source='linux', status='unverified'))
        changes = inventory.compare(new, self.data)
        self.assertIn('Added observation: host/dom', changes)
        self.assertIn('Changed host/iza: cores, status', changes)
        self.assertIn('removal unverified', inventory.compare(self.data, new)[0])

    def test_observation_time_only_is_not_drift(self):
        new = copy.deepcopy(self.data)
        new['records'][0]['observed_at'] = '2026-10-10T09:00:00+00:00'
        new['collected_at'] = '2026-10-10T09:00:00+00:00'
        self.assertEqual(inventory.compare(new, self.data), [])

    def test_reject_secrets_and_markdown_injection(self):
        for key, value in [('environment', {'PASSWORD': 'do-not-persist'}),
                           ('name', 'password-do-not-persist'), ('image', 'registry:credential@host'),
                           ('name', '<script>'), ('ports', '80|injected')]:
            with self.subTest(key=key, value=value):
                new = copy.deepcopy(self.data)
                new['records'][0][key] = value
                with self.assertRaises(ValueError):
                    inventory.validate(new)

    def test_schema_and_observation_requirements(self):
        for mutate in [lambda d: d.update(schema_version=2),
                       lambda d: d['records'].append(d['records'][0]),
                       lambda d: d['records'][0].pop('observed_at'),
                       lambda d: d['records'][0].update(memory_bytes=-1),
                       lambda d: d['records'][0].update(address='not-an-ip'),
                       lambda d: d.update(collected_at='2026-10-10T00:00:00')]:
            new = copy.deepcopy(self.data)
            mutate(new)
            with self.assertRaises(ValueError):
                inventory.validate(new)

    def test_new_history_and_collision_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory.report(self.data, None, directory)
            new = copy.deepcopy(self.data)
            new['collected_at'] = '2026-10-11T10:00:00+02:00'
            new['records'][0]['cores'] = 16
            inventory.report(new, self.data, directory)
            self.assertEqual(len(list((Path(directory) / 'history').glob('*.json'))), 2)
            new['records'][0]['cores'] = 32
            with self.assertRaises(ValueError):
                inventory.report(new, self.data, directory)
            with self.assertRaises(ValueError):
                inventory.report(self.data, self.data, directory)

    def test_docker_allowlist_and_local_socket(self):
        raw = dict(Names='web', Image='nginx:1.27', State='running',
                   Command='password=do-not-persist', Labels='token=do-not-persist')
        with patch.object(inventory, 'run', return_value=json.dumps(raw)) as runner, patch.object(inventory.socket, 'gethostname', return_value='iza'):
            data = inventory.collect('docker')
        self.assertIn('unix:///var/run/docker.sock', runner.call_args.args[0])
        self.assertNotIn('do-not-persist', json.dumps(data))
        self.assertEqual(data['coverage']['iza/docker'], 'complete')

    def test_unavailable_collection_does_not_leak_stderr(self):
        failure = subprocess.CalledProcessError(1, ['docker'], stderr='password=do-not-persist')
        with patch.object(inventory, 'run', side_effect=failure), patch.object(inventory.socket, 'gethostname', return_value='iza'):
            data = inventory.collect('docker')
        self.assertEqual(data['records'], [])
        self.assertEqual(data['coverage']['iza/docker'], 'unavailable')
        self.assertNotIn('do-not-persist', json.dumps(data))

    def test_proxmox_identity_and_projection(self):
        raw = [dict(type='qemu', node='dom', vmid=201, name='mysql01', status='running', maxcpu=2,
                    maxmem=4294967296, maxdisk=68719476736, password='do-not-persist'),
               dict(type='lxc', node='dtcode', vmid=102, name='dns01', status='stopped')]
        with patch.object(inventory, 'run', return_value=json.dumps(raw)), patch.object(inventory.socket, 'gethostname', return_value='dom'):
            data = inventory.collect('proxmox')
        self.assertEqual(data['records'][0]['id'], 'guest/dom/201')
        self.assertEqual(data['records'][1]['kind'], 'lxc')
        self.assertNotIn('do-not-persist', json.dumps(data))

    def test_proxmox_node_scopes_merge_without_cluster_duplicates(self):
        raw = [dict(type='qemu', node='dom', vmid=201, name='mysql01', status='running'),
               dict(type='lxc', node='dtcode', vmid=102, name='dns01', status='running')]
        snapshots = []
        for node in ('dom', 'dtcode'):
            with patch.object(inventory, 'run', return_value=json.dumps(raw)), \
                    patch.object(inventory.socket, 'gethostname', return_value=node):
                snapshots.append(inventory.collect('proxmox', node=node))
        merged = dict(schema_version=1, collected_at=snapshots[-1]['collected_at'],
                      coverage={key: value for snap in snapshots for key, value in snap['coverage'].items()},
                      records=[row for snap in snapshots for row in snap['records']])
        inventory.validate(merged)
        self.assertEqual([row['id'] for row in merged['records']], ['guest/dom/201', 'guest/dtcode/102'])
        with tempfile.TemporaryDirectory() as directory:
            inventory.report(merged, None, directory)
            inventory.report(snapshots[0], None, str(Path(directory) / 'partial'))
            self.assertNotIn('guest/dtcode/102', (Path(directory) / 'partial/INVENTORY.md').read_text())

    def test_linux_collection_and_partial_network_failure(self):
        interfaces = [{'ifname': 'eth0', 'addr_info': [
            {'family': 'inet', 'local': '192.168.55.7', 'prefixlen': 24},
            {'family': 'inet6', 'local': 'fe80::1', 'prefixlen': 64}]}]
        with patch.object(inventory.Path, 'read_text', return_value='MemTotal: 1024 kB\n'), \
                patch.object(inventory.socket, 'gethostname', return_value='iza'), \
                patch.object(inventory.os, 'cpu_count', return_value=8), \
                patch.object(inventory, 'run', return_value=json.dumps(interfaces)) as runner:
            data = inventory.collect('linux')
            self.assertEqual(len(data['records']), 3)
            self.assertEqual(data['records'][0]['memory_bytes'], 1048576)
            self.assertEqual(data['records'][2]['address'], 'fe80::1/64')
            runner.side_effect = FileNotFoundError('ip unavailable')
            partial = inventory.collect('linux')
            self.assertEqual(partial['coverage']['iza/network'], 'unavailable')
            self.assertEqual(len(partial['records']), 1)

    def test_cli_offline_merge_and_duplicate_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            command = ['python3', '-B', str(ROOT / 'scripts/infrastructure_inventory.py'), 'report',
                       str(ROOT / 'tests/fixtures/infrastructure/linux.json'), '--output', directory]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            command.insert(5, str(ROOT / 'tests/fixtures/infrastructure/linux.json'))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)

    def test_json_is_private_and_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.json'
            inventory.write_json(path, self.data)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                inventory.write_json(path, self.data)


if __name__ == '__main__':
    unittest.main()
