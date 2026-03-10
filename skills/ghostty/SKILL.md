---
name: "@tank/ghostty"
description: |
  Expert Ghostty terminal emulator configuration, themes, keybindings, and shell integration.
  Covers config file format, 500+ built-in themes with light/dark switching, custom theme
  authoring, keybind syntax with all actions (splits, tabs, search, quick terminal),
  shell integration auto-injection for zsh/bash/fish/elvish, SSH/sudo wrapping, $TERM
  and terminfo, platform differences between macOS and Linux (GTK/Wayland), and migration
  from iTerm2, kitty, alacritty, and WezTerm. Synthesizes ghostty.org official docs,
  mitchellh/ghostty GitHub, iterm2-color-schemes, and community dotfiles.

  Trigger phrases: ghostty config, ghostty theme, ghostty keybind, ghostty keybinding,
  ghostty shell integration, ghostty split, ghostty tab, ghostty font, ghostty quick terminal,
  quake terminal ghostty, configure ghostty, ghostty setup, ghostty dotfiles, ghostty theme list,
  ghostty opacity, ghostty background, ghostty linux, ghostty macos, migrate to ghostty,
  ghostty vs kitty, ghostty vs wezterm, jump to prompt ghostty, ghostty terminfo, ghostty ssh,
  ghostty reload config, ghostty color scheme, ghostty keybinds, ghostty transparency,
  ghostty font ligatures, ghostty splits, ghostty tabs, ghostty custom shader
---

# Ghostty

Configure, theme, and extend Ghostty — the fast, native, GPU-accelerated terminal emulator
by Mitchell Hashimoto. Zero required configuration; everything below is optional enhancement.

## Core Philosophy

1. **Zero config is a valid config.** Ghostty works out of the box with JetBrains Mono,
   sensible defaults, and built-in Nerd Fonts. Configure only what you actually want different.
2. **Read the config reference in-terminal.** `ghostty +show-config --default --docs` is the
   authoritative source for your exact installed version. Use it before guessing at option names.
3. **Themes are just config files.** Any config option can go in a theme. Load them with
   `theme = Name` and override individual settings in the main config after.
4. **Shell integration unlocks the terminal.** Enable it; it costs nothing and enables
   prompt jumping, smart cursor, CWD tracking, and SSH/sudo wrapping.
5. **Platform differences are real.** `global:` keybinds are macOS-only. Quick terminal needs
   Wayland on Linux. `macos-option-as-alt` is critical for vim/emacs. Know your platform.

## Quick-Start

### "Change my font and theme"

```ini
font-family = "Fira Code"
font-size = 14
font-feature = -calt,-liga    # disable ligatures if unwanted
theme = dark:Catppuccin Frappe,light:Catppuccin Latte
```

See `references/themes-and-appearance.md` for 460+ theme names and custom theme authoring.

### "Set up tmux-style splits with Ctrl+W"

```ini
keybind = ctrl+w>v=new_split:right
keybind = ctrl+w>s=new_split:down
keybind = ctrl+w>h=goto_split:left
keybind = ctrl+w>l=goto_split:right
keybind = ctrl+w>j=goto_split:down
keybind = ctrl+w>k=goto_split:up
keybind = ctrl+w>z=toggle_split_zoom
```

See `references/keybindings-and-input.md` for full action catalog and key tables.

### "Make Option key work in vim/zsh (macOS)"

```ini
macos-option-as-alt = left    # or true for both Option keys
```

### "Set up a global drop-down terminal (Quake-style)"

```ini
keybind = global:super+grave=toggle_quick_terminal
quick-terminal-position = top
quick-terminal-autohide = true
```

`global:` requires Accessibility permission on macOS. Linux requires Wayland.

### "Fix SSH showing 'unknown terminal type'"

Option A — enable SSH wrapping in shell integration:
```ini
shell-integration-features = cursor,sudo,ssh
```

Option B — copy terminfo to remote once:
```sh
infocmp -x ghostty | ssh remote-host -- "mkdir -p ~/.terminfo && tic -x -"
```

See `references/shell-integration-features.md`.

### "Make transparent background"

```ini
background-opacity = 0.92
background-blur-radius = 20
```

Bind toggle: `keybind = ctrl+shift+t=toggle_background_opacity`

## CLI Tools Decision Tree

| User Says | Command |
|-----------|---------|
| What options exist? | `ghostty +show-config --default --docs` |
| List my fonts | `ghostty +list-fonts` |
| List themes | `ghostty +list-themes` |
| What are my keybinds? | `ghostty +list-keybinds` |
| What version? | `ghostty +version` |
| Is my config valid? | `ghostty +show-config 2>&1 \| grep -i error` |

Or run `bash scripts/show-config.sh help` for an interactive wrapper.

## What Belongs Where

| Task | Reference |
|------|-----------|
| Font, window, cursor, scrollback, clipboard options | `references/config-reference.md` |
| Theme names, custom themes, background images, transparency | `references/themes-and-appearance.md` |
| Keybind syntax, all actions, key sequences, key tables | `references/keybindings-and-input.md` |
| Shell integration setup, SSH, $TERM, splits workflow | `references/shell-integration-features.md` |
| macOS vs Linux, migrating from kitty/iTerm2/WezTerm | `references/platform-migration.md` |

## Reference Files

| File | Contents |
|------|----------|
| `references/config-reference.md` | Config file locations and format, fonts (family/size/features/variation), window and appearance, cursor, scrollback, mouse, clipboard, shell command, notifications, custom shaders, CLI utilities |
| `references/themes-and-appearance.md` | Built-in theme system (500+ from iterm2-color-schemes), applying and listing themes, light/dark auto-switching, custom theme authoring, background images and transparency, color palette, cursor styles, alpha blending, community theme tools |
| `references/keybindings-and-input.md` | Keybind syntax, modifiers and trigger prefixes (all:/global:/unconsumed:/performable:), key sequences, key tables (modal mode), complete action catalog by category, tmux-style split recipes, quick terminal setup, font size bindings |
| `references/shell-integration-features.md` | Auto-injection for zsh/bash/fish/elvish, manual setup snippets, feature flags (cursor/sudo/ssh/title), SSH and sudo wrapping, env variables (GHOSTTY_RESOURCES_DIR/BIN_DIR), $TERM and terminfo, OSC sequences, command finish notifications, verification |
| `references/platform-migration.md` | macOS-specific config (option-as-alt, titlebar, global keybinds, AppleScript), Linux GTK (single-instance mode, Wayland/X11, adwaita feature matrix, FreeType rendering), community tools (ghostty.nvim, ghostty-ghost converter, ghostty.style), migration tables from iTerm2/kitty/alacritty/WezTerm |

## Scripts

| Script | Usage |
|--------|-------|
| `scripts/show-config.sh` | `bash show-config.sh <config\|defaults\|fonts\|themes\|keybinds\|diff\|search\|version>` |
