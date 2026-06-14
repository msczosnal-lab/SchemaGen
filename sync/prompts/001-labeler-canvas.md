# Zadanie 001: labeler/static/app.js — canvas bbox symboli

**Status:** OPEN — pierwsze zadanie Cowork po pivotcie  
**Model:** Sonnet, effort High  
**Plik:** `labeler/static/app.js`  
**API:** `labeler/app.py` (dziala)

## Kontekst

Labeler FastAPI na `:8765`. Backend i export YOLO dzialaja. Brakuje interaktywnego canvas do bbox.

## Implementuj

1. Rysowanie bbox: mousedown → mousemove → mouseup
2. Aktywna klasa z listy (`config/symbol-classes.yaml`), klawisze 1–9
3. Zoom: scroll na canvas
4. Wyswietlanie istniejacych bbox po zaladowaniu strony (GET `/api/annotations`)
5. Del — usuwa zaznaczony bbox
6. Zapis przez POST `/api/annotations`

## Test akceptacji (reczny)

```
python -m labeler.app   # lub dev.ps1
# localhost:8765 — 3 bbox, zapis, eksport
```

## Zakazy

- React, npm, cloud API
- Nie zmieniaj modeli Pydantic w `backend/models/`

## Po ukonczeniu

1. `pytest labeler/tests`
2. Wpis w `sync/zw-to-filip.md`
3. `sync/commit-message.txt` = `[Claude] labeler: canvas bbox (prompt 001)`

## Poprawka (runda N)

*(Cursor dopisuje tu feedback po review)*
