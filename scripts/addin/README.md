# SchemaGen Add-in — mapa plików

**Status sesji 1.4:** ✅ przetestowane — dwie strony, `PAGEDESCRIPTION`, makra przez `SchemaGenInsertPowerMacro`.

Kompilacja: [`../build_addin.ps1`](../build_addin.ps1) → `dist/SchemaGen.EplAddIn..dll` (auto-kopia do EPLAN)

Debug add-inu: [`../watch_addin.ps1`](../watch_addin.ps1) — rebuild przy każdej zmianie `.cs`

Rejestracja (jednorazowo): EPLAN → Plik → Dodatki → Interfejsy → API → Zarządzaj → Wczytaj

## Pliki źródłowe

| Plik | Odpowiedzialność | Akcja CLI | Status |
|------|------------------|-----------|--------|
| [`SchemaGenAddInModule.cs`](SchemaGenAddInModule.cs) | Rejestracja modułu IEplAddIn | — | ✅ |
| [`SchemaGenPaths.cs`](SchemaGenPaths.cs) | Stałe ścieżek makr i oznaczeń strony | — | ✅ |
| [`ProjectResolver.cs`](ProjectResolver.cs) | Rozwiązywanie otwartego projektu (jeden projekt naraz) | — | ✅ |
| [`PageFinder.cs`](PageFinder.cs) | Wyszukiwanie strony po PAGENAME | — | ✅ |
| [`SchemaGenUi.cs`](SchemaGenUi.cs) | Komunikaty Decider (sukces/błąd) | — | ✅ |
| [`Actions/CreatePageAction.cs`](Actions/CreatePageAction.cs) | Tworzenie strony schematu | `SchemaGenCreatePage` | ✅ sesja 1.2 |
| [`Actions/InsertPowerMacroAction.cs`](Actions/InsertPowerMacroAction.cs) | Wstawienie makra (400V / falownik) | `SchemaGenInsertPowerMacro` | ✅ sesja 1.3–1.4 |

## Parametry akcji

### SchemaGenCreatePage

| Parametr | Kierunek | Opis |
|----------|----------|------|
| `PROJECTPATH` | wejście | Ścieżka `.elk` (opcjonalna — fallback: aktywny projekt) |
| `PAGEDESCRIPTION` | wejście | Opcjonalny opis strony (po Create: `Properties.Page.PAGE_NOMINATIOMN` #11011) |
| `PAGENAME` | wyjście | Nazwa utworzonej strony, np. `=SCHEMAGEN+MAIN/1` |

### SchemaGenInsertPowerMacro

| Parametr | Kierunek | Opis |
|----------|----------|------|
| `PROJECTPATH` | wejście | Ścieżka `.elk` (opcjonalna) |
| `PAGENAME` | wejście | Wymagana — strona docelowa |
| `MACROPATH` | wejście | Opcjonalna — domyślnie `SchemaGenPaths.PowerSupply400Vac` |
| `MACROX` | wejście | Opcjonalna — domyślnie `SchemaGenPaths.MacroInsertX` |
| `MACROY` | wejście | Opcjonalna — domyślnie `SchemaGenPaths.MacroInsertY` |
| `DRIVETYPE` | wejście | Opcjonalna — typ napędu z XML (`SE_Drive_Type`) do komunikatu sukcesu |

## Odnośniki

- Notatki z testu: [`../../docs/eplan-api-notes.md`](../../docs/eplan-api-notes.md) § Sesja 1.4
- Ścieżki EPLAN: [`../../docs/eplan-data-paths.txt`](../../docs/eplan-data-paths.txt)
- Wzorzec API makr: [`../../docs/eplan-kb/schemagen-cheatsheet.md`](../../docs/eplan-kb/schemagen-cheatsheet.md) § Wstaw makro okna
- Orkiestracja ze skryptu: [`../SchemaGen_MVP.cs`](../SchemaGen_MVP.cs)
