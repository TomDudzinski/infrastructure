# Current Status

## Current phase

Proxmox inventory and read-only Terraform bootstrap.

## Working

- Proxmox VE 8.2.2 on `dtcode`
- Proxmox VE 9.2.2 on `dom`
- SSH automation from `iza` to both Proxmox hosts
- Terraform 1.15.8 on `iza`
- `bpg/proxmox` provider 0.111.1
- read-only Terraform API connectivity to both Proxmox environments
- AI server `iza`
- QNAP
- Docker
- Ollama
- Open WebUI
- code-server
- JupyterLab
- Restic local backup
- QNAP NFS access

## Terraform status

- separate privilege-separated `PVEAuditor` tokens exist on `dtcode` and `dom`;
- token secrets are stored locally on `iza` outside Git;
- both API certificates were verified by SHA-256 fingerprint;
- provider aliases `proxmox.dtcode` and `proxmox.dom` are configured;
- a read-only plan successfully reported Proxmox versions `8.2.2` and `9.2.2`;
- no Terraform state currently exists;
- no previous Terraform code or state was found under `/opt/ai/projects`;
- no existing VM or LXC has been imported into the new configuration;
- `terraform apply` is not approved at this phase.

## Existing infrastructure requiring controlled import review

The following active resources on `dtcode` carry a `terraform` tag, but their previous Terraform state was not found:

- `dns01`
- `home01`
- `forgejo01`
- `npm01`
- `tailscale-router`

The remaining stopped resources are templates `101` and `999`. Their relationship and intended future use require verification before either template is managed by Terraform.

Obsolete stopped VMs `104`, `201`, and `202` were removed from `dtcode` on `2026-08-17`.

## Current task

Design the Terraform state storage, locking, backup, restore, and recovery model before introducing managed infrastructure resources.

## Next tasks

1. Define and document separate Terraform state boundaries for `dtcode` and `dom`.
2. Configure state storage outside the Git repository.
3. Add encrypted state backup to the existing Restic and QNAP workflow.
4. Perform and document a Terraform state restore test.
5. Design a new minimal disposable VM for controlled Terraform lifecycle testing.
6. Design a separate least-privilege Proxmox management role and token.
7. Create, inspect, modify, and destroy the disposable VM through an explicitly approved Terraform workflow.
8. Document the full configuration and dependencies of each existing production guest before considering controlled imports.
9. Finish the remaining QNAP Restic backup work.
10. Design OpenBao.
11. Create the Ansible structure.
