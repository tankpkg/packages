# Caching Strategies

Sources: Synthesized from Kleppmann (Designing Data-Intensive Applications), Vitillo (Understanding Distributed Systems), Nygard (Release It!)

Covers: cache placement, caching patterns, distributed cache architecture, invalidation, eviction policies, failure modes, when not to cache.

## Cache Placement Decision

Caching can occur at multiple layers. Each layer trades freshness for latency reduction.

| Layer | Location | Latency Reduction | Staleness Risk | Best For |
|---|---|---|---|---|
| Client-side | Browser, mobile app | Eliminates network round-trip | High — user must refresh | Static assets, user preferences, offline support |
| CDN edge | Edge server near user | Reduces geographic latency | Moderate — TTL-controlled | Static content, cacheable API responses |
| API gateway | Entry point of backend | Avoids routing to upstream services | Moderate | Repeated identical API calls, rate-limited responses |
| Application layer | In-process or sidecar | Avoids database/service calls | Low-moderate (controlled) | Hot data, computed results, session data |
| Database query cache | Database server | Avoids query re-execution | Low — invalidated on write | Repeated identical queries (limited utility) |

### Multi-Tier Caching

Combine layers for maximum effect. A typical web application:
1. Browser caches static assets (CSS, JS, images) via `Cache-Control` headers
2. CDN caches static assets and some API responses at edge
3. Application caches hot data in Redis
4. Database query cache handles remaining repeated queries

**Rule**: Each tier should have progressively shorter TTLs as you move closer to the source of truth. Browser: hours. CDN: minutes. Application: seconds to minutes. Database cache: invalidated on write.

## Caching Patterns

### Cache-Aside (Lazy Loading)

Application manages the cache explicitly. On read miss, fetch from database, populate cache, return.

```
Read:  App → Cache (hit?) → YES → return
                           → NO  → Database → write to cache → return
Write: App → Database → invalidate/delete cache entry
```

| Advantage | Disadvantage |
|---|---|
| Simple to implement | First request always misses (cold start) |
| Cache only what is actually read | Stale data between write and invalidation |
| Cache failure degrades gracefully | Application contains caching logic |

**When to use**: Default choice. Works well for read-heavy workloads where cache misses are tolerable.

### Read-Through

Cache sits between application and database. Application always reads from cache, which fetches from database on miss.

| Advantage | Disadvantage |
|---|---|
| Application code is simpler (no cache management) | Cache library/provider must support it |
| Consistent read path | Same cold-start problem as cache-aside |

**When to use**: When using a cache provider that supports read-through natively (e.g., some Redis modules, NCache).

### Write-Through

Every write goes to cache first, then cache writes to database synchronously before confirming.

| Advantage | Disadvantage |
|---|---|
| Cache always has latest data | Write latency increases (cache + DB) |
| No stale reads | Every write populates cache, even for rarely-read data |
| Combined with read-through eliminates cache misses | Higher write cost |

**When to use**: Read-heavy with low tolerance for stale data. Pair with read-through for a fully managed cache layer.

### Write-Behind (Write-Back)

Write to cache immediately, return success. Cache asynchronously flushes to database in batches.

| Advantage | Disadvantage |
|---|---|
| Very fast writes (cache latency only) | Data loss risk if cache fails before flush |
| Batch writes to database reduce I/O | Complex consistency guarantees |
| Absorbs write spikes | Harder to debug |

**When to use**: Write-heavy workloads where slight data loss risk is acceptable (e.g., page view counters, analytics events).

### Refresh-Ahead

Cache proactively refreshes entries before they expire, based on predicted access patterns.

| Advantage | Disadvantage |
|---|---|
| Eliminates cache miss latency for hot data | Wastes resources refreshing data nobody reads |
| Users always get cached responses | Prediction accuracy determines effectiveness |

**When to use**: Small set of very hot keys with predictable access patterns (e.g., homepage content, popular product pages).

### Pattern Comparison Summary

| Pattern | Read Latency | Write Latency | Consistency | Complexity | Best Scenario |
|---|---|---|---|---|---|
| Cache-aside | Miss penalty on first read | Normal | Eventual (TTL-bound) | Low | General purpose, default choice |
| Read-through | Miss penalty on first read | Normal | Eventual | Low-Medium | Provider-supported caching |
| Write-through | Always from cache | Higher (cache + DB) | Strong | Medium | Low staleness tolerance |
| Write-behind | Always from cache | Very low (cache only) | Eventual (async flush) | High | High write throughput |
| Refresh-ahead | Always from cache | Normal | Near-real-time | Medium | Predictable hot data |

## Distributed Cache Architecture

### Redis vs Memcached

| Factor | Redis | Memcached |
|---|---|---|
| Data structures | Strings, hashes, lists, sets, sorted sets, streams | Strings only |
| Persistence | RDB snapshots, AOF log | None (pure cache) |
| Replication | Built-in primary-replica | None |
| Clustering | Redis Cluster (hash slots) | Client-side consistent hashing |
| Pub/sub | Built-in | None |
| Memory efficiency | Higher overhead per key | More memory-efficient for simple values |
| Use case | Feature-rich caching, sessions, leaderboards, queues | Simple, high-throughput key-value caching |

**Default choice**: Redis for most applications (richer features, persistence option, replication). Memcached when you need maximum memory efficiency for simple string caching at extreme scale.

### Cluster Topologies

| Topology | How | Trade-off |
|---|---|---|
| Client-side sharding | Client hashes key, routes to correct node | Simple, but client must know all nodes. No automatic failover. |
| Proxy-based (Twemproxy, Envoy) | Proxy routes requests to correct shard | Centralized routing, but proxy is a bottleneck/SPOF |
| Native clustering (Redis Cluster) | Nodes coordinate hash slot ownership | Automatic failover and rebalancing, but more operational complexity |

### Consistent Hashing for Cache Distribution

Map both cache keys and nodes onto a hash ring. Each key is stored on the next node clockwise on the ring. When a node is added or removed, only keys between the affected node and its predecessor are redistributed. Use virtual nodes (100-200 per physical node) for even distribution.

## Cache Invalidation

### Strategies

| Strategy | How | Consistency | Complexity |
|---|---|---|---|
| TTL-based | Set expiration time on cache entries | Eventual (stale up to TTL) | Lowest |
| Event-based | Publish invalidation event on data change | Near-real-time | Medium |
| Version-based | Store version counter, increment on change, include in cache key | Strong (versioned reads) | Medium |
| Write-invalidate | Delete cache entry on write | Eventual (brief window) | Low |
| Write-update | Update cache entry on write | Strong (if atomic) | Medium |

### TTL Guidelines

| Data Type | Suggested TTL | Rationale |
|---|---|---|
| Static content (logos, CSS hash) | 1 year (immutable URLs) | Content-addressed, never changes for a given URL |
| Semi-static (config, feature flags) | 1-5 minutes | Changes rarely, short TTL for quick propagation |
| User profile data | 5-15 minutes | Moderate staleness acceptable |
| API response cache | 30 seconds - 5 minutes | Balance freshness and load reduction |
| Session data | Match session timeout | Should not outlive the session |
| Real-time data (stock prices) | Do not cache or 1-5 seconds | Staleness is unacceptable or very costly |

### Pub/Sub Invalidation

When data changes, publish an invalidation message. All application instances subscribe and evict the corresponding cache entry. Works well with Redis pub/sub or a lightweight message bus. Eliminates cross-instance stale reads.

## Eviction Policies

When cache memory is full, the eviction policy determines which entry to remove.

| Policy | Evicts | Best For | Weakness |
|---|---|---|---|
| LRU (Least Recently Used) | Entry not accessed for the longest time | General purpose, default choice | Scan-resistant (one-time scans pollute cache) |
| LFU (Least Frequently Used) | Entry accessed the fewest times | Stable popularity distribution | Slow to adapt to changing access patterns |
| FIFO (First In, First Out) | Oldest entry by insertion time | Simple, predictable | Ignores access patterns entirely |
| Random | Random entry | Simple, avoids pathological cases | Not optimal for any specific pattern |
| TTL-based | Entries closest to expiration | Time-sensitive data | Requires TTL on all entries |
| Allkeys-LRU (Redis) | LRU across all keys | When all keys are cacheable | None — good default for Redis |
| Volatile-LRU (Redis) | LRU across keys with TTL set | Mix of persistent and cacheable keys | Only evicts keys with TTL |

**Default recommendation**: LRU (or allkeys-lru in Redis). Works well for most workloads. Switch to LFU if you observe cache pollution from infrequent bulk scans.

### Memory Budgeting

- Set `maxmemory` explicitly — never rely on default (unlimited growth)
- Monitor eviction rate — high eviction indicates undersized cache
- Target 80-90% hit ratio. Below 70% indicates cache is too small or access pattern is cache-unfriendly
- Size cache based on working set (actively accessed data), not total dataset

## Cache Failure Modes

### Cache Stampede (Thundering Herd)

A popular cache entry expires, and many concurrent requests simultaneously miss the cache and hit the database.

**Prevention**:
- **Locking**: First request acquires a lock, fetches from DB, populates cache. Others wait for lock release, then read from cache.
- **Probabilistic early expiration**: Each reader has a small random chance of refreshing the entry before TTL expires. Spreads refresh load.
- **Background refresh**: Separate process refreshes entries before expiration. Application never misses.

### Cache Penetration

Requests for keys that never exist in the database bypass the cache every time.

**Prevention**:
- **Cache negative results**: Store "not found" sentinel with short TTL (30-60 seconds)
- **Bloom filter**: Check a probabilistic filter before querying. If the filter says "definitely not present," skip the database call.
- **Input validation**: Reject obviously invalid keys before they reach cache or database.

### Cache Avalanche

Large number of cache entries expire simultaneously, causing a sudden flood of database requests.

**Prevention**:
- **Staggered TTLs**: Add random jitter to TTL values (e.g., base TTL ± 10-20%)
- **Multi-tier caching**: Tiers with different TTLs absorb different waves
- **Rate limiting on cache misses**: Limit concurrent database requests per cache miss path
- **Warm-up on deploy**: Pre-populate cache after application restart

## When NOT to Cache

| Scenario | Why Caching Hurts |
|---|---|
| Highly dynamic data (real-time prices, live scores) | Cache is stale before it is read |
| User-specific data with high cardinality | Cache size explodes, low hit ratio |
| Write-heavy with few reads | Invalidation overhead exceeds read savings |
| Security-sensitive data (PII, tokens) | Cache expands attack surface, harder to purge |
| Data with strict correctness requirements | Stale reads cause business logic errors |
| Simple fast queries on indexed data | Database response is already fast; cache adds complexity for minimal gain |

**Decision heuristic**: Cache when (read frequency × latency savings) > (invalidation complexity + staleness cost). If the equation does not clearly favor caching, do not cache.

## Cache Monitoring and Diagnostics

### Key Metrics

| Metric | Healthy Range | Action When Unhealthy |
|---|---|---|
| Hit ratio | > 80% (ideally > 90%) | If low: cache is too small, TTLs too short, or access pattern is cache-unfriendly |
| Eviction rate | Low and stable | If high: increase cache size or reduce TTL to expire entries before eviction |
| Memory utilization | 70-85% of maxmemory | If > 90%: increase cache size. If < 50%: may be over-provisioned. |
| Latency (p99) | < 1ms for Redis/Memcached | If high: check network, instance size, key size, connection pool |
| Connection count | Below max connections | If near max: increase pool size or reduce connection hold time |
| Key count | Stable or predictable growth | If unbounded growth: missing TTLs, key namespace pollution |

### Diagnosing Cache Performance Issues

| Symptom | Possible Cause | Investigation |
|---|---|---|
| Low hit ratio despite cache being large | Access pattern has high cardinality (many unique keys, each accessed once) | Analyze key access frequency distribution. If long-tail, caching may not help. |
| Hit ratio drops after deploy | New code paths bypass cache, or cache keys changed | Compare cache key patterns before and after deploy |
| Cache latency spikes | Hot key (many clients hitting same key), large values, network congestion | Check key size distribution, monitor per-key access patterns |
| Application slower despite high hit ratio | Cache overhead (serialization/deserialization) exceeds database query time | Profile the full request path; database may be fast enough without cache |

## Cache Architecture Patterns by Scale

| Scale | Architecture | Notes |
|---|---|---|
| Small (single server) | In-process cache (HashMap, Caffeine, lru-cache) | Zero network overhead, limited to single instance |
| Medium (few app instances) | Shared Redis instance | Simple, handles most workloads. Single point of failure. |
| Large (many app instances) | Redis Cluster or Memcached pool | Horizontal scaling, automatic failover |
| Very large (multi-region) | Regional cache clusters with async replication | Each region has local cache, cross-region sync for consistency |
| Hybrid | L1 in-process + L2 shared Redis | Lowest latency for hot keys, shared cache for warm keys |

**L1 + L2 pattern**: Application checks in-process cache first (microseconds). On miss, checks Redis (sub-millisecond network). On miss, queries database. In-process cache has very short TTL (seconds) or event-based invalidation to stay fresh.
