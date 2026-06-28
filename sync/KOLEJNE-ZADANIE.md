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
| **011-strip-yolo-classes** | ✅ kod DONE — zlaczka/mostek atomic; czeka re-train Filipa |
| **Harness walidacji** | ✅ `preview_schema.py --rebuild-conn` + `[GT-conn]` (read-only) |
| **Config runtime** | ✅ `terminal_tol_*`, `hough_*`, `connection_require_terminal: true` |

**Strona referencyjna:** `22_A_153_PL_Adamed_AGV_SA2_20250706_p040`

**Cursor review (domknięcie):** pytest **151 passed**; `--rebuild-conn` p040=15; GT conn wyczyszczone (`clear_gt_connections.py`).

---

## Aktywne zadanie — Filip (filar SYMBOLE: re-train)

| Pole | Wartość |
|------|---------|
| **Kod** | ✅ prompt 011 — eksport zlaczka/mostek/strzałki w YOLO |
| **Czeka** | **re-train GPU** → `symbols_strip_v1` + ONNX + registry |
| **Walidacja** | runtime p040 ≈ **19/19 bbox**, brak gwiazdy |

```powershell
python -m train.dataset_export --min-count 5
python -m train.train_symbols --name symbols_strip_v1 --batch 4
python -m train.export_onnx --version symbols_strip_v1
python scripts/preview_schema.py --page p040 --source runtime
```

---

## Aktywne zadanie — Claude (backlog)

| Pole | Wartość |
|------|---------|
| **DONE** | prompt 011 — klasy listwy w YOLO, testy 164 passed |
| **Backlog** | scalanie strzałek potencjału; derive_auto_terminals poza p040 |

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
