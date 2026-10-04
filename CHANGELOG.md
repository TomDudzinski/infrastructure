# Changelog

## 2026-10-04

### Completed state adoption (administrator report)

According to the administrator's completion report dated `2026-10-04`, `dns01` (LXC 102, `192.168.55.10`), `home01` (VM 103, `192.168.55.20`), `forgejo01` (VM 105, `192.168.55.22`), `npm01` (VM 106, `192.168.55.23`) and `tailscale-router` (VM 107, `192.168.55.4`) were imported individually into the current Terraform state. Each import was checked with a targeted plan; the final state list included all five resources. The final full plan reported **0 add, 5 change, 0 destroy**. **No terraform apply was performed.**

Remaining reported differences concern VM destroy-behavior defaults, VGA for all four VMs, memory for `tailscale-router`, and timeout/vm_id for `dns01`. Four VM definitions contain `serial_device { device = "socket" }`, consistent with the previously verified live hardware. A Terraform state backup was made after adoption; its location and restore were not checked here. This is not an application-data backup.

This laptop review confirms local definitions only. State membership, plan results, prior live hardware verification and backup completion are administrator-reported evidence, not operations performed or independently repeated here. None of the five hosts has current Ansible inventory, host_vars, playbooks or assigned roles. Adoption does not establish service deployment, runtime health or application restore capability.

### Documentation review

- Reconciled current Terraform adoption with local definitions and actual Ansible coverage.
- Recorded remaining adoption differences and absent Ansible coverage for these five guests without modifying Terraform or Ansible code.
- No infrastructure connections, deployments, commits or pushes in the laptop review.

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
- Added Terraform-managed VM `104` (`bao01`) on `dtcode`.
- Added the `secrets_servers` Ansible inventory group and `bao01` host configuration.
- Added the `openbao` Ansible role and `bao01` bootstrap playbook.
- Installed OpenBao `2.6.1` on `bao01`.
- Configured OpenBao integrated Raft storage.
- Enabled TLS for the OpenBao listener.
- Added the HomeLab Root CA and OpenBao Intermediate CA hierarchy.
- Enabled the OpenBao PKI secrets engine.
- Added `userpass` authentication and the administrative `tom` account.
- Added a dedicated HomeLab PKI certificate for `bao01.home.lab`.
- Added a separate Nginx Proxy Manager frontend certificate for `bao01.home.lab`.
- Added OpenBao service, PKI, recovery and VM documentation.
- Added encrypted OpenBao Raft snapshot backup to QNAP.
- Added `iza` as a locally managed Ansible host.
- Added the `qnap_mount` Ansible role and `iza` bootstrap playbook.
- Added the pinned `ansible.posix` collection.

### Changed

- Enabled automatic startup for `mysql01`.
- Enabled QEMU Guest Agent integration for `mysql01`.
- Restricted MySQL network bindings to localhost.
- Removed anonymous MySQL users and the default test database.
- Added `ansible-core` to the host dependency installation script.
- Updated the `dom` host documentation.
- Updated the current project status.
- Extended Terraform management to approved new resources on `dtcode`.
- Added restricted `VM.Clone` access for Terraform to template `101`.
- Added QNAP NFS systemd automount configuration on `iza`.
- Moved the existing QNAP NFS automount configuration under Ansible management.
- Configured Ansible on `iza` to use the classic `/usr/bin/sudo.ws` executable for local privilege escalation because the system-default `sudo-rs` was incompatible with the verified Ansible become workflow.
- Documented the QNAP NFS automount implementation and recovery behavior.
- Updated infrastructure inventory and status for the deployed OpenBao platform.

### Security

- Kept read-only and management Proxmox identities separate.
- Restricted Terraform management permissions instead of using the built-in `Administrator` role.
- Added `Sys.AccessNetwork` only where required by Proxmox VE 9.
- Restricted Terraform network use to `vmbr0`.
- Kept Terraform state, plans and token values outside Git.
- Kept SSH password authentication disabled on `mysql01`.
- Kept MySQL inaccessible from the LAN during initial deployment.
- Initialized OpenBao with Shamir key splitting using 5 shares and a threshold of 3.
- Revoked the initial OpenBao root token after administrative access was configured.
- Kept OpenBao initialization material, unseal shares, private keys and tokens outside Git.
- Added encrypted OpenBao initialization recovery material on `iza` and QNAP.
- Added a dedicated GPG recovery key for OpenBao backup material.
- Added an encrypted HomeLab Root CA private key backup on QNAP.
- Verified TLS access to OpenBao without disabling certificate validation.

### Backup

- Created and verified a QNAP-backed Restic repository.
- Completed `restic check` successfully.
- Completed an actual infrastructure configuration restore test successfully.
- Created the first OpenBao integrated Raft snapshot.
- Encrypted the Raft snapshot with the dedicated OpenBao recovery GPG key.
- Verified encrypted snapshot decryption against the original SHA-256 checksum.
- Copied the encrypted Raft snapshot to QNAP.
- Verified identical SHA-256 checksums for the local and QNAP encrypted snapshot copies.
- Documented that a complete OpenBao Raft restore test is still required.
- Verified the QNAP NFS 4.1 systemd automount at `/mnt/qnap-backup`.
- Verified that the Ansible-managed QNAP mount configuration is idempotent.

## 2026-08-17

### Removed

- Removed obsolete stopped VM `104` (`wiki01`) from `dtcode`.
- Removed obsolete stopped VM `201` (`ubuntu-test`) from `dtcode`.
- Removed obsolete stopped VM `202` (`tailscale-router`) from `dtcode`.
- Removed the associated VM disks and cloud-init volumes from `local-lvm`.

### Documentation

- Updated the verified `dtcode` workload inventory.
- Removed obsolete VM inventory entries and resolved the corresponding inventory gap.
