# Dziennik sesji SchemaGen

Każda sesja = nowy wpis **na górze**. Ostatni wpis zawsze wskazuje następny krok.

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
