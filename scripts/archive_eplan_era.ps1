# Jednorazowe archiwum ery EPLAN — pivot offline
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$staging = Join-Path "archive" "_staging"
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
New-Item -ItemType Directory -Force -Path $staging | Out-Null

$dirCopies = @(
    "scripts\addin",
    "scripts\validation",
    "mcp\schemagen_eplan",
    "docs\eplan-kb",
    "eplan_output"
)
foreach ($p in $dirCopies) {
    if (Test-Path $p) {
        $dest = Join-Path $staging (Split-Path $p -Leaf)
        Copy-Item $p -Destination $dest -Recurse -Force
    }
}

$csDest = Join-Path $staging "scripts_cs"
New-Item -ItemType Directory -Force -Path $csDest | Out-Null
Get-ChildItem "scripts\*.cs" -ErrorAction SilentlyContinue | Copy-Item -Destination $csDest -Force

$fileCopies = @(
    "scripts\build_addin.ps1",
    "scripts\watch_addin.ps1",
    "scripts\README.md",
    "scripts\extract_eplan_docs.py",
    "scripts\build_eplan_kb.py",
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
    "Start-ClaudeSession.ps1"
)
foreach ($f in $fileCopies) {
    if (Test-Path $f) {
        $destPath = Join-Path $staging $f
        $destDir = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        }
        Copy-Item $f -Destination $destPath -Force
    }
}

$zipPath = "archive\eplan-era-2026-06.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $zipPath -Force
Remove-Item $staging -Recurse -Force
Write-Host "Utworzono: $zipPath ($((Get-Item $zipPath).Length) bajtów)"
