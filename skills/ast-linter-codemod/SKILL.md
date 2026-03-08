---
name: "@tank/ast-linter-codemod"
description: |
  Build custom linters with auto-fix, write codemods for API migrations, and
  run large-scale code transforms using ts-morph, jscodeshift, ESLint custom
  rules, ast-grep, and Babel plugins. Covers AST fundamentals, the Visitor
  pattern, Fixer API, Collection API, YAML rule authoring, fixture-based
  testing, migration strategies, formatting preservation, and idempotency.
  Synthesizes Nystrom (Crafting Interpreters), Kyle (Babel Plugin Handbook),
  Noback/Votruba (Rector), ESTree spec, and production patterns from React,
  Next.js, and Angular codemods.

  Trigger phrases: "codemod", "linter", "custom lint rule", "ESLint rule",
  "auto-fix", "autofix", "ts-morph", "jscodeshift", "ast-grep", "AST",
  "abstract syntax tree", "code migration", "code transform",
  "custom ESLint plugin", "Fixer API", "RuleTester", "babel plugin",
  "recast", "migration script", "deprecation", "API rename",
  "refactoring tool", "lint rule with fix", "sg rule", "typed linting",
  "write a codemod", "build a linter", "AST transform"
---

# AST Linters, Codemods, and Migration Tools

Build linters that catch bugs and fix them automatically. Write codemods that
migrate entire codebases. Ship migration tools that handle edge cases.

## Core Philosophy

1. **Parse, don't regex.** Text manipulation breaks on edge cases. AST tools
   understand code structure — template literals, JSX, decorators, and all.
2. **Every lint rule deserves a fix.** A rule without auto-fix is a rule that
   creates manual work. Ship the fix with the rule.
3. **Test with fixtures, not assertions.** Input file → expected output file.
   Fixtures are readable, diffable, and catch regressions that assertions miss.
4. **Analyze first, transform second.** Collect all findings before mutating.
   AST manipulation invalidates nodes — iterating and mutating simultaneously
   causes forgotten-node bugs.
5. **Idempotent transforms only.** Running a codemod twice must produce the
   same output. If it doesn't, the codemod has a detection gap.

## Quick-Start: What Are You Building?

### "I need a custom ESLint rule with auto-fix"

1. Define the pattern to detect (use astexplorer.net to identify node types)
2. Write the rule with `context.report()` + `fix(fixer)` function
3. Test with `RuleTester` — valid cases, invalid cases, fix output
4. Package as an ESLint plugin

See `references/eslint-custom-rules.md`

### "I need a codemod to migrate an API"

1. Pick tool: jscodeshift for JS/TS transforms, ts-morph for type-aware transforms
2. Write the transform function (find pattern → replace pattern)
3. Test with input/output fixture pairs
4. Run with `--dry --print` first, then apply

See `references/jscodeshift-codemods.md` or `references/ts-morph-patterns.md`

### "I need to enforce a pattern across the codebase"

1. If simple pattern: use ast-grep YAML rules (fastest to write)
2. If needs type information: use ts-morph or typed ESLint rule
3. If needs CI integration: use ESLint plugin

See `references/ast-grep-rules.md`

### "I need to run a large-scale migration"

1. Audit: identify all patterns to transform
2. Prototype: write codemod for the most common pattern
3. Validate: run on a subset, review diffs
4. Execute: run across codebase with parallel processing
5. Clean up: fix remaining edge cases manually

See `references/migration-strategies.md`

## Tool Selection Decision Tree

| Scenario | Best Tool | Why |
|----------|-----------|-----|
| Quick pattern ban or rename | **ast-grep** | YAML rules, fastest to write, no JS required |
| ESLint rule with auto-fix for CI | **ESLint custom rule** | Integrates with existing lint pipeline |
| Type-aware linting or refactoring | **ts-morph** | Full TypeScript type checker access |
| API migration across many files | **jscodeshift** | Batch processing, formatting preservation via recast |
| Type-aware API migration | **ts-morph** | Type resolution for ambiguous patterns |
| Build-time code transform | **Babel plugin** | Integrates with build pipeline |
| One-off search and replace | **ast-grep CLI** | `sg run --pattern '$OLD' --rewrite '$NEW'` |

## Tool Capabilities Matrix

| Feature | ts-morph | jscodeshift | ESLint | ast-grep | Babel |
|---------|----------|-------------|--------|----------|-------|
| Type information | Full | None | Via typed linting | None | None |
| Format preservation | Manual | Automatic (recast) | Source ranges | Automatic | Via recast |
| Auto-fix API | DIY | replaceWith/remove | Fixer API | fix: in YAML | path.replaceWith |
| Testing framework | DIY | defineTest + fixtures | RuleTester | YAML test fixtures | babel-plugin-tester |
| Speed | Medium | Medium | Fast | Very fast | Fast |
| Learning curve | Medium | Medium | Low-Medium | Low | High |
| Language support | TS/JS | JS/TS/Flow | JS/TS/JSX | 25+ languages | JS/TS/JSX/Flow |
| CI integration | Script | Script | Native | CLI/CI | Build config |

## Common Patterns Across All Tools

### Find → Report → Fix

Every tool follows the same high-level pattern:

```
1. Parse source into AST
2. Find nodes matching a pattern (visitor, query, or traversal)
3. Report the finding (error message, location)
4. Apply a fix (replace text, insert, remove)
5. Output modified source (preserving formatting where possible)
```

### The Dirty Flag

Return `undefined`/`null` when no changes were made. Prevents unnecessary
file writes and makes diffs clean.

### Import-First Detection

Always check imports before analyzing usage. If the target API isn't imported,
skip the file entirely. Saves time and avoids false positives.

### Comment Escape Hatches

Support `// codemod-ignore` or `// eslint-disable-next-line` patterns so
developers can opt out of automated transforms for edge cases.

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Regex-based transforms | Breaks on edge cases (strings, comments, JSX) | Use AST tools |
| Mutating during traversal | Forgotten nodes, infinite loops | Collect changes, then apply |
| No idempotency test | Running twice corrupts code | Add "already transformed" detection |
| Fixing without testing | Silent code breakage | Fixture tests for every fix |
| Ignoring formatting | Clean diffs become noise | Use recast or ast-grep's format preservation |
| Hardcoding node types | Misses variants (class method vs arrow function) | Handle all syntactic forms |
| No dry-run mode | Can't preview changes | Always support `--dry` flag |

## Failure Map

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Node was forgotten" (ts-morph) | Mutated AST during iteration | Collect all changes first, apply after |
| Fix creates syntax error (ESLint) | Overlapping fix ranges | Use `fixer.replaceTextRange` with exact ranges |
| Codemod misses some files | Parser mismatch (JS vs TS vs JSX) | Detect file extension, select parser |
| Formatting destroyed after transform | Wrong printer or missing recast | Use recast for jscodeshift, toSource options |
| Type information unavailable | Missing tsconfig or wrong project setup | Pass tsConfigFilePath to ts-morph Project |
| Transform not idempotent | Missing "already transformed" check | Add guard: skip if new pattern already present |

## Reference Files

| File | Contents |
|------|----------|
| `references/ast-fundamentals.md` | AST mental model, parse→transform→generate pipeline, ESTree/TS node types, Visitor pattern, tool selection decision tree, tool comparison matrix |
| `references/ts-morph-patterns.md` | ts-morph Project setup, node navigation, type system access, linter patterns, codemod patterns, analyze-then-transform, performance |
| `references/eslint-custom-rules.md` | ESLint rule architecture, Fixer API (all 8 methods), auto-fixable rules, suggestion API, typed linting, RuleTester, plugin scaffolding |
| `references/jscodeshift-codemods.md` | jscodeshift Collection API, find/filter/replace, formatting preservation, production patterns from React/Next.js codemods |
| `references/ast-grep-rules.md` | ast-grep pattern syntax, metavariables, YAML rule format, fix/rewrite, constraints, sgconfig, testing, agent integration |
| `references/migration-strategies.md` | Big Bang vs Gradual vs Module-by-Module, 5-phase toolchain, codemod composition, edge cases, Stripe/Pinterest case studies |
| `references/testing-transforms.md` | Fixture-based testing, RuleTester, ast-grep YAML tests, idempotency testing, edge case catalog, CI integration |
