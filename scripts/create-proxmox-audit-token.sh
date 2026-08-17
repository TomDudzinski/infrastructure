#!/usr/bin/env bash

set -Eeuo pipefail

readonly REMOTE_USER="terraform-audit@pve"
readonly TOKEN_NAME="provider"
readonly TOKEN_ID="${REMOTE_USER}!${TOKEN_NAME}"
readonly SECRET_DIRECTORY="${HOME}/.config/homelab/terraform"

usage() {
    cat <<'EOF'
Usage:
  create-proxmox-audit-token.sh dtcode
  create-proxmox-audit-token.sh dom

Creates a privilege-separated Proxmox API token with the PVEAuditor role.
The token secret is stored locally and is never printed to the terminal.
EOF
}

if [[ $# -ne 1 ]]; then
    usage >&2
    exit 2
fi

readonly TARGET_HOST="$1"

case "${TARGET_HOST}" in
    -h|--help)
        usage
        exit 0
        ;;
    dtcode|dom)
        ;;
    *)
        echo "ERROR: Supported hosts are dtcode and dom." >&2
        exit 2
        ;;
esac

for command_name in ssh jq install mktemp; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo "ERROR: Required command is missing: ${command_name}" >&2
        exit 1
    fi
done

install -d -m 700 "${SECRET_DIRECTORY}"
readonly SECRET_FILE="${SECRET_DIRECTORY}/${TARGET_HOST}-audit-token.json"

if [[ -e "${SECRET_FILE}" ]]; then
    echo "ERROR: Secret file already exists: ${SECRET_FILE}" >&2
    exit 1
fi

echo "Checking the existing Proxmox identity on ${TARGET_HOST}..."

users_json="$(ssh "${TARGET_HOST}" 'pveum user list --output-format json')"
if jq -e --arg user "${REMOTE_USER}" \
    'any(.[]; .userid == $user)' <<<"${users_json}" >/dev/null; then
    echo "ERROR: User ${REMOTE_USER} already exists on ${TARGET_HOST}." >&2
    echo "Resolve the existing identity manually; no changes were made." >&2
    exit 1
fi

temporary_file="$(mktemp "${SECRET_DIRECTORY}/.${TARGET_HOST}.token.XXXXXX")"
chmod 600 "${temporary_file}"
trap 'rm -f -- "${temporary_file}"' EXIT

echo "Creating the audit user on ${TARGET_HOST}..."
ssh "${TARGET_HOST}" \
    "pveum user add '${REMOTE_USER}' --comment 'Terraform read-only audit from iza'"

echo "Granting PVEAuditor to the backing user on ${TARGET_HOST}..."
ssh "${TARGET_HOST}" \
    "pveum acl modify / --users '${REMOTE_USER}' --roles PVEAuditor"

echo "Creating the privilege-separated API token on ${TARGET_HOST}..."
ssh "${TARGET_HOST}" \
    "pveum user token add '${REMOTE_USER}' '${TOKEN_NAME}' --privsep 1 --output-format json" \
    > "${temporary_file}"

if ! jq -e \
    --arg token_id "${TOKEN_ID}" \
    '."full-tokenid" == $token_id and (.value | type == "string" and length > 0)' \
    "${temporary_file}" >/dev/null; then
    echo "ERROR: Proxmox returned an unexpected token response." >&2
    echo "The token may exist remotely. Inspect it before retrying." >&2
    exit 1
fi

install -m 600 "${temporary_file}" "${SECRET_FILE}"

echo "Granting PVEAuditor to the separated token on ${TARGET_HOST}..."
if ! ssh "${TARGET_HOST}" \
    "pveum acl modify / --tokens '${TOKEN_ID}' --roles PVEAuditor"; then
    echo "ERROR: The token was created, but its ACL could not be assigned." >&2
    echo "The secret remains protected at: ${SECRET_FILE}" >&2
    exit 1
fi

echo "Verifying effective token permissions on ${TARGET_HOST}..."
ssh "${TARGET_HOST}" \
    "pveum user permissions '${REMOTE_USER}' --path / --output-format json" \
    >/dev/null

echo "Audit token created successfully for ${TARGET_HOST}."
echo "Protected secret file: ${SECRET_FILE}"
echo "Do not display or commit this file."
