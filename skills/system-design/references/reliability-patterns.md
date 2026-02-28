# Reliability and Resilience Patterns

Sources: Synthesized from Nygard (Release It!), Vitillo (Understanding Distributed Systems), Beyer et al. (Site Reliability Engineering)

Covers: failure modes, circuit breakers, retry strategies, bulkheads, rate limiting, timeouts, health checks, failover, chaos engineering.

## Failure Modes in Distributed Systems

### Types of Failures

| Failure Type | Behavior | Example | Detection Difficulty |
|---|---|---|---|
| Crash failure | Process stops entirely | OOM kill, hardware failure, unhandled exception | Easy — no response, connection refused |
| Omission failure | Process fails to send or receive messages | Network packet loss, full queue dropping messages | Moderate — looks like slowness at first |
| Timing failure | Process responds outside expected time window | Garbage collection pause, disk I/O spike, network congestion | Hard — response is correct but too late |
| Byzantine failure | Process behaves arbitrarily (wrong results, corruption) | Software bugs, data corruption, compromised nodes | Very hard — system looks like it is working |

### Partial Failures

In a distributed system, some components can fail while others continue operating. This is fundamentally different from single-machine computing where failure is typically all-or-nothing. Design every inter-service interaction with the assumption that the remote end may be slow, unresponsive, or returning garbage.

### The Network Reality

Networks are unreliable, variable-latency, and can partition at any time. Build systems that handle:
- Packets lost, delayed, duplicated, or reordered
- Connections that hang indefinitely without timeout
- DNS resolution failures
- TLS handshake failures
- Load balancer returning errors during health check transitions

## Circuit Breaker Pattern

Prevent a failing dependency from consuming all resources and causing cascading failure. Modeled after electrical circuit breakers.

### States

| State | Behavior | Transition |
|---|---|---|
| Closed (normal) | Requests pass through, failures are counted | If failure count exceeds threshold within window → Open |
| Open (tripped) | All requests fail immediately without calling the dependency | After timeout period → Half-Open |
| Half-Open (testing) | A limited number of probe requests pass through | If probes succeed → Closed. If probes fail → Open. |

### Configuration Parameters

| Parameter | Typical Range | Guidance |
|---|---|---|
| Failure threshold | 5-50 failures | Lower for critical dependencies, higher for flaky ones |
| Failure window | 10-60 seconds | Window over which failures are counted |
| Open duration | 15-60 seconds | How long to wait before probing |
| Half-open max probes | 1-5 requests | Number of test requests before deciding |
| Failure criteria | HTTP 5xx, timeout, connection refused | Exclude client errors (4xx) from failure count |

### Fallback Strategies

When the circuit is open, instead of returning an error:

| Strategy | When to Use | Example |
|---|---|---|
| Cached response | Stale data is better than no data | Return last known product price |
| Default value | A sensible default exists | Return empty recommendations list |
| Degraded functionality | Feature can be disabled gracefully | Hide personalization, show generic content |
| Fail fast with message | No fallback makes sense | Return 503 with retry-after header |
| Queue for later | Work can be deferred | Queue email send for when service recovers |

### Circuit Breaker Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Single circuit for all endpoints | One bad endpoint trips circuit for healthy endpoints | Separate circuit per endpoint or operation |
| No monitoring on circuit state | Failures go unnoticed | Alert on state transitions, dashboard circuit health |
| Too sensitive threshold | Normal jitter trips circuit | Tune threshold to tolerate expected failure rate |
| No fallback | Open circuit returns raw error to user | Always define degraded behavior |

## Retry Strategies

### Retry Patterns

| Pattern | Behavior | Best For |
|---|---|---|
| Immediate retry | Retry instantly | Transient network glitches (rare) |
| Fixed delay | Wait constant time between retries | Simple, predictable |
| Exponential backoff | Double delay each retry (1s, 2s, 4s, 8s...) | Overloaded services, rate-limited APIs |
| Exponential backoff + jitter | Backoff plus random component | Prevents synchronized retry storms |
| Linear backoff | Increase delay linearly (1s, 2s, 3s, 4s...) | Moderate back-off without aggressive growth |

### Jitter Formulas

Without jitter, retries from many clients synchronize and create periodic load spikes.

| Jitter Type | Formula | Behavior |
|---|---|---|
| Full jitter | `random(0, base_delay * 2^attempt)` | Maximum spread, best for reducing thundering herd |
| Equal jitter | `base_delay * 2^attempt / 2 + random(0, base_delay * 2^attempt / 2)` | Guarantees minimum wait, plus random component |
| Decorrelated jitter | `min(cap, random(base, previous_delay * 3))` | Each retry independent of others |

### Retry Budgets

Limit the total percentage of requests that are retries. If more than 10-20% of requests are retries, the downstream is in trouble — more retries make it worse.

| Parameter | Guidance |
|---|---|
| Max retries per request | 2-3 (rarely more) |
| Retry budget (system-wide) | 10-20% of total requests |
| Non-retryable errors | 4xx client errors, business logic rejections |
| Retryable errors | 5xx server errors, timeouts, connection refused |

**Critical**: Retries are only safe when the operation is idempotent. A non-idempotent operation retried may cause duplicate side effects (double charges, duplicate orders).

## Bulkhead Pattern

Isolate components so that failure in one does not consume all shared resources and crash the entire system. Named after ship bulkheads that prevent a hull breach from sinking the whole vessel.

### Isolation Types

| Isolation Level | Mechanism | Granularity | Example |
|---|---|---|---|
| Thread pool isolation | Dedicated thread pool per dependency | Per-external-call | 20 threads for payment service, 10 for email service |
| Connection pool isolation | Separate connection pool per dependency | Per-external-call | 50 DB connections for reads, 20 for writes |
| Process isolation | Separate process per workload | Per-service | Critical path in one process, batch jobs in another |
| Semaphore isolation | Limit concurrent calls without dedicated threads | Per-operation | Max 10 concurrent calls to recommendation API |

### Sizing Bulkheads

| Factor | Guidance |
|---|---|
| Normal throughput | Size pool to handle normal load with headroom |
| Timeout × concurrency | Pool size ≥ (expected concurrent requests) × (p99 response time / average response time) |
| Failure impact | Critical dependencies get larger pools |
| Rejection behavior | When pool is full: fail fast, queue briefly, or shed load |

## Rate Limiting and Throttling

### Algorithms

| Algorithm | How It Works | Characteristic |
|---|---|---|
| Token bucket | Bucket fills at fixed rate, each request takes a token. Allows bursts up to bucket size. | Smooth average rate with configurable burst |
| Leaky bucket | Requests enter a fixed-size queue, processed at constant rate. | Strict constant output rate, no bursting |
| Fixed window | Count requests in fixed time windows (e.g., per minute). Reset at window boundary. | Simple but boundary spike problem (2x rate at window edges) |
| Sliding window log | Track timestamp of each request, count within sliding window. | Accurate but memory-intensive |
| Sliding window counter | Combine current and previous window counts weighted by overlap. | Good accuracy with low memory |

### Distributed Rate Limiting

Single-node rate limiting does not work when requests are spread across multiple application instances.

| Approach | How | Trade-off |
|---|---|---|
| Centralized counter (Redis) | Atomic increment in Redis with TTL | Accurate, but Redis is a dependency and latency added |
| Local rate limit + sync | Each instance keeps local count, periodically syncs | Less accurate, but no per-request external call |
| Token bucket in Redis | Lua script implements token bucket atomically | Precise, supports bursting, requires Redis |
| API gateway rate limiting | Gateway enforces limits before requests reach services | Centralized, simple, but limits apply at gateway level only |

### Rate Limit Response

Return HTTP 429 (Too Many Requests) with headers:
- `Retry-After`: Seconds until client can retry
- `X-RateLimit-Limit`: Total allowed requests in window
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Timestamp when window resets

## Timeouts and Deadlines

### Timeout Types

| Timeout | What It Bounds | Default Risk |
|---|---|---|
| Connection timeout | Time to establish TCP connection | Hanging on unreachable hosts |
| Read/response timeout | Time to receive response after sending request | Waiting indefinitely for slow responses |
| Request deadline | Total time budget for the entire operation including retries | Total user-facing latency unbounded |
| Idle timeout | Time a connection can be idle before closing | Connection pool exhaustion from idle connections |

### Timeout Configuration

| Service Type | Connection Timeout | Response Timeout | Guideline |
|---|---|---|---|
| Internal microservice | 1-3 seconds | 5-15 seconds | Services should respond fast; long timeouts hide problems |
| External third-party API | 3-5 seconds | 10-30 seconds | Less control, more variability |
| Database query | 1-2 seconds | 5-30 seconds (depends on query) | Short for OLTP, longer for analytics/reporting |
| Background job | N/A | Minutes-hours | Depends on job, but always set a maximum |

### Deadline Propagation

When service A calls B which calls C, propagate the remaining deadline:
- A has 10 second deadline, spends 2 seconds on local work, gives B 8 seconds
- B spends 1 second, gives C 7 seconds
- If C takes 8 seconds, B times out at 7 seconds, A returns error within its 10 second budget

Without propagation, each service adds its own full timeout, causing total latency to be sum of all timeouts.

## Health Checks and Failure Detection

### Health Check Types

| Check Type | What It Verifies | When to Fail |
|---|---|---|
| Liveness | Process is running and not deadlocked | Process is stuck, infinite loop, deadlock |
| Readiness | Process can accept and handle traffic | Dependencies unavailable, warming up, shutting down |
| Startup | Process has finished initialization | Loading config, building caches, connecting to DB |

### Deep vs Shallow Health Checks

| Depth | Checks | Response Time | Risk |
|---|---|---|---|
| Shallow | Process is running, port is open | Milliseconds | Misses dependency failures |
| Medium | Process + database connection + cache connection | Tens of milliseconds | Good balance |
| Deep | Process + all dependencies + business logic test | Hundreds of milliseconds | Cascading failure if dependency is flaky |

**Recommendation**: Liveness = shallow. Readiness = medium. Do not use deep checks for load balancer health — a flaky dependency will remove all instances.

### Graceful Shutdown

1. Stop accepting new requests (fail readiness check)
2. Complete in-flight requests (drain with timeout)
3. Close connections to dependencies
4. Exit process

Allow a drain period of 15-30 seconds. Kubernetes sends SIGTERM, waits `terminationGracePeriodSeconds`, then SIGKILL.

## Redundancy and Failover

### Deployment Topologies

| Pattern | Configuration | Failover Time | Cost | Data Consistency |
|---|---|---|---|---|
| Active-passive (cold standby) | Secondary offline, starts on failure | Minutes | Low | Potential data loss (replication lag) |
| Active-passive (warm standby) | Secondary running, receiving replication | Seconds-minutes | Medium | Minimal data loss |
| Active-passive (hot standby) | Secondary fully loaded, ready to serve | Seconds | Medium-high | Minimal data loss |
| Active-active | Both serving traffic simultaneously | Zero (already serving) | High | Conflict resolution required |

### Split-Brain Prevention

When two nodes both believe they are the leader:
- **Fencing tokens**: Include monotonically increasing token with writes. Storage rejects writes with stale tokens.
- **STONITH (Shoot The Other Node In The Head)**: Hard-kill the old leader via hardware (power off, IPMI).
- **Quorum-based election**: Require majority agreement before assuming leadership.

## Chaos Engineering Principles

### Approach

1. **Define steady state**: Normal system behavior in measurable terms (error rate, latency, throughput)
2. **Hypothesize**: System should maintain steady state even when [specific failure] occurs
3. **Inject failure**: Introduce the fault in a controlled manner
4. **Observe**: Measure whether steady state is maintained
5. **Learn and fix**: If steady state broke, fix the weakness before it happens in production

### Common Experiments

| Experiment | What It Tests |
|---|---|
| Kill a service instance | Auto-restart, load balancer failover, redundancy |
| Inject network latency | Timeout configuration, circuit breakers |
| Fail a database | Failover, read replica promotion, cache resilience |
| Exhaust disk space | Monitoring alerts, log rotation, graceful degradation |
| DNS failure | Service discovery resilience, cached DNS behavior |
| Clock skew | Time-dependent logic, certificate validation, TTL behavior |

### Safety Guardrails

- Start in non-production environments
- Use a small blast radius (single instance, one availability zone)
- Have a kill switch to stop the experiment immediately
- Run during business hours when the team is available
- Gradually increase scope as confidence grows
