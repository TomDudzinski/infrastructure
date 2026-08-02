#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="/opt/ai/projects/infrastructure"

echo "Creating system report..."
"${PROJECT_ROOT}/scripts/backup-report.sh"

echo
echo "Backing up infrastructure configuration..."
"${PROJECT_ROOT}/scripts/backup-config.sh"

echo
echo "Backing up projects and application data..."
"${PROJECT_ROOT}/scripts/backup-data.sh"

echo
echo "Checking repository..."
source "${PROJECT_ROOT}/config/backup.env"
restic check

echo
echo "Backup completed successfully."
restic snapshots --latest 5
