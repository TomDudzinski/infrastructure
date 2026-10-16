# Prototyp DB-GPT + LiteLLM

Status: przygotowano kod, **nie wdrożono**. Laptop służy wyłącznie do edycji i statycznego przeglądu. Wszystkie poniższe operacje sieciowe, Terraform i Ansible wykonuje operator na `iza` po akceptacji. Nie wykonano testów infrastruktury.

## Zakres i zgodność

Jedna VM `dbgpt01` na `dom`: Ubuntu 24.04, 4 vCPU, 8 GiB RAM, dysk 40 GiB. Terraform domyślnie ją wyłącza; VMID i IP nie zostały przydzielone. Ansible korzysta z istniejących ról Docker, QEMU i Zabbix Agent 2. Osobny dodatkowy inventory nie dodaje hosta do dotychczasowych zbiorczych wdrożeń.

DB-GPT używa `proxy/openai` przez LiteLLM (`/v1`), SQLite dla metadanych i Chroma dla schematu. `quality` jest pierwszym modelem; `fast` wybiera się w UI. LiteLLM kieruje aliasy do Qwen3 4B i 8B w istniejącej Ollama na `iza`; embeddingi do `qwen3-embedding:0.6b`. Brak dostawców zewnętrznych i automatycznego fallbacku. Prompty po polsku nie wymagają polskiej lokalizacji UI. Pliki nie zmieniają Ollama, Open WebUI ani db-agent.

Zweryfikowano kontrakt konfiguracji w źródłach, nie działanie obrazów:

- [DB-GPT: konfiguracja proxy w v0.7.5](https://github.com/eosphoros-ai/DB-GPT/blob/v0.7.5/configs/dbgpt-proxy-openai.toml)
- [DB-GPT: aktualny kontrakt proxy](https://github.com/eosphoros-ai/DB-GPT/blob/main/configs/dbgpt-proxy-openai.toml)
- [DB-GPT: Docker i trwałe dane](https://github.com/eosphoros-ai/DB-GPT/blob/main/docs/docs/installation/docker.md)
- [LiteLLM: Ollama](https://docs.litellm.ai/docs/providers/ollama)

Nie utożsamiaj v0.7.5 z aktualnym wydaniem. Obrazy są celowo wymaganymi parametrami w postaci digestów: na `iza` wybierz aktualne, sprawdzone wydanie `eosphorosai/dbgpt-openai` i LiteLLM, porównaj konfigurację z jego źródłami i zapisz digesty w host_vars. Dostępność obrazu, sterownika MySQL i obsługa embeddingów wymagają próby startowej. Nie stosuj `latest` do wdrożenia.

## Przygotowanie na iza

1. Potwierdź wolny VMID, IP w `192.168.55.0/24`, zasoby `dom` i uprawnienia istniejącego konta Terraform. Ustaw `dbgpt01_ip` i digesty obrazów w `ansible/inventories/production/host_vars/dbgpt01.yml`. Nie zmieniaj adresów istniejących hostów.
2. Sprawdź `ollama list` na `iza`. Wymagane są Qwen3 4B, 8B i embeddingi. Brakujące modele pobierz ręcznie dopiero po akceptacji dodatkowego zużycia zasobów; playbook nie zmienia Ollama. Potwierdź dostęp VM do istniejącego `192.168.55.7:11434`. Jeżeli endpoint nie jest dostępny, zatrzymaj wdrożenie i uzgodnij zmianę osobno.
3. W istniejącym podejściu Ansible Vault przygotuj zaszyfrowany plik `ansible/vaults/dbgpt01.yml` (przez `ansible-vault create`). Zawartość: `vault_dbgpt_litellm_key` (prefiks `sk-` i min. 32 znaki alfanumeryczne), `vault_dbgpt_encrypt_key` (32 znaki alfanumeryczne), `vault_dbgpt_mysql_password` (min. 24 znaki), dotychczasowy `vault_zabbix_admin_password` i mapa `vault_zabbix_psks` z wpisem `dbgpt01`. Można zamiast kopiowania sekretów podać dodatkowy istniejący zaszyfrowany plik przez `-e @...`. Nigdy nie zapisuj jawnego pliku ani hasła w poleceniu.
4. Zainstaluj kolekcje zgodnie z repozytorium: `cd ansible && ansible-galaxy collection install -r requirements.yml`.

## Wdrożenie wyłącznie z iza

W istniejącym katalogu i stanie Terraform utwórz ignorowany plik `dbgpt01.auto.tfvars` z `dbgpt01_enabled = true`, zatwierdzonym `dbgpt01_vmid` i `dbgpt01_ipv4_cidr`. Zachowaj wszystkie dotychczasowe parametry włączenia pozostałych VM. Uruchom zwykły `terraform plan -out=dbgpt01.tfplan` z dotychczasowym zestawem zmiennych. Plan musi zawierać wyłącznie utworzenie nowej VM, bez usunięć lub zmian istniejących zasobów. Po przeglądzie i akceptacji operator wykonuje `terraform apply dbgpt01.tfplan`. Nie używaj `-target` jako zamiennika przeglądu pełnego planu. Potwierdź klucz SSH nowej VM zgodnie z istniejącą procedurą.

Z katalogu `ansible` (wszystkie polecenia na `iza`):

```bash
ansible-playbook -i inventories/production/hosts.yml -i inventories/production/dbgpt.yml playbooks/dbgpt-synthetic-db.yml --limit mysql01 -e @vaults/dbgpt01.yml --ask-vault-pass -e dbgpt_synthetic_setup_approved=true
ansible-playbook -i inventories/production/hosts.yml -i inventories/production/dbgpt.yml playbooks/dbgpt01-bootstrap.yml --limit dbgpt01 -e @vaults/dbgpt01.yml --ask-vault-pass -e dbgpt_deployment_approved=true
ansible-playbook -i inventories/production/hosts.yml -i inventories/production/dbgpt.yml playbooks/zabbix-register.yml --limit zabbix01 -e @vaults/dbgpt01.yml --ask-vault-pass -e zabbix_deployment_approved=true -e zabbix_registration_mode=single -e zabbix_registration_target=dbgpt01
```

Pierwsze polecenie dodaje wyłącznie syntetyczną bazę i dedykowanego użytkownika na istniejącym MySQL. Nie uruchamia roli mysql_server i nie restartuje usługi. Dane wstawia przez INSERT IGNORE; ponowne uruchomienie nie przesuwa dat. Wymaga już istniejącego PyMySQL oraz dostępu administratora przez lokalny socket. Przed wykonaniem potwierdź, że nazwy `dbgpt_synthetic` i `dbgpt_reader` nie należą do innych zastosowań. Użytkownik może SELECT/SHOW VIEW wyłącznie w tej bazie, wyłącznie z IP nowej VM; nie ma uprawnień zapisu. Sprawdź istniejącą zaporę i dostęp do MySQL:3306, bez zmiany konfiguracji usługi.

UI jest związane wyłącznie z loopback VM. Na `iza` operator może otworzyć tunel `ssh -N -L 5670:127.0.0.1:5670 tom@APPROVED_VM_IP`; UI jest wtedy dostępne na loopback `iza`. Dalszy dostęp z przeglądarki wymaga prywatnego tunelu zgodnego z lokalną polityką. Brak publikacji w NPM/Cloudflare i brak portu hosta dla LiteLLM. DB-GPT nie ma skonfigurowanego logowania do UI: udostępniaj tunel tylko operatorowi. Dane i historia pozostają w trzech wolumenach Docker; nie wykonuj `down -v`. Zachowaj klucz szyfrowania w Vault.

W UI dodaj źródło MySQL: host `192.168.55.21`, port `3306`, baza `dbgpt_synthetic`, użytkownik `dbgpt_reader`, hasło z Vault. Nie dodawaj produkcyjnego źródła. Wybierz wbudowany Chat Data/Chat DB (Text-to-SQL), zaindeksuj schemat i wybierz `quality`. Sprawdź także `fast`. Jeżeli obraz nie zawiera konektora MySQL lub wybranej funkcji, zatrzymaj odbiór i dobierz oficjalny obraz z odpowiednimi dodatkami; nie instaluj własnego agenta.

## Krótki odbiór ręczny

Daty danych są względne wobec dnia pierwszego importu. Kontekst: turnus = stays, uczestnicy = SUM(reservations.participants), rezerwacje = COUNT(*), płatności = SUM(payments.amount). Nie sumuj uczestników po bezpośrednim złączeniu z payments: rezerwacja 1 ma dwie płatności.

Dla obu modeli zapisz wygenerowany SQL, wynik, czas od wysłania pytania do odpowiedzi (zimny i ciepły model), model i wersje obrazów. Porównaj z poniższymi SELECT-ami wykonanymi jako dbgpt_reader. Nie oznaczaj testu jako zaliczony bez pomiaru.

| Pytanie | SQL kontrolny / oczekiwanie |
|---|---|
| Pięć najbliższych turnusów | `SELECT id,name,starts_on FROM stays WHERE starts_on >= CURRENT_DATE ORDER BY starts_on,id LIMIT 5;` — tuż po imporcie ID 2–6 |
| Liczba uczestników we wszystkich turnusach | `SELECT SUM(participants) FROM reservations;` — 17 |
| A na ostatnim? (ta sama rozmowa) | Ustal znaczenie: ostatni zakończony czy ostatni chronologicznie. Dla ostatniego zakończonego: `SELECT SUM(r.participants) FROM reservations r JOIN stays s ON s.id=r.stay_id WHERE s.id=(SELECT id FROM stays WHERE ends_on < CURRENT_DATE ORDER BY ends_on DESC,id DESC LIMIT 1);` — tuż po imporcie 5. Dla ostatniego chronologicznie (ID 6): 2. Niejednoznaczność musi zostać wyjaśniona. |
| Porównaj liczbę rezerwacji w poprzednim turnusie i najbliższym przyszłym | `SELECT s.id,COUNT(r.id) FROM stays s LEFT JOIN reservations r ON r.stay_id=s.id WHERE s.id IN (1,2) GROUP BY s.id;` — 2 i 1; ID sprawdź względem aktualnej daty |
| Suma płatności | `SELECT SUM(amount) FROM payments;` — 1550.00 |

Sprawdź odrzucenie INSERT/UPDATE przez konto RO, indeksowanie schematu i zachowanie rozmowy po restarcie kontenera na nowej VM. Nie testuj zapisu na innych bazach. W Zabbix potwierdź host `dbgpt01`, jego zatwierdzony IP, PSK, przypisany szablon Linux, świeże Latest data i dostępność agenta. Sama rejestracja hosta nie dowodzi odbioru metryk.

Do weryfikacji na iza pozostają: obrazy i ich start, konektor MySQL, embeddingi, łączność, SQL i odpowiedzi po polsku, kontekst rozmowy, czasy, trwałość danych oraz metryki Zabbix. Nie uruchomiono lokalnie Terraform, Ansible ani Docker: narzędzia nie są zainstalowane w środowisku wykonawczym. Wykonano lokalny przegląd plików i parsowanie TOML. Po odbiorze uzupełnij INVENTORY.md i STATUS.md o faktyczne VMID/IP i wyniki, bez oznaczania obecnego kodu jako wdrożenia.
