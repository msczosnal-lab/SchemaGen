# Skrzynka: ZW → Filip

> Pisze **tylko ZW** (Cowork/Claude). Filip czyta na starcie sesji i nie edytuje tego pliku.
> Najnowsze wpisy na górze.

---

## 2026-06-14 [ZW] — Prompt 005 (BUILD M0): dataset export + kod treningu YOLO

Temat: **Kod eksportu datasetu (SQLite→YOLO) + trening YOLOv8n.** Implementacja + pytest na PC ZW. **Pełny trening GPU robisz Ty (RTX 2080).**

### Co zrobione (kod)

- **`labeler/export.py`** — fix: `export_yolo` kopiuje teraz źródłowy PNG z `data/raw/` do `images/` (para image/label wymagana przez YOLO). Dodane helpery `yolo_label_lines()` i `find_raw_image()`.
- **`train/dataset_export.py`** — NOWY. SQLite → struktura YOLO `images/{train,val}` + `labels/{train,val}` + `data.yaml`. Deterministyczny split (sort po `page_id`), domyślnie val_ratio 0.2 (przy 1 stronie ta sama w train i val). Pomija rekordy bez PNG.
- **`train/train_symbols.py`** — `train()` zaimplementowany: ultralytics YOLOv8n, leniwy import (testy nie wymagają torch/GPU), twardy limit `batch≤8` (8GB VRAM), zapis best.pt + metryki. `register_model()` bez zmian.
- **`train/tests/test_dataset_export.py`** — NOWY. 6 testów na fixturach (atrapy PNG, tmp dir), bez GPU.

### Testy (PC ZW)

```
pytest backend/tests labeler/tests train/tests   →  30 passed
python -m backend.cli validate schema/fixtures/page1_expected.json  →  approved: true
```

> Uwaga: `best.pt` **NIE** jest w repo — trenujesz u siebie. `data/schemagen.db` i `data/raw/*.png` są w `.gitignore`, na ZW ich nie ma → nie odpalałem pełnego treningu.

### Komendy dla Ciebie (Filip, RTX 2080, PowerShell)

```powershell
# 0. (raz) zależności GPU
pip install -e ".[gpu]"

# 1. Oznacz/wyeksportuj strony w labelerze (działa już na :8765) — adnotacje lądują w data/schemagen.db
#    Upewnij się, że PNG-i są w data/raw/

# 2. Zbuduj dataset YOLO z bazy (SQLite → train/val + kopie PNG)
python -m train.dataset_export
#    → tworzy data/dataset/{images,labels}/{train,val} + data/dataset/data.yaml
#    wypisze: Dataset: train=N val=M klasy=K -> ...data.yaml

# 3. Trening (batch jest twardo ograniczony do 8)
python -m train.train_symbols
#    lub z parametrami:
python -c "from train.train_symbols import train; print(train(epochs=50, batch=8, imgsz=640, device=0))"
#    → best.pt w data/models/runs/symbols/weights/best.pt

# 4. (prompt 006) export do ONNX — jeszcze NotImplemented, osobne zadanie
```

Jeśli masz mało oznaczonych stron (3–5), zacznij od `epochs=50` i sprawdź czy nie ma overfittu na val. Daj znać metryki (map50) — dostroję split / augmentacje.

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
