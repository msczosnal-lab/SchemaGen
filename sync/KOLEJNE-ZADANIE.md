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

## Aktywne zadanie — Cursor (023-runtime-graph-alignment)

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/023-runtime-graph-alignment.md`](prompts/023-runtime-graph-alignment.md) |
| **Cel** | net_builder: łańcuch rail + pary segmentów zamiast gwiazdy; baseline p028 w `sync/analysis/023-p028-conn-baseline.md` |
| **Równolegle** | Retrain YOLO `symbols_tiled_v1-3` (Filip GPU) — `tiled_export` zsynchronizowany z GT v2 |

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
