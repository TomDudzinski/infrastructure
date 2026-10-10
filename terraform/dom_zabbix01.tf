resource "proxmox_virtual_environment_vm" "zabbix01" {
  provider = proxmox.dom_manage
  count    = var.zabbix_enabled ? 1 : 0

  name        = "zabbix01"
  description = "Zabbix LTS monitoring server managed by Terraform and Ansible."
  tags        = ["observability", "zabbix", "terraform", "ubuntu"]

  node_name = "dom"
  vm_id     = var.zabbix_vmid
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
        address = "${var.zabbix_ip}/24"
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

variable "zabbix_enabled" {
  description = "Enable only after IP and VMID approval."
  type        = bool
  default     = false
}

variable "zabbix_vmid" {
  description = "Approved unused VMID on dom; no default allocation."
  type        = number
  default     = null
  validation {
    condition     = !var.zabbix_enabled || (var.zabbix_vmid == null ? false : var.zabbix_vmid >= 100 && floor(var.zabbix_vmid) == var.zabbix_vmid)
    error_message = "An approved integer VMID >= 100 is required when enabled."
  }
}

variable "zabbix_ip" {
  description = "Approved unused LAN address for zabbix01."
  type        = string
  default     = null
  validation {
    condition     = !var.zabbix_enabled || can(regex("^192\\.168\\.55\\.([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-4])$", var.zabbix_ip))
    error_message = "An approved usable address in 192.168.55.0/24 is required."
  }
}
