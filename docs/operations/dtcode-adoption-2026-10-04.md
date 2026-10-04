# dtcode adoption review — 2026-10-04

## Evidence boundary

This report covers only the adoption of dns01 (LXC 102), home01 (VM 103), forgejo01 (VM 105), npm01 (VM 106) and tailscale-router (VM 107) on 2026-10-04 and local review of their Terraform definitions and Ansible coverage. No infrastructure connections, Terraform/Ansible execution, deployments, commits or pushes were performed during this documentation review. Operational results below were supplied by the administrator.

The administrator reports that live Proxmox hardware was previously verified, each resource was imported individually and checked with a targeted Terraform plan, and the final state list contained all five resources. The final full plan was **0 add, 5 change, 0 destroy**. **No terraform apply was performed.** A Terraform state backup was made after adoption. These are supplied operational facts, not independently repeated laptop checks.

## Terraform configuration and adoption

| Guest | Resource address | ID | IPv4 | CPU cores | RAM MiB | System disk GiB |
|---|---|---:|---|---:|---:|---:|
| dns01 | `proxmox_virtual_environment_container.dns01` | 102 | 192.168.55.10 | 2 | 2048 | 20 |
| home01 | `proxmox_virtual_environment_vm.home01` | 103 | 192.168.55.20 | 1 | 1024 | 32 |
| forgejo01 | `proxmox_virtual_environment_vm.forgejo01` | 105 | 192.168.55.22 | 1 | 1024 | 32 |
| npm01 | `proxmox_virtual_environment_vm.npm01` | 106 | 192.168.55.23 | 1 | 1024 | 32 |
| tailscale-router | `proxmox_virtual_environment_vm.tailscale_router` | 107 | 192.168.55.4 | 1 | 512 | 32 |

Definitions are in `terraform/dtcode_*.tf`, use `proxmox.dtcode_manage`, node `dtcode`, storage `local-lvm`, bridge `vmbr0`, gateway `192.168.55.1`, preserved MAC addresses and automatic boot. The four VMs have cloud-init on `ide2`, disks on `scsi0`, `serial_device { device = "socket" }`, and explicit VGA. The LXC is unprivileged with nesting, no swap and a historical Ubuntu template path.

All five guests have `prevent_destroy = true` and `protection = false`. The former is a configuration guard, not Proxmox protection or a data backup. All ignore runtime `started`, guest user_account and DNS; VMs also ignore guest upgrades, and the LXC ignores the historical template input. Other hardware drift is not broadly suppressed. VM deletion settings disable purge and deletion of unreferenced disks, with `stop_on_destroy = true`.

The adoption definitions do not clone or provision these guests and do not require template 999. They preserve existing identities rather than recreate the services.

The definitions reflect hardware previously verified by the administrator. This does not mean the imported state and desired configuration have converged. Remaining reported differences are VM destroy-behavior defaults, VGA for four VMs, memory for tailscale-router, and timeout/vm_id for dns01. Exact old/new values and change consequences cannot be established without the full saved plan; the count alone is insufficient. No automatic code reconciliation or apply is proposed here.

## Ansible coverage of the five guests

| Guest | Inventory | host_vars / playbook | Assigned roles | Service automation in current repo | Assessment |
|---|---|---|---|---|---|
| dns01 | Absent | Absent / absent | None | None for Technitium DNS | Hardware adopted; guest/service management absent |
| home01 | Absent | Absent / absent | None | None for Homepage | Hardware adopted; guest/service management absent |
| forgejo01 | Absent | Absent / absent | None | None for Forgejo | Hardware adopted; guest/service management absent |
| npm01 | Absent | Absent / absent | None | None for Nginx Proxy Manager | Hardware adopted; guest/service management absent |
| tailscale-router | Absent | Absent / absent | None | None for Tailscale, forwarding or route approval | Hardware adopted; guest/service management absent |

The local review found no current Ansible service automation assigned to these five guests. Historical Terraform SSH provisioners are archival provenance, not active Ansible management in this repository. Terraform configuration and state adoption concern infrastructure resources; neither establishes operating-system/service configuration management or runtime health.

## Issues requiring a separate proposal

No Terraform or Ansible code was changed. Findings below describe files, risk and proposed follow-up, without claiming a runtime failure.

| File / location | Finding and risk | Proposed follow-up |
|---|---|---|
| `terraform/dtcode_{dns01,home01,forgejo01,npm01,tailscale_router}.tf`, header comments | Comments still claim resources were not imported; misleading operational guidance may encourage duplicate adoption | Update comments in a separately approved code change; do not repeat imports |
| Same five files; reported final plan | Five changes remain; exact field transitions were not supplied, so hardware impact cannot be independently assessed | Review the full saved plan/provider normalization before proposing individual reconciliations; do not hide differences with broad ignore_changes |
| Same files, lifecycle/protection | Terraform guard exists but Proxmox protection is false, matching supplied live configuration | Consider protection policy separately with explicit approval; preserve live settings now |
| `terraform/dtcode_dns01.tf`, operating_system | Template path is historical and ignored; present availability is unknown | Treat as provenance; design/test a separate recovery procedure rather than recreating from this definition |
| `ansible/inventories/production/hosts.yml`, playbooks/roles | Five adopted guests lack all Ansible coverage; service configuration is not reproducible from current Ansible | Inventory live guest configuration/data first, then propose host_vars and reusable service roles with Vault secrets, preserving existing resources |

## Historical identity cautions

Former wiki01 ID 104 now belongs to bao01. Historical wiki01/test-vm address 192.168.55.21 is allocated to mysql01 on dom. These historical identities are not part of the five-resource adoption and must not be used to recreate old guests. Historical tailscale-router ID 202 is distinct from the adopted VM 107.

## Runtime, backup and remaining verification

No new service health, DNS/proxy route, TLS certificate, Tailscale route approval/ACL, power state, data contents or deployed Ansible configuration was verified. Previously recorded observations remain historical and dated. The completion report does not establish backup destination, retention, integrity or restoration. Absence of backup artifacts in the repository does not establish absence of backups elsewhere.

Application coverage still needs evidence for Technitium configuration, Homepage configuration, Forgejo repositories/database/volume, NPM database/certificates and Tailscale identity/settings. The state backup preserves Terraform mappings/metadata; it does not preserve application data or prove a full guest/application recovery. Hardware adoption definitions are not complete disaster-recovery recipes.

## Completion and verification boundary

All five imports into the current Terraform state were completed on 2026-10-04 according to the administrator. This does not confirm completion of the entire former pre-import procedure. Full VM/container/application-data backup and restore remain unconfirmed. The Terraform state backup preserves resource mappings and metadata, not guest disks or application data.

This documentation update was reviewed locally with Git diff and whitespace checks. Terraform and Ansible code were not changed. No runtime verification was performed.
