# Infrastructure Inventory

This document provides a high-level inventory of the HomeLab infrastructure.

Detailed configuration, dependencies, persistent data, backup, and recovery information belong in the corresponding files under `docs/`.

## Verification status

| Status | Meaning |
|---|---|
| Verified | Previously recorded verification; date and source must be checked. Local code inspection confirms definitions only, not deployment or runtime state |
| Documented | Recorded in the project but not confirmed directly during the latest inventory review |
| Planned | Target state that is not implemented yet |

Last documented operational inventory: `2026-08-18`. Historical-source reconciliation: `2026-10-04` (local files only; no live verification).

## Network

| Item | Value | Status |
|---|---|---|
| Primary LAN | `192.168.55.0/24` | Documented |
| Default gateway | `192.168.55.1` | Documented |
| Local DNS domain | `home.lab` | Documented |
| DNS service | Technitium DNS on `dns01` | Documented |
| Remote access | Tailscale subnet router | Documented |

Detailed network configuration is maintained in `docs/network/NETWORK.md`.

## Physical infrastructure

| Host | Type | Address | Operating system | Role | Status |
|---|---|---|---|---|---|
| `dtcode` | Physical server | `192.168.55.6` | Proxmox VE 8.2.2 | Smaller virtualization host | Verified |
| `dom` | Physical server | `192.168.55.3` | Proxmox VE 9.2.2 | Main high-resource virtualization host | Verified |
| `iza` | Physical server | `192.168.55.7` | Ubuntu 26.04 LTS | Local AI and LLM platform | Verified |
| `qnap` | NAS | `192.168.55.5` | QTS 5.1.9.2954 | Central storage and backup target | Documented |

## Proxmox hosts

### dtcode

| Property | Value |
|---|---|
| Address | `192.168.55.6` |
| Proxmox version | `8.2.2` |
| Cluster | Single-node cluster `test` |
| Corosync member address | `192.168.55.150` |
| Role | Smaller virtualization host |
| Storage | `local`, `local-lvm` |
| Network bridge | `vmbr0` |
| Known workloads | VM IDs `101`, `103`-`107`, `999`; LXC ID `102` |
| Current management | Proxmox VE; Terraform and Ansible manage approved new resources including `bao01`; existing workloads remain outside the current Terraform state |
| Target management | Terraform and Ansible |
| Documentation | `docs/hosts/dtcode.md` |
| Verification status | Live inventory verified on `2026-08-17` |

### dom

| Property | Value |
|---|---|
| Address | `192.168.55.3` |
| Proxmox version | `9.2.2` |
| Cluster | Standalone host |
| Role | Main high-resource virtualization host |
| Storage | `local`, `local-lvm` |
| Network bridge | `vmbr0` |
| Known workloads | VM ID `201` (`mysql01`) |
| Current management | Proxmox VE; Terraform for managed resources; Ansible for guest configuration |
| Target management | Terraform and Ansible |
| Documentation | `docs/hosts/dom.md` |
| Verification status | Live inventory verified on `2026-08-18` |

## AI server

### iza

| Property | Value |
|---|---|
| Type | Physical server |
| Address | `192.168.55.7` |
| Operating system | Ubuntu 26.04 LTS (Resolute Raccoon) |
| Kernel | `7.0.0-28-generic` |
| CPU | Intel Core i7-11700K, 8 cores, 16 threads |
| Memory | 60 GiB available to the operating system |
| Swap | 8 GiB |
| System disk | Samsung SSD 980 1 TB NVMe |
| Root filesystem | 100 GiB ext4 on LVM |
| GPU | NVIDIA GeForce GTX 1050 Ti, 4 GiB VRAM |
| NVIDIA driver | `580.173.02` |
| CUDA compatibility | `13.0` |
| Docker Engine | `29.7.1` |
| Docker Compose | `5.3.1` |
| Main data root | `/opt/ai` |
| QNAP mount | `/mnt/qnap-backup` using NFS 4.1 |
| Documentation | `docs/hosts/iza.md` |
| Verification status | Verified on `2026-08-17` |

### iza directory structure

| Path | Purpose |
|---|---|
| `/opt/ai/ansible` | Ansible-related files outside the main repository |
| `/opt/ai/backups` | Local backup repository and backup reports |
| `/opt/ai/cache` | Application and model caches |
| `/opt/ai/data` | Persistent application data |
| `/opt/ai/datasets` | AI and data-analysis datasets |
| `/opt/ai/docker` | Docker-related host files |
| `/opt/ai/docs` | Host-local documentation |
| `/opt/ai/install` | Installation files and notes |
| `/opt/ai/models` | Local model storage, including Ollama models |
| `/opt/ai/notebooks` | Jupyter notebooks |
| `/opt/ai/projects` | Git repositories and development projects |
| `/opt/ai/scripts` | Host-local scripts |

### iza containerized applications

| Application | Container | Image | Published port | Persistent data | Status on 2026-08-17 |
|---|---|---|---:|---|---|
| Ollama | `ollama` | `ollama/ollama:latest` | `11434` | `/opt/ai/models/ollama` | Running |
| Open WebUI | `open-webui` | `ghcr.io/open-webui/open-webui:v0.11.0` | `3000` | `/opt/ai/data/open-webui` | Running and healthy |
| JupyterLab | `jupyter` | `iza-jupyter:latest` | `8888` | `/opt/ai/notebooks`, `/opt/ai/data/jupyter`, `/opt/ai/projects`, `/opt/ai/datasets`, `/opt/ai/cache/jupyter` | Running and healthy |
| code-server | `code-server` | `lscr.io/linuxserver/code-server:latest` | `8443` | `/opt/ai/data/code-server/config`, `/opt/ai/projects`, `/opt/ai/notebooks`, `/opt/ai/datasets` | Running |

## Storage

### QNAP TS-253D

| Property | Value |
|---|---|
| Address | `192.168.55.5` |
| Operating system | QTS 5.1.9.2954 |
| Disks | 2 x 4 TB |
| Role | Central backup and storage server |
| Export | `192.168.55.5:/Backup` |
| Mount point on iza | `/mnt/qnap-backup` |
| Protocol | NFS 4.1 |
| Documentation | `docs/qnap/README.md` |
| Verification status | NFS mount verified from `iza`; remaining NAS configuration requires review |

## Virtual machines and containers

The following machines already exist and must be preserved. Their live Proxmox configuration, dependencies, persistent data, and backup status require separate verification before significant changes.

| ID | Type | Name | Address | Proxmox host | State | Management status | Documentation |
|---:|---|---|---|---|---|---|---|
| 101 | VM template | `ubuntu-2404` | Not applicable | `dtcode` | Stopped template | Existing; unmanaged by current state | Documentation required |
| 102 | LXC | `dns01` | `192.168.55.10` | `dtcode` | Running | Existing legacy; historical Terraform code recovered; no current Terraform/Ansible definition | `docs/vms/dns01.md` |
| 103 | VM | `home01` | `192.168.55.20` | `dtcode` | Running | Existing legacy; historical Terraform code recovered; no current Terraform/Ansible definition | `docs/vms/home01.md` |
| 104 | VM | `bao01` | `192.168.55.24` | `dtcode` | Running | Managed by current Terraform state and Ansible | `docs/vms/bao01.md` |
| 105 | VM | `forgejo01` | `192.168.55.22` | `dtcode` | Running | Existing legacy; historical Terraform code recovered; no current Terraform/Ansible definition | `docs/vms/forgejo01.md` |
| 106 | VM | `npm01` | `192.168.55.23` | `dtcode` | Running | Existing legacy; historical Terraform code recovered; no current Terraform/Ansible definition | `docs/vms/npm01.md` |
| 107 | VM | `tailscale-router` | `192.168.55.4` | `dtcode` | Running | Existing legacy; historical Terraform code recovered; no current Terraform/Ansible definition | `docs/vms/tailscale-router.md` |
| 201 | VM | mysql01 | 192.168.55.21 | dom | Running | Managed by current Terraform state and Ansible | docs/vms/mysql01.md |
| 999 | VM template | `ubuntu-temp` | Not applicable | `dtcode` | Stopped template | Existing; unmanaged by current state | Documentation required |

## Management classification and historical evidence

Classification describes both resource lifecycle and management coverage; these are separate dimensions. **Legacy** means an existing resource retained from earlier infrastructure. **Current Terraform/Ansible** means a definition exists in this repository; it does not alone prove deployment or state membership. **Documented only** means no current management definition. **Historical** means archival evidence, not an active resource entry. **Planned** means a proposed future action without deployment confirmation.

| Resource | Lifecycle / evidence | Current Terraform | Current Ansible | Documentation / planned work |
|---|---|---|---|---|
| `dtcode` | Existing physical host; prior inventory | No host lifecycle definition; provider target only | No current host inventory entry | Documented only; preserve host and legacy guests |
| `dns01` | Existing legacy LXC, ID `102` | No | No | Documented only; verify before any adoption |
| `home01` | Existing legacy VM, ID `103` | No | No | Documented only; verify before any adoption |
| `forgejo01` | Existing legacy VM, ID `105` | No | No | Documented only; verify before any adoption |
| `npm01` | Existing legacy VM, ID `106` | No | No | Documented only; verify before any adoption |
| `tailscale-router` | Existing legacy VM, ID `107` | No | No | Documented only; verify before any adoption |
| `bao01` | Deployment recorded in prior documentation, ID `104` | Definition present; management previously documented | Inventory and bootstrap present | Current managed scope; no new runtime verification |
| `mysql01` | Deployment recorded in prior documentation, ID `201` | Definition present; management previously documented | Inventory and bootstrap present | Current managed scope; no new runtime verification |
| `qdrant01` | VM ID `202`, `192.168.55.25`, `dom`; code evidence only in this review | Definition present | Inventory and bootstrap present | Deployment/state membership unconfirmed; no runtime status asserted |
| `langfuse01` | VM ID `203`, `192.168.55.26`, `dom`; code evidence only in this review | Definition present | Inventory and bootstrap present | Deployment/state membership unconfirmed; no runtime status asserted |
| `grafana01` | VM ID `204`, `192.168.55.27`, `dom`; code evidence only in this review | Definition present | Inventory and bootstrap present | Deployment/state membership unconfirmed; no runtime status asserted |
| `cloudflare01` | VM ID `205`, `192.168.55.28`, `dom`; code evidence only in this review | Definition present | Inventory and bootstrap present | Deployment/state membership unconfirmed; no runtime status asserted |
| `wiki01` | Historical / probably removed; former VM ID `104`, former IP `192.168.55.21` | No | No | Administrator reports not running, probably removed, and absent from latest old state; not independently verified |
| `test-vm` | Historical `vm.tf_old`, VM ID `301`, former IP `192.168.55.21` | No | No | Archive only; current presence unconfirmed; no recreation planned |

Historical sources: `/home/tom/Projekty/infrastructure-old/homelab/terraform/environments/dev/{technitium-dns,homepage,forgejo,npm,tailscale,wiki}.tf` and `vm.tf_old`. The old repository is a read-only knowledge source, not the management repository. State files, credentials and keys were not copied. A historical `terraform` tag is not proof of current management.

`wiki01` has status **historical / probably removed**. According to the administrator, it is not running and was probably removed from Proxmox `dtcode`; the administrator also reports that the latest old `terraform.tfstate` no longer contains this VM. These statements were not independently verified in this local review; absence from state alone does not prove removal from Proxmox.

**Historically reused identifiers and addresses:** VM ID `104` on `dtcode`, formerly used by `wiki01`, now belongs to `bao01`. IP `192.168.55.21`, referenced by historical `wiki01` and `test-vm`, now belongs to `mysql01` on `dom`. These are historical reassignments, not active collisions; the identifiers and address are currently allocated and must not be restored from old definitions.

`test-vm` remains **historical**; its current presence cannot be confirmed. No active definitions or recreation plans are added for either historical guest.

## Backup inventory

| Item | Current state | Status |
|---|---|---|
| Restic backup scripts | Stored under `scripts/` | Verified in repository |
| Restic configuration | Loaded from `config/backup.env`, excluded from Git | Verified in repository |
| Backup schedule | Daily at approximately 03:00 UTC | Verified on `iza` |
| Retention schedule | Weekly, Sunday at approximately 04:00 UTC | Verified on `iza` |
| QNAP mount | `/mnt/qnap-backup` | Verified on `iza` |
| QNAP Restic repository | `/mnt/qnap-backup/AI/iza/restic` | Verified on `2026-08-17` |
| Infrastructure restore test | Successful restore from snapshot `aa5c516e` | Verified on `2026-08-17` |
| MySQL backup | Not configured | Required before production use |
| Backup monitoring | No central alerting documented | Verification required |

## Management inventory

| Area | Current state | Target state |
|---|---|---|
| Infrastructure lifecycle | Current Terraform definitions on `dom` and `dtcode`; five legacy guests on `dtcode` remain outside current management | Terraform for new resources and controlled imports |
| Operating system configuration | Ansible definitions cover `mysql01`, `bao01`, `iza`, `qdrant01`, `langfuse01`, `grafana01`, `cloudflare01`; execution not verified in this review | Extend Ansible coverage to approved guests |
| Containerized applications | Docker Compose | Docker Compose |
| Secrets | OpenBao deployed on `bao01`; migration of existing secrets is in progress | OpenBao as the central secrets-management and PKI platform |
| Backup | Restic with local and QNAP-related infrastructure | Restic and QNAP |
| Documentation | Partial repository documentation | Complete infrastructure documentation |
| Source control | Forgejo with a public GitHub mirror | Forgejo as source of truth with synchronized mirror |

## Inventory gaps

The following information still requires live verification:

- complete hardware inventory for `dtcode` and `dom`
- CPU, memory, disk, network, and startup configuration for each VM and LXC
- relationship between templates `101` and `999`
- physical network devices, switches, and management interfaces
- DHCP configuration and address reservations
- complete DNS zone and reverse proxy inventory
- current persistent data locations for services outside `iza` (historical paths for five legacy guests are now documented)
- backup coverage for every VM, LXC, service, and physical host
- database-aware backup and restore procedure for `mysql01`
- monitoring and alerting for `mysql01` and MySQL
- DNS verification for `mysql01.home.lab`
- controlled comparison and import plan for existing `dtcode` resources
- complete inventory of existing secrets that still require controlled migration into OpenBao
