[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$CodexExe, [Parameter(Mandatory=$true)][string]$AppRoot)

# This installs the owner's bundled, local plugin. It does not upload it to
# ChatGPT or make any claim that Android can see it.
$ErrorActionPreference = 'Stop'
function Result([string]$Status, [string]$Detail) {
    [pscustomobject]@{status=$Status; detail=$Detail}
}
function Read-JsonCommand([string[]]$Arguments) {
    $output = & $CodexExe @Arguments 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Codex command failed: $($Arguments -join ' ')" }
    return (($output -join "`n") | ConvertFrom-Json)
}
try {
    $appPath = [IO.Path]::GetFullPath($AppRoot).TrimEnd('\')
    $markets = Read-JsonCommand @('plugin','marketplace','list','--json')
    if (-not $markets.PSObject.Properties['marketplaces']) { throw 'Invalid marketplace list.' }
    $ours = @($markets.marketplaces | Where-Object { $_.name -eq 'codex-setting' })
    if ($ours.Count -gt 1) { throw 'Multiple codex-setting marketplace entries.' }
    if ($ours.Count -eq 1) {
        $existingPath = [IO.Path]::GetFullPath([string]$ours[0].root).TrimEnd('\')
        if (-not $existingPath.Equals($appPath,[StringComparison]::OrdinalIgnoreCase)) {
            return (Result 'conflict' 'The codex-setting marketplace already points elsewhere. It was not changed.')
        }
    } else {
        $null = Read-JsonCommand @('plugin','marketplace','add',$appPath,'--json')
        $markets = Read-JsonCommand @('plugin','marketplace','list','--json')
        $ours = @($markets.marketplaces | Where-Object { $_.name -eq 'codex-setting' })
        if ($ours.Count -ne 1 -or -not ([IO.Path]::GetFullPath([string]$ours[0].root).TrimEnd('\')).Equals($appPath,[StringComparison]::OrdinalIgnoreCase)) { throw 'Marketplace registration could not be verified.' }
    }
    $plugins = Read-JsonCommand @('plugin','list','--marketplace','codex-setting','--json')
    if (-not $plugins.PSObject.Properties['installed']) { throw 'Invalid plugin list.' }
    $installed = @($plugins.installed | Where-Object { $_.pluginId -eq 'autorun@codex-setting' })
    if ($installed.Count -gt 1) { throw 'Multiple AUTORUN plugin entries.' }
    if ($installed.Count -eq 1 -and -not $installed[0].enabled) {
        return (Result 'disabled' 'The existing AUTORUN plugin is disabled; its setting was preserved.')
    }
    if ($installed.Count -eq 0) {
        $null = Read-JsonCommand @('plugin','add','autorun@codex-setting','--json')
        $plugins = Read-JsonCommand @('plugin','list','--marketplace','codex-setting','--json')
        $installed = @($plugins.installed | Where-Object { $_.pluginId -eq 'autorun@codex-setting' -and $_.enabled })
        if ($installed.Count -ne 1) { throw 'AUTORUN plugin installation could not be verified.' }
        return (Result 'installed' 'The local AUTORUN plugin was installed and verified.')
    }
    return (Result 'present' 'The local AUTORUN plugin was already installed and enabled.')
} catch {
    return (Result 'error' $_.Exception.Message)
}
