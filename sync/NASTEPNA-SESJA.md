# NASTĘPNA SESJA — 2026-06-15

Wizja: [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md)

## Trzy filary

| Filar | Teraz | Prompt |
|-------|-------|--------|
| Symbole | **010** bbox-first + paleta | Claude |
| Tekst | OCR | 002-ocr-engine |
| Połączenia | linie w labelerze + tracer | 002-labeler-lines, 003-tracer |

**Potem:** relacje tekst↔symbol↔połączenie → `004-graph-builder`

## ⛔ Nie używamy

Atlas QET, kurator, cropy, `symbol-reference.yaml`

## Claude

[`sync/PROMPT-CLAUDE-010.md`](PROMPT-CLAUDE-010.md) lub „kolejne zadanie”

## Filip

Bboxy symboli na wielu schematach — baza pod YOLO.
