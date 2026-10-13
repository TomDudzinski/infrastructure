resource "proxmox_virtual_environment_vm" "n8n01" {
  provider = proxmox.dom_manage
  count    = var.n8n01_enabled ? 1 : 0

  name        = "n8n01"
  description = "n8n automation Docker host managed by Terraform and Ansible."
  tags        = ["automation", "n8n", "terraform", "ubuntu"]

  node_name = "dom"
  vm_id     = var.n8n01_vmid
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
    size         = 32
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
        address = "192.168.55.31/24"
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

variable "n8n01_enabled" {
  description = "Enable only after VMID and IP 192.168.55.31 approval."
  type        = bool
  default     = false
}

variable "n8n01_vmid" {
  description = "Approved unused VMID on dom; no default allocation."
  type        = number
  default     = null
  validation {
    condition     = !var.n8n01_enabled || (var.n8n01_vmid == null ? false : var.n8n01_vmid >= 100 && floor(var.n8n01_vmid) == var.n8n01_vmid)
    error_message = "An approved integer VMID >= 100 is required when enabled."
  }
}
