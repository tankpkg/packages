---
name: "@tank/macos-configurator"
description: |
  macOS system configuration via command line. Covers the full `defaults write`,
  `networksetup`, `pmset`, `systemsetup`, `scutil`, `hidutil`, and `PlistBuddy`
  universe for configuring keyboard, trackpad, Dock, Finder, screenshots,
  network (DNS, proxy, Wi-Fi, hostname), power management, display, sound,
  security/privacy, and per-app settings. Generates idempotent setup scripts
  and reads current configuration. Companion to @tank/macos-cleanup (space
  recovery) and @tank/macos-maintenance (system health) — this skill
  CONFIGURES preferences, not cleans or diagnoses.
  Synthesizes mathiasbynens/dotfiles, macos-defaults.com, Apple man pages,
  macOS Security Compliance Project (NIST), and Scripting OS X.

  Trigger phrases: "defaults write", "configure mac", "mac setup",
  "new mac setup", "macos defaults", "mac preferences", "system preferences",
  "system settings", "key repeat", "trackpad settings", "dock settings",
  "finder preferences", "change dns", "set proxy", "dark mode",
  "hot corners", "screenshot settings", "modifier keys", "caps lock remap",
  "remap caps lock", "power settings", "sleep timer", "configure keyboard",
  "mac configuration", "setup script", "dotfiles", "configure trackpad",
  "natural scrolling", "tap to click", "auto-correct off", "smart quotes",
  "hide dock", "dock position", "show hidden files", "file extensions",
  "hostname", "computer name", "accent color", "menu bar clock",
  "configure firewall", "startup chime", "login window"
---

# macOS Configurator

Configure macOS system preferences via command line. Covers every major
preference domain — keyboard, trackpad, Dock, Finder, network, power,
display, sound, security, and per-app settings.

## Core Philosophy

1. **Read before writing.** Check the current value with `defaults read`
   before changing anything. Show the user what will change.
2. **Explain side effects.** Many changes need `killall Dock`, logout, or
   restart to take effect. State the requirement with every command.
3. **Prefer built-in tools.** Use `defaults`, `networksetup`, `pmset`,
   `systemsetup`, `scutil` — not raw plist editing — unless nesting
   requires `PlistBuddy`.
4. **Script-friendly.** When users ask to configure multiple settings,
   generate a single idempotent shell script they can save and reuse.
5. **Know the boundaries.** Some settings can't be changed via CLI due to
   SIP or TCC restrictions. Say so instead of guessing.

## Quick-Start

### "Make key repeat faster"

```bash
defaults write NSGlobalDomain ApplePressAndHoldEnabled -bool false
defaults write NSGlobalDomain KeyRepeat -int 2
defaults write NSGlobalDomain InitialKeyRepeat -int 15
```
Requires logout/login. See `references/keyboard-trackpad-input.md`.

### "Change my DNS to Cloudflare"

```bash
sudo networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1
sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder
```
See `references/network-hostname.md`.

### "Set up a new Mac for development"

1. Run `bash scripts/read-config.sh` to capture current state
2. Apply settings from `references/app-settings-recipes.md` (Developer Setup recipe)
3. Verify with `defaults read` on changed domains

### "Generate a setup script from my current config"

```bash
bash scripts/read-config.sh --json > ~/my-mac-config.json
```
Then use the output to build an idempotent setup script.
See `references/app-settings-recipes.md` for script patterns.

## CLI Tool Selection

| Task | Tool | Sudo? |
|------|------|-------|
| App/system preferences | `defaults` | No (usually) |
| Nested plist values | `PlistBuddy` | No |
| Network (DNS, proxy, Wi-Fi) | `networksetup` | Yes for writes |
| Hostname | `scutil` | Yes |
| Power/sleep/hibernate | `pmset` | Yes |
| Time zone, remote login | `systemsetup` | Yes |
| Modifier key remapping | `hidutil` | No |
| Services/daemons | `launchctl` | Varies |

See `references/defaults-and-tools.md` for full tool reference.

## Decision Trees

### What to Configure Based on User Request

| User Says | Domain | Reference File |
|-----------|--------|----------------|
| Key repeat, auto-correct, caps lock, trackpad | Input | `keyboard-trackpad-input.md` |
| Dock, Finder, screenshots, hot corners, Spotlight | Desktop | `dock-finder-desktop.md` |
| DNS, proxy, Wi-Fi, hostname, firewall | Network | `network-hostname.md` |
| Sleep, display, dark mode, sound, login window | Power/Display | `power-display-sound.md` |
| Screen lock, Gatekeeper, FileVault, updates | Security | `security-privacy.md` |
| Safari, Mail, Terminal, TextEdit, setup scripts | Apps/Recipes | `app-settings-recipes.md` |
| How does `defaults` work? Tool reference | Tools | `defaults-and-tools.md` |

### Applying Changes

| Domain Changed | Restart Command |
|----------------|-----------------|
| `com.apple.dock` | `killall Dock` |
| `com.apple.finder` | `killall Finder` |
| `com.apple.screencapture` | `killall SystemUIServer` |
| Menu bar items | `killall SystemUIServer` |
| NSGlobalDomain keyboard | Logout/login required |
| `com.apple.Safari` | Restart Safari |
| Stubborn preferences | `killall cfprefsd` (nuclear option) |

## Companion Skills

| Skill | Focus | When to Use |
|-------|-------|-------------|
| `@tank/macos-cleanup` | Disk space recovery | "Free up space", "clean caches" |
| `@tank/macos-maintenance` | System health | "Is my Mac OK?", "security audit" |
| `@tank/macos-configurator` | System preferences | "Change settings", "configure Mac" |

## Reference Files

| File | Contents |
|------|----------|
| `references/defaults-and-tools.md` | Core CLI tools (defaults, PlistBuddy, systemsetup, scutil, launchctl, hidutil), domain discovery, applying changes, gotchas and version differences |
| `references/keyboard-trackpad-input.md` | Key repeat, text corrections, function keys, modifier remapping (hidutil), trackpad gestures, mouse, input sources, language/locale |
| `references/dock-finder-desktop.md` | Dock (size, autohide, position, hot corners), Finder (extensions, hidden files, views), screenshots, Mission Control, Spotlight, menu bar, desktop icons |
| `references/network-hostname.md` | DNS (with provider table), proxy, Wi-Fi, IP config, hostname (3 name types), firewall (socketfilterfw), VPN, AirDrop, network time |
| `references/power-display-sound.md` | pmset (sleep, hibernate, wake, caffeinate), display (dark mode, accent color, font smoothing), sound (startup chime, UI sounds), login window |
| `references/security-privacy.md` | Screen lock, Gatekeeper, FileVault, firewall rules, remote access, quarantine, auto-updates, Handoff, TCC limitations |
| `references/app-settings-recipes.md` | Per-app settings (Safari, Mail, Terminal, TextEdit, etc.), setup script patterns, backup/restore, common recipes (developer, designer, minimal) |

## Scripts

| Script | Usage |
|--------|-------|
| `scripts/read-config.sh` | Reads current macOS configuration across major domains. Flags: `--json` (JSON output), `--domain <name>` (single domain), `--diff <file>` (compare to saved config) |
