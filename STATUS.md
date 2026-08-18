# Infrastructure Status

Last updated: `2026-08-18`

## Current state

The HomeLab infrastructure repository is actively being expanded from documentation and discovery into controlled infrastructure management.

Terraform and Ansible currently manage approved newly created resources on both `dom` and `dtcode`.

The main recently deployed workloads are:

- `mysql01` on `dom`;
- `bao01` on `dtcode`.

Existing infrastructure is not automatically imported or recreated. Legacy workloads remain protected until their configuration, dependencies, persistent data and backup coverage are understood.

## Tooling

The current management environment includes:

- Terraform `1.15.8` on `iza`;
- BPG Proxmox Terraform provider;
- read-only Terraform API access to both Proxmox environments;
- restricted Terraform management access to both Proxmox environments;
- local Terraform state with protected filesystem permissions;
- QNAP-backed infrastructure backup;
- Ansible Core `2.20.1`;
- Forgejo as the primary Git server;
- GitHub as a public repository mirror.

## Terraform status

Terraform currently manages approved newly created resources on both `dom` and `dtcode`.

| Resource | Status |
|---|---|
| `mysql01` VM, ID `201` | Managed |
| `bao01` VM, ID `104` | Managed |
| State path | `terraform/state/terraform.tfstate` |
| State permissions | Protected locally |
| State backup to QNAP | Active |

The Terraform configuration uses restricted Proxmox management credentials rather than unrestricted administrative credentials.

Existing legacy workloads on `dtcode` have not been imported into the current Terraform state.

The newly created `bao01` VM is managed by the current Terraform state.

Existing infrastructure must not be imported or recreated only to make it conform to the current Terraform standard.

Any future import requires prior verification of:

- current live configuration;
- dependencies;
- persistent data;
- backup coverage;
- lifecycle expectations.

## Proxmox access

Terraform access is separated between read-only discovery and restricted resource management.

Known API identities include:

```text
terraform-audit@pve!prov
```

for read-only infrastructure inspection, and:

```text
terraform-manage@pve!provider
```

for approved Terraform-managed resources.

Management permissions are intentionally restricted.

Terraform-created resources use the:

```text
terraform-managed
```

resource pool where applicable.

## mysql01 status

| Property | Value |
|---|---|
| Proxmox host | `dom` |
| VM ID | `201` |
| Address | `192.168.55.21` |
| FQDN | `mysql01.home.lab` |
| Operating system | Ubuntu Server |
| Terraform management | Active |
| Ansible management | Active |
| MySQL management | Ansible |
| Database `ai_demo` | Ansible-managed |
| Database-aware backup | Not configured |

`mysql01` provides the MySQL platform for HomeLab application and AI demonstration workloads.

The Ansible MySQL role supports declarative creation of configured databases.

The currently configured database is:

```text
ai_demo
```

MySQL logical backup and restore still require implementation and testing.

## bao01 status

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

`bao01` is the central OpenBao secrets-management and PKI server for the HomeLab infrastructure.

The VM is protected against accidental destruction at the Proxmox/Terraform lifecycle level.

## OpenBao status

| Property | Value |
|---|---|
| Version | `2.6.1` |
| Service | Enabled and active |
| Storage | Integrated Raft |
| Raft node | `bao01` |
| API port | `8200` |
| Cluster port | `8201` |
| TLS | Enabled |
| UI | Enabled |
| Seal type | Shamir |
| Shares | `5` |
| Threshold | `3` |
| Authentication | `userpass`, token |
| Administrator account | `tom` |
| Initial root token | Revoked |
| PKI secrets engine | Enabled |
| Intermediate CA | Active |
| HTTPS through Nginx Proxy Manager | Verified |
| Raft snapshot backup | Created and encrypted |
| Raft restore test | Not yet performed |

OpenBao is initialized and operational.

The initial root token was revoked after administrative access through `userpass` was configured.

OpenBao currently uses Shamir unseal with five shares and a threshold of three.

A service or system restart causes OpenBao to become sealed and currently requires manual unseal.

The OpenBao Ansible bootstrap was verified as idempotent on `2026-08-18`:

```text
changed=0
unreachable=0
failed=0
```

## PKI status

The HomeLab internal PKI currently uses the following hierarchy:

```text
HomeLab Root CA
    |
    +-- HomeLab OpenBao Intermediate CA
            |
            +-- service certificates
```

The Root CA private key is maintained outside Git and is protected with a passphrase.

OpenBao operates the intermediate CA and can issue service certificates without requiring routine access to the Root CA private key.

The OpenBao listener uses TLS for:

```text
bao01.home.lab
```

Nginx Proxy Manager uses a separate certificate and private key for the client-facing `bao01.home.lab` endpoint.

The verified connection path is:

```text
client
  -> HTTPS
  -> Nginx Proxy Manager
  -> HTTPS
  -> OpenBao
```

TLS verification succeeds using the HomeLab Root CA without disabling certificate verification.

## Ansible status

The production inventory currently contains:

- `database_servers`;
- `secrets_servers`.

Managed hosts currently include:

- `mysql01`;
- `bao01`.

The bootstrap playbooks manage:

- QEMU Guest Agent;
- MySQL Server on `mysql01`;
- PyMySQL;
- MySQL service startup;
- baseline MySQL security configuration;
- configured MySQL databases;
- OpenBao package installation on `bao01`;
- OpenBao version;
- OpenBao Raft data directory;
- OpenBao TLS-enabled configuration;
- OpenBao systemd service.

The `ansible.mysql` collection is pinned to version `5.2.0`.

OpenBao TLS certificate provisioning is not yet fully automated.

The OpenBao role verifies that the required TLS files exist before deploying the TLS-enabled OpenBao configuration.

Runtime OpenBao configuration such as PKI issuers, authentication methods and policies is not yet fully declarative.

## Backup status

The current infrastructure backup state includes:

- local Restic backups remain available;
- the QNAP NFS export is mounted at `/mnt/qnap-backup`;
- systemd automount for `/mnt/qnap-backup` is configured;
- an independent Restic repository exists at `/mnt/qnap-backup/AI/iza/restic`;
- Terraform state is included in infrastructure backup coverage;
- OpenBao encrypted initialization material is stored outside Git and copied to QNAP;
- the HomeLab Root CA certificate and encrypted private key are backed up on QNAP;
- an encrypted OpenBao Raft snapshot has been created and copied to QNAP;
- encrypted Raft snapshot decryption was verified against the original snapshot checksum;
- the local encrypted Raft snapshot and QNAP copy have matching SHA-256 checksums;
- MySQL logical backup and restore have not yet been implemented;
- an OpenBao Raft restore test has not yet been performed.

The first verified OpenBao Raft snapshot was created on `2026-08-18`.

The plaintext snapshot was removed after successful encryption verification.

Only the encrypted `.snap.gpg` backup is retained.

OpenBao backup creation is not yet automated.

## Existing dtcode resources

Existing legacy resources on `dtcode` remain outside the current Terraform state unless explicitly documented otherwise.

`bao01` is an exception because it was deliberately created as a new Terraform-managed resource.

Legacy resources must not be imported until their:

- configuration;
- dependencies;
- persistent data;
- backup coverage;
- lifecycle requirements

have been documented and verified.

## Current task

Complete the documentation and backup coverage for the deployed MySQL and OpenBao infrastructure.

OpenBao is now operational, but several operational areas still require automation and recovery testing.

## Next tasks

1. Complete OpenBao service and recovery documentation.
2. Complete HomeLab PKI documentation.
3. Document the verified OpenBao backup architecture.
4. Automate OpenBao Raft snapshots.
5. Define OpenBao snapshot retention.
6. Perform a controlled OpenBao Raft snapshot restore test.
7. Automate service certificate renewal.
8. Add certificate-expiration monitoring.
9. Add OpenBao seal-state monitoring.
10. Continue controlled migration of infrastructure secrets into OpenBao.
11. Configure MySQL logical backups.
12. Test MySQL restore.
13. Implement backup monitoring and alerting.
14. Review existing `dtcode` resources before any Terraform import.
15. Continue migration of infrastructure management into Terraform and Ansible without unnecessarily rebuilding existing services.