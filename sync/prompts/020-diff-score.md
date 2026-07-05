# Zadanie 020: Funkcja celu GT↔runtime (score 0–100)

**Status:** ZAIMPLEMENTOWANE przez Claude 2026-07-05 — do weryfikacji w Cursor (patrz `sync/zw-to-filip.md`)
**Cel:** skalarny score zbieżności runtime→GT jako metryka pętli iteracyjnej na p027. Najpierw metryka, potem 018-terminals mierzony tą metryką (decyzja Filip 2026-07-05).

## Kontekst

Harness istnieje: `scripts/diff_gt_runtime.py`, `scripts/eval_val_pages.py`, `backend/validate/diff_metrics.py`. Braki:

- brak warstwy **linii** (GT `LabelRecord.lines` vs runtime `graphic_lines`) — tylko liczności
- brak metryk **per klasa** symbolu (na p027 recall `Strzałka potencjału (wejściowa)` = 0 — sufit modelu YOLO, nie kodu)
- brak **P/R/F1** i **jednego skalara** — nie ma czym mierzyć postępu iteracji
- brak **historii/delty** między runami

**Strony referencyjne:** p027 (cel iteracji), p040 (regresja).

## Reguły (nie zmieniać bez zgody Cursor)

- Kontrakt `SchemaModel` / `GraphicLine` / `Connection` (`backend/models/schema.py`) — nietknięty
- `backend/recognize/` — w tym zadaniu **zero zmian** (tylko pomiar)
- Istniejące klucze wyjścia `diff_*` zostają (kompatybilność `eval_val_pages.py`) — nowe pola tylko dodawane
- Bez cloud API

## 1. `diff_lines` — nowa warstwa

Plik: `backend/validate/diff_metrics.py`

GT: `LabelRecord.lines` (przez `label_to_schema` → `schema.graphic_lines`), runtime: `runtime.graphic_lines`.

Dopasowanie geometryczne polilinii (nie IoU bboxa):

- rasteryzacja obu zbiorów do masek (grubość ~5 px) lub próbkowanie punktów co N px
- **coverage GT** = % punktów linii GT w odległości ≤ `line_match_tol` (config, start 8 px) od dowolnej linii runtime → recall
- **coverage RT** analogicznie w drugą stronę → precision
- wynik: `{gt_count, runtime_count, precision, recall, f1, per_role: {wire: {...}, bus: {...}}}`

## 2. `diff_components` — per klasa

Rozszerzyć wynik o `per_class: {typ: {gt, rt, match, precision, recall, f1}}`. Matching bez zmian (IoU ≥ 0.5, typ musi się zgadzać).

Oddzielnie flaga strat modelu: klasa z `gt>0` i `match==0` → lista `model_gaps` (np. strzałka wejściowa na p027) — raportowane osobno, żeby nie gonić kodem błędów modelu YOLO.

## 3. `aggregate_score` — skalar 0–100

Nowa funkcja `aggregate_score(report: dict, weights: dict) -> dict`:

```
score = 100 * Σ w_i * f1_i   (warstwy: components, lines, connections, tags)
```

Wagi w **`config/eval-weights.yaml`** (nowy plik, loader w `backend/runtime_config.py`):

```yaml
eval_weights:
  components: 0.30
  lines: 0.25
  connections: 0.35
  tags: 0.10
line_match_tol: 8
```

Zwraca `{score, per_layer: {warstwa: {f1, weight, contribution}}}`. Warstwa bez GT (gt_count=0) → wyłączona z sumy, wagi renormalizowane.

## 4. `diff_gt_runtime.py` — historia + delta

- każdy run z `--json` dopisuje wpis do `data/output/diff_gt_runtime/{page_id}_history.jsonl` (timestamp, score, per_layer, git HEAD jeśli dostępny)
- na stdout: score + **delta vs poprzedni run** (`Δscore`, per warstwa) + top-3 kubły strat (największe `only_gt`)
- `model_gaps` wypisywane oddzielnie z adnotacją `[MODEL]` (wymaga retrain, nie kodu)

## 5. Testy

`backend/tests/test_diff_metrics.py` (rozszerzyć/utworzyć):

- `diff_lines`: identyczne linie → f1=1.0; przesunięcie > tol → 0; częściowe pokrycie
- `per_class` + `model_gaps` na syntetycznych schematach
- `aggregate_score`: wagi, renormalizacja przy pustej warstwie, monotoniczność
- istniejące 226 testów bez regresji

## Definition of Done

1. `pytest backend/tests labeler/tests` — 226 + nowe passed
2. `python scripts/diff_gt_runtime.py --page p027 --json` — score + historia + delta działa
3. `python scripts/eval_val_pages.py --page p040` — bez regresji, wynik zawiera score
4. Wpis w `sync/zw-to-filip.md`: score bazowy p027 i p040 (punkt odniesienia dla 018-terminals)
5. `sync/commit-message.txt`: `[Cursor] 020: diff score 0-100 + diff_lines + per-class + historia`

## Po tym zadaniu

018-terminals-strategy — każda zmiana TerminalResolver mierzona `Δscore` na p027 + regresja p040. Progi do `config/`, nie hardcode ([RYZYKO] overfit na p027).
