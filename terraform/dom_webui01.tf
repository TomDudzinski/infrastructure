resource "proxmox_virtual_environment_vm" "webui01" {
  provider = proxmox.dom_manage
  count    = var.webui01_enabled ? 1 : 0

  name        = "webui01"
  description = "Open WebUI Docker host managed by Terraform and Ansible."
  tags        = ["ai", "open-webui", "terraform", "ubuntu"]

  node_name = "dom"
  vm_id     = var.webui01_vmid
  pool_id   = "terraform-managed"

  started    = true
  on_boot    = true
  protection = true

  purge_on_destroy                     = false
  delete_unreferenced_disks_on_destroy = false

  cpu {
    cores = 4
    type  = "host"
  }

  memory {
    dedicated = 8192
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
    size         = 40
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
        address = "192.168.55.30/24"
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

variable "webui01_enabled" {
  description = "Enable only after VMID and IP 192.168.55.30 approval."
  type        = bool
  default     = false
}

variable "webui01_vmid" {
  description = "Approved unused VMID on dom; no default allocation."
  type        = number
  default     = null
  validation {
    condition     = !var.webui01_enabled || (var.webui01_vmid == null ? false : var.webui01_vmid >= 100 && floor(var.webui01_vmid) == var.webui01_vmid)
    error_message = "An approved integer VMID >= 100 is required when enabled."
  }
}
