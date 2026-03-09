# macOS Cleanup Targets

Exhaustive reference of what can be safely cleaned on macOS, organized by
category. Each target includes exact paths, commands, typical space savings,
and risk level.

## Risk Levels

| Level | Meaning | Action |
|-------|---------|--------|
| Safe | Regenerated automatically, no data loss | Clean without asking |
| Low | Unlikely to cause issues, minor convenience loss | List and confirm |
| Moderate | May require re-login, re-download, or rebuild | Warn and confirm |
| High | Potential data loss if user hasn't backed up | Explain risk, require explicit opt-in |

## 1. System & User Caches

Caches are the single biggest space waster on macOS. They regenerate
automatically — cleaning them is always safe, just slow (apps rebuild on next
launch).

### User-Level Caches

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| User cache root | `~/Library/Caches/*` | Safe | 2-20 GB |
| Specific app cache | `~/Library/Caches/com.app.name/` | Safe | varies |
| Safari cache | `~/Library/Caches/com.apple.Safari/` | Safe | 0.5-3 GB |
| Chrome cache | `~/Library/Caches/Google/Chrome/` | Safe | 0.5-5 GB |
| Arc cache | `~/Library/Caches/company.thebrowser.Browser/` | Safe | 0.5-3 GB |
| Firefox cache | `~/Library/Caches/Firefox/Profiles/*/cache2/` | Safe | 0.5-2 GB |
| Slack cache | `~/Library/Caches/com.tinyspeck.slackmacgap/` | Safe | 0.2-2 GB |
| Discord cache | `~/Library/Caches/com.hnc.Discord/` | Safe | 0.1-1 GB |
| Spotify cache | `~/Library/Caches/com.spotify.client/` | Safe | 0.5-5 GB |
| VS Code cache | `~/Library/Caches/com.microsoft.VSCode/` | Safe | 0.1-1 GB |

```bash
# Show total user cache size
du -sh ~/Library/Caches 2>/dev/null

# Clean all user caches (safe — apps rebuild them)
rm -rf ~/Library/Caches/*

# Clean specific app cache
rm -rf ~/Library/Caches/com.apple.Safari/
```

### System-Level Caches

| Target | Path | Risk | Notes |
|--------|------|------|-------|
| System cache | `/Library/Caches/*` | Low | Requires sudo, system rebuilds |
| Font caches | `/System/Library/Caches/com.apple.FontRegistry/` | Low | SIP-protected on modern macOS |

```bash
# Show system cache size (requires sudo for accurate count)
sudo du -sh /Library/Caches 2>/dev/null
```

## 2. Developer Tool Caches

These are typically the largest space consumers on developer machines.

### Xcode

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| DerivedData | `~/Library/Developer/Xcode/DerivedData/` | Safe | 5-50 GB |
| Archives | `~/Library/Developer/Xcode/Archives/` | Moderate | 2-20 GB |
| iOS DeviceSupport | `~/Library/Developer/Xcode/iOS DeviceSupport/` | Low | 2-30 GB |
| watchOS DeviceSupport | `~/Library/Developer/Xcode/watchOS DeviceSupport/` | Low | 1-5 GB |
| Old simulators | via `xcrun simctl` | Low | 5-30 GB |
| CoreSimulator caches | `~/Library/Developer/CoreSimulator/Caches/` | Safe | 1-10 GB |
| CoreSimulator devices | `~/Library/Developer/CoreSimulator/Devices/` | Moderate | 5-40 GB |
| Previews cache | `~/Library/Developer/Xcode/UserData/Previews/` | Safe | 1-5 GB |

```bash
# DerivedData — always safe to nuke
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# Old simulator runtimes
xcrun simctl delete unavailable 2>/dev/null

# Old iOS device support (keep latest 2 versions)
ls -dt ~/Library/Developer/Xcode/iOS\ DeviceSupport/*/ 2>/dev/null | tail -n +3 | xargs rm -rf

# Archives — user should review first (contains .ipa submissions)
du -sh ~/Library/Developer/Xcode/Archives/ 2>/dev/null
```

### Homebrew

| Target | Command | Risk | Typical Size |
|--------|---------|------|-------------|
| Old versions | `brew cleanup` | Safe | 0.5-5 GB |
| Download cache | `brew cleanup -s` | Safe | 0.5-3 GB |
| All caches | `brew cleanup --prune=all` | Safe | 1-8 GB |
| Autoremove unused | `brew autoremove` | Low | varies |

```bash
brew cleanup --prune=all -s 2>/dev/null
brew autoremove 2>/dev/null
```

### Node.js / JavaScript

| Target | Path/Command | Risk | Typical Size |
|--------|-------------|------|-------------|
| npm cache | `npm cache clean --force` | Safe | 0.5-5 GB |
| yarn cache | `yarn cache clean` | Safe | 0.5-5 GB |
| pnpm store | `pnpm store prune` | Safe | 1-10 GB |
| Stale node_modules | `find ~ -name node_modules -type d` | Moderate | 5-50 GB |
| .npm cache dir | `~/.npm/_cacache/` | Safe | 0.5-3 GB |
| Bun cache | `~/.bun/install/cache/` | Safe | 0.5-3 GB |

```bash
# npm
npm cache clean --force 2>/dev/null

# yarn (classic + berry)
yarn cache clean 2>/dev/null

# pnpm
pnpm store prune 2>/dev/null

# Find stale node_modules (not modified in 30+ days)
find ~/dev -name node_modules -type d -maxdepth 4 -mtime +30 2>/dev/null

# Bun cache
rm -rf ~/.bun/install/cache/ 2>/dev/null
```

### Python

| Target | Path/Command | Risk | Typical Size |
|--------|-------------|------|-------------|
| pip cache | `pip cache purge` | Safe | 0.5-3 GB |
| pip cache dir | `~/Library/Caches/pip/` | Safe | 0.5-3 GB |
| pyenv versions | `~/.pyenv/versions/` | Moderate | 1-5 GB |
| __pycache__ dirs | scattered | Safe | varies |
| .venv directories | scattered | Moderate | 1-10 GB |
| conda pkgs | `~/miniconda3/pkgs/` or `~/anaconda3/pkgs/` | Safe | 2-10 GB |

```bash
pip cache purge 2>/dev/null
pip3 cache purge 2>/dev/null
conda clean --all -y 2>/dev/null
```

### Rust

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Cargo registry | `~/.cargo/registry/` | Safe | 1-5 GB |
| Cargo git | `~/.cargo/git/` | Safe | 0.5-2 GB |
| Target dirs | `*/target/` | Moderate | 5-50 GB |

```bash
# Cargo cache cleanup (install cargo-cache first)
cargo cache --autoclean 2>/dev/null
# Or manual
rm -rf ~/.cargo/registry/cache/ 2>/dev/null
```

### Go

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Module cache | `~/go/pkg/mod/` | Safe | 1-5 GB |
| Build cache | via `go clean -cache` | Safe | 0.5-3 GB |

```bash
go clean -cache 2>/dev/null
go clean -modcache 2>/dev/null
```

### Docker

| Target | Command | Risk | Typical Size |
|--------|---------|------|-------------|
| Stopped containers | `docker container prune` | Low | 0.1-1 GB |
| Dangling images | `docker image prune` | Low | 1-10 GB |
| All unused images | `docker image prune -a` | Moderate | 5-50 GB |
| Build cache | `docker builder prune` | Low | 2-20 GB |
| Volumes | `docker volume prune` | High | 1-20 GB |
| Full system prune | `docker system prune -a --volumes` | High | 10-80 GB |
| Docker Desktop VM | `~/Library/Containers/com.docker.docker/Data/vms/` | Moderate | 5-60 GB |

```bash
# Safe: remove stopped containers and dangling images
docker container prune -f 2>/dev/null
docker image prune -f 2>/dev/null
docker builder prune -f 2>/dev/null

# Aggressive: remove everything unused (will re-pull images)
docker system prune -a -f 2>/dev/null

# Nuclear: include volumes (DATA LOSS risk)
docker system prune -a --volumes -f 2>/dev/null
```

### JetBrains IDEs

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Caches | `~/Library/Caches/JetBrains/` | Safe | 1-5 GB |
| Local history | `~/Library/Caches/JetBrains/*/LocalHistory/` | Moderate | 0.5-2 GB |
| Logs | `~/Library/Logs/JetBrains/` | Safe | 0.1-1 GB |

### Android Studio

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Gradle cache | `~/.gradle/caches/` | Safe | 2-10 GB |
| Gradle wrapper | `~/.gradle/wrapper/dists/` | Safe | 1-3 GB |
| AVD images | `~/.android/avd/` | Moderate | 5-30 GB |
| Android SDK | `~/Library/Android/sdk/` | High | 10-50 GB |

```bash
# Gradle cache cleanup
rm -rf ~/.gradle/caches/ 2>/dev/null
rm -rf ~/.gradle/wrapper/dists/ 2>/dev/null
```

### CocoaPods

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Pods cache | `~/Library/Caches/CocoaPods/` | Safe | 0.5-3 GB |

```bash
pod cache clean --all 2>/dev/null
```

## 3. System Logs & Reports

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| User logs | `~/Library/Logs/` | Safe | 0.1-2 GB |
| System logs | `/var/log/` | Low | 0.1-1 GB |
| Diagnostic reports | `~/Library/Logs/DiagnosticReports/` | Safe | 0.01-0.5 GB |
| Crash reports | `/Library/Logs/DiagnosticReports/` | Safe | 0.01-0.5 GB |
| ASL logs | `/var/log/asl/` | Low | 0.01-0.2 GB |
| System profiler | `~/Library/Logs/CoreSimulator/` | Safe | 0.1-1 GB |

```bash
# User logs
rm -rf ~/Library/Logs/* 2>/dev/null

# Diagnostic reports
rm -rf ~/Library/Logs/DiagnosticReports/* 2>/dev/null
rm -rf /Library/Logs/DiagnosticReports/* 2>/dev/null

# Old system logs (keep recent)
sudo rm -rf /var/log/*.gz 2>/dev/null
```

## 4. Trash

```bash
# Show Trash size
du -sh ~/.Trash 2>/dev/null

# Empty Trash
rm -rf ~/.Trash/* 2>/dev/null
```

Typical: 0-50 GB depending on user behavior. Risk: Moderate (user chose to
delete these, but might want to recover).

## 5. iOS/Device Backups

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| iOS backups | `~/Library/Application Support/MobileSync/Backup/` | High | 5-100 GB |

These are full device backups. Cleaning is HIGH risk — user loses backup data.
Always list backups with dates first and let user decide.

```bash
# List iOS backups with sizes
du -sh ~/Library/Application\ Support/MobileSync/Backup/*/ 2>/dev/null
```

## 6. Mail & Downloads

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Mail downloads | `~/Library/Containers/com.apple.mail/Data/Library/Mail Downloads/` | Moderate | 0.1-5 GB |
| Downloads folder | `~/Downloads/` | High | 1-30 GB |
| Old DMGs | `~/Downloads/*.dmg` | Low | 0.5-5 GB |
| Old ZIPs | `~/Downloads/*.zip` | Low | 0.5-5 GB |

```bash
# Find old DMGs in Downloads (older than 30 days)
find ~/Downloads -name "*.dmg" -mtime +30 2>/dev/null

# Find large files in Downloads
find ~/Downloads -size +100M 2>/dev/null
```

## 7. Application Leftovers

When apps are dragged to trash, they leave behind support files.

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| App support | `~/Library/Application Support/` | Moderate | varies |
| Preferences | `~/Library/Preferences/` | Low | minimal |
| Saved state | `~/Library/Saved Application State/` | Safe | 0.01-0.5 GB |
| Containers | `~/Library/Containers/` | Moderate | varies |
| Group Containers | `~/Library/Group Containers/` | Moderate | varies |

Cleaning app leftovers requires checking which apps are still installed.
Only remove support files for apps that no longer exist in /Applications.

```bash
# List Saved Application State (safe to clean)
du -sh ~/Library/Saved\ Application\ State/ 2>/dev/null
rm -rf ~/Library/Saved\ Application\ State/* 2>/dev/null
```

## 8. Language & Runtime Leftovers

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Old Ruby gems | `~/.gem/` | Low | 0.1-1 GB |
| rbenv versions | `~/.rbenv/versions/` | Moderate | 0.5-3 GB |
| nvm node versions | `~/.nvm/versions/` | Moderate | 1-5 GB |
| Old Java JDKs | `/Library/Java/JavaVirtualMachines/` | Moderate | 0.5-3 GB |
| Composer cache | `~/.composer/cache/` | Safe | 0.1-1 GB |

## 9. Cloud Storage Caches

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| Dropbox cache | `~/.dropbox/cache/` | Safe | 0.1-2 GB |
| iCloud drive cache | `~/Library/Mobile Documents/` (evictable) | Low | varies |

```bash
# Dropbox cache
rm -rf ~/.dropbox/cache/ 2>/dev/null
```

## 10. Miscellaneous

| Target | Path | Risk | Typical Size |
|--------|------|------|-------------|
| QuickLook thumbnails | `~/Library/Caches/com.apple.QuickLook.thumbnailcache/` | Safe | 0.01-0.5 GB |
| Speech data | `~/Library/Caches/com.apple.SpeechRecognitionCore/` | Safe | 0.1-1 GB |
| Siri analytics | `~/Library/Assistant/SiriAnalytics.db` | Safe | 0.01-0.1 GB |
| CoreDuet knowledge | `~/Library/Application Support/Knowledge/` | Safe | 0.01-0.1 GB |

## Priority Order for Maximum Impact

When cleaning for space, target in this order (highest ROI first):

1. **Xcode DerivedData + simulators** — 10-80 GB
2. **Docker images + build cache** — 10-80 GB
3. **node_modules (stale projects)** — 5-50 GB
4. **User caches** — 2-20 GB
5. **Rust target dirs** — 5-50 GB
6. **iOS backups** — 5-100 GB (but high risk)
7. **Homebrew cleanup** — 1-8 GB
8. **Gradle/Android caches** — 3-13 GB
9. **Package manager caches** (npm, pip, cargo) — 3-15 GB
10. **Trash** — 0-50 GB
11. **Logs** — 0.5-5 GB
12. **Downloads (old DMGs/ZIPs)** — 0.5-5 GB
