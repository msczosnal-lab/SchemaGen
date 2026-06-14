# Zadanie 004: GraphBuilder.build

**Status:** BLOCKED — po promptach 001-symbol-detector, 002-ocr, 003-line-tracer  
**Model:** Opus, effort High  
**Plik:** `backend/recognize/graph_builder.py`

## Kontekst

Skladanie `SchemaModel` z:
- `OnnxSymbolDetector` → `components`
- `PaddleOcrEngine` → tagi / `annotations`
- `LineTracer` + `LineClassifier` → `graphic_lines`

## Regula krytyczna

**Connection tworzysz TYLKO z linii gdzie** `LineClassifier.is_connection_candidate(line)` **== True** (role `wire` lub `bus`).

Linie `device_stroke`, `frame`, `crossing`, `dash` → tylko w `graphic_lines`, **nigdy** w `connections`.

## Implementuj `build(image_path, source)`

1. Detekcja symboli → components (bbox, type, confidence)
2. OCR → uzupelnij tagi
3. Trace + classify → graphic_lines
4. Dla linii wire/bus: znajdz przeciecia z bbox symboli → connections (from/to terminal heurystyka)
5. Ustaw `meta.source`, `meta.model_version`

## Testy

- Mock detector/tracer → SchemaModel ma components + graphic_lines + connections
- Linia device_stroke nie generuje Connection

## Po ukonczeniu

`sync/commit-message.txt` = `[Claude] recognize: graph builder (prompt 004)`

## Poprawka (runda N)

*(Cursor)*
