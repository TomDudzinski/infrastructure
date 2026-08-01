#!/usr/bin/env bash

set -euo pipefail

failed=0

check_url() {
    local name="$1"
    local url="$2"

    if curl --silent --fail --max-time 5 "$url" > /dev/null; then
        echo "[OK] $name"
    else
        echo "[FAIL] $name"
        failed=1
    fi
}

check_container() {
    local name="$1"

    if docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null | grep -q true; then
        echo "[OK] Container: $name"
    else
        echo "[FAIL] Container: $name"
        failed=1
    fi
}

check_container "ollama"
check_container "open-webui"
check_container "code-server"
check_container "jupyter"

check_url "Ollama API" "http://127.0.0.1:11434/api/tags"
check_url "Open WebUI" "http://127.0.0.1:3000"
check_url "code-server" "http://127.0.0.1:8443"
check_url "JupyterLab" "http://127.0.0.1:8888"

exit "$failed"
