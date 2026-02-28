---
name: "@tank/system-design"
description: |
  Practical system design for production distributed systems. Covers
  scalability patterns (load balancing, horizontal scaling, CDN, auto-scaling),
  data layer design (database selection, replication, sharding, consistency
  models, CAP theorem applied), caching strategies (cache-aside, write-through,
  invalidation, stampede prevention), messaging and async patterns (queues vs
  streams, event-driven architecture, CQRS, saga pattern, delivery guarantees),
  reliability (circuit breakers, bulkheads, retries, rate limiting, timeouts,
  chaos engineering), service architecture (monolith vs microservices, API
  gateway, service mesh, distributed transactions), and capacity planning
  (back-of-envelope estimation, SLOs/SLIs, monitoring, distributed tracing).

  Synthesizes Kleppmann (Designing Data-Intensive Applications), Vitillo
  (Understanding Distributed Systems), Newman (Building Microservices),
  Ford et al. (Software Architecture: The Hard Parts), Nygard (Release It!),
  Petrov (Database Internals), Richards & Ford (Fundamentals of Software
  Architecture), and Beyer et al. (Site Reliability Engineering).

  Trigger phrases: "system design", "distributed systems", "scalability",
  "load balancing", "horizontal scaling", "vertical scaling", "database
  sharding", "database replication", "caching strategy", "cache invalidation",
  "message queue", "event-driven", "Kafka", "RabbitMQ", "pub/sub",
  "circuit breaker", "rate limiting", "bulkhead", "retry strategy",
  "microservices", "monolith", "API gateway", "service mesh",
  "CAP theorem", "eventual consistency", "strong consistency",
  "CQRS", "event sourcing", "saga pattern", "back-of-envelope",
  "SLO", "SLI", "capacity planning", "distributed tracing",
  "back pressure", "cache stampede", "thundering herd",
  "how should I scale", "which database", "when to use microservices"
---

# Practical System Design

## Core Philosophy

1. **Every decision is a trade-off.** There are no best solutions, only context-appropriate ones. Articulate what you gain AND what you give up.
2. **Measure before designing.** Base architectural decisions on observed load, latency, and failure data — not hypothetical future scale.
3. **Start with a monolith, earn microservices.** Premature distribution adds complexity without proven benefit. Decompose when evidence demands it.
4. **Design for failure, not just success.** Every network call can fail, every dependency can slow down. The question is how your system behaves when things go wrong.
5. **Understand your data.** Read/write ratio, access patterns, consistency requirements, and growth rate drive most architectural choices.

## Quick-Start: Common Problems

### "How should I scale this?"

1. Identify the bottleneck → Is it CPU, memory, I/O, network, or a downstream dependency?
2. Can you scale vertically (bigger machine)? → Cheaper and simpler if it works
3. Is the bottleneck stateless? → Horizontal scaling behind a load balancer
4. Is the bottleneck the database? → Read replicas for read-heavy, sharding for write-heavy
5. Is there a hot path? → Cache it (see caching decision below)
→ See `references/scalability-patterns.md`

### "Which database should I use?"

1. What are the access patterns? → Key-value lookups, complex queries, graph traversals, time-series?
2. What consistency do you need? → Strong (financial), eventual (social feed), causal (collaboration)?
3. What's the read/write ratio? → Read-heavy favors replicas + cache, write-heavy favors LSM-based stores
4. Will you need joins across entities? → Relational. If not, document or key-value may fit.
→ See `references/data-layer.md` for the full selection matrix

### "Should I use microservices?"

1. Can separate teams deploy independently? → Key signal for decomposition
2. Do components need different scaling profiles? → Another strong signal
3. Is the domain well-understood? → If not, monolith first — wrong boundaries are expensive to fix
4. Team smaller than ~50 engineers? → Modular monolith likely sufficient
→ See `references/service-architecture.md`

### "My system keeps failing under load"

1. Are there missing timeouts? → Add timeouts to every external call
2. Is one failing dependency taking everything down? → Circuit breakers + bulkheads
3. Are retries amplifying the problem? → Add jitter, set retry budgets
4. Is the queue unbounded? → Add back-pressure, set queue depth limits
→ See `references/reliability-patterns.md`

## Decision Trees

### Architecture Style Selection

| Team Size | Domain Clarity | Deploy Independence Needed | Recommendation |
|---|---|---|---|
| < 20 engineers | Low | No | Monolith |
| < 20 engineers | High | Partial | Modular monolith |
| 20-50 engineers | High | Yes | Selective microservices |
| 50+ engineers | High | Yes | Microservices |
| Any | Uncertain | Any | Monolith first, decompose later |

### Communication Pattern Selection

| Need | Pattern | Protocol |
|---|---|---|
| Synchronous request-response, low latency | Direct call | REST or gRPC |
| Fire-and-forget, decoupled | Message queue | RabbitMQ, SQS |
| Event broadcast to many consumers | Pub/sub stream | Kafka, SNS |
| Long-running workflow coordination | Orchestrated saga | Temporal, Step Functions |
| High-throughput data pipeline | Event stream | Kafka, Kinesis |

### Caching Strategy Selection

| Scenario | Pattern | Why |
|---|---|---|
| Read-heavy, tolerant of stale data | Cache-aside with TTL | Simple, widely applicable |
| Reads must reflect recent writes | Write-through | Consistency at cost of write latency |
| Write-heavy, reads can lag | Write-behind | Fast writes, async persistence |
| Predictable access patterns | Refresh-ahead | Avoids cache miss latency |
| Never cache | Highly dynamic, user-specific, security-sensitive | Stale data cost > latency cost |

### Database Type Selection

| Access Pattern | Best Fit | Example |
|---|---|---|
| Structured data, complex queries, transactions | Relational (PostgreSQL, MySQL) | E-commerce orders, financial records |
| Flexible schema, document-oriented reads | Document (MongoDB) | Content management, user profiles |
| Simple key-value lookups, extreme throughput | Key-Value (Redis, DynamoDB) | Sessions, feature flags, counters |
| Wide rows, high write throughput | Wide-Column (Cassandra, ScyllaDB) | IoT telemetry, activity logs |
| Highly connected data, traversals | Graph (Neo4j) | Social networks, recommendations |
| Time-ordered data, aggregations | Time-Series (TimescaleDB, InfluxDB) | Metrics, monitoring, analytics |

## Anti-Patterns Quick Reference

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Distributed monolith | Microservices that must deploy together | Enforce data ownership, async communication |
| Premature microservices | Complexity before clarity | Start monolith, decompose with evidence |
| Unbounded queues | OOM under load, cascading backlog | Set queue limits, implement back-pressure |
| Missing timeouts | One slow dependency blocks all threads | Timeout every external call, propagate deadlines |
| Retry storms | Retries amplify load on failing service | Exponential backoff + jitter + retry budgets |
| Cache as source of truth | Data loss when cache evicts | Cache is acceleration, database is truth |
| Shared mutable state | Contention, inconsistency, scaling wall | Externalize state, share-nothing design |
| Over-engineering for scale | Building for 10M users when you have 1K | Measure actual load, scale when needed |

## Reference Files

| File | Contents |
|------|----------|
| `references/scalability-patterns.md` | Scaling dimensions (X/Y/Z axes), load balancing (L4 vs L7, algorithms), auto-scaling strategies, CDN architecture, stateless design, database scaling overview |
| `references/data-layer.md` | Database type selection matrix, replication strategies, partitioning/sharding, consistency models, CAP/PACELC applied, SQL vs NoSQL framework, data modeling for scale |
| `references/caching-strategies.md` | Cache placement, caching patterns (aside/through/behind/ahead), distributed cache architecture, invalidation, eviction policies, failure modes (stampede/penetration/avalanche) |
| `references/messaging-and-async.md` | Sync vs async decision, queue fundamentals, broker selection (Kafka/RabbitMQ/SQS), event-driven architecture, CQRS, saga pattern, back-pressure, delivery guarantees |
| `references/reliability-patterns.md` | Failure modes, circuit breakers, retry strategies, bulkheads, rate limiting, timeouts/deadlines, health checks, failover, chaos engineering |
| `references/service-architecture.md` | Architecture style selection, service decomposition, API gateway, communication patterns (REST/gRPC/GraphQL), service discovery, distributed transactions, service mesh |
| `references/capacity-and-observability.md` | Back-of-envelope estimation, latency reference numbers, SLOs/SLIs/SLAs, bottleneck analysis, monitoring strategy (RED/USE), distributed tracing, alerting design, capacity planning |
