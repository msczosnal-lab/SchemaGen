# Zadanie 033: LOOP — jakość linii (tylko `lines`)

**Status:** AKTYWNE (Cursor, tryb `/loop`)
**Model:** Opus 4.8
**loop_armed: true**
**Zakres: WYŁĄCZNIE komponent `lines` metryki SCORE.**

## Stan wyjściowy (p028, model `symbols_tiled_v1-4`, 2026-07-19)

```
lines  P=0.248  R=0.768  F1=0.375  (tol=8.0px)  waga 0.25 -> 9.4 pkt
Runtime: 158 linii    GT: 42 linii
```

Recall jest wysoki — **runtime widzi prawie wszystko, co jest w GT**. Precyzja 0.248 znaczy, że na jedną prawdziwą linię przypadają trzy zmyślone. To jest kubeł do opróżnienia: przy niezmienionym recall podniesienie P do ~0.6 daje F1 ≈ 0.68 i **+7 pkt SCORE na p028**.

Precedens: loop 021 na tym samym problemie (P=0.29) dał ~+10 pkt filtrem precyzji.

## Cel

**Podnieść precyzję linii bez utraty recall.** Kolejność ważności: `P` w górę > `F1` w górę > `R` bez spadku >−0.05.

## Strony pomiarowe — ograniczenie krytyczne

GT linii istnieje na **5 stronach z 199**:

| Strona | Linii w GT |
|---|---|
| p033 | 117 |
| p029 | 76 |
| p028 | 42 |
| p040 | 17 |
| p030 | 8 |

**Każda iteracja mierzy się na wszystkich pięciu.** Zmiana akceptowana tylko gdy średnia F1 linii rośnie **i żadna strona nie traci więcej niż 0.05 F1**.

Zysk wyłącznie na p028 = odrzucone. To jest ta sama pułapka, w którą wpadło 023 (cały zysk na jednej stronie) — nie powtarzać.

## Pomiar

```powershell
python scripts/diff_gt_runtime.py --page p028 --json
python scripts/diff_gt_runtime.py --page p029 --json
python scripts/diff_gt_runtime.py --page p030 --json
python scripts/diff_gt_runtime.py --page p033 --json
python scripts/diff_gt_runtime.py --page p040 --json
```

Log iteracji: `sync/loop-033-log.md`, jedna linia na iterację, format jak `loop-032-log.md`:

```
itN: <co zmienione> (<plik:linia>) | sr F1 X->Y | p028 ±a p029 ±b p030 ±c p033 ±d p040 ±e | OK|COFNIETE <powod>
```

## Poziomy zmian (OODA, wzorzec loop 032)

**L1 — parametry** (`config/runtime.yaml`): `hough_min_len_frac`, `hough_gap_frac`, `hough_bus_min_len_frac`, `hough_bus_gap_frac`, `hough_bus_axis_tol_deg`, `roi_bottom_cut_frac`, progi merge/contact.

**Maksymalnie 2 próby parametryczne na jeden kubeł błędu.** Po drugiej nieudanej — L2, nie trzecia próba.

**L2 — logika filtrów** (`backend/recognize/line_tracer.py`, sito linii): odsiewanie segmentów bez zaczepienia, scalanie kolinearnych, odrzucanie linii w obszarze tabliczki/tekstu.

**L3 — struktura**: tylko po wyczerpaniu L2 i z wpisem uzasadniającym w logu.

## Diagnoza przed pierwszą zmianą (obowiązkowa)

Nie zaczynać od strojenia. Najpierw rozbić 158 linii runtime na p028 wg przyczyny nadmiaru:

1. segmenty krótkie, nienależące do żadnej ścieżki (szum tekstu/rastru)
2. duplikaty tej samej linii z dwóch przebiegów Hougha (`hough_second_pass: true`)
3. linie w obszarze tabliczki rysunkowej mimo `roi_bottom_cut_frac: 0.93`
4. linie prawdziwe, ale pocięte na kawałki (jedna linia GT = N segmentów runtime — **to psuje precyzję, ale nie jest halucynacją**; leczy się scalaniem, nie odsiewaniem)

Kategoria 4 jest kluczowa do rozróżnienia. Jeśli dominuje, filtrowanie **pogorszy** wynik, a właściwą naprawą jest merge. Wynik diagnozy → `sync/analysis/033-lines-baseline.md`.

## POZA ZAKRESEM — nie dotykać

- `net_builder.py`, `connection_path.py`, emisja connections
- model YOLO, `registry.json`, klasy, `train-classes.yaml`
- GT (`gt/*.json`), labeler
- wagi SCORE, `diff_metrics.py`
- `arrow_supplement`

Jeżeli iteracja poprawia `lines`, ale rusza `components` lub `connections` — **cofnąć**. Zmiana ma być izolowana do jednego komponentu.

## STOP

- 3 kolejne iteracje z Δ średniej F1 < 0.01, **albo**
- osiągnięte P ≥ 0.60 przy R ≥ 0.72

Po STOP: `loop_armed: false`, podsumowanie w `sync/filip-to-zw.md` (tabela per strona, lista zaakceptowanych decyzji, co odrzucone i dlaczego).

## Znany błąd — NIE naprawiać w tym loopie

`_emit_multi_node` produkuje pętle własne (`element_X:1 -> element_X:1`) i gwiazdy wewnątrz jednego elementu. Widoczne w `diff_gt_runtime --page p028`, 271 runtime conn wobec 42 GT.

To dotyczy **connections**, nie linii. Osobne zadanie — zapisane, żeby nie zginęło.
