#!/usr/bin/env bash

set -Eeuo pipefail

readonly PROJECT_ROOT="/opt/ai/projects/infrastructure"
readonly QNAP_MOUNT="/mnt/qnap-backup"
readonly QNAP_REPOSITORY="${QNAP_MOUNT}/AI/iza/restic"
readonly PASSWORD_FILE="${PROJECT_ROOT}/config/restic-password"

for command_name in restic findmnt; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo "ERROR: Required command is missing: ${command_name}" >&2
        exit 1
    fi
done

if ! findmnt \
    --noheadings \
    --target "${QNAP_MOUNT}" \
    --types nfs,nfs4 \
    >/dev/null; then
    echo "ERROR: QNAP NFS storage is not mounted at ${QNAP_MOUNT}." >&2
    exit 1
fi

if [[ ! -f "${PASSWORD_FILE}" ]]; then
    echo "ERROR: Restic password file is missing: ${PASSWORD_FILE}" >&2
    exit 1
fi

if [[ "$(stat -c '%a' "${PASSWORD_FILE}")" != "600" ]]; then
    echo "ERROR: Restic password file must have mode 600." >&2
    exit 1
fi

if [[ ! -f "${QNAP_REPOSITORY}/config" ]]; then
    echo "ERROR: Restic repository is not initialized: ${QNAP_REPOSITORY}" >&2
    exit 1
fi

restic \
    --repo "${QNAP_REPOSITORY}" \
    --password-file "${PASSWORD_FILE}" \
    backup "${PROJECT_ROOT}" \
    --exclude .git \
    --exclude config/backup.env \
    --exclude config/restic-password \
    --tag qnap \
    --tag infrastructure-config
