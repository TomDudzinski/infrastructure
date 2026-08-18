# Ansible

## Purpose

Ansible manages operating-system and service configuration for infrastructure guests.

Terraform manages the Proxmox resource lifecycle. Ansible begins configuration only after a guest has been created and is reachable through SSH.

## Current status

Ansible is installed on `iza` and manages the initial configuration of `mysql01`.

| Property | Value |
|---|---|
| Execution host | `iza` |
| Ansible Core | `2.20.1` |
| Inventory | `inventories/production/hosts.yml` |
| Managed host | `mysql01` |
| SSH user | `tom` |
| SSH authentication | Dedicated automation key |
| Privilege escalation | Passwordless `sudo` |
| MySQL collection | `ansible.mysql` `5.2.0` |

## Directory structure

```text
ansible/
├── ansible.cfg
├── inventories/
│   └── production/
│       ├── host_vars/
│       │   └── mysql01.yml
│       └── hosts.yml
├── playbooks/
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
    └── qemu_guest_agent/
        └── tasks/
            └── main.yml
