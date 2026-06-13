# Dziennik sesji SchemaGen

Każda sesja = nowy wpis **na górze**. Ostatni wpis zawsze wskazuje następny krok.

---

#### 2026-06-13 — sesja 1.7g (handoff Claude + dual-pass numbering-rules)

**Etap:** Faza 1 — numeracja DT: MA globalne (MA1+MA2), FC per-lokalizacja

**Problem (Filip):** build OK, ale na schemacie nadal **MA1 + MA1** (+B2, +B4). Probe `TryRenumber_MA` nie rozwiązał.

**Zrobione (Cursor/Filip):**
- `sync/prompts/1.7g-ma-global-dt.md` — prompt zadania dla Claude Cowork (ZW)
- `Start-ClaudeSession.cmd` + `Start-ClaudeSession.ps1` — GitSync + prompt do schowka
- `docs/claude-opus-instructions.md` — sekcja 16 (obowiązkowy prompt z `sync/prompts/`)
- **MVP:** parser `numbering-rules.xml`, dual-pass `SchemaGenRenumberDevices` (FC → MA z CONFIGSCHEME)
- **Akcja:** `STARTVALUE` / `STEPVALUE` z ctx (fallback `SchemaGenPaths`)
- Handoff: `sync/filip-to-zw.md`, `sync/TASKS.md`

**[RYZYKO] Niezweryfikowane w EPLAN:**
- Czy dual-pass z pliku reguł daje widoczne MA1+MA2 (zależy od CONFIGSCHEME w Hello_world)
- Jeśli nadal MA1+MA1 → Plan B: FUNC_COUNTER w add-inie (zadanie #6 TASKS, ZW)

**Następny krok (Filip):**
1. `build_addin.ps1` + kopia `SchemaGen_MVP.cs` + `config/numbering-rules.xml` → `Skrypty\Schemagen\config\`
2. Przeładuj DLL, świeży Hello_world, uruchom MVP
3. Sprawdź `-MA1`/`-MA2` na +B2/+B4, `output/renumber-devices.json`, layout bez regresji
4. Wynik → `sync/filip-to-zw.md` (jeśli nadal MA1+MA1, ZW bierze Plan B)

#### 2026-06-13 — sesja 1.7e (fix RenumberDevices + audyt DT)

**Wynik testu MVP po merge (Filip):**
- Widoczne nazwy: **FC1** na str. 1 i 3, **FC2** na str. 2; **silniki MA1** bez zmian na wszystkich stronach.
- **Przyczyna:** schemat numeracji Hello_world numeruje **per lokalizacja** — na rysunku widać tylko `-FC1` (lokalizacja w nagłówku strony). Pełne DT: `=SCHEMAGEN+MAIN-FC1`, `=SCHEMAGEN+A2-FC2`, `=SCHEMAGEN+B4-FC1` — unikalne.
- **Bug w kodzie:** `RenumberDevicesAction` wołał niepełne `renumber /TYPE:DEVICES` (bez USESELECTION/STARTVALUE/STEPVALUE/POSTNUMERATE). Naprawiono — pełna linia CLI jak w `SchemaGen_TryRenumber.cs`.
- **Audyt:** `renumber-devices.json` zawiera listę `devices[]` (page, location, funcCode, funcCounter, visibleName, fullTag).
- **Globalne FC1/FC2/FC3 i MA1/MA2/MA3 na rysunku:** wymaga parametru `CONFIGSCHEME` (nazwa schematu „cały projekt” z Ustawienia projektu → Numeracja w EPLAN). Polityka MA per projekt — nie hardkodować.

**Następny krok:** `build_addin.ps1` → przeładuj DLL → MVP na świeżym Hello_world → sprawdź `output/renumber-devices.json` i DT na schemacie.

#### 2026-06-13 — sesja 1.7f (globalne MA) — probe + kontrakt reguł, czeka na test EPLAN
**Etap:** Faza 1 — numeracja DT: MA globalne (MA1, MA2), FC per-lokalizacja zostaje

**Root cause:** silniki są w różnych lokalizacjach (+B2, +B4). `=SCHEMAGEN+B2-MA1` i `+B4-MA1` to dla EPLAN **unikalne pełne DT** (różni je lokalizacja), więc `renumber` z domyślnym schematem (per-lokalizacja) zostawia MA1 wszędzie. Zakres liczenia ustawia **schemat numeracji (CONFIGSCHEME)**, nie `/IDENTIFIER` (ten tylko filtruje DT w przebiegu).

**Decyzja (od Filipa):** rozwiązanie **config-driven** — polityka numeracji per identyfikator w pliku, docelowo generowanym przez LLM/aplikację. Mechanizm: natywny EPLAN, dual-pass z różnym CONFIGSCHEME per identyfikator. Bez hardkodu, bez walki z chronionym `<20010>`.

**Zrobione:**
- `config/numbering-rules.xml` — kontrakt reguł (FC perLocation, MA projectWide, `configScheme` do uzupełnienia). Format pod przyszły generator.
- `scripts/SchemaGen_TryRenumber_MA.cs` — probe dual-pass: potwierdza `/IDENTIFIER` + `/CONFIGSCHEME` i nazwy schematów dające globalne MA.
- Akcja `SchemaGenRenumberDevices` (rozszerzona przez Filipa) już wspiera `CONFIGSCHEME`, `IDENTIFIER` (split `;`/`,`), audyt `FUNC_CODE`/`FUNC_COUNTER` → `renumber-devices.json`.

**[RYZYKO] do zrobienia u Filipa (blokuje wpięcie orkiestracji):**
- `/IDENTIFIER` i `/CONFIGSCHEME` **niepotwierdzone** — KB ma tylko „renumber | numbering functionality”. Probe wykaże czy działają (S025019 = nie).
- Schemat „cały projekt” musi **istnieć z nazwy** w EPLAN — utwórz/znajdź w Ustawienia → Projekty → Urządzenia → Numeracja offline; wpisz do probe, potem do `numbering-rules.xml`.
- Brak `output/renumber-devices.json` (MVP z nową akcją jeszcze nie puszczony).

**Następny krok (1.7f cd. — po probe):**
1. Filip: uruchom MVP (świeży Hello_world), potem `SchemaGen_TryRenumber_MA.cs`; podaj działające nazwy schematów + przyślij `renumber-devices.json`.
2. Wpięcie config-driven: MVP czyta `numbering-rules.xml` i woła akcję per reguła (IDENTIFIER + CONFIGSCHEME); fallback = obecny pojedynczy renumber (brak regresji). Akcja: czytaj START/STEP z ctx (fallback consts).
3. Test: MA1+MA2 widoczne, FC bez zmian, layout RY bez regresji.

---

#### 2026-06-13 — sesja 1.7d cd. (zad. 1+2: RenumberDevices) — kod gotowy, build u Filipa
**Etap:** Faza 1 — natywna numeracja DT + domknięcie pipeline MVP

**Zrobione:**
- Nowa akcja **`SchemaGenRenumberDevices`** ([`Actions/RenumberDevicesAction.cs`](../scripts/addin/Actions/RenumberDevicesAction.cs)) — wrapper CLI `renumber /TYPE:DEVICES` + `gedRedraw`. Ordinal 26. Params: `PROJECTPATH`, `OUTPUTPATH` (`renumber-devices.json`), `SILENT`. JSON: `renumbered`, `viewRefreshed`. Składnia potwierdzona ręcznym testem (FC1→FC2 OK, MA per-lokalizacja OK).
- Pipeline MVP ([`SchemaGen_MVP.cs`](../scripts/SchemaGen_MVP.cs)): **LinkPotentials → ConnectMotor → RenumberDevices → AuditLayout**. Dodano `RenumberDevices()` + guard `SchemaGenRenumberDevices` w obu blokach `EnsureAddInLoaded`.
- Docs: `addin/README.md` (wiersz + sekcja parametrów), `eplan-api-notes.md`.

**[RYZYKO] Niezweryfikowane (do zrobienia u Filipa):**
- Build: `scripts/build_addin.ps1` — kompilacji nie da się uruchomić w sandbox (Linux, brak csc + DLL EPLAN). Uruchom, potwierdź 0 błędów. **Przeładuj DLL w EPLAN** — pojawi się akcja `SchemaGenRenumberDevices`.
- Test pipeline: po `renumber` sprawdź DT na schemacie (brak duplikatów `-FC1` str.1/2, MA per-lokalizacja) i `output/renumber-devices.json`.
- **[RYZYKO] Git:** index znów uszkodzony (`index.lock` — `Operation not permitted` z sandboxa; `git status` pokazuje wszystko jako `D`). Z poziomu agenta nie da się usunąć `index.lock` ani zrobić `reset`. Filip: na Windows usuń `.git/index.lock`, `git reset` (mixed), potem normalny commit/push.

**Następny krok (sesja 1.7e):**
1. Test EPLAN całego pipeline + kalibracja, jeśli renumber zmienia layout.
2. Zad. 3: `SchemaGenSetDesignations` (jawne DT z parametrów/JSON) — jeśli numeracja natywna nie wystarcza.
3. Polityka MA: reguły per projekt od Filipa (nie hardkodować).

---

#### 2026-06-13 — sesja 1.7d (zad. 5: refaktor RemapTags) — kod gotowy, build u Filipa
**Etap:** Faza 1 — usunięcie martwego kodu DT, rename akcji

**Zrobione:**
- Usunięto `MacroAdaptation.RemapMotorTag` (ślepa uliczka DT z 1.7c: `func.Name`/`NameParts`/`<20010>` → S063113). Zostało `ConnectMotorWindings` + `IsMotorFunction`.
- Akcja `SchemaGenRemapTags` → **`SchemaGenConnectMotor`** (`ConnectMotorAction.cs`). Usunięto pętlę remap + param `MOTORTAG`; akcja łączy tylko uzwojenia U/V/W (`generate CONNECTIONS` + `gedRedraw`). JSON: `connectionPasses`, `viewRefreshed`.
- Skrypt diag. `SchemaGen_RemapTags.cs` → `SchemaGen_ConnectMotor.cs`.
- Orchestrator `SchemaGen_MVP.cs`: `RemapMotorTags`→`ConnectMotor`, `FindAction`/`Execute` na nową nazwę, OUTPUTPATH `remap-tags.json`→`connect-motor.json`.
- Docs: `addin/README.md`, `claude-opus-instructions.md` (tabela akcji).
- Pipeline MVP bez zmian funkcjonalnych: LinkPotentials → ConnectMotor → AuditLayout.

**[RYZYKO] Niezweryfikowane (do zrobienia u Filipa):**
- Build: `scripts/build_addin.ps1` — kompilacji nie dało się uruchomić w sandbox (Linux, brak csc + DLL EPLAN). Uruchom i potwierdź 0 błędów.
- Git index w repo był uszkodzony (`bad signature` / `index.lock`) — rename plików zrobiony przez `mv`, nie `git mv`. Przy commicie sprawdź `git status` (stare nazwy jako delete, nowe jako add).

**Następny krok (sesja 1.7d cd.):**
1. Zad. 1+4: przechwyć linię `renumber /...` z Action Monitor (Projekt → Numeruj na `=SCHEMAGEN*`) → akcja `SchemaGenRenumberDevices` jako wrapper CLI.
2. Zad. 3: `SchemaGenSetDesignations` (jawne DT z parametrów/JSON).
3. Zad. 6: czeka na `docs/electrical-domain.md` od Filipa.

---

#### 2026-06-11 — sesja 1.7c (debug layout RY + DT) — częściowy sukces
**Etap:** Faza 1 — layout ✅ (RY) | numeracja DT ❌ ślepa uliczka

**Działa — zachować (commit `aaba7b4`+):**
- **Layout RY:** `MeasureContentObjects` + `ShiftPlacementsRy` w `InsertPowerMacroAction` — makro w ramce góra/dół po korekcie; **RX nietknięty**
- **Frame A3:** `FrameMin 35/35`, `FrameMax 287/415`
- Skrypty diagnostyczne: `SchemaGen_AuditLayout.cs`, `SchemaGen_RemapTags.cs` (tylko CLI → akcje DLL, bez DataModel w skrypcie)

**Nie działa — DT / tagi urządzeń:**
- `func.Name`, `NameParts`, czyszczenie property `<20010>` (S063113) — nie zmieniają widocznego DT na schemacie
- Duplikaty: `=SCHEMAGEN+MAIN-FC1` na str. 1 i 2; silniki `=SCHEMAGEN+B2-MA1` / `+B4-MA1` wyświetlają się jako `-MA1` (lokalizacja w nagłówku strony)
- Stałe `MotorPlant=MACHINE` / `MotorLocation=CABINET` **błędne** — realna struktura: `=SCHEMAGEN` + lokalizacje per makro (+MAIN, +A2, +B2, +B4)

**Następny krok (sesja 1.7d):**
1. Porzucić ręczny `RemapDeviceTags` → natywna numeracja EPLAN (akcja renumber / Projekt → Numeruj)
2. Ręczny test numeracji w Hello_world → decyzja: MA globalne vs per-lokalizacja
3. Commit porządkujący: cofnąć martwy kod DT, zostawić layout + skrypty diag.

**Prompt na start sesji 1.7d:**
```
Kontekst: @docs/session-log.md @docs/eplan-api-notes.md
Sesja 1.7d: Zastąp RemapDeviceTags akcją natywnej numeracji EPLAN. Layout RY nie ruszać.
```

---

#### 2026-06-09 — sesja 1.6 + Faza 1b MCP (implementacja)
**Etap:** Faza 1 sesja 1.6 ✅ + Faza 1b fundament MCP ✅ — test EPLAN do wykonania

**Zrobione (sesja 1.6):**
- `SchemaGenRemapTags` — podmiana tagów silnika na `=MACHINE+CABINET-M1` + `generate CONNECTIONS` (uzwojenia U/V/W)
- `MacroAdaptation.RemapMotorTag` / `ConnectMotorWindings` — SafetyPoint + Transaction
- Orkiestracja MVP: po LinkPotentials → RemapTags → AuditLayout

**Zrobione (layout + MCP):**
- `PlacementBounds`, `FrameLayoutCalculator` — auto-pozycjonowanie (`USE_FRAME_LAYOUT=1` w MVP)
- `SchemaGenAuditLayout` — JSON bbox vs ramka → `output/layout-audit.json`
- `SchemaGenExportConnections` — CSV pod Fazę 2
- MCP `schemagen-eplan` — [`mcp/schemagen_eplan/server.py`](../mcp/schemagen_eplan/server.py)
- Walidacja: [`scripts/validation/validate_connections.py`](../scripts/validation/validate_connections.py) + [`config/validation-rules.json`](../config/validation-rules.json)
- Konfiguracja: [`.cursor/mcp.json`](../.cursor/mcp.json), [`config/claude_desktop_config.example.json`](../config/claude_desktop_config.example.json)

**Test EPLAN (kroki):**
1. `powershell scripts/build_addin.ps1`
2. Skopiuj `scripts/SchemaGen_MVP.cs` → `Skrypty\Schemagen\`
3. Narzędzia → Skrypty → `SchemaGen_MVP.cs`
4. Sprawdź: tag `=MACHINE+CABINET-M1`, pliki w `output/` (layout-audit.json, remap-tags.json)

**Następny krok:** test EPLAN → kalibracja `FrameMinRy/Rx/MaxRy/Rx` w `SchemaGenPaths.cs` po `layout-audit.json` → Faza 2 pełna pętla przez MCP `eplan_closed_loop`

**Prompt na start sesji 1.7:**
```
Kontekst: @docs/project-context.txt @docs/eplan-data-paths.txt @docs/ROADMAP.md @docs/eplan-api-notes.md
Po teście sesji 1.6: skoryguj Frame* w SchemaGenPaths.cs wg layout-audit.json. Uruchom eplan_closed_loop i dopracuj reguły validation-rules.json.
```

---

#### 2026-06-09 — koniec dnia (podsumowanie sesji 1.5)
**Etap:** Faza 1 — sesja 1.5 ✅ domknięta (pipeline OK, layout w ramce: **NIE**)

**Co działa:**
- Pełny pipeline: XML → 3 strony → 3 makra → `SchemaGenLinkPotentials`
- `MacroFitCalculator` — bbox offset per makro (cache `macro-offsets.xml` v3)
- `MacroAdaptation` — normalizacja potencjałów, PlaceHolder
- Add-in + `build_addin.ps1` — deploy bez Visual Studio

**Co nie działa — schematy poza ramką:**
- Makra są widoczne, ale **nie mieszczą się w ramce druku** strony EPLAN
- Przyczyna: brak algorytmu „dopasuj do ramki” — tylko ręczne stałe `MacroInsertRy/Rx` + offset makra
- Agent nie widzi wyniku w EPLAN → iteruje na ślepo; kod „wygląda OK”, ale bez sprzężenia zwrotnego
- Pułapka osi: `PointD(X,Y)` → X=RY, Y=RX (zmiana `MacroInsertY` przesuwa RX, nie RY)
- Aktualne współrzędne w kodzie: `RY=-1.0`, `RX=18.0` — [`SchemaGenPaths.cs`](../scripts/addin/SchemaGenPaths.cs)

**Otwarte (poza ramką):**
- Tagi PLC surowe `[20171<218<...]` — `RemapFunctionStructure` wyłączone (S063111)
- Pełna weryfikacja odnośników potencjałów między stronami

**Kierunek na przyszłość — MCP (zamknięty obieg):**
- Serwer `schemagen-eplan` — agent uruchamia skrypt, dostaje bbox/CSV/screenshot bez klikania
- Narzędzia: `eplan_run_script`, `eplan_build_addin`, `eplan_get_layout`, `eplan_export_connections`
- Akcja add-in `SchemaGenAuditLayout` — bbox makra vs granice ramki strony
- `FrameLayoutCalculator` — auto-pozycjonowanie zamiast ręcznych stałych
- Ten sam MCP dla **Cursor** i **Claude Cowork** (plan 5h, praca gdy użytkownika nie ma przy PC)
- Konfiguracja Cowork: `%APPDATA%\Claude\claude_desktop_config.json`

**Stan Fazy 1:** ~5/6 sesji MVP — brakuje sesji 1.6 i rozwiązania layoutu w ramce.

**Następna sesja (1.6 + fundament MCP):**
1. Połączenia uzwojenia silnika + tagi `=MACHINE+CABINET-M1`
2. Szkielet `SchemaGenAuditLayout` (bbox vs ramka)
3. Szkielet MCP `schemagen-eplan` (build + run + layout)

**Prompt na start sesji 1.6:**
```
Kontekst: @docs/project-context.txt @docs/eplan-data-paths.txt @docs/ROADMAP.md @docs/eplan-api-notes.md
1. Sesja 1.6: połączenia uzwojenia silnika + tagi =MACHINE+CABINET-M1
2. Dodaj akcję SchemaGenAuditLayout (bbox makra vs ramka strony) — fundament pod MCP
3. Szkielet MCP servera schemagen-eplan (eplan_run_script, eplan_build_addin)
```

---

#### 2026-06-09 — sesja 1.5 (feedback z testu EPLAN + poprawki)
**Etap:** Faza 1 — sesja 1.5 — poprawki po teście
**Problemy z testu:**
- RY=-0,6 zamiast docelowego 0,6; zmiana 8.35→9.85 przesuwała **RX**, nie RY
- Potencjały: `=GAA-2L1` (falownik) vs `2L1` (400V) — brak odnośników
- Tagi PLC: surowe stringi `[20171<218<44025...]` — struktura =GAA z Sample Project

**Poprawki:**
- **Oś RY/RX:** `PointD(X,Y)` → X=RY, Y=RX; `MacroInsertRy=17.2` (+1,2), `MacroInsertRx=8.35` (cofnięte 9.85) — [`SchemaGenPaths.cs`](../scripts/addin/SchemaGenPaths.cs)
- **Adaptacja makra:** [`MacroAdaptation.cs`](../scripts/addin/MacroAdaptation.cs) — remap =GAA→SCHEMAGEN, normalizacja potencjałów, PlaceHolder
- **LinkPotentials:** normalizacja przed `generate CONNECTIONS`
- **Architektura 2 etapy:** [`docs/macro-pipeline.md`](macro-pipeline.md)

**Retest:** `build_addin.ps1` + kopia MVP → uruchom skrypt, sprawdź RY=0,6, odnośniki 2L1, tagi PLC

---

#### 2026-06-09 — sesja 1.5 (implementacja)
**Etap:** Faza 1 — sesja 1.5 — implementacja ✅, test EPLAN do wykonania
**Zrobione:**
- **Layout:** `MacroInsertY` / `DriveMacroInsertY` / `ControlMacroInsertY` = **9.85** (było 8.35) w [`SchemaGenPaths.cs`](../scripts/addin/SchemaGenPaths.cs) i [`SchemaGen_MVP.cs`](../scripts/SchemaGen_MVP.cs)
- **Strona 3 + Start/Stop:** makro `Fan_motor_control_two_switches.ema` (Opcja 1 — dedykowane `.ema` z biblioteki Schemagen)
- **Odnośniki potencjałów:** nowa akcja `SchemaGenLinkPotentials` — `generate CONNECTIONS` + audyt `InterruptionPoint` / `PotentialDefinition` (CrossReferencedObjectsAll)
- **Orkiestracja MVP:** 3 strony → LinkPotentials na końcu

**Test EPLAN (kroki):**
1. `powershell scripts/build_addin.ps1` (DLL → `Skrypty\Schemagen\`)
2. Skopiuj `scripts\SchemaGen_MVP.cs` → `C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\`
3. Zamknij inne projekty → Narzędzia → Skrypty → `SchemaGen_MVP.cs`
4. Oczekiwany wynik: 3 strony (400V, napęd, Start/Stop), makra na Y=9.85, dialog audytu odnośników

**Następny krok:** po teście → **Sesja 1.6** (połączenia silnika + podmiana tagów)

**Prompt na start sesji 1.6:**
```
Kontekst: @docs/project-context.txt @docs/eplan-data-paths.txt @docs/ROADMAP.md @docs/eplan-api-notes.md
Sesja 1.6: Podłącz uzwojenie silnika do falownika i podmień oznaczenia (=MACHINE+CABINET-M1).
```

---

#### 2026-06-07 — koniec dnia (sesja 1.4+)
**Etap:** Faza 1 — sesja 1.4 ✅ domknięta
**Zrobione (dodatkowo):**
- **Fix nawigatora stron:** `CreatePageAction.cs` — `Properties.Page.PAGE_NOMINATIOMN` (#11011), nie #11013 (`PAGE_SUBCOUNTER`); opisy widoczne w drzewie ✅
- **Test EPLAN OK:** nazwy „Zasilanie 400VAC” / „Sterowanie napędem” w nawigatorze

**Na sesję 1.5 (pierwszy krok):**
- **Obniżyć oba makra o 1,5 jednostki RY** (= **dodać** 1,5 do Y) — `MacroInsertY` i `DriveMacroInsertY` w `SchemaGenPaths.cs` (obecnie **8.35** → docelowo **9.85**); makra są zbyt wysoko na stronie
- Zweryfikować odnośniki między stronami (`generate CONNECTIONS` / interruption points)
- Obwód Start/Stop na stronie 3

**Prompt na start sesji 1.5:**
```
Kontekst: @docs/project-context.txt @docs/eplan-data-paths.txt @docs/ROADMAP.md @docs/eplan-api-notes.md
Sesja 1.5: Obniż makra o 1,5 RY — dodaj 1,5 do Y (MacroInsertY/DriveMacroInsertY: 8.35→9.85). Zweryfikuj odnośniki między stronami, dodaj obwód Start/Stop na stronie 3.
```

---

#### 2026-06-07 — koniec dnia
**Etap:** Faza 1 — sesja 1.4 ✅ zakończona (implementacja + test EPLAN + debug layoutu)
**Podsumowanie dnia:** trzy iteracje sesji 1.3→1.4 — od pierwszego makra 400V, przez parser XML i makro falownika, po decyzję o **dwóch stronach**, opisy stron, strojenie pozycji makr (Y=8.35) i `generate CONNECTIONS`. Faza 1 na 4/6 sesji MVP.

#### 2026-06-07
**Etap:** Faza 1 — sesja 1.4 debug ✅ (dwie strony, opisy, generate) — częściowy sukces
**Zrobione:**
- `SchemaGen_MVP.cs` — **dwie strony**: `powerPageName` (400VAC) + `drivePageName` (falownik); po makrach `generate /TYPE:CONNECTIONS`
- `CreateSchematicPage(..., description)` — parametr `PAGEDESCRIPTION` do add-inu
- `CreatePageAction.cs` — opis strony po `Create()` przez `Properties[11013]` (brak `Properties.Page.PAGEDESCRIPTION` w API 2025)
- `SchemaGenPaths.cs` — `DrivePageDescription`, `MacroInsertY` / `DriveMacroInsertY` = **8.35** (wycentrowanie w ramce; wcześniej testowano 6.35)
- **Test EPLAN OK:** dwa makra na dwóch stronach, opisy stron, dialog z `Typ napędu (XML): 1,5 kW`

**Otwarte (sesja 1.5):**
- Czy `generate /TYPE:CONNECTIONS` tworzy **odnośniki** między punktami przerwania na stronach? (punkty są, link między stronami — do weryfikacji)
- Obwód Start/Stop na **stronie 3**
- Docelowo: API `PotentialDistributionPoint` / interruption points — czytanie i ustawianie powiązań potencjałów między stronami

**Deploy:** `build_addin.ps1` (CreatePage, Paths) + kopia `SchemaGen_MVP.cs` do `Skrypty\Schemagen\`

**Prompt na start sesji 1.5:**
```
Kontekst: @docs/project-context.txt @docs/eplan-data-paths.txt @docs/ROADMAP.md @docs/eplan-api-notes.md
Sesja 1.5: Zweryfikuj odnośniki między stronami (generate CONNECTIONS / interruption points), dodaj obwód Start/Stop na stronie 3.
```

---

#### 2026-06-07
**Etap:** Faza 1 — sesja 1.4 (XML + makro falownika) — implementacja ✅, test EPLAN do wykonania
**Zrobione:**
- `scripts/SchemaGenConfig.cs` — parser `ConfigurationVariable`, resolve ścieżki XML (primary + fallback)
- `SchemaGen_MVP.cs` — łańcuch: LoadConfig → CreatePage → 400V → Frequency_Control
- `SchemaGenPaths.cs` — `FrequencyControl`, `DriveMacroInsertX/Y`
- `InsertPowerMacroAction.cs` — opcjonalne `MACROX`, `MACROY`, `DRIVETYPE`
- `build_addin.ps1` OK — DLL skopiowana do EPLAN

**Test EPLAN (kroki):**
1. Skopiuj do `C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\`: tylko `SchemaGen_MVP.cs` (usuń `SchemaGenConfig.cs` jeśli jest)
2. Skopiuj `config\901_Drive_Design.xml` → `Skrypty\Schemagen\config\`
3. Zamknij inne projekty → Narzędzia → Skrypty → `SchemaGen_MVP.cs`
4. Oczekiwany wynik: dwa makra na stronie + dialog z `Typ napędu (XML): 1,5 kW`

**Następny krok:** po teście EPLAN → **Sesja 1.5** (obwód przekaźnika Start/Stop)

**Prompt na start sesji 1.5:**
```
Kontekst: @docs/project-context.txt @docs/eplan-data-paths.txt @docs/ROADMAP.md
Sesja 1.5: Dodaj obwód przekaźnika Start/Stop (przyciski + cewka KA + styk podtrzymujący).
```

---

#### 2026-06-07
**Etap:** Faza 1 — sesja 1.3 (makro zasilania 400V) ✅
**Zrobione:**
- Add-in w `scripts/addin/` — mapa plików: `scripts/addin/README.md`
- Akcja `SchemaGenInsertPowerMacro` → makro 400V na stronie z `PAGENAME`
- `SchemaGen_MVP.cs` — łańcuch: CreatePage → PAGENAME → InsertPowerMacro
- `build_addin.ps1` + `watch_addin.ps1` — kompilacja, auto-kopia DLL do EPLAN
- **Test EPLAN OK:** makro `400VAC_Power_Supply.ema` widoczne na `=SCHEMAGEN+MAIN/N`

**Następny krok:** **Sesja 1.4** — parsuj XML + wstaw `Frequency_Control.ema`

**Prompt na start sesji 1.4:**
```
Kontekst: @docs/project-context.txt @docs/eplan-data-paths.txt @docs/ROADMAP.md @config/901_Drive_Design.xml
Sesja 1.4: Parsuj XML konfiguracji i wstaw makro Frequency_Control.ema na stronę.
```

---

#### 2026-06-05
**Etap:** Faza 1 — sesja 1.2 (nowa strona schematu)
**Zrobione:**
- `scripts/addin/SchemaGenAddIn.cs` — add-in z akcją `SchemaGenCreatePage` (DataModel)
- `scripts/build_addin.ps1` — kompilacja DLL bez Visual Studio
- `scripts/SchemaGen_MVP.cs` — otwarcie projektu + wywołanie akcji tworzenia strony
- Ograniczenie skryptów `.cs`: brak `DataModel` w kompilatorze (potwierdzone w Scripts.html EPLAN 2025)

**Następny krok:** Test w EPLAN → **Sesja 1.3** — wstaw `400VAC_Power_Supply.ema`

**Test sesji 1.2:**
1. `powershell scripts/build_addin.ps1`
2. Skopiuj `dist/SchemaGen.EplAddin.dll` + `SchemaGen_MVP.cs` do `C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\`
3. EPLAN → API → Zarządzaj → Wczytaj → `SchemaGen.EplAddin.dll` (jednorazowo)
4. Uruchom skrypt → oczekiwana strona `=SCHEMAGEN+MAIN/1` w nawigatorze stron

**Prompt na start sesji 1.3:**
```
Kontekst: @docs/project-context.txt @docs/eplan-data-paths.txt @docs/ROADMAP.md
Sesja 1.3: Rozszerz SchemaGen o wstawienie makra 400VAC_Power_Supply.ema na utworzoną stronę.
```

---

#### 2026-06-05
**Etap:** Faza 1 — sesja 1.1 (otwarcie projektu — częściowy sukces)
**Zrobione:**
- `SchemaGen_MVP.cs` — otwarcie przez `ProjectOpen /Project:"...Hello_world.elk"`
- Poprawka ścieżki: plik `.elk`, nie katalog `.edb`
- Notatki w `docs/eplan-api-notes.md`

**Następny krok:** Sesja 1.2 — nowa strona schematu (wymaga add-in DLL)

---

#### 2026-06-05
**Etap:** Faza 0 — fundament (zakończony)
**Zrobione:**
- Struktura repo (`docs/`, `config/`, `scripts/`)
- Reguły Cursor (`.cursor/rules/eplan-schemagen.mdc`)
- `docs/eplan-data-paths.txt` — zweryfikowane ścieżki EPLAN
- `docs/ROADMAP.md` — ścieżka rozwoju faz 0–6
- `config/901_Drive_Design.xml` — przykładowa konfiguracja
- Usunięto archiwum `AutoGen/`

**Następny krok:** Nowy chat → **Sesja 1.1** — minimalny skrypt otwierający `Hello_world.edb`

**Prompt na start sesji 1.1:**
```
Kontekst: @docs/project-context.txt @docs/eplan-data-paths.txt @docs/ROADMAP.md
Sesja 1.1: Napisz scripts/SchemaGen_MVP.cs który otwiera Hello_world.edb
i pokazuje komunikat sukcesu. Wzorzec: PageNavi_ContextMenu_OpenFolders.cs
```

**Możliwości rozwoju:** Po 1.1 → 1.2 (nowa strona) → 1.3 (pierwsze makro). Nie przeskakiwać faz.

---

#### 2026-06-05 (wcześniej)
**Etap:** Faza 0 — organizacja repo (w toku)
**Zrobione:** struktura folderów, reguły Cursor, `eplan-data-paths.txt`, pliki kontekstowe w `docs/`
**Następny krok:** ROADMAP.md + session-log.md + config XML
**Możliwości rozwoju:** skopiować XML do `config/`, usunąć `AutoGen/`
