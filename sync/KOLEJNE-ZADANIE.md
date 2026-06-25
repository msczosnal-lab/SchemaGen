# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

**Wizja:** [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md) — trzy filary + relacje.

---

## Stan (2026-06-25)

| Prompt | Status |
|--------|--------|
| **010-labeler-bbox-first-palette** | ✅ DONE |
| **005–006, 001 recognize, train_cycle** | ✅ DONE |
| **symbols_atomic_v2** | ✅ mAP50≈0.92, aktywny w registry |
| **002-ocr-engine** | ✅ DONE (Claude) — `PaddleOcrEngine` |
| **002-labeler-lines-colors** | 🟢 **AKTYWNE dla Claude** |
| **003-line-tracer** | OPEN — w tej samej sesji co linie |
| **004-graph-builder** | OPEN — po filarach |
| **008a QET atlas** | ⛔ NIE UŻYWAĆ |

---

## Aktywne zadanie — Claude (PRIORYTET)

| Pole | Wartosc |
|------|---------|
| **Cel** | Filar **połączenia** — GT linii w labelerze + LineTracer |
| **Start** | [`sync/PROMPT-CLAUDE-002-LINES.md`](PROMPT-CLAUDE-002-LINES.md) |
| **Prompty** | `002-labeler-lines-colors.md`, `003-line-tracer-classifier.md` |

**Nie ruszaj:** GraphBuilder (004), atlas QET, trening GPU.

---

## Aktywne zadanie — Filip

| Pole | Wartosc |
|------|---------|
| **OCR smoke** | `pip install paddlepaddle-gpu paddleocr` → `python scripts/preview_ocr.py --page data/raw/..._p035.png --lang latin` |
| **Review autolabel** | labeler (incognito) — propozycje modelu na stronach p051+ |
| **YOLO ocena** | `data/output/preview_batch/symbols_atomic_v2/index.html` |

### Cykl YOLO (gdy GT poprawione)

```powershell
python scripts/train_cycle.py
```

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
