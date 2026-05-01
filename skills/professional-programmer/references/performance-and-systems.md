# Performance and Systems

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Spinellis on databases and tools; Stafford on IPC; Pepperdine on performance; Tank relational-db-mastery and clean-code skills

Covers: performance judgment, algorithms, data structures, databases, IPC, logging, profiling, and estimation.

## Performance Standard

Performance work starts with a user-visible goal and measurement. Optimizing code without evidence often makes systems harder to change while missing the real bottleneck.

Keep code clean enough to optimize. Dirty code hides performance bombs because the data flow and ownership are unclear.

## Algorithm and Data Structure Choice

Use the right algorithm and data structure before micro-optimizing syntax.

| Symptom | First Check |
| ------- | ----------- |
| Slow lookup in loop | Replace scan with map/set if identity is stable |
| Growing memory | Ownership, retention, cache eviction |
| Slow sort/filter | Input size, indexes, streaming, pagination |
| Timeout under load | Contention, shared state, I/O, N+1 calls |
| High CPU | Algorithmic complexity before micro-ops |

## Databases

Large interconnected data belongs in a database when relationships, queries, consistency, concurrency, and durability matter.

Do not reimplement a database with in-memory structures, JSON blobs, or ad hoc files unless the data is small, local, and disposable.

Use indexes intentionally. Every index helps some reads and costs writes, storage, and planning complexity.

## IPC and Distributed Boundaries

Inter-process communication affects response time. Network calls, serialization, queues, retries, and fan-out can dominate local computation.

Make remote boundaries visible in code names and tests. A function that looks local but performs I/O misleads maintainers.

Batch, cache, or colocate only after measuring and checking correctness risk.

## Logging

Verbose logging can disturb sleep by hiding the one useful line in a flood of noise.

Log business milestones, failure context, state transitions, and correlation IDs. Avoid secrets, high-cardinality noise, and repeated success spam.

Prefer structured logs when machines must search them.

## Profiling Workflow

1. Define the user-visible performance problem.
2. Measure baseline latency, throughput, memory, or cost.
3. Identify the dominant bottleneck.
4. Change the smallest thing that addresses that bottleneck.
5. Measure again.
6. Preserve readability unless the measurement proves a tradeoff is worth it.

## Estimation

Estimate with ranges and uncertainty. A professional estimate names assumptions and risk factors.

Break work into independently verifiable slices. Large estimates hide unknowns.

When pressure mounts, reduce scope before reducing quality gates for correctness or security.

## Routing

Use `@tank/relational-db-mastery` for schema, indexing, query plans, N+1 problems, and database tuning.

Use `@tank/clean-code` when performance problems are entangled with unclear structure.

Use `@tank/security-review` when optimization changes cache, auth, data exposure, or isolation.

## Systems Decision Catalog

| Signal | Recommended Move | Why |
| ------ | ---------------- | --- |
| Slow lookup | Map/set/index | Improves complexity |
| N+1 calls | Batch/eager load | Reduces I/O |
| Large related data | Database | Preserves query semantics |
| Remote fan-out | Batch/cache/queue | Controls latency |
| Hot loop allocation | Hoist/reuse after profiling | Reduces pressure |
| Noisy logs | Structured selective logs | Improves diagnosis |
| Stale cache | TTL/invalidation | Preserves correctness |
| Slow build | Profile pipeline | Improves feedback |
| Unclear estimate | Range plus assumptions | Communicates uncertainty |
| Dirty optimization | Refactor then measure | Keeps maintainability |

## Measurement Examples

### N Plus One Calls

A loop that calls an API or database per item should be measured by call count and latency distribution, not by local CPU time. The fix may be batching, eager loading, pagination, or moving the boundary.

### Cache Introduction

A cache is not only a speed feature. It creates freshness, ownership, invalidation, memory, and security questions. Add a cache only after naming the data lifetime and the consequence of stale reads.

### Database Boundary

Nested JSON files can be acceptable for small local state, but interconnected durable customer, order, and refund data needs query semantics, constraints, migrations, and concurrency control.

### Logging Cost

Verbose logs can increase storage cost and hide incidents. Keep logs that answer operational questions: what changed, who/what initiated it, whether it succeeded, and what safe identifier links related events.

## Systems Case Patterns

| Case | Professional Move |
| ---- | ----------------- |
| Nested scan | Use map/set/index when identity lookup dominates. |
| N plus one | Batch or eager load at the right boundary. |
| JSON persistence | Move interconnected durable data to database. |
| Remote fan-out | Measure call count and latency before caching. |
| Cache proposal | Define TTL, invalidation, ownership, and privacy impact. |
| Noisy logs | Keep transition and failure signals, not every success loop. |
| Memory growth | Trace ownership and retention before pooling. |
| Estimate pressure | Return range with assumptions and unknowns. |
| Dirty hot path | Refactor for clarity before targeted optimization. |
| Cost spike | Treat cloud spend as a performance metric. |

