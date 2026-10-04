# Existing legacy VM: definition only, not imported into the current state.
# Historical evidence: homepage.tf and terraform.tfstate (serial 203).
# Hardware configuration follows the live configuration supplied by the administrator.
# Do not apply before a separately approved import and drift review.
resource "proxmox_virtual_environment_vm" "home01" {
  provider = proxmox.dtcode_manage

  name        = "home01"
  description = "Homepage Dashboard"
  tags        = ["dashboard", "homepage", "terraform"]

  node_name = "dtcode"
  vm_id     = 103

  # No pool_id: historical state has no resource pool assignment.
  started = true
  on_boot = true
  # Current protection=0; enabling protection requires a separate policy change.
  protection      = false
  stop_on_destroy = true

  purge_on_destroy                     = false
  delete_unreferenced_disks_on_destroy = false

  bios          = "seabios"
  boot_order    = ["scsi0"]
  scsi_hardware = "virtio-scsi-pci"

  # Existing VM adoption does not depend on historical clone template 999.

  startup {
    order    = 2
    up_delay = 20
  }

  cpu {
    cores   = 1
    sockets = 1
    type    = "host"
  }

  memory {
    dedicated = 1024
    floating  = 0
  }

  agent {
    enabled = true
    timeout = "15m"
    trim    = false
  }

  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 32
  }

  operating_system {
    type = "l26"
  }

  initialization {
    datastore_id = "local-lvm"
    interface    = "ide2"

    ip_config {
      ipv4 {
        address = "192.168.55.20/24"
        gateway = "192.168.55.1"
      }
    }

    # Historical credentials/keys and guest DNS/package settings are omitted.
  }

  network_device {
    bridge      = "vmbr0"
    model       = "virtio"
    firewall    = false
    mac_address = "BC:24:11:E4:03:16"
  }

  serial_device {
    device = "socket"
  }

  vga {
    type   = "std"
    memory = 16
  }

  lifecycle {
    prevent_destroy = true

    # Runtime power is operational; guest credentials, DNS and package upgrades
    # remain outside this hardware adoption and must not be reset by Terraform.
    ignore_changes = [
      started,
      initialization[0].user_account,
      initialization[0].dns,
      initialization[0].upgrade,
    ]
  }
}
