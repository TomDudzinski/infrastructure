#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "This script must be sourced into the current shell." >&2
    echo "Run: source ./scripts/load-proxmox-manage-env.sh" >&2
    exit 1
fi

_PROXMOX_SECRET_DIRECTORY="${HOME}/.config/homelab/terraform"
_DTCODE_SECRET_FILE="${_PROXMOX_SECRET_DIRECTORY}/dtcode-manage-token.json"
_DOM_SECRET_FILE="${_PROXMOX_SECRET_DIRECTORY}/dom-manage-token.json"

for _required_command in jq stat; do
    if ! command -v "${_required_command}" >/dev/null 2>&1; then
        echo "ERROR: Required command is missing: ${_required_command}" >&2
        return 1
    fi
done

for _secret_file in "${_DTCODE_SECRET_FILE}" "${_DOM_SECRET_FILE}"; do
    if [[ ! -f "${_secret_file}" ]]; then
        echo "ERROR: Secret file is missing: ${_secret_file}" >&2
        return 1
    fi

    if [[ "$(stat -c '%a' "${_secret_file}")" != "600" ]]; then
        echo "ERROR: Secret file must have mode 600: ${_secret_file}" >&2
        return 1
    fi

    if ! jq -e \
        '."full-tokenid" | type == "string" and length > 0' \
        "${_secret_file}" >/dev/null || \
       ! jq -e \
        '.value | type == "string" and length > 0' \
        "${_secret_file}" >/dev/null; then
        echo "ERROR: Invalid secret file: ${_secret_file}" >&2
        return 1
    fi
done

export TF_VAR_dtcode_manage_api_token="$(
    jq -r '."full-tokenid" + "=" + .value' "${_DTCODE_SECRET_FILE}"
)"

export TF_VAR_dom_manage_api_token="$(
    jq -r '."full-tokenid" + "=" + .value' "${_DOM_SECRET_FILE}"
)"

unset \
    _required_command \
    _secret_file \
    _PROXMOX_SECRET_DIRECTORY \
    _DTCODE_SECRET_FILE \
    _DOM_SECRET_FILE

echo "Management Proxmox Terraform credentials loaded for dtcode and dom."
