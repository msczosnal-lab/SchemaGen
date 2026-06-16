# Trening multi-class — wszystkie klasy (komendy dla PC Filip)

> Kod jest już na origin (multi-class). Daemon Filipa pobierze sam; ręcznie: `git pull`.
> Wymaga: `data/schemagen.db` + `data/raw/*.png` (lokalnie), `pip install -e ".[gpu]"`.

## Co się zmieniło

Klasa YOLO jest teraz wyprowadzana z pola `tag` adnotacji (nie z `class_name`).
Klasy budują się **automatycznie ze WSZYSTKICH tagów w bazie** — paleta daje kanoniczne
nazwy, reszta to slug z tagu. Bboxy bez tagu są pomijane (nie ucz na nieprzypisanych).

- `backend/class_map.py` — mapowanie tag → klasa, budowa mapy klas
- `train/dataset_export.py` — multi-class export, auto-generuje `config/symbol-classes.yaml`
- `train/train_symbols.py` — augmentacja pod schematy (bez odbić/obrotów/koloru), 150 epok
- `scripts/class_report.py` — podgląd klas z bazy (read-only)

## Kolejność komend

```powershell
cd <repo>\SchemaGen
git pull   # jeśli daemon sam nie pobrał

# 1. PODGLĄD klas (read-only) — zobacz wszystkie klasy i licznosci PRZED treningiem
python scripts/class_report.py
#   opcjonalnie zbij rzadkie klasy do "inny":
#   python scripts/class_report.py --min-count 5

# 2. EKSPORT datasetu multi-class (regeneruje config/symbol-classes.yaml + data.yaml)
python -m train.dataset_export
#   z progiem rzadkich klas:
#   python -c "from train.dataset_export import export_dataset; export_dataset(min_count=5)"

# 3. TRENING (RTX 2080: imgsz/batch z config/runtime.yaml = 1280/4, 150 epok)
python -m train.train_symbols --name symbols_mc_v1
#   jeśli OOM na 8 GB -> mniejszy batch:
#   python -m train.train_symbols --name symbols_mc_v1 --batch 2

# 4. EKSPORT do ONNX
python -m train.export_onnx --version symbols_mc_v1

# 5. PODGLĄD detekcji (pokaże nazwy klas)
python scripts/preview_detection.py --page data/raw/<strona>.png --conf 0.25
```

## Na co patrzeć w wynikach

- `class_report.py`: ile klas, czy któreś mają 1 instancję (oznaczone [RYZYKO] —
  słabo się nauczą i nie trafią do walidacji).
- Po treningu: **mAP50 per-klasa** (nie tylko globalne) + confusion matrix w
  `data/runs/symbols_mc_v1/`. Klasy z 1–2 próbkami będą słabe — to normalne, dosypać danych.

## Uwagi techniczne

- [RYZYKO] Podział train/val jest per-strona — przy wielu klasach część klas może nie
  trafić do val (mAP dla nich = 0 mimo nauki). Przy małej liczbie stron to artefakt,
  nie błąd modelu. Rozwiązanie: więcej oznaczonych stron.
- `config/symbol-classes.yaml` jest teraz AUTO-GENEROWANY przy eksporcie — nie edytuj ręcznie.
- Wyjątki (ramka „obiekt", listwy zaciskowe) na razie traktowane jak zwykłe klasy
  (ich tag = ich klasa). Specjalną obsługę dodamy osobno, gdy będzie potrzebna.
- Pełna diagnoza dlaczego było źle: `sync/RAPORT-YOLO-trening.md`.
