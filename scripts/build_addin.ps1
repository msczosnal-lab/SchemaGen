# Kompiluje SchemaGen.EplAddin.dll (wymaga EPLAN Platform + .NET Framework csc)
param(
    [string]$EplanBin = "",
    [string]$OutDir = "$PSScriptRoot\..\dist"
)

$dllName = "SchemaGen.EplAddIn..dll"
$addinDir = Join-Path $PSScriptRoot "addin"
$sources = Get-ChildItem -Path $addinDir -Filter "*.cs" -Recurse | ForEach-Object { $_.FullName }
if ($sources.Count -eq 0) {
    Write-Error "Brak plikow .cs w $addinDir"
    exit 1
}

if (-not $EplanBin) {
    $candidates = @(
        "C:\Program Files\EPLAN\Platform\2025.0.3\Bin",
        "C:\Program Files\EPLAN\Platform\2024.0.3\Bin",
        "C:\Program Files (x86)\EPLAN\Platform\2025.0.3\Bin"
    )
    foreach ($c in $candidates) {
        if (Test-Path (Join-Path $c "Eplan.EplApi.AFu.dll")) {
            $EplanBin = $c
            break
        }
    }
}

if (-not $EplanBin -or -not (Test-Path $EplanBin)) {
    Write-Error "Nie znaleziono folderu Bin EPLAN. Uruchom z parametrem -EplanBin 'C:\Program Files\EPLAN\Platform\2025.0.3\Bin'"
    exit 1
}

$csc = "${env:WINDIR}\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path $csc)) {
    $csc = "${env:WINDIR}\Microsoft.NET\Framework\v4.0.30319\csc.exe"
}

$refs = @(
    "Eplan.EplApi.AFu.dll",
    "Eplan.EplApi.Baseu.dll",
    "Eplan.EplApi.DataModelu.dll",
    "Eplan.EplApi.HEServicesu.dll"
) | ForEach-Object { "/reference:`"$EplanBin\$_`"" }

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$outPath = Join-Path $OutDir $dllName

& $csc /nologo /target:library /out:$outPath @refs @sources
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "OK: $outPath"

# --- Auto-copy do folderu EPLAN ---
$deployDir = "C:\Users\Public\EPLAN\Data\Skrypty\Schemagen"
if (Test-Path $deployDir) {
    Copy-Item -Path $outPath -Destination (Join-Path $deployDir $dllName) -Force
    Write-Host "Skopiowano -> $deployDir\$dllName"
} else {
    Write-Warning "Folder EPLAN nie istnieje: $deployDir — pominam kopię."
}

# --- Hot-reload add-in w EPLAN (jeśli EPLAN jest otwarty) ---
$eplanExe = Get-Process -Name "EPLAN" -ErrorAction SilentlyContinue
if ($eplanExe) {
    $dllDest = Join-Path $deployDir $dllName
    Write-Host "EPLAN jest otwarty — próba hot-reload add-in..."
    # Użyj skryptu orkiestrującego SchemaGen_MVP.cs który sam wywołuje EplApiModuleAction,
    # albo wpisz w EPLAN: Narzędzia -> Skrypty -> SchemaGen_MVP.cs
    Write-Host "Aby przeładować: w EPLAN uruchom SchemaGen_MVP.cs (wczyta DLL przez EplApiModuleAction)"
} else {
    Write-Host "EPLAN nie jest uruchomiony — DLL gotowa do załadowania przy starcie."
}

Write-Host "Rejestracja (pierwsze uruchomienie): EPLAN -> Plik -> Dodatki -> Interfejsy -> API -> Zarządzaj -> Wczytaj"
