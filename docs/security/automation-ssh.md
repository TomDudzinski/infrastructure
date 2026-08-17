# Automation SSH access

## Purpose

The `iza` host uses a dedicated SSH key to administer the Proxmox VE hosts and to support future Ansible automation.

Terraform does not use this SSH key to manage Proxmox resources. Terraform connects to the Proxmox API on TCP port `8006` and will use separate API credentials.

## Source identity

| Property | Value |
|---|---|
| Source host | `iza` |
| Source user | `tom` |
| Private key | `~/.ssh/homelab_automation_ed25519` |
| Public key | `~/.ssh/homelab_automation_ed25519.pub` |
| Key comment | `homelab-automation@iza` |
| SSH configuration | `~/.ssh/config.d/homelab.conf` |

The private key is not protected with a passphrase to allow unattended automation. It must remain readable only by its owner and must never be committed to Git.

## Destinations

| SSH alias | Address | Current user | Purpose |
|---|---|---|---|
| `dtcode` | `192.168.55.6` | `root` | Proxmox administration and automation |
| `dom` | `192.168.55.3` | `root` | Proxmox administration and automation |

The aliases `proxmox1` and `proxmox2` are compatibility aliases for `dtcode` and `dom`. Host names should be preferred in documentation and automation.

## Verified host keys

The ED25519 host-key fingerprints were verified against the local console of each Proxmox host on 2026-08-17.

| Host | ED25519 fingerprint |
|---|---|
| `dtcode` | `SHA256:3fetgLk/RFudl8OYac/L7fOiq/vgx2YDj2dx8GZPWks` |
| `dom` | `SHA256:BV9fhJl3fn5/lWLSv1RjAxA+vJVNijweAMjbOADncHI` |

## Setup and verification

Run from the infrastructure repository on `iza`:

```bash
./scripts/setup-automation-ssh.sh
./scripts/setup-automation-ssh.sh --install-key
./scripts/setup-automation-ssh.sh --test
```

The setup script must not overwrite an existing private key or host configuration.

## Security limitations

The current bootstrap configuration grants key-based SSH access to the `root` account on both Proxmox hosts. This provides broad administrative access and must be treated as a temporary bootstrap state.

Target state:

- create a dedicated automation account where Proxmox administration permits it;
- grant only the privileges required by Ansible tasks;
- keep Proxmox API tokens separate from SSH credentials;
- migrate suitable credentials to OpenBao;
- define key rotation and revocation procedures;
- back up recovery information without storing private keys in Git.

## Revocation

To revoke this identity, remove the line containing `homelab-automation@iza` from `/root/.ssh/authorized_keys` on both Proxmox hosts. Verify console access before changing or revoking remote access.
