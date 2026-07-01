# CQRS and Event Sourcing

Sources: Young (CQRS Journey), Fowler (CQRS pattern), Vernon (Implementing DDD), Kleppmann (Designing Data-Intensive Applications), Ford et al. (Software Architecture: The Hard Parts)

Covers: CQRS at application level, command/query separation, read model design, eventual consistency, event sourcing fundamentals, event store, projections, snapshots, when to use vs avoid, combining CQRS with event sourcing.

## CQRS: Command Query Responsibility Segregation

### Core Concept

Separate the write model (commands) from the read model (queries) into distinct models, possibly distinct data stores.

| Side | Purpose | Optimized For |
|---|---|---|
| Command (write) | Accept changes, enforce business rules | Consistency, validation, transactional integrity |
| Query (read) | Return data for display | Read performance, denormalized views, flexible shapes |

### Why Separate Reads and Writes

| Problem with Unified Model | How CQRS Solves It |
|---|---|
| Domain model is complex for reads | Read model is flat, denormalized, optimized for queries |
| Reads and writes have different scaling needs | Scale read and write sides independently |
| Query requirements distort domain model | Domain model stays pure; read model shaped for UI needs |
| Complex joins for display | Read model pre-joins data at write time |

### CQRS Levels of Separation

| Level | Description | Complexity | When to Use |
|---|---|---|---|
| Code separation | Same database, separate command/query classes | Low | Default starting point when reads/writes diverge |
| Schema separation | Same database, separate read tables/views | Medium | Read patterns differ significantly from write schema |
| Database separation | Different databases for read and write | High | Extreme read/write ratio asymmetry or different storage needs |

Start at the lowest level that solves the problem. Do not jump to separate databases without evidence.

### Command Side Design

| Component | Responsibility |
|---|---|
| Command | Data structure representing the user's intent: `PlaceOrderCommand { items, shippingAddress }` |
| Command Handler | Validates, loads aggregate, executes domain logic, persists. One handler per command |
| Write Model | Domain model (entities, aggregates, value objects) — optimized for invariant enforcement |

#### Command Design Rules

| Rule | Rationale |
|---|---|
| Commands are imperative: `PlaceOrder`, `CancelOrder` | Express user intent, not data mutation |
| Commands carry only the data needed | Do not pass the entire entity — only the fields the operation requires |
| One command, one handler | Single Responsibility — each handler is focused and testable |
| Commands can be rejected | Validation failure, business rule violation, concurrency conflict |
| Commands return minimal data | Success/failure + ID of created resource. Not the full entity |

### Query Side Design

| Component | Responsibility |
|---|---|
| Query | Data structure representing what the user wants to see: `GetOrderDetailsQuery { orderId }` |
| Query Handler | Reads from the read store, returns a read model / view model. No business logic |
| Read Model | Denormalized data structure shaped for a specific view or API response |

#### Read Model Design Rules

| Rule | Rationale |
|---|---|
| Read models are disposable | They can be rebuilt from the write side at any time |
| Shape per use case | Dashboard view, list view, detail view — each gets its own read model |
| No domain logic in queries | Read handlers are pure data retrieval. No validation, no state changes |
| Pre-compute expensive operations | Aggregate counts, totals, derived fields — compute at write time, store in read model |

### Synchronizing Read and Write Models

| Strategy | Mechanism | Consistency | Complexity |
|---|---|---|---|
| Synchronous update | Write handler updates read model in same transaction | Strong | Low (but coupling) |
| Domain events (in-process) | Write publishes event, read model handler updates asynchronously | Eventual (milliseconds) | Medium |
| Domain events (message broker) | Event published to Kafka/RabbitMQ, consumer updates read store | Eventual (seconds) | High |
| Change data capture | Database change log consumed by read model updater | Eventual (seconds) | Medium (infrastructure) |

### Eventual Consistency in Practice

When read and write models are separate, reads may lag behind writes.

| Strategy | How |
|---|---|
| Read-your-own-writes | After a command, redirect to a page that reads from the write model or waits for sync |
| Optimistic UI | UI assumes success immediately, reconciles if command fails |
| Polling/websockets | Client polls read model until updated version appears |
| Version tracking | Read model carries a version; client retries if version is stale |

## Event Sourcing

### Core Concept

Instead of storing current state, store the sequence of events that led to the current state. The current state is derived by replaying events.

```
Traditional:  Save current state -> { id: 1, balance: 150, status: "active" }

Event Sourced: Save events ->
  AccountOpened { id: 1, initialBalance: 0 }
  MoneyDeposited { id: 1, amount: 200 }
  MoneyWithdrawn { id: 1, amount: 50 }
  // Current state: replay all events -> balance: 150
```

### Event Store

| Property | Description |
|---|---|
| Append-only | Events are never modified or deleted |
| Ordered per aggregate | Events for an aggregate have a sequence number |
| The source of truth | Current state is derived, events are authoritative |
| Query by aggregate ID | Load all events for an aggregate to reconstruct its state |

### Projections (Read Models)

Event sourcing naturally pairs with CQRS. Projections consume the event stream and build read-optimized views.

| Projection Type | Description | Example |
|---|---|---|
| Synchronous | Updated in same process after event is appended | In-memory read model for testing |
| Asynchronous | Separate consumer subscribes to event stream | Elasticsearch index, reporting database |
| Catch-up subscription | Consumer reads from a position and processes all subsequent events | Rebuilding a read model from scratch |

### Rebuilding Projections

One of event sourcing's strongest benefits: any projection can be rebuilt from the event stream.

1. Create a new projection consumer
2. Start reading from the beginning of the event stream
3. Apply each event to build the new read model
4. Once caught up, switch traffic to the new projection

This enables adding new query capabilities without database migrations on the write side.

### Snapshots

Replaying thousands of events to reconstruct an aggregate is slow. Snapshots store the aggregate state at a point in time.

| Concept | Description |
|---|---|
| Snapshot | Serialized aggregate state at event N |
| Reconstruction | Load snapshot, then replay only events after N |
| Frequency | Snapshot every N events (e.g., every 100) or on demand |
| Storage | Same event store or separate snapshot store |

Snapshots are an optimization. The event stream remains the source of truth.

### Versioning Events

Events are immutable facts. When the event schema needs to change:

| Strategy | How | When |
|---|---|---|
| Upcasting | Transform old event format to new format at read time | Schema additions (new fields with defaults) |
| New event type | Introduce `OrderPlacedV2` alongside `OrderPlaced` | Breaking schema changes |
| Weak schema | Treat event data as a flexible map, handle missing fields gracefully | Evolving systems with many event types |

Never modify existing events in the store. Upcasting or new versions preserve the historical record.

### When to Use Event Sourcing

| Signal | Event Sourcing Adds Value |
|---|---|
| Full audit trail is a business requirement | Every state change is recorded as an event |
| Need to answer "how did we get here?" | Replay events to understand state transitions |
| Complex state transitions with business rules | Events capture intent, not just result |
| Multiple read model shapes needed | Build any view from the event stream |
| Temporal queries ("what was the state at time T?") | Replay events up to time T |
| Regulatory compliance (finance, healthcare) | Immutable, append-only event log |

### When to Avoid Event Sourcing

| Signal | Why Event Sourcing Hurts |
|---|---|
| Simple CRUD with no audit needs | Massive overhead for basic persistence |
| Querying current state is the primary use case | Reconstructing state from events is slower than reading a row |
| Team has no experience with event sourcing | Steep learning curve, subtle failure modes |
| Delete/GDPR requirements | "Right to be forgotten" conflicts with immutable events (requires crypto-shredding or tombstones) |
| High-frequency state changes on same aggregate | Thousands of events per aggregate, snapshot overhead |

### Event Sourcing Pitfalls

| Pitfall | Problem | Mitigation |
|---|---|---|
| Event schema evolution | Changing event structure breaks replay | Upcasting strategy from day one |
| Large event streams per aggregate | Slow reconstruction, memory pressure | Snapshots, aggregate size limits |
| Eventual consistency confusion | Developers expect immediate read-your-writes | Explicit consistency strategy in UI/API |
| Event granularity too fine | Noise drowns signal, slow projections | Events represent domain-meaningful state changes, not field-level diffs |
| Event granularity too coarse | Lost information, cannot build needed projections | Each event should capture one business-meaningful fact |
| Missing idempotency in projections | Duplicate events cause incorrect read models | Idempotent projection handlers, track processed event position |

## CQRS Without Event Sourcing

CQRS and event sourcing are independent patterns. Use CQRS without event sourcing when:

| Scenario | Approach |
|---|---|
| Read/write shape asymmetry | CQRS with separate read model, traditional state persistence on write side |
| Different scaling needs | CQRS with read replicas, no event store |
| Simple domain, complex query patterns | CQRS with materialized views or denormalized read tables |

CQRS without event sourcing is far simpler to implement and operate. Start here unless you have a clear need for event sourcing.

## CQRS + Event Sourcing Together

When combined: commands produce events (write side), events are stored in an event store, projections consume events to build read models (read side).

```
Command -> Command Handler -> Aggregate -> Events -> Event Store
                                                        |
                                                        v
                                              Projection Handler -> Read Database -> Query Handler -> Response
```

This combination gives maximum flexibility but maximum complexity. Reserve for core domains where both the audit trail and read model flexibility are genuine requirements.

## Implementation Guidance

### Command Bus Implementation

A command bus dispatches commands to their handlers and optionally applies pipeline behaviors.

```
interface CommandBus {
  dispatch<T>(command: Command): Promise<T>;
}

class SimpleCommandBus implements CommandBus {
  private handlers: Map<string, CommandHandler>;
  private middleware: Middleware[];

  async dispatch<T>(command: Command): Promise<T> {
    const handler = this.handlers.get(command.constructor.name);
    const pipeline = this.middleware.reduceRight(
      (next, mw) => () => mw.execute(command, next),
      () => handler.handle(command)
    );
    return pipeline();
  }
}
```

### Read Model Storage Options

| Storage | Best For | Trade-Off |
|---|---|---|
| Same relational database (materialized view) | Simple CQRS, same-transaction consistency | Limited denormalization flexibility |
| Separate relational tables | Different schema than write side, still relational queries | Eventual consistency, schema migration for both sides |
| Elasticsearch | Full-text search, complex filtering, analytics | Operational complexity, eventual consistency |
| Redis | Low-latency key-value lookups, counters | Limited query flexibility, memory-bound |
| MongoDB | Flexible document shapes per read model | Another database to operate |

### Event Store Technology Options

| Technology | Type | Strengths | Considerations |
|---|---|---|---|
| EventStoreDB | Purpose-built | Built for event sourcing, subscriptions, projections | Operational overhead of another database |
| PostgreSQL (append-only table) | Relational | Familiar, transactional, no new infrastructure | Must implement subscription and snapshot logic |
| DynamoDB | Managed NoSQL | Serverless, scales automatically | Limited querying without streams + Lambda |
| Kafka (as event store) | Log-based | High throughput, natural event streaming | Compaction semantics differ from true event store |
| Marten (.NET) | Library on PostgreSQL | Integrated event sourcing + document storage | .NET ecosystem only |

### Testing CQRS Systems

| Component | Test Strategy |
|---|---|
| Command handler | Unit test with in-memory repository. Assert events emitted or state changed |
| Query handler | Unit test against seeded read store. Assert correct data shape returned |
| Projection handler | Unit test: given events, assert read model state. Idempotency test: replay events twice, assert same result |
| End-to-end | Send command, wait for projection update, query read model, assert consistency |

### CQRS Monitoring Checklist

| Metric | Why |
|---|---|
| Projection lag (time between event and read model update) | Detect growing eventual consistency window |
| Command rejection rate | Detect validation or concurrency issues |
| Event store growth rate | Capacity planning, snapshot frequency tuning |
| Projection rebuild time | Ensure rebuilds complete within maintenance windows |
| Dead letter queue depth | Detect events that projections cannot process |
