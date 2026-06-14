# NASTĘPNA SESJA — 2026-06-15

Wizja: [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md)

## Zrobione (Cursor)

- **010** labeler bbox-first + `config/symbol-palette.yaml` (52 hasła)

## Filip

```powershell
python -m labeler.app
```
Narysuj bbox → wybierz typ po prawej. Oznaczaj więcej schematów.

## Claude (ZW) — następne

- **002-ocr-engine** — filar tekst (PaddleOCR)
- Start: [`sync/PROMPT-CLAUDE-002-OCR.md`](PROMPT-CLAUDE-002-OCR.md)

## Kolejka Claude

1. 002 OCR (tekst)
2. 002-labeler-lines-colors + 003 line tracer (połączenia)
3. 004 graph builder (relacje)
