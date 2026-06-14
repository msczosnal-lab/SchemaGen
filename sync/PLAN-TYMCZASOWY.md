# Plan — tymczasowy handoff (2026-06-14 wieczór)

> **Usuń po przeczytaniu** albo zarchiwizuj po następnej sesji. Start jutro: [`NASTEPNA-SESJA.md`](NASTEPNA-SESJA.md).

---

## Gdzie jesteśmy

**BUILD M0 domknięty lokalnie u Filipa** — pierwszy pełny obieg trening → ONNX → inferencja.

| Kamień | Status |
|--------|--------|
| Labeler + bbox (001 canvas, 003 hierarchia) | ✅ w repo |
| Dataset export + kod treningu (005) | ✅ kod + lokalny eksport |
| Trening YOLO RTX 2080 | ✅ `best.pt`, mAP50 ≈ **0.085** (30 epok) |
| Export ONNX (006) | ✅ `data/models/symbols_v1.onnx` + `registry.json` |
| Detektor ONNX (001 recognize) | ✅ działa (CPU); smoke: **5 detekcji** na p013 przy `conf=0.05` |
| Atlas QET (008a) | ⏳ następny sensowny krok jakości |
| Line tracer + graph builder (003/004 recognize) | ⏳ po detektorze/atlasie |
| Labeler linie + kolory (002) | ⏳ OPEN |

---

## Co poszło nie tak (i jak naprawiono)

### Claude (PC ZW)
- Pominął kolejność: zrobił **006+001** zanim Filip wytrenował model.
- Naprawy `export_onnx` (auto-find `best.pt`) były irrelevantne — wag po prostu nie było.
- Metryki „mAP50≈0.04, 17 epok” pochodziły z testów mock, nie z GPU Filipa.

### Środowisko GPU (Filip)
- **`.venv`** (Python 3.14 + `torch+cpu`) — **nie używać** do treningu/inferencji GPU.
- **`.venv311`** (Python 3.11) — właściwe venv; odbudowane z `torch cu121` + ultralytics.
- **onnxruntime-gpu**: brak `cublasLt64_12.dll` → CUDA provider pada, **fallback CPU działa**. Naprawa opcjonalna (CUDA Toolkit 12 + cuDNN 9 w PATH).

### Jakość modelu (oczekiwana)
- 9 stron treningu, jedna klasa `element`, mAP50 ≈ 0.085.
- Przy domyślnym `conf=0.25` → **0 detekcji** na p013/p015.
- Przy `conf=0.05` → **5 detekcji** na p013 (pipeline OK, model słaby).
- p019 i inne strony spoza train/val — zero trafień to norma na tym etapie.

---

## Podział pracy (stała zasada)

| Kto | Co |
|-----|-----|
| **Cursor** | Protokoły, prompty, review, akceptacja, sync |
| **Claude ZW** | Implementacja `NotImplementedError` + pytest (bez pełnego treningu / bez `data/schemagen.db`) |
| **Filip** | Labeler, trening GPU, eksport ONNX, testy ręczne, kierunek |

**Zakaz:** cloud API w `backend/recognize/`, `train/`, `labeler/`.

**Semantyka:** `GraphicLine` ≠ `Connection`. Tylko `wire`/`bus` → Connection w GraphBuilder.

---

## Plan — kolejność priorytetów

### Faza A — jakość detekcji (najbliższe tygodnie)

1. **008a — atlas QET** (Claude ZW)  
   `config/symbol-reference.yaml` + cropy z biblioteki QET.  
   Cel: więcej klas / referencja symboli, nie tylko jeden `element`.

2. **Filip — więcej bboxów** (opcjonalnie równolegle)  
   Rozszerzyć strony poza p013–p023; szczególnie typy symboli z atlasu.  
   Po zebraniu danych: re-export → re-train → re-export ONNX.

3. **009 — bbox symbol_id** (po 008a)  
   Powiązanie bboxów z kanonicznymi ID z atlasu.

### Faza B — pełny pipeline READ

4. **002-labeler-lines-colors** — polyline + kolory w labelerze (GT dla linii).

5. **003-line-tracer-classifier** — OpenCV linie + klasyfikacja kolorów.

6. **004-graph-builder** — detekcje + linie + OCR → `SchemaModel`.

7. **002-ocr-engine** — PaddleOCR (offline).

### Faza C — infrastruktura (gdy boli)

- ONNX GPU: CUDA 12 + cuDNN 9 dla `onnxruntime-gpu` (teraz CPU wystarczy).
- Dokumentacja venv: zawsze `.venv311` + jawna instalacja `torch cu121`.
- Reguła dla Claude: **006/001 dopiero po potwierdzeniu `best.pt` u Filipa**.

---

## Komendy Filipa (`.venv311`)

```powershell
cd C:\Users\Filip\Desktop\Cursor\SchemaGen
.venv311\Scripts\Activate.ps1

# Trening (gdy nowe dane)
python -m train.dataset_export
python -m train.train_symbols --epochs 30 --batch 8
python -m train.export_onnx

# Smoke inferencji (strona z treningu, niski próg)
python -c "from backend.recognize.symbol_detector import OnnxSymbolDetector; d=OnnxSymbolDetector('data/models/symbols_v1.onnx', {'element':0}); print(len(d.detect('data/raw/SchematWRT01_p013.png', conf_threshold=0.05)))"

# Testy
pytest backend/tests labeler/tests train/tests
python -m backend.cli validate schema/fixtures/page1_expected.json
```

---

## Następna sesja Claude (ZW)

Filip pisze: **„kolejne zadanie”** → wczytaj:

1. `sync/KOLEJNE-ZADANIE.md` (zaktualizowany: priorytet **008a**)
2. `sync/filip-to-zw.md` (najnowszy wpis)
3. `sync/prompts/008-symbol-atlas-extract.md`

**Nie rób:** pełnego treningu YOLO na ZW, cloud API, implementacji 003/004 w tej samej sesji co 008a (chyba że Filip każe).

---

## Artefakty lokalne (nie w gicie)

- `data/schemagen.db`, `data/raw/*.png`
- `data/runs/`, `best.pt`, `*.onnx`
- `.venv311/`

W repo zostaje tylko kod + `registry.json` (pusty/szkielet u innych) + labeled labels bez obrazów.
