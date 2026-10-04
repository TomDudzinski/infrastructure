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

## Prepared legacy adoption on dtcode (2026-10-04)

The definitions in `dtcode_home01.tf`, `dtcode_forgejo01.tf`, `dtcode_npm01.tf`,
`dtcode_tailscale_router.tf` and `dtcode_dns01.tf` now reflect live hardware
configuration supplied by the administrator. This laptop review did not contact
Proxmox, execute Terraform or confirm state membership. The resources remain
prepared for adoption, not imported by this change.

| Resource address suffix | ID | CPU cores | RAM MiB | Storage | IPv4 | Startup order |
|---|---|---|---|---|---|---|
| `vm.home01` | 103 | 1 | 1024 | local-lvm / scsi0 / 32 GiB | 192.168.55.20/24 | 2 |
| `vm.forgejo01` | 105 | 1 | 1024 | local-lvm / scsi0 / 32 GiB | 192.168.55.22/24 | 3 |
| `vm.npm01` | 106 | 1 | 1024 | local-lvm / scsi0 / 32 GiB | 192.168.55.23/24 | 1 |
| `vm.tailscale_router` | 107 | 1 | 512 | local-lvm / scsi0 / 32 GiB | 192.168.55.4/24 | 1 |
| `container.dns01` | 102 | 2 | 2048 | local-lvm / rootfs / 20 GiB | 192.168.55.10/24 | 1 |

VM resource addresses use the prefix `proxmox_virtual_environment_vm`;
the LXC uses `proxmox_virtual_environment_container`. All use node `dtcode`,
bridge `vmbr0`, gateway `192.168.55.1`, automatic boot and an up delay of 20 s.
Existing MAC addresses are preserved. VM disks use the repository's bpg/proxmox
0.111.1 declaration style: datastore, interface and size, without a generated
volume name or `file_id`. The four VMs use `virtio-scsi-pci`, `l26`, zero balloon
memory, VirtIO networking without firewall, and cloud-init on `ide2`.

All five definitions use `protection = false` to match reported protection=0.
`prevent_destroy = true` is a separate Terraform guard. Enabling Proxmox
protection is a future policy change requiring approval, not hidden import drift.

VM `clone` blocks were removed: template 999 is historical provenance, and its
existence is not required to adopt these existing VMs. These definitions are not
approved recipes for recreating lost guests.

Remaining lifecycle exclusions:

- All five: `started`, because runtime power state is operational rather than
  enforced by adoption; `initialization[0].user_account` and
  `initialization[0].dns`, to preserve excluded credentials/keys and guest DNS.
- Four VMs: `initialization[0].upgrade`, to avoid managing guest package upgrades.
- LXC only: `operating_system[0].template_file_id`, because this is a historical
  creation input and the supplied live configuration does not establish the
  image used or its current availability. It remains a historical value pending
  verification of the pinned provider's required schema/import behavior.

Disks and VM operating-system type are no longer ignored. No secret, SSH key,
SMBIOS UUID, vmgenid, timestamp or generated volume identifier was added.

Unverified: current power state; descriptions, tags, BIOS and resource pool;
additional hardware/devices or mounts not covered by the supplied configuration;
optional disk defaults (cache, discard, iothread, aio, backup, replication,
format and SSD emulation); optional NIC settings (MTU, VLAN, queues, rate and
LXC firewall); optional startup/down delay and agent settings; cloud-init DNS,
username and upgrade behavior; exact LXC template image and availability;
other LXC feature defaults; provider normalization after import; actual state
membership, dependencies, persistent data and backup/restore coverage.
Historical/default values in the definitions are not newly confirmed live facts.

### Before the first import on iza

This is a future operator procedure, not authorization to execute it here.

1. Obtain explicit approval for the selected resource's import. Synchronize and
   review these exact changes on `iza` using the approved transfer/Git workflow.
2. Ensure no concurrent Terraform process is using the local backend. Confirm
   the backend path `terraform/state/terraform.tfstate`, Terraform 1.15.x and
   the lock file pin to bpg/proxmox 0.111.1; do not upgrade providers.
3. Verify persistent data, resource backups and recovery coverage. Create a
   restricted backup of the current state and configuration before mutation;
   do not commit or display state, credentials or saved plans.
4. On `iza`, initialize the existing backend if required, then run formatting
   and schema validation. Inspect the pinned provider documentation/schema for
   import identifiers, disk defaults and LXC template requirements. Resolve
   validation failures without inventing volume names or fetching template 999.
5. Load approved audit and management credentials from the existing external
   credential files with shell tracing disabled. Confirm restricted ACLs cover
   the selected existing resource without moving it into a resource pool.
6. Inspect current state membership and confirm the selected node/ID is not
   already managed under another address/state. Confirm the supplied live
   configuration is still current and resolve the unverified parameters above.
7. Import one approved resource at a time using its exact resource address and
   the node/ID identifier confirmed for 0.111.1 (expected `dtcode/103`,
   `dtcode/105`, `dtcode/106`, `dtcode/107`, or `dtcode/102`). Import writes state;
   it does not authorize apply or recreation.
8. After each import, inspect a complete saved plan, including unrelated
   configured resources. Stop for any unexpected change, replacement, disk
   operation, cloud-init reset or protection drift. Reconcile definitions and
   review before considering the next import. Apply requires separate approval.
