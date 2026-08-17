provider "proxmox" {
  alias = "dtcode"

  endpoint  = "https://192.168.55.6:8006/"
  api_token = var.dtcode_api_token

  # The self-signed certificate fingerprint was verified out of band.
  # Replace this with trusted local PKI certificates in a later stage.
  insecure = true
}

provider "proxmox" {
  alias = "dom"

  endpoint  = "https://192.168.55.3:8006/"
  api_token = var.dom_api_token

  # The self-signed certificate fingerprint was verified out of band.
  # Replace this with trusted local PKI certificates in a later stage.
  insecure = true
}
