# Validation Workflow

Sources: NVIDIA/OpenShell lint-mermaid.mjs design notes, GitLab
scripts/lint/check_mermaid.mjs, Mermaid.js parse() API docs,
mermaid-js/mermaid v11 test suite.

Covers: running the bundled validator, interpreting its output, integrating
it into authoring loops and CI, the "parses here = renders there"
guarantee, and troubleshooting.

## What the validator does

`scripts/validate-mermaid.mjs` runs the **same** `mermaid.parse()` function
that real Mermaid renderers (GitHub, GitLab, Notion, Obsidian, VS Code
preview, mermaid.live) use to validate chart text before rendering.

The validator does **not** render. It does **not** require Chromium or
Puppeteer. It loads the official `mermaid` npm package in Node with a
minimal `jsdom` DOM shim (mermaid imports DOMPurify, which needs a `window`
and `document` to exist), then calls `await mermaid.parse(text)` for each
chart and collects the errors.

### The equivalence guarantee

If `mermaid.parse(text)` succeeds in this validator, then any renderer that
uses the same major version of the `mermaid` package will accept the chart
text. The renderer may still fail for layout reasons (out-of-bounds
labels, theme issues), but the **syntax** is guaranteed valid.

The bundled `scripts/package.json` pins `mermaid` to `^11.0.0`, matching
the version currently used by GitHub and GitLab in 2025.

### What the validator does NOT catch

| Category                            | Caught? | Notes                                  |
| ----------------------------------- | ------- | -------------------------------------- |
| Syntax errors                       | Yes     | Primary purpose                        |
| Unknown / typo'd diagram type       | Yes     | "No diagram type detected"             |
| Unbalanced brackets / quotes        | Yes     | Lexer / parser errors                  |
| Reserved keyword as node ID         | Yes     | Lexical error                          |
| Logical errors (cycles where invalid)| Yes     | If grammar enforces it                 |
| Label overflow at render time       | No      | Styling, not syntax                    |
| Theme / color mismatch              | No      | Styling                                |
| Performance issues (huge diagrams)  | No      | Will parse, may render slowly          |
| Logical mistakes (wrong arrow direction) | No | Renders fine, says the wrong thing |

If you need rendering verification, fall back to `@mermaid-js/mermaid-cli`
(`mmdc`) — but only as a CI backstop, since it pulls Chromium.

## Setup

One-time per project:

```bash
cd scripts/
npm install
```

This installs `mermaid` (`^11.0.0`) and `jsdom` (`^25.0.0`). Together
~30MB. Re-installs are not needed unless `package.json` changes.

Node 18+ required (top-level `await`, native ESM, `node:fs/promises`).

## Usage patterns

### Validate everything in a docs tree

```bash
node scripts/validate-mermaid.mjs docs/
```

Walks `docs/` recursively. Lints every `.md`, `.mdx`, `.markdown` file:
extracts ` ```mermaid ` fenced blocks and validates each. Treats `.mmd` /
`.mermaid` files as raw chart text.

Excludes by default: `node_modules/`, `.git/`, `.cache/`, `dist/`,
`build/`, `_build/`, `target/`, `.venv/`, `.next/`, `.turbo/`, and any
hidden directory.

### Validate a single file

```bash
node scripts/validate-mermaid.mjs README.md
node scripts/validate-mermaid.mjs path/to/diagram.mmd
```

### Validate piped text

```bash
echo 'flowchart TD
  A --> B' | node scripts/validate-mermaid.mjs --stdin
```

Useful for one-off validation inside an authoring loop or LLM tool call.
Exits 0 on success, 1 on parse error.

### Validate multiple roots

```bash
node scripts/validate-mermaid.mjs docs/ README.md guides/
```

## Reading the output

### Success

```
mermaid: scanned 12 file(s), validated 38 diagram(s) — all valid
```

Exit code 0.

### Failure

```
docs/architecture.md:42: mermaid parse error
  Parse error on line 3:
  ...flowchart TQ;A--x|text including
  -----------------------^
  Expecting 'NEWLINE', 'SEMI', 'EOF', 'OPEN_DIRECTIVE', ...

docs/api.md:128: mermaid parse error
  Lexical error on line 1. Unrecognized text.
  start --> end
  -------------^

mermaid: 2 error(s) across 2 file(s); scanned 12 file(s), 38 diagram(s)
```

Exit code 1. Format is `path:line:` — most editors and terminals jump to
the line on click.

### Crash

```
validate-mermaid: missing dependency `jsdom`.
  Run `npm install` in the scripts/ directory first.
```

Exit code 2. Indicates the validator itself failed to start, not a chart
error.

## Authoring loop

Tight, deterministic, no guessing:

```
┌─────────────────────────┐
│ 1. Write or edit chart  │
└──────────┬──────────────┘
           ▼
┌─────────────────────────┐
│ 2. Run validator        │
│    node scripts/...     │
└──────────┬──────────────┘
           ▼
       exit 0?
        / \
     yes   no
      │     │
      ▼     ▼
  ┌─────┐  ┌──────────────────────────────────┐
  │Done │  │ 3. Look up error in              │
  └─────┘  │    references/common-syntax-     │
           │    errors.md by message          │
           └────────────┬─────────────────────┘
                        ▼
                  ┌────────────┐
                  │ 4. Apply   │
                  │    fix     │
                  └─────┬──────┘
                        ▼
                    back to (2)
```

Never skip step 2. "Looks right" is not done. Exit code 0 is done.

## CI integration

### GitHub Actions

```yaml
# .github/workflows/mermaid.yml
name: Validate Mermaid

on:
  pull_request:
    paths:
      - '**/*.md'
      - '**/*.mdx'
      - '**/*.mmd'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install validator deps
        run: cd scripts && npm install
      - name: Validate mermaid diagrams
        run: node scripts/validate-mermaid.mjs docs/ README.md
```

### Pre-commit (lefthook)

```yaml
# lefthook.yml
pre-commit:
  commands:
    mermaid:
      glob: '*.{md,mdx,mmd}'
      run: node scripts/validate-mermaid.mjs {staged_files}
```

### Pre-commit (Husky + lint-staged)

```json
{
  "lint-staged": {
    "*.{md,mdx,mmd}": "node scripts/validate-mermaid.mjs"
  }
}
```

### Plain git pre-commit hook

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit
files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(md|mdx|mmd)$')
if [ -z "$files" ]; then exit 0; fi
node scripts/validate-mermaid.mjs $files
```

## Troubleshooting

### `Cannot find package 'mermaid'`

You did not run `npm install` in `scripts/`, or you ran the validator from
a directory without `node_modules`. Run:

```bash
cd scripts/ && npm install
```

The validator must be executed via `node /path/to/scripts/validate-mermaid.mjs`,
**after** dependencies are installed in `scripts/`.

### `ReferenceError: window is not defined`

The DOM shim failed to set up. Cause is almost always: `jsdom` is not
installed, or an older Node version is being used. Confirm Node 18+ and
re-run `npm install`.

### `Maximum call stack size exceeded` while parsing

Either a very large diagram (>200 nodes) or a genuine bug in a beta
diagram type. Try splitting the diagram. If the diagram is reasonable,
report upstream at https://github.com/mermaid-js/mermaid/issues.

### "Passes here, fails on GitHub"

Check the version on the GitHub renderer. As of mid-2025, GitHub uses
mermaid v10/v11. If you wrote a v11-only feature (e.g., `architecture-beta`,
`radar-beta`), older renderers will fail.

Workarounds:
1. Avoid `-beta` diagram types in docs that target older renderers.
2. Pin the validator to the renderer's version: edit `scripts/package.json`
   `"mermaid": "^10.0.0"` and `npm install` again.

### "Fails here, passes on Mermaid Live"

Mermaid Live often runs ahead of the npm release. If a chart works there
but not here, you may be using an unreleased syntax. Wait for the next
mermaid npm release, or rewrite using stable syntax.

### Validator hangs

Should not happen — `mermaid.parse()` is synchronous-ish (returns a
Promise that resolves immediately). If it hangs:

1. Check Node version (`node --version`). Must be ≥ 18.
2. Try a tiny known-good chart to isolate: `echo 'flowchart TD\n A --> B' | node scripts/validate-mermaid.mjs --stdin`.
3. If even that hangs, reinstall deps: `cd scripts && rm -rf node_modules package-lock.json && npm install`.

## Performance notes

- Cold start: ~500ms (loading mermaid + jsdom).
- Per-diagram parse: ~5–20ms for typical charts, ~50–100ms for very large.
- A 100-file repo with 200 diagrams validates in ~3–5 seconds total.

This is fast enough for pre-commit hooks. No need to parallelize or cache
unless your repo exceeds 1000 diagrams.

## When to escalate beyond syntax validation

Syntax validation is a **necessary**, not **sufficient**, quality gate.
After syntax passes, also verify:

1. **The chart says what you meant.** Reread the labels.
2. **The chart type matches the relationship.** See `chart-selection.md`.
3. **The chart fits on one screen** (or is intentionally split).
4. **Labels are unambiguous** and use the reader's vocabulary.

For rendering verification (the chart actually draws correctly), use
`@mermaid-js/mermaid-cli` in CI:

```bash
npx -p @mermaid-js/mermaid-cli mmdc -i diagram.mmd -o diagram.svg
```

This is heavyweight (Chromium) and slow (~3s per diagram). Reserve it for
publication gates, not authoring loops.
