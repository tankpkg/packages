# ast-grep Rules and Patterns

Sources: ast-grep.github.io documentation, coderabbitai/ast-grep-essentials, ast-grep MCP and agent integrations, 2025-2026 ecosystem research

ast-grep (sg) is a Rust-powered CLI tool for structural code search, linting, and rewriting across 20+ languages. Rules are declarative YAML, making them well-suited for AI agent generation and review.

---

## 1. Pattern Syntax

Patterns are code snippets that match structurally, not textually. Whitespace and formatting differences are ignored; AST shape is what matters.

| Syntax | Matches | Captured? |
|--------|---------|-----------|
| `$VAR` | Any single AST node | Yes — use `$VAR` in `fix` |
| `$$$VARS` | Zero or more nodes (variadic) | Yes — use `$$$VARS` in `fix` |
| `$_` | Any single node (wildcard) | No |

Metavariable names must be uppercase. The same name used twice enforces equality — `$A === $A` matches only when both sides are identical text.

```bash
sg run -p 'console.log($MSG)' --lang typescript   # single capture
sg run -p 'foo($$$ARGS)' --lang javascript         # variadic
sg run -p '($$$PARAMS) => $BODY' --lang javascript # arrow function
sg run -p 'use$HOOK($$$)' --lang tsx              # prefix match
```

Patterns must be syntactically valid code. Use the playground at ast-grep.github.io/playground.html to iterate on patterns and inspect tree-sitter node kinds.

---

## 2. Rule Types

Rules compose three layers: atomic (what to match), relational (where it must appear), and composite (boolean logic).

### Atomic Rules

Three atomic matchers: `pattern` (code template), `kind` (tree-sitter node type), `regex` (text match on node content). Find node kinds with `sg run --debug-query` or the playground.

### Relational Rules

| Key | Meaning | Common use |
|-----|---------|------------|
| `inside` | Node is a descendant of the specified node | Scope restriction |
| `has` | Node has a descendant matching the rule | Content requirement |
| `follows` | Node appears after the specified node | Import-then-use |
| `precedes` | Node appears before the specified node | Declaration order |

All relational rules accept `stopBy`:
- `stopBy: neighbor` (default) — immediate parent/child only
- `stopBy: end` — search all ancestors/descendants to scope boundary

```yaml
rule:
  pattern: await $EXPR
  inside:
    kind: arrow_function          # await must be inside arrow function

rule:
  pattern: Promise.all($A)
  has:
    pattern: await $_
    stopBy: end                   # await anywhere inside Promise.all
```

### Composite Rules

```yaml
rule:
  all:                            # AND — every condition must match
    - pattern: console.$METHOD($$$)
    - not:
        inside:
          kind: catch_clause
          stopBy: end

rule:
  any:                            # OR — at least one must match
    - pattern: console.log($$$)
    - pattern: console.debug($$$)
```

Composite rules nest arbitrarily. `all` inside `any` inside `not` is valid.

---

## 3. YAML Rule Format

```yaml
id: no-console-in-production   # unique, kebab-case
language: TypeScript            # JavaScript, Python, Go, Rust, etc.
severity: warning               # error | warning | info | hint
message: "Avoid console statements outside catch blocks"
note: "Use a structured logger. See docs/logging.md"
url: https://example.com/docs  # shown in IDE hover
rule:
  # ... matching logic
fix: ""                         # optional auto-fix string
```

`severity: error` causes `sg scan` to exit non-zero. `message` supports metavariable interpolation: `"Found $METHOD call"` substitutes the captured text.

---

## 4. Fix and Rewrite

The `fix` string replaces the matched node. Metavariables are substituted directly:

```yaml
id: remove-await-in-promise-all
language: TypeScript
severity: error
message: "await inside Promise.all defeats parallelism"
rule:
  pattern: await $A
  inside:
    pattern: Promise.all($_)
    stopBy: end
fix: $A
```

### Transform Operations

`transform` derives new variables from captured ones before substituting into `fix`:

```yaml
id: screaming-snake-constant
language: JavaScript
rule:
  pattern: const $NAME = $VALUE
transform:
  UPPER:
    convert:
      source: $NAME
      toCase: SCREAMING_SNAKE_CASE
fix: const $UPPER = $VALUE
```

| Operation | Purpose |
|-----------|---------|
| `replace` | Regex substitution on captured text |
| `substring` | Slice captured text by index |
| `convert` | Case conversion: `camelCase`, `snake_case`, `SCREAMING_SNAKE_CASE`, `PascalCase`, `kebab-case` |
| `rewrite` | Apply a named rewriter sub-rule to the captured node |

`rewrite` enables recursive transformation of captured subtrees — the most powerful option for multi-level migrations.

Apply fixes via `--rewrite` (preview), `--rewrite --interactive` (approve each), or `--rewrite -U` (apply all).

---

## 5. Constraints

Constraints add conditions to captured metavariables after the structural match. A node that matches the pattern but fails a constraint is not reported. Multiple constraints on the same variable combine with AND.

```yaml
# Restrict METHOD to specific values
rule:
  pattern: console.$METHOD($$$)
constraints:
  METHOD:
    regex: "^(log|debug|warn)$"

# Require VALUE to be a literal string, not a variable reference
constraints:
  VALUE:
    kind: string

# Detect weak RSA key sizes (< 2048 bits) via numeric regex
constraints:
  R:
    regex: "^(-?(0|[1-9][0-9]{0,2}|1[0-9]{3}|20[0-3][0-9]|204[0-7]))$"
```

---

## 6. Project Setup

Place `sgconfig.yml` at the repository root:

```yaml
ruleDirs:
  - rules/     # YAML rule files
utilDirs:
  - utils/     # reusable rule fragments
testConfigs:
  - testDir: tests/
```

Organize rules by language then category: `rules/typescript/security/`, `rules/javascript/style/`. Test files mirror the rule path under `tests/`. `sg scan` without arguments reads `sgconfig.yml` and applies all rules in `ruleDirs`.

---

## 7. CLI Commands

```bash
sg run -p 'PATTERN' --lang LANGUAGE [PATH]                         # search
sg run -p 'PATTERN' --rewrite 'REPLACEMENT' --lang LANGUAGE [PATH] # preview rewrite
sg run -p 'PATTERN' --rewrite 'REPLACEMENT' -U --lang LANGUAGE     # apply all
sg scan --rule rules/no-console.yml src/                           # single rule
sg scan                                                             # full project (sgconfig.yml)
sg scan --json                                                      # JSON for tooling
sg test                                                             # run test suite
sg new rule                                                         # scaffold interactively
sg lsp                                                              # language server
```

---

## 8. Testing Rules

Test files mirror the rule file path under `testDir`:

```yaml
# tests/typescript/style/no-console.yml
id: no-console-in-production
valid:
  - "try { doSomething(); } catch (e) { console.error(e); }"
invalid:
  - code: "console.log('hello');"
  - code: "console.warn('deprecated');"
```

For rules with `fix`, assert the output with `fixed`:

```yaml
invalid:
  - code: "await Promise.resolve(x)"
    fixed: "Promise.resolve(x)"
```

Tests fail if a `valid` case is flagged or an `invalid` case is not flagged.

---

## 9. Utility Rules

Utility rules are reusable fragments that other rules reference with `matches`. Define them in `utilDirs` — they do not produce diagnostics on their own.

```yaml
# utils/is-require-call.yml
id: is-require-call
language: JavaScript
rule:
  kind: call_expression
  has:
    kind: identifier
    regex: "^require$"

# rules/javascript/no-cjs-require.yml
id: no-cjs-require
language: JavaScript
severity: warning
message: "Use ES module import instead of require()"
rule:
  matches: is-require-call
```

Compose multiple utilities with `any` and add `constraints` to narrow matches further — for example, matching only numbers below 2048 for a weak RSA key rule:

```yaml
rule:
  kind: number
  any:
    - matches: MATCH_BITS_NODE_FORGE
    - matches: MATCH_BITS_NODE_RSA
constraints:
  R:
    regex: "^(-?(0|[1-9][0-9]{0,2}|1[0-9]{3}|20[0-3][0-9]|204[0-7]))$"
```

---

## 10. Real-World Rule Examples

### Ban Deprecated Library

```yaml
id: no-moment-js
language: TypeScript
severity: error
message: "moment.js is deprecated. Use date-fns or Temporal instead."
url: https://momentjs.com/docs/#/-project-status/
rule:
  any:
    - pattern: import $_ from 'moment'
    - pattern: require('moment')
```

### Detect Security Issue — JWT Without Verification

```yaml
id: jwt-simple-noverify
language: TypeScript
severity: warning
message: "Decoding a JWT without verification. Pass false as the third argument only in tests."
rule:
  pattern: $JWT.decode($TOKEN, $SECRET, $NOVERIFY $$$)
  inside:
    stopBy: end
    follows:
      stopBy: end
      kind: lexical_declaration
      has:
        kind: call_expression
        has:
          kind: string_fragment
          regex: "^jwt-simple$"
constraints:
  NOVERIFY:
    any:
      - regex: "^true$"
      - kind: string
```

### Enforce Naming Convention

```yaml
id: react-component-pascal-case
language: TSX
severity: warning
message: "React component '$NAME' must use PascalCase."
rule:
  kind: function_declaration
  all:
    - has:
        kind: identifier
        pattern: $NAME
    - has:
        kind: jsx_element
        stopBy: end
constraints:
  NAME:
    regex: "^[a-z]"
```

### Migrate API — Remove React forwardRef Wrapper

```yaml
id: remove-forward-ref-wrapper
language: TSX
severity: hint
message: "React 19: forwardRef wrapper is no longer needed."
rule:
  pattern: forwardRef(($$$PARAMS) => $BODY)
fix: ($$$PARAMS) => $BODY
```

### Detect Async Without Error Handling

```yaml
id: async-without-try-catch
language: TypeScript
severity: warning
message: "Async function uses await but has no try/catch."
rule:
  kind: function_declaration
  all:
    - has:
        kind: await_expression
        stopBy: end
    - not:
        has:
          kind: try_statement
          stopBy: end
```

---

## 11. Agent Integration

`ast-grep-mcp` exposes structural search to MCP-compatible agents — agents call `sg_search` with a pattern and language and receive matches with file path, line range, and matched text.

```bash
npx ast-grep-mcp
```

For LLM rule generation, fetch the full documentation bundle:

```
https://ast-grep.github.io/llms-full.txt
```

Add this directive to `AGENTS.md` to bias agents toward structural search:

```markdown
Prefer `ast-grep` over `grep` for any search involving code structure.
- Find async functions: `sg run -p 'async function $NAME($$$) { $$$ }' --lang typescript`
- Find useEffect calls: `sg run -p 'useEffect($$$)' --lang tsx`
For multi-file lint rules, write a YAML rule file and run `sg scan --rule rule.yml`.
```

ast-grep suits agent workflows: YAML rules are straightforward for LLMs to generate, the CLI integrates with any tool-calling mechanism, dry-run by default allows safe previewing, and Rust + tree-sitter speed supports tight loops across TypeScript, Python, Go, Rust, and more.

---

## Rule Key Reference

| Key | Layer | Purpose |
|-----|-------|---------|
| `pattern` / `kind` / `regex` | Atomic | What to match |
| `inside` / `has` / `follows` / `precedes` | Relational | Where it must appear |
| `all` / `any` / `not` | Composite | Boolean logic |
| `matches` | Utility | Reference a utility rule by id |
| `constraints` | Constraint | Regex/kind conditions on metavariables |
| `stopBy: end` | Modifier | Search all descendants, not just immediate |
