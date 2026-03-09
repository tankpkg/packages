# Windows Security Posture Checks

Verify Windows 10/11 security features are properly configured. All commands
PowerShell. (Admin) = requires elevated prompt.

## Quick Security Audit

```powershell
Write-Host "=== Windows Defender ===" -ForegroundColor Cyan
Get-MpComputerStatus | Select-Object AMRunningMode, AntivirusEnabled, RealTimeProtectionEnabled, AntivirusSignatureAge

Write-Host "`n=== Firewall ===" -ForegroundColor Cyan
Get-NetFirewallProfile | Select-Object Name, Enabled

Write-Host "`n=== BitLocker ===" -ForegroundColor Cyan
Get-BitLockerVolume -MountPoint C: -ErrorAction SilentlyContinue | Select-Object MountPoint, ProtectionStatus, EncryptionPercentage

Write-Host "`n=== UAC ===" -ForegroundColor Cyan
$uac = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
"UAC Enabled: $($uac.EnableLUA -eq 1)"

Write-Host "`n=== Secure Boot ===" -ForegroundColor Cyan
Confirm-SecureBootUEFI 2>$null

Write-Host "`n=== TPM ===" -ForegroundColor Cyan
Get-Tpm | Select-Object TpmPresent, TpmReady, TpmEnabled
```

## Windows Defender

```powershell
# Full status (Admin)
Get-MpComputerStatus | Select-Object *

# Key checks
Get-MpComputerStatus | Select-Object `
  AntivirusEnabled,
  RealTimeProtectionEnabled,
  IoavProtectionEnabled,
  AntispywareEnabled,
  BehaviorMonitorEnabled,
  AntivirusSignatureAge,
  AntivirusSignatureLastUpdated,
  QuickScanAge

# Check if definitions are current
$status = Get-MpComputerStatus
if ($status.AntivirusSignatureAge -gt 3) {
  Write-Warning "Defender signatures are $($status.AntivirusSignatureAge) days old. Update recommended."
  # Update-MpSignature  # (Admin)
}

# Run quick scan (Admin)
Start-MpScan -ScanType QuickScan

# Check threat history
Get-MpThreatDetection | Select-Object -First 5 ThreatName, DomainUser, ProcessName, InitialDetectionTime
```

**Health checks:**
- AntivirusEnabled: should be True
- RealTimeProtectionEnabled: should be True
- AntivirusSignatureAge: should be <3 days
- QuickScanAge: should be <7 days

## Windows Firewall

```powershell
# Profile status
Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction

# All three profiles should be enabled (Domain, Private, Public)

# Enable all profiles (Admin)
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# List recent blocked connections (Admin)
Get-WinEvent -FilterHashtable @{
  LogName='Security'
  Id=5157  # Connection blocked
} -MaxEvents 10 -ErrorAction SilentlyContinue |
  Select-Object TimeCreated, Message
```

## BitLocker (Disk Encryption)

```powershell
# Check encryption status (Admin)
Get-BitLockerVolume | Select-Object MountPoint, VolumeStatus, ProtectionStatus,
  EncryptionPercentage, EncryptionMethod, KeyProtector

# Check if recovery key is backed up
(Get-BitLockerVolume -MountPoint C:).KeyProtector | Select-Object KeyProtectorType, KeyProtectorId
```

**Expected state:**
- ProtectionStatus: On
- VolumeStatus: FullyEncrypted
- EncryptionMethod: XtsAes256 (preferred) or XtsAes128

**If disabled:**
```powershell
# Enable BitLocker (Admin, requires TPM)
Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 -RecoveryPasswordProtector
# Save the recovery key!
```

## UAC (User Account Control)

```powershell
$uac = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
[PSCustomObject]@{
  UACEnabled = $uac.EnableLUA -eq 1
  ConsentPromptBehaviorAdmin = switch($uac.ConsentPromptBehaviorAdmin) {
    0 { "Elevate without prompting (NOT RECOMMENDED)" }
    1 { "Prompt for credentials on secure desktop" }
    2 { "Prompt for consent on secure desktop" }
    3 { "Prompt for credentials" }
    4 { "Prompt for consent" }
    5 { "Prompt for consent for non-Windows binaries (default)" }
  }
}
```

UAC should always be enabled. Level 5 is the Windows default.

## Secure Boot & TPM

```powershell
# Secure Boot
try { $sb = Confirm-SecureBootUEFI; "Secure Boot: $sb" }
catch { "Secure Boot: Not supported or unavailable" }

# TPM status (Admin)
Get-Tpm | Select-Object TpmPresent, TpmReady, TpmEnabled, TpmActivated, ManufacturerVersion

# TPM version (need 2.0 for Windows 11)
Get-CimInstance -Namespace "root\cimv2\Security\MicrosoftTpm" -ClassName Win32_Tpm -ErrorAction SilentlyContinue |
  Select-Object SpecVersion
```

## Windows Update Settings

```powershell
# Check if auto-updates are enabled
$au = (New-Object -ComObject Microsoft.Update.AutoUpdate).Results
"Last search: $($au.LastSearchSuccessDate)"
"Last install: $($au.LastInstallationSuccessDate)"

# Active hours
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" -ErrorAction SilentlyContinue |
  Select-Object ActiveHoursStart, ActiveHoursEnd

# Pause status
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" -ErrorAction SilentlyContinue |
  Select-Object PauseUpdatesExpiryTime
```

## Remote Access

```powershell
# Remote Desktop
$rdp = Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server"
"Remote Desktop: $(if($rdp.fDenyTSConnections -eq 0){'Enabled (WARN)'}else{'Disabled (Good)'})"

# SSH Server
Get-Service sshd -ErrorAction SilentlyContinue | Select-Object Status, StartType

# WinRM (remote management)
Get-Service WinRM | Select-Object Status, StartType
```

**Recommendation:** Remote Desktop, SSH, and WinRM should be disabled unless
intentionally used.

## Security Scorecard

| Check | Expected | Status |
|-------|----------|--------|
| Windows Defender | Enabled + Real-time | |
| Defender signatures | <3 days old | |
| Firewall (all profiles) | Enabled | |
| BitLocker | On (FullyEncrypted) | |
| UAC | Enabled (level 5) | |
| Secure Boot | Enabled | |
| TPM | Present + Ready | |
| Auto Updates | Enabled | |
| Remote Desktop | Disabled | |

Score 8-9/9 = excellent, 6-7 = good, <6 = needs attention.
