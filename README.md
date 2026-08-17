# HomeLab Infrastructure

Infrastructure as Code, configuration, automation, and documentation for the HomeLab environment and the dedicated local AI platform.

## Scope

The repository covers:

- Proxmox VE hosts
- virtual machines and containers
- Terraform infrastructure definitions
- Ansible configuration management
- Docker Compose applications
- local DNS and reverse proxy
- Tailscale VPN access
- OpenBao secrets management
- QNAP storage
- Restic backups
- monitoring
- local AI and LLM services

## Repository model

The primary Git repository is hosted on the local Forgejo server:

- `http://git.home.lab/tom/infrastructure`

A public mirror is available on GitHub:

- `https://github.com/TomDudzinski/infrastructure`

Forgejo is the source of truth. The GitHub mirror may temporarily be behind the primary repository.

## Infrastructure overview

### Proxmox hosts

| Host | Address | Role |
|---|---|---|
| `dtcode` | `192.168.55.6` | Smaller virtualization host |
| `dom` | `192.168.55.3` | Main high-resource virtualization host |

### Physical hosts

| Host | Address | Role |
|---|---|---|
| `iza` | `192.168.55.7` | Local AI and LLM platform |
| `qnap` | `192.168.55.5` | Central storage and backup target |

### Known virtual machines

| VM ID | Name | Address | Role |
|---:|---|---|---|
| 102 | `dns01` | `192.168.55.10` | Technitium DNS |
| 103 | `home01` | `192.168.55.20` | Homepage dashboard |
| 105 | `forgejo01` | `192.168.55.22` | Primary Git server |
| 106 | `npm01` | `192.168.55.23` | Nginx Proxy Manager |
| 107 | `tailscale-router` | `192.168.55.4` | Tailscale subnet router |

## AI platform

The `iza` physical server currently runs:

- Ollama
- Open WebUI
- JupyterLab
- code-server
- Docker Engine
- NVIDIA Container Toolkit
- Restic

Persistent application data is stored outside containers under `/opt/ai`.

## Management responsibilities

### Terraform

Terraform manages infrastructure resources:

- Proxmox virtual machines and containers
- CPU, memory, disks, and networking
- cloud-init configuration
- infrastructure lifecycle

### Ansible

Ansible manages operating system and application configuration:

- users and SSH
- packages
- Docker
- certificates
- systemd services
- application installation and configuration

### Docker Compose

Docker Compose manages containerized applications.

### OpenBao

OpenBao is the target platform for centralized secrets management.

Secrets must never be committed to Git in plaintext.

### Restic and QNAP

Restic manages backups. The QNAP NAS is the central backup target.

## Repository structure

| Path | Purpose |
|---|---|
| `terraform/` | Proxmox infrastructure definitions |
| `ansible/` | Host and application configuration |
| `compose/` | Docker Compose applications |
| `systemd/` | Managed systemd units and timers |
| `scripts/` | Operational and backup scripts |
| `config/` | Non-secret configuration templates |
| `docs/` | Architecture and operational documentation |
| `Makefile` | Common operational commands |

## Change workflow

Major infrastructure changes follow this workflow:

1. Plan
2. Backup
3. Implementation
4. Test
5. Documentation
6. Git commit
7. Git push

Existing infrastructure must be inspected and documented before significant changes are made. Existing machines must not be rebuilt only to conform to a new standard.

## Make commands

Run these commands from `/opt/ai/projects/infrastructure` on the `iza` server.

### Help

```bash
make help
```

### Application lifecycle

```bash
make up
make down
make restart
make status
make ps
make logs
make pull
make update
```

### Individual applications

```bash
make ollama
make open-webui
make code-server
make jupyter
```

### Health and host diagnostics

```bash
make health
make server-status
make gpu
make sensors
make disk
make docker-usage
```

### Ollama benchmarks

Run a benchmark with the default model:

```bash
make benchmark
```

Run a benchmark with a selected model:

```bash
make benchmark MODEL=SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0
```

### Backup workflow

Run the complete backup workflow:

```bash
make backup
```

Run individual backup operations:

```bash
make backup-config
make backup-data
make backup-report
```

Inspect and verify the Restic repository:

```bash
make backup-list
make backup-check
make backup-check-full
```

Apply the configured Restic retention policy:

```bash
make backup-retention
```

### Host dependencies

```bash
make install-host-deps
```

Install Terraform from the official HashiCorp repository:

```bash
make install-terraform
```

## Documentation

Start with:

- [Project context](PROJECT_CONTEXT.md)
- [Current status](STATUS.md)
- [Infrastructure inventory](INVENTORY.md)
- [Architecture](ARCHITECTURE.md)
- [Roadmap](ROADMAP.md)
- [Host documentation](docs/hosts/)
- [Backup documentation](docs/backup/)
- [Security and secrets](docs/security/SECRETS.md)
