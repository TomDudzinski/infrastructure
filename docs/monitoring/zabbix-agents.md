# Zabbix Agent 2 — przygotowanie do wdrożenia

Kod przygotowany lokalnie; niczego nie zainstalowano ani nie zweryfikowano na hostach.
Ansible uruchamia administrator wyłącznie na `iza`. Pełna automatyzacja nowej VM i serwera: [procedura Zabbix](zabbix-deployment.md).
Grupa `zabbix_agents` obejmuje 14 istniejących hostów oraz planowany `zabbix01`; nie zawiera
zatrzymanych VM ani szablonów. Root: `dom`, `dtcode`, `dns01`; pozostali: `tom`.
Wspólny klucz `/home/tom/.ssh/homelab_automation_ed25519` musi istnieć na `iza`.
`iza` zachowuje połączenie lokalne i istniejące ustawienia `sudo.ws`.
Dla pozostałych kont `tom` wymagane są uprawnienia sudo; hasło podaje się interaktywnie.
Ustawienia dostępu są konfiguracją żądaną, nie potwierdzeniem łączności.

## Parametry

Przed uruchomieniem ustaw w `group_vars/zabbix_agents.yml` lub odpowiednich
`host_vars` (wartości zależne od systemu), albo w prywatnym pliku `-e @...`:

```yaml
zabbix_deployment_approved: true
zabbix_server_ip: "APPROVED_ZABBIX_SERVER_IP"
zabbix_agent_release: "7.0"
zabbix_agent_package_version: "EXACT_APT_VERSION"
zabbix_agent_server: "ZABBIX_SERVER_ADDRESS"
zabbix_agent_server_active: "ZABBIX_SERVER_ADDRESS:10051"
zabbix_agent_hostname: "HOSTNAME_REGISTERED_IN_ZABBIX"
zabbix_agent_tls_connect: psk
zabbix_agent_tls_accept: psk
zabbix_agent_tls_psk_identity: "HOST_UNIQUE_IDENTITY"
zabbix_agent_tls_psk: "{{ vault_zabbix_agent_tls_psk }}"
```

Nie kopiuj placeholderów do wdrożenia. Wersja pakietu jest wymagana (łącznie z epoch
oraz sufiksem dystrybucji), bez automatycznego upgrade/downgrade. Sprawdź ją na `iza`
przed wdrożeniem w oficjalnym repozytorium dla danego systemu. Domyślna macierz:
Debian 11/12/13 i Ubuntu 20.04/22.04/24.04; Proxmox korzysta z wersji bazowego Debiana.
Dostępność pakietów i URL nie była sprawdzana przez sieć.
Dla Ubuntu 26.04 na `iza` wymagane jest potwierdzenie oficjalnego wsparcia i ustawienie
`zabbix_agent_repository_deb_url` oraz `zabbix_agent_repository_deb_checksum`
(np. `sha256:...`). Nie wybieraj repozytorium 24.04 jako zamiennika. Jeżeli brak
obsługi danej wersji, nie wdrażaj na tym hoście; użyj `--limit` dla pozostałych.
Override URL/checksum umożliwia też przypięcie konkretnego pakietu repozytorium;
domyślny URL używa oficjalnego `zabbix-release_latest` dla wybranej gałęzi.

TLS: `unencrypted`, `psk` albo `cert`, osobno dla połączeń aktywnych i pasywnych.
Dla certyfikatów ustaw absolutne ścieżki `zabbix_agent_tls_ca_file`,
`zabbix_agent_tls_cert_file`, `zabbix_agent_tls_key_file`; przygotuj pliki oddzielnie,
z kluczem czytelnym dla użytkownika `zabbix`. Nie przechowuj kluczy prywatnych w Git.
PSK (32–512 znaków hex, parzysta długość) przechowuj w Ansible Vault, najlepiej
jako zaszyfrowaną zmienną per host przez `ansible-vault encrypt_string`.
Rola zapisuje PSK z prawami 0640 i ukrywa je w logach i diff.
Nie zmieniaj `host_vars/langfuse01/vault.yml`. Nie umieszczaj sekretów Langfuse
w grupie `all` ani nie wczytuj ich przez `vars_files` w tym playbooku.
`--limit mysql01` nie wymaga odszyfrowania Vault Langfuse; wybranie `langfuse01`
może wymagać istniejącego hasła Vault. Nie używaj `ansible-inventory --list` z Vault.

Rola zarządza pakietem, repozytorium i głównym plikiem konfiguracyjnym Agent 2
(z kopią poprzedniej konfiguracji), pozostawia istniejące fragmenty `.d` i inne usługi.
Przed wdrożeniem sprawdź istniejącą konfigurację agenta i konflikty dyrektyw we
fragmentach, zajęcie portu 10050 przez starszy agent oraz wersję serwera Zabbix.
Restart Agent 2 następuje przy zmianie pakietu, konfiguracji lub PSK.
Rejestrację API i instalację serwera opisuje [procedura Zabbix](zabbix-deployment.md).
Istniejące firewalle pozostają poza zarządzaniem rolą agenta.

## Testy lokalne — bez połączeń z hostami

Z katalogu głównego repozytorium:

```bash
python3 -B -m unittest discover -s tests -p 'test_zabbix_agent.py' -v
cd ansible
ansible-playbook playbooks/zabbix-agents.yml --syntax-check
ansible-playbook playbooks/zabbix-agents.yml --list-hosts --limit mysql01
```

Test renderowania TLS i parsowania YAML wymaga lokalnych PyYAML i Jinja2;
bez nich jest oznaczony jako pominięty. Kontrola składni wymaga Ansible Core.
Te komendy nie instalują narzędzi i nie wykonują playbooka na hostach.

## Wdrożenie — wyłącznie na iza, po zatwierdzeniu

Najpierw przygotuj parametry, dostęp SSH/sudo, sekrety, repozytorium i kopię
istniejącej konfiguracji. Zacznij od jednego zatwierdzonego hosta:

```bash
cd ansible
ansible-playbook playbooks/zabbix-agents.yml --limit mysql01 \
  --check --diff --ask-become-pass -e @/secure/zabbix-settings.yml
ansible-playbook playbooks/zabbix-agents.yml --limit mysql01 \
  --ask-become-pass -e @/secure/zabbix-settings.yml
```

Dodaj `--ask-vault-pass` lub istniejące `--vault-id`, jeśli wybrane hosty wymagają
odszyfrowania zmiennych. Tryb `--check` nadal łączy się z hostami: nie uruchamiaj go
na laptopie. Pomija pobranie repozytorium i instalację pakietu; na hoście bez agenta
nie symuluje konfiguracji ani usługi. Na hoście z agentem sprawdza diff konfiguracji.
Po wdrożeniu powtórz wykonanie dla tego samego zakresu i sprawdź idempotencję,
stan agenta oraz odbiór danych w Zabbix. Rozszerzaj zakres dopiero po weryfikacji.
Zaktualizuj dokumentację o rzeczywiste wyniki, bez utożsamiania kodu z wdrożeniem.
