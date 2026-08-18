# Current Status

## Current phase

Deployment and configuration of the first Terraform-managed workload on `dom`.

## Working infrastructure

- Proxmox VE 8.2.2 on `dtcode`;
- Proxmox VE 9.2.2 on `dom`;
- SSH automation from `iza`;
- Terraform 1.15.8 on `iza`;
- `bpg/proxmox` provider 0.111.1;
- read-only Terraform API access to both Proxmox environments;
- restricted Terraform management access to both Proxmox environments;
- local Terraform state with protected filesystem permissions;
- QNAP-backed Restic infrastructure configuration backup;
- Ansible Core 2.20.1;
- AI server `iza`;
- QNAP NFS access;
- Docker;
- Ollama;
- Open WebUI;
- code-server;
- JupyterLab.

## Terraform status

Terraform currently manages newly created resources on `dom`.

| Resource | State |
|---|---|
| Ubuntu 24.04 cloud image | Managed |
| `mysql01` VM, ID `201` | Managed |
| Local state backend | Active |
| State path | `terraform/state/terraform.tfstate` |
| State committed to Git | No |
| State backup to QNAP | Active |
| State restore test | Infrastructure repository restore completed |

The existing workloads on `dtcode` have not been imported into the current Terraform state.

### Provider identities

Read-only providers use:

```text
terraform-audit@pve!prov```

Restricted management providers use:

```text
terraform-manage@pve!provider
```

The audit identity remains separate and has not been broadened.

### Management boundaries

Management permissions are limited to:

- the `terraform-managed` resource pool;
- `local` and `local-lvm` storage;
- required node information;
- use of `vmbr0`;
- URL metadata and image download access where required.

The management identity does not use the built-in `Administrator` role.

## mysql01 status

| Property | Value |
|---|---|
| Proxmox host | `dom` |
| VM ID | `201` |
| Address | `192.168.55.21` |
| FQDN | `mysql01.home.lab` |
| Operating system | Ubuntu Server 24.04.4 LTS |
| CPU | 2 virtual cores |
| Memory | 4 GiB |
| Disk | 64 GiB |
| Start on Proxmox boot | Enabled |
| QEMU Guest Agent | Active |
| Terraform management | Active |
| Ansible management | Active |

## MySQL status

| Property | Value |
|---|---|
| Version | `8.0.46` |
| Service | Enabled and active |
| SQL port | `3306` |
| Current binding | `127.0.0.1` |
| MySQL X Protocol port | `33060` |
| Anonymous users | Removed |
| Test database | Removed |
| Remote access | Disabled |
| Application databases | Not created |
| AI agent account | Not created |
| Database-aware backup | Not configured |

MySQL currently accepts only local connections. This is intentional until credentials, firewall restrictions and the read-only application account are implemented.

## Ansible status

The production inventory currently contains the `database_servers` group and the `mysql01` host.

The bootstrap playbook manages:

- QEMU Guest Agent;
- MySQL Server;
- PyMySQL;
- MySQL service startup;
- baseline MySQL security configuration.

The `ansible.mysql` collection is pinned to version `5.2.0`.

## Backup status

- local Restic backups remain available;
- the QNAP NFS export is mounted at `/mnt/qnap-backup`;
- an independent Restic repository exists at `/mnt/qnap-backup/AI/iza/restic`;
- infrastructure configuration snapshots are stored in the QNAP repository;
- `restic check` completed successfully;
- an actual restore test completed successfully on `2026-08-17`;
- MySQL logical backup and restore have not yet been implemented.

## Existing infrastructure requiring controlled import review

The following existing resources on `dtcode` are not managed by the current Terraform state:

- template `101` (`ubuntu-2404`);
- LXC `102` (`dns01`);
- VM `103` (`home01`);
- VM `105` (`forgejo01`);
- VM `106` (`npm01`);
- VM `107` (`tailscale-router`);
- template `999` (`ubuntu-temp`).

They must not be imported until their configuration, dependencies, persistent data and backup coverage are documented.

## Current task

Complete the documentation for the Terraform, Ansible, backup and `mysql01` deployment.

## Next tasks

1. Update the infrastructure inventory and network documentation.
2. Update Terraform access, state and backup documentation.
3. Verify Ansible idempotency.
4. Create the demonstration MySQL database.
5. Create a restricted read-only AI agent account.
6. Introduce secure storage for the database credential.
7. Restrict MySQL network access to approved clients.
8. Configure MySQL logical backups.
9. Perform and document a MySQL restore test.
10. Add monitoring and alerting.
11. Design and deploy OpenBao.
12. Review existing `dtcode` resources before any Terraform import.
