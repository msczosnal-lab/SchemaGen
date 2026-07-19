# KOLEJNE ZADANIE — wczytaj ten plik po wiadomości od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

**Wizja:** [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md) — trzy filary + relacje.

---

## Stan (2026-07-05) — zmiana kierunku: GT = graf jawny (labeler v2)

| Prompt / kamień | Status |
|-----------------|--------|
| **001–004** symbole + OCR + linie + graph-builder | ✅ DONE |
| **011-strip-yolo-classes** | ✅ DONE — zlaczka/mostek/strzalki w YOLO |
| **012-mostek-orientacja** | ✅ DONE — D4 + eksemplarze |
| **014-tiling** | ✅ kod DONE — tiled_export + detect_tiled |
| **015-relations-layer** | ✅ DONE — RelationResolver |
| **019-fable5-terminals-lines** | ✅ DONE — analiza; findings zaakceptowane |
| **018-lines-quality** | ✅ DONE — drugi przebieg Hough, paleta, diag_lines (**226 pytest**) |
| **018-terminals-strategy** | ⏸ WSTRZYMANE — reguły terminali (wzorce klas) wchłania 022/023 |
| **022-labeler-graph-v2** | ✅ DONE — GT v2, remap diff, labeler canvas |
| **023-runtime-graph-alignment** | 🔵 **AKTYWNE** (Cursor) — emisja connections OD–DO |
| **016-e2e-metrics** | ⏳ KOLEJKA |
| **Harness walidacji** | ✅ `preview_schema.py`, `diff_gt_runtime.py`, `eval_val_pages.py` |

**Findings:** [`sync/analysis/019-terminals-lines-findings.md`](analysis/019-terminals-lines-findings.md) (+ Poprawka runda 1)

**Strona referencyjna:** p027 (szyna listwy), p040 (regresja connections)

---

## Stan (2026-07-19) — 023 DONE, retrain FAIL, trzy nowe tory

| Prompt | Status | Model |
|--------|--------|-------|
| **023-runtime-graph-alignment** | ✅ DONE — p028 conn 4/42 → 10/42, śr. 21.24 → 21.50, pytest 329 |
| **026-retrain-fail-diag** | ✅ ZDIAGNOZOWANE — 480 bbox / 20 klas, train = 1 strona. Tor modelu **zamrożony** na `symbols_tiled_v1-2` | — |
| **027-gt-cleanup-class-merge** | 🟡 Krok1+2 DONE (Sonnet 5) — eksport po `type`; Krok3 (scalenia) czeka na Filipa | Sonnet 5 |
| **025-labeler-audit** | 🔵 AKTYWNE — zły page_id / złe bboxy, audyt całości | Opus 4.8 (A/B) → Sonnet 5 (C) |
| **024-conn-remap-precision** | 🔵 AKTYWNE — remap fail 118 + precyzja 0.05 | Opus 4.8 |
| **028-element-review-v2** | ✅ DONE — rozbieżność 163/160 = `tag_to_class` vs `bbox_class` (3 bboxy p029, `type=styki`/`tag=SAF1-3`); `symbol-symmetry.yaml`; **1053 kafle, sufit wariantu 1 = 76,7 %**; pytest 523 | Opus 4.8 |

**028 — czeka na Filipa:** przegląd symetrii 12 klas zakresu 5–30 inst. w `element_review.py`
(11 z nich bez wpisu ⇒ wariant 1T da 2 kafle zamiast 128) + decyzja wariant 1T tak/nie:
[`sync/analysis/028-augmentacja-projekt.md`](analysis/028-augmentacja-projekt.md).
[RYZYKO] `data/labeled_tiled/` nieaktualny (12 kafli train, klasy `saf1`/`1`/`10`) — wymaga re-eksportu.

**Kolejność: 025 → 024, równolegle 027 + doznaczanie (Filip).** Hipoteza wspólnej przyczyny (rozjazd skali GT ↔ obraz) **obalona** — eksport zdrowy (`poza [0,1]: 0`, `pustych: 0`). Błąd labelera i porażka treningu to dwie osobne sprawy.

| Pole | Wartość |
|------|---------|
| **026** | [`prompts/026-retrain-fail-diag.md`](prompts/026-retrain-fail-diag.md) — zamknięte: przyczyną jest 480 bbox i train = p034; `v1-3` nie wchodzi do `registry.json` |
| **027** | [`prompts/027-gt-cleanup-class-merge.md`](prompts/027-gt-cleanup-class-merge.md) — Krok1+2 DONE, wynik: [`sync/analysis/027-export-type-fix.md`](analysis/027-export-type-fix.md) (179→61 klas na 199 stronach, 0 strat bbox). Bramka przeglądu poprawnie blokuje 556 bbox mimo >=5 inst. (`terminal_przylaczeniowy` 520, `styk_stycznika` 36) — **zamierzone**, Filip potwierdził (2026-07-19): to jest część Kroku 3 (przegląd przed treningiem), nie bug. Krok3 (przegląd + scalenia klas) czeka na Filipa. |
| **025** | [`prompts/025-labeler-audit.md`](prompts/025-labeler-audit.md) — priorytet: zapis pod złym page_id > błędy wyświetlania |
| **024** | [`prompts/024-conn-remap-precision.md`](prompts/024-conn-remap-precision.md) — najpierw metryka P/R/F1, potem breakdown, potem kod |

**Wykluczenie ze średniej GT:** `p031` (GT ~505 B, SCORE 0.00) → `config/gt-eval.yaml`. Po zmianie przeliczyć baseline 21.50.
[UWAGA] `p032` nie istnieje w `gt/`. `p040` jest w `val-pages.yaml`, ale **brak `gt/*p040.json`** — sprawdzić jako pierwszy trop w 025.

---

## ~~Aktywne zadanie — Cursor (023-runtime-graph-alignment)~~ DONE

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/023-runtime-graph-alignment.md`](prompts/023-runtime-graph-alignment.md) |
| **Wynik** | p028 10/42 (cel ≥15 nie osiągnięty); zysk wyłącznie na p028 |

---

## ~~Aktywne zadanie — Claude (022-labeler-graph-v2)~~ DONE

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/022-labeler-graph-v2.md`](prompts/022-labeler-graph-v2.md) |
| **Cel** | Krok 0: remap ID w diff_metrics; SchematicGraph; kompilacja → SchemaModel; labeler 2 tryby + prefill; migrator v1 |
| **Decyzja domenowa** | Bez junction — złączka do 4 terminali (left/right zwarte `link`, top/bottom odczepy); linia zawsze terminal→terminal |
| **Zależność** | 018-lines-quality ✅; wzorce terminali z 018-terminals (koncepcja) |

---

## ~~Aktywne zadanie — Claude (018-terminals-strategy)~~ WSTRZYMANE 2026-07-05

Decyzja Filipa: przebudowa GT na graf jawny (022) przed dalszymi heurystykami runtime. TerminalResolver/węzły-na-ścieżce wchodzą do 023-runtime-graph-alignment.

---

## ~~Aktywne zadanie — Claude (018-lines-quality)~~ DONE

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/018-lines-quality.md`](prompts/018-lines-quality.md) |
| **pytest** | **226 passed** (213 + 13 nowych) — potwierdzone na PC Filip 2026-07-04 |
| **Smoke Filip** | p027 `preview_lines` (szyna ≥90% rzędu), p040 `eval_val_pages` (bez regresji) — patrz `zw-to-filip.md` |

---

## ~~Kolejka — Claude (018-terminals-strategy)~~ → aktywne powyżej

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
