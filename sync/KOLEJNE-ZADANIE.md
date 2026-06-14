# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

**Wizja:** [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md) — trzy filary + relacje.

---

## Stan (2026-06-15)

| Prompt | Status |
|--------|--------|
| **010-labeler-bbox-first-palette** | ✅ DONE (Cursor) — bbox-first + paleta |
| **005–006, 001 recognize** | ✅ BUILD M0 |
| **008a QET atlas** | ⛔ NIE UŻYWAĆ |
| **002-ocr-engine** | **PRIORYTET #1 — filar: tekst** |
| **002-labeler-lines-colors** | OPEN — filar: połączenia (GT) |
| **003-line-tracer** | OPEN — filar: połączenia (runtime) |
| **004-graph-builder** | OPEN — relacje (po filarach) |

---

## Aktywne zadanie — PRIORYTET (Claude ZW)

| Pole | Wartosc |
|------|---------|
| **Prompt** | [`sync/prompts/002-ocr-engine.md`](prompts/002-ocr-engine.md) |
| **Deliverable** | `backend/recognize/ocr_engine.py` — PaddleOCR offline, testy |
| **Filar** | **Tekst** (2/3) |
| **Model** | Sonnet, effort **High** |

### Kroki Claude

1. `sync/filip-to-zw.md` + `002-ocr-engine.md` + `docs/schematic-interpretation.md`
2. Implementacja `PaddleOcrEngine.extract_text` — bez cloud API
3. `pytest backend/tests labeler/tests`
4. `sync/zw-to-filip.md` — instrukcja dla Filipa (zależności, smoke)
5. `sync/commit-message.txt` = `[Claude] recognize: PaddleOCR engine (prompt 002-ocr)`

### Czego NIE robić

- Atlas QET, labeler 010 (DONE), line tracer w tej samej sesji
- Cloud API

---

## Filip (równolegle)

- Oznaczaj bboxy symboli (`python -m labeler.app`) — workflow bbox → typ z palety
- Więcej stron z `data/raw/` i `sync/sources/`
- Re-train YOLO po zebraniu danych (`.venv311`)

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
