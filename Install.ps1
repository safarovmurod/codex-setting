[CmdletBinding()]
param(
    [string]$InstallRoot,
    [string]$ArchivePath,
    [switch]$NoStartup
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows 10/11 x64 is required; Android Remote runs this on its connected Windows host.' }
if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'The pinned recovery runtime requires Windows x64.' }
$documents = [Environment]::GetFolderPath('MyDocuments')
if (-not $InstallRoot) { $InstallRoot = Join-Path $documents 'CodexSetting' }
$rootPath = [IO.Path]::GetFullPath($InstallRoot).TrimEnd('\')
$sourcePath = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\')
if ($rootPath -eq $sourcePath -or $rootPath -eq [IO.Path]::GetPathRoot($rootPath).TrimEnd('\') -or $rootPath -match '["\r\n]') { throw 'Choose a separate, absolute installation folder.' }
function Assert-NoLinks([string]$Path) {
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        if ((Test-Path -LiteralPath $current) -and ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Linked path refused: $current" }
        $parent = Split-Path -Parent $current
        if ($parent -eq $current) { break }
        $current = $parent
    }
}
function Write-Json([string]$Path, $Value) {
    [IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 16), [Text.UTF8Encoding]::new($false))
}
Assert-NoLinks $rootPath
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$markerFile = Join-Path $rootPath 'installation.json'
if (Test-Path -LiteralPath $rootPath) {
    if (Test-Path -LiteralPath $markerFile) {
        $marker = Get-Content -LiteralPath $markerFile -Raw | ConvertFrom-Json
        if ($marker.product -ne 'codex-setting' -or $marker.owner_sid -ne $sid) { throw 'This directory belongs to another installation or user.' }
    } elseif (@(Get-ChildItem -LiteralPath $rootPath -Force).Count) { throw 'The target folder is not empty and is not owned by codex-setting.' }
}
$codex = Get-Command codex.exe -ErrorAction SilentlyContinue
if (-not (Get-AppxPackage -Name 'OpenAI.Codex' -ErrorAction SilentlyContinue)) {
    & winget install --id 9PLM9XGG6VKS -s msstore
    if ($LASTEXITCODE -ne 0) { throw 'Official desktop installation needs owner/Windows action. Run Install.ps1 again after it completes.' }
}
if (-not $codex) {
    throw 'Open ChatGPT/Codex once, sign in and let its native runtime finish installing; then run Install.ps1 again. No authentication will be copied.'
}
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
if ([IO.Path]::GetFullPath($codexHome) -ne [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE '.codex'))) { throw 'A custom CODEX_HOME requires a separate profile; this owner profile targets the standard .codex directory.' }
New-Item -ItemType Directory -Path $rootPath -Force | Out-Null
if (-not (Test-Path -LiteralPath $markerFile)) { Write-Json $markerFile @{product='codex-setting';owner_sid=$sid;host_id=[guid]::NewGuid().ToString();files=@{}} }
$taskName = 'CodexSetting.Autorun'
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($task) {
    if ($task.Actions.Execute -ne (Join-Path $rootPath 'recovery\package\payload\runtime\pythonw.exe') -or -not $task.Actions.Arguments.Contains($rootPath)) { throw 'An unrelated scheduled task uses CodexSetting.Autorun.' }
    Stop-ScheduledTask -TaskName $taskName
}
$app = Join-Path $rootPath 'app'
New-Item -ItemType Directory -Path $app -Force | Out-Null
foreach ($folder in @('src','payload','profiles','skills','docs','third_party','scripts','plugins','.agents/plugins','tools')) {
    $from = Join-Path $sourcePath $folder
    $to = Join-Path $app $folder
    if ([IO.Path]::GetFullPath($from) -eq [IO.Path]::GetFullPath($to)) { continue }
    if (Test-Path -LiteralPath $from) {
        New-Item -ItemType Directory -Path $to -Force | Out-Null
        Get-ChildItem -LiteralPath $from -Force | Copy-Item -Destination $to -Recurse -Force
    }
}
foreach ($name in @('runner.py','Install.ps1','CodexSetting.ps1','README.md','AGENTS.md')) {
    if ($sourcePath -ne $app -and (Test-Path -LiteralPath (Join-Path $sourcePath $name))) { Copy-Item -LiteralPath (Join-Path $sourcePath $name) -Destination (Join-Path $app $name) -Force }
}
$metaPath = Join-Path $app 'third_party\codex-auto-resume\upstream.json'
$meta = Get-Content -LiteralPath $metaPath -Raw | ConvertFrom-Json
if ($meta.version -ne '0.6.17' -or $meta.sha256 -ne '601e8081272a6c5b942ac465ca5d92938eca75007da24fa51cff4b7a6f130d16') { throw 'Unexpected upstream pin.' }
$recovery = Join-Path $rootPath 'recovery'
New-Item -ItemType Directory -Path $recovery -Force | Out-Null
$package = Join-Path $recovery 'package'
$prepare = @{ RecoveryRoot=$recovery; ArchiveName=$meta.archiveName; DownloadUrl=$meta.downloadUrl; Sha256=$meta.sha256 }
if ($ArchivePath) { $prepare.ArchivePath=$ArchivePath }
& (Join-Path $app 'scripts\Prepare-RecoveryPackage.ps1') @prepare | Out-Null
New-Item -ItemType Directory -Path (Join-Path $recovery 'scripts') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $app 'scripts\recovery-control.py') -Destination (Join-Path $recovery 'scripts\recovery-control.py') -Force
Copy-Item -LiteralPath $metaPath -Destination (Join-Path $recovery 'upstream.json') -Force
Write-Json (Join-Path $recovery 'recovery.json') @{schemaVersion=1;product='CodexAutoStart.Recovery';installRoot=$recovery;packageRoot=$package;stateRoot=(Join-Path $recovery 'state');codexExe=$codex.Source;codexHome=$codexHome}
Write-Json (Join-Path $recovery 'installation.json') @{schemaVersion=1;product='CodexAutoStart.Recovery';ownerSid=$sid;upstreamVersion=$meta.version;archiveSha256=$meta.sha256}
$python = Join-Path $package 'payload\runtime\python.exe'
$pythonw = Join-Path $package 'payload\runtime\pythonw.exe'
$runner = Join-Path $app 'runner.py'
$env:PYTHONDONTWRITEBYTECODE = '1'
& $python (Join-Path $recovery 'scripts\recovery-control.py') --config (Join-Path $recovery 'recovery.json') verify
if ($LASTEXITCODE -ne 0) { throw 'Pinned recovery payload validation failed.' }
& $python $runner --install-root $rootPath install --source $app --user-home $env:USERPROFILE --documents $documents
if ($LASTEXITCODE -ne 0) { throw 'Preference installation failed; backups retained.' }
# Keep the original backup; accept only the verified AUTORUN plugin key in the receipt.
$pluginConfigBefore = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $codexHome 'config.toml')))
$pluginResult = & (Join-Path $app 'scripts\Register-AutorunPlugin.ps1') -CodexExe $codex.Source -AppRoot $app
if ($pluginResult.status -in @('installed','present')) {
    $pluginConfigBefore | & $python $runner --install-root $rootPath finalize-plugin-config
    if ($LASTEXITCODE -ne 0) { throw 'Plugin config changed unexpectedly; run doctor and review before repair.' }
    Write-Output "Local AUTORUN plugin: $($pluginResult.status)."
} else {
    Write-Warning "Local AUTORUN plugin: $($pluginResult.status). $($pluginResult.detail)"
}
if (-not $NoStartup) {
    # Preserve old tasks before disabling the superseded global/warm-up behavior.
    $migration = Join-Path $rootPath 'backups\scheduled-tasks'
    New-Item -ItemType Directory -Path $migration -Force | Out-Null
    foreach ($oldName in @('CodexAutoStart.Local','CodexAutoStart.Recovery')) {
        $old = Get-ScheduledTask -TaskName $oldName -ErrorAction SilentlyContinue
        if ($old) {
            if (-not (($old.Actions.Arguments -join ' ').Contains('CodexAutoStart'))) { throw "Unrecognized old task: $oldName" }
            $savePath = Join-Path $migration ($oldName+'.xml')
            if (-not (Test-Path -LiteralPath $savePath)) { [IO.File]::WriteAllText($savePath,(Export-ScheduledTask -TaskName $oldName),[Text.UTF8Encoding]::new($false)) }
            Stop-ScheduledTask -TaskName $oldName
            Disable-ScheduledTask -TaskName $oldName | Out-Null
        }
    }
    $arguments = '"{0}" --install-root "{1}" watch' -f $runner,$rootPath
    $action = New-ScheduledTaskAction -Execute $pythonw -Argument $arguments -WorkingDirectory $rootPath
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $sid
    $principal = New-ScheduledTaskPrincipal -UserId $sid -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    Start-ScheduledTask -TaskName $taskName
}
# Phone/cloud: build the account plugin archive from the installed PC rules (upload stays an owner UI step).
$dist = Join-Path $rootPath 'dist'
& $python (Join-Path $app 'tools\build_mobile_plugin.py') --zip $dist
if ($LASTEXITCODE -ne 0) { Write-Warning 'Шеф Rules plugin archive was not built.' }
$doctorJson = & $python $runner --install-root $rootPath doctor
$doctorJson
Write-Output "Шеф, файлҳо насб шуданд. AUTORUN то даъвати худат фаъол намешавад."
Write-Output "Плагини телефон: $dist (ChatGPT -> Plugins -> Add -> Upload plugin archive)."
Write-Output "Санҷиш: & '$app\CodexSetting.ps1' doctor"
Write-Output 'Қадамҳои боқимонда (UI): docs/personalization.md, Upload-и плагин ва docs/android.md; натиҷа танҳо баъди санҷиши UI тасдиқ мешавад.'
