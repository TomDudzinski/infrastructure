# Infrastructure Inventory

| Host | Type | IP | Role |
|---|---|---|---|
| dtcode | Proxmox | 192.168.55.6 | Small virtualization host |
| dom | Proxmox | 192.168.55.3 | Main high-resource virtualization host |
| iza | Physical server | TBD | AI / LLM |
| QNAP | NAS | 192.168.55.5 | Backup / storage |

## Virtual Machines

| ID | Name | IP | Host | Purpose |
|---|---|---|---|---|
| 102 | dns01 | 192.168.55.10 | dtcode | Technitium DNS |
| 103 | home01 | 192.168.55.20 | dtcode | Homepage |
| 105 | forgejo01 | 192.168.55.22 | dtcode | Forgejo |
| 106 | npm01 | 192.168.55.23 | dtcode | Nginx Proxy Manager |
| 107 | tailscale-router | 192.168.55.4 | dtcode | VPN / subnet router |
