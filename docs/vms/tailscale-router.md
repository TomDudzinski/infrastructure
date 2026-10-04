# tailscale-router

## Identity and purpose

| Property | Value |
|---|---|
| Host | `dtcode` |
| Type | VM |
| ID | `107` |
| Address | `192.168.55.4` |
| Purpose | Tailscale subnet router |
| Historical source | `tailscale.tf` |
| Historical allocation | 1 core, 512 MiB RAM |
| Historical clone source | Full clone of template ID `999` |
| Network | VirtIO on `vmbr0`; `192.168.55.4/24`; gateway `192.168.55.1` |
| Startup | Enabled at host boot; order 1; delay 20 seconds |

## Evidence and management status

This is an existing legacy resource recorded in the current inventory on `2026-08-17`. Its configuration below was recovered from historical source code in `/home/tom/Projekty/infrastructure-old/homelab/terraform/environments/dev/` during a local documentation review on `2026-10-04`.

- Current Terraform: definition in `terraform/dtcode_tailscale_router.tf`; imported into the current state on `2026-10-04` according to the administrator. Hardware matches the previously verified live configuration; remaining provider/state differences are recorded in the [adoption review](../operations/dtcode-adoption-2026-10-04.md).
- Current Ansible: no inventory entry or dedicated playbook for this guest.
- Current scope: adopted existing resource managed by current Terraform state; application configuration is not managed by current Ansible.
- Next review: remaining provider/state drift, service configuration, dependencies, persistent data and backup/restore coverage. Ansible adoption requires a separate proposal; no apply or rebuild is authorized.

Historical code records intended configuration, not proof of successful provisioning or current runtime state. No infrastructure connections or commands were executed in this review. Secret values and keys are intentionally excluded.

## Historical configuration and persistent data

Historical Terraform used a wait resource and `local-exec` over SSH to install Tailscale through its installation script and enable `tailscaled`. It enabled IPv4 and IPv6 forwarding in `/etc/sysctl.d/99-tailscale.conf`, advertised `192.168.55.0/24` and set `--accept-dns=false`. Route approval, ACLs and current client DNS behavior are not established by those flags. The code does not establish exit-node operation.

Persistent configuration includes `/etc/sysctl.d/99-tailscale.conf`. Tailscale normally maintains node identity/state under `/var/lib/tailscale`; this is an expected path, not a path explicitly configured or verified by the historical source. Node identity, approved routes and recovery/re-enrollment procedures require verification. Authentication material is excluded from documentation. No backup or restore verification was recovered.

## Remaining verification

Current hardware sizing is declared in Terraform and was previously verified by the administrator. Running service versions, guest configuration drift, dependencies, firewall rules, data paths and application backup/restore coverage still require a separately authorized operational review. Preserve existing IDs, IPs and data.

See [inventory](../../INVENTORY.md), [host](../hosts/dtcode.md) and [network](../network/NETWORK.md).
