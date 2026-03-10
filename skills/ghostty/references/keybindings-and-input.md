# Keybindings and Input

Sources: ghostty.org/docs/config/keybind, ghostty.org/docs/config/keybind/reference

## Syntax

```ini
keybind = trigger=action
keybind = ctrl+shift+t=new_tab
keybind = super+shift+f=toggle_fullscreen
```

View all default keybinds: `ghostty +list-keybinds --default`
View current effective keybinds: `ghostty +list-keybinds`

## Triggers

### Modifiers

| Config value | Aliases | Notes |
|---|---|---|
| `shift` | — | |
| `ctrl` | `control` | |
| `alt` | `opt`, `option` | |
| `super` | `cmd`, `command` | macOS Cmd / Linux Win |

Combine: `ctrl+shift+a`, `super+alt+k`, `ctrl+shift+alt+t`

The `fn` / globe key is not supported as a modifier.

### Unicode Keys

Use a Unicode codepoint directly for non-US layouts:
```ini
keybind = ctrl+ö=new_tab          # German keyboard
keybind = super+á=toggle_fullscreen
```

## Trigger Prefixes

Prefixes modify how and where the keybind applies. Multiple prefixes can stack.

```ini
keybind = global:super+grave=toggle_quick_terminal
keybind = unconsumed:ctrl+shift+r=reload_config
keybind = all:ctrl+shift+q=close_window
keybind = performable:ctrl+c=copy_to_clipboard
keybind = global:unconsumed:super+k=clear_screen
```

| Prefix | Effect |
|---|---|
| `all:` | Apply to all terminal surfaces (not just focused) |
| `global:` | Works even when Ghostty is not focused (macOS only, needs Accessibility permission) |
| `unconsumed:` | Pass encoded key to terminal app in addition to running action |
| `performable:` | Only consume key if action can be performed (e.g., only copy if text selected) |

`global:` implies `all:`. Keybind triggers are not unique per prefix — later entries win.

## Key Sequences (Tmux-style Leader)

Chain keys with `>`:
```ini
keybind = ctrl+w>h=goto_split:left
keybind = ctrl+w>l=goto_split:right
keybind = ctrl+w>j=goto_split:down
keybind = ctrl+w>k=goto_split:up
keybind = ctrl+w>ctrl+w=goto_split:next
keybind = ctrl+w>v=new_split:right
keybind = ctrl+w>s=new_split:down
keybind = ctrl+w>z=toggle_split_zoom
```

Cancel a sequence without sending keys: `end_key_sequence`
```ini
keybind = ctrl+w>escape=end_key_sequence
```

## Unbinding Defaults

```ini
keybind = ctrl+shift+c=unbind    # remove default copy binding
keybind = super+t=unbind         # remove default new tab (macOS)
```

## Actions Reference

### Navigation and Window Management

```ini
new_window
new_tab
close_surface          # close focused window/tab/split
close_tab              # close current tab
close_window           # close entire window
toggle_maximize        # maximize/restore (Linux)
toggle_fullscreen
toggle_window_decorations       # show/hide titlebar (Linux)
toggle_window_float_on_top      # always-on-top (macOS)
goto_window:previous
goto_window:next
```

### Tabs

```ini
new_tab
previous_tab
next_tab
last_tab
goto_tab:1             # go to tab by index (1-based)
move_tab:1             # move tab right by 1
move_tab:-1            # move tab left by 1
toggle_tab_overview    # tab switcher UI (Linux, adwaita 1.4+)
prompt_tab_title       # rename tab interactively
prompt_surface_title   # rename surface (split) interactively
```

### Splits

```ini
new_split:right        # right | down | left | up | auto
new_split:auto         # splits along longer dimension
goto_split:right       # right | down | left | up | previous | next
toggle_split_zoom      # zoom in/out of current split
resize_split:right,20  # direction,pixels
resize_split:left,10
equalize_splits        # make all splits equal size
toggle_readonly        # prevent input to current split
```

### Scrollback

```ini
scroll_to_top
scroll_to_bottom
scroll_to_selection
scroll_page_up
scroll_page_down
scroll_page_fractional:0.5     # half page down, negative = up
scroll_page_lines:5            # 5 lines down, negative = up
scroll_to_row:0                # absolute row number
clear_screen                   # clear screen + scrollback
```

### Search (since 1.3.0)

```ini
start_search            # open search UI
end_search              # close search UI
search_selection        # search for selected text
navigate_search:next    # next match (also just navigate_search)
navigate_search:previous
```

### Clipboard

```ini
copy_to_clipboard
paste_from_clipboard
paste_from_selection    # X11 selection clipboard
copy_url_to_clipboard   # copy URL under cursor
copy_title_to_clipboard
```

### Font Size

```ini
increase_font_size:1         # increase by 1pt
decrease_font_size:1
reset_font_size
set_font_size:16             # set specific size
```

### Terminal State

```ini
reset                        # reset terminal (escape sequences)
select_all
inspector:toggle             # built-in terminal inspector
open_config                  # open config in default editor
reload_config
toggle_mouse_reporting       # pause mouse event forwarding
toggle_secure_input          # prevent keyboard monitoring (macOS)
```

### Undo/Redo (macOS)

```ini
undo                         # undo last window/tab/split operation
redo
```

Configurable timeout:
```ini
undo-timeout = 10            # seconds before action is no longer undoable
```

### Quick Terminal (Quake-style)

```ini
toggle_quick_terminal        # show/hide dropdown terminal
toggle_visibility            # show/hide all windows (macOS)
toggle_background_opacity    # toggle transparent/opaque
```

## Common Configuration Recipes

### Tmux-like Splits with Ctrl+W Leader

```ini
keybind = ctrl+w>v=new_split:right
keybind = ctrl+w>s=new_split:down
keybind = ctrl+w>h=goto_split:left
keybind = ctrl+w>l=goto_split:right
keybind = ctrl+w>j=goto_split:down
keybind = ctrl+w>k=goto_split:up
keybind = ctrl+w>z=toggle_split_zoom
keybind = ctrl+w>=equalize_splits
keybind = ctrl+w>ctrl+w=goto_split:next
keybind = ctrl+w>escape=end_key_sequence
```

### Quick Terminal (Global Hotkey)

```ini
# macOS: Cmd+` summons terminal from anywhere
keybind = global:super+grave=toggle_quick_terminal

# Linux: Ctrl+` (Wayland only)
keybind = global:ctrl+grave=toggle_quick_terminal
```

Configure quick terminal behavior:
```ini
quick-terminal-position = top          # top | bottom | left | right | center
quick-terminal-screen = main           # main | mouse | macos-menu-bar
quick-terminal-animation-duration = 0.2  # seconds; 0 = no animation
quick-terminal-autohide = true         # hide on focus loss
```

### Jump Between Prompts (Shell Integration Required)

```ini
keybind = super+up=jump_to_prompt:-1   # previous prompt
keybind = super+down=jump_to_prompt:1  # next prompt
```

### Font Size Like a Browser

```ini
keybind = super+equal=increase_font_size:1
keybind = super+minus=decrease_font_size:1
keybind = super+0=reset_font_size
```

### Clipboard Safety (Bracketed Paste)

```ini
# Copy only when selection exists
keybind = performable:ctrl+c=copy_to_clipboard
keybind = ctrl+v=paste_from_clipboard
```

### Search

```ini
keybind = super+f=start_search              # macOS default
keybind = ctrl+shift+f=start_search        # GTK default
keybind = super+g=navigate_search          # macOS default (next match)
keybind = shift+super+g=navigate_search:previous
```

## Key Tables (Modal Keybinds, since 1.3.0)

Key tables enable modal keybinds — a named mode where different bindings apply.
Think of it as a structured alternative to key sequences.

```ini
# Define bindings that only apply inside "splits" mode
keybind = ctrl+w=set_key_table:splits

# These only activate while in the "splits" table
keybind = table:splits>h=goto_split:left
keybind = table:splits>l=goto_split:right
keybind = table:splits>j=goto_split:down
keybind = table:splits>k=goto_split:up
keybind = table:splits>v=new_split:right
keybind = table:splits>s=new_split:down
keybind = table:splits>z=toggle_split_zoom
keybind = table:splits>escape=clear_key_table:splits
```

Actions: `set_key_table:name`, `clear_key_table:name`, `clear_all_key_tables`

Key tables vs sequences: tables are persistent modes (enter/exit explicitly) while
sequences are transient (consume input once matched or fail).

## Write Scrollback to File

```ini
keybind = ctrl+shift+s=write_scrollback_file:open   # open in default editor
keybind = ctrl+shift+s=write_scrollback_file:copy   # copy path to clipboard
keybind = ctrl+shift+s=write_scrollback_file:paste  # paste path into terminal
```
