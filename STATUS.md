# Infrastructure Status

Last documentation reconciliation: `2026-10-04` (local review only). Operational observations below were previously recorded on `2026-08-17`–`2026-08-18`; they were not revalidated against infrastructure.

## Current state

The HomeLab infrastructure repository is actively being expanded from documentation and discovery into controlled infrastructure management.

Terraform and Ansible currently manage approved newly created resources on both `dom` and `dtcode`.

The main recently deployed workloads are:

- `mysql01` on `dom`;
- `bao01` on `dtcode`.

Existing infrastructure is not automatically imported or recreated. Legacy workloads remain protected until their configuration, dependencies, persistent data and backup coverage are understood.

## Tooling

The current management environment includes:

- Terraform `1.15.8` on `iza`;
- BPG Proxmox Terraform provider;
- read-only Terraform API access to both Proxmox environments;
- restricted Terraform management access to both Proxmox environments;
- local Terraform state with protected filesystem permissions;
- QNAP-backed infrastructure backup;
- Ansible Core `2.20.1`;
- Forgejo as the primary Git server;
- GitHub as a public repository mirror.

## Terraform status

Terraform manages approved newly created resources and the five adopted existing `dtcode` guests.

| Resource | Status |
|---|---|
| `mysql01` VM, ID `201` | Managed |
| `bao01` VM, ID `104` | Managed |
| `dns01` LXC, ID `102` | Adopted 2026-10-04; administrator report |
| `home01` VM, ID `103` | Adopted 2026-10-04; administrator report |
| `forgejo01` VM, ID `105` | Adopted 2026-10-04; administrator report |
| `npm01` VM, ID `106` | Adopted 2026-10-04; administrator report |
| `tailscale-router` VM, ID `107` | Adopted 2026-10-04; administrator report |
| State path | `terraform/state/terraform.tfstate` |
| State permissions | Protected locally |
| State backup to QNAP | Active |

The Terraform configuration uses restricted Proxmox management credentials rather than unrestricted administrative credentials.

The five existing guests `dns01`, `home01`, `forgejo01`, `npm01` and `tailscale-router` were adopted into the current Terraform state on `2026-10-04`, according to the administrator; no apply followed.

The newly created `bao01` VM is managed by the current Terraform state.

Existing infrastructure must not be imported or recreated only to make it conform to the current Terraform standard.

Any future import requires prior verification of:

- current live configuration;
- dependencies;
- persistent data;
- backup coverage;
- lifecycle expectations.

## Proxmox access

Terraform access is separated between read-only discovery and restricted resource management.

Known API identities include:

```text
terraform-audit@pve!prov
```

for read-only infrastructure inspection, and:

```text
terraform-manage@pve!provider
```

for approved Terraform-managed resources.

Management permissions are intentionally restricted.

Terraform-created resources use the:

```text
terraform-managed
```

resource pool where applicable.

## mysql01 status

| Property | Value |
|---|---|
| Proxmox host | `dom` |
| VM ID | `201` |
| Address | `192.168.55.21` |
| FQDN | `mysql01.home.lab` |
| Operating system | Ubuntu Server |
| Terraform management | Active |
| Ansible management | Active |
| MySQL management | Ansible |
| Database `ai_demo` | Ansible-managed |
| Database-aware backup | Not configured |

`mysql01` provides the MySQL platform for HomeLab application and AI demonstration workloads.

The Ansible MySQL role supports declarative creation of configured databases.

The currently configured database is:

```text
ai_demo
```

MySQL logical backup and restore still require implementation and testing.

## bao01 status

| Property | Value |
|---|---|
| Proxmox host | `dtcode` |
| VM ID | `104` |
| Address | `192.168.55.24` |
| FQDN | `bao01.home.lab` |
| Operating system | Ubuntu Server 24.04.4 LTS |
| CPU | 2 virtual cores |
| Memory | 2 GiB |
| Disk | 32 GiB |
| Start on Proxmox boot | Enabled |
| QEMU Guest Agent | Active |
| Terraform management | Active |
| Ansible management | Active |

`bao01` is the central OpenBao secrets-management and PKI server for the HomeLab infrastructure.

The VM is protected against accidental destruction at the Proxmox/Terraform lifecycle level.

## OpenBao status

| Property | Value |
|---|---|
| Version | `2.6.1` |
| Service | Enabled and active |
| Storage | Integrated Raft |
| Raft node | `bao01` |
| API port | `8200` |
| Cluster port | `8201` |
| TLS | Enabled |
| UI | Enabled |
| Seal type | Shamir |
| Shares | `5` |
| Threshold | `3` |
| Authentication | `userpass`, token |
| Administrator account | `tom` |
| Initial root token | Revoked |
| PKI secrets engine | Enabled |
| Intermediate CA | Active |
| HTTPS through Nginx Proxy Manager | Verified |
| Raft snapshot backup | Created and encrypted |
| Raft restore test | Not yet performed |

OpenBao is initialized and operational.

The initial root token was revoked after administrative access through `userpass` was configured.

OpenBao currently uses Shamir unseal with five shares and a threshold of three.

A service or system restart causes OpenBao to become sealed and currently requires manual unseal.

The OpenBao Ansible bootstrap was verified as idempotent on `2026-08-18`:

```text
changed=0
unreachable=0
failed=0
```

## PKI status

The HomeLab internal PKI currently uses the following hierarchy:

```text
HomeLab Root CA
    |
    +-- HomeLab OpenBao Intermediate CA
            |
            +-- service certificates
```

The Root CA private key is maintained outside Git and is protected with a passphrase.

OpenBao operates the intermediate CA and can issue service certificates without requiring routine access to the Root CA private key.

The OpenBao listener uses TLS for:

```text
bao01.home.lab
```

Nginx Proxy Manager uses a separate certificate and private key for the client-facing `bao01.home.lab` endpoint.

The verified connection path is:

```text
client
  -> HTTPS
  -> Nginx Proxy Manager
  -> HTTPS
  -> OpenBao
```

TLS verification succeeds using the HomeLab Root CA without disabling certificate verification.

## Ansible status

The production inventory currently contains:

- `database_servers`;
- `secrets_servers`.

Managed hosts currently include:

- `mysql01`;
- `bao01`.

The bootstrap playbooks manage:

- QEMU Guest Agent;
- MySQL Server on `mysql01`;
- PyMySQL;
- MySQL service startup;
- baseline MySQL security configuration;
- configured MySQL databases;
- OpenBao package installation on `bao01`;
- OpenBao version;
- OpenBao Raft data directory;
- OpenBao TLS-enabled configuration;
- OpenBao systemd service.

The `ansible.mysql` collection is pinned to version `5.2.0`.

OpenBao TLS certificate provisioning is not yet fully automated.

The OpenBao role verifies that the required TLS files exist before deploying the TLS-enabled OpenBao configuration.

Runtime OpenBao configuration such as PKI issuers, authentication methods and policies is not yet fully declarative.

## Backup status

The current infrastructure backup state includes:

- local Restic backups remain available;
- the QNAP NFS export is mounted at `/mnt/qnap-backup`;
- systemd automount for `/mnt/qnap-backup` is configured;
- an independent Restic repository exists at `/mnt/qnap-backup/AI/iza/restic`;
- Terraform state is included in infrastructure backup coverage;
- OpenBao encrypted initialization material is stored outside Git and copied to QNAP;
- the HomeLab Root CA certificate and encrypted private key are backed up on QNAP;
- an encrypted OpenBao Raft snapshot has been created and copied to QNAP;
- encrypted Raft snapshot decryption was verified against the original snapshot checksum;
- the local encrypted Raft snapshot and QNAP copy have matching SHA-256 checksums;
- MySQL logical backup and restore have not yet been implemented;
- an OpenBao Raft restore test has not yet been performed.

The first verified OpenBao Raft snapshot was created on `2026-08-18`.

The plaintext snapshot was removed after successful encryption verification.

Only the encrypted `.snap.gpg` backup is retained.

OpenBao backup creation is not yet automated.

## Historical knowledge reconciliation

The current repository remains the primary infrastructure repository. `/home/tom/Projekty/infrastructure-old/homelab` is an archival knowledge source only. Historical Terraform definitions were read locally; no old code, state, secret values or keys were imported.

The five legacy services now have documentation covering IDs, addresses, purpose, historical allocation, persistent data and earlier provisioning: [dns01](docs/vms/dns01.md), [home01](docs/vms/home01.md), [forgejo01](docs/vms/forgejo01.md), [npm01](docs/vms/npm01.md), [tailscale-router](docs/vms/tailscale-router.md). They now have current Terraform definitions and completed state adoption reported on 2026-10-04. They have no current Ansible definitions; service/data/backup verification remains separate.

`dtcode` is an existing physical host, documented rather than lifecycle-managed by current Terraform/Ansible. `bao01` and `mysql01` have both current Terraform and Ansible definitions and previously documented deployment. Current code also defines `qdrant01`, `langfuse01`, `grafana01` and `cloudflare01` with Ansible inventory/playbooks. Their deployment and current state membership are unconfirmed in this review; code presence alone does not establish operation. The earlier Terraform/Ansible sections describe the previously documented operational subset, not the full current code inventory. See [management classification](INVENTORY.md#management-classification-and-historical-evidence).

`wiki01` has status **historical / probably removed**. According to the administrator, it is not running and was probably removed from Proxmox `dtcode`; the administrator also reports that the latest old `terraform.tfstate` no longer contains this VM. These statements were not independently verified in this local review; absence from state alone does not prove removal from Proxmox.

**Historically reused identifiers and addresses:** VM ID `104` on `dtcode`, formerly used by `wiki01`, now belongs to `bao01`. IP `192.168.55.21`, referenced by historical `wiki01` and `test-vm`, now belongs to `mysql01` on `dom`. These are historical reassignments, not active collisions; the identifiers and address are currently allocated and must not be restored from old definitions.

`test-vm` remains **historical**; its current presence cannot be confirmed. No active definitions or recreation plans are added for either historical guest.

Unconfirmed: guest/application configuration drift, current service images, DNS/proxy routes, certificate provenance, Tailscale approvals/ACLs, data locations and contents, backup coverage and restore capability. Historical definitions do not confirm execution, simultaneous operation or decommissioning dates. Laptop work is limited to local code/documentation review; infrastructure checks require a separately authorized operational environment.

## Existing dtcode resources

The five guests listed above have completed state adoption. Templates 101 and 999 are still documented as outside current state; this review did not confirm their membership. Any additional import requires a separate review and approval.

## Current task

Complete the documentation and backup coverage for the deployed MySQL and OpenBao infrastructure.

OpenBao is now operational, but several operational areas still require automation and recovery testing.

## Next tasks

1. Complete OpenBao service and recovery documentation.
2. Complete HomeLab PKI documentation.
3. Document the verified OpenBao backup architecture.
4. Automate OpenBao Raft snapshots.
5. Define OpenBao snapshot retention.
6. Perform a controlled OpenBao Raft snapshot restore test.
7. Automate service certificate renewal.
8. Add certificate-expiration monitoring.
9. Add OpenBao seal-state monitoring.
10. Continue controlled migration of infrastructure secrets into OpenBao.
11. Configure MySQL logical backups.
12. Test MySQL restore.
13. Implement backup monitoring and alerting.
14. Review the five adopted `dtcode` guests' remaining provider/state differences and plan application backup/restore and Ansible coverage.
15. Continue migration of infrastructure management into Terraform and Ansible without unnecessarily rebuilding existing services.

## Completed dtcode state adoption (2026-10-04)

According to the administrator's completion report dated `2026-10-04`, `dns01` (LXC 102, `192.168.55.10`), `home01` (VM 103, `192.168.55.20`), `forgejo01` (VM 105, `192.168.55.22`), `npm01` (VM 106, `192.168.55.23`) and `tailscale-router` (VM 107, `192.168.55.4`) were imported individually into the current Terraform state. Each import was checked with a targeted plan; the final state list included all five resources. The final full plan reported **0 add, 5 change, 0 destroy**. **No terraform apply was performed.**

Remaining reported differences concern VM destroy-behavior defaults, VGA for all four VMs, memory for `tailscale-router`, and timeout/vm_id for `dns01`. Four VM definitions contain `serial_device { device = "socket" }`, consistent with the previously verified live hardware. A Terraform state backup was made after adoption; its location and restore were not checked here. This is not an application-data backup.

This laptop review confirms local definitions only. State membership, plan results, prior live hardware verification and backup completion are administrator-reported evidence, not operations performed or independently repeated here. None of the five hosts has current Ansible inventory, host_vars, playbooks or assigned roles. Adoption does not establish service deployment, runtime health or application restore capability.

See [detailed review](docs/operations/dtcode-adoption-2026-10-04.md).

## Inventory automation preparation — 2026-10-10

Added `dom` and `dtcode` to the Ansible `proxmox_hosts` group and prepared a
separate temporary-collector playbook supporting explicit limits and partial
reports on `iza`. Existing service roles are unchanged. Offline collector/report
tests pass; Ansible syntax validation was unavailable on the development laptop.
No remote connections, runtime collection, service changes or deployments were
performed. See [procedure](docs/infrastructure/README.md#integracja-z-ansible).

## Zabbix Agent 2 — 2026-10-10

Przygotowano rolę `zabbix_agent`, playbook `zabbix-agents.yml` i grupę 14 hostów.
Wyłącznie praca lokalna; brak instalacji, połączeń i weryfikacji infrastruktury.
Przed wdrożeniem wymagane są parametry serwera, dokładne wersje pakietów i TLS;
Ubuntu 26.04 wymaga potwierdzonego repozytorium oraz checksum override.
[Procedura i testy](docs/monitoring/zabbix-agents.md).

## Zabbix — przygotowanie lokalne (2026-10-10)

Przygotowano kod `zabbix01` na `dom` (Ubuntu 24.04, 2 vCPU, 4 GiB RAM,
40 GiB dysku) oraz etapy Ansible: serwer/PostgreSQL, lokalny DNS/NPM,
Agent 2 z PSK dla 15 hostów i rejestracja API z szablonami Linux/Proxmox.
**Nie wdrożono i nie sprawdzono działania w infrastrukturze.** Docelowy IP: `192.168.55.29`; VMID
pozostaje do zatwierdzenia; Terraform domyślnie nie tworzy tej VM.
Planowany panel: `http://zabbix.home.lab` przez `npm01`, tylko LAN.
Obsługa Ubuntu 26.04, wersje pakietów i zgodność API DNS/NPM wymagają
potwierdzenia na iza. Procedura i parametry: [Zabbix](docs/monitoring/zabbix-deployment.md).

Przegląd lokalny Zabbix: przypięto serwer do 7.0.31 LTS dla Ubuntu 24.04,
repozytorium z SHA256 oraz poprawiono konfigurację Nginx/PHP-FPM i testy offline.
PostgreSQL lokalny; frontend przez NPM, wyłącznie LAN. Bez wdrożenia i weryfikacji runtime.

## Centralny katalog usług Ansible — etap 1 (2026-10-10)

Dodano pasywny katalog dziewięciu usług w
`ansible/inventories/production/group_vars/all/services.yml`: Homepage, NPM,
Technitium DNS, Open WebUI, VS Code, Jupyter, Forgejo, OpenBao i Zabbix.
Wszystkie wpisy mają `npm_enabled: false`; Grafana pozostaje poza katalogiem.
Nie zmieniono hostów, adresów ani działających usług. Nieznane domeny i protokoły
zapisano jako `null`. Zabbix pozostaje w zakresie istniejącej, niezmienionej roli
`zabbix_local_access`; katalog nie steruje jej wykonaniem ani istniejącymi trasami.
Wykonano wyłącznie walidację i testy offline, bez wdrożenia.
Źródła danych, niejasności i komendy testów: [dokumentacja Ansible](ansible/README.md#central-service-catalogue--stage-1-offline-only).

## Porównywanie Proxy Hostów NPM — etap 1 (2026-10-10)

Przygotowano rolę `npm_proxy_hosts`, porównującą centralny katalog z jawnie
przekazaną listą Proxy Hostów. Raportuje `matching`, `missing`, `conflict`
i `unmanaged`, obsługuje hosty wielodomenowe i nie interpretuje
`npm_enabled: false` jako usunięcia lub wyłączenia trasy. Zabbix zachowuje
właściciela `zabbix_local_access`; tej roli nie zmieniono.
Brak klienta API, operacji zapisu i przypisania roli do playbooków wdrożeniowych.
Dane NPM są wyłącznie przykładowymi danymi testowymi. Testy offline: 15 nowych
oraz 12 testów katalogu przeszło; katalog 11 usług poprawny. Nie wykonywano
Ansible ani kontroli składni przez `ansible-playbook` (niedostępny lokalnie).
Bez połączeń z infrastrukturą i bez wdrożenia.
[Kontrakt i późniejszy adapter odczytu](ansible/roles/npm_proxy_hosts/README.md).

## Odczyt Proxy Hostów NPM — przygotowanie lokalne (2026-10-10)

Rozszerzono `npm_proxy_hosts` o opcjonalny adapter GET i osobny playbook
`npm-proxy-hosts-read.yml` do lokalnego wykonania na iza. Tryb offline pozostaje
domyślny. Wcześniej wydany token pochodzi z Ansible Vault; zadania z tokenem
lub odpowiedzią mają `no_log`. Brak logowania, odświeżania tokenów i operacji
zapisu. Błędy zatrzymują wykonanie, bez zastępowania odpowiedzi pustą listą.
Kontrakt zainstalowanej wersji NPM, widoczność całej listy i paginacja wymagają
weryfikacji na iza; brak potwierdzenia blokuje odczyt. HTTPS wymaga poprawnego
certyfikatu, HTTP jest dopuszczone tylko do loopback (np. tunel SSH).
Bez połączeń z NPM, wdrożenia i zmian w `zabbix_local_access`.
Testy lokalne: 28 testów porównania/adaptera oraz 12 testów katalogu przeszło;
walidacja 11 usług poprawna. Ansible nie uruchamiano; `ansible-playbook`
pozostaje niedostępny lokalnie.
[Instrukcja pierwszego odczytu](ansible/roles/npm_proxy_hosts/README.md#first-safe-run--on-iza-only-not-performed-here).

## Zabbix — rejestracja pilot/full (2026-10-13)

Przygotowano lokalnie monitoring całej grupy `zabbix_agents` (15 hostów):
wymagany `zabbix_registration_mode` (`pilot` = tylko `zabbix01`, `full` = wszystkie),
odporne na pola API porównywanie tagów, bezpieczne komunikaty błędów rejestracji,
adres `iza` w `host_vars` oraz przywrócone ustawienia `sudo.ws` dla `iza`.
Procedura: [Zabbix](docs/monitoring/zabbix-deployment.md), sekcja „2–5“.
Testy offline Zabbix: 36 (3 pominięte); Ansible niedostępny lokalnie.
**Nie wdrożono i nie zweryfikowano w infrastrukturze.**

## webui01 / Open WebUI — przygotowanie lokalne (2026-10-13)

Dodano `terraform/dom_webui01.tf` (wyłączony domyślnie, VMID do zatwierdzenia),
rolę `open_webui`, playbook `webui01-bootstrap.yml`, `webui01` w `zabbix_agents`
oraz rejestrację Zabbix w trybie `full` dla 16 hostów (walidacja PSK bez zmian).
Agent `db-agent-mvp` jest podłączany przez istniejący endpoint `/v1` bez adaptera.
Trasa Cloudflare Tunnel jest krokiem ręcznym (konfiguracja tunelu poza repozytorium).
Testy offline: 114 przeszło (1 pominięty); Terraform/Ansible niedostępne lokalnie.
**Nie wdrożono i nie zweryfikowano w infrastrukturze.**
[Procedura](docs/vms/webui01.md).

## n8n01 / n8n — przygotowanie lokalne (2026-10-13)

Dodano `terraform/dom_n8n01.tf` (wyłączony domyślnie, VMID do zatwierdzenia),
rolę `n8n` (n8n + PostgreSQL, sekrety w plikach env `0600` z Ansible Vault),
playbook `n8n01-bootstrap.yml`, `n8n01` w `automation_servers` i `zabbix_agents`.
Rejestracja Zabbix w trybie `single` (tylko `n8n01`). OAuth2: edytor i callback
`https://authn8n.tdcode.pl` (tylko DNS wewnętrzny i Tailscale, bez trasy publicznej;
n8n 2.43.4 buduje redirect URI z `N8N_EDITOR_BASE_URL` i wymaga sesji na callbacku),
webhooki `N8N_WEBHOOK_URL=https://webhookn8n.tdcode.pl/`. NPM, DNS, certyfikat
DNS-01 i Cloudflare Tunnel (tylko `^/webhook/`) są krokami ręcznymi
(konfiguracja poza repozytorium). Testy offline: 122 przeszło (3 pominięte);
Terraform/Ansible/Docker niedostępne lokalnie.
**Nie wdrożono i nie zweryfikowano w infrastrukturze.**
[Procedura](docs/vms/n8n01.md).

## n8n01 — publiczny edytor `n8n.tdcode.pl` (2026-10-13)

Według zgłoszenia operatora `n8n01` (VMID `208`, `192.168.55.31`) jest wdrożona:
n8n `2.43.4`, PostgreSQL `17.11`, `/healthz` HTTP 200, webhooki przez
`https://webhookn8n.tdcode.pl/`. Prywatny edytor `authn8n.tdcode.pl` zastąpiono
publicznym `https://n8n.tdcode.pl/` (Cloudflare Tunnel, logowanie n8n, bez Cloudflare
Access); callback OAuth2 `https://n8n.tdcode.pl/rest/oauth2-credential/callback`.
`N8N_SECURE_COOKIE=true` ustawione jawnie; PostgreSQL, wolumeny, klucz szyfrowania
i hasła bez zmian. Trasa tunelu `n8n.tdcode.pl` → `http://192.168.55.31:5678` i
aktualizacja redirect URI u dostawców OAuth2 to kroki ręczne.
Testy offline przeszły; Ansible niedostępne lokalnie.
**Kod przygotowany, nie wdrożono i nie zweryfikowano w infrastrukturze.**
[Procedura](docs/vms/n8n01.md).


## DB-GPT + LiteLLM — przygotowane, niewdrożone

Kod prototypu `dbgpt01` na `dom` jest przygotowany. VMID i IP oczekują zatwierdzenia; nie potwierdzono utworzenia VM, działania aplikacji ani monitoringu. Osobna syntetyczna baza na mysql01 i konto tylko do odczytu są opisane w [instrukcji](docs/dbgpt/README.md). Wdrożenie i testy wyłącznie z iza.
