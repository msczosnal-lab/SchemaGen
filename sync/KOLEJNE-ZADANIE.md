# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

**Wizja:** [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md) — trzy filary + relacje.

---

## Stan (2026-06-15)

| Prompt | Status |
|--------|--------|
| **010-labeler-bbox-first-palette** | ✅ DONE (Cursor) — bbox-first + paleta |
| **005–006, 001 recognize** | ✅ BUILD M0 (stary GT — zarchiwizowany) |
| **008a QET atlas** | ⛔ NIE UŻYWAĆ |
| **002-ocr-engine** | ⏸ WSTRZYMANE (brak Claude) |
| **002-labeler-lines-colors** | OPEN — filar: połączenia (GT) |
| **003-line-tracer** | OPEN — filar: połączenia (runtime) |
| **004-graph-builder** | OPEN — relacje (po filarach) |

**WRT01:** stare bboxy → `data/archive/wrt01-legacy-2026-06-15/`. Labeler od zera (77 PNG w `data/raw/`).

---

## Aktywne zadanie — PRIORYTET (Filip + Cursor)

| Pole | Wartosc |
|------|---------|
| **Cel** | WRT01 od nowa — bbox-first + typ z palety |
| **Archiwum** | `data/archive/wrt01-legacy-2026-06-15/MANIFEST.json` (11 stron, ~402 bboxy) |
| **Claude** | ⏸ wstrzymany do powrotu sesji |

### Kroki Filip

1. `python -m labeler.app` → http://localhost:8765
2. **Wyczyść szkice:** DevTools → Application → localStorage → usuń klucze `schemagen:draft:*` (albo tryb prywatny)
3. Zacznij od `SchematWRT01_p013` — 5–10 stron reprezentatywnych
4. Workflow: narysuj bbox → wybierz typ z palety → Ctrl+S
5. Po ~15 stronach: `python -m train.dataset_export` + re-train (`.venv311`)

### Cursor (równolegle, bez pełnego kodu Cowork)

- `011-ingest-batch` — ingest PDF → PNG (kolejne projekty)
- `011-bbox-crops` — spec cropów ze skanu
- `docs/data-layout.md`

### Czego NIE robić

- Atlas QET, OCR/line tracer (stuby Cowork)
- Nie używaj starego `symbols_v1.onnx` jako benchmarku nowych bboxów

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
