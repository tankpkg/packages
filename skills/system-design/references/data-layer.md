# Data Layer Design

Sources: Synthesized from Kleppmann (Designing Data-Intensive Applications), Petrov (Database Internals), Richards & Ford (Fundamentals of Software Architecture)

Covers: database type selection, replication strategies, partitioning/sharding, consistency models, CAP/PACELC applied, SQL vs NoSQL, data modeling for scale.

## Database Type Selection

No database is universally best. Selection depends on access patterns, consistency requirements, scale needs, and operational maturity.

### Selection Matrix

| Database Type | Data Model | Query Strength | Consistency | Scale Model | Best Fit |
|---|---|---|---|---|---|
| Relational (PostgreSQL, MySQL) | Tables, rows, foreign keys | Complex joins, aggregations, ad-hoc queries | Strong (ACID) | Vertical + read replicas, limited sharding | Transactional systems, complex queries, reporting |
| Document (MongoDB, CouchDB) | Nested JSON documents | Queries on document fields, flexible schema | Tunable (per-operation) | Horizontal via sharding | Content management, user profiles, catalogs |
| Key-Value (Redis, DynamoDB) | Opaque values by key | Point lookups by key, range scans on sort key | Tunable (DynamoDB), single-threaded (Redis) | Horizontal, partitioned by key | Sessions, caches, feature flags, counters |
| Wide-Column (Cassandra, ScyllaDB) | Rows with dynamic columns, partitioned by key | Partition-key lookups, range within partition | Tunable (quorum-based) | Horizontal, masterless | Time-series, activity logs, IoT telemetry |
| Graph (Neo4j, Neptune) | Nodes + edges + properties | Traversals, shortest path, pattern matching | Strong (Neo4j), eventual (Neptune) | Limited horizontal (mostly vertical) | Social networks, fraud detection, recommendations |
| Time-Series (TimescaleDB, InfluxDB) | Time-stamped data points | Time-range aggregations, downsampling | Varies | Horizontal with time partitioning | Metrics, monitoring, financial tick data |
| Search (Elasticsearch, OpenSearch) | Inverted index on documents | Full-text search, faceting, fuzzy matching | Eventual | Horizontal via shards | Search features, log analysis, analytics |

### Decision Framework

Ask these questions in order:

1. **Do you need ACID transactions across multiple entities?** → Relational database
2. **Is the primary access pattern key-value lookup?** → Key-value store
3. **Is the data naturally hierarchical or semi-structured?** → Document store
4. **Do you need to traverse relationships?** → Graph database
5. **Is it time-stamped with range-query and aggregation focus?** → Time-series database
6. **Do you need full-text search as primary query pattern?** → Search engine
7. **Is it write-heavy with simple partition-key access?** → Wide-column store

**Polyglot persistence**: Most production systems use multiple database types. An e-commerce platform might use PostgreSQL for orders (ACID), Redis for sessions (speed), Elasticsearch for product search (full-text), and TimescaleDB for analytics (time-series).

## Replication Strategies

Replication keeps copies of data on multiple nodes for durability, availability, and read throughput.

### Single-Leader (Primary-Replica)

One node accepts writes (leader), replicates to followers that serve reads.

| Aspect | Detail |
|---|---|
| Write path | Client → leader → replicate to followers |
| Read path | Client → any follower (or leader) |
| Consistency | Strong if reading from leader; eventual if reading from followers |
| Failover | Promote a follower to leader (manual or automatic) |
| Best for | Read-heavy workloads with moderate write volume |
| Risk | Replication lag causes stale reads from followers |

### Multi-Leader

Multiple nodes accept writes independently, synchronize with each other asynchronously.

| Aspect | Detail |
|---|---|
| Use case | Multi-datacenter writes, offline-capable clients, collaborative editing |
| Conflict handling | Last-write-wins (data loss risk), merge functions, or CRDTs |
| Complexity | Conflict detection and resolution logic required |
| Avoid unless | You genuinely need writes in multiple regions simultaneously |

### Leaderless (Quorum-Based)

Any node accepts reads and writes. Consistency achieved through quorum: read from R nodes, write to W nodes, where R + W > N (total replicas).

| Configuration | Behavior | Trade-off |
|---|---|---|
| W=N, R=1 | Write to all, read from any | Fast reads, slow writes, unavailable if any node down for writes |
| W=1, R=N | Write to any, read from all | Fast writes, slow reads, risk of reading stale data |
| W=majority, R=majority | Balanced quorum | Good balance of consistency and availability |

### Synchronous vs Asynchronous Replication

| Mode | Durability | Latency | Availability Impact |
|---|---|---|---|
| Synchronous | Write confirmed only after replica acknowledges | Higher (network round-trip to replica) | Write fails if replica is down |
| Asynchronous | Write confirmed after leader persists locally | Lower | Potential data loss if leader fails before replication |
| Semi-synchronous | One replica synchronous, rest async | Moderate | Balances durability with availability |

## Partitioning and Sharding

Split data across multiple nodes so each handles a subset of the total dataset.

### Partitioning Strategies

| Strategy | How | Strength | Weakness |
|---|---|---|---|
| Range-based | Assign key ranges to partitions (A-M, N-Z) | Efficient range queries within partition | Hot spots if access skewed to certain ranges |
| Hash-based | Hash the key, assign hash ranges to partitions | Even distribution eliminates most hot spots | Range queries scatter across all partitions |
| Directory-based | Lookup table maps keys to partitions | Maximum flexibility | Lookup table becomes bottleneck and SPOF |
| Compound | Hash for partition, range for sort within partition | Range queries within a partition key (DynamoDB model) | Two-level key design required |

### Hot Spot Prevention

- **Add salt to keys**: Append random suffix to high-traffic keys, scatter writes across partitions. Reassemble on read.
- **Time-bucket keys**: For time-series, include date in partition key to spread writes across time-based partitions.
- **Monitor partition sizes**: Alert when any partition grows disproportionately. Rebalance before it becomes critical.

### Rebalancing Strategies

| Approach | How | Disruption |
|---|---|---|
| Fixed partition count | Pre-create many partitions, assign multiple per node, reassign on scaling | Low — only reassign partition ownership |
| Dynamic splitting | Split partitions that grow too large | Moderate — data movement during split |
| Consistent hashing | Assign hash ring ranges to nodes, minimal reassignment on add/remove | Low — only neighbors affected |

### Cross-Partition Queries

Queries spanning partitions are expensive (scatter-gather). Mitigate with:
- **Denormalize**: Store data needed together in the same partition
- **Secondary index**: Global secondary index (maintained separately) or local secondary index (per-partition)
- **Materialized views**: Pre-compute cross-partition aggregations
- **Avoid if possible**: Design partition keys around primary access patterns

## Consistency Models

Ordered from strongest to weakest. Stronger consistency costs more in latency and availability.

| Model | Guarantee | Practical Implication |
|---|---|---|
| Linearizability | Every read returns the most recent write | Behaves as if a single copy exists. Required for locks, leader election. |
| Sequential consistency | All nodes see operations in the same order, but not necessarily real-time | Slightly weaker than linearizability. Sufficient for many coordination tasks. |
| Causal consistency | Operations causally related are seen in order; concurrent operations may differ | If A causes B, everyone sees A before B. Good for messaging, collaboration. |
| Read-your-writes | A client always sees its own writes | User updates profile, immediately sees the change. Does not guarantee others see it yet. |
| Eventual consistency | All replicas converge to the same state given enough time without new writes | Acceptable for social feeds, analytics, caches. Cheapest in latency and availability. |

### Choosing Consistency Level

| Use Case | Required Consistency | Why |
|---|---|---|
| Bank account balance | Linearizable | Must not allow overdraft from stale reads |
| Inventory count (last item) | Linearizable or serializable | Overselling creates real-world problems |
| User profile display | Read-your-writes | User expects to see their own changes |
| Social media feed | Eventual | Slight delay in seeing new posts is acceptable |
| Analytics dashboard | Eventual | Minutes-old data is fine for reporting |
| Collaborative editing | Causal | Users need to see cause-and-effect ordering |
| Distributed lock | Linearizable | Incorrect lock state causes data corruption |

## CAP and PACELC Applied

### CAP in Practice

CAP states that during a network partition, a distributed system must choose between consistency and availability. Since partitions are inevitable in distributed systems, the real choice is between CP and AP behavior during failures.

| Choice | Behavior During Partition | Example Systems |
|---|---|---|
| CP (Consistency + Partition tolerance) | Rejects requests rather than serve stale data | ZooKeeper, etcd, MongoDB (default), PostgreSQL |
| AP (Availability + Partition tolerance) | Serves requests with potentially stale data | Cassandra, DynamoDB (default), CouchDB |

### PACELC Extension

When there is NO partition: choose between latency and consistency.

| System Behavior | Normal Operation | During Partition | Example |
|---|---|---|---|
| PC/EC | Consistent, higher latency | Consistent, unavailable | PostgreSQL with sync replicas |
| PA/EL | Available, low latency | Available, inconsistent | Cassandra with ONE consistency |
| PA/EC | Available, low latency | Available, inconsistent → converges | DynamoDB default |
| PC/EL | Consistent, low latency | Consistent, unavailable | Single-node database |

### Practical Decision Framework

1. **Identify the data domain**: Financial transactions? Social feed? Configuration?
2. **Determine the cost of inconsistency**: Lost money? Annoyed users? Stale dashboard?
3. **Determine the cost of unavailability**: Lost revenue? Blocked operations? Degraded experience?
4. **Choose per-operation, not per-system**: A single application can use strong consistency for payments and eventual consistency for notifications.

## SQL vs NoSQL Decision Framework

| Criterion | Favors Relational (SQL) | Favors Non-Relational (NoSQL) |
|---|---|---|
| Schema stability | Known, stable schema | Rapidly evolving or unpredictable schema |
| Query complexity | Joins, aggregations, ad-hoc queries | Simple key-based lookups or document retrieval |
| Transactions | Multi-row, multi-table ACID needed | Single-document atomicity sufficient |
| Scale pattern | Read-heavy (replicas handle reads) | Write-heavy or massive data volume |
| Consistency needs | Strong consistency required | Eventual consistency acceptable |
| Team expertise | SQL and relational modeling skills | Document/key-value modeling skills |
| Operational maturity | Managed PostgreSQL/MySQL widely available | Managed DynamoDB/Cassandra/MongoDB available |

**Warning**: "We might need to scale" is not a valid reason to choose NoSQL. PostgreSQL handles millions of rows and thousands of QPS on a single well-tuned instance. Choose based on actual access patterns, not hypothetical scale.

## Data Modeling for Scale

### Denormalization Trade-offs

| Factor | Normalized | Denormalized |
|---|---|---|
| Write complexity | Simple — update in one place | Complex — update in multiple places |
| Read complexity | Requires joins | Single read, no joins |
| Storage | Minimal duplication | Significant duplication |
| Consistency | Single source of truth | Risk of inconsistency across copies |
| Best for | Write-heavy, consistency-critical | Read-heavy, latency-critical |

### Practical Denormalization Patterns

- **Materialized views**: Database maintains a pre-joined, pre-aggregated view. Refresh on schedule or via triggers.
- **Precomputed aggregates**: Store running totals (order count, total spend) updated on each write.
- **Embedded documents**: In document stores, embed related data within the parent document when read together.
- **Cache-based denormalization**: Keep normalized database, serve reads from a denormalized cache.

### Data Locality Optimization

Store data that is accessed together physically close:
- **Partition key design**: Choose keys that group co-accessed data on the same node
- **Column family grouping**: In wide-column stores, group frequently co-read columns
- **Document embedding**: In document stores, embed vs reference based on access patterns
- **Table co-location**: In distributed SQL, co-locate related tables on the same shard

## Schema Migration at Scale

### Migration Strategies

| Strategy | How | Risk | Best For |
|---|---|---|---|
| Expand-contract (online) | Add new column/table → backfill → migrate code → drop old | Low — no downtime, rollback easy | Production databases with uptime requirements |
| Blue-green schema | Maintain two schema versions, switch traffic | Medium — requires dual-write during transition | Major schema overhauls |
| Shadow writes | Write to both old and new schema, compare results | Low — validates correctness before cutover | High-risk migrations on critical data |
| Offline migration | Take system offline, migrate, bring back | High — downtime required | Small systems where downtime is acceptable |

### Safe Migration Rules

1. **Never rename a column in one step** — Add new column, backfill, migrate code, drop old column
2. **Never change a column type destructively** — Add new column with new type, migrate data, update code, drop old
3. **Always add columns as nullable or with defaults** — Non-nullable without default locks the table on large datasets
4. **Backfill in batches** — Processing millions of rows in one transaction locks the table and may cause OOM
5. **Test migrations against production-size data** — A migration that takes 1 second on dev may take 1 hour on production

## Choosing Between Single-Database and Multi-Database

| Signal | Single Database | Multiple Databases |
|---|---|---|
| Team size | Small (< 20 engineers) | Large (20+, multiple teams) |
| Data relationships | Tightly coupled, frequent joins | Loosely coupled, different access patterns |
| Consistency requirements | Strong consistency across all data | Different consistency needs per domain |
| Scaling needs | Uniform scaling sufficient | Different domains need different scaling |
| Operational maturity | Limited ops capacity | Can manage multiple database types |
| Deployment independence | Not required | Teams need independent data evolution |

**Default**: Start with a single relational database. Split when you have concrete evidence that different data domains need different database types, consistency models, or scaling strategies.

## Data Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Shared database between services | Tight coupling, schema changes break other services | Each service owns its database exclusively |
| Storing derived data without source | Cannot rebuild when derivation logic changes | Store source data, derive on read or via materialized views |
| Using a relational DB as a message queue | Polling is inefficient, locking contention | Use a proper message broker |
| Storing large blobs in the database | Bloats database, slows backups, wastes buffer cache | Use object storage (S3), store reference in database |
| No data retention policy | Database grows unbounded | Define TTL per data type, archive or delete old data |
| Premature sharding | Operational complexity before it is needed | Single node handles more than you think — optimize first |
