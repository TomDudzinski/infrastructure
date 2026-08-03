# QNAP TS-253D

## System

- Model: TS-253D
- Address: 192.168.55.5
- Operating system: QTS 5.1.9.2954
- Disks: 2 x 4 TB
- Purpose: central backup storage for the homelab

## Backup share

- Shared folder: Backup
- Protocol: NFS
- Access: restricted to the Iza AI server IP
- Mount point on Iza: /mnt/qnap-backup

## Planned structure

- /AI/iza/restic
- /AI/iza/reports
- /Proxmox
- /Windows
- /Archive
