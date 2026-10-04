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

- Current Terraform: definition in `terraform/dtcode_forgejo01.tf`; imported into the current state on `2026-10-04` according to the administrator. Hardware matches the previously verified live configuration; remaining provider/state differences are recorded in the [adoption review](../operations/dtcode-adoption-2026-10-04.md).
- Current Ansible: no inventory entry or dedicated playbook for this guest.
- Current scope: adopted existing resource managed by current Terraform state; application configuration is not managed by current Ansible.
- Next review: remaining provider/state drift, service configuration, dependencies, persistent data and backup/restore coverage. Ansible adoption requires a separate proposal; no apply or rebuild is authorized.

Historical code records intended configuration, not proof of successful provisioning or current runtime state. No infrastructure connections or commands were executed in this review. Secret values and keys are intentionally excluded.

## Historical configuration and persistent data

Historical Terraform used wait/retry resources and `local-exec` over SSH to install Docker and Compose, write `/opt/forgejo/docker-compose.yml` and start the stack. The image was `codeberg.org/forgejo/forgejo:10`, database type SQLite, HTTP port `3000:3000` and Git SSH port `222:22`.

The named Docker volume `forgejo-data` was mounted at `/data`, holding repositories, application configuration and the SQLite database. The resolved volume name and host filesystem location must be verified; do not assume data resides under `/opt/forgejo`. Repository data, database, configuration and access credentials require coordinated backup and restore verification.

Historical provisioning forced public resolvers `8.8.8.8`/`8.8.4.4` for Docker, changed `/etc/resolv.conf` and disabled Docker IPv6. These are historical workarounds, not the current recommended network policy. Current documentation identifies Forgejo as the primary Git service at `git.home.lab`; the DNS/proxy mapping was not checked in this review.

## Remaining verification

Current hardware sizing is declared in Terraform and was previously verified by the administrator. Running service versions, guest configuration drift, dependencies, firewall rules, data paths and application backup/restore coverage still require a separately authorized operational review. Preserve existing IDs, IPs and data.

See [inventory](../../INVENTORY.md), [host](../hosts/dtcode.md) and [network](../network/NETWORK.md).
