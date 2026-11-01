[CmdletBinding()]
param(
    [Parameter(Position=0)][ValidateSet('doctor','status','runtime-doctor','repair','uninstall','autorun','autoruoff')][string]$Command='status',
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$Remaining
)
$ErrorActionPreference='Stop'
$codexHome=if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$info=Get-Content -LiteralPath (Join-Path $codexHome 'codex-setting.json') -Raw | ConvertFrom-Json
if ($Command -eq 'repair') { & (Join-Path $info.root 'app\Install.ps1') -InstallRoot $info.root; exit $LASTEXITCODE }
if ($Command -eq 'uninstall') {
    $task=Get-ScheduledTask -TaskName 'CodexSetting.Autorun' -ErrorAction SilentlyContinue
    if ($task) {
        if (-not $task.Actions.Arguments.Contains($info.root)) { throw 'Foreign scheduled task refused.' }
        Stop-ScheduledTask -TaskName 'CodexSetting.Autorun'
        Unregister-ScheduledTask -TaskName 'CodexSetting.Autorun' -Confirm:$false
    }
}
& $info.python (Join-Path $info.root 'app\runner.py') --install-root $info.root $Command @Remaining
exit $LASTEXITCODE
