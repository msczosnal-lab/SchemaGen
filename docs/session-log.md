# Dziennik sesji SchemaGen

Każda sesja = nowy wpis **na górze**. Ostatni wpis zawsze wskazuje następny krok.

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
