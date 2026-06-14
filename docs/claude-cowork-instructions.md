# Claude Cowork — instrukcje implementacji

## Start sesji

Filip pisze **„kolejne zadanie”** → wczytaj w tej kolejności:

1. **`sync/KOLEJNE-ZADANIE.md`** — aktywny prompt i kroki
2. **`sync/filip-to-zw.md`** — najnowszy wpis od Cursor
3. **`docs/claude-cowork-instructions.md`** — ten plik
4. Aktywny plik z **`sync/prompts/NNN-*.md`**

## Projekt

SchemaGen offline — Python, FastAPI, YOLO ONNX, RTX 2080. **Bez cloud API w runtime.**

## Twoja rola (Builder)

Implementujesz funkcje oznaczone `NotImplementedError` i `COWORK_TASK` w plikach.

**Nie zmieniaj bez zgody Cursor:**
- sygnatur w `backend/protocols/`
- modeli Pydantic w `backend/models/` (GraphicLine, SchemaModel — juz gotowe)
- kontraktu SchemaModel JSON

## Workflow

1. `sync/KOLEJNE-ZADANIE.md` + `sync/filip-to-zw.md`
2. Implementuj aktywny prompt
3. `pytest backend/tests labeler/tests`
4. Wpis w `sync/zw-to-filip.md`
5. Cursor review → sekcja `## Poprawka (runda N)` w promptcie

## Mapa repo

```
backend/          — CLI, API, validate (dziala), recognize (stub)
backend/colors/   — palette.py (gotowe — uzywaj w classify/render)
config/           — semantic-colors.yaml, symbol-classes.yaml
labeler/          — FastAPI :8765, export YOLO (dziala), canvas (TODO)
train/            — YOLO + ONNX (stub)
blocks/           — biblioteka blokow JSON
schema/fixtures/  — ground truth (page1_expected.json ma graphic_lines)
sync/prompts/     — twoje zadania
sync/KOLEJNE-ZADANIE.md — co robic teraz
```

## Zasady domenowe (wazne)

1. **Linia graficzna ≠ polaczenie logiczne**
   - `GraphicLine` — co widać na rysunku (wire, bus, device_stroke, frame, dash, crossing…)
   - `Connection` — graf elektryczny; tylko z linii `wire` / `bus` + topologia
2. **Kolory semantyczne** — `config/semantic-colors.yaml`; rozpoznawanie i walidacja po kolorze grupy obiektu
3. Linie `device_stroke`, `crossing`, `frame` **nigdy** nie stają się Connection

## Zasady kodu

- Python 3.11+, type hints
- pytest dla kazdej nowej funkcji
- ruff + mypy (pre-commit)
- **Zakaz** openai/anthropic w backend/recognize, train/, labeler/

## Kolejnosc promptow

1. `001-labeler-canvas.md` — canvas bbox ← **TERAZ**
2. `002-labeler-lines-colors.md` — polyline + kolory w labelerze
3. `001-symbol-detector.md` — ONNX inferencja
4. `002-ocr-engine.md` — PaddleOCR
5. `003-line-tracer-classifier.md` — OpenCV linie + klasyfikacja (NIE stary wire-tracer)
6. `004-graph-builder.md` — pipeline → SchemaModel
7. `005-train-symbols.md` — ultralytics
8. `006-export-onnx.md` — export ONNX

## Test akceptacji

```powershell
pytest backend/tests labeler/tests
python -m backend.cli validate schema/fixtures/page1_expected.json
```

## Commit etapu (GitSync)

Po zakonczonym prompcie + pytest OK:

1. Wpis w `sync/zw-to-filip.md` (status)
2. `sync/commit-message.txt` = jedna linia, np. `[Claude] labeler: canvas bbox (prompt 001)`
3. GitSync na PC ZW: `Start-GitSync.cmd Claude`

**Przed zapisem** sprawdz `commit-message.txt` — jesli niepusty i autor to Cursor, **nie nadpisuj**.

## Model i effort (rekomendacja)

| Zadanie | Model | Effort |
|---------|-------|--------|
| canvas JS, labeler linie | Sonnet | High |
| ONNX, line tracer, graph builder | Opus | High / Ultra |
| Poprawka po review Cursor | Sonnet | Medium |
