# Messaging and Asynchronous Patterns

Sources: Synthesized from Kleppmann (Designing Data-Intensive Applications), Newman (Building Microservices), Vitillo (Understanding Distributed Systems)

Covers: sync vs async communication, message queue fundamentals, broker selection, event-driven architecture, CQRS, saga pattern, back-pressure, delivery guarantees.

## Synchronous vs Asynchronous Communication

### Decision Framework

| Factor | Favors Synchronous | Favors Asynchronous |
|---|---|---|
| Response needed immediately | Yes — user waiting for result | No — result can arrive later |
| Temporal coupling acceptable | Yes — caller and callee must both be available | No — decouple sender and receiver |
| Failure handling | Caller handles error immediately | Message persists, retry later |
| Latency sensitivity | Low total latency required | Throughput matters more than latency |
| Call chain depth | Shallow (1-2 hops) | Deep chains benefit from decoupling |

### When to Use Each

| Use Synchronous | Use Asynchronous |
|---|---|
| User-facing request that needs immediate response | Background processing (email, notifications, reports) |
| Simple CRUD operations | Long-running workflows |
| Health checks and status queries | Event broadcasting to multiple consumers |
| Authentication and authorization checks | Data pipeline processing |
| Operations where caller needs the result to proceed | Tasks where producer should not wait for consumer |

## Message Queue Fundamentals

### Point-to-Point vs Pub/Sub

| Model | Behavior | Use Case |
|---|---|---|
| Point-to-point (Queue) | One message consumed by exactly one consumer | Work distribution, task processing |
| Publish/Subscribe (Topic) | One message delivered to all subscribers | Event broadcasting, notifications |
| Consumer group | Message delivered to one consumer within each group | Parallel processing with broadcast to different systems |

### Core Concepts

| Concept | Definition | Why It Matters |
|---|---|---|
| Producer | Sends messages to a queue or topic | Decoupled from consumer lifecycle |
| Consumer | Reads and processes messages | Can scale independently of producer |
| Acknowledgment | Consumer confirms successful processing | Prevents message loss — unacked messages get redelivered |
| Dead letter queue (DLQ) | Queue for messages that fail processing repeatedly | Prevents poison messages from blocking the queue |
| Message ordering | Guarantee that messages are consumed in send order | Required for stateful processing, optional for independent tasks |
| Partitioning | Messages distributed across partitions by key | Enables parallel consumption while preserving per-key ordering |

### Message Design

| Principle | Guidance |
|---|---|
| Self-contained | Include all data needed for processing. Avoid requiring consumer to call back for more data. |
| Idempotent key | Include a unique message ID so consumers can deduplicate. |
| Schema versioned | Use a schema registry or version field for forward/backward compatibility. |
| Small payload | Keep messages small (KB, not MB). Use references (S3 URLs) for large payloads. |
| Typed | Include message type or event name for routing and deserialization. |

## Message Broker Selection

| Broker | Model | Ordering | Persistence | Throughput | Replay | Best For |
|---|---|---|---|---|---|---|
| RabbitMQ | Traditional queue + exchange routing | Per-queue FIFO | Until consumed + acked | Moderate (tens of thousands/sec) | No (consumed messages removed) | Task distribution, RPC-style, complex routing |
| Apache Kafka | Distributed commit log | Per-partition | Configurable retention (days/weeks) | Very high (millions/sec) | Yes (consumer offset-based) | Event streaming, data pipelines, audit logs |
| Amazon SQS | Managed queue | Standard: best-effort. FIFO: strict | Until consumed + acked | High (managed, auto-scales) | No | Simple queuing without infrastructure management |
| Amazon SNS + SQS | Managed pub/sub + queue fanout | Per-subscription queue ordering | Via SQS subscribers | High | No | Fan-out to multiple consumers in AWS |
| Redis Streams | Lightweight stream with consumer groups | Per-stream | In-memory + optional persistence | Very high | Yes (stream ID-based) | Lightweight streaming when Redis is already in stack |
| NATS | Lightweight pub/sub | Per-subject | Optional (JetStream) | Very high, low latency | With JetStream | Microservice communication, IoT, edge |

### Selection Decision Tree

1. **Need event replay or audit log?** → Kafka (log-based retention)
2. **Complex routing rules (topic, header, fanout)?** → RabbitMQ (exchange model)
3. **Managed service, minimal ops?** → SQS/SNS (AWS) or Cloud Pub/Sub (GCP)
4. **Already using Redis, lightweight needs?** → Redis Streams
5. **Ultra-low latency, ephemeral messages?** → NATS
6. **High-throughput data pipeline?** → Kafka

## Event-Driven Architecture

### Event Types

| Type | Content | Consumer Behavior | Coupling |
|---|---|---|---|
| Event notification | Minimal: "Order #123 was placed" | Consumer fetches details from source if needed | Low (consumer decides what to fetch) |
| Event-carried state transfer | Full: "Order #123: {items, total, customer, address}" | Consumer has all data, no callback needed | Medium (schema dependency) |
| Event sourcing | State change: "ItemAdded {productId, qty}" | Consumer rebuilds state by replaying events | High (sequence-dependent) |

### Event Notification

Lightweight events that signal something happened. Consumers decide whether and how to react.

**Advantages**: Low coupling, small messages, producer unaware of consumer needs.
**Disadvantage**: Consumer may need to call back to get full data, creating coupling.

### Event-Carried State Transfer

Events include the full data snapshot. Consumers maintain their own copy of the data they need.

**Advantages**: Consumers are fully autonomous, no callback needed, works offline.
**Disadvantage**: Larger messages, data duplication, eventual consistency between copies.

### Event Sourcing

Store every state change as an immutable event. Current state is derived by replaying events.

| Aspect | Detail |
|---|---|
| Storage | Append-only event log (event store) |
| Current state | Replay all events for an entity, or maintain snapshots |
| Audit trail | Complete history of every change |
| Debugging | Replay events to reproduce any past state |
| Complexity | High — event schema evolution, replay performance, snapshot management |
| When to use | Audit-critical domains (finance, healthcare, legal), complex business workflows |
| When to avoid | Simple CRUD, low complexity domains, small teams |

### Domain Events vs Integration Events

| Aspect | Domain Event | Integration Event |
|---|---|---|
| Scope | Within a bounded context | Across bounded contexts or services |
| Audience | Internal handlers | External services |
| Schema coupling | Can change freely | Must be versioned and backward-compatible |
| Transport | In-process or internal bus | Message broker (Kafka, RabbitMQ) |

## CQRS (Command Query Responsibility Segregation)

Separate the write model (commands) from the read model (queries). Each optimized independently.

### When CQRS Adds Value

| Signal | Why CQRS Helps |
|---|---|
| Read and write models are fundamentally different shapes | Avoids compromise in either direction |
| Read volume vastly exceeds write volume | Scale read side independently |
| Complex queries slow down write-optimized tables | Read model pre-joins and denormalizes |
| Multiple views of the same data needed | Each read model optimized for its view |

### When CQRS Is Overkill

| Signal | Why CQRS Hurts |
|---|---|
| Simple CRUD with similar read/write shapes | Unnecessary complexity |
| Small team or early-stage product | Maintenance burden disproportionate to benefit |
| Strong consistency required between read and write | Eventual consistency between models adds complexity |

### Synchronization Between Models

| Approach | Latency | Consistency | Complexity |
|---|---|---|---|
| Synchronous projection | Immediate | Strong | Low (but couples read/write) |
| Async event projection | Seconds | Eventual | Medium |
| Change data capture (CDC) | Seconds | Eventual | Medium-High (infrastructure) |
| Scheduled batch rebuild | Minutes-hours | Periodic | Low (but stale between rebuilds) |

## Saga Pattern

Manage distributed transactions across services without two-phase commit. A saga is a sequence of local transactions, each publishing events or commands that trigger the next step. On failure, compensating transactions undo previous steps.

### Choreography vs Orchestration

| Approach | How | Advantage | Disadvantage |
|---|---|---|---|
| Choreography | Each service listens for events and acts independently | Decoupled, no central coordinator | Hard to understand full flow, complex error handling |
| Orchestration | Central coordinator directs each step | Clear workflow visibility, centralized error handling | Coordinator is a coupling point, potential bottleneck |

**Selection heuristic**: Use choreography for simple flows (2-3 steps). Use orchestration for complex workflows (4+ steps) or when visibility and error handling are critical.

### Compensating Transactions

For each forward action, define a compensating action that semantically undoes it:

| Forward Action | Compensating Action |
|---|---|
| Reserve inventory | Release inventory |
| Charge payment | Refund payment |
| Create shipment | Cancel shipment |
| Send confirmation email | Send cancellation email |

**Key constraint**: Compensating actions must be idempotent. They may be triggered multiple times due to retries.

### Saga Failure Handling

| Failure Point | Behavior |
|---|---|
| Step N fails | Execute compensating transactions for steps N-1 through 1 |
| Compensation fails | Retry compensation with backoff. If still failing, alert for manual intervention. |
| Coordinator crashes (orchestration) | Resume from last known state (requires durable state storage) |

## Back-Pressure and Flow Control

### Why Unbounded Queues Are Dangerous

A producer faster than its consumer causes the queue to grow without limit. This leads to: memory exhaustion, increased latency (messages wait longer), cascading failures when the broker crashes.

### Back-Pressure Mechanisms

| Mechanism | How | Trade-off |
|---|---|---|
| Bounded queue | Reject or block producer when queue is full | Producer must handle rejection |
| Rate limiting at producer | Producer self-limits based on consumer capacity signal | Requires feedback mechanism |
| Consumer scaling | Auto-scale consumers based on queue depth | Lag between queue growth and scaling |
| Load shedding | Drop low-priority messages when overloaded | Data loss for shed messages |
| Credit-based flow control | Consumer grants credits to producer, producer stops when credits exhausted | Fine-grained control, more complex protocol |

### Queue Depth Monitoring

| Queue Depth Trend | Interpretation | Action |
|---|---|---|
| Stable near zero | Consumer keeps up with producer | Healthy |
| Steadily growing | Consumer is slower than producer | Scale consumers or reduce producer rate |
| Spike then recovery | Temporary burst absorbed | Healthy if recovery is fast |
| Growing unbounded | Systemic imbalance | Alert, investigate, apply back-pressure |

## Delivery Guarantees

| Guarantee | Meaning | Implementation | Data Impact |
|---|---|---|---|
| At-most-once | Message delivered zero or one time | Fire-and-forget, no ack | Possible message loss |
| At-least-once | Message delivered one or more times | Ack after processing, retry on failure | Possible duplicates — consumer must be idempotent |
| Exactly-once | Message delivered and processed exactly once | Transactional processing + deduplication | No loss, no duplicates — highest complexity |

### Achieving "Exactly Once" in Practice

True exactly-once delivery is a coordination problem. Practical approach: at-least-once delivery + idempotent consumer.

| Technique | How |
|---|---|
| Idempotency key | Consumer tracks processed message IDs, skips duplicates |
| Transactional outbox | Write message to outbox table in same DB transaction as business logic. Separate process publishes outbox entries. |
| Database upsert | Use INSERT ON CONFLICT or MERGE so reprocessing produces same result |
| Kafka transactions | Producer transactions + consumer read-committed isolation (Kafka-specific) |

**Default recommendation**: Design consumers to be idempotent and use at-least-once delivery. This is simpler and more resilient than attempting true exactly-once semantics.

## Dead Letter Queue Handling

Messages that fail processing repeatedly should not block the queue forever. Route them to a dead letter queue (DLQ) for investigation.

### DLQ Configuration

| Parameter | Guideline |
|---|---|
| Max delivery attempts | 3-5 before routing to DLQ |
| DLQ retention | Days to weeks (long enough for investigation) |
| Monitoring | Alert on DLQ depth — non-zero means something is failing |
| Reprocessing | After fixing the bug, replay DLQ messages back to main queue |

### Common DLQ Causes

| Cause | Fix |
|---|---|
| Malformed message (schema violation) | Fix producer schema, add validation at consumer |
| Transient dependency failure (all retries exhausted) | Fix dependency, replay from DLQ |
| Business logic rejection | Investigate, potentially discard or route to manual review |
| Deserialization error | Version mismatch — fix schema compatibility |

## Event Schema Evolution

As systems evolve, event schemas change. Breaking changes to shared events cause cascading failures across consumers.

### Compatibility Modes

| Mode | Rule | Consumer Impact |
|---|---|---|
| Backward compatible | New schema can read data written by old schema | Old producers, new consumers — works |
| Forward compatible | Old schema can read data written by new schema | New producers, old consumers — works |
| Full compatible | Both backward and forward compatible | Any combination works — safest |

### Safe Schema Changes

| Safe (backward compatible) | Unsafe (breaking) |
|---|---|
| Add optional field with default | Remove a field |
| Add new event type | Rename a field |
| Deprecate field (keep but ignore) | Change field type |
| Add new enum value | Remove enum value |

### Schema Registry

Use a schema registry (Confluent Schema Registry, AWS Glue) to:
- Enforce compatibility rules on schema evolution
- Reject breaking changes before they reach production
- Provide schema lookup for consumers
- Track schema versions and lineage

## Messaging Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Database as message queue | Polling is expensive, locking causes contention | Use a proper message broker |
| Unbounded queue without monitoring | Silent backlog growth, eventual OOM or disk full | Set limits, monitor depth, alert on growth |
| Large payloads in messages | Broker performance degrades, memory pressure | Store payload in S3/blob, send reference in message |
| No dead letter queue | Poison messages block processing forever | Configure DLQ with monitoring |
| Synchronous over queue | Using request-reply over a queue when REST/gRPC is simpler | Use queues for async; use direct calls for sync |
| Missing idempotency in consumer | Retries cause duplicate side effects | Track processed message IDs, use idempotent operations |
