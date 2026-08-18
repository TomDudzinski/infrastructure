#!/usr/bin/env bash

set -Eeuo pipefail

readonly REMOTE_USER="terraform-manage@pve"
readonly TOKEN_NAME="provider"
readonly TOKEN_ID="${REMOTE_USER}!${TOKEN_NAME}"
readonly SECRET_DIRECTORY="${HOME}/.config/homelab/terraform"

readonly POOL_ID="terraform-managed"

readonly VM_ROLE="TerraformVMManager"
readonly VM_PRIVILEGES="Pool.Audit Sys.Audit VM.Allocate VM.Audit VM.Clone VM.Config.CDROM VM.Config.Cloudinit VM.Config.CPU VM.Config.Disk VM.Config.HWType VM.Config.Memory VM.Config.Network VM.Config.Options VM.PowerMgmt"

readonly STORAGE_ROLE="TerraformStorageManager"
readonly STORAGE_PRIVILEGES="Datastore.AllocateSpace Datastore.AllocateTemplate Datastore.Audit"

readonly NODE_ROLE="TerraformNodeAuditor"
readonly DTCODE_NODE_PRIVILEGES="Sys.Audit"
readonly DOM_NODE_PRIVILEGES="Sys.AccessNetwork Sys.Audit"

readonly NETWORK_ROLE="TerraformNetworkUser"
readonly NETWORK_PRIVILEGES="SDN.Use"
readonly NETWORK_PATH="/sdn/zones/localnetwork/vmbr0"

usage() {
    cat <<'EOF'
Usage:
  create-proxmox-management-token.sh dtcode
  create-proxmox-management-token.sh dom

Creates a privilege-separated Proxmox API identity for Terraform.

Access is limited to:
  - the terraform-managed resource pool;
  - local and local-lvm storage;
  - read-only node information;
  - the vmbr0 local network bridge.

The dom host additionally receives Sys.AccessNetwork because Proxmox VE 9
requires it to query URL metadata and download cloud images.

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

case "${TARGET_HOST}" in
    dtcode)
        readonly NODE_PRIVILEGES="${DTCODE_NODE_PRIVILEGES}"
        ;;
    dom)
        readonly NODE_PRIVILEGES="${DOM_NODE_PRIVILEGES}"
        ;;
esac

for command_name in ssh jq install mktemp; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo "ERROR: Required command is missing: ${command_name}" >&2
        exit 1
    fi
done

install -d -m 700 "${SECRET_DIRECTORY}"
readonly SECRET_FILE="${SECRET_DIRECTORY}/${TARGET_HOST}-manage-token.json"

if [[ -e "${SECRET_FILE}" ]]; then
    echo "ERROR: Secret file already exists: ${SECRET_FILE}" >&2
    exit 1
fi

echo "Checking existing Proxmox objects on ${TARGET_HOST}..."

users_json="$(ssh "${TARGET_HOST}" 'pveum user list --output-format json')"

if jq -e --arg user "${REMOTE_USER}" \
    'any(.[]; .userid == $user)' <<<"${users_json}" >/dev/null; then
    echo "ERROR: User ${REMOTE_USER} already exists on ${TARGET_HOST}." >&2
    echo "Resolve the existing identity manually; no changes were made." >&2
    exit 1
fi

roles_json="$(ssh "${TARGET_HOST}" 'pveum role list --output-format json')"

for role_name in \
    "${VM_ROLE}" \
    "${STORAGE_ROLE}" \
    "${NODE_ROLE}" \
    "${NETWORK_ROLE}"; do
    if jq -e --arg role "${role_name}" \
        'any(.[]; .roleid == $role)' <<<"${roles_json}" >/dev/null; then
        echo "ERROR: Role already exists on ${TARGET_HOST}: ${role_name}" >&2
        echo "Resolve the existing role manually; no changes were made." >&2
        exit 1
    fi
done

pools_json="$(ssh "${TARGET_HOST}" 'pvesh get /pools --output-format json')"

if jq -e --arg pool "${POOL_ID}" \
    'any(.[]; .poolid == $pool)' <<<"${pools_json}" >/dev/null; then
    echo "ERROR: Pool already exists on ${TARGET_HOST}: ${POOL_ID}" >&2
    echo "Resolve the existing pool manually; no changes were made." >&2
    exit 1
fi

temporary_file="$(
    mktemp "${SECRET_DIRECTORY}/.${TARGET_HOST}.manage-token.XXXXXX"
)"
chmod 600 "${temporary_file}"
trap 'rm -f -- "${temporary_file}"' EXIT

echo "Creating Terraform roles on ${TARGET_HOST}..."

ssh "${TARGET_HOST}" \
    "pveum role add '${VM_ROLE}' --privs '${VM_PRIVILEGES}'"

ssh "${TARGET_HOST}" \
    "pveum role add '${STORAGE_ROLE}' --privs '${STORAGE_PRIVILEGES}'"

ssh "${TARGET_HOST}" \
    "pveum role add '${NODE_ROLE}' --privs '${NODE_PRIVILEGES}'"

ssh "${TARGET_HOST}" \
    "pveum role add '${NETWORK_ROLE}' --privs '${NETWORK_PRIVILEGES}'"

echo "Creating the Terraform resource pool on ${TARGET_HOST}..."

ssh "${TARGET_HOST}" \
    "pveum pool add '${POOL_ID}' --comment 'Resources managed by Terraform'"

echo "Creating the management user on ${TARGET_HOST}..."

ssh "${TARGET_HOST}" \
    "pveum user add '${REMOTE_USER}' --comment 'Terraform management from iza'"

echo "Granting backing-user permissions on ${TARGET_HOST}..."

ssh "${TARGET_HOST}" \
    "pveum acl modify '/pool/${POOL_ID}' --users '${REMOTE_USER}' --roles '${VM_ROLE}'"

ssh "${TARGET_HOST}" \
    "pveum acl modify '/storage/local' --users '${REMOTE_USER}' --roles '${STORAGE_ROLE}'"

ssh "${TARGET_HOST}" \
    "pveum acl modify '/storage/local-lvm' --users '${REMOTE_USER}' --roles '${STORAGE_ROLE}'"

ssh "${TARGET_HOST}" \
    "pveum acl modify '/nodes/${TARGET_HOST}' --users '${REMOTE_USER}' --roles '${NODE_ROLE}'"

ssh "${TARGET_HOST}" \
    "pveum acl modify '${NETWORK_PATH}' --users '${REMOTE_USER}' --roles '${NETWORK_ROLE}'"

echo "Creating the privilege-separated API token on ${TARGET_HOST}..."

ssh "${TARGET_HOST}" \
    "pveum user token add '${REMOTE_USER}' '${TOKEN_NAME}' --privsep 1 --output-format json" \
    >"${temporary_file}"

if ! jq -e \
    --arg token_id "${TOKEN_ID}" \
    '."full-tokenid" == $token_id and (.value | type == "string" and length > 0)' \
    "${temporary_file}" >/dev/null; then
    echo "ERROR: Proxmox returned an unexpected token response." >&2
    echo "The token may exist remotely. Inspect it before retrying." >&2
    exit 1
fi

install -m 600 "${temporary_file}" "${SECRET_FILE}"

echo "Granting separated-token permissions on ${TARGET_HOST}..."

ssh "${TARGET_HOST}" \
    "pveum acl modify '/pool/${POOL_ID}' --tokens '${TOKEN_ID}' --roles '${VM_ROLE}'"

ssh "${TARGET_HOST}" \
    "pveum acl modify '/storage/local' --tokens '${TOKEN_ID}' --roles '${STORAGE_ROLE}'"

ssh "${TARGET_HOST}" \
    "pveum acl modify '/storage/local-lvm' --tokens '${TOKEN_ID}' --roles '${STORAGE_ROLE}'"

ssh "${TARGET_HOST}" \
    "pveum acl modify '/nodes/${TARGET_HOST}' --tokens '${TOKEN_ID}' --roles '${NODE_ROLE}'"

ssh "${TARGET_HOST}" \
    "pveum acl modify '${NETWORK_PATH}' --tokens '${TOKEN_ID}' --roles '${NETWORK_ROLE}'"

echo "Verifying the resulting ACL configuration on ${TARGET_HOST}..."

ssh "${TARGET_HOST}" \
    "pveum acl list --output-format json" |
    jq -e \
        --arg user "${REMOTE_USER}" \
        --arg token "${TOKEN_ID}" \
        --arg pool_path "/pool/${POOL_ID}" \
        --arg node_path "/nodes/${TARGET_HOST}" \
        --arg local_storage_path "/storage/local" \
        --arg local_lvm_storage_path "/storage/local-lvm" \
        --arg network_path "${NETWORK_PATH}" \
        '
        any(.[]; .ugid == $user and .path == $pool_path) and
        any(.[]; .ugid == $token and .path == $pool_path) and
        any(.[]; .ugid == $user and .path == $node_path) and
        any(.[]; .ugid == $token and .path == $node_path) and
        any(.[]; .ugid == $user and .path == $local_storage_path) and
        any(.[]; .ugid == $token and .path == $local_storage_path) and
        any(.[]; .ugid == $user and .path == $local_lvm_storage_path) and
        any(.[]; .ugid == $token and .path == $local_lvm_storage_path) and
        any(.[]; .ugid == $user and .path == $network_path) and
        any(.[]; .ugid == $token and .path == $network_path)
        ' \
        >/dev/null

echo "Management token created successfully for ${TARGET_HOST}."
echo "Protected secret file: ${SECRET_FILE}"
echo "Do not display or commit this file."