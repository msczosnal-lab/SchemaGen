# 023 baseline — p028 connections (2026-07-15)

Źródło: `diff_gt_runtime.py --page p028 --json` + analiza remap.

## Metryki

| Metryka | Wartość |
|---------|---------|
| GT conn | 42 |
| Runtime conn | 207 |
| **Match** | **4/42** |
| SCORE | 35.83 |
| Parowanie bbox | 40/49 GT ↔ 51 RT |
| Niesparowane GT symbole | 9 |

## Podział błędów runtime (207 conn)

| Kategoria | Liczba | Uwagi |
|-----------|--------|-------|
| Remap fail (symbol/terminal) | 118 | niesparowane symbole lub terminal poza tol |
| Remap OK, topologia ≠ GT | 85 | głównie gwiazda `net_*` vs łańcuch OD–DO |
| Directed flip (A→B vs B→A) | 0 | kierunek nie jest problemem |
| Trafienia | 4 | — |

## Przykłady only_gt (wzorzec GT)

Łańcuch `link` między `element_*` (szyna złączek):

```
element_1781557626710:3 -> element_1781557627333:1 (link)
element_1781557627333:2 -> element_1781557627918:1 (link)
```

Power do symboli YOLO (`sym_*`):

```
element_1781557627918:3 -> sym_8:1 (power)
element_1781557638813:1 -> sym_13:1 (power)
```

## Diagnoza

1. **Topologia (85)** — `net_builder` emituje gwiazdę do `node_ids[0]` dla netów ≥3 węzłów; GT ma krawędzie ścieżkowe (łańcuch `link` + segmenty `power`). Remap ID (022) działa — to nie jest `element_*` vs `sym_*` na surowo.
2. **Remap fail (118)** — 9 niesparowanych GT bbox + nadmiar 207 runtime conn (gwiazdy generują N−1 krawędzi per net).
3. **Kierunek** — nie blokuje match (0 flip).

## Cel 023

Emisja adjacent/chain w `net_builder` (współdzielone z `rail_extractor`); bez zmiany wag eval ani `_norm_conn`.

## Wynik (2026-07-15)

| Metryka | Przed | Po |
|---------|-------|-----|
| p028 Conn match | 4/42 | **10/42** |
| p028 SCORE | 35.83 | **37.02** |
| Śr. 6 stron SCORE | 21.24 | **21.50** |
