# Secrets Management

## Rule

No plaintext secrets are stored in Git.

## Target platform

OpenBao.

## Secret groups

### Infrastructure

- Proxmox API tokens
- Terraform credentials
- SSH credentials
- Ansible credentials
- Tailscale credentials

### Applications

- database passwords
- SMTP credentials
- API keys
- OAuth secrets
- application administrator passwords

### PKI

- HomeLab CA private key
- wildcard TLS private key
- certificates

### Backup

- Restic repository passwords

## Current migration requirement

Existing secrets currently embedded in Terraform or scripts must be rotated and moved to OpenBao.
