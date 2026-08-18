# Restic

## Purpose

Restic provides encrypted, deduplicated and integrity-checked backups for the HomeLab infrastructure.

This document describes repository access and technical verification. The complete backup and recovery policy is documented in `BACKUP.md`.

## Repositories

### Existing repository

The existing repository is configured through:

```text
config/backup.env
```

Use the existing project commands:

```bash
make backup-list
make backup-check
make backup-check-full
```

### QNAP infrastructure repository

| Property | Value |
|---|---|
| Repository | `/mnt/qnap-backup/AI/iza/restic` |
| Storage | QNAP NFS export |
| Mount point | `/mnt/qnap-backup` |
| Password file | `config/restic-password` |
| Repository format | Restic repository version 2 |
| Repository ID prefix | `a64b8b3f` |
| Status | Initialized and verified |

## Prerequisites

Verify that the QNAP export is mounted:

```bash
findmnt --target /mnt/qnap-backup
```

Expected source:

```text
192.168.55.5:/Backup
```

Verify available storage:

```bash
df -hT /mnt/qnap-backup
```

Verify password-file permissions without displaying its contents:

```bash
stat -c '%A %a %U:%G %n' config/restic-password
```

Expected mode:

```text
600
```

## Environment variables

For repeated manual commands, define non-sensitive shell variables:

```bash
RESTIC_QNAP_REPOSITORY="/mnt/qnap-backup/AI/iza/restic"
RESTIC_QNAP_PASSWORD_FILE="/opt/ai/projects/infrastructure/config/restic-password"
```

Do not reuse common system variable names.

## Repository access test

```bash
restic \
  --repo "${RESTIC_QNAP_REPOSITORY}" \
  --password-file "${RESTIC_QNAP_PASSWORD_FILE}" \
  snapshots
```

## Backup

Use the project script:

```bash
cd /opt/ai/projects/infrastructure
./scripts/backup-config-qnap.sh
```

Equivalent manual backup:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  backup /opt/ai/projects/infrastructure \
  --exclude .git \
  --exclude config/backup.env \
  --exclude config/restic-password \
  --tag qnap \
  --tag infrastructure-config
```

The project script is preferred because it performs prerequisite checks.

## Snapshot listing

List the latest snapshots:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  snapshots --latest 5
```

List only infrastructure configuration snapshots:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  snapshots \
  --tag infrastructure-config
```

## Repository integrity

Standard check:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  check
```

Full stored-data check:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  check --read-data
```

The standard check completed successfully on `2026-08-17`.

## Locks

Display repository locks:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  list locks
```

Do not remove a lock until all backup, restore, check and retention processes using the repository have been confirmed stopped.

Unlock only after verification:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  unlock
```

## Restore test

Create a unique temporary directory:

```bash
RESTIC_RESTORE_DIRECTORY="$(mktemp -d /tmp/restic-qnap-restore.XXXXXX)"
```

Restore the latest tagged snapshot:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  restore latest \
  --tag infrastructure-config \
  --target "${RESTIC_RESTORE_DIRECTORY}"
```

Locate the restored repository:

```bash
find "${RESTIC_RESTORE_DIRECTORY}" \
  -type d \
  -path '*/opt/ai/projects/infrastructure' \
  -print
```

Verify expected files:

```bash
find "${RESTIC_RESTORE_DIRECTORY}" \
  -type f \
  \( \
    -name 'backend.tf' \
    -o -name 'dom_mysql01.tf' \
    -o -name 'mysql01-bootstrap.yml' \
    -o -name 'terraform.tfstate' \
  \) \
  -print
```

Do not restore directly over the live repository during a test.

## Verified restore

An actual restore test completed successfully on `2026-08-17`.

| Property | Value |
|---|---|
| Snapshot | `aa5c516e` |
| Restored objects | 113 files and directories |
| Restored size | 27.553 MiB |
| Destination | Temporary directory under `/tmp` |
| Result | Successful |

## Terraform state

The Terraform state is ignored by Git but included in the repository backup because the backup source is the complete infrastructure directory.

Expected state path:

```text
/opt/ai/projects/infrastructure/terraform/state/terraform.tfstate
```

After a test restore, verify that the state exists without printing its contents.

## Retention safety

Do not run retention or pruning commands against the QNAP repository until its policy has been reviewed.

Before running `forget --prune`:

1. verify the repository path;
2. verify the selected snapshot policy;
3. list snapshots;
4. run a dry run;
5. confirm recent successful backups;
6. confirm the latest restore test;
7. obtain explicit approval.

## Cache

Restic may create a local cache under:

```text
~/.cache/restic
```

The cache is disposable and is not a backup repository.

Repository checks may use a temporary cache under `/tmp`.

## Security

- Never commit the password file.
- Never print the Restic password.
- Do not enable shell tracing around credential handling.
- Do not expose repository configuration containing credentials.
- Protect the QNAP export from unauthorized clients.
- Keep a separate recovery copy of the repository password.
- Test password recovery before depending on the repository.

## References

- Main backup policy: `docs/backup/BACKUP.md`
- Disaster recovery: `docs/operations/disaster-recovery.md`
- Backup scripts: `scripts/`