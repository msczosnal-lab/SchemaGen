# SchemaGen MCP — schemagen-eplan

Lokalny serwer MCP łączący Cursor / Claude Cowork z EPLAN P8 2025.

## Narzędzia

| Tool | Opis |
|------|------|
| `eplan_build_addin` | `scripts/build_addin.ps1` → DLL w Skrypty\Schemagen |
| `eplan_run_script` | Headless `ExecuteScript` → `SchemaGen_MVP.cs` |
| `eplan_get_layout` | `SchemaGenAuditLayout` → `output/layout-audit.json` |
| `eplan_export_connections` | CSV połączeń → `output/connections.csv` |
| `eplan_validate_and_report` | CSV + `scripts/validation/validate_connections.py` |
| `eplan_closed_loop` | Pełna pętla: build → run → layout → walidacja |

## Cursor

Konfiguracja: [`.cursor/mcp.json`](../.cursor/mcp.json)

## Claude Cowork

Skopiuj fragment z [`config/claude_desktop_config.example.json`](../config/claude_desktop_config.example.json) do:

`%APPDATA%\Claude\claude_desktop_config.json`

Uruchom ponownie Claude Desktop. Cowork mostkuje lokalne serwery stdio przez Desktop SDK.

## Wymagania

- Python 3.10+
- EPLAN Electric P8 2025 (ścieżka domyślna lub zmienna `EPLAN_EXE`)
- Skrypt MVP w `C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\SchemaGen_MVP.cs`

## Wyjścia

`C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\output\`

- `layout-audit.json` — bbox vs ramka
- `remap-tags.json` — wynik sesji 1.6
- `connections.csv` — lista połączeń
- `validation-report.json` — reguły Fazy 2
