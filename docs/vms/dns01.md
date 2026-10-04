# dns01

## Identity and purpose

| Property | Value |
|---|---|
| Host | `dtcode` |
| Type | LXC |
| ID | `102` |
| Address | `192.168.55.10` |
| Purpose | Technitium DNS |
| Historical source | `technitium-dns.tf` |
| Historical platform | Unprivileged Ubuntu 22.04 LXC; nesting enabled |
| Historical allocation | 2 cores, 2048 MiB RAM, 20 GiB disk on `local-lvm` |
| Network | `eth0` on `vmbr0`; `192.168.55.10/24`; gateway `192.168.55.1` |
| Startup | Enabled at host boot; order 1; delay 20 seconds |

## Evidence and management status

This is an existing legacy resource recorded in the current inventory on `2026-08-17`. Its configuration below was recovered from historical source code in `/home/tom/Projekty/infrastructure-old/homelab/terraform/environments/dev/` during a local documentation review on `2026-10-04`.

- Current Terraform: definition in `terraform/dtcode_dns01.tf`; imported into the current state on `2026-10-04` according to the administrator. Hardware matches the previously verified live configuration; remaining provider/state differences are recorded in the [adoption review](../operations/dtcode-adoption-2026-10-04.md).
- Current Ansible: no inventory entry or dedicated playbook for this guest.
- Current scope: adopted existing resource managed by current Terraform state; application configuration is not managed by current Ansible.
- Next review: remaining provider/state drift, service configuration, dependencies, persistent data and backup/restore coverage. Ansible adoption requires a separate proposal; no apply or rebuild is authorized.

Historical code records intended configuration, not proof of successful provisioning or current runtime state. No infrastructure connections or commands were executed in this review. Secret values and keys are intentionally excluded.

## Historical configuration and persistent data

Historical Terraform used `remote-exec` over SSH to install Docker and run `technitium/dns-server:latest` as `technitium-dns`, with host networking and `unless-stopped` restart policy. This was imperative provisioning, not current Ansible management.

Persistent configuration was bind-mounted from `/opt/technitium/config` to `/etc/dns`. DNS zones, settings and any associated credentials must be preserved; actual contents, upstream resolvers, zones and backup coverage remain unverified. Historical Homepage configuration linked to the DNS administration interface on port `5380`; current listeners and access rules are not confirmed.

## Remaining verification

Current hardware sizing is declared in Terraform and was previously verified by the administrator. Running service versions, guest configuration drift, dependencies, firewall rules, data paths and application backup/restore coverage still require a separately authorized operational review. Preserve existing IDs, IPs and data.

See [inventory](../../INVENTORY.md), [host](../hosts/dtcode.md) and [network](../network/NETWORK.md).
