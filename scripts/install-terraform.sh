#!/usr/bin/env bash

set -Eeuo pipefail

readonly EXPECTED_FINGERPRINT="798AEC654E5C15428C8E42EEAA16FCBCA621E701"
readonly KEYRING_PATH="/usr/share/keyrings/hashicorp-archive-keyring.gpg"
readonly REPOSITORY_PATH="/etc/apt/sources.list.d/hashicorp.list"

if [[ "${EUID}" -ne 0 ]]; then
    echo "This script must be run with sudo."
    echo "Run: sudo ./scripts/install-terraform.sh"
    exit 1
fi

if [[ ! -r /etc/os-release ]]; then
    echo "ERROR: /etc/os-release is not available." >&2
    exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release

if [[ "${ID:-}" != "ubuntu" && "${ID:-}" != "debian" ]]; then
    echo "ERROR: Unsupported operating system: ${ID:-unknown}." >&2
    exit 1
fi

if [[ -z "${VERSION_CODENAME:-}" ]]; then
    echo "ERROR: The operating system codename is not available." >&2
    exit 1
fi

if [[ "$(dpkg --print-architecture)" != "amd64" ]]; then
    echo "ERROR: This installer currently supports amd64 only." >&2
    exit 1
fi

temporary_directory="$(mktemp -d)"
trap 'rm -rf -- "${temporary_directory}"' EXIT

echo "Installing repository dependencies..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates \
    curl \
    gnupg

echo "Downloading the HashiCorp repository signing key..."
curl -fsSL \
    https://apt.releases.hashicorp.com/gpg \
    -o "${temporary_directory}/hashicorp.asc"

actual_fingerprint="$(
    gpg --batch --show-keys --with-colons \
        "${temporary_directory}/hashicorp.asc" |
        awk -F: '$1 == "fpr" { print $10; exit }'
)"

if [[ "${actual_fingerprint}" != "${EXPECTED_FINGERPRINT}" ]]; then
    echo "ERROR: The HashiCorp signing-key fingerprint does not match." >&2
    echo "Expected: ${EXPECTED_FINGERPRINT}" >&2
    echo "Received: ${actual_fingerprint:-missing}" >&2
    exit 1
fi

echo "Verified HashiCorp signing-key fingerprint: ${actual_fingerprint}"

gpg --batch --yes --dearmor \
    --output "${temporary_directory}/hashicorp.gpg" \
    "${temporary_directory}/hashicorp.asc"
install -m 0644 "${temporary_directory}/hashicorp.gpg" "${KEYRING_PATH}"

echo "Configuring the HashiCorp repository for ${VERSION_CODENAME}..."
printf '%s\n' \
    "deb [arch=amd64 signed-by=${KEYRING_PATH}] https://apt.releases.hashicorp.com ${VERSION_CODENAME} main" \
    > "${REPOSITORY_PATH}"
chmod 0644 "${REPOSITORY_PATH}"

echo "Installing Terraform..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y terraform

echo
terraform version
echo
echo "Terraform installed successfully."
