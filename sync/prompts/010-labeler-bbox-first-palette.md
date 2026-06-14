# Zadanie 010: labeler — bbox najpierw + paleta haseł

**Status:** OPEN — decyzja Filipa 2026-06-15  
**Model:** Sonnet, effort **High**  
**Filar:** symbole graficzne (1/3) — patrz [`docs/schematic-interpretation.md`](../../docs/schematic-interpretation.md)

## Kontekst (decyzja Filipa)

System interpretuje schemat przez **trzy filary wizualne**, potem **relacje**:
1. **Symbole graficzne** ← *ten prompt*
2. Tekst (OCR — prompt 002)
3. Połączenia (linie — prompty 002-labeler / 003-tracer)

**Relacje później:** tekst↔symbol, symbol↔symbol — `004-graph-builder`.

**Rezygnacja:** atlas QET, kurator, cropy, `symbol-reference.yaml` — **nie używać**. Paleta = statyczne hasła PL w YAML.

| Teraz | Później |
|-------|---------|
| Duża baza bboxów ze skanów | OCR, line tracer, GraphBuilder |
| Bbox → hasło typu z palety | Relacje tekst–symbol–połączenie |
| YOLO klasa `element` | Multi-class gdy starczy bboxów ze skanu |

**Labeler dziś:** opis **przed** bboxem — odwrócić na bbox **przed** wyborem typu.

**Trening YOLO:** wyłącznie bboxy ze skanów. Hasło w `tag` → JSON/schema, nie do YOLO `.txt`.

---

## Cel

1. **`config/symbol-palette.yaml`** — biblioteka ~40–60 najczęstszych typów (hasła PL).
2. **Backend** — loader + `GET /api/symbol-palette?q=…` (filtrowanie po `label_pl`, `aliases`).
3. **Labeler UI** — workflow bbox-first + picker po zaznaczeniu.
4. **Docs** — zaktualizuj [`docs/labeling-guide.md`](../../docs/labeling-guide.md).

**Nie psuj:** auto-zapis stron, localStorage, hierarchii bboxów (003), eksportu YOLO ze wszystkimi prostokątami.

---

## 1. `config/symbol-palette.yaml`

Format:

```yaml
meta:
  version: 1
  purpose: picker labelera — hasła jednowierszowe, bez cropów atlasu

symbols:
  - id: fuse
    label_pl: bezpiecznik
    tag_prefix: F
    aliases: [bezpiecznik topikowy, fusible]
  - id: contactor
    label_pl: stycznik
    tag_prefix: KM
  # ...
```

**Wymagane pola per wpis:** `id`, `label_pl`.  
**Opcjonalne:** `tag_prefix` (IEC 81346-1), `aliases` (lista stringów PL).

**Minimalna lista (~45 pozycji)** — pokryj typy z WRT01 / IEC 60617 (Filip oznacza hasłowo):

| Grupa | Przykłady `label_pl` |
|-------|----------------------|
| Zabezpieczenia | bezpiecznik, wyłącznik, wyłącznik silnikowy, rozłącznik, ogranicznik przepięć |
| Styczniki / przekaźniki | stycznik, przekaźnik, przekaźnik termiczny, stycznik pomocniczy |
| Silniki / napędy | silnik, falownik, softstart, hamulec |
| Zasilanie | transformator, zasilacz, prostownik, kondensator |
| Sygnalizacja / sterowanie | przycisk, lampka, przełącznik, selektor, przycisk awaryjny |
| Pomiary / czujniki | czujnik, licznik, amperomierz, woltomierz |
| Połączenia | zacisk, listwa zaciskowa, wtyczka, gniazdo |
| Moduły / automatyka | moduł PLC, moduł IO, przekaźnik interfejsu |
| Półprzewodniki / pasywne | dioda, rezystor, cewka, filtr |
| Inne | uziemienie, mostek, węzeł, szyna, moduł zasilania, bloczek |

Dopisz `id` slug (ASCII, snake_case). **Nie** duplikuj wpisów semantycznie identycznych.

---

## 2. Backend — `backend/symbol_palette.py` (nowy)

```python
def load_symbol_palette() -> dict: ...
def list_palette_entries() -> list[dict]: ...
def search_palette(query: str, limit: int = 20) -> list[dict]:
    """Case-insensitive: label_pl, aliases, id."""
```

Stała: `CONFIG / "symbol-palette.yaml"`. **Nie** importuj z `backend/atlas/` — atlas QET nieużywany.

---

## 3. Labeler API — [`labeler/app.py`](../../labeler/app.py)

```python
@app.get("/api/symbol-palette")
def api_symbol_palette(q: str = "", limit: int = 30) -> dict:
    return {"symbols": search_palette(q, limit=limit)}
```

Zachowaj istniejące `/api/element-catalog` (wpisy z labelera Filipa — merge w UI: paleta + ostatnie z katalogu).

---

## 4. UI — odwrócony workflow

Pliki: [`labeler/static/app.js`](../../labeler/static/app.js), [`index.html`](../../labeler/static/index.html), [`style.css`](../../labeler/static/style.css).  
**Bump** `app.js?v=15` w index.html.

### 4.1 Rysowanie bez opisu

- Usuń wymóg `tagInput.value.trim()` przed utworzeniem bboxa w `finishDraw` / odpowiedniku.
- Nowy bbox: `tag: ""`, wizualnie **„nieprzypisany”** (np. szary/obrys przerywany, label `(?)` lub `#seq`).

### 4.2 Przypisanie typu po bboxie

- Klik bbox na liście lub canvas → **panel przypisania** (prawy panel lub rozwinięty wiersz):
  - pole wyszukiwania (`/api/symbol-palette?q=…`, debounce ~200 ms),
  - lista wyników (klik = ustaw `tag` = `label_pl`),
  - sekcja **Ostatnie** z `element-catalog`,
  - pole **Wolne hasło** (wyjątki) — Enter zapisuje custom tekst do `tag` + `register_labels` przy save.
- Po przypisaniu: kolor z hasła (`colorFromTag`), usuń stan nieprzypisany.

### 4.3 Lewy panel

- Zmień copy: zamiast „Wpisz opis, narysuj bbox” → **„Narysuj bbox, potem wybierz typ po prawej”**.
- Opcjonalnie: ukryj lub zmniejsz stary `textarea` tag-input (nie blokuj rysowania); focus search w panelu przypisania po nowym bboxie.

### 4.4 Skróty (minimum)

- Po narysowaniu bboxa: auto-focus wyszukiwarki typu.
- `Enter` w search: wybierz pierwszy wynik.
- Edycja istniejącego bboxa: jak dziś (accordion + textarea OK).

### 4.5 Zapis

- `buildSavePayload` bez zmian struktury — `tag` może być pusty (Filip może zapisać nieprzypisane; UI ostrzega licznikiem „N nieprzypisanych” przy Zapisz).

---

## 5. Eksport — bez zmian semantyki

- [`labeler/export.py`](../../labeler/export.py): YOLO nadal `class_name: element` dla wszystkich bboxów.
- `label_to_schema`: `Component.tag` = hasło z pickera (może być pusty).

---

## 6. Testy

| Plik | Co |
|------|-----|
| `backend/tests/test_symbol_palette.py` (nowy) | load, search, aliases, brak pliku → pusty |
| `labeler/tests/test_export.py` | bbox z pustym tagiem nadal eksportuje YOLO |
| opcjonalnie | test API palette przez TestClient FastAPI |

```bash
pytest backend/tests labeler/tests
python -m backend.cli validate schema/fixtures/page1_expected.json
```

Oczekiwane: zero regresji, nowe testy green.

---

## 7. Dokumentacja

Zaktualizuj [`docs/labeling-guide.md`](../../docs/labeling-guide.md):

- Workflow bbox-first.
- Hasła krótkie (typ), nie relacje w tekście.
- Złożone urządzenia: na razie jeden obrys + hasło blokowe; terminale — później.
- Paleta vs `element-catalog.yaml` (paleta = stała lista, katalog = Twoje wyjątki).

Krótka notatka w [`docs/project-context.txt`](../../docs/project-context.txt) — Etap 1 = detekcja elementów.

---

## Czego NIE robić

- **`backend/atlas/`**, QET, `build_reference`, kurator, cropy PNG
- Multi-class YOLO / line tracer / OCR / GraphBuilder w tej sesji
- Cloud API

---

## Po ukończeniu

1. `pytest backend/tests labeler/tests`
2. Wpis w [`sync/zw-to-filip.md`](../../sync/zw-to-filip.md) — pliki, jak używać pickera
3. [`sync/commit-message.txt`](../../sync/commit-message.txt) = `[Claude] labeler: bbox-first + symbol palette (prompt 010)`

## Poprawka (runda N)

*(Cursor)*
