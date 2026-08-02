#!/usr/bin/env bash

set -Eeuo pipefail

REPORT_DIR="/opt/ai/backups/reports"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
REPORT_FILE="${REPORT_DIR}/server-${TIMESTAMP}.txt"

mkdir -p "${REPORT_DIR}"

{
    echo "IZA AI SERVER BACKUP REPORT"
    echo "Generated: $(date --iso-8601=seconds)"
    echo

    echo "=== SYSTEM ==="
    hostnamectl
    echo

    echo "=== OPERATING SYSTEM ==="
    cat /etc/os-release
    echo

    echo "=== STORAGE ==="
    lsblk
    echo
    df -h
    echo

    echo "=== MEMORY ==="
    free -h
    echo

    echo "=== GPU ==="
    nvidia-smi
    echo

    echo "=== DOCKER VERSION ==="
    docker version
    echo

    echo "=== DOCKER CONTAINERS ==="
    docker ps -a
    echo

    echo "=== DOCKER IMAGES ==="
    docker image ls
    echo

    echo "=== DOCKER VOLUMES ==="
    docker volume ls
    echo

    echo "=== OLLAMA MODELS ==="
    docker exec ollama ollama list 2>/dev/null || echo "Ollama unavailable"
    echo

    echo "=== INSTALLED APT PACKAGES ==="
    dpkg-query -W -f='${binary:Package}\t${Version}\n'
} > "${REPORT_FILE}"

ln -sfn "${REPORT_FILE}" "${REPORT_DIR}/latest.txt"

echo "Report created: ${REPORT_FILE}"
