# Space Analysis Techniques

How to find where disk space is being consumed on macOS, identify the
biggest offenders, and present actionable recommendations.

## Quick Disk Overview

```bash
# Total disk usage and free space
df -h /

# Accurate reading with purgeable space
diskutil info / | grep -E "(Total|Free|Available|Purgeable)"

# Top-level home directory usage
du -sh ~/*/ ~/.[!.]* 2>/dev/null | sort -hr | head -20
```

## The Scan → Report → Clean Workflow

### Step 1: Scan

Run the analysis script to discover all cleanup targets:

```bash
# The analyze-disk.sh script automates this
# It checks every known cleanup target and reports sizes

# Manual equivalent — scan key directories
echo "=== User Caches ==="
du -sh ~/Library/Caches 2>/dev/null

echo "=== Logs ==="
du -sh ~/Library/Logs 2>/dev/null

echo "=== Xcode ==="
du -sh ~/Library/Developer/Xcode/DerivedData 2>/dev/null
du -sh ~/Library/Developer/Xcode/Archives 2>/dev/null
du -sh ~/Library/Developer/Xcode/iOS\ DeviceSupport 2>/dev/null

echo "=== Homebrew ==="
brew cleanup --dry-run 2>/dev/null | tail -1

echo "=== Docker ==="
docker system df 2>/dev/null

echo "=== Trash ==="
du -sh ~/.Trash 2>/dev/null
```

### Step 2: Report

Present findings as a categorized summary table:

```
macOS Disk Cleanup Report
========================

Disk: 494 GB total, 42 GB free (8.5%)

Category                         Size     Risk     
─────────────────────────────────────────────────────
Xcode DerivedData               18.2 GB   Safe     
Docker images (unused)          12.4 GB   Moderate 
User Caches                      8.3 GB   Safe     
Stale node_modules (4 dirs)      6.1 GB   Moderate 
Trash                            4.8 GB   Moderate 
npm/yarn/pnpm cache              3.2 GB   Safe     
Homebrew old versions            2.1 GB   Safe     
iOS Device Support (old)         1.8 GB   Low      
Logs & diagnostics               0.9 GB   Safe     
pip cache                        0.7 GB   Safe     
─────────────────────────────────────────────────────
Total reclaimable:              58.5 GB

Safe to clean now:              34.4 GB
Needs confirmation:             24.1 GB
```

### Step 3: Clean

Execute cleanup in risk-level order:
1. Clean all Safe targets (no confirmation needed)
2. Present Moderate targets, ask for confirmation
3. Present High-risk targets only if specifically asked

## Finding Large Files

```bash
# Find files larger than 500 MB anywhere in home
find ~ -type f -size +500M -not -path "*/Library/*" 2>/dev/null | \
  while read f; do echo "$(du -sh "$f" 2>/dev/null)"; done | sort -hr

# Find files larger than 1 GB anywhere
find ~ -type f -size +1G 2>/dev/null | \
  while read f; do echo "$(du -sh "$f" 2>/dev/null)"; done | sort -hr

# Top 20 largest files in home
find ~ -type f 2>/dev/null | xargs du -s 2>/dev/null | sort -rn | head -20 | \
  while read size file; do echo "$(du -sh "$file" 2>/dev/null)"; done
```

## Finding Large Directories

```bash
# Top 20 largest directories under home (depth 3)
du -d 3 ~ 2>/dev/null | sort -rn | head -20 | \
  while read size dir; do echo "$(du -sh "$dir" 2>/dev/null)"; done

# Just Library subdirectories
du -sh ~/Library/*/ 2>/dev/null | sort -hr | head -20
```

## Finding Stale node_modules

Node modules in projects you haven't touched in weeks are pure waste.

```bash
# Find node_modules directories, show parent project and last modified
find ~/dev -name node_modules -type d -maxdepth 4 2>/dev/null | while read dir; do
  project_dir=$(dirname "$dir")
  size=$(du -sh "$dir" 2>/dev/null | cut -f1)
  last_modified=$(stat -f "%Sm" -t "%Y-%m-%d" "$dir" 2>/dev/null)
  echo "$size  $last_modified  $project_dir"
done | sort -hr
```

To clean, the user can `rm -rf` individual node_modules directories.
The project will need `npm install` (or equivalent) to restore them.

## Finding Stale Rust target/ Directories

```bash
find ~/dev -name target -type d -maxdepth 4 2>/dev/null | while read dir; do
  # Check if parent has a Cargo.toml
  if [ -f "$(dirname "$dir")/Cargo.toml" ]; then
    project_dir=$(dirname "$dir")
    size=$(du -sh "$dir" 2>/dev/null | cut -f1)
    last_modified=$(stat -f "%Sm" -t "%Y-%m-%d" "$dir" 2>/dev/null)
    echo "$size  $last_modified  $project_dir"
  fi
done | sort -hr
```

## Docker Space Analysis

```bash
# Docker's own space report
docker system df -v 2>/dev/null

# Docker Desktop VM disk image (the real space consumer)
du -sh ~/Library/Containers/com.docker.docker/Data/vms/ 2>/dev/null

# Orbstack (Docker alternative)
du -sh ~/Library/Group\ Containers/*.orbstack/ 2>/dev/null
```

Docker Desktop's VM disk image only shrinks when you do a factory reset or
use `docker system prune`. Even after deleting images, the VM file stays
the same size.

## Time Machine Snapshots

Local TM snapshots can consume significant space invisibly:

```bash
# List local snapshots
tmutil listlocalsnapshots /

# Show snapshot sizes (requires sudo)
sudo tmutil listlocalsnapshots / | while read snap; do
  echo "$snap"
done

# Delete specific snapshot
sudo tmutil deletelocalsnapshots <YYYY-MM-DD-HHMMSS>

# Delete all local snapshots (aggressive)
for snap in $(tmutil listlocalsnapshots / | cut -d. -f4); do
  sudo tmutil deletelocalsnapshots "$snap"
done
```

## Recommended CLI Tools

These are established tools the agent can suggest for interactive
space exploration:

| Tool | Install | Description |
|------|---------|-------------|
| `ncdu` | `brew install ncdu` | Interactive terminal disk analyzer |
| `dust` | `brew install dust` | Rust-based `du` replacement with visual bars |
| `duf` | `brew install duf` | Modern `df` replacement with better output |
| `gdu` | `brew install gdu` | Fast disk usage analyzer with TUI |

These are for user reference only — the agent should use its own scripts
and `du`/`find` commands rather than depending on these being installed.

## Volume-Specific Paths

macOS mounts the data volume separately. Space calculations should consider:

```bash
# System volume (read-only on modern macOS)
df -h /System/Volumes/Data

# Same as root on APFS
df -h /
```

On APFS, `/` and `/System/Volumes/Data` share the same container, so
free space is the same regardless of which you query.

## Interpreting macOS Storage

Finder's "About This Mac" storage display categories:

| Category | Includes | Agent can clean? |
|----------|----------|------------------|
| Apps | /Applications, ~/Applications | No (user decision) |
| Documents | ~/Documents, ~/Desktop, etc. | No (user data) |
| System Data | Caches, logs, TM snapshots | Yes (caches, logs) |
| macOS | /System | No (SIP-protected) |
| Other | Everything else | Depends on content |

"System Data" and "Other" are the categories most inflated by cleanable
content (caches, dev tool artifacts, Docker images).
