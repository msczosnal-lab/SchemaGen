<#
  Start-ClaudeSession.ps1 - przygotowanie sesji Claude Cowork (komputer ZW).
  1. Upewnia sie ze GitSync dziala (opcjonalnie uruchamia daemon)
  2. fetch + pull --rebase
  3. Podsumowuje skrzynke filip-to-zw.md i TASKS.md
  4. Wczytuje plik promptu sesji i kopiuje do schowka

  Przyklad:
    .\Start-ClaudeSession.ps1 -MachineTag ZW
    .\Start-ClaudeSession.ps1 -MachineTag ZW -PromptFile sync/prompts/1.7g-ma-global-dt.md
#>

param(
    [string]$RepoPath = $PSScriptRoot,
    [string]$MachineTag = "ZW",
    [string]$PromptFile = "sync/prompts/1.7g-ma-global-dt.md",
    [int]$DaemonMaxAgeSec = 30
)

$ErrorActionPreference = "Continue"

function Write-Step {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
    Write-Step -Message "[BLAD] $RepoPath nie jest repozytorium git." -Color Red
    exit 1
}

Write-Step -Message ""
Write-Step -Message "=== SchemaGen - start sesji Claude [$MachineTag] ===" -Color Cyan
Write-Step -Message "Repo: $RepoPath"
Write-Step -Message ""

# --- GitSync daemon ---
$statusFile = Join-Path $RepoPath "sync\.status-$MachineTag.json"
$daemonRunning = $false
if (Test-Path $statusFile) {
    try {
        $status = Get-Content $statusFile -Raw -Encoding UTF8 | ConvertFrom-Json
        $statusTime = [datetimeoffset]::Parse($status.time)
        $ageSec = ((Get-Date) - $statusTime.LocalDateTime).TotalSeconds
        if ($ageSec -lt $DaemonMaxAgeSec) {
            $daemonRunning = $true
            $hbMsg = "[OK] GitSync daemon aktywny (ostatni heartbeat {0:N0}s temu)." -f $ageSec
            Write-Step -Message $hbMsg -Color Green
        }
    } catch {}
}

if (-not $daemonRunning) {
    Write-Step -Message "[INFO] GitSync nie wykryty - uruchamiam daemon w osobnym oknie..." -Color Yellow
    $daemonScript = Join-Path $RepoPath "GitSyncDaemon.ps1"
    if (Test-Path $daemonScript) {
        Start-Process powershell -ArgumentList @(
            "-NoProfile", "-ExecutionPolicy", "Bypass", "-NoExit",
            "-File", $daemonScript, "-MachineTag", $MachineTag,
            "-RepoPath", $RepoPath, "-Toast"
        )
        Start-Sleep -Seconds 3
    } else {
        Write-Step -Message "[UWAGA] Brak GitSyncDaemon.ps1 - sync reczny." -Color Yellow
    }
}

# --- pull ---
Write-Step -Message ""
Write-Step -Message "--- Synchronizacja git ---" -Color Cyan
& git -C $RepoPath fetch origin 2>&1 | Out-Null
$pullOut = & git -C $RepoPath pull --rebase origin main 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Step -Message "[OK] pull --rebase" -Color Green
    if ($pullOut) { Write-Step -Message $pullOut -Color Gray }
} else {
    Write-Step -Message "[BLAD] pull --rebase nie powiodl sie:" -Color Red
    Write-Step -Message $pullOut -Color Red
    Write-Step -Message "Rozwiaz konflikt recznie przed sesja Claude." -Color Red
}

# --- skrzynka Filip ---
Write-Step -Message ""
Write-Step -Message "--- Skrzynka od Filipa (filip-to-zw.md) ---" -Color Cyan
$inbox = Join-Path $RepoPath "sync\filip-to-zw.md"
if (Test-Path $inbox) {
    $lines = Get-Content $inbox -Encoding UTF8
    $inSection = $false
    $shown = 0
    foreach ($line in $lines) {
        if ($line -match '^## \d{4}-\d{2}-\d{2}') {
            if ($inSection) { break }
            $inSection = $true
            $shown = 0
        }
        if ($inSection -and $shown -lt 12) {
            Write-Step -Message $line -Color Gray
            $shown++
        }
    }
} else {
    Write-Step -Message "(brak pliku)" -Color Yellow
}

# --- TASKS OPEN ---
Write-Step -Message ""
Write-Step -Message "--- TASKS.md (OPEN) ---" -Color Cyan
$tasks = Join-Path $RepoPath "sync\TASKS.md"
if (Test-Path $tasks) {
    Get-Content $tasks -Encoding UTF8 | Where-Object { $_ -match '\| OPEN \|' } | ForEach-Object {
        Write-Step -Message $_ -Color Gray
    }
}

# --- prompt sesji ---
Write-Step -Message ""
Write-Step -Message "--- Prompt sesji ---" -Color Cyan
$promptPath = Join-Path $RepoPath ($PromptFile -replace '/', '\')
if (-not (Test-Path $promptPath)) {
    Write-Step -Message "[BLAD] Brak pliku promptu: $promptPath" -Color Red
    exit 1
}

$promptText = Get-Content $promptPath -Raw -Encoding UTF8
try {
    Set-Clipboard -Value $promptText
    Write-Step -Message "[OK] Prompt skopiowany do schowka." -Color Green
} catch {
    Write-Step -Message "[UWAGA] Nie udalo sie skopiowac do schowka: $_" -Color Yellow
}

Write-Step -Message ""
Write-Step -Message "Plik promptu (pelna sciezka):" -Color White
Write-Step -Message $promptPath -Color Cyan
Write-Step -Message ""
Write-Step -Message "W Claude Cowork:" -Color White
Write-Step -Message "  1. Wklej prompt ze schowka LUB dolacz pliki:" -Color White
Write-Step -Message "     @$PromptFile" -Color Yellow
Write-Step -Message "     @docs/claude-opus-instructions.md" -Color Yellow
Write-Step -Message "     @sync/filip-to-zw.md" -Color Yellow
Write-Step -Message "  2. Po pracy: wpis tylko w sync/zw-to-filip.md + TASKS.md" -Color White
Write-Step -Message "  3. GitSync wypchnie commit automatycznie w ok. 10 s" -Color White
Write-Step -Message ""
