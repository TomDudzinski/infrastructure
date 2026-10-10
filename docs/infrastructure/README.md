# Inwentaryzacja infrastruktury

Raport bazowy: **2026-10-10 (Europe/Warsaw)**. Analiza wyłącznie lokalna;
żaden kolektor nie został uruchomiony na rzeczywistej infrastrukturze.

## Zakres i źródła

- `terraform/*.tf`: 11 definicji VM/LXC; Terraform zarządza infrastrukturą.
- `ansible/inventories/production/hosts.yml`, `playbooks/`, `roles/`:
  konfiguracja hostów i usług, istniejący Ansible Vault dla sekretów Langfuse.
  Grupa `dtcode_existing` jest inventory-only, nie oznacza przypisania ról.
- `compose/*/compose.yaml`: cztery aplikacje na `iza`.
  Jupyter używa zmiennej `JUPYTER_PORT` (domyślnie 8888);
  port w bazowym JSON jest wartością domyślną, nie pomiarem.
- Szablony Compose w rolach Ansible dla Qdrant i Langfuse nie są dowodem
  uruchomienia kontenerów. Bazowa lista kontenerów obejmuje tylko `compose/`.
- Istniejące źródła: [główna inwentaryzacja](../../INVENTORY.md),
  [status](../../STATUS.md), [sieć](../network/NETWORK.md),
  [backup](../backup/BACKUP.md), [adopcja dtcode](../operations/dtcode-adoption-2026-10-04.md).
  Zachowują opis architektury i historyczne ustalenia; nowy raport jest
  datowanym rejestrem obserwacji, nie ich zamiennikiem.
- `scripts/server-status.sh`, `healthcheck.sh`, `backup-report.sh` istnieją,
  lecz generują diagnostykę tekstową i część wykonuje operacje na usługach.
  Nowy skrypt pozostaje w `scripts/`, bez zależności i bez nowego frameworka.

Bazowy JSON przygotowano przez lokalny przegląd wybranych pól konfiguracji
(nazwa, ID, node, IP, bridge, CPU, pamięć, pierwszy dysk, obraz i port).
Nie jest pełnym parserem Terraform/YAML ani automatycznym odczytem state.
Nie czytano `.env`, tfstate, tfvars, kluczy ani zawartości Vault.
Po zmianie kodu operator aktualizuje ten plik na podstawie przeglądu diffu;
nie wolno automatycznie uznawać konfiguracji za stan rzeczywisty.

## Statusy i granice potwierdzenia

- `confirmed`: odczyt kolektora z `observed_at`; potwierdza tylko zapisane pola
  w chwili odczytu. Nie oznacza zdrowia aplikacji, restore ani zgodności z kodem.
- `unverified`: kod, dokumentacja lub starsze informacje bez aktualnego pomiaru.
- `planned`: jawnie zatwierdzony zamiar przyszłej zmiany; sam kod nie wystarcza.

W bazie wszystkie 19 rekordów mają `unverified`. Starsze opisy „Verified”
nie są nowym potwierdzeniem na 2026-10-10. Snapshot datowany na początek dnia
jest etykietą raportu bazowego, nie czasem pomiaru infrastruktury.
Status rekordu nie zastępuje oceny bezpieczeństwa i pokrycia backupem.

## Kolektory — tylko na właściwym hoście, przez operatora

**Nie uruchamiać tych poleceń na laptopie deweloperskim.** Laptop służy
wyłącznie do edycji, przeglądu i statycznej walidacji oraz generowania raportu
z już dostarczonych plików JSON. Brak SSH, zdalnej automatyzacji i wdrożeń.

Przykłady wykonywane ręcznie przez operatora na hostach infrastruktury:

```bash
# Linux, na inwentaryzowanym hoście (Python 3.9+, iproute2):
python3 scripts/infrastructure_inventory.py collect linux --output /tmp/iza-linux.json
# Docker, na hoście lokalnego demona (Python + docker CLI, dostęp do socketu):
python3 scripts/infrastructure_inventory.py collect docker --output /tmp/iza-docker.json
# Proxmox, na węźle PVE (Python + pvesh, uprawnienia odczytu):
python3 scripts/infrastructure_inventory.py collect proxmox --output /tmp/dtcode-proxmox.json
```

Linux zbiera hostname, liczbę logicznych CPU, RAM i adresy interfejsów.
Proxmox odczytuje `pvesh get /cluster/resources --type vm`: VM/LXC, node,
ID, nazwę, stan, CPU, RAM, pojemność dysku. To zestawienie klastra;
nie odczytuje konfiguracji sieci gościa, storage backendów ani backupów.
Wystarczy jeden odczyt na klaster; nie łączyć duplikatów tego samego zasobu.
Docker odczytuje listę kontenerów przez jawny lokalny socket
`unix:///var/run/docker.sock`, niezależnie od DOCKER_HOST i kontekstu CLI:
nazwy, obrazy i stan. Nie zbiera env, etykiet, poleceń, logów ani inspect.
Porty, wolumeny, sieci Docker i obrazy nieużywane nie są obecnie kolekcjonowane.
Dostęp do socketu Docker i pvesh jest uprzywilejowany; nie nadawać nowych
uprawnień ani nie zmieniać konfiguracji usług na potrzeby tej analizy.

Kod wyjścia 0 = odczyt zakończony; 2 = dane niepełne/niedostępne, ale JSON
z informacją o pokryciu zapisany; 1 = odrzucony schemat/błąd zapisu.
Nie zapisujemy stderr narzędzi. Wyjątki i pola o podejrzanej treści blokują
zapis zamiast kopiowania surowych danych. Kolektory mają timeout 30 s.
Snapshot nie nadpisuje istniejącego pliku; używać nowych nazw.
Dane przenieść na laptop zatwierdzonym procesem operatora poza tym narzędziem.

## Generowanie i aktualizacja — offline na laptopie

Bez instalowania zależności, z katalogu głównego repozytorium:

```bash
# Odtworzenie bazowego raportu (ta sama migawka i porównanie są idempotentne):
python3 -B scripts/infrastructure_inventory.py report \
  docs/infrastructure/data/baseline-2026-10-10.json --output docs/infrastructure

# Nowa inwentaryzacja z plików dostarczonych przez operatora:
python3 -B scripts/infrastructure_inventory.py report \
  /tmp/iza-linux.json /tmp/iza-docker.json /tmp/dtcode-proxmox.json \
  --previous docs/infrastructure/history/20261009T220000Z.json \
  --output docs/infrastructure

# Testy wyłącznie na fixture i mockach, bez połączeń:
python3 -B -m unittest discover -s tests -v
```

Nowy raport zastępuje CURRENT_STATE, INVENTORY, NETWORK i indeks CHANGELOG,
pozostawiając SECURITY, BACKUPS i tę instrukcję do ręcznej aktualizacji.
W `history/` zapisuje migawkę UTC i jej niezmienny opis różnic Markdown.
Do `--previous` wskazać najnowszą wcześniejszą migawkę; generator wymaga
starszej daty. Historia nie jest automatycznie usuwana. Jednoczesne uruchamianie
generatora w jednym katalogu nie jest obsługiwane.

Nie mieszać bazowej i runtime listy tego samego zasobu: duplikaty ID są
odrzucane. Nie nadpisywać `confirmed` starszym wpisem statycznym. Porównywać
podobny zakres i sprawdzać `coverage`; brak rekordu oznacza brak obserwacji,
nie dowód usunięcia. Dodanie, brak, zmienione pola i statusy trafiają do historii;
same daty obserwacji nie powodują różnic. Hostname musi być stabilny.
Nazwy node w Proxmox i nazwę hosta Docker porównać z nazwami bazowymi przed
interpretacją diffu; różne nazwy utworzą odrębne ID.

Schemat v1: `schema_version`, `collected_at` (ISO 8601 ze strefą), `coverage`
(mapa scope → complete/partial/unavailable/static), `records`.
Pola rekordu są jawnie dozwolone w `FIELDS` skryptu; dodatkowe pola są błędem.
ID: `host/<host>`, `guest/<node>/<vmid>`, `container/<host>/<name>`,
`interface/<host>/<interface>/<address>`. Jednostki pamięci i dysku: bajty.
Brak pola = nie zebrano; zero w Proxmox może oznaczać brak wartości w API.
Przykłady schematu: `data/baseline-2026-10-10.json` i fixture w `tests/fixtures/`.

Po każdej zmianie: przejrzeć JSON i diff raportów, zaktualizować SECURITY,
BACKUPS oraz w razie potrzeby główne INVENTORY.md, STATUS.md i dokumentację
architektury. Wskazać źródła i brakujące dowody. Raport nie zastępuje audytu
firewalli, sekretów, backupów ani testu odtworzenia. Przed umieszczeniem w Git
sprawdzić wrażliwe informacje. Nie commitować ani pushować bez polecenia.

## Integracja z Ansible

Przygotowano osobny playbook `ansible/playbooks/infrastructure-inventory.yml`
i rolę `infrastructure_inventory`. Nie uruchamiano ich na infrastrukturze.
W inventory dodano tylko grupę `proxmox_hosts`: `dom` i `dtcode`; inne wpisy
pozostają zachowane. Laptop nadal służy wyłącznie do pracy lokalnej.

Dokładna komenda z katalogu głównego repozytorium **na `iza`**:

```bash
cd ansible
ansible-playbook -i inventories/production/hosts.yml \
  playbooks/infrastructure-inventory.yml --limit 'iza,dom,dtcode' --ask-become-pass
```

Dla częściowego raportu zastąpić limit np. przez `dom` lub `iza,mysql01`.
Playbook wymaga jawnego limitu, kontrolera o nazwie `iza` i normalnego trybu;
`--check` nie zbiera danych. Nie wybierać gości z niezweryfikowanymi parametrami
SSH. Operator wcześniej zapewnia zaufane host keys, Python 3.9+ i istniejące
uprawnienia odczytu; playbook nie instaluje pakietów ani nie nadaje uprawnień.
Wykonanie kolektorów używa `become: true`; hasło sudo wprowadza się interaktywnie.
Na Proxmox root nie wymaga sudo. Kontroler wymaga Python 3.9+ i Ansible;
nie wymaga dodatkowych kolekcji.

Na każdym wybranym hoście powstaje prywatny katalog tymczasowy. Skrypt jest
kopiowany, uruchamiany i usuwany wraz z wynikami w sekcji `always`.
Nie ma zmian usług, restartów ani trwałej instalacji. Linux zbierany jest na
wszystkich hostach; Proxmox na `proxmox_hosts`, Docker na pozostałych.
Listę można nadpisać przez `infrastructure_inventory_collectors` w host_vars.
`infrastructure_inventory_node` domyślnie odpowiada nazwie hosta inventory;
musi odpowiadać nazwie węzła PVE. Odczyt Proxmox filtruje wyniki klastra do tego
węzła (`collect proxmox --node dom`), aby uniknąć duplikatów w raporcie.
Brak Docker/ip/pvesh skutkuje informacją `unavailable`, bez instalacji narzędzi.
Kod 2 kolektora jest akceptowany jako częściowy wynik; inne błędy pomijają host.

JSON jest pobierany do nowego prywatnego katalogu `/tmp/infrastructure-inventory-*`
na kontrolerze. Generator otrzymuje wyłącznie pliki pomyślnie pobrane w bieżącym
uruchomieniu i zapisuje raport w podkatalogu `report`. Ścieżkę pokazuje playbook.
Nie nadpisuje raportu bazowego ani dokumentacji repozytorium. Jeśli żaden host
nie dostarczy kompletu plików, raport nie powstaje. Niedostępne hosty nie mają
wpisów coverage; trzeba sprawdzić recap Ansible i listę wybranych hostów.
Brak wpisu nie potwierdza usunięcia zasobu. Przerwanie procesu lub utrata
połączenia może uniemożliwić zdalne sprzątanie — operator usuwa wtedy pozostały
katalog tymczasowy po przywróceniu dostępu.

Surowe stdout/stderr kolektorów i transfer są objęte `no_log`. Kolektory stosują
istniejącą listę dozwolonych pól i walidację; nie czytają sekretów, env ani
pełnego inspect. Filtry tekstowe nie są pełnym wykrywaniem sekretów ukrytych
w nazwach zasobów: przed publikacją operator przegląda JSON i raport.
Pliki kontrolera pozostają do przeglądu; po zatwierdzonym przeniesieniu operator
usuwa katalog tymczasowy. Nie umieszczać wyników automatycznie w Git.

Testy offline obejmują filtrowanie dwóch węzłów, scalanie bez duplikatów,
częściowy raport oraz dotychczasowe zabezpieczenia schematu i kolektorów:
`python3 -B -m unittest discover -s tests -v`.
Walidacja składni i `--list-hosts` są lokalne; nie potwierdzają SSH, sudo ani
przebiegu rzeczywistego zbierania. Na laptopie nie wykonywać zwykłego playbooka.
