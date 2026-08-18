#!/usr/bin/env bash

set -Eeuo pipefail

if [[ "${EUID}" -ne 0 ]]; then
    echo "This script must be run with sudo."
    echo "Run: sudo ./scripts/install-host-dependencies.sh"
    exit 1
fi

PACKAGES=(
    ansible-core
    btop
    ca-certificates
    curl
    git
    htop
    jq
    lm-sensors
    make
    nvtop
    openssl
    ripgrep
    smartmontools
    sysstat
    tree
    unzip
    vim
    wget
    zip
)

echo "Updating APT package index..."
apt-get update

echo "Installing host dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -y "${PACKAGES[@]}"

echo
echo "Installed packages:"
printf ' - %s\n' "${PACKAGES[@]}"

echo
echo "Host dependencies installed successfully."
echo "You can run 'sudo sensors-detect' separately if sensor detection is required."
