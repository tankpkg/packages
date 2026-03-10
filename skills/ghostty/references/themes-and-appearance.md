# Themes and Appearance

Sources: ghostty.org/docs/features/theme, ghostty.org/docs/config/reference, iterm2colorschemes.com

## Theme System Overview

Ghostty ships with hundreds of built-in themes sourced from iterm2-color-schemes and updated
weekly. A theme is simply another config file that sets color options first; user config
overrides anything in the theme.

Themes can set any config option — not just colors. Treat themes from untrusted sources with
the same caution as arbitrary shell scripts.

## Applying a Built-in Theme

```ini
theme = Catppuccin Frappe
```

List all available themes:
```sh
ghostty +list-themes
```

Browse with previews at iterm2colorschemes.com.

After changing the theme, reload config: use the `reload_config` keybind or restart Ghostty.

## Popular Built-in Themes

Dark themes:
```
Catppuccin Frappe
Catppuccin Macchiato
Catppuccin Mocha
Dracula
Tokyo Night
Tokyo Night Storm
Nord
Rose Pine
Rose Pine Moon
Everforest Dark Medium
Solarized Dark
One Dark Pro
Gruvbox Dark
Kanagawa Wave
```

Light themes:
```
Catppuccin Latte
Rose Pine Dawn
Solarized Light
One Light
Papercolor Light
Github Light
```

Note: In version 1.2.0, theme names changed from kebab-case to Title Case.
Old: `catppuccin-mocha` → New: `Catppuccin Mocha`. If themes appear broken after
upgrading, update theme names in your config.

## Automatic Light/Dark Switching

Ghostty switches between themes when the OS appearance changes:

```ini
theme = dark:Catppuccin Frappe,light:Catppuccin Latte
theme = dark:Tokyo Night,light:Github Light
theme = dark:Rose Pine,light:Rose Pine Dawn
```

Order of `dark:` and `light:` does not matter. Both must be specified.

## Authoring a Custom Theme

A theme file is a Ghostty config file. Place it in `~/.config/ghostty/themes/` and reference
by filename (without extension):

```ini
# ~/.config/ghostty/config
theme = my-theme
```

Minimal theme template (16-color palette + chrome):
```ini
# ~/.config/ghostty/themes/my-theme

# Terminal palette: indices 0-15 (ANSI colors)
palette = 0=#1e1e2e    # black
palette = 1=#f38ba8    # red
palette = 2=#a6e3a1    # green
palette = 3=#f9e2af    # yellow
palette = 4=#89b4fa    # blue
palette = 5=#cba6f7    # magenta
palette = 6=#94e2d5    # cyan
palette = 7=#cdd6f4    # white
palette = 8=#585b70    # bright black
palette = 9=#f38ba8    # bright red
palette = 10=#a6e3a1   # bright green
palette = 11=#f9e2af   # bright yellow
palette = 12=#89b4fa   # bright blue
palette = 13=#cba6f7   # bright magenta
palette = 14=#94e2d5   # bright cyan
palette = 15=#a6adc8   # bright white

# Window chrome
background = #1e1e2e
foreground = #cdd6f4
cursor-color = #f5e0dc
cursor-text = #cdd6f4
selection-background = #585b70
selection-foreground = #cdd6f4
```

### Extended Palette Generation

For themes that only define 16 base colors, have Ghostty auto-generate colors 16-255:

```ini
palette-generate = true         # derive 256-color palette from base 16
palette-harmonious = true       # invert order for better light/dark compat
```

Do not use `palette-generate` if the theme explicitly sets indices 16-255 — it won't
overwrite explicit entries, but legacy programs may break.

## Color Options Reference

### Window Colors

```ini
background = #1e1e2e      # or named X11 color
foreground = #cdd6f4
```

### Cursor Colors

```ini
cursor-color = #f5e0dc           # hex, cell-foreground, or cell-background
cursor-text = #cdd6f4            # text color under cursor
cursor-opacity = 1.0             # 0.0 fully transparent, 1.0 fully opaque
```

### Selection Colors

```ini
selection-background = #585b70   # or cell-background
selection-foreground = #cdd6f4   # or cell-foreground
selection-clear-on-typing = true
selection-clear-on-copy = false
```

### Contrast and Accessibility

```ini
minimum-contrast = 1.1   # prevents invisible text (same color as bg)
# 1.0 = no constraint, 3.0 = readable, 7.0 = WCAG AAA
```

## Background Transparency and Blur

```ini
background-opacity = 0.92        # 0.0-1.0; requires compositor
background-blur-radius = 20      # pixels; macOS + some Linux compositors
```

Toggle transparency without restart: bind `toggle_background_opacity` action.
```ini
keybind = ctrl+shift+t=toggle_background_opacity
```

## Background Images (since 1.2.0)

```ini
background-image = ~/wallpapers/bg.png   # PNG or JPEG
background-image-opacity = 0.15          # relative to background-opacity
background-image-fit = contain           # contain | cover | stretch | none
background-image-position = center       # top-left, center, bottom-right, etc.
background-image-repeat = false
```

For a subtle texture: set `background-image-opacity = 0.05` to 0.15.
For a wallpaper: use `background-image-fit = cover`, higher opacity.

Multiple splits each render the background image independently (current limitation).

## Alpha Blending

Controls how text anti-aliasing interacts with background color:

```ini
alpha-blending = linear-corrected   # best on Linux/dark backgrounds
alpha-blending = native             # macOS default (Display P3)
alpha-blending = linear             # removes dark halos, thins light text
```

`linear-corrected` eliminates the color-fringing artifacts visible with
certain foreground/background combinations (e.g., red text on dark bg) while
preserving text weight. Use it on Linux; `native` is fine on macOS.

## Selection Word Characters

Double-click selects a word. Customize what counts as a word boundary:

```ini
# Default: space, tab, quotes, pipes, colons, semicolons, brackets, etc.
selection-word-chars = " \t'\"│`|:;,()\[\]{}<>$"
```

Remove `=` to select shell variable assignments as single words.

## Theme Directories and Discovery

| Resource | URL | Contents |
|---|---|---|
| ghostty.style | ghostty-style.vercel.app | 460+ curated themes with previews |
| iterm2-color-schemes | iterm2colorschemes.com | Source of all built-in themes |
| ghostty.zerebos.com | ghostty.zerebos.com | Web config generator (2900+ stars) |

To browse themes interactively without leaving the terminal:
```sh
ghostty +list-themes | fzf --preview 'echo theme = {}' | pbcopy   # macOS
ghostty +list-themes | fzf --preview 'echo theme = {}' | xclip    # Linux
```

## Cursor Styles

```ini
cursor-style = bar              # recommended for editing
cursor-style = block            # traditional
cursor-style = underline
cursor-style = block_hollow     # outline block
cursor-style-blink = true       # | false | (blank = OS preference)
```

Shell integration overrides cursor to bar at the prompt automatically.
Disable: `shell-integration-features = no-cursor`

## Window Padding and Balance

Padding affects how colors interact visually with the theme:

```ini
window-padding-x = 12           # horizontal padding in pixels
window-padding-y = 8            # vertical padding in pixels
window-padding-balance = true   # center content, equal padding all sides
window-padding-color = background    # background | extend | extend-always
```

`window-padding-color = extend` bleeds the terminal's edge colors into the padding area,
giving a cleaner look with themes that have colored backgrounds.

## Community Config Generators

- **ghostty.zerebos.com** — Visual config editor with live preview (2900+ stars)
- **spectre-ghostty-config.vercel.app** — Preview with libghostty WASM renderer, 200+ themes
