# Platform Primitives

Sources: Cloudflare Workers official documentation, KV documentation, D1 documentation, R2 documentation, Durable Objects documentation, Queues documentation, Vectorize documentation, Workers AI documentation

Covers: KV, D1, R2, Durable Objects, Queues, Vectorize, Workers AI, and how to choose the right Cloudflare platform primitive for a given edge workload.

## Pick the Right Primitive, Not Just the Most Interesting One

Cloudflare gives you many stateful and semi-stateful building blocks. The main design challenge is choosing the simplest primitive that matches the consistency and workload shape you actually need.

| Primitive | Best for |
|----------|----------|
| KV | global read-heavy key/value data |
| D1 | relational data and SQL queries |
| R2 | blob/object storage |
| Durable Objects | per-key coordination and strong consistency |
| Queues | asynchronous background processing |
| Vectorize | vector search use cases |
| Workers AI | model inference at the edge |

## KV

KV is a globally distributed key/value store optimized for reads.

### Good KV use cases

| Use case | Why |
|---------|-----|
| config flags and small lookup data | replicated and cheap to read |
| caching rendered fragments or API results | simple global reads |
| session-like non-critical edge data | eventual consistency is acceptable |

### KV cautions

| Concern | Why |
|--------|-----|
| eventual consistency | writes are not instantly visible everywhere |
| large/relational queries | wrong tool |
| coordination logic | use Durable Objects instead |

## D1

D1 is Cloudflare’s SQLite-based relational database offering.

| Good fit | Example |
|---------|---------|
| CRUD apps with relational queries | posts, users, comments |
| internal tools and app metadata | admin panels |
| moderate structured workloads | SQL-friendly apps |

### D1 cautions

| Concern | Note |
|--------|------|
| edge SQL is not magic | model query patterns carefully |
| write-heavy coordination | Durable Objects may still be needed |
| migration discipline | schema changes still need process |

## R2

R2 is object storage for files and blobs.

| Good fit | Example |
|---------|---------|
| user uploads | images, docs, media |
| generated artifacts | exports, reports, cached bundles |
| static binary assets | large non-relational files |

R2 is not a database. Pair it with metadata in D1/KV when object discovery matters.

## Durable Objects

Durable Objects are the coordination primitive.

| Use case | Why DOs fit |
|---------|-------------|
| chat rooms | single logical owner for room state |
| collaborative sessions | strong ordering and coordination |
| locks/rate counters | serialized state mutations |

Use Durable Objects when you need one place that “owns” a piece of mutable state.

## Queues

Queues decouple slow or retryable work from the request path.

| Good fit | Example |
|---------|---------|
| image processing | post-upload transforms |
| email/webhook fanout | background side effects |
| indexing pipelines | move heavy work off request path |

Queues are for eventual completion, not synchronous correctness.

## Vectorize

Vectorize is for vector search and retrieval workloads.

| Good fit | Example |
|---------|---------|
| semantic search | docs/product search |
| lightweight RAG retrieval | AI-backed apps |
| similarity lookup | recommendation / clustering |

Use it only when you genuinely need vector retrieval, not as a default storage layer.

## Workers AI

Workers AI exposes model inference from the Workers platform.

| Good fit | Example |
|---------|---------|
| text generation or classification near user edge | low-latency AI features |
| image/audio model invocation | AI product paths |
| AI gateway/orchestration with Worker logic | integrated edge pipelines |

Measure cost, latency, and model fit before coupling product flows tightly to inference calls.

## Primitive Selection Matrix

| Need | Primitive |
|------|-----------|
| global eventually-consistent reads | KV |
| SQL tables and joins | D1 |
| file storage | R2 |
| synchronized per-entity state | Durable Objects |
| async background jobs | Queues |
| vector similarity | Vectorize |
| model inference | Workers AI |

## Composition Patterns

| Pattern | Example |
|--------|---------|
| D1 + R2 | metadata in D1, blobs in R2 |
| Durable Objects + KV | coordinated write path, replicated read cache |
| Worker + Queue + R2 | upload request, queue processing, object storage |
| Worker + Vectorize + Workers AI | retrieval + inference pipeline |

## Common Primitive Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| using KV for strong-consistency workflows | stale reads / coordination bugs | use DOs or D1 |
| storing relational metadata in R2 only | poor queryability | pair with D1 |
| doing heavy background work inline in fetch | latency spikes | queue it |
| using Durable Objects for static lookup data | unnecessary coordination overhead | use KV |

## Primitive Cost and Complexity Heuristics

| Primitive | Complexity profile |
|----------|--------------------|
| KV | low conceptual load, eventual-consistency caveat |
| D1 | familiar SQL model, schema discipline required |
| R2 | simple storage, metadata still needed elsewhere |
| Durable Objects | highest coordination power, most architecture responsibility |
| Queues | operationally simple, requires eventual-work mindset |

Choose the primitive whose complexity you are actually prepared to operate.

## Data Lifecycle Patterns

| Lifecycle | Pattern |
|----------|---------|
| upload file + metadata | R2 + D1 |
| request cache + invalidation | KV + explicit busting path |
| collaborative room/session | Durable Object |
| ingest then process later | Queue + storage target |

Design the full lifecycle, not just the first write target.

## Durable Object Design Questions

1. What is the key that defines ownership?
2. How much state lives in memory vs persisted storage?
3. What happens when demand spikes on a single object key?
4. Can stale reads or eventual consistency be acceptable instead?

If you cannot answer these cleanly, you may not need a Durable Object yet.

## D1 Operational Notes

| Concern | Recommendation |
|--------|----------------|
| schema migrations | track and review like any SQL system |
| query tuning | keep statements intentional |
| write-heavy coordination | don’t pretend D1 is a lock manager |

Use D1 as a relational store, not a universal coordination primitive.

## KV Operational Notes

| Concern | Recommendation |
|--------|----------------|
| cache invalidation | define it explicitly |
| stale reads | assume them in architecture |
| large object use | prefer R2 |

KV succeeds when stale reads are acceptable and reads dominate writes.

## R2 Design Notes

| Concern | Recommendation |
|--------|----------------|
| object naming | choose deterministic, queryable key schemes |
| metadata lookup | keep searchable metadata in D1/KV |
| public asset serving | pair with cache strategy and access rules |

R2 is excellent for bytes, but weak for discovery by itself.

## Queue Design Notes

| Concern | Recommendation |
|--------|----------------|
| retry semantics | make consumers idempotent |
| poison messages | define dead-letter or failure handling policy |
| fanout pipelines | keep messages small and explicit |

Queues are easiest to operate when jobs are replay-safe.

## Workers AI and Vectorize Pairing

| Pattern | Use |
|--------|-----|
| Vectorize only | semantic retrieval |
| Workers AI only | direct inference/classification |
| Vectorize + Workers AI | retrieval + answer generation |

Do not combine them unless product behavior truly requires both retrieval and inference.

## Primitive Migration Paths

Sometimes the first primitive choice changes as traffic or correctness needs evolve.

| From | To | Why |
|-----|----|-----|
| KV | Durable Objects | stronger coordination needed |
| KV | D1 | relational querying emerges |
| inline fetch work | Queue | async backlog grows |
| D1 metadata only | D1 + R2 | binary objects become primary artifact |

Thinking about migration paths early reduces platform rewrites later.

## Anti-Patterns by Primitive

| Primitive | Anti-pattern |
|----------|--------------|
| KV | pretending writes are strongly consistent globally |
| D1 | putting every coordination problem into SQL |
| R2 | using object keys as if they were a query engine |
| Durable Objects | centralizing too many unrelated entities in one object |
| Queues | relying on queue completion for immediate request correctness |

## Operational Review Questions

1. What are the read/write characteristics of this workload?
2. Does it need strong consistency, eventual consistency, or explicit serialization?
3. Will the dominant data shape be records, objects, or events?
4. Can this work happen asynchronously?

These four questions usually narrow the primitive choice quickly.

## Release Readiness Checklist

- [ ] Each data/workload need is mapped to the correct primitive
- [ ] Consistency assumptions are explicit
- [ ] Object data and metadata are separated appropriately
- [ ] Background work leaves the request path when possible
- [ ] AI/vector features are justified by actual product needs
