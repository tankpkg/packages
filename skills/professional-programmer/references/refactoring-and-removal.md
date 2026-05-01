# Refactoring and Removal

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Fowler (Refactoring); Martin's Boy Scout Rule; Tank clean-code, ast-linter-codemod, and js-tools skills

Covers: safe refactoring, characterization tests, incremental cleanup, code removal, and technical debt handling.

## Refactoring Standard

Refactoring changes structure without changing externally required behavior. If behavior changes, call it a feature or bug fix and test it as such.

Before refactoring, know what behavior must stay the same. If tests are missing, add characterization tests around the risky seams.

## Before You Refactor

| Check | Why |
| ----- | --- |
| Is the goal named? | Prevents wandering rewrites |
| Is behavior covered? | Catches accidental changes |
| Is the change small? | Keeps reviewable diffs |
| Can it be reverted? | Reduces risk |
| Is it mixed with a feature? | Separates behavior from structure |

## Safe Workflow

1. Read the surrounding code and tests.
2. Identify the smallest structural improvement.
3. Add a characterization test when behavior is important and untested.
4. Make one transformation.
5. Run tests.
6. Repeat only if the next step is still clearly valuable.

## Boy Scout Rule

Leave code better than you found it, but keep the improvement proportional to the task.

Good Boy Scout changes include renaming a misleading local variable, removing dead code, tightening a guard clause, or adding a missing regression test.

Bad Boy Scout changes include broad rewrites, unrelated formatting churn, and new architecture under the cover of a small bug fix.

## Removal Beats Addition

Deleted code has no bugs, no maintenance cost, and no onboarding burden.

Before adding a new branch, helper, abstraction, or package, ask whether the old path can be removed.

| Removal Candidate | Evidence Needed |
| ----------------- | --------------- |
| Dead feature flag | Flag permanently on/off and no rollout need |
| Unused public API | No internal references and no external contract |
| Duplicate helper | Same concept and same constraints |
| Legacy compatibility | Supported versions no longer require it |
| Speculative option | No current requirement or user |

## Technical Debt

Debt is acceptable when deliberate, visible, and scheduled for repayment. Hidden debt is just decay.

Record:

- what shortcut was taken
- why it was taken
- what risk it creates
- how to detect pain
- when to revisit

## Do Not Touch That Code

Some code is dangerous because it is poorly understood, untested, or externally depended upon. Touch it only after building safety rails.

Use characterization tests, logs, feature flags, or staged rollout before changing it.

## Routing

Use `@tank/clean-code` for detailed refactoring recipes.

Use `@tank/ast-linter-codemod` for repeated mechanical transformations.

Use `js-tools` for TypeScript structural operations such as move, rename, split, and import organization.

## Refactoring Decision Catalog

| Signal | Recommended Move | Why |
| ------ | ---------------- | --- |
| Unsafe legacy code | Characterize first | Preserves behavior |
| Dead flag | Remove after rollout proof | Reduces complexity |
| Pass-through layer | Collapse | Improves traceability |
| Misleading name | Rename | Improves reading |
| Mixed behavior/refactor | Split commits | Improves review |
| Repeated edit | Codemod | Reduces manual errors |
| Untested public API | Compatibility review | Avoids breaking users |
| Large function | Extract concepts | Clarifies intent |
| Duplicate concept | Unify carefully | Reduces drift |
| Duplicate shape only | Keep separate | Avoids bad coupling |

## Refactoring Examples

### Characterize Before Cleanup

A legacy tax function should not be cleaned because it looks ugly. First capture current outputs for representative jurisdictions and boundary values. Then change structure while preserving those outputs.

### Remove After Rollout

A feature flag is removable only when rollout state, fallback requirements, and references are known. Remove the flag path, tests, docs, and config together so the old behavior cannot reappear.

### Collapse Pass-Through Layers

A wrapper that only forwards arguments adds reading cost without ownership. Collapse it unless it defines a stable boundary, policy, instrumentation point, or compatibility seam.

### Keep Duplicates Temporarily

Two similar blocks should remain separate when their domain meanings differ or when requirements are still moving. Premature unification creates shared bugs and awkward conditionals.

## Refactoring Case Patterns

| Case | Professional Move |
| ---- | ----------------- |
| Tax calculation cleanup | Capture representative outputs before reorganizing. |
| Dead feature flag | Remove code, config, docs, and tests after rollout proof. |
| Misleading name | Rename first when comprehension blocks safe change. |
| Bulk API migration | Use codemod and sample review instead of hand edits. |
| Public API deletion | Provide migration path or version boundary. |
| Mixed feature cleanup | Split behavior and refactor commits. |
| Pass-through wrapper | Collapse unless it owns compatibility or instrumentation. |
| Duplicate shape | Keep separate when concepts change independently. |
| Temporary debt | Record reason and repayment trigger. |
| Stopping point | Stop when next change lacks clear value. |

