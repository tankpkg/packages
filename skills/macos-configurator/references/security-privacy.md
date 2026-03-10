# Security and Privacy Configuration

Sources: macOS Security Compliance Project (NIST/NASA), mathiasbynens/dotfiles, Apple man pages

This file covers configuring security and privacy settings via CLI. Security auditing and
posture scoring (SIP status, FileVault health checks, Gatekeeper state reporting) is handled
by @tank/macos-maintenance. This file is about changing settings, not evaluating them.

---

## Screen Lock

Require a password immediately when the screensaver activates or the display sleeps.

```bash
# Require password after screensaver or sleep begins
defaults write com.apple.screensaver askForPassword -int 1

# Delay before password is required (seconds); 0 = immediately
defaults write com.apple.screensaver askForPasswordDelay -int 0
```

Set the screensaver idle timeout (in seconds). This writes to the current host's preferences,
which is required for screensaver settings to take effect on the active display.

```bash
# Activate screensaver after 5 minutes of inactivity (300 seconds)
defaults -currentHost write com.apple.screensaver idleTime -int 300

# Disable screensaver (set to 0 — not recommended on shared machines)
defaults -currentHost write com.apple.screensaver idleTime -int 0
```

Apply changes:

```bash
killall cfprefsd
```

The login window can also display a custom message (useful for asset tags or contact info):

```bash
sudo defaults write /Library/Preferences/com.apple.loginwindow LoginwindowText \
  "Property of Acme Corp. If found, call +1-555-0100."
```

---

## Gatekeeper

Gatekeeper controls which applications are allowed to run based on their code-signing status.

```bash
# Enable Gatekeeper (default; restricts to App Store and identified developers)
sudo spctl --master-enable

# Disable Gatekeeper (allows any app to run — use with caution)
sudo spctl --master-disable

# Check current Gatekeeper status
spctl --status
# Output: "assessments enabled" or "assessments disabled"
```

Assess whether a specific application would be allowed to run:

```bash
# Assess an app bundle
spctl --assess --verbose /Applications/SomeApp.app

# Assess a downloaded binary
spctl --assess --verbose /usr/local/bin/sometool
```

Add a specific app to the Gatekeeper allowlist without disabling Gatekeeper globally:

```bash
# Allow a specific app (equivalent to clicking "Open Anyway" in System Settings)
sudo spctl --add /Applications/SomeApp.app

# Allow with a label for later removal
sudo spctl --add --label "MyTrustedApp" /Applications/SomeApp.app

# Remove a labeled rule
sudo spctl --remove --label "MyTrustedApp"
```

Remove the quarantine attribute from a downloaded file (see also: Quarantine section):

```bash
xattr -d com.apple.quarantine /Applications/SomeApp.app
```

Gatekeeper signing states, from most to least restrictive:
- App Store only: enforced via MDM profile; no CLI equivalent
- App Store and identified developers: `spctl --master-enable` (default)
- Anywhere: `spctl --master-disable`

---

## FileVault

FileVault encrypts the startup disk using XTS-AES-128 with a 256-bit key.

```bash
# Check FileVault status
sudo fdesetup status
# Output: "FileVault is On." or "FileVault is Off."

# Check encryption progress (during initial encryption)
sudo fdesetup status -extended

# Enable FileVault (interactive; prompts for a user password and generates a recovery key)
sudo fdesetup enable

# Enable and save the personal recovery key to a file
sudo fdesetup enable -outputplist /private/var/root/fv_recovery.plist

# Disable FileVault (decryption runs in the background; requires restart)
sudo fdesetup disable
```

List users who can unlock the FileVault volume:

```bash
sudo fdesetup list
```

Add an additional user to the FileVault unlock list:

```bash
sudo fdesetup add -usertoadd username
```

Recovery key management: the personal recovery key generated at enable time is the only
out-of-band recovery mechanism for a standalone Mac. Store it in a password manager or
institutional key escrow (Jamf, Mosyle, or a custom MDM) immediately after enabling.
Institutional recovery keys require a certificate and MDM deployment; they cannot be
configured via CLI alone.

---

## Firewall

macOS has an application-layer firewall managed by `socketfilterfw`. This controls per-app
inbound connection rules. For network-level firewall rules (pf) and hostname/DNS configuration,
see `references/network-hostname.md`.

```bash
FIREWALL=/usr/libexec/ApplicationFirewall/socketfilterfw

# Enable the application firewall
sudo "$FIREWALL" --setglobalstate on

# Disable the application firewall
sudo "$FIREWALL" --setglobalstate off

# Check current state
sudo "$FIREWALL" --getglobalstate
```

Stealth mode drops ICMP ping requests and TCP connection attempts on closed ports instead of
sending a rejection response. Recommended for laptops used on untrusted networks.

```bash
# Enable stealth mode
sudo "$FIREWALL" --setstealthmode on

# Disable stealth mode
sudo "$FIREWALL" --setstealthmode off

# Check stealth mode state
sudo "$FIREWALL" --getstealthmode
```

Block all incoming connections (allows only outbound and established connections):

```bash
sudo "$FIREWALL" --setblockall on

# Revert to per-app rules
sudo "$FIREWALL" --setblockall off
```

Per-application rules:

```bash
# Allow an app to accept incoming connections
sudo "$FIREWALL" --add /Applications/SomeApp.app
sudo "$FIREWALL" --unblockapp /Applications/SomeApp.app

# Block an app from accepting incoming connections
sudo "$FIREWALL" --blockapp /Applications/SomeApp.app

# Remove an app from the firewall rules
sudo "$FIREWALL" --remove /Applications/SomeApp.app

# List all firewall rules
sudo "$FIREWALL" --listapps
```

Allow built-in signed software and downloaded signed software automatically:

```bash
sudo "$FIREWALL" --setallowsigned on
sudo "$FIREWALL" --setallowsignedapp on
```

Apply changes without rebooting:

```bash
sudo pkill -HUP socketfilterfw
```

---

## Remote Access

### SSH (Remote Login)

```bash
# Enable SSH (Remote Login)
sudo systemsetup -setremotelogin on

# Disable SSH
sudo systemsetup -setremotelogin off

# Check current state
sudo systemsetup -getremotelogin
```

Restrict SSH access to specific users or groups by editing `/etc/ssh/sshd_config`:

```bash
# Allow only members of the 'staff' group
sudo sh -c 'echo "AllowGroups staff" >> /etc/ssh/sshd_config'

# Reload sshd to apply changes
sudo launchctl kickstart -k system/com.openssh.sshd
```

### Screen Sharing (VNC)

```bash
# Enable Screen Sharing
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.screensharing.plist

# Disable Screen Sharing
sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.screensharing.plist
```

### Remote Apple Events

Remote Apple Events allow AppleScript to target this Mac from other machines on the network.
Disable unless explicitly required.

```bash
# Disable Remote Apple Events
sudo systemsetup -setremoteappleevents off

# Enable Remote Apple Events
sudo systemsetup -setremoteappleevents on

# Check current state
sudo systemsetup -getremoteappleevents
```

### Remote Management (ARD)

```bash
# Disable Apple Remote Desktop agent
sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart \
  -deactivate -stop

# Enable ARD for all users with full access
sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart \
  -activate -configure -access -on -users admin -privs -all -restart -agent -menu
```

---

## Quarantine

macOS tags files downloaded from the internet with a quarantine extended attribute. When a
quarantined file is opened, Gatekeeper checks it and may show a warning dialog.

Disable the quarantine warning dialog for all downloads (not recommended; removes a useful
friction layer):

```bash
defaults write com.apple.LaunchServices LSQuarantine -bool false
```

Re-enable:

```bash
defaults write com.apple.LaunchServices LSQuarantine -bool true
```

Remove the quarantine attribute from a specific file or app:

```bash
xattr -d com.apple.quarantine ~/Downloads/SomeApp.dmg
xattr -rd com.apple.quarantine /Applications/SomeApp.app
```

Change the CrashReporter dialog type. The default `crashreport` dialog prompts the user to
send a crash report. Setting it to `none` suppresses the dialog entirely.

```bash
# Suppress crash report dialogs
defaults write com.apple.CrashReporter DialogType -string "none"

# Restore default behavior
defaults write com.apple.CrashReporter DialogType -string "crashreport"
```

---

## Disk Image Verification

By default, macOS verifies the checksum of disk images before mounting. Skipping verification
speeds up mounting of large images but removes integrity checking.

```bash
# Skip disk image verification (not recommended for untrusted sources)
defaults write com.apple.frameworks.diskimages skip-verify -bool true
defaults write com.apple.frameworks.diskimages skip-verify-locked -bool true
defaults write com.apple.frameworks.diskimages skip-verify-remote -bool true

# Restore verification (default)
defaults write com.apple.frameworks.diskimages skip-verify -bool false
defaults write com.apple.frameworks.diskimages skip-verify-locked -bool false
defaults write com.apple.frameworks.diskimages skip-verify-remote -bool false
```

---

## Automatic Updates

Configure which categories of software updates are downloaded and installed automatically.
These keys write to the system-level SoftwareUpdate domain and require `sudo`.

```bash
# Enable automatic update checks
sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true

# Set check frequency (in days; 1 = daily)
sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate ScheduleFrequency -int 1

# Automatically download updates in the background
sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload -bool true

# Automatically install macOS updates
sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates -bool true

# Automatically install critical security updates (strongly recommended)
sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate CriticalUpdateInstall -bool true

# Automatically install app updates from the App Store
sudo defaults write /Library/Preferences/com.apple.commerce AutoUpdate -bool true
```

Trigger an immediate update check:

```bash
softwareupdate --list
softwareupdate --install --all --restart
```

---

## Handoff and Continuity

Handoff allows activity to be passed between Apple devices signed into the same iCloud account.
Disable it to reduce background network activity and cross-device data sharing.

```bash
# Disable Handoff
defaults write com.apple.coreservices.useractivityd ActivityAdvertisingAllowed -bool false
defaults write com.apple.coreservices.useractivityd ActivityReceivingAllowed -bool false

# Re-enable Handoff
defaults write com.apple.coreservices.useractivityd ActivityAdvertisingAllowed -bool true
defaults write com.apple.coreservices.useractivityd ActivityReceivingAllowed -bool true
```

Apply changes:

```bash
killall useractivityd 2>/dev/null; true
```

---

## Privacy Quick Wins

### Disable Siri Suggestions in Spotlight

Spotlight can send search queries to Apple and third-party sources. Disable the Siri
Suggestions category to keep searches local.

```bash
# Disable Spotlight Siri Suggestions (prevents queries leaving the device)
defaults write com.apple.lookup.shared LookupSuggestionsDisabled -bool true
```

For full Spotlight category management (enable/disable individual categories, rebuild index), see `references/dock-finder-desktop.md`.

### Disable Analytics and Diagnostics Sharing

```bash
# Disable sending diagnostic and usage data to Apple
defaults write com.apple.DiagnosticReportingPrefs AutoSubmit -bool false
defaults write com.apple.DiagnosticReportingPrefs AutoSubmitVersion -int 0

# Disable sharing crash data with app developers
defaults write com.apple.DiagnosticReportingPrefs ThirdPartyDataSubmit -bool false

# Disable Siri analytics
defaults write com.apple.assistant.support "Siri Data Sharing Opt-In Status" -int 2
```

### Disable Personalized Ads

```bash
defaults write com.apple.AdLib allowApplePersonalizedAdvertising -bool false
```

---

## CLI Limitations: TCC and MDM

### TCC-Protected Permissions (No CLI Override)

TCC (Transparency, Consent, and Control) gates sensitive resources. Its database is SIP-protected
— direct modification requires disabling SIP. These permissions require user approval in System
Settings or an MDM PPPC profile: Full Disk Access, Camera, Microphone, Contacts, Calendar,
Reminders, Photos, Location Services, Screen Recording, Accessibility, and Bluetooth.

To pre-approve TCC permissions in managed environments, deploy a PPPC profile via Jamf, Mosyle,
or Kandji. Settings that cannot be configured via CLI at all include App Store enforcement,
FileVault institutional keys, KEXT/SEXT approval, content filtering, Software Update deferral,
passcode policy, and iCloud restrictions — these require an MDM or Apple Configurator 2 profile.
