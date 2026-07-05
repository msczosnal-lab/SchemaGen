# Zadanie 022: Labeler grafowy v2 — bbox + linie OD-DO

**Status:** AKTYWNE — implementacja (Claude Cowork)
**Model:** Sonnet/Opus, effort High
**Zależność:** 018-lines-quality ✅; reguły terminali z 018-terminals-strategy (wzorce klas) — ale NIE kopiujemy Hougha do GT
**Zastępuje:** plan Cursora „Prompt 020 labeler v2" (kolizja numeracji z 020-diff-score; poprawki wg review Claude 2026-07-05)

## Kontekst

Decyzja Filipa: jeden prawidłowy układ — GT opisuje docelowy stan grafu (symbole, terminale, linie OD-DO), runtime ma do niego dążyć. Labeler nie symuluje Hougha, tylko rysuje wynik końcowy. Obecne 5 trybów i 3 niezależne warstwy GT (bbox / linie-role / connections ręczne-lub-net_builder) powodują drift GT↔runtime (p027/p040).

**Decyzja domenowa (Filip, 2026-07-05):** BEZ węzłów junction (linia→linia). Szyna listwy = złączki zwarte mostkami: złączka ma do 4 terminali — `left 0.5` + `right 0.5` (tor szyny, połączenia `kind: link` między sąsiadami) oraz `top 0.5` / `bottom 0.5` (odczepy). Każda linia zawsze OD terminalu DO terminalu. Potencjał szyny wynika z domknięcia przechodniego połączeń `link` na etapie kompilacji.

## Krok 0 — remap ID w diff (PRZED labelerem; to urealnia score natychmiast)

[BŁĄD dzisiejszy] `diff_connections` porównuje dokładne stringi `from/to`. Runtime nadaje `sym_{i}` (graph_builder.py:83), GT ma własne id labelera — zbiory się nie przecinają, score connections jest strukturalnie zaniżony.

Implementuj w `backend/validate/diff_metrics.py`:

1. `pair_components(gt, runtime)` — parowanie po IoU bbox (próg jak diff_components, greedy po malejącym IoU, 1:1).
2. Translacja adresów runtime `sym_i:t` → id GT przed porównaniem connections; terminal dopasowany po pozycji absolutnej (tol z `runtime.yaml`), nie po id.
3. Connections niesparowanych komponentów → only_gt/only_runtime jak dotąd.
4. Test: syntetyczny GT + runtime z innymi id, te same połączenia → F1 = 1.0.
5. **Ciągłość historii:** po zmianie uruchom `diff_gt_runtime.py --page p027` i `--page p040`, wpisz delty i przyczynę do `sync/zw-to-filip.md` (historia jsonl musi mieć wyjaśniony skok).

## Format GT — SchematicGraph (źródło prawdy)

NOWY `backend/models/schematic_graph.py` (Pydantic, `version: 2`). SQLite: nowa tabela `schematic_graph` (LabelRecord zostaje, adapter kompiluje oba do SchemaModel).

```yaml
version: 2
page_id: p027
image_width: 4963      # wymagane — eksport YOLO
image_height: 3509
symbols:
  - id: sym_k1
    type: cewka_przekaznika
    tag: "-K1"                 # opcjonalny string; warstwa tekstu = faza tekstowa, nie tu
    bbox: [x1, y1, x2, y2]     # px absolutne
    terminals:
      - id: "1"
        x: 0.0                 # JEDNA reprezentacja: x,y ∈ [0,1] wzgl. bboxa,
        y: 0.5                 # na obrysie: x∈{0,1} lub y∈{0,1} ± tol (walidacja)
        name: ""
lines:
  - id: L323
    from: sym_k1:1             # {symbol_id}:{terminal_id}
    to: sym_mostek_12:3
    vertices: [[x0,y0], ...]   # ortho H/V; pierwszy/ostatni = pozycja terminala (snap)
    kind: power                # ConnectionKind z SchemaModel: power|signal|pe|control|link|other
```

Reguły walidacji (wspólne GT + docelowo runtime; `labeler/graph_validate.py`):

1. Terminal na obrysie bboxa (nie w środku).
2. `vertices` tylko osiowe, kąty 90°; snap końców do terminali (tol z `runtime.yaml`).
3. `from`/`to` muszą istnieć; linia bez terminali = błąd (odpowiednik `connection_require_terminal: true`).
4. Jedna linia = jedno logiczne połączenie. Brak osobnego trybu „connection".
5. `vertices` może być puste → auto-routing ortho (L-kształt) przy zapisie; edytowalne. Netlista (kto-z-kim) jest pierwszorzędna, geometria drugorzędna.
6. Linie dekoracyjne (frame, device_stroke) — poza fazą 1.

## Kompilacja — `labeler/graph_compile.py`

SchematicGraph → SchemaModel, deterministycznie:

1. `symbols` → `components[]` (+ `terminals[]` bez zmian formatu — x,y już zgodne).
2. `lines` → `graphic_lines[]` (role=wire, points=vertices po auto-routingu) + po jednym `Connection` (from/to/kind).
3. Potencjały: domknięcie przechodnie po połączeniach `kind: link` → wspólny `potential` dla terminali toru szyny (nazwa `POT_n` lub z tagu złączki skrajnej).
4. Zastępuje rozdzielone `label_to_schema` + ręczne connections dla rekordów v2; eksport YOLO bez zmian (bboxy z symbols).
5. `labeler/graph_serialize.py` — dump tekstowy („lista Filipa"):
   `bbox: cewka_przekaznika [-K1]; terminal_1 @ (0.0,0.5) → L323`
   `line: L323 OD sym_k1:1 DO sym_mostek_12:3; załamania: (1200,450)→(1200,300); kind=power`

## UI labelera v2

Stary kod → `labeler/legacy/`. Jeden labeler na :8765. Dwa tryby + podtryb (Bbox ⇄ [B/L] ⇄ Linia; zaznaczony bbox → edycja terminali; Esc wraca).

**BboxMode:** rysowanie prostokąta; klasa z `config/symbol-classes.yaml` + paleta/hasło (jak `api/symbol-palette`); klik na krawędź zaznaczonego bboxa → terminal (Del usuwa).

**LineMode:** klik terminal źródłowy → ortho vertices (Shift=free wyłączony) → klik terminal docelowy → zapis, auto-ID `L###`, wybór kind (domyślnie power; `link` dla mostków szyny). Panel: lista `L323: sym_k1:1 → sym_mostek_12:3`.

**Prefill (PIERWSZOPLANOWE — dźwignia wydajności GT):** przycisk „Import draft": bboxy z YOLO ONNX + terminale z wzorców klas (`terminal-patterns.yaml` z 018-terminals; dla `zlaczka`: left/right 0.5 required, top/bottom optional). Człowiek koryguje bboxy i rysuje TYLKO linie. Bez importu linii z Hougha — nigdy.

**Wizualizacja:** bbox pomarańczowy, terminale żółte kropki z id, linie zielone z podświetlonymi końcami OD/DO. Brak trybów review/crop/connection.

## API (`labeler/app.py`)

| Endpoint | Opis |
|---|---|
| GET/POST `/api/graph/{page_id}` | SchematicGraph JSON |
| GET `/api/graph-rules` | progi ortho/snap/tol z runtime.yaml |
| POST `/api/graph/validate` | walidacja przed zapisem |
| GET `/api/graph/{page_id}/dump` | lista tekstowa |
| POST `/api/graph/{page_id}/prefill` | draft bbox+terminale (YOLO + patterns) |

`/api/pages` zostaje; `/api/annotations` → adapter v1 (deprecated).

## Migracja

`scripts/migrate_label_v1_to_graph.py`: bbox+terminale+linie wire+connections → linie OD-DO; raport niejednoznaczności (linia bez pary terminali → do ręcznej decyzji, nie zgaduj). Uruchom na p027 i p040; test akceptacji: score diff po migracji porównywalny (delta wyjaśniona w raporcie).

## Testy akceptacji

| Test | Plik |
|---|---|
| Remap ID w diff (krok 0) | `backend/tests/test_diff_id_remap.py` |
| Model roundtrip | `backend/tests/test_schematic_graph.py` |
| Walidacja ortho/snap/obrys | `backend/tests/test_graph_validate.py` |
| Kompilacja → SchemaModel + potencjał z link | `labeler/tests/test_graph_compile.py` |
| API zapis/odczyt/prefill | `labeler/tests/test_graph_api.py` |
| Ręczny: 2 bboxy, 2 terminale, 1 linia → dump + 1 Connection | smoke Filipa |

Smoke Filipa:

```
.\.venv311\Scripts\python.exe -m labeler.app
# :8765 — prefill → korekta bbox → linia OD-DO → zapis → dump
python scripts/diff_gt_runtime.py --page p040 --json   # GT kompilowane z grafu
```

## Zakazy (schemagen.mdc)

1. Brak cloud API w `labeler/`, `backend/recognize/`.
2. Kontrakt `SchemaModel` nietknięty (tylko kompilacja DO niego).
3. Bez OCR/tekstu (osobna faza), bez GPU/treningu YOLO.
4. Nie ruszać `_lines_joined` / `_point_at_node` w runtime.

## Kolejność implementacji

1. Krok 0: remap ID w `diff_metrics` + test + rerun p027/p040
2. Pydantic `SchematicGraph` + `graph_validate`
3. `graph_compile` → SchemaModel (+ potencjał z link) + testy
4. API CRUD + SQLite + prefill
5. Canvas: bbox + terminale na obrysie
6. Canvas: linia OD-DO ortho + kind
7. Panel listy + dump
8. Migrator v1 + `docs/labeler-graph-rules.md`
9. Legacy: stare tryby do `labeler/legacy/`

## Po zakończeniu

1. `pytest backend/tests labeler/tests`
2. Wpis w `sync/zw-to-filip.md` (pliki, testy, delty score p027/p040)
3. `sync/commit-message.txt` = `[Claude] labeler: graph v2 bbox+linie OD-DO, remap ID w diff (prompt 022)`

## Faza następna (023, osobny prompt — NIE w tym zadaniu)

`023-runtime-graph-alignment`: GraphBuilder emituje ten sam graf/compile-path zamiast inferować Connection z net_builder; wchłania reguły 018-terminals (wzorce klas, węzły na ścieżce). Bez 023 diff nadal karze heurystyki — 022 daje wzorzec GT i uczciwą metrykę.
