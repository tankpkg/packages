---
name: "@tank/macos-cleanup"
description: |
  macOS disk space recovery and system cleanup — a developer-focused
  replacement for CCleaner. Analyzes disk usage, identifies space hogs
  (caches, dev tool artifacts, stale dependencies, logs, Docker images),
  and safely reclaims storage with risk-aware confirmation workflows.
  Covers Xcode DerivedData/simulators, Homebrew, npm/yarn/pnpm/Bun caches,
  pip/conda, Cargo/Rust targets, Go modules, Gradle, Docker (images +
  build cache + VM disk), CocoaPods, JetBrains caches, VS Code caches,
  browser caches, iOS backups, Time Machine snapshots, stale node_modules,
  system logs, and large file discovery. Includes an analysis script that
  scans all known targets and produces a prioritized cleanup report.

  Trigger phrases: "disk cleanup", "free disk space", "clean up my mac",
  "disk full", "running out of space", "storage full", "clear cache",
  "clear caches", "delete caches", "clean caches", "clean storage",
  "system cleanup", "mac cleanup", "ccleaner", "free up space",
  "disk usage", "what's using space", "large files", "space hog",
  "node_modules cleanup", "clean node_modules", "clean docker",
  "docker disk space", "docker prune", "xcode cleanup", "DerivedData",
  "brew cleanup", "npm cache", "pip cache", "cargo clean",
  "clean dev tools", "reclaim space", "storage management",
  "system data large", "other storage", "purge caches",
  "Time Machine snapshots", "iOS backups", "stale dependencies"
---

# macOS Disk Cleanup

Recover disk space on macOS by cleaning caches, dev tool artifacts, stale
dependencies, logs, and other reclaimable storage. Developer-focused — knows
where the real space hogs hide on a dev machine.

## Core Philosophy

1. **Analyze before deleting.** Always scan first. Show the user what's
   consuming space and how much can be reclaimed before touching anything.
2. **Risk-aware cleanup.** Categorize targets by risk (safe → low →
   moderate → high). Clean safe items freely, require confirmation for
   everything else.
3. **Use built-in cleanup commands.** Prefer `brew cleanup`, `npm cache clean`,
   `xcrun simctl delete unavailable` over raw `rm -rf`. Tools know their own
   cleanup semantics better than we do.
4. **Never touch user data.** Documents, Desktop, Pictures, credentials,
   SSH keys, keychains, git repos — hands off. Always.
5. **Report results.** After cleanup, show before/after disk space comparison.

## Quick-Start

### "My disk is full, help me clean up"

| Step | Action |
|------|--------|
| 1 | Run `scripts/analyze-disk.sh` to scan all targets |
| 2 | Review report — prioritize by size and risk |
| 3 | Clean safe targets first (caches, logs, DerivedData) |
| 4 | Present moderate targets for user confirmation |
| 5 | Only mention high-risk targets if user asks |
| 6 | Show before/after disk space comparison |

### "Clean everything safe"

Execute safe-tier cleanup in order:
1. User caches (`rm -rf ~/Library/Caches/*`)
2. User logs (`rm -rf ~/Library/Logs/*`)
3. Xcode DerivedData (`rm -rf ~/Library/Developer/Xcode/DerivedData/*`)
4. Simulator caches (`rm -rf ~/Library/Developer/CoreSimulator/Caches/*`)
5. Homebrew (`brew cleanup --prune=all && brew autoremove`)
6. npm/yarn/pip caches (`npm cache clean --force`, etc.)
7. Diagnostic reports
8. Saved Application State

### "What's using all my space?"

Run analysis only — no cleanup:
```bash
bash scripts/analyze-disk.sh
```

Or for machine-readable output:
```bash
bash scripts/analyze-disk.sh --json
```

## Cleanup Priority Order

Targets ordered by typical space savings (highest ROI first):

| Priority | Target | Typical Savings | Risk |
|----------|--------|----------------|------|
| 1 | Xcode DerivedData + simulators | 10-80 GB | Safe |
| 2 | Docker images + build cache | 10-80 GB | Moderate |
| 3 | Stale node_modules | 5-50 GB | Moderate |
| 4 | Rust target/ directories | 5-50 GB | Moderate |
| 5 | User caches (all apps) | 2-20 GB | Safe |
| 6 | Homebrew cleanup | 1-8 GB | Safe |
| 7 | Package manager caches | 3-15 GB | Safe |
| 8 | Gradle/Maven caches | 3-13 GB | Safe |
| 9 | iOS Device Support (old) | 2-30 GB | Low |
| 10 | Trash | 0-50 GB | Moderate |
| 11 | Logs & diagnostic reports | 0.5-5 GB | Safe |
| 12 | iOS device backups | 5-100 GB | High |

## Decision Trees

### What to Clean Based on User Request

| User Says | Action |
|-----------|--------|
| "Clean up my Mac" | Full scan → report → clean safe → confirm moderate |
| "Clean caches" | User + system caches, browser caches, dev tool caches |
| "Clean dev tools" | npm/pip/cargo/brew/xcode/docker/gradle caches only |
| "What's using space?" | Analysis only, no cleanup |
| "Clean Docker" | `docker system prune -a` (confirm first) |
| "Clean Xcode" | DerivedData + simulators + old device support |
| "Free up X GB" | Prioritized cleanup until target is reached |
| "Clean everything" | Full cleanup including moderate-risk targets |

### Docker Cleanup Levels

| Level | Command | Cleans | Risk |
|-------|---------|--------|------|
| Light | `docker container prune && docker image prune` | Stopped containers + dangling images | Low |
| Medium | `docker system prune -a` | All unused images + containers + networks | Moderate |
| Heavy | `docker system prune -a --volumes` | Everything + volumes (data loss!) | High |

Note: Docker Desktop's VM disk (`Docker.raw`) doesn't shrink after cleanup.
To reclaim host disk space: Docker Desktop → Settings → Resources → reduce
disk limit, or Troubleshoot → Clean/Purge Data.

### Time Machine Local Snapshots

If disk space wasn't freed after deletion, local TM snapshots may be holding
references:
```bash
tmutil listlocalsnapshots /
sudo tmutil deletelocalsnapshots <date>
```

## Safety Rules

Never touch these paths:
- `~/Documents`, `~/Desktop`, `~/Pictures`, `~/Music`, `~/Movies`
- `~/Library/Keychains/`, `~/Library/Accounts/`
- `~/.ssh/`, `~/.gnupg/`, `~/.aws/`, `~/.kube/`, `~/.config/gcloud/`
- `/System/`, `/usr/`, `/bin/`, `/sbin/`
- `~/.cargo/bin/` (installed Rust binaries, not cache)
- Any `.git/` directory
- `~/Library/Mail/` (use Mail.app for mail cleanup)
- iCloud files (use `brctl evict` or Finder, never `rm`)

See `references/safety-protocols.md` for detailed safety rules and
confirmation flow patterns.

## After Cleanup

Always verify space was freed:
```bash
df -h /
diskutil info / | grep -E "(Free|Available|Purgeable)"
```

If space wasn't freed, check Time Machine local snapshots (see above).

## Reference Files

| File | Contents |
|------|----------|
| `references/cleanup-targets.md` | Exhaustive list of cleanup targets with exact paths, commands, risk levels, and typical space savings for each category |
| `references/safety-protocols.md` | Golden rules, confirmation flow patterns per risk level, paths to never touch, pre-cleanup checklist, recovery procedures |
| `references/space-analysis.md` | Disk usage analysis techniques, scan/report/clean workflow, finding large files, stale node_modules/Rust targets, Docker analysis, recommended CLI tools |

## Scripts

| Script | Usage |
|--------|-------|
| `scripts/analyze-disk.sh` | Scans all known cleanup targets, reports sizes and risk levels. Flags: `--json` (JSON output), `--dev-only` (dev caches only), `--quick` (skip slow scans) |
