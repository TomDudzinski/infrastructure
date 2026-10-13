"""Offline regressions; optional YAML/Jinja checks require local dependencies."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / 'ansible/roles/zabbix_agent'
EXPECTED = {'dom', 'dtcode', 'iza', 'dns01', 'home01', 'forgejo01', 'npm01',
            'tailscale-router', 'mysql01', 'bao01', 'qdrant01', 'langfuse01',
            'grafana01', 'cloudflare01', 'webui01', 'zabbix01'}


class ZabbixOfflineTests(unittest.TestCase):
    def test_inventory_membership_and_access(self):
        text = (ROOT / 'ansible/inventories/production/hosts.yml').read_text()
        members = set(re.findall(r'^        ([\w-]+):', text.split('    zabbix_agents:\n')[1], re.M))
        self.assertEqual(members, EXPECTED)
        self.assertEqual(text.count('ansible_ssh_private_key_file:'), 1)
        self.assertIn('    ansible_user: tom', text)
        self.assertIn('          ansible_user: root', text)
        self.assertIn('        ansible_user: root', text)
        self.assertIn('ansible_connection: local', text)

    def test_distribution_versions_and_repository_url(self):
        text = (ROOT / 'ansible/inventories/production/group_vars/zabbix_agents.yml').read_text()
        mapping = text.split('zabbix_agent_package_versions:\n')[1]
        versions, distribution = {}, None
        for line in mapping.splitlines():
            if re.fullmatch(r'  (\w+):', line):
                distribution = line.strip()[:-1]
            elif match := re.fullmatch(r'    "([\d.]+)": "([^"]+)"', line):
                versions[(distribution, match[1])] = match[2]
        self.assertEqual(set(versions), {('Debian', '12'), ('Debian', '13'), ('Ubuntu', '22.04'), ('Ubuntu', '24.04'), ('Ubuntu', '26.04')})
        for (distribution, release), version in versions.items():
            # Pinned 7.0 build whose suffix matches the distribution release.
            self.assertRegex(version, r'^1:7\.0\.\d+-\d+\+' + re.escape(distribution.lower() + release) + '$')
        tasks = (ROLE / 'tasks/main.yml').read_text()
        self.assertIn("'https://repo.zabbix.com/zabbix/' + zabbix_agent_release + '/' + (ansible_distribution | lower)", tasks)
        self.assertNotIn('/release/', tasks)

    def test_guard_precedes_remote_facts(self):
        text = (ROOT / 'ansible/playbooks/zabbix-agents.yml').read_text()
        self.assertIn('gather_facts: false', text)
        self.assertLess(text.index("hostname -s"), text.index('ansible.builtin.setup:'))
        self.assertIn('ansible_limit', text)
        self.assertIn('hosts: zabbix_agents', text)

    def test_secrets_and_change_handlers(self):
        text = (ROLE / 'tasks/main.yml').read_text()
        psk = text.split('- name: Write private PSK file')[1].split('- name: Manage Agent')[0]
        self.assertIn('no_log: true', psk)
        self.assertIn('diff: false', psk)
        self.assertIn("mode: '0640'", psk)
        self.assertEqual(text.count('not ansible_check_mode'), 3)
        self.assertNotIn('latest\n', text)
        self.assertNotIn('vault.yml', text)
        self.assertIn('notify: Restart Zabbix Agent 2', text)

    def test_yaml_and_tls_templates(self):
        try:
            import yaml
            from jinja2 import Environment, StrictUndefined
        except ImportError:
            self.skipTest('Local PyYAML/Jinja2 unavailable; no dependencies installed automatically')
        for path in list(ROLE.rglob('*.yml')) + [ROOT / 'ansible/playbooks/zabbix-agents.yml', ROOT / 'ansible/inventories/production/hosts.yml']:
            yaml.safe_load(path.read_text())
        defaults = yaml.safe_load((ROLE / 'defaults/main.yml').read_text())
        template = Environment(undefined=StrictUndefined).from_string((ROLE / 'templates/zabbix_agent2.conf.j2').read_text())
        defaults.update(zabbix_agent_server='192.0.2.10', zabbix_agent_server_active='192.0.2.10:10051', zabbix_agent_hostname='test-host', zabbix_agent_tls_psk_identity='test-host')
        for mode in ['unencrypted', 'psk', 'cert']:
            defaults.update(zabbix_agent_tls_connect=mode, zabbix_agent_tls_accept=mode)
            result = template.render(defaults)
            self.assertIn('ServerActive=192.0.2.10:10051', result)
            self.assertEqual('TLSPSKFile=' in result, mode == 'psk')
            self.assertEqual('TLSKeyFile=' in result, mode == 'cert')


if __name__ == '__main__':
    unittest.main()
