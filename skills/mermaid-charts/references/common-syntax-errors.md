# Common Mermaid Syntax Errors

Sources: mermaid-js/mermaid source (Jison + Langium grammars), GitLab
check_mermaid logs, NVIDIA OpenShell lint-mermaid issues, real
mermaid.parse() error catalog.

Covers: error message → root cause → fix. Lookup by the error text the
parser actually prints. Each entry shows broken code, the parser error,
and the fix.

## How to read a parse error

The parser prints messages like:

```
Parse error on line 3:
...flowchart TQ;A--x|text including
-----------------------^
Expecting 'NEWLINE', 'SEMI', 'EOF', 'OPEN_DIRECTIVE' ...
```

- `line 3` is the line **within the diagram body**, not the source file. The
  bundled validator adjusts this to a source-file line for you.
- The caret `^` points at the **first token the parser could not consume**.
- "Expecting" lists what would have been valid at that position. Read it as
  a hint about what the parser thought the previous token was.

Fix the token at the caret. Do not refactor the whole diagram on a hunch.

## Catalog: by error message

### `No diagram type detected matching given configuration for text: ...`

**Cause:** the first non-empty, non-comment line is not a known diagram
declaration. Common reasons:

1. Typo in declaration: `flowChart TD` (case-sensitive in older versions;
   prefer `flowchart TD`), `sequencediagram` (must be `sequenceDiagram`).
2. Stray text before the declaration. Only YAML frontmatter
   (`---\n...\n---`) is allowed as a prefix.
3. Backticks or fence markers leaked into the body (e.g. the chart body
   begins with ` ``` `).

**Fix:** ensure the body starts with one of: `flowchart`, `graph`,
`sequenceDiagram`, `classDiagram`, `stateDiagram-v2`, `erDiagram`, `gantt`,
`pie`, `mindmap`, `gitGraph`, `journey`, `quadrantChart`, `timeline`,
`sankey-beta`, `xychart-beta`, `block-beta`, `packet-beta`, `kanban`,
`architecture-beta`, `radar-beta`, `C4Context`, `C4Container`,
`C4Component`, `C4Dynamic`, `C4Deployment`.

### `Lexical error on line N. Unrecognized text.`

**Cause:** the lexer hit a character it cannot categorize. Common reasons:

1. **Reserved keyword used as a node ID** — the most frequent cause.
   Reserved tokens vary by diagram, but the common offenders are: `end`,
   `class`, `default`, `subgraph`, `direction`, `style`, `linkStyle`,
   `click`, `interpolate`. Even mixed-case (`End`, `End_State`) trips
   the lexer in many contexts.

   Broken:
   ```
   flowchart TD
     start --> end
   ```
   Fix: rename or quote.
   ```
   flowchart TD
     start --> finish
   ```
   ```
   flowchart TD
     start --> END_NODE["end"]
   ```

2. **Unicode / smart quotes** snuck in from a doc editor (`'`, `'`, `"`,
   `"`). Replace with ASCII `'` and `"`.

3. **Tab characters** mixed with spaces in indentation-sensitive diagrams
   (mindmap, timeline). Use spaces only.

### `Parse error ... Expecting 'NEWLINE'`

**Cause:** two statements on one line without a separator. Mermaid expects
each edge / declaration on its own line, optionally separated by `;`.

Broken:
```
flowchart TD A --> B B --> C
```
Fix:
```
flowchart TD
  A --> B
  B --> C
```

### `Parse error ... Expecting 'NODE_STRING' ... got 'PS'` (or 'BRKT', 'PIPE')

**Cause:** unbalanced brackets in a node shape.

| Broken                | Why                                  | Fix                  |
| --------------------- | ------------------------------------ | -------------------- |
| `A[Label`             | Missing closing `]`                  | `A[Label]`           |
| `A((Circle)`          | Missing closing `)`                  | `A((Circle))`        |
| `A[(Cyl)`             | Missing closing `)]`                 | `A[(Cyl)]`           |
| `A{Diamond`           | Missing closing `}`                  | `A{Diamond}`         |
| `A -->|label B`       | Missing closing `|`                  | `A -->|label| B`     |

### `Parse error ... Expecting 'OPEN_DIRECTIVE'` (sequence diagram)

**Cause:** flowchart arrow (`-->`) used inside `sequenceDiagram`. Sequence
diagrams use `->>`, `-->>`, `-x`, `--x`, `-)`, `--)`.

Broken:
```
sequenceDiagram
  A --> B: Hello
```
Fix:
```
sequenceDiagram
  A->>B: Hello
```

### `Parse error ... Expecting '...' got 'OPEN_IN_STRUCT'` (class diagram)

**Cause:** class diagram class block uses `{ }` but its content syntax is
distinct. Visibility prefixes must be `+`, `-`, `#`, `~`. Method parens are
required: `method() ReturnType`.

Broken:
```
class Dog {
  bark void
}
```
Fix:
```
class Dog {
  +bark() void
}
```

### `Cannot read properties of undefined (reading 'parser')`

**Cause:** the diagram declaration is recognized but the diagram type's
package failed to load. Usually a version mismatch between an old `mermaid`
install and a beta diagram (`architecture-beta`, `packet-beta`,
`radar-beta`). Upgrade mermaid to ^11.x.

### `RangeError: Maximum call stack size exceeded`

**Cause:** a cycle in a diagram type that does not permit cycles, or an
extremely large diagram. Rare. Reduce diagram size or split into multiple.

## Catalog: by symptom (no specific error)

### "Chart renders empty"

1. Diagram type missing or misspelled — the parser may accept a generic
   "graph" declaration and then nothing else parses.
2. Diagram body has only comments. `%%` lines are not content.
3. All edges reference nodes that resolve to the same coordinate due to a
   layout config (rare). Try removing `config:` block.

### "Chart renders, but labels are cut off"

This is not a syntax error — it's a styling issue. Outside this skill's
scope. Use `htmlLabels: true` in config or shorten labels.

### "Chart works in Mermaid Live but fails in GitHub"

Almost always **version skew**. The live editor often runs ahead of what
GitHub ships. Two recovery paths:

1. Run the bundled validator (pinned to ^11.0.0, which matches current
   GitHub). If it fails here, fix the indicated issue.
2. Constrain yourself to non-beta diagrams (`-beta` suffix indicates the
   diagram may not yet render on all platforms).

### "Chart works on first render, breaks after editing"

Almost always an unbalanced bracket or pipe introduced by the edit. Re-run
the validator after every change.

## Quoting rules (every diagram)

When a label contains any of `()[]{}<>|:;#"` or a leading digit, **quote
it**:

```
A["label: with colon"] --> B["label (with parens)"]
```

Inside double-quoted labels, escape internal double quotes with `&quot;`
(HTML entity), not `\"`.

For sequence-diagram messages, the colon `:` is part of the syntax — do
not quote it:

```
A->>B: This is the message (colon stays bare)
```

## Indentation rules

| Diagram     | Indentation matters?                     |
| ----------- | ---------------------------------------- |
| Flowchart   | No (any whitespace allowed)              |
| Sequence    | No                                       |
| Class       | No                                       |
| State       | No                                       |
| ER          | No                                       |
| Gantt       | No                                       |
| Mindmap     | **Yes** — indentation defines hierarchy  |
| Timeline    | No, but section grouping is by position  |

For mindmap, use a consistent indent (2 or 4 spaces). Do not mix tabs and
spaces. Inconsistent indentation in mindmap produces "expected `INDENT`"
errors that are hard to read.

## Frontmatter pitfalls

```
---
title: My title
---
flowchart TD
  A --> B
```

- Frontmatter MUST start at line 1, column 1 of the diagram. No leading
  blank lines, no whitespace before the opening `---`.
- The closing `---` MUST be on its own line.
- Use YAML, not JSON. Booleans are `true`/`false`, not `True`/`False`.
- Multiline values need `|` or `>` indicators.

## Recovery procedure

When a chart fails to parse:

1. Run `node scripts/validate-mermaid.mjs <file>` to get the exact line.
2. Look up the error text in this file — start with section "Catalog: by
   error message".
3. Apply the fix.
4. Re-run the validator.
5. If still failing and the message changed, repeat from step 2 — your
   fix likely uncovered the next error.
6. If still failing and the message is identical, the fix did not address
   the indicated token. Look one or two tokens earlier in the diagram —
   parsers often complain at the symptom site, not the cause.

Do not "rewrite the whole chart" to escape a parse error. The token at the
caret is the problem; fix it.
