# Network

## Purpose

This document records the HomeLab network addressing, service dependencies and access boundaries.

## Evidence boundary

Reconciled on `2026-10-04` using local documentation and source code only. Existing “Verified” labels refer to prior recorded observations, not checks performed in this review. Historical port mappings and routes describe intended old configuration; current listeners, DNS records, ACLs and firewall policy remain unconfirmed. Operational command examples below must not be executed from the development laptop.

## Primary network

| Property | Value |
|---|---|
| IPv4 network | `192.168.55.0/24` |
| Default gateway | `192.168.55.1` |
| Local DNS domain | `home.lab` |
| Primary DNS server | `192.168.55.10` |
| Proxmox bridge | `vmbr0` |

## Address inventory

| Address | Host | Type | Role | Status |
|---|---|---|---|---|
| `192.168.55.1` | Gateway | Network device | Default gateway | Documented |
| `192.168.55.3` | `dom` | Physical server | Proxmox VE host | Verified |
| `192.168.55.4` | `tailscale-router` | VM | Remote access router | Verified |
| `192.168.55.5` | `qnap` | NAS | Storage and backup | Verified |
| `192.168.55.6` | `dtcode` | Physical server | Proxmox VE host | Verified |
| `192.168.55.7` | `iza` | Physical server | AI, automation and management | Verified |
| `192.168.55.10` | `dns01` | LXC | Technitium DNS | Verified |
| `192.168.55.20` | `home01` | VM | HomeLab portal | Verified |
| `192.168.55.21` | `mysql01` | VM | MySQL database server | Verified |
| `192.168.55.22` | `forgejo01` | VM | Git service | Verified |
| `192.168.55.23` | `npm01` | VM | Reverse proxy | Previously documented; legacy |
| `192.168.55.24` | `bao01` | VM | OpenBao | Current Terraform/Ansible; prior deployment documented |
| `192.168.55.25` | `qdrant01` | VM | Vector database | Current code; deployment unconfirmed |
| `192.168.55.26` | `langfuse01` | VM | LLM observability | Current code; deployment unconfirmed |
| `192.168.55.27` | `grafana01` | VM | Observability | Current code; deployment unconfirmed |
| `192.168.55.28` | `cloudflare01` | VM | Tunnel gateway | Current code; deployment unconfirmed |
| `192.168.55.30` | `webui01` | VM | Open WebUI (public via Cloudflare Tunnel) | Planned; code only, not deployed |

## Recovered legacy network configuration

All five legacy guests use historical static addresses in `192.168.55.0/24`, gateway `192.168.55.1` and bridge `vmbr0`. Current Terraform definitions preserve these addresses, and state adoption was completed on 2026-10-04 according to the administrator. None has current Ansible management. The following service ports/routes remain historical evidence, not new runtime verification.

| Resource | Historical service exposure / routing | Evidence |
|---|---|---|
| `dns01`, ID `102`, `.10` | Technitium with Docker host networking; administration link on `5380` | `technitium-dns.tf`, `homepage.tf` |
| `home01`, ID `103`, `.20` | Homepage TCP `3000`; allowed names included `home.lab` and `home.home.lab` | `homepage.tf`; DNS records unconfirmed |
| `forgejo01`, ID `105`, `.22` | HTTP TCP `3000`; Git SSH host TCP `222` to container `22` | `forgejo.tf` |
| `npm01`, ID `106`, `.23` | HTTP `80`, HTTPS `443`, administration `81`; historical wildcard `*.home.lab` / `home.lab` | `npm.tf`; current proxy routes unconfirmed |
| `tailscale-router`, ID `107`, `.4` | Advertised `192.168.55.0/24`; `--accept-dns=false`; IPv4/IPv6 forwarding enabled | `tailscale.tf`; approval and ACLs unconfirmed |

Historical Forgejo/NPM provisioning used public DNS resolvers `8.8.8.8` and `8.8.4.4` and disabled Docker IPv6; Homepage also disabled Docker IPv6. These workarounds must not be mistaken for the current LAN DNS policy or reapplied from this documentation. The historical `qnap.lab` dashboard link is ambiguous and does not establish a current Proxmox hostname.

`wiki01` has status **historical / probably removed**. According to the administrator, it is not running and was probably removed from Proxmox `dtcode`; the administrator also reports that the latest old `terraform.tfstate` no longer contains this VM. These statements were not independently verified in this local review; absence from state alone does not prove removal from Proxmox.

**Historically reused identifiers and addresses:** VM ID `104` on `dtcode`, formerly used by `wiki01`, now belongs to `bao01`. IP `192.168.55.21`, referenced by historical `wiki01` and `test-vm`, now belongs to `mysql01` on `dom`. These are historical reassignments, not active collisions; the identifiers and address are currently allocated and must not be restored from old definitions.

`test-vm` remains **historical**; its current presence cannot be confirmed. No active definitions or recreation plans are added for either historical guest.

See the [dtcode inventory](../hosts/dtcode.md) and individual [guest documents](../vms/).

## Proxmox networking

Both Proxmox environments use:

```text
vmbr0
```

Terraform attaches approved managed VMs to this bridge.

The restricted Terraform management identity receives `SDN.Use` only at:

```text
/sdn/zones/localnetwork/vmbr0
```

This permits VM network attachment without granting unrestricted SDN administration.

## mysql01

`mysql01` uses a static cloud-init configuration:

| Property | Value |
|---|---|
| Address | `192.168.55.21/24` |
| Gateway | `192.168.55.1` |
| DNS server | `192.168.55.10` |
| FQDN | `mysql01.home.lab` |
| Interface model | VirtIO |
| Bridge | `vmbr0` |

The address was checked before VM creation and was not present in the ARP neighbor table.

The DNS record for `mysql01.home.lab` still requires explicit verification.

## MySQL access

MySQL currently listens only on the VM loopback interface:

```text
127.0.0.1:3306
127.0.0.1:33060
```

No MySQL port is currently exposed to the LAN.

The planned remote access model is:

| Source | Destination | Port | Purpose |
|---|---|---:|---|
| `192.168.55.7` (`iza`) | `192.168.55.21` (`mysql01`) | `3306/tcp` | Approved AI demonstration client |

Remote access must not be enabled until:

1. a dedicated database has been created;
2. a read-only MySQL account has been created;
3. its credential is stored outside Git;
4. host firewall rules restrict the source address;
5. MySQL account host restrictions are configured;
6. backup and restore requirements are documented.

The planned AI agent account must receive only the required database privileges, initially `SELECT`.

## Management access

### Proxmox API

Terraform on `iza` connects to:

| Destination | Port | Protocol |
|---|---:|---|
| `192.168.55.6` (`dtcode`) | `8006` | HTTPS |
| `192.168.55.3` (`dom`) | `8006` | HTTPS |

### SSH

Ansible on `iza` connects to managed guests using TCP port `22`.

`mysql01` accepts public-key authentication for the `tom` account. SSH password authentication is disabled.

### QNAP backup

`iza` mounts:

```text
192.168.55.5:/Backup
```

at:

```text
/mnt/qnap-backup
```

using NFS 4.1.

## DNS

Technitium DNS runs on:

```text
192.168.55.10
```

The local domain is:

```text
home.lab
```

Required DNS verification for `mysql01`:

```bash
getent hosts mysql01.home.lab
dig @192.168.55.10 mysql01.home.lab
```

The expected address is:

```text
192.168.55.21
```

## Remote access

Tailscale provides remote access through `tailscale-router`.

Tailscale routing and DNS behavior require separate documentation and verification for each client network.

Remote MySQL access through Tailscale is not currently approved or configured.

## Verification commands

Display local addresses and routing on `iza`:

```bash
ip -br address
ip route
ip neigh show
```

Verify core hosts:

```bash
ping -c 3 192.168.55.3
ping -c 3 192.168.55.5
ping -c 3 192.168.55.6
ping -c 3 192.168.55.10
ping -c 3 192.168.55.21
```

Verify SSH to `mysql01`:

```bash
ssh \
  -i "${HOME}/.ssh/homelab_automation_ed25519" \
  -o IdentitiesOnly=yes \
  tom@192.168.55.21
```

Verify MySQL bindings through Ansible:

```bash
cd /opt/ai/projects/infrastructure/ansible

ansible mysql01 \
  --become \
  --module-name ansible.builtin.shell \
  --args 'ss -lntp | grep ":3306" || true'
```

## Remaining work

- verify the `mysql01.home.lab` DNS record;
- document DHCP scopes and reservations;
- document physical switches and network interfaces;
- document reverse proxy routes;
- document Tailscale routes and DNS behavior;
- define the firewall policy for database access;
- add network monitoring and alerting.
