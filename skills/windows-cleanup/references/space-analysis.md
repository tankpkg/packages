# Space Analysis Techniques (Windows)

How to find where disk space is consumed on Windows, identify biggest
offenders, and present actionable recommendations. All commands are
PowerShell.

## Quick Disk Overview

```powershell
# Drive summary
Get-PSDrive -PSProvider FileSystem | Select-Object Name,
  @{N='UsedGB';E={[math]::Round($_.Used/1GB,1)}},
  @{N='FreeGB';E={[math]::Round($_.Free/1GB,1)}},
  @{N='TotalGB';E={[math]::Round(($_.Used+$_.Free)/1GB,1)}},
  @{N='PctUsed';E={[math]::Round($_.Used/($_.Used+$_.Free)*100,1)}}

# Just C: drive
$c = Get-PSDrive C
"{0:N1} GB free of {1:N1} GB ({2:N1}% used)" -f ($c.Free/1GB), (($c.Used+$c.Free)/1GB), ($c.Used/($c.Used+$c.Free)*100)
```

## The Scan, Report, Clean Workflow

### Step 1: Scan

Run the analysis script to discover all cleanup targets:

```powershell
# The analyze-disk.ps1 script automates this
.\scripts\analyze-disk.ps1

# Manual equivalent — scan key locations
"User Temp: " + "{0:N2} GB" -f ((Get-ChildItem $env:TEMP -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1GB)
"Windows Temp: " + "{0:N2} GB" -f ((Get-ChildItem "C:\Windows\Temp" -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1GB)
```

### Step 2: Report

Present as categorized summary — same format as macOS cleanup skill.

### Step 3: Clean

Execute in risk-level order: safe first, then moderate with confirmation,
high-risk only if specifically asked.

## Finding Large Files

```powershell
# Files larger than 500 MB in user profile
Get-ChildItem $env:USERPROFILE -Recurse -File -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -gt 500MB } |
  Sort-Object Length -Descending |
  Select-Object @{N='SizeGB';E={[math]::Round($_.Length/1GB,2)}}, FullName |
  Format-Table -AutoSize

# Files larger than 1 GB anywhere on C:
Get-ChildItem C:\ -Recurse -File -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -gt 1GB } |
  Sort-Object Length -Descending |
  Select-Object @{N='SizeGB';E={[math]::Round($_.Length/1GB,2)}}, FullName |
  Format-Table -AutoSize
```

## Finding Large Directories

```powershell
# Top-level user profile directories by size
Get-ChildItem $env:USERPROFILE -Directory -Force -ErrorAction SilentlyContinue |
  ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -File -Force -ErrorAction SilentlyContinue |
      Measure-Object -Property Length -Sum).Sum
    [PSCustomObject]@{ SizeGB = [math]::Round($size/1GB,2); Path = $_.FullName }
  } | Sort-Object SizeGB -Descending | Format-Table -AutoSize
```

## Finding Stale node_modules

```powershell
# Find node_modules not modified in 30+ days
$devDirs = @("$env:USERPROFILE\dev", "$env:USERPROFILE\projects",
             "$env:USERPROFILE\code", "$env:USERPROFILE\source\repos")

foreach ($dir in $devDirs) {
  if (Test-Path $dir) {
    Get-ChildItem $dir -Filter "node_modules" -Directory -Recurse -Depth 4 -ErrorAction SilentlyContinue |
      Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
      ForEach-Object {
        $size = (Get-ChildItem $_.FullName -Recurse -File -Force -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum).Sum
        [PSCustomObject]@{
          SizeMB = [math]::Round($size/1MB,0)
          LastModified = $_.LastWriteTime.ToString("yyyy-MM-dd")
          Path = (Split-Path $_.FullName -Parent)
        }
      } | Sort-Object SizeMB -Descending
  }
}
```

## Docker Space Analysis

```powershell
# Docker's own report
docker system df -v

# WSL2 virtual disk size (the real space consumer)
Get-ChildItem "$env:LOCALAPPDATA\Docker\wsl" -Recurse -Filter "*.vhdx" -ErrorAction SilentlyContinue |
  Select-Object @{N='SizeGB';E={[math]::Round($_.Length/1GB,2)}}, FullName
```

## Recommended CLI Tools

| Tool | Install | Description |
|------|---------|-------------|
| WizTree | `winget install AntibodySoftware.WizTree` | Fastest disk analyzer (reads MFT directly) |
| TreeSize Free | `winget install JAMSoftware.TreeSize.Free` | Visual tree view, context menu integration |
| WinDirStat | `winget install WinDirStat.WinDirStat` | Classic treemap visualization |
| SpaceSniffer | manual | Portable, real-time treemap |

The agent should use PowerShell commands directly rather than depending on
these tools being installed. Suggest them for interactive exploration.

## Windows Storage Settings

Windows has a built-in storage breakdown:

```
Settings > System > Storage
```

This shows: Apps & features, Temporary files, Other, System & reserved.
"Temporary files" includes many cleanable items and lets users delete
from the GUI.
