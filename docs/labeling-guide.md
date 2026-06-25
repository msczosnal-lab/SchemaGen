# Instrukcja oznaczania schematow

Wizja trzech filarow: [`schematic-interpretation.md`](schematic-interpretation.md)

## Cel (etap 1 — symbole graficzne)

Tworzysz ground truth bboxow do JSON/schema i — dla klas **atomowych** — do treningu YOLO.

Pelna instrukcja treningu: [`../TRENING-SIEC.md`](../TRENING-SIEC.md)

## Workflow labelera (prompt 010)

1. Uruchom: `python -m labeler.app` → http://localhost:8765
2. Wybierz strone z listy
3. **Narysuj bbox** wokol symbolu/urzadzenia na schemacie (bez opisu)
4. Kliknij element na liscie po prawej → **wybierz typ** z palety lub wpisz wolne haslo
5. Zapisz strone (Ctrl+S)

**Reset 2026-06-15:** stare bboxy WRT01 w `data/archive/wrt01-legacy-2026-06-15/`. Po resecie wyczysc szkice przegladarki (`localStorage`, klucze `schemagen:draft:*`).

Skroty: `/` = focus wyszukiwarki typu, strzalki = zmiana strony.

## Hasla (typ urządzenia)

- **Krotko:** `stycznik`, `bezpiecznik`, `modul PLC` — jedno haslo, nie relacje w tekscie
- **Paleta:** `config/symbol-palette.yaml` (~50 typow IEC/WRT01)
- **Wyjatki:** pole „Wolne haslo” — trafia do `config/element-catalog.yaml` i od razu do listy typow
- **Czestotliwosc:** licznik uzyc w SQLite — bez filtra najczesciej uzywane hasla na gorze listy
- **Nieprzypisany bbox:** szary, przerywany obrys — mozna zapisac, ale warto uzupelnic typ

## Klasa YOLO (multi-class)

Zobacz `config/symbol-classes.yaml` — lista klas **atomowych** (auto-generowana przy eksporcie).

Typ wpisujesz w polu **`tag`**. Eksport YOLO bierze tag → klase kanoniczna (`backend/class_map.py`).

### Klasy kontekstowe (bez YOLO)

Oznaczaj w labelerze — potrzebne do GT relacji i `ContextResolver` — ale **nie ucz** ich w YOLO (`config/train-classes.yaml`):

| Rząd | Tagi (przykłady) |
|------|------------------|
| złączki → listwa / zwarta listwa | `złączka`, `listwa złączek`, `zwarta listwa złączek` |
| złącza (rząd bez „listy”) | `złącze` |
| oznaczniki → oznaczenie kabla | `oznaczenie przewodu`, `oznaczenie kabla` |
| terminale urządzenia | `terminale urządzenia` |

**W YOLO zostają** m.in. `terminal_plc`, `relay`, `styki`, `led`.

Przy eksporcie `.schema.json` powstaje tez `context_assignments[]` (wiersze + kotwice).

## Hierarchia bboxow

Duzy bbox-blok (np. `modul zasilania`) + mniejsze symbole w srodku — system sam wykrywa `parent_id`, `depth`, `rel_bbox`. Eksport YOLO = tylko klasy atomowe (nie kontekstowe).

## Zlozone urzadzenia (device_block)

Na razie: **jeden obrys** + haslo blokowe (`szafa`, `listwa zaciskow`). Terminali urządzenia oznaczaj osobno w rzędzie na skraju bloku ([`docs/adr/device-block-stub.md`](adr/device-block-stub.md)).

## Po eksporcie

Pliki w `data/labeled/`:
- `labels/*.txt` — YOLO (tylko klasy atomowe)
- `*.schema.json` — SchemaModel GT z `tag`, `spatial_relations`, `context_assignments`
- `data.yaml` — konfig treningu

## Nastepne filary (nie w tym labelerze jeszcze)

- **Tekst** — OCR + bboxy tekstu
- **Polaczenia** — linie wire/bus w labelerze (prompt 002-labeler-lines-colors)
