# Notatki EPLAN API

Uzupełniaj po każdej sesji testowej w EPLAN.

## Sesja 1.3 — 2026-06-07

- Co zaimplementowano: wstawienie makra `400VAC_Power_Supply.ema` przez akcję `SchemaGenInsertPowerMacro`
- Architektura: add-in rozbity na małe pliki — mapa w [`scripts/addin/README.md`](../scripts/addin/README.md)
- Kluczowe pliki: [`InsertPowerMacroAction.cs`](../scripts/addin/Actions/InsertPowerMacroAction.cs), [`ProjectResolver.cs`](../scripts/addin/ProjectResolver.cs), [`SchemaGen_MVP.cs`](../scripts/SchemaGen_MVP.cs)
- API: `Insert.WindowMacro(path, 0, page, PointD(70,0), Relative)` — wzorzec w [`schemagen-cheatsheet.md`](eplan-kb/schemagen-cheatsheet.md)
- Ścieżka makra: [`eplan-data-paths.txt`](eplan-data-paths.txt) → `SchemaGenPaths.PowerSupply400Vac`
- Ograniczenie: EPLAN wymaga **jednego otwartego projektu**; `ProjectResolver` używa `GetCurrentProject(false)` jako fallback
- Kompilacja: `scripts/build_addin.ps1` — OK, `dist/SchemaGen.EplAddIn..dll`
- Test w EPLAN: oczekiwany wynik — makro zasilania 400V na stronie `=SCHEMAGEN+MAIN/N`, komunikat z `Functions.Length > 0`

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
