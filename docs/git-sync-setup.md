# Uruchomienie ciągłej synchronizacji + koordynacji agentów

System z dwóch warstw:
- **Transport** — `GitSyncDaemon.ps1` na obu komputerach (Windows, natywnie). Fetch→rebase→commit→push co 10 s.
- **Koordynacja** — katalog `sync/` (skrzynki jednokierunkowe + `TASKS.md`). Patrz `sync/README.md`.

---

## 0. Najpierw posprzątaj zablokowane locki (jednorazowo, na komputerze ZW)

Sesja Cowork zostawiła puste pliki blokujące — usuń je w PowerShell:

```powershell
$r = "C:\Users\ZW\Desktop\prywatne\automatyzacja\KodKlon\SchemaGen\.git"
Remove-Item "$r\HEAD.lock","$r\index.lock.bak","$r\refs\heads\main.lock" -ErrorAction SilentlyContinue
```

## 1. Uwierzytelnienie (raz na każdym komputerze)

Wybrana metoda: **PAT fine-grained, HTTPS, tylko repo SchemaGen** — odwoływalny, bez wpływu na inne repo.

1. GitHub → Settings → Developer settings → **Fine-grained tokens** → Generate.
2. Repository access: **Only select repositories → msczosnal-lab/SchemaGen**.
3. Permissions → Repository → **Contents: Read and write**. Reszta domyślnie.
4. Skopiuj token (widoczny raz).
5. Zapisz go w Windows Credential Manager przez jedno wypchnięcie:

```powershell
git config --global credential.helper manager
# pierwszy push poprosi o login — podaj nazwę użytkownika GitHub i jako hasło wklej TOKEN
```

Token trafia do Menedżera poświadczeń Windows, daemon używa go bez pytania. **Nie wpisuj tokena do żadnego pliku w repo.**

## 2. Uruchomienie daemona — ZAWSZE w widocznym oknie

Daemon NIE działa w ukryciu. Widzisz okno konsoli z logiem na żywo: szare „. czuwam" co cykl,
kolorowe linie przy zdarzeniach (zielone PUSH/COMMIT, cyjan NOWE/PULL, czerwone KONFLIKT/BLAD).

### Sposób A — podwójne kliknięcie (najprostszy)

Uruchom `Start-GitSync.cmd`, wpisz tag (`ZW` lub `Filip`). Otworzy się okno i zostaje otwarte.
Zatrzymanie = zamknięcie okna albo Ctrl+C. Trzeba uruchamiać ręcznie po zalogowaniu.

### Sposób B — auto-start przy logowaniu (też widoczne okno)

Komputer **ZW**:
```powershell
cd C:\Users\ZW\Desktop\prywatne\automatyzacja\KodKlon\SchemaGen
.\Install-GitSyncTask.ps1 -MachineTag ZW
Start-ScheduledTask -TaskName "SchemaGen GitSync"
```

Komputer **Filip**:
```powershell
cd C:\Users\Filip\Desktop\Cursor\SchemaGen
.\Install-GitSyncTask.ps1 -MachineTag Filip -RepoPath "C:\Users\Filip\Desktop\Cursor\SchemaGen"
Start-ScheduledTask -TaskName "SchemaGen GitSync"
```

Zadanie otwiera widoczne okno (`cmd start ... powershell -NoExit`) przy każdym logowaniu.
Wyłączenie: `Unregister-ScheduledTask -TaskName "SchemaGen GitSync" -Confirm:$false`.

## 3. Test (2 minuty)

1. Na ZW dopisz linię do `sync/zw-to-filip.md`.
2. W ≤20 s na Filip plik ma tę linię (toast „nowe zmiany”).
3. Odwrotnie z `sync/filip-to-zw.md`.

Podgląd na żywo: `Get-Content sync\.daemon-ZW.log -Wait`.

## 4. Jak współpracują dwa modele

- Start sesji: każdy agent czyta skrzynkę od drugiego + `TASKS.md`.
- Przekazanie zadania = wpis w `TASKS.md` + nota w swojej skrzynce.
- Daemon przenosi to na drugą maszynę w ~10 s; tamten agent zobaczy przy następnym starcie sesji.

---

## Ograniczenia i ryzyka

- **[RYZYKO] Równoległa edycja tego samego pliku kodu** przez oba komputery → konflikt rebase. Daemon wtedy **przerywa rebase, alarmuje i nie pushuje** (praca lokalna bezpieczna), ale scalić trzeba ręcznie. Dlatego kod edytuje jedna strona naraz (zasada w `sync/README.md`).
- **[RYZYKO] Auto-commit `add -A`** wciąga też pliki tymczasowe. Zadbaj, by `.gitignore` pokrywał `output/`, buildy, `sync/.daemon-*.log`, `sync/.status-*.json`.
- **Cowork nie jest silnikiem syncu** — moja sesja w sandboxie jest chwilowa. Ciągłość daje wyłącznie daemon na Windows. Ja jestem jednym z dwóch *autorów*, nie pompą.
- **Granularność 10 s** wystarcza dla notatek/zadań; nie traktuj tego jak współdzielonej edycji w czasie rzeczywistym (to nie Google Docs).
