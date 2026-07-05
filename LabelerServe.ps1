<#
  LabelerServe.ps1 - serwer labelera SchemaGen (FastAPI, localhost:8765).

  Uruchamiany przez Start-Labeler.cmd (podwojne klikniecie).
  Repo = folder z tym skryptem (dziala na ZW i Filip).

  Przyklad:
    .\LabelerServe.ps1
    .\LabelerServe.ps1 -RepoPath "C:\Users\Filip\Desktop\Cursor\SchemaGen" -Port 8765
#>

param(
    [string]$RepoPath = (Split-Path -Parent $MyInvocation.MyCommand.Path),
    [int]   $Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$logFile = Join-Path $RepoPath "sync\.labeler.log"

function Log([string]$msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Write-Host $line -ForegroundColor Gray
    try {
        New-Item -ItemType Directory -Force -Path (Join-Path $RepoPath "sync") | Out-Null
        Add-Content -Path $logFile -Value $line -Encoding UTF8
    } catch {}
}

function Resolve-Python([string]$root) {
    foreach ($name in @(".venv311", ".venv")) {
        $py = Join-Path $root "$name\Scripts\python.exe"
        if (Test-Path $py) { return $py }
    }
    return "python"
}

if (-not (Test-Path (Join-Path $RepoPath "labeler\app.py"))) {
    Write-Host "[BLAD] $RepoPath nie wyglada na repo SchemaGen (brak labeler\app.py)." -ForegroundColor Red
    exit 1
}

Set-Location $RepoPath
$python = Resolve-Python $RepoPath
$url = "http://127.0.0.1:$Port/"

Log "Start labelera, python=$python, url=$url"
Log "Stop = zamknij okno lub Ctrl+C"

& $python -m backend.cli init-db 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
    Log "init-db zwrocilo kod $LASTEXITCODE (kontynuuje)"
}

if (-not $NoBrowser) {
    Start-Job -ScriptBlock {
        param($u)
        Start-Sleep -Seconds 2
        Start-Process $u
    } -ArgumentList $url | Out-Null
    Log "Przegladarka otworzy sie za ~2 s: $url"
}

Write-Host ""
Write-Host "  Labeler:  $url" -ForegroundColor Green
Write-Host "  Log:      $logFile" -ForegroundColor DarkGray
Write-Host ""

& $python -c "from labeler.app import run; run(port=$Port)"
