# Ansible

## Purpose

Ansible manages operating-system and service configuration for infrastructure hosts and guests.

Terraform manages the Proxmox resource lifecycle. Ansible configures operating systems and services after infrastructure resources are available.

Ansible is executed from `iza`. The `iza` host is also managed locally by Ansible for selected host-level configuration.

## Coverage of adopted dtcode guests — 2026-10-04

Following the [adoption review](../docs/operations/dtcode-adoption-2026-10-04.md), `dns01`, `home01`, `forgejo01`, `npm01` and `tailscale-router` are now listed in the `dtcode_existing` inventory group. This group provides a target for future diagnostics after access is verified; it does not assign service roles. No host_vars or playbooks were added for these guests, and existing playbooks target other hosts by name.

Access to `dns01` at `192.168.55.10` was verified from the trusted execution host `iza`: SSH authentication works as `root` with `/home/tom/.ssh/homelab_automation_ed25519`, and Python 3 is available. Its inventory entry records the verified SSH user and key path. This remains inventory-only onboarding; no host or service configuration was applied.

The other four guests retain IP-only entries. Their SSH user, authorized automation key and execution-host key path, SSH port/options and host-key verification, privilege escalation requirements/method and permissions, and Python availability/path still require verification. The `tom` user and key declared for other guests are not evidence of access to these four hosts. `ansible.cfg` uses `interpreter_python = auto_silent`, which is discovery policy rather than a verified interpreter path, including for `dns01`. Do not attempt diagnostics with implicit access defaults before the required details are confirmed.

Only local/static checks were performed on the inventory change. Current Ansible does not manage these guests' operating systems or Technitium, Homepage, Forgejo, NPM and Tailscale services. Terraform state adoption and inventory entries do not establish Ansible management or runtime health. Historical absence findings in the adoption review describe the review before this inventory addition.

## Current status

Ansible is installed on `iza` and currently manages:

- `mysql01` through SSH;
- `bao01` through SSH;
- selected configuration of `iza` through the local connection.

| Property | Value |
|---|---|
| Execution host | `iza` |
| Ansible Core | `2.20.1` |
| Inventory | `inventories/production/hosts.yml` |
| Managed hosts | `mysql01`, `bao01`, `iza` |
| Remote SSH user | `tom` |
| SSH authentication | Dedicated automation key |
| Local connection | `iza` uses `ansible_connection: local` |
| MySQL collection | `ansible.mysql` `5.2.0` |
| POSIX collection | `ansible.posix` `2.1.0` |

## Managed configuration

### mysql01

The `mysql01` host is configured by:

```text
playbooks/mysql01-bootstrap.yml
```

Its configuration includes the MySQL server and QEMU guest agent roles.

### bao01

The `bao01` host is configured by:

```text
playbooks/bao01-bootstrap.yml
```

### iza

Selected host-level configuration on `iza` is managed by:

```text
playbooks/iza-bootstrap.yml
```

The current managed configuration includes the QNAP NFS automount through the `qnap_mount` role.

The role manages the persistent `/etc/fstab` entry for:

```text
192.168.55.5:/Backup
```

mounted at:

```text
/mnt/qnap-backup
```

using NFS 4.1 and `x-systemd.automount`.

The role intentionally does not enforce ownership or permissions on the mounted directory because, after the NFS filesystem is mounted, those attributes belong to the QNAP export rather than only to the local mount point.

## Local privilege escalation on iza

Ubuntu 26.04 on `iza` provides `sudo-rs` as the default `sudo` implementation.

Ansible Core `2.20.1` did not successfully handle password-based local privilege escalation through the active `sudo-rs` executable during verification.

The classic sudo implementation is also installed and available as:

```text
/usr/bin/sudo.ws
```

The `iza` host variables therefore configure:

```yaml
ansible_become_exe: /usr/bin/sudo.ws
```

This override applies to Ansible privilege escalation for `iza`. It does not replace the system-wide default `sudo` command.

Do not store the sudo password in the repository. Interactive runs requiring privilege escalation should use:

```bash
ansible-playbook playbooks/iza-bootstrap.yml --ask-become-pass
```

## Directory structure

```text
ansible/
├── ansible.cfg
├── inventories/
│   └── production/
│       ├── host_vars/
│       │   ├── bao01.yml
│       │   ├── iza.yml
│       │   └── mysql01.yml
│       └── hosts.yml
├── playbooks/
│   ├── bao01-bootstrap.yml
│   ├── iza-bootstrap.yml
│   └── mysql01-bootstrap.yml
├── requirements.yml
└── roles/
    ├── mysql_server/
    │   ├── handlers/
    │   │   └── main.yml
    │   ├── tasks/
    │   │   └── main.yml
    │   └── templates/
    │       └── homelab.cnf.j2
    ├── qemu_guest_agent/
    │   └── tasks/
    │       └── main.yml
    └── qnap_mount/
        ├── defaults/
        │   └── main.yml
        └── tasks/
            └── main.yml
```

## Collections

Required Ansible collections are defined in:

```text
requirements.yml
```

Install or verify them with:

```bash
ansible-galaxy collection install -r requirements.yml
```

The currently required collections are:

- `ansible.mysql` `5.2.0`;
- `ansible.posix` `2.1.0`.

## Verification

Check inventory:

```bash
ansible-inventory --graph
```

Check the `iza` playbook syntax:

```bash
ansible-playbook playbooks/iza-bootstrap.yml --syntax-check
```

Run the `iza` playbook in check mode:

```bash
ansible-playbook \
  playbooks/iza-bootstrap.yml \
  --check \
  --diff \
  --ask-become-pass
```

A fully converged host should complete with:

```text
changed=0
failed=0
```

## Infrastructure inventory collection (prepared, not runtime verified)

`playbooks/infrastructure-inventory.yml` uses the existing Linux, Docker and
Proxmox collectors. It assigns no service configuration roles. `proxmox_hosts`
contains `dom` (`192.168.55.3`) and `dtcode` (`192.168.55.6`), both using root
and `/home/tom/.ssh/homelab_automation_ed25519`. These access settings are
requested configuration, not evidence of verified connectivity.

See [collection procedure](../docs/infrastructure/README.md#integracja-z-ansible).
Run only on `iza`, never on the development laptop. An explicit `--limit` is
required. From the repository root on `iza`:

```bash
cd ansible
ansible-playbook -i inventories/production/hosts.yml \
  playbooks/infrastructure-inventory.yml --limit 'iza,dom,dtcode' --ask-become-pass
```

Local static commands (no host connections):

```bash
ansible-inventory -i inventories/production/hosts.yml --graph
ansible-playbook playbooks/infrastructure-inventory.yml --syntax-check
ansible-playbook playbooks/infrastructure-inventory.yml --list-hosts --limit 'dom'
```

## Zabbix Agent 2 — kod przygotowany

Grupa `zabbix_agents` obejmuje 14 hostów. Wspólne ustawienia SSH to użytkownik
`tom` i istniejący klucz automatyzacji; `dns01`, `dom`, `dtcode` zachowują `root`.
To aktualizuje wcześniejszy opis wpisów IP-only: ustawienia są teraz jawne,
lecz dostęp do wcześniej niezweryfikowanych hostów nadal wymaga sprawdzenia na `iza`.
Rola i playbook nie zostały wdrożone. Parametry, ograniczenia systemów, TLS, Vault,
testy offline i komendy wdrożenia: [procedura](../docs/monitoring/zabbix-agents.md).
