# Visual Resources: Color Schemes, Themes, Snippets, Completions

Sources: Sublime Text Official Docs (sublimetext.com/docs/color_schemes.html, themes.html), sublimehq/Packages repository analysis, ST Community Docs (docs.sublimetext.io)

Covers: `.sublime-color-scheme` JSON format, `.sublime-theme` UI themes, `.sublime-snippet` XML format, `.sublime-completions` JSON format, `.tmTheme` legacy format. Does NOT cover `.sublime-syntax` (see syntax-definitions.md), `.sublime-build` (see package-structure.md), or Python API (see plugin-api.md).

## Color Schemes (.sublime-color-scheme)

JSON format replacing legacy `.tmTheme`. Three sections: variables, globals, rules.

### Complete Structure

```json
{
    "name": "My Dark Scheme",
    "variables": {
        "bg":      "#1e1e1e",
        "fg":      "#d4d4d4",
        "red":     "hsl(0, 80%, 60%)",
        "green":   "hsl(120, 60%, 55%)",
        "blue":    "hsl(210, 80%, 65%)",
        "yellow":  "hsl(40, 90%, 60%)",
        "purple":  "hsl(270, 70%, 65%)",
        "cyan":    "hsl(185, 70%, 60%)",
        "comment": "hsl(0, 0%, 45%)"
    },
    "globals": {
        "background":         "var(bg)",
        "foreground":         "var(fg)",
        "caret":              "white",
        "line_highlight":     "rgba(255,255,255,0.05)",
        "selection":          "rgba(100,100,200,0.3)",
        "selection_border":   "rgba(100,100,200,0.5)",
        "inactive_selection": "rgba(100,100,200,0.15)",
        "find_highlight":     "hsl(50, 100%, 50%)",
        "gutter":             "color(var(bg) l(- 2%))",
        "gutter_foreground":  "color(var(fg) a(0.4))",
        "guide":              "rgba(255,255,255,0.08)",
        "active_guide":       "rgba(255,255,255,0.2)",
        "stack_guide":        "rgba(255,255,255,0.12)",
        "rulers":             "rgba(255,255,255,0.1)",
        "brackets_options":   "underline",
        "brackets_foreground": "rgba(255,255,255,0.7)",
        "misspelling":        "var(red)",
        "accent":             "var(blue)"
    },
    "rules": [
        {"name": "Comment",    "scope": "comment",            "foreground": "var(comment)", "font_style": "italic"},
        {"name": "String",     "scope": "string",             "foreground": "var(green)"},
        {"name": "Number",     "scope": "constant.numeric",   "foreground": "var(purple)"},
        {"name": "Keyword",    "scope": "keyword",            "foreground": "var(blue)"},
        {"name": "Storage",    "scope": "storage",            "foreground": "var(blue)", "font_style": "italic"},
        {"name": "Entity",     "scope": "entity.name",        "foreground": "var(yellow)"},
        {"name": "Tag",        "scope": "entity.name.tag",    "foreground": "var(red)"},
        {"name": "Attribute",  "scope": "entity.other.attribute-name", "foreground": "var(yellow)"},
        {"name": "Variable",   "scope": "variable",           "foreground": "var(fg)"},
        {"name": "Function",   "scope": "variable.function",  "foreground": "var(yellow)"},
        {"name": "Support",    "scope": "support.function",   "foreground": "var(cyan)"},
        {"name": "Escape",     "scope": "constant.character.escape", "foreground": "var(cyan)"},
        {"name": "Invalid",    "scope": "invalid",            "foreground": "#fff", "background": "var(red)"},
        {"name": "Diff Add",   "scope": "markup.inserted",    "foreground": "var(green)"},
        {"name": "Diff Del",   "scope": "markup.deleted",     "foreground": "var(red)"}
    ]
}
```

### Color Formats

| Format | Example |
|--------|---------|
| Hex RGB/RGBA | `#FF0000`, `#F00`, `#FF0000AA` |
| rgb/rgba | `rgb(255, 0, 0)`, `rgba(255, 0, 0, 0.5)` |
| hsl/hsla | `hsl(0, 100%, 50%)`, `hsla(0, 100%, 50%, 0.5)` |
| hwb | `hwb(0, 20%, 20%)` (ST3 3181+) |
| CSS named | `red`, `blue`, `white` |
| Variable reference | `var(my_variable)` |
| Color modifier | `color(var(bg) blend(#fff 20%))` |

### Color Modifier Functions

```
color(var(bg) alpha(0.5))          # Set alpha (shorthand: a())
color(var(fg) lightness(0.9))      # Set lightness (shorthand: l())
color(var(fg) saturation(0.9))     # Set saturation (shorthand: s())
color(var(bg) blend(#fff 20%))     # Blend with color
color(var(bg) min-contrast(var(fg) 4.5))  # Ensure contrast ratio
```

### font_style Values

Space-separated: `"bold"`, `"italic"`, `"underline"`, `"squiggly_underline"`,
`"stippled_underline"`, `"glow"` (ST4 4050+).

### Hashed Semantic Highlighting

```json
{"scope": "source - punctuation - keyword",
 "foreground": ["hsl(200, 60%, 70%)", "hsl(330, 60%, 70%)"]}
```

Array of two colors creates identifier-based color variation.

### User Customization Pattern

Create `Packages/User/SchemeName.sublime-color-scheme` to override built-in:
variables/globals merge (user wins), rules append.

### Minimum Scope Coverage

A color scheme should style at minimum: `comment`, `string`, `constant.numeric`,
`constant.language`, `constant.character.escape`, `keyword`, `keyword.operator`,
`storage`, `entity.name`, `entity.name.tag`, `variable`, `variable.language`,
`support`, `invalid`.

## UI Themes (.sublime-theme)

JSON format controlling all UI elements: tabs, sidebar, status bar, panels.

### Structure

```json
{
    "extends": "Default.sublime-theme",
    "variables": {
        "bg": "#1e1e1e",
        "fg": "#cccccc",
        "accent": "#4a9eff"
    },
    "rules": [
        {"class": "title_bar", "bg": "var(bg)", "fg": "var(fg)"},
        {"class": "tab_control", "layer0.tint": "#252526", "layer0.opacity": 1.0,
         "content_margin": [8, 5, 8, 5]},
        {"class": "tab_control", "attributes": ["selected"],
         "layer0.tint": "var(bg)"},
        {"class": "tab_control", "attributes": ["dirty"],
         "layer1.texture": "Theme - Mine/dot.png", "layer1.opacity": 1.0},
        {"class": "sidebar_container", "layer0.tint": "#252526"},
        {"class": "status_bar", "layer0.tint": "#007acc"}
    ]
}
```

### Key UI Classes

| Class | Element |
|-------|---------|
| `title_bar` | Window title bar |
| `tabset_control` | Tab bar container |
| `tab_control` | Individual tab |
| `tab_label` | Tab filename text |
| `tab_close_button` | Close button on tab |
| `sidebar_container` | Sidebar scroll area |
| `sidebar_tree` | Sidebar tree widget |
| `sidebar_label` | File/folder names |
| `sidebar_heading` | Section headings |
| `status_bar` | Bottom status bar |
| `overlay_control` | Command palette overlay |
| `quick_panel` | Results list |
| `auto_complete` | Autocomplete popup |
| `panel_control` | Find/Replace panel |
| `scroll_bar_control` | Scrollbars |
| `button_control` | Buttons |

### Attributes

| Attribute | Meaning |
|-----------|---------|
| `hover` | Mouse over element |
| `selected` | Active/selected item |
| `dirty` | Unsaved changes |
| `expanded` | Tree row expanded |
| `pressed` | Button pressed |
| `file_light` / `file_dark` | Color scheme luminosity |

### Layer System

Each element supports 4 texture layers (`layer0`-`layer3`):

```json
{"class": "tab_control",
 "layer0.tint": "#252526", "layer0.opacity": 1.0,
 "layer1.texture": "Theme/textures/tab.png",
 "layer1.inner_margin": [4, 4, 4, 4], "layer1.opacity": 0.0}
```

### Animated Properties

```json
{"class": "button_control", "attributes": ["hover"],
 "layer1.opacity": {"target": 1.0, "speed": 1.5, "interpolation": "smoothstep"}}
```

### Settings-Based Conditional Rules

```json
{"class": "sidebar_label", "settings": ["bold_folder_labels"], "font.bold": true}
```

## Snippets (.sublime-snippet)

XML format for tab-triggered text expansion.

```xml
<snippet>
    <content><![CDATA[
def ${1:function_name}(${2:args}):
    """${3:Docstring.}"""
    ${0:pass}
]]></content>
    <tabTrigger>def</tabTrigger>
    <scope>source.python</scope>
    <description>Function definition</description>
</snippet>
```

### Field Markers

| Syntax | Purpose |
|--------|---------|
| `$1`, `$2` ... `$n` | Tab stops (cursor positions in order) |
| `$0` | Final cursor position after all tab stops |
| `${1:default}` | Tab stop with default text |
| `${1:${2:nested}}` | Nested fields |
| `${1/regex/replace/flags}` | Regex transformation on field |
| `\$` | Literal dollar sign |

### Built-in Variables

| Variable | Value |
|----------|-------|
| `$TM_SELECTED_TEXT` / `$SELECTION` | Current selection |
| `$TM_FILENAME` | Current filename |
| `$TM_FILEPATH` | Full file path |
| `$TM_DIRECTORY` | Directory of current file |
| `$TM_LINE_NUMBER` | 1-based line number |
| `$TM_CURRENT_WORD` | Word under cursor |
| `$TM_CURRENT_LINE` | Full current line |
| `$TM_TAB_SIZE` | Spaces per tab |

### Regex Transformations

```xml
<!-- Lowercase field 1 for field 2 -->
Name: ${1:MyClass}
File: ${2:${1/(.+)/\L$1/}}.py

<!-- Replace spaces with dashes -->
Title: ${1:My Title}
Slug:  ${2:${1/\s+/-/g}}
```

Flags: `g` (global), `i` (case-insensitive), `m` (multiline).

### Multi-Scope Snippets

```xml
<scope>source.js, source.ts, source.jsx, source.tsx</scope>
```

## Completions (.sublime-completions)

JSON format for static completion suggestions.

```json
{
    "scope": "source.python",
    "completions": [
        "pass",
        "None",
        {
            "trigger": "def\tfunction",
            "contents": "def ${1:name}($2):\n    $0",
            "kind": "snippet",
            "annotation": "function definition",
            "details": "Define a <code>function</code>"
        },
        {
            "trigger": "class",
            "contents": "class ${1:Name}(${2:object}):\n    $0",
            "kind": ["type", "C", "Class"]
        }
    ]
}
```

### Trigger with Description

```json
"trigger": "def\tfunction definition"
```

Tab character separates trigger text from description shown in popup.

### kind Values

String shorthand: `"ambiguous"`, `"function"`, `"keyword"`, `"markup"`,
`"namespace"`, `"navigation"`, `"snippet"`, `"type"`, `"variable"`.

Custom 3-element array: `["function", "m", "Method"]` — category, letter, tooltip.

### details HTML Tags

Allowed: `<a href="">`, `<b>`, `<strong>`, `<i>`, `<em>`, `<u>`, `<tt>`, `<code>`.

## Legacy Color Schemes (.tmTheme)

PList XML format. Still supported but `.sublime-color-scheme` is preferred.
Lacks variables, color modifiers, and hashed semantic highlighting.
