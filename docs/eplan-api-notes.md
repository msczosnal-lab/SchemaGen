# Notatki EPLAN API

Uzupełniaj po każdej sesji testowej w EPLAN.

## Sesja 1.4 — 2026-06-07 ✅ przetestowane (debug: dwie strony)

- **Wynik testu:** XML wczytany, makro 400V na stronie 1, `Frequency_Control.ema` na stronie 2, opisy stron ustawione
- **Decyzja layoutu:** dwa makra **nie mieszczą się na jednej stronie** → osobne strony zasilania i napędu
- Parser: klasa `SchemaGenConfig` w [`SchemaGen_MVP.cs`](../scripts/SchemaGen_MVP.cs)
- **EPLAN S046013:** osobny plik `.cs` bez `[Start]` w `Skrypty\` → helper w tym samym pliku co `[Start]`
- Orkiestracja: LoadConfig → CreatePage (400V) → InsertPowerMacro → CreatePage (napęd) → InsertDriveMacro → `generate /TYPE:CONNECTIONS`
- **CreatePage + opis:** [`CreatePageAction.cs`](../scripts/addin/Actions/CreatePageAction.cs) — `PAGEDESCRIPTION`; opis **po** `Page.Create()` przez `Properties.Page.PAGE_NOMINATIOMN` (#11011). **Pułapka:** #11013 to `PAGE_SUBCOUNTER`, nie opis — stąd w nawigatorze widać tylko liczniki 1, 2
- Makra: [`InsertPowerMacroAction.cs`](../scripts/addin/Actions/InsertPowerMacroAction.cs) — `MACROX`, `MACROY`, `DRIVETYPE`
- Pozycja Y makr: `MacroInsertY` / `DriveMacroInsertY` = **8.35** w [`SchemaGenPaths.cs`](../scripts/addin/SchemaGenPaths.cs) — **do obniżenia o 1,5 RY na sesji 1.5** (dodać 1,5 → **9.85**; makra zbyt wysoko)
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
