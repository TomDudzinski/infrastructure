# home01

## Identity and purpose

| Property | Value |
|---|---|
| Host | `dtcode` |
| Type | VM |
| ID | `103` |
| Address | `192.168.55.20` |
| Purpose | Homepage dashboard |
| Historical source | `homepage.tf` |
| Historical allocation | 1 core, 1024 MiB RAM |
| Historical clone source | Full clone of template ID `999` |
| Network | VirtIO on `vmbr0`; `192.168.55.20/24`; gateway `192.168.55.1` |
| Startup | Enabled at host boot; order 2; delay 20 seconds |

## Evidence and management status

This is an existing legacy resource recorded in the current inventory on `2026-08-17`. Its configuration below was recovered from historical source code in `/home/tom/Projekty/infrastructure-old/homelab/terraform/environments/dev/` during a local documentation review on `2026-10-04`.

- Current Terraform: no resource definition in this repository; not managed according to existing documentation. Current state membership was not independently checked.
- Current Ansible: no inventory entry or dedicated playbook for this guest.
- Current scope: documented legacy resource; historical Terraform is evidence only, not an active management mechanism.
- Planned: verify configuration, dependencies, persistent data and backup coverage before proposing any controlled Terraform import or Ansible adoption. No import or rebuild is authorized by this documentation.

Historical code records intended configuration, not proof of successful provisioning or current runtime state. No infrastructure connections or commands were executed in this review. Secret values and keys are intentionally excluded.

## Historical configuration and persistent data

Historical Terraform used a wait resource and `local-exec` over SSH to install Docker and run `ghcr.io/gethomepage/homepage:latest` as `homepage`, with port `3000:3000` and `unless-stopped` restart policy. Docker IPv6 was disabled in the historical provisioning.

Persistent configuration was bind-mounted from `/opt/homepage/config` to `/app/config`: `settings.yaml`, `services.yaml`, `bookmarks.yaml` and `widgets.yaml`. The initial dashboard linked to Proxmox and Technitium DNS. Its Proxmox link used `qnap.lab`, an ambiguous historical value that is not evidence of a current DNS mapping. Allowed hosts included `192.168.55.20:3000`, `home.lab:3000` and `home.home.lab:3000`; current DNS/proxy mappings and dashboard customizations remain unverified.

## Remaining verification

Confirm actual guest sizing and disk layout, running service versions, configuration drift, dependencies, firewall rules, data paths and backup/restore coverage in a separately authorized operational review. Historical VM definitions do not specify a disk size; clone-derived storage must not be inferred. Preserve existing IDs, IPs and data.

See [inventory](../../INVENTORY.md), [host](../hosts/dtcode.md) and [network](../network/NETWORK.md).
