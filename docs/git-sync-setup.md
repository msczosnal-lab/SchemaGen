# Uruchomienie ciągłej synchronizacji + koordynacji agentów

System z dwóch warstw:
- **Transport** — `GitSyncDaemon.ps1` na obu komputerach (Windows, natywnie). Fetch→rebase→commit→push co 10 s.
- **Koordynacja** — katalog `sync/` (skrzynki, `TASKS.md`, `commit-message.txt`). Patrz `sync/README.md`.

---

## Tagi maszyn

| Tag | Komputer | Uruchomienie |
|-----|----------|--------------|
| **Claude** | PC ZW (Cowork) | `Start-GitSync.cmd Claude` |
| **Cursor** | PC Filip | `Start-GitSync.cmd Cursor` |

Logi: `sync\.daemon-Claude.log`, `sync\.daemon-Cursor.log`

---

## Nazwane commity

Przed commitem (lub gdy etap gotowy) wpisz w [`sync/commit-message.txt`](../sync/commit-message.txt):

```
[Cursor] opis kamienia milowego
```

```
[Claude] opis zakonczonego promptu
```

Daemon odczytuje wiadomosc przy auto-commit. Historia: [`sync/commit-log.md`](../sync/commit-log.md).

Bez wiadomosci: `auto[Cursor] 2026-06-14 ...` lub `auto[Claude] ...`

---

## 1. Uwierzytelnienie (raz na każdym komputerze)

PAT fine-grained, HTTPS, repo SchemaGen — patrz poprzednia dokumentacja.

```powershell
git config --global credential.helper manager
```

## 2. Uruchomienie daemona

### Sposób A — podwójne kliknięcie

`Start-GitSync.cmd` → tag **Claude** lub **Cursor**

### Sposób B — harmonogram

Komputer **Claude (ZW)**:
```powershell
cd C:\Users\ZW\Desktop\prywatne\automatyzacja\KodKlon\SchemaGen
.\Install-GitSyncTask.ps1 -MachineTag Claude
Start-ScheduledTask -TaskName "SchemaGen GitSync"
```

Komputer **Cursor (Filip)**:
```powershell
cd C:\Users\Filip\Desktop\Cursor\SchemaGen
.\Install-GitSyncTask.ps1 -MachineTag Cursor -RepoPath "C:\Users\Filip\Desktop\Cursor\SchemaGen"
Start-ScheduledTask -TaskName "SchemaGen GitSync"
```

## 3. Test sync + named commit

1. Cursor wpisuje `[Cursor] test: named commit flow` w `commit-message.txt`
2. Lokalna zmiana w repo
3. W ≤10 s daemon commituje z ta nazwa, czysci plik, dopisuje `commit-log.md`
4. Na drugim PC: toast „nowe zmiany”, `commit-log.md` widoczny po pull

Podgląd: `Get-Content sync\.daemon-Cursor.log -Wait`

## 4. Współpraca agentów

- Start sesji: skrzynka + `TASKS.md` + `commit-log.md`
- Koniec etapu: `commit-message.txt` + wpis w skrzynce
- Daemon sync co ~10 s

---

## Ograniczenia

- Równoległa edycja tego samego pliku → konflikt rebase
- Auto-commit `add -A` — `.gitignore` musi pokrywac `data/`, `.venv/`, logi daemona
- `commit-message.txt` i `commit-log.md` **nie** ignoruj w git — musza syncowac
