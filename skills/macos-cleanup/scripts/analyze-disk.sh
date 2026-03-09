#!/usr/bin/env bash
# macOS Disk Cleanup Analyzer
# Scans known cleanup targets and reports sizes with risk levels.
# Output: structured text report suitable for agent consumption.
#
# Usage: bash analyze-disk.sh [--json] [--dev-only] [--quick]
#   --json      Output as JSON instead of table
#   --dev-only  Only scan developer tool caches
#   --quick     Skip slow scans (stale node_modules, large file search)

set -euo pipefail

# Parse arguments
JSON_OUTPUT=false
DEV_ONLY=false
QUICK=false
for arg in "$@"; do
  case "$arg" in
    --json) JSON_OUTPUT=true ;;
    --dev-only) DEV_ONLY=true ;;
    --quick) QUICK=true ;;
  esac
done

# Helper: get directory size in bytes, return "0" if doesn't exist
dir_size_bytes() {
  local path="$1"
  if [ -d "$path" ]; then
    du -sk "$path" 2>/dev/null | awk '{print $1 * 1024}' || echo "0"
  else
    echo "0"
  fi
}

# Helper: get directory size human-readable
dir_size_human() {
  local path="$1"
  if [ -d "$path" ]; then
    du -sh "$path" 2>/dev/null | cut -f1 || echo "0B"
  else
    echo "0B"
  fi
}

# Helper: format bytes to human-readable
format_bytes() {
  local bytes=$1
  if [ "$bytes" -ge 1073741824 ]; then
    echo "$(echo "scale=1; $bytes / 1073741824" | bc) GB"
  elif [ "$bytes" -ge 1048576 ]; then
    echo "$(echo "scale=1; $bytes / 1048576" | bc) MB"
  elif [ "$bytes" -ge 1024 ]; then
    echo "$(echo "scale=0; $bytes / 1024" | bc) KB"
  else
    echo "${bytes} B"
  fi
}

# Collect disk info
DISK_TOTAL=$(diskutil info / 2>/dev/null | grep "Container Total Space" | awk -F'(' '{print $2}' | awk '{print $1}' || echo "0")
DISK_FREE=$(diskutil info / 2>/dev/null | grep "Container Free Space" | awk -F'(' '{print $2}' | awk '{print $1}' || echo "0")
DISK_FREE_HUMAN=$(df -h / 2>/dev/null | tail -1 | awk '{print $4}')
DISK_TOTAL_HUMAN=$(df -h / 2>/dev/null | tail -1 | awk '{print $2}')
DISK_USED_PCT=$(df -h / 2>/dev/null | tail -1 | awk '{print $5}')

# Results array (category|size_bytes|size_human|risk|path)
declare -a RESULTS=()

add_result() {
  local category="$1" size_bytes="$2" size_human="$3" risk="$4" path="$5"
  if [ "$size_bytes" -gt 0 ] 2>/dev/null; then
    RESULTS+=("${category}|${size_bytes}|${size_human}|${risk}|${path}")
  fi
}

echo "Scanning macOS disk for cleanup targets..." >&2

# === CACHES ===
if [ "$DEV_ONLY" = false ]; then
  echo "  Scanning user caches..." >&2
  bytes=$(dir_size_bytes ~/Library/Caches)
  human=$(dir_size_human ~/Library/Caches)
  add_result "User Caches" "$bytes" "$human" "safe" "~/Library/Caches/"

  echo "  Scanning logs..." >&2
  bytes=$(dir_size_bytes ~/Library/Logs)
  human=$(dir_size_human ~/Library/Logs)
  add_result "User Logs" "$bytes" "$human" "safe" "~/Library/Logs/"

  # Diagnostic reports
  bytes=$(dir_size_bytes ~/Library/Logs/DiagnosticReports)
  human=$(dir_size_human ~/Library/Logs/DiagnosticReports)
  add_result "Diagnostic Reports" "$bytes" "$human" "safe" "~/Library/Logs/DiagnosticReports/"

  # Trash
  echo "  Scanning Trash..." >&2
  bytes=$(dir_size_bytes ~/.Trash)
  human=$(dir_size_human ~/.Trash)
  add_result "Trash" "$bytes" "$human" "moderate" "~/.Trash/"

  # Saved Application State
  bytes=$(dir_size_bytes ~/Library/Saved\ Application\ State)
  human=$(dir_size_human ~/Library/Saved\ Application\ State)
  add_result "Saved App State" "$bytes" "$human" "safe" "~/Library/Saved Application State/"

  # Downloads (old DMGs/ZIPs)
  echo "  Scanning Downloads..." >&2
  if [ -d ~/Downloads ]; then
    dmg_bytes=$(find ~/Downloads -name "*.dmg" -mtime +30 -exec stat -f%z {} \; 2>/dev/null | awk '{s+=$1}END{print s+0}')
    zip_bytes=$(find ~/Downloads -name "*.zip" -mtime +30 -exec stat -f%z {} \; 2>/dev/null | awk '{s+=$1}END{print s+0}')
    old_dl_bytes=$((dmg_bytes + zip_bytes))
    if [ "$old_dl_bytes" -gt 0 ]; then
      old_dl_human=$(format_bytes "$old_dl_bytes")
      add_result "Old Downloads (DMG/ZIP >30d)" "$old_dl_bytes" "$old_dl_human" "low" "~/Downloads/*.{dmg,zip}"
    fi
  fi

  # iOS backups
  echo "  Scanning iOS backups..." >&2
  bytes=$(dir_size_bytes ~/Library/Application\ Support/MobileSync/Backup)
  human=$(dir_size_human ~/Library/Application\ Support/MobileSync/Backup)
  add_result "iOS Device Backups" "$bytes" "$human" "high" "~/Library/Application Support/MobileSync/Backup/"

  # Mail downloads
  bytes=$(dir_size_bytes ~/Library/Containers/com.apple.mail/Data/Library/Mail\ Downloads)
  human=$(dir_size_human ~/Library/Containers/com.apple.mail/Data/Library/Mail\ Downloads)
  add_result "Mail Downloads" "$bytes" "$human" "moderate" "~/Library/Containers/com.apple.mail/.../Mail Downloads/"
fi

# === DEVELOPER TOOLS ===

# Xcode
echo "  Scanning Xcode..." >&2
bytes=$(dir_size_bytes ~/Library/Developer/Xcode/DerivedData)
human=$(dir_size_human ~/Library/Developer/Xcode/DerivedData)
add_result "Xcode DerivedData" "$bytes" "$human" "safe" "~/Library/Developer/Xcode/DerivedData/"

bytes=$(dir_size_bytes ~/Library/Developer/Xcode/Archives)
human=$(dir_size_human ~/Library/Developer/Xcode/Archives)
add_result "Xcode Archives" "$bytes" "$human" "moderate" "~/Library/Developer/Xcode/Archives/"

bytes=$(dir_size_bytes ~/Library/Developer/Xcode/iOS\ DeviceSupport)
human=$(dir_size_human ~/Library/Developer/Xcode/iOS\ DeviceSupport)
add_result "iOS Device Support" "$bytes" "$human" "low" "~/Library/Developer/Xcode/iOS DeviceSupport/"

bytes=$(dir_size_bytes ~/Library/Developer/CoreSimulator/Devices)
human=$(dir_size_human ~/Library/Developer/CoreSimulator/Devices)
add_result "Simulator Devices" "$bytes" "$human" "moderate" "~/Library/Developer/CoreSimulator/Devices/"

bytes=$(dir_size_bytes ~/Library/Developer/CoreSimulator/Caches)
human=$(dir_size_human ~/Library/Developer/CoreSimulator/Caches)
add_result "Simulator Caches" "$bytes" "$human" "safe" "~/Library/Developer/CoreSimulator/Caches/"

bytes=$(dir_size_bytes ~/Library/Caches/com.apple.dt.Xcode)
human=$(dir_size_human ~/Library/Caches/com.apple.dt.Xcode)
add_result "Xcode App Cache" "$bytes" "$human" "safe" "~/Library/Caches/com.apple.dt.Xcode/"

# Homebrew
echo "  Scanning Homebrew..." >&2
if command -v brew &>/dev/null; then
  brew_cache=$(brew --cache 2>/dev/null || echo "")
  if [ -n "$brew_cache" ] && [ -d "$brew_cache" ]; then
    bytes=$(dir_size_bytes "$brew_cache")
    human=$(dir_size_human "$brew_cache")
    add_result "Homebrew Cache" "$bytes" "$human" "safe" "$brew_cache"
  fi
fi

# npm
echo "  Scanning package manager caches..." >&2
bytes=$(dir_size_bytes ~/.npm)
human=$(dir_size_human ~/.npm)
add_result "npm Cache" "$bytes" "$human" "safe" "~/.npm/"

# yarn
bytes=$(dir_size_bytes ~/Library/Caches/Yarn)
human=$(dir_size_human ~/Library/Caches/Yarn)
add_result "Yarn Cache" "$bytes" "$human" "safe" "~/Library/Caches/Yarn/"

# pnpm
if command -v pnpm &>/dev/null; then
  pnpm_store=$(pnpm store path 2>/dev/null || echo "")
  if [ -n "$pnpm_store" ] && [ -d "$pnpm_store" ]; then
    bytes=$(dir_size_bytes "$pnpm_store")
    human=$(dir_size_human "$pnpm_store")
    add_result "pnpm Store" "$bytes" "$human" "safe" "$pnpm_store"
  fi
fi

# Bun
bytes=$(dir_size_bytes ~/.bun/install/cache)
human=$(dir_size_human ~/.bun/install/cache)
add_result "Bun Cache" "$bytes" "$human" "safe" "~/.bun/install/cache/"

# pip
bytes=$(dir_size_bytes ~/Library/Caches/pip)
human=$(dir_size_human ~/Library/Caches/pip)
add_result "pip Cache" "$bytes" "$human" "safe" "~/Library/Caches/pip/"

# conda
for conda_dir in ~/miniconda3/pkgs ~/anaconda3/pkgs ~/miniforge3/pkgs; do
  if [ -d "$conda_dir" ]; then
    bytes=$(dir_size_bytes "$conda_dir")
    human=$(dir_size_human "$conda_dir")
    add_result "Conda Package Cache" "$bytes" "$human" "safe" "$conda_dir"
  fi
done

# Cargo (Rust)
echo "  Scanning Rust/Cargo..." >&2
cargo_total=0
for cargo_sub in ~/.cargo/registry/cache ~/.cargo/registry/src ~/.cargo/git/checkouts; do
  if [ -d "$cargo_sub" ]; then
    sub_bytes=$(dir_size_bytes "$cargo_sub")
    cargo_total=$((cargo_total + sub_bytes))
  fi
done
if [ "$cargo_total" -gt 0 ]; then
  cargo_human=$(format_bytes "$cargo_total")
  add_result "Cargo Cache" "$cargo_total" "$cargo_human" "safe" "~/.cargo/registry/ + ~/.cargo/git/"
fi

# Go
echo "  Scanning Go..." >&2
bytes=$(dir_size_bytes ~/go/pkg/mod)
human=$(dir_size_human ~/go/pkg/mod)
add_result "Go Module Cache" "$bytes" "$human" "safe" "~/go/pkg/mod/"

go_build_cache="${HOME}/.cache/go-build"
if [ -d "$go_build_cache" ]; then
  bytes=$(dir_size_bytes "$go_build_cache")
  human=$(dir_size_human "$go_build_cache")
  add_result "Go Build Cache" "$bytes" "$human" "safe" "$go_build_cache"
fi

# Gradle
bytes=$(dir_size_bytes ~/.gradle/caches)
human=$(dir_size_human ~/.gradle/caches)
add_result "Gradle Cache" "$bytes" "$human" "safe" "~/.gradle/caches/"

bytes=$(dir_size_bytes ~/.gradle/wrapper/dists)
human=$(dir_size_human ~/.gradle/wrapper/dists)
add_result "Gradle Wrapper Dists" "$bytes" "$human" "safe" "~/.gradle/wrapper/dists/"

# Maven
bytes=$(dir_size_bytes ~/.m2/repository)
human=$(dir_size_human ~/.m2/repository)
add_result "Maven Local Repo" "$bytes" "$human" "safe" "~/.m2/repository/"

# CocoaPods
bytes=$(dir_size_bytes ~/Library/Caches/CocoaPods)
human=$(dir_size_human ~/Library/Caches/CocoaPods)
add_result "CocoaPods Cache" "$bytes" "$human" "safe" "~/Library/Caches/CocoaPods/"

# Docker
echo "  Scanning Docker..." >&2
docker_raw="$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
if [ -f "$docker_raw" ]; then
  bytes=$(stat -f%z "$docker_raw" 2>/dev/null || echo "0")
  human=$(format_bytes "$bytes")
  add_result "Docker Desktop VM Disk" "$bytes" "$human" "moderate" "$docker_raw"
fi

# JetBrains
bytes=$(dir_size_bytes ~/Library/Caches/JetBrains)
human=$(dir_size_human ~/Library/Caches/JetBrains)
add_result "JetBrains Caches" "$bytes" "$human" "safe" "~/Library/Caches/JetBrains/"

bytes=$(dir_size_bytes ~/Library/Logs/JetBrains)
human=$(dir_size_human ~/Library/Logs/JetBrains)
add_result "JetBrains Logs" "$bytes" "$human" "safe" "~/Library/Logs/JetBrains/"

# VS Code
vscode_cache_total=0
for vsc_dir in \
  ~/Library/Application\ Support/Code/Cache \
  ~/Library/Application\ Support/Code/CachedData \
  ~/Library/Application\ Support/Code/CachedExtensions \
  ~/Library/Application\ Support/Code/CachedExtensionVSIXs \
  ~/Library/Application\ Support/Code/logs; do
  if [ -d "$vsc_dir" ]; then
    sub_bytes=$(dir_size_bytes "$vsc_dir")
    vscode_cache_total=$((vscode_cache_total + sub_bytes))
  fi
done
if [ "$vscode_cache_total" -gt 0 ]; then
  vsc_human=$(format_bytes "$vscode_cache_total")
  add_result "VS Code Caches" "$vscode_cache_total" "$vsc_human" "safe" "~/Library/Application Support/Code/Cache*"
fi

# Stale node_modules (slow scan)
if [ "$QUICK" = false ]; then
  echo "  Scanning for stale node_modules (this may take a moment)..." >&2
  stale_nm_bytes=0
  stale_nm_count=0
  # Search common dev directories
  for search_dir in ~/dev ~/projects ~/code ~/src ~/work ~/repos; do
    if [ -d "$search_dir" ]; then
      while IFS= read -r nm_dir; do
        nm_bytes=$(dir_size_bytes "$nm_dir")
        stale_nm_bytes=$((stale_nm_bytes + nm_bytes))
        stale_nm_count=$((stale_nm_count + 1))
      done < <(find "$search_dir" -name node_modules -type d -maxdepth 5 -mtime +30 -prune 2>/dev/null)
    fi
  done
  if [ "$stale_nm_bytes" -gt 0 ]; then
    stale_nm_human=$(format_bytes "$stale_nm_bytes")
    add_result "Stale node_modules (${stale_nm_count} dirs, >30d)" "$stale_nm_bytes" "$stale_nm_human" "moderate" "various ~/dev/**/node_modules"
  fi

  # Stale Rust target/ dirs
  echo "  Scanning for stale Rust target/ dirs..." >&2
  stale_target_bytes=0
  stale_target_count=0
  for search_dir in ~/dev ~/projects ~/code ~/src ~/work ~/repos; do
    if [ -d "$search_dir" ]; then
      while IFS= read -r t_dir; do
        if [ -f "$(dirname "$t_dir")/Cargo.toml" ]; then
          t_bytes=$(dir_size_bytes "$t_dir")
          stale_target_bytes=$((stale_target_bytes + t_bytes))
          stale_target_count=$((stale_target_count + 1))
        fi
      done < <(find "$search_dir" -name target -type d -maxdepth 5 -mtime +30 -prune 2>/dev/null)
    fi
  done
  if [ "$stale_target_bytes" -gt 0 ]; then
    stale_target_human=$(format_bytes "$stale_target_bytes")
    add_result "Stale Rust target/ (${stale_target_count} dirs, >30d)" "$stale_target_bytes" "$stale_target_human" "moderate" "various ~/dev/**/target"
  fi
fi

# Dropbox cache
bytes=$(dir_size_bytes ~/.dropbox/cache)
human=$(dir_size_human ~/.dropbox/cache)
add_result "Dropbox Cache" "$bytes" "$human" "safe" "~/.dropbox/cache/"

# Swift Package Manager
bytes=$(dir_size_bytes ~/Library/Caches/org.swift.swiftpm)
human=$(dir_size_human ~/Library/Caches/org.swift.swiftpm)
add_result "Swift PM Cache" "$bytes" "$human" "safe" "~/Library/Caches/org.swift.swiftpm/"

# Flutter/Dart
bytes=$(dir_size_bytes ~/.pub-cache)
human=$(dir_size_human ~/.pub-cache)
add_result "Flutter/Dart pub-cache" "$bytes" "$human" "safe" "~/.pub-cache/"

# Composer (PHP)
bytes=$(dir_size_bytes ~/.composer/cache)
human=$(dir_size_human ~/.composer/cache)
add_result "Composer Cache" "$bytes" "$human" "safe" "~/.composer/cache/"

echo "  Scan complete." >&2

# === OUTPUT ===

if [ "$JSON_OUTPUT" = true ]; then
  echo "{"
  echo "  \"disk\": {"
  echo "    \"total\": \"$DISK_TOTAL_HUMAN\","
  echo "    \"free\": \"$DISK_FREE_HUMAN\","
  echo "    \"used_pct\": \"$DISK_USED_PCT\""
  echo "  },"
  echo "  \"targets\": ["
  first=true
  # Sort by size descending
  IFS=$'\n' sorted=($(for r in "${RESULTS[@]}"; do echo "$r"; done | sort -t'|' -k2 -rn))
  for result in "${sorted[@]}"; do
    IFS='|' read -r category size_bytes size_human risk path <<< "$result"
    if [ "$first" = true ]; then
      first=false
    else
      echo ","
    fi
    printf '    {"category": "%s", "size_bytes": %s, "size_human": "%s", "risk": "%s", "path": "%s"}' \
      "$category" "$size_bytes" "$size_human" "$risk" "$path"
  done
  echo ""
  echo "  ]"
  echo "}"
else
  echo ""
  echo "macOS Disk Cleanup Report"
  echo "========================"
  echo ""
  echo "Disk: ${DISK_TOTAL_HUMAN} total, ${DISK_FREE_HUMAN} free (${DISK_USED_PCT} used)"
  echo ""

  # Calculate totals by risk
  safe_total=0
  moderate_total=0
  high_total=0
  low_total=0
  grand_total=0

  printf "%-45s %10s   %-10s\n" "Category" "Size" "Risk"
  printf "%-45s %10s   %-10s\n" "─────────────────────────────────────────────" "──────────" "──────────"

  # Sort by size descending
  IFS=$'\n' sorted=($(for r in "${RESULTS[@]}"; do echo "$r"; done | sort -t'|' -k2 -rn))
  for result in "${sorted[@]}"; do
    IFS='|' read -r category size_bytes size_human risk path <<< "$result"
    # Skip items under 10 MB
    if [ "$size_bytes" -lt 10485760 ] 2>/dev/null; then
      continue
    fi
    printf "%-45s %10s   %-10s\n" "$category" "$size_human" "$risk"
    grand_total=$((grand_total + size_bytes))
    case "$risk" in
      safe) safe_total=$((safe_total + size_bytes)) ;;
      low) low_total=$((low_total + size_bytes)) ;;
      moderate) moderate_total=$((moderate_total + size_bytes)) ;;
      high) high_total=$((high_total + size_bytes)) ;;
    esac
  done

  echo ""
  printf "%-45s %10s\n" "─────────────────────────────────────────────" "──────────"
  printf "%-45s %10s\n" "Total reclaimable" "$(format_bytes $grand_total)"
  echo ""
  printf "  %-43s %10s\n" "Safe to clean now" "$(format_bytes $safe_total)"
  printf "  %-43s %10s\n" "Low risk (confirm)" "$(format_bytes $low_total)"
  printf "  %-43s %10s\n" "Moderate risk (review first)" "$(format_bytes $moderate_total)"
  printf "  %-43s %10s\n" "High risk (explicit opt-in only)" "$(format_bytes $high_total)"
fi
