# 027 Krok 1+2: eksport klasy po `type`, nie po `tag` — wynik na pełnym GT

**Data:** 2026-07-19 | **GT:** 199 stron (`gt/*.json`), 3505 bbox, 0 pominiętych (bez klasy)
**Kod:** `bbox_class()` w `backend/class_map.py` (prompt `027-gt-cleanup-class-merge.md` v2)

## Podsumowanie

| | przed (klasa = `tag`) | po (klasa = `type`) |
|---|---:|---:|
| unikalnych "klas" | **179** | **61** |
| bbox bez klasy | 0 | 0 |
| suma bbox | 3505 | 3505 |

118 fragmentów zniknęło — to niemal wyłącznie tagi numeryczne/kolorów (`6`, `bn`, `saf1_plc_64_1`, `ks2_16`...), które wcześniej tworzyły osobne "klasy" i wypadały przez `--min-count`.

## Największe przesunięcia (klasa: przed → po)

| klasa | przed | po | Δ |
|---|---:|---:|---:|
| zlaczka | 393 | **490** | +97 |
| oznaczenie_przewodu | 196 | 258 | +62 |
| strzalka_potencjalu_wyjsciowa | 148 | 176 | +28 |
| strzalka_potencjalu_wejsciowa | 48 | 66 | +18 |
| terminale_urzadzenia | 71 | 87 | +16 |
| urzadzenie | 609 | 624 | +15 |
| terminal_plc | 192 | 201 | +9 |
| przekaznik | 63 | 69 | +6 |
| styk_nc | 19 | 25 | +6 |

Klasy numeryczne/tagowe znikły całkowicie: `6`(23), `4`(10), `3`(10), `5`(10), `2`(11), `8`(9), `7`(9), `1`(9), `bn`(6), `bu`(6), `9`(6), `11`(6), `wh`(4), `bk`(4), `saf3`(4), `ye`(5), `saf1`(5), `saf2`(5), i ~90 dalszych pojedynczych tagów (patrz surowe dane w commicie kodu).

## Klasy do treningu (min-count=5, `class_report.py --min-count 5`)

19 klas, 1545 instancji w treningu:

```
zlaczka 490 · mostek 158 · strzalka_potencjalu_wyjsciowa 176 · terminal_plc 201
styki 157 · przekaznik 69 · przycisk 49 · styki_przekaznika 33 · lampka 25
styk_nc 25 · strzalka_potencjalu_wejsciowa 66 · gniazdo_rj_45 21 · cewka_zaworow 21
terminal_sterownika_safety 17 · uziemienie 10 · wylacznik_nadpradowy 10
polaczenie_przewodow 6 · przycisk_awaryjny 6 · ekranowanie_kabla 5
```

Kontekstowe (świadomie poza YOLO, GT relacji): 1337 bbox w `listwa_zlaczek`, `oznaczenie_kabla`,
`oznaczenie_przewodu`, `terminale_urzadzenia`, `urzadzenie`, `zlacze`, `zwarta_listwa_zlaczek`.

## [BŁĄD] Blokada bramki przeglądu — 556 bbox traconych mimo >=5 instancji

`config/reviewed-classes.yaml` (bramka z `element_review.py`, dodana dzisiaj — 028) blokuje
2 klasy z dużą liczebnością, mimo że przechodzą `--min-count 5`:

| klasa | instancji | powód |
|---|---:|---|
| `terminal_przylaczeniowy` | **520** | brak wpisu "przejrzana" |
| `styk_stycznika` | **36** | brak wpisu "przejrzana" |

To nie regresja Krok 1 — bramka działa jak zaprojektowano (patrz `54645d79`, `028-element-review-v2`).
Ale `terminal_przylaczeniowy` to druga po `zlaczka` klasa co do wielkości — bez przeglądu trening
traci 520 bbox. **Decyzja do Filipa:** `scripts/element_review.py` → `scripts/apply_reviewed.py --apply`.

## Krok 3 — wciąż do decyzji Filipa (wiedza domenowa)

- `zlaczka` (490) vs `zlacze` (199, kontekstowa) vs `listwa_zlaczek` — trzy typy czy warianty?
- `styki` (157) / `styki_przekaznika` (33) / `styk_nc` (25) / `styk_stycznika` (36, zablokowana) — scalić czy rozdzielać?
- `urzadzenie` (624, kontekstowa) vs `custom_urzadzenie`/`custom_urządzenie` (scalone automatycznie przez ascii-fold w Kroku 1) — to samo?

Ustalenia → `config/class-aliases.yaml`.

## Środowisko

Pomiar robiony w sandboxie Cowork bez dostępu do `data/raw/*.png` i z niesprawnym SQLite na
zamontowanym dysku (`disk I/O error`) — obejście: `backend.db.DB_PATH` wskazany na lokalny
`/tmp` (v1 SQLite ma i tak 0 wierszy, cała realna dana jest w `gt/*.json`). Wynik = wyłącznie
`load_graph_v2_records()`. Do potwierdzenia lokalnie: `python -m train.tiled_export ...` (wymaga obrazów).
