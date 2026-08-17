# Homelab & AI Infrastructure - Project Context

## Purpose

The project manages the user's homelab and local AI infrastructure.

The main goals are:

- Infrastructure as Code
- reproducible server configuration
- centralized secrets management
- reliable backups
- documentation of all infrastructure
- local AI/LLM platform
- gradual migration of existing infrastructure to Terraform + Ansible

## Important rule

Existing infrastructure must not be rebuilt or modified only to fit the new standard.

Before changing an existing machine:

1. Inventory it.
2. Document it.
3. Verify backup.
4. Identify dependencies.
5. Plan the change.
6. Perform the change.
7. Test.
8. Update documentation.
9. Commit to Git.

## Infrastructure management

Terraform manages infrastructure resources.

Ansible manages operating system and application configuration.

OpenBao will manage secrets.

Docker Compose manages containerized applications.

Restic manages backups.

Git is the source of truth for configuration and documentation.

## Proxmox Hosts

### dtcode

- IP: 192.168.55.6
- Role: smaller Proxmox host

### dom

- IP: 192.168.55.3
- Role: main high-resource Proxmox host

## AI Server

### iza

Dedicated physical AI/LLM server.

Services currently include:

- Ollama
- Open WebUI
- code-server
- JupyterLab
- Docker
- NVIDIA GPU support
- Restic

## Storage

### QNAP TS-253D

- IP: 192.168.55.5
- QTS 5.1.9.2954
- 2 x 4 TB disks
- central backup storage

## Known Virtual Machines

- dns01 - VM ID 102 - 192.168.55.10
- home01 - VM ID 103 - 192.168.55.20
- forgejo01 - VM ID 105 - 192.168.55.22
- npm01 - VM ID 106 - 192.168.55.23
- tailscale-router - VM ID 107 - 192.168.55.4

These machines already exist and must be preserved.

## Secrets

Secrets must never be committed to Git in plaintext.

Target solution:

OpenBao

Secret categories:

- infrastructure secrets
- application secrets
- SSH credentials
- Proxmox API credentials
- certificates and private keys
- backup credentials

## Current direction

1. Document existing infrastructure.
2. Finish QNAP backup.
3. Implement OpenBao.
4. Introduce Ansible.
5. Gradually migrate existing provisioning from Terraform provisioners to Ansible.
6. Manage both Proxmox hosts using Terraform.
