# Zadanie 003: labeler — hierarchia bboxów i relacje przestrzenne

**Status:** OPEN — priorytet przed 002-labeler-lines-colors  
**Model:** Sonnet, effort **High**  
**Pliki główne:**
- `backend/geometry/bbox_layout.py` (nowy)
- `backend/models/label.py`, `backend/models/schema.py`
- `schema/schema-model.json`
- `labeler/app.py`, `labeler/export.py`
- `labeler/static/app.js`, `labeler/static/index.html`, `labeler/static/style.css`
- `backend/tests/test_bbox_layout.py` (nowy)
- `labeler/tests/test_export.py` (rozszerzyć)
- `docs/labeling-guide.md` (krótka sekcja)

## Kontekst (od Filipa)

Filip oznacza schematy **warstwowo**:
- duży bbox-blok (np. „Blok zasilania RUPS1”),
- mniejsze bboxy **w środku** (rozłącznik, symbol, tag `-11`, cyfry).

Dziś każdy bbox to płaski wpis — brak informacji, że bbox B jest **wewnątrz** bboxa A i jak elementy leżą względem siebie. To ma trafić do JSON/schema jako ground truth do nauki.

**Eksport YOLO:** bez zmian — **wszystkie** bboxy idą do `labels/*.txt` (Filip świadomie akceptuje nakładanie się). Hierarchia tylko w JSON.

Labeler ma już: canvas bbox, accordion, auto-zapis stron, localStorage (`app.js?v=12`). Nie psuj tego.

## Cel

Po narysowaniu bboxa wewnątrz innego system automatycznie:
1. wykrywa rodzica (najmniejszy bbox w pełni zawierający nowy),
2. zapisuje `parent_id`, `depth`, `rel_bbox` (pozycja względem rodzica, 0–1),
3. generuje `spatial_relations` (contains + left_of/right_of/above/below między rodzeństwem),
4. pokazuje hierarchię w UI (wcięcie, podgląd rodzica na canvas).

---

## 1. Modele danych

### `backend/models/label.py`

Rozszerz `BboxAnnotation`:

```python
parent_id: str = ""
depth: int = 0
rel_bbox: list[float] = Field(default_factory=list)  # [rx, ry, rw, rh] względem rodzica
```

Nowy model:

```python
SpatialRelation(BaseModel):
    from_id: str
    to_id: str
    relation: Literal["contains", "left_of", "right_of", "above", "below"]
```

W `LabelRecord` dodaj:

```python
spatial_relations: list[SpatialRelation] = Field(default_factory=list)
```

### `backend/models/schema.py`

Rozszerz `Component`: opcjonalne `parent_id`, `depth`, `rel_bbox`.  
Rozszerz `SchemaModel`: `spatial_relations: list[SpatialRelation]`.

### `schema/schema-model.json`

Dopisz nowe pola jako **opcjonalne** (backward compatible).

> Ten prompt **jawnie** obejmuje modele — wyjątek od ogólnego zakazu w `docs/claude-cowork-instructions.md`.

---

## 2. Geometria — `backend/geometry/bbox_layout.py`

Nowy moduł z czystymi funkcjami (100% pokryte testami):

| Funkcja | Opis |
|---------|------|
| `contains(outer, inner) -> bool` | Strict containment (inner w całości w outer) |
| `find_parent(bbox, others) -> str \| None` | Kandydaci: contains; wybór: **min. powierzchnia** |
| `compute_hierarchy(bboxes)` | Ustawia `parent_id`, `depth`, `rel_bbox` dla każdego |
| `compute_spatial_relations(bboxes)` | `contains` (rodzic→dziecko) + compass między **rodzeństwem** (wspólny `parent_id`, centroidy) |
| `enrich_label_record(record) -> LabelRecord` | Entry point: hierarchy + relations na całym rekordzie |

**Reguły:**
- Containment **ścisły** — częściowe nachodzenie ≠ rodzic.
- `depth`: 0 = korzeń, +1 na poziom w dół.
- `rel_bbox`: `(x-px)/pw`, `(y-py)/ph`, `w/pw`, `h/ph` względem bboxa rodzica; `[]` gdy brak rodzica.
- Przy usunięciu rodzica (w JS): przy następnym `recompute` dzieci dostają dziadka lub `parent_id=""`.

Dodaj `backend/geometry/__init__.py` jeśli brakuje.

---

## 3. API — `labeler/app.py`

**POST `/api/annotations`:**
1. Przyjąć payload.
2. `record = enrich_label_record(body.record)` **przed** `save_annotation`.
3. Odpowiedź: `status`, `page_id`, `bbox_count`, opcjonalnie `hierarchy_depth_max`.

**GET `/api/annotations/{page_id}`:**
- Po odczycie z DB: jeśli brak `parent_id` w starych danych → `enrich_label_record` on-the-fly (migracja w locie dla np. `SchematWRT01_p013`).

---

## 4. Eksport — `labeler/export.py`

- `label_to_schema()`: mapuj `parent_id`, `depth`, `rel_bbox` na `Component`; przenieś `spatial_relations` na `SchemaModel`.
- `export_yolo()`: **bez zmian** — wszystkie bboxy.
- `export_all()`: wystarczy rozszerzyć istniejące `*.label.json` i `*.schema.json` (bez nowego formatu pliku).

Przed eksportem wywołaj `enrich_label_record` jeśli relations puste.

---

## 5. UI — `labeler/static/app.js`

### Auto-hierarchia (JS mirror logiki Python)

Po utworzeniu bboxa (`mouseup`) i po `removeBboxAt()`:
- `recomputeHierarchy()` na całej liście `bboxes` (ta sama logika: contains + min area parent).
- Ustaw `parent_id`, `depth`, `rel_bbox` lokalnie.

### Wizualizacja

- **Accordion**: wcięcie CSS wg `depth`; w nagłówku np. `#3` + subtelnie `↳ w #1` gdy jest rodzic (seq rodzica).
- **Canvas**: przy zaznaczeniu dziecka — przerywana obwódka **rodzica** (inny kolor/styl).
- **Sortowanie listy**: drzewiaste — rodzic, potem jego dzieci (w grupie: nadal sensowny porządek, np. seq rosnąco lub top→left).

### Zapis

Rozszerz `buildSavePayload()` o `parent_id`, `depth`, `rel_bbox`. Backend i tak przeliczy — ale mniej rozjazdu UI.

Bump w `index.html`: `app.js?v=13`.

---

## 6. Testy

### `backend/tests/test_bbox_layout.py` (nowy)

- Blok zawiera symbol → poprawny `parent_id`, `depth` 0/1.
- 3 poziomy zagnieżdżenia.
- Rodzeństwo → relacje `left_of` / `above` (centroidy).
- Brak fałszywego rodzica przy częściowym overlap.
- Stary `LabelRecord` bez pól → po `enrich` pełne drzewo.

### `labeler/tests/test_export.py`

- Zagnieżdżone bboxy → `schema.json` ma `parent_id` na `Component` i niepuste `spatial_relations`.

---

## 7. Dokumentacja

W `docs/labeling-guide.md` dodaj sekcję **„Oznaczanie warstwowe”** (~10 linii):
- bbox-blok + bboxy szczegółów w środku = OK,
- system sam wykrywa zawieranie,
- YOLO = wszystkie prostokąty; hierarchia w JSON/schema,
- tag w bloku = kontekst, tag w dziecku = konkret (`-11`).

---

## Przykład oczekiwanego JSON po zapisie

```json
{
  "bboxes": [
    {"id": "element_1", "seq": 1, "parent_id": "", "depth": 0, "rel_bbox": [],
     "tag": "Blok zasilania RUPS1"},
    {"id": "element_2", "seq": 2, "parent_id": "element_1", "depth": 1,
     "rel_bbox": [0.34, 0.28, 0.16, 0.37], "tag": "Rozłącznik -11"}
  ],
  "spatial_relations": [
    {"from_id": "element_1", "to_id": "element_2", "relation": "contains"}
  ]
}
```

Istniejące strony (np. `SchematWRT01_p013`, 10 bboxów) — hierarchia wyliczona przy pierwszym GET/zapisie.

---

## Test akceptacji

```powershell
pytest backend/tests labeler/tests
python -m labeler.app   # localhost:8765
```

Ręcznie:
1. Narysuj duży bbox-blok, potem mniejszy w środku.
2. Zapisz → w DevTools/network sprawdź POST: dziecko ma `parent_id` bloku.
3. Odśwież stronę → hierarchia wczytana, accordion z wcięciem.
4. Zaznacz dziecko → widać obwódkę rodzica na canvas.
5. Eksport → `*.schema.json` ma `spatial_relations`.
6. YOLO txt nadal ma **oba** bboxy.

---

## Zakazy

- React, npm, cloud API
- Nie zmieniaj logiki auto-zapisu / localStorage / pageCache (v12) — tylko rozszerzaj
- Nie filtruj bboxów w eksporcie YOLO
- Nie implementuj ręcznego „przypnij do rodzica” (na później)
- Nie implementuj przesuwania/resiz bboxów

---

## Po ukończeniu

1. `pytest backend/tests labeler/tests`
2. Wpis w `sync/zw-to-filip.md` — co zrobione, jak testować
3. `sync/commit-message.txt` = `[Claude] labeler: bbox hierarchy + spatial relations (prompt 003)`

## Poprawka (runda N)

*(Cursor dopisuje tu feedback po review)*
