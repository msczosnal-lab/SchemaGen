# KOLEJNE ZADANIE — wczytaj ten plik po wiadomości od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

**Wizja:** [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md) — trzy filary + relacje.

---

## Stan (2026-07-04) — review 019 DONE, implementacja 018 WIP

| Prompt / kamień | Status |
|-----------------|--------|
| **001–004** symbole + OCR + linie + graph-builder | ✅ DONE |
| **011-strip-yolo-classes** | ✅ DONE — zlaczka/mostek/strzalki w YOLO |
| **012-mostek-orientacja** | ✅ DONE — D4 + eksemplarze |
| **014-tiling** | ✅ kod DONE — tiled_export + detect_tiled |
| **015-relations-layer** | ✅ DONE — RelationResolver |
| **019-fable5-terminals-lines** | ✅ DONE — analiza; findings zaakceptowane |
| **018-lines-quality** | 🔵 **AKTYWNE** (Claude) — Hough, paleta, diag_lines |
| **018-terminals-strategy** | ⏳ KOLEJKA — TerminalResolver + węzły-na-ścieżce |
| **016-e2e-metrics** | ⏳ KOLEJKA — po smoke Filipa (bez zmian) |
| **Harness walidacji** | ✅ `preview_schema.py`, `diff_gt_runtime.py`, `eval_val_pages.py` |

**Findings:** [`sync/analysis/019-terminals-lines-findings.md`](analysis/019-terminals-lines-findings.md) (+ Poprawka runda 1)

**Strona referencyjna:** p027 (szyna listwy), p040 (regresja connections)

---

## Aktywne zadanie — Claude (018-lines-quality)

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/018-lines-quality.md`](prompts/018-lines-quality.md) |
| **Cel** | Naprawa LineTracer (Hough pod kółka węzłów, skalowany merge_collinear), kalibracja niebieskiego w semantic-colors, overlay preview_lines, diag_lines.py |
| **Kryteria** | Szyna p027 ≥90% rzędu jako wire; p040 bez regresji; pytest ≥213 |
| **Następne** | [`018-terminals-strategy.md`](prompts/018-terminals-strategy.md) po akceptacji 018-lines |

---

## Kolejka — Claude (018-terminals-strategy)

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/018-terminals-strategy.md`](prompts/018-terminals-strategy.md) |
| **Cel** | TerminalResolver + terminal-patterns.yaml + `_nodes_on_net` (węzły na ścieżce) + labeler „zapisz wzorzec klasy" + rozdzielenie terminal_tol |
| **Zależność** | 018-lines-quality DONE |

---

## Aktywne zadanie — Filip

| Pole | Wartość |
|------|---------|
| **GT p027** | ✅ strzałki 7/8 + terminale — komplet (2026-07-04) |
| **Smoke 015** | `preview_schema.py`, `diff_gt_runtime.py`, `eval_val_pages.py --page p040` |
| **Config** | `common_terminal:` w `config/mostek-orient.yaml` |
| **Opcjonalnie** | `preview_schema.py --page p027 --source gt --rebuild-conn`; po eksporcie — `dataset_export` (retrain strzałek) |

---

## Kolejka — Claude (po smoke Filipa)

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/016-e2e-metrics.md`](prompts/016-e2e-metrics.md) |
| **Cel** | rozbudowa `eval_val_pages.py`, testy batch |

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
