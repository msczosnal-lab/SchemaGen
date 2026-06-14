# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

---

## Stan (2026-06-14 — BUILD M0)

| Prompt | Status |
|--------|--------|
| **001-labeler-canvas** | DONE |
| **003-labeler-bbox-hierarchy** | DONE |
| **007-sources-analysis** | DONE — akceptacja Filipa |
| **005-train-symbols (BUILD M0)** | **PRIORYTET #1** |
| **008-symbol-atlas-extract (QET)** | OPEN — po 005 lub równolegle |
| **002-labeler-lines-colors** | OPEN |
| **009-bbox-symbol-id** | po 008a |

---

## Aktywne zadanie — PRIORYTET

| Pole | Wartosc |
|------|---------|
| **Prompt** | [`sync/prompts/005-train-symbols.md`](prompts/005-train-symbols.md) |
| **Deliverable** | `train/dataset_export.py`, `train/train_symbols.py`, pierwszy `best.pt` |
| **Typ** | Implementacja + uruchomienie treningu offline |
| **Model** | Sonnet, effort **High** |

### Dataset (gotowy w SQLite — NIE w data/labeled/)

9 stron, ~394 bboxy: p013(75), p014(99), p015(152), p016–p018, p021–p023.  
Eksport batch = część zadania 005.

### Kroki

1. Przeczytaj `sync/filip-to-zw.md` (wpis BUILD M0)
2. `pip install -e ".[gpu]"` jeśli brak torch/ultralytics
3. Zaimplementuj **005** wg promptu
4. `python -m train.dataset_export`
5. `python -m train.train_symbols --epochs 30 --batch 8`
6. `pytest backend/tests labeler/tests train/tests`
7. Wpis w `sync/zw-to-filip.md`
8. `sync/commit-message.txt` = `[Claude] train: dataset export + YOLOv8n symbols M0 (prompt 005)`

### Czego NIE robic w 005

- Atlas QET (008a) — osobne zadanie
- ONNX (006) — następne po best.pt
- Cloud API

---

## Zadanie wtórne (po 005 lub równolegle)

| Prompt | Plik |
|--------|------|
| **008a QET atlas** | [`008-symbol-atlas-extract.md`](prompts/008-symbol-atlas-extract.md) |

---

## Kontekst

- Filip oznaczył **9 stron** ogólniej (krótsze tagi) — **STOP bboxów** do wyniku buildu
- WRT01 PNG: `data/raw/SchematWRT01_p*.png`
- RTX 2080, batch≤8

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]`. Nie nadpisuj jesli jest `[Cursor]` i niepusty.
