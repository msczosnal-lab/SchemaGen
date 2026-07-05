# Skrzynka: Filip → ZW

> Pisze **tylko Filip** (Cursor). ZW czyta na starcie sesji.

---

## 2026-07-05 [Cursor] — loop 021 w toku (Fable review)

**Baseline:** p027 SCORE **48.45** (GT po relabelu linii: 155 bbox, 96 wire). p040 **45.30** (bbox 17/19).

| iter | zmiana | p027 SCORE | wynik |
|------|--------|------------|-------|
| it1 | `_merge_horizontal_rails` (line_tracer) | 48.42 | **COFNIĘTE** (Δ≤0 vs 48.50; lines R↑ ale SCORE↓) |
| it2 | `yolo_conf_threshold` 0.25→**0.20** | **49.44** | **OK** (+0.99), bbox **86/155** |

**p040 regresja:** score 45.30 (było 33.39), bbox 17/19 (było 9/19) — **bez regresji**.

Kubły [MODEL] bez zmian: `strzalka_potencjalu_wejsciowa`, `zwarta_listwa_zlaczek`. Następny kubeł kodu: linie (precision 0.29) lub tagi (7).

Stan: `sync/loop-021-state.json`. Commit pending: `[Cursor] loop 021 it2: yolo conf 0.20 — p027 49.44`

---

## 2026-07-05 [Cursor] — loop 021 STOP (plateau)

**p027:** 48.50 → **49.93** (+1.43) | **p040:** 45.30 (bez regresji)

Zaakceptowane: `yolo_conf_threshold` 0.25→0.20→**0.18** (config/runtime.yaml).

STOP: plateau it5/it6 + kubły kodowe wyczerpane ([MODEL] strzałki, YOLO recall). Log: `sync/loop-021-log.md`.

Commit: `[Cursor] loop 021: p027 score 48.5→49.93`

---

## 2026-07-05 [Cursor] — GT linie p027 relabeled (labeler)

Filip poprawił linie GT na p027 w labelerze. **Bez zmian kodu** — baseline loop 021 odświeżony.

| | Było | Teraz |
|---|------|-------|
| Linie GT | 93 (w tym **2× bus**) | **96× wire** (0 bus) |
| Bbox GT | 154 | 155 |
| SCORE p027 | 48.50 | **48.42** |
| lines F1 | 0.430 (P=0.311 R=0.701) | **0.432** (P=0.289 R=0.852) |
| components F1 | 0.692 (82/154) | 0.689 (82/155) |
| % dł. linii GT bez RT | ~30% | **~15%** |

Bus→wire w GT zgodne z runtime (`wire` only). Metryki diff bez zmian.

`sync/loop-021-state.json`: `score_start_p027` = `score_current_p027` = **48.42**.

Commit pending: `[Cursor] sync: GT linie p027 relabeled — baseline score 48.42`

---

## 2026-07-05 [Cursor] — fix: typ GT z `tag` (diff components zgodny z YOLO)

**Problem:** `label_to_schema` używał `class_name` (= `element` dla wszystkich bboxów labelera). Runtime YOLO ma kanoniczne id (`zlaczka`, `mostek`…). Diff wymaga zgodności typu → **0/154** mimo IoU≥0.5 u 82 bboxów.

**Fix:** `component_type_from_bbox()` (`class_map.py`) — gdy `class_name==element`, typ z `tag_to_class(tag)`. Podpięte w `label_to_schema`.

| Strona | SCORE (po fix) | bbox match |
|--------|----------------|------------|
| **p027** | **48.50** | **82/154** |
| p040 | do ponownego smoke | — |

`[MODEL]` gaps p027: `strzalka_potencjalu_wejsciowa` (4 GT, 0 RT), `zwarta_listwa_zlaczek` (2 GT, contextual).

pytest: **193 passed** (+2 nowe).

Commit pending: `[Cursor] GT type z tagu w label_to_schema — diff components zgodny z YOLO`

---

## 2026-07-05 [Cursor] — 020-diff-score DONE: weryfikacja + score bazowy

**Status:** commit `45f8cf7b` **[Claude] 020: diff score 0-100…** — **zaakceptowany** po review i smoke na PC Filip (`.venv311`).

### Testy

| Suite | Wynik |
|-------|-------|
| `pytest backend/tests labeler/tests` | **191 passed**, 0 failed |
| `test_diff_metrics.py` | **12 passed** (3 stare + 9 nowych) |

Uwaga: dokumentacja mówiła o 226+9 — na HEAD jest **191** testów w tych dwóch katalogach (brak regresji: wszystkie zielone). Drift licznika vs wpis 018-lines — nie bloker.

### Score bazowy (punkt odniesienia dla 018-terminals)

| Strona | SCORE | Warstwy aktywne (wagi znormalizowane) | Uwagi |
|--------|-------|----------------------------------------|-------|
| **p027** | **16.56/100** | components f1=0.00 (0/154 bbox), **lines f1=0.43** → 16.6 pkt, tags f1=0.00 | GT: 154 bbox, 93 linii, 0 conn. RT: 83 sym, 208 linii, 69 conn. `[MODEL]` gap: typ `element` (YOLO bez trafień IoU≥0.5) |
| **p040** | **33.39/100** | bbox 9/19, conn **0/0** (GT conn=0 — bez regresji), tags 27 | `eval_val_pages.py --page p040` |

### Smoke 020

- `diff_gt_runtime.py --page p027` — SCORE + top kubły + `[MODEL]` OK
- `--json` → `data/output/diff_gt_runtime/*_history.jsonl` (3 wpisy), delta **Δ +0.00** przy powtórce
- `eval_val_pages.py --page p040` — `mean_score` na stdout, connections bez regresji
- **`diff_lines` na p027 (6617×4678): 0.58 s** — poniżej progu 10 s, `step=4px` (tol/2) zostaje

### Review kodu

- Stare klucze `match` / `only_gt` / `only_runtime` zachowane we wszystkich `diff_*`; nowe pola (`precision`, `recall`, `f1`, `per_class`, `model_gaps`, `per_role`) tylko dodane
- Commit 020 **nie dotyka** `backend/recognize/`
- `config/eval-weights.yaml` + loader `eval_settings()` / `eval_weights()` / `line_match_tol()` OK

### [RYZYKO] Windows cp1250

`diff_gt_runtime.py --json` przy drugim runie: `UnicodeEncodeError` na znak `Δ` w stdout (bez `PYTHONIOENCODING=utf-8`). JSON + historia zapisują się poprawnie; crash po zapisie. Opcjonalny fix: `Δ` → `d` lub `errors=replace` — nie bloker merge.

### Następne

**018-terminals-strategy** — każda zmiana TerminalResolver mierzona **Δscore na p027** + regresja **p040**. Progi do `config/`, nie hardcode.

Commit pending: `[Cursor] 020: diff score verified — baseline p027/p040`

---

## 2026-07-05 [Filip] — GT p027: strzałki wejściowe doznaczone

**Status:** w labelerze oznaczone **strzałki potencjału wejściowe** (wcześniej brak w GT — runtime 0× `wejsciowa` na p027).

| Co | DB `p027` (po zapisie) |
|----|------------------------|
| `Strzałka potencjału (wejściowa)` | **4** |
| `Strzałka potencjału (wyjściowa)` | 80 |
| `złączka` | 56 |
| `mostek` | 9 |

**Następny krok danych:** eksport w labelerze → `dataset_export` → retrain YOLO (klasa 7 była rzadka w `labeled_tiled`). Po nowym ONNX: `preview_schema.py --page p027 --source both` / `diff_gt_runtime.py`.

**Runtime:** recall `wejsciowa` nadal wymaga nowego modelu; `arrow_supplement` nie pomoże, jeśli raw YOLO da choć jedną detekcję wyjściową na stronie (H9b).

**Jutro:** loop w Cursorze (`/loop 20m` lub dynamiczny na commit-log) — `diff_gt_runtime` + `preview_schema --source runtime` na p027; regresja p040. GT = wzorzec, poprawiamy runtime.

---

## 2026-07-04 [Cursor] — 018-lines DONE: pytest 226 passed, smoke p027/p040 = Filip

**Kod Claude zaakceptowany po review** (szczegóły w `zw-to-filip.md`). Na PC Filip: `pytest` → **226 passed**.

**Filip — smoke wizualny (przed 018-terminals):**

```powershell
python scripts/preview_lines.py --page data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p027.png
python scripts/diag_lines.py --page p027
python scripts/eval_val_pages.py --page p040
python scripts/preview_schema.py --page p027 --source runtime
```

Kryteria: szyna y≈2945 jako wire ≥90% rzędu; p040 connections bez regresji; niebieski z grupą `blue_wire`.

**Następne dla Claude:** [`018-terminals-strategy.md`](prompts/018-terminals-strategy.md).

---

## 2026-07-04 [Filip] — GT p027: strzałki + terminale (komplet)

**Status:** wszystkie strzałki (klasy 7/8) i terminale na p027 poprawione w labelerze.

| Co | Uwagi |
|----|--------|
| Strzałki listwy | Doznaczone przy złączkach (wcześniej TP bez GT — findings H9) |
| Terminale złączek | Skorygowane na całej stronie |
| Następny krok danych | `dataset_export` po zapisie; opcjonalnie `preview_schema.py --page p027 --source gt --rebuild-conn` jako referencja topologii |

**Bloker runtime p027** nadal = jakość linii (018-lines) + TerminalResolver (018-terminals), nie GT.

---

## 2026-07-04 [Cursor] — Review 019 DONE + prompty 018-lines / 018-terminals

Temat: **Findings zaakceptowane (Poprawka runda 1). Implementacja: najpierw linie, potem terminale.**

| Pole | Wartość |
|------|---------|
| **Findings** | [`sync/analysis/019-terminals-lines-findings.md`](analysis/019-terminals-lines-findings.md) — zaakceptowane + § Poprawka (runda 1) |
| **018-lines-quality** | [`sync/prompts/018-lines-quality.md`](prompts/018-lines-quality.md) — **AKTYWNE** (Claude) |
| **018-terminals-strategy** | [`sync/prompts/018-terminals-strategy.md`](prompts/018-terminals-strategy.md) — kolejka po 018-lines |
| **Decyzja** | `_nodes_on_net` (węzły-na-ścieżce) w 018-terminals; `_point_at_node` nietknięte w rundzie 1 |

Commit pending: `[Cursor] sync: review 019 + prompty 018-lines/018-terminals`

---

## 2026-07-04 [Cursor] — Prompt 019: analiza terminali + linii dla Fable 5

Temat: **Jakość ~65%. Bloker: terminale + linie (nie symbole). Analiza przed implementacją.**

| Pole | Wartość |
|------|---------|
| **Prompt** | [`sync/prompts/019-fable5-terminals-lines-analysis.md`](prompts/019-fable5-terminals-lines-analysis.md) |
| **Wykonawca** | Claude (Fable 5), główny PC z pełnym repo |
| **Zakres** | Analiza kodu (`net_builder`, `line_tracer`, `line_classifier`, `line_sieve`, `mostek_terminals`, `graph_builder`) + hipotezy (fragmentacja linii, kolizja kolorów enclosure/pe_wire, brak grupy czerwonej, sito demotujące bus wire p027) + plan `TerminalResolver` |
| **Kontekst smoke** | `sync/fable5-smoke-context.md` (p027/p035/p040, preview_detection conf=0.25) |
| **Wynik** | `sync/analysis/019-terminals-lines-findings.md` + propozycja podziału na `018-lines-quality`/`018-terminals-strategy` |

Commit pending: `[Cursor] sync: prompt 019 Fable5 analiza terminali i linii`

---

## 2026-07-04 [Cursor] — Faza 5 DONE (prompt 015) + kolejka 016

Temat: **RelationResolver wdrożony. Smoke p040 + common_terminal = Filip.**

| Pole | Wartość |
|------|---------|
| **pytest** | **213 passed** (+6 relation_resolver, +3 diff_metrics) |
| **015** | `backend/recognize/relation_resolver.py` — tag proximity, wire labels, scalanie strzałek, context runtime |
| **016** | prompt + `eval_val_pages.py` + `diff_metrics.py` (szkielet batch eval) |
| **net-builder** | nietknięty |

### Filip — smoke (TERAZ)

```powershell
python scripts/preview_schema.py --page p040 --source runtime
python scripts/diff_gt_runtime.py --page p040
python scripts/eval_val_pages.py --page p040
```

Sprawdź: tagi na bboxach, `Connection.potential`, brak conn między strzałkami o tej samej nazwie, `--rebuild-conn` GT ≈ 15.

Uzupełnij `common_terminal:` w `config/mostek-orient.yaml`.

### Claude — następne

Prompt **016** gdy Filip zaakceptuje smoke 015: [`sync/prompts/016-e2e-metrics.md`](prompts/016-e2e-metrics.md)

Commit pending: `[Cursor] recognize: relation resolver (prompt 015) + eval val-pages skeleton`

---

## 2026-06-28 [Cursor] — Domknięcie sesji ZW: pytest OK (151 passed)

Temat: **Sesja ZW zamknięta. Filar POŁĄCZENIA DONE. Następny kamień = filar SYMBOLE (detekcja listwy).**

| Pole | Wartość |
|------|---------|
| **git pull** | main up to date; commit ZW `865b1aac` (+ `clear_gt_connections.py`, zw-to-filip ZAMKNIĘCIE) |
| **pytest** | `backend/tests` + `labeler/tests` → **151 passed** (4.3s) |
| **Nowe testy** | `test_net_builder`: +3 (`star`, `require_terminal`×2); `test_line_sieve`: +4 (mostki, `recover_terminal_bridges`) |
| **`--rebuild-conn` p040** | **15** par `[GT-conn]`, bez gwiazdy `8:mostek` |
| **GT po czyszczeniu** | `clear_gt_connections.py --apply` → 19 bbox, 17 linii, **0 conn** (connections = wynik algorytmu) |

### Review diffów (Cursor akceptuje)

| Moduł | Werdykt |
|-------|---------|
| `net_builder.py` | terminal=granica scalania — listwa 2 nety, fragmentacja/T bez regresji |
| `line_sieve.py` | `recover_terminal_bridges` + ochrona mostków terminal↔terminal |
| `graph_builder.py` | krok 4b recover, `connection_require_terminal` z config |
| `preview_schema.py` | `--rebuild-conn`, overlay trasowany, `[GT-conn]` read-only |
| `clear_gt_connections.py` | NOWY — czyści stale conn w SQLite, zostawia bbox/linie/terminale |

### Wniosek sesji (potwierdzony)

- **Net-builder OK** na czystym GT (15 conn).
- **Bloker runtime:** YOLO wykrywa **9 z 19** bbox na p040 — brak złączek/mostków/strzałek potencjału. Gwiazda runtime → skutek detekcji, nie net-buildera.
- **Decyzja:** connections w GT nie są wzorcem; walidacja przez `--rebuild-conn` / runtime po poprawie detekcji.

### Następny kamień — Filip (filar SYMBOLE)

1. Doznaczenie klas listwy (złączka / mostek / strzałka potencjału) na p040+ — **decyzja o re-train YOLO** (następna sesja, nie teraz)
2. Po detekcji: `diff_gt_runtime` / `--rebuild-conn` na runtime ma sens

**NIE teraz:** atlas QET, trening YOLO bez decyzji Filipa.

### Backlog — Claude

- Scalanie strzałek potencjału po nazwie; `derive_auto_terminals` poza p040; tuning Hough

---

## 2026-06-27 [Filip] — GT linii DONE, strona testowa p040

Temat: **Linie oznaczone. Walidacja e2e na p040.**

| Pole | Wartosc |
|------|---------|
| **GT linii** | ✅ `22_A_153_PL_Adamed_AGV_SA2_20250706_p040` |
| **Smoke Cursor** | 9 sym, 1321 linii (Hough), **4 conn**, 72 OCR |

### Następne

- Filip: ocena 4 connections vs GT od–do na p040
- Cursor: `preview_schema.py` + diff GT vs runtime
- Claude: poprawki po feedbacku (Hough / tolerancja końców wire)

---

## 2026-06-25 [Cursor] — Commit OCR/preview + handoff Claude 004

Temat: **Smoke OCR/linie zaakceptowany. Claude → GraphBuilder.**

### Commit

`[Cursor] scripts: OCR worker venv + preview_lines + line tracer sampling`

### Claude — START

Wklej: [`sync/PROMPT-CLAUDE-004.md`](PROMPT-CLAUDE-004.md)

### Filip równolegle

- Labeler tryb **L** — GT linii p030
- Review autolabel bbox p051+

---

Temat: **Smoke OCR i linii na Adamed. GraphBuilder (004) dalej dla Claude.**

### OCR (DONE smoke)

- `.venv-ocr` — paddle 2.6 + paddleocr 2.9 **bez torch** (`scripts/setup_ocr_venv.ps1`)
- `scripts/ocr_worker.py` + delegacja w `PaddleOcrEngine` (auto gdy `.venv-ocr` lub torch w procesie)
- p035: **70 detekcji** z `import torch` w rodzicu — OK

### Linie (smoke + Poprawka)

- `scripts/preview_lines.py` — galeria overlay role/grupa
- p035: ~1672 segmentów — **za dużo szumu** (Hough łapie tekst/tło). Zgłosić kalibrację progów.

### Testy

```
pytest backend/tests labeler/tests train/tests  →  120 passed
```

### Następne

- Claude: **004-graph-builder** (gdy Filip zaakceptuje smoke)
- Filip: labeler tryb L, review autolabel bbox

Commit pending: `[Cursor] scripts: OCR worker venv + preview_lines`

---

Temat: **Push Claude (`96809b50`) zintegrowany. Konflikt w `line_classifier` rozwiązany.**

### Git

- `git pull` → fast-forward + stash pop
- Konflikt: `line_classifier._role_for` — **zostaje wersja Claude** (`_color_role_hint`, dash/device_stroke przed bus; `wire` z palety nie blokuje bus)
- `line_tracer`: Claude re-sample po merge + Cursor sampling w pasie prostopadłym

### Testy

```
pytest backend/tests labeler/tests train/tests
```

### Następne

- Claude: **004-graph-builder**
- Filip: labeler tryb L (GT linii), smoke Hough na Adamed p025–p035

Commit pending: `[Cursor] merge: line tracer sampling pas + sync po pull Claude 002/003`

---

## 2026-06-25 [Filip/Cursor] — 002 OCR DONE → Claude: linie + line tracer

Temat: **PaddleOCR wdrożony. Następny filar: połączenia (GT + runtime).**

### Co zrobione

- Claude: `backend/recognize/ocr_engine.py` + testy (commit `a4200e26`)
- Cursor: `scripts/preview_ocr.py` — wizualny smoke OCR
- YOLO: `symbols_atomic_v2` aktywny (mAP50≈0.92)

### Twoje zadanie (PRIORYTET #1)

[`sync/PROMPT-CLAUDE-002-LINES.md`](PROMPT-CLAUDE-002-LINES.md)

1. `002-labeler-lines-colors` — polyline wire/bus w labelerze
2. `003-line-tracer-classifier` — OpenCV line tracer

Po kodzie: pytest → `sync/zw-to-filip.md` → `[Claude] labeler: linie + line tracer (prompt 002/003)`

**Nie:** GraphBuilder (004), QET, trening YOLO.

Handoff: [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

### Filip — równolegle

```powershell
pip install paddlepaddle-gpu paddleocr
python scripts/preview_ocr.py --page data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p035.png --lang latin
```

Commit pending: `[Cursor] scripts: preview_ocr + sync handoff po 002-ocr`

---

## 2026-06-24 [Cursor] — Pętla treningowa + handoff Claude OCR

Temat: **train_cycle, stały val, autolabel batch, delegacja filarów tekst/linie**

### Co zrobione (Cursor)

- `scripts/train_cycle.py` — export → train → ONNX → preview + log JSONL
- `config/val-pages.yaml` — 6 stron Adamed (p025–p050) jako stały val
- `train/dataset_export.py` — podział train/val ze stałej listy
- Audyt: `data/output/class_report_audit.json` (75 stron, 2762 bbox, 24 klasy YOLO)
- Autolabel: `data/output/autolabel_batch_log.json` (+138 stron, 782 propozycje)

### Filip — teraz

1. **Review autolabel** w labelerze (incognito) — propozycje modelu wymagają akceptacji
2. `python scripts/train_cycle.py --name symbols_atomic_v2`
3. Galeria: `data/output/preview_batch/symbols_atomic_v2/index.html`

### Claude — PRIORYTET #1

[`sync/PROMPT-CLAUDE-002-OCR.md`](PROMPT-CLAUDE-002-OCR.md) — **002-ocr-engine** (PaddleOCR)

Po OCR: [`sync/PROMPT-CLAUDE-002-LINES.md`](PROMPT-CLAUDE-002-LINES.md) — linie w labelerze + line tracer.

Handoff: [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

Commit pending: `[Cursor] train: train_cycle + fixed val-pages + autolabel batch`

---

## 2026-06-15 [Filip/Cursor] — Reset WRT01, archiwum starych bboxów

Temat: **WRT01 od zera — workflow bbox-first + paleta (010). Claude wstrzymany.**

### Co zrobione

- Archiwum: `data/archive/wrt01-legacy-2026-06-15/`
  - 11 stron, **406 bboxów** (stary workflow: opis przed paletą / bez typów)
  - `annotations/*.label.json`, kopia `labeled/`, `MANIFEST.json`
- SQLite: usunięte adnotacje `SchematWRT01_*`, status stron → `new`
- `data/labeled/`: wyczyszczone eksporty WRT01
- Skrypt: `scripts/archive_wrt01_reset.py` (`--apply`)

### Filip — teraz

1. Wyczyść localStorage labelera (`schemagen:draft:*`) lub okno prywatne
2. `python -m labeler.app` — zacznij od `SchematWRT01_p013`
3. Bbox → typ z palety → Ctrl+S
4. Stary `symbols_v1.onnx` **nie** jest benchmarkiem nowego GT

### Claude

⏸ Wstrzymany (brak sesji). Po powrocie: **002 OCR** — bez zmian w handoff.

Handoff: [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

Commit pending: `[Cursor] data: archive WRT01 legacy bboxes + reset labeler GT`

---

## 2026-06-15 [Filip/Cursor] — 010 DONE (Cursor) → Claude: 002 OCR

Temat: **Labeler bbox-first gotowy. Następny filar: tekst (PaddleOCR).**

### Co zrobione (Cursor, prompt 010)

- `config/symbol-palette.yaml` — 52 hasła PL
- `backend/symbol_palette.py` + `GET /api/symbol-palette`
- Labeler: bbox bez opisu → picker typu, stan nieprzypisany, wolne hasło
- `docs/labeling-guide.md`, `docs/adr/device-block-stub.md`
- Testy: `test_symbol_palette.py`, `test_palette_api.py`, export YOLO z pustym tagiem

**Filip:** `python -m labeler.app` — narysuj bbox, wybierz typ po prawej.

### Twoje zadanie (PRIORYTET #1)

[`sync/prompts/002-ocr-engine.md`](prompts/002-ocr-engine.md) — **filar tekst**

Handoff: [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)  
Start: [`sync/PROMPT-CLAUDE-002-OCR.md`](PROMPT-CLAUDE-002-OCR.md)

### Po kodzie

- `pytest backend/tests labeler/tests`
- `sync/zw-to-filip.md`
- `sync/commit-message.txt` = `[Claude] recognize: PaddleOCR engine (prompt 002-ocr)`

Commit pending: `[Cursor] labeler: bbox-first + symbol palette (prompt 010)`

---

## 2026-06-15 [Filip/Cursor] — Trzy filary + rezygnacja z atlasu QET

Temat: **Interpretacja wizualna schematu bez QET. Relacje — po zebraniu filarów.**

### Wizja (źródło prawdy)

[`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md)

**Trzy metody odczytu schematu:**
1. **Tekst** — OCR (tagi, opisy)
2. **Symbole graficzne** — YOLO + bboxy w labelerze
3. **Połączenia** — linie wire/bus (labeler + line tracer)

**Następnie:** relacje — tekst przypisany do symbolu, symbol połączony z symbolem (`004-graph-builder`).

### Rezygnacja

- **Atlas QET, kurator TAK/NIE, cropy, `symbol-reference.yaml` w UI** — nie używamy na tym etapie.
- Kod `backend/atlas/` może zostać w repo — **martwy**, bez runtime i bez pickera.

### Aktywne zadanie Claude

Nadal **010** (filar symbole): bbox-first + `config/symbol-palette.yaml` (same hasła PL, bez PNG).

Paleta: `backend/symbol_palette.py` — **nie** pakiet `atlas`.

Handoff: [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

Commit pending: `[Cursor] sync: trzy filary interpretacji, rezygnacja QET, wizja schematic-interpretation`

---

## 2026-06-15 [Filip/Cursor] — Etap 1: detekcja elementów + prompt 010

Temat: **Labeler bbox-first + paleta haseł. Kurator QET wstrzymany.**

### Decyzje Filipa

- **Etap 1:** rozpoznawanie **elementów** na schemacie (YOLO klasa `element`). Tagi, połączenia, charakterystyki — później, proceduralnie.
- **Workflow labelera:** najpierw **zaznacz obszar**, potem **wybierz typ** z biblioteki (odwrotnie niż dziś).
- **Paleta:** ~40–60 najczęstszych haseł PL — **bez** cropów QET w UI (brzydkie, domain gap).
- **Filip:** oznacza więcej schematów, krótkie hasła, wyjątki ręcznie → duża baza bboxów → re-train.
- **Złożone urządzenia** (box + terminale): na razie obrys + hasło blokowe; osobny tryb — faza 2.
- **Kurator atlasu QET (TAK/NIE):** wstrzymany do fazy 2.

### Twoje zadanie (PRIORYTET #1)

[`sync/prompts/010-labeler-bbox-first-palette.md`](prompts/010-labeler-bbox-first-palette.md)

Handoff: [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)  
Start: [`sync/PROMPT-CLAUDE-010.md`](PROMPT-CLAUDE-010.md)

### Po kodzie

- `pytest backend/tests labeler/tests`
- wpis w `sync/zw-to-filip.md`
- `sync/commit-message.txt` = `[Claude] labeler: bbox-first + symbol palette (prompt 010)`

### Nie rób

- Kurator :8766, multi-class YOLO, line tracer, GraphBuilder w tej sesji.

Commit pending: `[Cursor] sync: handoff prompt 010 bbox-first + paleta, etap 1 detekcja elementów`

---

## 2026-06-14 [Filip/Cursor] — BUILD M0 DONE + priorytet 008a

Temat: **Trening + ONNX + inferencja u Filipa zamknięte. Następne zadanie Claude = 008a (QET atlas).**

### Co zrobione lokalnie (Filip, RTX 2080)

- Odbudowa **`.venv311`** (Py 3.11, torch cu121) — `.venv` (Py 3.14 CPU) **nie używać** do GPU.
- `train_symbols` 30 epok → `data/runs/symbols_v1/weights/best.pt`, mAP50 ≈ **0.085**
- `export_onnx` → `data/models/symbols_v1.onnx`, `registry.json` active=symbols_v1
- Smoke inferencji: **5 detekcji** na p013 przy `conf=0.05` (0 przy domyślnym 0.25 — słaby model, pipeline OK)
- onnxruntime CUDA: brak `cublasLt64_12.dll` → fallback CPU (wystarczy na teraz)

Plan sesji: [`sync/PLAN-TYMCZASOWY.md`](PLAN-TYMCZASOWY.md)

### Twoje zadanie (PRIORYTET #1)

[`sync/prompts/008-symbol-atlas-extract.md`](prompts/008-symbol-atlas-extract.md) — **faza 1 tylko QET**

Handoff: [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

### Reguły po BUILD M0

- **Nie** implementuj ponownie 005/006/001 bez `## Poprawka` od Cursor.
- **Nie** zakładaj, że Filip ma `best.pt` — pytaj / czytaj `filip-to-zw.md`.
- **Nie** cytuj metryk treningu bez `symbols_v1_train_summary.json` od Filipa.
- Pełny trening YOLO = tylko u Filipa.

Commit pending: `[Cursor] sync: BUILD M0 done, handoff 008a + PLAN-TYMCZASOWY`

---

## 2026-06-14 [Filip/Cursor] — BUILD M0: podział GPU

Temat: **005 = kod u Claude (ZW), trening u Filipa (RTX 2080)**

**Claude (PC ZW):** tylko implementacja — `dataset_export`, `train_symbols`, testy pytest. **Nie uruchamiaj** pełnego treningu (brak datasetu w gicie; słabszy PC).

**Filip (RTX 2080):** po Twoim commicie — export + train lokalnie (komendy w `zw-to-filip.md`).

Gotowy prompt startowy: [`sync/PROMPT-CLAUDE-005.md`](PROMPT-CLAUDE-005.md)

---

## 2026-06-14 [Filip] — BUILD M0: pierwszy trening YOLO

Temat: **Dataset gotowy w SQLite — priorytet = prompt 005, nie dalsze bboxy**

Stan datasetu (`data/schemagen.db`):

| Strona | Bboxów |
|--------|-------:|
| p013 | 75 |
| p014 | 99 |
| p015 | 152 |
| p016–p018 | 2–3 |
| p021 | 2 |
| p022 | 10 |
| p023 | 48 |
| **Razem** | **~394, 9 stron** |

W `data/labeled/` jest tylko stary eksport p013 — **batch eksport = część 005**.

**Twoje zadanie (PRIORYTET #1):** [`sync/prompts/005-train-symbols.md`](prompts/005-train-symbols.md)  
- `train/dataset_export.py` — SQLite → YOLO train/val + PNG z `data/raw/`  
- `train/train_symbols.py` — ultralytics YOLOv8n (batch≤8)  
- fix: `labeler/export.py` kopiuje PNG przy eksporcie  
- **pytest tylko** — trening GPU = instrukcja dla Filipa, nie wykonuj na ZW  

**Handoff:** [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

Po kodzie:
- wpis w `sync/zw-to-filip.md` (pliki + komendy PowerShell dla Filipa)
- `sync/commit-message.txt` = `[Claude] train: dataset export + YOLO train code M0 (prompt 005)`

**008a QET** — po 005. **Filip: nie oznaczaj więcej stron** do wyniku buildu.

---

## 2026-06-14 [Filip/Cursor] — AKCEPTACJA 007 + korekta źródeł + prompt 008a

Temat: **Zaakceptowana analiza atlasu; następne zadanie Claude = 008a (QET)**

Decyzje Filipa:
- **Akceptuję** [`docs/knowledge-sources-analysis.md`](../docs/knowledge-sources-analysis.md) v4 — atlas warstwowy, Siemens-first, ControlByte tylko jako słownik PL.
- **WRT01:** mam **tylko PDF schematu** — **nie mam** projektu EPLAN / Data Portal dla WRT01. Wpis o `C:\Users\Public\EPLAN\Data\` w inbox **nie dotyczy mnie** (to była notatka z przeszukania — ignoruj jako źródło runtime).
- **Drugi PDF:** schematy w **`sync/sources/`** — 4 PDF, 523 strony (Norblin, Adamed×2, PL5); manifest: `sync/sources/MANIFEST.json`
- **BBox-y:** kontynuuję p013–p015, potem kilka stron pod różnorodność typów.
- **Licencje:** crop-y atlasu lokalnie; surowe QET i IEC poza gitem; w repo YAML + wybrane PNG z atrybucją GPL.

**Twoje zadanie:** [`sync/prompts/008-symbol-atlas-extract.md`](prompts/008-symbol-atlas-extract.md) — **faza 1 tylko QET**  
**Handoff:** [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

Po ukończeniu 008a:
- `pytest backend/tests labeler/tests`
- wpis w `sync/zw-to-filip.md`
- `sync/commit-message.txt` = `[Claude] atlas: QET extract → symbol-reference.yaml (prompt 008a)`

**002-labeler-lines-colors** — możesz iść równolegle jeśli masz capacity; priorytet = 008a.

---

## 2026-06-14 [Cursor] — prompt 007: analiza źródeł wiedzy

Temat: **Ocena poradników, wideo, atlasów symboli — hybrid ze schematem WRT01**

Kontekst:
- Filip znalazł poradnik wideo o schematach; rozważa bazę symboli zamiast samych opisów z PNG.
- SchemaGen nadal potrzebuje schematu (bboxy, linie, tagi instancji); źródła zewnętrzne = warstwa referencyjna.

**Twoje zadanie:** [`sync/prompts/007-sources-analysis.md`](prompts/007-sources-analysis.md)  
**Filip uzupełnia:** [`sync/sources-inbox.md`](sources-inbox.md) (linki, PDF, notatki)  
**Wynik:** `docs/knowledge-sources-analysis.md`  
**Handoff:** [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)

To **research** — bez implementacji kodu. Pracuj iteracyjnie z Filipem.

Po rundzie 1:
- commit analizy
- `sync/commit-message.txt` = `[Claude] docs: knowledge sources analysis (prompt 007)`

002-labeler-lines-colors — **wstrzymane** do czasu zakończenia 007 lub decyzji Filipa.

---

## 2026-06-14 [Cursor] — prompt 003 DONE, następny: 002

Temat: **Review 003 OK — akceptacja. Kolejne zadanie: linie + kolory.**

Stan:
- Commit `20392b1` — hierarchia bboxów, relacje przestrzenne, UI drzewa, 24 testy (wg Claude).
- Review Cursor: zgodne z promptem 003, bez poprawek blokujących.

**Twoje zadanie:** `sync/prompts/002-labeler-lines-colors.md`  
**Handoff:** `sync/KOLEJNE-ZADANIE.md` (zaktualizowany)

Po ukończeniu:
- `pytest backend/tests labeler/tests`
- wpis w `sync/zw-to-filip.md`
- `sync/commit-message.txt` = `[Claude] labeler: linie i kolory (prompt 002)`

Nie psuj: auto-zapis, localStorage, hierarchii bboxów (`app.js?v=13`).

---

## 2026-06-14 [Cursor] — prompt 003 priorytet

Temat: **Hierarchia bboxów w labelerze — nowe aktywne zadanie**

Kontekst:
- Filip oznacza schematy warstwowo: duży bbox-blok + mniejsze bboxy w środku (rozłącznik, tag `-11` itd.).
- System dziś zapisuje płaską listę — brak relacji rodzic/dziecko i położenia względem siebie.
- YOLO bez zmian (wszystkie bboxy); hierarchia w JSON/schema.

**Twoje zadanie:** `sync/prompts/003-labeler-bbox-hierarchy.md`  
**Handoff:** `sync/KOLEJNE-ZADANIE.md` (zaktualizowany)

Po ukończeniu:
- `pytest backend/tests labeler/tests`
- wpis w `sync/zw-to-filip.md`
- `sync/commit-message.txt` = `[Claude] labeler: bbox hierarchy + spatial relations (prompt 003)`

002-labeler-lines-colors — **wstrzymane** do czasu merge 003.

---

## 2026-06-14 [Cursor] — koniec sesji

Temat: **Prompt 001 DONE — czeka review. Następny: 002 po akceptacji.**

Stan:
- Canvas bbox wdrożony (`5d16757`), testy 14/14 OK.
- Handoff na jutro: **`sync/NASTEPNA-SESJA.md`** — zacznij od tego pliku.
- `sync/KOLEJNE-ZADANIE.md` zaktualizowany → 002-labeler-lines-colors po review.

Do zrobienia jutro (Filip/Cursor):
1. Test ręczny labelera `:8765` + review `labeler/static/app.js`
2. Akceptacja 001 **lub** `## Poprawka (runda 1)` w `sync/prompts/001-labeler-canvas.md`
3. Oznacz 3–5 stron schematu w labelerze (`data/raw/`)

Dla Claude (po akceptacji 001): prompt **002-labeler-lines-colors.md**.

Commit pending: `[Cursor] sync: handoff sesja 2026-06-14`

---

## 2026-06-14 [Cursor]

Temat: **Kolejne zadanie = prompt 001-labeler-canvas**

Kontekst:
- Cursor dodal warstwe **linii graficznych + kolory semantyczne** (model, paleta, fixture v2).
- **Twoje pierwsze zadanie:** wczytaj `sync/KOLEJNE-ZADANIE.md` i zaimplementuj `sync/prompts/001-labeler-canvas.md`.
- Po ukonczeniu: pytest → `zw-to-filip.md` → `commit-message.txt` = `[Claude] labeler: canvas bbox (prompt 001)`.

Nowe pliki (nie edytuj bez potrzeby):
- `config/semantic-colors.yaml` — paleta kolorow (Filip uzupelni grupy)
- `backend/colors/palette.py` — match_color, resolve_stroke
- `backend/models/schema.py` — `GraphicLine`, `graphic_lines[]`
- `schema/fixtures/page1_expected.json` — przyklad z liniami

Zasada: **linia na schemacie ≠ polaczenie**. Prompt 002 (linie w labelerze) — po 001.

Commit pending: `[Cursor] model: graphic lines + semantic colors palette`

**Trigger Claude (2026-06-14):** push wszedł — kolejne zadanie. GitHub Action: komentarz `@claude` z instrukcją z `sync/KOLEJNE-ZADANIE.md`.

---

## 2026-06-14 [Cursor]

Temat: GitSync — nazwane commity + tagi Cursor/Claude
Kontekst: `sync/commit-message.txt` — wpisuj `[Claude] opis` po ukonczeniu promptu. Daemon: `Start-GitSync.cmd Claude`. Historia: `sync/commit-log.md`. Tagi: **Cursor** (Filip), **Claude** (ZW).
Do zrobienia po stronie Claude: **001-labeler-canvas.md**
Commit: `[Cursor] gitsync: named commits + tags Cursor/Claude`

---

## 2026-06-14 [Cursor]

Temat: Pivot offline — Faza 0 gotowa
Commit: (po GitSync)

---

## 2026-06-13 [Filip]

Temat: ~~MA1+MA1 EPLAN~~ — anulowane (pivot offline 2026-06-14)
