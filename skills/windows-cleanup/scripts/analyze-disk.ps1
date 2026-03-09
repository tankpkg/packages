<#
.SYNOPSIS
  Windows Disk Cleanup Analyzer
.DESCRIPTION
  Scans known cleanup targets and reports sizes with risk levels.
.PARAMETER Json
  Output as JSON instead of table
.PARAMETER DevOnly
  Only scan developer tool caches
.PARAMETER Quick
  Skip slow scans (stale node_modules, large file search)
.EXAMPLE
  .\analyze-disk.ps1
  .\analyze-disk.ps1 -Json
  .\analyze-disk.ps1 -DevOnly -Quick
#>
param(
  [switch]$Json,
  [switch]$DevOnly,
  [switch]$Quick
)

$ErrorActionPreference = 'SilentlyContinue'

function Get-DirSizeBytes([string]$Path) {
  if (Test-Path $Path) {
    (Get-ChildItem $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
      Measure-Object -Property Length -Sum).Sum
  } else { 0 }
}

function Format-Size([long]$Bytes) {
  if ($Bytes -ge 1GB) { "{0:N1} GB" -f ($Bytes / 1GB) }
  elseif ($Bytes -ge 1MB) { "{0:N0} MB" -f ($Bytes / 1MB) }
  elseif ($Bytes -ge 1KB) { "{0:N0} KB" -f ($Bytes / 1KB) }
  else { "$Bytes B" }
}

$results = [System.Collections.ArrayList]::new()

function Add-Result([string]$Category, [long]$SizeBytes, [string]$Risk, [string]$Path) {
  if ($SizeBytes -gt 0) {
    [void]$results.Add([PSCustomObject]@{
      Category  = $Category
      SizeBytes = $SizeBytes
      SizeHuman = Format-Size $SizeBytes
      Risk      = $Risk
      Path      = $Path
    })
  }
}

$drive = Get-PSDrive C
$totalGB = [math]::Round(($drive.Used + $drive.Free) / 1GB, 1)
$freeGB  = [math]::Round($drive.Free / 1GB, 1)
$usedPct = [math]::Round($drive.Used / ($drive.Used + $drive.Free) * 100, 1)

Write-Host "Scanning Windows disk for cleanup targets..." -ForegroundColor Cyan

if (-not $DevOnly) {
  Write-Host "  Scanning temp files..."
  Add-Result "User Temp" (Get-DirSizeBytes $env:TEMP) "safe" $env:TEMP
  Add-Result "Windows Temp" (Get-DirSizeBytes "C:\Windows\Temp") "safe" "C:\Windows\Temp"

  Write-Host "  Scanning Windows Update cache..."
  Add-Result "Windows Update Cache" (Get-DirSizeBytes "C:\Windows\SoftwareDistribution\Download") "safe" "C:\Windows\SoftwareDistribution\Download"

  $doPath = "C:\Windows\ServiceProfiles\NetworkService\AppData\Local\Microsoft\Windows\DeliveryOptimization"
  Add-Result "Delivery Optimization" (Get-DirSizeBytes $doPath) "safe" $doPath

  Write-Host "  Scanning Recycle Bin..."
  try {
    $rbSize = (New-Object -ComObject Shell.Application).Namespace(0xA).Items() |
      Measure-Object -Property Size -Sum
    Add-Result "Recycle Bin" $rbSize.Sum "moderate" '$Recycle.Bin'
  } catch {}

  Write-Host "  Scanning Windows.old..."
  if (Test-Path "C:\Windows.old") {
    Add-Result "Windows.old" (Get-DirSizeBytes "C:\Windows.old") "moderate" "C:\Windows.old"
  }

  $hibFile = Get-Item "C:\hiberfil.sys" -Force -ErrorAction SilentlyContinue
  if ($hibFile) {
    Add-Result "Hibernation File" $hibFile.Length "low" "C:\hiberfil.sys"
  }

  Add-Result "Prefetch" (Get-DirSizeBytes "C:\Windows\Prefetch") "safe" "C:\Windows\Prefetch"

  $thumbs = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\thumbcache_*.db" -Force -ErrorAction SilentlyContinue |
    Measure-Object -Property Length -Sum
  Add-Result "Thumbnail Cache" $thumbs.Sum "safe" "$env:LOCALAPPDATA\...\Explorer\thumbcache_*"
}

Write-Host "  Scanning browser caches..."
Add-Result "Chrome Cache" (Get-DirSizeBytes "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache") "safe" "Chrome\Cache"
Add-Result "Edge Cache" (Get-DirSizeBytes "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache") "safe" "Edge\Cache"

$ffProfiles = Get-ChildItem "$env:LOCALAPPDATA\Mozilla\Firefox\Profiles" -Directory -ErrorAction SilentlyContinue
$ffTotal = 0
foreach ($p in $ffProfiles) { $ffTotal += Get-DirSizeBytes "$($p.FullName)\cache2" }
Add-Result "Firefox Cache" $ffTotal "safe" "Firefox\Profiles\*\cache2"

Write-Host "  Scanning dev tool caches..."
Add-Result "npm Cache" (Get-DirSizeBytes "$env:APPDATA\npm-cache") "safe" "$env:APPDATA\npm-cache"
Add-Result "Yarn Cache" (Get-DirSizeBytes "$env:LOCALAPPDATA\Yarn\Cache") "safe" "Yarn\Cache"

if (Get-Command pnpm -ErrorAction SilentlyContinue) {
  $pnpmStore = pnpm store path 2>$null
  if ($pnpmStore -and (Test-Path $pnpmStore)) {
    Add-Result "pnpm Store" (Get-DirSizeBytes $pnpmStore) "safe" $pnpmStore
  }
}

Add-Result "pip Cache" (Get-DirSizeBytes "$env:LOCALAPPDATA\pip\Cache") "safe" "pip\Cache"

$cargoTotal = 0
foreach ($sub in @("$env:USERPROFILE\.cargo\registry\cache","$env:USERPROFILE\.cargo\registry\src","$env:USERPROFILE\.cargo\git\checkouts")) {
  $cargoTotal += Get-DirSizeBytes $sub
}
Add-Result "Cargo Cache" $cargoTotal "safe" "~\.cargo\registry + git"

if (Get-Command go -ErrorAction SilentlyContinue) {
  Add-Result "Go Module Cache" (Get-DirSizeBytes "$env:USERPROFILE\go\pkg\mod") "safe" "~\go\pkg\mod"
  $goBuild = "$env:LOCALAPPDATA\go-build"
  Add-Result "Go Build Cache" (Get-DirSizeBytes $goBuild) "safe" $goBuild
}

Add-Result "NuGet Cache" (Get-DirSizeBytes "$env:USERPROFILE\.nuget\packages") "safe" "~\.nuget\packages"
Add-Result "Gradle Cache" (Get-DirSizeBytes "$env:USERPROFILE\.gradle\caches") "safe" "~\.gradle\caches"
Add-Result "Gradle Wrapper" (Get-DirSizeBytes "$env:USERPROFILE\.gradle\wrapper\dists") "safe" "~\.gradle\wrapper\dists"

$jbTotal = 0
Get-ChildItem "$env:LOCALAPPDATA\JetBrains" -Directory -ErrorAction SilentlyContinue |
  ForEach-Object { $jbTotal += Get-DirSizeBytes (Join-Path $_.FullName "caches") }
Add-Result "JetBrains Caches" $jbTotal "safe" "JetBrains\*\caches"

$vscTotal = 0
foreach ($sub in @("$env:APPDATA\Code\Cache","$env:APPDATA\Code\CachedData","$env:APPDATA\Code\CachedExtensions","$env:APPDATA\Code\logs")) {
  $vscTotal += Get-DirSizeBytes $sub
}
Add-Result "VS Code Caches" $vscTotal "safe" "Code\Cache*"

Write-Host "  Scanning Docker..."
$dockerVhdx = Get-ChildItem "$env:LOCALAPPDATA\Docker\wsl" -Recurse -Filter "*.vhdx" -ErrorAction SilentlyContinue |
  Measure-Object -Property Length -Sum
Add-Result "Docker Desktop VM" $dockerVhdx.Sum "moderate" "Docker\wsl\*.vhdx"

$wslVhdx = Get-ChildItem "$env:LOCALAPPDATA\Packages" -Recurse -Filter "ext4.vhdx" -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch 'Docker' } |
  Measure-Object -Property Length -Sum
Add-Result "WSL2 Virtual Disks" $wslVhdx.Sum "moderate" "Packages\*\ext4.vhdx"

if (Get-Command scoop -ErrorAction SilentlyContinue) {
  $scoopCache = "$env:USERPROFILE\scoop\cache"
  Add-Result "Scoop Cache" (Get-DirSizeBytes $scoopCache) "safe" $scoopCache
}

Add-Result "Composer Cache" (Get-DirSizeBytes "$env:USERPROFILE\.composer\cache") "safe" "~\.composer\cache"

if (-not $Quick) {
  Write-Host "  Scanning for stale node_modules (this may take a moment)..."
  $nmTotal = 0; $nmCount = 0
  $devDirs = @("$env:USERPROFILE\dev","$env:USERPROFILE\projects","$env:USERPROFILE\code",
               "$env:USERPROFILE\source\repos","$env:USERPROFILE\repos")
  foreach ($dir in $devDirs) {
    if (Test-Path $dir) {
      Get-ChildItem $dir -Filter "node_modules" -Directory -Recurse -Depth 4 -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        ForEach-Object {
          $s = Get-DirSizeBytes $_.FullName
          $nmTotal += $s; $nmCount++
        }
    }
  }
  if ($nmTotal -gt 0) {
    Add-Result "Stale node_modules ($nmCount dirs, >30d)" $nmTotal "moderate" "various dev\**\node_modules"
  }

  Write-Host "  Scanning for stale Rust target/ dirs..."
  $rtTotal = 0; $rtCount = 0
  foreach ($dir in $devDirs) {
    if (Test-Path $dir) {
      Get-ChildItem $dir -Filter "target" -Directory -Recurse -Depth 4 -ErrorAction SilentlyContinue |
        Where-Object {
          $_.LastWriteTime -lt (Get-Date).AddDays(-30) -and
          (Test-Path (Join-Path (Split-Path $_.FullName -Parent) "Cargo.toml"))
        } |
        ForEach-Object {
          $s = Get-DirSizeBytes $_.FullName
          $rtTotal += $s; $rtCount++
        }
    }
  }
  if ($rtTotal -gt 0) {
    Add-Result "Stale Rust target/ ($rtCount dirs, >30d)" $rtTotal "moderate" "various dev\**\target"
  }
}

Write-Host "  Scan complete." -ForegroundColor Green

$sorted = $results | Sort-Object SizeBytes -Descending

if ($Json) {
  @{
    disk = @{ total = "${totalGB} GB"; free = "${freeGB} GB"; used_pct = "${usedPct}%" }
    targets = $sorted | ForEach-Object {
      @{ category = $_.Category; size_bytes = $_.SizeBytes; size_human = $_.SizeHuman; risk = $_.Risk; path = $_.Path }
    }
  } | ConvertTo-Json -Depth 3
} else {
  Write-Host ""
  Write-Host "Windows Disk Cleanup Report" -ForegroundColor Yellow
  Write-Host "==========================" -ForegroundColor Yellow
  Write-Host ""
  Write-Host "Disk: ${totalGB} GB total, ${freeGB} GB free (${usedPct}% used)"
  Write-Host ""

  $safeTotal = 0; $modTotal = 0; $highTotal = 0; $lowTotal = 0; $grandTotal = 0

  "{0,-45} {1,10}   {2,-10}" -f "Category", "Size", "Risk"
  "{0,-45} {1,10}   {2,-10}" -f ("-" * 45), ("-" * 10), ("-" * 10)

  foreach ($r in $sorted) {
    if ($r.SizeBytes -lt 10MB) { continue }
    "{0,-45} {1,10}   {2,-10}" -f $r.Category, $r.SizeHuman, $r.Risk
    $grandTotal += $r.SizeBytes
    switch ($r.Risk) {
      "safe"     { $safeTotal += $r.SizeBytes }
      "low"      { $lowTotal += $r.SizeBytes }
      "moderate" { $modTotal += $r.SizeBytes }
      "high"     { $highTotal += $r.SizeBytes }
    }
  }

  Write-Host ""
  "{0,-45} {1,10}" -f ("-" * 45), ("-" * 10)
  "{0,-45} {1,10}" -f "Total reclaimable", (Format-Size $grandTotal)
  Write-Host ""
  "  {0,-43} {1,10}" -f "Safe to clean now", (Format-Size $safeTotal)
  "  {0,-43} {1,10}" -f "Low risk (confirm)", (Format-Size $lowTotal)
  "  {0,-43} {1,10}" -f "Moderate risk (review first)", (Format-Size $modTotal)
  "  {0,-43} {1,10}" -f "High risk (explicit opt-in only)", (Format-Size $highTotal)
}
