#
# codex-setting bootstrap: one command for the whole setup in PowerShell.
#
# From a clone (recommended, this repo is private):
#   .\bootstrap.ps1
#
# One line, no clone kept:
#   $d="$env:TEMP\codex-setting"; Remove-Item $d -Recurse -Force -ErrorAction SilentlyContinue; git clone -q https://github.com/safarovmurod/codex-setting.git $d; & "$d\bootstrap.ps1"
#
# Checks afterwards:
#   .\bootstrap.ps1 -Action doctor
#
# ASCII only on purpose: a UTF-8 BOM breaks `irm | iex`, and without a BOM
# Windows PowerShell 5.1 reads non-ASCII text in a .ps1 file as ANSI.
#
[CmdletBinding()]
param(
    [ValidateSet('install', 'doctor', 'status', 'runtime-doctor', 'repair', 'uninstall')][string]$Action = 'install',
    [string]$Ref = 'main',
    [string]$InstallRoot,
    [switch]$NoStartup
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

if ($env:OS -ne 'Windows_NT') { throw 'Windows 10/11 x64 is required.' }
if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'The pinned recovery runtime requires Windows x64.' }

$repository = 'https://github.com/safarovmurod/codex-setting.git'
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$descriptor = Join-Path $codexHome 'codex-setting.json'

function Get-ExistingRoot {
    if (-not (Test-Path -LiteralPath $descriptor)) { return $null }
    try {
        $info = Get-Content -LiteralPath $descriptor -Raw | ConvertFrom-Json
        if ($info.root -and (Test-Path -LiteralPath $info.root)) { return [string]$info.root }
    } catch {}
    return $null
}

# An install already on this PC keeps its own root, so a re-run repairs it instead of forking a second copy.
$existingRoot = Get-ExistingRoot
if (-not $InstallRoot) {
    $InstallRoot = if ($existingRoot) { $existingRoot } else { Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'CodexSetting' }
}

if ($Action -ne 'install') {
    if (-not $existingRoot) { throw 'No installation found on this PC. Run .\bootstrap.ps1 first.' }
    $controller = Join-Path $existingRoot 'app\CodexSetting.ps1'
    if (-not (Test-Path -LiteralPath $controller)) { throw "Installed controller not found: $controller" }
    Write-Host "Installation: $existingRoot"
    & $controller $Action
    exit $LASTEXITCODE
}

$local = if ($PSScriptRoot) { Join-Path $PSScriptRoot 'Install.ps1' } else { $null }
$work = $null
try {
    if ($local -and (Test-Path -LiteralPath $local)) {
        $installer = $local
        Write-Host "Source: $PSScriptRoot"
    }
    else {
        $work = Join-Path ([IO.Path]::GetTempPath()) ('codex-setting-' + [guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $work | Out-Null
        $source = Join-Path $work 'repo'
        if (Get-Command git -ErrorAction SilentlyContinue) {
            # git carries the owner's stored credentials, which a plain download of a private repo does not.
            Write-Host "Cloning $repository ($Ref)"
            & git clone --quiet --depth 1 --branch $Ref $repository $source
            if ($LASTEXITCODE -ne 0) { throw 'git clone failed. Sign in to GitHub for this account, then run it again.' }
        }
        else {
            $zip = Join-Path $work 'source.zip'
            $url = "https://github.com/safarovmurod/codex-setting/archive/refs/heads/$Ref.zip"
            Write-Host "Downloading $url"
            Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
            Write-Host 'Unpacking'
            Expand-Archive -LiteralPath $zip -DestinationPath $work -Force
            $unpacked = Get-ChildItem -LiteralPath $work -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'Install.ps1') } | Select-Object -First 1
            if (-not $unpacked) { throw 'Install.ps1 was not found in the downloaded archive.' }
            $source = $unpacked.FullName
        }
        $installer = Join-Path $source 'Install.ps1'
        if (-not (Test-Path -LiteralPath $installer)) { throw "Install.ps1 was not found in $source" }
    }

    Write-Host "Install root: $InstallRoot"
    $arguments = @{ InstallRoot = $InstallRoot }
    if ($NoStartup) { $arguments.NoStartup = $true }
    & $installer @arguments
    exit $LASTEXITCODE
}
finally {
    if ($work) { Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue }
}
