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

- Current Terraform: no resource definition in this repository; not managed according to existing documentation. Current state membership was not independently checked.
- Current Ansible: no inventory entry or dedicated playbook for this guest.
- Current scope: documented legacy resource; historical Terraform is evidence only, not an active management mechanism.
- Planned: verify configuration, dependencies, persistent data and backup coverage before proposing any controlled Terraform import or Ansible adoption. No import or rebuild is authorized by this documentation.

Historical code records intended configuration, not proof of successful provisioning or current runtime state. No infrastructure connections or commands were executed in this review. Secret values and keys are intentionally excluded.

## Historical configuration and persistent data

Historical Terraform used `remote-exec` over SSH to install Docker and run `technitium/dns-server:latest` as `technitium-dns`, with host networking and `unless-stopped` restart policy. This was imperative provisioning, not current Ansible management.

Persistent configuration was bind-mounted from `/opt/technitium/config` to `/etc/dns`. DNS zones, settings and any associated credentials must be preserved; actual contents, upstream resolvers, zones and backup coverage remain unverified. Historical Homepage configuration linked to the DNS administration interface on port `5380`; current listeners and access rules are not confirmed.

## Remaining verification

Confirm actual guest sizing and disk layout, running service versions, configuration drift, dependencies, firewall rules, data paths and backup/restore coverage in a separately authorized operational review. Preserve existing IDs, IPs and data.

See [inventory](../../INVENTORY.md), [host](../hosts/dtcode.md) and [network](../network/NETWORK.md).
