# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

**Wizja:** [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md) — trzy filary + relacje.

---

## Stan (2026-06-24)

| Prompt | Status |
|--------|--------|
| **010-labeler-bbox-first-palette** | ✅ DONE |
| **005–006, 001 recognize** | ✅ BUILD M0 + multi-class |
| **train_cycle + val-pages** | ✅ DONE (Cursor) — `scripts/train_cycle.py`, `config/val-pages.yaml` |
| **symbols_atomic_v1** | ✅ wytrenowany (mAP50≈0.15) |
| **symbols_atomic_v2** | 🔄 trening w toku / Filip: `python scripts/train_cycle.py --name symbols_atomic_v2` |
| **008a QET atlas** | ⛔ NIE UŻYWAĆ |
| **002-ocr-engine** | 🟢 GOTOWE DO CLAUDE — [`sync/PROMPT-CLAUDE-002-OCR.md`](PROMPT-CLAUDE-002-OCR.md) |
| **002-labeler-lines-colors** | OPEN — po OCR: [`sync/PROMPT-CLAUDE-002-LINES.md`](PROMPT-CLAUDE-002-LINES.md) |
| **003-line-tracer** | OPEN — w PROMPT-CLAUDE-002-LINES |
| **004-graph-builder** | OPEN — po filarach |

**Dane:** 75+ stron GT, autolabel +138 stron (2026-06-24) — **wymaga review w labelerze** przed treningiem na surowych propozycjach.

---

## Aktywne zadanie — Claude (PRIORYTET)

| Pole | Wartosc |
|------|---------|
| **Cel** | Filar **tekst** — PaddleOCR offline |
| **Prompt** | [`sync/prompts/002-ocr-engine.md`](prompts/002-ocr-engine.md) |
| **Start** | [`sync/PROMPT-CLAUDE-002-OCR.md`](PROMPT-CLAUDE-002-OCR.md) |

### Po OCR (kolejna sesja Claude)

[`sync/PROMPT-CLAUDE-002-LINES.md`](PROMPT-CLAUDE-002-LINES.md) — labeler linie + line tracer.

---

## Aktywne zadanie — Filip

| Pole | Wartosc |
|------|---------|
| **Review autolabel** | `python -m labeler.app` (incognito) — strony p051+ z propozycjami modelu |
| **Pętla treningowa** | `python scripts/train_cycle.py --name symbols_atomic_v2` |
| **Ocena** | `data/output/preview_batch/symbols_atomic_v2/index.html` |

### Cykl (powtarzalny)

```powershell
python scripts/autolabel.py --all-unlabeled --conf 0.3 --apply
python -m labeler.app
python scripts/train_cycle.py
```

Log: `data/models/train_cycle_log.jsonl` · audyt: `data/output/class_report_audit.json`

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
