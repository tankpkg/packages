---
name: "@tank/windows-maintenance"
description: |
  Windows 10/11 system health checks, security auditing, and periodic
  maintenance. Diagnoses disk SMART status, system file integrity (sfc/DISM),
  Windows Defender and firewall status, BitLocker encryption, UAC, Secure
  Boot, TPM, battery health, memory pressure, pending updates, event log
  errors, driver health, and startup program audit. Includes a PowerShell
  checkup script that produces a scored health report. Companion to
  @tank/windows-cleanup (space recovery).

  Trigger phrases: "windows health check", "system checkup", "is my pc ok",
  "windows maintenance", "pc running slow", "sfc scannow", "DISM repair",
  "check Defender", "check BitLocker", "check firewall", "battery health",
  "SMART status", "disk health", "memory usage", "security audit",
  "chkdsk", "windows diagnostics", "windows slow", "BSOD", "blue screen",
  "startup programs", "event log errors", "driver issues", "windows update",
  "system file check", "windows tune up", "Secure Boot", "TPM status"
---

# Windows Maintenance

System health checks, security auditing, and periodic maintenance for
Windows 10/11. Keeps your PC healthy, secure, and performant — the
diagnostic counterpart to `@tank/windows-cleanup`.

## Core Philosophy

1. **Diagnose before fixing.** Run the checkup script first.
2. **Scored health reports.** Every check is PASS/WARN/FAIL.
3. **Security by default.** Defender, firewall, BitLocker, UAC, Secure Boot
   should all be enabled. Flag anything that's off.
4. **PowerShell first.** All commands are PowerShell. Mark Admin requirements.
5. **Know when to restart.** Many issues resolve with a restart.

## Quick-Start

### "Is my PC OK?" / "Run a health check"

```powershell
.\scripts\system-checkup.ps1
```

Flags: `-Json`, `-Quick`, `-SecurityOnly`

### "My PC is running slow"

| Step | Check | Command |
|------|-------|---------|
| 1 | Memory | `Get-Process \| Sort WorkingSet64 -Desc \| Select -First 10` |
| 2 | CPU | `Get-Counter '\Processor(_Total)\% Processor Time'` |
| 3 | Disk space | `Get-PSDrive C` (needs >10% free) |
| 4 | Uptime | `(Get-Date) - (gcim Win32_OperatingSystem).LastBootUpTime` |
| 5 | Startup items | `Get-CimInstance Win32_StartupCommand` |
| 6 | System files | `sfc /scannow` (Admin) |
| 7 | Restart | Fixes most transient issues |

### "Run security audit"

```powershell
.\scripts\system-checkup.ps1 -SecurityOnly
```

### "Fix corrupted system files"

```powershell
DISM /Online /Cleanup-Image /RestoreHealth  # Admin, 10-30 min
sfc /scannow                                # Admin, 5-15 min
```

## Decision Trees

### What to Check Based on Symptom

| Symptom | First Check | Then |
|---------|-------------|------|
| PC is slow | Memory + CPU | Disk space, uptime, startup items |
| BSOD/crash | Event logs, sfc/DISM | Drivers, disk health |
| Battery drains fast | Battery report | Startup programs |
| Updates failing | DISM repair | Clear update cache |
| App won't install | Disk space, UAC | sfc /scannow |
| Network issues | DNS, connectivity | Wi-Fi report |

### Security Issue Priority

| Issue | Severity | Fix |
|-------|----------|-----|
| Defender disabled | Critical | Enable in Windows Security |
| UAC disabled | Critical | Registry or Group Policy |
| BitLocker off | High | `Enable-BitLocker` (Admin) |
| Firewall off | High | `Set-NetFirewallProfile -Enabled True` |
| Secure Boot off | Medium | BIOS/UEFI settings |
| Auto-updates off | Medium | Settings > Windows Update |
| Remote Desktop on | Low | Disable if not needed |

### Maintenance Frequency

| Task | Frequency |
|------|-----------|
| Windows Update check | Weekly |
| Defender signature check | Weekly |
| Full health check | Quarterly |
| sfc /scannow + DISM | Quarterly |
| Driver audit | Quarterly |
| Startup programs review | Quarterly |
| Battery report (laptops) | Monthly |
| Event log review | Monthly |
| Component store cleanup | Quarterly |
| Drive optimization check | Monthly |

## Common Fix Commands

```powershell
# System file repair (Admin)
DISM /Online /Cleanup-Image /RestoreHealth
sfc /scannow

# Flush DNS
Clear-DnsClientCache

# Network reset (Admin)
netsh int ip reset
netsh winsock reset

# Force Windows Update check
(New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher().Search("IsInstalled=0")

# Enable firewall (Admin)
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# Generate battery report (Admin)
powercfg /batteryreport /output "$env:USERPROFILE\Desktop\battery-report.html"
```

## Reference Files

| File | Contents |
|------|----------|
| `references/health-checks.md` | Disk SMART, chkdsk, battery report, memory/page file, CPU, sfc/DISM, event logs, driver health, uptime, backup status |
| `references/security-posture.md` | Defender, firewall, BitLocker, UAC, Secure Boot, TPM, auto-updates, remote access, security scorecard |
| `references/maintenance-tasks.md` | sfc/DISM repair, Windows Update maintenance, drive optimization, startup audit, services audit, DNS flush, network reset, troubleshooting guides |
| `references/network-diagnostics.md` | Connectivity tests, DNS diagnostics, Wi-Fi report, port/firewall testing, VPN status, network reset |

## Scripts

| Script | Usage |
|--------|-------|
| `scripts/system-checkup.ps1` | Full health report with scored results. Flags: `-Json`, `-Quick`, `-SecurityOnly` |
