variable "dtcode_api_token" {
  description = "Read-only Proxmox API token for dtcode."
  type        = string
  sensitive   = true
}

variable "dom_api_token" {
  description = "Read-only Proxmox API token for dom."
  type        = string
  sensitive   = true
}

variable "dtcode_manage_api_token" {
  description = "Management Proxmox API token for dtcode."
  type        = string
  sensitive   = true
}

variable "dom_manage_api_token" {
  description = "Management Proxmox API token for dom."
  type        = string
  sensitive   = true
}
