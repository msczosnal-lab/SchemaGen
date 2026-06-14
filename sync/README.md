# sync/ — Cursor ↔ Claude Cowork

Dwa agenci + uzytkownik (wiatr: kierunek + oznaczanie danych).

## Tagi GitSync (MachineTag)

| Tag | Maszyna | Agent |
|-----|---------|-------|
| **Cursor** | PC Filip | Cursor IDE |
| **Claude** | PC ZW | Claude Cowork |

Uruchomienie: `Start-GitSync.cmd Cursor` lub `Start-GitSync.cmd Claude`

## Pliki

| Plik | Autor | Czyta |
|------|-------|-------|
| `filip-to-zw.md` | Cursor | Claude |
| `zw-to-filip.md` | Claude | Cursor |
| `prompts/*.md` | Cursor | Claude |
| `commit-message.txt` | Cursor **lub** Claude | GitSync daemon |
| `commit-log.md` | GitSync (append) | obaj |
| `TASKS.md` | obaj (append) | obaj |

## Nazwane commity — `commit-message.txt`

Po ukonczeniu etapu wpisz **jedna linia**:

```
[Cursor] pivot Faza 0: szkielet backend
```

```
[Claude] labeler: canvas bbox (prompt 001)
```

- Pusty plik (tylko komentarze `#`) → fallback `auto[Cursor]` / `auto[Claude]`
- Po commicie daemon **czysci** plik i dopisuje wiersz do `commit-log.md`
- Jesli plik niepusty i to nie Twoj autor → **nie nadpisuj**; napisz w skrzynce

## Start sesji Claude

1. `sync/zw-to-filip.md` + `TASKS.md` + `commit-log.md` (ostatnie etapy)
2. Aktywny prompt: `sync/prompts/001-labeler-canvas.md`
3. Po implementacji: wpis w `zw-to-filip.md` + opcjonalnie `[Claude] ...` w `commit-message.txt`

## Regula

Jeden agent edytuje plik kodu naraz. Cursor akceptuje funkcje po review.
