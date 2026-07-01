# Per-App Settings and Configuration Recipes

Sources: mathiasbynens/dotfiles, macos-defaults.com (Yann Bertrand), Scripting OS X (Armin Briegel), Apple man pages

---

## Safari

```bash
# Show the full URL in the address bar (no hiding of http:// or www)
defaults write com.apple.Safari ShowFullURLInSmartSearchField -bool true

# Show status bar at the bottom of the window
defaults write com.apple.Safari ShowStatusBar -bool true

# Enable developer menu and Web Inspector
defaults write com.apple.Safari IncludeInternalDebugMenu -bool true
defaults write com.apple.Safari IncludeDevelopMenu -bool true
defaults write com.apple.Safari WebKitDeveloperExtrasEnabledPreferenceKey -bool true
defaults write com.apple.Safari com.apple.Safari.ContentPageGroupIdentifier.WebKit2DeveloperExtrasEnabled -bool true

# Disable auto-open of downloaded files
defaults write com.apple.Safari AutoOpenSafeDownloads -bool false

# Don't send search queries to Apple
defaults write com.apple.Safari SuppressSearchSuggestions -bool true
defaults write com.apple.Safari UniversalSearchEnabled -bool false

# Disable auto-fill for passwords and credit cards
defaults write com.apple.Safari AutoFillPasswords -bool false
defaults write com.apple.Safari AutoFillCreditCardData -bool false

# Enable "Do Not Track" header
defaults write com.apple.Safari SendDoNotTrackHTTPHeader -bool true

# Warn about fraudulent websites
defaults write com.apple.Safari WarnAboutFraudulentWebsites -bool true

# Block pop-up windows
defaults write com.apple.Safari WebKitJavaScriptCanOpenWindowsAutomatically -bool false

# Set homepage
defaults write com.apple.Safari HomePage -string "about:blank"
```

Restart Safari after applying: `killall Safari`

---

## Terminal

```bash
# Use UTF-8 encoding
defaults write com.apple.terminal StringEncodings -array 4

# Disable line marks (visual marks in output)
defaults write com.apple.Terminal ShowLineMarks -int 0

# Set a theme by name (must exist in Terminal preferences)
defaults write com.apple.Terminal "Default Window Settings" -string "Pro"
defaults write com.apple.Terminal "Startup Window Settings" -string "Pro"
```

To set a custom theme, import the `.terminal` file first:
`open /path/to/theme.terminal` — then set it as default in Terminal > Preferences.

---

## TextEdit

```bash
# Use plain text by default (not RTF)
defaults write com.apple.TextEdit RichText -int 0

# Open and save files in UTF-8
defaults write com.apple.TextEdit PlainTextEncoding -int 4
defaults write com.apple.TextEdit PlainTextEncodingForWrite -int 4

# Disable smart quotes and smart dashes
defaults write com.apple.TextEdit SmartQuotes -bool false
defaults write com.apple.TextEdit SmartDashes -bool false

# Show ruler
defaults write com.apple.TextEdit ShowRuler -bool true
```

---

## Mail

```bash
# Display emails in thread view by default
defaults write com.apple.mail DraftsViewerAttributes -dict-add DisplayInThreadedMode -string yes

# Copy email addresses as "Foo Bar <foo@bar.com>" not plain address
defaults write com.apple.mail AddressesIncludeNameOnPasteboard -bool true

# Disable send and reply animations
defaults write com.apple.mail DisableReplyAnimations -bool true
defaults write com.apple.mail DisableSendAnimations -bool true

# Inline attachments — show as icons instead of inline
defaults write com.apple.mail DisableInlineAttachmentViewing -bool true

# Spell checking: only check before sending (0=always, 1=never, 2=before sending)
defaults write com.apple.mail SpellCheckingBehavior -string "InlineSpellCheckingEnabled"
```

Restart Mail: `killall Mail`

---

## Xcode

```bash
# Show build duration in toolbar
defaults write com.apple.dt.Xcode ShowBuildOperationDuration -bool true

# Trim whitespace from edited lines only (not whole file on save)
defaults write com.apple.dt.Xcode DVTTextEditorTrimTrailingWhitespace -bool true
defaults write com.apple.dt.Xcode DVTTextEditorTrimWhitespaceOnlyLines -bool false

# Show line numbers
defaults write com.apple.dt.Xcode DVTTextShowLineNumbers -bool true

# Open new tabs instead of windows
defaults write com.apple.dt.Xcode IDEDocumentNavigatorOpenMode -string "tab"
```

---

## Activity Monitor

```bash
# Show all processes by default (0=mine, 1=all, 2=hierarchy, 3=other, 4=active)
defaults write com.apple.ActivityMonitor ShowCategory -int 0

# Update frequency in seconds (1=very often, 2=often, 5=normally)
defaults write com.apple.ActivityMonitor UpdatePeriod -int 2

# Show Dock icon as CPU usage graph
defaults write com.apple.ActivityMonitor IconType -int 5
```

---

## Disk Utility

```bash
# Show all partitions in the sidebar
defaults write com.apple.DiskUtility SidebarShowAllDevices -bool true
```

---

## Photos

```bash
# Prevent Photos from opening automatically when a device is connected
defaults -currentHost write com.apple.ImageCapture disableHotPlug -bool true
```

---

## Script Editor

```bash
# Open scripts in plain text view by default
defaults write com.apple.ScriptEditor2 defaultLanguage -string "AppleScript"
defaults write com.apple.ScriptEditor2 showStartupWindow -bool false
```

---

## Common Setup Recipes

### Developer Workstation Recipe

Apply these settings in sequence after a fresh macOS install:

```bash
#!/usr/bin/env bash
# Developer workstation setup
# Run once after a fresh macOS install. Requires logout to complete keyboard settings.

set -euo pipefail

echo "==> Input"
defaults write NSGlobalDomain ApplePressAndHoldEnabled -bool false
defaults write NSGlobalDomain KeyRepeat -int 2
defaults write NSGlobalDomain InitialKeyRepeat -int 15
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false

echo "==> Trackpad"
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

echo "==> Finder"
defaults write com.apple.finder AppleShowAllFiles -bool true
defaults write NSGlobalDomain AppleShowAllExtensions -bool true
defaults write com.apple.finder ShowStatusBar -bool true
defaults write com.apple.finder ShowPathbar -bool true
defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"
defaults write com.apple.finder FXPreferredViewStyle -string "Nlsv"
defaults write com.apple.finder NewWindowTarget -string "PfHm"

echo "==> Dock"
defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock tilesize -int 48
defaults write com.apple.dock show-recents -bool false

echo "==> Screenshots"
defaults write com.apple.screencapture location -string "${HOME}/Desktop"
defaults write com.apple.screencapture type -string "png"
defaults write com.apple.screencapture disable-shadow -bool true

echo "==> Safari"
defaults write com.apple.Safari ShowFullURLInSmartSearchField -bool true
defaults write com.apple.Safari IncludeDevelopMenu -bool true
defaults write com.apple.Safari AutoOpenSafeDownloads -bool false

echo "==> TextEdit"
defaults write com.apple.TextEdit RichText -int 0
defaults write com.apple.TextEdit PlainTextEncoding -int 4
defaults write com.apple.TextEdit PlainTextEncodingForWrite -int 4

echo "==> Restart affected processes"
for app in Dock Finder Mail Safari SystemUIServer; do
  killall "${app}" &>/dev/null || true
done

echo "Done. Log out and back in for keyboard settings to take effect."
```

---

### Minimal Distraction Recipe

For focused writing or general-purpose use:

```bash
# Auto-hide Dock
defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock show-recents -bool false

# Disable notification sounds
defaults write com.apple.systemsound com.apple.sound.uiaudio.enabled -int 0

# Reduce motion
defaults write com.apple.universalaccess reduceMotion -bool true

# Disable autocorrect and smart substitutions
defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false

# Use plain text in TextEdit
defaults write com.apple.TextEdit RichText -int 0

for app in Dock SystemUIServer; do
  killall "${app}" &>/dev/null || true
done
```

---

## Backup and Restore Configuration

### Export Current Settings for a Domain

```bash
# Export a single domain to a plist file
defaults export com.apple.dock ~/dock-backup.plist
defaults export com.apple.finder ~/finder-backup.plist
defaults export NSGlobalDomain ~/global-backup.plist
```

### Restore from Backup

```bash
defaults import com.apple.dock ~/dock-backup.plist
killall Dock
```

### Diff Two Configs

```bash
# Compare current Dock settings to a baseline
diff <(defaults read com.apple.dock) <(plutil -p ~/dock-backup.plist)
```

### Read All Domains at Once

```bash
# List all domains with user-level preferences
defaults domains | tr ',' '\n' | sort

# Read a specific sandboxed app's preferences
defaults read ~/Library/Containers/com.apple.mail/Data/Library/Preferences/com.apple.mail
```

---

## Script Patterns

### Idempotent Settings Function

Wrap each write in a function that checks the current value first:

```bash
set_default() {
  local domain="$1" key="$2" type="$3" value="$4"
  local current
  current=$(defaults read "${domain}" "${key}" 2>/dev/null || echo "__unset__")
  if [[ "${current}" != "${value}" ]]; then
    defaults write "${domain}" "${key}" "${type}" "${value}"
    echo "  set ${domain} ${key} = ${value}"
  else
    echo "  skip ${domain} ${key} (already ${value})"
  fi
}

# Usage
set_default com.apple.dock tilesize -int 48
set_default NSGlobalDomain AppleShowAllExtensions -bool true
```

### Restart Guard

Only restart an app if it is currently running:

```bash
restart_if_running() {
  local app="$1"
  if pgrep -x "${app}" &>/dev/null; then
    killall "${app}"
    echo "  restarted ${app}"
  fi
}

restart_if_running Dock
restart_if_running Finder
restart_if_running SystemUIServer
```

### Apply Changes Summary

| Domain Touched | Restart Needed |
|----------------|----------------|
| `com.apple.dock` | `killall Dock` |
| `com.apple.finder` | `killall Finder` |
| `com.apple.screencapture` | `killall SystemUIServer` |
| `NSGlobalDomain` keyboard | Logout/login |
| `com.apple.Safari` | `killall Safari` |
| `com.apple.mail` | `killall Mail` |
| Hostname / network | No restart needed |
| Power / sleep | No restart needed |

---

## Sandboxed App Preferences

Apps distributed via the Mac App Store store preferences inside their container:

```
~/Library/Containers/<bundle-id>/Data/Library/Preferences/<bundle-id>.plist
```

Read and write these the same way with `defaults`, using the full bundle ID:

```bash
# Read sandboxed Tweetbot preferences
defaults read ~/Library/Containers/com.tapbots.Tweetbot3Mac/Data/Library/Preferences/com.tapbots.Tweetbot3Mac

# Write to a sandboxed app domain
defaults write com.tapbots.Tweetbot3Mac fontSize -int 14
```

Note: Some sandboxed apps ignore `defaults write` due to entitlement restrictions. Check the
plist file directly if writes have no effect.
