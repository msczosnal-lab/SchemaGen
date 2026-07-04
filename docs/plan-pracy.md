# Plan pracy SchemaGen — całościowy

**Data:** 2026-06-20
**Podstawa:** [`schematic-interpretation.md`](schematic-interpretation.md) — trzy filary + relacje.
**Cel końcowy:** skan schematu → `SchemaModel JSON` (komponenty + tekst + połączenia + relacje), offline.

---

## Gdzie jesteśmy

- **Filar Symbole:** DONE runtime (YOLO multi-class, listwa 011, mostek D4 012, tiling 014). GT w budowie (Filip).
- **Filar Tekst:** DONE — `PaddleOcrEngine` (prompt 002).
- **Filar Połączenia:** DONE — line tracer, net-builder, terminale, mostki (`--rebuild-conn` p040=15).
- **Faza 5 Relacje:** WIP — prompt 015 (`RelationResolver`: tekst→symbol, potencjały, context runtime).
- **Wąskie gardło:** jakość relacji OCR↔symbol na runtime; walidacja e2e per filar (Faza 6).

---

## Fazy

### Faza 0 — GT symboli (TERAZ, Filip) — w toku

**Cel:** baza bboxów ze skanów, wystarczająca do stabilnej detekcji multi-class.

Kroki:
1. Labeluj dalej Adamed AGV SA2, potem INTEROL SA1, Norblin Cars.
2. **Priorytet na klasy rzadkie** (<20 instancji): `styki_nc`(5), `ekranowanie_kabla`(5), `polaczenie_przewodow`(6), `emergency_stop`(6), `push_button`(7) — te zaniżają mAP i wypadają z treningu przy `min-count=5`.
3. Cel ilościowy: **min. 20–30 instancji/klasa** zanim klasa wejdzie sensownie do treningu.
4. Świadomie odpuść klasy, których nie ma w korpusie (`motor`, `enkoder` itp.) — nie trać czasu.

Exit: każda klasa docelowa ≥20 instancji, ≥3 projekty w GT (różnorodność rysownika/biura).

---

### Faza 1 — Domknięcie detekcji symboli

**Cel:** stabilny recall na gęstych rzędach + rozsądne AP na klasach rzadkich.

Kroki:
1. **Baseline v5** — eksport ONNX (imgsz=1280!) + `preview_batch` na rzędzie 16 złączek. Zapisz recall jako punkt odniesienia.
2. **A/B v6 z flipem** — `--fliplr 0.5 --flipud 0.5` (bezpieczne: klasy rozróżnia relacja linia↔grot, nie kierunek). Porównaj confusion matrix.
3. **Jeśli gęste rzędy nadal gubią:** podnieś imgsz inferencji (1536) lub przejdź na **yolov8s**.
4. **Jeśli mylą się strzałki wej/wyj:** rozważ crop-classifier 2. stopnia (YOLO lokalizuje „strzałka", binarny model rozsądza wej/wyj).
5. **NMS:** per-klasa + `iou≈0.55` w `symbol_detector.py` (teraz class-agnostic → ryzyko tłumienia sąsiadów).

Exit: recall `zlaczka` na gęstym rzędzie ≥95%; AP klas rzadkich > 0.

Pliki: `train/train_symbols.py`, `train/export_onnx.py`, `backend/recognize/symbol_detector.py`, `scripts/preview_batch.py`.

---

### Faza 2 — Akcelerator GT: crop-review (active learning)

**Cel:** szybciej budować GT rzadkich klas, mniejszym nakładem niż pełny labeling.

Założenia (z ustaleń): **tylko wycinek symbolu**, accept / reject / zmień-klasę, lokalnie.

Kroki:
1. Tryb review w istniejącym `labeler/` — predykcje jako wstępne bboxy.
2. Queue: **pasmo niepewności 0.15–0.5** (nie dno `p<0.1`) + priorytet rzadkich klas.
3. **Dedup + cap per klasa** (np. `zlaczka` max 300, rzadkie: wszystko) — przy dużym korpusie redundancja, nie brak danych, jest wąskim gardłem.
4. Margines cropa +30%/+15 px (żeby ocenić relację linia↔grot).
5. Round-trip: accept → YOLO txt → `dataset_export` → re-train.

Status: **opcjonalny**, włączyć gdy ręczny labeling stanie się wąskim gardłem. Hosting zewnętrzny/płatni recenzenci — dopiero po anonimizacji i kontroli jakości (gold questions). **[RYZYKO]** poufność schematów klientów.

---

### Faza 3 — Filar Tekst (OCR)

**Status:** ✅ DONE (prompt 002).

### Faza 4 — Filar Połączenia

**Status:** ✅ DONE (prompty 002/003/004, net-builder, terminale, mostki).

### Faza 5 — Warstwa relacji → SchemaModel

**Status:** ⏳ WIP (prompt 015 — `RelationResolver`).

**Cel:** dopięcie tekstu do symboli/połączeń, scalanie strzałek potencjału, `context_assignments` runtime.

Kroki:
1. `015-relations-layer` — `RelationResolver` w `backend/recognize/`.
2. Eksport `SchemaModel JSON` z wypełnionymi relacjami (kontrakt bez zmian).
3. `backend.cli validate` na fixture.

Exit: tagi instancji na runtime p040; strzałki potencjału scalone; `Connection.potential` z OCR.

---

### Faza 5 (archiwum planu) — Warstwa relacji (oryginalna spec)

**Cel:** złożenie filarów w graf logiczny.

Kroki:
1. `004-graph-builder` — relacje:
   - tekst → symbol (bliskość geometryczna, IEC 81346-1),
   - symbol → symbol (linia wire/bus łączy brzeg/terminal A z B),
   - tekst → połączenie (potencjał, etykieta przewodu).
2. Eksport `SchemaModel JSON` (kontrakt — **bez zmian sygnatury bez zgody**).
3. `backend.cli validate` na fixture.

Exit: `validate schema/fixtures/page1_expected.json` przechodzi.

---

### Faza 6 — Walidacja end-to-end

**Cel:** pierwszy pełny schemat skan → SchemaModel, z metryką.

Kroki:
1. Pełny pipeline na 1 kompletnym projekcie (np. WRT01 / Stanley — DONE w GT).
2. Metryki per filar + manualny przegląd wyniku.
3. Decyzja: które filary wymagają dodatkowych danych.

---

## Tory równoległe

| Tor | Kto | Zakres |
|-----|-----|--------|
| GT (labeling, priorytet rzadkie klasy) | Filip | Faza 0 — ciągły |
| Trening + detekcja + eval | Filip + Cowork | Faza 1 |
| Ingest / cropy / infra | Cursor | `011-ingest-batch`, `011-bbox-crops` |
| OCR / linie / graf (stuby → implementacja) | Cowork | Fazy 3–5 |

---

## Zasady przekrojowe

1. **Trening tylko ze skanów Filipa** — żadnych bibliotek CAD (QET, IEC PDF) jako obrazów treningowych.
2. **Eval per-klasa, nie ogólny mAP** — mAP zdominuje `zlaczka` (998 vs ~5–20 na klasach rzadkich).
3. **Wersjonowanie modeli** — czyste nazwy biegów (`_v5`, `_v6_flip`), pilnuj auto-sufiksów ultralytics (`-2`) przy eksporcie.
4. **Eksport ONNX = imgsz treningu** — niezgodność (640 vs 1280) kasuje zysk z wysokiej rozdzielczości.
5. **Nie zmieniać bez zgody:** sygnatury `backend/protocols/`, kontrakt `SchemaModel JSON`, modele Pydantic.

---

## Kolejność (skrót)

GT symboli (rzadkie klasy) → domknięcie detekcji (v5/v6, NMS, ew. yolov8s) → [opc. crop-review] → OCR → linie/tracer → graph builder → walidacja pełnego schematu.
