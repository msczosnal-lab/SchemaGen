# Zadanie 015: Warstwa relacji (RelationResolver)

**Status:** DONE — wdrożone 2026-07-04  
**Model:** Opus, effort High  
**Plik:** `backend/recognize/relation_resolver.py`

## Kontekst

`GraphBuilder.build()` składa `SchemaModel` z detekcji YOLO, OCR i linii. Net-builder (krok 5) daje czystą geometrię `Connection`. **Ten prompt** dopina semantykę relacji:

- tekst → symbol (tag instancji),
- tekst → potencjał na `Connection`,
- scalanie strzałek potencjału o tej samej nazwie,
- `context_assignments[]` na runtime YOLO (bez tagów PL z palety).

**Strona referencyjna:** `22_A_153_PL_Adamed_AGV_SA2_20250706_p040`

## Reguły (nie zmieniać bez zgody)

- `GraphicLine` ≠ `Connection` — net-builder nietknięty
- Sygnatury `backend/protocols/` i kontrakt `SchemaModel JSON` — tylko wypełnianie pól
- Bez cloud API w `backend/recognize/`

## Implementuj `RelationResolver.resolve()`

```python
def resolve(
    components: list[Component],
    texts: list[TextDetection],
    connections: list[Connection],
    graphic_lines: list[GraphicLine],
    potentials: list[str],
    *,
    image_size: tuple[int, int] | None = None,
) -> tuple[list[Component], list[Connection], list[str], list[ContextAssignment], list[str]]:
```

Kroki wewnętrzne (kolejność ma znaczenie):

### 1. Przypisanie tagów do symboli

- Najpierw overlap bbox OCR ∩ bbox symbolu (jak dotychczas `_assign_tags`).
- Fallback: najbliższy symbol w promieniu `tag_proximity_frac * max(W,H)` z `config/runtime.yaml`.
- Preferuj tekst pasujący do wzorca tagu instancji (`^-?[A-Z]\d+`).
- Teksty nieprzypisane → `annotations[]`.

### 2. OCR → potencjał na Connection

- Tekst blisko końca linii `wire` (nie wewnątrz bbox symbolu) → `Connection.potential`.
- Tolerancja: `wire_label_proximity_frac * max(W,H)`.
- Nie nadpisuj `potential` już ustawionego przez net-builder (`net_k`).

### 3. Scalanie strzałek potencjału

- Komponenty z `type` w `potential_arrow_classes` (config).
- Grupuj po znormalizowanym `tag` (po kroku 1).
- Gdy `merge_potential_arrows_by_tag: true` i grupa ≥2: wspólny `pot_{tag}` w `potentials[]`.
- Usuń `Connection` między dwoma strzałkami tej samej grupy (elektrycznie ten sam węzeł).
- Połączenia strzałka→inny symbol: ustaw `potential` na wspólny id grupy.

### 4. Runtime context

- Z `components` zbuduj `BboxAnnotation[]`.
- Klasa efektywna: `tag_to_class(tag)` lub fallback `component.type` (YOLO).
- Użyj `group_into_rows` + `assign_contextual` z `backend/geometry/row_layout.py`.

## Konfiguracja

Rozszerz `config/runtime.yaml`:

```yaml
relations:
  tag_proximity_frac: 0.015
  wire_label_proximity_frac: 0.012
  potential_arrow_classes:
    - strzalka_potencjalu_wejsciowa
    - strzalka_potencjalu_wyjsciowa
  merge_potential_arrows_by_tag: true
```

Dodaj loadery w `backend/runtime_config.py`.

## Integracja GraphBuilder

Po kroku 5 (net-builder), przed `return SchemaModel`:

```python
components, connections, potentials, context_assignments, annotations = (
    RelationResolver().resolve(components, texts, connections, graphic_lines, potentials, image_size=size)
)
```

Usuń `_assign_tags` i `_resolve_context_safe` z `graph_builder.py` (logika w resolverze).

## Testy

`backend/tests/test_relation_resolver.py` + fixture `backend/tests/fixtures/relations_minimal.json`:

- tag `-K1` blisko bbox bez overlap → przypisany do symbolu
- dwie strzałki z tagiem `24V` → jeden potential, brak Connection między nimi
- `W1` OCR przy linii wire → `Connection.potential == "W1"`
- tekst tabelki (daleko od symboli) → tylko `annotations`, nie tag symbolu
- złączki w wierszu → `context_assignments` z `role=zlaczka`

Mocki — bez GPU/OCR w CI. Istniejące testy `test_graph_builder.py` muszą przechodzić.

## Kryteria akceptacji

| Kryterium | Sprawdzenie |
|-----------|-------------|
| Tagi instancji runtime p040 | `preview_schema.py --source runtime` |
| Strzałki o tej samej nazwie scalone | brak zbędnego Connection; wspólny `potential` |
| Etykiety przewodu na Connection | `Connection.potential` ≠ `""` gdzie OCR widzi marker |
| `context_assignments` runtime | złączki: `role=zlaczka` |
| pytest | `backend/tests` + `labeler/tests` + `train/tests` bez regresji |
| GT conn referencja | `--rebuild-conn` p040 ≈ **15** (net-builder nietknięty) |

## Po ukończeniu

`sync/commit-message.txt` = `[Claude] recognize: relation resolver (prompt 015)`

## Poprawka (runda N)

*(Cursor)*
