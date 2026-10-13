# webui01 — Open WebUI

**Status: przygotowany kod, nie wdrożono.** Nic z poniższych kroków nie zostało
wykonane ani sprawdzone w infrastrukturze (stan na 2026-10-13).

| Parametr | Wartość |
|---|---|
| Proxmox | `dom` |
| VMID | do zatwierdzenia (`webui01_vmid`, brak domyślnej wartości) |
| Adres | `192.168.55.30/24`, brama `192.168.55.1`, DNS `192.168.55.10` (kolejny wolny w planie `.24`–`.29`; potwierdzić brak kolizji) |
| Zasoby | 4 vCPU, 8 GiB RAM, 40 GiB `local-lvm`, Ubuntu 24.04 cloud image |
| Terraform | `terraform/dom_webui01.tf`, domyślnie wyłączony (`webui01_enabled = false`) |
| Ansible | `playbooks/webui01-bootstrap.yml`: `qemu_guest_agent`, `docker_host`, `open_webui` |
| Open WebUI | `ghcr.io/open-webui/open-webui:v0.11.0` (ta sama wersja co na `iza`), port LAN `3000` |
| Dane | `/opt/open-webui/data` → `/app/backend/data` (bind mount, trwały) |
| Monitoring | Zabbix Agent 2 z PSK, grupa `zabbix_agents` (16 hostów) |

Istniejący Open WebUI na `iza` (`chat.home.lab`, `/opt/ai/data/open-webui`)
pozostaje bez zmian. Nowa instancja ma osobną, pustą bazę użytkowników.

## Przepływ ruchu

```text
Internet --HTTPS--> Cloudflare --tunel (wychodzący)--> cloudflared na cloudflare01
  --HTTP LAN--> webui01:3000 (Open WebUI, logowanie wymagane)
                  |--> iza:11434  Ollama        (tylko LAN)
                  '--> iza:8000/v1 db-agent-mvp (tylko LAN, model db-agent)
```

Brak przekierowań portów na routerze. Cloudflare publikuje wyłącznie Open WebUI;
Ollama i API agenta nie dostają publicznych hostów.

## Agent `db-agent-mvp`

Agent działa na `iza` jako `db-agent.service` (Uvicorn `0.0.0.0:8000`, jeden worker)
i ma wbudowany adapter OpenAI (`GET /v1/models`, `POST /v1/chat/completions`,
model `db-agent`). Adapter API nie jest potrzebny; Open WebUI łączy się przez
`OPENAI_API_BASE_URLS=http://192.168.55.7:8000/v1`. Agent nie wymaga klucza API.
`ENABLE_FORWARD_USER_INFO_HEADERS=true` przekazuje `X-OpenWebUI-Chat-Id`, którego
agent używa do rozmów wieloetapowych (przekazywane są też nazwa/e-mail użytkownika,
wyłącznie w LAN). Logika SQL i dostęp do bazy nie zostały zmienione.

Uwaga: API agenta nie ma uwierzytelniania i nasłuchuje w całym LAN. Ograniczenie
portu 8000 na `iza` do `webui01` i loopback (firewall) jest rekomendowane, ale
nie jest częścią tej zmiany i wymaga osobnej zgody.

Zmienne `ENABLE_SIGNUP`, `OPENAI_API_BASE_URLS` itp. Open WebUI zapisuje w bazie
przy pierwszym starcie; późniejsze zmiany wprowadza się w panelu administratora.

## Język interfejsu

`DEFAULT_LOCALE=pl-PL` (zmienna `open_webui_default_locale`) ustawia polski jako
domyślny język od pierwszego uruchomienia, bez zmian w kodzie Open WebUI.

- Zakres: to ustawienie **globalne domyślne** serwera. Wybór języka przez użytkownika
  (avatar → Ustawienia/Settings → Ogólne/General → Język/Language) jest zapisywany
  w przeglądarce (`localStorage`) i ma pierwszeństwo przed wartością domyślną.
  Przeglądarka, w której wcześniej wybrano inny język, nadal go pokaże; wtedy
  wybierz „Polski” w tym samym miejscu albo wyczyść dane strony.
- Trwałość: wartość trafia do bazy w `/opt/open-webui/data` przy pierwszym starcie
  (PersistentConfig), więc zostaje po restarcie i aktualizacji obrazu. Późniejsza
  zmiana zmiennej nie nadpisze wartości już zapisanej w bazie.
- Do potwierdzenia po wdrożeniu: w wersji `v0.11.0` istnieje katalog tłumaczeń
  `pl-PL`, a strona logowania w nowej przeglądarce jest po polsku.

## Brakujące dane przed wdrożeniem

1. Wolny VMID na `dom` (np. sprawdzić `qm list` na `dom` oraz VMID `zabbix01`).
2. Potwierdzenie, że `192.168.55.30` jest wolny (DHCP/rezerwacje, `ping`/ARP z `iza`).
3. Publiczna subdomena, np. `https://chat.example.com` → `open_webui_public_url`.
4. Typ istniejącego tunelu na `cloudflare01` (zarządzany z panelu tokenem czy lokalny `config.yml`).
5. Sekrety (generowane na `iza`, nigdy w Git): `vault_open_webui_secret_key`
   oraz `vault_zabbix_psks.webui01`.

## Polecenia — wyłącznie na `iza`, po zatwierdzeniu

### 0. Pliki prywatne

```bash
umask 077
mkdir -p /home/tom/.config/infrastructure/webui01
cat > /home/tom/.config/infrastructure/webui01/webui01.tfvars <<'EOF'
webui01_enabled = true
webui01_vmid    = <APPROVED_VMID>
EOF
# Zawartość: vault_open_webui_secret_key: <openssl rand -hex 32>
ansible-vault create /home/tom/.config/infrastructure/webui01/vault.yml
# Dodaj do istniejącego vaulta Zabbix: vault_zabbix_psks: { webui01: <openssl rand -hex 32> }
ansible-vault edit /home/tom/.config/infrastructure/zabbix/vault.yml
```

Ustaw `open_webui_public_url` w `ansible/inventories/production/host_vars/webui01.yml`
(np. `https://chat.example.com`). Rola odmawia działania bez tej wartości.

### 1. VM (Terraform)

Tak jak przy `zabbix01`: wyłączony domyślnie zasób wymaga podawania **obu**
prywatnych var-file w każdym kolejnym `plan`/`apply`, inaczej Terraform zaproponuje
usunięcie VM (ochrona Proxmox blokuje usunięcie, ale nie zastępuje przeglądu planu).

```bash
cd /opt/ai/projects/infrastructure
source ./scripts/load-proxmox-manage-env.sh
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
terraform -chdir=terraform plan \
  -var-file=/home/tom/.config/infrastructure/zabbix/zabbix.tfvars \
  -var-file=/home/tom/.config/infrastructure/webui01/webui01.tfvars \
  -target='proxmox_virtual_environment_vm.webui01[0]' \
  -out=/home/tom/.config/infrastructure/webui01/vm.plan
terraform -chdir=terraform show /home/tom/.config/infrastructure/webui01/vm.plan
# Plan musi zawierać wyłącznie "1 to add" (webui01). Dopiero po zatwierdzeniu:
terraform -chdir=terraform apply /home/tom/.config/infrastructure/webui01/vm.plan
# Kontrola: pełny plan bez -target nie może proponować zmian istniejących VM.
terraform -chdir=terraform plan \
  -var-file=/home/tom/.config/infrastructure/zabbix/zabbix.tfvars \
  -var-file=/home/tom/.config/infrastructure/webui01/webui01.tfvars
```

### 2. Docker i Open WebUI (Ansible)

```bash
cd /opt/ai/projects/infrastructure/ansible
ssh-keyscan -t ed25519 192.168.55.30 >> ~/.ssh/known_hosts   # porównaj odcisk z konsolą Proxmox
ansible webui01 -m ansible.builtin.ping
ansible-playbook playbooks/webui01-bootstrap.yml --limit webui01 --syntax-check
ansible-playbook playbooks/webui01-bootstrap.yml --limit webui01 \
  --ask-become-pass --ask-vault-pass \
  -e @/home/tom/.config/infrastructure/webui01/vault.yml
curl -fsS http://192.168.55.30:3000/health
```

### 3. Konto administratora — przed publikacją

Otwórz `http://192.168.55.30:3000` z LAN i utwórz pierwsze konto (zostaje
administratorem). Następnie sprawdź, że rejestracja jest zamknięta: wyloguj się,
formularz nie może pozwalać na nowe konto. Dopiero wtedy publikuj przez Cloudflare.
`ENABLE_INITIAL_ADMIN_SIGNUP` należy potwierdzić w wersji `v0.11.0`.

W panelu: Admin → Settings → Connections — połączenie `http://192.168.55.7:8000/v1`
i model `db-agent` widoczny na liście. Sprawdzenie z VM:

```bash
ssh tom@192.168.55.30 'docker exec open-webui curl -fsS http://192.168.55.7:8000/v1/models'
```

### 4. Cloudflare Tunnel

W istniejącym tunelu działającym na `cloudflare01` dodaj tylko jedną trasę:

- tunel zarządzany z panelu (Zero Trust → Networks → Tunnels → tunel → Public Hostname):
  subdomena/domena z `open_webui_public_url`, Service `HTTP`, URL `192.168.55.30:3000`;
- tunel lokalny (`/etc/cloudflared/config.yml` na `cloudflare01`): dodaj regułę
  `- hostname: <subdomena>` / `service: http://192.168.55.30:3000` **przed** regułą
  `http_status:404`, zrób kopię pliku, `cloudflared tunnel ingress validate`,
  `cloudflared tunnel route dns <tunel> <subdomena>`, restart `cloudflared`.

Nie dodawaj tras dla `:11434` ani `:8000`. Konfiguracja tunelu nie jest
zarządzana przez to repozytorium (rola `cloudflared` tylko instaluje pakiet).
Opcjonalnie: Cloudflare Access jako dodatkowa warstwa przed logowaniem Open WebUI.

### 5. Zabbix

```bash
cd /opt/ai/projects/infrastructure/ansible
ansible-playbook playbooks/zabbix-agents.yml --limit webui01 \
  --ask-become-pass --ask-vault-pass \
  -e @/home/tom/.config/infrastructure/zabbix/settings.yml \
  -e @/home/tom/.config/infrastructure/zabbix/vault.yml
ansible-playbook playbooks/zabbix-register.yml --limit zabbix01 \
  --ask-become-pass --ask-vault-pass \
  -e zabbix_registration_mode=full \
  -e @/home/tom/.config/infrastructure/zabbix/settings.yml \
  -e @/home/tom/.config/infrastructure/zabbix/vault.yml
```

Tryb `full` wymaga PSK dla wszystkich 16 hostów; istniejące hosty są aktualizowane
bez duplikatów. W panelu: Monitoring → Hosts → `webui01` — ZBX zielony, świeże dane.

### 6. Po wdrożeniu

Z sieci zewnętrznej: `https://<subdomena>` pokazuje logowanie; `http://<publiczne IP>:3000`
nie odpowiada. Zaktualizuj `INVENTORY.md`/`STATUS.md` o rzeczywiste wyniki i VMID.
Kopia `/opt/open-webui/data` nie jest jeszcze objęta backupem — do zaplanowania.
