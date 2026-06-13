# SchemaGen Add-in — mapa plików

**Status sesji 1.6:** implementacja ✅ — RemapTags, AuditLayout, FrameLayout, ExportConnections; test EPLAN do wykonania.

Kompilacja: [`../build_addin.ps1`](../build_addin.ps1) → `dist/SchemaGen.EplAddIn..dll` (auto-kopia do EPLAN)

Debug add-inu: [`../watch_addin.ps1`](../watch_addin.ps1) — rebuild przy każdej zmianie `.cs`

Rejestracja (jednorazowo): EPLAN → Plik → Dodatki → Interfejsy → API → Zarządzaj → Wczytaj

## Pliki źródłowe

| Plik | Odpowiedzialność | Akcja CLI | Status |
|------|------------------|-----------|--------|
| [`SchemaGenAddInModule.cs`](SchemaGenAddInModule.cs) | Rejestracja modułu IEplAddIn | — | ✅ |
| [`SchemaGenPaths.cs`](SchemaGenPaths.cs) | Stałe ścieżek, ramka, tag silnika | — | ✅ |
| [`PlacementBounds.cs`](PlacementBounds.cs) | Pomiar bbox Placement | — | ✅ sesja 1.6 |
| [`FrameLayoutCalculator.cs`](FrameLayoutCalculator.cs) | Auto-pozycjonowanie w ramce | — | ✅ sesja 1.6 |
| [`MacroFitCalculator.cs`](MacroFitCalculator.cs) | Offset origin makra | — | ✅ |
| [`MacroAdaptation.cs`](MacroAdaptation.cs) | Potencjały, uzwojenia silnika (U/V/W) | — | ✅ |
| [`ProjectResolver.cs`](ProjectResolver.cs) | Rozwiązywanie otwartego projektu | — | ✅ |
| [`PageFinder.cs`](PageFinder.cs) | Wyszukiwanie strony po PAGENAME | — | ✅ |
| [`SchemaGenUi.cs`](SchemaGenUi.cs) | Komunikaty Decider | — | ✅ |
| [`Actions/CreatePageAction.cs`](Actions/CreatePageAction.cs) | Tworzenie strony | `SchemaGenCreatePage` | ✅ |
| [`Actions/InsertPowerMacroAction.cs`](Actions/InsertPowerMacroAction.cs) | Wstawienie makra | `SchemaGenInsertPowerMacro` | ✅ |
| [`Actions/LinkPotentialsAction.cs`](Actions/LinkPotentialsAction.cs) | generate CONNECTIONS + audyt | `SchemaGenLinkPotentials` | ✅ |
| [`Actions/ConnectMotorAction.cs`](Actions/ConnectMotorAction.cs) | Uzwojenia silnika (U/V/W) + generate CONNECTIONS | `SchemaGenConnectMotor` | ✅ sesja 1.7d |
| [`Actions/RenumberDevicesAction.cs`](Actions/RenumberDevicesAction.cs) | Numeracja DT (natywny renumber) | `SchemaGenRenumberDevices` | ✅ sesja 1.7d cd. |
| [`Actions/ForceGlobalCounterAction.cs`](Actions/ForceGlobalCounterAction.cs) | Globalny licznik DT (FUNC_COUNTER przez NameParts) | `SchemaGenForceGlobalCounter` | ✅ sesja 1.7g (Plan B) |
| [`Actions/AuditLayoutAction.cs`](Actions/AuditLayoutAction.cs) | Bbox vs ramka (JSON) | `SchemaGenAuditLayout` | ✅ sesja 1.6 |
| [`Actions/ExportConnectionsAction.cs`](Actions/ExportConnectionsAction.cs) | Eksport CSV | `SchemaGenExportConnections` | ✅ sesja 1.6 |

## Parametry akcji (nowe w 1.6)

### SchemaGenConnectMotor

Łączy uzwojenia silnika (U/V/W) przez `generate /TYPE:CONNECTIONS` + `gedRedraw`. **Nie** nadaje DT — numeracja urządzeń to osobny krok (natywny renumber EPLAN, sesja 1.7d).

| Parametr | Kierunek | Opis |
|----------|----------|------|
| `PROJECTPATH` | wejście | Ścieżka `.elk` (opcjonalna) |
| `OUTPUTPATH` | wejście | JSON wyniku (opcjonalny), np. `output/connect-motor.json` |
| `SILENT` | wejście | `1` — bez dialogu |

### SchemaGenRenumberDevices

Natywna numeracja oznaczeń urządzeń (DT) przez CLI `renumber /TYPE:DEVICES` + `gedRedraw`. Zastępuje ręczny remap DT (ślepa uliczka 1.7c, S063113). Działa na aktywnym projekcie — wymaga wcześniejszego `SchemaGenEnsureProject`.

| Parametr | Kierunek | Opis |
|----------|----------|------|
| `PROJECTPATH` | wejście | Ścieżka `.elk` (opcjonalna) |
| `OUTPUTPATH` | wejście | JSON wyniku (opcjonalny), np. `output/renumber-devices.json` — audyt DT po ostatnim przebiegu |
| `IDENTIFIER` | wejście | Identyfikator DT (np. `FC`, `MA`); wiele wartości: `;` lub `,` |
| `CONFIGSCHEME` | wejście | Nazwa schematu numeracji z EPLAN (pusty = domyślny projektu) |
| `STARTVALUE` | wejście | Wartość początkowa licznika (domyślnie `1` z `SchemaGenPaths`) |
| `STEPVALUE` | wejście | Krok licznika (domyślnie `1`) |
| `USESELECTION` | wejście | `0` = cały projekt (domyślnie) |
| `SILENT` | wejście | `1` — bez dialogu |

### SchemaGenForceGlobalCounter

Wymusza **globalny licznik DT** dla jednego identyfikatora — kolejne funkcje główne z danym `FUNC_CODE` dostają `STARTVALUE`, `STARTVALUE+STEPVALUE`, ... (np. `-MA1`, `-MA2` dla silników w różnych lokalizacjach). Mechanizm: `func.NameParts` → `FUNC_COUNTER` w `Transaction`+`SafetyPoint`; widoczne `DESIGNATION_PRODUCT` jest przekomponowane (KB datamodel.md:454). **Nie** pisze property `<20010>` wprost (ślepa uliczka S063113). Plan B sesji 1.7g — gdy natywny `CONFIGSCHEME` nie daje globalnych liczników. Wołane z MVP po `SchemaGenRenumberDevices` dla reguł `forceGlobalCounter="true"`.

| Parametr | Kierunek | Opis |
|----------|----------|------|
| `PROJECTPATH` | wejście | Ścieżka `.elk` (opcjonalna) |
| `IDENTIFIER` | wejście | Identyfikator DT (jeden, np. `MA`) — wymagany |
| `STARTVALUE` | wejście | Pierwszy licznik (domyślnie `1`) |
| `STEPVALUE` | wejście | Krok (domyślnie `1`) |
| `OUTPUTPATH` | wejście | JSON wyniku, np. `output/force-global-counter.json` (changed/total/log + audyt DT) |
| `SILENT` | wejście | `1` — bez dialogu |

### SchemaGenAuditLayout

| Parametr | Kierunek | Opis |
|----------|----------|------|
| `PROJECTPATH` | wejście | Ścieżka `.elk` (opcjonalna) |
| `PAGENAME` | wejście | Opcjonalna — jedna strona |
| `OUTPUTPATH` | wejście | Ścieżka JSON (np. `output/layout-audit.json`) |
| `SILENT` | wejście | `1` — bez dialogu |

### SchemaGenInsertPowerMacro (rozszerzenie)

| Parametr | Kierunek | Opis |
|----------|----------|------|
| `USE_FRAME_LAYOUT` | wejście | `1` — użyj `FrameLayoutCalculator` zamiast stałych MACROX/MACROY |

### SchemaGenExportConnections

| Parametr | Kierunek | Opis |
|----------|----------|------|
| `OUTPUTPATH` | wejście | Domyślnie `output/connections.csv` |
| `SILENT` | wejście | `1` — bez dialogu |

## MCP

Narzędzia MCP wołają powyższe akcje headless — patrz [`../../mcp/README.md`](../../mcp/README.md).

## Odnośniki

- Notatki: [`../../docs/eplan-api-notes.md`](../../docs/eplan-api-notes.md)
- Ścieżki EPLAN: [`../../docs/eplan-data-paths.txt`](../../docs/eplan-data-paths.txt)
- Orkiestracja: [`../SchemaGen_MVP.cs`](../SchemaGen_MVP.cs)
