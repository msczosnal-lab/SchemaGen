# NASTĘPNA SESJA — start tutaj (2026-06-15)

> Plik handoff po sesji 2026-06-14. Cursor / Filip: wczytaj ten plik na początku jutrzejszej pracy.

---

## Stan repo

| Pole | Wartość |
|------|---------|
| **Branch** | `main` @ `7984129` |
| **GitSync** | Działa na PC Filip (`Start-GitSync.cmd Cursor`) |
| **Testy** | `14 passed` (`pytest labeler/tests backend/tests`) |
| **Labeler** | Canvas bbox zaimplementowany — **wymaga review Cursor** |

---

## Co zrobiliśmy dziś (2026-06-14)

### Cursor
- Model `GraphicLine` + `config/semantic-colors.yaml` + `backend/colors/palette.py`
- GitSync: nazwane commity (`[Cursor]` / `[Claude]`), tagi maszyn
- Weryfikacja integracji Claude (GitHub Action + GitSync)
- Commity: `524df2c`, `884ae28`

### Claude (PC ZW)
- **Prompt 001 DONE** — interaktywny canvas bbox w `labeler/static/app.js`
- Commit: `5d16757` — `[Claude] labeler: canvas bbox (prompt 001)`
- Wpis w `sync/zw-to-filip.md` z instrukcją testów ręcznych

### Infrastruktura
- `.github/workflows/claude.yml` — trigger `@claude` na issue/PR (commit `477043b`)
- Push **nie** uruchamia Claude automatycznie — wymaga komentarza `@claude` lub ręcznej wiadomości w sesji

---

## Pierwsze kroki jutro

### 1. Filip / Cursor — review promptu 001

```powershell
cd C:\Users\Filip\Desktop\Cursor\SchemaGen
Start-GitSync.cmd Cursor          # jeśli nie działa
python -m labeler.app             # localhost:8765
```

**Test ręczny:**
1. Załaduj stronę, wybierz klasę (1–9)
2. Narysuj 3 bbox, zapisz, odśwież — bbox wracają
3. Del usuwa zaznaczony, scroll = zoom

**Review kodu:** `labeler/static/app.js` vs `sync/prompts/001-labeler-canvas.md`

- OK → akceptacja, przejście do promptu 002
- Poprawki → dopisz `## Poprawka (runda 1)` w `sync/prompts/001-labeler-canvas.md` + wpis w `sync/filip-to-zw.md`

### 2. Filip — oznaczanie danych (równolegle)

- Oznacz **3–5 stron** schematu w labelerze (`data/raw/`)
- Po zebraniu danych → Claude może iść w `001-symbol-detector` + train

### 3. Claude — następne zadanie (po akceptacji 001)

| Prompt | Plik | Warunek |
|--------|------|---------|
| **002-labeler-lines-colors** | labeler + API | po review 001 |
| 001-symbol-detector | `backend/recognize/symbol_detector.py` | po danych od Filipa |

Start sesji Claude: „kolejne zadanie” → `sync/KOLEJNE-ZADANIE.md`

---

## Architektura — pamiętać

1. **Linia ≠ połączenie** — `GraphicLine` (grafika) vs `Connection` (graf logiczny)
2. **Kolory semantyczne** — `config/semantic-colors.yaml`, `backend/colors/palette.py`
3. Tylko linie `wire` / `bus` → kandydaci na `Connection` w GraphBuilder
4. **Zakaz** cloud API w `backend/recognize/`, `train/`, `labeler/`

Fixture: `schema/fixtures/page1_expected.json` (ma `graphic_lines`).

---

## Otwarte zadania (TASKS)

| # | Status | Kto | Zadanie |
|---|--------|-----|---------|
| 10, 15 | **DONE** | Claude | 001-labeler-canvas |
| 11, 17 | OPEN | Filip | Oznacz 3–5 stron w labelerze |
| 16 | OPEN | Claude | 002-labeler-lines-colors (po review 001) |
| 12, 18 | OPEN | Claude | symbol-detector + train (po danych) |
| — | **NOWE** | Cursor | Review + akceptacja prompt 001 |

---

## Historia commitów (dziś)

| Hash | Autor | Wiadomość |
|------|-------|-----------|
| 477043b | ZW | GitHub Action `@claude` |
| 524df2c | Cursor | model: graphic lines + semantic colors |
| 884ae28 | Cursor | auto sync |
| 5d16757 | Claude | labeler: canvas bbox (prompt 001) |
| 7984129 | Claude | auto sync |

Pełna historia: `sync/commit-log.md`

---

## Pliki sync — mapa

| Plik | Rola |
|------|------|
| **`sync/NASTEPNA-SESJA.md`** | ← **TEN PLIK** — start jutro |
| `sync/KOLEJNE-ZADANIE.md` | Aktywny prompt dla Claude |
| `sync/filip-to-zw.md` | Instrukcje Cursor → Claude |
| `sync/zw-to-filip.md` | Raport Claude → Cursor |
| `sync/TASKS.md` | Kolejka wspólna |
| `docs/claude-cowork-instructions.md` | Reguły dla Claude |

---

## Commit na koniec sesji Cursor (opcjonalnie)

Gdy review/handoff gotowy:

```
sync/commit-message.txt = [Cursor] sync: handoff sesja 2026-06-14, prompt 001 review
```

GitSync zacommituje w ≤10 s.
