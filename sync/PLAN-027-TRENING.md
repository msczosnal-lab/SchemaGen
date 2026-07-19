# Plan: przegląd danych (027) → trening YOLO

**Stan wyjściowy (2026-07-19, po odzysku GT z prompta 025):**

| | wartość |
|---|---|
| Stron GT | 199 (train **191** / val **8**) |
| Symboli surowo | 3639 (train 3218 / val 421 — **11.6% val**) |
| Klas YOLO ≥5 instancji | 25 |
| Instancji w treningu | 2308 |
| Kontekstowe (bez YOLO) | 1263 |
| Model bazowy | `symbols_tiled_v1-2` (zamrożony w 026) |

Proporcja val jest zdrowa: 8 stron to te najlepiej oznaczone (p028, p029, p033…), więc trzymają
11.6% instancji przy 4% stron. Nie ruszać `val-pages.yaml`.

---

## Etap 0 — sanity przed dotknięciem czegokolwiek (2 min)

```powershell
cd C:\Users\Filip\Desktop\Cursor\SchemaGen
.venv311\Scripts\Activate.ps1

git status --short          # ma być czysto
python -m tools.audit_gt    # 0 sierot, 2 CRIT (bbox_out_of_frame = urzadzenie, P3)
git tag gt-pre-027          # punkt powrotu przed masową zmianą klas
```

**STOP jeśli:** `audit_gt` pokazuje `cache_orphan_data` albo `page_id_mismatch`.

---

## Etap 1 — przegląd i scalenie klas (027) · ręczny, najdłuższy

```powershell
python scripts/element_review.py --thumb 120 --thicken 2
# otwiera data/output/element_review.html
```

### Na czym się skupić (kolejność wg zysku)

| Priorytet | Co | Dlaczego |
|---|---|---|
| **1** | `limit_switch`(4) + `krancowka_nc`(4) + `styk_krancowki`(1) | razem **9** → przekroczy próg min-count=5, nowa klasa w treningu |
| **2** | `styk_nc`(20) vs `styki_nc`(5) | duplikat PL/PL — dziś sieć uczy się dwóch klas tego samego |
| **3** | `styki`(163) | najbardziej podejrzana klasa: worek zbiorczy? sprawdzić, czy nie miesza `styki_przekaznika`(33) i `styk_stycznika`(36) |
| **4** | 35 klas <5 instancji (68 bbox) | tam siedzą pary EN/PL: `motor`, `fuse`, `socket`, `switch`, `disconnector`, `contactor`, `power_supply`, `diode` |
| **5** | `custom_*` (63+17+16) | czy `custom_urzadzenie` ma zostać osobno, skoro `urzadzenie` wypadło z YOLO? |

### Filtrowanie w przeglądarce

Praca po klasie (`--class`) jest szybsza niż przewijanie 3639 crops:

```powershell
python scripts/element_review.py --class styki --thumb 140
python scripts/element_review.py --class limit_switch --thumb 140
```

Wynik: `reassignments.json` z przeglądarki → `data/reassignments.json`.

### Zastosowanie

```powershell
python scripts/apply_reassign.py                    # DRY-RUN, przeczytaj podsumowanie
python scripts/apply_reassign.py --apply            # backup gt/ robi sam
python -m tools.audit_gt                            # nic się nie zepsuło?
python scripts/class_report.py --min-count 5        # ile klas przeszło próg
```

**Kryterium sukcesu etapu:** liczba klas ≥5 rośnie, liczba klas <5 maleje, `audit_gt` bez nowych CRIT.

[RYZYKO] `element_review.py` klasyfikuje crops przez `tag_to_class(tag)`, a eksport przez
`bbox_class(class_name, tag)` (Krok 1 z 027). Jeśli klasa w dropdownie nie zgadza się z `class_report`,
to jest ta rozbieżność — nie błąd danych. Warto naprawić przy okazji.

---

## Etap 2 — eksport datasetu

```powershell
python -m train.tiled_export --win 1536 --overlap 0.2 --min-visible 0.35 --min-count 5
```

**Zanotuj z outputu: liczbę kafli train/val.** `tile_page` zwraca tylko okna z ≥1 bboxem, więc
kafli będzie znacznie mniej niż `strony × 24`. Ta liczba decyduje o czasie treningu — patrz Etap 3.

Kontrola wzrokowa, czy kafle i labelki się zgadzają:

```powershell
python scripts/visualize_yolo_dataset.py
```

**STOP jeśli:** kafli train < 300 (za mało na 25 klas) albo któraś klasa ma 0 instancji w train.

---

## Etap 3 — trening

**Najpierw krótki bieg diagnostyczny, nie od razu 150 epok.** Przy 1536 px i batch 4 na RTX 2080
pełny cykl może iść kilkanaście godzin, a błąd w danych zobaczysz po 30 epokach tak samo dobrze.

```powershell
python -m train.train_symbols --data data/labeled_tiled/data.yaml `
    --name symbols_tiled_v1-3-probe --epochs 30 --cache disk
```

Po 30 epokach sprawdź w `data/runs/symbols_tiled_v1-3-probe/results.csv`:

| Sygnał | Interpretacja |
|---|---|
| mAP50 rośnie, box_loss spada | dane OK → pełny bieg |
| mAP50 płaski przy ~0 | błąd w labelkach/klasach → wróć do Etapu 2 |
| mAP50 rośnie tylko dla 2–3 klas | reszta ma za mało instancji → wróć do 027 |

Pełny bieg dopiero po zielonym świetle z probe:

```powershell
python -m train.train_symbols --data data/labeled_tiled/data.yaml `
    --name symbols_tiled_v1-3 --epochs 150 --patience 30 --cache disk
```

Augmentacje obrotu/odbicia zostają na 0 (domyślne) — schematy elektryczne mają ustaloną orientację,
a `strzalka_potencjalu_wejsciowa` / `wyjsciowa` różnią się właśnie kierunkiem. **Nie włączać
`--fliplr` ani `--degrees`.**

---

## Etap 4 — ONNX i smoke

```powershell
python -m train.export_onnx --version symbols_tiled_v1-3
python scripts/preview_batch.py --version symbols_tiled_v1-3 --conf 0.18 --limit 30
```

Obejrzyj podglądy. Szukaj: fałszywych `zlaczka` na liniach, gubionych `terminal_plc`,
detekcji na tabliczce rysunkowej (dolne 7% — `roi_bottom_cut_frac`).

---

## Etap 5 — metryka i decyzja

```powershell
python scripts/diff_gt_runtime.py --page p028
python scripts/eval_val_pages.py
python -m tools.baseline_eval_gt
```

**Porównaj z baseline z 023: średnia GT 6 stron = 21.50, val-pages mean = 30.77.**

Uwaga metodologiczna: val-pages mean **nie jest porównywalny** z 30.77, bo p025, p040, p045, p050
mają teraz GT i wchodzą do liczenia. Pierwszy pomiar po zmianie = nowy punkt odniesienia, nie regresja.
Baseline GT 6 stron pozostaje porównywalny.

`registry.json` aktualizuj dopiero, gdy `v1-3` bije `v1-2` na tych liczbach — inaczej tor modelu
zostaje zamrożony i wracamy do 027.

---

## Czego NIE robić

* nie włączać augmentacji obrotu/odbicia (orientacja niesie znaczenie)
* nie ruszać `val-pages.yaml` (stały zestaw walidacyjny, proporcja jest zdrowa)
* nie dodawać `urzadzenie` z powrotem do YOLO (obrysy 1500–3500 px psują tiling)
* nie uruchamiać pełnych 150 epok przed probe
* nie aktualizować `registry.json` przed Etapem 5

---

## Dług, który zostaje na później

* **Faza C prompta 025** — F1 (wyścig `selectPage` zapisuje GT pod cudzym page_id, udowodnione)
  i F3 (cache czytany przed plikiem, sieroty nieusuwane). Dopóki nie naprawione, **nie przewijaj
  szybko stron w labelerze.**
* `config/gt-eval.yaml` nie istnieje mimo notatki w `KOLEJNE-ZADANIE.md` — p031 (SCORE 0.00)
  zaniża średnią 21.50 o ~3.6 pkt.
* 8 bboxów `urzadzenie` poza kadrem (P3) — istotne dopiero, gdyby klasa wróciła do YOLO.
