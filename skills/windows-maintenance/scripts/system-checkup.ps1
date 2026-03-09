<#
.SYNOPSIS
  Windows System Health Checkup
.DESCRIPTION
  Runs security, disk, memory, updates, and maintenance checks. Produces a scored report.
.PARAMETER Json
  Output as JSON
.PARAMETER Quick
  Skip slow checks (Windows Update scan)
.PARAMETER SecurityOnly
  Only run security posture checks
.EXAMPLE
  .\system-checkup.ps1
  .\system-checkup.ps1 -SecurityOnly
  .\system-checkup.ps1 -Json -Quick
#>
param(
  [switch]$Json,
  [switch]$Quick,
  [switch]$SecurityOnly
)

$ErrorActionPreference = 'SilentlyContinue'
$results = [System.Collections.ArrayList]::new()

function Add-Check([string]$Category, [string]$Check, [string]$Status, [string]$Detail) {
  [void]$results.Add([PSCustomObject]@{
    Category = $Category; Check = $Check; Status = $Status; Detail = $Detail
  })
}

Write-Host "Running Windows system checkup..." -ForegroundColor Cyan

function Test-Security {
  Write-Host "  Checking security posture..."

  try {
    $defender = Get-MpComputerStatus
    if ($defender.AntivirusEnabled -and $defender.RealTimeProtectionEnabled) {
      Add-Check "Security" "Windows Defender" "PASS" "Enabled, real-time protection on"
    } else {
      Add-Check "Security" "Windows Defender" "FAIL" "Disabled or real-time protection off"
    }
    if ($defender.AntivirusSignatureAge -le 3) {
      Add-Check "Security" "Defender Signatures" "PASS" "$($defender.AntivirusSignatureAge) day(s) old"
    } else {
      Add-Check "Security" "Defender Signatures" "WARN" "$($defender.AntivirusSignatureAge) day(s) old — update recommended"
    }
  } catch {
    Add-Check "Security" "Windows Defender" "INFO" "Could not query (may need Admin)"
  }

  $profiles = Get-NetFirewallProfile
  $allEnabled = ($profiles | Where-Object { -not $_.Enabled }).Count -eq 0
  if ($allEnabled) {
    Add-Check "Security" "Firewall" "PASS" "All profiles enabled"
  } else {
    $disabled = ($profiles | Where-Object { -not $_.Enabled }).Name -join ", "
    Add-Check "Security" "Firewall" "WARN" "Disabled profiles: $disabled"
  }

  try {
    $bl = Get-BitLockerVolume -MountPoint C:
    if ($bl.ProtectionStatus -eq 'On') {
      Add-Check "Security" "BitLocker" "PASS" "On ($($bl.EncryptionMethod))"
    } else {
      Add-Check "Security" "BitLocker" "WARN" "Off — enable for disk encryption"
    }
  } catch {
    Add-Check "Security" "BitLocker" "INFO" "Could not query (may need Admin)"
  }

  $uac = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
  if ($uac.EnableLUA -eq 1) {
    Add-Check "Security" "UAC" "PASS" "Enabled"
  } else {
    Add-Check "Security" "UAC" "FAIL" "Disabled — re-enable immediately"
  }

  try {
    $sb = Confirm-SecureBootUEFI
    if ($sb) { Add-Check "Security" "Secure Boot" "PASS" "Enabled" }
    else { Add-Check "Security" "Secure Boot" "WARN" "Disabled" }
  } catch {
    Add-Check "Security" "Secure Boot" "INFO" "Not available (legacy BIOS or unsupported)"
  }

  try {
    $tpm = Get-Tpm
    if ($tpm.TpmPresent -and $tpm.TpmReady) {
      Add-Check "Security" "TPM" "PASS" "Present and ready"
    } elseif ($tpm.TpmPresent) {
      Add-Check "Security" "TPM" "WARN" "Present but not ready"
    } else {
      Add-Check "Security" "TPM" "WARN" "Not detected"
    }
  } catch {
    Add-Check "Security" "TPM" "INFO" "Could not query"
  }

  $rdp = Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server"
  if ($rdp.fDenyTSConnections -eq 1) {
    Add-Check "Security" "Remote Desktop" "PASS" "Disabled"
  } else {
    Add-Check "Security" "Remote Desktop" "WARN" "Enabled — disable if not needed"
  }

  $au = try { (New-Object -ComObject Microsoft.Update.AutoUpdate).Results } catch { $null }
  if ($au) {
    $lastSearch = $au.LastSearchSuccessDate
    $daysSince = ((Get-Date) - $lastSearch).Days
    if ($daysSince -le 7) {
      Add-Check "Security" "Auto Updates" "PASS" "Last check: $($lastSearch.ToString('yyyy-MM-dd'))"
    } else {
      Add-Check "Security" "Auto Updates" "WARN" "Last check $daysSince days ago"
    }
  }
}

function Test-Disk {
  Write-Host "  Checking disk health..."

  try {
    $disk = Get-PhysicalDisk | Select-Object -First 1
    if ($disk.HealthStatus -eq 'Healthy') {
      Add-Check "Disk" "Physical Disk" "PASS" "$($disk.FriendlyName) — Healthy"
    } else {
      Add-Check "Disk" "Physical Disk" "FAIL" "$($disk.FriendlyName) — $($disk.HealthStatus)"
    }
  } catch {
    Add-Check "Disk" "Physical Disk" "INFO" "Could not query SMART (may need Admin)"
  }

  $c = Get-PSDrive C
  $pct = [math]::Round($c.Used / ($c.Used + $c.Free) * 100, 1)
  $freeGB = [math]::Round($c.Free / 1GB, 1)
  if ($pct -lt 70) {
    Add-Check "Disk" "Space Usage" "PASS" "${pct}% used, ${freeGB} GB free"
  } elseif ($pct -lt 85) {
    Add-Check "Disk" "Space Usage" "WARN" "${pct}% used, ${freeGB} GB free — consider cleanup"
  } else {
    Add-Check "Disk" "Space Usage" "FAIL" "${pct}% used, ${freeGB} GB free — cleanup needed"
  }
}

function Test-Memory {
  Write-Host "  Checking memory..."

  $os = Get-CimInstance Win32_OperatingSystem
  $totalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
  $freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
  $pct = [math]::Round((1 - $os.FreePhysicalMemory / $os.TotalVisibleMemorySize) * 100, 1)

  if ($pct -lt 70) {
    Add-Check "Memory" "Usage" "PASS" "${pct}% used (${freeGB} GB free of ${totalGB} GB)"
  } elseif ($pct -lt 85) {
    Add-Check "Memory" "Usage" "WARN" "${pct}% used — moderate pressure"
  } else {
    Add-Check "Memory" "Usage" "FAIL" "${pct}% used — high pressure"
  }

  $pf = Get-CimInstance Win32_PageFileUsage
  if ($pf) {
    $pfPct = if ($pf.AllocatedBaseSize -gt 0) { [math]::Round($pf.CurrentUsage / $pf.AllocatedBaseSize * 100, 0) } else { 0 }
    if ($pfPct -lt 50) {
      Add-Check "Memory" "Page File" "PASS" "${pfPct}% used ($($pf.CurrentUsage) MB of $($pf.AllocatedBaseSize) MB)"
    } else {
      Add-Check "Memory" "Page File" "WARN" "${pfPct}% used — consider more RAM"
    }
  }
}

function Test-Uptime {
  Write-Host "  Checking uptime..."
  $boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
  $uptime = (Get-Date) - $boot
  $uptimeStr = "{0}d {1}h {2}m" -f $uptime.Days, $uptime.Hours, $uptime.Minutes

  if ($uptime.Days -lt 7) {
    Add-Check "System" "Uptime" "PASS" $uptimeStr
  } elseif ($uptime.Days -lt 30) {
    Add-Check "System" "Uptime" "WARN" "$uptimeStr — consider restarting"
  } else {
    Add-Check "System" "Uptime" "FAIL" "$uptimeStr — restart recommended"
  }
}

function Test-Updates {
  if ($Quick) { return }
  Write-Host "  Checking for updates (this may take a moment)..."

  try {
    $session = New-Object -ComObject Microsoft.Update.Session
    $searcher = $session.CreateUpdateSearcher()
    $result = $searcher.Search("IsInstalled=0")
    $count = $result.Updates.Count
    if ($count -eq 0) {
      Add-Check "Updates" "Windows Update" "PASS" "Up to date"
    } else {
      Add-Check "Updates" "Windows Update" "WARN" "$count update(s) available"
    }
  } catch {
    Add-Check "Updates" "Windows Update" "INFO" "Could not check"
  }
}

function Test-EventLogErrors {
  Write-Host "  Checking event logs..."

  $critErrors = Get-WinEvent -FilterHashtable @{
    LogName='System'; Level=1,2; StartTime=(Get-Date).AddHours(-24)
  } -MaxEvents 50 -ErrorAction SilentlyContinue

  $count = ($critErrors | Measure-Object).Count
  if ($count -eq 0) {
    Add-Check "System" "Event Log (24h)" "PASS" "No critical/error events"
  } elseif ($count -lt 10) {
    Add-Check "System" "Event Log (24h)" "WARN" "$count error(s) in last 24h"
  } else {
    Add-Check "System" "Event Log (24h)" "FAIL" "$count error(s) in last 24h — review Event Viewer"
  }
}

function Test-Drivers {
  Write-Host "  Checking drivers..."

  $problemDevices = Get-PnpDevice | Where-Object Status -ne 'OK'
  $count = ($problemDevices | Measure-Object).Count
  if ($count -eq 0) {
    Add-Check "Drivers" "Device Status" "PASS" "All devices OK"
  } else {
    Add-Check "Drivers" "Device Status" "WARN" "$count device(s) with issues"
  }
}

function Test-Battery {
  Write-Host "  Checking battery..."
  $batt = Get-CimInstance Win32_Battery
  if (-not $batt) {
    Add-Check "Battery" "Battery" "INFO" "No battery (desktop PC)"
    return
  }

  $charge = $batt.EstimatedChargeRemaining
  Add-Check "Battery" "Charge" "INFO" "${charge}%"

  if ($batt.DesignCapacity -and $batt.FullChargeCapacity -and $batt.DesignCapacity -gt 0) {
    $healthPct = [math]::Round($batt.FullChargeCapacity / $batt.DesignCapacity * 100, 0)
    if ($healthPct -gt 80) {
      Add-Check "Battery" "Health" "PASS" "${healthPct}% of design capacity"
    } elseif ($healthPct -gt 60) {
      Add-Check "Battery" "Health" "WARN" "${healthPct}% of design capacity"
    } else {
      Add-Check "Battery" "Health" "FAIL" "${healthPct}% of design capacity — consider replacement"
    }
  }
}

Test-Security

if (-not $SecurityOnly) {
  Test-Disk
  Test-Memory
  Test-Uptime
  Test-Battery
  Test-Updates
  Test-EventLogErrors
  Test-Drivers
}

Write-Host "  Checkup complete." -ForegroundColor Green

if ($Json) {
  $results | ConvertTo-Json -Depth 3
} else {
  $passCount = ($results | Where-Object Status -eq 'PASS').Count
  $warnCount = ($results | Where-Object Status -eq 'WARN').Count
  $failCount = ($results | Where-Object Status -eq 'FAIL').Count
  $total = $passCount + $warnCount + $failCount

  Write-Host ""
  Write-Host "Windows System Checkup Report" -ForegroundColor Yellow
  Write-Host "=============================" -ForegroundColor Yellow
  Write-Host ""

  $currentCat = ""
  foreach ($r in $results) {
    if ($r.Category -ne $currentCat) {
      if ($currentCat) { Write-Host "" }
      Write-Host "--- $($r.Category) ---" -ForegroundColor Cyan
      $currentCat = $r.Category
    }
    $icon = switch ($r.Status) {
      "PASS" { "[OK]" }
      "WARN" { "[!!]" }
      "FAIL" { "[XX]" }
      "INFO" { "[--]" }
    }
    $color = switch ($r.Status) {
      "PASS" { "Green" }
      "WARN" { "Yellow" }
      "FAIL" { "Red" }
      "INFO" { "Gray" }
    }
    Write-Host ("  {0,-6} {1,-30} {2}" -f $icon, $r.Check, $r.Detail) -ForegroundColor $color
  }

  Write-Host ""
  Write-Host "=============================" -ForegroundColor Yellow
  Write-Host "Score: ${passCount}/${total} checks passed"
  if ($warnCount -gt 0) { Write-Host "  ${warnCount} warning(s)" -ForegroundColor Yellow }
  if ($failCount -gt 0) { Write-Host "  ${failCount} issue(s) need attention" -ForegroundColor Red }

  if ($failCount -eq 0 -and $warnCount -le 2) {
    Write-Host "`nSystem is in good shape." -ForegroundColor Green
  } elseif ($failCount -gt 0) {
    Write-Host "`nAction needed - review items marked [XX] above." -ForegroundColor Red
  }
}
