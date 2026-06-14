Add-Type -AssemblyName System.Windows.Forms

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptDir "GitSyncCommit.ps1")

$repoPath = $scriptDir

$form = New-Object System.Windows.Forms.Form
$form.Text = "SchemaGen Git Sync"
$form.Width = 300
$form.Height = 150
$form.StartPosition = "CenterScreen"

$pushButton = New-Object System.Windows.Forms.Button
$pushButton.Text = "Push"
$pushButton.Width = 80
$pushButton.Height = 30
$pushButton.Left = 20
$pushButton.Top = 40

$pullButton = New-Object System.Windows.Forms.Button
$pullButton.Text = "Pull"
$pullButton.Width = 80
$pullButton.Height = 30
$pullButton.Left = 110
$pullButton.Top = 40

$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Text = "Anuluj"
$cancelButton.Width = 80
$cancelButton.Height = 30
$cancelButton.Left = 200
$cancelButton.Top = 40

$commitHelperPath = (Join-Path $scriptDir "GitSyncCommit.ps1") -replace "'", "''"
$repoPathEscaped = $repoPath -replace "'", "''"

$pushButton.Add_Click({
    Start-Process powershell `
        -ArgumentList "-NoExit", "-Command", "
        . '$commitHelperPath';
        cd '$repoPathEscaped';
        git diff --quiet;
        `$dirty = git status --porcelain;
        if (-not `$dirty) {
            Write-Host 'Brak zmian do wyslania.';
        } else {
            `$r = Invoke-GitSyncCommit -RepoPath '$repoPathEscaped' -MachineTag Manual -Manual;
            if (`$r.Ok) { Write-Host ('Commit: ' + `$r.Message) } else { Write-Host 'Commit nieudany.' }
            git pull --rebase;
            git push;
        }"
    $form.Close()
})

$pullButton.Add_Click({
    Start-Process powershell `
        -ArgumentList "-NoExit", "-Command", "
        cd '$repoPathEscaped';
        git pull --rebase"
    $form.Close()
})

$cancelButton.Add_Click({
    $form.Close()
})

$form.Controls.Add($pushButton)
$form.Controls.Add($pullButton)
$form.Controls.Add($cancelButton)

$form.ShowDialog()
