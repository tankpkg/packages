# Dock, Finder, and Desktop Configuration

Sources: mathiasbynens/dotfiles, macos-defaults.com (Yann Bertrand), Apple man pages

---

## Dock

Managed through `com.apple.dock`. All changes require `killall Dock`.

### Size and Appearance

```bash
# Tile size in pixels (16–128; default 48)
defaults write com.apple.dock tilesize -int 48

# Enable magnification and set magnified size (must be >= tilesize)
defaults write com.apple.dock magnification -bool true
defaults write com.apple.dock largesize -int 72

# Position: left, bottom, right
defaults write com.apple.dock orientation -string "bottom"

# Minimize effect: genie, scale, suck
defaults write com.apple.dock mineffect -string "scale"

# Animate opening applications
defaults write com.apple.dock launchanim -bool false

# Show process indicators (dots under running apps)
defaults write com.apple.dock show-process-indicators -bool true

# Show recent applications section
defaults write com.apple.dock show-recents -bool false

# Only show open applications (static-only hides pinned-but-closed apps)
defaults write com.apple.dock static-only -bool false

# Enable spring-loading for all Dock items (hover to open)
defaults write com.apple.dock enable-spring-load-actions-on-all-items -bool true
```

### Auto-hide

```bash
# Enable auto-hide
defaults write com.apple.dock autohide -bool true

# Delay before Dock appears on hover (seconds; 0 = instant)
defaults write com.apple.dock autohide-delay -float 0

# Animation duration for show/hide (seconds; 0 = instant)
defaults write com.apple.dock autohide-time-modifier -float 0.5
```

### Persistent Apps — Wipe and Add Spacers

```bash
# Remove all pinned apps
defaults write com.apple.dock persistent-apps -array

# Add a full-width spacer tile
defaults write com.apple.dock persistent-apps -array-add '{"tile-type"="spacer-tile";}'

# Add a small spacer tile
defaults write com.apple.dock persistent-apps -array-add '{"tile-type"="small-spacer-tile";}'

killall Dock
```

After `killall Dock`, drag real applications into position manually. To add app entries programmatically, use PlistBuddy to construct the full tile dict.

---

## Hot Corners

Stored in `com.apple.dock` as `wvous-<pos>-corner` (action) and `wvous-<pos>-modifier` (key mask). Positions: `tl`, `tr`, `bl`, `br`.

### Corner Action Values

| Value | Action |
|-------|--------|
| 0 | No action |
| 2 | Application Windows (Expose) |
| 3 | Desktop |
| 4 | Dashboard (removed macOS 11) |
| 5 | Start Screen Saver |
| 6 | Disable Screen Saver |
| 7 | Sleep Display |
| 10 | Put Display to Sleep |
| 11 | Launchpad |
| 12 | Notification Center |
| 13 | Lock Screen |
| 14 | Quick Note |

### Modifier Key Masks

| Value | Modifier |
|-------|----------|
| 0 | None |
| 131072 | Shift |
| 262144 | Control |
| 524288 | Option |
| 1048576 | Command |

Combine modifiers by adding values (Shift + Option = 655360).

### Example Configuration

```bash
# Top-left: Application Windows
defaults write com.apple.dock wvous-tl-corner -int 2
defaults write com.apple.dock wvous-tl-modifier -int 0

# Top-right: Notification Center
defaults write com.apple.dock wvous-tr-corner -int 12
defaults write com.apple.dock wvous-tr-modifier -int 0

# Bottom-left: Start Screen Saver
defaults write com.apple.dock wvous-bl-corner -int 5
defaults write com.apple.dock wvous-bl-modifier -int 0

# Bottom-right: Desktop (Option required to avoid accidental trigger)
defaults write com.apple.dock wvous-br-corner -int 3
defaults write com.apple.dock wvous-br-modifier -int 524288

killall Dock
```

---

## Finder

Settings span `com.apple.finder` and `NSGlobalDomain`. Changes require `killall Finder`.

### File Visibility

```bash
# Show all filename extensions
defaults write NSGlobalDomain AppleShowAllExtensions -bool true

# Show hidden files (dot-files)
defaults write com.apple.finder AppleShowAllFiles -bool true

# Suppress warning when changing a file extension
defaults write com.apple.finder FXEnableExtensionChangeWarning -bool false
```

### Interface Elements

```bash
# Show path bar at the bottom of Finder windows
defaults write com.apple.finder ShowPathbar -bool true

# Show status bar (item count, disk space)
defaults write com.apple.finder ShowStatusBar -bool true

# Allow quitting Finder via Cmd-Q
defaults write com.apple.finder QuitMenuItem -bool true

# Enable text selection in Quick Look previews
defaults write com.apple.finder QLEnableTextSelection -bool true
```

### Default View Style

| Code | View |
|------|------|
| `Nlsv` | List view |
| `icnv` | Icon view |
| `clmv` | Column view |
| `glyv` | Gallery view |

```bash
defaults write com.apple.finder FXPreferredViewStyle -string "Nlsv"
```

### Search Scope

| Code | Scope |
|------|-------|
| `SCev` | This Mac (everywhere) |
| `SCcf` | Current folder |
| `SCsp` | Previous scope |

```bash
defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"
```

### Folder Sorting

```bash
# Keep folders on top when sorting by name (windows and Desktop)
defaults write com.apple.finder _FXSortFoldersFirst -bool true
defaults write com.apple.finder _FXSortFoldersFirstOnDesktop -bool true
```

### New Window Target

| Value | Target |
|-------|--------|
| `PfCm` | Computer |
| `PfVo` | Volumes |
| `PfHm` | Home folder |
| `PfDe` | Desktop |
| `PfDo` | Documents |
| `PfLo` | Custom path |

```bash
# Home folder
defaults write com.apple.finder NewWindowTarget -string "PfHm"

# Custom path (file:// URL required)
defaults write com.apple.finder NewWindowTarget -string "PfLo"
defaults write com.apple.finder NewWindowTargetPath -string "file:///Users/$(whoami)/Projects/"
```

### .DS_Store Files

```bash
# Prevent .DS_Store on network volumes
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true

# Prevent .DS_Store on USB volumes
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

killall Finder
```

---

## Screenshots

Settings in `com.apple.screencapture`. Most take effect immediately; run `killall SystemUIServer` to refresh the menu bar tool.

### Format

| Value | Format |
|-------|--------|
| `png` | PNG (default; lossless) |
| `jpg` | JPEG (lossy; smaller files) |
| `pdf` | PDF |
| `gif` | GIF |
| `tiff` | TIFF |

```bash
defaults write com.apple.screencapture type -string "png"
```

### Location, Shadow, Thumbnail, and Filename

```bash
# Save location (directory must exist)
defaults write com.apple.screencapture location -string "${HOME}/Screenshots"
mkdir -p "${HOME}/Screenshots"

# Disable drop shadow on window screenshots (Cmd-Shift-4, Space)
defaults write com.apple.screencapture disable-shadow -bool true

# Disable floating thumbnail preview after capture
defaults write com.apple.screencapture show-thumbnail -bool false

# Include date and time in filename (default: true)
defaults write com.apple.screencapture include-date -bool true

# Custom filename prefix (default: "Screenshot")
# With include-date true: "capture 2026-03-10 at 14.30.00.png"
defaults write com.apple.screencapture name -string "capture"

killall SystemUIServer
```

---

## Mission Control

Stored in `com.apple.dock`. Changes require `killall Dock`.

```bash
# Animation speed (seconds; lower = faster)
defaults write com.apple.dock expose-animation-duration -float 0.15

# Do not rearrange Spaces based on most recent use
defaults write com.apple.dock mru-spaces -bool false

# Group windows by application
defaults write com.apple.dock expose-group-apps -bool true

# Each display has its own Space (requires logout)
defaults write com.apple.spaces spans-displays -bool false

# Disable Dashboard (macOS 10.10–10.15 only; removed in macOS 11)
defaults write com.apple.dashboard mcx-disabled -bool true

killall Dock
```

---

## Spotlight

Controlled via `com.apple.spotlight`. The `orderedItems` array sets which categories are enabled and in what order.

### Category Identifiers

| Name | Category |
|------|----------|
| `APPLICATIONS` | Applications |
| `SYSTEM_PREFS` | System Preferences |
| `DIRECTORIES` | Folders |
| `PDF` | PDF Documents |
| `DOCUMENTS` | Documents |
| `CONTACT` | Contacts |
| `EVENT_TODO` | Events & Reminders |
| `IMAGES` | Images |
| `BOOKMARKS` | Bookmarks |
| `MUSIC` | Music |
| `MOVIES` | Movies |
| `SOURCE` | Developer |
| `MENU_DEFINITION` | Dictionary |
| `MENU_EXPRESSION` | Calculator |
| `MENU_CONVERSION` | Conversion |
| `MENU_WEBSEARCH` | Web Searches |
| `MENU_SPOTLIGHT_SUGGESTIONS` | Spotlight Suggestions |

### Set orderedItems

Write the full array to control order and enabled state. Omitted categories are disabled.

```bash
defaults write com.apple.spotlight orderedItems -array \
  '{"enabled" = 1;"name" = "APPLICATIONS";}' \
  '{"enabled" = 1;"name" = "SYSTEM_PREFS";}' \
  '{"enabled" = 1;"name" = "DIRECTORIES";}' \
  '{"enabled" = 1;"name" = "PDF";}' \
  '{"enabled" = 1;"name" = "DOCUMENTS";}' \
  '{"enabled" = 1;"name" = "CONTACT";}' \
  '{"enabled" = 1;"name" = "EVENT_TODO";}' \
  '{"enabled" = 1;"name" = "IMAGES";}' \
  '{"enabled" = 1;"name" = "BOOKMARKS";}' \
  '{"enabled" = 1;"name" = "MUSIC";}' \
  '{"enabled" = 1;"name" = "MOVIES";}' \
  '{"enabled" = 1;"name" = "SOURCE";}' \
  '{"enabled" = 1;"name" = "MENU_DEFINITION";}' \
  '{"enabled" = 1;"name" = "MENU_EXPRESSION";}' \
  '{"enabled" = 1;"name" = "MENU_CONVERSION";}' \
  '{"enabled" = 0;"name" = "MENU_WEBSEARCH";}' \
  '{"enabled" = 0;"name" = "MENU_SPOTLIGHT_SUGGESTIONS";}'
```

### Rebuild Index

```bash
# Erase and rebuild (takes several minutes; results incomplete during rebuild)
sudo mdutil -E /

# Check status
sudo mdutil -s /

# Disable indexing entirely (breaks Spotlight)
sudo mdutil -i off /

# Re-enable
sudo mdutil -i on /
```

---

## Menu Bar

Clock settings in `com.apple.menuextra.clock`; auto-hide in `NSGlobalDomain`. Changes require `killall SystemUIServer`.

### Clock DateFormat Tokens

| Token | Meaning |
|-------|---------|
| `EEE` | Abbreviated weekday (Mon) |
| `d` | Day of month |
| `MMM` | Abbreviated month (Jan) |
| `HH` | 24-hour hour (00–23) |
| `h` | 12-hour hour (1–12) |
| `mm` | Minutes |
| `ss` | Seconds |
| `a` | AM/PM |

```bash
# Date and 24-hour time: "Mon 10 Mar 14:30"
defaults write com.apple.menuextra.clock DateFormat -string "EEE d MMM HH:mm"

# 12-hour time with seconds: "2:30:45 PM"
defaults write com.apple.menuextra.clock DateFormat -string "h:mm:ss a"

# Flash the time separator colon
defaults write com.apple.menuextra.clock FlashDateSeparators -bool false

# Analog clock face
defaults write com.apple.menuextra.clock IsAnalog -bool false

# Show battery percentage
defaults write com.apple.menuextra.battery ShowPercent -string "YES"

# Auto-hide the menu bar
defaults write NSGlobalDomain _HIHideMenuBar -bool true

killall SystemUIServer
```

---

## Desktop Icons

Controlled through `com.apple.finder`. Files remain in `~/Desktop`; only their visibility on the Desktop surface changes.

```bash
# Hide all icons on the Desktop surface
defaults write com.apple.finder CreateDesktop -bool false

# Show internal hard drives
defaults write com.apple.finder ShowHardDrivesOnDesktop -bool true

# Show external disks
defaults write com.apple.finder ShowExternalHardDrivesOnDesktop -bool true

# Show removable media (USB drives, SD cards)
defaults write com.apple.finder ShowRemovableMediaOnDesktop -bool true

# Show connected servers
defaults write com.apple.finder ShowMountedServersOnDesktop -bool false

killall Finder
```

---

## Applying All Changes

Restart all affected processes after a batch of writes:

```bash
for app in Dock Finder SystemUIServer; do
  killall "${app}" &>/dev/null || true
done
```

For Spotlight category changes, also rebuild the index:

```bash
sudo mdutil -E /
```
Settings that require logout: `spans-displays` (Mission Control), `_HIHideMenuBar` on some macOS versions — note these in setup scripts.
