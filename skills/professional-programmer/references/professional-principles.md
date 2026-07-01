# Professional Principles

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Rai's 97-step Medium roadmap; Martin (Clean Code); Ousterhout (A Philosophy of Software Design); Tank clean-code and bdd-e2e-testing skills

Covers: the operating posture that turns a coding agent into a professional teammate rather than a code generator.

## Operating Standard

Professional programming is a posture, not a style. It is the habit of producing code that the next maintainer can read, run, change, deploy, and operate at 3am without first phoning the original author.

A professional answer is shaped by three constraints, in order: correctness, maintainability, and delivery. Performance, elegance, and cleverness are downstream of those three. When pressure pushes the order around, a professional says so explicitly instead of silently trading correctness for appearance.

A coding agent is professional when its output passes the simplest test a senior reviewer applies: would I trust this engineer with the next change to the same file? If the answer requires "yes, but I'd rewrite it first," the work is not done.

## Quick Routing

| Situation | Principle to apply |
| --------- | ------------------ |
| You are about to make a "safe-looking" speculative change | Principle 1: Act with prudence |
| Something is broken and you suspect the framework | Principle 2: Check your code first |
| You are unsure but tempted to proceed silently | Principle 3: Make uncertainty visible |
| You are editing code you did not write | Principle 4: Read code before changing it |
| You are finishing a change and ready to "ship it" | Principle 5: Code is for the next maintainer |
| You are tempted to "clean up while you're in there" | Principle 6: Keep the change narrow |

## Principle 1: Act with prudence

State: when evidence is incomplete, prefer the smallest reversible action and name what additional evidence would change the decision.

### What goes wrong without it

The most expensive bugs in production are not "I had no idea this could happen." They are "I had a hunch but I shipped anyway." Imprudent action looks confident in the moment and looks negligent on the incident review.

### Anti-pattern

```python
# Caching auth lookups for "performance" without measuring or scoping the cache.
USER_ROLE_CACHE = {}

def get_role(user_id):
    if user_id in USER_ROLE_CACHE:
        return USER_ROLE_CACHE[user_id]
    role = db.fetch_role(user_id)
    USER_ROLE_CACHE[user_id] = role
    return role
```

The hidden cost: this cache outlives role changes. A user demoted from admin keeps admin until the process restarts. There is no profile showing the database lookup was a problem, no eviction policy, no test that role changes are visible, and no scoping to a request. The change feels like a small optimization. It is actually an authorization bug waiting for the next promotion or demotion.

### Better approach

```python
# Same hot path, but the cache lifetime is bounded and the risk is named in code.
def get_role(user_id, role_loader):
    # Per-request cache only. Role changes become visible on the next request.
    return role_loader.cached(user_id, ttl_seconds=0)
```

Or: do not add a cache until a profile shows `fetch_role` actually dominates a real user-visible operation. The professional move is to leave the readable code in place and add a one-line comment noting why the cache was considered and rejected, so the next person does not re-do the analysis.

### Why this wins

- The change is reversible. Removing a per-request helper does not require thinking about cache invalidation.
- The decision is auditable. The next reviewer sees the bound on lifetime.
- The risk is local. Role changes are visible within one request, not "next process restart."

### Why the alternative loses

- The original cache silently couples auth correctness to process lifetime.
- It only fails on demotion, which is rare in dev and common in production incidents.
- The bug is invisible until the wrong user accesses the wrong action.

### When this principle yields

When the user-visible problem is concrete and measured (profiler shows the lookup on a hot path, p95 misses an SLA), prudence yields to the optimization. It does not yield to "this might be slow."

### Verification

A test that demotes a user mid-session and confirms the next authorization decision reflects the new role. If the test cannot be written, the production behavior cannot be trusted.

## Principle 2: Check your code first

State: when something does not work, suspect the local change, the local environment, and the local data before suspecting the framework, the compiler, the OS, or the database.

### What goes wrong without it

Blame seeking is faster than evidence seeking, so it feels productive. The cost shows up later: a wasted hour reading framework source for a bug that was a missing `await`, or a vendor escalation for a bug that was a stale Docker image.

### Anti-pattern

```typescript
// "Express must be broken — my route returns 500."
app.post("/orders", async (req, res) => {
  const order = createOrder(req.body)  // returns Promise<Order>
  res.json(order)                       // sends "{}" because order is a pending Promise
})
```

The developer opens a GitHub issue against Express. The actual problem is the missing `await`. Several hours disappear into framework source while the fix was three characters away.

### Better approach

```typescript
app.post("/orders", async (req, res) => {
  const order = await createOrder(req.body)
  res.json(order)
})
```

Before suspecting the framework, the professional move is a quick local triage:

1. Reproduce with the minimum surface (one route, one input, no middleware).
2. Log or `console.log` the value at the suspected boundary. Confirm the type.
3. Check the framework only when the local boundary is verified.

### Why this wins

- 90%+ of "the framework is broken" cases turn out to be local. Searching local first is the higher-EV strategy by far.
- It builds a habit of evidence over narrative.
- It keeps the bug report quality high when escalation is genuinely needed.

### Why the alternative loses

- Framework debugging is expensive. Even reading the right file in a popular library takes longer than printing a value.
- Public framework issues filed without local verification create noise, lose credibility, and are usually closed as user error.

### When this principle yields

When local verification confirms the bug is reproducible with a minimal example that exercises the framework directly, framework suspicion is now evidence-based and worth pursuing.

### Verification

A reproduction script that triggers the bug with the smallest possible surface. If you cannot reproduce, you do not yet know what is broken.

## Principle 3: Make uncertainty visible

State: name what you do not know, what you assumed, and what would change the answer. Silent assumptions become silent bugs.

### What goes wrong without it

The agent ships a confident-looking diff with hidden assumptions like "I assumed the caller validates input," "I assumed this runs single-threaded," or "I assumed the column is UTC." The reviewer cannot challenge what they cannot see, and the assumption fails the first time the system meets a real user.

### Anti-pattern

```python
def calculate_late_fee(due_date, paid_date):
    days_late = (paid_date - due_date).days
    return Decimal("5.00") * days_late
```

The implementation assumes both dates are timezone-aware, in the same timezone, and on the same calendar system. None of those assumptions are visible. A user in a `+13:00` timezone paying at 11pm local time may be charged a fee for a payment that was on time in the billing timezone.

### Better approach

```python
def calculate_late_fee(due_date_utc: datetime, paid_date_utc: datetime) -> Decimal:
    """Both inputs MUST be UTC. Caller is responsible for conversion.

    Open question: does the business consider 'on time' to mean
    'before midnight in the billing timezone' or 'before midnight UTC'?
    Current behavior is UTC. Confirm with product before relying on this
    for invoices visible to international customers.
    """
    if due_date_utc.tzinfo is None or paid_date_utc.tzinfo is None:
        raise ValueError("dates must be timezone-aware")
    days_late = (paid_date_utc - due_date_utc).days
    return Decimal("5.00") * max(days_late, 0)
```

The assumption is now visible at three levels: the type signature, the docstring, and a runtime check that fails loud if the assumption is wrong.

### Why this wins

- The reviewer can challenge the assumption directly.
- A wrong assumption fails immediately, not silently.
- The next maintainer sees what is decided and what is still an open question.

### Why the alternative loses

- A silent assumption defaults to "whatever the test data happened to be," which is rarely the real production distribution.
- The bug surface is the entire space of inputs the original author did not imagine.

### When this principle yields

When the assumption is genuinely universal in the language or platform (e.g., assuming integers are 64-bit on a JVM target), naming it adds noise. The test is whether a thoughtful reviewer could plausibly disagree. If yes, name it.

### Verification

A test that fails with an assumption-violating input. The failure message should mention the assumption by name.

## Principle 4: Read code before changing it

State: before editing a file, read its callers, its tests, and one or two recent commits that touched it. Match the conventions you find unless you have explicit reason to break them.

### What goes wrong without it

You introduce a second pattern next to the first. Now the codebase has two ways to do auth, two ways to validate input, two ways to format errors. The next person has to learn both, and a third pattern starts to look reasonable.

### Anti-pattern

```typescript
// Existing convention in 12 routes:
export async function getUserHandler(req: AuthedRequest, res: Response) {
  const user = await userService.findById(req.user.id)
  return res.json(toUserDTO(user))
}

// New route, written without reading the rest:
export async function getOrderHandler(req: Request, res: Response) {
  const userId = req.headers["x-user-id"]  // no auth middleware, raw header
  const order = await db.query("SELECT * FROM orders WHERE user_id = $1", [userId])
  res.send(JSON.stringify(order))  // raw shape, not a DTO
}
```

This works in isolation but creates four problems: it bypasses the auth middleware, it leaks the database row shape, it returns a JSON string instead of an object response, and it teaches the next contributor that two patterns are acceptable.

### Better approach

Before writing the new handler, the professional move is a 3-minute read:

1. `grep` for one similar route in the same directory.
2. Read its imports: `AuthedRequest`, `userService`, `toUserDTO`.
3. Read one test for that route to see the expected shape.
4. Match the convention.

```typescript
export async function getOrderHandler(req: AuthedRequest, res: Response) {
  const order = await orderService.findForUser(req.user.id)
  return res.json(toOrderDTO(order))
}
```

### Why this wins

- One pattern stays one pattern. New contributors learn it once.
- The auth middleware actually runs. Authorization is not optional per route.
- The DTO boundary stays intact. Database shape changes do not leak to clients.

### Why the alternative loses

- Two patterns becomes three within months.
- Security guarantees become "depends which route you hit."
- Reviewers cannot tell whether deviations are bugs or intentional.

### When this principle yields

When the existing convention is genuinely wrong (uses `as any`, swallows errors, ignores auth) and you can fix it in a separate, scoped commit. Do not silently introduce a third pattern as a fix; either follow the existing one or fix it explicitly.

### Verification

The new file imports the same helpers as nearby files. A linter rule or code-review checklist catches direct database access from handlers.

## Principle 5: Code is for the next maintainer

State: optimize for readability and operability under pressure, not for the moment of writing. The next maintainer is often you, six months later, on-call.

### What goes wrong without it

Code that was clear in the author's head is opaque in the reviewer's, and worse in the on-call engineer's at 3am. Generic names, hidden state, swallowed errors, and clever tricks all read the same in calm conditions and become incident multipliers under stress.

### Anti-pattern

```javascript
// Three hours into an outage, on-call sees this in the trace:
function handle(d, opts = {}) {
  const x = process(d, opts)
  if (!x) return
  for (const r of x) {
    fn(r, opts.f || defaultFn)
  }
}
```

There is nothing wrong with this code in isolation. There is everything wrong with it during an incident. What is `d`? What is `process`? What is `fn`? Why is `!x` ignored silently? An on-call engineer cannot answer any of those without spelunking, and spelunking on incidents is how outages become long outages.

### Better approach

```javascript
function notifyAffectedSubscribers(event, options = {}) {
  const subscribers = findSubscribers(event, options)
  if (subscribers.length === 0) {
    log.info("no_subscribers_for_event", { eventId: event.id })
    return
  }
  const sendNotification = options.notifier ?? defaultNotifier
  for (const subscriber of subscribers) {
    sendNotification(subscriber, options)
  }
}
```

Same logic, but every name carries domain meaning, the empty case is explicit and observable, and the fallback is a named alternative rather than a `||` chain.

### Why this wins

- An on-call engineer reading a stack trace can guess what this function does without reading the rest of the file.
- The "no subscribers" case is now visible in logs, which is exactly the case operators want to see during a partial outage.
- Future changes do not need to retrace the original author's reasoning.

### Why the alternative loses

- During incidents, time spent decoding intent is time the system is broken.
- Generic names invite generic edits, which expand scope drift.
- Silent empty-case handling is indistinguishable from "everything broke."

### When this principle yields

It does not. Maintainability is a load-bearing constraint, not a preference. The closest exception is hot-path code where named locals would force allocations the runtime cannot eliminate, and that case is rare and provable with a profiler.

### Verification

A new contributor (or a code-review tool that simulates one) can describe the function from its name and signature alone. If the description matches the behavior, the code carries its own intent.

## Principle 6: Keep the change narrow

State: a change should do one coherent thing. If you find yourself fixing unrelated bugs, renaming neighbors, or upgrading dependencies inside the same diff, stop and split.

### What goes wrong without it

Wide changes are unreviewable. Reviewers either rubber-stamp them (accepting unknown risk) or block them (delaying the actual fix). Either way, the team loses.

### Anti-pattern

```
PR title: "Fix login bug"
Files changed: 47
Includes:
  - the actual one-line login fix
  - a refactor of the auth module
  - eslint config update
  - dependency upgrade for date-fns
  - rename of UserService to UsersService
  - removal of dead feature flag
```

A reviewer cannot reason about whether the login fix is correct because it is buried in 46 other concerns. A revert of the bug fix would also revert the dependency upgrade and the rename. The change is no longer atomic.

### Better approach

Six pull requests, in dependency order:

1. The one-line login fix, with a regression test.
2. The dead feature flag removal.
3. The rename, executed by tooling.
4. The dependency upgrade.
5. The eslint config update.
6. The auth module refactor.

Each is independently reviewable and revertable. The login fix can ship today; the refactor can ship next week with proper review.

### Why this wins

- Reviewers can engage with each change at the right level of attention.
- A bisect later can identify which change caused a regression.
- The on-call engineer who reverts at 3am reverts only what they need to.

### Why the alternative loses

- Wide diffs hide regressions inside unrelated work.
- Bisecting becomes useless because each commit changes too many concerns.
- Cleanup work becomes coupled to feature work, so cleanup gets blocked by feature timelines.

### When this principle yields

When two changes are genuinely inseparable (a type definition and the only file that uses it, a migration and the model change that depends on it), they belong in one commit. The test is whether one could be reverted without breaking the other. If not, they are one change.

### Verification

`git log --stat` shows one coherent intent per commit. The commit message describes one decision, not a list.

## Failure Modes to Watch

| Failure | Why It Hurts | Correction |
| ------- | ------------ | ---------- |
| Hero rewrite | Unsafe to review, hides risk | Slice changes |
| Unstated assumption | Bugs land silently | Encode the assumption in code or test |
| Generic naming (`data`, `result`, `process`) | Domain disappears | Rename around the business concept |
| Silent failure (empty `catch`) | False success in production | Classify failure, return typed result |
| Speculative config | Untestable state space | Wait for the requirement |
| Verification skipped | Performative confidence | Run the closest evidence first |
| Pretending to know | Wrong answer wears a confident voice | Name the unknown and route to evidence |

## Routing

Use `references/conflict-resolution.md` when two principles point in different directions.

Use `@tank/clean-code` when the issue is a code smell, naming, or modularity problem rather than a posture problem.

Use `@tank/bdd-e2e-testing` when the professional move depends on real-system verification.

Use `@tank/security-review` when the principle conflict crosses a security boundary.
