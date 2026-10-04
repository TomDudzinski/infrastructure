# Existing legacy LXC: definition only, not imported into the current state.
# Historical evidence: technitium-dns.tf and terraform.tfstate (serial 203).
# Hardware configuration follows the live configuration supplied by the administrator.
# Do not apply before a separately approved import and drift review.
resource "proxmox_virtual_environment_container" "dns01" {
  provider = proxmox.dtcode_manage

  node_name = "dtcode"
  vm_id     = 102

  description  = "Technitium DNS Server"
  tags         = ["dns", "technitium", "terraform"]
  unprivileged = true

  # No pool_id: historical state has no resource pool assignment.
  started       = true
  start_on_boot = true
  # Current protection=0; enabling protection requires a separate policy change.
  protection    = false

  startup {
    order    = 1
    up_delay = 20
  }

  cpu {
    architecture = "amd64"
    cores        = 2
  }

  memory {
    dedicated = 2048
    swap      = 0
  }

  disk {
    datastore_id = "local-lvm"
    size         = 20
  }

  initialization {
    hostname = "dns01"

    ip_config {
      ipv4 {
        address = "192.168.55.10/24"
        gateway = "192.168.55.1"
      }
    }

    # Historical credentials/keys and guest DNS settings are omitted.
  }

  # Historical creation input only; the live ostype confirms Ubuntu, not this image.
  # Verify the provider import behavior before adoption; never recreate from it.
  operating_system {
    template_file_id = "local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
    type             = "ubuntu"
  }

  # Proxmox LXC uses a veth interface; no VM model attribute is applicable.
  network_interface {
    name        = "eth0"
    bridge      = "vmbr0"
    mac_address = "BC:24:11:24:50:CB"
  }

  features {
    nesting = true
  }

  lifecycle {
    prevent_destroy = true

    # Preserve runtime power state and excluded guest initialization fields.
    # The template records provenance; its present availability is unverified.
    ignore_changes = [
      started,
      initialization[0].user_account,
      initialization[0].dns,
      operating_system[0].template_file_id,
    ]
  }
}
