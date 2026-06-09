# Skrypty EPLAN



Kod źródłowy skryptów C# dla EPLAN API.



## Status Fazy 1



| Sesja | Pliki | Test EPLAN |

|-------|-------|------------|

| 1.1 ✅ | `SchemaGen_MVP.cs` (OpenProject) | Projekt otwarty |

| 1.2 ✅ | `addin/Actions/CreatePageAction.cs` | Strona `=SCHEMAGEN+MAIN/N` |

| 1.3 ✅ | `addin/Actions/InsertPowerMacroAction.cs` | Makro 400V na stronie |

| 1.4 ✅ | `SchemaGen_MVP.cs`, `CreatePageAction.cs`, `InsertPowerMacroAction.cs` | Dwie strony + XML + generate CONNECTIONS |
| 1.5 | `LinkPotentialsAction.cs`, strona 3 Start/Stop, Y=9.85 | Trzy strony + audyt odnośników (test do wykonania) |



## Pliki runtime



| Plik | Opis |

|------|------|

| [`SchemaGen_MVP.cs`](SchemaGen_MVP.cs) | Orchestrator + parser XML (`SchemaGenConfig` w tym samym pliku) |

| `dist/SchemaGen.EplAddIn..dll` | Skompilowany add-in (nie w gicie — buduj lokalnie) |



Folder docelowy EPLAN: `C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\`



Uruchomienie: EPLAN → Narzędzia → Skrypty → `SchemaGen_MVP.cs`



## Add-in



Skrypty `.cs` nie mają dostępu do `DataModel` / `HEServices` — strony i makra wymagają DLL.



**Mapa plików add-in:** [`addin/README.md`](addin/README.md)



| Plik | Opis |

|------|------|

| [`build_addin.ps1`](build_addin.ps1) | Kompilacja + auto-kopia DLL do EPLAN |

| [`watch_addin.ps1`](watch_addin.ps1) | File watcher — rebuild przy edycji add-inu |

| [`addin/`](addin/) | Źródła DLL (moduł, helpers, actions) |



```powershell

.\scripts\build_addin.ps1

# debug add-inu:

.\scripts\watch_addin.ps1

```



## Narzędzia bazy wiedzy EPLAN API



| Skrypt | Opis |

|--------|------|

| `extract_eplan_docs.py` | Ekstrakcja 104 plików HTML → `docs/eplan-kb/raw-extract.json` |

| `build_eplan_kb.py` | Budowa `docs/eplan-kb/topics/*.md`, INDEX, actions-index |



Źródło HTML: `C:\Users\Filip\Desktop\startUp\AutoGen\EPLAN API docs`


