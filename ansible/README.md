# Ansible

## NPM proxy comparison and GET adapter — prepared locally

The `npm_proxy_hosts` role compares `infrastructure_services` with an explicitly
supplied snapshot, reporting `matching`, `missing`, `conflict` and `unmanaged`.
Offline comparison remains the default. A separate opt-in GET adapter and
`playbooks/npm-proxy-hosts-read.yml` are prepared for local execution on iza;
there are no write operations or changes to deployment playbooks. Disabled
catalogue entries remain observational; Zabbix retains its existing owner.
Contract, multi-domain handling, offline tests and the guarded read
adapter: [role documentation](roles/npm_proxy_hosts/README.md).

## Central service catalogue — stage 1 (offline only)

`inventories/production/group_vars/all/services.yml` declares the passive
`infrastructure_services` mapping. No role or playbook consumes it to configure
DNS, NPM or services. All eleven entries start with `npm_enabled: false`.
Grafana is excluded. Zabbix remains owned by the unchanged `zabbix_local_access`
role; the validator rejects enabling its catalogue NPM entry. Disabling an entry
here does not disable existing proxy routes or that independent role.

Fields: `name`, inventory `host`, nullable `domain`, upstream `ip`, host `port`,
nullable upstream `protocol` (`http`/`https`), `npm_enabled`, and repository `source`.
Ports refer to web interfaces (NPM 81, Technitium 5380), not DNS or proxy ingress.
Addresses come from inventory/host documentation; endpoint sources are recorded
per entry. Historical configuration and defaults are evidence, not runtime checks.

Unknown domains remain `null` for Homepage, NPM, Technitium, Open WebUI,
VS Code and Jupyter. Homepage's historical allowed names do not establish its
canonical domain. Upstream protocols remain `null` for Homepage, Open WebUI,
VS Code and Jupyter: published ports alone do not prove HTTP/TLS. Jupyter's
8888 is the Compose default; the effective `JUPYTER_PORT` remains unverified.
Zabbix's endpoint is prepared configuration, not evidence of deployment.

The file uses JSON syntax, a valid YAML subset supported by Ansible, so local
validation requires only Python's standard library and no package installation.
Keep this syntax when editing. From the repository root:

```bash
python3 scripts/validate_services.py
python3 -m unittest discover -s tests -p 'test_services_catalogue.py' -v
```

Validation checks structure, duplicate keys, domain uniqueness (case/trailing-dot
insensitive), IP literals, integer ports 1–65535, upstream protocols and boolean
NPM flags, and optional boolean `websocket`. Existing entries without `websocket`
remain valid. Unknown endpoint fields are allowed only for disabled entries;
activation requires complete data and a separately reviewed integration change.
These checks perform no network access or infrastructure execution.

### Proxmox VE panels — user-supplied correction (2026-10-10)

The catalogue records `dom` at `192.168.55.3:8006` (`https`,
`pve-dom.home.lab`) and `dtcode` at `192.168.55.6:8006` (`https`,
`pve-dtcode.home.lab`). Both have `npm_enabled: false` and `websocket: true`.
The administrator reports direct SSH confirmation of these names and addresses.
This supersedes the earlier incorrect `tdcode` entry and reversed IP mapping;
no `tdcode` panel remains in the catalogue.

The catalogue now agrees with `production/hosts.yml`. Inventory, Terraform,
Zabbix and the other service entries were not changed. Validation and tests
were performed offline only; Codex made no infrastructure connections and
applied no proxy configuration.

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
