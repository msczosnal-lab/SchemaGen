# Zadanie 008: ekstrakcja atlasu symboli (faza 1 — QET)

**Status:** ANULOWANY na etapie 1 (2026-06-15) — rezygnacja z atlasu QET w runtime. Kod może zostać w repo; **Claude nie rozszerza, nie używa w labelerze.** Wizja: [`docs/schematic-interpretation.md`](../../docs/schematic-interpretation.md).  
**Model:** Sonnet, effort **High**  
**Faza:** **008a** — tylko QElectroTech. IEC 60617 PDF i warstwa producenta → fazy 008b/008c (osobne prompty).

## Kontekst (decyzje Filipa)

- **Akceptacja** [`docs/knowledge-sources-analysis.md`](../../docs/knowledge-sources-analysis.md) v4: atlas warstwowy + trening Siemens-first (klasy generyczne).
- **WRT01:** Filip ma **tylko PDF schematu**, brak projektu EPLAN / Data Portal.
- **Drugi PDF** (inne producenci) — Filip uzupełni ścieżkę w `sync/sources-inbox.md`; na razie **nie implementuj** ekstrakcji z tego PDF (008c).
- Lokalne `C:\Users\Public\EPLAN\Data\` z inbox **nie dotyczy** Filipa — nie zakładaj dostępu EPLAN.

## Cel fazy 008a

Z biblioteki QET wygenerować lokalny atlas offline:

1. `config/symbol-reference.yaml` — kanoniczne `symbol_id`, opisy, aliasy PL, `yolo_class`, `source_refs`
2. `data/atlas/crops/{symbol_id}.png` — render symboli z `.elmt` (wektor → PNG)
3. Moduł Python do parsowania i (opcjonalnie) ponownego importu

Bez cloud API. Surowa biblioteka QET **poza gitem** (`data/atlas/qet/`).

## Wejście

1. Sklonuj repo (jednorazowo, lokalnie):
   ```bash
   git clone --depth 1 https://github.com/qelectrotech/qelectrotech-elements.git data/atlas/qet
   ```
2. Raport pokrycia: [`docs/qet-library-report.md`](../../docs/qet-library-report.md)
3. Istniejące klasy YOLO: [`config/symbol-classes.yaml`](../../config/symbol-classes.yaml) — dziś tylko `element`
4. Propozycja formatu YAML: sekcja w `knowledge-sources-analysis.md`

## Zakres symboli (MVP)

Nie importuj wszystkich 8732 plików. Wybierz **~80–120** wpisów priorytetowych pod WRT01 + Siemens-first:

| Priorytet | Ścieżki QET | Typy |
|-----------|-------------|------|
| P0 | `10_electric/10_allpole/` | fuse, relay, contactor, switch, terminal, motor, disconnector |
| P1 | `10_electric/91_en_60617/` | dedup z allpole — tylko gdy brak odpowiednika w P0 |
| P2 | `10_electric/20_manufacturers_articles/` | filtr **Siemens** + generyki (WAGO, ABB…) — max ~30 |

Reguła deduplikacji: jeden `symbol_id` na kształt semantyczny; `source_refs[]` = lista plików `.elmt`.

## Format `config/symbol-reference.yaml`

```yaml
meta:
  version: 1
  generated_at: "<ISO8601>"
  sources:
    - id: qet
      type: gpl_lib
      ref: "data/atlas/qet"
      license: "GNU/GPL — atrybucja w README/docs"
  tag_standard: "IEC 81346-1"

symbols:
  - id: fuse_disconnector
    yolo_class: element
    iec_ref: null  # uzupełni 008b z IEC PDF
    aliases_pl: ["rozłącznik bezpiecznikowy", "bezpiecznik"]
    tag_prefix: "F"
    default_description: "<z .elmt name PL lub EN>"
    atlas_crop: "data/atlas/crops/fuse_disconnector.png"
    source_refs:
      - "qet:10_electric/10_allpole/..."
```

Pola wymagane per symbol: `id`, `yolo_class`, `default_description`, `atlas_crop`, `source_refs`.  
Opcjonalne: `aliases_pl`, `tag_prefix`, `iec_ref`, `product_type`.

## Implementacja — pliki

| Plik | Rola |
|------|------|
| `backend/atlas/__init__.py` | pakiet |
| `backend/atlas/qet_parser.py` | parsowanie `.elmt` (XML): nazwa, języki, bounding box geometrii |
| `backend/atlas/qet_render.py` | render wektorów → PNG (cairosvg lub ręczny raster — **offline**, bez sieci) |
| `backend/atlas/build_reference.py` | CLI: skan katalogów, dedup, zapis YAML + crop-y |
| `backend/atlas/reference.py` | `load_symbol_reference()`, lookup po `id` / alias |
| `config/symbol-reference.yaml` | output (commituj) |
| `backend/tests/test_qet_parser.py` | testy na 2–3 fixture `.elmt` (małe pliki w `schema/fixtures/atlas/`) |
| `backend/tests/test_symbol_reference.py` | walidacja YAML, unikalność `id` |

### CLI

```bash
python -m backend.atlas.build_reference \
  --qet-dir data/atlas/qet \
  --out config/symbol-reference.yaml \
  --crops-dir data/atlas/crops
```

Opcje: `--max-symbols 120`, `--include-siemens`, dry-run.

### Render PNG

- Rozmiar crop: min. 64×64, max. 256×256, tło białe, linie czarne (spójne z YOLO).
- Jeśli cairosvg niedostępne — fallback: prosty renderer SVG→PNG przez Pillow + ręczne linie z XML QET (wystarczy dla MVP).

## Relacja do istniejącego kodu

- **`config/element-catalog.yaml`** — instancje z labelera; w przyszłości pole `symbol_id` (prompt **009**).
- **`backend/catalog.py`** — bez zmian w 008a (009 zintegruje lookup).
- **Nie zmieniaj** labelera UI w tym zadaniu.

## Licencja / git

- `data/atlas/qet/` → `.gitignore`
- `data/atlas/crops/*.png` → commituj **tylko** crop-y użyte w `symbol-reference.yaml` (~120 plików OK) **lub** trzymaj crops lokalnie — wybierz jedną strategię i opisz w `docs/atlas-setup.md` (krótko, ≤30 linii).
- W `symbol-reference.yaml` meta.sources.license = GPL + link do QET.
- **Nie** commituj `IEC60617.pdf` ani surowego QET.

## [RYZYKO] — rozwiąż w implementacji

1. **Dedup allpole ↔ en_60617** — ten sam symbol podwójnie → jeden `symbol_id`, wiele `source_refs`.
2. **PL tylko ~34%** — gdy brak PL, `default_description` EN + pusta lub częściowa `aliases_pl`.
3. **GPL** — dokumentuj atrybucję; nie kopiuj całej biblioteki do repo.

## Zakazy

- Cloud API
- Ekstrakcja `IEC60617.pdf` (to **008b**)
- Parser PDF producenta (to **008c**)
- EPLAN `.sdb` / `.edz`
- Zmiany w `labeler/static/app.js` (to **009**)

## Test akceptacji

- [ ] `python -m backend.atlas.build_reference` kończy się sukcesem (przy sklonowanym QET)
- [ ] `config/symbol-reference.yaml` ma ≥80 wpisów, unikalne `id`
- [ ] Każdy wpis ma istniejący plik `atlas_crop`
- [ ] `pytest backend/tests/test_qet_parser.py backend/tests/test_symbol_reference.py` — pass
- [ ] `python -m backend.cli validate` — bez regresji (fixture schema bez zmian)

## Po ukończeniu

1. `pytest backend/tests labeler/tests`
2. Wpis w `sync/zw-to-filip.md` — liczba symboli, ścieżki, jak odpalić build
3. `sync/commit-message.txt` = `[Claude] atlas: QET extract → symbol-reference.yaml (prompt 008a)`

## Następne (nie w tym zadaniu)

| Prompt | Co |
|--------|-----|
| **008b** | layout-aware ekstrakcja `data/raw/IEC60617.pdf` → uzupełnienie `iec_ref` |
| **008c** | mapowanie symboli z PDF producenta (Filip poda plik) |
| **009** | picker `symbol_id` w labelerze |
| **002** | linie + kolory w labelerze (równolegle możliwe) |
