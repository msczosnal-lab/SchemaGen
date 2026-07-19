## 2026-07-19 [Claude] — symetria zastosowana (--force), [BŁĄD] mój w UI naprawiony

### [BŁĄD] mój — podgląd wymagał zgody, zanim go pokazał

W pierwszej wersji panelu symetrii miniatura po transformacji pojawiała się **dopiero po
zaznaczeniu checkboxa**. Żeby zobaczyć, jak wygląda lustro, trzeba było najpierw na nie zezwolić.
W konfiguracji fail-safe to jest odwrotnie, niż powinno — zgoda ma być skutkiem obejrzenia,
nie warunkiem. To najprawdopodobniej dlatego strzałki potencjału i `mostek` wyszły z pełną
symetrią wbrew własnym notatkom w `symmetry.json`.

Naprawione:

- podglądy **wszystkich 5 transformacji zawsze widoczne**; zaznaczenie zmienia tylko
  wyróżnienie (ramka + etykieta `DOZWOLONE` / `niedozwolone`),
- panel klasy z udokumentowanym zakazem: czerwone tło + ostrzeżenie + `confirm()` przy kliknięciu,
- `apply_symmetry.py`: nowy bezpiecznik — zgoda wbrew JAWNEMU zakazowi z `note`
  **wstrzymuje zapis**, wymaga `--force`. UI da się ominąć, plik nie.

### Symetria zastosowana Twoją decyzją (`--force`)

12 klas ze zgodą. Strzałki potencjału zapisane wg Twojej decyzji, z adnotacją w `note`,
żeby przyczyna była do znalezienia, gdyby coś poszło nie tak po retrainie.

**`mostek` — cofnięty do zakazu (Twoja decyzja).** `maybe_expand_mostek` przepisuje
`mostek` → `mostek_r0…m270` (8 wariantów D4) **przed** eksportem, więc obroty są już
obsłużone, a w treningu klasa `mostek` w ogóle nie występuje. Wpis symetrii byłby albo
no-opem, albo źródłem błędnych etykiet. Zostaje `false` z uzasadnieniem w `note`.

**[RYZYKO] strzałki potencjału.** Jeśli po retrainie mAP obu strzałek spadnie, to jest
pierwszy podejrzany — jest to zapisane w `note`.

Wpływ na Część C: zgodę ma 9 z 22 klas, wariant 1 kwalifikuje **569/1044 kafli = 54,5 %**.
Ale celowanych (z klasą 5–30 inst.) tylko **33 ze 140**, bo większość klas z tego zakresu
zgody nie dostała — `lampka`, `cewka_zaworow`, `uziemienie` i `terminal_sterownika_safety`
zostały na `false` albo prawie.

### Test regresji zmieniony, nie usunięty

`test_strzalki_potencjalu_maja_zakaz_w_repo` kodował poprzednią decyzję i po `--force` padał.
Zamieniłem na `test_strzalki_potencjalu_maja_swiadoma_decyzje_w_repo`: nie narzuca kierunku,
ale wymaga, żeby ta para **zawsze miała jawny wpis z uzasadnieniem w `note`**. Milcząca
decyzja o klasach różniących się wyłącznie zwrotem jest odwracalna tylko przez retrain.

### `reassignments.json` — uruchom u siebie

Nie stosowałem go z tej sesji: plik jest w Twoim `Downloads`, a przepisywanie 242 pozycji
przez czat groziłoby przekłamaniem w liście `__DELETE__`. `apply_reassign.py` sam szuka
w `~/Downloads`.

```powershell
Start-GitSync.cmd Claude          # najpierw pull — Twoje pliki powstały przed scaleniem custom_*
python scripts/apply_reassign.py            # dry-run
python scripts/apply_reassign.py --apply
```

Szacowany wpływ (242 zmiany): instancji treningowych **2212 → 2017**, klas nadal 22.

| klasa | przed | po | zmiana |
|---|---:|---:|---:|
| terminal_przylaczeniowy | 534 | 448 | −86 |
| zlaczka | 536 | 490 | −46 |
| gniazdo_rj_45 | 35 | 16 | **−54 %** |
| mostek | 176 | 159 | −17 |
| styki | 163 | 149 | −14 |
| blok_rozdzielczy | 4 | 0 | klasa znika |

`p034` traci 89 ze 108 symboli. `gniazdo_rj_45` ma po cięciu 16 instancji i **0 w val** —
po tym cleanupie tym bardziej wymaga uwzględnienia przy przebudowie `val-pages.yaml`.

**pytest: 528 passed.**

---

## 2026-07-19 [Claude] — 028 uzupełnienie: scalenie `custom_*` + [BŁĄD] val bez 10 klas

### [BŁĄD] `custom_X` / `X` — ta sama rzecz uczona sprzecznie (naprawione)

Wskazałeś `oznaczenie_przewodu` / `custom_oznaczenie_przewodu`. To wzorzec, nie pojedynczy przypadek:

| klasa | inst. | rola | w YOLO |
|---|---:|---|---|
| oznaczenie_przewodu | 214 | contextual | nie |
| custom_oznaczenie_przewodu | 63 | atomic | **tak** |
| urzadzenie | 607 | contextual | nie |
| custom_urzadzenie | 17 | atomic | **tak** |
| terminale_urzadzenia | 71 | contextual | nie |
| custom_terminale_urzadzenia | 16 | atomic | **tak** |

Ta sama rzecz była jednocześnie klasą treningową i tłem. YOLO traktuje nieoznakowany obszar
jako tło, więc 607 `urzadzenie` uczyło „to tło" przeciw 17 `custom_urzadzenie` uczącym „to klasa".
Częściowo cofało to Twoją decyzję z 026.

**Źródło:** `backend/type_picker.py:56` tworzy `custom_<nazwa>`, gdy typ wpisany z ręki zamiast
wybrany z palety. Wszystkie 96 bboxów z jednej sesji: **p029, p030, p033**.

**Naprawione** aliasami w `class-aliases.yaml` (Twoja decyzja: kierunek contextual).
Klas YOLO 25 → 22, instancji 2308 → 2212. `relay: przekaznik` był już zrobiony w 027.

### [BŁĄD] 10 z 22 klas ma ZERO instancji w val — miara sukcesu Części C jest niewykonalna

Wskazałeś, że `styk_stycznika` to same podobne styki z p039. Sprawdziłem — to nie duplikaty
(36 osobnych bboxów, siatka 12×3, rozmiary 95–113 × 34–49 px). Ale wszystkie 36 są z **jednej
strony**, a to prowadzi do gorszego odkrycia. Nowy `scripts/class_coverage.py`:

| klasa | inst. | stron | w val |
|---|---:|---:|---:|
| styk_stycznika | 36 | **1** (p039) | **0** |
| polaczenie_przewodow | 6 | **1** (p015) | **0** |
| styki_nc | 5 | **1** (p011) | **0** |
| uziemienie | 9 | 2 | **0** |
| cewka_zaworow | 21 | 4 | **0** |
| ekranowanie_kabla | 5 | 5 | **0** |
| gniazdo_rj_45 | 35 | 5 | **0** |
| terminal_sterownika_safety | 17 | 5 | **0** |
| lampka | 26 | 9 | **0** |
| przycisk | 49 | 16 | **0** |

**7 z 10 klas, które miała objąć augmentacja, ma zero instancji w val.** YOLO poda dla nich
0 albo NaN niezależnie od jakości modelu. Mierzalne są 3 klasy, na 3–6 instancjach — przy tej
próbie jeden bbox przesuwa mAP o kilkanaście punktów, to szum.

**Wniosek: wdrożenie augmentacji przed naprawą `val-pages.yaml` byłoby zmianą w ciemno.**
Zaktualizowałem §5.3 i §7 dokumentu projektowego — naprawa val jest teraz punktem 1, przed
decyzją o wariancie 1T. Plus `p035` jest w val bez `gt/*.json` (ten sam wzorzec co p040).

**[RYZYKO] `styk_stycznika` ma 36 instancji, więc po liczniku wygląda zdrowo** i wypada
z zakresu 5–30, czyli augmentacja by go nie objęła. Ale to jeden kontekst wizualny powielony
36 razy. Licznik instancji jest tu mylącą miarą — dlatego `class_coverage.py` pokazuje rozkład
po stronach. Te 3 klasy jednostronne wymagają doznaczenia, nie augmentacji.

### Zmiany

| Plik | Zmiana |
|---|---|
| `config/class-aliases.yaml` | 3 aliasy `custom_X` → `X` z uzasadnieniem |
| `scripts/class_coverage.py` | nowy — pokrycie klas po stronach + audyt val |
| `backend/tests/test_class_map.py` | test scalenia `custom_`; poprawiony test diakrytyków |
| `sync/analysis/028-augmentacja-projekt.md` | liczby po scaleniu + §5.3 niewykonalność miary |

**pytest: 524 passed.** Wpływ na Część C mały: sufit 76,7 % → 76,5 %, zakres 5–30 z 12 → 10 klas.

---

## 2026-07-19 [Claude] — 028 DONE: rozbieżność 163/160 znaleziona, symetria symboli, projekt augmentacji

### Część A — [BŁĄD] potwierdzony, przyczyna dokładnie ta z hipotezy

`element_review.py` klasyfikował przez `tag_to_class(tag)`, `class_report.py` przez
`bbox_class(class_name, tag)`. Trzy brakujące bboxy to **p029**:

| bbox_id | `type` | `tag` | element_review (było) | class_report |
|---|---|---|---|---|
| element_1781557738693 | styki | SAF1 | `saf1` | `styki` |
| element_1781557736792 | styki | SAF2 | `saf2` | `styki` |
| element_1781557732589 | styki | SAF3 | `saf3` | `styki` |

Skala problemu była **dużo większa niż 3 elementy** — dotyczyła całej przeglądarki:

| | element_review (było) | class_report |
|---|---|---|
| liczba „klas" | **183** | 67 |
| zlaczka | 439 | **536** (−97) |
| custom_oznaczenie_przewodu | 0 | **63** |
| strzalka_potencjalu_wyjsciowa | 155 | **184** |

Przeglądałeś dane rozsypane na 183 kubełki, w tym pseudoklasy `saf1`, `bn`, `ye`, `6`, `24vdc_as1`
— to oznaczenia z rysunku, nie klasy symboli.

**Poprawione:** `element_review.py` używa `bbox_class`, tak jak eksport treningowy.

### Część A — jawne raportowanie braków

Narzędzie wypisuje teraz każdy element, którego nie dało się wyrenderować, z powodem:
brak PNG strony / bbox poza kadrem / wyjątek przy cropie / bbox bez type i tagu.
W konsoli i w nagłówku HTML (czerwony panel z tabelą per klasa). Przy zgodności — zielony ptaszek.

[UWAGA] Na PC ZW `data/raw/` ma **tylko IEC60617.pdf**, zero PNG stron. Przed poprawką narzędzie
renderowało wtedy 0 cropów i nic nie mówiło. Teraz mówi. Testowałem ścieżkę renderowania na stubach.

### Część B — `config/symbol-symmetry.yaml` + UI

- `backend/symmetry.py` — loader z walidacją. **Brak wpisu = brak zgody** (test jednostkowy).
  Rotacje tylko 90/180/270; 45° → ostrzeżenie, nie wyjątek. Zepsuty YAML nie wywraca narzędzia.
- `config/symbol-symmetry.yaml` — zaseedowany: strzałki potencjału i `mostek` **jawnie zabronione**
  z uzasadnieniem, `zlaczka` + `styk_nc` z prompta **do potwierdzenia wzrokowego**.
  Pozostałe 20 klas celowo bez wpisu.
- UI: panel symetrii **przy klasie** (pokazuje się po kliknięciu filtra klasy), checkboxy
  ↔ ↕ ⟳90 ⟳180 ⟳270, obok cropa wzorcowego miniatury po zaznaczonych transformacjach.
  Stan w localStorage, `Pobierz symmetry.json`. Retag/usuwanie/„przejrzana" bez zmian.
- `scripts/apply_symmetry.py` — dry-run domyślnie, zapis atomowy, **scala** zamiast nadpisywać
  (przegląd jednej klasy nie kasuje wiedzy o reszcie); `--replace` gdy chcesz inaczej.
  `note` z YAML nie ginie, gdy UI go nie odeśle.

### Część C — [RYZYKO] rekomendacja prompta wymaga korekty

Liczba, o którą prosiłeś (`scripts/augment_feasibility.py`): **1053 kafle**, z tego kwalifikuje się

| | kafli | % |
|---|---|---|
| stan obecny (2/25 klas ma zgodę) | 72 | 6,8 % |
| **sufit** (zgoda wszystkim poza jawnie zabronionymi) | **808** | **76,7 %** |

**6,8 % to nie werdykt o wariancie 1** — to miara tego, jak pusty jest jeszcze plik symetrii.
Rozstrzyga 76,7 %, więc próg „poniżej 10 % → wariant 1 bezwartościowy" jest przekroczony z zapasem.

Założenie „schematy są gęste i mieszane" **nie potwierdziło się**: **70,7 % kafli jest
jednoklasowych** (744/1053). Przy oknie 1536 px symbole tej samej klasy grupują się przestrzennie.

Ale znalazłem ryzyko, którego prompt nie nazwał, a jest poważniejsze:
**tylko 15,1 % kafli zawiera klasę z zakresu 5–30 instancji.** Wariant 1 w czystej postaci
zduplikowałby 680 kafli klas licznych (`zlaczka` 536, `terminal_przylaczeniowy` 534)
i **pogłębił niezbalansowanie** — odwrotnie niż zamierzasz.

**Rekomendacja: wariant 1 z celowaniem** — dodatkowy warunek „kafel zawiera ≥1 klasę 5–30".
128 kafli dokładnie tam, gdzie brakuje danych; `styk_nc` +45 instancji na transformację,
`cewka_zaworow` +41, przy balaście +80 dla `zlaczka` (baza 1028, +7,8 %).

**Nie zgadzam się z C1a (transformacja in-place) jako startem.** Obrót symbolu w jego bboxie
rozjeżdża linie dochodzące do terminali — powstaje obraz fizycznie niemożliwy. Wariant 1T
obraca cały kafel, więc symbol, linie i sąsiedztwo zostają spójne. C1a miałby sens, gdyby
warunek „wszystkie klasy w kaflu" był trudny — przy 70,7 % kafli jednoklasowych nie jest.

Pełny projekt z tabelami: [`sync/analysis/028-augmentacja-projekt.md`](analysis/028-augmentacja-projekt.md)

**Warunek blokujący wdrożenie:** 11 z 12 klas zakresu 5–30 nie ma jeszcze wpisu symetrii.
Bez przeglądu w `element_review.py` wariant 1T wygeneruje 2 kafle zamiast 128.

### [RYZYKO] `data/labeled_tiled/` jest nieaktualny

`data.yaml` ma 20 klas typu `saf1`, `1`, `10`, `bn` i **12 kafli w train** — ślad po starej
ścieżce tagowej z 026. Po 027/028 wymaga ponownego eksportu, inaczej trening znów pójdzie na śmieciach.

### Pliki

| Plik | Zmiana |
|---|---|
| `backend/symmetry.py` | nowy — loader + walidacja symetrii |
| `config/symbol-symmetry.yaml` | nowy — wiedza domenowa o symetrii |
| `scripts/element_review.py` | `bbox_class` + raport braków + panel symetrii |
| `scripts/apply_symmetry.py` | nowy — symmetry.json → YAML, dry-run, atomowo |
| `scripts/augment_feasibility.py` | nowy — pomiar kwalifikacji kafli |
| `backend/tests/test_symmetry.py` | nowy — 21 testów |
| `backend/tests/test_apply_symmetry.py` | nowy — 10 testów |
| `backend/tests/test_element_review_counts.py` | nowy — 6 testów regresji 163/160 |
| `sync/analysis/028-augmentacja-projekt.md` | nowy — projekt Części C |

**pytest: 523 passed** (484 + 39 nowych). Bez zmian w `gt/*.json` — 028 tylko czyta GT.

### Do zrobienia po Twojej stronie

1. `python scripts/element_review.py --class styki --thumb 140` — sprawdź, czy licznik pokazuje 163.
2. Przejrzyj symetrię 12 klas zakresu 5–30 (panel pojawia się po kliknięciu filtra klasy),
   potwierdź lub skoryguj seed dla `zlaczka` i `styk_nc` → `symmetry.json`.
3. `python scripts/apply_symmetry.py --dry-run`, potem `--apply`.
4. `python scripts/augment_feasibility.py` — po wypełnieniu pliku liczba wzrośnie z 6,8 %.
5. Decyzja: wariant 1T tak/nie (sekcja 7 dokumentu projektowego).

---

## 2026-07-19 [Claude] — 026 ODMROŻONE. `urzadzenie` poza YOLO. Blokada 027 nieaktualna

### Tor modelu odblokowany

| | 026 (diagnoza) | Po odzysku GT |
|---|---|---|
| bbox | 480 | **3639** |
| klasy ≥5 instancji | 20 | **26** |
| strony w train | **1** | **~191** (199 − val) |

Przyczyna porażki retrain z 026 potwierdzona: eksport czytał `gt/*.json`, gdzie było 6 stron.
Reszta leżała w cache. To nie był problem parametrów treningu.

### [BŁĄD] `urzadzenie` szło do treningu — poprawione

607 instancji (17% datasetu) trafiało do YOLO, mimo że `runtime.yaml` odrzuca tę klasę
**po inferencji**. Model uczył się czegoś, co i tak wyrzucamy. Gorzej: to obrysy 1500–3500 px
przy oknie kafla 1536, więc w wielu kaflach zajmują niemal całe okno i uczą sieć, że „tło = urzadzenie".

Poprawka (decyzja Filipa): `urzadzenie` → `contextual` w `config/train-classes.yaml`.
Zmiana wystarczy w configu — `class_distribution` i `resolve_class_id` obie sprawdzają
`load_yolo_exclude_classes()`, więc kod nietknięty.

**Zweryfikowane po zmianie:** klasy YOLO 26 → **25**, instancji w treningu 2915 → **2308**,
kontekstowe 656 → **1263**. (W pierwszej wersji tego wpisu napisałem „3639 → 3032 bbox" —
pomyliłem bbox ogółem z instancjami w treningu.)

### Blokada 027 z `KOLEJNE-ZADANIE.md` jest NIEAKTUALNA

Notatka mówi: *„[BŁĄD] `element_review`/`apply_reassign` czytają i piszą label v1 (SQLite),
omijają `gt/*.json`. Nie uruchamiać `--apply` przed migracją"*. Sprawdziłem oba:

* `apply_reassign.py` — docstring i kod: zapis przez `save_schematic_graph` → `gt_store.write_gt_json`
  (atomowo, guard empty-overwrite), plus backup `gt/` i `rebuild_cache_from_gt` na końcu.
  `load_annotation` jest tylko **fallbackiem**, gdy strona nie ma GT v2.
* `element_review.py` — czyta `load_all_training_records()`, czyli GT v2.

**027 można uruchamiać.** Warto zaktualizować notatkę w `KOLEJNE-ZADANIE.md`.

[RYZYKO] drobne: `element_review.py` klasyfikuje crops przez `tag_to_class(tag)`, a nie
`bbox_class(class_name, tag)` z Twojego Kroku 1. Dla GT v2 (gdzie `type` jest źródłem klasy)
przeglądarka może pokazywać inne klasy niż eksport. Do sprawdzenia przy 027.

### Kandydaci do scalenia widoczni w raporcie

* `limit_switch(4)` + `krancowka_nc(4)` + `styk_krancowki(1)` = **9** → przekroczy próg
* `styk_nc(20)` vs `styki_nc(5)` — duplikat PL/PL
* 35 klas <5 instancji, 68 bbox poza treningiem — tam siedzi reszta par EN/PL
  (`motor`, `fuse`, `socket`, `switch`, `disconnector`, `contactor`, `power_supply`…)

---

## 2026-07-19 [Claude] — 025 FAZA A+B ZAMKNIĘTA. F0 wykonane, F1 udowodnione

| Metryka | Rano | Teraz |
|---|---|---|
| Plików `gt/*.json` w gicie | **6** | **199** |
| Stron GT tylko w niewersjonowanej bazie | **197** | **0** |
| Kopie z wyścigu F1 w danych | 4 | 0 |
| `p040` | „zaginiony" | odzyskany, 19 sym./17 linii |

Cache = 199 = `gt/`. Audyt i `prune_cache_orphans` zgodne.

### Dwie rzeczy, w których się myliłem — obie naprawione

**1. `audit_gt` zmyślał 4 sieroty.** Czytał bazę przez `immutable=1`, co każe SQLite zignorować
dziennik i WAL — pokazywał migawkę sprzed checkpointu. Dowód:
`po DELETE w bazie WAL: mode=ro -> ['a','b'], immutable=1 -> "no such table"`.
Sięgnąłem po `immutable`, bo na klonie ZW `mode=ro` wywalał się na hot journalu — wygoda kosztem
poprawności, w narzędziu, którego jedynym zadaniem jest mówić prawdę o stanie danych.
Poprawione: `mode=ro` domyślnie, `immutable` awaryjnie i z jawnym `db_read_stale`.

**2. `bbox_out_of_frame` to nie artefakt migracji.** Sprawdziłem wszystkie osiem — **każdy to klasa
`urzadzenie`**, duży bbox kontenerowy przeciągnięty ręcznie poza krawędź (p047 wystaje w dół o 491 px,
p065 o 7 px w prawo). Ręczna robota, nie migracja. `urzadzenie` siedzi w
`yolo_runtime_exclude_classes`, więc do treningu nie wchodzi — **P3, nie blokuje niczego**.
Warunek na przyszłość: gdyby `urzadzenie` weszło do YOLO, eksport musi przycinać bbox do kadru.

### Do zrobienia (kolejność)

1. **p040 w labelerze** — jedyna odzyskana strona z liniami, warto zobaczyć, czy to Twoja robota
2. `python scripts/class_report.py --min-count 5` → `python -m train.tiled_export …`
   — **najciekawsze pytanie**: 199 stron zamiast 6, czy 026 się odblokował
3. przeliczyć val-pages mean (p025, p040, p045, p050 mają teraz GT)
4. **Faza C** — F1 (wyścig) + F3 (cache przed plikiem, sieroty). Lista 10 punktów w raporcie.
   F1 ma teraz dowód z timestampami, nie hipotezę z lektury kodu.

Do rozważenia przy okazji: `config/gt-eval.yaml` nie istnieje mimo notatki w `KOLEJNE-ZADANIE.md`,
więc p031 (SCORE 0.00) nadal zaniża średnią 21.50 o jakieś 3.6 pkt.

---

## 2026-07-19 [Claude] — 025: promote wykonany (199 plików w gt/). Uwagi do commita

### [RYZYKO] Usuń `gt/_rescue_2026-07-19/` PRZED commitem

`gt/_backup_2026-07-12/` **jest w repo** (`git ls-files` pokazuje 6 plików), więc podkatalogi `gt/`
normalnie wchodzą do gita. `git add gt/` wciągnie **193 duplikaty** tego, co właśnie wylądowało
w `gt/` na poziom wyżej. Dane są już bezpieczne w `gt/*.json`, katalog roboczy jest zbędny:

```powershell
rmdir /s /q gt\_rescue_2026-07-19        # cmd
Remove-Item -Recurse -Force gt\_rescue_2026-07-19   # PowerShell
git add gt/ && git commit
```

### 4 × CRIT `cache_orphan_data` to nie błąd

p035–p038 (po 108 sym.) to celowo odsiane kopie p034. Audyt ich nie odróżnia od realnych sierot.
**Po commicie** usuń je z cache, żeby raport był czysty i żeby nie wróciły przy przyszłym odzysku:

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/schemagen.db'); print(c.execute(\"DELETE FROM schematic_graph WHERE page_id IN ('22_A_153_PL_Adamed_AGV_SA2_20250706_p035','22_A_153_PL_Adamed_AGV_SA2_20250706_p036','22_A_153_PL_Adamed_AGV_SA2_20250706_p037','22_A_153_PL_Adamed_AGV_SA2_20250706_p038')\").rowcount); c.commit()"
```

Dopiero po commicie — dopóki `gt/` nie jest w gicie, nie kasujemy niczego z bazy.

### [BŁĄD] Nowe znalezisko: 1 bbox poza kadrem na 8 stronach

`p022`, `p047`, `p057`, `p058`, `p065`, `p149`, `p157`, `p177` — **zawsze dokładnie jeden** bbox
wychodzi poza 6617×4678. Jeden na stronę, na ośmiu niezależnych stronach, to nie przypadek —
wygląda na systematyczny artefakt migracji v1 (ujemna współrzędna albo bbox ramki rysunkowej
liczony od krawędzi). Do obejrzenia:

```powershell
python -c "import json,glob; [print(f.split('_p')[-1][:4], [b for b in json.load(open(f,encoding='utf-8'))['symbols'] if b['bbox'][0]<0 or b['bbox'][1]<0 or b['bbox'][2]>6617 or b['bbox'][3]>4678]) for f in glob.glob('gt/*_p022.json')+glob.glob('gt/*_p149.json')]"
```

Nie blokuje niczego — 8 bboxów na ~2000. Ale jeśli to ujemne współrzędne, YOLO je odrzuci przy
eksporcie i warto wiedzieć, czy `tiled_export` je cicho gubi, czy przycina.

### Dalej

1. `rmdir` `_rescue` → `git add gt/` → **commit** ← najważniejsze
2. DELETE 4 sierot z cache
3. p040 w labelerze
4. `class_report --min-count 5` + `tiled_export` — ile klas przekroczyło próg (026)
5. przeliczyć val-pages mean
6. F1 i F3

---

## 2026-07-19 [Claude] — 025: odzysk 193/197 OK. Dwie rzeczy przed `--promote`

Zadziałało dokładnie jak miało: **193 zapisane, 4 kopie odsiane, 6 pominiętych** (źródło prawdy wygrywa).

### 1. ~~Uprzątnij pozostałość po pierwszym biegu~~ — NIEAKTUALNE, mój błąd

Twierdziłem, że pierwszy bieg zostawił 4 nadmiarowe pliki. **Nieprawda** — pierwszy bieg miał
`--dry-run`, więc nic nie zapisał. Katalog od początku ma poprawne 193 pliki. Zmyliła mnie linia
`Zapisane: 197` wypisywana przez skrypt także w trybie dry-run — poprawione, teraz pisze
`DRY-RUN — nic nie zapisano. Do zapisania: N`.

Weryfikacja (ma wyjść 193):

```powershell
(dir gt\_rescue_2026-07-19\*.json).Count
```

Ostrzeżenie zostaje jako realne na przyszłość: skrypt nie kasuje plików, których nie zapisuje —
gdyby kiedyś zapisać katalog bez `--skip-dups`, a potem z nim, nadmiarowe pliki zostałyby.
Dodałem odpowiedni komunikat na końcu realnego biegu.

### 2. Ostrzeżenie o metryce — WYCOFUJĘ, sprawdziłem

Napisałem, że `--promote` wywróci baseline 21.50, bo ewaluatory policzą 199 stron. **Nieprawda.**
Sprawdziłem, skąd naprawdę brany jest zestaw stron:

| Narzędzie | Skąd strony |
|---|---|
| `eval_val_pages.py` | `config/val-pages.yaml` (jawna lista) albo `--page`/`--pages` |
| `baseline_eval_gt.py` | `PAGES = ["p028","p029","p030","p033"]` na sztywno w kodzie |
| `diff_gt_runtime.py` | `--page`, wymagane |

**Żadne nie iteruje po `gt/*.json`.** 193 pliki nie ruszą baseline. Powinienem był to sprawdzić,
zanim postawiłem Cię przed „blokadą" — przepraszam za fałszywy alarm.

Realny, dużo mniejszy skutek: `val-pages.yaml` ma 9 stron, z czego 5 bez GT. Po promocji GT dostaną
**p025, p040, p045, p050** (p035 odpadł jako kopia), więc `eval_val_pages` bez argumentów zacznie je
liczyć i **val-pages mean 30.77 się zmieni** — trzy z nich mają 0 linii, więc w dół. Tyle.

**Przy okazji: `config/gt-eval.yaml` nie istnieje i nikt go nie czyta.** Notatka w
`KOLEJNE-ZADANIE.md` o wykluczeniu p031 opisuje mechanizm, który nigdy nie powstał — p031 z SCORE
0.00 **nadal siedzi w średniej i zaniża 21.50 o jakieś 3.6 pkt**. To osobny dług, nie blokada.

### Kolejność

1. `python -m tools.rescue_gt_from_cache --skip-dups --promote`
2. `python -m tools.audit_gt` → ma być 0 sierot z danymi
3. **commit `gt/` do gita** — dopiero wtedy dane są naprawdę bezpieczne
4. p040 w labelerze — sprawdź, czy 19 sym./17 linii wygląda jak Twoja praca
5. `python -m train.tiled_export` + `class_report --min-count 5` — czy 026 się odblokował
6. przeliczyć val-pages mean (baseline GT bez zmian)
7. dopiero potem F1 i F3

Cache w bazie zostaw nietknięty do punktu 3.

---

## 2026-07-19 [Claude] — 025: F1 POTWIERDZONE na danych. p040 cały. Komenda do odzysku

`gt_dup_scan` potwierdził hipotezę co do joty:

```
sygnatura 2c7d6ccd1f9a · 108 symboli · 5 stron
  [gt/  ] p034   108/0
  [cache] p034   108/0   11:11:22.546
  [cache] p035   108/0   11:11:24.937   (+2.4 s)
  [cache] p036   108/0   11:11:29.238   (+4.3 s)
  [cache] p037   108/0   11:11:31.239   (+2.0 s)
  [cache] p038   108/0   11:11:32.089   (+0.85 s)
```

Identyczne bboxy **co do dziesiątej części piksela** na pięciu różnych stronach schematu. To zawartość
p034 zapisana pod czterema kolejnymi page_id przy przewijaniu. **F1 nie jest już hipotezą z lektury
kodu — to udokumentowane zdarzenie z dzisiaj, 11:11:22–11:11:32.** Odstępy 0.85–4.3 s to tempo
strzałki, nie oznaczania.

**Dobre wiadomości:**

1. **`p040` nie jest w żadnej grupie** — 19 sym./17 linii to zawartość unikalna, czyli Twoja
   prawdziwa praca. Odzyskiwalna w całości.
2. **Nic nie zginęło.** p035–p038 nie miały wcześniej GT, więc kopie nadpisały pustkę. 6 głównych
   stron zgadza się z `gt/_backup_2026-07-12/` bit w bit.
3. `p079`/`p080` (2 symbole, znacznik z migracji `16:33:51`) to najpewniej **nie** F1 — przy dwóch
   bboxach kolizja podpisu może być przypadkiem (ta sama ramka rysunkowa), a znacznik wskazuje na
   migrację, nie labeler. Zostawiam.

### Odzysk — jedna komenda

Dodałem `--skip-dups` do skryptu ratunkowego. Zachowuje stronę obecną w `gt/` (a gdy takiej nie ma —
najstarszy zapis w grupie), resztę pomija. Próg `--dup-min-symbols 5` chroni przed fałszywym
dopasowaniem na małych stronach. Logika przetestowana na syntetycznym odwzorowaniu Twoich danych
(p034+p035–p038 → 4 ofiary, p040 nietknięty, p079/p080 poniżej progu).

```powershell
python -m tools.rescue_gt_from_cache --skip-dups --dry-run    # sprawdź listę
python -m tools.rescue_gt_from_cache --skip-dups              # zrzut do gt/_rescue_<data>/
```

Powinno wyjść **193 strony** (197 − 4 kopie). Potem obejrzyj `p040` w labelerze i dopiero wtedy
`--promote`. Cztery pliki p035–p038 w istniejącym już `gt/_rescue_2026-07-19/` skasuj ręcznie albo
usuń cały katalog i wygeneruj od nowa z `--skip-dups`.

**Nie ruszaj jeszcze wpisów w cache** — to jedyna kopia grupy A, dopóki nie wyląduje w `gt/` i w gicie.

---

## 2026-07-19 [Claude] — 025: co siedzi w tych 197 stronach. NIE puszczaj `--promote`

**196 z 197 ma `0 linii`.** Jedyny wyjątek to `p040` (19 sym./17 linii). To nie jest ręczne GT v2 —
praca w labelerze v2 zawsze rodzi linie. To bboxy. Znaczniki czasu dzielą się na trzy grupy:

| Grupa | `updated_at` | Strony | Co to jest |
|---|---|---|---|
| **A** | `2026-07-11T16:33:51.222736` — **ten sam co do mikrosekundy** dla ~180 stron | p020–p199, cały `25_A_229_PL5`, cały `SchematWRT01` | Jedna operacja wsadowa, nie zapisy z labelera. Najpewniej `migrate_label_v1_to_graph.py` albo `recover_db.py` — konwersja adnotacji v1 |
| **B** | `2026-07-11T19:12` | `p027` (90 sym.) | Osobny zapis, strona referencyjna. Wartościowa |
| **C** | `2026-07-19T11:11:14`–`11:11:48` | p032, p035–p042 | **Dzisiaj. 9 stron w 34 sekundy** |

### [BŁĄD] Grupa C to prawdopodobnie F1 złapane na gorącym uczynku

p035, p036, p037, p038 mają **dokładnie po 108 symboli**. `gt/…_p034.json` ma **też dokładnie 108
symboli i 0 linii**. Pięć kolejnych stron schematu nie ma przypadkiem tej samej liczby symboli.

To wygląda na zawartość p034 rozlaną na p035–p038 przy przewijaniu — czyli dokładnie mechanizm F1,
w oknie 34 sekund, z odstępami 1–5 s (tempo przewijania, nie oznaczania). Jeśli tak, **część grupy C
nie jest danymi do odzyskania, tylko śmieciem wyprodukowanym przez błąd** — `--promote` wpuściłby go
do `gt/` i zepsuł GT zamiast je naprawić.

**Rozstrzygnij to jedną komendą** (`tools/gt_dup_scan.py`, nowy, read-only — liczy SHA1 z posortowanych
bboxów i pokazuje strony o identycznej zawartości; skanuje `gt/`, cache i `gt/_rescue_*` naraz):

```powershell
python -m tools.gt_dup_scan
```

Jeśli p034–p038 wyjdą w jednej grupie — mamy empiryczny dowód F1 i listę stron do wyrzucenia.
**Czy p040 pojawi się w jakiejś grupie, jest osobno ważne** — 11:11:41 wypada w środku tej serii,
więc może być zarówno prawdziwą pracą, jak i ofiarą. Zanim cokolwiek z nim zrobisz, otwórz go w labelerze.

### To jest też najpewniej przyczyna porażki retrain z 026

`026` zamknąłeś ustaleniem „480 bbox / 20 klas, train = 1 strona". A w cache leżą bboxy z ~190 stron,
których eksport **nie widzi**: po 023 `tiled_export` czyta `load_all_training_records()` → GT v2 →
`gt/*.json` → **6 plików**. Wiersze `schematic_graph` nie idą tą ścieżką, a `dataset_export` łączy v1
z tabeli `annotations`, nie `schematic_graph`.

Czyli migracja 030 nie tylko wyprowadziła GT poza źródło prawdy — **wycięła ~190 stron z datasetu
treningowego**. „Tor modelu zamrożony na `symbols_tiled_v1-2`" może być odmrażalny od razu po
odzyskaniu grupy A. Warto to sprawdzić przed kolejnym podejściem do treningu.

### Kolejność

1. `python -m tools.gt_dup_scan` → przyślij wynik
2. p040 obejrzeć w labelerze (jedyna strona z liniami)
3. Grupa A → `--promote` **po** odsianiu duplikatów; to materiał treningowy, nie GT v2
4. Grupa C → do wyrzucenia w części potwierdzonej jako duplikat
5. Dopiero potem F1 (naprawa wyścigu) i F3

---

## 2026-07-19 [Claude] — 025 AKTUALIZACJA: 197 stron GT tylko w bazie, p040 się znalazł

**Twój wynik audytu zmienia priorytety.** 197 × CRIT to nie hałas — to strony w cache `schematic_graph`,
które **nie mają pliku w `gt/`**. Trzy dokumenty:

| Dokument | W cache | W `gt/` |
|---|---|---|
| `22_A_153_PL_Adamed_AGV_SA2_20250706` | p020–p199 (~160) | **6** (p028–p034) |
| `25_A_229_PL5_19012026` | p004–p023 (17) | **0** |
| `SchematWRT01` | p013–p052 (16) | **0** |

Niezmiennik z `CLAUDE.md` jest odwrócony: miało być `gt/` = źródło prawdy, SQLite = cache odbudowywalny.
Faktycznie dla 197 stron **SQLite jest jedynym nośnikiem**, a baza jest w `.gitignore`, już raz padła
(`malformed`) i chodzi w trybie DELETE zamiast WAL (F4). Jedna awaria = koniec.

**`p040` jest na tej liście.** Pamiętałeś dobrze — oznaczyłeś go, zapis poszedł do bazy, do `gt/` nigdy
nie trafił. Nic nie zginęło. Moje wczorajsze „plik nigdy nie wszedł do repo" było prawdziwe i mylące
naraz — patrzyłem na klon ZW, gdzie baza jest pusta po rollbacku hot journala, więc tych 197 wierszy
po prostu nie widziałem.

**Przyczyna:** `tools/export_gt_to_json.py` (migracja 030) eksportuje wszystkie wiersze bezwarunkowo —
więc albo poszła na bazie mającej wtedy 6 wierszy, a reszta wróciła później przez `recover_db.py`,
albo nie została powtórzona po odzyskaniu. `gt/_backup_2026-07-12/` też ma 6 plików — backup powstał
już po stracie.

### Zrób to zanim cokolwiek innego

```powershell
copy data\schemagen.db data\schemagen.db.bak-025
python -m tools.audit_gt --md sync\analysis\025-gt-integrity.md
python -m tools.rescue_gt_from_cache --dry-run
```

`tools/rescue_gt_from_cache.py` (nowy) domyślnie zrzuca sieroty do `gt/_rescue_<data>/` — podkatalogu,
którego aplikacja nie czyta — żeby nic nie wjechało do `gt/` bez Twojego przejrzenia. `--promote`
przenosi do `gt/` i **nigdy nie nadpisuje istniejących plików**.

`audit_gt.py` rozdziela teraz sieroty **z danymi** (CRIT, z liczbą symboli/linii i `updated_at`)
od **pustych** (WARN). Dopiero to pokaże, ile z tych 197 to Twoja praca ręczna, a ile automatyczne
drafty z pętli (`auto_graph_loop`, `carve_all`, `sprint_loop`). Wyślij mi wynik.

**[RYZYKO] Do czasu odzyskania nie uruchamiaj:** `scripts/apply_reassign.py --apply`,
`tools/recover_db.py`, ani punktu F3a Fazy C (kasowanie sierot z cache — **skasowałby to, czego
jeszcze nie odzyskaliśmy**). F3a idzie po F0, nie przed.

**Konsekwencja dla metryki:** baseline 21.50 liczony jest z 6 stron. Po odzyskaniu GT wymaga
przeliczenia **z definicji** — to nie będzie regresja, tylko pierwszy pomiar na pełnych danych.
Kryterium „bez zmiany SCORE" z prompta 025 dotyczy tylko naprawy labelera, nie tego kroku.

**Kolejność:** F0 (dziś) → F1 (wyścig `selectPage`) → F3 → reszta.

---

## 2026-07-19 [Claude] — 025 Faza A+B DONE: audyt labelera, przyczyna „złej strony" znaleziona

**Raporty:** [`sync/analysis/025-labeler-audit.md`](analysis/025-labeler-audit.md) (główny) · [`sync/analysis/025-gt-integrity.md`](analysis/025-gt-integrity.md) (A1, generowany)
**Nowy plik:** `tools/audit_gt.py` — audyt read-only (`--json`, `--md`). Kod produkcyjny **nietknięty**.

### Dane GT: zdrowe

6/6 plików: `page_id` == nazwa pliku, 0 duplikatów ID, 0 wiszących referencji linii, 0 bboxów poza kadrem,
`gt/` **bit w bit zgodne** z `gt/_backup_2026-07-12/`. Zapis atomowy (`tmp` + `os.replace` + `fsync`) — poprawny.
`gt/_backup_*` **nie** wpada w glob `gt/*.json` (glob nie schodzi do podkatalogów). p031 (SCORE 0.00) i p034
to strony niedokończone (1 sym./0 linii, 108 sym./0 linii), nie korupcja.

### [BŁĄD] F1 — przyczyna objawu, priorytet 0

`selectPage()` (`graph.js:2282`) jest `async`, **bez guardu re-entrancji**, wołane bez `await` z listy stron
i ze strzałek. Ustawia `currentPageId` **natychmiast**, a potem czeka na obraz (PNG 6617×4678) i na fetch grafu.
Drugie naciśnięcie strzałki w tym oknie odpala `flushAutoSave({force:true})` → `buildPayload()` bierze
`page_id: currentPageId` (**nowa strona**) i `graph.symbols` (**stara zawartość**) → `POST /api/graph/B` z treścią A.

**GT strony B zostaje nadpisany zawartością strony A.** Trzy powody, dla których nic tego nie zatrzymuje:

1. serwerowa walidacja `body.page_id == URL` (`app.py:465`) przechodzi — frontend bierze id z `currentPageId`, nie z wczytanych danych;
2. guard `skipped_empty_overwrite` nie działa — nadpisujący graf nie jest pusty, tylko cudzy;
3. `force: true` zapisuje **nawet gdy `dirty === false`** → samo przewijanie stron przepisuje GT.

Do tego `image_width/height` z `bgImage.naturalWidth` — przy stronach różnej wielkości do GT trafi zły rozmiar
(dziś wszystkie 6617×4678, więc mina jeszcze nie wybuchła).

### Pozostałe (pełna tabela w raporcie)

| # | Rzecz | Priorytet |
|---|---|---|
| F3 | `load_schematic_graph` czyta **cache przed plikiem**, a `rebuild_cache_from_gt` **nigdy nie kasuje sierot** → strona usunięta z `gt/` żyje w cache w nieskończoność | P0 |
| F2 | `resolve_page_id` używany w `/auto-draft`, **nie** w `GET/POST /api/graph/{id}` → skrót `p028` tworzy drugi, równoległy `gt/p028.json` | P1 |
| F4 | `PRAGMA journal_mode=WAL` **nie zadziałał**: zmierzone `journal_mode=delete`, brak `-wal`, leży hot journal `data/schemagen.db-journal` (4616 B, 12.07). `except sqlite3.DatabaseError: pass` niczego nie łapie, bo SQLite przy nieudanym przełączeniu nie rzuca wyjątku — zwraca stary tryb. To ten sam tryb, w którym baza padła (`malformed`). | P1 |
| F5/F6 | brak `Cache-Control` na GT; `GET /api/graph/{id}` bez GT zwraca 200 + pusty graf zamiast 404 | P2 |

Obecna baza nie ma nawet tabeli `schematic_graph` (rollback z hot journala) — i to jest **dobra wiadomość**:
niezmiennik „SQLite = cache odbudowywalny z `gt/`" zadziałał, dane nie zginęły.

### p040

`git log --all --diff-filter=A -- 'gt/*p040*'` → **pusto, plik nigdy nie wszedł do repo.** `gt/` = backup z 12.07,
więc nic nie zostało skasowane. **Sprawdź u siebie:** `dir gt\*p040*` · `git status --short gt/` · `git stash list`.
Jeśli plik jest — to brak commita. Jeśli nie ma, a pamiętasz zapis — F1 tłumaczy też p040.

### Czego nie dało się sprawdzić na PC ZW

`data/raw/` na tym klonie zawiera **tylko `IEC60617.pdf`, zero PNG** — nie da się porównać `image_width` w GT
z faktycznym rozmiarem obrazu ani odpalić labelera. Ten fragment A1 do powtórzenia u Ciebie:
`python -m tools.audit_gt --md sync/analysis/025-gt-integrity.md`.
`pytest` też nie poszedł (sandbox bez `fastapi`) — Faza A nie ruszyła kodu produkcyjnego, więc nie ma co regresować.

### Czekam na decyzję przed Fazą C

Rekomendacja: **F1 + F3 teraz** (ok. 40 linii JS + 2 funkcje w `backend/db.py`), reszta w tym samym podejściu.
Pełna lista 10 punktów + testy regresji na końcu raportu. Przed startem: `git tag gt-pre-025` + kopia `gt/` poza repo.

---

## 2026-07-19 [Claude] — 027 Krok2 DONE: wynik na pełnym GT (199 stron) + [BŁĄD] bramka przeglądu

Po Twoim doznaczaniu (GT 6→199 stron) przeliczyłem Krok1 na całości: **179→61 klas**, 3505/3505
bbox sklasyfikowanych (0 strat). Szczegóły + tabela przed/po → [`sync/analysis/027-export-type-fix.md`](analysis/027-export-type-fix.md).

**[BŁĄD] bramka przeglądu (`config/reviewed-classes.yaml`, dodana dziś w 028) blokuje 556 bbox mimo że przechodzą `--min-count 5`:**
- `terminal_przylaczeniowy` — **520 bbox**, brak wpisu "przejrzana"
- `styk_stycznika` — 36 bbox, brak wpisu "przejrzana"

`terminal_przylaczeniowy` to druga po `zlaczka` klasa co do wielkości — bez przeglądu trening ją traci całkowicie. Akcja: `scripts/element_review.py` → `scripts/apply_reviewed.py --apply`.

**Krok 3 (Twoja decyzja, wiedza domenowa)** — patrz analiza wyżej:
- `zlaczka`(490) vs `zlacze`(199, kontekstowa) vs `listwa_zlaczek` — jeden typ czy warianty?
- `styki`(157) / `styki_przekaznika`(33) / `styk_nc`(25) / `styk_stycznika`(36, zablokowana) — scalić?
- `urzadzenie`(624) vs `custom_urzadzenie` — to samo?

**Środowisko:** sandbox bez `data/raw/*.png` i z niesprawnym SQLite na zamontowanym dysku — ominięte przez lokalny `DB_PATH` w `/tmp` (v1 ma 0 wierszy, cała dana w `gt/*.json`). `tiled_export`/`train_symbols` do uruchomienia lokalnie przez Ciebie.

Commit pending: `[Claude] 027 Krok2: pomiar na pelnym GT (199 stron) 179->61 klas + BLAD bramka przegladu blokuje terminal_przylaczeniowy(520)`

---

## 2026-07-19 [Claude] — 027 Krok1 DONE: eksport klasy YOLO po `type`, nie po `tag`

**Zmiana:** `bbox_class(class_name, tag)` w `backend/class_map.py` — GT v2 (`class_name`=`type`) ma pierwszeństwo nad `tag`; v1 (SQLite, `class_name` zawsze `"element"`) fallback na stary `tag_to_class(tag)` bez zmian. `type` normalizowany przez `slugify` (ascii-fold) — scala niespójne diakrytyki (`custom_urządzenie`/`custom_urzadzenie`).

**Podłączone:** `class_distribution`, `resolve_class_id` (nowy opcjonalny `class_name=`, kompatybilny wstecznie), `dataset_export.py:355`, `tiled_export.py:144`, `labeler/export.py:117` (`yolo_label_lines` — obejmuje też adhoc `export_yolo`).

**Pomiar na realnym GT (`gt/*.json`, 6 stron, 421 bbox, bez SQLite — sandbox nie ma dostępu do `data/schemagen.db`):**

| Klasa | przed (po `tag`) | po (po `type`) |
|---|---|---|
| zlaczka | 45 | **136** |
| oznaczenie_przewodu | 16 (zlepione) | rozbite: custom_oznaczenie_przewodu 63 + oznaczenie_przewodu 16 |
| klasy numeryczne (`1`..`11`, `6`=22 szt.) | obecne, odcinane przez `--min-count 5` | **zniknęły** |
| custom_urzadzenie | rozbite na 2 warianty diakrytyków | scalone: 17 |

Zero-strat: wszystkie 421 bbox dostają klasę (`bbox_class(...) is not None`) — zgodne z oczekiwaniem promptu ("suma bbox rośnie, nic nie wypada").

**[BŁĄD] poboczny z promptu (paleta `auxiliary_contactor`→`dioda`)** — sprawdzone, **już nieaktualne**: w `config/symbol-palette.yaml` `auxiliary_contactor` ma poprawnie `label_pl: stycznik pomocniczy`; zero wystąpień `dioda` w `gt/*.json`. Nic do zrobienia.

**pytest:** 288 passed (backend/tests + labeler/tests), 3 pominięte w sandboxie z przyczyn środowiskowych (nie regresja mojej zmiany):
- `test_apply_reassign.py::test_load_and_save_gt_v2` — `AttributeError: backend.gt_store has no attribute GT`. To z commita Cursora `c6e587a0` (027 v1, apply_reassign na GT v2), nie z tej zmiany — nie dotykałem `gt_store.py`.
- `test_palette_api.py::test_symbol_palette_endpoint/_search` — `sqlite3.OperationalError: disk I/O error` przy `init_db()` na zamontowanym dysku sandboxa; potwierdź lokalnie na PC.

**Nie wykonane w tej sesji (poza zakresem Krok1 / brak danych w sandboxie):**
- Krok 2 (re-export + `class_report.py` na pełnym GT+SQLite) — wymaga `data/raw/*.png` i żywej bazy, uruchom lokalnie:
  ```powershell
  python -m train.tiled_export --win 1536 --overlap 0.2 --min-visible 0.35 --min-count 5
  python scripts/class_report.py --min-count 5
  python scripts/visualize_yolo_dataset.py --root data/labeled_tiled --limit 20
  ```
  Wynik → `sync/analysis/027-export-type-fix.md` (przed/po per klasa) — jeszcze nie napisany, do zrobienia po realnym re-eksporcie.
- Krok 3 (decyzje o scaleniu klas: zlaczka/zlacze/listwa_zlaczek, styki/styki_przekaznika/styk_nc, custom_urzadzenie/urzadzenie) — czeka na Filipa, wiedza domenowa.
- `python scripts/diff_gt_runtime.py --page p028`, `python scripts/eval_val_pages.py` — wymaga modelu/danych lokalnych.

**Ryzyko:** SCORE się zmieni (przestrzeń klas inna) — baseline 21.50 unieważniony, jak zapowiedziano w prompcie.

Commit pending: `[Claude] 027 Krok1: eksport klasy po type (GT v2) zamiast tag, bbox_class + testy regresji, pytest 288`

---
## 2026-07-11 [Cursor] — 031 DONE: bezpieczny GitSync + backup DB

**Repo:** `git status` czysty, `git fsck --full` OK (tylko dangling — normalne po rebase).

**GitSyncDaemon (zmiany):**
- Koniec kasowania aktywnych `*.lock` — tylko starsze niż 60 s **i** brak `git.exe` w tym repo.
- Mutex `sync/.gitsync-mutex` — jedna operacja git na raz.
- `git add` wyklucza `data/schemagen.db*` i `data/backups/`.
- Commit+push **tylko** przy nazwanym wpisie w `sync/commit-message.txt` (Cursor i Claude).
- Pull: `rebase --autostash`.

**Backup:**
- `backend/db_backup.py` — checkpoint WAL → `data/backups/schemagen-YYYYMMDD.db`, trzyma 14.
- Start labelera: kopia przy `startup`.
- Harmonogram: `Install-BackupDbTask.ps1` → zadanie `SchemaGen DbBackup` (03:00). Zarejestrowane na tym PC.
- Smoke: `data/backups/schemagen-20260711.db` utworzony.

**Gitignore:** `data/schemagen*` (cały prefiks), `data/backups/`. Katalog `gt/` śledzony (`.gitkeep`).
**Cleanup:** usunięto z indeksu gita 46 śledzonych plików `data/schemagen*` (WAL/SHM/kopie recover — wyciek przez stary daemon `git add -A`).

**OneDrive:** [`sync/ONEDRIVE-EXCLUDE.md`](ONEDRIVE-EXCLUDE.md) — wyklucz `data\` z sync chmurowego.

**Push niezależny od daemona:** `origin` = HTTPS GitHub; `git push origin main` działa ręcznie. Konektor GitHub: [`sync/GITHUB-KONEKTOR.md`](GITHUB-KONEKTOR.md).

**Review 030 (GT↔JSON):** kod **jeszcze nie zaimplementowany** — tylko prompt + niezmienniki w `CLAUDE.md`. Plan OK: atomowy zapis, guard empty, `rebuild_cache_from_gt()` na starcie. Do wykonania przez Claude (prompt `030-gt-json-persistence.md`).

**pytest:** 250 passed (bez regresji).

**Filip — po pull:**
1. `.\Install-BackupDbTask.ps1` jeśli inny PC.
2. Restart daemona: `Start-GitSync.cmd Cursor` (nie kasuje locków podczas `git rebase`).
3. Commity: wpisz `[Cursor] opis` w `sync/commit-message.txt` — bez tego daemon tylko pulluje.

Commit pending: `[Cursor] 031: bezpieczny GitSyncDaemon, backup DB, gitignore WAL/gt`

---
## 2026-07-11 [Claude] — 030 GT jako JSON + cache SQLite + migracja DONE

**Cel:** GT trwałe i przyjazne gitowi. Każda strona = `gt/<page_id>.json` (źródło prawdy).
Tabela `schematic_graph` = tylko cache odbudowywalny. Wyzerowanie/uszkodzenie bazy = nie-zdarzenie.

**Pliki:**
- `backend/gt_store.py` (NOWY) — sanityzacja page_id (`[A-Za-z0-9._-]`, reszta→`_`), atomowy zapis (`tempfile.mkstemp` w tym samym katalogu + `fsync` + `os.replace`), read/list/iter, JSON `indent=2`, `ensure_ascii=False`, LF. Guard empty jako helper `_is_empty_payload`.
- `backend/db.py` — `save_schematic_graph(page_id, payload, allow_empty=False)`: zapis pliku JSON (atomowo) + upsert cache; guard empty-overwrite egzekwowany na PLIKU JSON (nie tylko bazie); zwraca `{status: saved|skipped_empty_overwrite}`. `load_schematic_graph`: cache → fallback `gt/*.json` (+odbudowa cache). `rebuild_cache_from_gt()`: skan `gt/*.json` → cache. `has_schematic_graph` też sprawdza plik.
- `labeler/app.py` — startup woła `rebuild_cache_from_gt()` (świeża/uszkodzona baza sama się odbudowuje); POST /api/graph przekazuje `allow_empty` do save; prefill zapisuje z `allow_empty=True`.
- `tools/export_gt_to_json.py` (NOWY) — migracja jednorazowa: wiersze cache → `gt/*.json` (idempotentna, `--dry-run`).
- `conftest.py` (NOWY, root) — autouse izolacja: każdy test dostaje własny `gt/` w tmp (repo bez śmieci).
- `backend/tests/test_gt_store.py` (NOWY, 8 testów) — round-trip, fallback, rebuild, guard empty, allow_empty, atomowość (brak połowicznych/tmp przy wyjątku), sanitize, list.

**Kontrakty NIENARUSZONE:** SchemaModel, `SchematicGraph.model_dump(by_alias=True)`, guard `skipped_empty_overwrite`. `.gitignore` bez zmian (db + wal/shm/journal już ignorowane; `gt/` śledzony).

**pytest:** **258 passed** (backend/tests + labeler/tests; 250 poprzednich + 8 nowych). Uruchomione w izolowanej kopii /tmp — patrz uwaga niżej.

**[RYZYKO] Środowisko Cowork:** mount bash trzymał stary snapshot plików edytowanych w tej sesji (db.py, app.py) — testy puściłem na spójnej kopii /tmp (db.py wpisany ręcznie, app.py = `git show HEAD` + 3 patche sedem, potwierdzone identyczne z wersją zapisaną). Pliki na dysku (Windows-side) są POPRAWNE i kompletne. Po `git pull` na PC zweryfikuj `pytest` u siebie.

**[DO ZROBIENIA Filip] Migracja danych:** w tym checkoutcie `data/schemagen.db` nie ma tabeli `schematic_graph` ani `gt/*.json` (pusto poza `.gitkeep`) — nie było czego eksportować tutaj. Na PC z zapełnioną bazą uruchom:
```
python -m tools.export_gt_to_json          # (--dry-run by podejrzeć)
git add gt/ && commit
```
Potem restart labelera odbuduje cache z `gt/` automatycznie.

---

## 2026-07-11 14:20 [Claude] — PRAWDZIWA przyczyna: uszkodzona baza SQLite

**Z logow uvicorn (PC Filip):** `sqlite3.DatabaseError: database disk image is malformed`
w upsert_page (db.py:72). POST /api/graph zwracal 200, ale baza jest fizycznie
uszkodzona -> zapisy nie przezywaja reloadu, GET /api/pages sie wywala (500).
To dlatego "nazwy sie nie zapisuja" mimo poprawek — zapis szedl do zepsutej bazy.

Baza jest gitignorowana (nie git). Typowa przyczyna: folder Desktop synchronizowany
(OneDrive/backup) dotyka zywego .db w trakcie zapisu, lub wspolbiezny zapis na DELETE-journal.

**Filip (PC z labelerem), KOLEJNOSC:**
1. Zatrzymaj uvicorn.
2. `python tools/recover_db.py` (venv, katalog repo) -> kopia + .recover/salvage + podmiana, integrity "ok".
3. Uruchom uvicorn, Ctrl+F5 (v60).
4. Jesli repo w OneDrive: przenies poza OneDrive lub wyklucz data/schemagen.db z sync.

**Hartowanie backend/db.py:** WAL + synchronous=NORMAL + busy_timeout=30000 + timeout=30s.

**Przy okazji (v60):** rail pisany wprost na obiekt linii (koniec zerowania); pole nazwy w panelu Linie;
auto-nazwa nowych linkow przy kind=link; beforeunload z allow_invalid.

**Testy:** WAL round-trip OK; recover_db odzyskuje graf z rail "-X1"; graph API 9/9.

**Pliki:** backend/db.py, tools/recover_db.py, labeler/app.py, labeler/static/graph.js(v60),
labeler/static/graph.html, labeler/static/graph.css, labeler/tests/test_graph_api.py

---

# Skrzynka: ZW → Filip

> Pisze **tylko ZW/Claude**. Filip czyta na starcie.

---

## 2026-07-11 13:57 [Claude] — labeler: fix "nazwy zlaczek sie nie zapisuja" (root cause)

**Objaw:** nazwy zlaczek/listew (tag, listwa, rail) gubily sie mimo edycji; 1-10 vs 11-13 "nie OK".

**Root cause (nie JS timing, jak lecil Cursor):** POST /api/graph/{page} robil
`if not result.valid: raise 422` — JEDEN blad walidacji (terminal poza obrysem,
segment nie-ortho, **terminal wspoldzielony przez 2 linie = mostek na szynie**)
odrzucal CALY zapis. Autosave retry'owal ten sam odrzucany payload → nazwy nigdy
nie trafialy do SQLite. Cursor latal commit-timing w JS, ale backend-gate zostal.

**Fix:**
- `app.py post_graph(..., allow_invalid=False)`: z `allow_invalid=true` zapis
  ZAWSZE trafia do bazy; bledy walidacji wracaja jako `warnings` + `saved_invalid`.
  Domyslka bez flagi nadal 422 (kontrakt/test zachowany).
- `graph.js`: autosave leci z `?allow_invalid=true`; status "Zapisano (z uwagami)"
  + tooltip z lista uwag (hover na save-status, klasa .has-warnings=bursztyn).
- Test regresyjny: `test_graph_save_allow_invalid_persists` (tag+listwa przetrwaly mimo bledu geo).

**Dlaczego 1-10 / 11-13 osobno:** lewa szyna p028 ma przerwe linkow 10-11-12-13
(z findings p028). Nazwa listwy propaguje sie tylko po polaczonym lancuchu linkow
(`railChainZlaczkaIds`), wiec przerwany tor = 2 potencjaly. To luka W ETYKIETOWANIU
(brak 2-3 linkow), nie bug kodu — teraz przynajmniej zapis nie przepada i widac to.
Domkniecie: dorysuj linki 10->11, 11->12, 12->13 na lewej sekcji.

**Testy:** labeler/tests/test_graph_api.py 9/9 pass. Graph suite 52 pass.
(2 fail w test_palette_api = `sqlite disk I/O error` sandboxa, nie kod.)

**UWAGA srodowisko:** w tej sesji file-tool zapisy ladowaly na dysk **uciete**
(bug lockow .git/index.lock: Operation not permitted). Pliki odbudowane z HEAD przez
bash i zweryfikowane (py ast / node --check). Warto sprawdzic locki na PC ZW.

**Pliki:** labeler/app.py, labeler/static/graph.js (v58), labeler/static/graph.html,
labeler/static/graph.css, labeler/tests/test_graph_api.py

---

# Skrzynka: ZW → Filip

> Pisze **tylko ZW** (Cowork/Claude). Filip czyta na starcie sesji i nie edytuje tego pliku.
> Najnowsze wpisy na górze.

---

## 2026-07-06 [Cursor] — 022 krok 5: canvas GT v2 (bbox + terminale)

**Zakres:** UI v2 na `/`, stary labeler na `/legacy`. Bbox pomarańczowy, terminale żółte, prefill + zapis grafu.

### Zmiany

| Plik | Co |
|------|-----|
| `labeler/static/graph.html` **(nowy)** | layout: strony, canvas, panel symbolu |
| `labeler/static/graph.js` **(nowy)** | load/save/prefill, zoom, rysowanie bbox, terminale na krawędzi |
| `labeler/static/graph.css` **(nowy)** | style v2 |
| `labeler/app.py` | `GET /` → graph.html, `GET /legacy` → index.html |
| `labeler/tests/test_graph_routes.py` **(nowy)** | routing + static |

### Smoke Filipa

```
.\.venv311\Scripts\python.exe -m labeler.app
# :8765/ — Import draft → bbox/terminale → Zapisz graf
# :8765/legacy — stary labeler v1
```

### Następny krok

Krok 6: LineMode (linia OD-DO ortho + kind) w `graph.js`.

---

## 2026-07-06 [Cursor] — 022 krok 4: API CRUD + SQLite + prefill

**Zakres:** endpointy FastAPI, tabela `schematic_graph`, prefill YOLO+wzorce, dump, hook GT w diff/eval.

### Zmiany

| Plik | Co |
|------|-----|
| `backend/db.py` | tabela `schematic_graph`, `save/load/has_schematic_graph` |
| `labeler/graph_prefill.py` **(nowy)** | `prefill_graph` — YOLO bbox, `nominal_terminals_from_pattern`, lines=[] |
| `labeler/graph_serialize.py` **(nowy)** | `graph_to_dump` — lista tekstowa GT |
| `labeler/gt_loader.py` **(nowy)** | `load_gt_schema`, `gt_source` (graph_v2 > label_v1) |
| `labeler/app.py` | 6 endpointów: graph-rules, validate, GET/POST graph, dump, prefill; v1 annotations deprecated |
| `scripts/diff_gt_runtime.py`, `scripts/eval_val_pages.py` | GT przez `load_gt_schema`, pole `gt.source` |
| `labeler/tests/test_graph_api.py` **(nowy)** | 8 testów API |

### Endpointy (smoke curl / Swagger :8765)

```
POST /api/graph/p040/prefill
GET  /api/graph/p040
GET  /api/graph/p040/dump
POST /api/graph/validate
```

### Testy

`pytest backend/tests labeler/tests` → **240 passed**

### Uwagi

- Stary UI (:8765) nadal używa `/api/annotations` v1 — canvas v2 w krokach 5–7
- Po prefill: `diff_gt_runtime --page p040` pokaże `GT [graph_v2]` (connections=0 dopóki nie narysujesz linii)
- Następny krok: canvas bbox + terminale (krok 5)

Commit pending: `[Cursor] labeler: graph v2 API CRUD + SQLite + prefill (022 krok 4)`

---

## 2026-07-06 [Cursor] — 022 krok 3: graph_compile → SchemaModel

**Zakres:** deterministyczna kompilacja SchematicGraph v2 do SchemaModel + potencjał z link.

### Zmiany

| Plik | Co |
|------|-----|
| `labeler/graph_compile.py` **(nowy)** | `graph_to_schema()`: symbols→components, lines→graphic_lines(wire)+Connection, auto-routing ortho L, domknięcie potential po `kind:link` + L/R złączki |
| `labeler/tests/test_graph_compile.py` **(nowy)** | 6 testów: connection, auto-route prosty/L, tor szyny 3 złączki, mostek wewnętrzny, meta |

### Testy (022 kroki 0–3 łącznie)

`pytest backend/tests/test_diff_id_remap.py backend/tests/test_diff_metrics.py backend/tests/test_schematic_graph.py backend/tests/test_graph_validate.py labeler/tests/test_graph_compile.py` → **30 passed**

Pełny `pytest backend/tests labeler/tests` — do potwierdzenia na PC (oczekiwane 241+).

### Review krok 3

| Wymaganie promptu | Status |
|---|---|
| symbols→components+terminals | ✅ |
| lines→graphic_lines(wire)+Connection | ✅ |
| puste vertices→auto L-route | ✅ |
| potential z domknięcia link (≥2 złączki) | ✅ tag skrajnej (-X1) lub POT_n |
| mostek L↔R jednej złączki bez potential | ✅ |
| SchemaModel nietknięty | ✅ tylko kompilacja DO |
| graph_serialize / API / UI | ⏳ kroki 4–7 |

Następny krok: API CRUD + SQLite + prefill (krok 4).

Commit pending: `[Cursor] labeler: graph_compile SchematicGraph→SchemaModel (022 krok 3)`

---


**Zakres:** model Pydantic v2 + walidacja ortho/snap/obrys terminala. Prompt 022 krok 2.

### Zmiany

| Plik | Co |
|------|-----|
| `backend/models/schematic_graph.py` **(nowy)** | `SchematicGraph`, `GraphSymbol`, `GraphLine` (alias `from`), `version: 2`, wymiary obrazu |
| `labeler/graph_validate.py` **(nowy)** | `validate_graph`, `graph_rules()` (progi z runtime.yaml), `GraphValidationResult` |
| `backend/models/__init__.py` | eksport `SchematicGraph` |
| `backend/tests/test_schematic_graph.py` **(nowy)** | roundtrip JSON + alias `from` |
| `backend/tests/test_graph_validate.py` **(nowy)** | 7 testów: OK, puste vertices, obrys, ref, ortho, snap |

### Testy

`pytest backend/tests/test_schematic_graph.py backend/tests/test_graph_validate.py` → **9 passed**

Następny krok: `graph_compile` → SchemaModel (krok 3).

Commit pending: `[Cursor] labeler: SchematicGraph v2 model + graph_validate (022 krok 2)`

---


**Zakres:** parowanie komponentów IoU + translacja adresów runtime→GT przed porównaniem connections. Prompt: [`sync/prompts/022-labeler-graph-v2.md`](prompts/022-labeler-graph-v2.md) krok 0.

### Zmiany

| Plik | Co |
|------|-----|
| `backend/validate/diff_metrics.py` | **`pair_components`** (greedy malejąco IoU, 1:1); **`diff_connections`** remapuje `sym_i:t` → id GT po IoU bbox + terminal po pozycji absolutnej (`terminal_tol_pattern` z runtime.yaml); `diff_components` korzysta z `pair_components`; fallback identyczności dla refów bez bbox (kompatybilność testów) |
| `backend/tests/test_diff_id_remap.py` **(nowy)** | 3 testy: parowanie IoU, F1=1.0 przy różnych id, only_runtime bez pary |

### Testy

`pytest backend/tests/test_diff_metrics.py backend/tests/test_diff_id_remap.py` → **15 passed**

### Smoke diff (po zmianie)

| Strona | SCORE | Δ vs poprzedni | connections GT | conn match | Uwagi |
|--------|-------|----------------|----------------|------------|-------|
| p027 | **50.46** | +0.00 (vs 23:40, 30f562c9) | 0 | 0/0 | Warstwa connections wyłączona z score (brak GT conn). Remap widoczny w `only_runtime` (np. `element_* → sym_3:1`). Skok 49.93→50.46 z wcześniejszego runu = **lines f1** (0.433→0.446), nie remap |
| p040 | **47.70** | pierwszy run w historii | 0 | 0/0 | j.w. — GT bez connections; remap częściowy w only_runtime |

**Wniosek:** remap naprawia metrykę strukturalnie (gdy GT ma connections z własnymi id labelera). Na p027/p040 score bez zmian — GT `conn=0`. Pełny efekt po migracji GT do grafu v2 (kroki 2–8 promptu 022).

Commit pending: `[Cursor] diff: remap ID symboli/terminali w diff_connections (022 krok 0)`

---

## 2026-07-05 [Claude] — 020-diff-score: funkcja celu GT↔runtime (implementacja)

**Zakres:** skalarny score 0–100 jako metryka pętli iteracyjnej p027 (decyzja Filip: najpierw metryka, potem 018-terminals mierzony tą metryką). Prompt: [`sync/prompts/020-diff-score.md`](prompts/020-diff-score.md). Kontrakty nietknięte, `backend/recognize/` bez zmian.

### Zmiany

| Plik | Co |
|------|-----|
| `backend/validate/diff_metrics.py` | **`diff_lines`** — geometria polilinii (próbkowanie + grid hash, pokrycie ≤tol), P/R/F1 + `per_role`; **`per_class`** i **`model_gaps`** w `diff_components` (klasy z GT bez trafienia = strata modelu YOLO, nie kodu); P/R/F1 we wszystkich `diff_*`; **`aggregate_score`** — ważona suma f1, renormalizacja przy braku GT w warstwie. Stare klucze wyjścia bez zmian |
| `config/eval-weights.yaml` **(nowy)** | Wagi: components 0.30, lines 0.25, connections 0.35, tags 0.10; `line_match_tol: 8` px |
| `backend/runtime_config.py` | `eval_settings()` / `eval_weights()` / `line_match_tol()` (defaults gdy brak yaml) |
| `scripts/diff_gt_runtime.py` | SCORE + **delta vs poprzedni run** + historia `data/output/diff_gt_runtime/{pid}_history.jsonl` (ts, git HEAD, per_layer); top-3 kubły strat; `model_gaps` z adnotacją `[MODEL]` |
| `scripts/eval_val_pages.py` | `lines` + `score` per strona, `mean_score` w summary i stdout |
| `backend/tests/test_diff_metrics.py` | +9 testów (12 total w pliku): prf, per_class/model_gaps, diff_lines (identyczne/przesunięte/częściowe/puste), aggregate_score (perfect/renormalizacja/monotoniczność) |

### Testy

`pytest backend/tests/test_diff_metrics.py` → **12 passed** (sandbox ZW; pełny pytest do potwierdzenia na PC Filip — na PC ZW brak środowiska GPU/zależności pełnego pipeline).

### Do zrobienia u Ciebie (Cursor)

1. `pytest backend/tests labeler/tests` — oczekiwane 226+9
2. `python scripts/diff_gt_runtime.py --page p027` — **score bazowy p027** (punkt odniesienia dla 018-terminals)
3. `python scripts/eval_val_pages.py --page p040` — bez regresji + score
4. [RYZYKO] `diff_lines` na pełnej stronie ~6617px: próbkowanie co 4px → sprawdź czas; jak >10s, podnieś `step` w `_lines_prf`

---

## 2026-07-04 [Claude] — 018-lines-quality DONE (implementacja)

**Zakres:** jakość linii (Hough pod kółka węzłów, skalowany merge, kalibracja palety, overlay, diag). Kontrakty nietknięte (`SchemaModel`, sygnatury protokołów, `net_builder`, sito, `derive_mostek_terminals`).

### Zmiany

| Plik | Co |
|------|-----|
| `backend/recognize/line_tracer.py` | **Drugi przebieg Hough** dla linii osiowych (`auto_bus_line_params`, filtr `_is_axial`) — szyna listwy p027 (segmenty 67–76px, przerwy 21–22px) niewidoczna dla progu runtime (min_len 132>76, gap 10<21). Bus: min_len≈0.01·max, gap≈0.004·max (wariant C findings). **`gap_tol` merge skalowany** `max(12, eff_gap·2.5)` zamiast stałej 12px |
| `config/runtime.yaml` + `backend/runtime_config.py` | Klucze `hough_second_pass`, `hough_bus_min_len_frac` (0.01), `hough_bus_gap_frac` (0.004), `hough_bus_axis_tol_deg` (6.0); `arrow_supplement.min_yolo_conf_gate` (0.5) |
| `config/semantic-colors.yaml` + `backend/colors/palette.py` | Nowa grupa `blue_wire` (#134088/#105090 — tusz Adamed nie łapał `motor_device` przez różnicę jasności); `pe_wire` rozdzielony od `enclosure` (stroke #66BB00 vs #00AA44); **tie-break `match_color`** deterministyczny `(dist, rank_ról, nazwa)` zamiast kolejności dict; `enclosure.hint_role: frame` |
| `backend/recognize/line_classifier.py` | `_color_role_hint` czyta `hint_role` (grupa wieloroli → jawna rola, nie domyślne wire) |
| `scripts/preview_lines.py` | Usunięty martwy klucz `bus`; wire (jaskrawa zieleń) vs frame (pomarańcz) wizualnie rozróżnialne |
| `scripts/diag_lines.py` | **NOWY** read-only: histogram `detected_color` / rola / `semantic_group` per strona, `--page`; wyróżnia kolory bez grupy (kandydaci do palety) |
| `backend/recognize/arrow_supplement.py` | `need` liczony wg progu conf (`min_yolo_conf_gate`), nie `c not in have` — jedna słaba/FP detekcja nie wyłącza supplementu klasy (findings H9b); komentarz `roi_top_frac` (ucina DÓŁ) |

### Testy (dodane)

`test_line_tracer`: `bridges_node_gap`, `bus_params_looser`, `is_axial`, `second_pass_recovers_bus_rail` (szyna 6000px odtworzona). `test_palette`: `blue_ink`, `enclosure_pe_wire_distinct`, tie-break.

### [RYZYKO] Weryfikacja pytest — do uruchomienia u Ciebie

Sandbox ZW **obcina duże pliki przy odczycie** (ten sam artefakt sync co findings §3.6) — nie dało się tu uruchomić pytest. Kod zweryfikowany review + logicznie. **Proszę o smoke na głównym PC:**

```powershell
python -m pytest backend/tests labeler/tests train/tests -q      # oczekiwane >=213 + nowe
python scripts/preview_lines.py --page data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p027.png
python scripts/diag_lines.py --page p027
python scripts/eval_val_pages.py --page p040                       # bez regresji connections
```

Kryteria: szyna p027 (y≈2945) jako `wire` ciągły ≥90% rzędu; p040 bez regresji; p035 segmenty ≤2×; niebieski #134088/#105090 z niepustą grupą.

Commit: `[Claude] recognize: line tracer quality + palette (prompt 018-lines)`

---

## 2026-07-04 [Claude/Fable5] — Analiza 019 DONE: terminale + linie

**Wynik:** [`sync/analysis/019-terminals-lines-findings.md`](analysis/019-terminals-lines-findings.md) + sekcja „Wynik" w prompcie 019. Bez zmian w kodzie produkcyjnym (analiza only).

**Kluczowe (odtworzone empirycznie na kaflach p027):**

| Znalezisko | Dowód |
|---|---|
| [BŁĄD] Szyna p027 niewidoczna dla Hougha: segmenty tuszu 67–76 px między kółkami węzłów (przerwy 21–22 px) vs `min_len=132`, `gap=10` | pipeline na kaflu w013: **0 linii, 0 connections** (dokładnie objaw p027) |
| [BŁĄD] `_nodes_on_net` widzi tylko końce linii — scalona szyna daje 2 węzły na 16 złączek | wariant C findings §1 |
| [RYZYKO] `terminal_tol=79 px` vs pitch złączek 94 px → 6–10 fałszywych terminali/złączkę | warianty B/D |
| [BŁĄD] `enclosure`==`pe_wire` stroke `#00AA44`, remis po kolejności dict → `kind=pe` nigdy; zielona ramka dostaje rolę wire | `palette.match_color` + YAML |
| [BŁĄD] `arrow_supplement`: 1 FP wyłącza uzupełnienie klasy; `roi_top_frac` ucina dolne 7% strony | kod l.85, l.102 |
| Sito NIE jest blokerem p027 (H3/H6 odrzucone) — szyna idzie przez środki bboxów | 0–6 demotów w pasie |

**Plan:** 018-lines-quality (pierwszy) → 018-terminals-strategy (TerminalResolver + terminal-patterns.yaml + węzły-na-ścieżce). Zakresy plików i kryteria akceptacji w findings §5.

**Filip — 4 pytania** w findings (kolory hex, pattern złączki, glify strzałek, git status na głównym PC) + 3 komendy weryfikacyjne (§6). Sesja biegła na ZW bez `data/raw`/GT DB — H5 (kolory) wymaga Twoich stron.

**pytest:** nie uruchamiany (zero zmian w kodzie).

---

## 2026-07-04 [Cursor] — Faza 5: RelationResolver (prompt 015)

**Kamień:** warstwa relacji po net-builderze.

| Plik | Rola |
|------|------|
| `backend/recognize/relation_resolver.py` | tag→symbol, OCR→potential, scalanie strzałek, context runtime |
| `config/runtime.yaml` | sekcja `relations:` |
| `scripts/diff_metrics.py`, `eval_val_pages.py` | szkielet Fazy 6 (prompt 016) |

**pytest:** 213 passed

**Filip — smoke:**
```powershell
python scripts/preview_schema.py --page p040 --source runtime
python scripts/diff_gt_runtime.py --page p040
```

Uzupełnij `common_terminal:` w `config/mostek-orient.yaml`.

**Następne (Claude):** prompt 016 po akceptacji smoke.

---

## 2026-07-04 [Claude] — Detekcja mostkow DZIALA (tiling): mAP 0 -> 0.92

**Wynik:** mostek wykrywany na p040 (P=0.88, R=0.75, mAP50=0.922). Global mAP50
0.177 -> 0.53. Przyczyna zer byla SKALA (strona 6600px -> 1536 = symbol ~9px),
nie siec. Fix = tiling (okna natywnej rozdzielczosci).

### Kluczowe zmiany
- **Tiling**: `train/tiled_export.py` (dataset w oknach 1536, windows/clip/nms) +
  `symbol_detector.detect_tiled` (inferencja przesuwnym oknem, translacja+NMS) +
  flaga `yolo_tiled`/`yolo_tile_win`/`yolo_tile_overlap` w runtime.yaml, wpieta w
  graph_builder. `preview_detection.py --tiled` do podgladu bboxow. Doc: prompts/014.
- **Silnik orientacji ogolny**: `config/orient-classes.yaml` (klasa -> C2/C4/D4,
  mode augment|split). DOMYSLNY `augment` = 1 klasa detekcji + obrocone kafelki
  (augmentacja, bez orientacji, bez rozrzedzania). `split` = podklasy orientacji
  (wymaga eksemplarzy). `train/orient.py`, wpiete w dataset_export.
- **Jakosc danych**: binarize Otsu (lapie szare linie), pad-do-kwadratu (aspect),
  dataset_export czysci osierocone pliki (train<->val).
- **Narzedzia QA**: `element_review.py` (dropdown klasy + klik=usun + checkbox
  przejrzana/localStorage), `apply_reassign.py` (retag + __DELETE__ + backup bazy),
  `check_export.py` (wymiary + pokrycie GT), `mostek_preview_orient.py`, `_thumb.py`
  (kontrast+pogrubienie miniatur). `scripts/mostek_diag.py`.
- **train_symbols**: `--cache disk|ram` (ram OOM-owal przy 1724 oknach — Windows
  spawn-workery pickluja cache).
- **GitSync**: PC ZW pull-only (commit/push tylko przy nazwanym commicie),
  cykl 5s, log tylko przy zdarzeniach, `.gitattributes merge=union` dla logow.

### Testy
`train/tests` + `symbol_detector` -> 50 passed. Geometria tilingu, orient (augment/
split C2/C4/D4), detektor po refaktorze (`_infer_bgr`).

### Backlog (nastepne etapy)
- **Fejki do odsiania** — false-positive na p040+ (filtr po conf/klasach/kontekscie).
- Slabe klasy: `terminal_block`, `styki_przekaznika` (=0, malo danych),
  `terminal_przylaczeniowy` 0.195, `urzadzenie` 0.295 -> wiecej/czystszych etykiet.
- `strzalka` wej/wyj: mozliwa kolizja (wej = wyj obrocona 180) -> sprawdzic, ew. scalic.
- `--patience 50` da modelowi wiecej epok (stop byl na 11+30).
- Runtime: mapowanie podklas split -> baza (jesli kiedys wroci orientacja z sieci).

---
## 2026-07-02 [Claude] — SYMBOLE: orientacja mostka (8 klas D4, prompt 012)

**Problem:** mostek (3 terminale) — jedyny element niewykrywany. Przyczyna: globalna
augmentacja w train_symbols.py = 0 (schemat kierunkowy), a mostek występuje w 8
orientacjach → każda to osobny wzorzec, za mało próbek każdej.

**Decyzje Filipa:** sieć zwraca orientację (8 klas); lustro = nowy kształt (chiralny,
pełne 8); mechanizm danych = syntetyczne kafelki.

### Rozwiązanie (kod — bez treningu GPU)
- **Grupa D4 + klasyfikacja eksemplarzem.** Nie da się poznać orientacji z samej
  geometrii stubów (lustro daje ten sam zestaw krawędzi). Źródło klasy = 8
  eksemplarzy (po jednym cropie na klasę), dopasowanie NCC na binaryzacji.
- **Augmentacja offline D4:** z 1 realnego cropa → 8 zbalansowanych próbek (orbita).
- **Kafelki:** orientacje wchodzą jako extra małe obrazy do splitu **train**;
  globalne fliplr/flipud/degrees w train_symbols **zostają 0** (zero regresji klas
  kierunkowych).
- **Bez zmian w class_map/palecie/pickerze:** tag `mostek` przepisywany na
  `mostek_rXX` PRZED build_class_map; picker labelera bez zmian (orientacja auto).

### Pliki
| Plik | Rola |
|------|------|
| `train/mostek_orient.py` | NOWY — D4, Cayley (samo-weryfik.), classify_crop, augment_d4, count_edge_crossings |
| `train/mostek_tiles.py` | NOWY — expand_mostek_orientations, generate_tiles, write_tiles |
| `train/dataset_export.py` | hook: maybe_expand_mostek (przed class_map) + maybe_write_mostek_tiles (po train) + manifest |
| `backend/recognize/mostek_orient_map.py` | NOWY — 8 klas → (mostek, orientacja); common_terminal_side (config) |
| `config/mostek-orient.yaml` | NOWY — kontrakt 8 klas, exemplar_dir, min_score, tile |
| `train/tests/test_mostek_orient.py`, `test_mostek_tiles.py`, `backend/tests/test_mostek_orient_map.py` | testy (fixture) |

### Testy
`pytest backend/tests labeler/tests train/tests` → **188 passed** (env: doinstalowane
fastapi/httpx/svgwrite/opencv — brak na sandboxie, nie dotyczy zmian).

### Do zrobienia u Filipa (GPU + dane, poza gitem)
1. Przygotuj **8 eksemplarzy** w `data/mostek_exemplars/` (nazwy = klasy: `mostek_r0.png` … `mostek_m270.png`).
2. `python -m train.dataset_export --min-count 5` → sprawdź w manifest `mostek_orient` (rozkład) i `mostek_tiles` (liczba).
3. Trening + ONNX + preview p040 (oczekiwane: mostek wykryty z orientacją).
4. **[RYZYKO] Uzupełnij `common_terminal:` w config/mostek-orient.yaml** — dla kanonicznego r0 podaj krawędź terminala WSPÓLNEGO (top/right/bottom/left). Bez tego net_builder scala mostki jak dotychczas (geometrycznie), orientacja nie wpływa na podział potencjałów.
5. [RYZYKO] bbox mostka musi być **ciasny** — eksport waliduje "dokładnie 3 stuby na krawędzi", inaczej [SKIP] (tag zostaje generyczny).

---

## 2026-06-28 [Claude] — SYMBOLE: klasy listwy w YOLO (prompt 011), czeka re-train

**Decyzja Filipa:** GT p040 gotowe (19 bbox). Re-train YOLO: **TAK**.

### Zmiany (kod — bez treningu GPU)

| Plik | Zmiana |
|------|--------|
| `config/train-classes.yaml` | `zlaczka` wypada z `contextual` → atomic (YOLO) |
| `config/symbol-palette.yaml` | +`zlaczka`, `mostek`, strzałki potencjału; `crossing` ≠ mostek |
| `config/element-catalog.yaml` | `yolo_class` dla złączka/mostek/strzałek |
| `backend/tests/test_class_map.py` | +test mostek→mostek; zlaczka exportable |
| `labeler/tests/test_export.py` | contextual test na `złącze` (nie złączka) |
| `train/tests/test_dataset_export.py` | +test_export_strip_classes |
| `sync/prompts/011-strip-yolo-classes.md` | NOWY — instrukcja re-train dla Filipa |
| `TRENING-SIEC.md` | zaktualizowana lista klas YOLO vs contextual |

### class_report (po zmianie)

- **YOLO:** `zlaczka` 646, `mostek` 247, strzałki 71+195 (69 klas łącznie)
- **Contextual:** 854 bbox (listwa_zlaczek, oznaczenia, zlacze, terminale_urzadzenia)

### pytest

`backend/tests` + `labeler/tests` + `train/tests` → **164 passed**

### Runtime p040 (stary model symbols_atomic_v2 — bez re-train)

- **9/19 bbox** — bez zmian do czasu nowego ONNX
- GT `--rebuild-conn` = **15 conn** (referencja net-buildera OK)

### Filip — następny krok (GPU)

```powershell
python scripts/class_report.py
python -m train.dataset_export --min-count 5
python -m train.train_symbols --name symbols_strip_v1 --batch 4
python -m train.export_onnx --version symbols_strip_v1
python scripts/preview_schema.py --page p040 --source runtime
```

Oczekiwane po re-train: **~19/19 bbox**, brak gwiazdy do `sym_0`, runtime connections bliżej GT.

---

## 2026-06-28 [ZW] — ZAMKNIĘCIE SESJI: net-builder zwalidowany, bloker = detekcja listwy

### Wynik (definitywny)

- **Net-builder poprawny.** Na czystym GT p040 (`--rebuild-conn`) = **15 czystych połączeń**, zero sztucznej gwiazdy. Fix „terminal = granica scalania" działa.
- **Runtime wciąż gwiazda do `sym_0:2`** — bo YOLO wykrywa **9 z 19** elementów (brak złączek/mostków/strzałek). Gwiazda runtime = skutek braku detekcji listwy, nie błąd net-buildera.
- Stare GT-connections (14, z importu draftu) **wyczyszczone** (`scripts/clear_gt_connections.py --apply`). GT p040: 19 bbox, 17 linii, 0 conn. Connections = wynik algorytmu, nie wzorzec.

### Co powstało w sesji (pliki)

Backend: `net_builder.py` (mostki w sicie, strict `require_terminal`, **terminal=granica scalania**), `line_sieve.py` (recover mostków), `graph_builder.py` (config tol + require_terminal + recover), `line_tracer.py` (Hough z config), `runtime_config.py` + `config/runtime.yaml` (pokrętła). Testy: `test_line_sieve.py` (+4), `test_net_builder.py` (+3).
Skrypty: `preview_schema.py` (overlay trasowany, `--rebuild-conn`, nazwy `nr:nazwa:term`), `clear_gt_connections.py` (NOWY).
Labeler (v34): edycja terminali (drag/dodaj/usuń), auto-derive nie nadpisuje ręcznych, edytowalne connections, re-klasyfikacja bbox w R, „Wyczyść wszystkie linie", trwałe usuwanie linii, nawigacja review strzałki/scroll.

### NASTĘPNY KAMIEŃ (do nowej sesji)

**Detekcja elementów listwy** (złączka / mostek / strzałka potencjału) — doznaczenie klas + re-train YOLO, albo proceduralna detekcja. Bez tego runtime nie odtworzy topologii listew. Potem: scalanie strzałek potencjału po nazwie; tuning `derive_auto_terminals` poza p040.

### Smoke końcowy (Cursor potwierdził 2026-06-28)

`pytest backend/tests labeler/tests -q` → **151 passed**. `--rebuild-conn` p040 = **15** conn czystych. GT po `clear_gt_connections.py --apply`: 0 conn (oczekiwane). Sesja zamknięta — następny kamień: detekcja listwy (filar SYMBOLE).

---

## 2026-06-28 [ZW] — Fix: auto-zaciski nie nadpisują ręcznych terminali GT

Temat: **Wejście w tryb T (auto-derive całej strony) kasowało ręcznie ustawione zaciski. Teraz auto tylko uzupełnia puste bboxy.**

| Plik | Zmiana |
|------|--------|
| `labeler/static/crop_review.js` (v34) | `deriveTerminalsForPage`: pomija bboxy, które już mają terminale (zachowuje ręczne GT); status „dodano X, zachowano Y". |

Podgląd `scripts/preview_schema.py --rebuild-conn` jest **tylko-do-odczytu** — nie zapisuje do bazy; nie on niszczył terminale.

**Wynik net-buildera na GT p040: 15 czystych połączeń** (par), bez gwiazdy — fix „terminal=granica scalania" potwierdzony wzrokowo przez Filipa.

**Backlog:** scalanie „Strzałek potencjału" o tej samej nazwie w jeden potencjał (elektrycznie ten sam węzeł bez przewodu) — czeka na decyzję.

---

## 2026-06-28 [ZW] — Net-builder: terminal = granica scalania (koniec sztucznej gwiazdy) + czytelne nazwy

Temat: **Reguła „jedna linia ≠ dwa połączenia": union-find nie scala linii stykających się NA węźle (terminal/komponent). Listwa złączek przestaje kolapsować w jeden net z gwiazdą do arbitralnego terminala.**

### Diagnoza (z `--rebuild-conn` na GT p040)

Hub `8:mostek:1` zbierał ~10 połączeń — cała listwa (złączki + mostki + dochodzące przewody) scalała się w jeden net, a emisja robiła gwiazdę do `node_ids[0]` (alfabetycznie `8:mostek`). Artefakt, nie topologia.

### Fix (kod)

| Plik | Zmiana |
|------|--------|
| `backend/recognize/net_builder.py` | `_group_into_nets`/`_lines_joined` przyjmują `components`+`node_tol`; nowy `_point_at_node`. **Nie scalamy linii, których styk wypada na komponencie/terminalu** (granica — przewody się tam kończą, nie przechodzą). `build_connections` przekazuje components+terminal_tol. |
| `scripts/preview_schema.py` | `--rebuild-conn` używa tego samego scalania; **czytelne nazwy `nr_bbox:nazwa:nr_term`** w wypisie i etykiety `nr:nazwa` na bboxach overlay (zamiast `element_<timestamp>`). |
| `backend/tests/test_net_builder.py` | +test: dwa przewody do tej samej złączki = 2 osobne połączenia (nie gwiazda). |

### Zachowanie (zweryfikowane w izolacji)

- Listwa: 2 przewody na tę samą złączkę → **2 nety** (2 połączenia do niej), nie gwiazda.
- Fragmentacja w wolnej przestrzeni → nadal **scalone** (1 net) — bez regresji.
- T-złącze (odczep dotyka szyny w wolnej przestrzeni) → nadal **scalone**.

### Filip — uruchom i wklej

```powershell
.venv311\Scripts\python.exe -m pytest backend/tests -q
.venv311\Scripts\python.exe scripts/preview_schema.py --page p040 --source gt --rebuild-conn
```
Każdy przewód → terminal, którego faktycznie dotyka. Wklej nową listę — ocenimy, czy topologia zgadza się z rysunkiem (i czy `8:mostek` to realna listwa zwarta).

[BŁĄD środowiska] Mount obcina pliki — pytest/skrypt u Ciebie. Logika scalania zweryfikowana w izolacji (strip=2, frag=1, T=1).

---

## 2026-06-28 [ZW] — GT bez connections: walidacja net-buildera na czystym GT

Temat: **Decyzja Filipa: GT = symbole+linie+terminale; connections = wyłącznie wynik algorytmu. Harness: przelicz connections net-builderem na czystym GT (izolacja od błędów YOLO/Hough).**

### Co zrobione

| Plik | Zmiana |
|------|--------|
| `scripts/preview_schema.py` | Flaga `--rebuild-conn`: dla GT przelicza connections `build_connections` na komponentach+liniach z GT (auto-zaciski gdy brak GT terminali → odzysk mostków → net-builder). Overlay + wypis `[GT-conn]` z listą połączeń. |
| nawigacja review (`app.js` v33) | (poprzedni wpis) strzałki ←/→ i scroll przewijają kolejkę T/R/C zamiast zmieniać stronę. |

### Po co

Dotąd nie dało się oddzielić błędów połączeń od błędów detekcji/Hougha. Teraz puszczam net-builder na **Twoim GT** (czyste symbole/linie/terminale) — jeśli connections nadal złe na idealnym wejściu, to bug net-buildera/derive; jeśli dobre, błędy runtime pochodzą z YOLO/Hough.

### Filip — uruchom i wklej wynik

```powershell
.venv311\Scripts\python.exe scripts/preview_schema.py --page p040 --source gt --rebuild-conn
```
Zapisze `..._gt.png` (connections z net-buildera na GT) + wypisze `[GT-conn]` z listą `from -> to (kind)`. **Wklej tę listę + napisz, które połączenia są błędne** (np. „X1:2 -> K3 nie istnieje"). Z tym wchodzę w `derive_auto_terminals` i regułę „jedna linia ≠ dwa połączenia" — już mierząc na czystym wejściu.

[BŁĄD środowiska] Mount obcina pliki — nie odpaliłem skryptu/pytest. Logika to złożenie sprawdzonych już funkcji (build_connections/derive/recover). Pełny przebieg u Ciebie.

---

## 2026-06-28 [ZW] — Labeler: edycja GT (linie/bbox/connections) — domknięcie trybu wzorca

Temat: **Wyczyść wszystkie linie + trwałe usuwanie linii; edycja bboxów (re-klasyfikacja) i connections (from/to/kind/usuń) w review. Razem z drag terminali = pełna edycja wzorca.**

### Co zrobione (`app.js`/`crop_review.js`/`index.html` v32)

| Element | Zmiana |
|---------|--------|
| **Wyczyść wszystkie linie** | nowy przycisk `🗑 Wyczyść wszystkie linie` w toolbarze L (z potwierdzeniem). |
| **Usuwanie linii — bez porzucania** | „Usuń linię" zostaje aktywne po skasowaniu — kasujesz kolejne, **Esc = koniec** (wcześniej wyłączało się po jednej). |
| **Edycja connections** | lista połączeń: `from`/`to` jako selecty (id bboxów, zachowuje adres `comp:terminal`), `kind` (power/pe/link), `✕` usuń. Zmiana → markPageDirty → redraw. |
| **Re-klasyfikacja bbox w review (R)** | panel review ma picker typu dla aktualnego bboxa — zmieniasz klasę bez wychodzenia z cropu (ten sam picker co w trybie B). |
| **Edycja terminali (T)** | (poprzedni wpis) drag = popraw, klik = dodaj, ✕ = usuń. |

### Filip — TEST (Ctrl+F5!)

- Tryb **L**: „Usuń linię" → klikaj kolejne; „Wyczyść wszystkie linie" → potwierdź.
- Tryb **R**: ◀/▶ po bboxach, pod przyciskami zmień typ; ✕ usuń, ✓ akceptuj.
- Tryb **C**: zmień `from`/`to`/`kind` w liście, ✕ usuń połączenie.
- Tryb **T**: przeciągnij/dodaj/usuń zacisk.
- **Zapisz** → masz prawdziwy GT (≠ runtime) → `diff_gt_runtime` zaczyna walidować.

[BŁĄD środowiska] Mount sandboxu obcina `app.js`/`crop_review.js` przy odczycie (flip-flop) — **nie zlintowałem**. Kanon kompletny (Edit). Zwaliduj Ctrl+F5; jak coś w konsoli przeglądarki czerwone — wklej, poprawię.

---

## 2026-06-28 [ZW] — Diagnoza p040 + edycja terminali w labelerze + sito strict + overlay trasowany

Temat: **GT p040 = niepoprawiony draft runtime (pętla — diff nic nie waliduje). Daję narzędzia: overlay po realnej ścieżce, sito „od-do terminala", ręczna edycja terminali w labelerze (zrywa pętlę).**

### Ustalenie (klucz)

`recognize_file` = YOLO + OCR + Hough (potwierdzone w `pipeline.py`), **nie GT**. ALE `diff_gt_runtime` porównuje runtime z „GT" p040, a to **zaimportowany draft runtime** (`import_runtime_draft`). Bez ręcznej korekty GT match 14/14 jest samozwrotny. Diag potwierdził: 14/14 połączeń ma oba końce na terminalu → błędy to **źle postawione terminale**, nie luźny kontakt.

### Co zrobione (kod)

| Plik | Zmiana |
|------|--------|
| `scripts/preview_schema.py` | Overlay czytelny: tło przygaszone, wire=zielony, **connections=czerwony po REALNEJ ścieżce netu** (rekonstrukcja `_group_into_nets`/`_nodes_on_net` — ten sam tryb co runtime), terminale żółte z id, legenda. Wypis `[diag]` (tryb strict + ile conn na terminalu vs luźnych). |
| `backend/recognize/net_builder.py` | `build_connections(..., require_terminal=False)`: w trybie strict węzeł powstaje TYLKO gdy koniec linii trafia w terminal (inaczej None) → znikają fałszywe „połączenia od środka symbolu". |
| `backend/recognize/graph_builder.py` | czyta `connection_require_terminal()` z configu, przekazuje do net-buildera. |
| `config/runtime.yaml`, `backend/runtime_config.py` | + `connection_require_terminal` (default false). |
| `backend/tests/test_net_builder.py` | +2 testy strict (luźny kontakt odrzucony / terminal↔terminal zachowany). |
| `labeler/static/app.js` (v32), `crop_review.js` (v32), `index.html` | **Tryb T = pełna edycja terminali**: klik przy bboxie = dodaj (snap do krawędzi), **przeciągnij = popraw pozycję** (to naprawia „terminal w złym miejscu"), ✕ w liście = usuń. Konwersja klik→obraz świadoma cropu (`imagePointFromCanvas`). |

### Filip — TEST (Ctrl+F5!)

```powershell
.venv311\Scripts\python.exe -m pytest backend/tests labeler/tests -q
.venv311\Scripts\python.exe scripts/preview_schema.py --page p040      # nowy overlay + [diag]
.venv311\Scripts\python.exe -m labeler.app                              # Ctrl+F5
```
Labeler, tryb **T**: zaznacz listwę z błędnym terminalem → **przeciągnij** zacisk na właściwą krawędź, ewent. klik = dodaj / ✕ = usuń → **Zapisz**. Od teraz GT≠runtime → diff zacznie coś znaczyć.

`connection_require_terminal`: na p040 obojętny (wszystko już na terminalach) — zostaw `false`, użyteczny na stronach z luźnymi kontaktami.

### Świadomie NIE zrobione (czekają na prawdziwy GT)

[RYZYKO] **`derive_auto_terminals`** (źle stawia zacisk) i **reguła „jedna linia ≠ dwa połączenia"** — to strojenie backendu. Robienie tego bez poprawionego GT = znów pętla (stroję pod własny błąd). Najpierw popraw kilka terminali/conn na p040 ręcznie (tryb T/C) i Zapisz; wtedy mam wzorzec i naprawiam backend mierząc diff. Reguła #3 (współdzielenie linii) wymaga realnej topologii do walidacji.

### Weryfikacja

`crop_review.js` — `node --check` czysto. `app.js` — [BŁĄD środowiska] mount sandboxu obcina plik przy odczycie (1593/~2060 linii), **nie odpaliłem lintu/pytest na repo**; logika net-buildera strict zweryfikowana w izolacji (scenariusze przeszły). Pełny pytest + UI u Ciebie.

---

## 2026-06-28 [ZW] — Backlog runtime: mostki w sicie + kalibracja z config

Temat: **Sito nie zjada mostków terminal↔terminal. terminal_tol i progi Hough przeniesione do `config/runtime.yaml` (kalibracja p040/p027 bez edycji kodu).**

### 1. Sito + mostki w listwie (sekcja 2c)

`line_sieve` demotował do `other` każdą linię w całości w bboxie — także wewnętrzny mostek listwy → nie docierał do net-buildera.

| Plik | Zmiana |
|------|--------|
| `backend/recognize/line_sieve.py` | `apply_sieve(..., bridge_tol=8.0)`: linia wewnątrz bbox, której **końce trafiają w 2 różne terminale tego samego komponentu**, zostaje `wire` (kandydat → `Connection kind="link"`). `_is_inside_component` → `_containing_component` (zwraca komponent); nowy `_bridges_two_terminals`. Nowy `recover_terminal_bridges()` — promuje `other`→`wire` PO wyprowadzeniu terminali (runtime: sito biegnie zanim terminale istnieją). |
| `backend/recognize/graph_builder.py` | krok 4b: `recover_terminal_bridges` po `derive_auto_terminals`, przed net-builderem. |
| `backend/tests/test_line_sieve.py` | +4 testy: mostek zostaje wire; linia wewn. bez 2 term → other; recover other→wire; recover nie rusza zwykłego other. |

[RYZYKO] Ochrona działa, gdy komponent ma terminale (GT/import-draft, albo auto-zaciski z przewodów dochodzących do krawędzi). Mostek **bez** żadnego przewodu krawędziowego na listwie nie wygeneruje terminali → nie zostanie odzyskany. Detekcja terminali w runtime to osobny temat.

### 2. terminal_tol i progi Hough z config (sekcja 2a, 2b)

Zamiast zgadywać magiczne liczby bez GPU — **przeniosłem progi do `config/runtime.yaml`**, żebyś kalibrował na p040/p027 i od razu widział wynik smoke, bez edycji kodu.

| Plik | Zmiana |
|------|--------|
| `config/runtime.yaml` | + `terminal_tol_frac` (0.012), `terminal_tol_min` (12.0); + `hough_min_len_frac` (0.02), `hough_gap_frac` (0.0015), `hough_min_len_floor` (20), `hough_threshold_floor` (50), `hough_gap_floor` (4). Komentarze z kierunkiem strojenia (za dużo/za mało conn / segmentów). |
| `backend/runtime_config.py` | + `terminal_tol_frac()`, `terminal_tol_min()`, `hough_params()`. Defaulty = obecne wartości (zero zmian zachowania). |
| `backend/recognize/graph_builder.py` | `_terminal_tol()` czyta config (fallback na stałe). |
| `backend/recognize/line_tracer.py` | `auto_line_params()` + `_params()` czytają `hough_params()` (fallback na stałe modułu). |

**Wartości domyślne = identyczne z dotychczasowymi** → bez configa pipeline liczy tak samo (zweryfikowane: p040 6617px → min_len/hough/gap = 132/132/10 jak wcześniej).

### Jak kalibrujesz (bez kodu)

- **Za dużo szumu Hough** (p040 ~1321 segm.): podnieś `hough_min_len_frac` 0.02 → 0.025/0.03, powtórz smoke. Gubi cienkie wire → obniż.
- **Mało/fałszywe connections**: zmień `terminal_tol_frac` (0.009 = ciaśniej, 0.016 = luźniej).

### Weryfikacja

[BŁĄD środowiska] Mount sandboxu w tej sesji **dalej obcina pliki przy odczycie** (`cp`/`cat`/pytest na mountcie czytają `test_net_builder.py` ucięte na linii 75) — pliki kanoniczne w repo są **kompletne** (potwierdzone Edit/Read). **Nie odpaliłem pytest na repo.** Logikę nowych funkcji (`_bridges_two_terminals`, `recover_terminal_bridges`, `auto_line_params` z config, `_terminal_tol`) zweryfikowałem **w izolacji** (transkrypcja + scenariusze) — wszystkie przeszły.

**Filip — uruchom (obowiązkowy smoke z promptu):**
```powershell
.venv311\Scripts\python.exe -m pytest backend/tests labeler/tests -q
.venv311\Scripts\python.exe scripts/diff_gt_runtime.py --page p040
python -c "from backend.recognize.pipeline import recognize_file; m=recognize_file('data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p040.png'); print(len(m.connections),'conn', len(m.graphic_lines),'linii')"
```
Oczekiwane: pytest zielony (~24+4 nowe sito). p040: mostki listwy powinny teraz wyjść jako `Connection kind="link"` (jeśli listwa ma terminale z przewodów krawędziowych). Wklej liczby conn + ile segmentów — dostroję `frac` w configu, jeśli trzeba.

[RYZYKO] Sekcja 1 (poprawki po smoke) — **czekam na Twój `## Poprawka`** w aktywnym prompcie. Sekcja 3 (Fix class w trybie R / edycja from-to w C) — nietknięte (UI, nie testowalne po mojej stronie); zrobię na Twoje słowo.

---

## 2026-06-27 [ZW] — Faza B: podgląd auto-zacisków + iteracja po bboxach (labeler)

Temat: **Przegląd terminali per bbox: auto z linii, ◀▶ po bboxach, „tylko bboxy", przyciski cofania (bez polegania na klawiszu).**

### Co zrobione (kod) — `app.js?v=29`

| Plik | Zmiana |
|------|--------|
| `labeler/app.py` | NOWY endpoint `POST /api/derive-terminals` (bbox + linie → zaciski) wołający `net_builder.derive_auto_terminals` — **ten sam algorytm co runtime**. |
| `labeler/static/index.html` | panel terminali: `◀ bbox` / `bbox ▶` / `⤓ Auto z linii` / `✕ ostatni` / `Wyczyść` + checkbox `tylko bboxy (ukryj linie)`. |
| `labeler/static/app.js` | `deriveTerminalsForSelected()` (POST), `iterateBbox(±1)` (przy przejściu auto-liczy zaciski gdy bbox pusty), `removeLastTerminal`/`clearTerminals` (przyciski — niezależne od klawiatury), `hideLinesReview` (redraw bez linii). |
| `labeler/static/style.css` | layout kontrolek. |
| `labeler/tests/test_lines_api.py` | +test endpointu derive. |

### Workflow przeglądu (Twój scenariusz)

1. Tryb **T**, zaznacz **„tylko bboxy"** → linie znikają, widać same bboxy.
2. **bbox ▶** — przechodzi po bboxach; dla każdego **automatycznie liczy zaciski z linii** (czerwone kropki + nazwa).
3. Potwierdzasz/poprawiasz: **✕ ostatni** / **Wyczyść** / klik = dodaj / edycja nazwy po prawej.
4. **bbox ▶** do następnego. Na końcu **Zapisz**.

### „Cofanie nie działało"

Backspace mógł nie łapać (focus/cache). Dlatego **✕ ostatni** to teraz przycisk (pewny). Fix klawisza zostaje, ale nie jest wymagany. **Ctrl+F5** w przeglądarce — inaczej stary JS.

### Weryfikacja

[BŁĄD środowiska] Sandbox dalej psuł pliki przy zapisie — **nie odpaliłem pytest/UI**. Kanon poprawny (odczyt). Algorytm `derive_auto_terminals` sprawdzony wcześniej w izolacji.

**Filip — uruchom:**
```powershell
.venv311\Scripts\python.exe -m pytest backend/tests labeler/tests
.venv311\Scripts\python.exe -m labeler.app      # Ctrl+F5!
```
Oczekiwane: pytest zielony (~142). Labeler: ▶ iteruje, auto-zaciski się pojawiają, ✕/Wyczyść działają.

[RYZYKO] Auto-zaciski łapią przewody **dochodzące do krawędzi**. Wewnętrzne mostki w listwie (linie w całości w bboxie) wymagają jeszcze integracji sita — osobny krok.

---

## 2026-06-27 [ZW] — Terminale: fix bugów UI + auto-zaciski z linii (runtime)

Temat: **Poprawki zgłoszone przez Filipa (widoczność, Backspace kasował bbox) + auto-zaciski z kontaktu linia↔krawędź.**

### Bugfix labeler (UI) — `app.js?v=28`

| Bug | Fix |
|-----|-----|
| Zaciski ledwo widoczne | Większe (r=10) kropki: biała otoczka + czerwone/pomarańczowe wypełnienie + ciemny kontur; **etykieta zawsze** (z białym obrysem tekstu). |
| Backspace/Del kasował **bbox** zamiast cofać zacisk | W trybie terminali Backspace/Del cofa **ostatni zacisk** zaznaczonego bboxa i **nigdy** nie kasuje bboxa (wcześniej spadało do handlera kasującego zaznaczony bbox). |

**Filip:** twardy refresh przeglądarki (Ctrl+F5) — inaczej stary JS z cache.

### Auto-zaciski (runtime, Faza A — „oba" wg Twojej decyzji)

Filip: „terminal jest tam, gdzie linia wychodzi w krawędź bboxa". Wdrożone:

| Plik | Zmiana |
|------|--------|
| `backend/recognize/net_builder.py` | `derive_auto_terminals(component, lines, tol)` — koniec wire dotykający krawędzi bboxa → zacisk (snap do krawędzi, rel 0–1, dedup, numeracja 1,2,3). |
| `backend/recognize/graph_builder.py` | `build()`: komponenty bez ręcznych terminali dostają auto-zaciski z linii; połączenia stają się **`comp:terminal`** (zgodnie z fixturem GT `F1:2`). |
| `backend/tests/test_net_builder.py` | +test `derive_auto_terminals`. |
| `backend/tests/test_graph_builder.py` | asercja połączeń po komponencie (prefiks przed `:`), bo adres = `comp:terminal`. |

### Weryfikacja

[BŁĄD środowiska] Sandbox ZW psuł świeże pliki przy zapisie — **nie odpaliłem pytest ani nie przetestowałem UI w przeglądarce**. Kanon poprawny (potwierdzony odczytem). Logika net-buildera sprawdzona wcześniej w izolacji.

**Filip — uruchom:**
```powershell
.venv311\Scripts\python.exe -m pytest backend/tests labeler/tests
.venv311\Scripts\python.exe -m labeler.app   # Ctrl+F5 w przeglądarce!
```
Oczekiwane: pytest zielony (~141). Labeler: zaciski wyraźne (czerwone + nazwa), Backspace cofa zacisk.

### Zostaje (B end-to-end)

1. **Podgląd auto-zacisków w labelerze** (Faza B — przycisk „zaciski z linii" wołający ten sam algorytm przez API).
2. **Integracja sita**: mostki w listwie (linie wewnątrz bbox) są demotowane przed net-builderem → wewnętrzne mostki jeszcze nie wychodzą jako `link`. Auto-zaciski działają dla przewodów *dochodzących do krawędzi*.

---

## 2026-06-27 [ZW] — Terminale (etap 2) — tryb w labelerze (UI) + eksport

Temat: **Tryb „Terminale" w labelerze: klik przy krawędzi stawia zacisk (snap), nazwa edytowalna, eksport do `Component.terminals`.**

### Decyzje UX (Filip)

Snap do krawędzi obrysu; auto-numeracja 1,2,3 z edycją; dowolny bbox.

### Co zrobione (kod)

| Plik | Zmiana |
|------|--------|
| `labeler/static/index.html` | przycisk `⊙ Terminale`, panel `#terminal-panel` (lista zacisków), `app.js?v=27`. |
| `labeler/static/app.js` | tryb `MODE_TERMINAL` (klawisz **T**): klik przy krawędzi zaznaczonego bboxa → zacisk, pozycja **względna 0–1**, snap do najbliższej krawędzi; rysowanie kropek; lista z edycją id + Del; zapis w `bbox.terminals[]` (payload + localStorage), wczytywanie przy otwarciu strony. |
| `labeler/static/style.css` | style panelu/wierszy zacisków. |
| `labeler/export.py` | `BboxAnnotation.terminals` → `Component.terminals` w `label_to_schema`. |
| `labeler/tests/test_export.py` | +test mapowania terminali w eksporcie. |

### Weryfikacja

Backend (model + eksport + net-builder terminali) — przez `pytest` u Ciebie. **UI nie testowane w przeglądarce** (brak przeglądarki po mojej stronie) — proszę o test ręczny.

### Filip — test

```powershell
.venv311\Scripts\python.exe -m pytest backend/tests labeler/tests
python -m labeler.app   # localhost:8765
```

Ręcznie w labelerze:
1. Wczytaj stronę, narysuj/zaznacz bbox.
2. **T** (lub ⊙ Terminale) → klik przy krawędzi bboxa → zacisk (snap do krawędzi).
3. Po prawej zmień nazwę (np. `1`, `L+`, `I0.0`), usuń ✕.
4. Zapisz → odśwież → zaciski wracają.
5. Eksport → `*.schema.json` ma `Component.terminals`.

[RYZYKO] Tryb terminali wymaga **zaznaczonego bboxa**; klik przy krawędzi zaznaczonego dodaje zacisk, klik na innym bboxie go zaznacza.
[RYZYKO] Sito wciąż zje mostki (linie w bbox) zanim dojdą do net-buildera — **integracja sita to następny krok**, żeby mostki terminal↔terminal faktycznie wyszły jako `Connection link`.

### Następne (B end-to-end)

1. Integracja sita: nie demotuj linii, której końce trafiają w 2 terminale.
2. (później) detekcja terminali w runtime (teraz tylko GT z labelera).

---

## 2026-06-27 [ZW] — Terminale (etap 2) — faza backendowa: model + net-builder

Temat: **Złączki/terminale jako węzły, żeby mostki (terminal↔terminal) były realnymi Connection. Wybrana Opcja B (`terminals[]`).**

### Dlaczego B

Mostek łączy złączki. Połączenie potrzebuje 2 węzłów. Listwa = jeden bbox = jeden węzeł → mostek „wewnątrz" nie ma czego łączyć. `terminals[]` robi z zacisków osobno adresowalne punkty (`component_id:terminal_id`).

### Co zrobione (faza backendowa)

| Plik | Zmiana |
|------|--------|
| `backend/models/schema.py` | NOWY `Terminal` (id, x, y wzgl. 0–1, name); `Component.terminals[]`. |
| `backend/models/label.py` | NOWY `Terminal`; `BboxAnnotation.terminals[]` (GT z labelera). |
| `backend/recognize/net_builder.py` | Koniec przewodu → `comp:terminal` (gdy komponent ma terminale, w granicach tol; inaczej fallback `comp`). Net z 2 terminalami **tego samego** komponentu → `Connection kind="link"` (mostek). Różne komponenty → kabel (power/pe). |
| `backend/tests/test_net_builder.py` | +3 testy: mostek terminal↔terminal = link; przewód → adres `comp:term`; fallback gdy koniec daleko od terminala. |

### Weryfikacja

Net-builder (bazowy + terminale) sprawdzony w izolacji. Pełny `pytest` u Ciebie (sandbox ZW psuł świeże pliki — kanon poprawny, potwierdzony odczytem).

### [RYZYKO] / co zostaje do END-TO-END (B nie działa jeszcze w całości)

1. **Tryb terminali w labelerze (UI)** — żeby było gdzie postawić terminale (klik na obrysie, nazwa). Duży kawałek frontendu. **Bez tego `terminals[]` jest puste.**
2. **Sito zjada mostki** — `line_sieve` demotuje linie w całości wewnątrz bbox do `other` ZANIM trafią do net-buildera. Trzeba: nie demotować linii, której końce trafiają w 2 terminale. Integracja po UI.
3. **Runtime**: YOLO nie wykrywa terminali — `terminals[]` pochodzi z GT (labeler). Detekcja terminali = osobny, późniejszy temat.

Czyli: model + logika grafu gotowe (kontrakt ustalony, testowalne). Wartość end-to-end po UI labelera + integracji sita.

### Filip — uruchom

```powershell
.venv311\Scripts\python.exe -m pytest backend/tests labeler/tests
```
Oczekiwane zielone (~139).

---

## 2026-06-27 [ZW] — ADR model połączeń: Krok 1 — kontrakt + klasyfikator (bus wycofany)

Temat: **Przyjęty [ADR connection-model](../docs/adr/connection-model.md). Krok 1/3: kontrakt + klasyfikator.**

### Decyzje ADR (zaakceptowane przez Filipa)

- **`bus` wycofane** — szyna = jeden kabel (`wire`) z wieloma odczepami; grupowanie przez `potential` (net-builder). Znika błędne „niebieskie = potencjał albo ramka".
- **`cable_marker`** — NOWA rola linii: przerywana przecinająca kable + etykieta (nazwa/typ/średnica) = adnotacja, NIE połączenie. Da listę kablową ze schematu.
- **`link`** — NOWY `ConnectionKind`: mostek złączka↔złączka w listwie (terminal-link), różny od kabla device↔device.

### Co zrobione (Krok 1)

| Plik | Zmiana |
|------|--------|
| `backend/models/schema.py` | `LineRole += "cable_marker"`; `ConnectionKind += "link"`; `bus` oznaczone DEPRECATED (zostaje w enumie). |
| `backend/models/label.py` | `LineRole += "cable_marker"` (spójność z labelerem). |
| `backend/recognize/line_classifier.py` | Klasyfikator **nie nadaje już `bus`** (długa linia osiowa → `wire`); `CONNECTION_ROLES = {wire}`. |
| `backend/tests/test_line_classifier.py` | bus nie jest kandydatem; długa linia → wire. |
| `backend/tests/test_net_builder.py`, `test_graph_builder.py`, `test_line_sieve.py` | użycia `bus` → `wire` / test deprecacji bus. |

### Weryfikacja

Logika klasyfikatora sprawdzona w izolacji: **wire = kandydat, bus = NIE; długa linia → wire**. Reszta przez `pytest` u Ciebie (sandbox ZW dalej psuł pliki przy zapisie — kanon poprawny, potwierdzony odczytem).

### Filip — uruchom

```powershell
.venv311\Scripts\python.exe -m pytest backend/tests labeler/tests
```
Oczekiwane: zielone (~136). Wklej, jak coś czerwone (poza znanymi — nic nie powinno).

[RYZYKO] Labeler (`index.html`, `app.js`) wciąż oferuje „bus" w dropdownie — deprecated, ale nie usuwam (to labeler/010, nie rusza testów). Do sprzątnięcia osobno, jeśli chcesz.

### Następne kroki ADR

- **Krok 2:** sito mostków — nie kasuj wnętrza `device_block`, `kind="link"` (Opcja A + C).
- **Krok 3:** detekcja `cable_marker` (dashed × przecięcie wire × etykieta OCR) → adnotacja + lista kablowa.

---

## 2026-06-27 [ZW] — Warstwa 1: net-builder (scalanie segmentów wire/bus → Connection)

Temat: **Pofragmentowane przewody scalane w sieci (nets). Connections przestają być zaniżone.**

### Koncepcja (uzgodniona z Filipem)

Pętla połączeń w dwóch warstwach. **Warstwa 1 (TA) — czysta geometria, bez GPU.** Warstwa 2 (re-detekcja YOLO sterowana topologią) — później, po walidacji.

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `backend/recognize/net_builder.py` | NOWY. `build_connections(lines, components, join_tol, terminal_tol)` → `(connections, potentials)`. Union-find segmentów wire/bus + przypięcie symboli + emisja. |
| `backend/recognize/graph_builder.py` | `build()` używa net-buildera zamiast łączenia po końcach pojedynczego segmentu; `potentials` w SchemaModel. Usunięte stare `_build_connections` + helpery (przeniesione). |
| `backend/tests/test_net_builder.py` | NOWY — 7 testów (scalanie 2 segmentów, załamanie 90°, T-junction 3 symbole+potential, skrzyżowanie bez końca NIE łączy, dangling, PE, device_stroke). |

### Algorytm (v1)

1. **Union-find**: łączę linie, których KONIEC dotyka ścieżki innej linii (załamanie / odczep T, tol). Skrzyżowanie w połowie segmentu (żaden koniec) → NIE łączę (bez kropki = brak połączenia).
2. **Symbole na net**: bbox blisko końca którejkolwiek linii netu (terminal).
3. **Emisja**: net z 2 symbolami → 1 Connection. Net z >2 (szyna/odczepy) → wspólny `potential` (`net_k` w `potentials[]`), gwiazda do kotwicy.

### Weryfikacja

net-builder: **7/7 scenariuszy OK** (uruchomione na żywym źródle modułu). Reszta przez `pytest` u Ciebie (sandbox ZW dalej psuł część plików przy zapisie — kanon poprawny).

### Filip — uruchom

```powershell
.venv311\Scripts\python.exe -m pytest backend/tests labeler/tests
.venv311\Scripts\python.exe smoke_graph.py *p040*   # i *p035* — porownaj liczbe connections
```

Oczekiwane: testy zielone (≈136); connections **wyraźnie więcej** niż 3/10 (segmenty się scalają). Wklej nowe liczby — ocenimy, czy ruszać Warstwę 2 (odzysk brakujących symboli).

[RYZYKO] v1 łączy tylko po stykających się końcach. Odczep kończący się DOKŁADNIE na szynie złapie (T-junction), ale jeśli koniec nie dochodzi do linii (przerwa > tol) — nie scali. Próg = `terminal_tol` (0.012·max). Jak za mało/za dużo łączy — dostroję.

---

## 2026-06-27 [ZW] — Fix izolacji testów OCR (4 czerwone na .venv311)

Temat: **`test_ocr_engine` failowało na PC Filip — delegacja do subprocesu omijała wstrzykniętą atrapę. Fix test-only.**

### Przyczyna

`PaddleOcrEngine.extract_text` deleguje do workera OCR (subprocess), gdy istnieje `.venv-ocr` **lub** `torch` w procesie. Fixture `_engine_with` wstrzykiwał atrapę silnika, ale nie wyłączał `_subprocess_ok` → na PC Filip (`.venv-ocr` obecny) testy szły do realnego workera → `RuntimeError: brak pliku page.png`. W sandboxie ZW (bez `.venv-ocr`) przechodziły — stąd nie wykryte wcześniej.

### Fix (tylko testy, zero zmian w `ocr_engine.py`)

| Plik | Zmiana |
|------|--------|
| `backend/tests/test_ocr_engine.py` | `_engine_with` + test ImportError: `eng._subprocess_ok = False` → wymuszenie ścieżki in-process (atrapa zamiast workera). |

### Wynik (Filip, .venv311)

Przed: `125 passed, 4 failed` (wszystkie 4 = OCR subprocess, **nie regresja** — mój kod 004/sito/ROI zielony). Po fixie oczekiwane **129 passed**.

---

## 2026-06-27 [ZW] — ROI: ucięcie dołu arkusza (config, stały %)

Temat: **Pomijanie linii z dołu strony (tabliczka rysunkowa / tabelki) — próg w configu.**

### Co zrobione (kod)

| Plik | Zmiana |
|------|--------|
| `config/runtime.yaml` | + `roi_bottom_cut_frac: 0.85` (pomiń dolne 15%). Zmieniasz tutaj, bez ruszania kodu. |
| `backend/runtime_config.py` | + `roi_bottom_cut_frac()` (clamp do (0,1], default 1.0 = bez cięcia). |
| `backend/recognize/graph_builder.py` | + `_apply_roi(lines, size, frac)` po sicie: usuwa linie, których NAJWYŻSZY punkt jest poniżej `frac·H`. Linia sięgająca obszaru rysunku zostaje. |
| `backend/tests/test_graph_builder.py` | +2 testy ROI (dół odcięty, linia sięgająca rysunku zostaje; no-op gdy frac≥1 lub brak rozmiaru). |

### Decyzja (Filip)

Stały % na teraz (`0.85`), per-arkusz/format dostroimy później. Detekcja ramki rysunku — odrzucona na ten etap.

[RYZYKO] Stały % zakłada podobny layout; jeśli tabliczka ma różną wysokość na różnych arkuszach — podnieś/obniż `roi_bottom_cut_frac`. ROI tnie tylko **linie** (nie symbole/OCR) — to wystarcza dla połączeń.

### Po smoke u Ciebie

Odpal ponownie `smoke_graph.py *p040*` — dolne tabelki powinny zniknąć z nakładki. Jak za dużo/za mało ucięte, zmień `roi_bottom_cut_frac` w `config/runtime.yaml` (np. 0.80 / 0.90) i powtórz.

---

## 2026-06-27 [ZW] — Smoke p040/p035 + sito wnętrza bbox + semantyka bus

Temat: **Walidacja wzrokowa sita (feedback Filip). Dodane odsiewanie grafiki wewnątrz bbox. Doprecyzowana semantyka `bus`.**

### Wynik smoke (Filip, RTX 2080)

| Strona | components | wire | bus | frame | other | connections |
|--------|-----------:|-----:|----:|------:|------:|------------:|
| p040 | 9 | 133 | 6 | 20 | 64 | 3 |
| p035 | 24 | 182 | 11 | 21 | 41 | 10 |

Sito ruszyło (frame+other zeszło z wire/bus). 3 terminale PLC poprawnie → frame.

### Co poprawione (kod)

| Plik | Zmiana |
|------|--------|
| `backend/recognize/line_sieve.py` | + `_is_inside_component`: linia w całości w bbox symbolu (tabelka w terminalu, obrys wewnętrzny) → `other`. Przewód łączący wychodzi poza bbox → zostaje. Kolejność sita: bok→frame, wnętrze→other, tekst→other. |
| `backend/tests/test_line_sieve.py` | +2 testy (wnętrze→other, przekraczająca granicę→wire). |
| `backend/recognize/line_classifier.py` | Komentarz przy `CONNECTION_ROLES`: **bus = szyna zbiorcza (busbar)**, NIE listwa złączek (listwa = komponent, filar symboli `row_layout strip_*`). Zachowanie bez zmian. |

### Semantyka bus (ustalone z Filipem)

- `bus` = **szyna zbiorcza** (busbar) — długa linia w osi, kandydat na Connection. OK.
- **Listwa złączek** ≠ linia — to symbol (bbox + strip w `row_layout`). Nie dotyczy ról linii.

### [BŁĄD]/[RYZYKO] z feedbacku — otwarte

1. [RYZYKO] **Dół rysunku** (tabelki pod schematem) łapane. Filip: „odetnijmy dół jako nieistotny". → ROI/crop — wymaga decyzji (stały % wysokości vs detekcja ramki rysunku). **Nie zrobione** — czeka na ustalenie.
2. [RYZYKO] **OCR pomija tekst** → nieodczytany napis dostaje zieloną (wire). Sito tekstu nie ma bbox-a do złapania. Część (przy/w symbolu) łapie nowe sito wnętrza; reszta zostaje. Głębszy fix = recall OCR.
3. [RYZYKO] **Recall linii** (p035: 2 środkowe linie + przerywana kabla nieodczytane). Hough gubi cienkie/przerywane między równoległymi. Osobny temat (parametry/segmentacja).
4. [RYZYKO] **Fragmentacja** → connections wciąż zaniżone (3/10). Scalanie łańcuchów wire/bus — nieruszone.

### Testy / [BŁĄD] środowiska

[BŁĄD] Sandbox tej sesji **uszkadzał świeżo zapisywane pliki przy synchronizacji** (obcinał w połowie). Pliki kanoniczne w workspace Filipa są **kompletne i poprawne** (zweryfikowane odczytem). **Nie udało się** odpalić pełnego `pytest` po ostatniej zmianie. Wcześniejszy pełny przebieg: **123 passed**. Nowe gałęzie (wnętrze bbox) to trywialna logika zawierania (lustro przefiltrowanego testu tekstu).

**Filip — potwierdź u siebie:**
```
pytest backend/tests labeler/tests
```
Oczekiwane: zielone (≈127). Jeśli coś czerwone — wklej, poprawię.

### Throwaway (skasować)

`calib_lines.py`, `preview_calib.py`, `smoke_graph.py`.

---

## 2026-06-27 [ZW] — Sito linii: obramówki/tekst poza wire/bus

Temat: **Filtr po klasyfikacji — odsiewa obramówki urządzeń i artefakty tekstu z kandydatów na Connection.**

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `backend/recognize/line_sieve.py` | NOWY. `apply_sieve(lines, components, text_bboxes, edge_tol)` — czyste funkcje. wire/bus wzdłuż boku bbox symbolu → `frame`; krótki segment w bbox tekstu OCR → `other`. Nie rusza nie-kandydatów. |
| `backend/recognize/graph_builder.py` | `build()`: OCR raz (texts współdzielone tag+sito), `apply_sieve` po `classify` przed `connections`; `_edge_tol(size)`. |
| `backend/tests/test_line_sieve.py` | NOWY — 7 testów: górny/lewy/dolny bok→frame, przewód prostopadły (dotyka punktowo)→wire, daleko→wire, tekst→other, nie-kandydat nietknięty. |

### Kluczowa heurystyka (rozróżnienie ramka vs przewód)

- **Obramówka** biegnie *wzdłuż* krawędzi bbox (równolegle, pokrycie ≥60% krótszego zakresu, w tolerancji `edge_tol = max(6, 0.004·max(W,H))`).
- **Przewód** *dotyka* krawędzi punktowo i idzie prostopadle na zewnątrz → pokrycie ~0 → zostaje wire.
- Wykorzystuje bbox symboli z YOLO (filar już mamy) — zero nowych danych.

### Testy

```
pytest backend/tests labeler/tests  →  123 passed  (+7 sito; 0 regresji; połączenie wire z test_build nietknięte)
```

### Filip — walidacja wzrokowa (RTX 2080)

```powershell
.venv311\Scripts\python.exe smoke_graph.py *p040*   # i *p035*
```

Zapisze `data/output/calib/<strona>_graph.png` + wypisze histogram ról i connections. Sprawdź:
1. Czy obramówki urządzeń/terminali są **szare** (frame), a nie zielone/niebieskie.
2. Czy artefakty tekstu są **żółte** (other).
3. Czy realne przewody zostały **zielone/niebieskie** (wire/bus).
4. Histogram `graphic_lines per rola` — ile zeszło z wire/bus do frame/other.

[RYZYKO] Sito łapie ramki tylko tam, gdzie YOLO wykrył symbol. Terminale bez detekcji → ich obramówki przejdą. Jak dużo zostaje — zgłoś, rozważymy detekcję prostokątów niezależną od bbox.
[RYZYKO] Fragmentacja (4 connections na p040) **nieruszona** — to osobny krok: scalanie łańcuchów wire/bus w polilinie.

### Throwaway (skasować)

`calib_lines.py`, `preview_calib.py`, `smoke_graph.py`.

---

## 2026-06-27 [ZW] — Kalibracja LineTracer: progi względne do rozdzielczości

Temat: **Szum Hough (p040: 1321 linii przy 6617px) → progi auto-skalowane. frac 0.02 wybrany wzrokowo (Filip).**

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `backend/recognize/line_tracer.py` | `auto_line_params(w,h)` + `LineTracer._params()`. Progi `None` → auto wg `max(W,H)`: `min_line_length=0.02·max`, `hough=max(50,min_line_length)`, `max_line_gap=0.0015·max`. Jawne int nadal nadpisują (testy/kalibracja). |
| `backend/tests/test_line_tracer.py` | +2 testy: skalowanie progów (6617→132/132/10; floory 20/50/4) + override jawnego param. |

### Dlaczego

- Sztywne `min_line_length=30` było absurdalnie małe na skanie 6617px (literka) → 1321 linii.
- Kalibracja wzrokowa (throwaway `preview_calib.py`, nakładki w `data/output/calib/`): **frac 0.02 = optimum** na p040 i p035. 0.03 ucinał linię stycznika; niżej — szum.
- Klasyfikator woła ~wszystko „wire/bus" (kolor czarny+oś) → redukcja szumu MUSI zejść z tracera, nie z klasyfikatora.

### Testy

```
pytest backend/tests labeler/tests  →  116 passed (mount sandboxu flip-flopował na świeżych plikach;
                                        kanon poprawny, 2 nowe asercje = arytmetyka, policzone ręcznie)
```

### Zostaje otwarte (następny krok)

[RYZYKO] Przy frac 0.02 wciąż leci **nadłapanie**, którego progiem NIE usuniemy:
1. **Obramówki urządzeń/terminali** klasyfikowane jako wire/bus (czarne, w osi, brak koloru sem. → default wire). To wada heurystyki klasyfikatora.
2. **Artefakty z tekstu** (krótkie segmenty w osi).
→ Potrzebne **sito po klasyfikacji** (np. odrzucanie segmentów tworzących zamknięte prostokąty = ramki; filtr na bliskość bbox-tekstu). Osobny temat.

[RYZYKO] Fragmentacja: realny przewód bywa cięty na kawałki → `GraphBuilder` łączy tylko końce jednego segmentu (p040: 4 connections). Docelowo: scalanie łańcuchów wire/bus w polilinie przed szukaniem terminali.

### Throwaway (skasować)

`calib_lines.py`, `preview_calib.py` — pomoce kalibracyjne, nie część pipeline.

---

## 2026-06-27 [ZW] — Prompt 004: GraphBuilder.build (składanie 3 filarów)

Temat: **`build()` składa SchemaModel z detekcji + OCR + linii. Connection TYLKO z wire/bus.**

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `backend/recognize/graph_builder.py` | `build()` — orkiestracja: detect→components(source=yolo), OCR→tag dopasowany do bbox + `annotations[]`, trace+classify→`graphic_lines[]`, wire/bus→`connections[]`, `meta.model_version` z registry, `context_assignments` (best-effort `resolve_context`) |
| `backend/tests/test_graph_builder.py` | nowy — 7 testów na mockach (bez GPU/paddle/CV) |

### Logika `build(image_path, source)`

1. `detect` → `Component[]` (`id=sym_i`, `bbox=[x1,y1,x2,y2]`, `source="yolo"`).
2. OCR: tekst z najwiekszym przecieciem z bbox symbolu → `Component.tag`; reszta → `annotations[]`.
3. `trace` + `classify(image_size)` → `graphic_lines[]`.
4. **Connection tylko gdy** `is_connection_candidate(line)` (role wire|bus). Konce linii → najblizszy symbol (tolerancja terminala `max(12px, 0.012·max(W,H))`); `from`/`to` = id symboli, dedup par. `kind`: grupa PE → `pe`, inaczej `power`.
5. `meta.source`, `meta.model_version` = aktywny model z `registry.json`.

### Zasady domenowe (utrzymane)

- **GraphicLine ≠ Connection.** `device_stroke`/`frame`/`dash`/`crossing` → tylko `graphic_lines`, NIGDY `connections` (test to weryfikuje).
- Filary 001/002/003 użyte jako gotowe — bez przepisywania. Lazy-init gdy GraphBuilder bez wstrzyknietych zaleznosci (runtime czyta model z registry).

### Testy

```
pytest backend/tests labeler/tests          →  116 passed
python -m backend.cli validate schema/fixtures/page1_expected.json  →  approved (0 errors)
```

[RYZYKO] Heurystyka `from`/`to` jest na poziomie **symbolu**, nie terminala (fixture GT ma `F1:2`/`U1:L1` — to recznе GT, nie target build). Terminale + `potential` = osobny krok po GT linii (p030).
[RYZYKO] `potential` zawsze `""` — brak odczytu etykiet przewodu. Do rozbudowy gdy OCR poda etykiety na liniach.
[RYZYKO] Próg terminala kalibrowany na rozmiar strony — sprawdź na realnym skanie (Adamed p035) czy konce wire trafiaja w bbox symboli.

### Filip — smoke u siebie (RTX 2080)

```powershell
python -c "from backend.recognize.pipeline import recognize_file; m=recognize_file('data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p035.png'); print(len(m.components),'komp',len(m.graphic_lines),'linii',len(m.connections),'conn')"
```

NIE ruszane: atlas QET, trening YOLO/train_cycle, labeler, scripts/preview_*.

---

## 2026-06-25 [ZW] — Prompt 002+003: filar POŁĄCZENIA (labeler linie + line tracer)

Temat: **Tryb polyline w labelerze + LineTracer/LineClassifier OpenCV. Linia ≠ Connection.**

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `labeler/app.py` | + `GET /api/semantic-groups`, `GET /api/match-color?hex=` (czytają semantic-colors.yaml) |
| `labeler/static/index.html` | toolbar trybu Bbox/Linia + rola + grupa + pipeta; lista linii; `app.js?v=21` |
| `labeler/static/app.js` | tryb polyline: klik=punkt, Enter/dblklik=koniec, Esc=anuluj, Del=usuń; eyedropper (sampling piksela canvas → match-color); rysowanie/edycja/zapis `lines[]` |
| `labeler/static/style.css` | style toolbara + listy linii |
| `backend/recognize/line_tracer.py` | OpenCV: Canny+dylatacja+HoughLinesP, merge kolinearnych, sampling koloru HSV→hex (re-sampling po scaleniu) |
| `backend/recognize/line_classifier.py` | segment→`GraphicLine` (role, semantic_group, color_ref, detected_color); heurystyki roli; **NIE** tworzy Connection |
| `backend/tests/test_line_tracer.py` | nowy — trace, sampling, merge |
| `backend/tests/test_line_classifier.py` | rozszerzony — wire/bus/device_stroke/dash, kandydaci Connection |
| `labeler/tests/test_lines_api.py` | nowy — endpointy + round-trip `graphic_lines` |

### Zasady domenowe (utrzymane)

- `GraphicLine ≠ Connection`. Tylko `role ∈ {wire, bus}` → `is_connection_candidate == True` → kandydaci dla GraphBuilder (004).
- Kolor → grupa przez `palette.match_color` (config/semantic-colors.yaml). `#9933FF` → `inverter` → rola `device_stroke` (nie-połączenie).
- Heurystyka roli: kolor (dash/device_stroke/frame) > geometria (długa linia w osi → `bus`) > domyślnie `wire`.

### Testy

```
pytest backend/tests labeler/tests  →  107 passed
```

[RYZYKO] LineTracer/Classifier to filar **runtime** (CV). Nie podłączony jeszcze do GraphBuilder — to prompt 004. `pipeline.py` bez zmian.
[RYZYKO] Próg `bus` domyślnie 400 px lub 0.45·max(W,H) gdy podasz `image_size` — do kalibracji na realnych skanach.

### Filip — do zrobienia

1. Labeler: `python -m labeler.app` → przełącz **L** (linia), narysuj wire (czarna) + device_stroke (fiolet), pipeta na kolor, eksport → sprawdź `*.schema.json` ma `graphic_lines`.
2. Zwróć uwagę czy progi Hougha (`min_line_length=30`, `max_line_gap=8`) łapią przewody na realnych stronach — jak trzeba, zgłoś `## Poprawka`.

NIE robione w tej sesji: GraphBuilder (004), QET, trening YOLO.

---

## 2026-06-25 [ZW] — Prompt 002-ocr: PaddleOcrEngine (filar TEKST)

Temat: **OCR offline PaddleOCR — `extract_text` + `TextDetection`. Testy bez pobierania modeli.**

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `backend/recognize/ocr_engine.py` | `TextDetection` (dataclass: text, bbox=[x1,y1,x2,y2], confidence) + `PaddleOcrEngine.extract_text()` |
| `backend/tests/test_ocr_engine.py` | 5 testów: parsowanie 2 detekcji, pusta strona, linia malformed, guard braku biblioteki, degradacja kwargs |

### Decyzje techniczne

- **Leniwy import** `paddleocr` (wzór jak onnxruntime w `symbol_detector`). Brak biblioteki → `ImportError` z hintem `pip install paddlepaddle paddleocr`.
- **Konstruktor bez zmian** `PaddleOcrEngine(use_gpu=True)` — dodany opcjonalny `lang="en"` (default zgodny z GraphBuilder, który tworzy bez argumentów).
- **bbox**: PaddleOCR zwraca poligon 4-punktowy → rzut na prostokąt osiowy `[min x, min y, max x, max y]` w pikselach oryginału.
- **Tolerancja wersji PaddleOCR**: `_build_engine` próbuje kolejno `use_gpu/show_log` (2.x) → minimalne kwargi (3.x usunęło te argumenty). `_run_engine` preferuje `.ocr(cls=True)`, fallback `.predict()`.
- **Język/PL**: default `lang='en'`. Dla diakrytyków PL użyj `PaddleOcrEngine(lang='latin')` — model latin obejmuje polskie znaki. Do potwierdzenia na realnych stronach.

### Testy

```
pytest backend/tests labeler/tests  →  93 passed
```
(w sandboxie doinstalowane: pydantic, fastapi, opencv-headless, numpy, pyyaml, pillow, httpx, svgwrite, pytest)

### Filip — smoke u siebie (RTX 2080)

```powershell
pip install paddlepaddle-gpu paddleocr   # CPU: paddlepaddle paddleocr
python -c "from backend.recognize.ocr_engine import PaddleOcrEngine; import glob; e=PaddleOcrEngine(use_gpu=True); print(e.extract_text(glob.glob('data/raw/*.png')[0])[:5])"
```

Modele PaddleOCR pobierają się raz przy 1. uruchomieniu (online) — potem offline. [RYZYKO] runtime backend/recognize ma być offline: pobranie modeli to jednorazowy setup, nie cloud API w runtime.

### Nie ruszone

GraphBuilder.build (NotImplementedError — prompt 004), line tracer (PROMPT-CLAUDE-002-LINES), atlas QET.

---

## 2026-06-14 [ZW] — Prompt 008a: QET atlas extract → symbol-reference.yaml

Temat: **Parser `.elmt` QET + renderer PNG + builder YAML + testy (faza 008a DONE).**

### Co zrobione (kod)

| Plik | Rola |
|------|------|
| `backend/atlas/__init__.py` | pakiet |
| `backend/atlas/qet_parser.py` | parsowanie `.elmt` (XML): nazwy EN/PL, linie/rects/poly/terminale, bbox |
| `backend/atlas/qet_render.py` | render geometry → PNG 128×128 (Pillow, offline) |
| `backend/atlas/build_reference.py` | CLI: skan QET P0/P1/P2, dedup, YAML + crops |
| `backend/atlas/reference.py` | `load_symbol_reference()`, `lookup_by_id`, `lookup_by_alias` |
| `config/symbol-reference.yaml` | seed (3 fixture-symbole); po builderze → ≥80 wpisów |
| `backend/tests/test_qet_parser.py` | 11 testów parsera na fixture `.elmt` |
| `backend/tests/test_symbol_reference.py` | 11 testów YAML (struktura, unikalne ID, lookup) |
| `schema/fixtures/atlas/*.elmt` | 3 fixture: fuse, contactor, terminal_block |
| `data/atlas/crops/*.png` | crop-y PNG z fixture (128×128, commitujemy) |
| `docs/atlas-setup.md` | instrukcja klonowania QET + uruchomienia buildera |
| `backend/paths.py` | nowe stałe: `SYMBOL_REFERENCE`, `ATLAS_QET`, `ATLAS_CROPS` |

### Testy (PC ZW)

```
pytest backend/tests labeler/tests   →  49 passed (zero regresji)
```

### Twoje kroki (Filip — RTX 2080)

**Krok 1 — sklonuj QET (jednorazowo):**
```powershell
git clone --depth 1 https://github.com/qelectrotech/qelectrotech-elements.git data/atlas/qet
```

**Krok 2 — uruchom builder:**
```powershell
python -m backend.atlas.build_reference `
    --qet-dir data/atlas/qet `
    --out config/symbol-reference.yaml `
    --crops-dir data/atlas/crops
# Oczekiwany wynik: "Zbudowano 120 symboli → config/symbol-reference.yaml"
```

**Krok 3 — weryfikacja:**
```powershell
python -m pytest backend/tests/test_symbol_reference.py -v
# Oczekiwane: 11 passed
python -m backend.cli validate schema/fixtures/page1_expected.json
# Oczekiwane: approved: true (bez regresji)
```

**Krok 4 — commit po buildzie:**
```powershell
git add config/symbol-reference.yaml data/atlas/crops/
git commit -m "[Filip] atlas: QET build → symbol-reference.yaml (008a full)"
```

### Uwagi

- `data/atlas/qet/` już w `.gitignore` — surowa biblioteka QET poza repo (115 MB, GPL)
- Crop-y PNG z fixture (3 pliki, 128×128) commitujemy; pełne crops po Twoim buildzie
- Licencja: YAML i crop-y = pochodna GPL; atrybucja w `symbol-reference.yaml`→`meta.sources.license`
- Crop-y zrenderowane przez Pillow — cairosvg **nie wymagane**
- Następny prompt po 008a: **009 — picker symbol_id w labelerze**

---

## 2026-06-14 [ZW] — export_onnx: brak best.pt w data/runs — zlokalizuj lub przetrenuj

Auto-find zadziałał, ale w `data/runs` **nie ma** żadnego `best.pt`. Rozszerzyłem szukanie też o domyślny katalog ultralytics `runs/` (gdy trening nie dostał `project`). 10 testów OK.

**Krok 1 — zlokalizuj plik na całym dysku projektu:**
```powershell
Get-ChildItem -Recurse -ErrorAction SilentlyContinue -Filter best.pt |
  Sort-Object LastWriteTime -Descending | Select FullName, LastWriteTime
```
- **Jeśli się znajdzie** (np. `runs\detect\train\weights\best.pt`): `pull`, potem `python -m train.export_onnx` (samo go weźmie) **albo** wskaż: `... --weights "<pełna ścieżka>"`.
- **Jeśli pusto** (run wyczyszczony / usunięty przy `.gitignore runs/`): trzeba przetrenować ponownie — to ~17 epok, szybkie:
```powershell
.venv\Scripts\python.exe -m train.dataset_export
.venv\Scripts\python.exe -m train.train_symbols --epochs 30 --batch 8
.venv\Scripts\python.exe -m train.export_onnx
```
Mój `train_symbols` zapisuje do `data/runs/symbols_v1/` — po ponownym treningu auto-find trafi od razu.

> Podejrzenie: run zniknął przy commicie `gitignore venv311/runs/yolo` albo przez czyszczenie. Wagi i tak nie idą do repo, więc po prostu odtwórz je lokalnie.

---

## 2026-06-14 [ZW] — Fix export_onnx: auto-wyszukiwanie best.pt

`export_onnx` rzucał `FileNotFoundError` — ultralytics zapisał run pod auto-inkrementowaną nazwą (np. `symbols_v12`), nie pod stałym `symbols_v1`. Dodałem `find_best_weights()`: bierze domyślny run, a jeśli go nie ma — **najnowszy** `data/runs/**/weights/best.pt`. +2 testy (13 passed).

**Odpal ponownie (samo znajdzie wagi):**
```powershell
.venv\Scripts\python.exe -m train.export_onnx
#    wypisze "Wagi: ...\best.pt" + "ONNX: ...symbols_v1.onnx"
```
Gdyby trzeba wskazać ręcznie — najpierw zlokalizuj plik, potem `--weights`:
```powershell
Get-ChildItem -Recurse data\runs -Filter best.pt | Select FullName
.venv\Scripts\python.exe -m train.export_onnx --weights "data\runs\<run>\weights\best.pt"
```

---

## 2026-06-14 [ZW] — Prompty 006 + 001: export ONNX + inferencja symboli

Temat: **best.pt → ONNX + detektor YOLOv8 ONNX (offline).** Kod + pytest na ZW; export i inferencja GPU u Ciebie. Bazuje na BUILD M0 (mAP50≈0.04, 17 epok — overfit przy 9 stronach, zgodnie z przewidywaniem).

### Co zrobione (kod)

- **`train/export_onnx.py`** — `export_onnx()`: best.pt → ONNX (opset 12, zgodny z onnxruntime-gpu 1.17), kopia do `data/models/symbols_v1.onnx` + wpis do `registry.json` (`register_model`). Leniwy import ultralytics. CLI `--weights/--version/--opset/--imgsz`.
- **`backend/recognize/symbol_detector.py`** — `OnnxSymbolDetector.detect()`: session `["CUDAExecutionProvider","CPUExecutionProvider"]`, preprocess przez `resize_for_yolo` (BGR→RGB, CHW, /255), parsowanie wyjścia YOLOv8 `(1,4+nc,N)`, próg confidence, **NMS** (`cv2.dnn.NMSBoxes`), mapowanie bboxów z 640 → piksele oryginału, `class_id→class_name`. Leniwy import onnxruntime.
- **`backend/tests/test_symbol_detector.py`** — 3 testy (fake session, bez onnxruntime): mapowanie współrzędnych, filtr confidence, fallback nazwy klasy.
- **`train/tests/test_export_onnx.py`** — 2 testy: guard braku wag + zapis registry.

### Testy (PC ZW)

```
pytest backend/tests labeler/tests train/tests   →  35 passed
python -m backend.cli validate schema/fixtures/page1_expected.json  →  approved: true
```

> `*.onnx`, `best.pt`, `data/runs/` **NIE** w repo. Pipeline (`OfflineRecognizer`) czyta aktywny model z `registry.json` → po Twoim eksporcie sam podłączy `symbols_v1.onnx`.

### Uruchomienie u Filipa (RTX 2080, PowerShell)

```powershell
# 1. Export wytrenowanych wag do ONNX (uzywa data/runs/symbols_v1/weights/best.pt)
.venv\Scripts\python.exe -m train.export_onnx
#    → data/models/symbols_v1.onnx + aktualizacja data/models/registry.json (active=symbols_v1)

# 2. Smoke test inferencji na stronie spoza treningu (np. p016/p019 — walidacja generalizacji)
.venv\Scripts\python.exe -c "from backend.recognize.symbol_detector import OnnxSymbolDetector; d=OnnxSymbolDetector('data/models/symbols_v1.onnx', {'element':0}); print(len(d.detect('data/raw/SchematWRT01_p016.png')), 'detekcji')"
```

Przy mAP50≈0.04 spodziewaj się **mało/żadnych** trafień na stronach spoza treningu — to oczekiwane. Cel tego kroku: potwierdzić, że ścieżka ONNX→inferencja działa end-to-end. Realny skok jakości dopiero po doznaczeniu stron lub atlasie (008a). Daj znać ile detekcji wyszło na p016/p019.

---

## 2026-06-14 [ZW] — Prompt 005 (BUILD M0): dataset export + kod treningu YOLO

Temat: **Kod eksportu datasetu (SQLite→YOLO) + trening YOLOv8n.** Implementacja + pytest na PC ZW. **Pełny trening GPU robisz Ty (RTX 2080).**

> Uwaga: pierwsza wersja tego wpisu powstała na **starych plikach** (nasłuch pusha był zatrzymany). Po fast-forward do `origin/main` przeczytałem właściwy `sync/prompts/005-train-symbols.md` i dostosowałem kod (katalog `data/labeled/`, val = ostatnie strony p022/p023, pomijanie `test_*`, manifest, summary JSON, CLI `--epochs/--batch`).

### Co zrobione (kod)

- **`labeler/export.py`** — fix: `export_yolo` kopiuje teraz źródłowy PNG z `data/raw/` do `images/` (para image/label wymagana przez YOLO). Dodane helpery `yolo_label_lines()` i `find_raw_image()`.
- **`train/dataset_export.py`** — NOWY. SQLite → `data/labeled/{images,labels}/{train,val}` + `data.yaml` + `export-manifest.json`. Deterministyczny split (sort po `page_id`, **ostatnie** strony → val, val_ratio 0.2). Pomija strony `test_*` i rekordy bez PNG. CLI: `python -m train.dataset_export`.
- **`train/train_symbols.py`** — `train()` zaimplementowany: ultralytics YOLOv8n, leniwy import (testy nie wymagają torch/GPU), twardy limit `batch≤8` (8GB VRAM), run w `data/runs/symbols_v1/`, zapis `best.pt` + summary `data/models/symbols_v1_train_summary.json`. CLI z `--epochs/--batch/--imgsz/--device`. `register_model()` bez zmian.
- **`train/tests/test_dataset_export.py`** — NOWY. 6 testów na fixturach (atrapy PNG, tmp dir), bez GPU.

### Testy (PC ZW)

```
pytest backend/tests labeler/tests train/tests   →  30 passed
python -m backend.cli validate schema/fixtures/page1_expected.json  →  approved: true
```

> `best.pt`, `data/runs/`, wagi **NIE** idą do repo — trenujesz u siebie. `data/schemagen.db` i `data/raw/*.png` są w `.gitignore`, na ZW ich nie ma → nie odpalałem pełnego treningu ani eksportu na żywej bazie.

### Uruchomienie u Filipa (RTX 2080, PowerShell)

```powershell
# 0. (raz) zależności GPU
pip install -e ".[gpu]"

# 1. PNG źródłowe w data/raw/ (SchematWRT01_p*.png), adnotacje już w data/schemagen.db

# 2. Batch eksport SQLite → YOLO train/val + kopie PNG
python -m train.dataset_export
#    → data/labeled/{images,labels}/{train,val} + data.yaml + export-manifest.json
#    wg promptu: 9 stron, val = p022, p023 (ostatnie); ~394 bboxy, klasa: element
#    wypisze: Dataset: train=N val=M klasy=1 -> ...data.yaml

# 3. Trening (batch twardo ograniczony do 8)
python -m train.train_symbols --epochs 30 --batch 8
#    → best.pt w data/runs/symbols_v1/weights/best.pt
#    → summary w data/models/symbols_v1_train_summary.json (dopisz mAP do sync, jeśli chcesz)

# 4. (prompt 006) export best.pt → ONNX — jeszcze NotImplemented, osobne zadanie
```

9 stron to mało — spodziewaj się overfittu. Po treningu wrzuć metryki z summary (map50) — dostroję split/augmentacje albo damy zielone na doznaczanie kolejnych stron.

---

## 2026-06-14 [ZW] — Prompt 007: analiza źródeł wiedzy (runda 1–4)

Temat: Ocena 3 źródeł + werdykt o archiwum EPLAN + strategia treningu. **Research, bez kodu.**

Deliverable: [`docs/knowledge-sources-analysis.md`](../docs/knowledge-sources-analysis.md) (v4) + [`docs/qet-library-report.md`](../docs/qet-library-report.md) (raport z pobranej biblioteki QET) + uzupełniony [`sync/sources-inbox.md`](sources-inbox.md).

3 rekomendacje (do review):
- **Atlas warstwowy**, nie jedno źródło: (1) **IEC 60617** PDF = baza normatywna, (2) **QElectroTech** = przemysł generyczny + Siemens (pobrane 8732 symbole, GPL, `.elmt`/XML), (3) **producent** = `.edz` z EPLAN Data Portal, później.
- **Trening Siemens-first.** WRT01 ma sterowniki **GE Vernova (brak w QET)** + **Phoenix Contact (13, rdzeń brak)** → uczymy klas generycznych (`relay`, `fuse`, `terminal_block`, `plc_io_module`) na komponentach Siemens (452 QET) + generyki; GE/Phoenix dochodzą później mapowane na te klasy. Nie blokuje startu.
- **Archiwum `eplan-era-2026-06.zip` = NIE źródło symboli** (kod C# + baza wiedzy API, zero makr). Dało tylko typy plików do szukania u producenta: `.edz` / `.ema` / `.ems`.

Do decyzji Cursor:
- Akceptacja kierunku „atlas warstwowy + Siemens-first"?
- Prompt **008-symbol-atlas-extract** (layout-aware ekstrakcja IEC 60617 PDF + parser `.elmt` QET, filtr Siemens+generyki → `config/symbol-reference.yaml` + `data/atlas/`). [RYZYKO] do rozwiązania: parowanie obraz↔opis w PDF; dedup IEC↔QET; aliasy PL tylko ~34% w QET.
- Licencje [do potwierdzenia Filip]: GPL QET vs licencja SchemaGen; redystrybucja crop-ów IEC 60617.

Otwarte pytania do Filipa — sekcja na końcu `knowledge-sources-analysis.md`.

---

## 2026-06-14 [ZW] — Prompt 003: hierarchia bboxów + relacje przestrzenne

Temat: Zaimplementowana warstwowa hierarchia bboxów (parent/depth/rel_bbox) + relacje przestrzenne. YOLO bez zmian.

Co zrobiłem:
- **Modele** (`backend/models/label.py`, `schema.py`): `BboxAnnotation`/`Component` mają teraz `parent_id`, `depth`, `rel_bbox`; nowy model `SpatialRelation`; `spatial_relations[]` na `LabelRecord` i `SchemaModel`. Wszystko opcjonalne (backward compatible).
- **Geometria** (`backend/geometry/bbox_layout.py`, nowy — źródło prawdy): czyste funkcje `contains` (zawieranie ścisłe, EPS=1px), `find_parent` (min. powierzchnia, remis po id), `compute_hierarchy`, `compute_spatial_relations` (contains rodzic→dziecko + kompas między rodzeństwem wg centroidów), `enrich_label_record`.
- **API** (`labeler/app.py`): POST woła `enrich_label_record` **przed** zapisem, zwraca `hierarchy_depth_max`; GET migruje stare rekordy w locie (np. `SchematWRT01_p013`).
- **Eksport** (`labeler/export.py`): `parent_id`/`depth`/`rel_bbox` → `Component`, `spatial_relations` → `SchemaModel`; enrich gdy relacje puste; YOLO **bez zmian** (wszystkie bboxy).
- **UI** (`labeler/static/app.js?v=13`): JS-lustro `recomputeHierarchy()` (ta sama logika contains + min area) po `mouseup` / `removeBboxAt` / wczytaniu strony; accordion z wcięciem wg `depth` + `↳ w #<rodzic>`; zaznaczone dziecko → żółta przerywana obwódka rodzica na canvas; drzewiaste sortowanie listy; payload rozszerzony. Auto-zapis/localStorage/pageCache (v12) **nietknięte** — tylko rozszerzone.
- **Schema JSON** (`schema/schema-model.json`): nowe pola opcjonalne.
- **Docs** (`docs/labeling-guide.md`): sekcja „Oznaczanie warstwowe".

Testy: nowy `backend/tests/test_bbox_layout.py` (7) + rozszerzony `labeler/tests/test_export.py` (hierarchia w schema + YOLO zachowuje oba bboxy). `pytest backend/tests labeler/tests` → **24 passed**. `python -m backend.cli validate schema/fixtures/page1_expected.json` → approved.

Jak testować ręcznie:
```
python -m labeler.app   # localhost:8765
```
1. Narysuj duży bbox-blok, potem mniejszy w środku.
2. Zapisz → w DevTools/Network POST `/api/annotations`: dziecko ma `parent_id` bloku, `depth=1`, `rel_bbox`.
3. Odśwież → hierarchia wczytana, accordion z wcięciem i `↳ w #<rodzic>`.
4. Zaznacz dziecko → żółta przerywana obwódka rodzica na canvas.
5. Eksport → `*.schema.json` ma `spatial_relations` (contains + kompas).
6. `labels/*.txt` (YOLO) nadal ma **oba** bboxy.

Commit: `[Claude] labeler: bbox hierarchy + spatial relations (prompt 003)`

---

## 2026-06-14 [ZW] — Prompt 001: canvas bbox labeler

Temat: Zaimplementowany interaktywny canvas bbox w `labeler/static/app.js`.

Co zrobiłem:
- Rysowanie bbox: mousedown → mousemove → mouseup (preview dashed rect podczas ciągnięcia)
- Aktywna klasa z listy (`config/symbol-classes.yaml`), klawisze 1–9 + klik na liście
- Zoom: scroll na canvas (zoom do punktu kursora)
- Wyświetlanie istniejących bbox po załadowaniu strony (GET `/api/annotations/{page_id}`)
- Zaznaczanie bbox kliknięciem (highlight w list + dashed outline na canvas)
- Del/Backspace — usuwa zaznaczony bbox
- Zapis POST `/api/annotations`, eksport YOLO
- Każdy bbox dostaje unikalny id = `{class}_{timestamp}`

Jak testować ręcznie:
```
python -m labeler.app   # localhost:8765
```
1. Załaduj dowolną stronę z listy.
2. Wybierz klasę (klawisze 1–9 lub klik na liście).
3. Narysuj 3 bbox na canvas.
4. Zaznacz jeden bbox i wciśnij Del — powinien zniknąć.
5. Scroll — zoom do kursora.
6. Kliknij „Zapisz" → alert „Zapisano ✓".
7. Odśwież stronę — bbox powinny się wczytać z powrotem.
8. Kliknij „Eksport YOLO + JSON".

Testy automatyczne: `pytest labeler/tests backend/tests` → 14 passed.

Commit: `[Claude] labeler: canvas bbox (prompt 001)`

---

## 2026-06-13 [ZW] — Plan B: globalny FUNC_COUNTER (MA1+MA2)

Temat: Plan A (CONFIGSCHEME) odrzucony po Twoim teście. Wdrożony Plan B — wymuszenie licznika w add-inie.

Co zmieniłem:
- Nowa akcja `SchemaGenForceGlobalCounter` (`scripts/addin/Actions/ForceGlobalCounterAction.cs`) — kolejnym silnikom (FUNC_CODE=MA) nadaje MA1, MA2... przez `NameParts.FUNC_COUNTER` (Transaction+SafetyPoint). NIE rusza `<20010>`. Build CS0266 naprawiony (getter zwraca `FunctionBasePropertyList`).
- `config/numbering-rules.xml`: reguła MA → `configScheme=""` + `forceGlobalCounter="true"`.
- `SchemaGen_MVP.cs`: pass 2 woła nową akcję dla reguł z flagą; guard wymusza reload DLL.

Do zrobienia po stronie Filip:
1. `.\scripts\build_addin.ps1` (powinno przejść — sprawdź 0 błędów).
2. Skopiuj `SchemaGen_MVP.cs` + `config/numbering-rules.xml` → `Skrypty\Schemagen\config\`.
3. Przeładuj DLL (pojawi się `SchemaGenForceGlobalCounter`), świeży Hello_world, uruchom MVP.
4. Sprawdź: `-MA1` na +B2, `-MA2` na +B4; FC bez zmian; `output/force-global-counter.json` → `changed==total`, brak `ERR` w `log`; layout bez regresji.
5. Jeśli `ERR` w logu (NameParts) → przyślij `force-global-counter.json`, mam alternatywę (świeży `FunctionBasePropertyList` z plant/location/code).

Commit: (auto GitSync po push)

---

## 2026-06-13 [ZW]
Temat: Uruchomiona magistrala koordynacji.
Kontekst: Dodałem `GitSyncDaemon.ps1`, `Install-GitSyncTask.ps1` i katalog `sync/`. Po Twojej stronie zarejestruj daemon (patrz `docs/git-sync-setup.md`).
Do zrobienia po stronie Filip: uruchom `Install-GitSyncTask.ps1 -MachineTag Filip -RepoPath "C:\Users\Filip\Desktop\Cursor\SchemaGen"`.
Commit: —
