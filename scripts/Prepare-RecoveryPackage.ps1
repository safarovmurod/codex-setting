[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RecoveryRoot,
    [Parameter(Mandatory=$true)][string]$ArchiveName,
    [Parameter(Mandatory=$true)][string]$DownloadUrl,
    [Parameter(Mandatory=$true)][string]$Sha256,
    [string]$ArchivePath
)
$ErrorActionPreference = 'Stop'
$recoveryPath = [IO.Path]::GetFullPath($RecoveryRoot).TrimEnd('\')
if (-not [IO.Path]::IsPathRooted($RecoveryRoot) -or $recoveryPath -eq [IO.Path]::GetPathRoot($recoveryPath).TrimEnd('\')) { throw 'An absolute recovery directory is required.' }
if ($ArchiveName -ne [IO.Path]::GetFileName($ArchiveName) -or $ArchiveName -match '[\\/:\r\n]' -or $ArchiveName -in @('.', '..') -or -not $ArchiveName) { throw 'Invalid archive name.' }
if ($Sha256 -notmatch '^[a-fA-F0-9]{64}$') { throw 'Invalid archive digest.' }
if ([Uri]$DownloadUrl -and ([Uri]$DownloadUrl).Scheme -ne 'https') { throw 'A pinned HTTPS download is required.' }
function Assert-PlainPath([string]$Path) {
    $itemPath = [IO.Path]::GetFullPath($Path)
    while ($itemPath) {
        if ((Test-Path -LiteralPath $itemPath) -and ((Get-Item -LiteralPath $itemPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Linked recovery path refused: $itemPath" }
        $parentPath = Split-Path -Parent $itemPath
        if ($parentPath -eq $itemPath) { break }
        $itemPath = $parentPath
    }
}
function Test-ArchiveDigest([string]$Path) {
    Assert-PlainPath $Path
    return (Test-Path -LiteralPath $Path -PathType Leaf) -and ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -eq $Sha256)
}
function Get-SafeEntryPath([string]$Base, $Entry) {
    $prefix = [IO.Path]::GetFullPath($Base).TrimEnd('\') + '\'
    $target = [IO.Path]::GetFullPath((Join-Path $Base $Entry.FullName))
    if (-not $target.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase) -or (($Entry.ExternalAttributes -shr 16) -band 0xF000) -eq 0xA000) { throw 'Unsafe archive entry.' }
    return $target
}
function Assert-ArchiveLayout($Zip, [string]$Base) {
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($entry in $Zip.Entries) {
        $target = Get-SafeEntryPath $Base $entry
        if (-not $seen.Add($target.TrimEnd('\'))) { throw 'Duplicate archive entry.' }
    }
    foreach ($relative in @('payload/runtime/python.exe','payload/runtime/pythonw.exe','payload/app/src/auto_resume.py')) {
        if (-not ($Zip.Entries | Where-Object { $_.FullName.Replace('\','/') -eq $relative })) { throw 'Incomplete recovery archive.' }
    }
}
function Test-PackageMatches($Zip, [string]$Base) {
    if (-not (Test-Path -LiteralPath $Base -PathType Container)) { return $false }
    Assert-PlainPath $Base
    $expected = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($entry in $Zip.Entries) {
        $target = Get-SafeEntryPath $Base $entry
        Assert-PlainPath $target
        if ($entry.FullName.EndsWith('/') -or $entry.FullName.EndsWith('\')) { continue }
        [void]$expected.Add($target)
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { return $false }
        $stream = $entry.Open()
        $hasher = [Security.Cryptography.SHA256]::Create()
        try { $expectedHash = ([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-','') }
        finally { $hasher.Dispose(); $stream.Dispose() }
        if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $expectedHash) { return $false }
    }
    $pending = [Collections.Generic.Queue[string]]::new()
    $pending.Enqueue($Base)
    while ($pending.Count) {
        foreach ($file in Get-ChildItem -LiteralPath $pending.Dequeue() -Force) {
            Assert-PlainPath $file.FullName
            if ($file.PSIsContainer) { $pending.Enqueue($file.FullName); continue }
            if (-not $expected.Contains($file.FullName) -and -not ($file.Extension -eq '.pyc' -and $file.DirectoryName -match '[\\/]__pycache__([\\/]|$)')) { return $false }
        }
    }
    return $true
}
Assert-PlainPath $recoveryPath
New-Item -ItemType Directory -Path $recoveryPath -Force | Out-Null
$archive = Join-Path $recoveryPath $ArchiveName
$package = Join-Path $recoveryPath 'package'
Assert-PlainPath $archive
Assert-PlainPath $package
$stage = Join-Path $recoveryPath ('.prepare-'+[guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $stage | Out-Null
$archiveRepaired = $false
$packageRepaired = $false
try {
    $selectedArchive = $archive
    if ($ArchivePath) {
        if (-not (Test-ArchiveDigest $ArchivePath)) { throw 'Archive hash mismatch.' }
        $selectedArchive = [IO.Path]::GetFullPath($ArchivePath)
    } elseif (-not (Test-ArchiveDigest $archive)) {
        $selectedArchive = Join-Path $stage $ArchiveName
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $selectedArchive -UseBasicParsing -TimeoutSec 180
        if (-not (Test-ArchiveDigest $selectedArchive)) { throw 'Archive hash mismatch; previous package was retained.' }
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead($selectedArchive)
    try {
        Assert-ArchiveLayout $zip $package
        $matches = Test-PackageMatches $zip $package
    } finally { $zip.Dispose() }
    $stagedPackage = Join-Path $stage 'package'
    if (-not $matches) {
        [IO.Compression.ZipFile]::ExtractToDirectory($selectedArchive,$stagedPackage)
        $zip = [IO.Compression.ZipFile]::OpenRead($selectedArchive)
        try { if (-not (Test-PackageMatches $zip $stagedPackage)) { throw 'Extracted recovery package is incomplete.' } }
        finally { $zip.Dispose() }
    }
    if ([IO.Path]::GetFullPath($selectedArchive) -ne [IO.Path]::GetFullPath($archive)) {
        # The existing archive is an owned immutable cache, not a configuration file.
        # Replace it only after the replacement and package layout have been verified.
        if (-not (Test-ArchiveDigest $archive)) {
            Copy-Item -LiteralPath $selectedArchive -Destination (Join-Path $stage 'verified.zip')
            if (-not (Test-ArchiveDigest (Join-Path $stage 'verified.zip'))) { throw 'Archive copy verification failed.' }
            Move-Item -LiteralPath (Join-Path $stage 'verified.zip') -Destination $archive -Force
            $archiveRepaired = $true
        }
    }
    if (-not $matches) {
        $oldPackage = $null
        if (Test-Path -LiteralPath $package) {
            $backupRoot = Join-Path $recoveryPath 'backups'
            Assert-PlainPath $backupRoot
            New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
            $oldPackage = Join-Path $backupRoot ('package-'+[guid]::NewGuid().ToString())
            Assert-PlainPath $oldPackage
            # Both absolute move destinations are confined under the selected recovery root.
            if (-not ([IO.Path]::GetFullPath($oldPackage)).StartsWith($recoveryPath+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe package backup target.' }
            Move-Item -LiteralPath $package -Destination $oldPackage
        }
        try { Move-Item -LiteralPath $stagedPackage -Destination $package }
        catch {
            if ($oldPackage -and -not (Test-Path -LiteralPath $package)) { Move-Item -LiteralPath $oldPackage -Destination $package }
            throw
        }
        $packageRepaired = $true
    }
    [pscustomobject]@{ archiveRepaired=$archiveRepaired; packageRepaired=$packageRepaired }
} finally {
    # Never recursively remove a computed path before verifying its resolved boundary.
    $absoluteStage = [IO.Path]::GetFullPath($stage)
    if ((Split-Path -Parent $absoluteStage) -ne $recoveryPath -or (Split-Path -Leaf $absoluteStage) -notmatch '^\.prepare-[0-9a-f-]{36}$') { throw 'Unsafe staging cleanup target.' }
    Assert-PlainPath $absoluteStage
    if (Test-Path -LiteralPath $absoluteStage) { Remove-Item -LiteralPath $absoluteStage -Recurse -Force }
}
