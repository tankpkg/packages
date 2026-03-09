---
name: "@tank/windows-cleanup"
description: |
  Windows 10/11 disk space recovery and system cleanup for developers.
  Analyzes disk usage, identifies space hogs (temp files, Windows Update
  cache, WinSxS, browser caches, dev tool artifacts, stale node_modules,
  Docker WSL2 images, NuGet/Gradle/npm/pip/Cargo caches, hibernation file,
  Recycle Bin), and safely reclaims storage with risk-aware PowerShell
  workflows. Includes an analysis script that produces a prioritized report.
  Companion to @tank/macos-cleanup for Windows users.

  Trigger phrases: "disk cleanup", "free disk space", "clean up windows",
  "disk full", "running out of space", "clear cache", "clean storage",
  "ccleaner", "windows cleanup", "temp files", "cleanmgr", "Storage Sense",
  "WinSxS", "Windows Update cache", "node_modules cleanup",
  "docker disk space", "WSL disk", "npm cache", "pip cache", "cargo clean",
  "NuGet cache", "reclaim space", "hiberfil.sys", "Windows.old",
  "Recycle Bin", "system data large", "purge caches", "clean dev tools"
---

# Windows Disk Cleanup

Recover disk space on Windows 10/11 by cleaning temp files, caches, dev
tool artifacts, stale dependencies, and other reclaimable storage.
Developer-focused — knows where the real space hogs hide on a dev machine.

## Core Philosophy

1. **Analyze before deleting.** Always scan first with the analysis script.
2. **Risk-aware cleanup.** Categorize by risk (safe/low/moderate/high).
   Clean safe items freely, confirm everything else.
3. **Use built-in tools when possible.** `cleanmgr`, `DISM`, `Storage Sense`,
   `dotnet nuget locals`, `npm cache clean` over raw `Remove-Item`.
4. **PowerShell everything.** All commands are PowerShell. Indicate which
   need elevation (Run as Administrator).
5. **Never touch user data.** Documents, Desktop, Pictures, credentials,
   SSH keys, registry — hands off.

## Quick-Start

### "My disk is full, help me clean up"

| Step | Action |
|------|--------|
| 1 | Run `.\scripts\analyze-disk.ps1` to scan all targets |
| 2 | Review report — prioritize by size and risk |
| 3 | Clean safe targets first (caches, temp files, logs) |
| 4 | Present moderate targets for user confirmation |
| 5 | Mention high-risk targets only if asked |
| 6 | Show before/after disk space comparison |

### "Clean everything safe"

```powershell
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue  # Admin
Remove-Item "C:\Windows\Prefetch\*" -Force -ErrorAction SilentlyContinue       # Admin
npm cache clean --force 2>$null
pip cache purge 2>$null
dotnet nuget locals all --clear 2>$null
```

## Cleanup Priority Order

| Priority | Target | Typical Savings | Risk |
|----------|--------|----------------|------|
| 1 | Windows.old | 15-30 GB | Moderate |
| 2 | Docker WSL2 vhdx | 10-100 GB | Moderate |
| 3 | Hibernation file | 8-64 GB (=RAM) | Low |
| 4 | Stale node_modules | 5-50 GB | Moderate |
| 5 | Rust target dirs | 5-50 GB | Moderate |
| 6 | Windows Update + WinSxS | 2-15 GB | Safe |
| 7 | NuGet/Gradle/npm caches | 5-25 GB | Safe |
| 8 | User & system temp | 1-15 GB | Safe |
| 9 | Browser caches | 1-5 GB | Safe |
| 10 | Recycle Bin | 0-50 GB | Moderate |

## Decision Trees

### What to Clean Based on Request

| User Says | Action |
|-----------|--------|
| "Clean up my PC" | Full scan, report, clean safe, confirm moderate |
| "Clean caches" | Temp files, browser caches, dev tool caches |
| "Clean dev tools" | npm/pip/NuGet/cargo/gradle caches only |
| "What's using space?" | Analysis only, no cleanup |
| "Clean Docker" | `docker system prune -a` + compact WSL2 vhdx |
| "Free up X GB" | Prioritized cleanup until target reached |

### WinSxS Cleanup

Never manually delete from WinSxS. Use DISM only:
```powershell
DISM /Online /Cleanup-Image /StartComponentCleanup  # Admin
```

### Docker WSL2 Disk

Docker's WSL2 virtual disk doesn't auto-shrink. After `docker system prune`:
```powershell
wsl --shutdown
Optimize-VHD -Path "$env:LOCALAPPDATA\Docker\wsl\disk\docker_data.vhdx" -Mode Full  # Admin
```

## Safety Rules

Never touch:
- User profile folders (Documents, Desktop, Pictures, etc.)
- `C:\Windows\Installer` (breaks app repair/uninstall)
- `C:\Windows\WinSxS` directly (use DISM only)
- `$env:USERPROFILE\.ssh`, `.gnupg`, `.aws`, `.kube` (credentials)
- `C:\Windows\System32`, `C:\Windows\SysWOW64`
- Registry hives, `.git` directories, database files

See `references/safety-protocols.md` for full safety rules.

## Reference Files

| File | Contents |
|------|----------|
| `references/cleanup-targets.md` | Exhaustive cleanup targets with paths, PowerShell commands, risk levels, typical sizes |
| `references/safety-protocols.md` | Golden rules, confirmation flows, never-touch paths, recovery procedures |
| `references/space-analysis.md` | Disk analysis techniques, finding large files/dirs, stale node_modules, recommended tools |

## Scripts

| Script | Usage |
|--------|-------|
| `scripts/analyze-disk.ps1` | Scans all targets, reports sizes and risk. Flags: `-Json`, `-DevOnly`, `-Quick` |
