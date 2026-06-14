# Analiza źródeł wiedzy — schematy elektryczne

**Data:** 2026-06-14
**Autor:** Claude (ZW) + Filip
**Wersja:** 4 (runda 4 — werdykt o archiwum EPLAN + strategia treningu Siemens-first)
**Profil WRT01 (Filip):** sterowniki **GE Vernova**, złączki/IO **Phoenix Contact**; trening na komponentach **Siemens**
**Prompt:** `sync/prompts/007-sources-analysis.md`

---

## Streszczenie wykonawcze

Trzy źródła tworzące **warstwowy atlas**. Profil WRT01 (PLC/IO/sieci + aparatura producencka) oznacza, że **żadne pojedyncze źródło nie wystarczy** — IEC 60617 to podstawa normatywna, ale modułów PLC i symboli handlowych prawie nie ma.

- **ControlByte (1)** — wprowadzenie; wartość = system oznaczeń **IEC 81346-1 (`=`/`+`/`–`)** + słownik pojęć PL. Do typów/treningu nieprzydatny, miejscami **błędny** (patrz [BŁĘDY]).
- **IEC 60617 (2)** — atlas normatywny, 53 str., ~533 symbole. **Baza** katalogu i `default_description`. Słabo pokrywa PLC/IO i aparaturę producencką.
- **QElectroTech (3)** — biblioteka CAD open-source, **8732 symbole** (pobrane; pełny raport `docs/qet-library-report.md`), format **.elmt/XML**, licencja **GPL**. Najsilniejsza warstwa **generyczna** (allpole, IEC 60617, WAGO/Siemens). [KOREKTA] PL tylko **~34%** plików (nie „za darmo"), a **aparatura WRT01 — GE Vernova (brak) i Phoenix Contact (13, rdzeń brak)** — wymaga osobnej warstwy producenta.

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

**Wniosek dla źródła 2:** **fundament katalogu typów** (warstwa bazowa). Realna droga: ekstrakcja layout-aware → `config/symbol-reference.yaml`. Słabo pokrywa PLC/IO i aparaturę producencką → uzupełnić QET i bibliotekami producentów.

---

### Źródło 3 — QElectroTech (biblioteka symboli CAD)

**Co zawiera:** open-source'owy program do schematów elektrycznych z **oficjalną kolekcją >8000 symboli** (`qelectrotech-elements`). Obejmuje folder **IEC 60617** oraz obszerne zbiory **przemysłowe: PLC/IO, styczniki, przekaźniki, napędy/falowniki, czujniki, pneumatykę**. Każdy symbol to plik **`.elmt` (XML)** z geometrią wektorową i **nazwami wielojęzycznymi (w tym PL)**. Licencja **GNU/GPL**.

**Dlaczego najlepiej trafia w WRT01:** profil = PLC/IO/sieci + aparatura producencka — dokładnie to, czego IEC 60617 nie ma. Plus rozwiązuje dwie bolączki źródła 2: **aliasy PL** (nazwy już są PL) i **licencję** (GPL zamiast normy zamkniętej).

**Macierz oceny (1–5):**

| Kryterium | Ocena | Uzasadnienie |
|-----------|:-----:|--------------|
| Przydatność dla oznaczającego | **5** | Tysiące symboli + nazwy PL → gotowe `symbol_id` i opisy dla labelera |
| Przydatność dla treningu YOLO | **4** | Wektory → renderowalne crop-y i **syntetyka** (skalowanie, szum); wciąż domain gap vs skan |
| Przydatność dla walidacji | **4** | Spójna semantyka + kategorie (styki, PLC, napędy) jako reguły |
| Koszt integracji | **niski–średni** | `.elmt` to XML — parsowanie proste; render SVG→PNG dla crop-ów |
| Ryzyko | **niskie** | GPL (atrybucja!); duplikaty z IEC 60617 do deduplikacji |

**Zgodność z WRT01: 5/5** — najszerszy zakres + PL + przemysł. Minus jedyny: symbole **generyczne**, nie konkretne modele producenckie (te z biblioteki producenta — patrz luka niżej).

#### [RYZYKO] / uwagi

1. **[RYZYKO] GPL — atrybucja/copyleft.** Symbole QET są na GPL. Użycie crop-ów/derywatów w SchemaGen wymaga zachowania atrybucji i sprawdzenia, czy nie „zaraża" licencji projektu. **[do potwierdzenia przez Filipa]** — jak licencjonowany jest sam SchemaGen.
2. **[RYZYKO] Deduplikacja IEC ↔ QET.** Ten sam symbol w obu źródłach → potrzebny kanoniczny `symbol_id` i `source_refs[]`, inaczej dublet klas YOLO.
3. **Pobranie = osobny krok** (repo `qelectrotech-elements`), nie w 007. Runtime offline zachowany — pobieramy raz, parsujemy lokalnie.

**Wniosek dla źródła 3:** **warstwa przemysłowa atlasu** i główne źródło aliasów PL. Razem z IEC 60617 pokrywa większość WRT01; resztę (konkretne modele) dobiera biblioteka producenta.

---

## Luka pokrycia — PLC/IO/sieci + aparatura producentów (profil WRT01)

Filip wskazał, że dominują **PLC/IO/sieci** i **aparatura konkretnych producentów**. Stan pokrycia:

| Kategoria z WRT01 | IEC 60617 | QElectroTech | Biblioteka producenta / EPLAN |
|-------------------|:---------:|:------------:|:-----------------------------:|
| Aparatura łączeniowa (styczniki, bezpieczniki, wyłączniki) | ✓ pełne | ✓ pełne | ✓ modele |
| Styki, przekaźniki, zaciski, uziemienia | ✓ | ✓ | ✓ |
| **Moduły PLC / IO** | ✗ brak | ◐ generyczne | ✓ konkretne (Siemens S7, itp.) |
| **Sieci / magistrale (PROFINET/PROFIBUS)** | ✗ | ◐ częściowo | ✓ |
| **Falowniki / napędy** | ◐ ogólny silnik | ◐ generyczne | ✓ modele |
| **Czujniki przemysłowe (PNP/NPN, IO-Link)** | ◐ | ◐ | ✓ |

**Wniosek:** dla profilu WRT01 **konieczna trzecia warstwa** — biblioteki symboli producentów (EPLAN Data Portal / makra) lub ekstrakcja z `archive/eplan-era-2026-06.zip`. IEC 60617 + QET dają fundament i przemysł generyczny; konkretne moduły PLC i marki dokłada producent.

[RYZYKO] **Nazewnictwo modeli** — symbole producenckie często niosą oznaczenia handlowe (np. „6ES7..."), które nie są symbolem graficznym, lecz tagiem typu. W katalogu rozdzielić **symbol graficzny** (kształt) od **typu handlowego** (pole `product_type`/`order_no`).

---

## Mapowanie na SchemaGen

Co realnie pokrywa potrzeby — i skąd:

| Potrzeba | WRT01 (must) | ControlByte (1) | IEC 60617 (2) | QElectroTech (3) |
|----------|:------------:|:---------------:|:-------------:|:----------------:|
| Pozycja bbox | ✓ (labeler) | — | — | — |
| Tag instancji (`-11`, `-K1`) | OCR / labeler | Częściowo (=/+/–) | — | — |
| Typ urządzenia (fuse, contactor…) | YOLO / dopas. | NIE | **TAK** (~533) | **TAK** (>8000) |
| Opis / definicja typu | dziś ręcznie | Słabo (błędy) | TAK (EN) | **TAK (PL)** |
| Trening YOLO (obrazy) | bboxy WRT01 | NIE | Częściowo | **TAK** (wektor→syntetyka) |
| PLC/IO, sieci, napędy | — | NIE | Słabo | **TAK** (+producent) |
| Połączenia elektryczne | LineTracer + graf | Częściowo | TAK (styki) | TAK |
| Bloki funkcjonalne (RUPS1…) | tylko projekt | NIE | NIE | NIE |

Wniosek: **ControlByte** = tagi + słownik PL. **IEC 60617** = baza normatywna typów/opisów. **QElectroTech** = warstwa przemysłowa (PLC/IO/napędy) + aliasy PL + syntetyka treningowa. Konkretne modele producenckie → trzecia warstwa (EPLAN/producent).

---

## Proponowany format bazy symboli

Propozycja (do akceptacji Cursor — **nie implementować w 007**). Rozdzielamy **bibliotekę typów** (atlas, stabilna) od **instancji** (labeler, `element-catalog.yaml`).

```yaml
# config/symbol-reference.yaml  (PROPOZYCJA — nie implementuj bez zgody Cursor)
meta:
  standard: "IEC 60617 / PN-EN 60617"   # atlas symboli
  tag_standard: "IEC 81346-1"           # =FUNKCJA +LOKALIZACJA -ELEMENT
  sources:                              # warstwy atlasu
    - {id: iec60617,  type: norm,   ref: "data/raw/IEC60617.pdf"}
    - {id: qet,       type: gpl_lib, ref: "qelectrotech-elements"}
    - {id: eplan_era, type: vendor, ref: "archive/eplan-era-2026-06.zip"}
symbols:
  - id: fuse_disconnector              # kanoniczny symbol_id (dedup między źródłami)
    iec_ref: "IEC 60617 S00289"
    yolo_class: element                # spójne z config/symbol-classes.yaml
    aliases_pl: ["rozłącznik bezpiecznikowy", "bezpiecznik"]
    tag_prefix: "F"                     # typowy człon -F..
    default_description: "<z IEC 60617 / QET>"
    atlas_crop: "data/atlas/fuse_disconnector.png"
    source_refs: ["iec60617#p17", "qet#electric/fuse"]   # skąd kształt+opis
  - id: plc_io_module                  # przykład: pokrywa QET/producent, nie IEC
    iec_ref: null
    yolo_class: element
    aliases_pl: ["moduł we/wy PLC", "karta IO"]
    tag_prefix: "A"
    product_type: "6ES7..."            # oznaczenie handlowe ≠ symbol graficzny
    default_description: "<z QET / biblioteki producenta>"
    atlas_crop: "data/atlas/plc_io_module.png"
    source_refs: ["qet#plc", "eplan_era#siemens"]
```

**Relacja do istniejących plików:**

- `config/element-catalog.yaml` — **instancje** z labelera (`-11` na p013). Łączyć przez `symbol_id` → wpis w `symbol-reference.yaml`.
- `config/symbol-classes.yaml` — klasa YOLO `element`. `symbol-reference.yaml.symbols[].yolo_class` musi się zgadzać.
- `blocks/*.json` — szablony **obwodów** (RUPS1…), nie pojedyncze symbole. Bez zmian; symbol-reference działa o poziom niżej.
  `default_description` w przykładzie ciągniemy z **IEC 60617** (źródło 2), `aliases_pl` ze słownika PL (źródło 1), `atlas_crop` = crop z `IEC60617.pdf`.
- `archive/eplan-era-2026-06.zip` — **[WERDYKT] NIE jest źródłem symboli.** Przejrzane (71 plików): to historyczny **kod ery EPLAN** — add-in C# (`addin/*.cs`), baza wiedzy o API EPLAN (`eplan-kb/`), skrypty, logi. **Zero symboli/makr.** Wartość: tylko referencja, *jakich typów plików szukać* u producenta (patrz niżej). Wątek atlasu z tego archiwum — zamknięty.

---

## Archiwum EPLAN + typy plików symboli producenta

Z przeglądu `archive/eplan-era-2026-06.zip` (kod + baza wiedzy API EPLAN) wynika, **jakich plików szukać**, gdy będziemy pozyskiwać symbole producentów (Siemens, Phoenix, GE):

| Rozszerzenie | Co to | Wartość dla atlasu |
|--------------|-------|--------------------|
| **`.edz`** | EPLAN Data Portal — pakiet artykułu (część + makro + symbol + 3D) | **Najbogatsze** — jedno pobranie = symbol + dane części |
| **`.ema`** | makro okna (placed circuit / reprezentacja urządzenia) | graficzny układ symboli — dobre do crop-ów i wzorców |
| **`.ems`** | makro symbolu | pojedynczy symbol |
| **`.xml`** | eksport bazy części (parts master data) | opisy/typy handlowe, bez grafiki |

Źródło symboli producenta = **EPLAN Data Portal** (`.edz` per artykuł) lub biblioteki producenta. To **nie jest** to archiwum — archiwum tylko nazywa te formaty.

## Strategia treningu — Siemens-first (decyzja Filipa)

Filip: *można użyć innych komponentów do uczenia — schematy z komponentami Siemensa*. To rozwiązuje lukę GE Vernova:

1. **Trenuj na schematach z aparaturą Siemens** — QET ma **452 symbole Siemens** + 1982 WAGO + IEC 60617 generyczne. Pokrycie pełne, materiał referencyjny obfity (Siemens publikuje makra EPLAN/Data Portal masowo).
2. **GE Vernova / Phoenix Contact (rdzeń)** — odkładamy. Detektor uczy się **generycznych klas** (`relay`, `fuse`, `terminal_block`, `plc_io_module`), nie konkretnych modeli; symbole GE/Phoenix dochodzą później jako `.edz` z Data Portal, mapowane na te same klasy.
3. **Konsekwencja:** SchemaGen nie musi czekać na symbole GE — start na Siemens + generyki, generalizacja przez klasy. To skraca drogę do pierwszego działającego detektora.

## Rekomendacje i następne kroki — „Co robimy"

1. **Bbox-y na WRT01: TAK, kontynuować.** Schematu nic nie zastąpi (pozycje, tagi, topologia). Cel: dokończyć 3 oznaczone (p013–p015), potem 5–10 reprezentatywnych stron pod różnorodność typów — nie wszystkie 77 naraz.
2. **Atlas warstwowy** zamiast jednego źródła:
   - **Warstwa 1 — IEC 60617** (`data/raw/IEC60617.pdf`): baza normatywna, `iec_ref` + opisy. Ekstrakcja layout-aware (parowanie crop ↔ opis).
   - **Warstwa 2 — QElectroTech** (repo `qelectrotech-elements`): PLC/IO, sieci, napędy, pneumatyka + **nazwy PL** + wektory pod syntetykę. Parsowanie `.elmt` (XML) → crop SVG/PNG.
   - **Warstwa 3 — producent / EPLAN** (`archive/eplan-era-2026-06.zip` lub Data Portal): konkretne moduły PLC i marki z WRT01.
   - Spina je jeden `config/symbol-reference.yaml` z kanonicznym `symbol_id` + `source_refs[]` (dedup).
3. **Skrócony workflow labelera.** Filip wpisuje tylko **tag instancji** (np. `-11`) + wskazuje **symbol_id** z atlasu; opis/typ ciągnie się z `symbol-reference.yaml`. Koniec ręcznego przepisywania opisów.
4. **Co odkładamy.** Pełne ręczne rysowanie linii — czekamy na auto-tracer (003-line-tracer). Streszczanie wideo w runtime — odpada (offline). Encyklopedyczne opisy w bboxach — zastąpione katalogiem. ControlByte → tylko słownik PL + kontrola terminologii.
5. **Następny prompt implementacyjny (propozycja dla Cursor):**
   - **008-symbol-atlas-extract** *(implementacja, offline, multi-source)* — (a) layout-aware ekstrakcja `IEC60617.pdf` (parowanie po wierszu tabeli → [RYZYKO] alignment), (b) parser `.elmt` QET (XML → nazwy PL + render PNG), (c) scalanie do `config/symbol-reference.yaml` z dedup `symbol_id`. Pobranie QET = krok wstępny. Bez cloud API.
   - następnie **009-bbox→symbol_id w labelerze** — wybór `symbol_id` z atlasu przy bboxie; katalog dostarcza opis/typ.

---

## Otwarte pytania do Filipa

1. **Pobranie QET:** mam pobrać repo `qelectrotech-elements` (osobny krok) i potwierdzić realne pokrycie PLC/IO przed pisaniem promptu 008?
2. **Licencje [do potwierdzenia]:** (a) jak licencjonowany jest **SchemaGen** — kompatybilny z **GPL** (QET)? (b) czy crop-y **IEC 60617** mogą trafić do repo, czy tylko lokalnie (`data/atlas` w `.gitignore`)?
3. **Aparatura producencka:** którzy producenci dominują na WRT01 (Siemens? Schneider? Eaton? Finder?) — zdeterminuje warstwę 3 i czy sięgać po `archive/eplan-era-2026-06.zip`.
4. **Zakres bbox:** zostajemy na p013–p015, czy dobieramy kolejne strony pod różnorodność typów? Które stacje/obwody najważniejsze?
5. **`tag_prefix`:** czy WRT01 trzyma konwencję członów literowych (`-F` bezpiecznik, `-K` przekaźnik/stycznik, `-M` silnik, `-Q` wyłącznik, `-A` moduł/PLC)? Zdeterminuje regułę walidacji tag → typ.
