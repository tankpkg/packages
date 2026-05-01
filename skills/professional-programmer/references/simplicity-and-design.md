# Simplicity and Design

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Martin (Clean Code); Fowler (Refactoring); Ousterhout (A Philosophy of Software Design); Tank clean-code and ast-linter-codemod skills

Covers: simple design, code as design, responsibility boundaries, domain language, APIs, behavior encapsulation, and reduction.

## Design Standard

Code is design. It is not the mechanical output of a design document; it is the artifact future maintainers must understand and modify.

Prefer designs where the main path is obvious, invalid states are constrained, and supporting details are named at the right level.

Simplicity is not shortness. Simple code has fewer concepts in play at once, fewer hidden dependencies, and fewer reasons to change.

## Reduction Before Addition

Before adding code, ask what can be removed:

| Addition Temptation | Reduction Move |
| ------------------- | -------------- |
| Add a config option | Remove the need for variation |
| Add a wrapper | Use the existing boundary directly |
| Add a helper | Inline until repetition is conceptual |
| Add a dependency | Use platform capability if enough |
| Add a branch | Split the workflow or encode state |

## Responsibility Boundaries

A module should have a stable reason to exist. If its description needs "and", split or rename it.

Prefer behavior encapsulation over state bags. A class or module that only exposes data pushes business rules into callers.

Keep policy away from plumbing when possible. Business decisions should not be hidden inside HTTP, database, or UI adapter code.

## Domain Language

Use names from the domain. If users say "invoice", "authorization", or "shipment", avoid generic names like `record`, `item`, or `processData`.

Prefer domain-specific types for values with rules. Money, percentages, identifiers, durations, and states deserve explicit representation when misuse is plausible.

Avoid primitive obsession when primitive values carry business meaning.

## API Design

Make interfaces easy to use correctly and hard to use incorrectly.

| API Smell | Better Design |
| --------- | ------------- |
| Boolean flag controls behavior | Split into named functions |
| Caller must pass fields in same order | Use an object or named type |
| Null means several things | Use explicit result states |
| Throws undocumented exceptions | Return typed errors or document failure |
| Requires setup order knowledge | Provide a constructor/factory that enforces invariants |

## Comments and Layout

Use layout to reveal structure. Group related ideas, separate levels of abstraction, and keep guard clauses visible.

Comment what code cannot express: historical context, external constraints, surprising tradeoffs, or non-obvious algorithms.

Do not comment around unclear names. Rename or extract first.

## Polymorphism and Patterns

Use polymorphism when behavior varies by type and the variation is stable. Do not introduce class hierarchies just to avoid a small conditional.

Avoid singleton as a default. If a process-wide object is necessary, keep lifecycle, reset behavior, and dependency injection explicit.

## Design Review Checklist

1. Can a maintainer describe the module in one sentence?
2. Are domain terms visible in names and types?
3. Are invalid states constrained?
4. Are dependencies pointed toward stable policy rather than volatile detail?
5. Is abstraction reducing cognitive load rather than hiding simple code?
6. Is there a test proving the main behavior?

## Routing

Use `@tank/clean-code` for detailed function, naming, modularity, and smell guidance.

Use `@tank/ast-linter-codemod` for repeated structural changes or custom lint enforcement.

Use `js-tools` for TypeScript moves, renames, import organization, and file splitting.

## Design Decision Catalog

| Signal | Recommended Move | Why |
| ------ | ---------------- | --- |
| Boolean flag | Split named operations | Flag changes behavior invisibly |
| Primitive domain value | Introduce value type | Prevents invalid mixing |
| One implementation interface | Inline or keep concrete | Avoids ceremony |
| Long function | Extract named concept | Improves reading |
| Generic payload | Rename to domain term | Makes rules visible |
| Magic helper | Expose contract | Protects critical behavior |
| State bag object | Move behavior to owner | Reduces caller burden |
| Deep nesting | Use guard clauses | Reveals main path |
| Speculative option | Remove/defer | Reduces state space |
| Public API growth | Narrow interface | Lowers support cost |

## Design Examples

### Boolean Flags

A function with a boolean flag often contains two operations hiding under one name. Split it into named operations when callers must understand which mode they are choosing.

### Domain Types

Passing raw strings for user IDs, order IDs, and invoice IDs makes accidental mixing easy. Domain-specific types or value objects move mistakes closer to compile time or validation time.

### One-Implementation Interface

An interface with one implementation is useful only when it protects a boundary or enables tests without lying. Otherwise it is ceremony and should stay concrete.

### Magic Helper

A helper named `process` or `doMagic` around critical behavior hides the design. Rename it around the domain transformation and add tests that describe the contract.

## Design Review Cases

| Case | Professional Move |
| ---- | ----------------- |
| Boolean flag in API | Split into named operations so call sites reveal intent. |
| One implementation interface | Keep concrete unless it protects a boundary. |
| Raw domain primitives | Introduce values for money, identifiers, and states. |
| Pass-through layer | Delete it when it adds no policy or compatibility. |
| Magic helper name | Rename around the transformation contract. |
| Deep nesting | Use guard clauses to expose the main path. |
| Leaky adapter | Keep transport details outside business policy. |
| Premature pattern | Start from pain, not pattern vocabulary. |
| State bag | Move behavior to the owner of the state. |
| Public optional sprawl | Use a request object or smaller operations. |

