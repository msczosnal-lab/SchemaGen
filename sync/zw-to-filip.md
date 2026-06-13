# Skrzynka: ZW → Filip

> Pisze **tylko ZW** (Cowork/Claude). Filip czyta na starcie sesji i nie edytuje tego pliku.
> Najnowsze wpisy na górze.

---

## 2026-06-13 [ZW] — Plan B: globalny FUNC_COUNTER (MA1+MA2)

Temat: Plan A (CONFIGSCHEME) odrzucony po Twoim teście. Wdrożony Plan B — wymuszenie licznika w add-inie.

Co zmieniłem:
- Nowa akcja `SchemaGenForceGlobalCounter` (`scripts/addin/Actions/ForceGlobalCounterAction.cs`) — kolejnym silnikom (FUNC_CODE=MA) nadaje MA1, MA2... przez `NameParts.FUNC_COUNTER` (Transaction+SafetyPoint). NIE rusza `<20010>`. Build CS0266 naprawiony (getter zwraca `FunctionBasePropertyList`).
- `config/numbering-rules.xml`: reguła MA → `configScheme=""` + `forceGlobalCounter="true"`.
- `SchemaGen_MVP.cs`: pass 2 woła nową akcję dla reguł z flagą; guard wymusza reload DLL.

Do zrobienia po stronie Filip:
1. `.\scripts\build_addin.ps1` (powinno przejść — sprawdź 0 błędów).
2. Skopiuj `SchemaGen_MVP.cs` + `config/numbering-rules.xml` → `Skrypty\Schemagen\config\`.
3. Przeładuj DLL (pojawi się `SchemaGenForceGlobalCounter`), świeży Hello_world, uruchom MVP.
4. Sprawdź: `-MA1` na +B2, `-MA2` na +B4; FC bez zmian; `output/force-global-counter.json` → `changed==total`, brak `ERR` w `log`; layout bez regresji.
5. Jeśli `ERR` w logu (NameParts) → przyślij `force-global-counter.json`, mam alternatywę (świeży `FunctionBasePropertyList` z plant/location/code).

Commit: (auto GitSync po push)

---

## 2026-06-13 [ZW]
Temat: Uruchomiona magistrala koordynacji.
Kontekst: Dodałem `GitSyncDaemon.ps1`, `Install-GitSyncTask.ps1` i katalog `sync/`. Po Twojej stronie zarejestruj daemon (patrz `docs/git-sync-setup.md`).
Do zrobienia po stronie Filip: uruchom `Install-GitSyncTask.ps1 -MachineTag Filip -RepoPath "C:\Users\Filip\Desktop\Cursor\SchemaGen"`.
Commit: —
