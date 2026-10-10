# Backups — baseline 2026-10-10

Bieżące wykonanie backupów i możliwość odtworzenia: **unverified**.
Źródło: [istniejąca dokumentacja backupu](../backup/BACKUP.md),
[scripts](../../scripts/) i [OpenBao recovery](../procedures/openbao-recovery.md).

| Zakres | Ustalenie z repozytorium | Status na dzień raportu |
|---|---|---|
| Konfiguracja i dane iza | Skrypty Restic i jednostki systemd istnieją | unverified |
| Terraform state | Dokumentowany backup repozytorium na QNAP | unverified |
| QNAP | NFS 192.168.55.5:/Backup; niezależne repozytorium Restic | unverified |
| Retencja lokalna | Skrypt: 7 daily, 4 weekly, 6 monthly, 2 yearly | unverified |
| Retencja QNAP | Dokumentacja wskazuje brak uzgodnionej polityki | unverified |
| OpenBao | Historyczny snapshot i weryfikacja szyfrowania; pełny restore niepotwierdzony | unverified |
| MySQL | Dokumentacja wskazuje brak skonfigurowanego logical backup | unverified |
| Pozostałe usługi | Brak aktualnych dowodów kompletności i restore | unverified |

Historyczne testy opisane na 2026-08-17 i 2026-08-18 nie są pomiarem
2026-10-10. Brak plików w checkout nie dowodzi braku kopii gdzie indziej.
Migawka inwentaryzacji nie jest backupem konfiguracji, state ani danych aplikacji.

Kolektory nie uruchamiają Restic, nie montują NFS, nie przeglądają archiwów,
nie pobierają sekretów i nie wykonują backupów ani restore. Weryfikacja
świeżości kopii, RPO/RTO, kompletności i odtworzenia wymaga oddzielnych dowodów
od operatora na zatwierdzonym hoście. Nigdy nie uruchamiać prune/forget lub
restore na potrzeby generowania tego raportu.

Historię raportów przechowywać w `history/`; aktualny mechanizm jej nie usuwa.
Przegląd plików i zatwierdzenie są wymagane przed ewentualnym commitem.
