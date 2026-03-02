# Package Structure and Resource Files

Sources: Sublime Text Official Packages Docs (sublimetext.com/docs/packages.html), ST Community Docs (docs.sublimetext.io), sublimehq/Packages repository analysis

Covers: Package directory layout, all resource file formats (.sublime-commands, .sublime-keymap, .sublime-menu, .sublime-settings, .sublime-build, .tmPreferences, messages.json), package load order, .sublime-package format. Does NOT cover Python API (see plugin-api.md), syntax definitions (see syntax-definitions.md), or color schemes/themes (see visual-resources.md).

## Package Locations

| Location | Purpose |
|----------|---------|
| `<executable>/Packages/` | Shipped packages (read-only `.sublime-package` zips) |
| `<data>/Installed Packages/` | User-installed `.sublime-package` zips (Package Control) |
| `<data>/Packages/` | Loose packages for development and overrides |

Access `<data>/Packages/` via **Preferences > Browse Packages**.

## Load Order

1. `Packages/Default` (always first)
2. Shipped packages (alphabetical)
3. Installed packages (alphabetical)
4. Remaining user packages (alphabetical)
5. `Packages/User` (always last, wins all conflicts)

Files in `Packages/<Name>/` override identically-named files inside the matching `.sublime-package` zip.

## Standard Directory Layout

```
MyPackage/
├── .python-version              # "3.8" for Python 3.8 plugin host
├── .no-sublime-package          # Force unpacked install (for binaries)
├── plugin.py                    # Main plugin entry point
├── lib/                         # Helper modules (not auto-loaded)
│   └── helpers.py
│
├── Default.sublime-commands     # Command Palette entries
├── Main.sublime-menu            # Top menu bar
├── Context.sublime-menu         # Right-click in editor
├── Side Bar.sublime-menu        # Right-click in sidebar
├── Tab Context.sublime-menu     # Right-click on tab
│
├── Default (Windows).sublime-keymap
├── Default (OSX).sublime-keymap
├── Default (Linux).sublime-keymap
│
├── MyPackage.sublime-settings   # Default settings
├── MyPackage.sublime-build      # Build system
├── MyPackage.sublime-syntax     # Syntax definition
├── MyPackage.sublime-color-scheme
├── MyPackage.sublime-completions
├── Snippets/
│   └── function.sublime-snippet
├── Comments.tmPreferences       # Comment token metadata
│
├── messages.json                # Release note manifest
├── messages/
│   ├── install.txt              # Shown on first install
│   └── 1.0.0.txt               # Shown on upgrade to 1.0.0
│
├── README.md
├── LICENSE
├── .gitignore
└── .gitattributes               # export-ignore to shrink distribution
```

## Command Palette (.sublime-commands)

JSON array. File name: `Default.sublime-commands` (convention).

```json
[
    {
        "caption": "My Package: Do Something",
        "command": "my_do_something",
        "args": {"mode": "fast"}
    },
    {
        "caption": "My Package: Open Settings",
        "command": "edit_settings",
        "args": {
            "base_file": "${packages}/MyPackage/MyPackage.sublime-settings",
            "default": "// MyPackage Settings\n// See default settings on the left\n{\n\t$0\n}\n"
        }
    }
]
```

Prefix captions with package name for discoverability: `"My Package: Action"`.

## Key Bindings (.sublime-keymap)

JSON array. Platform-specific files are required:
- `Default (Windows).sublime-keymap`
- `Default (OSX).sublime-keymap`
- `Default (Linux).sublime-keymap`

```json
[
    {
        "keys": ["ctrl+shift+t"],
        "command": "my_command",
        "args": {"flag": true},
        "context": [
            {"key": "selector", "operator": "equal", "operand": "source.python"},
            {"key": "selection_empty", "operator": "equal", "operand": true}
        ]
    }
]
```

### Context Keys

| Key | Tests |
|-----|-------|
| `selector` | Scope at cursor matches operand |
| `selection_empty` | Whether selection is empty |
| `preceding_text` | Regex match on text before cursor |
| `following_text` | Regex match on text after cursor |
| `num_selections` | Number of cursors |
| `has_next_field` / `has_prev_field` | Snippet field navigation |
| `panel_visible` | Whether a panel is open |
| `overlay_visible` | Whether command palette is open |
| `auto_complete_visible` | Whether autocomplete is showing |

Best practice: Provide an `Example.sublime-keymap` with commented-out suggestions
rather than binding keys by default. Avoid hijacking common shortcuts.

## Menus (.sublime-menu)

JSON arrays. Menu files are **merged** across packages (not overridden).

### Menu File Names

| File | Location |
|------|----------|
| `Main.sublime-menu` | Top menu bar |
| `Context.sublime-menu` | Right-click in editor |
| `Side Bar.sublime-menu` | Right-click in sidebar |
| `Side Bar Mount Point.sublime-menu` | Right-click on folder root |
| `Tab Context.sublime-menu` | Right-click on tab |
| `Widget Context.sublime-menu` | Right-click in input widget |
| `Find in Files.sublime-menu` | Find in Files panel |

### Format

```json
[
    {
        "id": "tools",
        "children": [
            {"caption": "-", "id": "my-package-separator"},
            {
                "caption": "My Package",
                "id": "my-package-menu",
                "children": [
                    {"caption": "Run", "command": "my_run"},
                    {"caption": "-"},
                    {"caption": "Settings", "command": "edit_settings",
                     "args": {"base_file": "${packages}/MyPackage/MyPackage.sublime-settings"}}
                ]
            }
        ]
    }
]
```

Use `"id"` to merge into existing menus. `"caption": "-"` creates a separator.

## Settings (.sublime-settings)

JSON object. Three-tier merge: Default -> User -> Project.

```json
{
    "my_enabled": true,
    "my_threshold": 80,
    "my_excluded_patterns": ["*.min.js", "vendor/**"]
}
```

### Settings Access Patterns

```python
# Load package settings (searches Default then User)
settings = sublime.load_settings("MyPackage.sublime-settings")
value = settings.get("my_enabled", True)

# Modify and save
settings.set("my_enabled", False)
sublime.save_settings("MyPackage.sublime-settings")

# View-level settings (highest priority)
view.settings().get("my_enabled")
view.settings().set("my_enabled", False)
```

### Settings Hints (.sublime-settings-hints)

ST4: Provide type hints for the settings UI. JSON object mapping keys to type descriptions.

```json
{
    "my_enabled": "boolean",
    "my_threshold": "integer",
    "my_excluded_patterns": ["string"]
}
```

### Opening Settings in Split View

Use the `edit_settings` command to open default and user settings side-by-side:

```json
{
    "caption": "Preferences: My Package Settings",
    "command": "edit_settings",
    "args": {
        "base_file": "${packages}/MyPackage/MyPackage.sublime-settings",
        "default": "// MyPackage User Settings\n{\n\t$0\n}\n"
    }
}
```

## Build Systems (.sublime-build)

JSON format. Auto-selected via `selector` matching the file scope.

```json
{
    "cmd": ["python3", "-u", "$file"],
    "selector": "source.python",
    "file_regex": "^[ ]*File \"(...*?)\", line ([0-9]*)",
    "working_dir": "$file_path",
    "env": {"PYTHONIOENCODING": "utf-8"},
    "variants": [
        {"name": "Run Tests", "cmd": ["python3", "-m", "pytest", "$file", "-v"]},
        {"name": "Lint", "shell_cmd": "flake8 \"$file\""}
    ],
    "windows": {"cmd": ["python", "-u", "$file"]},
    "osx": {"cmd": ["python3", "-u", "$file"]}
}
```

### Build Variables

| Variable | Value |
|----------|-------|
| `$file` | Full path to current file |
| `$file_path` | Directory of current file |
| `$file_name` | Filename with extension |
| `$file_base_name` | Filename without extension |
| `$file_extension` | Extension only |
| `$folder` | First open folder in sidebar |
| `$project_path` | Directory of `.sublime-project` file |
| `$packages` | Path to `Packages/` directory |
| `$platform` | `windows`, `osx`, or `linux` |

### file_regex Capture Groups

```
Group 1 -> filename
Group 2 -> line number
Group 3 -> column (optional)
Group 4 -> error message (optional)
```

### Custom Build Target

Set `"target": "my_build"` to route to a custom `WindowCommand`:

```python
class MyBuildCommand(sublime_plugin.WindowCommand):
    def run(self, **kwargs):
        # Custom build logic
        pass
```

## Comment Metadata (.tmPreferences)

XML plist defining comment tokens for Toggle Comment commands.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>scope</key>
    <string>source.mylang</string>
    <key>settings</key>
    <dict>
        <key>shellVariables</key>
        <array>
            <dict>
                <key>name</key><string>TM_COMMENT_START</string>
                <key>value</key><string>// </string>
            </dict>
            <dict>
                <key>name</key><string>TM_COMMENT_START_2</string>
                <key>value</key><string>/* </string>
            </dict>
            <dict>
                <key>name</key><string>TM_COMMENT_END_2</string>
                <key>value</key><string> */</string>
            </dict>
        </array>
    </dict>
</dict>
</plist>
```

## Release Messages (messages.json)

Map version strings to message files shown on install/upgrade.

```json
{
    "install": "messages/install.txt",
    "1.0.0": "messages/1.0.0.txt",
    "2.0.0": "messages/2.0.0.txt"
}
```

Keep messages brief. Include: what changed, migration steps, links.

## .gitattributes for Distribution

Exclude non-essential files from the `.sublime-package` zip:

```gitattributes
.gitignore       export-ignore
.gitattributes   export-ignore
.github/         export-ignore
tests/           export-ignore
docs/            export-ignore
*.md             export-ignore
tox.ini          export-ignore
setup.cfg        export-ignore
pyproject.toml   export-ignore
.flake8          export-ignore
```

## .gitignore

```gitignore
*.pyc
__pycache__/
*.sublime-workspace
*.sublime-project
.DS_Store
.cache/
.mypy_cache/
```

## Special Files

| File | Purpose |
|------|-------|
| `.python-version` | Contains `3.8` to use Python 3.8 plugin host |
| `.no-sublime-package` | Forces unpacked install (needed for executables) |
| `dependencies.json` | Package Control library dependencies |
| `package-metadata.json` | Auto-generated by PC on install. NEVER commit. |

## File Extension Reference

| Extension | Format | Purpose |
|-----------|--------|---------|
| `.sublime-syntax` | YAML | Syntax highlighting (modern) |
| `.tmLanguage` | PList XML | Syntax highlighting (legacy) |
| `.sublime-color-scheme` | JSON | Color scheme (ST3.1+) |
| `.tmTheme` | PList XML | Color scheme (legacy) |
| `.sublime-theme` | JSON | UI theme |
| `.sublime-snippet` | XML | Code snippet |
| `.sublime-completions` | JSON | Completion list |
| `.sublime-build` | JSON | Build system |
| `.sublime-keymap` | JSON | Key bindings |
| `.sublime-settings` | JSON | Settings |
| `.sublime-commands` | JSON | Command palette entries |
| `.sublime-menu` | JSON | Menu definitions |
| `.sublime-macro` | JSON | Recorded macro |
| `.tmPreferences` | PList XML | Metadata (comment tokens, symbols) |
