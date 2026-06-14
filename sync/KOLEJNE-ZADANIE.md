# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

---

## Stan (2026-06-14)

| Prompt | Status |
|--------|--------|
| **001-labeler-canvas** | **DONE** |
| **003-labeler-bbox-hierarchy** | **AKTYWNE** — priorytet (Filip oznacza zagnieżdżone bboxy) |
| **002-labeler-lines-colors** | **BLOCKED** — po 003 |

---

## Aktywne zadanie

| Pole | Wartosc |
|------|---------|
| **Prompt** | [`sync/prompts/003-labeler-bbox-hierarchy.md`](prompts/003-labeler-bbox-hierarchy.md) |
| **Pliki** | `backend/geometry/bbox_layout.py`, modele, `labeler/app.py`, `labeler/export.py`, `labeler/static/app.js` |
| **Cel** | Hierarchia bboxów (parent/depth/rel_bbox) + relacje przestrzenne; UI drzewa; YOLO bez zmian |
| **Model** | Sonnet, effort **High** |

### Kroki

1. Przeczytaj `docs/claude-cowork-instructions.md`
2. Przeczytaj `sync/filip-to-zw.md` (najnowszy wpis)
3. Zaimplementuj **003-labeler-bbox-hierarchy.md**
4. `pytest labeler/tests backend/tests`
5. Wpis w `sync/zw-to-filip.md`
6. `sync/commit-message.txt` = `[Claude] labeler: bbox hierarchy + spatial relations (prompt 003)`
7. GitSync: `Start-GitSync.cmd Claude`

### Czego NIE robic teraz

- **002-labeler-lines-colors** — dopiero po 003
- **001-symbol-detector** — dopiero po danych od Filipa (oznaczone strony)
- Nie psuj auto-zapisu / localStorage z app.js v12

---

## Nowosc (prompt 003) — zapamietaj

1. Filip robi **bbox w bboxie** — blok + szczegóły w środku
2. Zapisuj: `parent_id`, `depth`, `rel_bbox`, `spatial_relations`
3. YOLO: **wszystkie** bboxy (bez filtra); hierarchia tylko w JSON/schema
4. Źródło prawdy geometrii: `backend/geometry/bbox_layout.py`

---

## Kolejnosc promptow (labeler)

| # | Prompt | Status |
|---|--------|--------|
| 1 | 001-labeler-canvas | DONE |
| 2 | **003-labeler-bbox-hierarchy** | **AKTYWNE** |
| 3 | 002-labeler-lines-colors | po 003 |

(Pozostałe: symbol-detector, OCR, line-tracer, graph-builder, train — bez zmian w `sync/prompts/`.)

---

## Test akceptacji (zawsze)

```powershell
pytest backend/tests labeler/tests
python -m backend.cli validate schema/fixtures/page1_expected.json
```

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]`. Nie nadpisuj jesli jest `[Cursor]` i niepusty.
