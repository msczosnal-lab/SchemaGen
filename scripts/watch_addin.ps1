# Obserwuje scripts/addin/**/*.cs i odpala build_addin.ps1 przy kazdej zmianie
param(
    [string]$EplanBin = ""
)

$addinDir = Join-Path $PSScriptRoot "addin"
$buildScript = Join-Path $PSScriptRoot "build_addin.ps1"

Write-Host "Watcher uruchomiony. Obserwuje: $addinDir"
Write-Host "Ctrl+C aby zatrzymac."
Write-Host ""

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $addinDir
$watcher.Filter = "*.cs"
$watcher.IncludeSubdirectories = $true
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite
$watcher.EnableRaisingEvents = $true

$lastBuild = [datetime]::MinValue

try {
    while ($true) {
        $result = $watcher.WaitForChanged([System.IO.WatcherChangeTypes]::Changed -bor [System.IO.WatcherChangeTypes]::Created, 1000)
        if ($result.TimedOut) { continue }

        # Debounce - ignoruj zdarzenia blizej niz 2 sekundy od ostatniego buildu
        if (([datetime]::Now - $lastBuild).TotalSeconds -lt 2) { continue }
        $lastBuild = [datetime]::Now

        Write-Host ""
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Zmiana: $($result.Name)"
        Write-Host "--- BUILD START ---"

        $buildArgs = @()
        if ($EplanBin) { $buildArgs = @("-EplanBin", $EplanBin) }

        & $buildScript @buildArgs 2>&1 | ForEach-Object { Write-Host $_ }

        Write-Host "--- BUILD END ---"
        Write-Host ""
    }
} finally {
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Write-Host "Watcher zatrzymany."
}
