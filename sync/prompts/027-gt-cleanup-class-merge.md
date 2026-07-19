# Zadanie 027 (v2): eksport po `type`, nie po `tag`

**Status:** AKTYWNE — blokuje trening i 024
**Model:** Sonnet 5
**Uwaga:** wersja v1 tego pliku kazała scalać klasy EN/PL aliasami. To było leczenie objawu — patrz ustalenie niżej. `config/class-aliases.yaml` (commit `c6e587a0`) zostaje, ale traci znaczenie po tej poprawce.

## Ustalenie 2026-07-19 (pomiar na `gt/*.json`)

GT v2 ma **dwa pola** na symbolu: `type` (kanoniczny typ elementu) i `tag` (co inżynier wpisał na rysunku — oznaczenie).

Rozkład `type` w GT (421 symboli, 21 typów, wszystkie polskie):

```
zlaczka 136 · custom_oznaczenie_przewodu 63 · mostek 40 · strzalka_potencjalu_wyjsciowa 39
zlacze 38 · strzalka_potencjalu_wejsciowa 20 · custom_terminale_urządzenia 16
oznaczenie_przewodu 16 · custom_urządzenie 15 · terminal_plc 6 · styk_nc 6
styki_przekaznika 4 · listwa_zlaczek 4 · styki 3 · emergency_stop 3 · contactor 2
wylacznik_nadpradowy 2 · custom_urzadzenie 2 · terminale_urzadzenia 2 · oznaczenie_kabla 2 · urzadzenie 2
```

Rozkład `tag` w tym samym GT (126 różnych wartości, 138 czysto numerycznych):

```
złączka 45 · mostek 39 · złącze 36 · "6" 22 · Oznaczenie przewodu 16
"2" 11 · "5" 10 · "4" 10 · "3" 10 · "1" 10 · BN 6 · BU 6 · SAF2 5 ...
```

**W 382 z 421 symboli `type` ≠ `tag`.**

## [BŁĄD] Przyczyna

`backend/class_map.py:188` — `tag_to_class(tag)` klasyfikuje po polu `tag`:

```python
cls = pmap[norm] if norm in pmap else slugify(tag)
```

Dwa skutki:

1. `tag="6"` (numer złączki na listwie) → klasa `6` → odcięta przez `--min-count 5` → **bbox wypada z treningu**. Stąd `zlaczka` miała 10 przykładów zamiast 136.
2. `tag="przekaźnik"` → paleta mapuje na `id: relay` → **stąd angielskie nazwy klas**. Nie pochodzą od AI ani od ręcznego oznaczania: `config/symbol-palette.yaml` ma `id` angielskie i `label_pl` polskie, a eksport zapisuje `id`.

## Cel

`type` jest klasą. `tag` jest oznaczeniem z rysunku i **nie trafia do YOLO**.

## Krok 1 — eksport czyta `type`

1. W ścieżce GT v2 (`load_all_training_records()` i to, z czego korzystają `dataset_export` oraz `tiled_export`) klasa symbolu = `type`, nie `tag`.
2. `tag` zachowany w rekordzie jako oznaczenie (przyda się dla OCR / relacji), ale nie wchodzi do `data.yaml`.
3. Fallback dla starych rekordów label v1 bez `type`: `tag_to_class(tag)` jak dotąd. Ścieżka v1 zostaje nietknięta.
4. Normalizacja `type` do ASCII przed użyciem jako nazwy klasy — w GT są niespójne diakrytyki:
   - `custom_urządzenie` (15) vs `custom_urzadzenie` (2)
   - `custom_terminale_urządzenia` (16) vs `terminale_urzadzenia` (2)

   Dziś to osobne klasy. Po `_ascii()` scalają się same.

## Krok 2 — re-export i pomiar

```powershell
python -m train.tiled_export --win 1536 --overlap 0.2 --min-visible 0.35 --min-count 5
python scripts/class_report.py --min-count 5
python scripts/visualize_yolo_dataset.py --root data/labeled_tiled --limit 20
```

Oczekiwane po poprawce:

- `zlaczka` rośnie z 10 do rzędu ~100+
- znikają klasy numeryczne (`1`, `2`, `6`, …)
- znikają nazwy angielskie (`relay`, `led`, `push_button`, `terminal_block`, `ground`, `emergency_stop`)
- łączna liczba bbox **rośnie** — nic już nie wypada przez `min-count`

Jeśli angielskie nazwy zostały, `type` nie jest używany wszędzie. Jeśli suma bbox spadła, coś wypadło — szukać, nie iść dalej.

Wynik → `sync/analysis/027-export-type-fix.md` (przed/po per klasa).

## Krok 3 — dopiero teraz decyzja o scaleniach

Po re-eksporcie obejrzeć:

```powershell
python scripts/visualize_class_crops.py --per-class 80
```

Do rozstrzygnięcia przez Filipa (wiedza domenowa, nie zgadywać):

- `zlaczka` (136) vs `zlacze` (38) vs `listwa_zlaczek` (4) — trzy typy czy jeden z wariantami?
- `styki` (3) / `styki_przekaznika` (4) / `styk_nc` (6) — 13 bboxów na trzy klasy; sensowne rozdzielenie czy scalić?
- `custom_*` (96 razem) — czy `custom_urzadzenie` i `urzadzenie` to to samo

Dopiero ustalone scalenia wpisać do `config/class-aliases.yaml`. Większość wpisów z v1 (EN→PL) stanie się martwa — usunąć te, które nie mają już zastosowania, zamiast zostawiać jako szum.

## [BŁĄD] Poboczny, do naprawy przy okazji

`config/symbol-palette.yaml`:

```yaml
- id: auxiliary_contactor
  label_pl: dioda
```

Stycznik pomocniczy opisany jako dioda. Kto klikał „dioda" w palecie, zapisywał `auxiliary_contactor`. Sprawdzić, czy w GT są tak oznaczone symbole i poprawić.

## Walidacja

```powershell
pytest backend/tests labeler/tests -q
python scripts/diff_gt_runtime.py --page p028
python scripts/eval_val_pages.py
```

SCORE **się zmieni** — zmienia się przestrzeń klas. To oczekiwane; zapisać nowy baseline, stary 21.50 unieważniony.

Test regresji: symbol z `type="zlaczka"` i `tag="6"` eksportuje się jako klasa `zlaczka`. Bez tego testu błąd wróci.

## Poza zakresem

- Trening (zamrożony — 026; wraca do gry po doznaczeniu stron)
- Zmiana `val-pages.yaml`
- ContextResolver
