# dom

## Type

Proxmox VE host.

## Address

`192.168.55.3`

## Role

Main high-resource virtualization server.

## Platform version

Verified on 2026-08-17:

- Proxmox VE `9.2.2`;
- running kernel `7.0.2-6-pve`.

## Intended workloads

- resource-intensive infrastructure services
- OpenBao
- future databases
- future AI supporting services
- workloads that require more CPU or RAM

## Management

SSH automation from `iza` currently uses the `root` account and the dedicated `homelab-automation@iza` key. This is a bootstrap configuration; a least-privilege automation identity is the target state.

Target state:

Terraform + Ansible.

See [Automation SSH access](../security/automation-ssh.md).
