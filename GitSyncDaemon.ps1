<#
  GitSyncDaemon.ps1 - ciagla, dwukierunkowa synchronizacja repo SchemaGen.
  Uruchamiany natywnie na Windows (NIE w sandboxie Cowork) na obu komputerach.

  Cykl co -IntervalSec:
    1. fetch origin
    2. jesli jestesmy behind -> rebase --autostash na origin/<branch>
    3. jesli sa niezacommitowane zmiany -> commit TYLKO przy nazwanym sync/commit-message.txt
    4. push (jesli ahead i byl nazwany commit)
    5. log TYLKO przy zdarzeniach (NOWE/PULL/COMMIT/PUSH/KONFLIKT/BLAD)
    6. zapis statusu do sync/.status-<TAG>.json (cicho)

  Tryb -PushOnNamedOnly (domyslny na obu maszynach):
    Cyklicznie tylko POBIERA (fetch + rebase --autostash) i trzyma repo w zgodzie
    z origin, ale NIE commituje ani nie pushuje automatycznych zmian WIP.
    Commit + push nastepuje WYLACZNIE gdy w sync/commit-message.txt jest nazwany
    commit ([Claude] ... / [Cursor] ...).

  Tagi maszyn: Cursor (PC Filip), Claude (PC ZW)

  Przyklad:
    .\GitSyncDaemon.ps1 -MachineTag Claude -IntervalSec 10
    .\GitSyncDaemon.ps1 -MachineTag Cursor -IntervalSec 10 -RepoPath "C:\Users\Filip\Desktop\Cursor\SchemaGen"
#>

param(
    [string]$RepoPath   = "C:\Users\ZW\Desktop\prywatne\automatyzacja\KodKlon\SchemaGen",
    [string]$Branch     = "main",
    [int]   $IntervalSec = 5,
    [Parameter(Mandatory=$true)][string]$MachineTag,
    [switch]$Toast,
    [switch]$Once,
    [switch]$AllowAutoCommit
)

# Domyslnie: commit+push tylko przy nazwanym sync/commit-message.txt.
# Przekaz -AllowAutoCommit aby przywrocic auto-commity (niezalecane).
$PushOnNamedOnly = -not $AllowAutoCommit

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptDir "GitSyncCommit.ps1")

$logFile = Join-Path $RepoPath "sync\.daemon-$MachineTag.log"
$mutexFile = Join-Path $RepoPath "sync\.gitsync-mutex"

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

function Test-ActiveGitInRepo {
    param([string]$RepoPath)
    try {
        $procs = Get-CimInstance Win32_Process -Filter "Name='git.exe'" -ErrorAction SilentlyContinue
        foreach ($p in $procs) {
            if ($p.CommandLine -and $p.CommandLine -like "*$RepoPath*") { return $true }
        }
    } catch {}
    return $false
}

function Remove-StaleGitLocks {
    param([string]$RepoPath)
    if (Test-ActiveGitInRepo -RepoPath $RepoPath) { return }
    $lockCutoff = (Get-Date).AddSeconds(-60)
    Get-ChildItem -Path (Join-Path $RepoPath ".git") -Recurse -Filter "*.lock" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $lockCutoff } | ForEach-Object {
            Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
        }
}

# Mutex zapisuje PID + czas startu procesu. Windows RECYKLINGUJE PID-y: sam PID
# zmarlego daemona moze trafic do obcego procesu -> mutex zajety na zawsze, cicho.
# Para (PID, StartTime) jest unikalna, wiec taki deadlock nie moze wystapic.
function Get-MutexToken {
    param([int]$ProcId = $PID)
    $p = Get-Process -Id $ProcId -ErrorAction SilentlyContinue
    if (-not $p) { return $null }
    return "{0}|{1}" -f $ProcId, $p.StartTime.Ticks
}

function Enter-GitSyncMutex {
    param([string]$MutexPath)
    if (Test-Path $MutexPath) {
        try {
            $raw = (Get-Content $MutexPath -Raw).Trim()
            $parts = $raw -split '\|'
            $ownerPid = [int]$parts[0]
            if ($ownerPid -gt 0) {
                $live = Get-MutexToken -ProcId $ownerPid
                # zajety tylko gdy proces zyje I to ten sam proces (zgodny StartTime)
                if ($live -and ($parts.Count -lt 2 -or $live -eq $raw)) { return $false }
            }
        } catch {}
        Remove-Item $MutexPath -Force -ErrorAction SilentlyContinue
    }
    try {
        Set-Content -Path $MutexPath -Value (Get-MutexToken) -NoNewline -Encoding ASCII
        return $true
    } catch {
        return $false
    }
}

function Exit-GitSyncMutex {
    param([string]$MutexPath)
    if (-not (Test-Path $MutexPath)) { return }
    try {
        $raw = (Get-Content $MutexPath -Raw).Trim()
        if ($raw -eq (Get-MutexToken)) {
            Remove-Item $MutexPath -Force -ErrorAction SilentlyContinue
        }
    } catch {}
}

if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
    Write-Host "[BLAD] $RepoPath nie jest repozytorium git. Stop." -ForegroundColor Red
    exit 1
}
New-Item -ItemType Directory -Force -Path (Join-Path $RepoPath "sync") | Out-Null

Log "Start daemona [$MachineTag], branch=$Branch, interval=${IntervalSec}s, namedOnly=$PushOnNamedOnly"
Log "Repo: $RepoPath"

$lastRemote = ""
$pullOnlyNoted = $false
$blockedSince = $null

do {
    if (-not (Enter-GitSyncMutex -MutexPath $mutexFile)) {
        # NIE milcz. Zablokowany mutex = daemon nie synchronizuje, choc okno stoi otwarte.
        if (-not $blockedSince) { $blockedSince = Get-Date }
        $blockedFor = [int]((Get-Date) - $blockedSince).TotalSeconds
        if ($blockedFor -ge 60) {
            $owner = try { (Get-Content $mutexFile -Raw).Trim() } catch { "?" }
            Log "[BLAD] mutex zajety od ${blockedFor}s (PID $owner) - SYNC NIE DZIALA. Jesli ten PID to nie daemon: usun sync\.gitsync-mutex"
            Show-Toast "SchemaGen: SYNC STOI" "Mutex zablokowany od ${blockedFor}s"
            $blockedSince = Get-Date   # kolejny alert za 60 s, nie co cykl
        }
        if (-not $Once) { Start-Sleep -Seconds $IntervalSec }
        continue
    }
    $blockedSince = $null
    try {
        Remove-StaleGitLocks -RepoPath $RepoPath

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
            & git -C $RepoPath rebase --autostash "origin/$Branch" 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                & git -C $RepoPath rebase --abort 2>&1 | Out-Null
                Log "[KONFLIKT] rebase przerwany - wymagane reczne scalenie. Push wstrzymany, praca lokalna zachowana."
                Show-Toast "SchemaGen: KONFLIKT" "Rozbiezne zmiany na tym samym pliku - scal recznie."
                if ($Once) { break } else { continue }
            }
            Log "[PULL] zintegrowano $behind commit(ow) z origin."
        }

        $dirty = (& git -C $RepoPath status --porcelain 2>$null)
        $pending = Get-PendingCommitMessage -RepoPath $RepoPath
        $committedThisCycle = $false
        if ($dirty) {
            if ($PushOnNamedOnly -and -not $pending) {
                if (-not $pullOnlyNoted) {
                    Log "[PULL-ONLY] zmiany lokalne - czekam na nazwany commit (sync/commit-message.txt: [Cursor]/[Claude] opis)."
                    $pullOnlyNoted = $true
                }
            } else {
                $result = Invoke-GitSyncCommit -RepoPath $RepoPath -MachineTag $MachineTag
                if ($result.Ok) {
                    Log "[COMMIT] $($result.Message)"
                    $pullOnlyNoted = $false
                    $committedThisCycle = $result.Named
                }
            }
        } else {
            $pullOnlyNoted = $false
        }

        # Push przy KAZDYM ahead>0, nie tylko po wlasnym commicie tego cyklu.
        # Wczesniej: commit zrobiony recznie albo przez innego agenta zostawal
        # lokalnie na zawsze — daemon widzial rozbieznosc i swiadomie jej nie ruszal,
        # a drugi komputer nie dostawal nic. Bramka "tylko nazwane commity" i tak
        # dziala na etapie commitowania, wiec tu jest zbedna.
        $ahead = [int](& git -C $RepoPath rev-list --count "origin/$Branch..$Branch" 2>$null)
        if ($ahead -gt 0) {
            & git -C $RepoPath fetch origin --quiet 2>&1 | Out-Null
            $behindNow = [int](& git -C $RepoPath rev-list --count "$Branch..origin/$Branch" 2>$null)
            if ($behindNow -gt 0) {
                & git -C $RepoPath rebase --autostash "origin/$Branch" 2>&1 | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    & git -C $RepoPath rebase --abort 2>&1 | Out-Null
                    Log "[KONFLIKT] rebase przed push przerwany - scal recznie."
                    if ($Once) { break } else { continue }
                }
                Log "[PULL] zintegrowano $behindNow commit(ow) przed push."
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
        }

        $lh = (& git -C $RepoPath rev-parse --short $Branch 2>$null)
        $rh = (& git -C $RepoPath rev-parse --short "origin/$Branch" 2>$null)
        if ($lh) { $lh = $lh.Trim() }
        if ($rh) { $rh = $rh.Trim() }
        $ahead  = [int](& git -C $RepoPath rev-list --count "origin/$Branch..$Branch" 2>$null)
        $behind = [int](& git -C $RepoPath rev-list --count "$Branch..origin/$Branch" 2>$null)
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
    finally {
        Exit-GitSyncMutex -MutexPath $mutexFile
    }

    if (-not $Once) { Start-Sleep -Seconds $IntervalSec }
} while (-not $Once)
