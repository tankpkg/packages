#!/usr/bin/env bash
# Detect hardware relevant to local LLM inference.
# Prints: OS, CPU, total RAM, GPU(s) with VRAM, memory bandwidth estimate.
# Safe on macOS, Linux, WSL. Falls back gracefully when tools are missing.

set -u

section() { printf '\n=== %s ===\n' "$1"; }
kv() { printf '%-22s %s\n' "$1:" "$2"; }

detect_os() {
  case "$(uname -s)" in
    Darwin) echo "macOS $(sw_vers -productVersion 2>/dev/null || echo unknown)" ;;
    Linux)
      if [ -r /etc/os-release ]; then
        . /etc/os-release
        echo "$PRETTY_NAME"
      else
        echo "Linux $(uname -r)"
      fi
      ;;
    *) echo "$(uname -s) $(uname -r)" ;;
  esac
}

detect_cpu() {
  case "$(uname -s)" in
    Darwin)
      sysctl -n machdep.cpu.brand_string 2>/dev/null || echo unknown
      ;;
    Linux)
      awk -F': ' '/^model name/ { print $2; exit }' /proc/cpuinfo 2>/dev/null \
        || awk -F': ' '/^Model/ { print $2; exit }' /proc/cpuinfo 2>/dev/null \
        || echo unknown
      ;;
    *) echo unknown ;;
  esac
}

detect_ram_gb() {
  case "$(uname -s)" in
    Darwin)
      local bytes
      bytes=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
      awk -v b="$bytes" 'BEGIN { printf "%.0f GB", b / 1024 / 1024 / 1024 }'
      ;;
    Linux)
      awk '/MemTotal/ { printf "%.0f GB", $2 / 1024 / 1024 }' /proc/meminfo 2>/dev/null \
        || echo unknown
      ;;
    *) echo unknown ;;
  esac
}

detect_apple_chip() {
  [ "$(uname -s)" = "Darwin" ] || return 1
  sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -qi "Apple" || return 1
  local chip cores
  chip=$(sysctl -n machdep.cpu.brand_string 2>/dev/null)
  cores=$(system_profiler SPDisplaysDataType 2>/dev/null | awk -F': ' '/Total Number of Cores/ { print $2; exit }')
  kv "Apple Silicon" "$chip"
  [ -n "${cores:-}" ] && kv "GPU cores" "$cores"
  # Rough bandwidth hint by chip family — user should confirm.
  local hint=""
  case "$chip" in
    *M1\ Ultra*)   hint="~800 GB/s" ;;
    *M1\ Max*)     hint="~400 GB/s" ;;
    *M1\ Pro*)     hint="~200 GB/s" ;;
    *M1*)          hint="~68 GB/s" ;;
    *M2\ Ultra*)   hint="~800 GB/s" ;;
    *M2\ Max*)     hint="~400 GB/s" ;;
    *M2\ Pro*)     hint="~200 GB/s" ;;
    *M2*)          hint="~100 GB/s" ;;
    *M3\ Ultra*)   hint="~800 GB/s" ;;
    *M3\ Max*)     hint="~300-400 GB/s (check GPU cores)" ;;
    *M3\ Pro*)     hint="~150 GB/s" ;;
    *M3*)          hint="~100 GB/s" ;;
    *M4\ Max*)     hint="~410-546 GB/s (check GPU cores)" ;;
    *M4\ Pro*)     hint="~273 GB/s" ;;
    *M4*)          hint="~120 GB/s" ;;
  esac
  [ -n "$hint" ] && kv "Bandwidth (est)" "$hint"
  local wired
  wired=$(sysctl -n iogpu.wired_limit_mb 2>/dev/null || echo "default (~67-75% of RAM)")
  kv "Wired VRAM cap" "$wired MB"
}

detect_nvidia() {
  command -v nvidia-smi >/dev/null 2>&1 || return 1
  echo
  section "NVIDIA GPUs"
  nvidia-smi --query-gpu=index,name,memory.total,memory.free,driver_version \
    --format=csv,noheader 2>/dev/null \
    | awk -F', ' '{ printf "  [%s] %s | VRAM %s total, %s free | driver %s\n", $1,$2,$3,$4,$5 }'
}

detect_amd() {
  command -v rocm-smi >/dev/null 2>&1 || return 1
  echo
  section "AMD GPUs (ROCm)"
  rocm-smi --showproductname --showmeminfo vram 2>/dev/null \
    | grep -E 'GPU\[|Card series|Total Memory|Used Memory' \
    || rocm-smi 2>/dev/null
}

detect_intel_gpu_linux() {
  [ "$(uname -s)" = "Linux" ] || return 1
  command -v lspci >/dev/null 2>&1 || return 1
  local intel
  intel=$(lspci | grep -iE 'VGA.*Intel|Display.*Intel|3D.*Intel' || true)
  [ -z "$intel" ] && return 1
  echo
  section "Intel GPUs"
  echo "$intel"
}

detect_wsl_gpu() {
  [ "$(uname -s)" = "Linux" ] || return 1
  grep -qi microsoft /proc/version 2>/dev/null || return 1
  echo
  section "WSL"
  echo "Running under WSL; GPU passthrough depends on Windows drivers."
  echo "Use nvidia-smi above if present, or check Windows Task Manager for AMD."
}

dmidecode_ram_speed_linux() {
  [ "$(uname -s)" = "Linux" ] || return 1
  command -v sudo >/dev/null 2>&1 || return 1
  command -v dmidecode >/dev/null 2>&1 || return 1
  # Non-fatal; needs sudo. Don't prompt, just try without.
  sudo -n dmidecode --type memory 2>/dev/null \
    | awk '/Configured Memory Speed/ && !/Unknown/ { print $4, $5; exit }'
}

main() {
  section "System"
  kv "OS" "$(detect_os)"
  kv "CPU" "$(detect_cpu)"
  kv "RAM" "$(detect_ram_gb)"

  if detect_apple_chip; then :; fi

  detect_nvidia || true
  detect_amd || true
  detect_intel_gpu_linux || true
  detect_wsl_gpu || true

  if [ "$(uname -s)" = "Linux" ]; then
    local speed
    speed=$(dmidecode_ram_speed_linux || true)
    if [ -n "${speed:-}" ]; then
      echo
      section "RAM"
      kv "Configured speed" "$speed (per DIMM)"
    fi
  fi

  echo
  echo "Pass this output back to the LLM-fit skill along with the exact model name."
}

main
