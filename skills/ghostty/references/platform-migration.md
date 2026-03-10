# Platform Differences and Migration

Sources: ghostty.org/docs, ghostty.org/docs/install/release-notes, community dotfiles

## macOS-Specific Features

### Native Integration

macOS Ghostty uses AppKit/Metal and integrates deeply with the OS:

```ini
macos-titlebar-style = tabs           # tabs | transparent | mouse | hidden | native
macos-titlebar-proxy-icon = visible   # visible | hidden
macos-option-as-alt = true           # treat Option as Alt (needed for zsh alt-bindings)
macos-window-shadow = true
macos-non-native-fullscreen = false  # true = hide Dock and menubar, faster
```

### macOS-Only Actions

```ini
keybind = super+shift+t=toggle_window_float_on_top    # always-on-top toggle
keybind = ctrl+shift+s=toggle_secure_input            # prevent keyboard monitoring
keybind = super+shift+u=check_for_updates
# Undo/redo window structure
keybind = super+z=undo
keybind = super+shift+z=redo
```

### Option as Alt

Essential for zsh users (alt-f, alt-b, alt-backspace word movement):
```ini
macos-option-as-alt = true
# Or only left option:
macos-option-as-alt = left
```

### Global Keybinds (Accessibility Permission)

macOS `global:` keybinds require Accessibility permission:
1. Open System Settings > Privacy & Security > Accessibility
2. Enable Ghostty

When Ghostty launches with a `global:` keybind, it prompts for permission automatically.

### AppleScript

Ghostty supports basic AppleScript for automation:
```applescript
tell application "Ghostty"
    new window
    tell current application
        activate
    end tell
end tell
```

See ghostty.org/docs/features/applescript for full API.

## Linux-Specific Features

### GTK Backend

Linux Ghostty uses GTK4 + libadwaita. Feature availability depends on library version:

| Feature | Requires |
|---|---|
| Tab overview UI | adwaita 1.4+ |
| Command palette | adwaita 1.5+ |
| Layer shell (quick terminal) | wlr-layer-shell-v1 protocol |
| Slide-in animations | KDE + "Sliding Popups" KWin plugin |

Check versions: `ghostty +version`

### Single-Instance Mode (10x Faster Startup)

GTK apps start faster when reusing a running instance:
```ini
gtk-single-instance = true     # dramatically faster startup
gtk-single-instance = desktop  # use desktop environment default
```

With single-instance enabled, `ghostty` in the shell opens a new window in the existing
process instead of launching a new process.

### Wayland vs X11

| Feature | Wayland | X11 |
|---|---|---|
| Quick terminal | Yes (wlr-layer-shell) | No |
| Global keybinds | Limited | No |
| Transparency/blur | Compositor-dependent | Compositor-dependent |
| HiDPI | Full support | Works |

Check if running on Wayland: `echo $WAYLAND_DISPLAY`

### FreeType Font Rendering (Linux)

Linux uses FreeType (macOS uses CoreText). Tune for your preference:
```ini
freetype-load-flags = hinting,autohint,light    # defaults, good for most
freetype-load-flags = no-hinting                # for pixel/bitmap fonts
freetype-load-flags = force-autohint            # override font's native hinter
freetype-load-flags = monochrome                # 1-bit, disables anti-aliasing
alpha-blending = linear-corrected               # best text quality on Linux
```

### Window Decorations Toggle

```ini
window-decoration = true       # show titlebar by default
keybind = super+shift+d=toggle_window_decorations   # toggle at runtime
```

## Version History Gotchas

### 1.2.0 Breaking Changes

- **Theme names changed to Title Case**: `catppuccin-mocha` → `Catppuccin Mocha`
- **Keyboard handling overhauled**: some custom keybinds may need updating
- **Font ligatures disabled by default**: re-enable with `font-feature = calt`
- **Background image support added**
- **alpha-blending option added**

### 1.3.0 (Latest, March 2026)

- **Scrollback search added** (cmd+f macOS, ctrl+shift+f GTK)
- **Native scrollbars** added
- **cursor-click-to-move** option added (click to position in prompts)
- **palette-generate / palette-harmonious** options added
- **selection-word-chars** option added
- **language** option added (GTK, UI localization)
- **Security fix**: CVE-2026-26982 (control chars in pasted text)

## Migrating from Other Terminals

### From kitty

| kitty | Ghostty equivalent |
|---|---|
| `font_family` | `font-family` |
| `font_size` | `font-size` |
| `background_opacity` | `background-opacity` |
| `background` | `background` |
| `tab_bar_style` | No direct equivalent; use native tabs |
| `map ctrl+shift+enter new_window` | `keybind = ctrl+shift+enter=new_window` |
| `include` | `config-file` |
| `kitty @` remote control | No equivalent (AppleScript on macOS) |
| `layout splits` | Built-in splits via keybinds |

**kitty-specific**: `kitten` tools (icat, diff, ssh) have no Ghostty equivalent. icat is
replaced by Ghostty's native image rendering (sixel/kitty-graphics). For other kittens,
keep kitty installed or find standalone alternatives.

### From iTerm2 (macOS)

| iTerm2 | Ghostty equivalent |
|---|---|
| Profiles | Multiple config files with `config-file` or `--config-file` flag |
| Hotkey Window | `toggle_quick_terminal` with `global:` keybind |
| Shell Integration | Built-in; auto-injected |
| Triggers | No equivalent |
| Coprocesses | No equivalent |
| Badges | No equivalent |
| Python API | AppleScript for basic automation |
| Smart Selection | `selection-word-chars` customization |
| Marks (jump to prompt) | `jump_to_prompt` via shell integration |

iTerm2's triggers and coprocesses have no Ghostty equivalent. If you rely on these
heavily, iTerm2 may still be the better choice.

### From Alacritty

| Alacritty | Ghostty equivalent |
|---|---|
| `font.normal.family` | `font-family` |
| `font.size` | `font-size` |
| `window.opacity` | `background-opacity` |
| `key_bindings` | `keybind` |
| `shell` | `command` |
| `colors.primary.background` | `background` |
| `import` | `config-file` |
| Multiplexer-only for splits | Built-in splits |

Alacritty has no built-in tabs or splits — everything goes through tmux. Ghostty's native
splits may let you reduce tmux usage.

### From WezTerm

| WezTerm (Lua config) | Ghostty equivalent |
|---|---|
| `config.font` | `font-family` |
| `config.font_size` | `font-size` |
| `config.color_scheme` | `theme` |
| `config.window_background_opacity` | `background-opacity` |
| `config.keys` table | `keybind` lines |
| `config.tab_bar_at_bottom` | `gtk-tabs-location = bottom` (Linux) |
| `SplitHorizontal`/`SplitVertical` | `new_split:right` / `new_split:down` |
| `config.window_decorations` | `window-decoration` |
| Event-driven Lua API | No scripting equivalent |
| `wezterm.action` functions | Ghostty actions |

WezTerm's Lua API allows arbitrarily complex configurations. Ghostty deliberately avoids a
scripting layer. If you rely on WezTerm's event hooks or dynamic config generation, that
logic needs to move into shell startup scripts or external tools.

## Community Tools and Ecosystem

| Tool | Stars | Purpose |
|---|---|---|
| ghostty.zerebos.com | 2,900 | Visual config editor with live preview |
| spectre-ghostty-config.vercel.app | 115 | Config generator with WASM renderer |
| ghostty.style | — | 460+ theme catalog with previews |
| isak102/ghostty.nvim | — | Neovim plugin: validate config, open config file |
| gambithunt/ghostty-ghost | — | Convert kitty/alacritty configs to Ghostty format |
| dacrab/ghostty-config | 15 | 18 handcrafted color themes with install script |

### Neovim Integration (ghostty.nvim)

```lua
-- lazy.nvim
{ "isak102/ghostty.nvim" }
```

Provides:
- `:Ghostty open_config` — open config in editor
- `:Ghostty check_config` — validate config, show errors
- Highlights Ghostty config files with syntax colors

### Config Converter (ghostty-ghost)

Converts other terminal configs automatically:
```sh
ghostty-ghost --from kitty ~/.config/kitty/kitty.conf
ghostty-ghost --from alacritty ~/.config/alacritty/alacritty.toml
```

## $TERM Compatibility Reference

| Scenario | Setting | Why |
|---|---|---|
| Default | `term = ghostty` | Full capability, modern features |
| Remote SSH without terminfo | `term = xterm-256color` | Universal fallback |
| tmux inside Ghostty | Set in tmux: `set -g default-terminal "tmux-256color"` | tmux manages $TERM internally |
| Old tools complaining | `term = xterm-256color` | Use SSH wrapping instead if possible |

The Ghostty terminfo is not installed on remote hosts by default. Copy it once:
```sh
# From local machine
infocmp -x ghostty | ssh remote-host -- "mkdir -p ~/.terminfo && tic -x -"
```
