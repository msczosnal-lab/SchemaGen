# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

---

## Stan (2026-06-15)

| Prompt | Status |
|--------|--------|
| **005–006, 001 recognize** | ✅ BUILD M0 (trening + ONNX u Filipa) |
| **008a QET atlas** | ✅ kod w repo; kurator TAK/NIE **wstrzymany** (faza 2) |
| **010-labeler-bbox-first-palette** | **PRIORYTET #1 — następny kod u Claude** |
| **002-labeler-lines-colors** | OPEN — po 010 |
| **003-line-tracer / 004-graph-builder** | OPEN — po dużej bazie bbox |
| **009-bbox-symbol-id** | wchłonięty przez **010** (picker w labelerze) |

---

## Aktywne zadanie — PRIORYTET

| Pole | Wartosc |
|------|---------|
| **Prompt** | [`sync/prompts/010-labeler-bbox-first-palette.md`](prompts/010-labeler-bbox-first-palette.md) |
| **Deliverable (Claude ZW)** | `config/symbol-palette.yaml`, `backend/atlas/palette.py`, labeler bbox-first + picker, testy, docs |
| **Deliverable (Filip)** | Oznaczanie bboxów na wielu schematach; re-train YOLO po zebraniu danych |
| **Typ** | Implementacja + pytest (bez cloud API) |
| **Model** | Sonnet, effort **High** |
| **Start** | [`sync/PROMPT-CLAUDE-010.md`](PROMPT-CLAUDE-010.md) |

### Etap 1 — założenia (Filip)

- Skrypt ma **widzieć elementy** na schemacie (YOLO `element`).
- **Najpierw bbox, potem hasło** z palety (nie odwrotnie).
- Hasła = **typ urządzenia** (krótko); wyjątki ręcznie.
- Tagi `-K1`, połączenia, terminale złożonych urządzeń — **później**.

### Kroki Claude (ZW)

1. `sync/filip-to-zw.md` + `010-labeler-bbox-first-palette.md`
2. Implementacja palety + odwrócony workflow labelera
3. `pytest backend/tests labeler/tests`
4. `sync/zw-to-filip.md` — instrukcja pickera dla Filipa
5. `sync/commit-message.txt` = `[Claude] labeler: bbox-first + symbol palette (prompt 010)`

### Czego NIE robic

- Kurator atlasu QET, cropy w pickerze
- Multi-class YOLO, line tracer, GraphBuilder
- Pełny trening YOLO na PC ZW
- Cloud API
- **008/006/001 ponownie** bez `## Poprawka` od Cursor

---

## BUILD M0 — zamknięty u Filipa

Trening GPU, export ONNX, smoke inferencji. **Venv:** `.venv311` (Py 3.11 + torch cu121).

Filip buduje **dużą bazę bboxów** z `data/raw/` + PDF z `sync/sources/` — to główny sygnał dla detekcji.

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
