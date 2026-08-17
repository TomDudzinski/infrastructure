output "proxmox_versions" {
  description = "Versions reported by the two read-only Proxmox providers."

  value = {
    dtcode = {
      version       = data.proxmox_version.dtcode.version
      release       = data.proxmox_version.dtcode.release
      repository_id = data.proxmox_version.dtcode.repository_id
    }
    dom = {
      version       = data.proxmox_version.dom.version
      release       = data.proxmox_version.dom.release
      repository_id = data.proxmox_version.dom.repository_id
    }
  }
}
