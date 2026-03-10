# macOS Configuration Tools

Sources: mathiasbynens/dotfiles, macos-defaults.com (Yann Bertrand), Apple man pages, Scripting OS X (Armin Briegel)

---

## `defaults` — Preference Domains

Reads and writes XML property lists in `~/Library/Preferences/`. Each domain
maps to a bundle identifier (`com.apple.dock`) or `NSGlobalDomain` for
system-wide settings.

```bash
defaults read com.apple.dock              # entire domain
defaults read com.apple.dock tilesize     # single key
defaults read-type com.apple.dock tilesize
defaults write com.apple.dock tilesize -int 48
defaults delete com.apple.dock tilesize   # remove key
defaults domains                          # list all domains
defaults find tilesize                    # search across all domains
```

### Value Types

| Flag | Type | Example |
|------|------|---------|
| `-string` | String | `"left"` |
| `-int` | Integer | `48` |
| `-float` | Float | `0.5` |
| `-bool` | Boolean | `true` / `false` |
| `-array` | Array (replaces entire array) | `"item1" "item2"` |
| `-array-add` | Array (appends) | `"item3"` |
| `-dict` | Dictionary (replaces) | `key1 value1 key2 value2` |
| `-dict-add` | Dictionary (merges) | `key1 value1` |

### NSGlobalDomain

`NSGlobalDomain` (aliases: `-g`, `-globalDomain`) stores preferences that
apply across all applications — text behavior, UI appearance, input settings.

```bash
defaults write NSGlobalDomain AppleShowAllExtensions -bool true
defaults write -g AppleShowAllExtensions -bool true   # equivalent
defaults read NSGlobalDomain
```

### `-currentHost` Flag

Some preferences are stored per-host rather than per-user. Trackpad and mouse
settings frequently use this tier. Omitting `-currentHost` silently writes to
the wrong location.

```bash
defaults -currentHost read com.apple.driver.AppleBluetoothMultitouch.trackpad
defaults -currentHost write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
```

### Sandboxed App Preferences

Mac App Store apps store preferences under
`~/Library/Containers/<bundle-id>/Data/Library/Preferences/`. The `defaults`
command resolves the bundle ID automatically, but PlistBuddy and direct file
access require the full container path.

```bash
defaults read com.apple.Safari   # resolves to container automatically
# If that fails, target the container explicitly:
defaults read ~/Library/Containers/com.apple.Safari/Data/Library/Preferences/com.apple.Safari
```

---

## `PlistBuddy` — Nested Plist Editing

`/usr/libexec/PlistBuddy` operates directly on plist files and handles nested
dicts and arrays that `defaults` cannot express in a single command.

```bash
# Read / set / add / delete
/usr/libexec/PlistBuddy -c "Print :autohide" ~/Library/Preferences/com.apple.dock.plist
/usr/libexec/PlistBuddy -c "Set :tilesize 48" ~/Library/Preferences/com.apple.dock.plist
/usr/libexec/PlistBuddy -c "Add :mykey string myvalue" ~/Library/Preferences/com.apple.dock.plist
/usr/libexec/PlistBuddy -c "Delete :mykey" ~/Library/Preferences/com.apple.dock.plist

# Navigate nested structures with : separator
/usr/libexec/PlistBuddy -c "Print :persistent-apps:0:tile-data:file-label" \
  ~/Library/Preferences/com.apple.dock.plist

# Merge a plist fragment into a destination
/usr/libexec/PlistBuddy -c "Merge /path/to/source.plist" /path/to/destination.plist
```

### When to Use PlistBuddy vs defaults

| Situation | Tool |
|-----------|------|
| Simple key read/write | `defaults` |
| Searching across domains | `defaults find` |
| Modifying a specific array element | `PlistBuddy` |
| Adding a key to a nested dict | `PlistBuddy` |
| Merging plist fragments | `PlistBuddy` |
| Scripting with reliable exit codes | `PlistBuddy` (exits non-zero on failure) |

---

## `systemsetup` — System-Level Configuration

Configures sleep timers, time zone, remote access, and network time. Most
operations require `sudo`. On Apple Silicon with SIP enabled, some subcommands
silently fail — always verify with the corresponding read command.

```bash
sudo systemsetup -printSettings              # list all available settings
sudo systemsetup -setsleep 30               # computer sleep (minutes; 0 = never)
sudo systemsetup -setdisplaysleep 10
sudo systemsetup -settimezone "America/New_York"
sudo systemsetup -listtimezones
sudo systemsetup -setnetworktimeserver "time.apple.com"
sudo systemsetup -setusingnetworktime on
sudo systemsetup -setremotelogin on         # enable SSH
sudo systemsetup -setwakeonnetworkaccess on
```

---

## `scutil` — System Configuration Utility

Reads and writes the System Configuration framework's dynamic store. Use it
for hostname management and DNS/proxy diagnostics.

### Hostname Variants

macOS maintains three distinct hostname values. Set all three consistently
when renaming a machine.

| Key | Purpose |
|-----|---------|
| `ComputerName` | Friendly name shown in Finder and Sharing preferences |
| `HostName` | UNIX hostname used by the shell prompt and SSH |
| `LocalHostName` | Bonjour/mDNS name (`.local` suffix); DNS-label safe only |

```bash
scutil --get ComputerName
scutil --get HostName
scutil --get LocalHostName

sudo scutil --set ComputerName "Elad's MacBook Pro"
sudo scutil --set HostName "eladmbp"
sudo scutil --set LocalHostName "eladmbp"   # lowercase, hyphens only
```

### Diagnostics and VPN

```bash
scutil --dns          # current DNS configuration
scutil --proxy        # current proxy configuration
scutil --nwi          # network interface info and reachability

scutil --nc list                  # list VPN configurations
scutil --nc start "My VPN"
scutil --nc stop "My VPN"
scutil --nc status "My VPN"
```

---

## `launchctl` — Service Management

Manages LaunchDaemons (system-wide, root) and LaunchAgents (per-user). The
modern `bootstrap`/`bootout` syntax replaced `load`/`unload` in macOS 10.10;
both still work.

### Plist Locations

| Location | Scope | Runs As |
|----------|-------|---------|
| `/Library/LaunchDaemons/` | System-wide | root |
| `/Library/LaunchAgents/` | All users | logged-in user |
| `~/Library/LaunchAgents/` | Current user | current user |
| `/System/Library/LaunchDaemons/` | Apple system services | root |

### Modern Syntax (Preferred)

```bash
# User agents — use gui/<uid> domain
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.agent.plist
launchctl bootout  gui/$(id -u) ~/Library/LaunchAgents/com.example.agent.plist
launchctl kickstart gui/$(id -u)/com.example.agent        # start immediately
launchctl kickstart -k gui/$(id -u)/com.example.agent     # force restart

# System daemons
sudo launchctl bootstrap system /Library/LaunchDaemons/com.example.daemon.plist
sudo launchctl bootout  system /Library/LaunchDaemons/com.example.daemon.plist
sudo launchctl enable  system/com.example.daemon
sudo launchctl disable system/com.example.daemon

# Inspect
launchctl list | grep com.example
launchctl print gui/$(id -u)/com.example.agent
```

---

## `hidutil` — Modifier Key Remapping

Remaps HID keyboard keys at the driver level. Changes apply immediately but
reset on reboot. Persist with a LaunchAgent.

### Key Code Reference

| Key | HID Code | Key | HID Code |
|-----|----------|-----|----------|
| Caps Lock | `0x700000039` | Left Control | `0x7000000E0` |
| Left Option | `0x7000000E2` | Left Command | `0x7000000E3` |
| Right Option | `0x7000000E6` | Right Command | `0x7000000E7` |
| Escape | `0x700000029` | F18 | `0x700000069` |

```bash
# Remap Caps Lock to Escape
hidutil property --set '{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc":0x700000039,"HIDKeyboardModifierMappingDst":0x700000029}]}'

# Multiple remappings
hidutil property --set '{"UserKeyMapping":[
  {"HIDKeyboardModifierMappingSrc":0x700000039,"HIDKeyboardModifierMappingDst":0x700000029},
  {"HIDKeyboardModifierMappingSrc":0x7000000E0,"HIDKeyboardModifierMappingDst":0x700000039}
]}'

hidutil property --set '{"UserKeyMapping":[]}'   # clear all
hidutil property --get "UserKeyMapping"           # read current
```

Use https://hidutil-generator.netlify.app/ to generate JSON for complex
configurations. To persist, create `~/Library/LaunchAgents/com.local.hidutil.plist`
with `ProgramArguments` calling `hidutil property --set '...'` and `RunAtLoad = true`,
then load with `launchctl bootstrap gui/$(id -u) <plist-path>`.

---

## Discovering Preference Keys

When a setting exists in System Settings but has no documented `defaults` key,
use the diff technique to find it.

### Diff Technique

```bash
# 1. Snapshot before
defaults read com.apple.dock > /tmp/dock-before.txt

# 2. Change the setting in System Settings

# 3. Snapshot after and compare
defaults read com.apple.dock > /tmp/dock-after.txt
diff /tmp/dock-before.txt /tmp/dock-after.txt
```

For system-wide settings, diff `NSGlobalDomain`. For input device settings,
also diff with `-currentHost`.

### Searching and Inspecting

```bash
defaults find autohide                    # search key name across all domains
defaults read com.apple.finder            # all keys in a domain
plutil -p ~/Library/Preferences/com.apple.finder.plist   # human-readable XML

# Check if a key exists
defaults read com.apple.finder ShowPathbar 2>/dev/null && echo "exists" || echo "not set"

# Find bundle ID from app name
osascript -e 'id of app "Finder"'
mdls -name kMDItemCFBundleIdentifier /System/Library/CoreServices/Finder.app
```

---

## Applying Changes

Most `defaults write` commands require killing the affected process before
taking effect. macOS restarts system processes automatically.

### Process Restart Patterns

| Domain | Command |
|--------|---------|
| `com.apple.dock` | `killall Dock` |
| `com.apple.finder` | `killall Finder` |
| `com.apple.SystemUIServer` | `killall SystemUIServer` |
| `com.apple.controlcenter` | `killall ControlCenter` |
| `NSGlobalDomain` (UI appearance) | `killall SystemUIServer` |
| `NSGlobalDomain` (input/keyboard) | Log out and back in |
| `com.apple.screencapture` | `killall SystemUIServer` |
| Third-party apps | Quit and relaunch the app |

### Flushing the Preference Cache

`cfprefsd` caches preferences in memory. If killing the target process is
insufficient, flush the cache:

```bash
killall cfprefsd              # user preferences
sudo killall cfprefsd         # system preferences (written with sudo)
```

Settings that require logout or restart (not just process kill):
- `KeyRepeat` and `InitialKeyRepeat`
- Login window settings in `/Library/Preferences/com.apple.loginwindow`
- Shell environment variables set via `launchctl setenv`

---

## Gotchas and Version Differences

### cfprefsd Caching

`defaults write` updates the plist on disk immediately, but the running
process reads from `cfprefsd`'s in-memory cache. Always kill the target
process after writing. If the setting still does not apply, kill `cfprefsd`.

### Sandboxed Apps

If `defaults write` appears to succeed but the app ignores the change, the
app is likely sandboxed. Verify with `codesign -dv --entitlements - /path/to/App.app`
and look for `com.apple.security.app-sandbox`. Target the container path
explicitly or use the app's own preferences UI.

### SIP Restrictions

SIP blocks writes to `/System/Library/Preferences/` even as root. All
legitimate user-facing configuration lives in `/Library/` or `~/Library/`,
which SIP does not protect. Never disable SIP to work around this.

### TCC Requirements

Terminal may need Full Disk Access (System Settings → Privacy & Security →
Full Disk Access) to read sandboxed container directories. Without it, reads
silently return empty results rather than an error.

### `-currentHost` vs Global Domain

Input device domains (`com.apple.driver.*`, `com.apple.AppleMultitouchTrackpad`)
use the host-specific store. Writing without `-currentHost` silently targets
the wrong location.

```bash
# Wrong — no effect on trackpad behavior
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true

# Correct
defaults -currentHost write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
```

### Boolean Storage

`defaults` accepts `true`/`false`, `yes`/`no`, and `1`/`0`. When reading, it
returns `1` or `0`. Some keys documented as booleans are stored as integers —
if `defaults read-type` returns `integer`, write with `-int 1` or `-int 0`.

### Version Differences

| Change | Scope | Notes |
|--------|-------|-------|
| `launchctl load/unload` deprecated | macOS 10.10+ | Use `bootstrap`/`bootout`; old syntax still works |
| `airport` CLI removed | macOS 15 Sequoia | Use `networksetup` or `wdutil` |
| `systemsetup` silent failures | Apple Silicon + SIP | Verify every write with a read |
| Privacy TCC expanded | macOS 14 Sonoma | More domains require explicit user consent |
| Sandboxed container path enforcement | macOS 12+ | Bundle ID resolution stricter for some apps |
