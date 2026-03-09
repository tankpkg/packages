# Safety Protocols

Rules and workflows for safely cleaning a macOS system without causing
data loss, broken apps, or system instability.

## Golden Rules

1. **Analyze before deleting.** Always run the analysis script first to show
   what will be cleaned and how much space will be freed. Never jump straight
   to deletion.

2. **Dry-run by default.** Every cleanup operation should first show what
   WOULD be deleted, with sizes. Only proceed after user confirmation.

3. **Never touch these without explicit user consent:**
   - `~/Documents`, `~/Desktop`, `~/Pictures`, `~/Music`, `~/Movies`
   - `~/Library/Keychains/` (passwords and certificates)
   - `~/Library/Application Support/` (app data — not cache)
   - `/System/` (SIP-protected, impossible anyway)
   - `~/.ssh/`, `~/.gnupg/`, `~/.aws/`, `~/.kube/` (credentials)
   - Any database files (.db, .sqlite) in app support directories
   - Git repositories (.git directories)

4. **Respect SIP.** System Integrity Protection blocks writes to system
   directories. Never try to `sudo rm` anything under `/System/`.

5. **Categorize by risk.** Group operations by risk level and present them
   separately. Clean safe items first, warn for moderate, require explicit
   opt-in for high-risk.

## Confirmation Flow

### For Safe Operations (risk: safe)

Show summary and proceed:
```
Cache cleanup will free ~4.2 GB:
  ~/Library/Caches/             3.8 GB  (app caches, auto-regenerate)
  ~/Library/Logs/               0.4 GB  (old logs)

Proceed? [Y/n]
```

### For Moderate Operations (risk: moderate)

Show detailed breakdown with explanation:
```
The following require re-download or rebuild:
  Xcode DerivedData               12.3 GB  (rebuild on next Xcode build)
  3 stale node_modules dirs        4.1 GB  (run npm install to restore)
    ~/dev/old-project/node_modules  (last modified 89 days ago)
    ~/dev/archived/node_modules     (last modified 142 days ago)
    ~/dev/test-app/node_modules     (last modified 67 days ago)

Clean these? [y/N]
```

### For High-Risk Operations (risk: high)

Require explicit acknowledgment:
```
WARNING: The following operations may cause DATA LOSS:

  iOS device backups              28.4 GB
    iPhone backup from 2024-03-15  14.2 GB
    iPhone backup from 2023-11-20  14.2 GB

  Docker volumes                   5.2 GB
    postgres_data                  3.1 GB
    redis_data                     2.1 GB

These cannot be recovered after deletion.
Type 'DELETE' to confirm, or press Enter to skip:
```

## What NOT to Clean

These paths should NEVER be touched by the cleanup agent:

| Path | Reason |
|------|--------|
| `~/Library/Keychains/` | Passwords, certificates, identity |
| `~/Library/Accounts/` | System account credentials |
| `~/.ssh/` | SSH keys — irrecoverable if lost |
| `~/.gnupg/` | GPG keys — irrecoverable if lost |
| `~/.aws/`, `~/.kube/`, `~/.config/gcloud/` | Cloud credentials |
| `~/Library/Application Support/MobileSync/` | Only with HIGH-risk consent |
| `/System/` | SIP-protected |
| `/usr/` | System binaries |
| `/bin/`, `/sbin/` | Core system tools |
| `~/Library/Mail/` | Email data (not same as downloads) |
| Any `.git/` directory | Version control history |
| `*.keychain-db` | Keychain databases |
| `~/.local/share/opencode/` | AI agent session data |

## Pre-Cleanup Checklist

Before running any cleanup:

1. **Check available space first**: `df -h /` — if user has 50+ GB free,
   aggressive cleanup may not be needed
2. **Ensure no builds running**: Cleaning DerivedData during a build will
   cause build failure
3. **Check Docker containers**: Don't prune images that running containers
   depend on
4. **Verify Xcode is closed**: DerivedData cleanup works best with Xcode closed
5. **Note Time Machine status**: If TM is running, cleanup will free space
   on the next snapshot, not immediately

## Recovery Procedures

If something goes wrong:

| Problem | Recovery |
|---------|----------|
| App won't launch after cache clean | Restart the app — it rebuilds cache on launch |
| Xcode build fails after DerivedData clean | Clean build (Cmd+Shift+K), then rebuild |
| Docker images missing | `docker pull <image>` to re-download |
| npm packages missing | `cd <project> && npm install` |
| Brew app broken | `brew reinstall <package>` |
| Simulator missing | `xcode-select --install` or re-download via Xcode |
| Python packages missing | `pip install -r requirements.txt` in the project |
| Login items broken | Re-add from System Settings > General > Login Items |

## Space Verification

After cleanup, always verify space was actually freed:

```bash
# Check disk space
df -h /

# If space wasn't freed, check Time Machine local snapshots
tmutil listlocalsnapshots /

# Delete old TM snapshots if needed (requires sudo)
sudo tmutil deletelocalsnapshots <date>
```

Time Machine snapshots are the most common reason "deleted files don't free
space." The snapshot still references the data. Snapshots auto-expire, but
if immediate space is needed, they can be manually deleted.

## Purgeable Space

macOS has a concept of "purgeable" space — storage that macOS will
automatically free when needed (iCloud-optimized files, old Time Machine
snapshots). The `df -h` output may differ from Finder's reported free space
because Finder includes purgeable space as "available."

```bash
# Accurate space reading including purgeable
diskutil info / | grep -E "(Free|Available|Purgeable)"
```

## Agent Behavior Rules

When the agent is performing cleanup:

1. **Always show a summary first** — total space that could be freed,
   broken down by category and risk level
2. **Ask permission per risk level** — don't batch safe and high-risk
   items together
3. **Show progress** — for large operations (like finding node_modules),
   show what's being scanned
4. **Report results** — after cleanup, show before/after space comparison
5. **Suggest follow-ups** — if Docker or Xcode aren't cleaned because
   they're high-impact, mention it
6. **Don't touch what wasn't asked** — if user says "clean caches," don't
   also clean Docker volumes
7. **Prefer targeted over nuclear** — `brew cleanup` over `rm -rf $(brew --cache)`
8. **Use built-in cleanup commands** when available — `brew cleanup`, `npm cache
   clean`, `xcrun simctl delete unavailable` over raw `rm -rf`
