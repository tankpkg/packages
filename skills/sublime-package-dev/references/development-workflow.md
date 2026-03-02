# Development Workflow and Patterns

Sources: Sublime Text Official Docs (sublimetext.com/docs), ST Community Docs (docs.sublimetext.io), sublimehq/Packages default plugin analysis, popular package patterns (SublimeLinter, GitGutter, BracketHighlighter)

Covers: Local development setup, plugin auto-reload, console debugging, threading patterns, common plugin architectures, settings patterns, error handling, package scaffolding checklist. Does NOT cover file formats (see package-structure.md), API details (see plugin-api.md), or publishing (see publishing.md).

## Local Development Setup

1. Open **Preferences > Browse Packages** to access `<data>/Packages/`
2. Create package directory: `Packages/MyPackage/`
3. Create `.python-version` with content `3.8`
4. Create main plugin file (e.g., `plugin.py` or `my_package.py`)
5. Sublime auto-loads top-level `.py` files immediately

### Project Structure for Development

```
Packages/MyPackage/
├── .python-version          # "3.8"
├── plugin.py                # Entry point (auto-loaded)
├── lib/                     # Helper modules (NOT auto-loaded)
│   ├── __init__.py
│   └── core.py
├── Default.sublime-commands
├── MyPackage.sublime-settings
└── tests/
    └── test_plugin.py
```

## Plugin Auto-Reload

Sublime automatically reloads top-level `.py` files when saved. However:

- **Sub-modules** (`lib/core.py`) are NOT auto-reloaded
- For complex packages: restart Sublime Text
- Manual reload via console:

```python
import importlib
import MyPackage.lib.core
importlib.reload(MyPackage.lib.core)
```

### Reliable Reload Pattern

For packages with sub-modules, use a reload helper in the entry point:

```python
import importlib
import sys

# Reload sub-modules before importing
modules_to_reload = [
    "MyPackage.lib.core",
    "MyPackage.lib.utils",
]

for mod_name in modules_to_reload:
    if mod_name in sys.modules:
        importlib.reload(sys.modules[mod_name])

from .lib.core import MyCore
from .lib.utils import helper_function
```

## Console Debugging

Open console: **Ctrl+`** (backtick) or **View > Show Console**.

### Useful Console Commands

```python
# Inspect active view
view = sublime.active_window().active_view()
view.file_name()
view.size()
view.substr(view.sel()[0])
view.scope_name(view.sel()[0].begin())
view.settings().get("tab_size")

# Run commands manually
view.run_command("my_text_command", {"arg": "value"})
sublime.active_window().run_command("my_window_command")

# Debug logging
sublime.log_commands(True)    # Log every command invocation
sublime.log_input(True)       # Log keyboard/mouse input
sublime.log_result_regex(True) # Log build system regex matching

# Turn off logging
sublime.log_commands(False)
```

### print() Debugging

`print()` in plugin code outputs to the Sublime console. Python exceptions
print full tracebacks automatically.

```python
class MyCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print(f"[MyPackage] Selection: {self.view.sel()[0]}")
        print(f"[MyPackage] Scope: {self.view.scope_name(self.view.sel()[0].begin())}")
```

### Status Bar Debugging

```python
view.set_status("my_debug", f"Cursor at: {view.rowcol(view.sel()[0].begin())}")
```

### Scope Inspector

Press **Ctrl+Shift+P** (Mac) or **Ctrl+Alt+Shift+P** (Win/Linux) to show
scope at cursor. Essential for syntax definition development.

## Threading Patterns

All API functions are thread-safe. However, buffer modifications must happen
on the main thread via `set_timeout`.

### Background Work Pattern

```python
import threading
import sublime
import sublime_plugin

class LongRunningCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.status_message("Processing...")
        thread = threading.Thread(target=self._work)
        thread.start()

    def _work(self):
        result = expensive_operation()
        # Schedule UI update on main thread
        sublime.set_timeout(lambda: self._on_complete(result), 0)

    def _on_complete(self, result):
        view = self.window.active_view()
        view.run_command("my_insert_result", {"text": result})
        self.window.status_message("Done!")
```

### Simple Async Pattern

```python
def on_post_save_async(self, view):
    # Already on worker thread (_async suffix)
    result = check_file(view.file_name())
    # Update UI on main thread
    sublime.set_timeout(lambda: self._show_results(view, result), 0)
```

### set_timeout vs set_timeout_async

| Function | Thread | Use For |
|----------|--------|---------|
| `set_timeout(fn, delay)` | Main | UI updates, buffer modifications |
| `set_timeout_async(fn, delay)` | Worker | Background processing |

## Common Plugin Patterns

### Settings with Defaults

```python
def plugin_loaded():
    global settings
    settings = sublime.load_settings("MyPackage.sublime-settings")

def get_setting(key, default=None):
    return settings.get(key, default)
```

### View-Specific Settings Override

```python
def get_setting_for_view(view, key, default=None):
    # Check view settings first (project-level), then package defaults
    value = view.settings().get(key)
    if value is not None:
        return value
    return sublime.load_settings("MyPackage.sublime-settings").get(key, default)
```

### Output Panel Pattern

```python
class ShowResultsCommand(sublime_plugin.WindowCommand):
    def run(self, results):
        panel = self.window.create_output_panel("my_results")
        panel.settings().set("word_wrap", True)
        panel.run_command("append", {"characters": results})
        self.window.run_command("show_panel", {"panel": "output.my_results"})
```

### Gutter Marks and Regions

```python
class HighlightErrorsListener(sublime_plugin.ViewEventListener):
    @classmethod
    def is_applicable(cls, settings):
        return True

    def on_post_save_async(self):
        errors = run_linter(self.view.file_name())
        regions = []
        for err in errors:
            point = self.view.text_point(err["line"] - 1, 0)
            regions.append(self.view.line(point))

        # Schedule region update on main thread
        sublime.set_timeout(lambda: self.view.add_regions(
            "my_errors", regions, "region.redish",
            "dot", sublime.DRAW_NO_FILL | sublime.DRAW_SQUIGGLY_UNDERLINE
        ), 0)
```

### Hover Popup Pattern

```python
def on_hover(self, point, hover_zone):
    if hover_zone != sublime.HoverZone.TEXT:
        return

    word_region = self.view.word(point)
    word = self.view.substr(word_region)

    info = lookup_docs(word)
    if info:
        self.view.show_popup(
            f"<b>{word}</b><br>{info}",
            sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            point,
            max_width=500
        )
```

### Dynamic Completions

```python
class MyCompletionListener(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], "source.mylang"):
            return None

        items = [
            sublime.CompletionItem(
                trigger="myFunc",
                annotation="My function",
                completion="myFunc(${1:arg})",
                completion_format=sublime.COMPLETION_FORMAT_SNIPPET,
                kind=sublime.KIND_FUNCTION
            )
        ]

        return sublime.CompletionList(
            items,
            flags=sublime.INHIBIT_WORD_COMPLETIONS
        )
```

### Input Handler with Preview

```python
class TransformTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, transform):
        for region in self.view.sel():
            text = self.view.substr(region)
            if transform == "upper":
                self.view.replace(edit, region, text.upper())
            elif transform == "lower":
                self.view.replace(edit, region, text.lower())

    def input(self, args):
        return TransformInputHandler()

class TransformInputHandler(sublime_plugin.ListInputHandler):
    def list_items(self):
        return [
            sublime.ListInputItem("UPPERCASE", "upper", annotation="ABC"),
            sublime.ListInputItem("lowercase", "lower", annotation="abc"),
        ]

    def preview(self, value):
        return f"Transform selection to {value}"
```

## Error Handling

```python
try:
    result = risky_operation()
except Exception as e:
    sublime.error_message(f"MyPackage Error: {e}")
    # Also print traceback to console
    import traceback
    traceback.print_exc()
```

For non-blocking errors, use status bar:

```python
sublime.status_message("MyPackage: Operation failed — check console")
```

## Package Scaffolding Checklist

When creating a new package from scratch:

### Minimal Package (Command Plugin)

```
MyPackage/
├── .python-version          # "3.8"
├── plugin.py                # TextCommand/WindowCommand classes
├── Default.sublime-commands # Command palette entries
└── MyPackage.sublime-settings  # (if package has settings)
```

### Syntax Package

```
MyLang/
├── MyLang.sublime-syntax
├── Comments.tmPreferences   # Toggle Comment support
├── Snippets/
│   └── *.sublime-snippet
├── MyLang.sublime-completions
├── MyLang.sublime-build     # (if language has compiler/runner)
└── tests/
    └── syntax_test_mylang.ext
```

### Theme/Color Scheme Package

```
MyTheme/
├── MyTheme.sublime-color-scheme
├── MyTheme.sublime-theme    # (if also customizing UI)
└── icons/                   # (if theme has custom icons)
```

### Full-Featured Package

```
MyPackage/
├── .python-version
├── .gitignore
├── .gitattributes
├── LICENSE
├── README.md
├── plugin.py
├── lib/
├── Default.sublime-commands
├── Main.sublime-menu
├── Default (OSX).sublime-keymap
├── Default (Windows).sublime-keymap
├── Default (Linux).sublime-keymap
├── Example.sublime-keymap    # Commented-out suggestions
├── MyPackage.sublime-settings
├── messages.json
├── messages/
│   └── install.txt
├── unittesting.json
├── tests/
│   └── test_plugin.py
└── .github/
    └── workflows/
        └── test.yml
```

## Typing Stubs for IDE Support

For autocompletion and type checking during development:

- [ST-API-stubs](https://github.com/jfcherng-sublime/ST-API-stubs) — `.pyi` stubs
  for `sublime`, `sublime_plugin`, `sublime_api`

```bash
pip install sublime-api-stubs
```

Or add to `pyrightconfig.json`:

```json
{"stubPath": "./path/to/ST-API-stubs/typings"}
```

## Study Default Plugins

Use **Command Palette > View Package File** and filter for `Default/*.py`:

| File | Demonstrates |
|------|-------------|
| `exec.py` | Phantoms, build system integration |
| `font.py` | Settings, `add_on_change` |
| `goto_line.py` | TextInputHandler, updating selection |
| `mark.py` | `add_regions()`, gutter icons |
| `show_scope_name.py` | Popups, `scope_name()` |
| `arithmetic.py` | ListInputHandler, Command Palette input |
