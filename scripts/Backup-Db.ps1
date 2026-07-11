<#
  Backup-Db.ps1 - kopia data/schemagen.db -> data/backups/schemagen-YYYYMMDD.db
  Wołany z harmonogramu Windows lub ręcznie.
#>
param(
    [string]$RepoPath = (Split-Path -Parent $PSScriptRoot)
)

$venvPy = Join-Path $RepoPath ".venv311\Scripts\python.exe"
$py = if (Test-Path $venvPy) { $venvPy } else { "python" }

Push-Location $RepoPath
try {
    & $py -c "from backend.db_backup import backup_schemagen_db; p=backup_schemagen_db(); print(p or 'brak bazy')"
} finally {
    Pop-Location
}
