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

Additional stopped VMs and templates also require classification before any import decision.

## Current task

Document the verified Proxmox inventory and establish a safe Terraform baseline without modifying existing infrastructure.

## Next tasks

1. Commit the read-only Terraform bootstrap and documentation.
2. Document the full configuration and dependencies of each existing guest.
3. Decide the Terraform state backend, locking, backup, and recovery model.
4. Design a separate least-privilege management role and token.
5. Select one low-risk resource for a controlled import test.
6. Finish QNAP Restic backup.
7. Design OpenBao.
8. Create the Ansible structure.
