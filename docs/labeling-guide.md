# Instrukcja oznaczania schematow

## Cel

Tworzysz ground truth do treningu YOLO i walidacji pozniejszej inferencji.

## Kroki

1. Umiesc PNG/PDF strony w `data/raw/` (PDF: `python -m backend.cli recognize` konwertuje via ingest)
2. Uruchom labeler: `python -m labeler.app` → http://localhost:8765
3. Wybierz strone z listy
4. **Wpisz opis elementu** (lewy panel), np. `Stycznik -K1`
5. Narysuj bbox wokol symbolu na schemacie
6. Zapisz — opis trafia do katalogu `config/element-catalog.yaml`
7. Eksport YOLO + JSON

Klasa techniczna YOLO: `element` (jedna dla wszystkich). Szczegoly = opis tekstowy.

## Klasy (start)

Zobacz `config/symbol-classes.yaml` — 9 klas MVP.

## Minimum datasetu

10 stron × ~15 symboli = proof-of-concept YOLOv8n na RTX 2080.

## Oznaczanie warstwowe (hierarchia bboxow)

Mozesz rysowac **bbox w bboxie** — duzy blok (np. „Blok zasilania RUPS1”)
i mniejsze bboxy szczegolow w srodku (rozlacznik, symbol, tag `-11`).

- System **sam wykrywa zawieranie** — najmniejszy bbox w pelni obejmujacy nowy
  zostaje jego rodzicem; zapisywane sa `parent_id`, `depth`, `rel_bbox`.
- W panelu po prawej dzieci sa wciete, z adnotacja `↳ w #<nr rodzica>`;
  po zaznaczeniu dziecka rodzic ma zolta przerywana obwodke na canvas.
- **Eksport YOLO = wszystkie prostokaty** (nakladanie jest celowe);
  hierarchia trafia tylko do JSON/schema (`spatial_relations`, relacje przestrzenne).
- Tag na bloku = **kontekst**, tag na dziecku = **konkret** (np. `-11`).

## Po eksporcie

Pliki trafiaja do `data/labeled/`:
- `labels/*.txt` — YOLO
- `*.schema.json` — SchemaModel GT
- `data.yaml` — konfig treningu
