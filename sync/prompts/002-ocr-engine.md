# Zadanie 002: PaddleOcrEngine — filar TEKST

**Status:** OPEN — priorytet po 010 (symbole DONE)  
**Model:** Sonnet, effort **High**  
**Plik:** `backend/recognize/ocr_engine.py`  
**Wizja:** [`docs/schematic-interpretation.md`](../../docs/schematic-interpretation.md)

## Kontekst

Trzeci filar interpretacji schematu (2/3): **tekst** — tagi `-K1`, opisy, adresy krosowe.

- **Symbole (010):** DONE — YOLO + labeler bbox-first
- **Tekst (ten prompt):** OCR offline na PNG strony
- **Połączenia:** później (003 line tracer)

**Bez cloud API.** PaddleOCR lokalnie (GPU opcjonalnie, CPU OK na smoke).

## Cel

Implementuj `PaddleOcrEngine.extract_text(image_path: Path) -> list[TextDetection]`:

```python
@dataclass
class TextDetection:
    text: str
    bbox: list[float]  # [x1, y1, x2, y2] w pikselach obrazu
    confidence: float
```

- Leniwy import `paddleocr` (jak onnxruntime w detektorze)
- Jeśli brak biblioteki — czytelny `ImportError` z hintem instalacji
- Język: **en** + obsługa polskich znaków jeśli model wspiera (domyślnie `lang='en'` lub `latin` — dokumentuj w zw-to-filip)

## Integracja

- `GraphBuilder` już importuje `PaddleOcrEngine` — nie zmieniaj sygnatury konstruktora
- Wynik OCR → później `SchemaModel.annotations` / przypisanie tagów do symboli (004)

## Testy — `backend/tests/test_ocr_engine.py`

- Mock paddleocr — bez pobierania modeli w CI
- Fake engine zwraca 1–2 `TextDetection`
- Guard: brak paddleocr → sensowny wyjątek

```bash
pytest backend/tests/test_ocr_engine.py backend/tests labeler/tests
```

## Czego NIE robić

- Cloud API (Google Vision, Azure OCR)
- Labeler UI dla tekstu (osobny prompt później)
- GraphBuilder / line tracer w tej sesji
- Atlas QET

## Po ukończeniu

1. `pytest backend/tests labeler/tests`
2. `sync/zw-to-filip.md` — `pip install paddleocr`, smoke na `data/raw/*.png`
3. `sync/commit-message.txt` = `[Claude] recognize: PaddleOCR engine (prompt 002-ocr)`

## Poprawka (runda N)

*(Cursor)*
