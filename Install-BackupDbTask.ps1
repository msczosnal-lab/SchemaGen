<#
  Install-BackupDbTask.ps1 - codzienny backup data/schemagen.db (ostatnie ~14 kopii).

  Uruchom RAZ na PC Filip (PowerShell):
    .\Install-BackupDbTask.ps1 -RepoPath "C:\Users\Filip\Desktop\Cursor\SchemaGen"

  Usuniecie:
    Unregister-ScheduledTask -TaskName "SchemaGen DbBackup" -Confirm:$false
#>

param(
    [string]$RepoPath = "C:\Users\Filip\Desktop\Cursor\SchemaGen",
    [string]$TaskName = "SchemaGen DbBackup",
    [string]$RunAt    = "03:00"
)

$script = Join-Path $RepoPath "scripts\Backup-Db.ps1"
if (-not (Test-Path $script)) { throw "Nie znaleziono $script" }

$arg = "-NoProfile -ExecutionPolicy Bypass -File `"$script`" -RepoPath `"$RepoPath`""
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg
$trigger = New-ScheduledTaskTrigger -Daily -At $RunAt
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Host "Zarejestrowano zadanie '$TaskName' (codziennie o $RunAt)."
Write-Host "Test: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Kopie: $RepoPath\data\backups\schemagen-YYYYMMDD.db"
