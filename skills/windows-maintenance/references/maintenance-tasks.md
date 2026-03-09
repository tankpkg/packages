# Windows Maintenance Tasks

Periodic maintenance for Windows 10/11. All commands PowerShell.
(Admin) = requires elevated prompt.

## System File Repair

The most important maintenance operation on Windows.

```powershell
# Step 1: DISM — repair the component store (Admin)
DISM /Online /Cleanup-Image /RestoreHealth
# Takes 10-30 minutes. Downloads repair files from Windows Update.

# Step 2: SFC — repair system files using the (now repaired) store (Admin)
sfc /scannow
# Takes 5-15 minutes.
```

**When to run:**
- After BSOD or system crashes
- When Windows features break
- After malware removal
- Quarterly as preventive maintenance

## Windows Update Maintenance

```powershell
# Check for updates
$UpdateSession = New-Object -ComObject Microsoft.Update.Session
$Searcher = $UpdateSession.CreateUpdateSearcher()
$Results = $Searcher.Search("IsInstalled=0")
$Results.Updates | Select-Object Title, IsDownloaded, IsMandatory

# Force install all pending updates (Admin)
# Using PSWindowsUpdate module:
Install-Module PSWindowsUpdate -Force -Scope CurrentUser
Install-WindowsUpdate -AcceptAll -AutoReboot 2>$null

# Component store cleanup (Admin)
DISM /Online /Cleanup-Image /StartComponentCleanup

# Clear update cache and retry (for stuck updates, Admin)
Stop-Service wuauserv -Force
Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force
Start-Service wuauserv
```

## Drive Optimization

```powershell
# Check current fragmentation/optimization status (Admin)
Optimize-Volume -DriveLetter C -Analyze -Verbose

# Optimize (SSD: TRIM, HDD: defrag, Admin)
Optimize-Volume -DriveLetter C -Verbose

# Schedule (Windows does this automatically, but verify)
Get-ScheduledTask -TaskName "ScheduledDefrag" | Select-Object State, LastRunTime
```

Windows automatically optimizes drives weekly. Only manual intervention
needed if the scheduled task is disabled or if fragmentation is >10% on HDD.

## Startup Programs Audit

```powershell
# List startup programs
Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location, User

# Registry-based startup items
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue
Get-ItemProperty "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue

# Startup folder items
Get-ChildItem "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup" -ErrorAction SilentlyContinue
Get-ChildItem "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup" -ErrorAction SilentlyContinue

# Scheduled tasks that run at logon
Get-ScheduledTask | Where-Object {
  $_.Triggers | Where-Object { $_ -is [Microsoft.PowerShell.ScheduledJob.ScheduledJobTrigger] -or $_.CimClass.CimClassName -eq 'MSFT_TaskLogonTrigger' }
} | Select-Object TaskName, State -ErrorAction SilentlyContinue
```

**Audit guidance:**
- Microsoft items — typically fine
- Known software (Google, Adobe, Spotify) — disable if not needed at startup
- Unknown items — investigate before disabling

## Windows Services Audit

```powershell
# Non-Microsoft services currently running
Get-CimInstance Win32_Service |
  Where-Object { $_.PathName -and $_.PathName -notmatch 'Windows|Microsoft|svchost' } |
  Select-Object Name, DisplayName, State, StartMode, PathName |
  Sort-Object State

# Services set to auto-start that aren't Microsoft
Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -eq 'Running' } |
  Select-Object Name, DisplayName, Status
```

## Scheduled Tasks Audit

```powershell
# Non-Microsoft scheduled tasks
Get-ScheduledTask |
  Where-Object { $_.Author -notmatch 'Microsoft' -and $_.State -ne 'Disabled' } |
  Select-Object TaskName, State, Author,
    @{N='LastRun';E={$_.LastRunTime}},
    @{N='NextRun';E={$_.NextRunTime}} |
  Sort-Object LastRun -Descending
```

## DNS Cache

```powershell
# Flush DNS cache
Clear-DnsClientCache

# Verify
Resolve-DnsName google.com
```

**When to flush:** After changing DNS, VPN issues, sites not loading.

## Network Reset

```powershell
# Reset TCP/IP stack (Admin)
netsh int ip reset

# Reset Winsock (Admin)
netsh winsock reset

# Flush DNS
ipconfig /flushdns

# Release and renew IP
ipconfig /release
ipconfig /renew
```

Requires restart after reset commands.

## Recommended Maintenance Schedule

### Weekly
- Check for Windows updates
- Check Defender signature age
- Review Task Manager startup tab

### Monthly
- Run `sfc /scannow` (Admin)
- Check disk space
- Review Event Viewer for critical errors
- Run `Optimize-Volume` if HDD

### Quarterly
- Full security audit (scorecard)
- DISM + SFC repair cycle
- Component store cleanup
- Check battery report (laptops)
- Audit startup programs and services
- Review scheduled tasks
- Check driver health
- Generate reliability report

### Annually
- Full system backup before OS upgrade
- Review installed applications
- Check BitLocker recovery key access
- Update driver software

## Troubleshooting Common Issues

### PC Running Slow

1. Check RAM: `Get-Process | Sort-Object WorkingSet64 -Desc | Select -First 5`
2. Check CPU: `Get-Counter '\Processor(_Total)\% Processor Time'`
3. Check disk: `Get-PSDrive C` (needs >10% free)
4. Check startup programs (disable unnecessary ones)
5. Check uptime (restart if >30 days)
6. Run `sfc /scannow`

### BSOD Analysis

```powershell
# Recent BSOD events
Get-WinEvent -FilterHashtable @{
  LogName='System'
  ProviderName='Microsoft-Windows-WER-SystemErrorReporting'
} -MaxEvents 5 -ErrorAction SilentlyContinue |
  Select-Object TimeCreated, Message

# Minidump files
Get-ChildItem "C:\Windows\Minidump" -ErrorAction SilentlyContinue |
  Select-Object Name, CreationTime, Length
```

### Windows Update Stuck

```powershell
# 1. Stop update services (Admin)
Stop-Service wuauserv, bits, cryptSvc, msiserver -Force

# 2. Rename update folders (Admin)
Rename-Item "C:\Windows\SoftwareDistribution" "SoftwareDistribution.old" -Force
Rename-Item "C:\Windows\System32\catroot2" "catroot2.old" -Force

# 3. Restart services (Admin)
Start-Service wuauserv, bits, cryptSvc, msiserver

# 4. Re-check for updates
```
