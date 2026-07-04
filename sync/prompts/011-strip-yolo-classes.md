# Zadanie 011: klasy listwy w YOLO + re-train

**Status:** OPEN — kod eksportu DONE (2026-06-28); trening = Filip (GPU)  
**Model:** Sonnet  
**Pliki:** `config/train-classes.yaml`, `config/symbol-palette.yaml`, `config/element-catalog.yaml`, `train/dataset_export.py`, testy

## Kontekst

Runtime p040: YOLO wykrywa **9/19** bbox — brak złączek, mostków, strzałek potencjału.  
Przyczyna: `zlaczka` była w `contextual` (wykluczona z eksportu); `mostek` mapował się na `crossing`.

GT p040: **19 bbox** (6 złączka, 2 mostek, 2 strzałka wejściowa, 9 urządzeń).  
Cała baza: **646 złączek / 28 stron**, **247 mostków**, **71+195 strzałek**.

## Cel

1. ✅ `zlaczka`, `mostek` → klasy YOLO (atomic)
2. ✅ Paleta: dedykowany `mostek` (nie `crossing`); `crossing` = skrzyżowanie przewodów
3. ✅ Testy eksportu bez GPU
4. ⏳ Re-train + ONNX — **Filip lokalnie** (nie Cursor/Claude)

## Decyzja Filipa (2026-06-28)

GT listwy p040 gotowe. **Re-train YOLO: TAK.**

## Komendy treningu (Filip, RTX 2080)

```powershell
cd C:\Users\Filip\Desktop\Cursor\SchemaGen
.venv311\Scripts\Activate.ps1

# 1. Podgląd klas (zlaczka, mostek powinny być w YOLO)
python scripts/class_report.py

# 2. Eksport datasetu
python -m train.dataset_export --min-count 5

# 3. Trening (nowa wersja)
python -m train.train_symbols --name symbols_strip_v1 --batch 4

# 4. ONNX + registry
python -m train.export_onnx --version symbols_strip_v1

# 5. Walidacja p040
python scripts/preview_schema.py --page p040 --source runtime
python scripts/diff_gt_runtime.py --page p040   # jeśli istnieje
```

Oczekiwany wynik po re-train: **~19/19 bbox** runtime, brak gwiazdy do `sym_0`, connections bliżej GT.

## Nie ruszać

- `net_builder`, `line_sieve`, `graph_builder` (DONE)
- `config/runtime.yaml` pokrętła
- atlas QET
