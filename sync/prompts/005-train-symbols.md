# Zadanie 005: eksport datasetu + trening YOLOv8n (BUILD M0)

**Status:** OPEN — **PRIORYTET** (Filip: „spróbujmy build”, 2026-06-14)  
**Model:** Sonnet, effort **High**  
**Pliki:** `train/dataset_export.py` (nowy), `train/train_symbols.py`, `labeler/export.py` (fix PNG), opcjonalnie `backend/cli.py`

## Kontekst

Filip oznaczył strony w labelerze (SQLite). **Nie eksportował batch** — w `data/labeled/` jest tylko stary eksport p013.

### Stan datasetu (SQLite `data/schemagen.db`)

| page_id | bboxes |
|---------|-------:|
| SchematWRT01_p013 | 75 |
| SchematWRT01_p014 | 99 |
| SchematWRT01_p015 | 152 |
| SchematWRT01_p016 | 2 |
| SchematWRT01_p017 | 3 |
| SchematWRT01_p018 | 3 |
| SchematWRT01_p021 | 2 |
| SchematWRT01_p022 | 10 |
| SchematWRT01_p023 | 48 |
| **Razem** | **~394 bboxy, 9 stron** |

PNG źródłowe: `data/raw/SchematWRT01_p*.png`  
Klasa YOLO: jedna — `element` ([`config/symbol-classes.yaml`](../../config/symbol-classes.yaml))

**Filip:** STOP dalszego oznaczania do wyniku pierwszego buildu.

## Cel

Kod pierwszego treningu offline (Filip odpala GPU u siebie):

1. Batch eksport SQLite → struktura YOLO train/val
2. Implementacja `train_symbols.train()` (ultralytics)
3. Testy jednostkowe + instrukcja uruchomienia dla Filipa (RTX 2080)
4. **NIE** pełny trening na PC ZW — brak datasetu w gicie, słabe GPU/CPU

## Podział maszyn (OBOWIĄZKOWE)

| PC | Rola |
|----|------|
| **ZW (Claude Cowork)** | Implementacja kodu, `pytest`, commit. Smoke test exportu **tylko jeśli masz lokalnie** `data/schemagen.db` — inaczej testy na mock/fixture. |
| **Filip (RTX 2080, 8 GB)** | `pip install -e ".[gpu]"`, `python -m train.dataset_export`, `python -m train.train_symbols --epochs 30 --batch 8` |

Dane (`data/schemagen.db`, `data/raw/*.png`) są w `.gitignore` — **na ZW ich nie ma**. W `sync/zw-to-filip.md` podaj Filipowi gotowe komendy PowerShell.

**Nie commituj:** `best.pt`, `data/runs/`, ciężkie wagi — tylko kod + ewent. `symbols_v1_train_summary.json` po treningu u Filipa (opcjonalnie, lokalnie).

## 1. `train/dataset_export.py` (nowy)

CLI: `python -m train.dataset_export`

- Czytaj strony z bbox>0 z SQLite (`backend.db.list_pages`, `load_annotation`)
- Pomiń `test_*`
- Split **train/val** (~80/20): ostatnie 2 strony → val (p022, p023) lub `val_ratio=0.2`
- Struktura wyjściowa w `data/labeled/`:

```
data/labeled/
  data.yaml
  export-manifest.json
  images/train/*.png
  images/val/*.png
  labels/train/*.txt
  labels/val/*.txt
```

- Kopiuj PNG z `data/raw/` (po `page_id` lub `record.image_path`)
- Generuj etykiety YOLO — reuse logiki z [`labeler/export.py`](../../labeler/export.py) (`export_yolo`)
- `data.yaml`:

```yaml
path: <abs path data/labeled>
train: images/train
val: images/val
names:
  0: element
```

## 2. Fix `labeler/export.py`

Przy `export_yolo` / `export_all`: **kopiuj PNG** z `data/raw/` do `data/labeled/images/` (dziś brakuje — tylko `.txt`).

## 3. `train/train_symbols.py`

Usuń stub. Implementuj:

```python
def train(data_yaml=None, epochs=50, batch=8, imgsz=640, device=0, name="symbols_v1") -> dict
```

- Wymaga u Filipa: `pip install -e ".[gpu]"` (torch, ultralytics) — **nie instaluj ciężkiego GPU stacku na ZW jeśli niepotrzebny**
- Model startowy: `yolov8n.pt` (auto-download ultralytics)
- Config: [`train/configs/symbols.yaml`](../../train/configs/symbols.yaml) — epochs 50, batch 8, device 0
- Output run: `data/runs/symbols_v1/` (weights/best.pt)
- Zapisz summary JSON: `data/models/symbols_v1_train_summary.json`

CLI: `python -m train.train_symbols --epochs 30 --batch 8`

## 4. Testy

- `train/tests/test_dataset_export.py` — mock SQLite lub fixture JSON → sprawdź strukturę katalogów
- **Nie uruchamiaj** pełnego treningu 30–50 epok na PC ZW
- W `sync/zw-to-filip.md`: sekcja **„Uruchomienie u Filipa (RTX 2080)”** z komendami; metryki mAP dopisze Filip po swoim treningu

## Zakazy

- Cloud API
- Zmiana architektury modelu (zostaje YOLOv8n)
- Oznaczanie nowych stron przez Filipa w tym zadaniu

## Kolejność względem 008a

**005 ma priorytet nad 008a** — Filip chce build teraz. Atlas (008a) może iść **po** buildzie M0 lub równolegle jeśli masz capacity.

## Po ukończeniu

1. `pytest backend/tests labeler/tests train/tests`
2. Wpis w `sync/zw-to-filip.md` — pliki, pytest, **komendy dla Filipa** (bez best.pt z ZW)
3. `sync/commit-message.txt` = `[Claude] train: dataset export + YOLO train code M0 (prompt 005)`

## Następny krok (osobny prompt)

- **006-export-onnx** — `best.pt` → ONNX
- **001-symbol-detector** — inferencja na p016/p019
