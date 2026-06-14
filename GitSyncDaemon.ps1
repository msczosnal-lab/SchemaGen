<#
  GitSyncDaemon.ps1 - ciagla, dwukierunkowa synchronizacja repo SchemaGen.
  Uruchamiany natywnie na Windows (NIE w sandboxie Cowork) na obu komputerach.

  Cykl co -IntervalSec:
    1. fetch origin
    2. jesli jestesmy behind -> rebase na origin/<branch>
    3. jesli sa niezacommitowane zmiany -> add + commit (sync/commit-message.txt lub auto[<TAG>])
    4. push (jesli ahead)
    5. heartbeat w konsoli + wykrycie commitu drugiego komputera
    6. zapis statusu do sync/.status-<TAG>.json

  Tagi maszyn: Cursor (PC Filip), Claude (PC ZW)

  Przyklad:
    .\GitSyncDaemon.ps1 -MachineTag Claude -IntervalSec 10
    .\GitSyncDaemon.ps1 -MachineTag Cursor -IntervalSec 10 -RepoPath "C:\Users\Filip\Desktop\Cursor\SchemaGen"
#>

param(
    [string]$RepoPath   = "C:\Users\ZW\Desktop\prywatne\automatyzacja\KodKlon\SchemaGen",
    [string]$Branch     = "main",
    [int]   $IntervalSec = 10,
    [Parameter(Mandatory=$true)][string]$MachineTag,
    [switch]$Toast,
    [switch]$Once
)

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptDir "GitSyncCommit.ps1")

$logFile = Join-Path $RepoPath "sync\.daemon-$MachineTag.log"

function Log([string]$msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    $color = "Gray"
    if     ($msg -like "*KONFLIKT*" -or $msg -like "*BLAD*") { $color = "Red" }
    elseif ($msg -like "*NOWE*")   { $color = "Cyan" }
    elseif ($msg -like "*PUSH*")   { $color = "Green" }
    elseif ($msg -like "*COMMIT*") { $color = "Green" }
    elseif ($msg -like "*PULL*")   { $color = "Cyan" }
    Write-Host $line -ForegroundColor $color
    try { Add-Content -Path $logFile -Value $line -Encoding UTF8 } catch {}
}

function Show-Toast([string]$title, [string]$text) {
    if (-not $Toast) { return }
    try {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $ni = New-Object System.Windows.Forms.NotifyIcon
        $ni.Icon = [System.Drawing.SystemIcons]::Information
        $ni.Visible = $true
        $ni.ShowBalloonTip(4000, $title, $text, [System.Windows.Forms.ToolTipIcon]::Info)
        Start-Sleep -Milliseconds 200
        $ni.Dispose()
    } catch {}
}

function script:Show-ToastIfAvailable {
    param([string]$Title, [string]$Text)
    Show-Toast -title $Title -text $Text
}

if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
    Write-Host "[BLAD] $RepoPath nie jest repozytorium git. Stop." -ForegroundColor Red
    exit 1
}
New-Item -ItemType Directory -Force -Path (Join-Path $RepoPath "sync") | Out-Null

Log "Start daemona [$MachineTag], branch=$Branch, interval=${IntervalSec}s"
Log "Repo: $RepoPath"

$lastRemote = ""

do {
    try {
        Get-ChildItem -Path (Join-Path $RepoPath ".git") -Recurse -Filter "*.lock" -ErrorAction SilentlyContinue | ForEach-Object {
            Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
        }

        & git -C $RepoPath fetch origin --quiet 2>&1 | Out-Null

        $local  = (& git -C $RepoPath rev-parse $Branch 2>$null)
        $remote = (& git -C $RepoPath rev-parse "origin/$Branch" 2>$null)
        if ($local)  { $local  = $local.Trim() }
        if ($remote) { $remote = $remote.Trim() }

        if ($remote -and $remote -ne $lastRemote -and $remote -ne $local) {
            $msg = (& git -C $RepoPath log -1 --pretty=format:"%h %an: %s" "origin/$Branch" 2>$null)
            Log "[NOWE] commit od drugiego komputera: $msg"
            Show-Toast "SchemaGen: nowe zmiany" "$msg"
        }
        $lastRemote = $remote

        $ahead  = [int](& git -C $RepoPath rev-list --count "origin/$Branch..$Branch" 2>$null)
        $behind = [int](& git -C $RepoPath rev-list --count "$Branch..origin/$Branch" 2>$null)

        if ($behind -gt 0) {
            & git -C $RepoPath rebase "origin/$Branch" 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                & git -C $RepoPath rebase --abort 2>&1 | Out-Null
                Log "[KONFLIKT] rebase przerwany - wymagane reczne scalenie. Push wstrzymany, praca lokalna zachowana."
                Show-Toast "SchemaGen: KONFLIKT" "Rozbiezne zmiany na tym samym pliku - scal recznie."
                if ($Once) { break } else { Start-Sleep -Seconds $IntervalSec; continue }
            }
            Log "[PULL] zintegrowano $behind commit(ow) z origin."
        }

        $dirty = (& git -C $RepoPath status --porcelain 2>$null)
        if ($dirty) {
            $result = Invoke-GitSyncCommit -RepoPath $RepoPath -MachineTag $MachineTag
            if ($result.Ok) {
                Log "[COMMIT] $($result.Message)"
            }
        }

        $ahead = [int](& git -C $RepoPath rev-list --count "origin/$Branch..$Branch" 2>$null)
        if ($ahead -gt 0) {
            & git -C $RepoPath push origin $Branch 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Log "[PUSH] wyslano $ahead commit(ow) do origin."
            } else {
                Log "[INFO] push odrzucony (wyscig) - nastepny cykl scali."
            }
        }

        $lh = (& git -C $RepoPath rev-parse --short $Branch 2>$null)
        $rh = (& git -C $RepoPath rev-parse --short "origin/$Branch" 2>$null)
        if ($lh) { $lh = $lh.Trim() }
        if ($rh) { $rh = $rh.Trim() }
        $ahead  = [int](& git -C $RepoPath rev-list --count "origin/$Branch..$Branch" 2>$null)
        $behind = [int](& git -C $RepoPath rev-list --count "$Branch..origin/$Branch" 2>$null)
        $hb = "{0}  czuwam [{1}]  local={2} remote={3} ahead={4} behind={5}" -f (Get-Date -Format "HH:mm:ss"), $MachineTag, $lh, $rh, $ahead, $behind
        if ($lh -eq $rh) {
            Write-Host $hb -ForegroundColor DarkGray
        } else {
            Write-Host $hb -ForegroundColor Yellow
        }

        $status = [ordered]@{
            machine    = $MachineTag
            time       = (Get-Date -Format "o")
            localHead  = $lh
            remoteHead = $rh
            ahead      = $ahead
            behind     = $behind
        }
        $status | ConvertTo-Json -Compress | Set-Content -Path (Join-Path $RepoPath "sync\.status-$MachineTag.json") -Encoding UTF8
    }
    catch {
        Log ("[BLAD] " + $_.Exception.Message)
    }

    if (-not $Once) { Start-Sleep -Seconds $IntervalSec }
} while (-not $Once)
