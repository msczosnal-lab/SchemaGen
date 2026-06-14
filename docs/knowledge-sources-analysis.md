# Analiza źródeł wiedzy — schematy elektryczne

**Data:** 2026-06-14
**Autor:** Claude (ZW) + Filip
**Wersja:** 1 (runda 1 — 1 źródło)
**Prompt:** `sync/prompts/007-sources-analysis.md`

---

## Streszczenie wykonawcze

Pierwsze źródło (blog ControlByte) to materiał **wprowadzający**, nie atlas symboli ani norma. Jego jedyna realna wartość dla SchemaGen to **potwierdzenie i wyjaśnienie systemu oznaczeń IEC 81346-1 (`=` funkcja / `+` lokalizacja / `–` element)** — który jest dokładnie tym językiem tagów, jakim opisany jest WRT01 (`-11`, `-K1`, `+RG1`). To realnie pomaga przy **parsowaniu i walidacji tagów**, a nie przy rozpoznawaniu typów symboli.

Do dwóch kluczowych potrzeb — **trening YOLO** (obrazy symboli) i **katalog opisów typów** — to źródło jest **nieprzydatne**: ma kilka niskiej jakości grafik i słowne, miejscami **błędne** opisy symboli (patrz [BŁĘDY] niżej). Nie nadaje się na `default_description`.

**Rekomendacja:** użyć ControlByte wyłącznie jako **glosariusza pojęć PL → IEC** (system =/+/–, adresy krosowe, linie potencjałowe). Do typów i treningu potrzebny prawdziwy **atlas symboli IEC 60617 / PN-EN 60617**. Priorytet #1 = pozyskanie takiego atlasu; bbox-y na WRT01 kontynuować równolegle.

---

## Źródła (tabela)

| # | Nazwa | Typ | Język | Standard | Offline | Zgodność z WRT01 (1–5) |
|---|-------|-----|-------|----------|---------|------------------------|
| 1 | ControlByte — „Jak czytać schematy elektryczne" | blog/HTML | PL | IEC 81346-1 (wzm.) | TAK (zapis HTML) | **3** |

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

## Mapowanie na SchemaGen

Co realnie pokrywa potrzeby — i skąd:

| Potrzeba | Ze schematu WRT01 (must) | Ze źródła referencyjnego (nice) | Pokrywa ControlByte? |
|----------|--------------------------|----------------------------------|:--------------------:|
| Pozycja bbox | ✓ (labeler) | — | — |
| Tag instancji (`-11`, `-K1`) | OCR / labeler | reguły składni IEC 81346-1 | **Częściowo** — wyjaśnia =/+/– |
| Typ urządzenia (fuse, contactor…) | YOLO / dopasowanie | atlas symboli | **NIE** (brak atlasu) |
| Opis / definicja typu | dziś ręcznie | podręcznik → katalog | **Słabo** (i z błędami) |
| Połączenia elektryczne | LineTracer + graf | reguły walidacji | **Częściowo** — linie/węzły, krosy, potencjały |
| Bloki funkcjonalne (RUPS1…) | tylko projekt | częściowo teoria | **NIE** |

Wniosek: ControlByte zasila głównie **warstwę tagów/walidacji**, marginalnie **opisy**, **wcale** trening i atlas typów.

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
- `archive/eplan-era-2026-06.zip` — **potencjalnie najlepsze źródło atlasu**: zawiera realne symbole EPLAN tego samego języka co WRT01. Warto **jednorazowo, offline** ocenić ekstrakcję crop-ów symboli + nazw do `data/atlas/` i `symbol-reference.yaml`. **Nie** rozpakowywać do runtime. (Decyzja: osobny prompt — patrz niżej.)

---

## Rekomendacje i następne kroki — „Co robimy"

1. **Bbox-y na WRT01: TAK, kontynuować.** Schematu nic nie zastąpi (pozycje, tagi, topologia). Cel rundy: dokończyć 3 oznaczone (p013–p015), potem dobrać 5–10 reprezentatywnych stron pod różnorodność typów, nie wszystkie 77 na raz.
2. **Priorytet źródła #1: atlas symboli, NIE ten blog.** ControlByte zostaje jako glosariusz pojęć. Realny priorytet = **IEC 60617 / PN-EN 60617** lub **ekstrakcja symboli z `archive/eplan-era-2026-06.zip`** (ten sam język co WRT01 — prawdopodobnie najszybsza droga do atlasu zgodnego 1:1).
3. **Skrócony workflow labelera.** Filip wpisuje tylko **tag instancji** (np. `-11`) + wskazuje **symbol_id** z listy; opis/typ ciągniemy z `symbol-reference.yaml`. Eliminuje ręczne przepisywanie opisów.
4. **Co odkładamy.** Pełne ręczne rysowanie linii — czekamy na auto-tracer (prompt 003-line-tracer). Streszczanie wideo w runtime — odpada (offline). Encyklopedyczne opisy w bboxach — zastąpione katalogiem.
5. **Następny prompt implementacyjny (propozycja dla Cursor):**
   - **008-eplan-atlas-probe** *(research/offline)* — ocena `archive/eplan-era-2026-06.zip`: ile symboli, jaki format, czy da się wyciąć crop + nazwa → szkic `data/atlas/` + `config/symbol-reference.yaml`. Bez runtime API.
   - następnie **009-symbol-reference + bbox→symbol_id** — labeler wybiera `symbol_id`, katalog dostarcza opis/typ.

---

## Otwarte pytania do Filipa

1. **Atlas:** wolisz, żebym najpierw ocenił `archive/eplan-era-2026-06.zip` jako źródło symboli (runda 2 = prompt 008), czy dorzucisz zewnętrzny atlas IEC 60617 (PDF/obrazy)?
2. **Zakres bbox:** zostajemy na p013–p015, czy dobieramy kolejne strony pod różnorodność typów (które stacje/obwody są najważniejsze)?
3. **Więcej źródeł do oceny w tej rundzie?** (np. norma PN-EN 60617, karty katalogowe producentów aparatury z WRT01 — Finder, Schneider, Eaton)
4. **`tag_prefix`:** czy WRT01 trzyma konwencję członów literowych (`-F` bezpiecznik, `-K` przekaźnik/stycznik, `-M` silnik, `-Q` wyłącznik)? To zdeterminuje regułę walidacji tag → typ.
