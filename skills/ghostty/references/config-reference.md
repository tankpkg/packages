# Config Reference

Sources: ghostty.org/docs/config, ghostty.org/docs/config/reference, ghostty +show-config --default --docs

## Config File Locations

| Platform | Primary Path | Secondary Path |
|----------|-------------|----------------|
| All (XDG) | `~/.config/ghostty/config` | `$XDG_CONFIG_HOME/ghostty/config` |
| macOS | `~/Library/Application Support/com.mitchellh.ghostty/config` | Same XDG path |
| Themes | `~/.config/ghostty/themes/` | `$XDG_CONFIG_HOME/ghostty/themes/` |

## Config Format Basics

```ini
# Comments use hash
font-family = JetBrains Mono
font-size = 14
theme = Catppuccin Frappe

# Repeatable options use multiple lines (font fallbacks)
font-family = "JetBrains Mono"
font-family = "Symbols Nerd Font Mono"
font-family = "Apple Color Emoji"

# Reset a repeatable option before setting new values
font-family = ""
font-family = "My Preferred Font"
```

Include additional config files (loaded after user config):
```ini
config-file = ~/.config/ghostty/work-config
```

Reload config without restarting: use `reload_config` keybind or send `SIGHUP`.

## Font Configuration

### Font Family

```ini
font-family = "JetBrains Mono"
font-family-bold = "JetBrains Mono"        # optional, falls back to font-family
font-family-italic = "JetBrains Mono"      # optional
font-family-bold-italic = "JetBrains Mono" # optional
```

List available fonts: `ghostty +list-fonts`

Ghostty synthesizes bold/italic if a variant is unavailable. Disable:
```ini
font-synthetic-style = no-bold,no-italic,no-bold-italic
# or disable all:
font-synthetic-style = false
```

### Font Size and Adjustments

```ini
font-size = 14          # points, non-integer allowed (e.g., 13.5)
```

Fine-tune rendering metrics (integer pixels or percentage):
```ini
adjust-cell-width = 0         # widen/narrow cells
adjust-cell-height = 2        # add vertical breathing room
adjust-font-baseline = -1     # move baseline up/down
adjust-underline-position = 1
adjust-underline-thickness = 1
adjust-cursor-height = 0
adjust-icon-height = 0        # nerd font icon sizing
```

### OpenType Features

```ini
font-feature = -calt           # disable ligatures (programming)
font-feature = -calt,-liga,-dlig  # disable most ligatures
font-feature = ss01            # enable stylistic set 1
font-feature = "calt on"       # CSS-compatible syntax
```

### Variable Fonts

```ini
font-variation = wght=450      # weight axis
font-variation-bold = wght=700
```

### Font Rendering Quality

```ini
font-thicken = true            # macOS only: thicker strokes
font-thicken-strength = 128    # 0-255, macOS only
grapheme-width-method = unicode # or legacy (for older shells)
alpha-blending = linear-corrected  # best text rendering on Linux
# options: native (macOS default), linear, linear-corrected (Linux default)
```

### Codepoint Mapping

Force specific codepoints to a named font:
```ini
font-codepoint-map = U+E000-U+F8FF=Symbols Nerd Font Mono
```

Replace characters on clipboard copy (e.g., box-drawing to ASCII):
```ini
clipboard-codepoint-map = U+2500=U+002D
clipboard-codepoint-map = U+2502=U+007C
```

## Window and Appearance

```ini
window-width = 120             # columns
window-height = 36             # rows
window-padding-x = 8           # horizontal padding pixels
window-padding-y = 4           # vertical padding pixels
window-padding-balance = true  # center content in window

window-decoration = true       # show title bar / decorations
window-title = "My Terminal"   # static title override
background-opacity = 0.95      # 0.0-1.0, requires compositor support
background-blur-radius = 20    # blur behind transparent window (Linux/macOS)
```

### Background Image (since 1.2.0)

```ini
background-image = /path/to/image.png  # PNG or JPEG
background-image-opacity = 0.15        # relative to background-opacity
background-image-fit = contain         # contain | cover | stretch | none
background-image-position = center     # top-left, top-center, ..., bottom-right
background-image-repeat = false
```

## Cursor

```ini
cursor-style = bar              # block | bar | underline | block_hollow
cursor-style-blink = true       # true | false | (blank = respect DEC mode 12)
cursor-color = cell-foreground  # hex #RRGGBB, cell-foreground, cell-background
cursor-text = cell-background   # color of text under cursor
cursor-opacity = 1.0            # 0.0-1.0
cursor-click-to-move = true     # move cursor by clicking prompt (needs shell integration)
```

## Scrollback and Scrolling

```ini
scrollback-limit = 10000        # lines; 0 = unlimited
scroll-to-bottom = keystroke    # keystroke, output, or no-keystroke,no-output
```

## Mouse

```ini
mouse-hide-while-typing = true
mouse-shift-capture = false     # let Ghostty handle shift+click, not the app
```

## Clipboard

```ini
clipboard-read = ask            # allow | deny | ask
clipboard-write = allow         # allow | deny | ask
clipboard-trim-trailing-spaces = true
copy-on-select = clipboard      # clipboard | primary | false
```

## Selection Behavior

```ini
selection-clear-on-typing = true       # clear selection when typing
selection-clear-on-copy = false        # clear selection after copy
selection-word-chars = " \t'\"│`|:;,()\[\]{}<>$"  # word boundary chars
minimum-contrast = 1.0          # WCAG contrast ratio 1-21; 1.1 prevents invisible text
```

## Shell and Command

```ini
command = /bin/zsh              # override default shell
command = tmux new-session -A -s main  # launch tmux by default
initial-command = neofetch      # run once at start, then hand off to shell
term = xterm-256color           # override $TERM (usually ghostty)
```

## Other Useful Options

```ini
confirm-close-surface = true    # ask before closing with running process
quit-after-last-window-closed = false  # macOS: keep app in dock
window-step-resize = true       # snap to character grid when resizing
focus-follows-mouse = true      # auto-focus split under cursor
```

## CLI Utilities (Self-Documentation)

These commands are the ground truth for your current Ghostty installation:

| Command | Purpose |
|---------|---------|
| `ghostty +show-config` | Merged effective config (all sources) |
| `ghostty +show-config --default --docs` | All options with documentation |
| `ghostty +list-fonts` | Fonts Ghostty can render |
| `ghostty +list-themes` | All available themes (built-in + custom) |
| `ghostty +list-keybinds` | Current keybind mappings |
| `ghostty +list-keybinds --default` | Default keybinds before user overrides |
| `ghostty +version` | Version, platform, and linked library versions |
| `ghostty --config-file=path` | Start with a specific config file |

## Config Reloading

Changes take effect without restart for most options. Reload via:
- Keybind: `keybind = ctrl+shift+r=reload_config` (set this yourself)
- Signal: `kill -HUP $(pgrep ghostty)`
- Menu: Ghostty > Reload Configuration (macOS)

Options that require a full restart (not reloadable at runtime):
- `shell-integration` type
- `term` value
- `command`
- `language` (GTK)
- `window-decoration` (some platforms)

## Notifications

```ini
notify-on-command-finish = 30    # notify if command takes >30 seconds
notify-on-command-finish = 0     # disable (default)
```

When enabled, Ghostty shows a system notification when a long-running command completes,
useful for `make`, `npm install`, long test runs, etc.

## Custom GLSL Shaders

Apply post-processing effects to the terminal surface:

```ini
custom-shader = /path/to/shader.glsl
custom-shader-animation = false     # true = re-render every frame (animated shaders)
```

Shaders receive `iTime`, `iResolution`, `iChannel0` (terminal texture) uniforms.
Community shaders: search GitHub for "ghostty shader glsl". Examples:
- CRT scanline effect
- Subtle film grain / noise
- Color grading and vignette

Performance note: `custom-shader-animation = true` disables idle optimizations.
Use only when the shader actually animates.

## Validating Config

Ghostty logs errors on startup. Check:
```sh
ghostty +show-config 2>&1 | grep -i error
```

Or test a specific config file without using it:
```sh
ghostty --config-file=/path/to/test-config +show-config
```
