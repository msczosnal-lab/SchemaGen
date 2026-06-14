# Wspolna logika nazwanych commitow — GitSyncDaemon.ps1 + GitSync.ps1

function Get-CommitMessageFilePath {
    param([string]$RepoPath)
    Join-Path $RepoPath "sync\commit-message.txt"
}

function Get-CommitLogFilePath {
    param([string]$RepoPath)
    Join-Path $RepoPath "sync\commit-log.md"
}

function Get-PendingCommitMessage {
    param([string]$RepoPath)
    $path = Get-CommitMessageFilePath -RepoPath $RepoPath
    if (-not (Test-Path $path)) { return $null }
    $text = (Get-Content $path -Raw -Encoding UTF8)
    if (-not $text) { return $null }
    $text = $text.Trim()
    if (-not $text) { return $null }
    $line = $text -split "`r?`n" | Where-Object {
        $_ -match '\S' -and $_ -notmatch '^\s*#'
    } | Select-Object -First 1
    if (-not $line) { return $null }
    return $line.Trim()
}

function Get-AuthorFromCommitMessage {
    param(
        [string]$Message,
        [string]$MachineTag
    )
    if ($Message -match '^\[(Cursor|Claude)\]') {
        return $Matches[1]
    }
    return $MachineTag
}

function Clear-CommitMessageFile {
    param([string]$RepoPath)
    $path = Get-CommitMessageFilePath -RepoPath $RepoPath
    $header = @(
        "# Jedna linia wiadomosci commita (bez tego daemon uzyje auto[MachineTag]):"
        "# [Cursor] opis etapu - agent Cursor (PC Filip)"
        "# [Claude] opis etapu - agent Claude Cowork (PC ZW)"
        "#"
        "# Po udanym commicie plik jest czyszczony automatycznie."
        ""
    ) -join "`n"
    Set-Content -Path $path -Value $header -Encoding UTF8 -NoNewline
    Add-Content -Path $path -Value "" -Encoding UTF8
}

function Append-CommitLog {
    param(
        [string]$RepoPath,
        [string]$Hash,
        [string]$Message,
        [string]$Author
    )
    $logPath = Get-CommitLogFilePath -RepoPath $RepoPath
    if (-not (Test-Path $logPath)) {
        $header = @(
            "# Historia nazwanych commitow (append-only, dopisuje GitSyncDaemon)"
            ""
            "| Data | Autor | Hash | Wiadomosc |"
            "|------|-------|------|-----------|"
            ""
        ) -join "`n"
        Set-Content -Path $logPath -Value $header -Encoding UTF8
    }
    $safeMsg = ($Message -replace '\|', '/')
    $line = "| {0} | {1} | {2} | {3} |" -f (Get-Date -Format "yyyy-MM-dd HH:mm"), $Author, $Hash, $safeMsg
    Add-Content -Path $logPath -Value $line -Encoding UTF8
}

function Invoke-GitSyncCommit {
    param(
        [string]$RepoPath,
        [string]$MachineTag,
        [switch]$Manual
    )
    & git -C $RepoPath add -A 2>&1 | Out-Null
    $pending = Get-PendingCommitMessage -RepoPath $RepoPath
    $named = $false
    if ($pending) {
        $commitMsg = $pending
        $named = $true
    } else {
        $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        if ($Manual) {
            $commitMsg = "auto[Manual] $stamp"
        } else {
            $commitMsg = "auto[$MachineTag] $stamp"
        }
    }
    & git -C $RepoPath commit -m $commitMsg 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        return @{ Ok = $false; Message = $commitMsg; Named = $named }
    }
    $hash = (& git -C $RepoPath rev-parse --short HEAD 2>$null)
    if ($hash) { $hash = $hash.Trim() }
    if ($named) {
        $author = Get-AuthorFromCommitMessage -Message $commitMsg -MachineTag $MachineTag
        Append-CommitLog -RepoPath $RepoPath -Hash $hash -Message $commitMsg -Author $author
        Clear-CommitMessageFile -RepoPath $RepoPath
        if (-not $Manual) {
            Show-ToastIfAvailable -Title "SchemaGen: commit" -Text $commitMsg
        }
    }
    return @{ Ok = $true; Message = $commitMsg; Named = $named; Hash = $hash }
}

function Show-ToastIfAvailable {
    param([string]$Title, [string]$Text)
}
