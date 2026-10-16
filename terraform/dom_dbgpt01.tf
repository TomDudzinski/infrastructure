resource "proxmox_virtual_environment_vm" "dbgpt01" {
  provider = proxmox.dom_manage
  count    = var.dbgpt01_enabled ? 1 : 0

  name        = "dbgpt01"
  description = "DB-GPT and LiteLLM prototype host managed by Terraform and Ansible."
  tags        = ["ai", "text-to-sql", "terraform", "ubuntu"]

  node_name = "dom"
  vm_id     = var.dbgpt01_vmid
  pool_id   = "terraform-managed"

  started    = true
  on_boot    = true
  protection = true

  purge_on_destroy                     = false
  delete_unreferenced_disks_on_destroy = false

  lifecycle {
    prevent_destroy = true
  }

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
        address = var.dbgpt01_ipv4_cidr
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

variable "dbgpt01_enabled" {
  description = "Enable only on iza after approval of unused VMID and LAN IP."
  type        = bool
  default     = false
}

variable "dbgpt01_vmid" {
  type    = number
  default = null
  validation {
    condition     = !var.dbgpt01_enabled || try(var.dbgpt01_vmid >= 100 && floor(var.dbgpt01_vmid) == var.dbgpt01_vmid, false)
    error_message = "An approved unused integer VMID >= 100 is required."
  }
}

variable "dbgpt01_ipv4_cidr" {
  description = "Approved unused address in the existing LAN; no automatic allocation."
  type        = string
  default     = null
  validation {
    condition     = !var.dbgpt01_enabled || try(can(cidrhost(var.dbgpt01_ipv4_cidr, 0)) && startswith(var.dbgpt01_ipv4_cidr, "192.168.55.") && endswith(var.dbgpt01_ipv4_cidr, "/24") && !contains(["192.168.55.0/24", "192.168.55.255/24"], var.dbgpt01_ipv4_cidr), false)
    error_message = "Use an approved unused host address in 192.168.55.0/24."
  }
}
