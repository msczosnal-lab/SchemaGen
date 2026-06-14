# Claude Cowork — instrukcje implementacji

## Projekt

SchemaGen offline — Python, FastAPI, YOLO ONNX, RTX 2080. **Bez cloud API w runtime.**

## Twoja rola (Builder)

Implementujesz funkcje oznaczone `NotImplementedError` i `COWORK_TASK` w plikach.

**Nie zmieniaj:**
- sygnatur w `backend/protocols/`
- modeli Pydantic w `backend/models/`
- kontraktu SchemaModel JSON

## Workflow

1. Przeczytaj `sync/zw-to-filip.md` i `sync/TASKS.md`
2. Wez aktywny prompt z `sync/prompts/NNN-*.md`
3. Implementuj + testy pytest
4. Dopisz status do `sync/zw-to-filip.md`
5. Cursor review → sekcja `## Poprawka (runda N)` w promptcie

## Mapa repo

```
backend/          — CLI, API, validate (dziala), recognize (stub)
labeler/          — FastAPI :8765, export YOLO (dziala), canvas (TODO)
train/            — YOLO + ONNX (stub)
blocks/           — biblioteka blokow JSON
schema/fixtures/  — ground truth testowy
sync/prompts/     — twoje zadania
```

## Zasady kodu

- Python 3.11+, type hints
- pytest dla kazdej nowej funkcji
- ruff + mypy (pre-commit)
- **Zakaz** openai/anthropic w backend/recognize, train/, labeler/

## Kolejnosc promptow

1. `001-labeler-canvas.md` — canvas bbox w labeler/static/app.js
2. `001-symbol-detector.md` — ONNX inferencja
3. `002-ocr-engine.md` — PaddleOCR
4. `003-wire-tracer.md` — OpenCV linie
5. `004-graph-builder.md` — polaczenie pipeline
6. `005-train-symbols.md` — ultralytics
7. `006-export-onnx.md` — export ONNX

## Test akceptacji

```powershell
pytest backend/tests labeler/tests
python -m backend.cli validate schema/fixtures/page1_expected.json
```
