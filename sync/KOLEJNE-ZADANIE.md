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

## Wniosek sesji 2026-06-28 (ZW) — net-builder OK, bloker = detekcja listwy

Walidacja na p040: net-builder na **czystym GT** = 15 czystych połączeń (zero gwiazdy).
Runtime (YOLO) wciąż robi gwiazdę do `sym_0:2`, bo **YOLO wykrywa 9 z 19 elementów** —
nie zna złączek/mostków/strzałek potencjału. Gwiazda w runtime = skutek braku detekcji
listwy, NIE błąd net-buildera. Stare GT-connections wyczyszczone (`clear_gt_connections.py`).
Decyzja: **connections = wynik algorytmu, nie GT.**

**NASTĘPNY KAMIEŃ:** detekcja elementów listwy (złączka / mostek / strzałka potencjału) —
doznaczenie klas + re-train YOLO, albo proceduralna detekcja listwy. Bez tego runtime nie
odtworzy topologii listew.

---

## Aktywne zadanie — Claude (backlog)

| Pole | Wartość |
|------|---------|
| **Detekcja listwy** | złączka/mostek/strzałka — filar SYMBOLE (po doznaczeniu Filipa) |
| **Strzałki potencjału** | scalanie o tej samej nazwie w jeden potencjał |
| **derive_auto_terminals** | tuning poza p040 |
| **Hough** | kalibracja per strona (pokrętła w `runtime.yaml`) |

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
