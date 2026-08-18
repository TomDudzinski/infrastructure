# OpenBao Recovery Procedure

## Purpose

This procedure describes how to verify, unseal, and recover the HomeLab OpenBao server `bao01`.

It intentionally does not contain unseal keys, root tokens, passwords, private keys, or other secrets.

## Server information

| Property | Value |
|---|---|
| Host | `bao01` |
| FQDN | `bao01.home.lab` |
| Address | `192.168.55.24` |
| OpenBao API | `https://bao01.home.lab:8200` |
| Public HomeLab endpoint | `https://bao01.home.lab` |
| Storage | Integrated Raft |
| Seal type | Shamir |
| Key shares | 5 |
| Unseal threshold | 3 |

## Important behavior

OpenBao using the current Shamir configuration becomes sealed after the OpenBao service or operating system is restarted.

Three different unseal key shares are required to unseal it.

This is currently a manual recovery procedure.

## Recovery material

The encrypted OpenBao initialization data is stored outside Git.

Primary location on `iza`:

```text
/opt/ai/secrets/openbao/bao01-init.json.gpg
```

The file contains sensitive OpenBao initialization material and must remain encrypted at rest.

A recovery copy is stored on QNAP.

The GPG private key required to decrypt the initialization material is also recovery-critical and must be backed up independently.

Never commit any of the following to Git:

- unseal keys;
- root tokens;
- administrator passwords;
- GPG private keys;
- TLS private keys;
- decrypted initialization JSON.

## Step 1 - Verify OpenBao service

From `iza`:

```bash
ssh -i /home/tom/.ssh/homelab_automation_ed25519 \
  tom@192.168.55.24 \
  "sudo systemctl status openbao --no-pager"
```

The service should be active even when OpenBao is sealed.

## Step 2 - Check health status

Through the HomeLab reverse proxy:

```bash
curl \
  --cacert /opt/ai/secrets/pki/root-ca/home-lab-root-ca.crt \
  https://bao01.home.lab/v1/sys/health
```

A sealed server reports:

```text
"initialized": true
"sealed": true
```

An operational server reports:

```text
"initialized": true
"sealed": false
```

## Step 3 - Unseal OpenBao

Run the following from `iza`.

The command decrypts the initialization material locally, extracts one unseal share at a time, and sends it directly to the OpenBao API.

```bash
for i in 0 1 2; do
  gpg --decrypt /opt/ai/secrets/openbao/bao01-init.json.gpg 2>/dev/null \
    | jq -c --argjson i "$i" '{key: .unseal_keys_b64[$i]}' \
    | ssh -i /home/tom/.ssh/homelab_automation_ed25519 \
        tom@192.168.55.24 \
        'sudo curl -fsS \
          --resolve bao01.home.lab:8200:127.0.0.1 \
          --cacert /etc/openbao/tls/ca-chain.crt \
          -X POST \
          -H "Content-Type: application/json" \
          --data-binary @- \
          https://bao01.home.lab:8200/v1/sys/unseal'
  echo
done
```

Expected progress:

```text
progress: 1
progress: 2
sealed: false
```

The command must not print or persist individual unseal keys.

## Step 4 - Verify operational status

After unseal:

```bash
curl \
  --cacert /opt/ai/secrets/pki/root-ca/home-lab-root-ca.crt \
  https://bao01.home.lab/v1/sys/health
```

Expected state:

```text
"initialized": true
"sealed": false
"standby": false
```

## Step 5 - Verify Ansible configuration

After recovery, verify that configuration management remains idempotent:

```bash
cd /opt/ai/projects/infrastructure/ansible

ansible-playbook playbooks/bao01-bootstrap.yml
```

Expected result:

```text
changed=0
unreachable=0
failed=0
```

Do not repeatedly run the playbook while changing OpenBao configuration without considering that a configuration change can trigger a service restart and therefore seal OpenBao again.

## TLS verification

Direct OpenBao listener verification can be performed while bypassing normal DNS routing:

```bash
curl \
  --resolve bao01.home.lab:8200:192.168.55.24 \
  --cacert /opt/ai/secrets/pki/root-ca/home-lab-root-ca.crt \
  https://bao01.home.lab:8200/v1/sys/health
```

Normal HomeLab access through Nginx Proxy Manager is:

```bash
curl \
  --cacert /opt/ai/secrets/pki/root-ca/home-lab-root-ca.crt \
  https://bao01.home.lab/v1/sys/health
```

Do not use `curl -k` as a normal operational procedure.

## Complete VM recovery

If `bao01` must be rebuilt completely:

1. Verify that current backups and recovery material are available.
2. Preserve the existing VM and Raft data until recovery has been validated.
3. Verify the encrypted OpenBao initialization material.
4. Verify access to the GPG recovery key.
5. Verify availability of the HomeLab Root CA recovery material.
6. Verify the latest OpenBao/Raft backup before replacing any existing data.
7. Recreate the VM through Terraform only after confirming that destructive replacement is safe.
8. Configure the operating system and OpenBao through Ansible.
9. Restore or recover OpenBao persistent data using the documented backup procedure.
10. Restore the required TLS material.
11. Start OpenBao.
12. Unseal OpenBao using three valid shares.
13. Verify authentication, policies, PKI, and stored secrets.
14. Verify the reverse proxy endpoint.
15. Keep the old VM or backup data until recovery is fully validated.

Do not initialize a new OpenBao instance over an existing recovery scenario unless the loss of the previous OpenBao data has been explicitly accepted.

Running `bao operator init` against a new empty storage backend creates a new cryptographic environment and does not recover the previous secrets.

## Recovery testing

The recovery procedure should be tested periodically.

A recovery test should verify at minimum:

- encrypted initialization material can be decrypted;
- three unseal shares are available;
- OpenBao can be unsealed after a controlled restart;
- TLS verification succeeds;
- administrator authentication succeeds;
- PKI configuration is present;
- expected secrets are accessible;
- backups required for full disaster recovery are available.

Testing must not expose recovery material in shell history, logs, Git, screenshots, or documentation.

## Future improvements

The following items remain planned:

- automated certificate renewal;
- OpenBao-aware backup automation;
- documented Raft snapshot restore;
- periodic recovery tests;
- monitoring of seal state;
- monitoring of certificate expiration;
- evaluation of an appropriate automated unseal mechanism.
