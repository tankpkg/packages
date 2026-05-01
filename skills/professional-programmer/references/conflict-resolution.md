# Conflict Resolution

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Martin (Clean Code); Fowler (Refactoring); Ousterhout (A Philosophy of Software Design); Tank clean-code, bdd-e2e-testing, and security-review skills

Covers: tiebreakers for professional programming principles when two good ideas point in different directions.

## Decision Order

Apply this priority order before choosing a tactic:

1. Preserve correctness, safety, and data integrity.
2. Preserve security and privacy boundaries.
3. Preserve maintainability and understandable change.
4. Preserve delivery speed only inside the above constraints.
5. Improve performance when measurement shows it matters.
6. Improve elegance only when it reduces total complexity.

## Core Tiebreakers

| Conflict | Default Winner | Reason | Verification |
| -------- | -------------- | ------ | ------------ |
| Correctness vs speed | Correctness | Fast wrong code creates hidden downstream work | Failing test reproduced, passing test added |
| Security vs convenience | Security | Convenience cannot justify exposing users or secrets | Threat path reviewed, unsafe shortcut removed |
| Simplicity vs extensibility | Simplicity | Most predicted variation never arrives | Current requirements covered without speculative hooks |
| Readability vs performance | Readability | Optimized unreadable code rots unless bottleneck is proven | Profile before changing structure |
| DRY vs clarity | Clarity | Shared abstractions can couple unrelated reasons to change | Duplication has same concept, not just same shape |
| Comments vs self-documenting code | Self-documenting code | Comments drift; executable names and structure are checked constantly | Comment explains why, not what |
| Tests vs deadline | Critical tests | Untested risky behavior makes the schedule fictional | Minimal behavior or characterization tests pass |
| Abstraction vs duplication | Duplication first | Early abstraction freezes ignorance | Abstract after repeated concept and stable boundary |
| Singleton/global state vs infrastructure boundary | Boundary-specific state | Uncontrolled globals harm tests and concurrency | Lifecycle, reset behavior, and ownership are explicit |
| User request vs user need | User need | Users often describe solutions rather than outcomes | Clarifying question or domain example confirms intent |

## How to Apply

Name the conflict explicitly. Do not say "best practice" when two values are trading off.

Pick the smallest reversible step when evidence is incomplete. If the decision is hard to reverse, gather more evidence first.

Write down what would change your mind. For example: "If profiling shows this loop accounts for more than 10% of request latency, revisit the readable implementation."

## Common Misapplications

| Smell | Better Move |
| ----- | ----------- |
| Adding an interface because a second implementation might appear | Keep concrete code until the second implementation exists |
| Removing duplication that names different domain concepts | Keep duplication and improve names |
| Writing comments to justify confusing code | Refactor names and structure first |
| Skipping tests because the patch is small | Add the smallest test that proves the behavior or guards the risk |
| Optimizing before measuring | Add instrumentation or a benchmark first |
| Accepting swallowed errors to avoid user-facing failures | Return typed failure, retry, or log with actionable context |

## Agent Output Pattern

When reviewing or coding, use this structure:

1. Principle conflict: name both sides.
2. Winner: state the chosen priority.
3. Evidence: point to code, tests, requirements, or runtime behavior.
4. Action: describe the smallest change.
5. Verification: list the test, command, or observation that proves it.

## Delegation

Use `@tank/clean-code` when the conflict is mostly about structure, naming, function design, or modularity.

Use `@tank/security-review` when the conflict crosses auth, input validation, secrets, injection, SSRF, data exposure, or privilege boundaries.

Use `@tank/bdd-e2e-testing` when the conflict is about what behavior to prove and how to prove it against real systems.

Use `@tank/relational-db-mastery` when the conflict involves database shape, query plans, indexes, or persistence boundaries.

Use `@tank/ast-linter-codemod` or `js-tools` when the chosen action requires a safe structural code transformation.

## Expanded Tradeoff Matrix

| Pressure | Default | Exception | Evidence Needed |
| -------- | ------- | --------- | --------------- |
| Correctness vs speed | Correctness | Disposable prototype | Explicit scope |
| Security vs convenience | Security | None for production | Security review |
| Simplicity vs extensibility | Simplicity | Second implementation exists | Concrete variation |
| Readability vs performance | Readability | Measured bottleneck | Profiler |
| DRY vs clarity | Clarity | Same domain concept | Shared invariant |
| Tests vs deadline | Risk tests | Throwaway spike | No production claim |
| Global state vs context | Context | Immutable config | Lifecycle documented |
| Automation vs manual | Automation | One-off task | Frequency estimate |
| Customer request vs need | Need | Exact regulated requirement | Acceptance criteria |
| Compatibility vs cleanup | Compatibility | Breaking version | Migration path |

## Bad Tiebreakers

| Phrase | Problem | Replacement |
| ------ | ------- | ----------- |
| Best practice says | No context | Given this risk |
| Might need later | Speculation | Defer |
| Cleaner to me | Taste | Reduces concepts because |
| Faster probably | No measurement | Measure first |
| No time | Avoids risk | Keep safety gate |
| Everyone knows | Hidden assumption | Encode it |

## Decision Record Examples

### Security Shortcut

A staging-only authorization bypass is proposed because manual testing is slow. Security wins because the flag can drift into production and the failure mode is privilege escalation. The smaller safe action is to create a test-only fixture or seeded account that exercises the real authorization path.

### DRY Pressure

Two pieces of code look the same but represent invoice approval and shipment release. Clarity wins until the business rules change together. The safer move is to improve names and keep the flows separate.

### Performance Claim

A readable loop is replaced with clever indexing before any latency target is missed. Readability wins until profiling identifies the loop as material. The reversible action is to keep readable code and add a benchmark if performance matters.

### Deadline Pressure

A payment failure path has no test and a release is due today. Correctness wins for the failure path; scope should shrink before the team ships false success for money movement.

## Tradeoff Examples

| Case | Professional Move |
| ---- | ----------------- |
| Speed vs correctness | Release less functionality rather than unverified money movement. |
| Security vs convenience | Use seeded test users instead of bypass flags. |
| DRY vs clarity | Do not merge invoice and shipment flows just because shapes match. |
| Performance vs readability | Keep readable code until profiling names the hot path. |
| Compatibility vs cleanup | Use expand/contract migration when old clients exist. |
| Global state vs context | Pass scoped request context instead of mutable singleton data. |
| Automation vs one-off | Script repeated releases; do not automate one accidental task. |
| Comments vs naming | Rename unclear operations before adding explanatory comments. |
| Extensibility vs current need | Wait for real variation before adding plugin architecture. |
| Customer request vs outcome | Build the workflow outcome, not blindly the requested widget. |

