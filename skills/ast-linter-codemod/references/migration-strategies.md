# Large-Scale Migration Strategies

Sources: Stripe Engineering (Flow→TypeScript 3.7M lines), Pinterest Engineering (JS→TypeScript), Noback/Votruba (Rector: Automated Refactoring), Angular/React migration patterns, 2025-2026 industry practices

This reference covers strategy and process for large-scale code migrations. Tool-specific APIs belong in the tool references. Testing patterns belong in testing-transforms.md.

---

## 1. Migration Strategy Selection

Three patterns dominate production migrations. Choose based on codemod maturity, team size, and risk tolerance.

| Strategy | When to Use | Risk | Duration |
|----------|-------------|------|----------|
| Big Bang (single PR) | Proven codemod, well-understood migration, small team | High upfront, low ongoing | Days to weeks |
| Gradual (file-by-file) | Unproven automation, large team, no full coverage | Low per-change, high coordination | Months |
| Module-by-Module | Well-modularized codebase, clear ownership boundaries | Medium | Weeks to months |

**Big Bang** works when the codemod covers 95%+ of cases automatically. Stripe converted 3.7M lines of Flow to TypeScript in a single weekend PR. The key precondition: they had already validated the codemod on a representative sample and knew the residual manual work was bounded.

**Gradual** is safer but creates a long-lived mixed state. Engineers must maintain two mental models simultaneously. Voluntary adoption without coordination produces inconsistent results — a platform team must own the migration and enforce progress.

**Module-by-Module** requires a dependency graph. Migrate leaf modules first (no internal dependencies), then work inward. This avoids the mixed-state problem of gradual migration while reducing the blast radius of any single change.

Decision matrix:

| Condition | Favors |
|-----------|--------|
| Codemod automation > 95% | Big Bang |
| Codemod automation 70–95% | Module-by-Module |
| Codemod automation < 70% | Gradual |
| Team > 50 engineers | Gradual or Module-by-Module |
| Team < 20 engineers | Big Bang |
| Zero type errors in baseline | Big Bang |
| Existing type errors in baseline | Gradual |
| Monorepo with clear package boundaries | Module-by-Module |
| Monolith with tangled imports | Big Bang or Gradual |

---

## 2. The 5-Phase Migration Toolchain

Every successful large-scale migration follows this sequence. Skipping phases produces regressions that are expensive to diagnose.

### Phase 1: Audit

Quantify the migration surface before writing a single transform.

- Count files and lines by type: `find src -name "*.flow" | wc -l`
- Sample 50–100 files manually to identify pattern distribution
- Categorize patterns: common (>5% of files), uncommon (1–5%), rare (<1%), manual-only
- Estimate automation coverage: what percentage of files can be fully automated?
- Identify blockers: patterns that require type information, runtime behavior, or human judgment

Output: a written scope document with pattern catalog and automation estimate. This document drives codemod development priorities.

### Phase 2: Prepare

Set up the infrastructure before running any transforms.

- Configure the target toolchain (TypeScript compiler, new linter, build system)
- Establish a baseline: run `tsc --noEmit` and record the error count (should be 0 for a clean migration)
- Run the full test suite and record pass rate
- Set up CI for the target language/configuration
- Create a migration branch strategy (single long-lived branch vs. many small PRs)
- Write the codemod for the 80% common case first; defer edge cases

### Phase 3: Transform

Execute the codemod and handle residual cases.

- Run on a 10% sample first; review diffs manually before full execution
- Execute the codemod on the full codebase
- Commit the automated changes separately from manual fixes — this preserves reviewability
- Triage residual errors: categorize by pattern, fix the most common patterns with additional codemods
- Insert `// TODO(migration): manual review needed` comments for cases that cannot be automated

The Angular team's approach for large monorepos: use environment variables to shard the migration across CI workers. Run `CURRENT_SHARD=1 NUM_SHARDS=4` to process one quarter of files per worker, then merge results.

### Phase 4: Validate

Confirm the migration did not introduce regressions. See testing-transforms.md for detailed test patterns.

- Type check: `tsc --noEmit` — error count must be equal to or lower than baseline
- Test suite: pass rate must match baseline
- Build: production build must succeed
- Spot-check: manually review 20 randomly selected files
- Linter: run ESLint or Biome on the output

### Phase 5: Clean Up

Harden the codebase after the migration completes.

- Enable stricter compiler options incrementally (`strict`, `noImplicitAny`, `strictNullChecks`)
- Add lint rules to prevent regression to the old pattern
- Remove migration scaffolding (compatibility shims, temporary type aliases)
- Update documentation and onboarding guides
- Archive the codemod in the repository for reference

---

## 3. Codemod Composition

Complex migrations require multiple transforms applied in sequence. Composition is the primary tool for managing this complexity.

### Chaining Transforms

The Next.js codemod runner demonstrates the canonical composition pattern:

```typescript
export default function transform(file: FileInfo, api: API) {
  const transforms = [transformDynamicProps, transformDynamicAPI];
  return transforms.reduce<string>((source, transformFn) => {
    const result = transformFn(source, api, file.path);
    if (!result) return source;
    return result;
  }, file.source);
}
```

Each transform receives the output of the previous one. If a transform returns null (no changes), the source passes through unchanged. This pattern allows independent transforms to be developed and tested in isolation, then composed for the full migration.

### Ordering Dependencies

Transform order matters when one transform's output is another's input. Common ordering rules:

1. Import renames before usage renames — rename the module path before renaming the imported symbols
2. Type annotation additions before type assertion removals — add explicit types before removing casts
3. Structural changes before cosmetic changes — change the AST shape before adjusting formatting
4. Removal transforms last — remove deprecated patterns only after replacements are in place

Violating these rules produces intermediate states that fail type checking, which breaks validation between phases.

### Parameterized Codemods

Avoid hardcoding module names and symbol names in transforms. Accept them as options:

```typescript
export default function transform(file: FileInfo, api: API, options: Options) {
  const fromModule = options.from || 'old-module';
  const toModule = options.to || 'new-module';
  // ...
}
// Usage: jscodeshift -t transform.ts --from=lodash --to=lodash-es src/
```

Parameterization enables the same transform to serve multiple migration targets. The React codemod collection uses this pattern extensively — a single rename transform handles dozens of API changes by accepting the old and new names as parameters.

---

## 4. Formatting Preservation

Formatting preservation is not cosmetic. Diffs that reformat unchanged code are unreviable at scale and generate spurious merge conflicts.

### How recast Preserves Formatting

recast (the formatting layer under jscodeshift) uses a "print only what changed" strategy:

1. Parse source into an AST with source location info attached to every node
2. When printing, check whether each node was modified
3. Unmodified nodes: print verbatim from the original source bytes
4. Modified nodes: pretty-print using the code generator

The result: only the lines you actually changed appear in the diff. A rename of one import path produces a one-line diff even in a 500-line file.

### Comment Handling

Comments are attached to AST nodes as `leadingComments` and `trailingComments`. When you replace a node, comments do not transfer automatically.

Preserve comments on node replacement:

```typescript
const newNode = j.identifier('newName');
newNode.comments = path.node.comments;  // transfer explicitly
j(path).replaceWith(newNode);
```

For the first node in a file (which often carries license headers or `@flow` annotations), save and restore comments explicitly:

```typescript
const firstNode = root.find(j.Program).get('body', 0).node;
const { comments } = firstNode;
// ... transform ...
const firstNodeAfter = root.find(j.Program).get('body', 0).node;
if (firstNodeAfter !== firstNode) {
  firstNodeAfter.comments = comments;
}
```

### Known Pitfalls and Workarounds

| Issue | Tool | Workaround |
|-------|------|------------|
| JSXText leading space lost | recast upstream | Use `@putout/recast` fork |
| Comments lost on node replacement | jscodeshift | Transfer `.comments` manually |
| Parentheses removed around expressions | @babel/generator | Use recast instead of @babel/generator |
| Indentation changed | ts-morph | Set `manipulationSettings.setIndentationText()` |
| Quote style changed | recast | Pass `{ quote: 'single' }` to `toSource()` |
| Trailing comma added/removed | recast | Pass `{ trailingComma: false }` to `toSource()` |

Prefer in-place mutation over node replacement when possible. Changing `path.node.source.value = 'new-module'` preserves all surrounding formatting. Rebuilding the entire `ImportDeclaration` node loses it.

---

## 5. Edge Cases in Transforms

These patterns appear in nearly every large-scale migration and require explicit handling.

### Template Literals

Template literals have a non-obvious AST structure: alternating `quasis` (static string parts) and `expressions` (interpolated values). Modifying an expression inside a template literal requires indexing into both arrays simultaneously.

When migrating from string concatenation to template literals, watch for expressions that contain backticks — they must be escaped in the output.

Babel 8 introduced a breaking change: TypeScript template literal types (`type T = \`Hello ${string}\``) now produce `TSTemplateLiteralType` nodes instead of `TemplateLiteral`. Check your Babel version when writing transforms that touch template literal types.

### JSX

JSX requires the TSX parser (`--parser=tsx`). Key edge cases:

- Self-closing vs. paired tags: renaming a component requires updating both `openingElement.name` and `closingElement.name`
- Fragments (`<>...</>`) have no name property — pattern matching on component name will not find them
- JSXText whitespace: recast issue #886 causes leading spaces in JSXText to be lost on reprint
- Spread attributes (`<Comp {...props} />`) cannot be matched by attribute name

### Decorators

Decorator AST representation changed between TypeScript legacy decorators (`experimentalDecorators: true`) and TC39 Stage 3 decorators. The same `@Injectable()` syntax produces different AST node types depending on the TypeScript configuration. Detect which mode is active before writing decorator transforms.

Parameter decorators exist only in legacy mode and have no equivalent in Stage 3 decorators — they require manual migration.

### Type Assertions

TypeScript supports two syntaxes for type assertions: `value as Type` (preferred) and `<Type>value` (not valid in TSX files). A migration from angle-bracket assertions to `as` assertions must skip TSX files or handle the parser difference.

### Async/Await

When making a function `async` to support `await`, check for nested sync functions that access the same data. The Next.js `next-async-request-api` codemod handles this by detecting the closest parent function scope for each `await` insertion point — if the closest parent is a sync nested function, it inserts a comment instead of awaiting.

### Destructuring

Object destructuring patterns appear in function parameters, variable declarations, and catch clauses. A rename of a property key must handle all three locations. The property key and the local binding name are separate AST nodes — renaming the key without renaming the local binding (or vice versa) produces broken code.

---

## 6. Pre/Post Migration Validation

Validation gates prevent regressions from reaching production. Run these checks at each phase boundary.

Record the baseline before any transforms: type error count (`tsc --noEmit 2>&1 | grep "error TS" | wc -l`), test pass rate, and build status. Post-migration, each metric must be equal to or better than baseline.

Spot-check protocol: select 20 files at random (`shuf -n 20 <(find src -name "*.ts")`) and review each diff manually. Look for dropped comments, formatting changes in untouched regions, incorrectly inferred type annotations, and partially renamed import paths.

---

## 7. Idempotency

A codemod is idempotent if running it twice produces the same result as running it once. Idempotency is not optional for production codemods — it enables safe re-runs when new files are added or when the codemod is applied incrementally.

The Rector book (Noback/Votruba) identifies idempotency as a first-class requirement and provides a testing recipe: run the transform on its own output and assert the output is unchanged.

Idempotency failures occur when:

- A transform adds a prefix or suffix unconditionally (running twice doubles it)
- A transform inserts an import without checking whether it already exists
- A transform renames a symbol that was already renamed by a previous run

Guard against these by checking preconditions before transforming:

```typescript
// Check before inserting import
const alreadyImported = root.find(j.ImportDeclaration, {
  source: { value: 'new-module' }
}).size() > 0;

if (!alreadyImported) {
  // insert import
}
```

The dirty flag pattern (`let isDirty = false`) naturally supports idempotency: if the precondition check finds nothing to transform, the flag stays false and the file is not written.

---

## 8. Parallel Processing

Large codebases (>10,000 files) require parallel processing to complete migrations in reasonable time.

### Worker Threads

jscodeshift runs transforms in parallel by default, spawning one worker per CPU core. Control parallelism with `--cpus`:

```bash
npx jscodeshift -t transform.ts src/ --cpus=8
```

For ts-morph-based tools that do not have a built-in runner, implement worker threads manually:

```typescript
const NUM_WORKERS = Math.max(1, os.cpus().length);
for (let i = 0; i < NUM_WORKERS; i++) {
  const fileChunk = sourceFiles.slice(start, end).map(sf => sf.getFilePath());
  const worker = new Worker(__filename, { workerData: { filePaths: fileChunk } });
}
```

### File Sharding

For migrations that must be distributed across CI workers or run incrementally, shard by file hash:

```typescript
const isFileInShard = (filePath: string): boolean => {
  return Math.abs(hashCode(filePath) % NUM_SHARDS) === CURRENT_SHARD - 1;
};
// Run as: CURRENT_SHARD=1 NUM_SHARDS=4 node migrate.js
```

Hash-based sharding ensures each file is processed by exactly one shard and the assignment is deterministic across runs.

### The Angular Shard Pattern

Angular's signal migration uses an environment variable to limit processing to root files during development, then the full set for production:

```bash
LIMIT_TO_ROOT_NAMES_ONLY=1 node migrate.js   # fast iteration
node migrate.js                               # full run
```

---

## 9. Escape Hatches

Not every pattern can be safely automated. Escape hatches allow the codemod to make progress while flagging cases that require human review.

### Ignore Comments

Every production codemod ecosystem supports a per-line opt-out:

```typescript
// eslint-disable-next-line rule-name
// ts-morph: check getLeadingCommentRanges() for ignore marker
// jscodeshift: check path.node.leadingComments for disable comment
```

Implement ignore support in custom codemods:

```typescript
const IGNORE_COMMENT = '// migration-ignore-next';
const hasIgnoreComment = (path: ASTPath): boolean => {
  return path.node.leadingComments?.some(c =>
    c.value.trim() === 'migration-ignore-next'
  ) ?? false;
};
```

### TODO Markers

When a transform cannot safely automate a case, insert a structured comment rather than skipping silently or failing:

```typescript
// Next.js pattern: NEXT_CODEMOD_ERROR_PREFIX
j.commentBlock(` CODEMOD_ERROR: This Link previously used legacyBehavior. Verify child component does not render an anchor. `);
```

Structured prefixes (`CODEMOD_ERROR:`, `MIGRATION_TODO:`) allow the team to find all manual review items with a single grep after the automated pass completes.

### Suggest vs. Fix

ESLint distinguishes between `fix` (applied automatically) and `suggest` (requires user approval). Apply the same distinction to codemods:

- Use automated transforms for patterns where the correct output is deterministic
- Use TODO comments for patterns where the correct output depends on runtime behavior or business logic
- The React hooks exhaustive-deps rule uses `suggest` instead of `fix` because auto-fixing dependency arrays can introduce infinite render loops

---

## 10. Case Studies

### Stripe: 3.7M Lines Flow → TypeScript (2022)

Scale: 3.7 million lines, single PR, one weekend. Strategy: Big Bang. Stripe contacted Airtable (who had done a similar migration) and built on their open-source `flow-to-typescript-codemod`. The codemod automated 95%+ of conversions; residual `any` types were accepted as technical debt. Single PR avoided long-lived branches; weekend execution minimized team disruption.

Source: stripe.com/blog/migrating-to-typescript

### Pinterest: 3.7M Lines Flow → TypeScript (2025)

Scale: 3.7 million lines, 8 months.

Strategy: Three-phase gradual migration. Pinterest achieved 100% Flow coverage before starting — no files were partially typed. This made the migration all-or-nothing rather than gradual at the file level.

Phase 1 (Setup): Configure TypeScript compiler, set up CI, create migration tooling.
Phase 2 (Conversion): Run `flow-to-typescript-codemod` (Stripe's tool) on all files, handle edge cases with custom rules.
Phase 3 (Integration): Daily automated testing, type error triage, gradual rollout.

Key insight: "We achieved 100% Flow coverage first, meaning no gradual transition left. It was all or nothing."

Source: medium.com/pinterest-engineering/migrating-3-7-million-lines-of-flow-code-to-typescript-8a836c88fea5

### Angular Schematics: 14 Official Migrations

Angular ships official migration schematics with each major version (signal migration, output migration, control flow migration). Architecture: a two-phase Tsurge framework — analyze phase collects `Replacement[]` (text spans + new text) by walking the AST; migrate phase applies them. This separation enables parallelism and dry-run mode. The schematics integrate with `ng update @angular/core`, which applies both the npm version bump and the corresponding code transforms automatically.

### React Codemods: Incremental API Evolution

The `reactjs/react-codemod` repository contains 15+ transforms covering React 15 through React 19. The pattern: ship the deprecation warning in version N, ship the codemod alongside the breaking change in version N+1.

- React 16.3: `rename-unsafe-lifecycles` — prefix deprecated lifecycle methods with `UNSAFE_`
- React 18: `replace-reactdom-render` — `ReactDOM.render()` → `createRoot().render()`
- React 19: `remove-forward-ref` — unwrap `React.forwardRef()` (ref is now a regular prop)

Engineers run `npx react-codemod <transform-name>` before upgrading.

---

## 11. Migration Planning Checklist

Use this template before starting any migration affecting more than 500 files.

### Pre-Migration Assessment

- [ ] File count and LOC by type (run `find` + `wc -l`)
- [ ] Pattern catalog: sample 50 files, list all patterns requiring transformation
- [ ] Automation estimate: what percentage of files can be fully automated?
- [ ] Blocker identification: which patterns require type information or human judgment?
- [ ] Baseline recorded: type error count, test pass rate, build status
- [ ] Strategy selected: Big Bang / Gradual / Module-by-Module (with rationale)
- [ ] Codemod validated on 10% sample before full execution
- [ ] Escape hatch defined: ignore comment syntax, TODO marker prefix
- [ ] Rollback plan: can the migration be reverted if a critical bug is found post-merge?

### Execution Checklist

- [ ] Codemod run in dry-run mode first (`--dry` flag)
- [ ] Automated changes committed separately from manual fixes
- [ ] Type check passes (error count <= baseline)
- [ ] Test suite passes (pass rate >= baseline)
- [ ] Build succeeds
- [ ] 20 random files spot-checked manually
- [ ] All `CODEMOD_ERROR:` markers triaged and resolved or tracked
- [ ] Linter clean on output

### Post-Migration Hardening

- [ ] Stricter compiler options enabled (incrementally)
- [ ] Lint rules added to prevent regression
- [ ] Compatibility shims removed
- [ ] Codemod archived in repository
- [ ] Documentation updated
- [ ] Onboarding guide updated for new patterns
