# Trening sieci YOLO — SchemaGen

Skrócona instrukcja do samodzielnej pracy na PC z GPU (RTX 2080).  
Pełna historia napraw: [`sync/SESJA-2026-06-16-SSN.md`](sync/SESJA-2026-06-16-SSN.md), [`sync/RAPORT-YOLO-trening.md`](sync/RAPORT-YOLO-trening.md).

---

## Wymagania

```powershell
cd C:\Users\Filip\Desktop\Cursor\SchemaGen
.venv311\Scripts\Activate.ps1          # Py 3.11 — unikaj systemowego python
pip install -e .                       # jednorazowo; skrypt dziala tez bez tego
python scripts/class_report.py
```

Dane lokalne (poza gitem): `data/schemagen.db`, `data/raw/*.png`.

---

## Co uczy YOLO, a co nie

| Warstwa | Źródło | Uwagi |
|---------|--------|--------|
| **Klasa YOLO** | pole `tag` w labelerze → [`backend/class_map.py`](backend/class_map.py) | Multi-class, auto lista w `config/symbol-classes.yaml` |
| **Kontekstowe (bez YOLO)** | [`config/train-classes.yaml`](config/train-classes.yaml) | GT w bazie — resolver wierszy (faza 2) |

### Semantyka wierszy (oś Y)

Na schemacie wiele obiektów ma sens **tylko w poziomym rzędzie** (wspólna oś Y). Odległości między elementami nie są ustandaryzowane. Na jednej stronie może być **wiele rzędów**. Rząd złączek tworzy **listwę złączek** lub **zwartą listwę złączek** (jeden rząd = jedna listwa), chyba że na tym samym Y widać **drugi oznacznik listy** — wtedy dwie listwy obok siebie.

| Rząd składa się z… | Tworzy obiekt-nadzór? | Przykładowe tagi |
|--------------------|----------------------|------------------|
| złączki | tak → **listwa złączek** albo **zwarta listwa złączek** | `zlaczka` (YOLO), `listwa_zlaczek`, `zwarta_listwa_zlaczek` (GT) |
| złącza | nie (rząd bez „listy”) | `zlacze` |
| oznaczniki przewodów | tak → oznaczenie kabla | `oznaczenie_przewodu`, `oznaczenie_kabla` |
| terminale urządzenia | nie (skraj bloku) | `terminale_urzadzenia` |

**Wykluczone z YOLO** — oznaczaj dalej w labelerze (GT relacji):

- `zlacze`
- `listwa_zlaczek`, `zwarta_listwa_zlaczek` (bbox całej listwy też tylko GT)
- `oznaczenie_kabla`, `oznaczenie_przewodu`
- `terminale_urzadzenia`

**Klasy listwy w YOLO** (od 2026-06-28, prompt 011): `zlaczka`, `mostek`, `strzalka_potencjalu_wejsciowa`, `strzalka_potencjalu_wyjsciowa`.

**Zostają w YOLO** (klasy atomowe): m.in. `relay`, `terminal_plc`, `zlaczka`, `mostek`, `styki`, `led` — wszystko poza powyższą listą wykluczeń.

Parametry treningu: [`config/runtime.yaml`](config/runtime.yaml) — domyślnie `imgsz: 1536`, `batch: 4`, `conf: 0.25`.

---

## Cykl treningu (powtarzalny)

### 0. Pętla jednym poleceniem (zalecane)

```powershell
python scripts/train_cycle.py
python scripts/train_cycle.py --name symbols_atomic_v2 --min-count 5
python scripts/train_cycle.py --skip-train   # tylko export + preview
```

Log iteracji: `data/models/train_cycle_log.jsonl`  
Stały val: `config/val-pages.yaml`

### 1. Podgląd klas w bazie

```powershell
python scripts/class_report.py
python scripts/class_report.py --min-count 5
```

Pokazuje liczności, klasy wykluczone kontekstowo i co wypadnie przez `--min-count`.

### 2. Eksport datasetu

```powershell
python -m train.dataset_export --min-count 5
```

Wynik: `data/labeled/` (`data.yaml`, `images/`, `labels/`, `export-manifest.json`).  
Regeneruje `config/symbol-classes.yaml` (nie edytuj ręcznie).

### 3. Trening

```powershell
python -m train.train_symbols --name symbols_atomic_v1
# OOM na 8 GB VRAM:
python -m train.train_symbols --name symbols_atomic_v1 --batch 2
# inny rozmiar wejścia:
python -m train.train_symbols --name symbols_atomic_v1 --imgsz 1536 --batch 2
```

Wagi: `data/runs/symbols_atomic_v1/weights/best.pt`  
Podsumowanie: `data/models/symbols_atomic_v1_train_summary.json`

Augmentacja wyłączona (flip/mosaic/hsv = 0) — bboxy ciasne, schemat kierunkowy.

### 4. Eksport ONNX

```powershell
python -m train.export_onnx --version symbols_atomic_v1
```

Model aktywny: `data/models/registry.json` → `symbols_atomic_v1.onnx`

**Sanity check klas w modelu:**

```powershell
python -c "import onnxruntime as ort; m=ort.InferenceSession('data/models/symbols_atomic_v1.onnx'); print(m.get_modelmeta().custom_metadata_map.get('names'))"
```

### 5. Ocena wzrokowa

```powershell
python scripts/preview_batch.py --version symbols_atomic_v1 --conf 0.25 --limit 30
python scripts/preview_batch.py --version symbols_atomic_v1 --offset 20 --limit 16 --conf 0.25 --gt-context
# strony p020–p035 Adamed (offset=20, limit=16)
python scripts/preview_detection.py --page data/raw/SchematWRT01_p013.png --conf 0.25
python scripts/visualize_yolo_dataset.py
python scripts/visualize_bboxes.py
```

Patrz na **mAP50 per-klasa** w `data/runs/symbols_atomic_v1/` — globalne mAP przy małym val bywa zaszumione.

---

## Labeler i active learning

```powershell
python -m labeler.app
```

Po zmianie danych w bazie: **wyczyść localStorage** (`schemagen:draft:*`) lub okno incognito.

Propozycje modelu na nowe strony:

```powershell
python scripts/autolabel.py --all-unlabeled --conf 0.3 --apply
```

Poprawki klas:

```powershell
python scripts/relabel_tool.py
python scripts/apply_reassign.py --apply
```

---

## Wyższa rozdzielczość skanu

PDF → PNG @ 400 DPI ([`config/ingest.yaml`](config/ingest.yaml)):

```powershell
python scripts/reingest_highdpi.py --dry-run
python scripts/reingest_highdpi.py --apply
```

Po `--apply` bboxy w SQLite są przeskalowane. Potem ponowny eksport + trening (`symbols_atomic_v1`).

## OCR (filar tekst — po commicie Claude 002)

```powershell
pip install paddlepaddle-gpu paddleocr   # CPU: paddlepaddle paddleocr
python scripts/preview_ocr.py --page data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p035.png --lang latin
python scripts/preview_ocr.py --offset 20 --limit 5 --lang latin
```

Wynik: `data/output/preview_ocr/index.html`

## Resolver kontekstu (faza 2)

GT z labelera: `ContextResolver` w [`backend/geometry/row_layout.py`](backend/geometry/row_layout.py) — grupy Y, kotwice listwy/kabla, pole `context_assignments` w `.schema.json`.

Runtime import: `from backend.recognize.context_resolver import ContextResolver`

---

## Pułapki

| Problem | Rozwiązanie |
|---------|-------------|
| Stare bboxy w labelerze | localStorage / incognito |
| `export_onnx` bierze zły model | `--version` musi = nazwa folderu w `data/runs/` |
| Wszystko klasa `element` | stary pipeline — użyj multi-class (`class_map.py`) |
| 8/10 identycznych złączek | `zlaczka` nie jest klasą YOLO — resolver kontekstowy (faza 2) |
| ONNX na CPU zamiast GPU | brak `cublasLt64_12.dll` — torch cu121 dodaje DLL; inferencja i tak działa |

---

## Pliki kluczowe

| Plik | Rola |
|------|------|
| [`config/train-classes.yaml`](config/train-classes.yaml) | klasy kontekstowe bez YOLO |
| [`config/symbol-palette.yaml`](config/symbol-palette.yaml) | picker labelera |
| [`config/symbol-classes.yaml`](config/symbol-classes.yaml) | klasy YOLO (auto) |
| [`train/dataset_export.py`](train/dataset_export.py) | SQLite → YOLO |
| [`train/train_symbols.py`](train/train_symbols.py) | trening ultralytics |
| [`backend/recognize/symbol_detector.py`](backend/recognize/symbol_detector.py) | inferencja ONNX |

Szczegółowe komendy multi-class: [`sync/KOMENDY-trening-multiclass.md`](sync/KOMENDY-trening-multiclass.md).
