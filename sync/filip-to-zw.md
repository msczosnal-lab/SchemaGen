# Skrzynka: Filip → ZW

> Pisze **tylko Filip** (Cursor). ZW czyta na starcie sesji.

---

## 2026-06-14 [Cursor]

Temat: **Kolejne zadanie = prompt 001-labeler-canvas**

Kontekst:
- Cursor dodal warstwe **linii graficznych + kolory semantyczne** (model, paleta, fixture v2).
- **Twoje pierwsze zadanie:** wczytaj `sync/KOLEJNE-ZADANIE.md` i zaimplementuj `sync/prompts/001-labeler-canvas.md`.
- Po ukonczeniu: pytest → `zw-to-filip.md` → `commit-message.txt` = `[Claude] labeler: canvas bbox (prompt 001)`.

Nowe pliki (nie edytuj bez potrzeby):
- `config/semantic-colors.yaml` — paleta kolorow (Filip uzupelni grupy)
- `backend/colors/palette.py` — match_color, resolve_stroke
- `backend/models/schema.py` — `GraphicLine`, `graphic_lines[]`
- `schema/fixtures/page1_expected.json` — przyklad z liniami

Zasada: **linia na schemacie ≠ polaczenie**. Prompt 002 (linie w labelerze) — po 001.

Commit pending: `[Cursor] model: graphic lines + semantic colors palette`

---

## 2026-06-14 [Cursor]

Temat: GitSync — nazwane commity + tagi Cursor/Claude
Kontekst: `sync/commit-message.txt` — wpisuj `[Claude] opis` po ukonczeniu promptu. Daemon: `Start-GitSync.cmd Claude`. Historia: `sync/commit-log.md`. Tagi: **Cursor** (Filip), **Claude** (ZW).
Do zrobienia po stronie Claude: **001-labeler-canvas.md**
Commit: `[Cursor] gitsync: named commits + tags Cursor/Claude`

---

## 2026-06-14 [Cursor]

Temat: Pivot offline — Faza 0 gotowa
Commit: (po GitSync)

---

## 2026-06-13 [Filip]

Temat: ~~MA1+MA1 EPLAN~~ — anulowane (pivot offline 2026-06-14)
