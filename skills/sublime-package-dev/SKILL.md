---
name: "@tank/sublime-package-dev"
description: |
  Create, develop, test, and publish Sublime Text packages. Covers the full
  lifecycle: Python plugin API (commands, events, views, settings), package
  structure (all file formats), syntax definitions (.sublime-syntax YAML),
  color schemes, UI themes, snippets, completions, build systems, local
  development workflow, debugging, and publishing to Package Control.
  Synthesizes official Sublime Text documentation, Package Control docs,
  sublimehq/Packages repository patterns, and popular package analysis
  (SublimeLinter, GitGutter, BracketHighlighter).

  Trigger phrases: "sublime text package", "sublime plugin", "sublime text
  plugin", "create sublime package", "sublime-syntax", "sublime syntax
  definition", "color scheme", "sublime theme", "sublime snippet",
  "sublime completions", "sublime build system", "package control",
  "submit to package control", "sublime text command", "TextCommand",
  "WindowCommand", "EventListener", "ViewEventListener", "sublime API",
  ".sublime-settings", ".sublime-keymap", ".sublime-commands",
  ".sublime-menu", ".sublime-color-scheme", ".sublime-theme",
  ".sublime-build", "tmLanguage", "scope naming"
---

# Sublime Text Package Development

## Core Principles

1. **Start with the right package type** — command plugins, syntax
   definitions, color schemes, and themes are fundamentally different
   artifacts with different file formats.
2. **Use Python 3.8+** — create `.python-version` with `3.8`. Python 3.3
   is being phased out (removed after Q1 2026). Python 3.13 is next.
3. **Use .sublime-syntax version 2** — always set `version: 2` for new
   syntax definitions. Fixes scope-stacking bugs from version 1.
4. **Avoid default key bindings** — provide `Example.sublime-keymap` with
   commented suggestions. Let users choose their own shortcuts.
5. **Test before publishing** — use `syntax_test_` files for syntaxes and
   UnitTesting package for plugin logic. Set up GitHub Actions CI.

## Quick-Start: Package Type Selection

### "I want to add a command/feature"

1. Create `Packages/MyPackage/` with `.python-version` (`3.8`)
2. Write plugin `.py` with TextCommand/WindowCommand/EventListener
3. Add `Default.sublime-commands` for Command Palette
4. Add settings, menus, key bindings as needed
5. See `references/plugin-api.md` and `references/package-structure.md`

### "I want to add syntax highlighting for a language"

1. Create `MyLang.sublime-syntax` (YAML, version 2)
2. Define `main` context with match patterns and scopes
3. Add `Comments.tmPreferences` for Toggle Comment
4. Add snippets, completions, build system
5. Write `syntax_test_` files to verify scopes
6. See `references/syntax-definitions.md`

### "I want to create a color scheme or theme"

1. Color scheme: `.sublime-color-scheme` (JSON with variables, globals, rules)
2. UI theme: `.sublime-theme` (JSON with rules targeting UI classes)
3. Syntax packages should NOT bundle a color scheme
4. See `references/visual-resources.md`

### "I want to publish to Package Control"

1. Host on GitHub (one package per repo, root = package root)
2. Create semver git tags (e.g., `1.0.0`)
3. Fork `sublimehq/package_control_channel`
4. Add JSON entry to `repository/` alphabetical file
5. Submit PR with completed checklist
6. See `references/publishing.md`

## Decision Trees

### Command Type Selection

| Need | Class | Has |
|------|-------|-----|
| Modify buffer text | `TextCommand` | `self.view`, `edit` param |
| Window operations (open files, panels) | `WindowCommand` | `self.window` |
| App-wide settings/actions | `ApplicationCommand` | Neither |
| React to editor events | `EventListener` | All views |
| React to specific view events | `ViewEventListener` | `self.view`, filterable |
| Track text changes precisely | `TextChangeListener` | Buffer-level |

### Resource File Selection

| Content | File Type | Format |
|---------|-----------|--------|
| Command Palette entries | `.sublime-commands` | JSON array |
| Key bindings | `.sublime-keymap` | JSON array (per-platform) |
| Menu items | `.sublime-menu` | JSON array (by location) |
| Package settings | `.sublime-settings` | JSON object |
| Syntax highlighting | `.sublime-syntax` | YAML |
| Color scheme | `.sublime-color-scheme` | JSON |
| UI theme | `.sublime-theme` | JSON |
| Code snippets | `.sublime-snippet` | XML |
| Completions | `.sublime-completions` | JSON |
| Build system | `.sublime-build` | JSON |
| Comment tokens | `.tmPreferences` | XML plist |
| Recorded macro | `.sublime-macro` | JSON array |

### Event Listener Selection

| Scenario | Use |
|----------|-----|
| Need events from ALL views | `EventListener` |
| Need events from specific file types | `ViewEventListener` with `is_applicable()` |
| Need precise text change details | `TextChangeListener` (ST4) |
| Heavy processing on events | Use `_async` method variants |
| Rarely: completion provider | `on_query_completions` on either listener |

### Threading Decision

| Task | Approach |
|------|----------|
| Quick UI update | Direct call (main thread) |
| Network/disk I/O | `threading.Thread` or `set_timeout_async` |
| Update UI after background work | `set_timeout(fn, 0)` from worker thread |
| Periodic background check | `set_timeout_async` with self-rescheduling |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| No `.python-version` file | Add file with content `3.8` |
| Syntax version 1 (or missing) | Set `version: 2` in header |
| Default key bindings in package | Use `Example.sublime-keymap` with comments |
| `on_modified` without `_async` | Use `on_modified_async` for non-trivial work |
| Committing `.pyc` files | Add `*.pyc` to `.gitignore` |
| Committing `package-metadata.json` | Delete it; auto-generated by Package Control |
| Buffer edit outside TextCommand | All `insert`/`erase`/`replace` need `edit` param |
| Missing `meta_include_prototype: false` | Add to string/regex contexts to prevent comment injection |
| Syntax package bundles color scheme | Separate them; Package Control rejects this |
| Branch-based releases | Use semver git tags instead |

## Reference Files

| File | Contents |
|------|----------|
| `references/plugin-api.md` | Python API: commands, events, View, Window, Region, Settings, input handlers, threading, ST4 enums |
| `references/package-structure.md` | Directory layout, all resource file formats (.sublime-commands, .sublime-keymap, .sublime-menu, .sublime-settings, .sublime-build, .tmPreferences, messages.json) |
| `references/syntax-definitions.md` | .sublime-syntax YAML format, contexts, match patterns, meta patterns, push/pop/set/embed/branch, variables, inheritance, scope naming, syntax testing |
| `references/visual-resources.md` | Color schemes (.sublime-color-scheme), UI themes (.sublime-theme), snippets (.sublime-snippet), completions (.sublime-completions), legacy .tmTheme |
| `references/publishing.md` | Package Control submission process, channel JSON format, naming rules, versioning, PR checklist, UnitTesting, GitHub Actions CI |
| `references/development-workflow.md` | Local dev setup, auto-reload, console debugging, threading patterns, common plugin architectures, scaffolding checklists |
