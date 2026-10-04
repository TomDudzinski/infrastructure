# npm01

## Identity and purpose

| Property | Value |
|---|---|
| Host | `dtcode` |
| Type | VM |
| ID | `106` |
| Address | `192.168.55.23` |
| Purpose | Nginx Proxy Manager reverse proxy and TLS |
| Historical source | `npm.tf` |
| Historical allocation | 1 core, 1024 MiB RAM |
| Historical clone source | Full clone of template ID `999` |
| Network | VirtIO on `vmbr0`; `192.168.55.23/24`; gateway `192.168.55.1` |
| Startup | Enabled at host boot; order 1; delay 20 seconds |

## Evidence and management status

This is an existing legacy resource recorded in the current inventory on `2026-08-17`. Its configuration below was recovered from historical source code in `/home/tom/Projekty/infrastructure-old/homelab/terraform/environments/dev/` during a local documentation review on `2026-10-04`.

- Current Terraform: no resource definition in this repository; not managed according to existing documentation. Current state membership was not independently checked.
- Current Ansible: no inventory entry or dedicated playbook for this guest.
- Current scope: documented legacy resource; historical Terraform is evidence only, not an active management mechanism.
- Planned: verify configuration, dependencies, persistent data and backup coverage before proposing any controlled Terraform import or Ansible adoption. No import or rebuild is authorized by this documentation.

Historical code records intended configuration, not proof of successful provisioning or current runtime state. No infrastructure connections or commands were executed in this review. Secret values and keys are intentionally excluded.

## Historical configuration and persistent data

Historical Terraform used wait/retry resources and `local-exec` over SSH to install Docker, Compose and OpenSSL, write `/opt/npm/docker-compose.yml` and start `jc21/nginx-proxy-manager:latest`. Published ports were `80`, `443` and administration port `81`.

Persistent paths in that Compose stack:

| Host path | Container path | Purpose |
|---|---|---|
| `/opt/npm/data` | `/data` | Application database, proxy hosts and configuration |
| `/opt/npm/letsencrypt` | `/etc/letsencrypt` | Certificate-related state |
| `/opt/npm/ssl` | `/etc/ssl/homelab` (read-only) | Historical local CA and wildcard TLS material |

Historical provisioning generated a local CA and certificates for `*.home.lab` and `home.lab` in `/opt/npm/ssl`. This does not establish their current validity or their relationship to the subsequently documented OpenBao PKI. Private material must remain outside Git; only paths and purposes are recorded here.

Historical provisioning also changed `/etc/resolv.conf`, configured Docker public resolvers `8.8.8.8`/`8.8.4.4` and disabled Docker IPv6. Current proxy routes, certificates, data contents and backup/restore coverage remain unverified. Existing OpenBao documentation records a later HTTPS proxy path through NPM; it was not retested locally.

## Remaining verification

Confirm actual guest sizing and disk layout, running service versions, configuration drift, dependencies, firewall rules, data paths and backup/restore coverage in a separately authorized operational review. Historical VM definitions do not specify a disk size; clone-derived storage must not be inferred. Preserve existing IDs, IPs and data.

See [inventory](../../INVENTORY.md), [host](../hosts/dtcode.md) and [network](../network/NETWORK.md).
