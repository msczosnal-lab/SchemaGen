# Skrzynka: Filip → ZW

> Pisze **tylko Filip** (Cursor). ZW czyta na starcie sesji.

---

## 2026-06-14 [Filip/Cursor] — BUILD M0 DONE + priorytet 008a

Temat: **Trening + ONNX + inferencja u Filipa zamknięte. Następne zadanie Claude = 008a (QET atlas).**

### Co zrobione lokalnie (Filip, RTX 2080)

- Odbudowa **`.venv311`** (Py 3.11, torch cu121) — `.venv` (Py 3.14 CPU) **nie używać** do GPU.
- `train_symbols` 30 epok → `data/runs/symbols_v1/weights/best.pt`, mAP50 ≈ **0.085**
- `export_onnx` → `data/models/symbols_v1.onnx`, `registry.json` active=symbols_v1
- Smoke inferencji: **5 detekcji** na p013 przy `conf=0.05` (0 przy domyślnym 0.25 — słaby model, pipeline OK)
- onnxruntime CUDA: brak `cublasLt64_12.dll` → fallback CPU (wystarczy na teraz)

Plan sesji: [`sync/PLAN-TYMCZASOWY.md`](PLAN-TYMCZASOWY.md)

### Twoje zadanie (PRIORYTET #1)

[`sync/prompts/008-symbol-atlas-extract.md`](prompts/008-symbol-atlas-extract.md) — **faza 1 tylko QET**

Handoff: [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

### Reguły po BUILD M0

- **Nie** implementuj ponownie 005/006/001 bez `## Poprawka` od Cursor.
- **Nie** zakładaj, że Filip ma `best.pt` — pytaj / czytaj `filip-to-zw.md`.
- **Nie** cytuj metryk treningu bez `symbols_v1_train_summary.json` od Filipa.
- Pełny trening YOLO = tylko u Filipa.

Commit pending: `[Cursor] sync: BUILD M0 done, handoff 008a + PLAN-TYMCZASOWY`

---

## 2026-06-14 [Filip/Cursor] — BUILD M0: podział GPU

Temat: **005 = kod u Claude (ZW), trening u Filipa (RTX 2080)**

**Claude (PC ZW):** tylko implementacja — `dataset_export`, `train_symbols`, testy pytest. **Nie uruchamiaj** pełnego treningu (brak datasetu w gicie; słabszy PC).

**Filip (RTX 2080):** po Twoim commicie — export + train lokalnie (komendy w `zw-to-filip.md`).

Gotowy prompt startowy: [`sync/PROMPT-CLAUDE-005.md`](PROMPT-CLAUDE-005.md)

---

## 2026-06-14 [Filip] — BUILD M0: pierwszy trening YOLO

Temat: **Dataset gotowy w SQLite — priorytet = prompt 005, nie dalsze bboxy**

Stan datasetu (`data/schemagen.db`):

| Strona | Bboxów |
|--------|-------:|
| p013 | 75 |
| p014 | 99 |
| p015 | 152 |
| p016–p018 | 2–3 |
| p021 | 2 |
| p022 | 10 |
| p023 | 48 |
| **Razem** | **~394, 9 stron** |

W `data/labeled/` jest tylko stary eksport p013 — **batch eksport = część 005**.

**Twoje zadanie (PRIORYTET #1):** [`sync/prompts/005-train-symbols.md`](prompts/005-train-symbols.md)  
- `train/dataset_export.py` — SQLite → YOLO train/val + PNG z `data/raw/`  
- `train/train_symbols.py` — ultralytics YOLOv8n (batch≤8)  
- fix: `labeler/export.py` kopiuje PNG przy eksporcie  
- **pytest tylko** — trening GPU = instrukcja dla Filipa, nie wykonuj na ZW  

**Handoff:** [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

Po kodzie:
- wpis w `sync/zw-to-filip.md` (pliki + komendy PowerShell dla Filipa)
- `sync/commit-message.txt` = `[Claude] train: dataset export + YOLO train code M0 (prompt 005)`

**008a QET** — po 005. **Filip: nie oznaczaj więcej stron** do wyniku buildu.

---

## 2026-06-14 [Filip/Cursor] — AKCEPTACJA 007 + korekta źródeł + prompt 008a

Temat: **Zaakceptowana analiza atlasu; następne zadanie Claude = 008a (QET)**

Decyzje Filipa:
- **Akceptuję** [`docs/knowledge-sources-analysis.md`](../docs/knowledge-sources-analysis.md) v4 — atlas warstwowy, Siemens-first, ControlByte tylko jako słownik PL.
- **WRT01:** mam **tylko PDF schematu** — **nie mam** projektu EPLAN / Data Portal dla WRT01. Wpis o `C:\Users\Public\EPLAN\Data\` w inbox **nie dotyczy mnie** (to była notatka z przeszukania — ignoruj jako źródło runtime).
- **Drugi PDF:** schematy w **`sync/sources/`** — 4 PDF, 523 strony (Norblin, Adamed×2, PL5); manifest: `sync/sources/MANIFEST.json`
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
