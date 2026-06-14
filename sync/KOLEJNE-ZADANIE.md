# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

**Wizja:** [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md) — trzy filary (tekst, symbole, połączenia) + relacje.

---

## Stan (2026-06-15)

| Prompt | Status |
|--------|--------|
| **005–006, 001 recognize** | ✅ BUILD M0 (detektor symboli) |
| **008a QET atlas** | ⛔ **NIE UŻYWAĆ** — rezygnacja na tym etapie (kod w repo = martwy) |
| **010-labeler-bbox-first-palette** | **PRIORYTET #1 — filar: symbole graficzne** |
| **002-ocr-engine** | OPEN — filar: tekst |
| **002-labeler-lines-colors** | OPEN — filar: połączenia (GT) |
| **003-line-tracer** | OPEN — filar: połączenia (runtime) |
| **004-graph-builder** | OPEN — **relacje** (tekst↔symbol, połączenia) |

---

## Trzy filary interpretacji wizualnej

| Filar | Co rozpoznajemy | GT (Filip) | Runtime (Claude) |
|-------|-----------------|------------|------------------|
| **Symbole graficzne** | urządzenia, symbole IEC | bbox + hasło (labeler 010) | YOLO ONNX |
| **Tekst** | tagi `-K1`, opisy | bbox tekstu / korekta OCR | PaddleOCR |
| **Połączenia** | przewody, szyny | linie wire/bus (labeler) | LineTracer + Classifier |

**Potem:** relacje — jaki tekst do jakiego symbolu, gdzie symbol łączy się z innym (`004-graph-builder`).

---

## Aktywne zadanie — PRIORYTET

| Pole | Wartosc |
|------|---------|
| **Prompt** | [`sync/prompts/010-labeler-bbox-first-palette.md`](prompts/010-labeler-bbox-first-palette.md) |
| **Deliverable (Claude ZW)** | `config/symbol-palette.yaml`, loader palety, labeler bbox-first + picker, testy, docs |
| **Deliverable (Filip)** | Duża baza bboxów symboli z wielu schematów |
| **Start** | [`sync/PROMPT-CLAUDE-010.md`](PROMPT-CLAUDE-010.md) |

### Kroki Claude (ZW)

1. `sync/filip-to-zw.md` + `010-labeler-bbox-first-palette.md` + `docs/schematic-interpretation.md`
2. Implementacja (paleta **bez** atlasu QET — moduł `backend/symbol_palette.py`, nie `backend/atlas/`)
3. `pytest backend/tests labeler/tests`
4. `sync/zw-to-filip.md`
5. `sync/commit-message.txt` = `[Claude] labeler: bbox-first + symbol palette (prompt 010)`

### Czego NIE robic

- Atlas QET, kurator, `build_reference`, cropy atlasu, `symbol-reference.yaml` w UI
- GraphBuilder / OCR / line tracer w tej samej sesji (chyba że Filip każe)
- Cloud API

---

## BUILD M0

Trening GPU u Filipa (`.venv311`). Bboxy ze skanów = jedyny sygnał treningowy detekcji.

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
