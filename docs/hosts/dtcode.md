# dtcode

## Type

Proxmox VE host

## Address

192.168.55.6

## Role

Smaller virtualization host.

## Known workloads

- dns01
- home01
- forgejo01
- npm01
- tailscale-router

## Management

Terraform is currently used to create virtual machines and containers.

Some application provisioning is currently performed using Terraform provisioners.

Target state:

Terraform + Ansible.
