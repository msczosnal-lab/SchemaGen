# Obserwuje scripts/addin/**/*.cs i odpala build_addin.ps1 przy każdej zmianie
param(
    [string]$EplanBin = ""
)

$addinDir = Join-Path $PSScriptRoot "addin"
$buildScript = Join-Path $PSScriptRoot "build_addin.ps1"

Write-Host "Watcher uruchomiony. Obserwuję: $addinDir"
Write-Host "Ctrl+C aby zatrzymać."
Write-Host ""

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $addinDir
$watcher.Filter = "*.cs"
$watcher.IncludeSubdirectories = $true
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite

$action = {
    $path = $Event.SourceEventArgs.FullPath
    $changeType = $Event.SourceEventArgs.ChangeType
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $changeType : $path"
    Write-Host "Buduję..."

    $args = @()
    if ($Event.MessageData) { $args = @("-EplanBin", $Event.MessageData) }

    & $using:buildScript @args
    Write-Host ""
}

Register-ObjectEvent $watcher "Changed" -Action $action -MessageData $EplanBin | Out-Null
Register-ObjectEvent $watcher "Created" -Action $action -MessageData $EplanBin | Out-Null

$watcher.EnableRaisingEvents = $true

try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Write-Host "Watcher zatrzymany."
}
