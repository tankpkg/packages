# Correctness and State

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Dahan on shared state; Winder on message passing; Allison on floating point; Tank security-review and clean-code skills

Covers: state management, concurrency, error classification, money and other exact values, operational visibility, and making invalid states unrepresentable.

## Operating Standard

Correctness is not "the test passes once on the happy path." It is the system preserving its intended behavior under normal use, edge cases, partial failures, retries, concurrency, and the inputs the original author did not imagine.

State is where correctness goes to die. Most production bugs that survive code review are state bugs: a shared variable written by two callers, a cache that returns stale data, a payment status that can be both "captured" and "refunded" at the same time, a date treated as UTC by half the code and local time by the other half.

A coding agent's job in this domain is to push state to its smallest scope, model lifecycles as explicit states with explicit transitions, and treat every external input as adversarial until parsed and validated. When in doubt, prefer designs where invalid states cannot be expressed at all, then prefer designs where invalid states fail loudly, then accept designs where invalid states only fail late.

## Quick Routing

| Situation | Principle to apply |
| --------- | ------------------ |
| Multiple callers read or write the same in-memory object | Principle 1: Beware shared mutable state |
| You see `is_paid`, `is_refunded`, `is_voided` as booleans on the same object | Principle 2: Model lifecycles as states |
| Money or counts use `float` or `double` | Principle 3: Floating point is not money |
| `try { ... } catch (e) {}` with no logging | Principle 4: Distinguish business from technical failures |
| Behavior depends on flags, queues, jobs, or caches with no observability | Principle 5: Make invisible things visible |
| A function accepts inputs that should never be valid | Principle 6: Make invalid states unrepresentable |

## Principle 1: Beware shared mutable state

State: shared mutable state is the largest single source of "works on my machine, fails in production" bugs. Prefer ownership, immutability, or message passing.

### What goes wrong without it

Tests pass when run serially because there is no concurrency. Production runs many requests in parallel, and the same global is now a race condition. The bug appears under load, on a Tuesday, three weeks after the change shipped, and the original author is on vacation.

### Anti-pattern

```python
# A "simple" rate limiter, used by the auth middleware:
REQUEST_COUNTS = {}  # ip -> count

def check_rate_limit(ip):
    REQUEST_COUNTS[ip] = REQUEST_COUNTS.get(ip, 0) + 1
    if REQUEST_COUNTS[ip] > 100:
        raise RateLimitExceeded()
```

Three problems hide in four lines: the dict is mutated by every worker without a lock, the count never decays so legitimate users are eventually banned forever, and the dict grows unbounded so memory leaks until the process restarts. Tests pass because the test suite makes 5 requests serially. Production makes 50,000 requests in parallel.

### Better approach

```python
# Scoped to a single request, with explicit lifetime and explicit ownership:
class RateLimiter:
    def __init__(self, store, window_seconds=60, max_requests=100):
        self.store = store        # e.g., Redis with EXPIRE
        self.window = window_seconds
        self.limit = max_requests

    def check(self, ip):
        key = f"ratelimit:{ip}"
        count = self.store.incr(key)
        if count == 1:
            self.store.expire(key, self.window)
        if count > self.limit:
            raise RateLimitExceeded(ip=ip, count=count, window=self.window)
```

State now lives in a store with explicit semantics: atomic `incr`, automatic expiry, bounded memory, and a clear owner. The behavior is testable against a real store (or a fake that honors the same contract).

### Why this wins

- Concurrency is the store's job, not the application's. Most stores have spent years getting this right.
- The window is explicit. Old IPs disappear automatically.
- Memory is bounded. The system survives a flood without a process restart.
- Tests using a real store (or a contract-honoring fake) catch concurrency bugs that serial unit tests miss.

### Why the alternative loses

- The original code is a denial-of-service waiting for a load test that nobody runs.
- The mutation is invisible at the call site. A reviewer cannot tell the function has shared state.
- "Add a lock" is the wrong fix — a lock makes the function correct under concurrency but does not solve unbounded memory or absent expiry.

### When this principle yields

When the state genuinely is process-local and read-only (a parsed config loaded once at startup), or when a high-performance hot path needs a careful per-thread cache and the team is willing to write and review the concurrency primitives. Both cases require a written justification, not "I'll just add a global."

### Verification

A load test that issues concurrent requests and verifies both the rate limit and the memory bound. If the system cannot be load tested, a code review explicitly checks every global and asks: who else writes here?

## Principle 2: Model lifecycles as states, not booleans

State: when an entity has a lifecycle (orders, payments, jobs, sessions), represent it as an explicit state with explicit transitions. Booleans for `is_paid`, `is_refunded`, `is_voided` invite impossible combinations.

### What goes wrong without it

Three booleans means eight combinations. At least three of those combinations are impossible in the business domain ("paid AND refunded AND voided"), but the type system and the database happily accept them. Eventually a bug or a manual data fix produces an impossible row, and downstream code that assumed sanity does the wrong thing.

### Anti-pattern

```typescript
interface Payment {
  id: string
  amount: number
  isAuthorized: boolean
  isCaptured: boolean
  isRefunded: boolean
  isVoided: boolean
}

// Spread across the codebase:
function refund(p: Payment): void {
  if (p.isCaptured && !p.isRefunded) {
    gateway.refund(p.id)
    p.isRefunded = true
  }
}

function void_(p: Payment): void {
  if (p.isAuthorized && !p.isCaptured) {
    gateway.void(p.id)
    p.isVoided = true
  }
}
```

Question for the reader: what should happen if `isCaptured && isVoided` are both true? The code does not say. The database accepts it. A retry storm or a race condition between `capture` and `void` can produce it. Reconciliation breaks. The accountants spend a week tracing one transaction.

### Better approach

```typescript
type PaymentStatus =
  | { kind: "authorized"; authorizedAt: Date }
  | { kind: "captured"; capturedAt: Date }
  | { kind: "refunded"; capturedAt: Date; refundedAt: Date }
  | { kind: "voided"; voidedAt: Date }

interface Payment {
  id: string
  amount: number
  status: PaymentStatus
}

function refund(p: Payment): Payment {
  if (p.status.kind !== "captured") {
    throw new InvalidTransition(`cannot refund payment in state ${p.status.kind}`)
  }
  gateway.refund(p.id)
  return { ...p, status: { kind: "refunded", capturedAt: p.status.capturedAt, refundedAt: new Date() } }
}

function void_(p: Payment): Payment {
  if (p.status.kind !== "authorized") {
    throw new InvalidTransition(`cannot void payment in state ${p.status.kind}`)
  }
  gateway.void(p.id)
  return { ...p, status: { kind: "voided", voidedAt: new Date() } }
}
```

Three things change: `Payment` cannot be in two states at once, transitions are explicit and validated, and the type system refuses to let a `refunded` payment also claim to be `voided`.

### Why this wins

- Impossible states are unrepresentable. The bug class disappears.
- Reading any function that branches on `status.kind` forces the developer to handle every case (or have the compiler complain).
- Reconciliation becomes provable: one row has one status, with timestamps for the transitions that produced it.

### Why the alternative loses

- The boolean version requires every reader to know the implicit rules ("if isCaptured then isAuthorized must also be true"). New developers do not know.
- Bug fixes for impossible combinations turn into business logic ("if both flags are true, treat it as refunded") that calcifies over years.
- Database invariants become application code that gets re-implemented per feature.

### When this principle yields

When the entity genuinely has independent flags (a user might have `email_verified` and `mfa_enabled` independently — neither implies the other), they are real booleans, not a hidden state machine. The test is whether all combinations are valid in the business domain. If yes, booleans are honest.

### Verification

A test for each invalid transition that asserts the system refuses it. A schema check (database constraint or type system) that prevents impossible combinations from being stored at all.

## Principle 3: Floating point is not money

State: never use binary floating point for monetary amounts, exact counts, identifiers, or any value where decimal precision is contractually required.

### What goes wrong without it

`0.1 + 0.2 === 0.30000000000000004`. A cart of three $0.10 items priced at $0.30 should round-trip exactly. Stored as `float`, it does not. The bug surfaces as a one-cent discrepancy on a customer invoice, which surfaces as a refund request, which surfaces as an angry email to support. The fix is not "round at display time" — by then the wrong number has already been written to a ledger.

### Anti-pattern

```javascript
function calculateOrderTotal(items, taxRate) {
  let subtotal = 0
  for (const item of items) {
    subtotal += item.priceUSD * item.quantity   // float math
  }
  const tax = subtotal * taxRate                 // more float math
  return subtotal + tax                           // even more
}

// Caller stores result in the database:
const total = calculateOrderTotal(cart, 0.0875)
db.orders.insert({ ..., total })
```

Each multiplication and addition introduces a tiny rounding error. By the time the total is computed, it might be `127.4500000000001` instead of `127.45`. Stored as a float, the database happily accepts it. The next reconciliation run flags it as a mismatch. Manual cleanup follows.

### Better approach

```javascript
// Use integer minor units (cents) end-to-end:
function calculateOrderTotalCents(items, taxBasisPoints) {
  let subtotalCents = 0
  for (const item of items) {
    subtotalCents += item.priceCents * item.quantity   // integer math
  }
  // taxBasisPoints is e.g. 875 for 8.75%, scaled by 10000
  const taxCents = Math.round((subtotalCents * taxBasisPoints) / 10000)
  return { subtotalCents, taxCents, totalCents: subtotalCents + taxCents }
}

const result = calculateOrderTotalCents(cart, 875)
db.orders.insert({ ..., totalCents: result.totalCents })
// Display layer formats: $127.45
```

Or use a decimal library (`Decimal` in Python, `BigDecimal` in Java, `decimal.js` in Node) when the domain requires arbitrary precision. The principle is the same: keep money as exact representation, round only at boundaries with explicit rules.

### Why this wins

- Arithmetic is exact. `0.10 + 0.10 + 0.10` rounds to `0.30` exactly because it is computed as `10 + 10 + 10 = 30`.
- Reconciliation can prove that the sum of line items equals the total, byte-for-byte.
- The rounding rule is one explicit operation at the tax boundary, not a thousand implicit roundings throughout the code.

### Why the alternative loses

- Float arithmetic is non-associative. `(a + b) + c` is not always `a + (b + c)` for floats. Reordering loops can change results.
- "Round at display time" only hides the bug from users, not from accounting systems and audit logs.
- Different float representations on different platforms (or different languages calling the same data) produce different totals from the same inputs.

### When this principle yields

When the value is genuinely a measurement with inherent imprecision (a sensor reading, a percentage with no audit requirement, a probabilistic score), float is appropriate. The test is whether someone, somewhere, depends on the value being exact. For money, the answer is always yes.

### Verification

A test for the canonical bad case: `0.1 + 0.2`. If your code's representation passes through the test as exactly `0.3` (or its integer/decimal equivalent), the representation is correct. Boundary tests for tax, discount, and currency conversion should compare exact strings or integer cents, not float-with-tolerance.

## Principle 4: Distinguish business failures from technical failures

State: a declined card is not the same kind of event as a database timeout. Conflating them produces the wrong UX, the wrong retries, the wrong alerts, and the wrong incident response.

### What goes wrong without it

Everything becomes a 500. Users see "something went wrong" for both "your card was declined, please try a different one" and "our database is on fire." Operators get paged for legitimate user actions. Retries fire on declined cards (which makes nothing better and sometimes triggers fraud rules). On-call engineers waste time on non-incidents because the signal is buried in noise.

### Anti-pattern

```python
def charge_user(user_id, amount_cents):
    try:
        result = payment_gateway.charge(user_id, amount_cents)
        return result
    except Exception as e:
        log.error("payment failed", error=str(e))
        return None  # caller has no idea what happened
```

Three things go wrong here. The exception type is lost (was it a network timeout, a 4xx response, a card decline?). The caller cannot distinguish "retry might help" from "retry will not help." The error log hides the difference between an outage (operator concern) and a card decline (user concern, not an operator concern).

### Better approach

```python
class PaymentResult:
    pass

class PaymentSucceeded(PaymentResult):
    def __init__(self, transaction_id):
        self.transaction_id = transaction_id

class PaymentDeclined(PaymentResult):
    """Business outcome. Not retryable. User should try a different card."""
    def __init__(self, decline_code, decline_message):
        self.decline_code = decline_code
        self.decline_message = decline_message

class PaymentTemporarilyUnavailable(PaymentResult):
    """Technical failure. Retryable. Operator should be aware if frequent."""
    def __init__(self, error_code, retry_after_seconds):
        self.error_code = error_code
        self.retry_after_seconds = retry_after_seconds

def charge_user(user_id, amount_cents):
    try:
        result = payment_gateway.charge(user_id, amount_cents)
        return PaymentSucceeded(transaction_id=result.id)
    except CardDeclined as e:
        # Business outcome, log at info level, no operator alert.
        log.info("payment_declined", user_id=user_id, decline_code=e.code)
        return PaymentDeclined(decline_code=e.code, decline_message=e.message)
    except (GatewayTimeout, GatewayUnavailable) as e:
        # Technical failure, log at warning, alert if rate exceeds threshold.
        log.warning("payment_gateway_unavailable", user_id=user_id, error=str(e))
        return PaymentTemporarilyUnavailable(error_code="gateway_unavailable", retry_after_seconds=30)
```

The function now returns one of three explicit outcomes. The caller cannot accidentally treat a decline as a transient error or vice versa. Logs at appropriate levels. Alerts fire on the right condition.

### Why this wins

- Users get correct messages: "your card was declined" vs "we're having trouble, try again in a moment."
- Retries fire only on retryable failures. Declined cards are not pointlessly retried (and fraud rules are not pointlessly triggered).
- Operators see real outage signal because business outcomes are not buried in error logs.
- Metrics are clean: decline rate is a business KPI; gateway error rate is an operational KPI; they can be charted, alerted, and forecast separately.

### Why the alternative loses

- Operators page out at 3am for card declines.
- Users see "something went wrong" and try the same card three times in a row, triggering fraud blocks.
- The error budget reports become noise because they include user actions.

### When this principle yields

When you genuinely cannot tell from the response which kind of failure occurred (some legacy SOAP services do this), the wrapper layer should default to "technical failure, retry with backoff" and log the raw response for diagnosis. The default is conservative because retrying a true business decline is usually safe (the gateway will decline again), while assuming a technical failure is a business decline silently loses revenue.

### Verification

A test for each branch: succeeded, declined, temporarily unavailable. The test asserts the correct user-facing message, the correct log level, and the correct retry behavior.

## Principle 5: Make invisible things visible

State: behavior driven by feature flags, queues, retries, caches, background jobs, or partial failures must produce evidence operators can find at 3am. If it cannot be observed, it cannot be operated.

### What goes wrong without it

A background job silently stops processing. The product appears to work because the request path returns 200, but data that should be propagating is not. Users start filing tickets ("my email never arrived"). Support escalates. Engineering investigates and finds the queue has been stuck for six hours because a worker process crashed and was not restarted. There was no log line, no metric, no alert.

### Anti-pattern

```javascript
// Background job that processes outbound emails:
async function sendQueuedEmails() {
  while (true) {
    const message = await queue.pop()
    if (message) {
      try {
        await mailer.send(message)
      } catch (e) {
        // ignore and continue
      }
    }
    await sleep(1000)
  }
}
```

Failures are silent. The queue might be growing, the mailer might be down, the worker might be looping doing nothing — operators have no way to know. The only signal is downstream user complaints.

### Better approach

```javascript
async function sendQueuedEmails(metrics, log) {
  while (true) {
    const message = await queue.pop()
    if (!message) {
      metrics.gauge("email_worker.idle", 1)
      await sleep(1000)
      continue
    }
    metrics.gauge("email_worker.idle", 0)
    const start = Date.now()
    try {
      await mailer.send(message)
      metrics.increment("email_worker.sent")
      metrics.histogram("email_worker.duration_ms", Date.now() - start)
    } catch (e) {
      metrics.increment("email_worker.failed", { reason: classifyMailerError(e) })
      log.warn("email_worker.send_failed", {
        messageId: message.id,
        recipient: maskEmail(message.recipient),
        attempt: message.attempt,
        error: e.code,
      })
      await queue.nack(message, { retryDelaySeconds: backoff(message.attempt) })
    }
  }
}
```

Now operators can answer the questions that matter at 3am: how many messages have been sent in the last 5 minutes? How many failed? What's the failure mode? Is the worker idle or busy? They do not need the source code to diagnose a production issue.

### Why this wins

- Queue depth, success rate, and failure mode are all observable. An alert on "no successes in 5 minutes" or "failure rate exceeds 10%" catches the silent failure mode.
- Logs include the message ID and a masked recipient — enough to correlate with user reports without leaking PII.
- Failed messages are nacked with backoff, so a transient outage does not lose data.

### Why the alternative loses

- The first signal of a problem is user complaints. By the time those reach engineering, the queue has been broken for hours.
- Without metrics, postmortems become guesswork. "We think the worker died around 10am" is not the same as "the worker last successfully sent a message at 10:03:42."
- Without backoff and nack, transient outages produce permanent data loss.

### When this principle yields

When the operation is genuinely transient and unimportant (a debug log line, a development-only fixture loader), full instrumentation is overkill. The test is whether operators would want to know if this stopped working. For background jobs, queues, caches, and integrations, the answer is always yes.

### Verification

Run the system, kill the dependency it talks to, and watch the metrics and logs. If you can tell that something is wrong from the dashboards alone (without reading the code), the visibility is sufficient.

## Principle 6: Make invalid states unrepresentable

State: prefer designs where wrong inputs cannot be expressed, then designs where they fail loudly at the boundary, then designs where they fail late. The earlier the failure, the cheaper the bug.

### What goes wrong without it

Invalid state propagates from input through five layers of code, picks up partially-correct data along the way, and fails in a place that has no idea what the original input was. The stack trace points at a JSON serializer that received a `Date` object containing `NaN`; the actual bug was a malformed query string parsed two seconds earlier in a different module.

### Anti-pattern

```python
def schedule_meeting(payload):
    start = datetime.fromisoformat(payload["start"])
    end = datetime.fromisoformat(payload["end"])
    duration = end - start
    invitees = payload["invitees"].split(",")
    create_calendar_event(start, end, invitees)

# Caller passes:
schedule_meeting({"start": "2026-12-01T10:00", "end": "2026-12-01T09:00", "invitees": ""})
```

Three problems. `end < start` is silently accepted (negative duration). An empty `invitees` string becomes `[""]`, a list with one empty-string invitee. There is no validation that the start time is in the future. Each problem will surface somewhere downstream — the calendar service rejecting an empty email, or the booking page showing "duration: -1 hour."

### Better approach

```python
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class MeetingRequest:
    start: datetime
    end: datetime
    invitees: tuple[str, ...]

    def __post_init__(self):
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("start and end must be timezone-aware")
        if self.end <= self.start:
            raise ValueError(f"end ({self.end}) must be after start ({self.start})")
        if self.start <= datetime.now(timezone.utc):
            raise ValueError(f"start ({self.start}) must be in the future")
        if not self.invitees:
            raise ValueError("at least one invitee required")
        for invitee in self.invitees:
            if "@" not in invitee:
                raise ValueError(f"invalid invitee email: {invitee!r}")

def parse_meeting_request(payload: dict) -> MeetingRequest:
    return MeetingRequest(
        start=datetime.fromisoformat(payload["start"]).replace(tzinfo=timezone.utc),
        end=datetime.fromisoformat(payload["end"]).replace(tzinfo=timezone.utc),
        invitees=tuple(i.strip() for i in payload["invitees"].split(",") if i.strip()),
    )

def schedule_meeting(payload):
    request = parse_meeting_request(payload)
    create_calendar_event(request)
```

The `MeetingRequest` cannot exist in an invalid state. Every downstream function takes a `MeetingRequest` and can trust its invariants. The boundary between "untrusted dict from the network" and "trusted internal value" is one place: `parse_meeting_request`. Bugs are caught at the entry point with messages that name the actual problem.

### Why this wins

- The error message points at the real cause: "end must be after start", not a NullPointerException five layers deep.
- Internal code is shorter and clearer because it does not re-validate at every layer.
- The validation rule is in one place. Adding "meetings must be at most 4 hours long" is a one-line change.

### Why the alternative loses

- Invalid inputs propagate. The error appears far from the cause, and debugging it requires reading every layer between input and failure.
- Defensive checks get scattered. Each downstream function adds its own `if duration < 0`, and they disagree on the rule.
- The system ends up with "valid in some cases, invalid in others" data — the worst possible state to reason about.

### When this principle yields

When the value comes from a fully-trusted internal source (e.g., the row was already validated by the database constraint), repeating the validation is noise. The test is whether the producer of the value is part of the trust boundary. If it crosses one (network, file system, user input, third-party service), validate at the boundary and trust internally.

### Verification

A test for each invalid input that asserts a specific error message naming the violated rule. The internal code path has zero defensive checks because the type guarantees them.

## Routing

Use `@tank/security-review` when the correctness boundary is also a security boundary (auth tokens, secrets, untrusted user input) — the threat model adds requirements beyond just "don't crash."

Use `@tank/relational-db-mastery` when the correctness concern is database-level: schema constraints, transactional boundaries, isolation levels, race conditions in the persistence layer.

Use `@tank/clean-code` when state confusion is rooted in unclear module boundaries or weak naming, and the right fix is structural before correctness gets cleaner.

Use `references/testing-and-verification.md` for the test patterns that prove correctness across normal, edge, and failure paths.
