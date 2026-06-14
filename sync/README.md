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

**Pełna instrukcja + prompt do wklejenia:** [`sync/START-CLAUDE-SESJA.md`](START-CLAUDE-SESJA.md)

1. [claude.ai/code](https://claude.ai/code) → **New session** (nie stary link `session_…`)
2. Wklej prompt startowy z `START-CLAUDE-SESJA.md` (lub napisz: `kolejne zadanie`)
3. Claude czyta `KOLEJNE-ZADANIE.md` → `filip-to-zw.md` → aktywny `sync/prompts/`
4. Po implementacji: wpis w `zw-to-filip.md` + `[Claude] ...` w `commit-message.txt`

## Regula

Jeden agent edytuje plik kodu naraz. Cursor akceptuje funkcje po review.
