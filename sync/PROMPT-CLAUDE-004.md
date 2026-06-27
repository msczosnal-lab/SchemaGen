# Prompt startowy — 004 GraphBuilder

> Po akceptacji smoke OCR (~75%) i linii (002/003). Wklej w sesję Claude Cowork.

```
SchemaGen — Builder. PRIORYTET: filar składania — GraphBuilder.

Wczytaj:
- sync/prompts/004-graph-builder.md          ← spec implementacji
- sync/KOLEJNE-ZADANIE.md
- sync/filip-to-zw.md
- sync/zw-to-filip.md (wpisy 002 OCR, 002/003 linie)
- docs/schematic-interpretation.md

Plik do implementacji:
- backend/recognize/graph_builder.py         ← build() = NotImplementedError

Filar wejściowy (GOTOWE — używaj, nie przepisuj):
- OnnxSymbolDetector → components (bbox, type, confidence)
- PaddleOcrEngine → tagi / annotations (subprocess .venv-ocr, ~75% recall OK)
- LineTracer + LineClassifier → graphic_lines (role, semantic_group)

Reguły KRYTYCZNE:
- GraphicLine ≠ Connection
- Connection TYLKO gdy LineClassifier.is_connection_candidate(line) == True (role wire|bus)
- device_stroke / dash / frame → graphic_lines, NIGDY connections
- resolve_context() już jest — użyj na bboxach detekcji (ContextResolver)

build(image_path, source):
1. detect → Component[] (source=yolo)
2. OCR → dopasuj tagi do bbox (bbox OCR ∩ bbox symbolu) + annotations[]
3. trace + classify(image_size) → graphic_lines[]
4. wire/bus: przecięcia linii z bbox → Connection (from/to heurystyka terminali)
5. meta.source, meta.model_version z registry

Testy (mock detector/ocr/tracer — bez GPU/paddle w CI):
- backend/tests/test_graph_builder.py (nowy)
- SchemaModel: components + graphic_lines + connections
- Linia device_stroke NIE tworzy Connection

NIE ruszaj:
- atlas QET (008a)
- trening YOLO / train_cycle
- labeler (010, 002 linie DONE)
- scripts/preview_* (Cursor)

Po kodzie:
pytest backend/tests labeler/tests
sync/zw-to-filip.md — wpis z tabelą plików + wynik testów
sync/commit-message.txt = [Claude] recognize: graph builder (prompt 004)

Start-GitSync.cmd Claude po commicie.
```
