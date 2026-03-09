# Windows System Health Checks

Hardware and OS-level diagnostics for Windows 10/11. All commands are
PowerShell. Items marked (Admin) require an elevated prompt.

## Disk Health

### S.M.A.R.T. Status

```powershell
# Quick SMART check (Admin)
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, HealthStatus, OperationalStatus, Size

# Detailed reliability counters (Admin)
Get-PhysicalDisk | Get-StorageReliabilityCounter |
  Select-Object DeviceId, Temperature, Wear, ReadErrorsTotal, WriteErrorsTotal, PowerOnHours
```

**Health thresholds:**

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| HealthStatus | Healthy | Warning | Unhealthy |
| Wear (SSD) | <50% | 50-80% | >80% |
| Temperature | <45°C | 45-55°C | >55°C |
| ReadErrorsTotal | 0 | 1-10 | >10 |

### chkdsk (Filesystem Integrity)

```powershell
# Check filesystem (read-only, no fix, Admin)
chkdsk C: /scan

# Full check + fix (requires reboot for boot volume, Admin)
chkdsk C: /f /r

# Schedule check on next boot (Admin)
chkdsk C: /f
# Answer Y to schedule
```

### Drive Optimization

```powershell
# Check optimization status (Admin)
Get-Volume | Where-Object DriveLetter -eq 'C' |
  Optimize-Volume -Analyze -Verbose

# Optimize (TRIM for SSD, defrag for HDD, Admin)
Optimize-Volume -DriveLetter C -Verbose

# Check if SSD TRIM is enabled
fsutil behavior query DisableDeleteNotify
# 0 = TRIM enabled (good), 1 = TRIM disabled
```

SSD: Never defragment. Windows automatically sends TRIM commands.
HDD: Defragmentation helps if fragmentation >10%.

### Disk Space

```powershell
Get-PSDrive C | Select-Object @{N='UsedGB';E={[math]::Round($_.Used/1GB,1)}},
  @{N='FreeGB';E={[math]::Round($_.Free/1GB,1)}},
  @{N='PctUsed';E={[math]::Round($_.Used/($_.Used+$_.Free)*100,1)}}
```

**Thresholds:** <70% healthy, 70-85% monitor, 85-95% cleanup needed, >95% critical.

## System File Integrity

```powershell
# System File Checker — scans and repairs protected system files (Admin)
sfc /scannow
# Takes 5-15 minutes. Reports: no violations, repaired, or could not repair

# If sfc finds unrepairable files, run DISM first (Admin)
DISM /Online /Cleanup-Image /RestoreHealth
# Then re-run sfc /scannow

# Check DISM component store health (Admin)
DISM /Online /Cleanup-Image /CheckHealth    # Quick check
DISM /Online /Cleanup-Image /ScanHealth     # Thorough scan
```

**When to run:**
- After a crash or BSOD
- When Windows features stop working
- After malware removal
- Before/after major updates

## Battery Health (Laptops)

```powershell
# Generate battery report (saves to current directory, Admin)
powercfg /batteryreport /output "$env:USERPROFILE\Desktop\battery-report.html"

# Quick battery info
Get-CimInstance -ClassName Win32_Battery |
  Select-Object Name, EstimatedChargeRemaining, BatteryStatus, DesignCapacity, FullChargeCapacity
```

The HTML battery report includes: design capacity vs full charge capacity,
cycle count, recent usage history, and capacity over time.

**Health thresholds:**

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Full/Design capacity | >80% | 60-80% | <60% |
| Cycle count | <500 | 500-800 | >1000 |

## Memory Health

```powershell
# Memory usage overview
Get-CimInstance Win32_OperatingSystem |
  Select-Object @{N='TotalGB';E={[math]::Round($_.TotalVisibleMemorySize/1MB,1)}},
    @{N='FreeGB';E={[math]::Round($_.FreePhysicalMemory/1MB,1)}},
    @{N='PctUsed';E={[math]::Round((1 - $_.FreePhysicalMemory/$_.TotalVisibleMemorySize)*100,1)}}

# Top memory consumers
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name,
  @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,0)}}, Id

# Page file usage
Get-CimInstance Win32_PageFileUsage |
  Select-Object Name, @{N='AllocatedMB';E={$_.AllocatedBaseSize}},
    @{N='CurrentUsageMB';E={$_.CurrentUsage}},
    @{N='PeakUsageMB';E={$_.PeakUsage}}

# Run Windows Memory Diagnostic (requires reboot)
mdsched.exe
```

**Thresholds:**

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Memory used | <70% | 70-85% | >85% |
| Page file usage | <50% of allocated | 50-80% | >80% |

## CPU & Performance

```powershell
# Current CPU usage
Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 3 |
  ForEach-Object { $_.CounterSamples.CookedValue }

# Top CPU consumers
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name,
  @{N='CPU_Sec';E={[math]::Round($_.CPU,1)}}, Id

# System uptime
(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime |
  Select-Object Days, Hours, Minutes

# Boot time analysis (Admin)
# Check last boot time
Get-CimInstance Win32_OperatingSystem | Select-Object LastBootUpTime
```

## Windows Update Status

```powershell
# Pending updates (may require PSWindowsUpdate module)
# Install-Module PSWindowsUpdate -Force
Get-WindowsUpdate 2>$null

# Built-in: check update history
Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10

# Check for updates via COM (no module needed)
$UpdateSession = New-Object -ComObject Microsoft.Update.Session
$UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
$SearchResult = $UpdateSearcher.Search("IsInstalled=0")
$SearchResult.Updates | Select-Object Title, IsDownloaded

# Last Windows Update
Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 1
```

## System Uptime

```powershell
$uptime = (Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
"{0} days, {1} hours, {2} minutes" -f $uptime.Days, $uptime.Hours, $uptime.Minutes
```

Restart recommended if uptime >30 days.

## Event Log Health (Critical Errors)

```powershell
# Recent critical/error events in System log (last 24 hours)
Get-WinEvent -FilterHashtable @{
  LogName='System'
  Level=1,2  # 1=Critical, 2=Error
  StartTime=(Get-Date).AddHours(-24)
} -MaxEvents 20 -ErrorAction SilentlyContinue |
  Select-Object TimeCreated, LevelDisplayName, ProviderName, Message |
  Format-List

# BSOD / bugcheck events
Get-WinEvent -FilterHashtable @{
  LogName='System'
  ProviderName='Microsoft-Windows-WER-SystemErrorReporting'
} -MaxEvents 5 -ErrorAction SilentlyContinue

# Reliability history summary (launches GUI)
# perfmon /rel
```

## Driver Health

```powershell
# Problem devices
Get-PnpDevice | Where-Object Status -ne 'OK' |
  Select-Object Status, Class, FriendlyName, InstanceId

# All non-Microsoft drivers
Get-CimInstance Win32_PnPSignedDriver |
  Where-Object { $_.DriverProviderName -ne 'Microsoft' -and $_.DriverProviderName } |
  Select-Object DeviceName, DriverProviderName, DriverVersion, DriverDate |
  Sort-Object DriverDate -Descending

# Check for unsigned drivers (Admin)
sigverif  # launches GUI
```

## Backup Status

```powershell
# System Restore points
Get-ComputerRestorePoint | Select-Object -First 5 SequenceNumber, Description, CreationTime

# File History status
Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\FileHistory" -ErrorAction SilentlyContinue

# Check if System Restore is enabled
Get-CimInstance -ClassName Win32_ShadowCopy -ErrorAction SilentlyContinue |
  Select-Object InstallDate, VolumeName
vssadmin list shadows 2>$null
```
