# 028 Część C — projekt augmentacji geometrycznej

Status: **PROJEKT DO DECYZJI** (implementacja poza zakresem 028)
Data: 2026-07-19
Dane: 199 stron / 3639 bbox / 25 klas ≥5 instancji / **1053 kafle** (win=1536, overlap=0.2, min_visible=0.35)
Narzędzie pomiarowe: `scripts/augment_feasibility.py`

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
| Kafli z ≥1 bboxem | **1053** |
| Wariant 1, stan obecny (2/25 klas ma zgodę) | **72 kafle = 6,8 %** |
| Wariant 1, **sufit** (zgoda wszystkim poza jawnie zabronionymi) | **808 kafli = 76,7 %** |

**6,8 % to nie jest werdykt o wariancie 1.** To pomiar tego, jak bardzo
`config/symbol-symmetry.yaml` jest jeszcze niewypełniony — dziś zgodę mają tylko
`zlaczka` i `styk_nc`. Liczbą rozstrzygającą o geometrii jest **76,7 %**.

Próg „poniżej ~10 % wariant 1 jest bezwartościowy" z prompta zostaje **przekroczony
z dużym zapasem**. Rekomendacja prompta (wariant 1 jako pierwszy) się broni — ale
z jedną istotną korektą, patrz §3.

### 1.1 Założenie „schematy są gęste i mieszane" jest FAŁSZYWE

To był powód, dla którego prompt obawiał się o wariant 1. Pomiar go nie potwierdza:

| Różnych klas w kaflu | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Kafli | **744** | 183 | 81 | 34 | 7 | 2 | 2 |

**70,7 % kafli jest jednoklasowych.** Przy oknie 1536 px na stronie ~6600 px symbole
tej samej klasy grupują się przestrzennie (listwy zaciskowe, rzędy złączek). Warunek
„wszystkie klasy w kaflu dopuszczają transformację" jest więc łatwy do spełnienia,
a nie trudny.

---

## 2. [RYZYKO] Prawdziwy problem wariantu 1: augmentuje nie tam, gdzie trzeba

Wariant 1 duplikuje **kafle**, a kafle są zdominowane przez klasy liczne.

| Miara | Wynik |
|---|---|
| Kafli zawierających klasę z zakresu 5–30 instancji | **159 / 1053 = 15,1 %** |
| Z tego kwalifikuje się do transformacji (sufit) | 128 (80,5 % z nich) |
| Kafli kwalifikujących się **bez** klasy 5–30 | 808 − 128 = **680** |

Czyli 680 z 808 zduplikowanych kafli (84 %) nie zawiera żadnej klasy, której brakuje
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

### Przyrost instancji (sufit, 128 kafli celowanych)

| Klasa | inst. | +1 transformacja | +5 transformacji |
|---|---:|---:|---:|
| ekranowanie_kabla | 5 | +5 | +25 |
| styki_nc | 5 | +16 | +80 |
| polaczenie_przewodow | 6 | +8 | +40 |
| przycisk_awaryjny | 6 | +11 | +55 |
| uziemienie | 9 | +13 | +65 |
| wylacznik_nadpradowy | 10 | +8 | +40 |
| custom_terminale_urzadzenia | 16 | +42 | +210 |
| custom_urzadzenie | 17 | +30 | +150 |
| terminal_sterownika_safety | 17 | +27 | +135 |
| styk_nc | 20 | +45 | +225 |
| cewka_zaworow | 21 | +41 | +205 |
| lampka | 26 | +30 | +150 |

Balast dla klas licznych pozostaje mały: `zlaczka` +80 przy bazie 1028 (+7,8 %),
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
| **1T celowany** | **rekomendowany** | 128 kafli dokładnie tam, gdzie brak danych |
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
Przy 70,7 % kafli jednoklasowych nie jest.

### C1b — wymagania, jeśli kiedykolwiek

- miejsce docelowe białe (próg jasności) i bez kolizji z istniejącym bboxem ani linią,
- wklejony symbol dostaje krótkie odcinki linii do terminali (`terminals[]` w GT,
  względne wobec bbox) — inaczej uczymy wzorca „symbol bez podłączeń",
- zakaz wklejania w dolne `roi_bottom_cut_frac` (tabliczka rysunkowa).

---

## 5. Warunki wdrożenia — bez nich nie wdrażać

### 5.1 Wypełnić `config/symbol-symmetry.yaml`

Dziś zgodę mają 2 z 25 klas; **11 z 12 klas zakresu 5–30 nie ma jeszcze wpisu**.
Bez tego kroku 1T wygeneruje 2 kafle zamiast 128. To jest warunek blokujący.

Ścieżka: `scripts/element_review.py` (panel symetrii + podgląd transformacji)
→ `symmetry.json` → `scripts/apply_symmetry.py --apply`.

Podgląd miniatury po transformacji jest tu istotą sprawy — decyzja „czy to nadal ten
sam symbol" musi zapaść wzrokowo, nie z pamięci.

### 5.2 Kontrola jakości

Generator zapisuje ~30 kafli z narysowanymi bboxami do `data/output/augment_preview/`.
Augmentacja, której nikt nie obejrzał, to najszybsza droga do zatrucia datasetu —
przy 199 stronach nikt tego nie wyłapie po fakcie.

### 5.3 Miara sukcesu

**mAP per klasa** na tych samych 8 stronach val, przed i po, dla klas objętych
augmentacją. Nie „czy mAP ogólne wzrosło".

- wdrażamy: mAP rośnie dla większości klas 5–30 **i nie spada** dla klas dużych,
- odrzucamy: mAP klas dużych spada → artefakty psują cechy wspólne,
- **val nigdy nie jest augmentowany** (inaczej mierzysz sam siebie).

### 5.4 Deterministyczny seed

Bez niego dwa biegi treningu są nieporównywalne, a §5.3 traci sens.

---

## 6. [RYZYKO] Ograniczenia tego pomiaru

1. **Augmentacja nie tworzy nowej informacji.** Dla `ekranowanie_kabla` (5 instancji)
   pięć transformacji daje 25 obrazów tych samych pięciu egzemplarzy. Model uczy się
   ich na pamięć w pięciu orientacjach. **Dla klas poniżej ~5 instancji doznaczenie
   jest jedyną sensowną drogą** — augmentacja ich nie uratuje.
2. Sufit 76,7 % zakłada, że 22 klasy bez wpisu **dostaną** zgodę. Część jej nie dostanie
   (`przycisk`, `lampka`, `uziemienie` mogą mieć znaczącą orientację). Realny wynik
   będzie między 6,8 % a 76,7 % — dokładna wartość zależy od §5.1.
3. Pomiar liczy kafle z GT (`image_width/height`), nie z wyeksportowanych plików.
   Obecny `data/labeled_tiled/` jest **nieaktualny** (12 kafli train, klasy typu `saf1`,
   `1`, `10` — ślad po starej ścieżce tagowej, patrz prompt 026). Po naprawie
   z 027/028 wymaga ponownego eksportu.
4. Zmiana `win` lub `overlap` zmienia strukturę z §1.1. Przy mniejszym oknie kafli
   jednoklasowych będzie więcej, przy większym — mniej.

---

## 7. Decyzja do podjęcia przez Filipa

1. **Wariant 1T (celowany)** — rekomendowany, [ ] tak / [ ] nie
2. Przegląd symetrii 12 klas zakresu 5–30 w `element_review.py` — kiedy?
3. Czy `terminal_przylaczeniowy` (534 inst., blocker #1 w stanie obecnym) w ogóle
   wchodzi do rozważań? Przy 1T nie ma znaczenia — nie jest w zakresie 5–30.
