# Terraform Proxmox access

## Purpose

Terraform on `iza` connects to both Proxmox environments through HTTPS on TCP port `8006`.

Terraform uses separate read-only and restricted management identities.

Read-only access supports inventory and verification. Management access is limited to explicitly approved resource pools, storage, nodes and networks.

## Environments

| Provider alias | Host | Endpoint | Proxmox version | Access |
|---|---|---|---|---|
| `proxmox.dtcode` | `dtcode` | `https://192.168.55.6:8006/` | `8.2.2` | Read-only audit |
| `proxmox.dom` | `dom` | `https://192.168.55.3:8006/` | `9.2.2` | Read-only audit |
| `proxmox.dtcode_manage` | `dtcode` | `https://192.168.55.6:8006/` | `8.2.2` | Restricted management |
| `proxmox.dom_manage` | `dom` | `https://192.168.55.3:8006/` | `9.2.2` | Restricted management |

`dtcode` is a single-node cluster named `test`. `dom` is a standalone host.

## Provider

The configuration uses `bpg/proxmox` pinned to version `0.111.1`.

The version is pinned exactly because the provider remains on the `0.x` release line and does not guarantee compatibility between minor versions.

Provider upgrades require:

1. a separate compatibility review;
2. initialization with the new provider version;
3. validation;
4. an inspected saved plan;
5. explicit approval before applying changes.

## Identity separation

Terraform uses separate identities for audit and management operations.

The audit identity must not be expanded to support infrastructure changes. The management identity must be used only when a reviewed operation requires write access.

## Audit identities

Each Proxmox environment has a local audit identity:

```text
terraform-audit@pve!provider
```

The backing user and privilege-separated token both receive `PVEAuditor` at `/` with propagation enabled.

Effective token permissions are the intersection of the backing user permissions and the separated token permissions.

The audit token cannot create, modify, start, stop, migrate or delete VM and LXC resources.

## Management identities

Each Proxmox environment has a separate privilege-separated management identity:

```text
terraform-manage@pve!provider
```

The backing user and separated token receive identical ACL assignments.

The management identity does not receive the built-in `Administrator` role.

## Resource boundaries

Management access is restricted to the following paths:

| Path | Purpose |
|---|---|
| `/pool/terraform-managed` | Lifecycle management for approved Terraform resources |
| `/storage/local` | Cloud image, import and template allocation |
| `/storage/local-lvm` | Managed VM disk allocation |
| `/nodes/<node>` | Required node inspection and network access |
| `/sdn/zones/localnetwork/vmbr0` | Use of the approved Proxmox bridge |

Resources created by Terraform must be assigned to:

```text
terraform-managed
```

Existing resources outside this pool must not be modified or imported without a separate review.

## Custom roles

### TerraformVMManager

This role provides the approved VM lifecycle and configuration permissions:

```text
Pool.Audit
Sys.Audit
VM.Allocate
VM.Audit
VM.Clone
VM.Config.CDROM
VM.Config.CPU
VM.Config.Cloudinit
VM.Config.Disk
VM.Config.HWType
VM.Config.Memory
VM.Config.Network
VM.Config.Options
VM.PowerMgmt
```

The role is assigned only at:

```text
/pool/terraform-managed
```

### TerraformStorageManager

This role provides:

```text
Datastore.AllocateSpace
Datastore.AllocateTemplate
Datastore.Audit
```

The role is assigned only at:

```text
/storage/local
/storage/local-lvm
```

### TerraformNodeAuditor

The node role is version-specific.

On Proxmox VE 8.2 running on `dtcode`, it provides:

```text
Sys.Audit
```

On Proxmox VE 9.2 running on `dom`, it provides:

```text
Sys.AccessNetwork
Sys.Audit
```

Proxmox VE 9 requires `Sys.AccessNetwork` for URL metadata queries and storage downloads.

The broader `Sys.Modify` privilege is not granted merely to support image downloads.

### TerraformNetworkUser

This role provides:

```text
SDN.Use
```

It is assigned only at:

```text
/sdn/zones/localnetwork/vmbr0
```

This permission allows managed VMs to use `vmbr0` without granting unrestricted SDN administration.

## Known Proxmox permission requirements

### Image metadata and download

Proxmox VE 9 checks `Sys.AccessNetwork` when Terraform queries URL metadata or requests a storage download.

This permission is assigned on the specific node instead of granting `Sys.Modify` at `/`.

### VM creation

VM creation requires the approved VM permissions at the resource pool and storage permissions at the selected storage paths.

### Network attachment

Attaching a managed VM to `vmbr0` requires `SDN.Use` at the corresponding local network path.

### Startup configuration

Some detailed Proxmox startup-order settings require `Sys.Modify` at `/`.

The `mysql01` configuration avoids this broad permission. Automatic VM startup is enabled with `on_boot`, while detailed startup ordering is not managed.

## Secret storage

Token responses are stored only on `iza`:

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

Requirements:

- directory mode `700`;
- file mode `600`;
- ownership by `tom`;
- exclusion from Git;
- no token values in documentation;
- no token values in terminal transcripts;
- no token values in saved plans or commit history.

## Credential loading

Load audit credentials from the repository root:

```bash
source ./scripts/load-proxmox-audit-env.sh
```

Load management credentials only for an approved management operation:

```bash
source ./scripts/load-proxmox-manage-env.sh
```

Do not run the following while credentials are loaded:

```text
env
export -p
set -x
```

The loader scripts must never print token values.

## Token creation

Audit identities are created separately on each Proxmox environment:

```bash
./scripts/create-proxmox-audit-token.sh dtcode
./scripts/create-proxmox-audit-token.sh dom
```

Management identities are also created separately:

```bash
./scripts/create-proxmox-management-token.sh dtcode
./scripts/create-proxmox-management-token.sh dom
```

The management script creates the reviewed custom roles, resource pool, user, privilege-separated token and ACL assignments.

The script must stop instead of modifying an unexpected existing identity or secret file.

## TLS bootstrap

Both Proxmox endpoints currently use certificates that are not trusted by the `iza` operating-system CA store.

Their SHA-256 fingerprints were verified out of band against values read directly from the Proxmox hosts on `2026-08-17`.

| Host | SHA-256 certificate fingerprint |
|---|---|
| `dtcode` | `F4:85:DA:5C:0E:9B:FA:6C:8E:DB:59:49:8A:FC:1E:91:01:43:8F:55:D7:61:C2:27:F9:6C:A7:37:A0:9D:8B:86` |
| `dom` | `45:CC:82:CD:84:FA:B8:FA:36:4F:8A:34:C6:91:C9:DC:BE:1F:D8:13:1B:42:5A:B2:9E:44:97:5C:6B:BE:88:6F` |

The provider temporarily uses:

```hcl
insecure = true
```

This disables normal certificate-chain validation. The fingerprints must be checked again if a certificate changes unexpectedly.

The target state is trusted local PKI with certificate verification enabled.

## Terraform state

The current Terraform backend is local:

```text
terraform/state/terraform.tfstate
```

The state directory is restricted to the `tom` account. State files are excluded from Git.

Terraform state can contain sensitive values even when input variables are marked as sensitive.

The local backend does not provide remote locking. Terraform operations must be executed from `iza`, one at a time.

The current state tracks newly created resources on `dom`. Existing `dtcode` resources remain outside the state.

## State backup

The infrastructure repository, including ignored Terraform state, is backed up to the independent QNAP Restic repository:

```text
/mnt/qnap-backup/AI/iza/restic
```

Run the backup:

```bash
./scripts/backup-config-qnap.sh
```

A Restic repository check and an actual restore test were completed successfully on `2026-08-17`.

A future Terraform backend should provide encryption, locking, access control, versioning and documented recovery.

## Safe verification workflow

Run from the repository root:

```bash
source ./scripts/load-proxmox-audit-env.sh
source ./scripts/load-proxmox-manage-env.sh

terraform -chdir=terraform init -reconfigure -input=false
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
terraform -chdir=terraform plan -input=false -lock=false
```

A normal plan after a successful deployment should report no infrastructure changes.

## Saved-plan workflow

For an approved change, create a saved plan:

```bash
terraform -chdir=terraform plan \
  -input=false \
  -out=mysql01.tfplan
```

Inspect it:

```bash
terraform -chdir=terraform show mysql01.tfplan
```

Apply only the inspected plan:

```bash
terraform -chdir=terraform apply mysql01.tfplan
```

Remove it after use:

```bash
rm -f -- terraform/mysql01.tfplan
```

Saved plans can contain sensitive values and must not be committed.

## Managed resources

The current state manages the following resources on `dom`:

```text
proxmox_download_file.dom_ubuntu_2404_cloud_image
proxmox_virtual_environment_vm.mysql01
```

The VM is assigned to the `terraform-managed` resource pool.

Existing resources on `dtcode` have not been imported.

## Existing-resource import policy

Before importing an existing resource:

1. document its live configuration;
2. document dependencies and persistent data;
3. verify backup coverage;
4. create an exact Terraform definition;
5. import one selected resource deliberately;
6. inspect the complete plan;
7. resolve all drift;
8. apply only after explicit approval.

Existing infrastructure must not be recreated merely to bring it under Terraform management.

## Rotation and revocation

Token values are displayed only once by Proxmox.

If a value is lost or exposed:

1. confirm console or administrative access;
2. revoke the affected token;
3. create a replacement token;
4. update the protected local secret file;
5. verify access;
6. remove the old credential.

Rotation and revocation must be performed separately on each Proxmox environment.

Do not revoke remote credentials before confirming an alternative administrative access path.

## Future secret management

After OpenBao is deployed:

1. migrate Proxmox API credentials into OpenBao;
2. verify Terraform access through the new mechanism;
3. verify recovery when OpenBao is unavailable;
4. securely remove the local bootstrap token files;
5. document rotation and emergency recovery procedures.