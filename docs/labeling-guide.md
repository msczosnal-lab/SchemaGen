# Instrukcja oznaczania schematow

Wizja trzech filarow: [`schematic-interpretation.md`](schematic-interpretation.md)

## Cel (etap 1 — symbole graficzne)

Tworzysz ground truth bboxow do treningu YOLO (klasa `element`) i JSON/schema.

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
- **Wyjatki:** pole „Wolne haslo” — trafia do `config/element-catalog.yaml`
- **Nieprzypisany bbox:** szary, przerywany obrys — mozna zapisac, ale warto uzupelnic typ

## Klasa YOLO

Zobacz `config/symbol-classes.yaml` — na etapie 1 tylko **`element`**. Haslo (`tag`) idzie do JSON, **nie** do pliku YOLO `.txt`.

## Hierarchia bboxow

Duzy bbox-blok (np. `modul zasilania`) + mniejsze symbole w srodku — system sam wykrywa `parent_id`, `depth`, `rel_bbox`. Eksport YOLO = wszystkie prostokaty.

## Zlozone urzadzenia (device_block)

Na razie: **jeden obrys** + haslo blokowe (`szafa`, `listwa zaciskow`). Terminali nie oznaczaj — osobny tryb pozniej ([`docs/adr/device-block-stub.md`](adr/device-block-stub.md)).

## Po eksporcie

Pliki w `data/labeled/`:
- `labels/*.txt` — YOLO (klasa `element`)
- `*.schema.json` — SchemaModel GT z `tag`
- `data.yaml` — konfig treningu

## Nastepne filary (nie w tym labelerze jeszcze)

- **Tekst** — OCR + bboxy tekstu
- **Polaczenia** — linie wire/bus w labelerze (prompt 002-labeler-lines-colors)
