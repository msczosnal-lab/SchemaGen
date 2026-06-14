# Obserwuje scripts/addin/**/*.cs i odpala build_addin.ps1 przy kazdej zmianie (z debounce).
param(
    [string]$EplanBin = "",
    [int]$DebounceSeconds = 2
)

$ErrorActionPreference = "Stop"

$addinDir = Join-Path $PSScriptRoot "addin"
$buildScript = Join-Path $PSScriptRoot "build_addin.ps1"

if (-not (Test-Path $addinDir)) {
    Write-Error "Brak folderu: $addinDir"
    exit 1
}

$addinDir = (Resolve-Path -LiteralPath $addinDir).Path

$changeTypes = [System.IO.WatcherChangeTypes]::Changed -bor `
    [System.IO.WatcherChangeTypes]::Created -bor `
    [System.IO.WatcherChangeTypes]::Renamed

function Invoke-AddinBuild {
    param([string]$Reason)

    Write-Host ""
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Build: $Reason"
    Write-Host "--- BUILD START ---"

    $buildParams = @{}
    if ($EplanBin) { $buildParams["EplanBin"] = $EplanBin }

    & $buildScript @buildParams
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        Write-Host "--- BUILD FAILED (exit $exitCode) ---"
    } else {
        Write-Host "--- BUILD OK ---"
    }
    Write-Host ""

    return $exitCode
}

function Test-CsWatcherEvent {
    param($Result)
    return (-not $Result.TimedOut) -and $Result.Name -and ($Result.Name -match '\.cs$')
}

function Wait-AddinChanges {
    param(
        [System.IO.FileSystemWatcher]$Watcher,
        [int]$TimeoutMs
    )

    $collected = @{}
    $result = $Watcher.WaitForChanged($changeTypes, $TimeoutMs)
    if (-not (Test-CsWatcherEvent $result)) {
        return $collected
    }

    $collected[$result.Name] = $true

    # Edytor (Cursor/VS Code) zapisuje plik seria zdarzen — zbierz je w krotkim oknie.
    do {
        $more = $Watcher.WaitForChanged($changeTypes, 150)
        if (Test-CsWatcherEvent $more) {
            $collected[$more.Name] = $true
        }
    } while (-not $more.TimedOut)

    return $collected
}

Write-Host "Watcher uruchomiony."
Write-Host "Obserwuje (rekursywnie): $addinDir"
Write-Host "Debounce: ${DebounceSeconds}s | Ctrl+C aby zatrzymac."
Write-Host ""

Invoke-AddinBuild "start watchera" | Out-Null

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $addinDir
$watcher.Filter = "*.cs"
$watcher.IncludeSubdirectories = $true
$watcher.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor `
    [System.IO.NotifyFilters]::DirectoryName -bor `
    [System.IO.NotifyFilters]::LastWrite -bor `
    [System.IO.NotifyFilters]::CreationTime
$watcher.InternalBufferSize = 65536
$watcher.EnableRaisingEvents = $true

try {
    while ($true) {
        $pending = Wait-AddinChanges -Watcher $watcher -TimeoutMs 1000
        if ($pending.Count -eq 0) { continue }

        # Debounce: czekaj na koniec serii zapisow, potem zbierz ewentualne kolejne zdarzenia.
        $quietUntil = (Get-Date).AddSeconds($DebounceSeconds)
        while ((Get-Date) -lt $quietUntil) {
            $extra = Wait-AddinChanges -Watcher $watcher -TimeoutMs 200
            foreach ($name in $extra.Keys) {
                $pending[$name] = $true
                $quietUntil = (Get-Date).AddSeconds($DebounceSeconds)
            }
        }

        $fileList = ($pending.Keys | Sort-Object) -join ", "
        Invoke-AddinBuild "zmiana: $fileList" | Out-Null
    }
} finally {
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Write-Host "Watcher zatrzymany."
}
