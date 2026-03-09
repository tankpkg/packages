# System Health Checks

Hardware and OS-level diagnostics for macOS. Each check includes the command,
how to interpret results, and what to do when something is wrong.

## Disk Health

### APFS Container & Volume Status

```bash
# Quick volume verification (non-destructive, no unmount needed)
diskutil verifyVolume /

# Full APFS container check
diskutil apfs list

# Verify the data volume specifically
diskutil verifyVolume disk3s5  # adjust to your volume identifier

# Run First Aid via Disk Utility CLI (may need recovery mode for boot disk)
diskutil repairVolume /
```

**Interpreting results:**
- "The volume X appears to be OK" — healthy
- "Storage system check exit code is 0" — healthy
- Any "invalid" or "error" message — run First Aid from Recovery Mode
  (restart holding Cmd+R, open Disk Utility, run First Aid on the container)

### SMART Status (SSD/HDD Health)

```bash
# Built-in quick check
diskutil info disk0 | grep "SMART Status"
# Expected: "SMART Status: Verified" — healthy
# "SMART Status: Failing" — drive replacement needed urgently

# Detailed SMART data (requires smartmontools)
# brew install smartmontools
sudo smartctl -a /dev/disk0

# Key SMART attributes for SSDs:
#   Percentage Used: should be under 80%
#   Available Spare: should be above 10%
#   Media Errors: should be 0
#   Data Units Written: informational (wear indicator)
```

**Health thresholds:**

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| SMART Status | Verified | — | Failing |
| Percentage Used | <50% | 50-80% | >80% |
| Available Spare | >50% | 10-50% | <10% |
| Media Errors | 0 | 1-5 | >5 |

### Disk Space

```bash
# Human-readable overview
df -h /

# Accurate with purgeable space
diskutil info / | grep -E "(Total|Free|Available|Purgeable)"

# Percentage used
df -h / | tail -1 | awk '{print $5}'
```

**Thresholds:**
- <70% used — healthy
- 70-85% used — monitor, consider cleanup
- 85-95% used — cleanup needed, performance may degrade
- >95% used — critical, macOS needs ~10% free for swap/updates

## Battery Health (Laptops)

```bash
# Full battery report
system_profiler SPPowerDataType

# Key values via ioreg
ioreg -l -w0 | grep -E '"(MaxCapacity|DesignCapacity|CycleCount|BatteryHealth)"'

# Quick cycle count
system_profiler SPPowerDataType | grep "Cycle Count"

# Battery condition
system_profiler SPPowerDataType | grep "Condition"

# Current charge percentage
pmset -g batt
```

**Interpreting battery health:**

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Condition | Normal | — | Service Recommended / Replace |
| Cycle Count | <500 | 500-800 | >1000 |
| Max Capacity % | >80% | 60-80% | <60% |

Apple considers batteries consumed at 1000 cycles or <80% capacity.

**Battery drain diagnostics:**
```bash
# Check what's preventing sleep
pmset -g assertions

# Check wake reasons (why did it wake from sleep?)
pmset -g log | grep -E "Wake from|DarkWake" | tail -20

# Power-hungry processes
top -l 1 -o cpu -n 10 | tail -11

# Apps preventing sleep
pmset -g assertions | grep -A1 "PreventUserIdleSystemSleep"
```

## Memory Health

```bash
# Memory pressure (the most useful single check)
memory_pressure
# "The system has X% memory available"
# Below 20% = system is under pressure

# Detailed VM stats
vm_stat
# Key: "Pages free" and "Pages speculative" = available
# "Pageouts" > 0 means swapping occurred (not always bad on Apple Silicon)

# Swap usage
sysctl vm.swapusage
# If swap used is > 0 and growing, system is memory-constrained

# Physical RAM
sysctl hw.memsize | awk '{print $2/1073741824 " GB"}'

# Top memory consumers
ps aux --sort=-%mem | head -11
```

**Thresholds:**

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Memory available | >40% | 20-40% | <20% |
| Swap used | 0-1 GB | 1-4 GB | >4 GB |
| Memory pressure | green | yellow | red |

**Swap on Apple Silicon:** Small amounts of swap usage are normal on Apple
Silicon Macs due to unified memory architecture. macOS aggressively uses
swap as a performance optimization, not just as emergency overflow.

## CPU & Thermal

```bash
# Load averages (1, 5, 15 minutes)
sysctl -n vm.loadavg
# Or
uptime

# CPU usage by process (top 10)
ps aux --sort=-%cpu | head -11

# Thermal state (Apple Silicon)
sudo powermetrics --samplers smc -i 1 -n 1 2>/dev/null | grep -i "thermal"

# CPU throttling check
sudo powermetrics --samplers cpu_power -i 1000 -n 1 2>/dev/null | head -30

# Fan speed (Intel Macs, or with iStats)
# brew install iStats (Ruby gem: gem install iStats)
# istats fan speed
```

**Interpreting load averages:**
- Load / number of cores < 1.0 — system is idle
- Load / number of cores = 1.0-2.0 — moderate load
- Load / number of cores > 2.0 — system is overloaded

Get core count: `sysctl -n hw.ncpu`

**Finding runaway processes:**
```bash
# Processes using >50% CPU
ps aux | awk '$3 > 50.0 {print $0}'

# Processes using >1 GB memory
ps aux | awk '$6 > 1048576 {print $0}'

# WindowServer CPU (if high, GPU/display issue)
ps aux | grep WindowServer | grep -v grep
```

## System Uptime & Restart History

```bash
# Current uptime
uptime

# Last reboot
last reboot | head -5

# Last shutdown
last shutdown | head -5

# Kernel panics (crashes)
ls -la /Library/Logs/DiagnosticReports/*.panic 2>/dev/null
ls -la ~/Library/Logs/DiagnosticReports/*.panic 2>/dev/null
```

Macs should be restarted at least every few weeks. Extended uptime (30+ days)
can lead to memory leaks in long-running processes and stale system caches.

## Time Machine Status

```bash
# Backup status
tmutil status

# Last backup date
tmutil latestbackup

# Backup destination info
tmutil destinationinfo

# List local snapshots (consume disk space)
tmutil listlocalsnapshots /

# Machine directory info
tmutil machinedirectory 2>/dev/null
```

**Health checks:**
- Last backup > 24 hours ago — warning (if TM is configured)
- Last backup > 7 days ago — critical
- No backup destination configured — security risk

## Spotlight Index Health

```bash
# Index status
mdutil -s /

# Check if indexing is currently running
mdutil -s / | grep "Indexing"
# "Indexing enabled." + not actively indexing = healthy
# "Indexing disabled." = might need re-enabling

# Rebuild if search is broken (takes 10-60 min)
sudo mdutil -E /

# Check Spotlight CPU usage (should be low when idle)
ps aux | grep mds | grep -v grep
```

**When to rebuild Spotlight:**
- Search returns no results or wrong results
- `mds_stores` consuming high CPU persistently
- After major OS upgrade
