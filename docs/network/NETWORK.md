# Network

## Purpose

This document records the HomeLab network addressing, service dependencies and access boundaries.

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
| `192.168.55.23` | `npm01` | VM | Reverse proxy | Verified |

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