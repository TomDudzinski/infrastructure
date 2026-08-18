# mysql01

## Purpose

`mysql01` is the database server for HomeLab demonstration and AI integration workloads.

The VM is managed by Terraform. Its operating system and MySQL configuration are managed by Ansible.

## Identity

| Property | Value |
|---|---|
| Hostname | `mysql01` |
| FQDN | `mysql01.home.lab` |
| IPv4 address | `192.168.55.21/24` |
| Default gateway | `192.168.55.1` |
| DNS server | `192.168.55.10` |
| Proxmox host | `dom` |
| VM ID | `201` |
| Resource pool | `terraform-managed` |

## Virtual hardware

| Property | Value |
|---|---|
| CPU | 2 virtual cores |
| CPU type | `host` |
| Memory | 4 GiB |
| System disk | 64 GiB |
| Disk storage | `local-lvm` |
| Disk interface | SCSI |
| Network model | VirtIO |
| Network bridge | `vmbr0` |
| QEMU Guest Agent | Enabled |
| Start on Proxmox boot | Enabled |
| Proxmox protection | Enabled |

## Operating system

| Property | Value |
|---|---|
| Distribution | Ubuntu Server 24.04.4 LTS |
| Kernel family | Linux 6.8 |
| Provisioning | Ubuntu cloud image and cloud-init |
| Primary user | `tom` |

The Ubuntu cloud image is downloaded and checksum-verified by Terraform before VM creation.

## Management

### Terraform

Terraform manages:

- the Ubuntu cloud image on `dom`;
- the Proxmox VM;
- CPU and memory allocation;
- the system disk;
- the network interface;
- static IPv4 configuration;
- cloud-init user creation;
- SSH public keys;
- QEMU Guest Agent integration;
- automatic VM startup;
- Proxmox resource protection.

Terraform configuration:

```text
terraform/dom_mysql01.tf
