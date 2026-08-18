# Backup

## Purpose

The HomeLab backup system protects infrastructure configuration, application data and recovery information.

Restic provides encrypted, deduplicated and integrity-checked backups.

## Current backup layers

| Layer | Repository | Purpose | Status |
|---|---|---|---|
| Local Restic | Configured through `config/backup.env` | Existing configuration and application-data backups | Active |
| QNAP Restic | `/mnt/qnap-backup/AI/iza/restic` | Independent infrastructure configuration backup | Active |
| MySQL logical backup | Not configured | Database backup and point-in-time recovery | Required |

The QNAP repository is independent from the existing local Restic repository.

## QNAP storage

The QNAP NFS export is:

```text
192.168.55.5:/Backup
```

It is mounted on `iza` at:

```text
/mnt/qnap-backup
```

The verified filesystem is NFS 4.1.

The independent Restic repository is:

```text
/mnt/qnap-backup/AI/iza/restic
```

## Protected infrastructure configuration

The QNAP configuration backup includes:

```text
/opt/ai/projects/infrastructure
```

This includes:

- Terraform configuration;
- ignored local Terraform state;
- Ansible configuration;
- inventory;
- playbooks and roles;
- infrastructure scripts;
- project documentation;
- Docker Compose configuration stored in the repository.

The backup excludes:

```text
.git
config/backup.env
config/restic-password
```

Secrets must be protected separately. Excluding a secret from the repository backup does not replace a documented credential-recovery procedure.

## Backup scripts

### Complete existing workflow

```bash
./scripts/backup-all.sh
```

This workflow creates reports, backs up configuration and application data, and checks the configured Restic repository.

### Existing configuration backup

```bash
./scripts/backup-config.sh
```

### QNAP infrastructure backup

```bash
./scripts/backup-config-qnap.sh
```

The QNAP script verifies:

- the expected NFS mount;
- the repository path;
- the Restic password file;
- restrictive password-file permissions;
- repository availability.

It creates snapshots with the tags:

```text
qnap
infrastructure-config
```

## Password handling

The Restic password file is:

```text
config/restic-password
```

Requirements:

- mode `600`;
- ownership by `tom`;
- excluded from Git;
- not displayed in terminal transcripts;
- protected by a separate recovery procedure.

Loss of the Restic password makes the repository unrecoverable.

## Configuration handling

The existing backup environment is loaded from:

```text
config/backup.env
```

This file is excluded from Git.

Do not display its contents in logs or terminal transcripts if it contains credentials or repository access information.

## Manual QNAP backup

Run from the repository root:

```bash
cd /opt/ai/projects/infrastructure
./scripts/backup-config-qnap.sh
```

List recent snapshots:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  snapshots --latest 5
```

## Integrity check

Check repository metadata and stored packs:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  check
```

A successful check was completed on `2026-08-17`.

A full data read can be performed periodically:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  check --read-data
```

## Restore test

An actual restore test was completed successfully on `2026-08-17`.

Verified source snapshot:

```text
aa5c516e
```

The infrastructure repository was restored to a temporary directory. Restic reported:

```text
113 files and directories
27.553 MiB
```

The restored data was inspected successfully.

A repository check alone is not a restore test. Restore tests must create files in a separate destination and verify expected content.

## Safe restore example

Create a temporary destination:

```bash
RESTORE_TEST_DIRECTORY="$(mktemp -d /tmp/restic-qnap-restore.XXXXXX)"
```

Restore the latest infrastructure snapshot:

```bash
restic \
  --repo /mnt/qnap-backup/AI/iza/restic \
  --password-file config/restic-password \
  restore latest \
  --tag infrastructure-config \
  --target "${RESTORE_TEST_DIRECTORY}"
```

Inspect the restored repository:

```bash
find "${RESTORE_TEST_DIRECTORY}" \
  -maxdepth 5 \
  -type f \
  -print |
sort |
sed -n '1,100p'
```

Do not restore directly over the live repository during a test.

## Terraform state recovery

Terraform state is stored locally at:

```text
terraform/state/terraform.tfstate
```

It is ignored by Git but included in the QNAP infrastructure backup.

Before replacing the live state:

1. stop all Terraform operations;
2. preserve the current state file;
3. restore to a temporary directory;
4. verify the restored file;
5. compare state contents without exposing sensitive values;
6. replace the live state only with explicit approval;
7. run `terraform plan`;
8. investigate all unexpected changes before applying anything.

## MySQL backup gap

MySQL is running on `mysql01`, but a database-aware backup has not yet been configured.

A filesystem or VM backup taken while MySQL is active is not automatically equivalent to a verified logical database backup.

Before production use, implement:

- scheduled logical backups;
- encrypted backup storage;
- retention;
- backup monitoring;
- restore automation;
- an actual restore test;
- documentation of recovery time and recovery point expectations.

## Retention

The existing local Restic workflow has a separate retention script:

```bash
./scripts/backup-retention.sh
```

A reviewed retention policy for the independent QNAP repository still needs to be documented and implemented.

Do not apply `forget --prune` to the new repository until the retention rules and recovery requirements have been reviewed.

## Monitoring

Backup jobs must eventually report:

- successful completion;
- failed snapshots;
- repository lock problems;
- repository check failures;
- missing NFS mount;
- insufficient QNAP space;
- age of the newest valid snapshot;
- restore-test status.

Central alerting is not currently configured.

## Recovery priorities

1. Preserve credentials required to open backup repositories.
2. Restore infrastructure documentation and automation.
3. Restore Terraform state.
4. Restore service configuration.
5. Recreate virtual infrastructure.
6. Restore application and database data.
7. Verify service availability and security controls.

## Remaining work

- document secure recovery of the Restic password;
- define QNAP repository retention;
- automate regular QNAP snapshots;
- schedule full repository checks;
- schedule restore tests;
- configure MySQL logical backups;
- test MySQL restore;
- implement backup monitoring and alerting;
- document complete disaster-recovery procedures.