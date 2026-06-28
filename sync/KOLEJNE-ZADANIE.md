# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

**Wizja:** [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md) — trzy filary + relacje.

---

## Stan (2026-06-28) — etap POŁĄCZENIA DONE

| Prompt / kamień | Status |
|-----------------|--------|
| **004-graph-builder / net-builder** | ✅ DONE — terminal=granica scalania, `--rebuild-conn` p040=**15** conn |
| **Labeler edycja GT (T/R/C v34)** | ✅ DONE (ZW) — drag terminali, re-klasyfikacja R, conn C, linie L |
| **crop-review + import draft** | ✅ DONE (Cursor) |
| **010-labeler-bbox-first-palette** | ✅ DONE |
| **symbols_atomic_v2** | ✅ mAP50≈0.92 |
| **Harness walidacji** | ✅ `preview_schema.py --rebuild-conn` + `[GT-conn]` (read-only) |
| **Config runtime** | ✅ `terminal_tol_*`, `hough_*`, `connection_require_terminal: true` |

**Strona referencyjna:** `22_A_153_PL_Adamed_AGV_SA2_20250706_p040`

**Cursor review:** pytest **151 passed**; regresja net_builder/sito OK.

---

## Aktywne zadanie — Filip (~1 strona)

| Pole | Wartość |
|------|---------|
| **Cel** | Ręczne GT p040 — terminale i połączenia poprawione w labelerze |
| **Workflow** | Ctrl+F5 → tryby **T → C → L** → poprawki → **Zapisz stronę** |
| **Walidacja** | dopiero po Zapisz: `diff_gt_runtime.py --page p040` ma sens (GT ≠ draft) |

```powershell
python -m labeler.app   # Ctrl+F5, app.js v34
python scripts/diff_gt_runtime.py --page p040
python scripts/preview_schema.py --page p040 --source gt --rebuild-conn
```

---

## Aktywne zadanie — Claude (backlog)

| Pole | Wartość |
|------|---------|
| **Strzałki potencjału** | scalanie o tej samej nazwie |
| **derive_auto_terminals** | tuning poza p040 |
| **Hough** | kalibracja per strona (pokrętła w `runtime.yaml`, tuning czeka) |
| **Po GT p040** | ewentualnie `--rebuild-conn` na p027 po ręcznym GT |

**Nie ruszaj:** trening YOLO, atlas QET, labeler (edycja GT DONE).

---

## Aktywne zadanie — Cursor

| Pole | Wartość |
|------|---------|
| **DONE** | review sesji ZW 2026-06-28, pytest, KOLEJNE-ZADANIE zaktualizowane |
| **Czekaj** | wynik `diff_gt_runtime` po ręcznym GT Filipa |

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
