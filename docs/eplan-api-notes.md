# Notatki EPLAN API

Uzupełniaj po każdej sesji testowej w EPLAN.

## Sesja 1.7f — 2026-06-13 (globalne MA — dual-pass renumber)

- **Root cause MA1 wszędzie:** zakres licznika DT ustawia **schemat numeracji** (param `/CONFIGSCHEME`), NIE `/IDENTIFIER`. Silniki w różnych lokalizacjach (+B2, +B4) mają już unikalne pełne DT (`=SCHEMAGEN+B2-MA1` ≠ `+B4-MA1`), więc domyślny schemat per-lokalizacja zostawia MA1 w każdej lokalizacji.
- **Cel:** MA = schemat „cały projekt” (MA1, MA2 globalnie), FC = schemat per-lokalizacja (bez zmian) → **dual-pass**: dwa przebiegi renumber z różnym CONFIGSCHEME.
- `/IDENTIFIER` filtruje tylko, które DT renumerować w przebiegu — sam nie zmienia zakresu liczenia.
- **[RYZYKO] niepotwierdzone parametry:** `/IDENTIFIER`, `/CONFIGSCHEME` — brak w lokalnej KB (tylko „renumber | numbering functionality”). Potwierdzone testem 1.7d: `/TYPE:DEVICES /USESELECTION /STARTVALUE /STEPVALUE /POSTNUMERATE`. Probe `SchemaGen_TryRenumber_MA.cs` wykaże czy IDENTIFIER/CONFIGSCHEME działają (S025019 = brak wsparcia → plan B: `FUNC_COUNTER` w add-inie).
- **Schemat numeracji musi istnieć z nazwy** w EPLAN (Ustawienia → Projekty → Urządzenia → Numeracja offline) — nie tworzony z kodu. Nazwa trafia do `config/numbering-rules.xml` (`configScheme`).
- **Architektura config-driven:** `config/numbering-rules.xml` — per identyfikator {scope, configScheme, start, step}; docelowo generowany przez LLM/aplikację. Orkiestrator woła akcję per reguła. Plan B (FUNC_COUNTER) tylko gdy natywny CONFIGSCHEME zawiedzie.

## Sesja 1.7d cd. — 2026-06-13 (RenumberDevices)

- **Numeracja DT — rozwiązana natywnie:** akcja `SchemaGenRenumberDevices` woła `renumber /TYPE:DEVICES` (przechwycone z Action Monitor: Projekt → Numeruj). Ręczny test: FC1→FC2 OK, MA numerowane per-lokalizacja OK. To zamyka ślepą uliczkę ręcznego remapu DT z 1.7c.
- `renumber` działa na **aktywnym projekcie** (jak `generate /TYPE:CONNECTIONS`) — nie wymaga `/PROJECTNAME`, bo `SchemaGenEnsureProject` aktywuje Hello_world wcześniej. Po renumber: `gedRedraw`.
- Pipeline MVP: LinkPotentials → ConnectMotor → **RenumberDevices** → AuditLayout. Kolejność istotna: numerację robimy po połączeniach (ConnectMotor), przed audytem layoutu.
- **[RYZYKO] do potwierdzenia w EPLAN:** czy `renumber /TYPE:DEVICES` używa ostatnio użytego schematu numeracji (general remark: „last used scheme”). Jeśli schemat jest nie ten — ustawić w GUI przed pierwszym biegiem lub dodać parametr schematu.

## Sesja 1.7d — 2026-06-13 (refaktor: RemapTags → ConnectMotor)

- Usunięto `MacroAdaptation.RemapMotorTag` — ręczny remap DT przez `func.Name` był martwym kodem (1.7c). Akcja `SchemaGenRemapTags` przemianowana na `SchemaGenConnectMotor` (`ConnectMotorAction.cs`); robi tylko `ConnectMotorWindings` (U/V/W + `generate /TYPE:CONNECTIONS`) + `gedRedraw`.
- Skrypt diag.: `SchemaGen_RemapTags.cs` → `SchemaGen_ConnectMotor.cs`. Orchestrator i `FindAction` zaktualizowane.
- Rejestracja akcji w EPLAN jest automatyczna (IEplAction, brak jawnej listy w `SchemaGenAddInModule`) — zmiana nazwy nie wymaga edycji modułu, ale **w EPLAN trzeba przeładować DLL** (stara akcja `SchemaGenRemapTags` zniknie, pojawi się `SchemaGenConnectMotor`).
- Numeracja DT (FC/MA) = osobny krok: `SchemaGenRenumberDevices` → `renumber /TYPE:DEVICES` + pełne parametry (USESELECTION, STARTVALUE, STEPVALUE, POSTNUMERATE). Opcjonalnie `CONFIGSCHEME`, `IDENTIFIER`.
- **Wynik testu MVP:** widoczne `-FC1`/`-FC2`/`-FC1` na str. 1/2/3 i `-MA1` wszędzie = **numeracja per lokalizacja** w schemacie Hello_world (lokalizacja w nagłówku strony). Pełne DT: `=SCHEMAGEN+lokacja-FC1` — unikalne. Globalne liczniki na rysunku wymagają `CONFIGSCHEME` (schemat „cały projekt” z ustawień EPLAN).

## Sesja 1.7c — 2026-06-11 (layout RY + ślepa uliczka DT)

### Layout RY — działa
- **Przyczyna:** `MacroFitCalculator.EnsureMacroBounds` mierzył offset ze wszystkich obiektów makra (origin ~0) → `offset.X≈0` → treść funkcyjna na RY≈73 zamiast ~37 → wystawanie **górą** ramki.
- **Fix:** `PlacementBounds.MeasureContentObjects` (tylko Function/PotentialDefinition/InterruptionPoint) + `InsertPowerMacroAction.ShiftPlacementsRy` po insert — dosuwa makro w pionie do `FrameMinRy+margin`. **RX nietknięty.**
- **Ramka A3:** FrameMin 35/35, FrameMax 287/415. Oś audytu: `minRy=Location.Y`, `minRx=Location.X`.
- **Uwaga:** w `FrameLayoutCalculator.Evaluate` nazwy `overflow.top/bottom` mogą być mylące względem fizycznej góry strony — weryfikuj wizualnie PDF, nie tylko JSON.

### DT / oznaczenia urządzeń — nie ruszać ręcznie
- `func.Name` ustawia tylko fragment product (`-M1`), nie pełne DT na rysunku.
- `FunctionBasePropertyList.NameParts` — zmiany nie nadpisują widocznego DT w testach.
- Property **`<20010>`** (ID widoczne) — zapis pustym stringiem → **S063113** (chronione). Odczyt: `func.Properties[20010, 0]`.
- `func.IsMainFunction` — **konieczny filtr** (bez niego remap łapie ~140 funkcji zamiast ~17 głównych).
- `Properties.Function.FUNC_CODE` — brak jako stała (CS0117); działa `func.Properties.FUNC_CODE`.
- `generate /TYPE:IDENTIFIERS` — **nie istnieje** w akcji generate (tylko CONNECTIONS/CABLES). Odświeżenie: `gedRedraw`.
- **Realna struktura Hello_world:** `=SCHEMAGEN` + lokalizacje (+MAIN, +A2, +B2, +B4, +B2.X1). Nie `MACHINE/CABINET`.
- **Kierunek:** natywna numeracja EPLAN (akcja CLI `renumber`), nie ręczny remap property.
- **Pułapka (sesja 1.7d):** `StartOfflineNumeration` = numeracja **stron**, nie DT urządzeń.
- **Akcja `renumber` (urządzenia):** wymaga `/TYPE:DEVICES` — samo `renumber` → **S025019** „Proces jest nieobsługiwany”.
- **Minimalne CLI (cały projekt, schemat z ustawień projektu):**
  ```
  renumber /TYPE:DEVICES /USESELECTION:0 /STARTVALUE:1 /STEPVALUE:1 /POSTNUMERATE:0
  ```
- **TYPE:** `DEVICES` | `PAGES` | `TERMINALS` | `CABLES` | `CONNECTIONS`. Opcjonalnie `/CONFIGSCHEME:"..."` (nazwa z GUI numeracji).
- **Test:** skrypt `SchemaGen_TryRenumber.cs`.

### Skrypty diagnostyczne
- `SchemaGen_AuditLayout.cs`, `SchemaGen_ConnectMotor.cs` — tylko `CommandLineInterpreter` + akcje DLL.
- Skrypt `.cs` z `[Start]` **nie może** używać typów DataModel bezpośrednio (brak ref do DataModel.dll przy ExecuteScript).

## Sesja 1.6 — 2026-06-09 (tagi silnika + MCP + FrameLayout)

### Zaimplementowano
- `SchemaGenRemapTags` — `=MACHINE+CABINET-M1`, `ConnectMotorWindings` (U/V/W + generate CONNECTIONS)
- `SchemaGenAuditLayout` — JSON bbox vs ramka → `output/layout-audit.json`
- `FrameLayoutCalculator` + `USE_FRAME_LAYOUT=1` w MVP
- MCP `schemagen-eplan`, walidacja CSV (`validate_connections.py`)

### Test EPLAN
1. `build_addin.ps1` + kopia `SchemaGen_MVP.cs`
2. Uruchom skrypt → sprawdź tag silnika i `output/layout-audit.json`
3. Skoryguj `FrameMinRy/Rx/MaxRy/Rx` w `SchemaGenPaths.cs` wg audytu

## Koniec dnia 2026-06-09 — layout w ramce (kalibracja po teście)

### Objaw
Schematy tworzą się poprawnie (3 strony, 3 makra, potencjały), ale makra są **poza ramką druku** strony EPLAN.

### Przyczyna
- Brak odczytu granic ramki strony z API — tylko ręczne stałe w [`SchemaGenPaths.cs`](../scripts/addin/SchemaGenPaths.cs)
- Aktualne wartości: `MacroInsertRy=-1.0`, `MacroInsertRx=18.0` (wszystkie 3 makra)
- `MacroFitCalculator` wyrównuje lewy-górny róg bbox makra do punktu docelowego, ale **nie sprawdza overflow** względem ramki
- Agent nie widzi EPLAN po uruchomieniu — brak pętli testowej (docelowo: MCP + `SchemaGenAuditLayout`)

### Kierunek naprawy (Faza 1b)
1. Akcja `SchemaGenAuditLayout` — zwraca bbox makra + granice ramki strony
2. `FrameLayoutCalculator` — docelowy punkt = lewy-górny róg ramki + margines
3. MCP `schemagen-eplan` — agent iteruje bez ręcznego klikania

## Sesja 1.5+ — 2026-06-09 (MacroFitCalculator — rozrzucone elementy makra)

### Objaw
- Górna linia zasilająca OK w marginesie; sekcje pionowe po lewej przesunięte w lewo/dół, urwane połączenia.

### Przyczyna
- `MacroFitCalculator.MoveObjects` przesuwał tylko `Function.Location` po probe-insert — linie i inne elementy graficzne zostawały na miejscu.

### Poprawka
- Probe insert → pomiar bbox `Placement` → **usunięcie** probe → final `WindowMacro` na `target - offset` (makro jako całość).
- Cache `macro-offsets.xml` wersja 2 (`schemaVersion`) — stary cache ignorowany.

### Reguła projektu (zawsze)
- Linie muszą prowadzić dokądś lub kończyć się strzałką — graficznie urwane połączenia są niedopuszczalne.

## Sesja 1.5 — 2026-06-09 (poprawki po teście EPLAN)

### Oś RY/RX — pułapka Insert.WindowMacro
- `Insert.WindowMacro(..., new PointD(X, Y), Relative)` — **X = oś RY**, **Y = oś RX** (potwierdzone testem)
- Błąd sesji 1.5: zmiana `MacroInsertY` 8.35→9.85 przesuwała RX, nie RY
- Poprawka: `MacroInsertRy=17.2` (góra makra RY=0,6, było -0,6 przy 16.0), `MacroInsertRx=8.35`
- Parametry CLI: `MACROX`=RY, `MACROY`=RX

### Potencjały =GAA-2L1 vs 2L1
- Makra Sample używają prefiksu instalacji `=GAA-`; makro 400V używa krótkich nazw `2L1`
- [`MacroAdaptation.cs`](../scripts/addin/MacroAdaptation.cs) — `CanonicalPotentialName`: strip `=PLANT-` prefix
- [`LinkPotentialsAction.cs`](../scripts/addin/Actions/LinkPotentialsAction.cs) — normalizacja przed generate + audyt

### Tagi PLC — `[20171<218<44025...]`
- Nierozwiązane PropertyPlacement — makro niesie strukturę =GAA z projektu źródłowego
- Fix częściowy: remap `DESIGNATION_PLANT` GAA→SCHEMAGEN w `MacroAdaptation`
- Pełne rozwiązanie: etap 1 pipeline (macro-pipeline.md) — dedykowane makra lub generator

### Pipeline 2 etapy
- Dokumentacja: [`macro-pipeline.md`](macro-pipeline.md)
- Etap 2 (insert+adapt) — zaimplementowany; Etap 1 (generator makra) — Faza 3+

## Sesja 1.5 — 2026-06-09 (implementacja, test do wykonania)

- **Layout (historyczne):** `MacroInsertY` = 9.85 — **zastąpione** przez `FrameLayoutCalculator` + `USE_FRAME_LAYOUT=1` (sesja 1.6)
- **Strona 3:** opis „Sterowanie Start/Stop”, makro [`Fan_motor_control_two_switches.ema`](../scripts/addin/SchemaGenPaths.cs) (`203_Electrical_Engine/202_PCT-Loop/`)
- **Akcja audytu:** `SchemaGenLinkPotentials` → [`LinkPotentialsAction.cs`](../scripts/addin/Actions/LinkPotentialsAction.cs)
  - Wywołuje `generate /TYPE:CONNECTIONS`
  - Skanuje strony `=SCHEMAGEN*` — `InterruptionPoint` i `PotentialDefinition` w `AllFirstLevelPlacements`
  - Grupuje po nazwie; sprawdza `CrossReferencedObjectsAll` dla grup wielostronnych
  - EPLAN łączy punkty o **tej samej nazwie** automatycznie — audyt raportuje brakujące odnośniki
- **Orkiestracja:** [`SchemaGen_MVP.cs`](../scripts/SchemaGen_MVP.cs) — 3 strony + LinkPotentials (zamiast samego generate)
- **Deploy:** `build_addin.ps1` + kopia `SchemaGen_MVP.cs` do `Skrypty\Schemagen\`

## Sesja 1.4 — 2026-06-07 ✅ przetestowane (debug: dwie strony)

- **Wynik testu:** XML wczytany, makro 400V na stronie 1, `Frequency_Control.ema` na stronie 2, opisy stron ustawione
- **Decyzja layoutu:** dwa makra **nie mieszczą się na jednej stronie** → osobne strony zasilania i napędu
- Parser: klasa `SchemaGenConfig` w [`SchemaGen_MVP.cs`](../scripts/SchemaGen_MVP.cs)
- **EPLAN S046013:** osobny plik `.cs` bez `[Start]` w `Skrypty\` → helper w tym samym pliku co `[Start]`
- Orkiestracja: LoadConfig → CreatePage (400V) → InsertPowerMacro → CreatePage (napęd) → InsertDriveMacro → `generate /TYPE:CONNECTIONS`
- **CreatePage + opis:** [`CreatePageAction.cs`](../scripts/addin/Actions/CreatePageAction.cs) — `PAGEDESCRIPTION`; opis **po** `Page.Create()` przez `Properties.Page.PAGE_NOMINATIOMN` (#11011). **Pułapka:** #11013 to `PAGE_SUBCOUNTER`, nie opis — stąd w nawigatorze widać tylko liczniki 1, 2
- Makra: [`InsertPowerMacroAction.cs`](../scripts/addin/Actions/InsertPowerMacroAction.cs) — `MACROX`, `MACROY`, `DRIVETYPE`
- Pozycja Y makr: `MacroInsertY` / `DriveMacroInsertY` = **9.85** w [`SchemaGenPaths.cs`](../scripts/addin/SchemaGenPaths.cs) (sesja 1.5)
- **Otwarte:** `generate /TYPE:CONNECTIONS` — punkty przerwania potencjałów w makrach są; **odnośnik między stronami nie potwierdzony** → sesja 1.5: `PotentialDistributionPoint`, interruption points

## Sesja 1.3 — 2026-06-07 ✅ przetestowane

- **Wynik testu:** makro `400VAC_Power_Supply.ema` widoczne na stronie `=SCHEMAGEN+MAIN/N` w `Hello_world.elk`
- Implementacja: akcja `SchemaGenInsertPowerMacro` → [`InsertPowerMacroAction.cs`](../scripts/addin/Actions/InsertPowerMacroAction.cs)
- Orkiestracja: [`SchemaGen_MVP.cs`](../scripts/SchemaGen_MVP.cs) — CreatePage → PAGENAME → InsertPowerMacro
- Mapa plików add-in: [`scripts/addin/README.md`](../scripts/addin/README.md)
- API: `Insert.WindowMacro` — wzorzec w [`schemagen-cheatsheet.md`](eplan-kb/schemagen-cheatsheet.md)
- Ścieżka makra: [`eplan-data-paths.txt`](eplan-data-paths.txt) → `SchemaGenPaths.PowerSupply400Vac`
- Ograniczenie potwierdzone: **jeden otwarty projekt** naraz; `ProjectResolver` + `GetCurrentProject(false)` działa
- Build/deploy: `build_addin.ps1` (auto-kopia DLL) lub `watch_addin.ps1` przy debugu add-inu

## Sesja 1.2 — 2026-06-05

- Co testowano: utworzenie strony schematu w `Hello_world.elk`
- Ograniczenie skryptów: [Scripts.html](https://www.eplan.help/en-US/Infoportal/content/api/2025/Scripts.html) — kompilator skryptów **nie** referencjonuje `DataModelu.dll` ani `HEServicesu.dll`; nie da się dodać referencji nawet z licencją API Extension
- Rozwiązanie: minimalny add-in `SchemaGen.EplAddin.dll` z akcją `SchemaGenCreatePage`; skrypt orkiestruje przez `CommandLineInterpreter`
- Strona testowa: `DESIGNATION_PLANT = "=SCHEMAGEN"`, `DESIGNATION_LOCATION = "+MAIN"` → np. `=SCHEMAGEN+MAIN/1`
- Kompilacja: `scripts/build_addin.ps1` (csc.exe + referencje z `EPLAN\Platform\...\Bin`)
- Rejestracja add-in: EPLAN → Plik → Dodatki → Interfejsy → API → Zarządzaj (jednorazowo)
- Brak akcji CLI do tworzenia pustej strony (`edit`, `import`, `projectmanagement` — nie obsługują)

## Sesja 1.1 — 2026-06-05

- Co testowano: `SchemaGen_MVP.cs` — otwarcie `Hello_world.edb` + komunikat sukcesu
- Co nie działało (pierwsza wersja):
  - CS0105: duplikat `using Eplan.EplApi.Base` i `Eplan.EplApi.Scripting` (EPLAN wstrzykuje je automatycznie)
  - CS0234: `Eplan.EplApi.DataModel` niedostępne w skryptach `.cs` (kompilator nie referencjonuje `DataModelu.dll`)
- Przyczyna: skrypt EPLAN ma ograniczony zestaw assembly (Base, ApplicationFramework, Gui, MasterData) — patrz [Scripts.html](https://www.eplan.help/en-US/Infoportal/content/api/2025/Scripts.html)
- Poprawka v1: otwarcie projektu przez `CommandLineInterpreter` + akcja `edit /PROJECTNAME:...`
- Poprawka v2 (2026-06-05): ścieżka musi wskazywać plik **`.elk`**, nie katalog `.edb`
- Poprawka v3 (2026-06-05): akcja `ProjectOpen /Project:"..."` z cudzysłowem wokół ścieżki (bez tego `C:` obcina parametr); fallback `XPrjActionProjectOpen`, potem `edit`
- Logi błędów: `eplan_output/ErrorLog_*.csv`
- Fragment działający:

```csharp
bool ok = new CommandLineInterpreter().Execute(
    @"edit /PROJECTNAME:C:\Users\Public\EPLAN\Data\Projekty\Schemagen\Hello_world.elk");
```

- Uwaga na przyszłość: sesje 1.2+ (strony, makra) wymagają DataModel/HEServices → prawdopodobnie migracja do add-in DLL lub akcje CLI tam, gdzie to możliwe
