# Power, Display, and Sound Configuration

Sources: Apple pmset(1) man page, mathiasbynens/dotfiles, macos-defaults.com (Yann Bertrand)

---

## Power Management (pmset)

Most `pmset` writes require `sudo`. Scope flags: `-a` all sources, `-b` battery, `-c` AC charger, `-u` UPS.

### Reading Current State

```bash
pmset -g              # full current settings
pmset -g cap          # hardware capabilities
pmset -g assertions   # active power assertions (what prevents sleep)
pmset -g batt         # battery status and charge level
pmset -g sched        # scheduled power events
```

### Sleep Timers

```bash
sudo pmset -a sleep 30          # computer sleep after 30 min (0 = never)
sudo pmset -b sleep 10          # shorter on battery
sudo pmset -c sleep 0           # never sleep on AC
sudo pmset -a displaysleep 10   # display sleep after 10 min
sudo pmset -a disksleep 10      # disk sleep after 10 min
```

### Wake Behavior

```bash
sudo pmset -a womp 1            # wake on network access (Magic Packet)
sudo pmset -a lidwake 1         # wake when lid opens
sudo pmset -a ttyskeepawake 1   # keep awake when TTY is active
sudo pmset -a proximitywake 0   # disable wake from nearby Apple devices
sudo pmset -a autorestart 1     # restart automatically after power failure
```

### Power Nap

Allows background tasks (Mail, iCloud, Time Machine) during sleep. Drains battery on laptops.

```bash
sudo pmset -c powernap 1   # enable on AC
sudo pmset -b powernap 0   # disable on battery
```

### Hibernation Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `0` | RAM stays powered; no disk image | Desktops — fastest wake, no protection against power loss |
| `3` | RAM powered; disk image written as backup | Laptops default — safe sleep with fast wake |
| `25` | RAM powered off; disk image only | Maximum battery savings; slow wake |

```bash
pmset -g | grep hibernatemode       # read current mode
sudo pmset -a hibernatemode 0       # desktops
sudo pmset -a hibernatemode 3       # laptops (default)
sudo pmset -a hibernatemode 25      # deep hibernation
```

The hibernation image lives at `/var/vm/sleepimage` and must be as large as installed RAM.

### Standby

Transitions a sleeping Mac to a lower-power state after a delay.

```bash
sudo pmset -a standby 1
sudo pmset -a standbydelay 10800          # 3 hours (default)
sudo pmset -b standbydelayhigh 86400      # 24 h on battery above 50% charge
sudo pmset -b standbydelaylow 10800       # 3 h on battery below 50% charge
```

### Caffeinate — Prevent Sleep Temporarily

Creates a power assertion without permanently changing settings.

```bash
caffeinate -d              # prevent display sleep (Ctrl-C to stop)
caffeinate -i              # prevent system idle sleep
caffeinate -t 3600         # prevent sleep for 1 hour
caffeinate -s make all     # keep awake while command runs (AC only)
caffeinate -di             # prevent display and system sleep together
```

Assertion flags: `-d` display, `-i` system idle, `-m` disk idle, `-s` system sleep (AC only), `-u` user idle.

---

## Scheduled Power Events

### One-Time Events

```bash
sudo pmset schedule wake     "MM/DD/YY HH:MM:SS"
sudo pmset schedule sleep    "MM/DD/YY HH:MM:SS"
sudo pmset schedule poweron  "MM/DD/YY HH:MM:SS"
sudo pmset schedule shutdown "MM/DD/YY HH:MM:SS"
```

### Repeating Schedule

```bash
# Wake weekdays at 8 AM, sleep every day at 11 PM
sudo pmset repeat wake MTWRF 08:00:00 sleep SMTWRFS 23:00:00

# Cancel all repeating schedules
sudo pmset repeat cancel
```

Day codes: `S` Sun, `M` Mon, `T` Tue, `W` Wed, `R` Thu, `F` Fri, `A` Sat.

---

## Display

### Dark Mode

```bash
# Enable (takes effect at next login)
defaults write NSGlobalDomain AppleInterfaceStyle -string "Dark"

# Disable
defaults delete NSGlobalDomain AppleInterfaceStyle

# Toggle immediately via osascript (no logout required)
osascript -e 'tell app "System Events" to tell appearance preferences to set dark mode to not dark mode'
```

### Accent Color

```bash
defaults write NSGlobalDomain AppleAccentColor -int <value>
defaults delete NSGlobalDomain AppleAccentColor   # revert to Blue (default)
```

| Value | Color | Value | Color |
|-------|-------|-------|-------|
| `-1` | Graphite | `3` | Green |
| `0` | Red | `4` | Blue (default) |
| `1` | Orange | `5` | Purple |
| `2` | Yellow | `6` | Pink |

### Highlight Color

```bash
# Blue (default)
defaults write NSGlobalDomain AppleHighlightColor -string "0.698039 0.843137 1.000000 Blue"
# Green
defaults write NSGlobalDomain AppleHighlightColor -string "0.764706 0.976471 0.568627 Green"
# Graphite
defaults write NSGlobalDomain AppleHighlightColor -string "0.847059 0.847059 0.862745 Graphite"
defaults delete NSGlobalDomain AppleHighlightColor   # revert to default
```

### Font Smoothing

```bash
# 0 = disabled, 1 = light, 2 = medium, 3 = heavy
defaults write NSGlobalDomain AppleFontSmoothing -int 1
defaults delete NSGlobalDomain AppleFontSmoothing   # revert to system default
```

Apple disabled subpixel antialiasing by default in Mojave. On non-Retina displays, value `1` or `2` improves readability.

### Scrollbar Behavior

```bash
defaults write NSGlobalDomain AppleShowScrollBars -string "Always"
defaults write NSGlobalDomain AppleShowScrollBars -string "WhenScrolling"
defaults write NSGlobalDomain AppleShowScrollBars -string "Automatic"   # default
```

### Window and Animation Settings

```bash
# Faster window resize animation (default 0.2)
defaults write NSGlobalDomain NSWindowResizeTime -float 0.001

# Disable smooth scrolling
defaults write NSGlobalDomain NSScrollAnimationEnabled -bool false

# Disable animated focus ring
defaults write NSGlobalDomain NSUseAnimatedFocusRing -bool false
```

### HiDPI Modes

Enable additional HiDPI resolutions not shown by default in System Settings:

```bash
sudo defaults write /Library/Preferences/com.apple.windowserver DisplayResolutionEnabled -bool true
```

Log out and back in for the additional resolutions to appear.

---

## Sound

### Startup Chime (Apple Silicon)

```bash
sudo nvram StartupMute=%01   # mute startup chime
sudo nvram StartupMute=%00   # restore startup chime
nvram StartupMute            # verify current setting
```

Takes effect at next boot. On Intel Macs, this NVRAM key may have no effect.

### UI Sound Effects

```bash
defaults write NSGlobalDomain com.apple.sound.uiaudio.enabled -int 0   # disable
defaults write NSGlobalDomain com.apple.sound.uiaudio.enabled -int 1   # enable
```

### Volume Change Feedback Beep

```bash
defaults write NSGlobalDomain com.apple.sound.beep.feedback -int 0   # disable
defaults write NSGlobalDomain com.apple.sound.beep.feedback -int 1   # enable
```

### Bluetooth Audio Quality

When a Bluetooth headset is connected, macOS may reduce audio quality to support the microphone. Raise the bitpool range to improve output quality:

```bash
defaults write com.apple.BluetoothAudioAgent "Apple Bitpool Min (editable)" -int 40
defaults write com.apple.BluetoothAudioAgent "Apple Bitpool Max (editable)" -int 80
defaults write com.apple.BluetoothAudioAgent "Apple Initial Bitpool (editable)" -int 80
```

Toggle Bluetooth off and on after applying, or restart `bluetoothd`:

```bash
sudo pkill bluetoothd
```

### Music Playback Notifications

```bash
defaults write com.apple.Music userWantsPlaybackNotifications -int 0   # disable
defaults write com.apple.Music userWantsPlaybackNotifications -int 1   # enable
```

---

## Login Window

All settings write to `/Library/Preferences/com.apple.loginwindow` and require `sudo`.

```bash
# Show IP address / hostname when clicking the clock
sudo defaults write /Library/Preferences/com.apple.loginwindow AdminHostInfo HostName
# Valid values: HostName, IPAddress, DSStatus, SystemVersion

# Display a message below the login fields
sudo defaults write /Library/Preferences/com.apple.loginwindow LoginwindowText "Authorized use only."
sudo defaults delete /Library/Preferences/com.apple.loginwindow LoginwindowText   # remove

# Enable auto-login (incompatible with FileVault)
sudo defaults write /Library/Preferences/com.apple.loginwindow autoLoginUser "username"
sudo defaults delete /Library/Preferences/com.apple.loginwindow autoLoginUser   # disable

# Show input source menu at login screen
sudo defaults write /Library/Preferences/com.apple.loginwindow showInputMenu -bool true

# Hide Restart and Shutdown buttons
sudo defaults write /Library/Preferences/com.apple.loginwindow ShutDownDisabled -bool true
sudo defaults write /Library/Preferences/com.apple.loginwindow RestartDisabled -bool true
```

---

## Appearance (Accessibility)

```bash
# Reduce transparency in menu bar, Dock, and sidebars
defaults write com.apple.universalaccess reduceTransparency -bool true

# Reduce motion effects (parallax, window animations)
defaults write com.apple.universalaccess reduceMotion -bool true

# Increase contrast for UI elements
defaults write com.apple.universalaccess increaseContrast -bool true

# Auto-hide the menu bar
defaults write NSGlobalDomain _HIHideMenuBar -bool true
```

Revert any of the above by replacing `-bool true` with `-bool false`, or deleting the key.

Apply global appearance changes: `killall SystemUIServer`

---

## Notes

- Battery health diagnostics (cycle count, condition, capacity) are covered by @tank/macos-maintenance.
- `pmset -g cap` shows which power management features the current hardware supports. Not all flags apply to all machines — `womp` requires Ethernet on some models.
- On Apple Silicon with SIP enabled, `systemsetup` sleep commands may silently fail; use `pmset` instead.
- Night Shift, True Tone, and display resolution have no CLI equivalent and must be configured through System Settings.
- Login window changes take effect at the next login screen display. NVRAM changes take effect at the next boot.
