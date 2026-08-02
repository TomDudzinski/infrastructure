#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="/opt/ai/projects/infrastructure"

source "${PROJECT_ROOT}/config/backup.env"

BACKUP_PATHS=(
    "/opt/ai/projects"
    "/opt/ai/notebooks"
    "/opt/ai/datasets"
    "/opt/ai/data/open-webui"
    "/opt/ai/data/code-server"
    "/opt/ai/data/jupyter"
    "/opt/ai/backups/reports"
)

existing_paths=()

for path in "${BACKUP_PATHS[@]}"; do
    if [[ -e "${path}" ]]; then
        existing_paths+=("${path}")
    else
        echo "Skipping missing path: ${path}"
    fi
done

if [[ "${#existing_paths[@]}" -eq 0 ]]; then
    echo "No backup paths exist."
    exit 1
fi

restic backup \
    "${existing_paths[@]}" \
    --exclude-file="${PROJECT_ROOT}/config/restic-excludes.txt" \
    --tag "iza-data"
