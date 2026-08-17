# iza

## Overview

`iza` is a dedicated physical server for the local AI and LLM platform.

The server runs containerized AI applications, development tools, persistent application data, and the Restic backup workflow.

| Property | Value |
|---|---|
| Hostname | `iza` |
| Type | Physical server |
| Role | Local AI and LLM platform |
| LAN address | `192.168.55.7` |
| Main data root | `/opt/ai` |
| Repository path | `/opt/ai/projects/infrastructure` |
| Verification date | `2026-08-17` |

## Operating system

| Property | Value |
|---|---|
| Distribution | Ubuntu Server |
| Version | Ubuntu 26.04 LTS |
| Codename | Resolute Raccoon |
| Kernel | `7.0.0-28-generic` |
| Architecture | `x86_64` |

## Hardware

### Processor and memory

| Component | Value |
|---|---|
| CPU | 11th Gen Intel Core i7-11700K @ 3.60 GHz |
| CPU sockets | 1 |
| Physical cores | 8 |
| Threads | 16 |
| System memory | 60 GiB available to the operating system |
| Swap | 8 GiB |

### GPU

| Property | Value |
|---|---|
| GPU | NVIDIA GeForce GTX 1050 Ti |
| VRAM | 4 GiB |
| NVIDIA driver | `580.173.02` |
| CUDA compatibility reported by driver | `13.0` |
| NVIDIA persistence mode | Disabled |

The GPU is passed to Ollama through the NVIDIA container runtime configuration.

### Storage

| Device | Size | Type | Filesystem or role | Mount point |
|---|---:|---|---|---|
| Samsung SSD 980 1 TB | 931.5 GiB | NVMe | Physical system disk | N/A |
| `nvme0n1p2` | 2 GiB | Partition | ext4 | `/boot` |
| `nvme0n1p3` | 929.5 GiB | Partition | LVM physical volume | N/A |
| `ubuntu--vg-ubuntu--lv` | 100 GiB | LVM logical volume | ext4 | `/` |

The LVM physical volume is significantly larger than the 100 GiB root logical volume. Free space in the volume group must be verified before any storage expansion is planned.

Do not resize the filesystem or logical volume without checking:

```bash
sudo pvs
sudo vgs
sudo lvs
df -hT /
```

## Network

| Property | Value |
|---|---|
| LAN address | `192.168.55.7` |
| LAN subnet | `192.168.55.0/24` |
| Default gateway | `192.168.55.1` |
| Local DNS domain | `home.lab` |

Docker bridge addresses are dynamically managed by Docker and are not treated as host service addresses.

The network interface name, MAC address, DNS resolver configuration, and address assignment method still require documentation.

## Platform software

| Software | Version or state |
|---|---|
| Docker Engine | `29.7.1` |
| Docker Compose | `5.3.1` |
| NVIDIA driver | `580.173.02` |
| NVIDIA Container Toolkit | Installed and operational |
| Restic | Installed; version requires documentation |
| Git | Installed; version requires documentation |

## Containerized applications

### Application inventory

| Application | Container | Image | Published port | Status on 2026-08-17 |
|---|---|---|---:|---|
| Ollama | `ollama` | `ollama/ollama:latest` | `11434` | Running |
| Open WebUI | `open-webui` | `ghcr.io/open-webui/open-webui:v0.11.0` | `3000` | Running and healthy |
| JupyterLab | `jupyter` | `iza-jupyter:latest` | `8888` | Running and healthy |
| code-server | `code-server` | `lscr.io/linuxserver/code-server:latest` | `8443` | Running |

### Configuration files

| Application | Configuration |
|---|---|
| Ollama | `compose/ollama/compose.yaml` |
| Open WebUI | `compose/open-webui/compose.yaml` |
| JupyterLab | `compose/jupyter/compose.yaml`, `compose/jupyter/Dockerfile`, and local `.env` |
| code-server | `compose/code-server/compose.yaml` and local `.env` |

Local `.env` files may contain secrets and must not be committed to Git.

### Persistent data

| Application | Persistent paths |
|---|---|
| Ollama | `/opt/ai/models/ollama` |
| Open WebUI | `/opt/ai/data/open-webui` |
| JupyterLab | `/opt/ai/notebooks`, `/opt/ai/data/jupyter`, `/opt/ai/projects`, `/opt/ai/datasets`, `/opt/ai/cache/jupyter` |
| code-server | `/opt/ai/data/code-server/config`, `/opt/ai/projects`, `/opt/ai/notebooks`, `/opt/ai/datasets` |

Persistent data is stored outside containers. Removing or recreating a container must not remove these host paths.

## Directory structure

| Path | Purpose | Backup expectation |
|---|---|---|
| `/opt/ai/ansible` | Ansible-related host files | Review required |
| `/opt/ai/backups` | Local Restic repository and reports | Repository-dependent |
| `/opt/ai/cache` | Reproducible application caches | Generally excluded |
| `/opt/ai/data` | Persistent application data | Included selectively |
| `/opt/ai/datasets` | AI and data-analysis datasets | Included when practical |
| `/opt/ai/docker` | Docker-related host files | Review required |
| `/opt/ai/docs` | Host-local documentation | Review required |
| `/opt/ai/install` | Installation files and notes | Review required |
| `/opt/ai/models` | Local AI models | Large model files are excluded |
| `/opt/ai/notebooks` | Jupyter notebooks | Included |
| `/opt/ai/projects` | Git repositories and projects | Included |
| `/opt/ai/scripts` | Host-local scripts | Review required |

The infrastructure repository under `/opt/ai/projects/infrastructure` is the authoritative configuration and documentation source for this host.

## Application management

Run operational commands from:

```bash
cd /opt/ai/projects/infrastructure
```

Display all available commands:

```bash
make help
```

### Common status checks

```bash
make status
make health
make server-status
make gpu
make disk
make docker-usage
```

### Application lifecycle

```bash
make up
make down
make restart
make pull
make update
make logs
```

Stopping all applications with `make down` causes temporary service downtime. Check active use before running lifecycle operations.

## Backup

### Backup implementation

| Property | Value |
|---|---|
| Backup tool | Restic |
| Configuration | `config/backup.env` |
| Exclusion rules | `config/restic-excludes.txt` |
| Scripts | `scripts/backup-*.sh` |
| Reports | `/opt/ai/backups/reports` |
| QNAP mount | `/mnt/qnap-backup` |
| QNAP export | `192.168.55.5:/Backup` |
| Mount protocol | NFS 4.1 |

`config/backup.env` is intentionally excluded from Git because it contains repository-specific configuration and may reference credentials.

### Backup scope

The current data backup script includes existing paths from:

- `/opt/ai/projects`
- `/opt/ai/notebooks`
- `/opt/ai/datasets`
- `/opt/ai/data/open-webui`
- `/opt/ai/data/code-server`
- `/opt/ai/data/jupyter`
- `/opt/ai/backups/reports`

Large model files and reproducible caches are excluded according to `config/restic-excludes.txt`.

### Schedule

| Timer | Schedule | Purpose |
|---|---|---|
| `iza-ai-backup.timer` | Daily at approximately 03:00 UTC | Run the complete backup workflow |
| `iza-ai-backup-retention.timer` | Weekly, Sunday at approximately 04:00 UTC | Apply the Restic retention policy |

Both timers use persistent systemd scheduling, so a missed run may execute after the server starts.

### Backup verification commands

```bash
make backup-list
make backup-check
make backup-check-full
```

`make backup-check-full` reads all repository data and may take significantly longer than the standard check.

### Backup limitations

- The date and result of the latest successful restore test are not documented.
- Central backup failure alerting is not documented.
- Backup coverage for host-level configuration outside `/opt/ai` requires verification.
- Backup consistency for running application databases requires a separate review.
- The active Restic repository location must be verified from the local `config/backup.env` without exposing secrets.

## Dependencies

`iza` depends on:

- LAN connectivity
- local DNS for friendly service addresses
- QNAP availability for central backup storage
- Docker Engine and Docker Compose
- NVIDIA driver and container runtime for GPU acceleration
- local configuration files excluded from Git
- Forgejo for the primary infrastructure repository

Open WebUI, JupyterLab, and other clients depend on the Ollama API for local model inference.

## Security

- Do not commit `.env` files, passwords, tokens, private keys, or Restic credentials.
- OpenBao is the target centralized secrets-management platform.
- Published container ports are currently bound to all host interfaces.
- Reverse proxy, TLS, firewall rules, and direct-port exposure require a separate security review.
- Access to the QNAP NFS export must remain restricted to approved clients.

## Recovery outline

This is a high-level outline, not yet a verified disaster-recovery procedure.

1. Install the documented Ubuntu Server version.
2. Restore networking and SSH access.
3. Install the NVIDIA driver, Docker Engine, Docker Compose, and Restic.
4. Recreate the `/opt/ai` directory structure and required ownership.
5. Clone the primary repository from Forgejo into `/opt/ai/projects/infrastructure`.
6. Restore local configuration and secrets from the approved secret source.
7. Mount the QNAP backup export.
8. Restore persistent application data with Restic.
9. Start applications using the repository Makefile.
10. Run application, GPU, and backup verification checks.

The recovery procedure must be tested and expanded in `docs/operations/disaster-recovery.md`.

## Known gaps and follow-up work

- Verify the exact motherboard, firmware version, power supply, and network interface.
- Verify free LVM volume-group space before planning root filesystem expansion.
- Record the Restic version and active repository type without exposing credentials.
- Test restoration of Open WebUI data, notebooks, and one project.
- Document firewall rules and direct service exposure.
- Document reverse proxy and TLS configuration for services on `iza`.
- Verify backup coverage for `/etc`, systemd installation state, Docker configuration, and NVIDIA configuration.
- Move suitable secrets to OpenBao after its architecture is approved.
- Replace floating container tags such as `latest` with an approved versioning and update policy where appropriate.

## Change policy

Before a significant change to `iza`:

1. Check the current system and repository state.
2. Identify affected services and persistent data.
3. Verify the latest usable backup.
4. Plan the implementation and rollback.
5. Apply and test the change.
6. Update this document and related operational documentation.
7. Commit and push only the intended files.
