# SchemaGen dev — venv, deps, labeler + API
param(
    [switch]$Gpu,
    [switch]$NoServe
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install -q -r requirements.txt
if ($Gpu) {
    pip install -q -r requirements-gpu.txt
}
python -m backend.cli init-db

Write-Host ""
Write-Host "SchemaGen dev ready."
Write-Host "  Labeler:  python -m labeler.app     -> http://localhost:8765"
Write-Host "  API:      python -m backend.cli serve -> http://localhost:8780"
Write-Host "  Testy:    pytest backend/tests labeler/tests"
Write-Host ""

if (-not $NoServe) {
    Start-Process python -ArgumentList "-m", "labeler.app" -WorkingDirectory (Get-Location)
    Start-Process python -ArgumentList "-m", "backend.cli", "serve" -WorkingDirectory (Get-Location)
    Write-Host "Uruchomiono labeler (8765) i API (8780) w osobnych oknach."
}
