#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="/opt/ai/projects/infrastructure"

source "${PROJECT_ROOT}/config/backup.env"

restic forget \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 6 \
  --keep-yearly 2 \
  --prune

restic check
