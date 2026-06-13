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

function Write-Step([string]$msg, [string]$color = "White") {
    Write-Host $msg -ForegroundColor $color
}

if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
    Write-Step "[BLAD] $RepoPath nie jest repozytorium git." "Red"
    exit 1
}

Write-Step ""
Write-Step "=== SchemaGen — start sesji Claude [$MachineTag] ===" "Cyan"
Write-Step "Repo: $RepoPath"
Write-Step ""

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
            Write-Step "[OK] GitSync daemon aktywny (ostatni heartbeat ${ageSec:N0}s temu)." "Green"
        }
    } catch {}
}

if (-not $daemonRunning) {
    Write-Step "[INFO] GitSync nie wykryty — uruchamiam daemon w osobnym oknie..." "Yellow"
    $daemonScript = Join-Path $RepoPath "GitSyncDaemon.ps1"
    if (Test-Path $daemonScript) {
        Start-Process powershell -ArgumentList @(
            "-NoProfile", "-ExecutionPolicy", "Bypass", "-NoExit",
            "-File", "`"$daemonScript`"", "-MachineTag", $MachineTag,
            "-RepoPath", "`"$RepoPath`"", "-Toast"
        )
        Start-Sleep -Seconds 3
    } else {
        Write-Step "[UWAGA] Brak GitSyncDaemon.ps1 — sync reczny." "Yellow"
    }
}

# --- pull ---
Write-Step ""
Write-Step "--- Synchronizacja git ---" "Cyan"
& git -C $RepoPath fetch origin 2>&1 | Out-Null
$pullOut = & git -C $RepoPath pull --rebase origin main 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Step "[OK] pull --rebase" "Green"
    if ($pullOut) { Write-Step $pullOut "Gray" }
} else {
    Write-Step "[BLAD] pull --rebase nie powiodl sie:" "Red"
    Write-Step $pullOut "Red"
    Write-Step "Rozwiaz konflikt recznie przed sesja Claude." "Red"
}

# --- skrzynka Filip ---
Write-Step ""
Write-Step "--- Skrzynka od Filipa (filip-to-zw.md) ---" "Cyan"
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
            Write-Step $line "Gray"
            $shown++
        }
    }
} else {
    Write-Step "(brak pliku)" "Yellow"
}

# --- TASKS OPEN ---
Write-Step ""
Write-Step "--- TASKS.md (OPEN) ---" "Cyan"
$tasks = Join-Path $RepoPath "sync\TASKS.md"
if (Test-Path $tasks) {
    Get-Content $tasks -Encoding UTF8 | Where-Object { $_ -match '\| OPEN \|' } | ForEach-Object {
        Write-Step $_ "Gray"
    }
}

# --- prompt sesji ---
Write-Step ""
Write-Step "--- Prompt sesji ---" "Cyan"
$promptPath = Join-Path $RepoPath ($PromptFile -replace '/', '\')
if (-not (Test-Path $promptPath)) {
    Write-Step "[BLAD] Brak pliku promptu: $promptPath" "Red"
    exit 1
}

$promptText = Get-Content $promptPath -Raw -Encoding UTF8
try {
    Set-Clipboard -Value $promptText
    Write-Step "[OK] Prompt skopiowany do schowka." "Green"
} catch {
    Write-Step "[UWAGA] Nie udalo sie skopiowac do schowka: $_" "Yellow"
}

Write-Step ""
Write-Step "Plik promptu (pelna sciezka):" "White"
Write-Step $promptPath "Cyan"
Write-Step ""
Write-Step "W Claude Cowork:" "White"
Write-Step "  1. Wklej prompt ze schowka LUB dolacz pliki:" "White"
Write-Step "     @$PromptFile" "Yellow"
Write-Step "     @docs/claude-opus-instructions.md" "Yellow"
Write-Step "     @sync/filip-to-zw.md" "Yellow"
Write-Step "  2. Po pracy: wpis tylko w sync/zw-to-filip.md + TASKS.md" "White"
Write-Step "  3. GitSync wypchnie commit automatycznie (~10 s)" "White"
Write-Step ""
