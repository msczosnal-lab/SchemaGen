# 028 Część C — projekt augmentacji geometrycznej

Status: **PROJEKT DO DECYZJI** (implementacja poza zakresem 028)
Data: 2026-07-19 (zaktualizowane po scaleniu `custom_*`)
Dane: 199 stron / 3639 bbox / **22 klasy ≥5 instancji** / **1044 kafle** (win=1536, overlap=0.2, min_visible=0.35)
Narzędzie pomiarowe: `scripts/augment_feasibility.py`

> **Aktualizacja:** scalenie trzech par `custom_X` → `X` (rola contextual) usunęło z treningu
> 96 bboxów w 3 klasach fantomowych. Liczby poniżej są po tej zmianie; przed nią było
> 25 klas / 1053 kafle / sufit 76,7 % / 12 klas w zakresie 5–30. Wnioski się nie zmieniły.

---

## 0. Dlaczego augmentacja jest dziś wyłączona

`train/train_symbols.py`: `--fliplr 0.0 --flipud 0.0 --degrees 0.0` — **i słusznie**.

`strzalka_potencjalu_wejsciowa` i `strzalka_potencjalu_wyjsciowa` różnią się
**wyłącznie zwrotem**. Lustrzane odbicie zamienia jedną w drugą i uczy sieć błędu.
To samo dotyczy `mostek`, gdzie orientacja to osobna klasa (`mostek_rXX`, 8 wariantów D4)
— transformacja nie augmentuje klasy, tylko ją zmienia.

Ultralytics **nie obsługuje augmentacji per-klasa**. `fliplr`/`degrees` działają na całym
obrazie. Dlatego każde rozwiązanie musi działać poza pętlą Ultralytics — offline,
na etapie `tiled_export`.

---

## 1. Pomiar — liczba, o którą prosił prompt

```powershell
python scripts/augment_feasibility.py            # stan faktyczny
python scripts/augment_feasibility.py --ceiling  # sufit
```

| Miara | Wynik |
|---|---|
| Kafli z ≥1 bboxem | **1044** |
| Wariant 1, stan obecny (2/22 klasy mają zgodę) | **~7 %** |
| Wariant 1, **sufit** (zgoda wszystkim poza jawnie zabronionymi) | **799 kafli = 76,5 %** |

**~7 % to nie jest werdykt o wariancie 1.** To pomiar tego, jak bardzo
`config/symbol-symmetry.yaml` jest jeszcze niewypełniony — dziś zgodę mają tylko
`zlaczka` i `styk_nc`. Liczbą rozstrzygającą o geometrii jest **76,5 %**.

Próg „poniżej ~10 % wariant 1 jest bezwartościowy" z prompta zostaje **przekroczony
z dużym zapasem**. Rekomendacja prompta (wariant 1 jako pierwszy) się broni — ale
z jedną istotną korektą, patrz §3.

### 1.1 Założenie „schematy są gęste i mieszane" jest FAŁSZYWE

To był powód, dla którego prompt obawiał się o wariant 1. Pomiar go nie potwierdza:

| Różnych klas w kaflu | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Kafli | **752** | 181 | 77 | 25 | 7 | 1 | 1 |

**72,0 % kafli jest jednoklasowych.** Przy oknie 1536 px na stronie ~6600 px symbole
tej samej klasy grupują się przestrzennie (listwy zaciskowe, rzędy złączek). Warunek
„wszystkie klasy w kaflu dopuszczają transformację" jest więc łatwy do spełnienia,
a nie trudny.

---

## 2. [RYZYKO] Prawdziwy problem wariantu 1: augmentuje nie tam, gdzie trzeba

Wariant 1 duplikuje **kafle**, a kafle są zdominowane przez klasy liczne.

| Miara | Wynik |
|---|---|
| Kafli zawierających klasę z zakresu 5–30 instancji | **140 / 1044 = 13,4 %** |
| Z tego kwalifikuje się do transformacji (sufit) | 111 (79,3 % z nich) |
| Kafli kwalifikujących się **bez** klasy 5–30 | 799 − 111 = **688** |

Czyli 688 z 799 zduplikowanych kafli (86 %) nie zawiera żadnej klasy, której brakuje
danych. Duplikują `terminal_przylaczeniowy` (534 inst.) i `zlaczka` (536 inst.).

**Skutek: wariant 1 w czystej postaci pogłębia niezbalansowanie zbioru** — dokładnie
odwrotnie niż jest zamierzone. To ryzyko, którego prompt nie nazwał, a jest poważniejsze
niż to, którego się obawiał.

---

## 3. Rekomendacja: wariant 1 **z celowaniem** (1T)

Jedna dodatkowa reguła w stosunku do wariantu 1:

> Generuj zaugmentowaną kopię kafla wtedy i tylko wtedy, gdy
> (a) **wszystkie** klasy w kaflu dopuszczają daną transformację **oraz**
> (b) kafel zawiera **co najmniej jedną** klasę z zakresu 5–30 instancji.

Warunek (b) kosztuje jedną linię kodu i usuwa całe ryzyko z §2.

### Przyrost instancji (sufit, 111 kafli celowanych)

| Klasa | inst. | +1 transformacja | +5 transformacji |
|---|---:|---:|---:|
| ekranowanie_kabla | 5 | +5 | +25 |
| styki_nc | 5 | +16 | +80 |
| polaczenie_przewodow | 6 | +8 | +40 |
| przycisk_awaryjny | 6 | +11 | +55 |
| uziemienie | 9 | +13 | +65 |
| wylacznik_nadpradowy | 10 | +8 | +40 |
| terminal_sterownika_safety | 17 | +27 | +135 |
| styk_nc | 20 | +45 | +225 |
| cewka_zaworow | 21 | +41 | +205 |
| lampka | 26 | +30 | +150 |

Balast dla klas licznych pozostaje mały: `zlaczka` +41 przy bazie 1028 (+4,0 %),
`terminal_przylaczeniowy` +83 przy bazie 1152 (+7,2 %). **Rozkład klas się poprawia,
nie pogarsza.**

### Koszt

Zmiana wyłącznie w `train/tiled_export.py`: po zbudowaniu listy kafli dodatkowa pętla
po dozwolonych transformacjach. Bez detekcji wolnego miejsca, bez wklejania, bez
artefaktów krawędziowych. **Najtańsza opcja z trzech.**

---

## 4. Warianty odrzucone i odłożone

| Wariant | Werdykt | Powód |
|---|---|---|
| **1 czysty** (bez celowania) | odrzucony | §2 — pogłębia niezbalansowanie |
| **1T celowany** | **rekomendowany** | 111 kafli dokładnie tam, gdzie brak danych |
| **2 / C1b** copy-paste w nowe miejsce | odłożony | dopiero gdy 1T okaże się za słaby |
| **3** osobne kafle syntetyczne | odrzucony | rozkład tła odbiega od realnego, a §1.1 pokazuje, że nie ma takiej potrzeby |

### C1a (transformacja in-place) — dlaczego nie

Prompt rekomendował C1a jako start. **Nie zgadzam się, przy tych danych.**

C1a obraca symbol w jego własnym bboxie, zostawiając resztę kafla bez zmian. Linie
dochodzące do terminali przestają pasować — powstaje obraz fizycznie niemożliwy.
Detektor uczy się wtedy niespójności między symbolem a jego otoczeniem.

Wariant 1T obraca **cały kafel**, więc linie, symbol i sąsiedztwo pozostają wzajemnie
spójne — obraz jest nadal poprawnym schematem, tylko obejrzanym z innej strony.
C1a byłby uzasadniony, gdyby warunek „wszystkie klasy w kaflu" był trudny do spełnienia.
Przy 72,0 % kafli jednoklasowych nie jest.

### C1b — wymagania, jeśli kiedykolwiek

- miejsce docelowe białe (próg jasności) i bez kolizji z istniejącym bboxem ani linią,
- wklejony symbol dostaje krótkie odcinki linii do terminali (`terminals[]` w GT,
  względne wobec bbox) — inaczej uczymy wzorca „symbol bez podłączeń",
- zakaz wklejania w dolne `roi_bottom_cut_frac` (tabliczka rysunkowa).

---

## 5. Warunki wdrożenia — bez nich nie wdrażać

### 5.1 Wypełnić `config/symbol-symmetry.yaml`

Dziś zgodę mają 2 z 22 klas; **9 z 10 klas zakresu 5–30 nie ma jeszcze wpisu**.
Bez tego kroku 1T wygeneruje 2 kafle zamiast 111. To jest warunek blokujący.

Ścieżka: `scripts/element_review.py` (panel symetrii + podgląd transformacji)
→ `symmetry.json` → `scripts/apply_symmetry.py --apply`.

Podgląd miniatury po transformacji jest tu istotą sprawy — decyzja „czy to nadal ten
sam symbol" musi zapaść wzrokowo, nie z pamięci.

### 5.2 Kontrola jakości

Generator zapisuje ~30 kafli z narysowanymi bboxami do `data/output/augment_preview/`.
Augmentacja, której nikt nie obejrzał, to najszybsza droga do zatrucia datasetu —
przy 199 stronach nikt tego nie wyłapie po fakcie.

### 5.3 [BŁĄD] Miara sukcesu jest dziś NIEWYKONALNA — naprawić przed augmentacją

Zamierzona miara: **mAP per klasa** na stronach val, przed i po, dla klas objętych
augmentacją. Nie „czy mAP ogólne wzrosło".

**Tego dziś nie da się policzyć.** `scripts/class_coverage.py` pokazuje, że
**10 z 22 klas ma ZERO instancji w val** — YOLO poda dla nich 0 albo NaN niezależnie
od jakości modelu. Wśród nich **7 z 10 klas objętych augmentacją**:

| Klasa docelowa 1T | inst. | w val |
|---|---:|---:|
| ekranowanie_kabla | 5 | **0** |
| styki_nc | 5 | **0** |
| polaczenie_przewodow | 6 | **0** |
| uziemienie | 9 | **0** |
| terminal_sterownika_safety | 17 | **0** |
| cewka_zaworow | 21 | **0** |
| lampka | 26 | **0** |
| przycisk_awaryjny | 6 | 3 |
| wylacznik_nadpradowy | 10 | 3 |
| styk_nc | 20 | 6 |

Mierzalne są 3 klasy, i to na 3–6 instancjach. Przy tej próbie jeden trafiony
lub chybiony bbox przesuwa mAP o kilkanaście punktów — to szum, nie sygnał.

**Wdrożenie augmentacji bez naprawy tego kroku jest niemierzalne z definicji.**
Zrobilibyśmy zmianę, której skutku nie da się ocenić — a przy 199 stronach nikt
nie wyłapie regresji ręcznie.

Do naprawy przed §3:

1. Przebudować `config/val-pages.yaml` tak, by **każda klasa ≥5 instancji miała
   reprezentację w val** (stratyfikacja, nie losowy wybór stron).
2. [BŁĄD] `p035` jest w `val-pages.yaml`, ale **nie ma `gt/*.json`** — ten sam wzorzec
   co `p040` z `KOLEJNE-ZADANIE.md`. Dwie z dziewięciu stron val bez GT.
3. [RYZYKO] 3 klasy istnieją na **jednej stronie**: `styk_stycznika` (36 inst., wszystkie
   z p039 — siatka 12×3 jednego rozdzielacza), `polaczenie_przewodow` (6, p015),
   `styki_nc` (5, p011). Dla nich każdy podział jest zły: strona w train ⇒ zero w val,
   strona w val ⇒ zero w train. **Rozwiązaniem jest doznaczenie kolejnych stron,
   nie augmentacja** — patrz §6.1.

Warunki akceptacji po naprawie:

- wdrażamy: mAP rośnie dla większości klas 5–30 **i nie spada** dla klas dużych,
- odrzucamy: mAP klas dużych spada → artefakty psują cechy wspólne,
- **val nigdy nie jest augmentowany** (inaczej mierzysz sam siebie).

### 5.4 Deterministyczny seed

Bez niego dwa biegi treningu są nieporównywalne, a §5.3 traci sens.

---

## 6. [RYZYKO] Ograniczenia tego pomiaru

### 6.1 Augmentacja nie tworzy nowej informacji

Dla `ekranowanie_kabla` (5 instancji) pięć transformacji daje 25 obrazów tych samych
pięciu egzemplarzy. Model uczy się ich na pamięć w pięciu orientacjach. **Dla klas
poniżej ~5 instancji doznaczenie jest jedyną sensowną drogą** — augmentacja ich nie uratuje.

Dotyczy to szczególnie klas **jednostronnych**. `styk_stycznika` ma 36 instancji, więc
po liczbie wygląda zdrowo — ale wszystkie pochodzą z siatki 12×3 na p039. To jeden
kontekst wizualny, jedna skala, jeden układ. Obrócenie go pięć razy daje 180 obrazów
tej samej sytuacji i **zwiększa ryzyko, że model nauczy się strony, a nie symbolu**.
Licznik instancji jest tu myląca miara — `scripts/class_coverage.py` pokazuje rozkład
po stronach i to jest właściwe kryterium.

### 6.2 Pozostałe zastrzeżenia

1. Sufit 76,5 % zakłada, że 20 klas bez wpisu **dostanie** zgodę. Część jej nie dostanie
   (`przycisk`, `lampka`, `uziemienie` mogą mieć znaczącą orientację). Realny wynik
   będzie między 7 % a 76,5 % — dokładna wartość zależy od §5.1.
2. Pomiar liczy kafle z GT (`image_width/height`), nie z wyeksportowanych plików.
   Obecny `data/labeled_tiled/` jest **nieaktualny** (12 kafli train, klasy typu `saf1`,
   `1`, `10` — ślad po starej ścieżce tagowej, patrz prompt 026). Po naprawie
   z 027/028 wymaga ponownego eksportu.
3. Zmiana `win` lub `overlap` zmienia strukturę z §1.1. Przy mniejszym oknie kafli
   jednoklasowych będzie więcej, przy większym — mniej.

---

## 7. Decyzja do podjęcia przez Filipa

**Kolejność ma znaczenie — punkt 1 blokuje resztę.**

1. **[BŁĄD] Naprawić `val-pages.yaml`** (§5.3). Bez reprezentacji 10 brakujących klas
   w val augmentacja jest niemierzalna, więc jej wdrożenie byłoby zmianą w ciemno.
   Przy okazji: `p035` w val bez `gt/*.json`.
2. Przegląd symetrii 10 klas zakresu 5–30 w `element_review.py` — kiedy?
3. **Wariant 1T (celowany)** — rekomendowany, [ ] tak / [ ] nie
4. Doznaczyć klasy jednostronne (`styk_stycznika` p039, `polaczenie_przewodow` p015,
   `styki_nc` p011) — augmentacja ich nie uratuje (§6.1).
5. Czy `terminal_przylaczeniowy` (534 inst., blocker #1 w stanie obecnym) w ogóle
   wchodzi do rozważań? Przy 1T nie ma znaczenia — nie jest w zakresie 5–30.
