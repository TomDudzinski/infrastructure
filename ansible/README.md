# Ansible

## Purpose

Ansible manages operating-system and service configuration for infrastructure hosts and guests.

Terraform manages the Proxmox resource lifecycle. Ansible configures operating systems and services after infrastructure resources are available.

Ansible is executed from `iza`. The `iza` host is also managed locally by Ansible for selected host-level configuration.

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
