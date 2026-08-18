# dom

## Purpose

`dom` is the main high-resource Proxmox VE virtualization host in the HomeLab environment.

## Identity

| Property | Value |
|---|---|
| Hostname | `dom` |
| Address | `192.168.55.3` |
| Type | Physical server |
| Role | Main virtualization host |
| Cluster status | Standalone host |

## Platform

Verified on `2026-08-17`:

| Property | Value |
|---|---|
| Hardware | HP ProLiant DL360p Gen8 |
| Proxmox VE | `9.2.2` |
| Operating system | Debian 13 |
| Running kernel | `7.0.2-6-pve` |
| CPU allocation visible to PVE | 32 logical CPUs |
| Memory visible to PVE | Approximately 189 GiB |
| Storage | `local`, `local-lvm` |
| Network bridge | `vmbr0` |
| Bridge address | `192.168.55.3/24` |

The server firmware is old and requires a separate hardware and firmware review before production use.

## Storage

| Storage | Type | Purpose |
|---|---|---|
| `local` | Directory | ISO images, cloud images, templates, backups and imports |
| `local-lvm` | LVM thin pool | VM and LXC disks |

Terraform currently stores the verified Ubuntu 24.04 cloud image on `local` and the `mysql01` system disk on `local-lvm`.

## Network

The primary Proxmox bridge is:

```text
vmbr0
