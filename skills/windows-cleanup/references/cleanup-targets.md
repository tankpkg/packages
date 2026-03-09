# Windows Cleanup Targets

Exhaustive reference of what can be safely cleaned on Windows 10/11,
organized by category. All commands are PowerShell unless noted otherwise.
Run PowerShell as Administrator for items marked (Admin).

## Risk Levels

| Level | Meaning | Action |
|-------|---------|--------|
| Safe | Regenerated automatically, no data loss | Clean without asking |
| Low | Unlikely to cause issues, minor convenience loss | List and confirm |
| Moderate | May require re-download, re-login, or rebuild | Warn and confirm |
| High | Potential data loss if user hasn't backed up | Explain risk, require explicit opt-in |

## 1. Temporary Files

### User Temp

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| User temp | `$env:TEMP` (usually `%LOCALAPPDATA%\Temp`) | Safe | 0.5-10 GB |
| Windows temp | `C:\Windows\Temp` | Safe (Admin) | 0.5-5 GB |
| Recent items | `$env:APPDATA\Microsoft\Windows\Recent` | Safe | minimal |

```powershell
# User temp (safe — apps recreate as needed)
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue

# Windows temp (Admin)
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### Disk Cleanup (cleanmgr)

The built-in tool handles many categories. Run it programmatically:

```powershell
# Interactive
cleanmgr /d C:

# Automated with pre-configured options (Admin)
# First set flags in registry, then run with /sagerun
cleanmgr /sageset:1    # Configure which items to clean (GUI)
cleanmgr /sagerun:1    # Run the saved configuration silently
```

### Storage Sense

Windows 10/11 built-in automatic cleanup:

```powershell
# Enable Storage Sense
$path = "HKCU:\Software\Microsoft\Windows\CurrentVersion\StorageSense\Parameters\StoragePolicy"
Set-ItemProperty -Path $path -Name "01" -Value 1 -Type DWord

# Run Storage Sense now
# Settings > System > Storage > Configure Storage Sense > Clean now
```

## 2. Windows Update & System

### Windows Update Cache

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Update cache | `C:\Windows\SoftwareDistribution\Download` | Safe (Admin) | 1-15 GB |
| Delivery Optimization | `C:\Windows\ServiceProfiles\NetworkService\AppData\Local\Microsoft\Windows\DeliveryOptimization` | Safe (Admin) | 0.5-5 GB |

```powershell
# Stop Windows Update service first (Admin)
Stop-Service wuauserv -Force
Stop-Service bits -Force
Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
Start-Service wuauserv
Start-Service bits
```

### WinSxS (Component Store)

The WinSxS folder stores component versions for Windows features and updates.
It appears huge (10-20 GB) but most content is hard links — actual unique
data is usually 5-8 GB. Never manually delete from WinSxS.

```powershell
# Analyze component store size (Admin)
Dism /Online /Cleanup-Image /AnalyzeComponentStore

# Clean superseded components (Admin, safe)
Dism /Online /Cleanup-Image /StartComponentCleanup

# Aggressive: also remove old service pack backups (Admin)
Dism /Online /Cleanup-Image /StartComponentCleanup /ResetBase
# Warning: /ResetBase prevents uninstalling previous updates
```

### Windows.old

Left after a major Windows upgrade. Contains the entire previous installation.

```powershell
# Check if it exists and size
Get-ChildItem "C:\Windows.old" -ErrorAction SilentlyContinue |
  Measure-Object -Property Length -Sum

# Remove via Disk Cleanup (safest method, Admin)
cleanmgr /d C:
# Select "Previous Windows installation(s)"

# Or via Settings > System > Storage > Temporary files
```

**Risk: Moderate** — removes ability to roll back to previous Windows version.
Typical size: 15-30 GB.

### Hibernation File

```powershell
# Check size
Get-Item "C:\hiberfil.sys" -Force -ErrorAction SilentlyContinue |
  Select-Object Length, @{N='SizeGB';E={[math]::Round($_.Length/1GB,1)}}

# Disable hibernation to remove hiberfil.sys (Admin)
powercfg /hibernate off
# This deletes hiberfil.sys immediately, freeing RAM-sized space

# Re-enable if needed
powercfg /hibernate on
```

**Size: Equal to your RAM** (8-64 GB). Risk: Low — you lose hibernate/Fast
Startup. Sleep still works.

### Prefetch

```powershell
# Prefetch files (Admin)
Remove-Item "C:\Windows\Prefetch\*" -Force -ErrorAction SilentlyContinue
```

**Risk: Safe** — Windows rebuilds these. Apps may launch slightly slower
on first run after cleaning.

## 3. Browser Caches

### Google Chrome

| Path | Risk | Typical Size |
|------|------|-------------|
| `$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache` | Safe | 0.5-3 GB |
| `$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Code Cache` | Safe | 0.1-0.5 GB |

```powershell
# Close Chrome first
Stop-Process -Name "chrome" -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Remove-Item "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Code Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### Microsoft Edge

| Path | Risk | Typical Size |
|------|------|-------------|
| `$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache` | Safe | 0.3-2 GB |

```powershell
Stop-Process -Name "msedge" -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Remove-Item "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### Firefox

| Path | Risk | Typical Size |
|------|------|-------------|
| `$env:LOCALAPPDATA\Mozilla\Firefox\Profiles\*\cache2` | Safe | 0.3-2 GB |

```powershell
Stop-Process -Name "firefox" -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Get-ChildItem "$env:LOCALAPPDATA\Mozilla\Firefox\Profiles" -Directory |
  ForEach-Object { Remove-Item "$($_.FullName)\cache2\*" -Recurse -Force -ErrorAction SilentlyContinue }
```

## 4. Developer Tool Caches

### Node.js / npm / yarn / pnpm

| Target | Path/Command | Risk | Typical Size |
|--------|-------------|------|-------------|
| npm cache | `npm cache clean --force` | Safe | 0.5-5 GB |
| npm cache dir | `$env:APPDATA\npm-cache` | Safe | 0.5-5 GB |
| yarn cache | `$env:LOCALAPPDATA\Yarn\Cache` | Safe | 0.5-5 GB |
| pnpm store | `pnpm store path` | Safe | 1-10 GB |
| Stale node_modules | scattered in projects | Moderate | 5-50 GB |

```powershell
# npm cache
npm cache clean --force 2>$null

# yarn
yarn cache clean 2>$null

# pnpm
pnpm store prune 2>$null

# Find stale node_modules (not modified in 30+ days)
Get-ChildItem -Path "$env:USERPROFILE\dev" -Filter "node_modules" -Directory -Recurse -Depth 4 -ErrorAction SilentlyContinue |
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
  ForEach-Object { "{0,10} {1}" -f ((Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB).ToString("N0") + " MB", $_.FullName }
```

### Python / pip

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| pip cache | `$env:LOCALAPPDATA\pip\Cache` | Safe | 0.5-3 GB |

```powershell
pip cache purge 2>$null
# Or manual
Remove-Item "$env:LOCALAPPDATA\pip\Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### Rust / Cargo

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Cargo registry cache | `$env:USERPROFILE\.cargo\registry\cache` | Safe | 1-5 GB |
| Cargo registry src | `$env:USERPROFILE\.cargo\registry\src` | Safe | 2-10 GB |
| Cargo git | `$env:USERPROFILE\.cargo\git\checkouts` | Safe | 0.5-5 GB |
| Rust target dirs | `*\target\` in projects | Moderate | 5-50 GB |

```powershell
# Clean cargo caches
Remove-Item "$env:USERPROFILE\.cargo\registry\cache\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:USERPROFILE\.cargo\registry\src\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:USERPROFILE\.cargo\git\checkouts\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### Go

```powershell
go clean -cache 2>$null
go clean -modcache 2>$null
```

### .NET / NuGet

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| NuGet cache | `$env:USERPROFILE\.nuget\packages` | Safe | 2-15 GB |
| NuGet HTTP cache | `$env:LOCALAPPDATA\NuGet\v3-cache` | Safe | 0.1-1 GB |

```powershell
# NuGet cache cleanup
dotnet nuget locals all --clear 2>$null

# Or manual
Remove-Item "$env:LOCALAPPDATA\NuGet\v3-cache\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### Visual Studio

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Component cache | `$env:LOCALAPPDATA\Microsoft\VisualStudio\Packages` | Moderate | 2-10 GB |
| MEF cache | `$env:LOCALAPPDATA\Microsoft\VisualStudio\<ver>\ComponentModelCache` | Safe | 0.1-0.5 GB |
| Web cache | `$env:LOCALAPPDATA\Microsoft\VisualStudio\<ver>\WebCache` | Safe | 0.1-1 GB |

### JetBrains IDEs

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Caches | `$env:LOCALAPPDATA\JetBrains\<Product>\caches` | Safe | 1-5 GB |
| Logs | `$env:LOCALAPPDATA\JetBrains\<Product>\log` | Safe | 0.1-0.5 GB |

```powershell
# Clean all JetBrains caches
Get-ChildItem "$env:LOCALAPPDATA\JetBrains" -Directory -ErrorAction SilentlyContinue |
  ForEach-Object {
    $caches = Join-Path $_.FullName "caches"
    if (Test-Path $caches) { Remove-Item "$caches\*" -Recurse -Force -ErrorAction SilentlyContinue }
  }
```

### VS Code

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Cache | `$env:APPDATA\Code\Cache` | Safe | 0.2-1 GB |
| CachedData | `$env:APPDATA\Code\CachedData` | Safe | 0.5-2 GB |
| CachedExtensions | `$env:APPDATA\Code\CachedExtensions` | Safe | 0.1-0.5 GB |
| Logs | `$env:APPDATA\Code\logs` | Safe | 0.05-0.2 GB |

### Gradle / Android Studio

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Gradle cache | `$env:USERPROFILE\.gradle\caches` | Safe | 2-10 GB |
| Gradle wrapper | `$env:USERPROFILE\.gradle\wrapper\dists` | Safe | 1-3 GB |
| AVD images | `$env:USERPROFILE\.android\avd` | Moderate | 5-30 GB |

```powershell
Remove-Item "$env:USERPROFILE\.gradle\caches\*" -Recurse -Force -ErrorAction SilentlyContinue
```

## 5. Docker Desktop (WSL2 Backend)

| Target | Description | Risk | Typical Size |
|--------|------------|------|-------------|
| Docker data | `ext4.vhdx` inside WSL2 | Moderate | 10-100 GB |

```powershell
# Check Docker disk usage
docker system df

# Prune stopped containers + dangling images
docker system prune -f

# Prune ALL unused images
docker system prune -a -f

# Nuclear: include volumes (DATA LOSS for databases!)
docker system prune -a --volumes -f

# The WSL2 ext4.vhdx doesn't auto-shrink after pruning.
# To reclaim host disk space (Admin):
wsl --shutdown
# Then compact the disk:
# Find the vhdx: usually at
# $env:LOCALAPPDATA\Docker\wsl\disk\docker_data.vhdx
# or $env:LOCALAPPDATA\Packages\...\ext4.vhdx
Optimize-VHD -Path "$env:LOCALAPPDATA\Docker\wsl\disk\docker_data.vhdx" -Mode Full
# If Optimize-VHD unavailable, use diskpart:
# select vdisk file="<path>"
# compact vdisk
```

## 6. WSL2 Disk Reclaim

WSL2 distributions use virtual disks that grow but don't auto-shrink.

```powershell
# List WSL distributions and their disk usage
wsl --list --verbose

# Shut down WSL
wsl --shutdown

# Find the VHDX file
Get-ChildItem "$env:LOCALAPPDATA\Packages\*WSL*" -Recurse -Filter "ext4.vhdx" -ErrorAction SilentlyContinue
Get-ChildItem "$env:LOCALAPPDATA\Packages\*Ubuntu*" -Recurse -Filter "ext4.vhdx" -ErrorAction SilentlyContinue

# Compact using diskpart (Admin)
# diskpart
# select vdisk file="<path_to_ext4.vhdx>"
# compact vdisk
# exit

# Or Optimize-VHD if Hyper-V tools installed (Admin)
Optimize-VHD -Path "<path>" -Mode Full
```

## 7. Package Manager Caches

### winget

```powershell
# winget doesn't have a cache clean command, but cache is at:
Remove-Item "$env:LOCALAPPDATA\Packages\Microsoft.DesktopAppInstaller_*\LocalState\DiagOutputDir\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### Chocolatey

```powershell
# Chocolatey cache
Remove-Item "$env:LOCALAPPDATA\Temp\chocolatey\*" -Recurse -Force -ErrorAction SilentlyContinue
# Or
choco cache remove 2>$null
```

### Scoop

```powershell
# Clean old versions of installed apps
scoop cleanup * 2>$null
# Clear download cache
scoop cache rm * 2>$null
```

## 8. Recycle Bin

```powershell
# Empty Recycle Bin
Clear-RecycleBin -Force -ErrorAction SilentlyContinue

# Check Recycle Bin size first
(New-Object -ComObject Shell.Application).Namespace(0xA).Items() |
  Measure-Object -Property Size -Sum |
  ForEach-Object { "{0:N2} GB" -f ($_.Sum / 1GB) }
```

## 9. Event Logs

```powershell
# Clear all event logs (Admin)
Get-WinEvent -ListLog * -ErrorAction SilentlyContinue |
  Where-Object { $_.RecordCount -gt 0 } |
  ForEach-Object { [System.Diagnostics.Eventing.Reader.EventLogSession]::GlobalSession.ClearLog($_.LogName) }

# Or clear specific logs (Admin)
wevtutil cl System
wevtutil cl Application
wevtutil cl Security
```

**Risk: Low** — logs are for troubleshooting. Clear only if not actively
debugging an issue.

## 10. Thumbnail Cache

```powershell
# Close Explorer first
Stop-Process -Name "explorer" -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Remove-Item "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\thumbcache_*.db" -Force -ErrorAction SilentlyContinue
Start-Process explorer
```

## Priority Order for Maximum Impact

1. **Windows.old** — 15-30 GB (if present after upgrade)
2. **Docker (WSL2 vhdx)** — 10-100 GB
3. **Stale node_modules** — 5-50 GB
4. **Rust target dirs** — 5-50 GB
5. **Hibernation file** — 8-64 GB (equals RAM)
6. **Windows Update cache + WinSxS cleanup** — 2-15 GB
7. **NuGet/Gradle/npm caches** — 5-25 GB combined
8. **User temp** — 0.5-10 GB
9. **Browser caches** — 1-5 GB
10. **Recycle Bin** — 0-50 GB
11. **Event logs** — 0.1-1 GB
