# dom

## Type

Proxmox VE host.

## Address

`192.168.55.3`

## Role

Main high-resource virtualization server.

## Platform

Verified on `2026-08-17`:

| Property | Value |
|---|---|
| Proxmox VE | `9.2.2` |
| Running kernel | `7.0.2-6-pve` |
| Cluster | Standalone host |
| CPU allocation visible to PVE | 32 logical CPUs |
| Memory visible to PVE | Approximately 189 GiB |
| Storage | `local`, `local-lvm` |
| Network bridge | `vmbr0` |
| VM and LXC inventory | Empty at verification time |

## Intended workloads

- resource-intensive infrastructure services
- OpenBao
- future databases
- future AI supporting services
- workloads that require more CPU or RAM

Intended workloads are plans, not deployed services.

## Management

SSH automation from `iza` currently uses the `root` account and the dedicated `homelab-automation@iza` key. This is a bootstrap configuration; a least-privilege automation identity is the target state.

Terraform provider connectivity from `iza` is operational through a privilege-separated `PVEAuditor` token. The current Terraform configuration is read-only.

Target management:

Terraform + Ansible.

See:

- [Automation SSH access](../security/automation-ssh.md)
- [Terraform Proxmox access](../security/terraform-proxmox-access.md)
