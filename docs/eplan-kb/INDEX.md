# EPLAN API Knowledge Base (SchemaGen)

Lokalna baza wiedzy — **nie szukaj w internecie**, czytaj te pliki.

## Jak korzystać (najtaniej)

1. Zacznij od tego pliku (INDEX) — ~2 min kontekstu.
2. Otwórz **jeden** plik z `topics/` pasujący do zadania.
3. Szukaj w repo: `grep -r "WindowMacro" docs/eplan-kb/`
4. Pełny surowy extract: `raw-extract.json` (grep, nie wczytuj całości).
5. Notatki z testów: `docs/eplan-api-notes.md`

## Tematy (topics/)

- **[scripts](topics/scripts.md)** — MVP — struktura skryptu .cs, [Start], parametry (6 doc)
- **[datamodel](topics/datamodel.md)** — MVP — Project, Page, Function, właściwości, transakcje (19 doc)
- **[heservices](topics/heservices.md)** — MVP — wstawianie makr .ema, Insert, PlaceHolder (4 doc)
- **[actions-cli](topics/actions-cli.md)** — MVP — eksport CSV/PDF, CLI, CommandLineInterpreter (4 doc)
- **[addins](topics/addins.md)** — Przyszłość — migracja z .cs do DLL (10 doc)
- **[pro-panel-3d](topics/pro-panel-3d.md)** — Poza MVP — szafy 3D (22 doc)
- **[parts-masterdata](topics/parts-masterdata.md)** — Później — BOM, części (5 doc)
- **[misc](topics/misc.md)** — Na żądanie (34 doc)

## Szybkie odniesienia

- [actions-index.md](actions-index.md) — lista akcji EPLAN
- [source-manifest.md](source-manifest.md) — mapa 104 plików HTML
- [schemagen-cheatsheet.md](schemagen-cheatsheet.md) — gotowe snippety pod MVP

## Architektura API (skrót)

| Namespace | Rola |
|-----------|------|
| `Eplan.EplApi.ApplicationFramework` | Actions, skrypty, add-iny |
| `Eplan.EplApi.DataModel` | Project, Page, Function, właściwości |
| `Eplan.EplApi.HEServices` | Makra, eksport, Search, SelectionSet |
| `Eplan.EplApi.EServices` | Wiadomości, weryfikacje, GED interactions |
| `Eplan.EplApi.MasterData` | Baza części, symbole |

## SchemaGen MVP — typowy flow API

```
1. ProjectManager.OpenProject("...Hello_world.edb")
2. Page.Create(project, DocumentType.Circuit, PagePropertyList)
3. Insert.WindowMacro("...400VAC_Power_Supply.ema", variant, page, PointD, MoveKind)
4. PlaceHolder.ApplyRecord("...")  // jeśli makro ma PlaceHolder
5. Function.Name = "=MACHINE+CABINET-M1"  // w Transaction + SafetyPoint
6. CommandLineInterpreter.Execute("XMExportConnectionsAction ...")  // walidacja CSV
7. CommandLineInterpreter.Execute("XPrintPdf ...")  // PDF dla człowieka
```

## Makra EPLAN

| Rozszerzenie | Typ |
|-------------|-----|
| `.ema` | Window macro (na stronę) |
| `.emp` | Page macro (cała strona) |
| `.ems` | Symbol macro |

Klasa: `Eplan.EplApi.HEServices.Insert` — `WindowMacro()`, `PageMacro()`, `SymbolMacro()`

## Skrypt .cs — minimum

```csharp
public class SchemaGen_MVP {
    [Start]
    public void Run() { /* ... */ }
}
```

Uruchomienie: EPLAN → Narzędzia → Skrypty → Uruchom
Lokalizacja: `C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\`

## Zmienne ścieżek EPLAN

- `$(MD_PROJECTS)` — projekty
- `$(MD_MACROS)` — makra
- `$(MD_TEMPLATES)` — szablony projektów (.zw9)
