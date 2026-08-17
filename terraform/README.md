# Terraform

## Purpose

Terraform manages the lifecycle of Proxmox infrastructure resources, including:

- virtual machines and containers;
- CPU and memory allocation;
- disks and storage assignments;
- network devices;
- cloud-init configuration;
- controlled infrastructure lifecycle operations.

Operating-system and application configuration belongs to Ansible or Docker Compose rather than Terraform.

## Execution host

Terraform runs from the `iza` host.

| Property | Value |
|---|---|
| Operating system | Ubuntu 26.04 LTS (`resolute`) |
| Architecture | `amd64` |
| Terraform version | `1.15.8` |
| Installation source | Official HashiCorp APT repository |

Install or verify Terraform with:

```bash
make install-terraform
terraform version
```

## Proxmox environments

The target configuration will manage two existing Proxmox VE hosts:

| Provider alias | Host | Address | Proxmox version |
|---|---|---|---|
| `proxmox.dtcode` | `dtcode` | `192.168.55.6` | `8.2.2` |
| `proxmox.dom` | `dom` | `192.168.55.3` | `9.2.2` |

The provider implementation and version constraint must be selected only after the existing Terraform configuration and state have been inventoried.

## Authentication

Terraform connects to the Proxmox API over HTTPS on TCP port `8006`. It does not use the SSH automation key for normal Proxmox resource management.

Each Proxmox host must have a dedicated Terraform API token. Tokens must:

- be separate from personal administrator credentials;
- use the minimum privileges required by the managed resources;
- be supplied outside Git;
- never be written directly in `*.tf` files;
- be migrated to OpenBao when the secrets platform is available.

Local bootstrap values may be supplied through protected environment files or environment variables. Files containing credentials must have mode `600` and must be excluded from Git.

## State safety

Terraform state can contain sensitive values even when variables are marked as sensitive. State files and plan files must not be committed to Git.

Before the backend architecture is approved:

- do not create a new production state blindly;
- locate and inspect any existing state without publishing its contents;
- define state backup and recovery;
- define state locking;
- verify that `.gitignore` excludes state, plan, and local credential files.

## Existing infrastructure

The Proxmox hosts, virtual machines, and containers already exist. They must not be recreated merely to bring them under Terraform management.

Required workflow:

1. Inventory the existing Terraform code and state.
2. Inventory Proxmox resources and dependencies.
3. Select and pin the provider version.
4. Configure read-only connectivity where possible.
5. Import existing resources deliberately.
6. Review every plan before applying changes.
7. Back up affected systems before lifecycle changes.

Do not run `terraform apply` until the plan has been reviewed and the effect on existing resources is understood.

## Planned structure

The directory structure will be defined after the existing configuration has been inventoried. It should separate reusable configuration from environment-specific values and keep secrets outside the repository.

The likely initial files are:

```text
terraform/
├── versions.tf
├── providers.tf
├── variables.tf
├── outputs.tf
└── README.md
```

This structure is a plan, not confirmation that these files already exist.

## Next steps

1. Locate any existing Terraform code and state.
2. Review `.gitignore` for Terraform artifacts.
3. Select the Proxmox provider and version constraint.
4. Design least-privilege API roles and tokens for both hosts.
5. Configure provider aliases without committing credentials.
6. Run `terraform init`, `terraform fmt -check`, and `terraform validate`.
7. Produce and review a non-destructive plan before any apply.
