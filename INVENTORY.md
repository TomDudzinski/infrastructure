# Infrastructure Inventory

This document provides a high-level inventory of the HomeLab infrastructure.

Detailed configuration, dependencies, persistent data, backup, and recovery information belong in the corresponding files under `docs/`.

## Verification status

| Status | Meaning |
|---|---|
| Verified | Confirmed directly on the system or in the current repository configuration |
| Documented | Recorded in the project but not confirmed directly during the latest inventory review |
| Planned | Target state that is not implemented yet |

Inventory review date: `2026-08-17`

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
| Known workloads | VM IDs `101`, `103`, `105`-`107`, `999`; LXC ID `102` |
| Current management | Proxmox VE; previous Terraform state and code were not found |
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
| Known workloads | None at the time of verification |
| Current management | Proxmox VE; read-only Terraform provider connectivity established |
| Target management | Terraform and Ansible |
| Documentation | `docs/hosts/dom.md` |
| Verification status | Live inventory verified on `2026-08-17` |

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
| 102 | LXC | `dns01` | `192.168.55.10` | `dtcode` | Running | Tagged `terraform`; previous state not found | `docs/vms/dns01.md` |
| 103 | VM | `home01` | `192.168.55.20` | `dtcode` | Running | Tagged `terraform`; previous state not found | `docs/vms/home01.md` |
| 105 | VM | `forgejo01` | `192.168.55.22` | `dtcode` | Running | Tagged `terraform`; previous state not found | `docs/vms/forgejo01.md` |
| 106 | VM | `npm01` | `192.168.55.23` | `dtcode` | Running | Tagged `terraform`; previous state not found | `docs/vms/npm01.md` |
| 107 | VM | `tailscale-router` | `192.168.55.4` | `dtcode` | Running | Tagged `terraform`; previous state not found | `docs/vms/tailscale-router.md` |
| 999 | VM template | `ubuntu-temp` | Not applicable | `dtcode` | Stopped template | Existing; unmanaged by current state | Documentation required |

## Backup inventory

| Item | Current state | Status |
|---|---|---|
| Restic backup scripts | Stored under `scripts/` | Verified in repository |
| Restic configuration | Loaded from `config/backup.env`, excluded from Git | Verified in repository |
| Backup schedule | Daily at approximately 03:00 UTC | Verified on `iza` |
| Retention schedule | Weekly, Sunday at approximately 04:00 UTC | Verified on `iza` |
| QNAP mount | `/mnt/qnap-backup` | Verified on `iza` |
| Restore test | No current result recorded | Verification required |
| Backup monitoring | No central alerting documented | Verification required |

## Management inventory

| Area | Current state | Target state |
|---|---|---|
| Infrastructure lifecycle | Existing resources; read-only Terraform connectivity to both Proxmox environments | Terraform after controlled inventory and import |
| Operating system configuration | Manual configuration and scripts | Ansible |
| Containerized applications | Docker Compose | Docker Compose |
| Secrets | Existing local mechanisms | OpenBao |
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
- persistent data locations for services outside `iza`
- backup coverage for every VM, LXC, service, and physical host
- successful restore-test dates and results
- actual Terraform state compared with existing Proxmox resources
- current secret locations before migration to OpenBao
