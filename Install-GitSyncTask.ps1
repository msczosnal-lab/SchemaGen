<#
  Install-GitSyncTask.ps1 - rejestruje GitSyncDaemon.ps1 w Harmonogramie zadan Windows.
  Przy logowaniu OTWIERA WIDOCZNE OKNO konsoli z logiem na zywo (nie w tle).
  Alternatywa bez harmonogramu: podwojne klikniecie Start-GitSync.cmd.

  Uruchom RAZ na kazdym komputerze (PowerShell, ten sam uzytkownik co repo):
    .\Install-GitSyncTask.ps1 -MachineTag ZW
    .\Install-GitSyncTask.ps1 -MachineTag Filip -RepoPath "C:\Users\Filip\Desktop\Cursor\SchemaGen"

  Usuniecie zadania:
    Unregister-ScheduledTask -TaskName "SchemaGen GitSync" -Confirm:$false
#>

param(
    [Parameter(Mandatory=$true)][string]$MachineTag,
    [string]$RepoPath    = "C:\Users\ZW\Desktop\prywatne\automatyzacja\KodKlon\SchemaGen",
    [int]   $IntervalSec = 10,
    [string]$TaskName    = "SchemaGen GitSync"
)

$daemon = Join-Path $RepoPath "GitSyncDaemon.ps1"
if (-not (Test-Path $daemon)) { throw "Nie znaleziono $daemon" }

# cmd /c start ... -> nowe, WIDOCZNE okno konsoli przy logowaniu (nie ukryte)
$inner  = "powershell -NoProfile -ExecutionPolicy Bypass -NoExit -File `"$daemon`" -MachineTag $MachineTag -RepoPath `"$RepoPath`" -IntervalSec $IntervalSec -Toast"
$cmdArg = "/c start `"SchemaGen GitSync - $MachineTag`" $inner"

$action    = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $cmdArg
$trigger   = New-ScheduledTaskTrigger -AtLogOn
$settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Host "Zarejestrowano zadanie '$TaskName' (tag=$MachineTag, interval=${IntervalSec}s)."
Write-Host "Start teraz: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Logi:        $RepoPath\sync\.daemon-$MachineTag.log"
