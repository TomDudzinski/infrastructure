# forgejo01

## Identity and purpose

| Property | Value |
|---|---|
| Host | `dtcode` |
| Type | VM |
| ID | `105` |
| Address | `192.168.55.22` |
| Purpose | Forgejo Git service |
| Historical source | `forgejo.tf` |
| Historical allocation | 1 core, 1024 MiB RAM |
| Historical clone source | Full clone of template ID `999` |
| Network | VirtIO on `vmbr0`; `192.168.55.22/24`; gateway `192.168.55.1` |
| Startup | Enabled at host boot; order 3; delay 20 seconds |

## Evidence and management status

This is an existing legacy resource recorded in the current inventory on `2026-08-17`. Its configuration below was recovered from historical source code in `/home/tom/Projekty/infrastructure-old/homelab/terraform/environments/dev/` during a local documentation review on `2026-10-04`.

- Current Terraform: no resource definition in this repository; not managed according to existing documentation. Current state membership was not independently checked.
- Current Ansible: no inventory entry or dedicated playbook for this guest.
- Current scope: documented legacy resource; historical Terraform is evidence only, not an active management mechanism.
- Planned: verify configuration, dependencies, persistent data and backup coverage before proposing any controlled Terraform import or Ansible adoption. No import or rebuild is authorized by this documentation.

Historical code records intended configuration, not proof of successful provisioning or current runtime state. No infrastructure connections or commands were executed in this review. Secret values and keys are intentionally excluded.

## Historical configuration and persistent data

Historical Terraform used wait/retry resources and `local-exec` over SSH to install Docker and Compose, write `/opt/forgejo/docker-compose.yml` and start the stack. The image was `codeberg.org/forgejo/forgejo:10`, database type SQLite, HTTP port `3000:3000` and Git SSH port `222:22`.

The named Docker volume `forgejo-data` was mounted at `/data`, holding repositories, application configuration and the SQLite database. The resolved volume name and host filesystem location must be verified; do not assume data resides under `/opt/forgejo`. Repository data, database, configuration and access credentials require coordinated backup and restore verification.

Historical provisioning forced public resolvers `8.8.8.8`/`8.8.4.4` for Docker, changed `/etc/resolv.conf` and disabled Docker IPv6. These are historical workarounds, not the current recommended network policy. Current documentation identifies Forgejo as the primary Git service at `git.home.lab`; the DNS/proxy mapping was not checked in this review.

## Remaining verification

Confirm actual guest sizing and disk layout, running service versions, configuration drift, dependencies, firewall rules, data paths and backup/restore coverage in a separately authorized operational review. Historical VM definitions do not specify a disk size; clone-derived storage must not be inferred. Preserve existing IDs, IPs and data.

See [inventory](../../INVENTORY.md), [host](../hosts/dtcode.md) and [network](../network/NETWORK.md).
