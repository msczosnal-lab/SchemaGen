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

**WRT01:** DONE (Filip). **Stanley 229** — 25 PNG w `data/raw/` (`25_A_229_PL5_19012026_p000`…`p024`).

---

## Aktywne zadanie — PRIORYTET (Filip + Cursor)

| Pole | Wartosc |
|------|---------|
| **Cel** | Oznaczanie **Stanley 229 / PL5** (25 str.) — bbox-first + paleta |
| **Pliki** | `data/raw/25_A_229_PL5_19012026_p*.png` |
| **Źródło** | `sync/sources/25_A_229_PL5_19012026.pdf` |

### Kroki Filip

1. `python -m labeler.app` → odśwież listę stron
2. Wybierz **`25_A_229_PL5_19012026_p000`** (lub kolejne)
3. Ten sam workflow: bbox → typ z palety → Ctrl+S
4. WRT01 zostaje w liście — możesz go pominąć

### Kolejne projekty (po Stanley)

| Projekt | Stron | PDF |
|---------|------:|-----|
| Adamed INTEROL SA1 | 99 | `22_A_153_PL_Adamed_INTEROL_SA1_20250729.pdf` |
| Adamed AGV SA2 | 200 | `22_A_153_PL_Adamed_AGV_SA2_20250706.pdf` |
| Norblin Cars | 199 | `20_A_022_PL_Norblin_Cars_2022-06-26.pdf` |

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
