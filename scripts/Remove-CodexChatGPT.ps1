<#
Пурра тоза кардани боқимондаҳои Codex ва ChatGPT дар ҳамин Windows.
Пешфарз: фақат РӮЙХАТ (ҳеҷ чиз нест намешавад).
  .\scripts\Remove-CodexChatGPT.ps1                     # рӯйхат
  .\scripts\Remove-CodexChatGPT.ps1 -Delete             # ҷузвдонҳо → Recycle Bin, task-ҳо нест
  .\scripts\Remove-CodexChatGPT.ps1 -Delete -RemoveApps # + барномаҳои Codex/ChatGPT нест
  -IncludeWorkspace  Documents\Codex-ро ҳам (лоиҳаҳо ва worktree-ҳо!) ба Recycle Bin
Ҷузвдонҳо ба Recycle Bin мераванд, яъне баргардондан мумкин. auth/session нусха намешавад.
Ҳисоби ChatGPT (Custom Instructions, memory, плагинҳои upload-шуда) дар сервер аст — ин скрипт онро намерасад.
#>
[CmdletBinding()]
param([switch]$Delete, [switch]$RemoveApps, [switch]$IncludeWorkspace)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Танҳо Windows.' }
Add-Type -AssemblyName Microsoft.VisualBasic
$docs = [Environment]::GetFolderPath('MyDocuments')
$folders = @(
    (Join-Path $env:USERPROFILE '.codex'),
    (Join-Path $env:USERPROFILE '.agents\skills'),
    (Join-Path $env:USERPROFILE '.agents\plugins'),
    (Join-Path $env:USERPROFILE '.openclaw-autoclaw'),
    (Join-Path $docs 'CodexSetting'),
    'D:\User\CodexAutoStart'
)
$folders += @(Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'Packages') -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like 'OpenAI.*' } | ForEach-Object { $_.FullName })
foreach ($base in @($env:APPDATA, $env:LOCALAPPDATA)) {
    $folders += @(Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^(Codex|ChatGPT|OpenAI)' } | ForEach-Object { $_.FullName })
}
$workspace = Join-Path $docs 'Codex'
if ($IncludeWorkspace) { $folders += $workspace }
$folders = @($folders | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)
$tasks = @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -match '^(CodexSetting|CodexAutoStart)' })
$apps = @(Get-AppxPackage -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'OpenAI.*' -or $_.Name -like '*ChatGPT*' })
$procs = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^(codex|ChatGPT)$' -or ($_.Path -and $_.Path -like '*\OpenAI*') })
$npm = $null
if (Get-Command npm -ErrorAction SilentlyContinue) { $npm = (& npm ls -g --depth=0 @openai/codex 2>$null) -match '@openai/codex' }

Write-Output '=== Ҷузвдонҳо ==='; $folders | ForEach-Object { Write-Output "  $_" }
if (-not $IncludeWorkspace -and (Test-Path -LiteralPath $workspace)) { Write-Output "  (дахл карда намешавад, лоиҳаҳо: $workspace — барои он -IncludeWorkspace)" }
Write-Output '=== Scheduled tasks ==='; $tasks | ForEach-Object { Write-Output "  $($_.TaskPath)$($_.TaskName)" }
Write-Output '=== Барномаҳо (фақат бо -RemoveApps) ==='; $apps | ForEach-Object { Write-Output "  $($_.Name) $($_.Version)" }
if ($npm) { Write-Output '  npm global: @openai/codex' }
Write-Output '=== Processes, ки пеш аз нест кардан баста мешаванд ==='; $procs | ForEach-Object { Write-Output "  $($_.Name) [$($_.Id)]" }

if (-not $Delete) { Write-Output ''; Write-Output 'Ин фақат рӯйхат буд. Барои нест кардан: -Delete (ва -RemoveApps барои барномаҳо).'; return }

$procs | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2
foreach ($t in $tasks) { Stop-ScheduledTask -TaskName $t.TaskName -TaskPath $t.TaskPath -ErrorAction SilentlyContinue; Unregister-ScheduledTask -TaskName $t.TaskName -TaskPath $t.TaskPath -Confirm:$false; Write-Output "task нест шуд: $($t.TaskName)" }
foreach ($f in $folders) {
    try { [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($f, 'OnlyErrorDialogs', 'SendToRecycleBin'); Write-Output "ба Recycle Bin: $f" }
    catch { Write-Warning "нашуд: $f — $($_.Exception.Message)" }
}
if ($RemoveApps) {
    foreach ($a in $apps) { try { Remove-AppxPackage -Package $a.PackageFullName; Write-Output "барнома нест шуд: $($a.Name)" } catch { Write-Warning "барнома нашуд: $($a.Name) — $($_.Exception.Message)" } }
    if ($npm) { & npm uninstall -g @openai/codex; Write-Output 'npm: @openai/codex нест шуд' }
}
Write-Output ''
Write-Output 'Тамом. Санҷиш: скриптро бе -Delete аз нав ронед — рӯйхат бояд холӣ бошад.'
Write-Output 'Дар сервер (дастӣ): ChatGPT → Settings → Personalization (Custom Instructions, Memory), Plugins (AUTORUN, Шеф Rules), Connections → Control this PC.'
