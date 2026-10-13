"""Offline checks for n8n01; nothing here contacts infrastructure."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / 'ansible/roles/n8n'


class N8nOfflineTests(unittest.TestCase):
    def test_terraform_vm_is_gated_and_sized(self):
        text = (ROOT / 'terraform/dom_n8n01.tf').read_text()
        self.assertIn('count    = var.n8n01_enabled ? 1 : 0', text)
        self.assertIn('vm_id     = var.n8n01_vmid', text)
        self.assertIn('node_name = "dom"', text)
        self.assertRegex(text, r'cores = 2\n')
        self.assertIn('dedicated = 4096', text)
        self.assertRegex(text, r'size\s+= 32\n')
        self.assertIn('address = "192.168.55.31/24"', text)
        self.assertIn('protection = true', text)
        self.assertRegex(text, r'variable "n8n01_enabled" \{[^}]*default\s+= false')

    def test_address_is_not_reused(self):
        others = [p for p in (ROOT / 'terraform').glob('*.tf') if p.name != 'dom_n8n01.tf']
        for path in others:
            self.assertNotIn('192.168.55.31/', path.read_text(), path.name)
        inventory = (ROOT / 'ansible/inventories/production/hosts.yml').read_text()
        self.assertEqual(inventory.count('192.168.55.31'), 1)
        self.assertRegex(inventory, r'automation_servers:\n      hosts:\n        n8n01:\n          ansible_host: 192\.168\.55\.31\n')

    def test_only_n8n_is_published_and_images_are_pinned(self):
        compose = (ROLE / 'templates/compose.yml.j2').read_text()
        self.assertEqual(re.findall(r'^\s+- "(.+:5678)"$', compose, re.M), ['{{ n8n_port }}:5678'])
        self.assertEqual(len(re.findall(r'^\s+ports:$', compose, re.M)), 1)
        self.assertLess(compose.index('  n8n:\n'), compose.index('    ports:\n'))
        self.assertIn('N8N_WEBHOOK_URL: "{{ n8n_webhook_url }}"', compose)
        self.assertNotIn(' WEBHOOK_URL:', compose)
        self.assertIn('N8N_EDITOR_BASE_URL: "{{ n8n_editor_url }}"', compose)
        self.assertNotIn('vault_', compose)
        self.assertEqual(compose.count('restart: unless-stopped'), 2)
        defaults = (ROLE / 'defaults/main.yml').read_text()
        for image in re.findall(r'^n8n_(?:postgres_)?image: (\S+)$', defaults, re.M):
            self.assertRegex(image, r':\d+\.\d+(\.\d+)?$')
        self.assertIn('n8n_timezone: Europe/Warsaw', defaults)

    def test_urls_are_separated(self):
        host_vars = (ROOT / 'ansible/inventories/production/host_vars/n8n01.yml').read_text()
        self.assertIn('n8n_editor_url: https://n8n.tdcode.pl/', host_vars)
        self.assertIn('n8n_webhook_url: https://webhookn8n.tdcode.pl/', host_vars)

    def test_oauth_callback_stays_authenticated(self):
        # Redirect URI = N8N_EDITOR_BASE_URL + /rest/oauth2-credential/callback (n8n 2.43.4).
        compose = (ROLE / 'templates/compose.yml.j2').read_text()
        self.assertIn('N8N_SKIP_AUTH_ON_OAUTH_CALLBACK: "false"', compose)
        self.assertIn('N8N_OAUTH_BROWSER_BINDING: "true"', compose)
        self.assertIn('N8N_SECURE_COOKIE: "true"', compose)

    def test_docs_publish_only_webhook_path(self):
        doc = (ROOT / 'docs/vms/n8n01.md').read_text()
        self.assertIn('path: ^/webhook/', doc)
        self.assertNotRegex(doc, r'hostname: authn8n')
        self.assertNotIn('hooks.tdcode.pl', doc.replace('webhookn8n.tdcode.pl', ''))

    def test_secrets_stay_in_private_env_files(self):
        tasks = (ROLE / 'tasks/main.yml').read_text()
        env_task = tasks.split('- name: Deploy n8n secret environment files')[1].split('- name:')[0]
        self.assertIn('mode: "0600"', env_task)
        self.assertIn('no_log: true', env_task)
        self.assertEqual((ROLE / 'templates/n8n.env.j2').read_text(),
                         'DB_POSTGRESDB_PASSWORD={{ vault_n8n_postgres_password }}\n'
                         'N8N_ENCRYPTION_KEY={{ vault_n8n_encryption_key }}\n')
        self.assertEqual((ROLE / 'templates/postgres.env.j2').read_text(),
                         'POSTGRES_PASSWORD={{ vault_n8n_postgres_password }}\n')

    def test_playbook_reuses_existing_roles(self):
        text = (ROOT / 'ansible/playbooks/n8n01-bootstrap.yml').read_text()
        self.assertEqual(re.findall(r'- role: (\w+)', text), ['qemu_guest_agent', 'docker_host', 'n8n'])
        self.assertIn("hostname -s') == 'iza'", text)


if __name__ == '__main__':
    unittest.main()
