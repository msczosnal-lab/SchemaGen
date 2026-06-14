# Usuwa pliki ery EPLAN po utworzeniu archive/eplan-era-2026-06.zip
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path "archive\eplan-era-2026-06.zip")) {
    throw "Brak archive\eplan-era-2026-06.zip — najpierw uruchom archive_eplan_era.ps1"
}

$removePaths = @(
    "scripts\addin",
    "scripts\validation",
    "mcp\schemagen_eplan",
    "docs\eplan-kb",
    "eplan_output",
    "scripts\build_addin.ps1",
    "scripts\watch_addin.ps1",
    "scripts\README.md",
    "scripts\extract_eplan_docs.py",
    "scripts\build_eplan_kb.py",
    "scripts\archive_eplan_era.ps1",
    "mcp\README.md",
    "docs\eplan-api-notes.md",
    "docs\eplan-data-paths.txt",
    "docs\eplan-initial-prompt.txt",
    "docs\eplan-first-conversation.txt",
    "docs\claude-opus-instructions.md",
    "docs\session-log.md",
    "sync\prompts\1.7g-ma-global-dt.md",
    ".cursor\mcp.json",
    "config\numbering-rules.xml",
    "config\claude_desktop_config.example.json",
    "Start-ClaudeSession.cmd",
    "Start-ClaudeSession.ps1",
    ".cursor\rules\eplan-schemagen.mdc"
)
Get-ChildItem "scripts\*.cs" -ErrorAction SilentlyContinue | Remove-Item -Force
foreach ($p in $removePaths) {
    if (Test-Path $p) { Remove-Item $p -Recurse -Force }
}
Write-Host "Usunięto pliki ery EPLAN z root repo."
