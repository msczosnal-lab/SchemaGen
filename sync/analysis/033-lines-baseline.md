# 033 baseline — jakość linii (2026-07-19)

Źródło: `diff_gt_runtime.py` (tol=8px) + `scripts/diag_lines_excess.py --page p028`.

## Metryki per strona (baseline)

| Strona | GT | RT | P | R | F1 |
|--------|-----|-----|------|------|------|
| p028 | 42 | 158 | 0.248 | 0.768 | 0.375 |
| p029 | 76 | 259 | 0.347 | 0.951 | 0.509 |
| p030 | 8 | 120 | 0.112 | 0.959 | 0.201 |
| p033 | 117 | 397 | 0.371 | 0.859 | 0.518 |
| p040 | 17 | 138 | 0.327 | 0.991 | 0.492 |
| **śr. F1** | | | | | **0.419** |

Recall wysoki na wszystkich stronach — problem to **precyzja** (RT ≫ GT).

## Diagnoza nadmiaru p028 (158 linii runtime vs 42 GT)

| Kategoria | Liczba | % | Leczenie |
|-----------|--------|---|----------|
| **cat1_noise** — brak pokrycia GT | 131 | 83% | filtr / sito (nie merge) |
| **cat4_split** — prawdziwa linia GT w N segmentach | 15 | 9% | **scalenie**, nie filtr |
| **matched** — 1 segment = 1 linia GT | 11 | 7% | OK |
| **cat2_duplicate** — duplikat Hough (2. przebieg) | 1 | 1% | dedup / merge |
| **cat3_titleblock** — poniżej ROI 0.93 | 0 | 0% | ROI działa na p028 |

### cat1_noise — rozbicie

| Podgrupa | n | role | uwagi |
|----------|---|------|-------|
| Krótkie (<200px) | 54 | other 32, wire 17, dash 4 | szum tekstu/rastra, segmenty bez ścieżki |
| Długie obramowanie strony (>90% max(W,H)) | 4 | other | Hough na krawędzi skanu (6615px) |
| Reszta (wire/other bez match) | 73 | other 51, wire 16, dash 5, frame 6 | sito zostawia `other`/`frame` w `graphic_lines` mimo że GT = tylko `wire` |

12 segmentów noise ma `global_gt_coverage` > 0.1 — agresywny filtr obcina recall.

### cat4_split — kluczowe

5 z 15 segmentów ma `role=other` przy `gt_coverage=1.0` — **prawdziwe przewody źle zdemotowane przez sito** (wewnątrz dużego bbox). Filtr precyzji musi je zachować (promocja wire), nie wycinać.

### Wnioski OODA

1. **Dominuje cat1_noise (83%)** — filtr precyzji uzasadniony.
2. **cat4_split istotny (9%)** — merge_collinear / gap_tol; filtr by pogorszył.
3. **GT = wire-only** — `other`/`frame`/`dash` w runtime psują P bez wpływu na R (poza ~7 liniami other z częściowym pokryciem GT).
4. **ROI OK** na p028; titleblock nie jest kubełem tu.
5. Kolejność: (a) obramowanie strony, (b) promocja other→wire gdy terminal gate OK, (c) emit tylko wire do `graphic_lines`, (d) merge gap.
