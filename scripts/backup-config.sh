#!/usr/bin/env bash

set -Eeuo pipefail

source /opt/ai/projects/infrastructure/config/backup.env

restic backup \
  /opt/ai/projects/infrastructure \
  --exclude .git \
  --exclude config/backup.env \
  --exclude config/restic-password
