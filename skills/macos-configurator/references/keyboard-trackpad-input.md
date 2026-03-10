# Keyboard, Trackpad, and Input Configuration

Sources: mathiasbynens/dotfiles, macos-defaults.com (Yann Bertrand), Apple man pages

---

## Key Repeat

Both settings require a **logout/login** to take effect — `killall` is not sufficient.

```bash
# Disable press-and-hold accent popup (enables key repeat for all keys)
defaults write NSGlobalDomain ApplePressAndHoldEnabled -bool false

# Key repeat rate — lower = faster. Default: 6. Developer sweet spot: 2
defaults write NSGlobalDomain KeyRepeat -int 2

# Delay before repeat begins — lower = shorter. Default: 25. Developer sweet spot: 15
defaults write NSGlobalDomain InitialKeyRepeat -int 15
```

| KeyRepeat | Interval | Feel |
|-----------|----------|------|
| 1 | 15ms | Extremely fast |
| 2 | 30ms | Fast — recommended |
| 6 | 90ms | macOS default |

| InitialKeyRepeat | Delay | Feel |
|------------------|-------|------|
| 10 | 150ms | Very short |
| 15 | 225ms | Short — recommended |
| 25 | 375ms | macOS default |

---

## Text Corrections

All keys live in `NSGlobalDomain`. Changes take effect in new text fields immediately.

```bash
# Disable auto-correct
defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false

# Disable smart quotes (" " → " ")
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false

# Disable smart dashes (-- → —)
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false

# Disable auto-capitalize
defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false

# Disable period substitution (double-space → period)
defaults write NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false

# Disable inline text completion suggestions
defaults write NSGlobalDomain NSAutomaticTextCompletionEnabled -bool false
```

Write `-bool true` to re-enable any of these. No process restart required.

---

## Function Keys

### Standard Function Key Behavior

```bash
# Use F1–F12 as standard function keys (hold Fn for media controls)
defaults write NSGlobalDomain com.apple.keyboard.fnState -bool true

# Restore default: media keys without Fn
defaults write NSGlobalDomain com.apple.keyboard.fnState -bool false
```

### Fn Key Usage Type

Controls what the Fn/Globe key does when pressed alone.

```bash
# 0 = Do Nothing, 1 = Change Input Source, 2 = Emoji & Symbols, 3 = Dictation
defaults write NSGlobalDomain AppleFnUsageType -int 0
```

### Full Keyboard Access (AppleKeyboardUIMode)

```bash
# Enable: Tab navigates all UI controls, not just text fields
defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

# Disable (macOS default)
defaults write NSGlobalDomain AppleKeyboardUIMode -int 0
```

Restart affected apps after changing this setting.

---

## Modifier Key Remapping

`hidutil` remaps keys at the HID layer. Survives sleep, resets on reboot.
Make permanent with a LaunchAgent.

```bash
# Syntax
hidutil property --set '{"UserKeyMapping":[
  {"HIDKeyboardModifierMappingSrc": <src>, "HIDKeyboardModifierMappingDst": <dst>}
]}'
```

| Key | HID Code |
|-----|----------|
| Caps Lock | 0x700000039 |
| Left Control | 0x7000000E0 |
| Left Option/Alt | 0x7000000E2 |
| Left Command | 0x7000000E3 |
| Right Control | 0x7000000E4 |
| Right Option/Alt | 0x7000000E6 |
| Right Command | 0x7000000E7 |
| Escape | 0x700000029 |

```bash
# Remap Caps Lock → Escape (Vim users)
hidutil property --set '{"UserKeyMapping":[
  {"HIDKeyboardModifierMappingSrc":0x700000039,"HIDKeyboardModifierMappingDst":0x700000029}
]}'

# Remap Caps Lock → Left Control
hidutil property --set '{"UserKeyMapping":[
  {"HIDKeyboardModifierMappingSrc":0x700000039,"HIDKeyboardModifierMappingDst":0x7000000E0}
]}'

# Clear all remaps
hidutil property --set '{"UserKeyMapping":[]}'

# Read current mapping
hidutil property --get UserKeyMapping
```

### Making Remaps Permanent via LaunchAgent

Create `~/Library/LaunchAgents/com.local.hidutil.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.local.hidutil</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/hidutil</string>
    <string>property</string>
    <string>--set</string>
    <string>{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc":0x700000039,"HIDKeyboardModifierMappingDst":0x700000029}]}</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.local.hidutil.plist
```

Use `https://hidutil-generator.netlify.app/` to build JSON for complex remaps.

---

## Trackpad

Some keys must be written to both the Bluetooth and built-in trackpad domains,
plus the `-currentHost` variant of `NSGlobalDomain`.

### Tap to Click

```bash
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
defaults write com.apple.AppleMultitouchTrackpad Clicking -bool true
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
```

### Secondary Click (Two-Finger Right-Click)

```bash
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadRightClick -bool true
defaults write com.apple.AppleMultitouchTrackpad TrackpadRightClick -bool true
defaults -currentHost write NSGlobalDomain com.apple.trackpad.enableSecondaryClick -bool true
```

### Three-Finger Drag

```bash
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadThreeFingerDrag -bool true
defaults write com.apple.AppleMultitouchTrackpad TrackpadThreeFingerDrag -bool true
```

### Tracking Speed

Values range from 0 (slowest) to 3 (fastest).

```bash
defaults write NSGlobalDomain com.apple.trackpad.scaling -float 2.5
```

### Force Click

```bash
# Disable Force Click
defaults write com.apple.AppleMultitouchTrackpad ForceSuppressed -bool true
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad ForceSuppressed -bool true

# Click pressure: 0 = Light, 1 = Medium (default), 2 = Firm
defaults write com.apple.AppleMultitouchTrackpad FirstClickThreshold -int 1
defaults write com.apple.AppleMultitouchTrackpad SecondClickThreshold -int 1
```

### Natural Scrolling

```bash
# Disable natural scrolling (traditional: scroll down moves content down)
defaults write NSGlobalDomain com.apple.swipescrolldirection -bool false

# Enable natural scrolling (macOS default)
defaults write NSGlobalDomain com.apple.swipescrolldirection -bool true
```

Apply trackpad changes:

```bash
killall SystemUIServer
```

Some trackpad settings (three-finger drag, tap to click) require logout to fully apply.

---

## Mouse

### Tracking Speed

```bash
# Mouse tracking speed (0–3, default ~1.0)
defaults write NSGlobalDomain com.apple.mouse.scaling -float 2.5
```

### Scroll Direction

Mouse and trackpad share `com.apple.swipescrolldirection`. To reverse them
independently, use a third-party tool (Scroll Reverser, LinearMouse).

```bash
defaults write NSGlobalDomain com.apple.swipescrolldirection -bool false
```

### Secondary Click

```bash
# Enable right-click
defaults write com.apple.driver.AppleBluetoothMultitouch.mouse MouseButtonMode -string "TwoButton"

# Single button mode
defaults write com.apple.driver.AppleBluetoothMultitouch.mouse MouseButtonMode -string "OneButton"
```

Apply mouse changes: `killall SystemUIServer`

---

## Input Sources

### Reading Current Sources

```bash
# Active input source
defaults read com.apple.HIToolbox AppleSelectedInputSources

# All enabled input sources
defaults read com.apple.HIToolbox AppleEnabledInputSources
```

### Adding Input Sources

```bash
# Enable US English + Hebrew
defaults write com.apple.HIToolbox AppleEnabledInputSources -array \
  '{"Bundle ID" = "com.apple.keylayout.US"; "InputSourceKind" = "Keyboard Layout";}' \
  '{"Bundle ID" = "com.apple.keylayout.Hebrew"; "InputSourceKind" = "Keyboard Layout";}'
```

| Layout | Bundle ID |
|--------|-----------|
| US English | com.apple.keylayout.US |
| British | com.apple.keylayout.British |
| Dvorak | com.apple.keylayout.Dvorak |
| Colemak | com.apple.keylayout.Colemak |
| Hebrew | com.apple.keylayout.Hebrew |
| German | com.apple.keylayout.German |
| French | com.apple.keylayout.French |
| Japanese (Romaji) | com.apple.inputmethod.Kotoeri.RomajiTyping.Japanese |
| Chinese (Simplified) | com.apple.inputmethod.SCIM.ITABC |
| Emoji & Symbols | com.apple.CharacterPaletteIM |

```bash
# Apply input source changes
killall -SIGKILL SystemUIServer
```

### Fn Key for Input Source Switching

```bash
defaults write NSGlobalDomain AppleFnUsageType -int 1
```

---

## Language and Locale

Language and locale changes require a **logout/login** to apply system-wide.

```bash
# Set primary language
defaults write NSGlobalDomain AppleLanguages -array "en-US"

# Multiple languages in preference order
defaults write NSGlobalDomain AppleLanguages -array "en-US" "he" "fr-FR"

# Locale (affects date/time/number formatting)
defaults write NSGlobalDomain AppleLocale -string "en_US"

# Metric system
defaults write NSGlobalDomain AppleMeasurementUnits -string "Centimeters"
defaults write NSGlobalDomain AppleMetricUnits -bool true

# Imperial system
defaults write NSGlobalDomain AppleMeasurementUnits -string "Inches"
defaults write NSGlobalDomain AppleMetricUnits -bool false

# Temperature unit
defaults write NSGlobalDomain AppleTemperatureUnit -string "Celsius"
```

---

## Common Developer Setup

Fast key repeat, no text corrections, tap to click, traditional scroll direction.
Apply all at once, then log out and back in.

```bash
#!/usr/bin/env bash
# Developer input setup — logout required for key repeat to take effect

# Fast key repeat
defaults write NSGlobalDomain ApplePressAndHoldEnabled -bool false
defaults write NSGlobalDomain KeyRepeat -int 2
defaults write NSGlobalDomain InitialKeyRepeat -int 15

# Disable all text corrections
defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false
defaults write NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticTextCompletionEnabled -bool false

# F1–F12 as standard function keys
defaults write NSGlobalDomain com.apple.keyboard.fnState -bool true

# Full keyboard access
defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

# Tap to click
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
defaults write com.apple.AppleMultitouchTrackpad Clicking -bool true
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

# Traditional scroll direction
defaults write NSGlobalDomain com.apple.swipescrolldirection -bool false

# Fast tracking speed
defaults write NSGlobalDomain com.apple.trackpad.scaling -float 2.5

# Remap Caps Lock → Escape
hidutil property --set '{"UserKeyMapping":[
  {"HIDKeyboardModifierMappingSrc":0x700000039,"HIDKeyboardModifierMappingDst":0x700000029}
]}'

killall SystemUIServer 2>/dev/null || true
echo "Done. Log out and back in for key repeat settings to take effect."
```

---

## Restart Requirements Summary

| Setting | How to Apply |
|---------|--------------|
| KeyRepeat, InitialKeyRepeat, ApplePressAndHoldEnabled | Logout/login |
| Text corrections | Immediate (new fields); relaunch apps |
| Function key behavior, AppleKeyboardUIMode | Relaunch affected apps |
| Modifier key remapping (hidutil) | Immediate; resets on reboot |
| Trackpad tap/click/scroll | `killall SystemUIServer`; some need logout |
| Mouse settings | `killall SystemUIServer` |
| Input sources | `killall -SIGKILL SystemUIServer` or logout |
| Language, Locale, Measurement units | Logout/login |
