#!/usr/bin/env bash

set -Eeuo pipefail

readonly KEY_PATH="${HOME}/.ssh/homelab_automation_ed25519"
readonly SSH_CONFIG_DIR="${HOME}/.ssh/config.d"
readonly SSH_CONFIG_FILE="${SSH_CONFIG_DIR}/homelab.conf"
readonly MAIN_SSH_CONFIG="${HOME}/.ssh/config"

usage() {
    cat <<'EOF'
Usage:
  setup-automation-ssh.sh              Create the key and SSH aliases
  setup-automation-ssh.sh --install-key  Install the public key on both Proxmox hosts
  setup-automation-ssh.sh --test         Test key-based SSH connections

The script never overwrites an existing private key.
EOF
}

ensure_ssh_layout() {
    install -d -m 700 "${HOME}/.ssh" "${SSH_CONFIG_DIR}"
    touch "${MAIN_SSH_CONFIG}"
    chmod 600 "${MAIN_SSH_CONFIG}"

    if ! grep -Fqx 'Include ~/.ssh/config.d/*' "${MAIN_SSH_CONFIG}"; then
        {
            printf '%s\n' 'Include ~/.ssh/config.d/*'
            cat "${MAIN_SSH_CONFIG}"
        } > "${MAIN_SSH_CONFIG}.new"
        chmod 600 "${MAIN_SSH_CONFIG}.new"
        mv "${MAIN_SSH_CONFIG}.new" "${MAIN_SSH_CONFIG}"
    fi
}

ensure_key() {
    if [[ -e "${KEY_PATH}" || -e "${KEY_PATH}.pub" ]]; then
        if [[ ! -f "${KEY_PATH}" || ! -f "${KEY_PATH}.pub" ]]; then
            printf 'ERROR: Incomplete key pair at %s. Resolve it manually.\n' "${KEY_PATH}" >&2
            exit 1
        fi
        printf 'Using existing key pair: %s\n' "${KEY_PATH}"
        return
    fi

    ssh-keygen \
        -t ed25519 \
        -a 100 \
        -f "${KEY_PATH}" \
        -C 'homelab-automation@iza'
    chmod 600 "${KEY_PATH}"
    chmod 644 "${KEY_PATH}.pub"
}

write_host_config() {
    if [[ -e "${SSH_CONFIG_FILE}" ]]; then
        printf 'ERROR: %s already exists; it was not overwritten.\n' "${SSH_CONFIG_FILE}" >&2
        exit 1
    fi

    install -m 600 /dev/null "${SSH_CONFIG_FILE}"
    printf '%s\n' \
        'Host dtcode proxmox1' \
        '    HostName 192.168.55.6' \
        '    User root' \
        '    IdentityFile ~/.ssh/homelab_automation_ed25519' \
        '    IdentitiesOnly yes' \
        '' \
        'Host dom proxmox2' \
        '    HostName 192.168.55.3' \
        '    User root' \
        '    IdentityFile ~/.ssh/homelab_automation_ed25519' \
        '    IdentitiesOnly yes' \
        > "${SSH_CONFIG_FILE}"
}

configure() {
    ensure_ssh_layout
    ensure_key

    if [[ -f "${SSH_CONFIG_FILE}" ]]; then
        printf 'Using existing host configuration: %s\n' "${SSH_CONFIG_FILE}"
    else
        write_host_config
        printf 'Created host configuration: %s\n' "${SSH_CONFIG_FILE}"
    fi

    ssh -G dtcode >/dev/null
    ssh -G dom >/dev/null
    printf 'SSH aliases validated.\n'
}

install_key() {
    configure
    printf 'Installing the public key on dtcode. Verify the host fingerprint before accepting it.\n'
    ssh-copy-id -i "${KEY_PATH}.pub" dtcode
    printf 'Installing the public key on dom. Verify the host fingerprint before accepting it.\n'
    ssh-copy-id -i "${KEY_PATH}.pub" dom
}

test_connections() {
    configure
    ssh -o BatchMode=yes -o ConnectTimeout=5 dtcode 'hostname && pveversion'
    ssh -o BatchMode=yes -o ConnectTimeout=5 dom 'hostname && pveversion'
}

case "${1:-}" in
    '')
        configure
        ;;
    --install-key)
        install_key
        ;;
    --test)
        test_connections
        ;;
    -h|--help)
        usage
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac