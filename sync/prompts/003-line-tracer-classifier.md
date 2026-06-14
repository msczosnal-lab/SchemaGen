# Zadanie 003: LineTracer + LineClassifier — OpenCV + kolory

**Status:** BLOCKED — po promptach 001–002 lub rownolegle jesli brak danych labelera  
**Model:** Opus, effort High  
**Pliki:**
- `backend/recognize/line_tracer.py`
- `backend/recognize/line_classifier.py`
- `backend/tests/test_line_tracer.py` (nowy)
- `backend/tests/test_line_classifier.py` (rozszerz)

## Kontekst wazny

**Linia ≠ polaczenie.** Pipeline:
1. `LineTracer.trace(image)` → segmenty geometryczne + `detected_color` (sampling HSV wzdloz linii)
2. `LineClassifier.classify(segments)` → `list[GraphicLine]` z `role`, `semantic_group`, `color_ref`
3. Tylko linie z `role in {wire, bus}` ida do GraphBuilder jako kandydaci na Connection

Paleta: `backend/colors/palette.py` + `config/semantic-colors.yaml`

## LineTracer — implementuj

- OpenCV: morfologia, Canny/HoughLinesP lub podobne
- Merge kolinearnych segmentow
- Dla kazdego segmentu: probka koloru ze srodka linii → hex `detected_color`
- Zwroc `list[LineSegment]`

## LineClassifier — implementuj

- `palette.match_color(detected_color)` → `semantic_group`
- Heurystyki roli:
  - przerywana linia (analiza maski) → `dash`
  - gruba pozioma/pionowa linia w obszarze wielu symboli → `bus`
  - linia wokol bbox symbolu → `device_stroke`
  - domyslnie czarny/kolor cable → `wire`
- Polacz segmenty w polilinie (`GraphicLine.points`)
- **NIE** tworz `Connection` — to robi GraphBuilder (prompt 004)

## Testy pytest

- Sztuczny obraz 100x100 z czarna linia pozioma → trace zwraca >=1 segment
- `#9933FF` → match `inverter`
- `device_stroke` → `is_connection_candidate` == False

## Zakazy

- Cloud API
- Nie zmieniaj sygnatur klas bez zgody Cursor

## Po ukonczeniu

1. `pytest backend/tests`
2. `sync/commit-message.txt` = `[Claude] recognize: line tracer + classifier (prompt 003)`

## Poprawka (runda N)

*(Cursor)*
