# Scalability Patterns

Sources: Synthesized from Kleppmann (Designing Data-Intensive Applications), Vitillo (Understanding Distributed Systems), Newman (Building Microservices), Abbott & Fisher (The Art of Scalability)

Covers: scaling dimensions, load balancing, auto-scaling, content delivery, database scaling overview, stateless design, scaling anti-patterns.

## Scaling Dimensions

Three independent axes for scaling a system. Apply them in combination based on bottleneck analysis.

### X-Axis: Horizontal Duplication (Cloning)

Run multiple identical copies of the application behind a load balancer. Every instance handles the full range of requests.

| Aspect | Detail |
|---|---|
| What it solves | CPU/memory-bound request handling, redundancy |
| What it does NOT solve | Data-volume growth, complex query patterns |
| Requirement | Application must be stateless or externalize state |
| Scaling factor | Linear with instance count (minus coordination overhead) |
| When to apply first | Stateless web servers, API services, workers |

### Y-Axis: Functional Decomposition

Split the system into distinct services by function or business capability. Each service owns its data and scales independently.

| Aspect | Detail |
|---|---|
| What it solves | Independent scaling of different workloads, team autonomy |
| What it does NOT solve | Single-service bottlenecks, hot partitions in data |
| Requirement | Well-defined service boundaries, data ownership |
| Complexity cost | Distributed transactions, service communication, operational overhead |
| When to apply | Different components have vastly different resource profiles or change rates |

### Z-Axis: Data Partitioning

Split data across instances so each handles a subset. Requests route to the correct partition based on a key (user ID, region, tenant).

| Aspect | Detail |
|---|---|
| What it solves | Dataset exceeds single-node capacity, write throughput limits |
| What it does NOT solve | Compute-bound bottlenecks on individual requests |
| Requirement | A natural partition key with even distribution |
| Complexity cost | Cross-partition queries, rebalancing, operational complexity |
| When to apply | Single database instance at capacity despite optimization |

### Combining Axes

Most production systems combine all three. An e-commerce platform might:
- X-axis: 20 identical API server replicas behind a load balancer
- Y-axis: Separate services for catalog, orders, payments, notifications
- Z-axis: Orders database sharded by customer_id range

## Vertical vs Horizontal Scaling

| Factor | Vertical (Scale Up) | Horizontal (Scale Out) |
|---|---|---|
| Approach | Bigger machine (more CPU, RAM, faster disk) | More machines of the same size |
| Complexity | Low — no code changes, no distribution | Higher — needs load balancing, state management |
| Cost curve | Exponential (high-end hardware premium) | Linear (commodity hardware) |
| Ceiling | Physical hardware limits | Effectively unlimited |
| Downtime risk | Single point of failure, upgrade requires restart | Rolling upgrades, redundancy built in |
| Best for | Databases (up to a point), legacy apps, quick wins | Stateless services, web tiers, worker pools |

**Decision heuristic**: Scale vertically until the cost is unreasonable or the hardware ceiling approaches, then scale horizontally. Vertical scaling buys time with zero architectural change.

## Load Balancing

### Layer 4 vs Layer 7

| Property | Layer 4 (Transport) | Layer 7 (Application) |
|---|---|---|
| Operates on | TCP/UDP packets | HTTP requests, headers, URLs |
| Routing decisions | Source/destination IP and port | URL path, headers, cookies, content type |
| Performance | Higher throughput, lower latency | Slightly more overhead per request |
| TLS termination | Pass-through or terminate | Typically terminates TLS |
| Use case | High-throughput TCP, non-HTTP protocols | HTTP routing, A/B testing, canary, content-based |
| Examples | AWS NLB, HAProxy (TCP mode) | AWS ALB, Nginx, Envoy, HAProxy (HTTP mode) |

**Selection**: Use L4 for raw throughput or non-HTTP traffic. Use L7 when routing decisions depend on request content.

### Load Balancing Algorithms

| Algorithm | How It Works | Best For | Weakness |
|---|---|---|---|
| Round Robin | Rotates through servers sequentially | Uniform request cost, identical servers | Ignores server load and capacity |
| Weighted Round Robin | Rotates with proportional weights per server | Mixed server capacities | Requires manual weight configuration |
| Least Connections | Routes to server with fewest active connections | Variable request duration | May not reflect actual server CPU/memory load |
| Weighted Least Connections | Least connections adjusted by server weight | Mixed capacities + variable duration | Configuration complexity |
| IP Hash | Routes based on hash of client IP | Session affinity without sticky cookies | Uneven distribution with NAT, poor failover |
| Consistent Hashing | Hash ring assigns ranges to servers | Cache layers, stateful services | Requires virtual nodes for even distribution |
| Random | Randomly selects a server | Simple, surprisingly effective at scale | No intelligence about server state |

### Health Checking

| Check Type | What It Verifies | Interval |
|---|---|---|
| TCP connect | Port is open and accepting connections | 5-10 seconds |
| HTTP GET | Application responds with 2xx on health endpoint | 10-30 seconds |
| Deep health | Application and critical dependencies are healthy | 30-60 seconds |

Unhealthy threshold: Remove after 2-3 consecutive failures. Recovery threshold: Re-add after 2-3 consecutive successes. Avoid deep health checks at high frequency — a database blip should not instantly remove all servers.

### Session Persistence

| Method | How | Trade-off |
|---|---|---|
| No persistence (preferred) | Externalize state to Redis/database | Best distribution, highest resilience |
| Cookie-based | Load balancer inserts routing cookie | Uneven load if some sessions are heavier |
| IP-based | Route by client IP hash | Breaks behind NAT, mobile network changes |

**Default recommendation**: Externalize all session state. Session persistence is a crutch that hinders scaling and complicates failover.

## Auto-Scaling

### Reactive Scaling

Scale based on observed metrics crossing thresholds.

| Metric | Good For | Watch Out |
|---|---|---|
| CPU utilization | Compute-bound workloads | Lagging indicator, scale-up may be too slow |
| Request count / QPS | Traffic-driven services | Doesn't reflect per-request cost variation |
| Queue depth | Worker pools, async processors | Most responsive for queue-based architectures |
| Response latency (p99) | Latency-sensitive services | Can oscillate if threshold is too sensitive |
| Memory utilization | Memory-bound workloads | Slow to recover (GC-heavy apps) |
| Custom business metrics | Domain-specific load signals | Requires instrumentation |

### Scaling Configuration

| Parameter | Guideline |
|---|---|
| Scale-up threshold | 60-70% average CPU or equivalent metric |
| Scale-down threshold | 30-40% (set lower than scale-up to prevent flapping) |
| Cooldown period | 3-5 minutes after scale-up, 10-15 minutes after scale-down |
| Min instances | At least 2 for redundancy in production |
| Max instances | Set a hard cap to prevent cost runaway from traffic spikes or bugs |
| Warmup time | Account for JIT compilation, cache priming, connection pool setup |

### Predictive Scaling

Use historical patterns to pre-scale before expected load increases. Combine with reactive scaling as a safety net. Effective for systems with predictable traffic (business hours, batch jobs, seasonal events).

## Content Delivery Networks

### CDN Architecture

CDN edge servers cache content close to users, reducing latency and offloading origin servers.

| CDN Type | Behavior | Best For |
|---|---|---|
| Pull-based | Edge fetches from origin on first request, caches per TTL | Most web content, APIs with cache-friendly responses |
| Push-based | Origin proactively pushes content to edges | Large files, video, software updates |

### Cache-Control for CDN

| Header | Purpose | Example |
|---|---|---|
| `Cache-Control: public, max-age=3600` | CDN and browser cache for 1 hour | Static assets (CSS, JS, images) |
| `Cache-Control: s-maxage=300, max-age=0` | CDN caches 5 min, browser always revalidates | API responses with moderate staleness tolerance |
| `Cache-Control: private, no-store` | CDN must not cache, browser must not cache | User-specific data, sensitive content |
| `Surrogate-Control` | CDN-specific caching (not forwarded to browser) | Fine-grained CDN control |

### Origin Shielding

Place a caching layer between the CDN edge and the origin. All edge misses funnel through the shield, which deduplicates requests to the origin. Reduces origin load from N × edges to 1 × shield.

## Database Scaling Overview

Detailed strategies are in `references/data-layer.md`. Summary of scaling approaches:

| Strategy | When | Complexity |
|---|---|---|
| Connection pooling | Too many application connections saturating database | Low |
| Read replicas | Read-heavy workload saturating primary | Medium |
| Caching layer | Repeated identical queries | Medium |
| Vertical scaling | Single-node still viable, need headroom | Low |
| Partitioning (sharding) | Write volume or data size exceeds single node | High |
| Functional partitioning | Different tables have vastly different access patterns | Medium-High |

## Stateless Design

Statelessness is the prerequisite for horizontal scaling. A service is stateless when any instance can handle any request.

### Externalizing State

| State Type | Externalize To | Example |
|---|---|---|
| User sessions | Redis, database | Login tokens, shopping carts |
| File uploads | Object storage (S3, GCS) | User avatars, documents |
| Cached computations | Distributed cache (Redis, Memcached) | Query results, rendered templates |
| Coordination state | Distributed lock service (Redis, Zookeeper) | Leader election, distributed locks |

### Shared-Nothing Architecture

Each node operates independently with no shared memory or disk. Communication only through the network. Benefits: no contention, linear scaling, independent failure domains. Cost: data must be partitioned, coordination requires explicit messaging.

## Scaling Anti-Patterns

| Anti-Pattern | Why It Fails | Alternative |
|---|---|---|
| Scaling before measuring | Wastes money and adds complexity without evidence | Profile first, scale the actual bottleneck |
| Ignoring connection limits | Adding app instances without pooling exhausts database connections | Size connection pools, use PgBouncer or ProxySQL |
| Shared mutable state in memory | Cannot add instances without data inconsistency | Externalize to Redis or database |
| Synchronous call chains | Latency compounds, one slow service blocks the chain | Async messaging for non-critical paths |
| Scaling the wrong tier | Adding web servers when the database is the bottleneck | Measure end-to-end, identify the actual constraint |
| No graceful degradation | System crashes entirely instead of shedding load | Feature flags, load shedding, circuit breakers |
| Ignoring cold start | New instances serve traffic before warming up | Health checks with readiness gates, connection priming |
| Single region deployment | Latency for distant users, no geographic redundancy | Multi-region with data replication strategy |

## Scaling Readiness Checklist

Before scaling horizontally, verify:

- [ ] Application is stateless or state is externalized
- [ ] Health check endpoint exists (liveness + readiness)
- [ ] Configuration is environment-driven (not hardcoded)
- [ ] Logging and metrics are centralized (not local files)
- [ ] Database connection pooling is configured
- [ ] Graceful shutdown handles in-flight requests
- [ ] Deployment supports rolling updates
- [ ] Load balancer is configured with appropriate algorithm
- [ ] Auto-scaling policies have min, max, and cooldown set
- [ ] Monitoring alerts on scaling events and resource saturation

## Scaling Decision Workflow

Use this systematic approach when a system needs to handle more load.

### Step 1: Measure the Bottleneck

Before scaling anything, identify WHAT is saturated:

| Symptom | Likely Bottleneck | First Action |
|---|---|---|
| High CPU on application servers | Compute-bound processing | Profile hot code paths, optimize, then scale horizontally |
| High memory, frequent GC | Memory-bound, object churn | Reduce allocations, increase heap, then scale horizontally |
| High disk I/O on database | Query-bound or dataset exceeds memory | Optimize queries, add indexes, increase RAM, then replicas |
| Slow response from external API | Dependency latency | Cache responses, add circuit breaker, async where possible |
| Connection pool exhausted | Too many concurrent requests for pool size | Increase pool, add connection pooler, reduce query time |
| Request queue growing | More requests than processing capacity | Scale workers, add back-pressure, shed low-priority load |

### Step 2: Optimize Before Scaling

Scaling adds operational complexity. First, extract more from existing resources:
- **Caching**: Can you cache the hot path? (see `references/caching-strategies.md`)
- **Query optimization**: Is the database doing unnecessary work? (indexes, query rewrites)
- **Code optimization**: Is the application doing unnecessary computation? (profiling, algorithmic improvements)
- **Connection reuse**: Are connections being pooled effectively?

### Step 3: Scale the Bottleneck

Only after optimization, apply the appropriate scaling dimension:
- CPU/memory bottleneck on stateless services → X-axis (add instances)
- Different components need different resources → Y-axis (decompose)
- Data volume exceeds single node → Z-axis (partition)
- Vertical scaling still viable → Scale up first (simpler)

### Step 4: Verify and Monitor

After scaling, confirm the bottleneck is resolved and watch for it shifting to a different component. A system is only as fast as its slowest dependency.
