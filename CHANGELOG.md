# Changelog

## 2026-08-18

### Added

- Added restricted Terraform management providers for `dtcode` and `dom`.
- Added separate privilege-separated Proxmox management identities.
- Added custom Proxmox roles and ACL boundaries for managed resources, storage, node access and `vmbr0`.
- Added the local Terraform state backend.
- Added the checksum-verified Ubuntu 24.04 cloud image on `dom`.
- Added Terraform-managed VM `201` (`mysql01`) on `dom`.
- Added the production Ansible inventory and configuration.
- Added the `qemu_guest_agent` Ansible role.
- Added the `mysql_server` Ansible role.
- Added the pinned `ansible.mysql` collection.
- Installed MySQL Server 8.0.46 on `mysql01`.
- Added an independent Restic repository on the QNAP NFS storage.
- Added the QNAP infrastructure configuration backup script.
- Added documentation for `mysql01`.

### Changed

- Enabled automatic startup for `mysql01`.
- Enabled QEMU Guest Agent integration for `mysql01`.
- Restricted MySQL network bindings to localhost.
- Removed anonymous MySQL users and the default test database.
- Added `ansible-core` to the host dependency installation script.
- Updated the `dom` host documentation.
- Updated the current project status.

### Security

- Kept read-only and management Proxmox identities separate.
- Restricted Terraform management permissions instead of using the built-in `Administrator` role.
- Added `Sys.AccessNetwork` only where required by Proxmox VE 9.
- Restricted Terraform network use to `vmbr0`.
- Kept Terraform state, plans and token values outside Git.
- Kept SSH password authentication disabled on `mysql01`.
- Kept MySQL inaccessible from the LAN during initial deployment.

### Backup

- Created and verified a QNAP-backed Restic repository.
- Completed `restic check` successfully.
- Completed an actual infrastructure configuration restore test successfully.

## 2026-08-17

### Removed

- Removed obsolete stopped VM `104` (`wiki01`) from `dtcode`.
- Removed obsolete stopped VM `201` (`ubuntu-test`) from `dtcode`.
- Removed obsolete stopped VM `202` (`tailscale-router`) from `dtcode`.
- Removed the associated VM disks and cloud-init volumes from `local-lvm`.

### Documentation

- Updated the verified `dtcode` workload inventory.
- Removed obsolete VM inventory entries and resolved the corresponding inventory gap.