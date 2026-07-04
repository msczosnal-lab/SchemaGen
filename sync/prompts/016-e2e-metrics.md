# Zadanie 016: Walidacja e2e per filar (Faza 6)

**Status:** KOLEJKA — po akceptacji prompt 015  
**Model:** Opus, effort High  
**Pliki:** `scripts/eval_val_pages.py`, rozszerzenie `scripts/diff_gt_runtime.py`

## Kontekst

Trzy filary READ + RelationResolver (015) dają pełny `SchemaModel` runtime.
Potrzebujemy **metryk GT vs runtime** per filar na stałym zestawie stron walidacyjnych.

**Zestaw:** [`config/val-pages.yaml`](../config/val-pages.yaml) — 6 stron Adamed p025–p050.

## Cel

Jeden skrypt batch:

```powershell
python scripts/eval_val_pages.py
python scripts/eval_val_pages.py --page p040 --json
```

Raport JSON + podsumowanie tekstowe:

| Filar | Metryka |
|-------|---------|
| Symbole | recall/precision bbox (IoU≥0.5), per-klasa |
| Tekst | tag precision (GT tag vs runtime `Component.tag`) |
| Linie | recall segmentów wire (tolerancja px) — opcjonalnie v1 |
| Połączenia | F1 par `(from,to,kind)` — jak `diff_gt_runtime.py` |
| Relacje | `context_assignments` count; `Connection.potential` fill rate |

## Implementacja

### A. `scripts/eval_val_pages.py` (NOWY)

- Wczytaj `val_pages` z YAML.
- Dla każdej strony: GT z `label_to_schema(load_annotation)` vs `recognize_file`.
- GT connections: opcjonalnie `--rebuild-conn` (net-builder na czystym GT) — flaga `--gt-rebuild-conn` (domyślnie true, spójnie z p040).
- Zapis: `data/output/eval_val_pages/report.json` + `summary.txt`.

### B. Rozszerz `scripts/diff_gt_runtime.py`

- Dodaj sekcję `components`: match IoU, only_gt, only_runtime.
- Dodaj sekcję `tags`: matched/missed/extra (normalizacja `-F1` / spacje).
- Flaga `--components` / `--tags` (domyślnie wszystko).

### C. Integracja z `backend.cli validate`

- Po eksporcie GT `.schema.json` z labelera: `python -m backend.cli validate <runtime.json> --ground-truth <gt.schema.json>`.

## Testy

- `backend/tests/test_eval_val_pages.py` — mock GT/runtime na fixture, bez obrazów.
- Istniejące testy bez regresji.

## Kryteria akceptacji

- `eval_val_pages.py` na p040 (jeśli dane lokalne) — raport JSON bez crasha.
- Metryki connections zgodne z `diff_gt_runtime.py` dla tej samej strony.
- pytest OK.

## Po ukończeniu

`sync/commit-message.txt` = `[Claude] scripts: eval val-pages per filar (prompt 016)`

## Poprawka (runda N)

*(Cursor)*
