# Dziennik sesji SchemaGen

Każda sesja = nowy wpis **na górze**. Ostatni wpis zawsze wskazuje następny krok.

---

#### 2026-06-07
**Etap:** Faza 1 — sesja 1.3 (makro zasilania 400V)
**Zrobione:**
- Add-in rozbity na małe pliki w `scripts/addin/` — mapa: `scripts/addin/README.md`
- Nowa akcja `SchemaGenInsertPowerMacro` → `Insert.WindowMacro` na stronie z `PAGENAME`
- `SchemaGen_MVP.cs` — łańcuch: CreatePage → odczyt PAGENAME → InsertPowerMacro
- `build_addin.ps1` — kompilacja wszystkich `addin/**/*.cs`
- Kompilacja DLL: OK (`dist/SchemaGen.EplAddIn..dll`)

**Następny krok:** Test w EPLAN → **Sesja 1.4** — parsuj XML + wstaw `Frequency_Control.ema`

**Test sesji 1.3:**
1. Zamknij inne projekty EPLAN (tylko `Hello_world.elk`)
2. `powershell scripts/build_addin.ps1`
3. Skopiuj `dist/SchemaGen.EplAddIn..dll` + `SchemaGen_MVP.cs` do `C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\`
4. Po zmianie DLL: EPLAN → API → Zarządzaj → Wczytaj
5. Uruchom skrypt → oczekiwane makro 400V na nowej stronie `=SCHEMAGEN+MAIN/N`

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
