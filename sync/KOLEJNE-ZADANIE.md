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

**WRT01:** DONE. **Stanley 229:** DONE/w toku. **Adamed AGV SA2** — 200 PNG w `data/raw/`.

---

## Aktywne zadanie — PRIORYTET (Filip)

| Pole | Wartosc |
|------|---------|
| **Cel** | Oznaczanie **Adamed AGV SA2** — bbox-first + paleta |
| **Pliki** | `data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p*.png` (p000…p199) |
| **Źródło** | `sync/sources/22_A_153_PL_Adamed_AGV_SA2_20250706.pdf` |

### Kroki Filip

1. Odśwież labeler (F5) — na liście szukaj `22_A_153_PL_Adamed_AGV_SA2`
2. Zacznij od **`_p000`** (lub reprezentatywnych stron)
3. Bbox → typ (ostatni typ zapamiętywany) → Ctrl+S

### Kolejne projekty

| Projekt | Stron | PDF |
|---------|------:|-----|
| Adamed INTEROL SA1 | 99 | `22_A_153_PL_Adamed_INTEROL_SA1_20250729.pdf` |
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
