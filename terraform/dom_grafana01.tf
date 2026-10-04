resource "proxmox_virtual_environment_vm" "grafana01" {
  provider = proxmox.dom_manage

  name        = "grafana01"
  description = "Grafana observability server managed by Terraform and Ansible."
  tags        = ["observability", "grafana", "terraform", "ubuntu"]

  node_name = "dom"
  vm_id     = 204
  pool_id   = "terraform-managed"

  started    = true
  on_boot    = true
  protection = true

  purge_on_destroy                     = false
  delete_unreferenced_disks_on_destroy = false

  cpu {
    cores = 2
    type  = "host"
  }

  memory {
    dedicated = 4096
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
    import_from  = proxmox_download_file.dom_ubuntu_2404_cloud_image.id
    interface    = "scsi0"
    size         = 30
    discard      = "on"
    iothread     = true
  }

  initialization {
    datastore_id = "local-lvm"

    dns {
      domain  = "home.lab"
      servers = ["192.168.55.10"]
    }

    ip_config {
      ipv4 {
        address = "192.168.55.27/24"
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
