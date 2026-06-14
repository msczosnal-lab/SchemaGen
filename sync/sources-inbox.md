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

### Schemat WRT01 (PDF — główny projekt ground truth)
- **Typ:** PDF schematu elektrycznego + wyekstrahowane strony PNG
- **URL / ścieżka:** `data/raw/SchematWRT01.pdf` + `data/raw/SchematWRT01_p013.png` … `p089.png` (**77 stron**)
- **Język:** PL (tagi, opisy)
- **Standard:** IEC 81346-1 (tagi), symbole IEC
- **Dlaczego wybrałem:** ground truth bboxów, linii, tagów instancji — **obowiązkowe**
- **Notatki:** p013–p015 oznaczone bboxami. **Filip NIE ma** wersji EPLAN. Labeler czyta **PNG** z `data/raw/`.

### Korpus schematów PDF — inne projekty (`sync/sources/`)

Filip dodał **4 PDF + 1 skrót** (inwentaryzacja: [`sync/sources/MANIFEST.json`](sources/MANIFEST.json)).

| Plik | Projekt | Strony | ~MB | Rola |
|------|---------|-------:|----:|------|
| `20_A_022_PL_Norblin_Cars_2022-06-26.pdf` | Norblin Cars (A022) | 199 | 6,9 | trening / różnorodność producentów |
| `22_A_153_PL_Adamed_AGV_SA2_20250706.pdf` | Adamed AGV SA2 (A153) | 200 | 6,9 | j.w. |
| `22_A_153_PL_Adamed_INTEROL_SA1_20250729.pdf` | Adamed INTEROL SA1 (A153) | 99 | 2,9 | j.w. |
| `25_A_229_PL5_19012026.pdf` | Stanley 229 / PL5 (A229) | 25 | 0,9 | j.w. |
| `24_A_068_PL5_29102024 schemat PL5.lnk` | skrót OneDrive (PC ZW) | — | — | **niedziałający lokalnie** — skopiuj PDF jeśli potrzebny |

**Razem:** 523 strony PDF (wektor/tekst — dobry OCR). PDF-y w `.gitignore`; w repo tylko `MANIFEST.json`.

- **Typ:** PDF schematów projektowych (mix producentów / instalacji)
- **Ścieżka:** `sync/sources/*.pdf`
- **Język:** PL
- **Standard:** IEC + aparatura producencka
- **Dlaczego:** warstwa 3 atlasu + **dodatkowy korpus treningowy** (Siemens-first, klasy generyczne); prompt **008c** / ewent. konwersja PDF→PNG do labelera
- **Notatki:** to **nie** zastępuje WRT01 — osobny primary (`data/raw/`). Do labelera trzeba rasteru (`data/raw/*.png`) — osobny krok importu.

### ~~EPLAN Electric P8 — dane lokalne~~ *(NIE DOTYCZY Filipa)*
- Wpis z przeszukania Cursor — **Filip nie ma dostępu** do projektu WRT01 w EPLAN. Nie używać jako źródło runtime.

---

## Aparatura WRT01 (od Filipa, 2026-06-14)
- **Sterowniki:** GE Vernova
- **Złączki/IO:** Phoenix Contact
- Oba słabo/wcale pokryte w QET → potrzebne biblioteki producentów (EPLAN/DTR) jako źródła #4/#5.

---

## Kontekst projektu (dla Claude)

- **Primary:** SchematWRT01 — 77 stron PNG w `data/raw/`, bboxy p013–p015
- **Dodatkowy korpus:** `sync/sources/` — 4 PDF, **523 strony** (`sync/sources/MANIFEST.json`); Norblin / Adamed / PL5
- Oznaczanie: bbox + opis tekstowy; hierarchia bbox w bboxie
- Runtime **offline** — źródła muszą dać się przekuć w lokalny YAML/JSON
- Archiwum EPLAN: `archive/eplan-era-2026-06.zip` — tylko referencja offline, nie runtime API
