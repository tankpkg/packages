# Performance and Systems

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Spinellis on databases and tools; Stafford on IPC; Pepperdine on performance; Tank relational-db-mastery and clean-code skills

Covers: when performance work is justified, how to measure before changing, common system-level bottlenecks (databases, IPC, caches, logging), and how to estimate and operate under load.

## Operating Standard

Performance is a user-visible property: a feature is fast or slow because someone is waiting for it. Performance work that is not tied to a user-visible goal is decoration — it adds complexity, adds risk, and produces benchmarks nobody asked for. The first question on every performance task is "who is waiting for what, and how long is acceptable?"

Two failure modes dominate. First, optimization without measurement: rewriting a loop into a clever map-reduce because "it feels faster," then shipping a regression because the loop was already JIT-optimized and the new code has worse cache behavior. Second, optimization without scope: a 30% improvement in the wrong place buys nothing; a 5% improvement in the dominant bottleneck buys a lot. The professional move is to measure first, identify the dominant cost, and change the smallest thing that addresses it.

A coding agent's job in this domain is to refuse speculative optimization, to keep code clean enough that real bottlenecks are findable, to recognize the system-level patterns (N+1, fan-out, unbounded growth, cache invalidation) that dominate most performance problems, and to estimate honestly when asked.

## Quick Routing

| Situation | Principle to apply |
| --------- | ------------------ |
| About to optimize without a profile or benchmark | Principle 1: Measure before changing |
| About to micro-optimize a function | Principle 2: Algorithm and data structure first |
| Code makes a database/API call inside a loop | Principle 3: N+1 is the default performance bug |
| About to add a cache to "speed things up" | Principle 4: Caches are correctness liabilities |
| Logs are growing faster than feature usage | Principle 5: Verbose logs hide signal |
| Asked for an estimate | Principle 6: Estimates are ranges with assumptions |

## Principle 1: Measure before changing

State: do not optimize without a measurement that names the bottleneck. Without a measurement, you are guessing — and guessing has a 50% chance of making things worse.

### What goes wrong without it

The team rewrites a hot loop in C extension code to "make it faster." Two engineer-weeks later, benchmarks show a 3% improvement in synthetic tests and a 12% slowdown in real production traffic because the new code has worse cache locality on the hardware production actually runs on. The original code was already saturating the cache and the JIT had specialized it well; the rewrite undid both. The rollback is messy because the C extension has its own build pipeline.

### Anti-pattern

```python
# "I bet this is the slow part."
def process_orders(orders):
    return [enrich(o) for o in orders]

# Refactored to look faster, with no measurement:
import multiprocessing

def process_orders(orders):
    with multiprocessing.Pool(processes=8) as pool:
        return pool.map(enrich, orders)
```

The refactor adds process startup cost, pickling cost (if `enrich` returns large objects), and IPC overhead. For small batches, it's now 100x slower. For large batches, it might be faster — or not, depending on whether `enrich` does I/O (in which case threads or async would be better) or CPU work (in which case multiprocessing helps). Without a measurement, the author cannot say.

### Better approach

```python
import cProfile
import pstats

# Step 1: Profile a representative real workload.
def profile_real_load():
    orders = fetch_recent_orders(limit=10000)
    profiler = cProfile.Profile()
    profiler.enable()
    process_orders(orders)
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("cumulative")
    stats.print_stats(20)

# Output reveals (for example):
#   - 73% of time in `enrich` -> `external_api_lookup`  <-- the dominant cost
#   - 12% in JSON parsing
#   - 8% in database writes
#   - rest scattered

# Step 2: The dominant cost is API I/O, not CPU.
# Conclusion: multiprocessing would barely help; concurrent I/O (asyncio,
# threads, or batched API calls) would help a lot.

import asyncio
import aiohttp

async def enrich_batch_async(orders):
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[enrich_async(o, session) for o in orders])

def process_orders(orders):
    return asyncio.run(enrich_batch_async(orders))
```

The fix is targeted at the actual bottleneck (API I/O), uses the right concurrency model (async for I/O), and has a baseline to compare against (the profile). After shipping, a follow-up profile confirms the improvement and rules out regressions elsewhere.

### Why this wins

- The change addresses the real bottleneck, not the imagined one.
- The before/after comparison is concrete: a profile showing the new dominant cost.
- The team learns something useful for the next performance task (which functions actually dominate in real workloads).

### Why the alternative loses

- Speculative optimizations have a 50/50 chance of making things worse — and you won't know which until production tells you.
- The "optimized" code is harder to read and harder to refactor, so the cost is paid every time someone touches it.
- The team builds a culture of intuition-driven performance work, which compounds errors.

### When this principle yields

When the change is so cheap it is not worth a measurement (replacing `list(filter(...))` with a generator expression in code that is provably called rarely), eyeball judgment is fine. The test is whether the change costs something. If the change adds complexity, asks for a code review, or is hard to revert, it earns a measurement.

### Verification

Every performance PR includes a before/after measurement. The measurement uses real or representative workload, not a synthetic micro-benchmark. The change is rolled back if the production profile doesn't match the development profile.

## Principle 2: Algorithm and data structure beat micro-optimization

State: a O(N²) algorithm that runs in tight, micro-optimized inner loops is still O(N²). Choose the right complexity class first; optimize syntax later (if at all).

### What goes wrong without it

The team spends days hand-tuning a nested loop's branch prediction and SIMD-friendly data layout. The improvement is 30%. A teammate replaces the nested loop with a hash-map lookup, taking it from O(N²) to O(N). The improvement is 10000x. Two engineer-weeks of micro-optimization were unnecessary.

### Anti-pattern

```javascript
// "Find duplicate emails in a list of users."
function findDuplicates(users) {
  const duplicates = []
  for (let i = 0; i < users.length; i++) {
    for (let j = i + 1; j < users.length; j++) {
      if (users[i].email === users[j].email) {
        duplicates.push(users[i])
        break
      }
    }
  }
  return duplicates
}

// "Optimization": unroll loop, add branch prediction hints, use bitwise ops where possible.
```

The original is O(N²). Unrolling and bitwise tricks shave maybe 20%. For 100K users, that's still 5 billion iterations.

### Better approach

```javascript
function findDuplicates(users) {
  const seen = new Set()
  const duplicates = new Set()
  for (const user of users) {
    if (seen.has(user.email)) {
      duplicates.add(user)
    } else {
      seen.add(user.email)
    }
  }
  return [...duplicates]
}
```

O(N). For 100K users, 200K hash operations vs. 5 billion comparisons. No tricks, no unrolling, no SIMD — just the right data structure.

### Why this wins

- The improvement scales with input size. At 1K users, both versions are fast; at 100K, only the right algorithm finishes in reasonable time; at 1M, the wrong algorithm doesn't finish at all.
- The code is shorter and clearer, not more complex.
- Future performance work can focus on the next bottleneck instead of squeezing more out of this one.

### Why the alternative loses

- Micro-optimization on the wrong algorithm hits a ceiling fast. You can't unroll your way out of O(N²).
- Optimized-but-quadratic code looks fast enough on small inputs in development and breaks at scale in production.
- The complexity of the optimization (unrolling, bitwise tricks, SIMD) makes the code harder to read, maintain, and change later.

### When this principle yields

When the input is genuinely bounded and small (e.g., always exactly 8 elements, validated by the type system), a "worse" big-O can win on constant factors. The test is whether the input size is bounded, with the bound enforced — not just observed. If yes, micro-optimize. If no, fix the complexity class.

### Verification

For any function processing a collection, check the worst-case complexity. Anything quadratic or worse on a collection that can grow with users or data is a target for refactoring before any micro-optimization is considered.

## Principle 3: N+1 is the default performance bug

State: any time code calls a database, API, or external service inside a loop, you are probably making N+1 requests where you could be making 1. This is the most common production performance bug by orders of magnitude.

### What goes wrong without it

A page that loads in 50ms in development with 10 users in the database loads in 5 seconds in production with 10,000. The team blames "scaling," "infrastructure," or "the framework," and considers caches, CDNs, and read replicas. The actual bug is a loop that makes 10,000 database round-trips because the ORM lazily loaded a relation.

### Anti-pattern

```python
# In a Django view:
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, "orders.html", {"orders": orders})

# In the template:
{% for order in orders %}
  <li>{{ order.customer.name }} - {{ order.shipping_address.city }} - {{ order.line_items.count }} items</li>
{% endfor %}
```

Looks innocent. In production with 1000 orders per user, this generates:
- 1 query for orders
- 1000 queries for `order.customer` (one per order)
- 1000 queries for `order.shipping_address` (one per order)
- 1000 queries for `order.line_items.count` (one per order)

Total: 3001 database queries to render a page that should be 1 query.

### Better approach

```python
def order_list(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .select_related("customer", "shipping_address")  # JOIN in one query
        .annotate(line_item_count=Count("line_items"))    # COUNT in the same query
    )
    return render(request, "orders.html", {"orders": orders})

# In the template:
{% for order in orders %}
  <li>{{ order.customer.name }} - {{ order.shipping_address.city }} - {{ order.line_item_count }} items</li>
{% endfor %}
```

One query. The page renders in 50ms regardless of how many orders the user has (within reason — past 100K orders, pagination is the next concern).

### Why this wins

- Page latency drops 100x or more.
- Database load drops by the same factor, freeing capacity for other queries.
- The code is more explicit about what it needs from the database, which is easier to optimize further.

### Why the alternative loses

- N+1 patterns scale linearly with data. They look fine in development and slow to a crawl in production.
- Adding a cache to "fix" N+1 introduces stale-data problems without addressing the root cause.
- The team's mental model becomes "queries are free in dev but expensive in prod," which is a hard place to think clearly from.

### When this principle yields

When N is bounded and small (always 1 to 10), and the code is significantly clearer with separate queries, the cost is acceptable. The test is whether N can grow with users, data, or features. If yes, batch.

### Verification

A query log middleware in development counts queries per request. Any request making more than ~10 queries per page is a candidate for inspection. CI integration tests assert query counts on representative pages: `assertNumQueries(2)` is a real guard against N+1 regressions.

## Principle 4: Caches are correctness liabilities

State: a cache is not a free speedup. It is a deliberate decision to trade freshness for latency, and that trade has consequences for every reader of the cached data.

### What goes wrong without it

A team adds a cache to make a slow page fast. The cache works. Six months later, a customer reports that they updated their billing address, but the shipping label printed on their order has the old address. The cause is the cache: the order-creation flow read the address from a cache that hadn't expired yet. The bug is hard to reproduce (only happens within the cache TTL after an address change), and the fix requires invalidating the cache from a place that didn't know it existed.

### Anti-pattern

```javascript
// Original code, slow because it hits the database every time.
async function getUser(userId) {
  return await db.users.findById(userId)
}

// "Optimization": add a cache. No invalidation strategy.
const userCache = new Map()

async function getUser(userId) {
  if (userCache.has(userId)) {
    return userCache.get(userId)
  }
  const user = await db.users.findById(userId)
  userCache.set(userId, user)
  return user
}
```

Three hidden problems:
1. The cache never expires. A user's email change is invisible until the process restarts.
2. The cache is process-local. In a multi-instance deployment, each instance has its own stale view.
3. There is no invalidation. The code that updates the user has no way to tell the cache.

### Better approach

Decide every cache decision deliberately:

```javascript
// Question 1: What is the freshness contract?
//   "User data must reflect updates within 30 seconds."
// Question 2: Where does invalidation happen?
//   "User updates go through a single service; that service invalidates."
// Question 3: What is the cost of stale data?
//   "Wrong display name on a settings page is acceptable for 30s.
//    Wrong shipping address on order creation is not."

class UserCache {
  constructor({ store, ttlSeconds = 30 }) {
    this.store = store
    this.ttl = ttlSeconds
  }

  async get(userId) {
    const cached = await this.store.get(`user:${userId}`)
    if (cached) return JSON.parse(cached)
    const user = await db.users.findById(userId)
    await this.store.setex(`user:${userId}`, this.ttl, JSON.stringify(user))
    return user
  }

  async invalidate(userId) {
    await this.store.del(`user:${userId}`)
  }
}

// Order creation explicitly bypasses the cache for correctness-critical fields.
async function createOrder(userId, items) {
  const user = await db.users.findById(userId)  // direct, no cache
  const address = user.shippingAddress
  ...
}

// Display code uses the cache.
async function renderUserSettings(userId, userCache) {
  const user = await userCache.get(userId)
  return template.render({ user })
}

// User updates invalidate.
async function updateUser(userId, changes, userCache) {
  await db.users.update(userId, changes)
  await userCache.invalidate(userId)
}
```

The cache exists where staleness is acceptable, is bypassed where correctness matters, and has explicit invalidation. The TTL is a backstop, not the only safety mechanism.

### Why this wins

- Correctness-critical reads (order creation) are never stale.
- Display reads (settings page) are fast and acceptably fresh.
- Invalidation is explicit, so the staleness window has a known upper bound.
- The cache's freshness contract is documented in the class — a future maintainer can decide whether to cache something new by checking against that contract.

### Why the alternative loses

- An indefinite cache produces stale data forever. Users notice; trust drops.
- Process-local caches in multi-instance deployments disagree with each other; users see different data on different requests.
- Adding invalidation later is much harder than designing for it upfront — the producers of the data are scattered, and finding all of them is expensive.

### When this principle yields

When the cached data is genuinely immutable (the contents of a versioned blob keyed by content hash), no invalidation is needed because the data cannot change. The test is whether the data can ever change. If yes, design the invalidation. If no (and you can prove it), cache freely.

### Verification

For each cache in the codebase, the freshness contract is documented next to the cache definition. Each producer of the cached data either invalidates explicitly or has a written justification for why TTL is sufficient.

## Principle 5: Verbose logs hide signal

State: logs are not a free observability tool. Every log line has a cost (storage, ingestion, search latency) and a benefit (operator insight). Logs that don't help operators are noise that buries the logs that do.

### What goes wrong without it

Production has 50GB of logs per day. When an incident happens, the on-call engineer searches for "error" and gets 80,000 hits, most of them benign warnings logged on the happy path. The actual incident signal is buried in the noise. The mean time to diagnose grows from minutes to hours because the signal-to-noise ratio is too low.

### Anti-pattern

```python
def process_payment(order):
    log.info("entering process_payment")
    log.info(f"order: {order}")
    log.info(f"order id: {order.id}")
    log.info(f"order amount: {order.amount}")
    log.info(f"order user: {order.user_id}")
    log.info("looking up user")
    user = get_user(order.user_id)
    log.info(f"user: {user}")
    log.info("calling payment gateway")
    try:
        result = gateway.charge(user, order.amount)
        log.info(f"gateway result: {result}")
        log.info("payment succeeded")
        return result
    except Exception as e:
        log.info(f"exception: {e}")
        log.info("payment failed")
        raise
```

15 log lines per payment. At 100 payments per second, that's 1.5K log lines per second of mostly redundant information. The user PII is in there. The order amount is in there. The same data is logged at multiple levels. None of it answers the question an operator actually has during an incident.

### Better approach

```python
def process_payment(order):
    correlation_id = order.correlation_id or generate_correlation_id()

    try:
        result = gateway.charge(order.user_id, order.amount_cents)
    except CardDeclined as e:
        # Business outcome, info level, no PII.
        log.info(
            "payment.declined",
            order_id=order.id,
            user_id=order.user_id,
            amount_cents=order.amount_cents,
            decline_code=e.code,
            correlation_id=correlation_id,
        )
        raise
    except GatewayError as e:
        # Operator-relevant: warning, includes enough to diagnose without PII.
        log.warning(
            "payment.gateway_error",
            order_id=order.id,
            error_class=type(e).__name__,
            error_code=getattr(e, "code", None),
            retry_after_seconds=getattr(e, "retry_after", None),
            correlation_id=correlation_id,
        )
        raise

    # Success: structured event for metrics, no human-readable spam.
    log.info(
        "payment.succeeded",
        order_id=order.id,
        amount_cents=order.amount_cents,
        gateway_transaction_id=result.id,
        correlation_id=correlation_id,
    )
    return result
```

Three structured events: success, decline, gateway error. Each is at the right level. Each includes the operationally relevant fields without PII. Each has a correlation ID so a single transaction can be traced across services.

### Why this wins

- Log volume drops by 5-10x without losing any operator-relevant information.
- Structured logs are searchable, aggregable, and graphable. "How many declines per minute?" is one query.
- The correlation ID lets operators trace a transaction end-to-end during an incident.
- Sensitive data is not in the logs; compliance audits get much easier.

### Why the alternative loses

- Verbose logs increase storage cost and search latency. Operators waste time scrolling.
- Free-form log strings cannot be aggregated or counted. "Did we have more declines today?" requires manual log archaeology.
- PII in logs is a recurring compliance risk. The team will eventually have to redact and rebuild log retention.

### When this principle yields

For genuinely interactive debugging in a development environment, verbose logs are a useful tool — but those logs should not be in the production code. The test is whether the log line will run in production. If yes, it must serve an operational purpose.

### Verification

Production log volume scales with production events (transactions, requests), not linearly with code changes. Each log call is at the right level (info for normal events, warning for unusual ones, error for failures requiring action). PII fields are absent or explicitly masked.

## Principle 6: Estimates are ranges with assumptions

State: a single-number estimate is a guess dressed as a commitment. Honest estimates are ranges with named assumptions and named risks.

### What goes wrong without it

The team is asked "when can you ship this?" The senior engineer says "two days." Two weeks later, the work is still in progress because the database migration was harder than expected, the auth integration revealed an unrelated bug, and the QA team needs more time. The original "two days" was the optimistic case for the part the engineer had thought about; everything else was invisible.

### Anti-pattern

```
PM: "When can you have this feature ready?"
Engineer: "Two days."
PM: "Great, I'll tell the customer."

(Two weeks later)

PM: "I told the customer two days ago and they're escalating."
Engineer: "I hit some issues."
```

The original estimate was a guess. It became a commitment. The customer became unhappy. The engineer feels punished for being honest about the issues.

### Better approach

```
PM: "When can you have this feature ready?"
Engineer: "Best case 2 days, worst case 2 weeks. Most likely 4-7 days.

Assumptions that drive the optimistic case:
- The auth integration works as documented.
- The database migration is straightforward (no data backfill needed).
- QA can start review within 24 hours of dev-complete.

Risks that push toward the pessimistic case:
- The auth integration's documentation is from 2019 and may be stale.
- The migration may require backfill if any orders are in an in-flight state at deploy time.
- We have no second pair of eyes available for security review this week.

I'll know after the first day whether we're closer to optimistic or pessimistic.
What's the customer's actual deadline?"
```

The estimate is honest. The PM has the information needed to decide whether to commit, what to commit to, and what to escalate. The engineer is not on the hook for a number they didn't pick.

### Why this wins

- The PM can make a real commitment to the customer ("4-7 days, with a check-in after day 1") instead of a guess.
- Risk that materializes is not a surprise — it was named upfront.
- The engineer is not punished for being honest about uncertainty.
- The team's velocity improves over time because honest estimates inform planning, while guesses don't.

### Why the alternative loses

- Single-number estimates become commitments by accident.
- The engineer either pads (so the number is meaningless) or doesn't pad (so the number is wrong half the time).
- The team's estimation accuracy never improves because there's no feedback loop on what made the estimate wrong.

### When this principle yields

For genuinely tiny tasks where the variance is small (bumping a dependency version, fixing a typo), a single number is fine. The test is whether the work could plausibly take more than 2x the estimate. If yes, give a range and name the assumptions.

### Verification

Estimates are accompanied by assumptions and risks. After the work is done, the team retrospectively notes which assumptions held and which risks materialized — the goal is to calibrate, not to be right every time.

## Routing

Use `@tank/relational-db-mastery` for database-specific performance work: indexes, query plans, EXPLAIN ANALYZE, schema design, vacuum tuning.

Use `@tank/clean-code` when the performance problem is rooted in unclear structure that hides the actual hot path.

Use `@tank/security-review` when the performance change touches caching, auth, or data exposure — caches are common sources of authorization bugs.

Use `references/correctness-and-state.md` for the cache-as-state-management view of the same problem.

Use `references/conflict-resolution.md` when readability and performance pull in opposite directions and you need an explicit tiebreaker.
