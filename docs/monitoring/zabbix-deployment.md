# Zabbix w homelabie — kod przygotowany, bez wdrożenia

Zmiany wykonano wyłącznie lokalnie. Nie sprawdzono łączności, dostępności pakietów,
wersji działających API ani rzeczywistej idempotencji na serwerach. Poniższe polecenia
wdrożeniowe wykonuje administrator **wyłącznie na iza, po zatwierdzeniu**.
Tryb Ansible `--check` również łączy się z hostami; nie jest testem offline.

## Projekt i zakres

Terraform dodaje `zabbix01` na `dom`: Ubuntu 24.04 z istniejącego cloud image,
2 vCPU, 4096 MiB RAM, 40 GiB `local-lvm`, `vmbr0`, QEMU Guest Agent, użytkownik
`tom`, istniejące klucze SSH. IP i VMID nie mają domyślnych wartości. VM jest
wyłączona z konfiguracji (`zabbix_enabled=false`) do zatwierdzenia parametrów.
Nie zmieniono definicji istniejących VM, backendu ani stanu Terraform.

Zabbix 7.0.31 LTS, PostgreSQL, PHP 8.3/FPM i nginx działają na jednej nowej VM.
Schema jest importowana transakcyjnie wyłącznie do pustej bazy; istniejąca baza
bez tabeli `dbversion` powoduje błąd, nie automatyczną naprawę. Hasło bazy ustawiane
jest przy tworzeniu użytkownika; ponowne wykonanie nie zmienia go. Celowa rotacja
wymaga `zabbix_rotate_db_password=true` wraz z nowym hasłem w Vault.
Nie stosuj tej roli do istniejącego, obcego serwera Zabbix ani do zmiany gałęzi LTS.

Konfiguracja serwera przypina trzy pakiety (`zabbix-server-pgsql`,
`zabbix-frontend-php`, `zabbix-sql-scripts`) do `1:7.0.31-1+ubuntu24.04`.
Pakiet repozytorium: `zabbix-release_7.0-5%2Bubuntu24.04_all.deb`, SHA256:
`4f206504c2bc1cff36edf762e2274d0686b0e796b772533c95d04bbe265654de`.
APT sprawdza checksum podczas wdrożenia. Pakiety Zabbix otrzymują `hold`, aby
aktualizacje automatyczne nie zmieniły wersji. Kolejna aktualizacja wymaga osobnego
przeglądu, backupu i świadomego zdjęcia hold na iza; rola nie wymusza downgrade.
`policy_rc_d=101` blokuje start usług ze skryptów instalacyjnych przed konfiguracją.

Nie instalujemy `zabbix-nginx-conf`: rola zarządza własną witryną i używa
standardowego socketu puli `www` PHP 8.3. Pakiet dostarczyłby dodatkową konfigurację
Nginx/PHP-FPM, której nie potrzebujemy. Domyślna witryna Nginx jest odłączana;
frontend słucha na `192.168.55.29:8080` i `127.0.0.1:8080`, bez listenera IPv6.
PHP odrzuca nieistniejące pliki; katalogi wewnętrzne frontendu są niedostępne.
Handlery sprawdzają `php-fpm8.3 -t` i `nginx -t` przed restartem/reloadem.
PostgreSQL jest używany lokalnie: aplikacje przez `127.0.0.1`, administracja schematu
przez socket `/var/run/postgresql`, bez hasła w poleceniach. Na iza przed publikacją
potwierdź, że PostgreSQL nie nasłuchuje poza loopback i nie ma zdalnych wpisów HBA.
Skrypt importu używa `psql -X` i `ON_ERROR_STOP`; błąd odczytu, dekompresji lub
importu kończy etap bez zgłoszenia sukcesu. Import nie jest migracją istniejącej bazy.
Bootstrap używa loopback bez proxy środowiskowego, wymaga jednego konta Admin,
sprawdza odpowiedź aktualizacji i zamyka sesję także przy błędzie. Ponowne wykonanie
z aktualnym hasłem nie zmienia konta. Zmienione hasło Vault nie służy do rotacji
istniejącego administratora; przy innym haśle i braku hasła początkowego etap odmawia.

Frontend na 8080 przyjmuje ruch tylko z `npm01` i loopback. Technitium dostaje
jeden rekord A `zabbix.home.lab -> 192.168.55.23`; NPM jedną trasę HTTP na nową VM,
z `allow 192.168.55.0/24; deny all;`, bez certyfikatu publicznego. Nie są tworzone
rekordy publiczne, integracje Cloudflare, przekierowania portów ani nowe strefy DNS.
Zabbix nasłuchuje na adresie LAN na 10051; agenci akceptują wyłącznie serwer i PSK.
Zachowaj istniejącą izolację LAN, brak DNAT oraz brak publicznego dostępu do NPM
i PostgreSQL. Zweryfikuj na iza rzeczywistą konfigurację wygenerowaną przez NPM:
ACL musi obowiązywać także w `location /`, bez nadrzędnego `allow all` w include.
Przed publikacją sprawdź odmowę dostępu spoza LAN (także IPv6); jeśli NPM danej
wersji nadpisuje ACL, nie publikuj trasy, dopasuj integrację po przeglądzie.

Rola `zabbix_agent` pozostaje istniejącą implementacją. Grupa ma 16 hostów:
`dom`, `dtcode`, `iza`, `dns01`, `home01`, `forgejo01`, `npm01`, `tailscale-router`,
`mysql01`, `bao01`, `qdrant01`, `langfuse01`, `grafana01`, `cloudflare01`, `webui01`, `zabbix01`.
`webui01` dodano 2026-10-13 ([procedura](../vms/webui01.md)); tryb `full` wymaga dokładnie 16 hostów.
Wszyscy używają indywidualnych PSK i szablonu `Linux by Zabbix agent active`.
Proxmox dodatkowo otrzymuje `Proxmox VE by HTTP` oraz istniejące lub osobno
zatwierdzone tokeny **tylko do odczytu**, z uprawnieniami potrzebnymi temu szablonowi.
Nie używaj tokenów zarządzających Terraform. Nie twórz tokenów na laptopie.

Rejestrator sprawdza makra szablonu Proxmox przed zmianami. Zachowuje dodatkowe
szablony, grupy i tagi. Obcy host bez `managed-by=infrastructure-zabbix` oraz obca
trasa NPM powodują odmowę przejęcia. Nie usuwa hostów i nie czyści całych grup/stref.
Fingerprint sekretów pozwala rozpoznać rotację bez odczytywania ich z API;
nie wykrywa ręcznej zmiany sekretu w Zabbix przy pozostawieniu fingerprintu.
Po takiej zmianie usuń tag `credentials-sha256` z zarządzanego hosta i ponów etap.
Hasła/tokeny trafiają do skryptów przez stdin, zadania mają `no_log`, sekrety nie
są zapisywane w argumentach ani w diff. DNS/NPM i Zabbix API używają loopback
na odpowiednich hostach. Dostęp WWW przez HTTP nie szyfruje logowania w LAN.

## Parametry do zatwierdzenia i przygotowania

- Potwierdź dostępność docelowego IP `192.168.55.29` i wolny VMID na `dom`; sprawdź brak kolizji także
  z zasobami spoza Terraform. Nowa VM wymaga 40 GiB wolnego miejsca.
- Wersje agentów dla każdej dystrybucji pozostają do zatwierdzenia. Parametry
  serwera są przypięte w `group_vars/zabbix_servers.yml` (wartości podane przez
  administratora; dostępności pakietów i checksum nie sprawdzano przez sieć).
- Ubuntu 26.04 na `iza`: oficjalne repozytorium 7.0 (`resolute`) zawiera
  `1:7.0.31-1+ubuntu26.04` (sprawdzone 2026-10-13); rola używa domyślnego URL.
  Nie podstawiaj repozytorium 24.04. Nie deklaruj ukończenia wszystkich 16 hostów
  przy pominięciu iza.
- Kontrakty API zainstalowanych Technitium i NPM: endpointy użyte w `access.py`,
  odpowiedzi `zone.type=Primary`, `records[].rData.ipAddress`, pola proxy hostów,
  lokalne porty 5380 i 81, Python 3 oraz skuteczne ACL. Wersje usług nie były
  odczytywane; wymagana jest jawna zgoda `zabbix_local_api_compatibility_approved`.
- Dostęp SSH/sudo, hasła Vault, indywidualne PSK, hasło Admin i bazy, token DNS,
  konto NPM oraz tokeny monitorujące Proxmox. Bootstrap domyślnego konta Admin
  wymaga `zabbix_initial_admin_bootstrap_approved=true`; zabezpiecza hasło przed
  publikacją panelu. Zabbix API rejestracji loguje się tym kontem i wylogowuje sesję.
  Konto Admin jest używane tylko w tym etapie; tokeny nie są utrwalane w plikach.

## Pliki prywatne na iza

Nie wpisuj sekretów do repozytorium. Użyj istniejącej metody i identyfikatora
Ansible Vault. Vault Langfuse (`ansible/vaults/langfuse01.yml`) ładuje tylko
`langfuse01-bootstrap.yml`; playbooki Zabbix go nie odszyfrowują.
Nie wyświetlaj `ansible-inventory --list` z odszyfrowanymi sekretami.

```bash
# Tylko na iza. Zachowaj istniejący sposób przechowywania haseł Vault.
umask 077
mkdir -p /home/tom/.config/infrastructure/zabbix
ansible-vault create /home/tom/.config/infrastructure/zabbix/vault.yml
```

W zaszyfrowanym pliku przygotuj następujące klucze (wartości generuj lokalnie,
np. `openssl rand -hex 32`; nie wklejaj ich do czatu ani Git):

```yaml
vault_zabbix_db_password: <32-or-more-alphanumeric-characters>
vault_zabbix_admin_password: <unique-random-password-at-least-32-characters>
vault_zabbix_dns_token: <scoped-Technitium-token>
vault_zabbix_npm_identity: <NPM-account>
vault_zabbix_npm_password: <NPM-password>
vault_zabbix_psks:
  dom: <unique-64-hex-characters>
  # Dodaj osobny klucz dla każdego z pozostałych 15 hostów (w tym webui01).
# Opcjonalne: bez tokenów dom/dtcode są monitorowane tylko przez Agent 2.
vault_zabbix_proxmox_tokens:
  dom:
    id: <user@realm!readonly-token>
    secret: <token-secret>
  dtcode:
    id: <user@realm!readonly-token>
    secret: <token-secret>
```

Prywatny `/home/tom/.config/infrastructure/zabbix/settings.yml` zawiera parametry
zatwierdzone przez administratora; wszystkie placeholdery zastąp przed użyciem:

```yaml
zabbix_deployment_approved: true
# Adres wspólny pochodzi z group_vars/all/zabbix.yml: 192.168.55.29
zabbix_initial_admin_bootstrap_approved: true
zabbix_local_api_compatibility_approved: true
# Wersji Agent 2 nie ustawiaj tutaj: pochodzą z mapy dystrybucji w
# group_vars/zabbix_agents.yml (zabbix_agent_package_versions).
# Repozytorium Agent 2 (także Ubuntu 26.04 na iza) wynika z domyślnego URL roli.
```

Prywatny `zabbix.tfvars` w tym samym katalogu:

```hcl
zabbix_enabled = true
zabbix_vmid    = <APPROVED_VMID>
zabbix_ip      = "192.168.55.29"
```

## Testy offline na laptopie lub iza

### Bezpieczna diagnostyka bootstrapu Admin

`bootstrap_admin.py` zwraca na stdout JSON z `changed`, `failed` i `warnings`.
Przy błędzie dodaje `stage` i stały `code`; nie wypisuje wyjątków, treści HTTP,
żądań, odpowiedzi API, haseł ani tokenów. Etapy to `target_login`, `initial_login`,
`user_read`, `password_update` i `logout` (oraz `input` dla błędnego wejścia).
Kody obejmują `RPC_ERROR`, `MISSING_RESULT`, `HTTP_ERROR`, `TRANSPORT_ERROR`,
`INVALID_JSON`, `INVALID_RESPONSE`, `INVALID_TOKEN`, `INVALID_ADMIN_RESULT`,
`UPDATE_NOT_CONFIRMED` i `UNEXPECTED_ERROR`. `INITIAL_PASSWORD_NOT_APPROVED`
oznacza odmowę użycia hasła początkowego po odrzuceniu logowania docelowego.
`RPC_ERROR` celowo nie ujawnia komunikatu API ani nie przesądza o błędnym haśle.
Tylko odrzucenie JSON-RPC logowania docelowego pozwala na zatwierdzoną próbę
hasłem początkowym; błędy transportu i protokołu kończą bootstrap.

Zmiana jest potwierdzana wyłącznie przez `result.userids` zgodne z odczytanym
użytkownikiem. Dla Zabbix 7.0.31 żądanie `user.update` zawiera `current_passwd`
z tym samym hasłem początkowym, którym powiodło się logowanie Admin, oraz
`passwd` z hasłem docelowym. Oba hasła pozostają poza diagnostyką i logami.
Działające hasło docelowe pomija aktualizację. Błąd wylogowania
trafia do `warnings` i nie zmienia sukcesu w błąd ani nie przesłania pierwotnego
błędu. Przy niepotwierdzonej aktualizacji wynik jest błędem; kolejne uruchomienie
sprawdza hasło docelowe, więc może rozpoznać wcześniej wykonaną zmianę.

Zadanie Ansible zachowuje `no_log: true` i `diff: false`. Lokalny filtr roli
`zabbix_bootstrap_diagnostic` parsuje JSON, wymaga rzeczywistych wartości bool
dla `failed` i `changed` oraz sprawdza `stage` i `code` względem zamkniętych list.
Zadanie parsujące również ma `no_log: true`. Osobne `ansible.builtin.fail`
zatrzymuje wykonanie i pokazuje tylko `stage` oraz `code`, bez ostrzeżeń ani
surowego `stdout`, `stderr`, stdin, haseł i tokenów. Nieprawidłowy wynik daje
`stage=input code=DIAGNOSTIC_UNAVAILABLE`. Niezerowy kod wyjścia nigdy nie
jest sukcesem, a `failed=true` zatrzymuje wykonanie także przy kodzie wyjścia 0.
`changed_when` uznaje zmianę tylko dla zweryfikowanego sukcesu z `changed=true`;
ponowne wykonanie z aktualnym hasłem pozostaje bez zmian. W check mode wszystkie
trzy zadania są pomijane. Przepływ przygotowano lokalnie, bez wdrożenia.

Szablon serwera ustawia `PidFile=/run/zabbix/zabbix_server.pid`, zgodnie ze
ścieżką `PIDFile` zgłoszonej jednostki systemd z `Type=forking`. Zapobiega to
oczekiwaniu systemd na inny plik PID podczas zadania `Enable services`.
Nie zmieniamy jednostki ani nie dodajemy dublującego zarządzania katalogiem.
Tworzenie `/run/zabbix` przez pakiet wymaga potwierdzenia: lokalnie nie ma pakietu
ani jego jednostki, więc nie potwierdzono właściciela i uprawnień katalogu.
Opcjonalny test rozpakowuje lokalny pakiet bez instalacji i bez wykonywania jego
skryptów; sprawdza wersję, zgodność PID oraz `RuntimeDirectory` lub wpis tmpfiles
z właścicielem `zabbix:zabbix` i trybem `0755`:

```bash
ZABBIX_SERVER_DEB=/path/to/zabbix-server-pgsql_7.0.31-1+ubuntu24.04_amd64.deb \
  python3 -B -m unittest discover -s tests -p 'test_zabbix_server.py' -v
```

Bez `ZABBIX_SERVER_DEB` test pakietu jest pomijany; test regresyjny ścieżki PID
działa zawsze. Nie stanowi to potwierdzenia uruchomienia usługi na serwerze.

```bash
python3 -B -m unittest discover -s tests -p 'test_zabbix*.py' -v
terraform -chdir=terraform fmt -check dom_zabbix01.tf
# validate wymaga już lokalnie zainstalowanych providerów; nie wykonuj init na laptopie.
terraform -chdir=terraform validate
cd ansible
ansible-playbook playbooks/zabbix-server.yml --syntax-check
ansible-playbook playbooks/zabbix-local-access.yml --syntax-check
ansible-playbook playbooks/zabbix-agents.yml --syntax-check
ansible-playbook playbooks/zabbix-register.yml --syntax-check
```

Testy Python korzystają z atrap HTTP i nie łączą się z siecią. Sprawdzają tworzenie,
ponowne wykonanie, rotację PSK, zachowanie dodatkowych grup/szablonów/tagów,
odmowę przejęcia hostów i tras oraz idempotencję DNS/NPM. Parsowanie YAML i
renderowanie Jinja wymagają lokalnych PyYAML/Jinja2; brak powoduje pominięcie.
Nie instalowano zależności z sieci. Testy nie potwierdzają zgodności rzeczywistych API.

## Etapy wdrożenia — wyłącznie na iza po przeglądzie

Przed wykonaniem wykonaj kopię konfiguracji istniejących agentów i DNS/NPM,
sprawdź klucze SSH oraz sudo. Na iza (`/opt/ai/projects/infrastructure`) zainstaluj
zatwierdzone zależności kolekcji zgodnie z procedurą projektu:

```bash
cd /opt/ai/projects/infrastructure/ansible
ansible-galaxy collection install -r requirements.yml
```

### 1. VM

Załaduj istniejącą procedurą tokeny Proxmox na iza. Nie kopiuj ich do repozytorium.
Wyłączony domyślnie zasób wymaga zachowania zatwierdzonego `-var-file` **w każdym
późniejszym plan/apply**, inaczej Terraform zaproponuje usunięcie VM (ochrona
Proxmox nie zastępuje przeglądu planu). Docelowo włącz wartości w prywatnej
konfiguracji stosowanej przez administratora do wszystkich operacji Terraform.

```bash
cd /opt/ai/projects/infrastructure
terraform -chdir=terraform plan \
  -var-file=/home/tom/.config/infrastructure/zabbix/zabbix.tfvars \
  -target='proxmox_virtual_environment_vm.zabbix01[0]' \
  -out=/home/tom/.config/infrastructure/zabbix/vm.plan
terraform -chdir=terraform show /home/tom/.config/infrastructure/zabbix/vm.plan
# Dopiero po zatwierdzeniu zapisanego planu:
terraform -chdir=terraform apply /home/tom/.config/infrastructure/zabbix/vm.plan
```

Celowanie to jednorazowy etap nowej VM, z zależnościami cloud image. Plan musi
zawierać wyłącznie nową VM i ewentualnie zatwierdzone zależności; żadnej zmiany
istniejących VM. Jeśli wspólny obraz wymaga zmian lub provider proponuje inne
operacje, zatrzymaj się. Nie używaj import/state mv/rm. Po etapie przejrzyj pełny
plan bez `-target` (z tym samym var-file), bez automatycznego zastosowania.

### 2–5. Serwer → DNS/NPM → agenci → rejestracja

Polecenia zakładają jedno hasło Vault (`--ask-vault-pass`) dla prywatnego `vault.yml`
Zabbix; Vault Langfuse nie jest potrzebny. Pliki prywatne pozostają na iza. Nie uruchamiaj z `--diff` dla sekretów.

```bash
cd /opt/ai/projects/infrastructure/ansible
ansible-playbook playbooks/zabbix-server.yml --limit zabbix01 \
  --ask-become-pass --ask-vault-pass \
  -e @/home/tom/.config/infrastructure/zabbix/settings.yml \
  -e @/home/tom/.config/infrastructure/zabbix/vault.yml
ansible-playbook playbooks/zabbix-local-access.yml --limit dns01,npm01 \
  --ask-become-pass --ask-vault-pass \
  -e @/home/tom/.config/infrastructure/zabbix/settings.yml \
  -e @/home/tom/.config/infrastructure/zabbix/vault.yml
# Pilot: agent i rejestracja wyłącznie zabbix01 (bez tokenów Proxmox):
ansible-playbook playbooks/zabbix-agents.yml --limit zabbix01 \
  --ask-become-pass --ask-vault-pass \
  -e @/home/tom/.config/infrastructure/zabbix/settings.yml \
  -e @/home/tom/.config/infrastructure/zabbix/vault.yml
ansible-playbook playbooks/zabbix-register.yml --limit zabbix01 \
  --ask-become-pass --ask-vault-pass \
  -e zabbix_registration_mode=pilot \
  -e @/home/tom/.config/infrastructure/zabbix/settings.yml \
  -e @/home/tom/.config/infrastructure/zabbix/vault.yml
# Dopiero po weryfikacji pilota (poniżej):
ansible-playbook playbooks/zabbix-agents.yml --limit 'zabbix_agents:!zabbix01' \
  --ask-become-pass --ask-vault-pass \
  -e @/home/tom/.config/infrastructure/zabbix/settings.yml \
  -e @/home/tom/.config/infrastructure/zabbix/vault.yml
# Pełna rejestracja wszystkich 16 hostów (wymaga PSK wszystkich hostów; tokeny Proxmox opcjonalne):
ansible-playbook playbooks/zabbix-register.yml --limit zabbix01 \
  --ask-become-pass --ask-vault-pass \
  -e zabbix_registration_mode=full \
  -e @/home/tom/.config/infrastructure/zabbix/settings.yml \
  -e @/home/tom/.config/infrastructure/zabbix/vault.yml
```

`zabbix_registration_mode` jest wymagany: `pilot` rejestruje tylko `zabbix01`,
`full` — całą grupę `zabbix_agents`. Pełny tryb aktualizuje `zabbix01` utworzony
w pilocie (tag `managed-by`), bez duplikatów. Błąd rejestracji zwraca bezpieczny
komunikat (nazwa hosta lub metody API), bez sekretów.

Weryfikacja pilota (na `zabbix01`, a potem w panelu):

```bash
ssh -t tom@192.168.55.29 'systemctl is-active zabbix-server zabbix-agent2 \
  && sudo journalctl -u zabbix-agent2 -u zabbix-server --since -15min \
     | grep -iE "psk|active check|cannot|error" | tail -n 20'
```

W panelu: Monitoring → Hosts → `zabbix01` — dostępność ZBX (aktywne, zielona),
Latest data z ostatnich minut (np. `system.uptime`, CPU). Po pełnej rejestracji
to samo dla 16 hostów oraz dane szablonu `Proxmox VE by HTTP` dla `dom` i `dtcode`.

Serwer i integracje API wymagają realnego wykonania; `--check` nie symuluje pełnej
instalacji ani zapisów API. Dla agentów pozostaje opisana wcześniej ograniczona
obsługa check mode. Po wdrożeniu powtórz cztery etapy Ansible z tymi samymi
parametrami: konfiguracja, schema i rejestracja nie powinny wykazywać zmian.
Sprawdź z iza: `getent hosts zabbix.home.lab`, `curl -I http://zabbix.home.lab`,
16 hostów w panelu, dane aktywnych agentów, PSK, metryki Proxmox i odmowę dostępu
spoza LAN. Zweryfikuj `nginx -t`, stan usług i logi na nowej VM oraz ACL NPM.
Zapisz rzeczywiste wyniki w STATUS/INVENTORY dopiero po wykonaniu. Kopia bazy,
konfiguracji i zaszyfrowanych sekretów jest warunkiem odtwarzania; nie kasuj bazy
ani VM w celu ponowienia playbooków. Nie dodano harmonogramu backupu Zabbix.

## Wynik lokalnej kontroli (2026-10-10)

Po dodaniu bezpiecznej diagnostyki w Ansible:
`python3 -B -m unittest discover -s tests -v` — 47 testów, 44 zaliczone,
3 pominięte (brak PyYAML/Jinja2 i lokalnego `.deb`). Osiem nowych testów sprawdza
filtr używany przez rolę: sukces i powtórzenie, błąd, nieprawidłowy JSON,
zamknięte wartości i typy, sprzeczny kod wyjścia oraz brak ujawnienia sekretów.
Lokalny Ansible jest niedostępny, więc nie wykonano `--syntax-check` ani testu
wykonania zadań przez Ansible. Wynik dotyczy testów Python i kontroli statycznej.

Po poprawce diagnostyki bootstrapu: `python3 -B -m unittest discover -s tests -v`
— 39 testów, 36 zaliczonych, 3 pominięte (brak PyYAML/Jinja2 i lokalnego `.deb`).
Testy obejmują wszystkie etapy bootstrapu, błędy HTTP/transportu/JSON/JSON-RPC,
brak wyniku, potwierdzanie aktualizacji, ponowne uruchomienie, błędy wylogowania
i brak sekretów w diagnostyce. `git diff --check`: bez błędów.
Nie wykonano połączeń z serwerem ani bazą, wdrożenia, commita ani push.

Po poprawce PID pełny zestaw `python3 -B -m unittest discover -s tests -v`:
32 testy, 29 zaliczonych, 3 pominięte (brak PyYAML/Jinja2 i lokalnego pakietu
Zabbix do inspekcji). Test ścieżki PID zaliczony. Brak lokalnego Ansible
uniemożliwia `--syntax-check`. Poprawki nie wdrożono.

Testy Zabbix offline obejmują również import schematu z atrapami `psql`/`gzip`:
pusta baza, ponowne wykonanie, nieprawidłowa istniejąca baza i błędy importu.
Nie wykonują zapytań do PostgreSQL. Sprawdzają też przypięte parametry,
konfigurację usług i błędy bootstrapu przez atrapę HTTP.
`python3 -B -m unittest discover -s tests -p 'test_zabbix*.py' -v`: 16 testów,
14 zaliczonych, 2 pominięte. `bash -n` skryptu importu i `git diff --check`: bez błędów.
Brak lokalnych PyYAML/Jinja2 oraz Ansible ogranicza walidację: parsowanie YAML,
renderowanie szablonów i `--syntax-check` należy wykonać na iza przed wdrożeniem.
Nie wykonano połączeń sieciowych ani wdrożenia. Wyniki testów są dowodem lokalnym,
nie potwierdzeniem działania ani idempotencji na rzeczywistym serwerze.
