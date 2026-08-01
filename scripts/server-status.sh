#!/usr/bin/env bash

set -euo pipefail

echo "========================================"
echo " IZA AI SERVER STATUS"
echo "========================================"
echo

echo "--- System ---"
hostnamectl --static
uptime
echo

echo "--- CPU and memory ---"
free -h
echo

echo "--- Disk usage ---"
df -h / /opt/ai
echo

echo "--- GPU ---"
nvidia-smi \
  --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,driver_version \
  --format=csv,noheader
echo

echo "--- Docker containers ---"
docker ps \
  --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo

echo "--- Ollama models ---"
docker exec ollama ollama list 2>/dev/null || echo "Ollama is unavailable"
