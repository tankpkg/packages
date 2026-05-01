# Correctness and State

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Dahan on shared state; Winder on message passing; Allison on floating point; Tank security-review and clean-code skills

Covers: state, concurrency, floating-point traps, error classification, failure visibility, and prevention.

## Correctness Standard

Correctness means the system preserves intended behavior across normal, edge, and failure paths. It is not enough for the happy path to pass once.

Trust executable evidence. If the code, tests, logs, and runtime behavior disagree with an explanation, believe the system and revise the explanation.

## Shared State

Shared mutable state is a common source of race conditions, stale reads, hidden coupling, and hard-to-reproduce bugs.

Prefer ownership, immutability, message passing, or transactions when multiple actors need the same data.

| State Smell | Safer Move |
| ----------- | ---------- |
| Global mutable cache | Scoped cache with invalidation and tests |
| Multiple writers | Single owner or transactional boundary |
| Boolean state combinations | Explicit enum or state machine |
| Caller mutates returned object | Return immutable copy or command method |
| Background job changes hidden state | Emit event and record transition |

## Thinking in States

Model lifecycle explicitly when behavior changes over time. Orders, payments, jobs, sessions, and deployments usually have states, transitions, and forbidden moves.

Represent state transitions in one place when possible. Spread-out transition logic creates contradictions.

Test forbidden transitions, not only valid ones.

## Floating Point

Do not use binary floating point for money, counts, identity, or exact decimal rules.

Use integer minor units, decimal libraries, rational representations, or domain-specific value types depending on the domain.

Make rounding rules explicit and test boundary values.

## Error Handling

Distinguish business exceptions from technical failures.

Business exceptions are expected domain outcomes: card declined, item out of stock, user lacks permission.

Technical failures are infrastructure or programming problems: timeout, database unavailable, malformed response, invariant violation.

| Failure | Handling Pattern |
| ------- | ---------------- |
| Expected domain denial | Return typed business result |
| Retryable infrastructure failure | Retry with backoff or surface temporary failure |
| Programmer invariant violation | Fail fast with diagnostic context |
| User input invalid | Return actionable validation error |
| External provider unknown response | Preserve raw diagnostic safely and map to known failure |

Do not swallow errors. If failure is intentionally ignored, document why and preserve enough observability to debug later.

## Make Invisible Things Visible

Expose state that affects behavior: feature flags, retries, queues, migrations, caches, background jobs, and partial failures.

Visibility can be a log line, metric, trace, status endpoint, dashboard, audit record, or test assertion.

Do not add verbose logging everywhere. Add logs where they answer operational questions.

## Prevention

Prevent errors by constraining inputs, states, types, and boundaries.

Check external data at boundaries, then trust parsed internal data.

Use types to distinguish identifiers and domain values that should not mix.

Prefer impossible states over runtime checks when the language supports it.

## Routing

Use `@tank/security-review` when failures could expose data, privileges, or system integrity.

Use `@tank/clean-code` when state confusion is caused by poor module boundaries or unclear responsibilities.

## State and Failure Catalog

| Signal | Recommended Move | Why |
| ------ | ---------------- | --- |
| Shared mutable cache | Scoped owner or immutable snapshot | Avoids races |
| Money as float | Minor units or decimal | Avoids rounding defects |
| Swallowed exception | Typed failure/log context | Avoids false success |
| Boolean lifecycle | Explicit state enum | Avoids impossible combinations |
| Multiple writers | Transaction or single owner | Preserves invariants |
| Unbounded retry | Bounded backoff | Prevents storms |
| Hidden background job | Visible status/metrics | Supports operations |
| Unknown provider response | Safe diagnostic mapping | Prevents data loss |
| Mutable returned object | Copy or command method | Protects ownership |
| Cache without TTL | Invalidation policy | Prevents stale behavior |

## State Modeling Examples

### Payment Lifecycle

A payment should not be modeled as independent booleans such as `isAuthorized`, `isCaptured`, and `isRefunded`. Use explicit states and transitions so impossible combinations cannot occur silently.

### Shared Cache

A global mutable cache used by parallel requests needs ownership, invalidation, and isolation rules. Without those, tests passing serially do not prove production correctness.

### Business and Technical Failures

A declined card and a provider timeout are both failures, but they require different user messages, retry behavior, metrics, and alerts. Model them separately.

### Exact Values

Money, inventory counts, and externally visible identifiers deserve exact representation and boundary tests. Convenient primitives are not enough when the domain has precision rules.

## Correctness Review Cases

| Case | Professional Move |
| ---- | ----------------- |
| Global mutable cache | Define owner, TTL, invalidation, and isolation tests. |
| Payment booleans | Replace impossible combinations with explicit lifecycle states. |
| Provider timeout | Return retryable technical failure, not empty success. |
| Declined card | Return business denial, not infrastructure error. |
| Money arithmetic | Use integer minor units or decimal type. |
| Background job | Expose queued, running, failed, and completed states. |
| Retry loop | Bound attempts and log correlation context. |
| Mutable return object | Return immutable snapshot or command API. |
| Cache stale read | Test freshness rules and invalidation path. |
| Unknown external payload | Validate boundary and preserve safe diagnostics. |

