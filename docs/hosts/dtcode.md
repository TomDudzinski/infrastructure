# dtcode

## Type

Proxmox VE host.

## Address

`192.168.55.6`

## Role

Smaller virtualization host.

## Platform

Verified on `2026-08-17`:

| Property | Value |
|---|---|
| Proxmox VE | `8.2.2` |
| Running kernel | `6.8.4-2-pve` |
| Cluster | `test`, single node, quorate |
| Corosync member address | `192.168.55.150` |
| CPU allocation visible to PVE | 4 logical CPUs |
| Memory visible to PVE | Approximately 16 GiB |
| Storage | `local`, `local-lvm` |
| Network bridge | `vmbr0` |

## Guest inventory

| ID | Type | Name | State | Notes |
|---:|---|---|---|---|
| 101 | VM template | `ubuntu-2404` | Stopped | Template |
| 102 | LXC | `dns01` | Running | Tagged `dns`, `technitium`, `terraform` |
| 103 | VM | `home01` | Running | Tagged `dashboard`, `homepage`, `terraform` |
| 104 | VM | `wiki01` | Stopped | Purpose and disposition require review |
| 105 | VM | `forgejo01` | Running | Tagged `forgejo`, `git`, `terraform` |
| 106 | VM | `npm01` | Running | Tagged `nginx`, `proxy`, `ssl`, `terraform` |
| 107 | VM | `tailscale-router` | Running | Tagged `tailscale`, `terraform`, `vpn` |
| 201 | VM | `ubuntu-test` | Stopped | Purpose and disposition require review |
| 202 | VM | `tailscale-router` | Stopped | Possible obsolete or test instance; review required |
| 999 | VM template | `ubuntu-temp` | Stopped | Template relationship with ID 101 requires review |

## Management

SSH automation from `iza` currently uses the `root` account and the dedicated `homelab-automation@iza` key. This is a bootstrap configuration; a least-privilege automation identity is the target state.

Terraform provider connectivity from `iza` is operational through a privilege-separated `PVEAuditor` token. The current Terraform configuration is read-only.

Several guests have a `terraform` tag, but no previous Terraform code or state was found during the inventory. These resources must not be recreated or imported without reconstructing their full configuration and dependencies.

Target management:

Terraform + Ansible.

See:

- [Automation SSH access](../security/automation-ssh.md)
- [Terraform Proxmox access](../security/terraform-proxmox-access.md)
