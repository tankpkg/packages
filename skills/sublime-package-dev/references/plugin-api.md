# Sublime Text Plugin API

Sources: Sublime Text Official API Reference (sublimetext.com/docs/api_reference.html), ST Community Docs (docs.sublimetext.io), Build 4200 Blog Post (2025)

Covers: `sublime` module, `sublime_plugin` base classes, View/Window/Region/Settings objects, event listeners, input handlers, threading, ST4 enumerations. Does NOT cover file formats (see package-structure.md) or syntax definitions (see syntax-definitions.md).

## Plugin Lifecycle

Plugins run in a separate `plugin_host` process. A crashing plugin does not
crash the editor. All packages share one Python environment.

```python
def plugin_loaded():
    """Called when API is ready. Safe to call all functions here."""

def plugin_unloaded():
    """Called just before plugin is unloaded."""
```

At import time, only these functions are safe to call:
`sublime.version()`, `sublime.platform()`, `sublime.arch()`, `sublime.channel()`,
`sublime.executable_path()`, `sublime.packages_path()`,
`sublime.installed_packages_path()`, `sublime.cache_path()`

## Command Classes

All commands live in `sublime_plugin`. Class name determines command string:
`MyFooBarCommand` becomes `my_foo_bar`.

### TextCommand

Operates on a `View`. Receives `edit` object for buffer modifications.

```python
class InsertTimestampCommand(sublime_plugin.TextCommand):
    def run(self, edit, format="%Y-%m-%d"):
        import datetime
        stamp = datetime.datetime.now().strftime(format)
        for region in self.view.sel():
            self.view.replace(edit, region, stamp)

    def is_enabled(self):
        return not self.view.is_read_only()
```

### WindowCommand

Operates on a `Window`. No `edit` parameter.

```python
class OpenRelatedFileCommand(sublime_plugin.WindowCommand):
    def run(self, extension=".test.py"):
        view = self.window.active_view()
        if view and view.file_name():
            base = view.file_name().rsplit(".", 1)[0]
            self.window.open_file(base + extension)
```

### ApplicationCommand

App-wide. No `.window` or `.view` attribute.

```python
class ToggleGlobalSettingCommand(sublime_plugin.ApplicationCommand):
    def run(self, setting):
        s = sublime.load_settings("Preferences.sublime-settings")
        s.set(setting, not s.get(setting, False))
        sublime.save_settings("Preferences.sublime-settings")
```

### Common Command Methods

| Method | Purpose |
|--------|---------|
| `run(self, edit?, **args)` | Execute the command |
| `is_enabled(self, **args)` | Grayed out if False |
| `is_visible(self, **args)` | Hidden if False |
| `description(self, **args)` | Text shown in undo/redo menu |
| `input(self, args)` | Return InputHandler for Command Palette input |
| `want_event(self)` | Return True to receive `event` arg with mouse info |

## Input Handlers

Prompt users for input via Command Palette.

```python
class GreetCommand(sublime_plugin.WindowCommand):
    def run(self, name):
        sublime.message_dialog(f"Hello, {name}!")

    def input(self, args):
        if "name" not in args:
            return NameInputHandler()

class NameInputHandler(sublime_plugin.TextInputHandler):
    def placeholder(self):
        return "Enter your name"

    def validate(self, text):
        return len(text) > 0
```

| Handler | Use Case |
|---------|----------|
| `TextInputHandler` | Free-text entry |
| `ListInputHandler` | Selection from list (use `list_items()`) |
| `BackInputHandler` | Navigate back in multi-step input |

Key methods: `name()`, `placeholder()`, `initial_text()`/`list_items()`,
`validate()`, `confirm()`, `preview()`, `next_input()`.

## Event Listeners

### EventListener (Global)

Receives events from all views. Do not implement events you do not need.

```python
class AutoSaveListener(sublime_plugin.EventListener):
    def on_modified_async(self, view):
        if view.file_name() and view.is_dirty():
            view.run_command("save")
```

| Event | Fires When |
|-------|------------|
| `on_new(view)` | New buffer created |
| `on_load(view)` / `on_load_async` | File loaded from disk |
| `on_pre_save(view)` / `on_post_save(view)` | Before/after save |
| `on_pre_close(view)` / `on_close(view)` | Before/after tab close |
| `on_modified(view)` / `on_modified_async` | Buffer text changed |
| `on_selection_modified(view)` | Cursor/selection changed |
| `on_activated(view)` | View gains focus |
| `on_hover(view, point, zone)` | Mouse hover (zone: TEXT, GUTTER, MARGIN) |
| `on_query_completions(view, prefix, locations)` | Autocomplete requested |
| `on_query_context(view, key, op, operand, match_all)` | Key binding context query |
| `on_text_changed(view, changes)` | ST4: detailed change info |

Performance: `on_modified` and `on_selection_modified` fire extremely frequently.
Use `_async` variants when possible. Keep handlers fast.

### ViewEventListener (Scoped)

Attaches to specific views. Has `self.view` attribute.

```python
class PythonOnlyListener(sublime_plugin.ViewEventListener):
    @classmethod
    def is_applicable(cls, settings):
        return settings.get("syntax", "").endswith("Python.sublime-syntax")

    def on_hover(self, point, hover_zone):
        if hover_zone == sublime.HoverZone.TEXT:
            word = self.view.substr(self.view.word(point))
            self.view.show_popup(f"<b>{word}</b>", sublime.HIDE_ON_MOUSE_MOVE_AWAY, point)
```

### TextChangeListener (ST4)

Attaches to a `Buffer`, not a `View`. Use for precise change tracking.

```python
class MyChangeListener(sublime_plugin.TextChangeListener):
    def on_text_changed(self, changes):
        for change in changes:
            print(f"Changed at {change.a}: '{change.str}'")
```

## View Object

The `View` represents an open text buffer.

### Text Operations (require `edit` from TextCommand)

```python
view.insert(edit, point, "text")       # Returns chars inserted
view.erase(edit, region)               # Erase region
view.replace(edit, region, "new text") # Replace region
```

### Reading Content

| Method | Returns |
|--------|---------|
| `view.substr(region_or_point)` | String content |
| `view.size()` | Buffer length (int) |
| `view.line(point)` | Region of full line |
| `view.word(point)` | Region of word at point |
| `view.find(pattern, start, flags)` | First match Region |
| `view.find_all(pattern, flags)` | All match Regions |

### Selection

```python
sel = view.sel()          # Selection object (iterable of Regions)
sel.clear()               # Remove all cursors
sel.add(sublime.Region(0, 10))  # Add selection
sel.add(42)               # Add cursor at point
for region in sel:
    print(view.substr(region))
```

### Scopes and Syntax

```python
view.scope_name(point)               # Full scope string at point
view.match_selector(point, "source.python")  # Bool
view.score_selector(point, "string")  # Int (0 = no match)
view.syntax()                         # ST4: Syntax object
```

### Regions and Decorations

```python
# Add gutter icons and underlines
view.add_regions("my_key", regions, "region.redish",
    "dot", sublime.DRAW_NO_FILL | sublime.DRAW_SQUIGGLY_UNDERLINE)

view.get_regions("my_key")    # Retrieve
view.erase_regions("my_key")  # Remove

# Status bar
view.set_status("my_key", "Line count: 42")
view.erase_status("my_key")
```

### Popups and Phantoms

```python
# Popup (minihtml)
view.show_popup("<b>Info</b>", sublime.HIDE_ON_MOUSE_MOVE_AWAY,
    location=point, max_width=400)

# Phantom (inline HTML widget)
phantom = sublime.Phantom(region, "<span>Error here</span>",
    sublime.LAYOUT_BELOW)
phantom_set = sublime.PhantomSet(view, "my_phantoms")
phantom_set.update([phantom])
```

### Coordinates

```python
view.rowcol(point)           # (row, col) 0-indexed
view.text_point(row, col)    # Point from row/col
view.visible_region()        # Currently visible Region
view.show(point)             # Scroll to point
view.show_at_center(point)   # Center viewport on point
```

## Window Object

```python
window = sublime.active_window()
window.active_view()               # Current view
window.views()                     # All open views
window.new_file()                  # Create scratch buffer
window.open_file("path", flags)    # Open file
window.folders()                   # Project folders
window.run_command("cmd", args)    # Run WindowCommand

# Quick panel
window.show_quick_panel(["Option A", "Option B"],
    on_done=lambda idx: print(idx))

# Input panel
window.show_input_panel("Search:", "", on_done, on_change, on_cancel)

# Output panel
panel = window.create_output_panel("my_panel")
panel.run_command("append", {"characters": "Build output...\n"})
window.run_command("show_panel", {"panel": "output.my_panel"})
```

## Settings

Three-tier merge: Default (package) -> User -> Project.

```python
# Package settings
settings = sublime.load_settings("MyPackage.sublime-settings")
value = settings.get("key", default)
settings.set("key", value)
sublime.save_settings("MyPackage.sublime-settings")

# View-specific settings
view.settings().get("tab_size")
view.settings().set("word_wrap", True)

# Watch for changes
settings.add_on_change("my_tag", lambda: print("Settings changed"))
settings.clear_on_change("my_tag")
```

## Region Object

```python
r = sublime.Region(10, 20)
r.begin()           # 10 (always min)
r.end()             # 20 (always max)
r.size()            # 10
r.empty()           # False
r.contains(15)      # True
r.intersects(other)  # Bool
r.cover(other)       # Smallest region covering both
```

## Global Functions

| Function | Purpose |
|----------|---------|
| `sublime.active_window()` | Current window |
| `sublime.windows()` | All windows |
| `sublime.set_timeout(fn, delay)` | Run on main thread |
| `sublime.set_timeout_async(fn, delay)` | Run on worker thread |
| `sublime.load_resource(name)` | Load package resource as string |
| `sublime.find_resources(pattern)` | Glob search package resources |
| `sublime.score_selector(scope, selector)` | Score scope match |
| `sublime.encode_value(val, pretty)` | Encode to JSON string |
| `sublime.decode_value(string)` | Decode JSON string |
| `sublime.expand_variables(val, vars)` | Expand `${var}` in strings |
| `sublime.list_syntaxes()` | ST4: all available syntaxes |
| `sublime.find_syntax_for_file(path)` | ST4: auto-detect syntax |

## ST4 Key Enumerations

| Enum | Common Values |
|------|---------------|
| `HoverZone` | TEXT, GUTTER, MARGIN |
| `FindFlags` | LITERAL, IGNORECASE, WHOLEWORD, REVERSE, WRAP |
| `RegionFlags` | DRAW_EMPTY, PERSISTENT, DRAW_NO_FILL, DRAW_SQUIGGLY_UNDERLINE, HIDDEN |
| `PopupFlags` | COOPERATE_WITH_AUTO_COMPLETE, HIDE_ON_MOUSE_MOVE_AWAY |
| `AutoCompleteFlags` | INHIBIT_WORD_COMPLETIONS, DYNAMIC_COMPLETIONS |
| `PhantomLayout` | INLINE, BELOW, BLOCK |
| `KindId` | KEYWORD, TYPE, FUNCTION, NAMESPACE, VARIABLE, SNIPPET |
| `CompletionFormat` | TEXT, SNIPPET, COMMAND |

## Python Version

ST4 runs two plugin hosts simultaneously:
- Python 3.3 (legacy, default) - being phased out after Q1 2026
- Python 3.8 (opt-in via `.python-version` file containing `3.8`)
- Python 3.13 planned for next development cycle

Create `.python-version` at package root with content `3.8` to opt in.
