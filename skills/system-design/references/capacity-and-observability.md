# Capacity Planning and Observability

Sources: Synthesized from Beyer et al. (Site Reliability Engineering), Nygard (Release It!), Kleppmann (Designing Data-Intensive Applications)

Covers: back-of-envelope estimation, latency reference numbers, SLOs/SLIs/SLAs, bottleneck analysis, monitoring strategy, distributed tracing, alerting design, capacity planning.

## Back-of-Envelope Estimation

Quick order-of-magnitude calculations to validate or reject a design before building it. The goal is not precision — it is to determine if an approach is in the right ballpark.

### Estimation Framework

For any system, work through this sequence:

1. **Users**: Total registered → daily active users (DAU) → concurrent users
2. **Requests**: Actions per user per day → total daily requests → peak QPS
3. **Storage**: Data per action × actions per day × retention period
4. **Bandwidth**: Average request/response size × QPS
5. **Compute**: Processing time per request × QPS → CPU/memory requirements

### Reference Numbers for Estimation

| Quantity | Approximate Value | Useful For |
|---|---|---|
| Seconds in a day | ~86,400 (~100K for estimation) | Converting daily totals to per-second rates |
| Seconds in a month | ~2.5 million | Storage growth calculations |
| Seconds in a year | ~31.5 million (~30M for estimation) | Annual capacity planning |
| 1 million requests/day | ~12 QPS | Converting daily to QPS |
| 1 billion requests/day | ~12,000 QPS | Large-scale QPS estimation |

### Data Size References

| Unit | Size | Example |
|---|---|---|
| 1 KB | 1,000 bytes | Short text field, small JSON payload |
| 1 MB | 1,000 KB | High-res photo, small audio clip |
| 1 GB | 1,000 MB | 1 hour of HD video, large database backup |
| 1 TB | 1,000 GB | Large database, years of application logs |
| 1 PB | 1,000 TB | Enterprise data warehouse, major platform analytics |

### Powers of Two Quick Reference

| Power | Value | Rounded |
|---|---|---|
| 2^10 | 1,024 | ~1 thousand |
| 2^20 | 1,048,576 | ~1 million |
| 2^30 | 1,073,741,824 | ~1 billion |
| 2^40 | ~1.1 trillion | ~1 trillion |

### Estimation Example: URL Shortener

- 100M new URLs/month → ~40 writes/sec, peak ~80/sec
- 10:1 read:write ratio → ~400 reads/sec, peak ~800/sec
- Average URL: 500 bytes × 100M/month × 12 months × 5 years = ~300 GB total storage
- Conclusion: Single PostgreSQL instance with read replicas handles this comfortably

## Latency Reference Numbers

Approximate latencies for common operations. Use these to reason about where time is spent in a system.

| Operation | Approximate Latency | Implication |
|---|---|---|
| L1 cache reference | 1 ns | CPU-bound work is very fast |
| L2 cache reference | 4 ns | Still extremely fast |
| Main memory (RAM) reference | 100 ns | In-memory data structures are fast |
| SSD random read | 16 μs | SSD is ~100x slower than RAM |
| SSD sequential read (1 MB) | 50 μs | Sequential SSD is fast for bulk reads |
| HDD random read | 2-10 ms | HDD is ~1000x slower than SSD random |
| Network round-trip (same datacenter) | 0.5 ms | Network is fast within a datacenter |
| Network round-trip (same region, different AZ) | 1-2 ms | Cross-AZ adds latency |
| Network round-trip (cross-region, same continent) | 20-50 ms | Significant latency for synchronous calls |
| Network round-trip (cross-continent) | 100-200 ms | Too slow for synchronous call chains |
| TLS handshake | 2-10 ms | Connection reuse is critical |
| DNS resolution | 1-50 ms | Cache DNS, pre-resolve |
| Database query (simple indexed) | 1-5 ms | Fast if query is optimized |
| Database query (complex join) | 10-100 ms | Optimize or cache results |
| Redis GET | 0.1-0.5 ms | Near-zero latency for cached data |

### Practical Implications

| Design Decision | Latency Insight |
|---|---|
| Keep synchronous call chains short | Each hop adds network latency + processing time |
| Cache aggressively in the same datacenter | Redis (0.5ms) vs cross-region DB call (50ms) = 100x faster |
| Avoid cross-region synchronous calls | 100-200ms per call destroys user experience in chains |
| Use connection pooling | TLS handshake (5ms) × new connections is expensive |
| Prefer SSD for databases | Random read: SSD 16μs vs HDD 5ms = 300x faster |

## SLOs, SLIs, and SLAs

### Definitions

| Term | What | Who Defines | Example |
|---|---|---|---|
| SLI (Service Level Indicator) | A quantitative metric measuring service behavior | Engineering team | p99 latency, error rate, availability |
| SLO (Service Level Objective) | A target value for an SLI | Engineering + product team | p99 latency < 300ms, 99.9% availability |
| SLA (Service Level Agreement) | A contract with consequences for missing SLOs | Business + legal | 99.9% uptime or service credits apply |

### Common SLIs by Service Type

| Service Type | Key SLIs |
|---|---|
| Request-serving (API, web) | Availability, latency (p50, p95, p99), error rate |
| Data processing (pipeline, ETL) | Freshness (age of latest output), throughput, completeness |
| Storage system | Durability, availability, latency |
| Streaming (Kafka, events) | End-to-end latency, throughput, consumer lag |

### Choosing SLO Targets

| Target | Downtime per Year | Typical Use |
|---|---|---|
| 99% | 3.65 days | Internal tools, batch systems |
| 99.9% | 8.77 hours | Standard web services |
| 99.95% | 4.38 hours | Business-critical APIs |
| 99.99% | 52.6 minutes | Payment systems, core infrastructure |
| 99.999% | 5.26 minutes | Rarely achievable; life-critical systems |

**Guidance**: Choose the loosest SLO your users will accept. Higher availability is exponentially more expensive. Going from 99.9% to 99.99% may require multi-region active-active deployment, automated failover, and extensive testing.

### Error Budgets

Error budget = 100% - SLO target. If your SLO is 99.9%, your error budget is 0.1%.

| Budget Status | Action |
|---|---|
| Budget remaining | Continue shipping features at normal pace |
| Budget nearly exhausted | Slow feature work, prioritize reliability |
| Budget exceeded | Freeze feature releases, focus entirely on reliability |

## Bottleneck Analysis

### Systematic Approach

1. **Identify**: Which resource is saturated? (CPU, memory, disk I/O, network, database connections, external dependency)
2. **Measure**: Quantify the bottleneck (utilization %, queue depth, response time)
3. **Hypothesize**: What would improve throughput? (more resources, optimization, caching, async)
4. **Improve**: Apply the smallest change that addresses the bottleneck
5. **Re-measure**: Verify improvement. The bottleneck may shift elsewhere.

### Amdahl's Law Applied

If 80% of a request can be parallelized and 20% is sequential, maximum speedup is 5x regardless of how many workers you add. Identify the sequential portion and optimize it, or redesign to reduce it.

| Sequential Portion | Maximum Speedup | Implication |
|---|---|---|
| 50% | 2x | Parallelism has limited value |
| 20% | 5x | Good candidate for scaling |
| 10% | 10x | Excellent parallelization potential |
| 5% | 20x | Near-linear scaling achievable |

### Common Bottlenecks and Fixes

| Bottleneck | Symptom | Fix |
|---|---|---|
| Database queries | High DB CPU, slow queries in logs | Optimize queries, add indexes, read replicas |
| Single database writer | Write throughput plateau | Write-behind cache, sharding, async writes |
| External API calls | High latency, timeouts | Cache responses, circuit breaker, async where possible |
| Connection pool exhausted | Timeouts waiting for connection | Increase pool size, reduce query time, add connection pooling proxy |
| CPU saturation | High CPU%, increased latency under load | Optimize hot code paths, scale horizontally |
| Memory pressure | Frequent GC, swapping | Reduce object allocation, increase heap, scale horizontally |
| Network bandwidth | Throughput plateau, packet loss | Compress payloads, CDN for static content, increase bandwidth |

## Monitoring Strategy

### The Three Pillars

| Pillar | What | Strength | Tool Examples |
|---|---|---|---|
| Metrics | Numeric measurements over time (counters, gauges, histograms) | Efficient storage, alerting, dashboards, trend analysis | Prometheus, Datadog, CloudWatch |
| Logs | Structured or unstructured text records of events | Detailed context for debugging specific incidents | ELK stack, Loki, CloudWatch Logs |
| Traces | Request path across services with timing | End-to-end latency debugging, dependency mapping | Jaeger, Zipkin, Datadog APT, Tempo |

### RED Method (for Request-Driven Services)

| Metric | What | Alert When |
|---|---|---|
| **R**ate | Requests per second | Sudden drop (possible outage) or spike (possible attack/incident) |
| **E**rrors | Error rate (percentage of requests failing) | Exceeds SLO error budget burn rate |
| **D**uration | Latency distribution (p50, p95, p99) | p99 exceeds SLO target |

### USE Method (for Resources)

| Metric | What | Alert When |
|---|---|---|
| **U**tilization | Percentage of resource capacity in use | Approaches saturation (>80% sustained) |
| **S**aturation | Amount of queued work waiting for the resource | Queue is growing (resource cannot keep up) |
| **E**rrors | Count of error events on the resource | Non-zero hardware errors, connection failures |

### What to Monitor at Each Layer

| Layer | Key Metrics |
|---|---|
| Infrastructure | CPU, memory, disk I/O, network I/O, instance count |
| Application | Request rate, error rate, latency (RED), active connections, thread pool utilization |
| Business | Sign-ups, orders, payments, conversion rate, revenue per minute |
| Dependencies | External API latency/errors, database query time, cache hit ratio |

## Distributed Tracing

### Core Concepts

| Concept | Definition |
|---|---|
| Trace | The full journey of a request across all services |
| Span | A single unit of work within a trace (one service call, one DB query) |
| Trace ID | Unique identifier propagated across all services for correlation |
| Parent span ID | Links child spans to their parent, forming a tree |
| Baggage | Key-value metadata propagated through the trace (user ID, tenant) |

### Trace Propagation

Every outbound request must include the trace context (trace ID, span ID) in headers. Standard: W3C Trace Context (`traceparent` header) or B3 propagation.

### Sampling Strategies

| Strategy | How | Trade-off |
|---|---|---|
| Head-based | Decide at trace start whether to sample (e.g., 1% of traces) | Simple, low overhead. May miss rare errors. |
| Tail-based | Collect all spans, decide after trace completes whether to keep | Captures all errors/slow traces. Higher resource cost. |
| Error-biased | Always sample traces with errors, probabilistic for success | Good error visibility with manageable volume. |
| Adaptive | Adjust sampling rate based on traffic volume | Consistent trace volume regardless of traffic. |

**Recommendation**: Start with head-based sampling (1-10%). Add tail-based or error-biased when debugging requires capturing all failures.

## Alerting Design

### Symptom-Based vs Cause-Based Alerts

| Approach | Example | Effectiveness |
|---|---|---|
| Symptom-based (preferred) | "Error rate exceeds 1% for 5 minutes" | Catches problems regardless of cause |
| Cause-based | "Database CPU above 90%" | May not correlate with user impact, causes alert fatigue |

**Rule**: Alert on symptoms (user-visible impact), investigate causes in dashboards.

### Alert Severity Levels

| Severity | Response | Example |
|---|---|---|
| Critical (page) | Immediate human response required, 24/7 | Service down, data loss risk, SLO breach imminent |
| Warning | Investigate during business hours | Elevated error rate, approaching capacity, degraded performance |
| Informational | Review in next planning cycle | Scaling event, certificate expiring in 30 days, new error pattern |

### Preventing Alert Fatigue

| Technique | How |
|---|---|
| Alert on SLO burn rate | Alert when consuming error budget faster than sustainable |
| Multi-window alerts | Alert only when short window (5 min) AND medium window (1 hour) both trigger |
| Minimum duration | Require condition to persist for 2-5 minutes before firing |
| Deduplication | Group related alerts into one incident |
| Runbook links | Every alert has a link to investigation steps |
| Regular alert review | Quarterly review: silence alerts nobody acts on, tune noisy ones |

### Multi-Burn-Rate Alerting

Instead of static thresholds, alert when the SLO error budget is being consumed too fast.

| Window | Burn Rate | Meaning | Severity |
|---|---|---|---|
| 5 minutes | 14.4x | Budget exhausted in ~1 hour | Critical — page immediately |
| 30 minutes | 6x | Budget exhausted in ~6 hours | Warning — investigate soon |
| 6 hours | 1x | Budget exhausted in ~30 days (normal pace) | No alert — this is expected |

## Capacity Planning

### Growth Estimation

| Method | How | Accuracy |
|---|---|---|
| Linear extrapolation | Project current growth rate forward | Good for stable, mature products |
| Exponential modeling | Fit growth curve to historical data | Better for rapidly growing products |
| Business-driven | Planned launches, marketing campaigns, seasonal events | Most accurate for known events |
| Headroom percentage | Maintain N% headroom above current peak | Simple, defensive |

### Headroom Guidelines

| Environment | Recommended Headroom | Rationale |
|---|---|---|
| Stateless application tier | 30-50% above peak | Absorb traffic spikes, rolling deploys |
| Database | 40-60% above peak | Scaling database is slow and disruptive |
| Cache | 20-30% above working set | Eviction under memory pressure degrades hit ratio |
| Queue/messaging | 50-100% above peak throughput | Absorb burst without back-pressure |

### Load Testing

| Type | What It Tests | When |
|---|---|---|
| Load test | System behavior at expected peak load | Before launch, after major changes |
| Stress test | System behavior beyond expected peak | Identify breaking point and failure mode |
| Soak test | System behavior under sustained load over time | Detect memory leaks, resource exhaustion, degradation |
| Spike test | System response to sudden traffic surge | Validate auto-scaling, back-pressure mechanisms |

### Cost Optimization

| Strategy | How | Savings Potential |
|---|---|---|
| Right-sizing | Match instance size to actual resource usage | 20-40% |
| Reserved/committed use | Pre-purchase capacity at discount for predictable baseline | 30-60% |
| Spot/preemptible instances | Use interruptible instances for fault-tolerant workloads | 60-90% |
| Auto-scaling | Scale down during off-peak hours | 20-50% |
| Caching | Reduce database and compute costs by serving from cache | Variable |
| Storage tiering | Move cold data to cheaper storage classes | 30-70% for storage costs |
