# Jednorazowy setup venv OCR (CPU, paddle 2.6 + paddleocr 2.9 — bez torch).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root ".venv-ocr"
$Py = Join-Path $Venv "Scripts\python.exe"

if (-not (Test-Path $Py)) {
    py -3.11 -m venv $Venv
}
& (Join-Path $Venv "Scripts\pip.exe") install -r (Join-Path $Root "requirements-ocr.txt")
Write-Host "OK: $Py"
Write-Host "Smoke: $Py scripts\ocr_worker.py data\raw\22_A_153_PL_Adamed_AGV_SA2_20250706_p035.png --lang en --cpu"
