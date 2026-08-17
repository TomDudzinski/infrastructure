# dtcode

## Type

Proxmox VE host.

## Address

`192.168.55.6`

## Role

Smaller virtualization host.

## Platform version

Verified on 2026-08-17:

- Proxmox VE `8.2.2`;
- running kernel `6.8.4-2-pve`.

## Known workloads

- `dns01`
- `home01`
- `forgejo01`
- `npm01`
- `tailscale-router`

## Management

Terraform is currently used to create virtual machines and containers.

Some application provisioning is currently performed using Terraform provisioners.

SSH automation from `iza` currently uses the `root` account and the dedicated `homelab-automation@iza` key. This is a bootstrap configuration; a least-privilege automation identity is the target state.

Target state:

Terraform + Ansible.

See [Automation SSH access](../security/automation-ssh.md).
