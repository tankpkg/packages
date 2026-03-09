---
name: "@tank/macos-maintenance"
description: |
  macOS system health checks, security auditing, and periodic maintenance.
  Diagnoses disk SMART status, battery health, memory pressure, CPU thermals,
  security posture (SIP, Gatekeeper, FileVault, firewall, XProtect), pending
  updates, Time Machine backups, network issues, launch daemon cruft, and
  macOS periodic maintenance scripts. Includes a system checkup script that
  produces a scored health report. Companion to @tank/macos-cleanup (space
  recovery) — this skill focuses on system health, not disk space.

  Trigger phrases: "mac health check", "system checkup", "is my mac ok",
  "mac maintenance", "system maintenance", "mac running slow", "check SIP",
  "check FileVault", "check Gatekeeper", "battery health", "battery cycle",
  "SMART status", "disk health", "memory pressure", "mac security audit",
  "firewall status", "mac diagnostics", "periodic maintenance", "flush DNS",
  "rebuild spotlight", "rebuild launch services", "login items", "startup items",
  "launch agents", "launch daemons", "Wi-Fi issues", "network diagnostics",
  "mac updates", "brew outdated", "softwareupdate", "Time Machine status",
  "mac slow", "fan loud", "mac hot", "system check", "OnyX", "mac tune up",
  "kernel extensions", "system extensions", "mac security check"
---

# macOS Maintenance

System health checks, security auditing, and periodic maintenance for macOS.
Keeps your Mac healthy, secure, and performant — the diagnostic counterpart
to `@tank/macos-cleanup` (which handles disk space recovery).

## Core Philosophy

1. **Diagnose before fixing.** Run the checkup script first. Understand the
   state of the system before changing anything.
2. **Scored health reports.** Every check is PASS/WARN/FAIL. Users see a
   clear scorecard, not a wall of terminal output.
3. **Security by default.** SIP, Gatekeeper, FileVault, and firewall should
   all be enabled. Flag anything that's off.
4. **Non-destructive.** Diagnostics are read-only. Maintenance actions
   (flush DNS, rebuild Spotlight, run periodic scripts) are safe and
   idempotent — running them extra times causes no harm.
5. **Know when to restart.** Many issues resolve with a restart. Check uptime
   and recommend restart when >30 days.

## Quick-Start

### "Is my Mac OK?" / "Run a health check"

```bash
bash scripts/system-checkup.sh
```

The script checks security, disk, battery, memory, uptime, updates,
maintenance scripts, and Time Machine. Outputs a scored report.

Flags:
- `--json` — machine-readable output
- `--quick` — skip slow checks (software updates)
- `--security-only` — only run security posture checks

### "My Mac is running slow"

| Step | Check | Command |
|------|-------|---------|
| 1 | Memory pressure | `memory_pressure` |
| 2 | CPU hogs | `ps aux --sort=-%cpu \| head -11` |
| 3 | Disk space | `df -h /` (needs >10% free) |
| 4 | Swap usage | `sysctl vm.swapusage` |
| 5 | Uptime | `uptime` (restart if >30 days) |
| 6 | Spotlight indexing | `mdutil -s /` |
| 7 | Restart | Fixes most transient issues |

### "Run security audit"

```bash
bash scripts/system-checkup.sh --security-only
```

Or the agent can check manually — see `references/security-posture.md`
for the full scorecard.

### "Run periodic maintenance"

```bash
sudo periodic daily weekly monthly
```

Safe and idempotent. Rotates logs, rebuilds system databases. Should be
done if the Mac sleeps through scheduled run times (common for laptops).

## Decision Trees

### What to Check Based on Symptom

| Symptom | First Check | Then |
|---------|-------------|------|
| Mac is slow | Memory + CPU | Disk space, uptime, Spotlight |
| Fan is loud | CPU usage | Thermal state, runaway processes |
| Battery drains fast | `pmset -g assertions` | Activity Monitor Energy, cycle count |
| Wi-Fi issues | Signal strength (RSSI) | DNS, DHCP renewal |
| Apps crash | Disk space, memory | Crash logs in DiagnosticReports |
| Can't install updates | Disk space (need ~15 GB) | SIP status, time/date |
| Search broken | Spotlight index status | Rebuild: `sudo mdutil -E /` |
| Wrong app opens files | Launch Services DB | Rebuild: `lsregister -kill -r ...` |
| Login is slow | Login items count | Launch agent audit |

### Security Issue Priority

| Issue | Severity | Action |
|-------|----------|--------|
| SIP disabled | Critical | Re-enable from Recovery Mode |
| FileVault off | High | Enable in System Settings |
| Gatekeeper off | High | `sudo spctl --master-enable` |
| Firewall off | Medium | Enable via `socketfilterfw` |
| Auto-updates off | Medium | Enable in System Settings |
| Remote Login on | Low | Disable if not needed |

### Maintenance Frequency

| Task | Frequency | When |
|------|-----------|------|
| macOS updates | Weekly | `softwareupdate -l` |
| Homebrew update | Weekly | `brew update && brew upgrade` |
| Periodic scripts | Auto (or force monthly) | `sudo periodic daily weekly monthly` |
| Security audit | Quarterly | `system-checkup.sh --security-only` |
| Full health check | Quarterly | `system-checkup.sh` |
| SMART disk check | Quarterly | `diskutil info disk0 \| grep SMART` |
| Battery check | Monthly (laptops) | `system_profiler SPPowerDataType` |
| Login items audit | Quarterly | Review ~/Library/LaunchAgents/ |
| Flush DNS | As needed | After VPN/DNS issues |
| Rebuild Spotlight | As needed | When search is broken |

## Common Fix Commands

```bash
# Flush DNS
sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder

# Rebuild Launch Services (fixes "Open With" duplicates)
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user && killall Finder

# Rebuild Spotlight
sudo mdutil -E /

# Force periodic maintenance
sudo periodic daily weekly monthly

# Renew DHCP lease
sudo ipconfig set en0 DHCP

# Enable firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Check for macOS updates
softwareupdate -l
```

## Reference Files

| File | Contents |
|------|----------|
| `references/health-checks.md` | Disk SMART, battery cycle/condition, memory pressure/swap, CPU/thermal, uptime, Time Machine, Spotlight — with commands, thresholds, and fix procedures |
| `references/security-posture.md` | SIP, Gatekeeper, FileVault, firewall, XProtect/MRT, remote access, auto-updates, login items audit, privacy settings — with full security scorecard |
| `references/maintenance-tasks.md` | Periodic scripts, DNS flush, Launch Services rebuild, Spotlight rebuild, NVRAM/SMC reset, launch daemon audit, app updates, maintenance schedule, troubleshooting guides |
| `references/network-diagnostics.md` | Connectivity tests, DNS diagnostics, Wi-Fi signal/channel analysis, port testing, VPN status, proxy settings, network performance, network reset procedure |

## Scripts

| Script | Usage |
|--------|-------|
| `scripts/system-checkup.sh` | Full system health report with scored results. Flags: `--json`, `--quick`, `--security-only` |
