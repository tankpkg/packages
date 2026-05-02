# Conflict Resolution

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Martin (Clean Code); Fowler (Refactoring); Ousterhout (A Philosophy of Software Design); Tank clean-code, bdd-e2e-testing, and security-review skills

Covers: how to choose when two professional principles point in different directions — correctness vs speed, security vs convenience, simplicity vs extensibility, DRY vs clarity, performance vs readability, tests vs deadlines.

## Operating Standard

Most decisions in real codebases are not "right vs wrong." They are "principle A vs principle B," and the professional move is to name the conflict, choose deliberately, and document the choice so future maintainers know what was traded.

A coding agent's job in conflict cases is not to mechanically pick the higher-ranked principle. It is to understand which principle's failure mode is more expensive *in this specific context* — and to make the trade-off visible. Two engineers can agree on the principles and disagree on the call; the disagreement is professional if both sides can name what they're trading and what would change their mind.

Three habits separate good conflict resolution from bad. First, name both sides explicitly: "this is correctness vs speed." Slogans like "best practice says" hide the trade. Second, pick the smallest reversible step when evidence is incomplete; if the decision is hard to reverse, gather more evidence before committing. Third, write down the trigger that would change your mind: "if this loop accounts for >10% of request latency in production, revisit."

## Decision Order (when no other context is available)

When you must choose without clear context, this is the default priority. It can be overridden by deliberate decision; it cannot be overridden by speed pressure or aesthetic preference.

1. **Correctness, safety, and data integrity** — wrong outputs damage users, customers, and trust faster than any benefit they buy.
2. **Security and privacy** — a compromised system has no value, however fast it is.
3. **Maintainability** — code that cannot be safely changed is code that cannot be operated, fixed, or improved.
4. **Delivery speed within the above** — shipping less, correctly and securely, beats shipping more, broken.
5. **Performance** — when measured against a real user-visible goal.
6. **Elegance** — only when it reduces total complexity, not when it adds personal taste.

## Quick Routing

| Conflict | Default | Look at |
| -------- | ------- | ------- |
| Correctness vs speed | Correctness | Principle 1 |
| Security vs convenience | Security | Principle 2 |
| Simplicity vs extensibility | Simplicity | Principle 3 |
| DRY vs clarity | Clarity | Principle 4 |
| Performance vs readability | Readability | Principle 5 |
| Tests vs deadline | Critical tests | Principle 6 |

## Principle 1: Correctness wins over speed by default

State: when you can ship fast or ship correct, ship correct. Wrong outputs that look successful create downstream cost (refunds, support tickets, audit findings, customer trust loss) far larger than the time saved.

### What goes wrong without it

The team ships a refund flow without testing the partial-refund case because "we'll get to it." The flow ships. A customer requests a partial refund. The system processes it as a full refund. The customer is overpaid; the company is short. Reconciling takes a week of finance work, plus a customer escalation, plus a postmortem. The "saved time" cost two engineer-weeks and a customer relationship.

### Anti-pattern

```typescript
// Sprint commitment: ship the refund button by Friday.
// Wednesday afternoon, partial refunds aren't working. Decision:
async function processRefund(orderId: string, amount?: number) {
  // Skip the partial-refund logic for now; full refunds work and that's most of the volume.
  return paymentGateway.fullRefund(orderId)
}
```

The function silently ignores the `amount` parameter. Callers requesting a partial refund get a full refund instead. Most of the time it's fine because most refunds are full; rarely it's a disaster because a $200 partial refund of a $2000 order becomes a $2000 full refund.

### Better approach

Two professional moves. First, refuse to silently break the contract:

```typescript
async function processRefund(orderId: string, amount?: number) {
  if (amount !== undefined) {
    throw new NotImplementedError(
      "partial refunds not yet supported; use processFullRefund or wait for v1.1"
    )
  }
  return paymentGateway.fullRefund(orderId)
}
```

Second, ship less:

```
Friday release notes:
- Full refunds: shipped
- Partial refunds: NOT shipped, deferred to next sprint
  (We chose to ship correct full refunds rather than incorrect partial refunds.)
```

The team shipped less, but what shipped is correct. The partial-refund work continues with proper tests next sprint. No customer is overpaid; no postmortem is needed.

### Why correctness wins

- Wrong outputs cost more than missing features. A refund that doesn't exist yet is "we're working on it." A refund that processes incorrectly is "we charged a customer wrong" — those are very different conversations.
- Silent contract violations destroy trust in the entire codebase. Once one function lies about its inputs, every other function is suspect.
- The "we'll fix it later" debt usually doesn't get fixed before it bites. The bite happens at the worst possible time.

### When speed legitimately wins

In a disposable prototype with explicit "do not ship to users" scope, optimizing for speed of iteration is correct. The test is whether anyone is making a decision based on the output. If yes (a customer demo, a dashboard, a trial), correctness wins. If no (a one-off script to compute internal stats), speed can win.

### Verification

Look for code that silently ignores arguments, swallows errors, or returns "good enough" when the request was specific. Each one is a case where speed beat correctness; flag it and either fix it or make the limitation visible at the contract level.

## Principle 2: Security wins over convenience by default

State: convenience is never enough justification for exposing users, data, secrets, or privileges. The cost of a security incident is borne by users and regulators, not by the engineer who chose convenience.

### What goes wrong without it

A staging-only authorization bypass is added so QA can test admin features without going through the full SSO flow. The flag is read from environment-specific config. Months later, a deployment misconfiguration sets the flag to true in production. An attacker discovers the bypass within hours. Customer data is exposed. The cost is regulatory fines, customer churn, and a public incident report.

### Anti-pattern

```python
def require_admin(user, env=os.environ):
    if env.get("SKIP_AUTH_CHECK") == "true":
        return  # convenience for QA
    if not user.is_admin:
        raise PermissionDenied()

# QA sets SKIP_AUTH_CHECK=true in their dev env.
# Production deploy script accidentally inherits the env var.
# Every endpoint that uses require_admin is now world-accessible.
```

The bypass exists in production code. The only thing keeping it from being exploited is operational discipline, which is the wrong place to enforce a security boundary.

### Better approach

```python
def require_admin(user):
    if not user.is_admin:
        raise PermissionDenied()

# QA testing path: a real test admin account, seeded into the staging database.
# The QA team uses real credentials and goes through real auth.
# The bypass code path does not exist in any environment.

# tests/conftest.py — for automated tests:
@pytest.fixture
def admin_user(db):
    return db.create_user(email="qa-admin@test.example.com", is_admin=True, password="...")
```

The bypass is impossible because it doesn't exist in code. QA goes through real auth with seeded credentials. Tests use fixture users. There is no environment where authorization can be silently disabled.

### Why security wins

- A security incident affects users who didn't choose the convenience trade-off.
- Regulators don't care that the bypass was "only for staging." They care that customer data was exposed.
- Trust, once lost, is not bought back with the time the bypass saved.
- The cost of seeded test accounts is small and one-time. The cost of a production breach is recurring.

### When convenience legitimately wins

Inside a developer's local-only environment with no real data and no path to production (a Docker compose stack, a sandbox), convenience flags are fine because the trust boundary is the developer's machine. The test is whether the convenience can leak past the boundary. If the same code or config can reach production, convenience cannot win.

### Verification

`grep` the codebase for environment-conditional auth, debug flags that grant access, and "if env=='dev' skip" patterns. Each one is a case to refactor: replace with a real test account or remove entirely.

## Principle 3: Simplicity wins over extensibility by default

State: do not add abstraction for variation that does not exist. Most predicted variation never arrives, and the abstraction calcifies the wrong shape for the variation that eventually does.

### What goes wrong without it

The team designs a generic "notification provider" interface to support "future" channels: email, SMS, push, Slack, webhook, fax. They ship with one implementation (email). Six months later, the company adds SMS — and the interface is wrong for it because the original design assumed all channels accept the same template format, while SMS has length constraints, requires different opt-out handling, and uses a separate cost-tracking system. The "extensible" interface has to be rewritten anyway, and the year of speculative ceremony added nothing.

### Anti-pattern

```typescript
// Premature abstraction: the team has one notification channel (email).
interface INotificationChannel {
  send(template: Template, recipient: Recipient): Promise<Result>
}

interface Template {
  subject: string
  body: string
  variables: Record<string, unknown>
}

class EmailChannel implements INotificationChannel { /* ... */ }
class SMSChannel implements INotificationChannel { /* doesn't exist yet */ }
class PushChannel implements INotificationChannel { /* doesn't exist yet */ }

class NotificationFactory {
  create(channelType: string): INotificationChannel { /* speculative */ }
}
```

The interface freezes assumptions: "all channels have a subject, all use the same template format, all return the same Result." When real SMS arrives, none of those assumptions hold. The interface is rewritten; the original design was a tax for nothing.

### Better approach

```typescript
// Just write the email code.
async function sendOrderConfirmationEmail(order: Order, recipient: Recipient): Promise<void> {
  const html = renderOrderConfirmation(order)
  await mailer.send({
    to: recipient.email,
    subject: `Your order ${order.id} confirmation`,
    html,
  })
}
```

When SMS arrives later:

```typescript
async function sendOrderConfirmationSMS(order: Order, phone: PhoneNumber): Promise<void> {
  const message = `Order ${order.id} confirmed. Total: ${formatMoney(order.total)}. Track: ${order.trackingUrl}`
  if (message.length > 160) {
    throw new Error("SMS exceeds 160 chars; split or shorten template")
  }
  await smsGateway.send({ to: phone, message })
}
```

The two functions share a *purpose* (notify about an order) but not a *shape* (very different APIs, different constraints). When a third channel (push) arrives, you'll discover whether there's actually a useful abstraction across three channels — and you can extract it then, with three concrete examples to inform the design.

### Why simplicity wins

- The cost of "I'll abstract this later if needed" is small (a small refactor when the second case arrives).
- The cost of "I abstracted prematurely" is large: the abstraction is wrong, removing it requires changing every caller, and you've lived with ceremony in the meantime.
- Real abstractions emerge from concrete cases. You can extract a useful interface from three working examples; you cannot design one correctly from one example and two guesses.

### When extensibility legitimately wins

When a second concrete implementation already exists or is in active development with a known shape, an interface is justified. The test is whether you can name the second implementation, name its constraints, and name when it ships. If yes, abstract. If no, stay concrete.

### Verification

`grep` for interfaces with one implementation. For each, ask: who is the second implementation? When does it ship? If neither answer is concrete, the interface is speculative and the simpler concrete code wins.

## Principle 4: Clarity wins over DRY by default

State: duplication is sometimes the right answer. Extracting two similar-looking functions into one helper is harmful when the functions encode different concepts that will diverge.

### What goes wrong without it

The team merges two functions that look alike — one validates an email format for user signup, one validates an email format for newsletter subscription. Six months later, marketing wants to allow `+` aliases in newsletter emails (`alice+sale@example.com`) but not in signup (to prevent fake accounts). The merged helper now has an `if isNewsletter` branch. A year later, the rules drift further apart, and the helper has six conditional branches. Reading the signup flow now requires understanding all six.

### Anti-pattern

```python
# Two functions that look alike:
def validate_signup_email(email: str) -> ValidationResult:
    if not _is_valid_format(email): return invalid("bad format")
    if _is_disposable_email(email): return invalid("disposable not allowed")
    return valid()

def validate_newsletter_email(email: str) -> ValidationResult:
    if not _is_valid_format(email): return invalid("bad format")
    if _is_disposable_email(email): return invalid("disposable not allowed")
    return valid()

# "DRY violation" — merged into:
def validate_email(email: str, context: Literal["signup", "newsletter"]) -> ValidationResult:
    if not _is_valid_format(email): return invalid("bad format")
    if _is_disposable_email(email): return invalid("disposable not allowed")
    return valid()
```

The two functions are identical *today*. They might not be tomorrow. When marketing changes the newsletter rules, the helper grows a `context` branch. When signup adds anti-fraud checks, another branch. When newsletter adds GDPR-specific logic, another. The "DRY" function becomes a giant `match` statement on `context`.

### Better approach

```python
def validate_signup_email(email: str) -> ValidationResult:
    if not _is_valid_format(email): return invalid("bad format")
    if _is_disposable_email(email): return invalid("disposable not allowed")
    return valid()

def validate_newsletter_email(email: str) -> ValidationResult:
    if not _is_valid_format(email): return invalid("bad format")
    if _is_disposable_email(email): return invalid("disposable not allowed")
    return valid()

# Yes, the bodies look identical right now.
# That's fine. They are answering different business questions.
# When marketing changes newsletter rules, only validate_newsletter_email changes.
```

Two functions, one for each business concept. When the rules diverge (and they will), the changes are local. When the rules stay aligned (which sometimes happens), having two functions costs almost nothing — they're a few lines each.

### Why clarity wins

- Different concepts deserve different functions even when they look alike. The shape similarity is incidental; the conceptual difference is structural.
- Future changes that affect one concept are local. There is no risk of accidentally changing the other.
- Tests for each function are independent. A signup-validation bug cannot regress newsletter validation.

### When DRY legitimately wins

When the two functions encode the same business rule (e.g., both check "user must have an active subscription"), they are two implementations of one concept and should be merged. The test is whether changes to one would always be changes to the other. If yes, merge. If you'd need to change one without the other, leave them separate.

### Verification

For each "DRY violation" candidate, ask: "if requirements changed for one but not the other, would the merged helper still serve both?" If yes, merge. If no, document above each function why they look alike and why they're separate.

## Principle 5: Readability wins over performance by default

State: write clear code first; optimize only when measurement proves a real bottleneck. Premature optimization makes code harder to read, harder to change, and harder to debug — usually for no measurable benefit.

### What goes wrong without it

The team rewrites a clear list comprehension into a clever bitwise loop because it "feels faster." The code is now 30 lines instead of 3, has a subtle off-by-one bug under load, and is 0.5% faster than the original. The bug ships. The fix takes three days. The 0.5% improvement is invisible in production.

### Anti-pattern

```python
# Original: clear, idiomatic.
def find_active_user_ids(users):
    return [user.id for user in users if user.is_active and not user.is_suspended]

# "Optimized": author thinks loops are faster than comprehensions.
def find_active_user_ids(users):
    result = []
    n = len(users)
    i = 0
    while i < n:
        u = users[i]
        if u.is_active:
            if not u.is_suspended:
                result.append(u.id)
        i += 1
    return result
```

The "optimized" version is no faster (in CPython, the comprehension is actually faster), is harder to read, and has more places to introduce off-by-one bugs. The author was guessing.

### Better approach

```python
def find_active_user_ids(users):
    return [user.id for user in users if user.is_active and not user.is_suspended]
```

Keep the readable version. If profiling later shows this function dominates a real user-visible operation, then optimize — and at that point, the optimization is targeted (maybe replace the list with a generator if memory is the issue, or add an index if the iteration is the issue, or move to a database query if the data shape allows).

### Why readability wins

- Readable code is debuggable code. When something goes wrong at 3am, on-call wants to read the function, not reverse-engineer it.
- Readable code is changeable code. Future feature requests can be implemented; cryptic code becomes a "do not touch" zone.
- Most code is not on a hot path. Optimizing it provides no measurable benefit while paying ongoing readability cost.

### When performance legitimately wins

When a profile (or real production metrics) show a function genuinely dominates a user-visible operation, optimization is worth complexity. The trade is explicit: "we accept N% more reading cost for M% better latency." The test is whether the latency target is real and the bottleneck is measured. If yes, optimize. If no, leave it readable.

### Verification

Read the diff. If the new code is harder to follow than the old, ask: where is the profile showing the old code was a bottleneck? No profile, no rewrite.

## Principle 6: Critical tests win over deadlines by default

State: shipping under deadline pressure can mean reducing scope; it cannot mean shipping unverified risky behavior. Tests for risky paths are the cheapest insurance against weekend incidents.

### What goes wrong without it

The team is asked to ship the new payment flow by Friday. Wednesday, the integration tests are flaky and the team cuts them ("they'll be fine"). The flow ships. Saturday, an edge case in capture timing causes payments to be authorized but not captured for ~3% of orders. The team spends the weekend reconciling, contacting affected customers, and fixing the bug they could have caught Wednesday with a 30-minute test.

### Anti-pattern

```
Pressure: ship Friday.
Wednesday: integration tests for payment capture are flaky.
Decision: skip them, the unit tests pass.

Friday: ship.
Saturday: production bug surfaces.
Sunday-Monday: reconciliation, customer contacts, hotfix.

Net: 2 weekend days lost, customer trust damaged, vs. 1 day to fix the test on Wednesday.
```

The "save 1 day" decision cost 2 weekend days plus customer impact. The math was bad in the moment because the cost of the bug was discounted (it might not happen) and the cost of the test was inflated (it's annoying to fix).

### Better approach

```
Pressure: ship Friday.
Wednesday: integration tests for payment capture are flaky.
Conversation:
  Engineer: "These tests cover the capture race condition. They're flaky because
             the test setup has a timing issue, not because the code under test
             is wrong. I need a day to fix the test setup. I can either:
             (a) Cut scope: ship without partial-refund support, defer to next week.
             (b) Push the date: ship Monday with full scope and stable tests.
             What's the cost of each option?"
  PM: "(a) is fine — partial refunds aren't blocking the launch."
Friday: ship full refunds with stable tests. Partial refunds next sprint.
```

The deadline is met by reducing scope, not by reducing safety. The risky path either has tests, or that path doesn't ship.

### Why critical tests win

- A weekend incident costs more than a deferred feature.
- Customer trust is bought slowly and lost fast. A botched payment flow lingers in customer perception long after the fix.
- The "save time" calculation undervalues incident cost because incidents are uncertain. They are also expensive when they happen.

### When deadlines legitimately win

For genuinely throwaway code with no production claim — a one-off internal tool, a sandbox demo, a research spike — testing is overkill. The test is whether anyone, ever, will make a decision based on the output. If yes, the risky paths get tests.

### Verification

Every release ships with the tests for the risky paths green. If a test is flaky, it is fixed or the path is cut from the release — not skipped.

## When Two of These Conflict (Meta-Conflict Resolution)

When the principles themselves conflict (e.g., "security says use a real test account, but the deadline pressure says use a bypass flag"), apply the priority order from the Operating Standard. Correctness and security beat speed and elegance. Maintainability beats performance unless performance is measured and material.

When you genuinely cannot tell which principle applies, ask. A focused question is cheaper than a wrong default:

```
"I see two reasonable approaches:
  (a) [option A] — protects [principle 1] but costs [trade]
  (b) [option B] — protects [principle 2] but costs [trade]
What's the priority for this work?"
```

## Routing

Use `references/professional-principles.md` for the underlying principles being weighed.

Use `@tank/security-review` when the conflict crosses an auth, secrets, injection, or data-exposure boundary.

Use `@tank/clean-code` when the conflict is about structure, naming, or modularity.

Use `@tank/bdd-e2e-testing` when the conflict resolution depends on real-system verification of behavior.

Use `@tank/relational-db-mastery` when the conflict involves database tradeoffs (consistency vs availability, normalization vs query performance).
