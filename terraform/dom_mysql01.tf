resource "proxmox_download_file" "dom_ubuntu_2404_cloud_image" {
  provider = proxmox.dom_manage

  content_type = "import"
  datastore_id = "local"
  node_name    = "dom"

  url       = "https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img"
  file_name = "ubuntu-24.04-server-cloudimg-amd64-20260814.qcow2"

  checksum           = "6e40c07ae715f744f84af0bec76415cc1987dd115b4b8de437818561f01a3733"
  checksum_algorithm = "sha256"
}

resource "proxmox_virtual_environment_vm" "mysql01" {
  provider = proxmox.dom_manage

  name        = "mysql01"
  description = "MySQL database server managed by Terraform and Ansible."
  tags        = ["database", "mysql", "terraform", "ubuntu"]

  node_name = "dom"
  vm_id     = 201
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
    size         = 64
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
        address = "192.168.55.21/24"
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
