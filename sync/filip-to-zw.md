# Skrzynka: Filip → ZW

> Pisze **tylko Filip** (Cursor). ZW czyta na starcie sesji.

---

## 2026-06-14 [Cursor] — prompt 003 priorytet

Temat: **Hierarchia bboxów w labelerze — nowe aktywne zadanie**

Kontekst:
- Filip oznacza schematy warstwowo: duży bbox-blok + mniejsze bboxy w środku (rozłącznik, tag `-11` itd.).
- System dziś zapisuje płaską listę — brak relacji rodzic/dziecko i położenia względem siebie.
- YOLO bez zmian (wszystkie bboxy); hierarchia w JSON/schema.

**Twoje zadanie:** `sync/prompts/003-labeler-bbox-hierarchy.md`  
**Handoff:** `sync/KOLEJNE-ZADANIE.md` (zaktualizowany)

Po ukończeniu:
- `pytest backend/tests labeler/tests`
- wpis w `sync/zw-to-filip.md`
- `sync/commit-message.txt` = `[Claude] labeler: bbox hierarchy + spatial relations (prompt 003)`

002-labeler-lines-colors — **wstrzymane** do czasu merge 003.

---

## 2026-06-14 [Cursor] — koniec sesji

Temat: **Prompt 001 DONE — czeka review. Następny: 002 po akceptacji.**

Stan:
- Canvas bbox wdrożony (`5d16757`), testy 14/14 OK.
- Handoff na jutro: **`sync/NASTEPNA-SESJA.md`** — zacznij od tego pliku.
- `sync/KOLEJNE-ZADANIE.md` zaktualizowany → 002-labeler-lines-colors po review.

Do zrobienia jutro (Filip/Cursor):
1. Test ręczny labelera `:8765` + review `labeler/static/app.js`
2. Akceptacja 001 **lub** `## Poprawka (runda 1)` w `sync/prompts/001-labeler-canvas.md`
3. Oznacz 3–5 stron schematu w labelerze (`data/raw/`)

Dla Claude (po akceptacji 001): prompt **002-labeler-lines-colors.md**.

Commit pending: `[Cursor] sync: handoff sesja 2026-06-14`

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

**Trigger Claude (2026-06-14):** push wszedł — kolejne zadanie. GitHub Action: komentarz `@claude` z instrukcją z `sync/KOLEJNE-ZADANIE.md`.

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
