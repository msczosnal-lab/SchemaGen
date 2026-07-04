# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

**Wizja:** [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md) — trzy filary + relacje.

---

## Stan (2026-07-04) — etap READ DONE, Faza 5 WIP

| Prompt / kamień | Status |
|-----------------|--------|
| **001–004** symbole + OCR + linie + graph-builder | ✅ DONE |
| **011-strip-yolo-classes** | ✅ DONE — zlaczka/mostek/strzalki w YOLO |
| **012-mostek-orientacja** | ✅ DONE — D4 + eksemplarze |
| **014-tiling** | ✅ kod DONE — tiled_export + detect_tiled |
| **015-relations-layer** | ✅ DONE — RelationResolver |
| **016-e2e-metrics** | ⏳ KOLEJKA — po smoke Filipa |
| **Harness walidacji** | ✅ `preview_schema.py`, `diff_gt_runtime.py` |
| **Config runtime** | ✅ `terminal_tol_*`, `hough_*`, `connection_require_terminal` |

**Strona referencyjna:** `22_A_153_PL_Adamed_AGV_SA2_20250706_p040`

---

## Aktywne zadanie — Claude (Faza 5: relacje)

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/015-relations-layer.md`](prompts/015-relations-layer.md) |
| **Plik** | `backend/recognize/relation_resolver.py` |
| **Testy** | `backend/tests/test_relation_resolver.py` |
| **Regula** | net-builder nietkniety; `--rebuild-conn` p040 ≈ **15** conn |

---

## Aktywne zadanie — Filip (po 015)

| Pole | Wartość |
|------|---------|
| **Smoke** | `preview_schema.py --page p040 --source runtime` + `diff_gt_runtime.py` |
| **Config** | `common_terminal:` w `config/mostek-orient.yaml` |
| **Opcjonalnie** | trening `symbols_tiled_v1` + `yolo_tiled: true` (prompt 014) |

---

## Kolejka — po akceptacji 015

| Prompt | Cel |
|--------|-----|
| **016-e2e-metrics** | diff per filar + batch eval na `config/val-pages.yaml` |

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
