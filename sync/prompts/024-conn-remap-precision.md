# Zadanie 024: Connections — remap fail + precyzja emisji

**Status:** AKTYWNE (Cursor)
**Model:** Opus 4.8 (zmiana metryko-krytyczna, wysokie ryzyko cichej regresji)
**Zależność:** 023 DONE (`connection_path.py`, `_emit_multi_node`) | loop 032 STOP
**Baseline:** `sync/analysis/023-p028-conn-baseline.md`

## Kontekst

023 naprawił topologię (gwiazda → łańcuch/pary): p028 conn 4/42 → 10/42. To był mniejszy z dwóch kubłów błędu.

| Kubeł błędu (p028, 207 conn RT) | Liczba | Adresowane w |
|---|---|---|
| Remap fail (symbol/terminal niesparowany) | 118 | **024 (to zadanie)** |
| Topologia ≠ GT | 85 | 023 ✅ |
| Directed flip | 0 | — |

Dodatkowo: **precyzja ≈ 0.05** (207 RT vs 42 GT). Match rośnie, ale runtime nadprodukuje ~5× krawędzi i nikt tego nie mierzy.

## Cel

1. **Zamknąć remap fail** — 9 niesparowanych GT bbox na p028 i terminale poza tolerancją.
2. **Wprowadzić precyzję jako metrykę pierwszej klasy** — obok match.
3. Zysk mierzony na ≥3 stronach, nie tylko p028.

## Krok 1 — metryka precyzji (przed jakąkolwiek zmianą emisji)

W `backend/validate/diff_metrics.py` raportować dla connections:
`match`, `gt_total`, `rt_total`, `precision = match/rt_total`, `recall = match/gt_total`, `f1`.

`diff_gt_runtime.py --json` musi te pola wypisywać. **Wag SCORE nie zmieniać w tym kroku** — najpierw obserwacja, zmiana wag = osobna eskalacja (reguła loop 032).

Zapisać baseline P/R/F1 dla p028, p029, p030, p033, p034, p040 do `sync/analysis/024-conn-pr-baseline.md`.

## Krok 2 — diagnoza remap fail

Dla p028 rozbić 118 remap-fail na przyczyny:

1. GT bbox bez pary RT (YOLO nie wykrył / wykluczona klasa) — ile, jakie klasy
2. RT bbox bez pary GT (FP detekcji)
3. Para bbox OK, ale **terminal** poza tolerancją (indeks terminalu `:1`/`:2`/`:3` nie pasuje)
4. Klasa kontekstowa poza YOLO (`zlacze`, `listwa_zlaczek`, `terminale_urzadzenia`, `oznaczenie_*`) — remap strukturalnie niemożliwy

Kategoria 4 jest **sufitem nienaprawialnym bez ContextResolver** — policzyć ją jawnie i odjąć od celu. Bez tej liczby nie da się ocenić, czy 024 ma sens.

Wynik → `sync/analysis/024-remap-fail-breakdown.md` (tabela + 2 przykłady per kategoria).

## Krok 3 — implementacja (dopiero po kroku 2, zakres zależny od breakdown)

Kolejność wg masy błędu z kroku 2. Kandydaci:

- **Tolerancja terminali** — dopasowanie po pozycji terminalu względem bbox (znormalizowanej), nie po surowym indeksie
- **Filtr precyzji emisji** — odrzucać krawędzie bez pokrycia segmentem `GraphicLine` (wzorzec: filtr precyzji linii z loop 021, dał +10 pkt)
- **Sufit kategorii 4** — jeśli dominuje, zatrzymać się i eskalować ContextResolver jako 026 zamiast obchodzić

## Poza zakresem

- Zmiana wag SCORE / `_norm_conn` na undirected
- Zmiana GT v2
- Re-arm loop 032
- Retrain YOLO (osobny tor, Filip)

## Walidacja

```powershell
pytest backend/tests labeler/tests -q
python scripts/diff_gt_runtime.py --page p028 --json
python scripts/eval_val_pages.py
```

Kryterium:

1. p028 conn **F1** wyraźnie w górę (nie sam match — match rośnie też przez nadprodukcję)
2. Poprawa na **≥2 stronach poza p028** — inaczej to przeuczenie pod jedną stronę (023 dał zysk wyłącznie na p028)
3. Średnia GT bez regresji strony > −1.0 SCORE; val-pages mean ≥ 30.77

## Wykluczenie pustych stron ze średniej

`p031` ma GT ~505 B (pusta) i SCORE 0.00 od loop 032 — zaniża średnią i maskuje delty.

Dodać `config/gt-eval.yaml`:

```yaml
# Strony wykluczone ze sredniej GT (puste / niekompletne GT).
exclude_pages:
  - 22_A_153_PL_Adamed_AGV_SA2_20250706_p031
```

`eval_val_pages.py` i skrypt liczący średnią GT respektują tę listę; strona nadal liczona indywidualnie, tylko poza średnią. **Po zmianie przeliczyć baseline 21.50 i wpisać nową wartość** — stara przestaje być porównywalna.

[UWAGA] `p032` nie istnieje w `gt/` (zestaw to p028, p029, p030, p031, p033, p034). Jeśli miało być wykluczone coś innego — potwierdzić przed zmianą configu.
