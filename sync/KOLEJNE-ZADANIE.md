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

## Aktywne zadanie — Fable 5 (analiza, Faza 4b)

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/019-fable5-terminals-lines-analysis.md`](prompts/019-fable5-terminals-lines-analysis.md) |
| **Cel** | Analiza kodu + plan (NIE implementacja): terminale (definicja Filipa, terminal-to-terminal) + linie (fragmentacja, bus wire p027, kolory losowe). Wynik: `sync/analysis/019-terminals-lines-findings.md` + propozycja podzialu na `018-lines-quality` / `018-terminals-strategy`. |
| **Priorytet** | 1) linie (bus wire p027), 2) terminale (TerminalResolver + terminal-patterns.yaml), 3) symbole/strzalki retrain. OCR odlozone. |
| **Kontekst smoke** | `sync/fable5-smoke-context.md` |

---

## Aktywne zadanie — Filip (smoke 015)

| Pole | Wartość |
|------|---------|
| **Smoke** | `preview_schema.py`, `diff_gt_runtime.py`, `eval_val_pages.py --page p040` |
| **Config** | `common_terminal:` w `config/mostek-orient.yaml` |

---

## Aktywne zadanie — Claude (po akceptacji smoke)

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/016-e2e-metrics.md`](prompts/016-e2e-metrics.md) |
| **Cel** | rozbudowa `eval_val_pages.py`, testy batch |

---

## ~~Aktywne zadanie — Claude (Faza 5)~~ DONE

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/015-relations-layer.md`](prompts/015-relations-layer.md) |
| **Status** | ✅ RelationResolver + 213 pytest |

---

## ~~Aktywne zadanie — Filip (po 015)~~ → smoke powyżej

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
