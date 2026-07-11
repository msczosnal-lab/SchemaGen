# OneDrive / synchronizacja chmurowa — wyklucz `data/`

Żywa baza SQLite (`data/schemagen.db` + WAL) **nie może** być synchronizowana przez OneDrive,
Dropbox ani inny sync w czasie rzeczywistym. Współbieżny zapis + sync zewnętrzny = korupcja
pliku (dzisiejsze awarie).

## Co zrobić (PC Filip)

1. **Preferowane:** przenieś repo **poza** folder OneDrive (np. `C:\Users\Filip\Desktop\Cursor\SchemaGen` jest OK jeśli Desktop nie jest syncowany).
2. **Jeśli repo musi leżeć w OneDrive:** wyklucz z synchronizacji cały podfolder `data\`:
   - OneDrive → Ustawienia → Konto → „Wybierz foldery" **albo**
   - Klik prawy na `SchemaGen\data` → „Zawsze zachowuj na tym urządzeniu" wyłączone + „Zwolnij miejsce" (pliki tylko lokalne) **albo**
   - OneDrive → Pomoc i ustawienia → Ustawienia → Kopia zapasowa → Zarządzaj kopiami zapasowymi → wyłącz sync folderu zawierającego `data\`.

## Co jest bezpieczne w gicie

- GT w `gt/*.json` (zadanie 030) — wersjonowane gitem, odbudowa cache z plików.
- Lokalne kopie: `data\backups\schemagen-YYYYMMDD.db` (harmonogram + start labelera) — gitignore.

## Weryfikacja

Po wykluczeniu: uruchom labeler, zapisz GT, sprawdź że OneDrive nie pokazuje „sync w toku" na `schemagen.db`.
