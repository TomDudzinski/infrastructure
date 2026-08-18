resource "proxmox_virtual_environment_vm" "bao01" {
  provider = proxmox.dtcode_manage

  name        = "bao01"
  description = "OpenBao secrets management server managed by Terraform and Ansible."
  tags        = ["openbao", "secrets", "security", "terraform", "ubuntu"]

  node_name = "dtcode"
  vm_id     = 104
  pool_id   = "terraform-managed"

  started         = true
  on_boot         = true
  protection      = true
  stop_on_destroy = true

  purge_on_destroy                     = false
  delete_unreferenced_disks_on_destroy = false

  boot_order = ["scsi0"]

  clone {
    vm_id        = 101
    datastore_id = "local-lvm"
    full         = true
    retries      = 3
  }

  cpu {
    cores = 2
    type  = "host"
  }

  memory {
    dedicated = 2048
  }

  agent {
    enabled = true
    trim    = true

    wait_for_ip {
      disabled = true
    }
  }

  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 32
  }

  initialization {
    datastore_id = "local-lvm"

    dns {
      domain  = "home.lab"
      servers = ["192.168.55.10"]
    }

    ip_config {
      ipv4 {
        address = "192.168.55.24/24"
        gateway = "192.168.55.1"
      }
    }

    user_account {
      username = "tom"

      keys = [
        trimspace(file(pathexpand("~/.ssh/homelab_automation_ed25519.pub"))),
        trimspace(file(pathexpand("~/.ssh/tom-wsl-rsa.pub"))),
      ]
    }
  }

  network_device {
    bridge = "vmbr0"
    model  = "virtio"
  }

  operating_system {
    type = "l26"
  }

  serial_device {}

  vga {
    type = "serial0"
  }
}