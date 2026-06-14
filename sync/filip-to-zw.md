# Skrzynka: Filip → ZW

> Pisze **tylko Filip** (Cursor). ZW czyta na starcie sesji.

---

## 2026-06-14 [Filip/Cursor] — AKCEPTACJA 007 + korekta źródeł + prompt 008a

Temat: **Zaakceptowana analiza atlasu; następne zadanie Claude = 008a (QET)**

Decyzje Filipa:
- **Akceptuję** [`docs/knowledge-sources-analysis.md`](../docs/knowledge-sources-analysis.md) v4 — atlas warstwowy, Siemens-first, ControlByte tylko jako słownik PL.
- **WRT01:** mam **tylko PDF schematu** — **nie mam** projektu EPLAN / Data Portal dla WRT01. Wpis o `C:\Users\Public\EPLAN\Data\` w inbox **nie dotyczy mnie** (to była notatka z przeszukania — ignoruj jako źródło runtime).
- **Drugi PDF:** schemat z elementami **innych producentów** — dopiszę ścieżkę w `sync/sources-inbox.md` (warstwa 3 / prompt 008c, nie teraz).
- **BBox-y:** kontynuuję p013–p015, potem kilka stron pod różnorodność typów.
- **Licencje:** crop-y atlasu lokalnie; surowe QET i IEC poza gitem; w repo YAML + wybrane PNG z atrybucją GPL.

**Twoje zadanie:** [`sync/prompts/008-symbol-atlas-extract.md`](prompts/008-symbol-atlas-extract.md) — **faza 1 tylko QET**  
**Handoff:** [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

Po ukończeniu 008a:
- `pytest backend/tests labeler/tests`
- wpis w `sync/zw-to-filip.md`
- `sync/commit-message.txt` = `[Claude] atlas: QET extract → symbol-reference.yaml (prompt 008a)`

**002-labeler-lines-colors** — możesz iść równolegle jeśli masz capacity; priorytet = 008a.

---

## 2026-06-14 [Cursor] — prompt 007: analiza źródeł wiedzy

Temat: **Ocena poradników, wideo, atlasów symboli — hybrid ze schematem WRT01**

Kontekst:
- Filip znalazł poradnik wideo o schematach; rozważa bazę symboli zamiast samych opisów z PNG.
- SchemaGen nadal potrzebuje schematu (bboxy, linie, tagi instancji); źródła zewnętrzne = warstwa referencyjna.

**Twoje zadanie:** [`sync/prompts/007-sources-analysis.md`](prompts/007-sources-analysis.md)  
**Filip uzupełnia:** [`sync/sources-inbox.md`](sources-inbox.md) (linki, PDF, notatki)  
**Wynik:** `docs/knowledge-sources-analysis.md`  
**Handoff:** [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

To **research** — bez implementacji kodu. Pracuj iteracyjnie z Filipem.

Po rundzie 1:
- commit analizy
- `sync/commit-message.txt` = `[Claude] docs: knowledge sources analysis (prompt 007)`

002-labeler-lines-colors — **wstrzymane** do czasu zakończenia 007 lub decyzji Filipa.

---

## 2026-06-14 [Cursor] — prompt 003 DONE, następny: 002

Temat: **Review 003 OK — akceptacja. Kolejne zadanie: linie + kolory.**

Stan:
- Commit `20392b1` — hierarchia bboxów, relacje przestrzenne, UI drzewa, 24 testy (wg Claude).
- Review Cursor: zgodne z promptem 003, bez poprawek blokujących.

**Twoje zadanie:** `sync/prompts/002-labeler-lines-colors.md`  
**Handoff:** `sync/KOLEJNE-ZADANIE.md` (zaktualizowany)

Po ukończeniu:
- `pytest backend/tests labeler/tests`
- wpis w `sync/zw-to-filip.md`
- `sync/commit-message.txt` = `[Claude] labeler: linie i kolory (prompt 002)`

Nie psuj: auto-zapis, localStorage, hierarchii bboxów (`app.js?v=13`).

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
