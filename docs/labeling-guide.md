# Instrukcja oznaczania schematow

## Cel

Tworzysz ground truth do treningu YOLO i walidacji pozniejszej inferencji.

## Kroki

1. Umiesc PNG/PDF strony w `data/raw/` (PDF: `python -m backend.cli recognize` konwertuje via ingest)
2. Uruchom labeler: `python -m labeler.app` → http://localhost:8765
3. Wybierz strone z listy
4. Rysuj bbox wokol symbolu
5. **Opis tekstowy** — zaznacz bbox, wpisz w panelu „Opis elementu” (np. `Stycznik -K1`, `Silnik =M1`)
6. Zapisz — nowe opisy trafiaja do `config/element-catalog.yaml` (autouzupelnianie przy kolejnych stronach)
7. Eksport YOLO + JSON

Klasa YOLO (1–9) jest drugorzedna na tym etapie — domyslnie `text_label`; szczegoly sa w opisie.

## Klasy (start)

Zobacz `config/symbol-classes.yaml` — 9 klas MVP.

## Minimum datasetu

10 stron × ~15 symboli = proof-of-concept YOLOv8n na RTX 2080.

## Po eksporcie

Pliki trafiaja do `data/labeled/`:
- `labels/*.txt` — YOLO
- `*.schema.json` — SchemaModel GT
- `data.yaml` — konfig treningu
