# HomeLab PKI

## Purpose

The HomeLab PKI provides an internal certificate authority hierarchy for TLS certificates used by infrastructure services.

The PKI is designed so that private CA keys and issued private keys are never stored in Git.

## Certificate hierarchy

The current hierarchy is:

```text
HomeLab Root CA
    |
    +-- HomeLab OpenBao Intermediate CA
            |
            +-- service certificates
```

The Root CA is the trust anchor for the HomeLab infrastructure.

The OpenBao Intermediate CA is managed through the OpenBao PKI secrets engine and is used to issue service certificates.

## Root CA

The Root CA was created outside OpenBao.

Its certificate is stored on `iza` at:

```text
/opt/ai/secrets/pki/root-ca/home-lab-root-ca.crt
```

The Root CA private key is stored outside Git and must remain protected.

The Root CA private key must not be copied to application servers or committed to the infrastructure repository.

## OpenBao Intermediate CA

OpenBao operates an intermediate CA:

```text
CN=HomeLab OpenBao Intermediate CA
```

It is signed by:

```text
C=PL
O=HomeLab
OU=Infrastructure
CN=HomeLab Root CA
```

The intermediate CA is imported into the OpenBao PKI secrets engine.

OpenBao can therefore issue service certificates without requiring the Root CA private key during normal operation.

## OpenBao service certificate

The OpenBao listener on `bao01` uses a certificate for:

```text
bao01.home.lab
```

The certificate chain is:

```text
HomeLab Root CA
    -> HomeLab OpenBao Intermediate CA
        -> bao01.home.lab
```

TLS files on `bao01` are stored under:

```text
/etc/openbao/tls
```

The private key is readable only by the accounts required to operate the OpenBao service.

Private keys must never be committed to Git.

## Nginx Proxy Manager

Nginx Proxy Manager terminates client-facing TLS for:

```text
https://bao01.home.lab
```

The NPM frontend certificate is issued separately from the certificate used by the OpenBao listener.

This means the private key used by OpenBao is not copied to Nginx Proxy Manager.

The connection path is:

```text
client
  |
  | HTTPS
  v
Nginx Proxy Manager
  |
  | HTTPS
  v
OpenBao
```

Both TLS endpoints use certificates issued under the HomeLab PKI.

## Client trust

Clients that directly validate HomeLab certificates must trust:

```text
HomeLab Root CA
```

For command-line verification on `iza`, the Root CA can be explicitly supplied:

```bash
curl \
  --cacert /opt/ai/secrets/pki/root-ca/home-lab-root-ca.crt \
  https://bao01.home.lab/v1/sys/health
```

Successful verification must not require `curl -k`.

## Certificate lifecycle

Service certificates are currently issued manually through the OpenBao PKI secrets engine.

Certificate issuance and renewal are not yet fully automated.

The current `bao01.home.lab` service certificates have a limited lifetime and therefore require renewal before expiration.

Automatic certificate renewal is a future infrastructure task.

## Security requirements

The following rules apply to HomeLab PKI:

- Root CA private keys must never be stored in Git.
- Intermediate CA private keys must never be exported unnecessarily.
- Service private keys must never be stored in Git.
- Temporary files containing private keys must be removed after use.
- Certificate issuance must use authenticated OpenBao identities.
- Root tokens must not be used for routine certificate issuance.
- TLS verification must not be permanently disabled with insecure client options.
- Root CA material must have independent recovery copies.
- Certificate renewal procedures must be documented and tested.

## Current limitations

The current implementation still requires improvement in the following areas:

- automated service certificate renewal;
- automated deployment of renewed certificates;
- documented certificate revocation procedure;
- documented CA rotation procedure;
- monitoring of certificate expiration;
- declarative management of OpenBao PKI roles and configuration.

These items should be implemented incrementally without replacing working infrastructure unnecessarily.

## Verification

Verified on `2026-08-18`:

- HomeLab Root CA exists;
- OpenBao Intermediate CA is signed by the HomeLab Root CA;
- OpenBao can issue service certificates;
- `bao01.home.lab` has a certificate issued by the OpenBao Intermediate CA;
- Nginx Proxy Manager has a separate certificate for `bao01.home.lab`;
- OpenBao listener TLS is enabled;
- HTTPS access through Nginx Proxy Manager succeeds;
- certificate verification succeeds using the HomeLab Root CA without disabling TLS verification.# HomeLab PKI

## Purpose

The HomeLab PKI provides an internal certificate authority hierarchy for TLS certificates used by infrastructure services.

The PKI is designed so that private CA keys and issued private keys are never stored in Git.

## Certificate hierarchy

The current hierarchy is:

```text
HomeLab Root CA
    |
    +-- HomeLab OpenBao Intermediate CA
            |
            +-- service certificates
```

The Root CA is the trust anchor for the HomeLab infrastructure.

The OpenBao Intermediate CA is managed through the OpenBao PKI secrets engine and is used to issue service certificates.

## Root CA

The Root CA was created outside OpenBao.

Its certificate is stored on `iza` at:

```text
/opt/ai/secrets/pki/root-ca/home-lab-root-ca.crt
```

The Root CA private key is stored outside Git and must remain protected.

The Root CA private key must not be copied to application servers or committed to the infrastructure repository.

## OpenBao Intermediate CA

OpenBao operates an intermediate CA:

```text
CN=HomeLab OpenBao Intermediate CA
```

It is signed by:

```text
C=PL
O=HomeLab
OU=Infrastructure
CN=HomeLab Root CA
```

The intermediate CA is imported into the OpenBao PKI secrets engine.

OpenBao can therefore issue service certificates without requiring the Root CA private key during normal operation.

## OpenBao service certificate

The OpenBao listener on `bao01` uses a certificate for:

```text
bao01.home.lab
```

The certificate chain is:

```text
HomeLab Root CA
    -> HomeLab OpenBao Intermediate CA
        -> bao01.home.lab
```

TLS files on `bao01` are stored under:

```text
/etc/openbao/tls
```

The private key is readable only by the accounts required to operate the OpenBao service.

Private keys must never be committed to Git.

## Nginx Proxy Manager

Nginx Proxy Manager terminates client-facing TLS for:

```text
https://bao01.home.lab
```

The NPM frontend certificate is issued separately from the certificate used by the OpenBao listener.

This means the private key used by OpenBao is not copied to Nginx Proxy Manager.

The connection path is:

```text
client
  |
  | HTTPS
  v
Nginx Proxy Manager
  |
  | HTTPS
  v
OpenBao
```

Both TLS endpoints use certificates issued under the HomeLab PKI.

## Client trust

Clients that directly validate HomeLab certificates must trust:

```text
HomeLab Root CA
```

For command-line verification on `iza`, the Root CA can be explicitly supplied:

```bash
curl \
  --cacert /opt/ai/secrets/pki/root-ca/home-lab-root-ca.crt \
  https://bao01.home.lab/v1/sys/health
```

Successful verification must not require `curl -k`.

## Certificate lifecycle

Service certificates are currently issued manually through the OpenBao PKI secrets engine.

Certificate issuance and renewal are not yet fully automated.

The current `bao01.home.lab` service certificates have a limited lifetime and therefore require renewal before expiration.

Automatic certificate renewal is a future infrastructure task.

## Security requirements

The following rules apply to HomeLab PKI:

- Root CA private keys must never be stored in Git.
- Intermediate CA private keys must never be exported unnecessarily.
- Service private keys must never be stored in Git.
- Temporary files containing private keys must be removed after use.
- Certificate issuance must use authenticated OpenBao identities.
- Root tokens must not be used for routine certificate issuance.
- TLS verification must not be permanently disabled with insecure client options.
- Root CA material must have independent recovery copies.
- Certificate renewal procedures must be documented and tested.

## Current limitations

The current implementation still requires improvement in the following areas:

- automated service certificate renewal;
- automated deployment of renewed certificates;
- documented certificate revocation procedure;
- documented CA rotation procedure;
- monitoring of certificate expiration;
- declarative management of OpenBao PKI roles and configuration.

These items should be implemented incrementally without replacing working infrastructure unnecessarily.

## Verification

Verified on `2026-08-18`:

- HomeLab Root CA exists;
- OpenBao Intermediate CA is signed by the HomeLab Root CA;
- OpenBao can issue service certificates;
- `bao01.home.lab` has a certificate issued by the OpenBao Intermediate CA;
- Nginx Proxy Manager has a separate certificate for `bao01.home.lab`;
- OpenBao listener TLS is enabled;
- HTTPS access through Nginx Proxy Manager succeeds;
- certificate verification succeeds using the HomeLab Root CA without disabling TLS verification.
