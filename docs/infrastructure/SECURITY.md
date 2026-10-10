# Security — baseline 2026-10-10

Analiza lokalna; bieżące ustawienia hostów, ACL, TLS i firewalli: **unverified**.

| Obszar | Ustalenie ze źródeł | Status runtime | Źródło |
|---|---|---|---|
| Sekrety Ansible | Istniejący Vault dla Langfuse; zachować podejście Vault | unverified | ansible/inventories/production/host_vars/langfuse01/vault.yml (tylko lokalizacja) |
| Proxmox | Osobne tożsamości audit/manage; provider z insecure=true | unverified | terraform/providers.tf; docs/security/terraform-proxmox-access.md |
| SSH | Dedykowana automatyzacja; część dtcode ma tylko wpisy IP | unverified | ansible/README.md; docs/security/automation-ssh.md |
| OpenBao/PKI | Konfiguracja i opis odzyskiwania istnieją | unverified | docs/security/pki.md; docs/procedures/openbao-recovery.md |
| Kontenery | Jupyter deklaruje root; część obrazów używa latest | unverified | compose/jupyter/compose.yaml; compose/ |

Kolejne działania do uzgodnienia: weryfikacja TLS, ACL, firewalli i dostępu,
pokrycia sekretów odzyskiwaniem oraz ograniczeń kontenerów. Są to zalecenia,
nie zatwierdzone wdrożenia ani potwierdzone podatności.

Kolektory nie odczytują haseł, tokenów, kluczy, .env, tfstate ani Vault.
JSON i generator stosują allowlist pól, ograniczenia znaków i odrzucanie
podejrzanych nazw. To nie jest uniwersalny detektor sekretów umieszczonych
w dowolnej nazwie zasobu: operator musi sprawdzić dane przed eksportem i Git.
Nie umieszczać sekretów w hostname, nazwach kontenerów ani nazwach obrazów.
Nie używać surowego docker inspect, terraform show -json ani dumpów env
jako wejścia. Obce pola powodują odrzucenie całego pliku.

Nowe JSON-y mają tryb 600. Raporty zawierają wewnętrzne IP i topologię;
przechowywać je w prywatnym repozytorium, udostępniać po przeglądzie.
Nie zmieniono żadnej konfiguracji bezpieczeństwa ani uprawnień hostów.
