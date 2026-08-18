# bao01

## Purpose

`bao01` is the central OpenBao secrets-management and PKI server for the HomeLab infrastructure.

## Virtual machine

| Property | Value |
|---|---|
| Proxmox host | `dtcode` |
| VM ID | `104` |
| Address | `192.168.55.24` |
| FQDN | `bao01.home.lab` |
| Operating system | Ubuntu Server 24.04.4 LTS |
| CPU | 2 virtual cores |
| Memory | 2 GiB |
| Disk | 32 GiB |
| Start on Proxmox boot | Enabled |
| QEMU Guest Agent | Active |
| Terraform management | Active |
| Ansible management | Active |

The VM is created from template `101` (`ubuntu-2404`) using a full clone.

## OpenBao

| Property | Value |
|---|---|
| Version | `2.6.1` |
| Service | `openbao.service` |
| API port | `8200/tcp` |
| Cluster port | `8201/tcp` |
| Storage | Integrated Raft |
| Raft node ID | `bao01` |
| UI | Enabled |
| TLS | Enabled |
| Authentication | `userpass`, token |
| Administrator account | `tom` through `userpass` |
| Root token | Initial root token revoked after bootstrap |

## Persistent data

OpenBao Raft data is stored at:

```text
/opt/openbao/data
```

TLS files are stored at:

```text
/etc/openbao/tls
```

The private TLS key must never be stored in Git.

## TLS

The OpenBao listener uses a certificate for:

```text
bao01.home.lab
```

The certificate chain is:

```text
HomeLab Root CA
    -> HomeLab OpenBao Intermediate CA
        -> bao01.home.lab
```

The listener configuration is managed by Ansible.

TLS certificates are currently provisioned separately from the Ansible bootstrap role. The role verifies that the required TLS files exist before deploying the TLS-enabled OpenBao configuration.

## Reverse proxy

External HomeLab access uses Nginx Proxy Manager.

The reverse-proxy flow is:

```text
client
  -> https://bao01.home.lab
  -> Nginx Proxy Manager
  -> https://192.168.55.24:8200
  -> OpenBao
```

The NPM frontend uses a separate certificate and private key from the OpenBao listener certificate.

## Initialization and seal

OpenBao was initialized using Shamir key splitting:

```text
Shares: 5
Threshold: 3
```

OpenBao seals automatically after a restart and currently requires manual unseal using three shares.

Initialization, unseal keys and recovery credentials are not stored in Git.

## Recovery material

Encrypted initialization data is stored outside the repository.

Primary protected location on `iza`:

```text
/opt/ai/secrets/openbao/bao01-init.json.gpg
```

A copy of the encrypted initialization data is stored on QNAP.

The GPG recovery key and Root CA private key are maintained separately from the infrastructure repository.

See:

```text
docs/procedures/openbao-recovery.md
docs/security/pki.md
docs/backup/BACKUP.md
```

## Management

Terraform manages:

- VM lifecycle;
- CPU and memory;
- disk;
- networking;
- cloud-init;
- Proxmox protection and startup behavior.

Ansible manages:

- QEMU Guest Agent;
- OpenBao package installation;
- OpenBao version;
- Raft data directory;
- OpenBao configuration;
- systemd service.

Runtime OpenBao configuration such as PKI issuers, policies, authentication methods and recovery bootstrap currently requires separate documented procedures and is not yet fully declarative.

## Verification

Verified on `2026-08-18`:

- VM running;
- QEMU Guest Agent active;
- OpenBao service active;
- OpenBao version `2.6.1`;
- Raft storage active;
- TLS listener active;
- OpenBao initialized;
- OpenBao unsealed;
- administrator login through `userpass`;
- initial root token revoked;
- HTTPS health endpoint reachable through Nginx Proxy Manager;
- Ansible bootstrap idempotent with `changed=0` and `failed=0`.
