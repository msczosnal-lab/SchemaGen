# Claude Opus — instrukcje kodowania w projektu SchemaGen

Instrukcje ogólne dla agenta AI (Claude Opus) piszącego kod w repozytorium **EPLAN SchemaGen**. Wklej jako prompt, regułę Cursor lub prefix do zadania.

---

## 1. Co to jest ten projekt

Automatyczne generowanie schematów elektrycznych w **EPLAN Electric P8 2025** na podstawie XML `ConfigurationVariable` (format z EPLAN Sample Project). Agent AI generuje lub modyfikuje XML → skrypt C# + add-in DLL wołają EPLAN API → walidacja przez **CSV połączeń**, nie PDF.

**Architektura (decyzja projektu):**

- **Skrypt `.cs`** — orchestrator, parser XML, wywołania CLI (`CommandLineInterpreter`)
- **Add-in DLL** — pełny `DataModel` / `HEServices` (strony, makra, tagi, layout)
- Skrypt **nie ma** `DataModel` w kompilatorze EPLAN — nie próbuj tam wstawiać makr bezpośrednio

---

## 2. Mapa repozytorium

```
SchemaGen/
├── scripts/                          ← KOD ŹRÓDŁOWY (edytuj tutaj)
│   ├── SchemaGen_MVP.cs              ← główny orchestrator + SchemaGenConfig (XML)
│   ├── SchemaGen_AuditLayout.cs      ← skrypt diag. → SchemaGenAuditLayout
│   ├── SchemaGen_ConnectMotor.cs     ← skrypt diag. → SchemaGenConnectMotor
│   ├── build_addin.ps1               ← kompilacja DLL + kopia do EPLAN
│   ├── watch_addin.ps1               ← auto-rebuild przy edycji add-inu
│   ├── extract_eplan_docs.py         ← regeneracja KB z HTML
│   ├── build_eplan_kb.py
│   ├── validation/
│   │   └── validate_connections.py   ← walidacja CSV (Faza 2)
│   └── addin/                        ← źródła SchemaGen.EplAddIn..dll
│       ├── SchemaGenAddInModule.cs
│       ├── SchemaGenPaths.cs         ← ścieżki, ramka, tag silnika, osie
│       ├── MacroFitCalculator.cs     ← offset origin makra
│       ├── FrameLayoutCalculator.cs  ← auto-pozycjonowanie w ramce
│       ├── MacroAdaptation.cs        ← potencjały, uzwojenia U/V/W
│       ├── PlacementBounds.cs
│       ├── ProjectResolver.cs, PageFinder.cs, SchemaGenUi.cs
│       └── Actions/                  ← akcje IEplAction (CLI)
├── config/
│   ├── 901_Drive_Design.xml          ← przykładowa konfiguracja MVP
│   ├── validation-rules.json         ← reguły walidacji CSV
│   └── claude_desktop_config.example.json
├── docs/
│   ├── project-context.txt           ← kontekst techniczny (aktualny stan)
│   ├── session-log.md                ← dziennik sesji — OSTATNI WPIS = następny krok
│   ├── ROADMAP.md                    ← fazy 0–6
│   ├── eplan-api-notes.md            ← notatki z testów API (uzupełniaj po sesji)
│   ├── eplan-data-paths.txt          ← ścieżki instalacji EPLAN
│   ├── macro-pipeline.md             ← etap adaptacji makr vs insert
│   └── eplan-kb/                     ← LOKALNA BAZA EPLAN API (bez web)
│       ├── INDEX.md                  ← start tutaj
│       ├── schemagen-cheatsheet.md   ← gotowe snippety C#
│       ├── actions-index.md
│       └── topics/{scripts,datamodel,heservices,actions-cli,addins,...}.md
├── mcp/
│   ├── README.md
│   └── schemagen_eplan/server.py     ← MCP: build, run, layout, walidacja
└── .cursor/
    ├── rules/eplan-schemagen.mdc     ← reguła always-on w Cursor
    └── mcp.json                      ← konfiguracja MCP w Cursor
```

---

## 3. Ścieżki EPLAN (runtime — poza gitem)

Baza: `C:\Users\Public\EPLAN\Data\`

| Zasób | Ścieżka |
|--------|---------|
| Sandbox | `Projekty\Schemagen\Hello_world.elk` (nie `.edb`!) |
| Referencja | `Projekty\Schemagen\EPLAN_Sample_Project.elk` |
| Makra demo + XML | `Projekty\Schemagen\EPLAN_Sample_Macros.elk` → `DOC\901_Drive_Design.xml` |
| Biblioteka makr | `Makra\Schemagen\EPLAN_Macro\` |
| Skrypty runtime | `Skrypty\Schemagen\` |
| Add-in DLL | `Skrypty\Schemagen\SchemaGen.EplAddIn..dll` |
| Wyjścia MCP | `Skrypty\Schemagen\output\` |

**Makra MVP:**

- Zasilanie 400V: `201_Power_Supply\101_01_Variant_1\400VAC_Power_Supply.ema`
- Falownik: `203_Electrical_Engine\101_02_Variant_2\Frequency_Control.ema`
- Start/Stop: `203_Electrical_Engine\202_PCT-Loop\Fan_motor_control_two_switches.ema`

**Zmienne EPLAN:** `$(MD_PROJECTS)`, `$(MD_MACROS)`, `PathMap.SubstitutePath()`

---

## 4. Zasoby wiedzy — kolejność czytania

Przy każdym zadaniu EPLAN API:

1. `docs/session-log.md` — co działa, co nie, następny krok
2. `docs/project-context.txt` — stan MVP
3. `docs/eplan-kb/INDEX.md` → jeden plik z `topics/`
4. `docs/eplan-kb/schemagen-cheatsheet.md` — wzorce C#
5. `grep` w `docs/eplan-kb/` — **nie WebSearch**
6. Istniejący kod w `scripts/` — wzorzec stylu
7. `docs/eplan-api-notes.md` — pułapki odkryte w testach

**Źródło HTML API** (regeneracja KB): `C:\Users\Filip\Desktop\startUp\AutoGen\EPLAN API docs`

---

## 5. Akcje add-inu (CLI)

Skrypt woła je przez `CommandLineInterpreter().Execute(...)`:

| Akcja | Plik | Cel |
|--------|------|-----|
| `SchemaGenEnsureProject` | EnsureProjectAction | Otwarcie projektu |
| `SchemaGenCreatePage` | CreatePageAction | Strona `=SCHEMAGEN+MAIN/N` |
| `SchemaGenInsertPowerMacro` | InsertPowerMacroAction | Wstawienie `.ema` (+ `USE_FRAME_LAYOUT=1`) |
| `SchemaGenLinkPotentials` | LinkPotentialsAction | generate CONNECTIONS + audyt odnośników |
| `SchemaGenConnectMotor` | ConnectMotorAction | Uzwojenia silnika (U/V/W) |
| `SchemaGenAuditLayout` | AuditLayoutAction | `output/layout-audit.json` |
| `SchemaGenExportConnections` | ExportConnectionsAction | `output/connections.csv` |

Parametry CLI: ścieżki w **podwójnych cudzysłowach**. `SILENT=1` dla headless / MCP.

Szczegóły parametrów: `scripts/addin/README.md`

---

## 6. MCP — narzędzia agenta

Serwer: `mcp/schemagen_eplan/server.py` | config: `.cursor/mcp.json`

| Tool | Co robi |
|------|---------|
| `eplan_build_addin` | `build_addin.ps1` |
| `eplan_run_script` | Headless `SchemaGen_MVP.cs` |
| `eplan_get_layout` | `layout-audit.json` |
| `eplan_export_connections` | `connections.csv` |
| `eplan_validate_and_report` | CSV + `validate_connections.py` |
| `eplan_closed_loop` | build → run → layout → walidacja |

Wyjścia: `C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\`

---

## 7. Pipeline MVP

`SchemaGen_MVP.cs` wykonuje:

1. Wczytaj `901_Drive_Design.xml` (`SchemaGenConfig.TryLoad`)
2. Otwórz `Hello_world.elk`
3. Utwórz 3 strony (zasilanie, napęd, Start/Stop)
4. Wstaw 3 makra (XML `SE_Drive_Type` → falownik)
5. `SchemaGenLinkPotentials`
6. `SchemaGenConnectMotor`
7. `SchemaGenAuditLayout`

**Walidacja agenta:** CSV → `config/validation-rules.json` → `scripts/validation/validate_connections.py` → `{ errors, warnings, approved }`

---

## 8. Pułapki techniczne (obowiązkowe)

| Temat | Reguła |
|--------|--------|
| Oś makra | `PointD(X,Y)`: **X = RY (pion), Y = RX (poziom)**. `MACROX=RY`, `MACROY=RX` |
| Makra | Wstawiaj **całość** przez `WindowMacro` — nie przesuwaj Function bez linii |
| Połączenia | Linia → element lub strzałka — **nigdy urwane końce** |
| Projekt | Otwieraj `.elk`, nie katalog `.edb` |
| Skrypt vs DLL | `DataModel` tylko w add-inie |
| Layout RY | Działa (`MeasureContentObjects` + `ShiftPlacementsRy`) — nie ruszaj bez potrzeby |
| Tagi DT | Ręczny remap tagów urządzeń był problematyczny — kierunek: natywna numeracja EPLAN |
| Struktura GAA | Makra z Sample Project mają `=GAA` — adaptacja w `MacroAdaptation` / `macro-pipeline.md` |
| PDF | Tylko dla człowieka na końcu — **nie** jako feedback dla agenta |

---

## 9. Jak piszesz kod

### Przed edycją

- Przeczytaj **ostatni wpis** w `docs/session-log.md`
- Sprawdź, czy zmiana dotyczy skryptu, add-inu, czy obu
- Znajdź wzór w istniejącym pliku — nie wymyślaj API

### Podczas edycji

- **Minimalny diff** — jedna funkcja API / jedna akcja na krok
- Komentarze i komunikaty **po polsku**
- Stałe ścieżek w `SchemaGenPaths.cs` (add-in) lub `SchemaGenConfig` (skrypt)
- Nowa akcja add-inu: `IEplAction` w `Actions/`, rejestracja w `SchemaGenAddInModule.cs`
- Błędy: wcześnie `return false` + `SchemaGenUi.ShowError` z pełną ścieżką
- Kod czytelny sam w sobie — komentarze tylko przy nietypowej logice EPLAN
- Nie refaktoruj „przy okazji”, nie dodawaj abstrakcji na jedno użycie
- Nie dodawaj obsługi edge case’ów, które w tym projekcie nie występują

### Po edycji

- Add-in: `.\scripts\build_addin.ps1` (lub `watch_addin.ps1`)
- Skrypt: kopia `SchemaGen_MVP.cs` do `Skrypty\Schemagen\`
- Opisz **konkretny test EPLAN** lub MCP (`eplan_closed_loop`)
- Po udanej sesji: wpis w `session-log.md` + notatka w `eplan-api-notes.md`
- **Nie commituj / nie pushuj** bez prośby usera

---

## 10. Zakazy

| Zakaz | Powód |
|--------|--------|
| Plugin VS / pełna migracja DLL „na start” | Decyzja: najpierw skrypt (Faza 6 w ROADMAP) |
| Safety, layout szafy 3D, BOM | Poza MVP |
| Własny format konfiguracji | Format już jest w Sample Project |
| WebSearch dla EPLAN API | Lokalna KB w `docs/eplan-kb/` |
| PDF jako feedback dla agenta | Brak semantyki połączeń |
| Duży refaktor „przy okazji” | Minimalny diff |
| Naprawa layoutu RX bez potrzeby | Layout RY jest skalibrowany |

---

## 11. Fazy rozwoju

| Faza | Status |
|------|--------|
| Faza 1 — EPLAN POC (strony, makra, pipeline) | implementacja ✅, testy w toku |
| Faza 1b — MCP + AuditLayout + FrameLayout | fundament ✅ |
| Faza 2 — CSV + reguły + pętla walidacji | w trakcie |
| Faza 3 — WinForms UI | przyszłość |
| Faza 4 — AI → XML | przyszłość |

Szczegóły: `docs/ROADMAP.md`

---

## 12. Hierarchia priorytetów

1. Poprawne połączenia i makra jako całość
2. Zgodność z `session-log` i istniejącym kodem
3. Minimalny, testowalny krok
4. Aktualizacja dokumentacji po sukcesie
5. Elegancja abstrakcji — na końcu

---

## 13. Szablon myślenia przy każdym zadaniu

```
1. Co dokładnie ma działać po tej zmianie? (jeden observable outcome)
2. Czy to skrypt, add-in, czy oba?
3. Jest wzór w scripts/ lub docs/eplan-kb/? → skopiuj wzorzec, nie wymyślaj API
4. Najmniejsza zmiana która to realizuje
5. Jak user to zweryfikuje? (EPLAN + CSV, nie PDF)
```

---

## 14. Szablon startu sesji

```
Kontekst: @docs/session-log.md @docs/project-context.txt @docs/eplan-kb/INDEX.md

Zadanie: [opis]

Zasady:
- Kod w scripts/, runtime w Skrypty\Schemagen\
- EPLAN API tylko z docs/eplan-kb/ (grep, nie web)
- Skrypt = orchestrator CLI; DataModel tylko w add-inie
- Walidacja przez CSV, nie PDF
- Jeden mały krok, minimalny diff
- Komentarze po polsku
```

---

## 15. Przykład dobrego vs złego zachowania

**Dobrze:** „Dodam wywołanie `SchemaGenExportConnections` w orchestratorze MVP po `LinkPotentials`, wzoruję się na `ExportConnectionsAction.cs`. Test: po uruchomieniu MCP `eplan_closed_loop` plik `output/connections.csv` zawiera PE i uzwojenia U/V/W.»

**Źle:** „Zaimplementuję uniwersalny framework layoutu z pluginem, własnym JSON configiem i eksportem PDF do walidacji przez vision model.»
