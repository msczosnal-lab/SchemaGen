# Skrzynka: ZW → Filip

> Pisze **tylko ZW** (Cowork/Claude). Filip czyta na starcie sesji i nie edytuje tego pliku.
> Najnowsze wpisy na górze.

---

## 2026-06-27 [ZW] — Kalibracja LineTracer: progi względne do rozdzielczości

Temat: **Szum Hough (p040: 1321 linii przy 6617px) → progi auto-skalowane. frac 0.02 wybrany wzrokowo (Filip).**

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `backend/recognize/line_tracer.py` | `auto_line_params(w,h)` + `LineTracer._params()`. Progi `None` → auto wg `max(W,H)`: `min_line_length=0.02·max`, `hough=max(50,min_line_length)`, `max_line_gap=0.0015·max`. Jawne int nadal nadpisują (testy/kalibracja). |
| `backend/tests/test_line_tracer.py` | +2 testy: skalowanie progów (6617→132/132/10; floory 20/50/4) + override jawnego param. |

### Dlaczego

- Sztywne `min_line_length=30` było absurdalnie małe na skanie 6617px (literka) → 1321 linii.
- Kalibracja wzrokowa (throwaway `preview_calib.py`, nakładki w `data/output/calib/`): **frac 0.02 = optimum** na p040 i p035. 0.03 ucinał linię stycznika; niżej — szum.
- Klasyfikator woła ~wszystko „wire/bus" (kolor czarny+oś) → redukcja szumu MUSI zejść z tracera, nie z klasyfikatora.

### Testy

```
pytest backend/tests labeler/tests  →  116 passed (mount sandboxu flip-flopował na świeżych plikach;
                                        kanon poprawny, 2 nowe asercje = arytmetyka, policzone ręcznie)
```

### Zostaje otwarte (następny krok)

[RYZYKO] Przy frac 0.02 wciąż leci **nadłapanie**, którego progiem NIE usuniemy:
1. **Obramówki urządzeń/terminali** klasyfikowane jako wire/bus (czarne, w osi, brak koloru sem. → default wire). To wada heurystyki klasyfikatora.
2. **Artefakty z tekstu** (krótkie segmenty w osi).
→ Potrzebne **sito po klasyfikacji** (np. odrzucanie segmentów tworzących zamknięte prostokąty = ramki; filtr na bliskość bbox-tekstu). Osobny temat.

[RYZYKO] Fragmentacja: realny przewód bywa cięty na kawałki → `GraphBuilder` łączy tylko końce jednego segmentu (p040: 4 connections). Docelowo: scalanie łańcuchów wire/bus w polilinie przed szukaniem terminali.

### Throwaway (skasować)

`calib_lines.py`, `preview_calib.py` — pomoce kalibracyjne, nie część pipeline.

---

## 2026-06-27 [ZW] — Prompt 004: GraphBuilder.build (składanie 3 filarów)

Temat: **`build()` składa SchemaModel z detekcji + OCR + linii. Connection TYLKO z wire/bus.**

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `backend/recognize/graph_builder.py` | `build()` — orkiestracja: detect→components(source=yolo), OCR→tag dopasowany do bbox + `annotations[]`, trace+classify→`graphic_lines[]`, wire/bus→`connections[]`, `meta.model_version` z registry, `context_assignments` (best-effort `resolve_context`) |
| `backend/tests/test_graph_builder.py` | nowy — 7 testów na mockach (bez GPU/paddle/CV) |

### Logika `build(image_path, source)`

1. `detect` → `Component[]` (`id=sym_i`, `bbox=[x1,y1,x2,y2]`, `source="yolo"`).
2. OCR: tekst z najwiekszym przecieciem z bbox symbolu → `Component.tag`; reszta → `annotations[]`.
3. `trace` + `classify(image_size)` → `graphic_lines[]`.
4. **Connection tylko gdy** `is_connection_candidate(line)` (role wire|bus). Konce linii → najblizszy symbol (tolerancja terminala `max(12px, 0.012·max(W,H))`); `from`/`to` = id symboli, dedup par. `kind`: grupa PE → `pe`, inaczej `power`.
5. `meta.source`, `meta.model_version` = aktywny model z `registry.json`.

### Zasady domenowe (utrzymane)

- **GraphicLine ≠ Connection.** `device_stroke`/`frame`/`dash`/`crossing` → tylko `graphic_lines`, NIGDY `connections` (test to weryfikuje).
- Filary 001/002/003 użyte jako gotowe — bez przepisywania. Lazy-init gdy GraphBuilder bez wstrzyknietych zaleznosci (runtime czyta model z registry).

### Testy

```
pytest backend/tests labeler/tests          →  116 passed
python -m backend.cli validate schema/fixtures/page1_expected.json  →  approved (0 errors)
```

[RYZYKO] Heurystyka `from`/`to` jest na poziomie **symbolu**, nie terminala (fixture GT ma `F1:2`/`U1:L1` — to recznе GT, nie target build). Terminale + `potential` = osobny krok po GT linii (p030).
[RYZYKO] `potential` zawsze `""` — brak odczytu etykiet przewodu. Do rozbudowy gdy OCR poda etykiety na liniach.
[RYZYKO] Próg terminala kalibrowany na rozmiar strony — sprawdź na realnym skanie (Adamed p035) czy konce wire trafiaja w bbox symboli.

### Filip — smoke u siebie (RTX 2080)

```powershell
python -c "from backend.recognize.pipeline import recognize_file; m=recognize_file('data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p035.png'); print(len(m.components),'komp',len(m.graphic_lines),'linii',len(m.connections),'conn')"
```

NIE ruszane: atlas QET, trening YOLO/train_cycle, labeler, scripts/preview_*.

---

## 2026-06-25 [ZW] — Prompt 002+003: filar POŁĄCZENIA (labeler linie + line tracer)

Temat: **Tryb polyline w labelerze + LineTracer/LineClassifier OpenCV. Linia ≠ Connection.**

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `labeler/app.py` | + `GET /api/semantic-groups`, `GET /api/match-color?hex=` (czytają semantic-colors.yaml) |
| `labeler/static/index.html` | toolbar trybu Bbox/Linia + rola + grupa + pipeta; lista linii; `app.js?v=21` |
| `labeler/static/app.js` | tryb polyline: klik=punkt, Enter/dblklik=koniec, Esc=anuluj, Del=usuń; eyedropper (sampling piksela canvas → match-color); rysowanie/edycja/zapis `lines[]` |
| `labeler/static/style.css` | style toolbara + listy linii |
| `backend/recognize/line_tracer.py` | OpenCV: Canny+dylatacja+HoughLinesP, merge kolinearnych, sampling koloru HSV→hex (re-sampling po scaleniu) |
| `backend/recognize/line_classifier.py` | segment→`GraphicLine` (role, semantic_group, color_ref, detected_color); heurystyki roli; **NIE** tworzy Connection |
| `backend/tests/test_line_tracer.py` | nowy — trace, sampling, merge |
| `backend/tests/test_line_classifier.py` | rozszerzony — wire/bus/device_stroke/dash, kandydaci Connection |
| `labeler/tests/test_lines_api.py` | nowy — endpointy + round-trip `graphic_lines` |

### Zasady domenowe (utrzymane)

- `GraphicLine ≠ Connection`. Tylko `role ∈ {wire, bus}` → `is_connection_candidate == True` → kandydaci dla GraphBuilder (004).
- Kolor → grupa przez `palette.match_color` (config/semantic-colors.yaml). `#9933FF` → `inverter` → rola `device_stroke` (nie-połączenie).
- Heurystyka roli: kolor (dash/device_stroke/frame) > geometria (długa linia w osi → `bus`) > domyślnie `wire`.

### Testy

```
pytest backend/tests labeler/tests  →  107 passed
```

[RYZYKO] LineTracer/Classifier to filar **runtime** (CV). Nie podłączony jeszcze do GraphBuilder — to prompt 004. `pipeline.py` bez zmian.
[RYZYKO] Próg `bus` domyślnie 400 px lub 0.45·max(W,H) gdy podasz `image_size` — do kalibracji na realnych skanach.

### Filip — do zrobienia

1. Labeler: `python -m labeler.app` → przełącz **L** (linia), narysuj wire (czarna) + device_stroke (fiolet), pipeta na kolor, eksport → sprawdź `*.schema.json` ma `graphic_lines`.
2. Zwróć uwagę czy progi Hougha (`min_line_length=30`, `max_line_gap=8`) łapią przewody na realnych stronach — jak trzeba, zgłoś `## Poprawka`.

NIE robione w tej sesji: GraphBuilder (004), QET, trening YOLO.

---

## 2026-06-25 [ZW] — Prompt 002-ocr: PaddleOcrEngine (filar TEKST)

Temat: **OCR offline PaddleOCR — `extract_text` + `TextDetection`. Testy bez pobierania modeli.**

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `backend/recognize/ocr_engine.py` | `TextDetection` (dataclass: text, bbox=[x1,y1,x2,y2], confidence) + `PaddleOcrEngine.extract_text()` |
| `backend/tests/test_ocr_engine.py` | 5 testów: parsowanie 2 detekcji, pusta strona, linia malformed, guard braku biblioteki, degradacja kwargs |

### Decyzje techniczne

- **Leniwy import** `paddleocr` (wzór jak onnxruntime w `symbol_detector`). Brak biblioteki → `ImportError` z hintem `pip install paddlepaddle paddleocr`.
- **Konstruktor bez zmian** `PaddleOcrEngine(use_gpu=True)` — dodany opcjonalny `lang="en"` (default zgodny z GraphBuilder, który tworzy bez argumentów).
- **bbox**: PaddleOCR zwraca poligon 4-punktowy → rzut na prostokąt osiowy `[min x, min y, max x, max y]` w pikselach oryginału.
- **Tolerancja wersji PaddleOCR**: `_build_engine` próbuje kolejno `use_gpu/show_log` (2.x) → minimalne kwargi (3.x usunęło te argumenty). `_run_engine` preferuje `.ocr(cls=True)`, fallback `.predict()`.
- **Język/PL**: default `lang='en'`. Dla diakrytyków PL użyj `PaddleOcrEngine(lang='latin')` — model latin obejmuje polskie znaki. Do potwierdzenia na realnych stronach.

### Testy

```
pytest backend/tests labeler/tests  →  93 passed
```
(w sandboxie doinstalowane: pydantic, fastapi, opencv-headless, numpy, pyyaml, pillow, httpx, svgwrite, pytest)

### Filip — smoke u siebie (RTX 2080)

```powershell
pip install paddlepaddle-gpu paddleocr   # CPU: paddlepaddle paddleocr
python -c "from backend.recognize.ocr_engine import PaddleOcrEngine; import glob; e=PaddleOcrEngine(use_gpu=True); print(e.extract_text(glob.glob('data/raw/*.png')[0])[:5])"
```

Modele PaddleOCR pobierają się raz przy 1. uruchomieniu (online) — potem offline. [RYZYKO] runtime backend/recognize ma być offline: pobranie modeli to jednorazowy setup, nie cloud API w runtime.

### Nie ruszone

GraphBuilder.build (NotImplementedError — prompt 004), line tracer (PROMPT-CLAUDE-002-LINES), atlas QET.

---

## 2026-06-14 [ZW] — Prompt 008a: QET atlas extract → symbol-reference.yaml

Temat: **Parser `.elmt` QET + renderer PNG + builder YAML + testy (faza 008a DONE).**

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `backend/atlas/__init__.py` | pakiet |
| `backend/atlas/qet_parser.py` | parsowanie `.elmt` (XML): nazwy EN/PL, linie/rects/poly/terminale, bbox |
| `backend/atlas/qet_render.py` | render geometry → PNG 128×128 (Pillow, offline) |
| `backend/atlas/build_reference.py` | CLI: skan QET P0/P1/P2, dedup, YAML + crops |
| `backend/atlas/reference.py` | `load_symbol_reference()`, `lookup_by_id`, `lookup_by_alias` |
| `config/symbol-reference.yaml` | seed (3 fixture-symbole); po builderze → ≥80 wpisów |
| `backend/tests/test_qet_parser.py` | 11 testów parsera na fixture `.elmt` |
| `backend/tests/test_symbol_reference.py` | 11 testów YAML (struktura, unikalne ID, lookup) |
| `schema/fixtures/atlas/*.elmt` | 3 fixture: fuse, contactor, terminal_block |
| `data/atlas/crops/*.png` | crop-y PNG z fixture (128×128, commitujemy) |
| `docs/atlas-setup.md` | instrukcja klonowania QET + uruchomienia buildera |
| `backend/paths.py` | nowe stałe: `SYMBOL_REFERENCE`, `ATLAS_QET`, `ATLAS_CROPS` |

### Testy (PC ZW)

```
pytest backend/tests labeler/tests   →  49 passed (zero regresji)
```

### Twoje kroki (Filip — RTX 2080)

**Krok 1 — sklonuj QET (jednorazowo):**
```powershell
git clone --depth 1 https://github.com/qelectrotech/qelectrotech-elements.git data/atlas/qet
```

**Krok 2 — uruchom builder:**
```powershell
python -m backend.atlas.build_reference `
    --qet-dir data/atlas/qet `
    --out config/symbol-reference.yaml `
    --crops-dir data/atlas/crops
# Oczekiwany wynik: "Zbudowano 120 symboli → config/symbol-reference.yaml"
```

**Krok 3 — weryfikacja:**
```powershell
python -m pytest backend/tests/test_symbol_reference.py -v
# Oczekiwane: 11 passed
python -m backend.cli validate schema/fixtures/page1_expected.json
# Oczekiwane: approved: true (bez regresji)
```

**Krok 4 — commit po buildzie:**
```powershell
git add config/symbol-reference.yaml data/atlas/crops/
git commit -m "[Filip] atlas: QET build → symbol-reference.yaml (008a full)"
```

### Uwagi

- `data/atlas/qet/` już w `.gitignore` — surowa biblioteka QET poza repo (115 MB, GPL)
- Crop-y PNG z fixture (3 pliki, 128×128) commitujemy; pełne crops po Twoim buildzie
- Licencja: YAML i crop-y = pochodna GPL; atrybucja w `symbol-reference.yaml`→`meta.sources.license`
- Crop-y zrenderowane przez Pillow — cairosvg **nie wymagane**
- Następny prompt po 008a: **009 — picker symbol_id w labelerze**

---

## 2026-06-14 [ZW] — export_onnx: brak best.pt w data/runs — zlokalizuj lub przetrenuj

Auto-find zadziałał, ale w `data/runs` **nie ma** żadnego `best.pt`. Rozszerzyłem szukanie też o domyślny katalog ultralytics `runs/` (gdy trening nie dostał `project`). 10 testów OK.

**Krok 1 — zlokalizuj plik na całym dysku projektu:**
```powershell
Get-ChildItem -Recurse -ErrorAction SilentlyContinue -Filter best.pt |
  Sort-Object LastWriteTime -Descending | Select FullName, LastWriteTime
```
- **Jeśli się znajdzie** (np. `runs\detect\train\weights\best.pt`): `pull`, potem `python -m train.export_onnx` (samo go weźmie) **albo** wskaż: `... --weights "<pełna ścieżka>"`.
- **Jeśli pusto** (run wyczyszczony / usunięty przy `.gitignore runs/`): trzeba przetrenować ponownie — to ~17 epok, szybkie:
```powershell
.venv\Scripts\python.exe -m train.dataset_export
.venv\Scripts\python.exe -m train.train_symbols --epochs 30 --batch 8
.venv\Scripts\python.exe -m train.export_onnx
```
Mój `train_symbols` zapisuje do `data/runs/symbols_v1/` — po ponownym treningu auto-find trafi od razu.

> Podejrzenie: run zniknął przy commicie `gitignore venv311/runs/yolo` albo przez czyszczenie. Wagi i tak nie idą do repo, więc po prostu odtwórz je lokalnie.

---

## 2026-06-14 [ZW] — Fix export_onnx: auto-wyszukiwanie best.pt

`export_onnx` rzucał `FileNotFoundError` — ultralytics zapisał run pod auto-inkrementowaną nazwą (np. `symbols_v12`), nie pod stałym `symbols_v1`. Dodałem `find_best_weights()`: bierze domyślny run, a jeśli go nie ma — **najnowszy** `data/runs/**/weights/best.pt`. +2 testy (13 passed).

**Odpal ponownie (samo znajdzie wagi):**
```powershell
.venv\Scripts\python.exe -m train.export_onnx
#    wypisze "Wagi: ...\best.pt" + "ONNX: ...symbols_v1.onnx"
```
Gdyby trzeba wskazać ręcznie — najpierw zlokalizuj plik, potem `--weights`:
```powershell
Get-ChildItem -Recurse data\runs -Filter best.pt | Select FullName
.venv\Scripts\python.exe -m train.export_onnx --weights "data\runs\<run>\weights\best.pt"
```

---

## 2026-06-14 [ZW] — Prompty 006 + 001: export ONNX + inferencja symboli

Temat: **best.pt → ONNX + detektor YOLOv8 ONNX (offline).** Kod + pytest na ZW; export i inferencja GPU u Ciebie. Bazuje na BUILD M0 (mAP50≈0.04, 17 epok — overfit przy 9 stronach, zgodnie z przewidywaniem).

### Co zrobione (kod)

- **`train/export_onnx.py`** — `export_onnx()`: best.pt → ONNX (opset 12, zgodny z onnxruntime-gpu 1.17), kopia do `data/models/symbols_v1.onnx` + wpis do `registry.json` (`register_model`). Leniwy import ultralytics. CLI `--weights/--version/--opset/--imgsz`.
- **`backend/recognize/symbol_detector.py`** — `OnnxSymbolDetector.detect()`: session `["CUDAExecutionProvider","CPUExecutionProvider"]`, preprocess przez `resize_for_yolo` (BGR→RGB, CHW, /255), parsowanie wyjścia YOLOv8 `(1,4+nc,N)`, próg confidence, **NMS** (`cv2.dnn.NMSBoxes`), mapowanie bboxów z 640 → piksele oryginału, `class_id→class_name`. Leniwy import onnxruntime.
- **`backend/tests/test_symbol_detector.py`** — 3 testy (fake session, bez onnxruntime): mapowanie współrzędnych, filtr confidence, fallback nazwy klasy.
- **`train/tests/test_export_onnx.py`** — 2 testy: guard braku wag + zapis registry.

### Testy (PC ZW)

```
pytest backend/tests labeler/tests train/tests   →  35 passed
python -m backend.cli validate schema/fixtures/page1_expected.json  →  approved: true
```

> `*.onnx`, `best.pt`, `data/runs/` **NIE** w repo. Pipeline (`OfflineRecognizer`) czyta aktywny model z `registry.json` → po Twoim eksporcie sam podłączy `symbols_v1.onnx`.

### Uruchomienie u Filipa (RTX 2080, PowerShell)

```powershell
# 1. Export wytrenowanych wag do ONNX (uzywa data/runs/symbols_v1/weights/best.pt)
.venv\Scripts\python.exe -m train.export_onnx
#    → data/models/symbols_v1.onnx + aktualizacja data/models/registry.json (active=symbols_v1)

# 2. Smoke test inferencji na stronie spoza treningu (np. p016/p019 — walidacja generalizacji)
.venv\Scripts\python.exe -c "from backend.recognize.symbol_detector import OnnxSymbolDetector; d=OnnxSymbolDetector('data/models/symbols_v1.onnx', {'element':0}); print(len(d.detect('data/raw/SchematWRT01_p016.png')), 'detekcji')"
```

Przy mAP50≈0.04 spodziewaj się **mało/żadnych** trafień na stronach spoza treningu — to oczekiwane. Cel tego kroku: potwierdzić, że ścieżka ONNX→inferencja działa end-to-end. Realny skok jakości dopiero po doznaczeniu stron lub atlasie (008a). Daj znać ile detekcji wyszło na p016/p019.

---

## 2026-06-14 [ZW] — Prompt 005 (BUILD M0): dataset export + kod treningu YOLO

Temat: **Kod eksportu datasetu (SQLite→YOLO) + trening YOLOv8n.** Implementacja + pytest na PC ZW. **Pełny trening GPU robisz Ty (RTX 2080).**

> Uwaga: pierwsza wersja tego wpisu powstała na **starych plikach** (nasłuch pusha był zatrzymany). Po fast-forward do `origin/main` przeczytałem właściwy `sync/prompts/005-train-symbols.md` i dostosowałem kod (katalog `data/labeled/`, val = ostatnie strony p022/p023, pomijanie `test_*`, manifest, summary JSON, CLI `--epochs/--batch`).

### Co zrobione (kod)

- **`labeler/export.py`** — fix: `export_yolo` kopiuje teraz źródłowy PNG z `data/raw/` do `images/` (para image/label wymagana przez YOLO). Dodane helpery `yolo_label_lines()` i `find_raw_image()`.
- **`train/dataset_export.py`** — NOWY. SQLite → `data/labeled/{images,labels}/{train,val}` + `data.yaml` + `export-manifest.json`. Deterministyczny split (sort po `page_id`, **ostatnie** strony → val, val_ratio 0.2). Pomija strony `test_*` i rekordy bez PNG. CLI: `python -m train.dataset_export`.
- **`train/train_symbols.py`** — `train()` zaimplementowany: ultralytics YOLOv8n, leniwy import (testy nie wymagają torch/GPU), twardy limit `batch≤8` (8GB VRAM), run w `data/runs/symbols_v1/`, zapis `best.pt` + summary `data/models/symbols_v1_train_summary.json`. CLI z `--epochs/--batch/--imgsz/--device`. `register_model()` bez zmian.
- **`train/tests/test_dataset_export.py`** — NOWY. 6 testów na fixturach (atrapy PNG, tmp dir), bez GPU.

### Testy (PC ZW)

```
pytest backend/tests labeler/tests train/tests   →  30 passed
python -m backend.cli validate schema/fixtures/page1_expected.json  →  approved: true
```

> `best.pt`, `data/runs/`, wagi **NIE** idą do repo — trenujesz u siebie. `data/schemagen.db` i `data/raw/*.png` są w `.gitignore`, na ZW ich nie ma → nie odpalałem pełnego treningu ani eksportu na żywej bazie.

### Uruchomienie u Filipa (RTX 2080, PowerShell)

```powershell
# 0. (raz) zależności GPU
pip install -e ".[gpu]"

# 1. PNG źródłowe w data/raw/ (SchematWRT01_p*.png), adnotacje już w data/schemagen.db

# 2. Batch eksport SQLite → YOLO train/val + kopie PNG
python -m train.dataset_export
#    → data/labeled/{images,labels}/{train,val} + data.yaml + export-manifest.json
#    wg promptu: 9 stron, val = p022, p023 (ostatnie); ~394 bboxy, klasa: element
#    wypisze: Dataset: train=N val=M klasy=1 -> ...data.yaml

# 3. Trening (batch twardo ograniczony do 8)
python -m train.train_symbols --epochs 30 --batch 8
#    → best.pt w data/runs/symbols_v1/weights/best.pt
#    → summary w data/models/symbols_v1_train_summary.json (dopisz mAP do sync, jeśli chcesz)

# 4. (prompt 006) export best.pt → ONNX — jeszcze NotImplemented, osobne zadanie
```

9 stron to mało — spodziewaj się overfittu. Po treningu wrzuć metryki z summary (map50) — dostroję split/augmentacje albo damy zielone na doznaczanie kolejnych stron.

---

## 2026-06-14 [ZW] — Prompt 007: analiza źródeł wiedzy (runda 1–4)

Temat: Ocena 3 źródeł + werdykt o archiwum EPLAN + strategia treningu. **Research, bez kodu.**

Deliverable: [`docs/knowledge-sources-analysis.md`](../docs/knowledge-sources-analysis.md) (v4) + [`docs/qet-library-report.md`](../docs/qet-library-report.md) (raport z pobranej biblioteki QET) + uzupełniony [`sync/sources-inbox.md`](sources-inbox.md).

3 rekomendacje (do review):
- **Atlas warstwowy**, nie jedno źródło: (1) **IEC 60617** PDF = baza normatywna, (2) **QElectroTech** = przemysł generyczny + Siemens (pobrane 8732 symbole, GPL, `.elmt`/XML), (3) **producent** = `.edz` z EPLAN Data Portal, później.
- **Trening Siemens-first.** WRT01 ma sterowniki **GE Vernova (brak w QET)** + **Phoenix Contact (13, rdzeń brak)** → uczymy klas generycznych (`relay`, `fuse`, `terminal_block`, `plc_io_module`) na komponentach Siemens (452 QET) + generyki; GE/Phoenix dochodzą później mapowane na te klasy. Nie blokuje startu.
- **Archiwum `eplan-era-2026-06.zip` = NIE źródło symboli** (kod C# + baza wiedzy API, zero makr). Dało tylko typy plików do szukania u producenta: `.edz` / `.ema` / `.ems`.

Do decyzji Cursor:
- Akceptacja kierunku „atlas warstwowy + Siemens-first"?
- Prompt **008-symbol-atlas-extract** (layout-aware ekstrakcja IEC 60617 PDF + parser `.elmt` QET, filtr Siemens+generyki → `config/symbol-reference.yaml` + `data/atlas/`). [RYZYKO] do rozwiązania: parowanie obraz↔opis w PDF; dedup IEC↔QET; aliasy PL tylko ~34% w QET.
- Licencje [do potwierdzenia Filip]: GPL QET vs licencja SchemaGen; redystrybucja crop-ów IEC 60617.

Otwarte pytania do Filipa — sekcja na końcu `knowledge-sources-analysis.md`.

---

## 2026-06-14 [ZW] — Prompt 003: hierarchia bboxów + relacje przestrzenne

Temat: Zaimplementowana warstwowa hierarchia bboxów (parent/depth/rel_bbox) + relacje przestrzenne. YOLO bez zmian.

Co zrobiłem:
- **Modele** (`backend/models/label.py`, `schema.py`): `BboxAnnotation`/`Component` mają teraz `parent_id`, `depth`, `rel_bbox`; nowy model `SpatialRelation`; `spatial_relations[]` na `LabelRecord` i `SchemaModel`. Wszystko opcjonalne (backward compatible).
- **Geometria** (`backend/geometry/bbox_layout.py`, nowy — źródło prawdy): czyste funkcje `contains` (zawieranie ścisłe, EPS=1px), `find_parent` (min. powierzchnia, remis po id), `compute_hierarchy`, `compute_spatial_relations` (contains rodzic→dziecko + kompas między rodzeństwem wg centroidów), `enrich_label_record`.
- **API** (`labeler/app.py`): POST woła `enrich_label_record` **przed** zapisem, zwraca `hierarchy_depth_max`; GET migruje stare rekordy w locie (np. `SchematWRT01_p013`).
- **Eksport** (`labeler/export.py`): `parent_id`/`depth`/`rel_bbox` → `Component`, `spatial_relations` → `SchemaModel`; enrich gdy relacje puste; YOLO **bez zmian** (wszystkie bboxy).
- **UI** (`labeler/static/app.js?v=13`): JS-lustro `recomputeHierarchy()` (ta sama logika contains + min area) po `mouseup` / `removeBboxAt` / wczytaniu strony; accordion z wcięciem wg `depth` + `↳ w #<rodzic>`; zaznaczone dziecko → żółta przerywana obwódka rodzica na canvas; drzewiaste sortowanie listy; payload rozszerzony. Auto-zapis/localStorage/pageCache (v12) **nietknięte** — tylko rozszerzone.
- **Schema JSON** (`schema/schema-model.json`): nowe pola opcjonalne.
- **Docs** (`docs/labeling-guide.md`): sekcja „Oznaczanie warstwowe".

Testy: nowy `backend/tests/test_bbox_layout.py` (7) + rozszerzony `labeler/tests/test_export.py` (hierarchia w schema + YOLO zachowuje oba bboxy). `pytest backend/tests labeler/tests` → **24 passed**. `python -m backend.cli validate schema/fixtures/page1_expected.json` → approved.

Jak testować ręcznie:
```
python -m labeler.app   # localhost:8765
```
1. Narysuj duży bbox-blok, potem mniejszy w środku.
2. Zapisz → w DevTools/Network POST `/api/annotations`: dziecko ma `parent_id` bloku, `depth=1`, `rel_bbox`.
3. Odśwież → hierarchia wczytana, accordion z wcięciem i `↳ w #<rodzic>`.
4. Zaznacz dziecko → żółta przerywana obwódka rodzica na canvas.
5. Eksport → `*.schema.json` ma `spatial_relations` (contains + kompas).
6. `labels/*.txt` (YOLO) nadal ma **oba** bboxy.

Commit: `[Claude] labeler: bbox hierarchy + spatial relations (prompt 003)`

---

## 2026-06-14 [ZW] — Prompt 001: canvas bbox labeler

Temat: Zaimplementowany interaktywny canvas bbox w `labeler/static/app.js`.

Co zrobiłem:
- Rysowanie bbox: mousedown → mousemove → mouseup (preview dashed rect podczas ciągnięcia)
- Aktywna klasa z listy (`config/symbol-classes.yaml`), klawisze 1–9 + klik na liście
- Zoom: scroll na canvas (zoom do punktu kursora)
- Wyświetlanie istniejących bbox po załadowaniu strony (GET `/api/annotations/{page_id}`)
- Zaznaczanie bbox kliknięciem (highlight w list + dashed outline na canvas)
- Del/Backspace — usuwa zaznaczony bbox
- Zapis POST `/api/annotations`, eksport YOLO
- Każdy bbox dostaje unikalny id = `{class}_{timestamp}`

Jak testować ręcznie:
```
python -m labeler.app   # localhost:8765
```
1. Załaduj dowolną stronę z listy.
2. Wybierz klasę (klawisze 1–9 lub klik na liście).
3. Narysuj 3 bbox na canvas.
4. Zaznacz jeden bbox i wciśnij Del — powinien zniknąć.
5. Scroll — zoom do kursora.
6. Kliknij „Zapisz" → alert „Zapisano ✓".
7. Odśwież stronę — bbox powinny się wczytać z powrotem.
8. Kliknij „Eksport YOLO + JSON".

Testy automatyczne: `pytest labeler/tests backend/tests` → 14 passed.

Commit: `[Claude] labeler: canvas bbox (prompt 001)`

---

## 2026-06-13 [ZW] — Plan B: globalny FUNC_COUNTER (MA1+MA2)

Temat: Plan A (CONFIGSCHEME) odrzucony po Twoim teście. Wdrożony Plan B — wymuszenie licznika w add-inie.

Co zmieniłem:
- Nowa akcja `SchemaGenForceGlobalCounter` (`scripts/addin/Actions/ForceGlobalCounterAction.cs`) — kolejnym silnikom (FUNC_CODE=MA) nadaje MA1, MA2... przez `NameParts.FUNC_COUNTER` (Transaction+SafetyPoint). NIE rusza `<20010>`. Build CS0266 naprawiony (getter zwraca `FunctionBasePropertyList`).
- `config/numbering-rules.xml`: reguła MA → `configScheme=""` + `forceGlobalCounter="true"`.
- `SchemaGen_MVP.cs`: pass 2 woła nową akcję dla reguł z flagą; guard wymusza reload DLL.

Do zrobienia po stronie Filip:
1. `.\scripts\build_addin.ps1` (powinno przejść — sprawdź 0 błędów).
2. Skopiuj `SchemaGen_MVP.cs` + `config/numbering-rules.xml` → `Skrypty\Schemagen\config\`.
3. Przeładuj DLL (pojawi się `SchemaGenForceGlobalCounter`), świeży Hello_world, uruchom MVP.
4. Sprawdź: `-MA1` na +B2, `-MA2` na +B4; FC bez zmian; `output/force-global-counter.json` → `changed==total`, brak `ERR` w `log`; layout bez regresji.
5. Jeśli `ERR` w logu (NameParts) → przyślij `force-global-counter.json`, mam alternatywę (świeży `FunctionBasePropertyList` z plant/location/code).

Commit: (auto GitSync po push)

---

## 2026-06-13 [ZW]
Temat: Uruchomiona magistrala koordynacji.
Kontekst: Dodałem `GitSyncDaemon.ps1`, `Install-GitSyncTask.ps1` i katalog `sync/`. Po Twojej stronie zarejestruj daemon (patrz `docs/git-sync-setup.md`).
Do zrobienia po stronie Filip: uruchom `Install-GitSyncTask.ps1 -MachineTag Filip -RepoPath "C:\Users\Filip\Desktop\Cursor\SchemaGen"`.
Commit: —
