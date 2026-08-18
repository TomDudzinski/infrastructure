# Terraform

## Purpose

Terraform manages the lifecycle of approved Proxmox infrastructure resources, including:

- VM and LXC allocation;
- CPU and memory;
- disks and storage;
- network devices;
- cloud-init;
- operating-system images;
- VM startup behavior;
- controlled lifecycle operations.

Operating-system and application configuration belongs to Ansible or Docker Compose rather than Terraform.

## Current status

Terraform provides both read-only inventory access and restricted management access to the `dtcode` and `dom` Proxmox environments.

The first resource managed by the current Terraform state is `mysql01` on `dom`.

| Property | Value |
|---|---|
| Execution host | `iza` |
| Terraform version | `1.15.8` |
| Provider | `bpg/proxmox` `0.111.1` |
| Backend | Local |
| State path | `terraform/state/terraform.tfstate` |
| Managed Proxmox host | `dom` |
| Managed VM | `mysql01`, VM ID `201` |
| Existing `dtcode` resources | Not imported |

## Proxmox providers

| Provider alias | Host | Endpoint | Access |
|---|---|---|---|
| `proxmox.dtcode` | `dtcode` | `https://192.168.55.6:8006/` | Read-only audit |
| `proxmox.dom` | `dom` | `https://192.168.55.3:8006/` | Read-only audit |
| `proxmox.dtcode_manage` | `dtcode` | `https://192.168.55.6:8006/` | Restricted management |
| `proxmox.dom_manage` | `dom` | `https://192.168.55.3:8006/` | Restricted management |

The provider version is pinned exactly because the provider remains on the `0.x` release line. Provider upgrades require a separate compatibility review and an inspected saved plan.

## Identity separation

Read-only providers use:

```text
terraform-audit@pve!provider
```

Management providers use:

```text
terraform-manage@pve!provider
```

The audit token must not be broadened to support infrastructure changes.

The management identity uses reviewed custom roles and restricted ACL paths. It does not receive the built-in `Administrator` role.

## Files

```text
terraform/
├── .terraform.lock.hcl
├── backend.tf
├── data.tf
├── dom_mysql01.tf
├── outputs.tf
├── providers.tf
├── README.md
├── state/
├── variables.tf
└── versions.tf
```

The following files and directories must not be committed:

- `.terraform/`;
- Terraform state;
- saved plan files;
- variable files containing secrets;
- crash logs;
- local provider configuration.

The provider dependency lock file is committed.

## State

The current backend is defined in `backend.tf`:

```hcl
terraform {
  backend "local" {
    path = "state/terraform.tfstate"
  }
}
```

The state directory is restricted to the `tom` account.

The local backend does not provide remote locking or multi-user coordination. Terraform operations must be run from `iza`, one at a time.

State must never be edited manually or committed to Git.

Display tracked resources:

```bash
terraform -chdir=terraform state list
```

The current state should include:

```text
data.proxmox_version.dom
data.proxmox_version.dtcode
proxmox_download_file.dom_ubuntu_2404_cloud_image
proxmox_virtual_environment_vm.mysql01
```

## State backup

The complete infrastructure repository, including the ignored local Terraform state, is backed up to the independent QNAP Restic repository:

```text
/mnt/qnap-backup/AI/iza/restic
```

Run the configuration backup from the repository root:

```bash
./scripts/backup-config-qnap.sh
```

A Restic repository check and an actual restore test were completed successfully on `2026-08-17`.

The local backend remains a bootstrap solution. A future backend should provide:

- encryption;
- access control;
- locking;
- versioning;
- backup;
- documented recovery.


## Credentials

Credentials are stored outside the repository:

```text
~/.config/homelab/terraform/
```

Audit token files:

```text
dtcode-audit-token.json
dom-audit-token.json
```

Management token files:

```text
dtcode-manage-token.json
dom-manage-token.json
```

The directory must have mode `700`, and token files must have mode `600`.

Load audit credentials:

```bash
source ./scripts/load-proxmox-audit-env.sh
```

Load management credentials only when an approved management operation is required:

```bash
source ./scripts/load-proxmox-manage-env.sh
```

Do not display exported credential variables or enable shell tracing while credentials are loaded.

## Initialization

Run from the repository root:

```bash
terraform -chdir=terraform init -reconfigure -input=false
```

## Validation

```bash
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
```

## Planning

Load both credential sets:

```bash
set +x
source ./scripts/load-proxmox-audit-env.sh
source ./scripts/load-proxmox-manage-env.sh
```

Create a saved plan:

```bash
terraform -chdir=terraform plan \
  -input=false \
  -out=mysql01.tfplan
```

Inspect the saved plan:

```bash
terraform -chdir=terraform show mysql01.tfplan
```

The plan must not contain unexpected destruction or resource replacement.

## Applying changes

Apply only a previously inspected saved plan:

```bash
terraform -chdir=terraform apply mysql01.tfplan
```

Delete the saved plan after successful application or when it is no longer valid:

```bash
rm -f -- terraform/mysql01.tfplan
```

Saved plans can contain sensitive data and must not be committed or retained longer than necessary.


## Managed resources on dom

### Ubuntu cloud image

Terraform downloads the official Ubuntu 24.04 cloud image to the `local` storage on `dom`.

The download uses HTTPS certificate verification and a pinned SHA-256 checksum.

### mysql01

Terraform manages:

- VM ID `201`;
- name `mysql01`;
- resource pool `terraform-managed`;
- two CPU cores;
- 4 GiB memory;
- 64 GiB system disk on `local-lvm`;
- VirtIO network attached to `vmbr0`;
- static address `192.168.55.21/24`;
- gateway `192.168.55.1`;
- DNS server `192.168.55.10`;
- cloud-init user `tom`;
- approved SSH public keys;
- QEMU Guest Agent integration;
- automatic startup;
- Proxmox protection.

Guest packages and MySQL configuration are managed by Ansible.

## Existing infrastructure

Existing VMs, containers and templates on `dtcode` are not tracked by the current state.

They must not be recreated or imported merely to make the inventory appear complete.

Required import workflow:

1. Document the resource and its dependencies.
2. Verify persistent data and backup coverage.
3. Create an exact Terraform resource definition.
4. Save a backup.
5. Import the selected resource deliberately.
6. Inspect the complete plan.
7. Resolve all drift.
8. Apply only after explicit approval.

## Destructive operations

Before any plan containing `destroy` or resource replacement:

1. Identify the exact affected resource.
2. Verify the reason for the operation.
3. Verify current backup coverage.
4. Test recovery when practical.
5. Inspect the saved plan.
6. Obtain explicit approval.

The `mysql01` VM uses Proxmox protection and conservative Terraform deletion settings to reduce accidental removal risk.

## TLS

Both Proxmox endpoints currently use certificates that are not trusted by the `iza` operating-system CA store.

Their SHA-256 fingerprints were verified separately. The provider temporarily uses:

```hcl
insecure = true
```

The target state is trusted local PKI with certificate verification enabled.

## Verification after apply

```bash
terraform -chdir=terraform state list
terraform -chdir=terraform plan -input=false
ssh dom 'qm status 201'
ssh dom 'qm config 201'
```

A normal post-apply plan should report no infrastructure changes.

## Responsibility boundary

| Area | Tool |
|---|---|
| Proxmox resource lifecycle | Terraform |
| VM hardware and cloud-init | Terraform |
| Operating-system packages | Ansible |
| MySQL installation and configuration | Ansible |
| Container applications | Docker Compose |
| Configuration and state backup | Restic |
| Secret management target | OpenBao |
