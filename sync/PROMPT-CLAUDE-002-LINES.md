# Prompt startowy — 002 labeler linie + 003 line tracer

> Po **002-ocr-engine**. Wklej w sesję Claude Cowork.

```
SchemaGen — Builder. Kolejność filarów po OCR:

1. sync/prompts/002-labeler-lines-colors.md — GT linii wire/bus w labelerze
2. sync/prompts/003-line-tracer-classifier.md — LineTracer + LineClassifier (OpenCV)

Wczytaj:
- sync/KOLEJNE-ZADANIE.md
- sync/filip-to-zw.md
- docs/schematic-interpretation.md (filar 3 — połączenia)

Reguły:
- GraphicLine ≠ Connection — tylko wire/bus → Connection w GraphBuilder
- Kolory: config/semantic-colors.yaml
- NIE: atlas QET, trening GPU, GraphBuilder (004) w tej sesji

Po kodzie:
pytest backend/tests labeler/tests
sync/zw-to-filip.md
sync/commit-message.txt = [Claude] labeler: linie + line tracer (prompt 002/003)
```
