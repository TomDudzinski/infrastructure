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
| `dtcode` | Physical server | `192.168.55.6` | Proxmox VE | Smaller virtualization host | Documented |
| `dom` | Physical server | `192.168.55.3` | Proxmox VE | Main high-resource virtualization host | Documented |
| `iza` | Physical server | `192.168.55.7` | Ubuntu 26.04 LTS | Local AI and LLM platform | Verified |
| `qnap` | NAS | `192.168.55.5` | QTS 5.1.9.2954 | Central storage and backup target | Documented |

## Proxmox hosts

### dtcode

| Property | Value |
|---|---|
| Address | `192.168.55.6` |
| Role | Smaller virtualization host |
| Known workloads | `dns01`, `home01`, `forgejo01`, `npm01`, `tailscale-router` |
| Current management | Proxmox VE and existing Terraform configuration |
| Target management | Terraform and Ansible |
| Documentation | `docs/hosts/dtcode.md` |
| Verification status | Documented; live inventory required |

### dom

| Property | Value |
|---|---|
| Address | `192.168.55.3` |
| Role | Main high-resource virtualization host |
| Known workloads | Inventory required |
| Current management | Proxmox VE; detailed state requires verification |
| Target management | Terraform and Ansible |
| Documentation | `docs/hosts/dom.md` |
| Verification status | Documented; live inventory required |

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

## Virtual machines

The following machines already exist and must be preserved. Their live Proxmox configuration, dependencies, persistent data, and backup status require separate verification before significant changes.

| VM ID | Name | Address | Proxmox host | Purpose | Management status | Documentation |
|---:|---|---|---|---|---|---|
| 102 | `dns01` | `192.168.55.10` | `dtcode` | Technitium DNS | Existing; Terraform state requires verification | `docs/vms/dns01.md` |
| 103 | `home01` | `192.168.55.20` | `dtcode` | Homepage dashboard | Existing Terraform resource documented | `docs/vms/home01.md` |
| 105 | `forgejo01` | `192.168.55.22` | `dtcode` | Primary Forgejo Git server | Existing; Terraform state requires verification | `docs/vms/forgejo01.md` |
| 106 | `npm01` | `192.168.55.23` | `dtcode` | Nginx Proxy Manager | Existing Terraform resource documented | `docs/vms/npm01.md` |
| 107 | `tailscale-router` | `192.168.55.4` | `dtcode` | Tailscale VPN and subnet router | Existing Terraform resource documented | `docs/vms/tailscale-router.md` |

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
| Infrastructure lifecycle | Existing Terraform resources and manual infrastructure | Terraform |
| Operating system configuration | Manual configuration and scripts | Ansible |
| Containerized applications | Docker Compose | Docker Compose |
| Secrets | Existing local mechanisms | OpenBao |
| Backup | Restic with local and QNAP-related infrastructure | Restic and QNAP |
| Documentation | Partial repository documentation | Complete infrastructure documentation |
| Source control | Forgejo with a public GitHub mirror | Forgejo as source of truth with synchronized mirror |

## Inventory gaps

The following information still requires live verification:

- complete hardware inventory for `dtcode` and `dom`
- Proxmox VE versions and storage configuration
- all virtual machines and LXC containers on both Proxmox hosts
- CPU, memory, disk, network, and startup configuration for each VM and LXC
- workloads currently running on `dom`
- physical network devices, switches, and management interfaces
- DHCP configuration and address reservations
- complete DNS zone and reverse proxy inventory
- persistent data locations for services outside `iza`
- backup coverage for every VM, LXC, service, and physical host
- successful restore-test dates and results
- actual Terraform state compared with existing Proxmox resources
- current secret locations before migration to OpenBao
