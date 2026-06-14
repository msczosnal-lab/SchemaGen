# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

---

## Aktywne zadanie (2026-06-14)

| Pole | Wartosc |
|------|---------|
| **Prompt** | [`sync/prompts/001-labeler-canvas.md`](prompts/001-labeler-canvas.md) |
| **Plik** | `labeler/static/app.js` |
| **Cel** | Interaktywny canvas bbox symboli w labelerze (:8765) |
| **Model** | Sonnet, effort **High** |

### Kroki

1. Przeczytaj `docs/claude-cowork-instructions.md`
2. Przeczytaj `sync/filip-to-zw.md` (najnowszy wpis)
3. Zaimplementuj **001-labeler-canvas.md**
4. `pytest labeler/tests backend/tests`
5. Wpis w `sync/zw-to-filip.md` (co zrobiles, jak testowac)
6. `sync/commit-message.txt` = `[Claude] labeler: canvas bbox (prompt 001)`
7. GitSync: `Start-GitSync.cmd Claude`

### Czego NIE robic teraz

- **002-labeler-lines-colors** — dopiero po 001
- **003-line-tracer-classifier** — dopiero po 001 (lub rownolegle, ale priorytet labeler)
- Nie zmieniaj modeli w `backend/models/` (Cursor je utrzymuje)

---

## Nowosc architektury (2026-06-14) — zapamietaj

1. **Linia ≠ polaczenie** — `GraphicLine` (grafika) vs `Connection` (graf logiczny)
2. **Kolory semantyczne** — `config/semantic-colors.yaml`, modul `backend/colors/palette.py`
3. Tylko linie `wire` / `bus` moga stac sie `Connection` w GraphBuilder

Fixture z przykladem: `schema/fixtures/page1_expected.json` (ma `graphic_lines`).

---

## Kolejnosc promptow (pelna)

| # | Prompt | Plik glowny | Blokada |
|---|--------|-------------|---------|
| 1 | 001-labeler-canvas | `labeler/static/app.js` | **TERAZ** |
| 2 | 002-labeler-lines-colors | labeler + API | po 001 |
| 3 | 001-symbol-detector | `backend/recognize/symbol_detector.py` | po danych od Filipa |
| 4 | 002-ocr-engine | `backend/recognize/ocr_engine.py` | — |
| 5 | 003-line-tracer-classifier | line_tracer + line_classifier | po 002 labeler lub rownolegle |
| 6 | 004-graph-builder | graph_builder.py | po 3–5 |
| 7 | 005-train-symbols | `train/` | po danych |
| 8 | 006-export-onnx | `train/export_onnx.py` | po 005 |

---

## Test akceptacji (zawsze)

```powershell
pytest backend/tests labeler/tests
python -m backend.cli validate schema/fixtures/page1_expected.json
```

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]`. Nie nadpisuj jesli jest `[Cursor]` i niepusty.
