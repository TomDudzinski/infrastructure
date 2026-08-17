# Terraform

## Purpose

Terraform manages the lifecycle of Proxmox infrastructure resources, including VM and LXC allocation, compute, disks, networking, cloud-init, and controlled lifecycle operations.

Operating-system and application configuration belongs to Ansible or Docker Compose rather than Terraform.

## Current status

Terraform currently provides read-only connectivity from `iza` to both Proxmox environments. The configuration contains data sources only and does not manage infrastructure resources.

| Property | Value |
|---|---|
| Execution host | `iza` |
| Terraform version | `1.15.8` |
| Provider | `bpg/proxmox` `0.111.1` |
| State | Not created |
| Apply status | Not approved |

## Proxmox environments

| Provider alias | Host | Endpoint | Proxmox version | Access |
|---|---|---|---|---|
| `proxmox.dtcode` | `dtcode` | `https://192.168.55.6:8006/` | `8.2.2` | `PVEAuditor` |
| `proxmox.dom` | `dom` | `https://192.168.55.3:8006/` | `9.2.2` | `PVEAuditor` |

Provider `0.111.1` is pinned exactly. Upgrades require a separate compatibility review because the provider remains on the `0.x` release line.

## Files

```text
terraform/
├── .terraform.lock.hcl
├── data.tf
├── outputs.tf
├── providers.tf
├── README.md
├── variables.tf
└── versions.tf
```

The `.terraform/` working directory, state, plan files, and local variable files are excluded from Git. The dependency lock file is committed.

## Credentials

Credentials are not stored in Terraform files. Load the protected audit tokens into the current shell:

```bash
source ./scripts/load-proxmox-audit-env.sh
```

Do not display the resulting environment variables. See [Terraform Proxmox access](../docs/security/terraform-proxmox-access.md).

## Safe verification

Run from the repository root:

```bash
source ./scripts/load-proxmox-audit-env.sh
terraform -chdir=terraform init
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
terraform -chdir=terraform plan -input=false -lock=false
```

The plan must read `proxmox_version` for both provider aliases and report no infrastructure changes.

Do not run `terraform apply`. Applying the current configuration would create a local state only to persist output values and provides no operational benefit.

## TLS

The current Proxmox certificates were verified manually by SHA-256 fingerprint, but they are not trusted by the `iza` operating-system CA store. The provider temporarily uses `insecure = true`.

The target state is trusted local PKI with certificate verification enabled.

## Existing infrastructure

The Proxmox hosts, VMs, containers, and templates already exist. They must not be recreated merely to bring them under Terraform management.

No previous Terraform code or state was found under `/opt/ai/projects` on `2026-08-17`. Several existing guests on `dtcode` carry a `terraform` tag, so previous management history exists but cannot currently be reconstructed from state.

Required workflow before management:

1. Document each existing resource and its dependencies.
2. Define state storage, locking, backup, and recovery.
3. Design a separate least-privilege management role and token.
4. Reconstruct exact Terraform configuration for one selected resource.
5. Back up the affected workload.
6. Import the resource deliberately.
7. Review the complete plan and resolve all drift.
8. Apply only after explicit approval.

## State safety

Terraform state can contain sensitive values even when variables are marked as sensitive. State, saved plans, and credential files must never be committed to Git.

Before the first import or apply, document:

- backend location;
- encryption and access control;
- locking behavior;
- backup schedule;
- restore procedure and test;
- recovery procedure if OpenBao or the backend is unavailable.

## Next step

Complete guest-level inventory on `dtcode`, beginning with one low-risk stopped resource. Do not import active infrastructure until its configuration, persistent data, backup, and dependencies are understood.
