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

- Current Terraform: definition in `terraform/dtcode_home01.tf`; imported into the current state on `2026-10-04` according to the administrator. Hardware matches the previously verified live configuration; remaining provider/state differences are recorded in the [adoption review](../operations/dtcode-adoption-2026-10-04.md).
- Current Ansible: no inventory entry or dedicated playbook for this guest.
- Current scope: adopted existing resource managed by current Terraform state; application configuration is not managed by current Ansible.
- Next review: remaining provider/state drift, service configuration, dependencies, persistent data and backup/restore coverage. Ansible adoption requires a separate proposal; no apply or rebuild is authorized.

Historical code records intended configuration, not proof of successful provisioning or current runtime state. No infrastructure connections or commands were executed in this review. Secret values and keys are intentionally excluded.

## Historical configuration and persistent data

Historical Terraform used a wait resource and `local-exec` over SSH to install Docker and run `ghcr.io/gethomepage/homepage:latest` as `homepage`, with port `3000:3000` and `unless-stopped` restart policy. Docker IPv6 was disabled in the historical provisioning.

Persistent configuration was bind-mounted from `/opt/homepage/config` to `/app/config`: `settings.yaml`, `services.yaml`, `bookmarks.yaml` and `widgets.yaml`. The initial dashboard linked to Proxmox and Technitium DNS. Its Proxmox link used `qnap.lab`, an ambiguous historical value that is not evidence of a current DNS mapping. Allowed hosts included `192.168.55.20:3000`, `home.lab:3000` and `home.home.lab:3000`; current DNS/proxy mappings and dashboard customizations remain unverified.

## Remaining verification

Current hardware sizing is declared in Terraform and was previously verified by the administrator. Running service versions, guest configuration drift, dependencies, firewall rules, data paths and application backup/restore coverage still require a separately authorized operational review. Preserve existing IDs, IPs and data.

See [inventory](../../INVENTORY.md), [host](../hosts/dtcode.md) and [network](../network/NETWORK.md).
