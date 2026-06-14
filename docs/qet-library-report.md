# Raport: biblioteka symboli QElectroTech (QET)

**Data:** 2026-06-14
**Autor:** Claude (ZW)
**Źródło:** repo `qelectrotech/qelectrotech-elements` (git clone --depth 1, 2026-06-14)
**Licencja:** GNU/GPL
**Kontekst:** ocena warstwy przemysłowej atlasu dla SchemaGen — patrz `docs/knowledge-sources-analysis.md`

---

## Podsumowanie

Biblioteka zawiera **8 732 symbole** (`.elmt`, format XML), 115 MB. To realny, szeroki atlas przemysłowy — najsilniejsza warstwa generyczna dla SchemaGen. **Ale dla konkretnej aparatury WRT01 (GE Vernova, Phoenix Contact) pokrycie jest słabe lub zerowe** — te symbole trzeba pozyskać z bibliotek producentów (EPLAN/DTR).

**Trzy wnioski operacyjne:**

1. **Warstwa generyczna IEC + przemysł: bardzo dobra.** ~942 symbole „allpole" (typy łączeniowe, czujniki, przekaźniki) + 912 z folderu EN 60617 + tysiące artykułów producenckich. Świetna baza pod `symbol_id`, opisy i syntetykę treningową YOLO.
2. **GE Vernova: BRAK.** Sterowniki GE nieobecne (jest tylko softstart ASTAT XT). → warstwa producenta konieczna.
3. **Phoenix Contact: 13 symboli, rdzeń produktu (listwy/złączki) brak.** → warstwa producenta konieczna.

[KOREKTA do analizy v3] Nazwy **PL są w ~34% plików** (2 986 / 8 732), nie wszędzie. Folder normatywny EN 60617 ma głównie EN/FR. Aliasów PL nie da się przyjąć „za darmo" — trzeba dotłumaczyć podzbiór WRT01.

---

## 1. Struktura główna

| Katalog | Symbole | Zawartość |
|---------|--------:|-----------|
| `10_electric` | 6 895 | elektryka: aparatura, producenci, IEC 60617, grafika |
| `60_energy` | 1 325 | energetyka / fotowoltaika / sieci |
| `50_pneumatic` | 343 | pneumatyka (zawory, siłowniki) |
| `30_hydraulic` | 94 | hydraulika |
| `20_logic` | 75 | logika: bramki, grafcet, ladder, flow-chart |
| **Razem** | **8 732** | |

### 10_electric — rozbicie

| Podkatalog | Symbole | Rola dla SchemaGen |
|------------|--------:|--------------------|
| `20_manufacturers_articles` | 3 995 | symbole konkretnych producentów (artykuły handlowe) |
| `10_allpole` | 942 | **generyczne wielobiegunowe — kluczowe dla typów bbox** |
| `91_en_60617` | 912 | symbole normatywne IEC 60617 (pokrywa się z `IEC60617.pdf`) |
| `98_graphics` | 723 | grafika montażowa, thumbnaile, plany szaf |
| `11_singlepole` | 308 | reprezentacja jednobiegunowa |
| `99/90_*` | 15 | różne / standard amerykański |

### 10_allpole — typy najważniejsze dla WRT01 (mapowanie do bbox→typ)

| Podkategoria | Symbole |
|--------------|--------:|
| Instalacje domowe | 125 |
| **Czujniki / aparatura pomiarowa** | 113 |
| Elektronika / półprzewodniki | 102 |
| **Przekaźniki / styczniki / styki** | 88 |
| **Bezpieczniki / aparatura zabezpieczająca** | 78 |
| **Sygnalizacja / elementy sterownicze** | 71 |
| Złącza / wtyki | 57 |
| Kable / okablowanie | 56 |
| Odbiorniki / nastawniki | 54 |
| **Zaciski / listwy zaciskowe** | 52 |
| **Przekształtniki / falowniki** | 34 |
| Transformatory / zasilacze | 30 |
| Sieci / zasilanie | 16 |

To pokrywa **prawie cały rdzeń aparatury łączeniowej i pomiarowej** WRT01 na poziomie generycznym.

---

## 2. Producenci (3 995 symboli) — TOP i istotni dla WRT01

| Producent | Symbole | Uwaga |
|-----------|--------:|-------|
| WAGO | 1 982 | **bardzo bogate IO/listwy** — dobry wzorzec wizualny dla modułów IO |
| Siemens | 452 | aparatura + sterowniki (S7, magelis…) |
| Schneider Electric | 300 | w tym `01_PLC_controllers` |
| Allen-Bradley | 78 | PLC/IO Rockwell |
| Beckhoff | 76 | PLC/IO |
| KNX | 75 | automatyka budynkowa |
| Weidmüller | 62 | listwy/złączki |
| Omron | 57 | PLC/przekaźniki |
| Pilz | 44 | aparatura bezpieczeństwa |
| Endress+Hauser | 28 | pomiary procesowe |
| Eaton/Moeller | 23 | aparatura |
| ABB | 22 | aparatura |
| Unitronics | 21 | PLC |
| **Phoenix Contact** | **13** | **patrz §3 — rdzeń produktu brak** |
| **GE (geindustrial)** | **1** | **patrz §3 — tylko ASTAT XT** |

(pełna lista to ~140 producentów; powyżej istotni dla profilu WRT01)

---

## 3. Pokrycie aparatury WRT01 — GE Vernova + Phoenix Contact

### GE Vernova (sterowniki) — **BRAK**

- Wyszukiwanie `vernova`, `RX3i`, `PACSystems`, `pac` → **0 trafień**.
- W całej bibliotece GE to jeden plik: `geindustrial/astat-xt.elmt` (softstart ASTAT XT) + miniatura w planach montażowych.
- **Wniosek:** symbole sterowników GE Vernova (PACSystems RX3i/RSTi-EP itp.) **trzeba pozyskać osobno** — biblioteka EPLAN producenta / DTR / makra. QET tu nie pomoże.

### Phoenix Contact — **13 symboli, rdzeń brak**

Zawartość (głównie konwertery sygnału, interfejsy, przekaźnik bezpieczeństwa, monitor prądu):

| Plik | Co to |
|------|-------|
| `PSR-ESA2_B` | przekaźnik bezpieczeństwa |
| `cbm_e8_24dc_0_5-10a_no-r` (2905744) | elektroniczny wyłącznik obwodu |
| `emd-fl-c-10` (2866022) | monitor prądu |
| `2744461 / 2761266 / 2744416` | konwertery interfejsu RS232/422/485 |
| `2810913 / 2813512 / 2864082` | kondycjonery / wzmacniacze sygnału |
| `sacb-4/8, 6/12, 8/16` | rozdzielacze sensor/aktor |

- **Brak rdzenia Phoenix Contact:** listwy zaciskowe (Clipline), złączki PCB, zasilacze QUINT, moduły I/O — czyli to, czego na WRT01 będzie najwięcej.
- Część nazw jest po katalońsku (ca), nie PL.
- **Wniosek:** QET pokrywa Phoenix marginalnie. Listwy/zasilacze → biblioteka producenta (Phoenix ma EPLAN/.elmt na własnym portalu + Project Complete / Clip Project).

### Co QET realnie daje dla tych dwóch

Mimo braku konkretnych modeli, **generyczne symbole WAGO (1982) / Weidmüller / Siemens** są wizualnie zbliżone do modułów IO i listew Phoenix/GE — przydatne jako **proxy treningowy i klasy generyczne** (np. `terminal_block`, `plc_io_module`), zanim wejdą dokładne symbole producenta.

---

## 4. Format `.elmt` — łatwość ekstrakcji

- XML, geometria wektorowa (`<line>`, `<rect>`, `<polygon>`, `<terminal>`), blok `<names>` z `<name lang="...">`.
- **Nazwy:** EN 6 994 plików, PL **2 986** (~34%), plus FR/DE/inne.
- Ekstrakcja prosta: parse XML → nazwy + zaciski + render wektor→PNG (np. przez Qt/cairosvg po konwersji). Brak warstwy rastrowej do rozplątania (inaczej niż PDF IEC 60617 — tam parowanie obraz↔tekst było ryzykiem).
- **Zaleta nad IEC 60617 PDF:** każdy symbol to osobny plik z metadanymi i punktami przyłączeń (`terminal`) — idealne pod katalog i pod walidację topologii.

---

## 5. Rekomendacje

1. **QET = warstwa przemysłowa generyczna — przyjąć.** Parser `.elmt` → `config/symbol-reference.yaml` (allpole + en_60617 + wybrani producenci). Najlepszy stosunek pokrycie/koszt.
2. **GE Vernova i Phoenix Contact (rdzeń) — warstwa producenta osobno.** QET nie wystarczy. Źródła: portale EPLAN/EDZ producentów, Phoenix Project Complete, GE/Emerson library. Do oceny w osobnej rundzie (źródło #4/#5 w inboxie).
3. **Aliasy PL — dotłumaczyć podzbiór WRT01**, bo PL jest tylko w ~34%. Nie tłumaczyć wszystkich 8732.
4. **Trening YOLO:** użyć WAGO/Siemens/allpole jako bazy syntetyki dla klas generycznych (`terminal_block`, `plc_io_module`, `relay`, `fuse`); realne bboxy z WRT01 nadal konieczne (domain gap).
5. **Licencja GPL** — symbole QET na GPL; przy wciąganiu derywatów/crop-ów do repo zachować atrybucję i sprawdzić kompatybilność licencji SchemaGen. **[do potwierdzenia przez Filipa]**
6. **Lokalizacja w repo:** bibliotekę (115 MB) trzymać poza gitem produkcyjnym — `data/atlas/qet/` w `.gitignore`, do repo trafia tylko wygenerowany `symbol-reference.yaml` + wybrane crop-y.

---

## 6. Otwarte pytania

1. Pozyskuję symbole **GE Vernova** i **Phoenix Contact** z portali producentów jako źródła #4/#5? (osobna runda — wymaga linków/loginu do EPLAN Data Portal)
2. Które **typy WRT01** mają priorytet w pierwszej iteracji katalogu (lista typów z oznaczonych p013–p015)?
3. Licencja SchemaGen — kompatybilna z **GPL**?
