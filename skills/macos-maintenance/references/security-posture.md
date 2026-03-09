# Security Posture Checks

Verify macOS security features are properly configured. These are the same
checks Apple Genius Bar technicians run as part of system diagnostics.

## Quick Security Audit

Run all checks at once for a snapshot of security posture:

```bash
echo "=== SIP ===" && csrutil status
echo "=== Gatekeeper ===" && spctl --status
echo "=== FileVault ===" && fdesetup status
echo "=== Firewall ===" && sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
echo "=== Remote Login ===" && systemsetup -getremotelogin 2>/dev/null
echo "=== Auto Updates ===" && defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled 2>/dev/null
```

## System Integrity Protection (SIP)

```bash
csrutil status
# Expected: "System Integrity Protection status: enabled."
```

SIP prevents modification of protected system files, even by root. It should
always be enabled unless actively debugging kernel extensions.

**If disabled:**
- Restart into Recovery Mode (Cmd+R on Intel, hold power on Apple Silicon)
- Terminal → `csrutil enable`
- Restart

## Gatekeeper

```bash
spctl --status
# Expected: "assessments enabled"

# Check if specific app is allowed
spctl --assess --verbose /Applications/SomeApp.app
```

Gatekeeper verifies that apps are signed by identified developers or from
the App Store. Should always be enabled.

**If disabled:**
```bash
sudo spctl --master-enable
```

## FileVault (Disk Encryption)

```bash
fdesetup status
# Expected: "FileVault is On."

# Check encryption progress (if encrypting)
fdesetup status | grep -i progress
```

FileVault encrypts the entire startup disk. Critical for laptops that could
be lost or stolen. On Apple Silicon, hardware encryption is always on, but
FileVault adds the login-required-to-decrypt layer.

**If disabled:**
- System Settings → Privacy & Security → FileVault → Turn On
- Or: `sudo fdesetup enable` (returns recovery key — save it!)

## Firewall

```bash
# Status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
# Expected: "Firewall is enabled."

# Stealth mode (don't respond to pings/port scans)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode

# List allowed apps
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps

# Block all incoming (except essential services)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getblockall
```

**Recommended settings:**
- Firewall: enabled
- Stealth mode: enabled
- Block all incoming: off (breaks too many things)

**Enable if disabled:**
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on
```

## XProtect & MRT (Malware Protection)

```bash
# XProtect version and last update
system_profiler SPInstallHistoryDataType | grep -A3 "XProtect"

# XProtect definitions version
defaults read /Library/Apple/System/Library/CoreServices/XProtect.bundle/Contents/version.plist 2>/dev/null

# Check XProtect remediator version
defaults read /Library/Apple/System/Library/CoreServices/XProtect.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null

# MRT (Malware Removal Tool) version
defaults read /Library/Apple/System/Library/CoreServices/MRT.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null

# Last XProtect data update
ls -la /Library/Apple/System/Library/CoreServices/XProtect.bundle/
```

XProtect updates silently in the background. If the version is more than
2 weeks old, something may be blocking background updates.

## Remote Access

```bash
# Remote Login (SSH)
systemsetup -getremotelogin 2>/dev/null
# Should be "Off" unless intentionally used

# Screen Sharing
sudo launchctl list | grep screensharing
# Should not be loaded unless intentionally used

# Remote Management (ARD)
sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -agent -print 2>/dev/null
```

**Disable if not needed:**
```bash
sudo systemsetup -setremotelogin off
sudo launchctl disable system/com.apple.screensharing
```

## Automatic Updates

```bash
# Check all auto-update settings
defaults read /Library/Preferences/com.apple.SoftwareUpdate 2>/dev/null

# Key settings:
# AutomaticCheckEnabled = 1 (check for updates)
# AutomaticDownload = 1 (download in background)
# AutomaticallyInstallMacOSUpdates = 1 (install macOS updates)
# CriticalUpdateInstall = 1 (install security updates)
# ConfigDataInstall = 1 (install XProtect/MRT updates)

# Check via softwareupdate
softwareupdate --schedule
```

**Recommended: all auto-update settings should be enabled.**
Security responses (Rapid Security Response) and XProtect updates are
critical and should never be delayed.

## Privacy: Location Services, Analytics, Siri

```bash
# Location Services
sudo defaults read /var/db/locationd/Library/Preferences/ByHost/com.apple.locationd 2>/dev/null | grep -i "enabled"

# Analytics sharing
defaults read /Library/Application\ Support/CrashReporter/DiagnosticMessagesHistory.plist 2>/dev/null | grep -i "autosubmit"

# Siri
defaults read com.apple.assistant.support "Assistant Enabled" 2>/dev/null
```

These are privacy preferences, not security issues. Inform the user of
the current state without recommending changes — privacy is personal.

## Login Items & Background Items

```bash
# List login items (GUI-based, requires osascript)
osascript -e 'tell application "System Events" to get the name of every login item' 2>/dev/null

# Background items (macOS Ventura+)
# System Settings → General → Login Items & Extensions
# No CLI for the new managed background items — direct user to Settings

# Launch Agents (user-level)
ls ~/Library/LaunchAgents/ 2>/dev/null

# Launch Agents (system-wide)
ls /Library/LaunchAgents/ 2>/dev/null

# Launch Daemons (system-wide)
ls /Library/LaunchDaemons/ 2>/dev/null
```

**Audit guidance:**
- Apple items (`com.apple.*`) — always fine
- Known software items (`com.google.*`, `com.microsoft.*`) — typically fine
- Unknown items — investigate: `launchctl print system/<label>`
- Items for uninstalled apps — remove the plist file

## Security Scorecard

Present findings as a simple scorecard:

| Check | Expected | Status |
|-------|----------|--------|
| SIP | Enabled | |
| Gatekeeper | Enabled | |
| FileVault | On | |
| Firewall | Enabled | |
| Stealth Mode | Enabled | |
| Auto Updates | Enabled | |
| XProtect | Current (<14 days) | |
| Remote Login | Off | |
| Screen Sharing | Off | |

Count passing checks. 8-9/9 = excellent, 6-7 = good, <6 = needs attention.
