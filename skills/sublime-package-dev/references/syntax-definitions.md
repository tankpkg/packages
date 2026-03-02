# Syntax Definitions

Sources: Sublime Text Official Syntax Docs (sublimetext.com/docs/syntax.html), Scope Naming Reference (sublimetext.com/docs/scope_naming.html), sublimehq/Packages repository

Covers: `.sublime-syntax` YAML format, contexts and match patterns, meta patterns, push/pop/set/embed/branch actions, variables, inheritance, scope naming conventions, syntax testing, `.tmLanguage` legacy format comparison. Does NOT cover color schemes or themes (see visual-resources.md).

## .sublime-syntax Header

```yaml
%YAML 1.2
---
name: My Language
file_extensions: [mylang, ml]
hidden_file_extensions: [.mylang-internal]  # ST4: not in file dialogs
first_line_match: '^#!/.*\bmylang\b'
scope: source.mylang
version: 2                                  # Use 2 for new syntaxes
hidden: false
```

| Key | Required | Purpose |
|-----|----------|---------|
| `name` | No | Display name in menu (derived from filename if omitted) |
| `file_extensions` | Yes | Extensions triggering this syntax |
| `first_line_match` | No | Regex to match first line (shebang detection) |
| `scope` | Yes | Root scope (`source.*` for code, `text.*` for markup) |
| `version` | No | `2` fixes scope-stacking bugs. Always use `2` for new syntaxes. |
| `extends` | No | Parent syntax path for inheritance (ST4 4075+) |
| `hidden` | No | Hide from menu; still includable by other syntaxes |

## Contexts

Every syntax must define a `main` context. Contexts form a stack machine.

```yaml
variables:
  ident: '[A-Za-z_][A-Za-z_0-9]*'

contexts:
  prototype:
    - include: comments

  main:
    - include: keywords
    - include: strings
    - include: numbers

  keywords:
    - match: \b(if|else|for|while|return)\b
      scope: keyword.control.mylang
    - match: \b(true|false|null)\b
      scope: constant.language.mylang

  strings:
    - match: '"'
      scope: punctuation.definition.string.begin.mylang
      push: double-string

  double-string:
    - meta_include_prototype: false
    - meta_scope: string.quoted.double.mylang
    - match: \\.
      scope: constant.character.escape.mylang
    - match: '"'
      scope: punctuation.definition.string.end.mylang
      pop: true

  numbers:
    - match: '\b[0-9]+(\.[0-9]+)?\b'
      scope: constant.numeric.mylang

  comments:
    - match: //
      scope: punctuation.definition.comment.mylang
      push:
        - meta_scope: comment.line.double-slash.mylang
        - match: $
          pop: true
    - match: /\*
      scope: punctuation.definition.comment.begin.mylang
      push:
        - meta_scope: comment.block.mylang
        - match: \*/
          scope: punctuation.definition.comment.end.mylang
          pop: true
```

### prototype Context

Auto-included at the top of every other context unless
`meta_include_prototype: false` is set. Use for comments and other
constructs valid everywhere.

## Meta Patterns

Must be listed FIRST in a context, before any match or include patterns.

| Pattern | Effect |
|---------|--------|
| `meta_scope: scope.name` | Scope applied to ALL text including delimiters |
| `meta_content_scope: scope.name` | Scope applied to content only (not triggers) |
| `meta_include_prototype: false` | Prevent prototype injection (use in strings) |
| `clear_scopes: N` | Remove N scopes from stack before applying meta |
| `meta_prepend: true` | ST4: insert rules BEFORE parent's in inheritance |
| `meta_append: true` | ST4: insert rules AFTER parent's in inheritance |

## Match Pattern Keys

```yaml
- match: '\b(function)\s+({{ident}})'
  captures:
    1: storage.type.function.mylang
    2: entity.name.function.mylang
  push: function-params
```

| Key | Description |
|-----|-------------|
| `match` | Oniguruma regex (single line only, no literal tabs) |
| `scope` | Scope for entire match |
| `captures` | Map of capture group number to scope |

### Actions (mutually exclusive per match)

| Action | Behavior |
|--------|----------|
| `push: context` | Push context(s) onto stack |
| `pop: true` | Pop current context (or `pop: N` for N contexts) |
| `set: context` | Pop current + push new (match gets both meta_scopes) |
| `embed: context` | Push; auto-pops on `escape` pattern regardless of nesting |
| `branch: [ctx1, ctx2]` | Try contexts in order; `fail` rewinds (ST4 4050+) |
| `fail: branch_point` | Rewind to branch_point, try next context |

ST4 4075+: `pop` can combine with `push`/`set`/`embed`/`branch`.

### embed/escape (Syntax Embedding)

```yaml
- match: (<script>)
  captures:
    1: punctuation.section.embedded.begin.html
  embed: scope:source.js
  embed_scope: meta.embedded.js.html
  escape: (</script>)
  escape_captures:
    1: punctuation.section.embedded.end.html
```

### branch/fail (Ambiguous Constructs, ST4)

```yaml
expression:
  - match: (?=\()
    branch_point: open_parens
    branch:
      - paren_group
      - arrow_function
```

Max rewind: 128 lines. List contexts by likelihood (most likely first).

## Include Patterns

```yaml
- include: comments                      # Include local context
- include: scope:source.js               # Include external syntax
- include: Packages/C++/C.sublime-syntax # Include by path
```

Add `apply_prototype: true` to also include the target's prototype.

## Variables

Define reusable regex fragments at the top level:

```yaml
variables:
  ident: '[A-Za-z_][A-Za-z_0-9]*'
  hex_digit: '[0-9a-fA-F]'
  number: '[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?'

contexts:
  main:
    - match: '\b{{ident}}\b'
      scope: variable.other.mylang
```

Variables can reference other variables. Only `{{[A-Za-z0-9_]+}}` is treated
as a variable reference; literal `{{` passes through.

## Inheritance (ST4 4075+)

```yaml
%YAML 1.2
---
name: TypeScript
file_extensions: [ts]
scope: source.ts
extends: Packages/JavaScript/JavaScript.sublime-syntax
```

Inherits `variables` and `contexts` (NOT file_extensions, scope, name).
Same-name variables override. Same-name contexts override (use
`meta_prepend`/`meta_append` to merge instead). Multiple inheritance
supported (4086) — parents must share the same base.

## Scope Naming Conventions

Scopes are dot-separated, least-to-most specific. Final segment is
conventionally the syntax name.

### Standard Top-Level Scopes

| Scope | Used For | Examples |
|-------|----------|---------|
| `comment.line` | Line comments | `// ...`, `# ...` |
| `comment.block` | Block comments | `/* ... */` |
| `comment.block.documentation` | Doc comments | `/** ... */`, `"""..."""` |
| `constant.numeric` | Numbers | `42`, `3.14`, `0xFF` |
| `constant.language` | Language constants | `true`, `false`, `null`, `None` |
| `constant.character.escape` | Escape sequences | `\n`, `\x20`, `\\` |
| `entity.name.function` | Function definitions | `def foo`, `function bar` |
| `entity.name.class` | Class definitions | `class MyClass` |
| `entity.name.tag` | HTML/XML tags | `<div>`, `<span>` |
| `entity.other.attribute-name` | Tag attributes | `class=`, `id=` |
| `invalid.illegal` | Syntax errors | Unmatched brackets |
| `invalid.deprecated` | Deprecated constructs | |
| `keyword.control` | Control flow | `if`, `for`, `while`, `return` |
| `keyword.operator` | Operators | `+`, `=`, `&&`, `=>` |
| `keyword.declaration` | Declarations | `var`, `let`, `const`, `function` |
| `markup.heading` | Headings | `# Title`, `## Section` |
| `markup.bold` / `.italic` | Formatted text | `**bold**`, `*italic*` |
| `markup.inserted` / `.deleted` | Diff output | `+added`, `-removed` |
| `meta.function` | Function region | Structural, usually not colored |
| `meta.class` | Class region | Structural, usually not colored |
| `punctuation.definition.string` | String delimiters | `"`, `'`, `` ` `` |
| `punctuation.definition.comment` | Comment markers | `//`, `/*`, `#` |
| `punctuation.separator` | Separators | `,`, `:` |
| `punctuation.accessor` | Accessors | `.`, `->`, `::` |
| `source.*` | Root scope for code | `source.python`, `source.js` |
| `storage.type` | Type keywords | `int`, `bool`, `char`, `string` |
| `storage.modifier` | Modifiers | `static`, `const`, `public`, `async` |
| `string.quoted.single` | Single-quoted | `'text'` |
| `string.quoted.double` | Double-quoted | `"text"` |
| `string.regexp` | Regular expressions | `/pattern/` |
| `support.function` | Built-in functions | `print`, `console.log` |
| `support.type` | Built-in types | `Array`, `Promise` |
| `text.*` | Root scope for markup | `text.html`, `text.xml` |
| `variable.parameter` | Function parameters | `def foo(x)` → `x` |
| `variable.language` | Language variables | `this`, `self`, `super` |
| `variable.function` | Function calls | `foo()` → `foo` |

## Syntax Testing

Create test files to automatically verify scope assignments.

### Test File Requirements

1. Filename starts with `syntax_test_`
2. Saved in `Packages/` directory (next to syntax file)
3. First line: `<comment> SYNTAX TEST "Packages/MyLang/MyLang.sublime-syntax"`

### Test Markers

```
// SYNTAX TEST "Packages/MyLang/MyLang.sublime-syntax"
if (x > 0) {
// <- keyword.control.mylang
// ^^^ meta.group.mylang
//  ^ variable.other.mylang
//    ^ keyword.operator.mylang
//      ^ constant.numeric.mylang
```

| Marker | Tests |
|--------|-------|
| `^` | Scope at that column on previous non-test line |
| `^^^` | Consecutive carets test consecutive columns |
| `<-` | Scope at the comment character column |
| `@` | Symbol type: `none`, `definition`, `reference`, `local-definition`, `global-definition` |

### Running Tests

Build command with a syntax test or `.sublime-syntax` file selected runs all
tests. Use **F4** (Next Result) to navigate to failing tests.

### Test Options

Add after `SYNTAX TEST` on first line:
- `partial-symbols` — do not require exhaustive symbol testing
- `reindent-unchanged` — verify reindent produces no changes
- `reindent-unindented` — verify reindent from unindented reproduces file
- `reindent` — both reindent checks

## .tmLanguage Legacy Format

PList XML format. Still supported for cross-editor compatibility (VS Code,
TextMate). Use `.sublime-syntax` for new packages.

### Key Differences

| Feature | `.tmLanguage` | `.sublime-syntax` |
|---------|--------------|-------------------|
| Format | PList XML | YAML |
| Context stack | No (begin/end only) | Full push/pop/set |
| Variables | No | Yes |
| Prototype | No | Yes |
| Embedding | Limited | embed + with_prototype |
| Inheritance | No | Yes (ST4) |
| Branching | No | Yes (ST4) |
| Performance | Slower | Faster |

Cannot include `.tmLanguage` within `.sublime-syntax`.
