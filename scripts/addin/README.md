# SchemaGen Add-in — mapa plików

Kompilacja: [`../build_addin.ps1`](../build_addin.ps1) → `dist/SchemaGen.EplAddIn..dll`

Rejestracja: EPLAN → Plik → Dodatki → Interfejsy → API → Zarządzaj → Wczytaj

## Pliki źródłowe

| Plik | Odpowiedzialność | Akcja CLI |
|------|------------------|-----------|
| [`SchemaGenAddInModule.cs`](SchemaGenAddInModule.cs) | Rejestracja modułu IEplAddIn | — |
| [`SchemaGenPaths.cs`](SchemaGenPaths.cs) | Stałe ścieżek makr i oznaczeń strony | — |
| [`ProjectResolver.cs`](ProjectResolver.cs) | Rozwiązywanie otwartego projektu (jeden projekt naraz) | — |
| [`PageFinder.cs`](PageFinder.cs) | Wyszukiwanie strony po PAGENAME | — |
| [`SchemaGenUi.cs`](SchemaGenUi.cs) | Komunikaty Decider (sukces/błąd) | — |
| [`Actions/CreatePageAction.cs`](Actions/CreatePageAction.cs) | Tworzenie strony schematu | `SchemaGenCreatePage` |
| [`Actions/InsertPowerMacroAction.cs`](Actions/InsertPowerMacroAction.cs) | Wstawienie makra 400V | `SchemaGenInsertPowerMacro` |

## Parametry akcji

### SchemaGenCreatePage

| Parametr | Kierunek | Opis |
|----------|----------|------|
| `PROJECTPATH` | wejście | Ścieżka `.elk` (opcjonalna — fallback: aktywny projekt) |
| `PAGENAME` | wyjście | Nazwa utworzonej strony, np. `=SCHEMAGEN+MAIN/1` |

### SchemaGenInsertPowerMacro

| Parametr | Kierunek | Opis |
|----------|----------|------|
| `PROJECTPATH` | wejście | Ścieżka `.elk` (opcjonalna) |
| `PAGENAME` | wejście | Wymagana — strona docelowa |
| `MACROPATH` | wejście | Opcjonalna — domyślnie `SchemaGenPaths.PowerSupply400Vac` |

## Odnośniki

- Ścieżki EPLAN: [`../../docs/eplan-data-paths.txt`](../../docs/eplan-data-paths.txt)
- Wzorzec API makr: [`../../docs/eplan-kb/schemagen-cheatsheet.md`](../../docs/eplan-kb/schemagen-cheatsheet.md) § Wstaw makro okna
- Orkiestracja ze skryptu: [`../SchemaGen_MVP.cs`](../SchemaGen_MVP.cs)
