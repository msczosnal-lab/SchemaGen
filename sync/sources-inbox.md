# Skrzynka źródeł — Filip + Claude

> Filip dopisuje linki, pliki, notatki. Claude czyta przy promptcie **007-sources-analysis**.

---

## Źródła do oceny

*(Filip: wklej poniżej — jedno źródło = jedna sekcja)*

### Szablon wpisu

```markdown
### [Nazwa / tytuł]
- **Typ:** wideo | PDF | strona | atlas symboli | norma | inne
- **URL / ścieżka:** …
- **Język:** PL / EN / …
- **Standard:** IEC / PN / producent / ogólne / nie wiem
- **Dlaczego wybrałem:** …
- **Notatki:** (opcjonalnie)
```

---

### Jak czytać schematy elektryczne – praktyczny poradnik (ControlByte)
- **Typ:** strona / blog (HTML, zapis offline)
- **URL / ścieżka:** https://www.controlbyte.pl/blog/jak-czytac-schematy-elektryczne/ — lokalnie: `uploads/Jak czytać schematy elektryczne - praktyczny poradnik.html`
- **Język:** PL
- **Standard:** IEC ogólne; jawnie wymienia **IEC 81346-1** (oznaczenia =/+/-)
- **Dlaczego wybrałem:** poradnik o czytaniu schematów, symbole + system oznaczeń
- **Notatki:** poziom wprowadzający; autor Szymon Adamek; data 2024-09, akt. 2026-01. Ocena → `docs/knowledge-sources-analysis.md`

### IEC 60617 — atlas symboli (PDF)
- **Typ:** atlas symboli (PDF)
- **URL / ścieżka:** `data/raw/IEC60617.pdf`
- **Język:** EN (opisy), symbole graficzne
- **Standard:** **IEC 60617** (norma symboli graficznych)
- **Dlaczego wybrałem:** atlas symboli — typy urządzeń do katalogu i treningu
- **Notatki:** 53 strony, ~533 osadzone grafiki symboli; tabela SYMBOL | DESCRIPTION | COMMENTS. Pokrywa: bezpieczniki, styczniki, przekaźniki, wyłączniki, rozłączniki, silniki, transformatory, styki, zaciski, uziemienia.

### QElectroTech — biblioteka symboli (QET elements)
- **Typ:** biblioteka symboli CAD (open-source)
- **URL / ścieżka:** https://qelectrotech.org/ · repo: https://github.com/qelectrotech/qelectrotech-elements (do pobrania, osobny krok)
- **Język:** wielojęzyczny (w tym **PL**), folder IEC 60617
- **Standard:** IEC 60617 + symbole przemysłowe / **PLC** / pneumatyka
- **Dlaczego wybrałem:** uzupełnia IEC 60617 o PLC/IO/sieci i aparaturę przemysłową (profil WRT01)
- **Notatki:** **8732 symbole** (pobrane 2026-06-14), format **.elmt / XML**, licencja **GNU/GPL**. Pełny raport: `docs/qet-library-report.md`. PL tylko ~34% plików. **GE Vernova: brak; Phoenix Contact: 13 (rdzeń brak)** → warstwa producenta osobno.

### EPLAN Electric P8 — dane lokalne (instalacja)
- **Typ:** biblioteka symboli + makra producentów + baza artykułów
- **URL / ścieżka:** `C:\Users\Public\EPLAN\Data\`
- **Język:** PL (interfejs), symbole IEC
- **Standard:** **IEC** (głównie), też GOST, GB, NFPA, PID
- **Dlaczego wybrałem:** lokalna baza symboli tego samego typu co schematy projektowe EPLAN
- **Notatki (przeszukanie Cursor 2026-06-14):**
  - `Symbole\Schemagen\` — **604 pliki**, **22 biblioteki `.sdb`**: `IEC_symbol.sdb` (~26 MB), `IEC_single_symbol.sdb`, topologia IEC, SPECIAL, GRAPHICS (~200 MB łącznie)
  - Format `.eod`/`.eox` = **binarny EPLAN** — nie do runtime Pythona bez eksportera
  - `Makra\Schemagen\` — **854 makra `.ema` (XML)**: Siemens 90, **PXC/Phoenix 61**, Rittal 279, A-B 33, FESTO 48, EPLAN_Macro 135
  - `Artykuły\Schemagen\EPLAN_parts.adb` — baza części (binary)
  - `Definicja funkcji\Schemagen\` — FctDef (semantyka funkcji)
  - **Luka WRT01:** brak makr GE Vernova; Phoenix = numery katalogowe PXC
  - **Ekstrakcja:** batch export z EPLAN P8 → PNG/SVG do `data/symbol-atlas/eplan-iec/`; `.ema` → metadane XML

---

## Aparatura WRT01 (od Filipa, 2026-06-14)
- **Sterowniki:** GE Vernova
- **Złączki/IO:** Phoenix Contact
- Oba słabo/wcale pokryte w QET → potrzebne biblioteki producentów (EPLAN/DTR) jako źródła #4/#5.

---

## Kontekst projektu (dla Claude)

- Schemat analizy: **SchematWRT01** (77 stron, p013–p089), 3 strony oznaczone bboxami (~259 elementów)
- Oznaczanie: bbox + opis tekstowy; hierarchia bbox w bboxie
- Runtime **offline** — źródła muszą dać się przekuć w lokalny YAML/JSON, nie „link do YouTube w runtime”
- Archiwum EPLAN: `archive/eplan-era-2026-06.zip` — tylko referencja offline, nie runtime API
