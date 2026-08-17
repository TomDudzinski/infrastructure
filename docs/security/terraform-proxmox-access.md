# Terraform Proxmox access

## Purpose

Terraform on `iza` connects to both Proxmox environments through HTTPS on TCP port `8006`.

The initial connection is deliberately read-only. It verifies provider compatibility and supports inventory work without granting Terraform permission to modify infrastructure.

## Environments

| Provider alias | Host | Endpoint | Proxmox version | Current access |
|---|---|---|---|---|
| `proxmox.dtcode` | `dtcode` | `https://192.168.55.6:8006/` | `8.2.2` | `PVEAuditor` |
| `proxmox.dom` | `dom` | `https://192.168.55.3:8006/` | `9.2.2` | `PVEAuditor` |

`dtcode` is a single-node cluster named `test`. `dom` is a standalone host.

## Provider

The configuration uses `bpg/proxmox` pinned to version `0.111.1`.

The version is pinned exactly because the provider remains on the `0.x` release line and does not guarantee compatibility between minor versions. Provider upgrades require a separate review and a saved, inspected plan.

## Audit identities

Each Proxmox environment has a separate local API identity:

```text
terraform-audit@pve!provider
```

The backing user and privilege-separated token both receive `PVEAuditor` at `/` with propagation enabled. Effective permissions are the intersection of the user and token permissions.

The token cannot manage, create, modify, start, stop, migrate, or delete VM and LXC resources.

## Secret storage

Token responses are stored only on `iza`:

```text
~/.config/homelab/terraform/dtcode-audit-token.json
~/.config/homelab/terraform/dom-audit-token.json
```

Requirements:

- directory mode `700`;
- file mode `600`;
- ownership by `tom`;
- exclusion from Git;
- no token values in documentation, terminal transcripts, plans, or commit history.

The loader script exports sensitive Terraform variables into the current shell:

```bash
source ./scripts/load-proxmox-audit-env.sh
```

Do not run `env`, `export -p`, or shell tracing while credentials are loaded.

## TLS bootstrap

Both Proxmox endpoints currently use certificates that are not trusted by the operating-system CA store. Their SHA-256 fingerprints were verified out of band against values read directly from the Proxmox hosts on `2026-08-17`.

| Host | SHA-256 certificate fingerprint |
|---|---|
| `dtcode` | `F4:85:DA:5C:0E:9B:FA:6C:8E:DB:59:49:8A:FC:1E:91:01:43:8F:55:D7:61:C2:27:F9:6C:A7:37:A0:9D:8B:86` |
| `dom` | `45:CC:82:CD:84:FA:B8:FA:36:4F:8A:34:C6:91:C9:DC:BE:1F:D8:13:1B:42:5A:B2:9E:44:97:5C:6B:BE:88:6F` |

The provider temporarily uses `insecure = true`. The target state is trusted local PKI with certificate verification enabled.

## Safe verification workflow

Run from the repository root on `iza`:

```bash
source ./scripts/load-proxmox-audit-env.sh
terraform -chdir=terraform init
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
terraform -chdir=terraform plan -input=false -lock=false
```

The current configuration contains data sources only. It reads the version from both Proxmox APIs and must not propose infrastructure changes.

Do not run `terraform apply`. Applying the audit configuration would only persist output values to local state, which is not needed.

## State

No previous Terraform code or state was found under `/opt/ai/projects` during the inventory on `2026-08-17`.

The current audit configuration has not been applied and has no state. Before managing resources, the project must define:

- state location;
- encryption and access control;
- locking;
- backup and recovery;
- controlled import of existing resources.

## Management-token design

Do not broaden the audit token. Future write access must use a separate identity and token with a reviewed custom role.

The role must be derived from the exact resources and operations being introduced. It must not receive `Administrator` merely to avoid permission analysis.

## Rotation and revocation

Token values are displayed only once by Proxmox. If a value is lost or exposed, revoke the token and create a new one.

Revocation must be performed separately on each environment. Confirm console or administrative access before revoking remote credentials.

After OpenBao is deployed, migrate the API credentials into OpenBao and remove the local bootstrap files after verification.
