#!/usr/bin/env bash
set -euo pipefail

# Usage: bash system-checkup.sh [--json] [--quick] [--security-only]

JSON_OUTPUT=false
QUICK=false
SECURITY_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --json) JSON_OUTPUT=true ;;
    --quick) QUICK=true ;;
    --security-only) SECURITY_ONLY=true ;;
  esac
done

PASS="PASS"
WARN="WARN"
FAIL="FAIL"
INFO="INFO"

declare -a RESULTS=()

add_check() {
  local category="$1" check="$2" status="$3" detail="$4"
  RESULTS+=("${category}|${check}|${status}|${detail}")
}

echo "Running macOS system checkup..." >&2

check_security() {
  echo "  Checking security posture..." >&2

  local sip_status
  sip_status=$(csrutil status 2>/dev/null || echo "unknown")
  if echo "$sip_status" | grep -q "enabled"; then
    add_check "Security" "System Integrity Protection" "$PASS" "Enabled"
  else
    add_check "Security" "System Integrity Protection" "$FAIL" "Disabled — re-enable from Recovery Mode"
  fi

  local gatekeeper
  gatekeeper=$(spctl --status 2>/dev/null || echo "unknown")
  if echo "$gatekeeper" | grep -q "assessments enabled"; then
    add_check "Security" "Gatekeeper" "$PASS" "Enabled"
  else
    add_check "Security" "Gatekeeper" "$FAIL" "Disabled — run: sudo spctl --master-enable"
  fi

  local filevault
  filevault=$(fdesetup status 2>/dev/null || echo "unknown")
  if echo "$filevault" | grep -q "On"; then
    add_check "Security" "FileVault" "$PASS" "On"
  elif echo "$filevault" | grep -q "Off"; then
    add_check "Security" "FileVault" "$WARN" "Off — enable via System Settings > Privacy & Security"
  else
    add_check "Security" "FileVault" "$INFO" "Could not determine"
  fi

  local firewall
  firewall=$(sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null || echo "unknown")
  if echo "$firewall" | grep -qi "enabled"; then
    add_check "Security" "Firewall" "$PASS" "Enabled"
  else
    add_check "Security" "Firewall" "$WARN" "Disabled — enable via System Settings or socketfilterfw"
  fi

  local remote_login
  remote_login=$(systemsetup -getremotelogin 2>/dev/null || echo "unknown")
  if echo "$remote_login" | grep -qi "off"; then
    add_check "Security" "Remote Login (SSH)" "$PASS" "Off"
  elif echo "$remote_login" | grep -qi "on"; then
    add_check "Security" "Remote Login (SSH)" "$WARN" "On — disable if not needed"
  fi

  local auto_update
  auto_update=$(defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled 2>/dev/null || echo "0")
  if [ "$auto_update" = "1" ]; then
    add_check "Security" "Automatic Update Check" "$PASS" "Enabled"
  else
    add_check "Security" "Automatic Update Check" "$WARN" "Disabled — enable in System Settings > Software Update"
  fi
}

check_disk() {
  echo "  Checking disk health..." >&2

  local smart_status
  smart_status=$(diskutil info disk0 2>/dev/null | grep "SMART Status" | awk -F: '{print $2}' | xargs || echo "unknown")
  if [ "$smart_status" = "Verified" ]; then
    add_check "Disk" "SMART Status" "$PASS" "Verified"
  elif [ "$smart_status" = "Failing" ]; then
    add_check "Disk" "SMART Status" "$FAIL" "FAILING — back up immediately, replace drive"
  else
    add_check "Disk" "SMART Status" "$INFO" "$smart_status"
  fi

  local disk_pct
  disk_pct=$(df -h / 2>/dev/null | tail -1 | awk '{gsub(/%/,""); print $5}')
  local disk_free
  disk_free=$(df -h / 2>/dev/null | tail -1 | awk '{print $4}')
  if [ "$disk_pct" -lt 70 ] 2>/dev/null; then
    add_check "Disk" "Space Usage" "$PASS" "${disk_pct}% used, ${disk_free} free"
  elif [ "$disk_pct" -lt 85 ] 2>/dev/null; then
    add_check "Disk" "Space Usage" "$WARN" "${disk_pct}% used, ${disk_free} free — consider cleanup"
  else
    add_check "Disk" "Space Usage" "$FAIL" "${disk_pct}% used, ${disk_free} free — cleanup needed"
  fi
}

check_battery() {
  echo "  Checking battery..." >&2

  local has_battery
  has_battery=$(system_profiler SPPowerDataType 2>/dev/null | grep "Cycle Count" || echo "")
  if [ -z "$has_battery" ]; then
    add_check "Battery" "Battery" "$INFO" "No battery (desktop Mac)"
    return
  fi

  local cycle_count
  cycle_count=$(system_profiler SPPowerDataType 2>/dev/null | grep "Cycle Count" | awk '{print $NF}')
  if [ "$cycle_count" -lt 500 ] 2>/dev/null; then
    add_check "Battery" "Cycle Count" "$PASS" "$cycle_count cycles"
  elif [ "$cycle_count" -lt 800 ] 2>/dev/null; then
    add_check "Battery" "Cycle Count" "$WARN" "$cycle_count cycles — moderate wear"
  else
    add_check "Battery" "Cycle Count" "$FAIL" "$cycle_count cycles — high wear"
  fi

  local condition
  condition=$(system_profiler SPPowerDataType 2>/dev/null | grep "Condition" | awk -F: '{print $2}' | xargs)
  if [ "$condition" = "Normal" ]; then
    add_check "Battery" "Condition" "$PASS" "Normal"
  else
    add_check "Battery" "Condition" "$WARN" "$condition"
  fi
}

check_memory() {
  echo "  Checking memory..." >&2

  local mem_pressure
  mem_pressure=$(memory_pressure 2>/dev/null | grep "System-wide" | awk '{print $NF}' | tr -d '%')
  local mem_free=$((100 - ${mem_pressure:-0}))

  if [ "$mem_free" -gt 40 ] 2>/dev/null; then
    add_check "Memory" "Pressure" "$PASS" "${mem_free}% available"
  elif [ "$mem_free" -gt 20 ] 2>/dev/null; then
    add_check "Memory" "Pressure" "$WARN" "${mem_free}% available — moderate pressure"
  else
    add_check "Memory" "Pressure" "$FAIL" "${mem_free}% available — high pressure"
  fi

  local swap_used
  swap_used=$(sysctl vm.swapusage 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="used") print $(i+2)}' | tr -d 'M.' | head -c4)
  swap_used=${swap_used:-0}
  if [ "$swap_used" -lt 1024 ] 2>/dev/null; then
    add_check "Memory" "Swap" "$PASS" "${swap_used} MB used"
  elif [ "$swap_used" -lt 4096 ] 2>/dev/null; then
    add_check "Memory" "Swap" "$WARN" "${swap_used} MB used"
  else
    add_check "Memory" "Swap" "$FAIL" "${swap_used} MB used — excessive swapping"
  fi
}

check_uptime() {
  echo "  Checking uptime..." >&2

  local days
  days=$(uptime 2>/dev/null | awk -F'up ' '{print $2}' | awk -F',' '{print $1}')
  local day_count
  day_count=$(echo "$days" | grep -o '[0-9]*' | head -1)
  day_count=${day_count:-0}

  if [ "$day_count" -lt 7 ] 2>/dev/null; then
    add_check "System" "Uptime" "$PASS" "$days"
  elif [ "$day_count" -lt 30 ] 2>/dev/null; then
    add_check "System" "Uptime" "$WARN" "$days — consider restarting"
  else
    add_check "System" "Uptime" "$FAIL" "$days — restart recommended"
  fi
}

check_updates() {
  echo "  Checking for updates..." >&2

  if [ "$QUICK" = false ]; then
    local updates
    updates=$(softwareupdate -l 2>&1)
    if echo "$updates" | grep -q "No new software available"; then
      add_check "Updates" "macOS Updates" "$PASS" "Up to date"
    else
      local count
      count=$(echo "$updates" | grep -c "^\*" 2>/dev/null || echo "0")
      add_check "Updates" "macOS Updates" "$WARN" "$count update(s) available"
    fi
  fi

  if command -v brew &>/dev/null; then
    local brew_outdated
    brew_outdated=$(brew outdated 2>/dev/null | wc -l | xargs)
    if [ "$brew_outdated" -eq 0 ] 2>/dev/null; then
      add_check "Updates" "Homebrew" "$PASS" "All packages current"
    else
      add_check "Updates" "Homebrew" "$WARN" "$brew_outdated package(s) outdated — run: brew upgrade"
    fi
  fi
}

check_periodic() {
  echo "  Checking maintenance scripts..." >&2

  for period in daily weekly monthly; do
    local log="/var/log/${period}.out"
    if [ -f "$log" ]; then
      local last_run
      last_run=$(stat -f "%Sm" -t "%Y-%m-%d" "$log" 2>/dev/null || echo "unknown")
      local age_days
      age_days=$(( ($(date +%s) - $(stat -f "%m" "$log" 2>/dev/null || echo "0")) / 86400 ))

      local threshold=3
      [ "$period" = "weekly" ] && threshold=10
      [ "$period" = "monthly" ] && threshold=35

      if [ "$age_days" -lt "$threshold" ] 2>/dev/null; then
        add_check "Maintenance" "Periodic $period" "$PASS" "Last ran: $last_run"
      else
        add_check "Maintenance" "Periodic $period" "$WARN" "Last ran: $last_run (${age_days}d ago) — run: sudo periodic $period"
      fi
    else
      add_check "Maintenance" "Periodic $period" "$WARN" "Never ran — run: sudo periodic $period"
    fi
  done
}

check_time_machine() {
  echo "  Checking Time Machine..." >&2

  local tm_dest
  tm_dest=$(tmutil destinationinfo 2>/dev/null | grep "Name" || echo "")
  if [ -z "$tm_dest" ]; then
    add_check "Backup" "Time Machine" "$WARN" "No backup destination configured"
    return
  fi

  local last_backup
  last_backup=$(tmutil latestbackup 2>/dev/null || echo "")
  if [ -n "$last_backup" ]; then
    local backup_date
    backup_date=$(basename "$last_backup")
    add_check "Backup" "Time Machine" "$PASS" "Last backup: $backup_date"
  else
    add_check "Backup" "Time Machine" "$WARN" "Destination configured but no backup found"
  fi
}

check_security

if [ "$SECURITY_ONLY" = false ]; then
  check_disk
  check_battery
  check_memory
  check_uptime
  check_updates
  check_periodic
  check_time_machine
fi

echo "  Checkup complete." >&2

if [ "$JSON_OUTPUT" = true ]; then
  echo "["
  first=true
  for result in "${RESULTS[@]}"; do
    IFS='|' read -r category check status detail <<< "$result"
    if [ "$first" = true ]; then first=false; else echo ","; fi
    printf '  {"category": "%s", "check": "%s", "status": "%s", "detail": "%s"}' \
      "$category" "$check" "$status" "$detail"
  done
  echo ""
  echo "]"
else
  pass_count=0
  warn_count=0
  fail_count=0

  echo ""
  echo "macOS System Checkup Report"
  echo "==========================="
  echo ""

  current_category=""
  for result in "${RESULTS[@]}"; do
    IFS='|' read -r category check status detail <<< "$result"
    if [ "$category" != "$current_category" ]; then
      [ -n "$current_category" ] && echo ""
      echo "--- $category ---"
      current_category="$category"
    fi

    local icon="?"
    case "$status" in
      "$PASS") icon="[OK]"; pass_count=$((pass_count + 1)) ;;
      "$WARN") icon="[!!]"; warn_count=$((warn_count + 1)) ;;
      "$FAIL") icon="[XX]"; fail_count=$((fail_count + 1)) ;;
      "$INFO") icon="[--]" ;;
    esac

    printf "  %-6s %-30s %s\n" "$icon" "$check" "$detail"
  done

  echo ""
  echo "==========================="
  total=$((pass_count + warn_count + fail_count))
  echo "Score: ${pass_count}/${total} checks passed"
  [ "$warn_count" -gt 0 ] && echo "  ${warn_count} warning(s)"
  [ "$fail_count" -gt 0 ] && echo "  ${fail_count} issue(s) need attention"

  if [ "$fail_count" -eq 0 ] && [ "$warn_count" -le 2 ]; then
    echo ""
    echo "System is in good shape."
  elif [ "$fail_count" -gt 0 ]; then
    echo ""
    echo "Action needed — review items marked [XX] above."
  fi
fi
