# Analiza źródeł wiedzy — schematy elektryczne

**Data:** 2026-06-14
**Autor:** Claude (ZW) + Filip
**Wersja:** 3 (runda 3 — 3 źródła; doszedł QElectroTech)
**Profil WRT01 (Filip):** dominują **PLC/IO/sieci** + **aparatura producentów**
**Prompt:** `sync/prompts/007-sources-analysis.md`

---

## Streszczenie wykonawcze

Trzy źródła tworzące **warstwowy atlas**. Profil WRT01 (PLC/IO/sieci + aparatura producencka) oznacza, że **żadne pojedyncze źródło nie wystarczy** — IEC 60617 to podstawa normatywna, ale modułów PLC i symboli handlowych prawie nie ma.

- **ControlByte (1)** — wprowadzenie; wartość = system oznaczeń **IEC 81346-1 (`=`/`+`/`–`)** + słownik pojęć PL. Do typów/treningu nieprzydatny, miejscami **błędny** (patrz [BŁĘDY]).
- **IEC 60617 (2)** — atlas normatywny, 53 str., ~533 symbole. **Baza** katalogu i `default_description`. Słabo pokrywa PLC/IO i aparaturę producencką.
- **QElectroTech (3)** — biblioteka CAD open-source, **>8000 symboli** (IEC 60617 + **przemysłowe/PLC** + pneumatyka), format **.elmt/XML** (łatwa ekstrakcja), nazwy **wielojęzyczne w tym PL**, licencja **GPL**. **Najlepiej trafia w profil WRT01** i rozwiązuje aliasy PL oraz licencję.

**Rekomendacja (atlas warstwowy):**
1. **IEC 60617** — warstwa bazowa, kanoniczne `iec_ref` i opisy.
2. **QElectroTech** — warstwa przemysłowa: PLC/IO, sieci, napędy, pneumatyka + nazwy PL.
3. **Biblioteki producentów / EPLAN** (w tym `archive/eplan-era-2026-06.zip`) — symbole **konkretnej aparatury handlowej** z WRT01, których normy nie mają.

Następny krok techniczny: ekstrakcja **multi-source** do jednego `config/symbol-reference.yaml` z kanonicznym `symbol_id` + `source_refs[]` (deduplikacja IEC ↔ QET ↔ producent). Bbox-y na WRT01 kontynuować równolegle.

---

## Źródła (tabela)

| # | Nazwa | Typ | Język | Standard | Offline | Zgodność z WRT01 (1–5) |
|---|-------|-----|-------|----------|---------|------------------------|
| 1 | ControlByte — „Jak czytać schematy elektryczne" | blog/HTML | PL | IEC 81346-1 (wzm.) | TAK (zapis HTML) | **3** |
| 2 | **IEC 60617** — atlas symboli | PDF / atlas | EN | **IEC 60617** | TAK (`data/raw/IEC60617.pdf`) | **4** |
| 3 | **QElectroTech** — biblioteka symboli | CAD / open-source | PL/wieloj. | IEC 60617 + przemysł | TAK (repo do pobrania) | **5** |

---

## Ocena szczegółowa (per źródło)

### Źródło 1 — ControlByte „Jak czytać schematy elektryczne"

**Co zawiera (zakres merytoryczny):**

- Po co czytać schematy (diagnostyka, bezpieczeństwo, projektowanie)
- Podstawowe elementy: linie przewodów (ciągła = zasilanie/sygnał, przerywana = PE), węzły/złączki
- Symbole opisane słownie: przełącznik, przekaźnik (cewka + styki), stycznik, bezpiecznik, rezystor
- **Adresy krosowe** — odnośniki połączeń między stronami dokumentacji
- **Linie potencjałowe** — poziomy napięć (+12V, +24V, GND)
- **System oznaczeń IEC 81346-1:** `=` FUNKCJA, `+` LOKALIZACJA, `–` ELEMENT (np. `-M1`, `-K2`, `+RG1`)
- Wzmianka o SEE Electrical (układ zmiany kierunku obrotów) — ilustracja, nie dane

**Format użyteczności:** głównie tekst + kilka grafik poglądowych (jpg/png) i jedna tabela „element rzeczywisty → symbol". To **nie** jest usystematyzowany atlas symboli.

**Macierz oceny (1–5):**

| Kryterium | Ocena | Uzasadnienie |
|-----------|:-----:|--------------|
| Przydatność dla oznaczającego (Filip mniej pisze) | **2** | Brak gotowych opisów do wklejenia; daje tylko ramy pojęciowe (=/+/–, krosy) |
| Przydatność dla treningu YOLO | **1** | Brak atlasu — kilka grafik poglądowych, niespójny styl, za mało klas |
| Przydatność dla walidacji | **3** | System =/+/–, adresy krosowe i linie potencjałowe → reguły „co obok czego", parsowanie tagów |
| Koszt integracji | **niski** | Tekst PL, ręczny wyciąg pojęć do YAML; nic do pobrania/przetwarzania masowo |
| Ryzyko | **średnie** | Błędy merytoryczne w opisach symboli (niżej); materiał marketingowy kursu, nie normatywny |

**Zgodność z WRT01: 3/5** — ten sam **język oznaczeń** (IEC 81346-1, tagi `–`), ale **brak** konkretnej biblioteki symboli i typów, które realnie występują na WRT01.

#### [BŁĘDY] / [RYZYKO] merytoryczne w treści — nie propagować do katalogu

1. **[BŁĄD]** „Symbol bezpiecznika to linia przerywana" — niepoprawne. Wg IEC 60617 bezpiecznik to **prostokąt** (z linią/kreską przez środek), nie linia przerywana.
2. **[BŁĄD]** „Przełącznik… linia przerywana, która przecina dwie linie połączeń" — mylące; linia przerywana to zwykle **sprzężenie mechaniczne** styków, a nie sam symbol przełącznika.
3. **[RYZYKO]** Symbole opisane wyłącznie słownie, bez jednoznacznej grafiki referencyjnej → przy automatycznym streszczeniu łatwo o halucynację typu symbolu.
4. **[RYZYKO]** Źródło komercyjne (lejek na kurs) — traktować jako popularyzację, nie jako referencję normatywną.

**Wniosek dla źródła 1:** używać do **terminologii i systemu oznaczeń**, NIE jako źródła kształtów symboli ani opisów typów. Każdy opis symbolu z tego tekstu wymaga weryfikacji z IEC 60617.

---

### Źródło 2 — IEC 60617 (atlas symboli, PDF)

**Co zawiera:** 53 strony, ~**533 osadzone grafiki** symboli. Każda strona = tabela **IEC SYMBOL | IEC DESCRIPTION | COMMENTS**. Opisy i komentarze po **EN**. To norma-referencja symboli graficznych — autorytatywny język symboli, ten sam, na którym oparty jest WRT01.

**Pokrycie typów (zweryfikowane skanem treści) — kluczowe dla WRT01:**

| Typ urządzenia | Strony (PDF) |
|----------------|--------------|
| Bezpieczniki (fuse) | 17 |
| Styczniki (contactor) | 11, 14 |
| Przekaźniki (relay) | 16, 17, 52 |
| Wyłączniki / circuit breaker | 11, 14 |
| Rozłączniki / disconnector | 11, 14, 15, 17, 53 |
| Łączniki / switch | 11–15, 17, 22, 23 |
| Styki zwierne/rozwierne (make/break) | 12, 13, 14 |
| Silniki (motor) | 8, 10, 16, 31–33, 48 |
| Transformatory | 16, 22, 34–40 |
| Zaciski / terminal | 1, 2, 3, 11, 21, 52 |
| Uziemienia (earth/ground) | 11, 17, 20, 52, 53 |
| Rezystory, kondensatory, diody, tranzystory, lampy | 25–30, 43, 46 |

**Macierz oceny (1–5):**

| Kryterium | Ocena | Uzasadnienie |
|-----------|:-----:|--------------|
| Przydatność dla oznaczającego | **4** | Realne `default_description` per typ; minus: opisy EN → trzeba warstwy aliasów PL |
| Przydatność dla treningu YOLO | **4** | ~533 crop-y symboli jako klasy/syntetyka; minus: symbole **idealne** ≠ rendering skanu (domain gap) — wymaga augmentacji |
| Przydatność dla walidacji | **4** | Kanoniczna semantyka symboli + reguły „styk zwierny/rozwierny", topologia |
| Koszt integracji | **średni** | Ekstrakcja OK, ale **parowanie grafika ↔ opis** nietrywialne (patrz [RYZYKO]) |
| Ryzyko | **niskie–średnie** | EN-only; alignment obraz/tekst; idealne symbole vs skan |

**Zgodność z WRT01: 4/5** — ten sam normatywny język symboli (IEC). Minus za: opisy EN (WRT01 PL) oraz brak oznaczeń producenckich/handlowych aparatury (Finder, Schneider itp.).

#### [RYZYKO] integracyjne — do rozwiązania w prompcie implementacyjnym

1. **[RYZYKO] Parowanie obraz ↔ opis.** W PDF warstwa grafiki (533 obr.) i warstwa tekstu (~905 linii) są **rozdzielne**; `extract_text` nie zachowuje przypisania wiersza do symbolu. Potrzebna **ekstrakcja z koordynatami** (np. pozycje obrazów + bboxy tekstu, parowanie po współrzędnej Y w wierszu tabeli). Bez tego mapowanie symbol→nazwa będzie błędne.
2. **[RYZYKO] Domain gap dla YOLO.** Symbole w atlasie są czyste/wektorowe; WRT01 to skan/rendering o innej grubości linii, szumie, skali. Crop-y atlasu nadają się na **syntetykę / pretraining / walidację klas**, ale model i tak wymaga realnych bboxów z WRT01.
3. **[RYZYKO] Język.** Opisy EN — `aliases_pl` trzeba dołożyć ręcznie/półautomatycznie; ControlByte (źródło 1) pomaga jako słownik PL pojęć.
4. **[RYZYKO] Licencja.** IEC 60617 to treść normatywna — sprawdzić warunki redystrybucji crop-ów, jeśli atlas miałby trafić do repo publicznego. **[do potwierdzenia przez Filipa]**

**Wniosek dla źródła 2:** **fundament katalogu typów**. Realna droga: ekstrakcja layout-aware → `config/symbol-reference.yaml` (id, iec_ref, default_description EN + aliases_pl, crop PNG). Trening: crop-y jako baza syntetyki, ale priorytet to bboxy z WRT01.

---

## Mapowanie na SchemaGen

Co realnie pokrywa potrzeby — i skąd:

| Potrzeba | Ze schematu WRT01 (must) | Źródło referencyjne (nice) | ControlByte (1) | IEC 60617 (2) |
|----------|--------------------------|----------------------------|:---------------:|:-------------:|
| Pozycja bbox | ✓ (labeler) | — | — | — |
| Tag instancji (`-11`, `-K1`) | OCR / labeler | składnia IEC 81346-1 | **Częściowo** (=/+/–) | — |
| Typ urządzenia (fuse, contactor…) | YOLO / dopasowanie | atlas symboli | NIE | **TAK** (~533 symbole) |
| Opis / definicja typu | dziś ręcznie | atlas → katalog | Słabo (z błędami) | **TAK** (EN, +aliasy PL) |
| Trening YOLO (obrazy) | bboxy WRT01 | crop-y symboli / syntetyka | NIE | **Częściowo** (domain gap) |
| Połączenia elektryczne | LineTracer + graf | reguły walidacji | Częściowo | **TAK** (semantyka styków) |
| Bloki funkcjonalne (RUPS1…) | tylko projekt | częściowo teoria | NIE | NIE |

Wniosek: **ControlByte** zasila warstwę tagów/słownik PL. **IEC 60617** zasila **typy, opisy, walidację** i częściowo trening — to brakujący filar katalogu.

---

## Proponowany format bazy symboli

Propozycja (do akceptacji Cursor — **nie implementować w 007**). Rozdzielamy **bibliotekę typów** (atlas, stabilna) od **instancji** (labeler, `element-catalog.yaml`).

```yaml
# config/symbol-reference.yaml  (PROPOZYCJA — nie implementuj bez zgody Cursor)
meta:
  standard: "IEC 60617 / PN-EN 60617"   # atlas symboli
  tag_standard: "IEC 81346-1"           # =FUNKCJA +LOKALIZACJA -ELEMENT
symbols:
  - id: fuse_disconnector
    iec_ref: "IEC 60617 S00289"          # ref do normy/atlasu
    yolo_class: element                  # spójne z config/symbol-classes.yaml
    aliases_pl: ["rozłącznik bezpiecznikowy", "bezpiecznik"]
    tag_prefix: "F"                       # typowy człon -F..
    default_description: "<z atlasu, NIE z blogu>"
    atlas_crop: "data/atlas/fuse_disconnector.png"   # opcjonalny crop do treningu
    source_refs: ["controlbyte#oznaczenia"]          # skąd pojęcie, nie kształt
  - id: contactor
    iec_ref: "..."
    yolo_class: element
    aliases_pl: ["stycznik"]
    tag_prefix: "K"
    default_description: "..."
```

**Relacja do istniejących plików:**

- `config/element-catalog.yaml` — **instancje** z labelera (`-11` na p013). Łączyć przez `symbol_id` → wpis w `symbol-reference.yaml`.
- `config/symbol-classes.yaml` — klasa YOLO `element`. `symbol-reference.yaml.symbols[].yolo_class` musi się zgadzać.
- `blocks/*.json` — szablony **obwodów** (RUPS1…), nie pojedyncze symbole. Bez zmian; symbol-reference działa o poziom niżej.
  `default_description` w przykładzie ciągniemy z **IEC 60617** (źródło 2), `aliases_pl` ze słownika PL (źródło 1), `atlas_crop` = crop z `IEC60617.pdf`.
- `archive/eplan-era-2026-06.zip` — **schodzi na drugi plan**. Atlas normatywny (IEC 60617) już mamy. EPLAN warto wykorzystać dopiero gdyby brakowało konkretnych symboli aparatury producenckiej z WRT01 — wtedy jednorazowo, offline.

---

## Rekomendacje i następne kroki — „Co robimy"

1. **Bbox-y na WRT01: TAK, kontynuować.** Schematu nic nie zastąpi (pozycje, tagi, topologia). Cel: dokończyć 3 oznaczone (p013–p015), potem 5–10 reprezentatywnych stron pod różnorodność typów — nie wszystkie 77 naraz.
2. **Priorytet #1 = IEC 60617 (źródło 2).** Atlas jest w ręku — droga to **layout-aware ekstrakcja** (parowanie crop ↔ opis ↔ komentarz) → `config/symbol-reference.yaml` + crop-y PNG do `data/atlas/`. ControlByte zostaje jako słownik PL pojęć i kontrola terminologii.
3. **Skrócony workflow labelera.** Filip wpisuje tylko **tag instancji** (np. `-11`) + wskazuje **symbol_id** z listy z atlasu; opis/typ ciągnie się z `symbol-reference.yaml`. Koniec ręcznego przepisywania opisów.
4. **Co odkładamy.** Pełne ręczne rysowanie linii — czekamy na auto-tracer (003-line-tracer). EPLAN z archiwum — tylko gdy zabraknie symboli producenckich. Streszczanie wideo w runtime — odpada (offline). Encyklopedyczne opisy w bboxach — zastąpione katalogiem.
5. **Następny prompt implementacyjny (propozycja dla Cursor):**
   - **008-iec60617-atlas-extract** *(implementacja, offline)* — layout-aware ekstrakcja `data/raw/IEC60617.pdf`: pozycje grafik + bboxy tekstu → parowanie po wierszu tabeli → `data/atlas/<id>.png` + `config/symbol-reference.yaml` (id, iec_ref, default_description EN, aliases_pl, atlas_crop). Rozwiązuje [RYZYKO] alignmentu. Bez cloud API.
   - następnie **009-bbox→symbol_id w labelerze** — wybór `symbol_id` z atlasu przy bboxie; katalog dostarcza opis/typ.

---

## Otwarte pytania do Filipa

1. **Ekstrakcja atlasu:** akceptujesz prompt **008-iec60617-atlas-extract** (parowanie symbol↔opis + `symbol-reference.yaml`) jako następny krok implementacyjny dla Cursor?
2. **Aliasy PL:** dla ~533 symboli opisy są EN. Tłumaczymy **wszystkie**, czy tylko podzbiór realnie występujący na WRT01 (szybciej, mniej szumu)? Sugeruję podzbiór.
3. **Zakres bbox:** zostajemy na p013–p015, czy dobieramy kolejne strony pod różnorodność typów? Które stacje/obwody są najważniejsze?
4. **`tag_prefix`:** czy WRT01 trzyma konwencję członów literowych (`-F` bezpiecznik, `-K` przekaźnik/stycznik, `-M` silnik, `-Q` wyłącznik)? Zdeterminuje regułę walidacji tag → typ.
5. **[do potwierdzenia] Licencja IEC 60617** — czy crop-y symboli mogą trafić do repo (zwł. jeśli publiczne)? Jeśli nie — trzymamy atlas tylko lokalnie (`data/raw`, `data/atlas` w `.gitignore`).
