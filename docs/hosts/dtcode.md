# dtcode

## Type

Proxmox VE host.

## Address

`192.168.55.6`

## Role

Smaller virtualization host.

## Platform

Previously documented as verified on `2026-08-17`; not rechecked during the local review on `2026-10-04`:

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
| 104 | VM | `bao01` | Running (previously documented) | Current Terraform and Ansible; `192.168.55.24` |
| 105 | VM | `forgejo01` | Running | Tagged `forgejo`, `git`, `terraform` |
| 106 | VM | `npm01` | Running | Tagged `nginx`, `proxy`, `ssl`, `terraform` |
| 107 | VM | `tailscale-router` | Running | Tagged `tailscale`, `terraform`, `vpn` |
| 999 | VM template | `ubuntu-temp` | Stopped | Template relationship with ID 101 requires review |

## Management and recovered history

The physical host is documented only: the current Terraform uses it as a provider target, and the current Ansible inventory does not manage the host itself. Earlier documentation records SSH automation from `iza`; it was not verified in this local review.

Current Terraform includes restricted management of `bao01` (ID `104`), cloned from template `101`. Current Ansible has its inventory entry and OpenBao bootstrap. The host is no longer accurately described as a read-only Terraform environment.

The five existing guests (`dns01`, `home01`, `forgejo01`, `npm01`, `tailscale-router`) have current Terraform definitions and completed state adoption reported by the administrator on `2026-10-04`. They have no Ansible inventory entries or playbooks. Live hardware was previously verified by the administrator; no live checks were repeated here. See the [adoption review](../operations/dtcode-adoption-2026-10-04.md).

Historically, `dns01` was an unprivileged Ubuntu 22.04 LXC on `local-lvm`. The four legacy VMs were full clones of template `999` using cloud-init and `vmbr0`. Their old Terraform also performed imperative service installation over SSH (`remote-exec`/`local-exec`), rather than Ansible roles. This does not establish the present template contents, VM disk sizes or actual service versions.

| Legacy guest | ID | IP | Purpose | Historical persistent data | Details |
|---|---:|---|---|---|---|
| `dns01` | 102 | `192.168.55.10` | Technitium DNS | `/opt/technitium/config` | [dns01](../vms/dns01.md) |
| `home01` | 103 | `192.168.55.20` | Homepage | `/opt/homepage/config` | [home01](../vms/home01.md) |
| `forgejo01` | 105 | `192.168.55.22` | Git service | Named Docker volume `forgejo-data` at `/data` | [forgejo01](../vms/forgejo01.md) |
| `npm01` | 106 | `192.168.55.23` | Reverse proxy / TLS | `/opt/npm/data`, `/opt/npm/letsencrypt`, `/opt/npm/ssl` | [npm01](../vms/npm01.md) |
| `tailscale-router` | 107 | `192.168.55.4` | Subnet router | `/etc/sysctl.d/99-tailscale.conf`; expected node state under `/var/lib/tailscale` (unverified) | [tailscale-router](../vms/tailscale-router.md) |

`wiki01` has status **historical / probably removed**. According to the administrator, it is not running and was probably removed from Proxmox `dtcode`; the administrator also reports that the latest old `terraform.tfstate` no longer contains this VM. These statements were not independently verified in this local review; absence from state alone does not prove removal from Proxmox.

**Historically reused identifiers and addresses:** VM ID `104` on `dtcode`, formerly used by `wiki01`, now belongs to `bao01`. IP `192.168.55.21`, referenced by historical `wiki01` and `test-vm`, now belongs to `mysql01` on `dom`. These are historical reassignments, not active collisions; the identifiers and address are currently allocated and must not be restored from old definitions.

`test-vm` remains **historical**; its current presence cannot be confirmed. No active definitions or recreation plans are added for either historical guest.

State adoption is complete. Applying remaining Terraform differences or adding Ansible management requires a separate review of guest configuration, dependencies, persistent data and backup/restore coverage. Preserve all existing IDs, addresses and data; do not recreate guests from historical source.

See:

- [Infrastructure inventory](../../INVENTORY.md)
- [Automation SSH access](../security/automation-ssh.md)
- [Terraform Proxmox access](../security/terraform-proxmox-access.md)
