"""Offline checks for webui01; nothing here contacts infrastructure."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / 'ansible/roles/open_webui'


class OpenWebUIOfflineTests(unittest.TestCase):
    def test_terraform_vm_is_gated_and_sized(self):
        text = (ROOT / 'terraform/dom_webui01.tf').read_text()
        self.assertIn('count    = var.webui01_enabled ? 1 : 0', text)
        self.assertIn('vm_id     = var.webui01_vmid', text)
        self.assertIn('node_name = "dom"', text)
        self.assertRegex(text, r'cores = 4\n')
        self.assertIn('dedicated = 8192', text)
        self.assertRegex(text, r'size\s+= 40\n')
        self.assertIn('address = "192.168.55.30/24"', text)
        self.assertIn('protection = true', text)
        self.assertRegex(text, r'variable "webui01_enabled" \{[^}]*default\s+= false', )

    def test_address_and_vmid_are_not_reused(self):
        others = [p for p in (ROOT / 'terraform').glob('*.tf') if p.name != 'dom_webui01.tf']
        for path in others:
            self.assertNotIn('192.168.55.30/', path.read_text(), path.name)
        inventory = (ROOT / 'ansible/inventories/production/hosts.yml').read_text()
        self.assertEqual(inventory.count('192.168.55.30'), 1)
        self.assertRegex(inventory, r'webui_servers:\n      hosts:\n        webui01:\n          ansible_host: 192\.168\.55\.30\n')

    def test_only_open_webui_is_published(self):
        compose = (ROLE / 'templates/compose.yml.j2').read_text()
        ports = re.findall(r'^      - "(.+)"$', compose.split('ports:')[1].split('env_file:')[0], re.M)
        self.assertEqual(ports, ['{{ open_webui_port }}:8080'])
        self.assertIn('WEBUI_AUTH: "true"', compose)
        self.assertIn('ENABLE_SIGNUP: "false"', compose)
        self.assertIn('ENABLE_FORWARD_USER_INFO_HEADERS: "true"', compose)
        self.assertNotIn('vault_', compose)
        self.assertIn('DEFAULT_LOCALE: "{{ open_webui_default_locale }}"', compose)
        self.assertIn('open_webui_default_locale: pl-PL', (ROLE / 'defaults/main.yml').read_text())

    def test_secret_stays_in_private_env_file(self):
        tasks = (ROLE / 'tasks/main.yml').read_text()
        env_task = tasks.split('- name: Deploy Open WebUI environment')[1].split('- name:')[0]
        self.assertIn('mode: "0600"', env_task)
        self.assertIn('no_log: true', env_task)
        self.assertIn('vault_open_webui_secret_key | length >= 32', tasks)
        self.assertEqual((ROLE / 'templates/.env.j2').read_text(),
                         'WEBUI_SECRET_KEY={{ vault_open_webui_secret_key }}\n')

    def test_playbook_reuses_existing_roles(self):
        text = (ROOT / 'ansible/playbooks/webui01-bootstrap.yml').read_text()
        self.assertEqual(re.findall(r'- role: (\w+)', text), ['qemu_guest_agent', 'docker_host', 'open_webui'])
        self.assertIn("hostname -s') == 'iza'", text)


if __name__ == '__main__':
    unittest.main()
