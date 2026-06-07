# Skrypty EPLAN

Kod źródłowy skryptów C# dla EPLAN API.

| Plik | Opis |
|------|------|
| [`SchemaGen_MVP.cs`](SchemaGen_MVP.cs) | Orchestrator MVP — otwarcie projektu, create page, insert macro |

Po testach kopiuj gotowy skrypt do folderu uruchomieniowego EPLAN:

`C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\`

Uruchomienie: EPLAN → Narzędzia → Skrypty.

## Add-in (od sesji 1.2)

Skrypty `.cs` nie mają dostępu do `DataModel` / `HEServices` — tworzenie stron i makr wymaga DLL.

**Mapa plików add-in:** [`addin/README.md`](addin/README.md)

| Plik | Opis |
|------|------|
| [`build_addin.ps1`](build_addin.ps1) | Kompilacja → `dist/SchemaGen.EplAddIn..dll` |
| [`addin/`](addin/) | Źródła DLL (moduł, helpers, actions) |

```powershell
.\scripts\build_addin.ps1
# opcjonalnie: -EplanBin "C:\Program Files\EPLAN\Platform\2025.0.3\Bin"
```

DLL kopiuj do `C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\` i zarejestruj w EPLAN API.

## Narzędzia bazy wiedzy EPLAN API

| Skrypt | Opis |
|--------|------|
| `extract_eplan_docs.py` | Ekstrakcja 104 plików HTML → `docs/eplan-kb/raw-extract.json` |
| `build_eplan_kb.py` | Budowa `docs/eplan-kb/topics/*.md`, INDEX, actions-index |

Źródło HTML: `C:\Users\Filip\Desktop\startUp\AutoGen\EPLAN API docs`
