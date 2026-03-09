# Windows Safety Protocols

Rules and workflows for safely cleaning a Windows 10/11 system.

## Golden Rules

1. **Analyze before deleting.** Always scan first. Show what will be cleaned
   and how much space will be freed before touching anything.
2. **Dry-run by default.** Show what WOULD be deleted with sizes. Only
   proceed after user confirmation.
3. **Never touch these without explicit user consent:**
   - User profile folders: Documents, Desktop, Pictures, Music, Videos
   - `C:\Windows\Installer` — MSI repair data (breaks uninstall/repair)
   - `$env:USERPROFILE\.ssh`, `.gnupg`, `.aws`, `.kube` — credentials
   - Registry hives directly
   - `C:\Windows\System32` or `C:\Windows\SysWOW64`
   - Any database files (.mdf, .ldf, .sqlite) in app directories
   - Git repositories (.git directories)
   - WSL2 root filesystems
4. **Use built-in tools when available.** `cleanmgr`, `DISM`, `Storage Sense`,
   `dotnet nuget locals`, `npm cache clean` know their own cleanup semantics.
5. **Admin operations need elevation.** Clearly indicate which commands
   require "Run as Administrator."

## Confirmation Flow

### Safe Operations

```
Cache cleanup will free ~3.8 GB:
  User temp files                    1.2 GB  (auto-regenerated)
  Browser caches                     1.4 GB  (re-downloaded on visit)
  npm cache                          1.2 GB  (re-downloaded on install)

Proceed? [Y/n]
```

### Moderate Operations

```
The following require re-download or rebuild:
  3 stale node_modules dirs          4.1 GB  (run npm install to restore)
    C:\dev\old-project\node_modules  (last modified 89 days ago)
    C:\dev\archived\node_modules     (last modified 142 days ago)
  Hibernation file (hiberfil.sys)    16.0 GB (lose hibernate, keep sleep)

Clean these? [y/N]
```

### High-Risk Operations

```
WARNING: The following operations may cause DATA LOSS:

  Docker volumes                     5.2 GB
    postgres_data                    3.1 GB
    redis_data                       2.1 GB

These cannot be recovered after deletion.
Type 'DELETE' to confirm, or press Enter to skip:
```

## Paths to NEVER Touch

| Path | Reason |
|------|--------|
| `C:\Windows\Installer` | MSI repair/uninstall metadata |
| `C:\Windows\System32` | Core OS binaries |
| `C:\Windows\WinSxS` (directly) | Use DISM only, never manual deletion |
| `$env:USERPROFILE\.ssh` | SSH keys |
| `$env:USERPROFILE\.gnupg` | GPG keys |
| `$env:USERPROFILE\.aws`, `.kube`, `.azure` | Cloud credentials |
| `C:\ProgramData` (broadly) | App data, databases |
| User profile folders | Documents, Desktop, Pictures, etc. |
| `.git` directories | Version control history |
| Registry hives | System configuration |
| EFI System Partition | Boot configuration |

## Pre-Cleanup Checklist

1. **Check available space**: `Get-PSDrive C | Select Used,Free`
2. **Close applications** whose caches you're cleaning
3. **Check running Docker containers**: `docker ps`
4. **Note if Windows Update is running**: check Task Manager
5. **Ensure no builds in progress** (Visual Studio, Gradle, Cargo)

## Recovery Procedures

| Problem | Recovery |
|---------|----------|
| App won't launch after cache clean | Restart app — rebuilds cache |
| npm packages missing | `cd <project>; npm install` |
| NuGet restore failed | `dotnet restore` in project |
| Docker images gone | `docker pull <image>` |
| Windows Update broken after cache clean | `sfc /scannow` then retry update |
| Hibernate not working | `powercfg /hibernate on` (Admin) |
| Thumbnails not showing | They regenerate automatically |
| Gradle build fails | `gradle build` re-downloads |

## Space Verification

```powershell
# Check free space
Get-PSDrive C | Select-Object @{N='FreeGB';E={[math]::Round($_.Free/1GB,1)}},
  @{N='UsedGB';E={[math]::Round($_.Used/1GB,1)}},
  @{N='TotalGB';E={[math]::Round(($_.Used+$_.Free)/1GB,1)}}

# Percentage used
$drive = Get-PSDrive C
$pct = [math]::Round(($drive.Used / ($drive.Used + $drive.Free)) * 100, 1)
Write-Host "$pct% used"
```

## Agent Behavior Rules

1. **Always show summary first** — total reclaimable by category and risk
2. **Ask permission per risk level** — don't batch safe and high-risk
3. **Indicate Admin requirements** — mark which commands need elevation
4. **Report before/after** — show disk space comparison after cleanup
5. **Don't touch what wasn't asked** — "clean caches" doesn't mean "prune Docker volumes"
6. **Prefer built-in tools** — `cleanmgr`, `DISM`, `dotnet nuget locals` over raw `Remove-Item`
7. **PowerShell over CMD** — use PowerShell for all operations
