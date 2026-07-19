# Zadanie 028: element_review v2 — przegląd klas + oznaczanie symetrii symboli

**Status:** NOWE
**Model:** patrz sekcja „Dobór modelu" na końcu
**Zależności:** 027 (scalenie klas) — 028 jest jego narzędziem, nie następcą
**Nie łamać:** `gt/<page_id>.json` = źródło prawdy; zapis atomowo; niezmienniki z `CLAUDE.md`

---

## Kontekst

Po odzysku GT (prompt 025) mamy **199 stron / 3639 bbox / 25 klas YOLO ≥5 instancji**.
`scripts/element_review.py` to jedyne narzędzie do masowego przeglądu i retagowania — i w obecnej
formie nie wystarcza na tej skali.

Dwa braki:

1. **Rozbieżność licznika.** `class_report.py` pokazuje `styki: 163`, `element_review.py` renderuje
   **160** crops tej klasy. Trzy elementy gdzieś wypadają.
2. **Brak informacji o symetrii symbolu**, która jest potrzebna do sensownej augmentacji treningu.

---

## Część A — [BŁĄD] zdiagnozuj rozbieżność 163 vs 160

**Hipoteza główna:** dwa różne źródła klasyfikacji.

| Plik | Funkcja klasyfikująca |
|---|---|
| `scripts/class_report.py` → `backend/class_map.py:class_distribution` | `bbox_class(class_name, tag, pmap)` — **`type` z GT v2 ma pierwszeństwo** |
| `scripts/element_review.py:20` | `tag_to_class(tag)` — **wyłącznie `tag`** |

`bbox_class` powstało w Kroku 1 prompta 027 właśnie dlatego, że w GT v2 `class_name` = `type`
symbolu, a `tag` to oznaczenie z rysunku („6", „BN"). `element_review` nie został zmigrowany.

**Do zrobienia:**

1. Potwierdź hipotezę: wypisz elementy, dla których `bbox_class(...) != tag_to_class(tag)`.
   Jeśli różnica to nie 3 elementy w `styki`, szukaj dalej — kandydaci: brak PNG strony
   (`find_raw_image` → `None`), wyjątek w `crop_bbox`, bbox poza kadrem
   (8 znanych przypadków klasy `urzadzenie`, patrz `sync/analysis/025-labeler-audit.md`).
2. Napraw: `element_review.py` ma używać `bbox_class`, tak jak eksport treningowy.
3. **Narzędzie ma jawnie raportować, ilu elementów NIE udało się wyrenderować i dlaczego.**
   Cicha rozbieżność między raportem a przeglądarką jest gorsza niż brak przeglądarki —
   użytkownik podejmuje decyzje o danych, których nie widzi.

---

## Część B — oznaczanie symetrii symbolu

### Problem domenowy

Augmentacja geometryczna w treningu jest dziś globalnie wyłączona
(`train_symbols.py`: `--fliplr 0.0 --flipud 0.0 --degrees 0.0`) i słusznie: orientacja niesie
znaczenie. `strzalka_potencjalu_wejsciowa` i `strzalka_potencjalu_wyjsciowa` różnią się **wyłącznie**
kierunkiem — odbicie lustrzane zamienia jedną w drugą i uczy sieć błędu.

Ale to zerojedynkowe. Wiele symboli **jest** symetrycznych i dla nich augmentacja byłaby czystym
zyskiem — zwłaszcza dla klas z 5–20 instancjami, gdzie danych jest za mało.

### Model danych

Nowy plik `config/symbol-symmetry.yaml`, klucz = kanoniczna klasa (`type`, ta sama przestrzeń nazw
co `config/symbol-classes.yaml`):

```yaml
# Dozwolone transformacje geometryczne dla augmentacji treningowej.
# Puste/brak wpisu = BRAK zgody (bezpieczny domyślny — orientacja znacząca).
symmetry:
  zlaczka:
    mirror_h: true          # odbicie w poziomie zachowuje znaczenie
    mirror_v: true
    rotations: [90, 180, 270]
    note: "okrągła złączka — pełna symetria"
  strzalka_potencjalu_wejsciowa:
    mirror_h: false         # lustro zamienia w strzalka_potencjalu_wyjsciowa
    mirror_v: false
    rotations: []
    note: "kierunek = znaczenie, patrz 012-mostek-orientacja"
  styk_nc:
    mirror_h: true
    mirror_v: false
    rotations: [180]
```

**Wymagania:**

* domyślna wartość przy braku wpisu = **wszystko zabronione** (fail-safe: brak wiedzy ≠ zgoda)
* `rotations` tylko wielokrotności 90 — dowolne kąty wymagałyby przeliczania bboxów
  do obrysu prostokątnego i rozmywają etykietę
* walidacja schematu przy wczytaniu; nieznana klasa w pliku → ostrzeżenie, nie wyjątek

### UI w `element_review.html`

Przy każdej klasie (nie przy każdym elemencie — symetria jest własnością **klasy symbolu**,
nie egzemplarza) panel z checkboxami: `↔ lustro poziome`, `↕ lustro pionowe`, `⟳ 90°`, `⟳ 180°`, `⟳ 270°`.

* stan zapisywany do pobieranego `symmetry.json` (analogicznie do istniejącego `reassignments.json`)
* podgląd: obok crop-a wzorcowego renderuj miniatury po zaznaczonych transformacjach —
  **użytkownik ma zobaczyć, czy wynik nadal jest tym samym symbolem**, to jest cała wartość tego UI
* zachowaj istniejące funkcje: retag, usuwanie, „przejrzana" w localStorage, filtr po klasie

Nowy skrypt `scripts/apply_symmetry.py`: `symmetry.json` → `config/symbol-symmetry.yaml`,
z `--dry-run` domyślnie (konwencja z `apply_reassign.py`), zapis atomowy.

---

## Część C — [RYZYKO] jak to faktycznie wpiąć w trening

**To jest najtrudniejsza część zadania i nie wolno jej pominąć w projekcie.**

Ultralytics YOLO **nie obsługuje augmentacji per-klasa**. `fliplr`/`degrees` działają na całym
obrazie, więc kafel zawierający `zlaczka` (symetryczna) i `strzalka_potencjalu_wejsciowa`
(niesymetryczna) nie może być odbity — zepsułby tę drugą.

Trzy możliwe drogi, do rozstrzygnięcia w projekcie **przed implementacją**:

| Wariant | Na czym polega | Koszt | Ryzyko |
|---|---|---|---|
| **1. Offline, kafel-warunkowo** | w `train/tiled_export.py` generuj dodatkowe kopie kafla tylko wtedy, gdy **wszystkie** klasy w tym kaflu dopuszczają daną transformację | S | mało kafli spełni warunek — schematy są gęste i mieszane |
| **2. Copy-paste na poziomie symbolu** | wycinaj crop symbolu, transformuj, wklejaj w losowe wolne miejsce kafla, dopisz etykietę | L | artefakty na krawędziach wklejenia, tło schematu jest białe i regularne — może pomóc, może nauczyć artefaktu |
| **3. Osobne kafle syntetyczne** | generuj dodatkowe obrazy zawierające wyłącznie symbole symetryczne | M | rozkład tła odbiega od realnego |

Rekomendacja do weryfikacji: **wariant 1 jako pierwszy** — najprostszy, w pełni kontrolowalny,
i od razu pokaże w liczbach, ile kafli w ogóle kwalifikuje się do augmentacji. Jeśli wyjdzie
poniżej ~10% kafli, wariant 1 jest bezwartościowy i trzeba iść w 2.

**Zadanie ma dostarczyć tę liczbę przed decyzją o implementacji augmentacji.**

Niezależnie od wariantu: `config/symbol-symmetry.yaml` ma wartość samą w sobie jako
**udokumentowana wiedza domenowa** — dziś nie istnieje nigdzie w repo.

### C1 — silnik duplikacji symboli (rozwinięcie wariantu 2, propozycja Filipa)

**Zanim cokolwiek: augmentacja geometryczna nie tworzy nowej informacji.**
Dla `ekranowanie_kabla` (5 instancji) osiem transformacji daje 40 obrazów **tych samych pięciu
egzemplarzy**. Model uczy się ich na pamięć w ośmiu orientacjach — to nie jest to samo, co 40 różnych
egzemplarzy, a ryzyko przeuczenia rośnie. Dlatego:

**Zakres stosowania: klasy z 5–30 instancjami.** Poniżej 5 — najpierw doznaczyć, nie augmentować.
Powyżej ~30 — augmentacja daje malejący zwrot przy rosnącym ryzyku artefaktów.

Klasy kwalifikujące się dziś (12): `ekranowanie_kabla`(5), `styki_nc`(5), `polaczenie_przewodow`(6),
`przycisk_awaryjny`(6), `uziemienie`(9), `wylacznik_nadpradowy`(10), `custom_terminale_urzadzenia`(16),
`custom_urzadzenie`(17), `terminal_sterownika_safety`(17), `styk_nc`(20), `cewka_zaworow`(21),
`lampka`(26).

#### Dwa podejścia do „duplikowania", nie jedno

| | **C1a — transformacja in-place** | **C1b — copy-paste w nowe miejsce** |
|---|---|---|
| Co robi | obraca/odbija symbol **w jego własnym bboxie**, reszta kafla bez zmian | wycina crop, transformuje, wkleja w wolne miejsce kafla, dopisuje etykietę |
| Zaleta | brak problemu „gdzie wkleić", tło i sąsiedztwo naturalne | zwielokrotnia liczbę instancji w kaflu |
| Wada | linie dochodzące przestają pasować do terminali — obraz fizycznie niemożliwy | symbol wisi w powietrzu bez linii; model może nauczyć się „symbol bez podłączeń" |
| Ryzyko | średnie — detektor uczy się wyglądu, nie kontekstu, ale uczy się też niespójności | wysokie — trzeba wykryć wolne miejsce, inaczej przykryjesz inny symbol |

**Rekomendacja: zacząć od C1a.** Jest prostszy i nie wymaga detekcji wolnego miejsca. Jeśli okaże się
za słaby, C1b można dołożyć.

#### Wymagania dla C1b (jeśli w ogóle)

* miejsce docelowe musi być **białe** (próg jasności) i nie kolidować z żadnym istniejącym bboxem
  ani z linią — inaczej niszczysz dane, na których uczysz
* wklejony symbol powinien dostać **krótkie odcinki linii** dochodzące do terminali, żeby nie uczyć
  wzorca „symbol bez podłączeń"; pozycje terminali są w GT (`terminals[]` symbolu — względne wobec bbox)
* zakaz wklejania w dolne `roi_bottom_cut_frac` (tabliczka rysunkowa)

#### Kontrola jakości — obowiązkowa

Silnik ma zapisywać **próbkę wygenerowanych kafli do przeglądu wzrokowego**
(`data/output/augment_preview/`, ~30 obrazów z narysowanymi bboxami). Augmentacja, której nikt
nie obejrzał, to najszybsza droga do zatrucia datasetu — a przy 199 stronach nikt tego nie wyłapie
po fakcie.

#### Miara sukcesu — bez niej nie wdrażać

Nie „czy mAP ogólne wzrosło", tylko **mAP per klasa na tych samych 8 stronach val, przed i po**,
dla klas objętych augmentacją. Warunki:

* **wdrażamy**, gdy mAP rośnie dla większości klas 5–30 i **nie spada** dla klas dużych
* **odrzucamy**, gdy mAP klas dużych spada — znaczy, że artefakty psują wspólne cechy
* val **nigdy nie jest augmentowany** (inaczej mierzysz sam siebie)

Deterministyczny seed w generatorze — inaczej dwa biegi treningu są nieporównywalne.

---

## Walidacja

```powershell
python scripts/element_review.py --class styki --thumb 140
# licznik w naglowku == class_report; rozbieznosci wypisane jawnie z powodem

python scripts/class_report.py --min-count 5
python scripts/apply_symmetry.py --dry-run
python scripts/apply_symmetry.py --apply
pytest backend/tests labeler/tests -q
```

**Kryteria odbioru:**

1. `element_review` i `class_report` podają **tę samą liczbę** dla każdej klasy, albo różnica jest
   jawnie wypisana z przyczyną
2. `config/symbol-symmetry.yaml` powstaje i jest walidowany przy wczytaniu
3. brak wpisu = brak zgody na transformację (test jednostkowy)
4. raport: ile kafli kwalifikuje się do augmentacji w wariancie 1
5. `pytest` bez regresji (obecnie 329 passed)

---

## Poza zakresem

* sama implementacja augmentacji w treningu (osobne zadanie, po decyzji z Części C)
* zmiany w `gt/*.json` — 028 czyta GT, zapisuje wyłącznie do `config/` i `data/output/`
* retrain (to Etap 3 z `sync/PLAN-027-TRENING.md`)

---

## Dobór modelu

| Część | Model | Uzasadnienie |
|---|---|---|
| **A** (diagnoza rozbieżności) | **Sonnet 5** | hipoteza już postawiona i zawężona do dwóch funkcji — to weryfikacja i poprawka, nie śledztwo |
| **B** (schema + UI) | **Sonnet 5** | dobrze zdefiniowany CRUD + HTML/JS; zakres opisany w tym prompcie |
| **C** (projekt augmentacji) | **Opus 4.8** | otwarty problem projektowy z trzema wariantami i realnym ryzykiem, że wybrany okaże się bezwartościowy; wymaga rozumienia interakcji tiling ↔ augmentacja ↔ rozkład klas |

**Praktycznie:** jeśli robisz to jednym przebiegiem — **Opus 4.8**, bo Część C jest najdroższa
w skutkach i najłatwiej ją zrobić źle. Jeśli dzielisz: **Opus na projekt Części C i schemat danych
(bez kodu), potem Sonnet 5 na A + B + implementację według zatwierdzonego projektu** — to ten sam
podział, który zadziałał w 025.

**Czego nie robić:** nie dawaj Części C modelowi bez kontekstu `train/tiled_export.py` —
wariant „włącz fliplr w train_symbols" jest oczywisty, szybki i **błędny**, bo zepsuje strzałki
potencjału. Model musi wiedzieć, dlaczego augmentacja jest dziś wyłączona.
