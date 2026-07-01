# Simplicity and Design

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Martin (Clean Code); Fowler (Refactoring); Ousterhout (A Philosophy of Software Design); Tank clean-code and ast-linter-codemod skills

Covers: design judgment under real constraints — boolean flags, domain types, abstraction, encapsulation, layout, and naming.

## Operating Standard

Code is design. The mechanical act of typing is downstream of choices about responsibility, naming, and shape — and those choices outlive the code that expressed them. A function written in five minutes can survive in a hot path for a decade.

Simplicity is not shortness. Three lines of clever array spread can be less simple than fifteen lines of named intermediate variables. Simplicity is "few concepts in play at once." A reader holding the function in their head should be tracking one job, not three.

A coding agent's first job in design is to subtract. Before adding a config option, a wrapper, a pattern, or a class, ask whether something can be removed instead. The cheapest line is the one that does not exist.

## Quick Routing

| Situation | Principle to apply |
| --------- | ------------------ |
| API takes a boolean parameter | Principle 1: Boolean flags hide two operations |
| Code passes around `string`, `id`, or `data` for domain values | Principle 2: Use domain types |
| You found an `IFooService` with one implementation | Principle 3: One-implementation interfaces are usually waste |
| A class exposes only getters and setters | Principle 4: Encapsulate behavior, not state |
| You are about to add a third config option | Principle 5: Reduce before adding |
| You find yourself reaching for comments to explain code | Principle 6: Layout and names beat comments |

## Principle 1: Boolean flags hide two operations

State: when a function takes a boolean that switches its behavior, you have probably written two functions sharing a name. Split them.

### What goes wrong without it

Boolean flags hide intent at the call site. A reader sees `processOrder(order, true)` and has to navigate to the function definition to learn what `true` means. Worse, the next requirement adds a second flag, and now you have four code paths in one function with implicit dependencies between flags.

### Anti-pattern

```python
def send_notification(user, urgent=False):
    if urgent:
        sms_provider.send(user.phone, "Urgent action required")
        log.warning("urgent_notification_sent", user_id=user.id)
        metrics.increment("notifications.urgent")
    else:
        email_provider.send(user.email, "Update available")
        log.info("notification_sent", user_id=user.id)
        metrics.increment("notifications.standard")
```

Two side effects, two log levels, two metrics, two channels. The function name `send_notification` is true at a useless level of abstraction. Call sites read `send_notification(user, True)` — what does `True` mean? Urgent? Async? Encrypted? The call site does not say.

### Better approach

```python
def send_urgent_sms(user):
    sms_provider.send(user.phone, "Urgent action required")
    log.warning("urgent_notification_sent", user_id=user.id)
    metrics.increment("notifications.urgent")

def send_standard_email(user):
    email_provider.send(user.email, "Update available")
    log.info("notification_sent", user_id=user.id)
    metrics.increment("notifications.standard")
```

Two functions, two responsibilities, two test surfaces. Call sites read like prose: `send_urgent_sms(user)`. No flag interpretation required.

### Why this wins

- Call sites self-document. `send_urgent_sms(user)` is unambiguous; `send_notification(user, True)` is not.
- Each function has one reason to change. Adding a third channel does not require touching the existing two.
- Tests target one behavior per function instead of "with-flag and without-flag" matrices.

### Why the alternative loses

- The next requirement adds `async=True`, then `dry_run=True`, then `lang="es"`. Four flags = sixteen call combinations, most of which were never tested.
- Refactoring becomes risky because the function does too much.
- Call-site code reviews cannot judge correctness without inspecting the callee.

### When this principle yields

When the boolean is genuinely orthogonal data (e.g., `enabled: True` for a feature toggle inside a config object), it is data, not a behavior switch. The test is whether the function's name still describes one job after the flag is added. If you'd want to rename the function with the new flag, split instead.

### Verification

Each call site reads as a sentence describing the action. A grep for `, True)` or `, False)` in the codebase returns very few results, and each has an obvious justification.

## Principle 2: Use domain types for domain values

State: when a value carries business rules (money, identifiers, percentages, durations, statuses), give it a type. Primitives invite mistakes.

### What goes wrong without it

`process_payment(123, 4567, 8900)` — what is each number? Amount in cents? Amount in dollars? User ID? Order ID? Cents charged in a different currency? The type system cannot help you because all three are `int`. The bug surface is "any future caller passes the wrong arg in the wrong slot," and the failure mode is "wrong amount charged to the wrong user."

### Anti-pattern

```typescript
function chargeUser(userId: string, orderId: string, amount: number): Promise<void> {
  return paymentGateway.charge({ userId, orderId, amount })
}

// Caller, written six months later by someone else:
chargeUser(order.id, user.id, order.total)  // userId and orderId swapped, amount in dollars not cents
```

The compiler accepts every argument because they are all `string` or `number`. The bug ships. A user is charged for someone else's order, in the wrong currency unit. The fix involves manual reconciliation and refunds.

### Better approach

```typescript
type UserId = string & { readonly __brand: "UserId" }
type OrderId = string & { readonly __brand: "OrderId" }
type Cents = number & { readonly __brand: "Cents" }

function userId(s: string): UserId { return s as UserId }
function orderId(s: string): OrderId { return s as OrderId }
function cents(n: number): Cents {
  if (!Number.isInteger(n) || n < 0) throw new Error("invalid cents")
  return n as Cents
}

function chargeUser(userId: UserId, orderId: OrderId, amount: Cents): Promise<void> {
  return paymentGateway.charge({ userId, orderId, amount })
}

// Caller, six months later:
chargeUser(order.userId, order.id, order.totalCents)  // would not compile if swapped
```

The compiler now refuses to swap the arguments. The `cents` constructor refuses to accept floating-point dollar amounts. Mistakes are pushed to the boundary where data enters the system, not into the middle of business logic.

### Why this wins

- Mistakes that previously shipped to production now fail at the keyboard.
- Reading code at the call site is unambiguous: you know `order.userId` is a `UserId`, not a random string.
- New team members cannot accidentally invent the wrong unit.

### Why the alternative loses

- Bugs caught only by integration testing or production are 1000x more expensive than bugs caught by the compiler.
- Documentation describing "amount must be in cents" is rarely read at the call site.
- Mixing units in math (`order.amountDollars + tax.amountCents`) is a runtime bug, not a compile error.

### When this principle yields

When the value genuinely is a primitive with no business rules (a counter for a debug log line, the index of a loop variable), wrapping it adds noise without preventing bugs. The test is whether passing the wrong primitive in the wrong slot would be a real bug. If yes, type it.

### Verification

Search the codebase for raw `string`/`number`/`int` parameters in business-facing function signatures. Each one without a domain type is a question: would the compiler help here?

## Principle 3: One-implementation interfaces are usually ceremony

State: an interface (or abstract class) with one implementation is justified only when it protects a real boundary. Otherwise it is the fingerprint of speculative design.

### What goes wrong without it

The codebase grows a parallel naming system: `UserService` / `IUserService` / `UserServiceImpl` / `UserServiceFactory` / `UserServiceProvider`. None of them adds testability (the concrete class was already testable). None of them adds flexibility (there is still one implementation). All of them add navigation cost when reading the code.

### Anti-pattern

```java
public interface IPaymentProcessor {
    Result process(Payment p);
}

public class PaymentProcessorImpl implements IPaymentProcessor {
    @Override
    public Result process(Payment p) {
        return gateway.charge(p);
    }
}

public class PaymentProcessorFactory {
    public static IPaymentProcessor create() {
        return new PaymentProcessorImpl();
    }
}

// Used at exactly one call site, once:
IPaymentProcessor processor = PaymentProcessorFactory.create();
processor.process(payment);
```

Three classes for one operation. Reading the code requires three jumps. There is no second implementation, no plugin point, no actual variation — just patterns applied for their own sake.

### Better approach

```java
public class PaymentProcessor {
    public Result process(Payment p) {
        return gateway.charge(p);
    }
}

// Call site:
new PaymentProcessor().process(payment);
```

If a second implementation appears (a sandbox processor, a queue-based processor, a test fake that doesn't hit the network), introduce the interface at that point. The cost of refactoring later is small; the cost of carrying speculative ceremony forever is large.

### Why this wins

- Reading is faster. Navigating `PaymentProcessor.process` goes one level, not three.
- New team members do not have to learn an indirection that exists for no current reason.
- The factory disappears. Static factories with no decisions to make are pure ceremony.

### Why the alternative loses

- The interface freezes a shape based on today's ignorance. The day a second implementation arrives, the interface is usually wrong for it.
- "Interface for testing" is almost always a smell — testable code does not need an interface, it needs a clean boundary.
- The team learns a wrong lesson: that abstraction is good per se. They apply it to the next module too.

### When this principle yields

Three legitimate cases for one-implementation interfaces:

1. The interface defines a boundary you genuinely plan to swap (cloud provider, payment gateway with planned multi-vendor) within 6 months, with a concrete second implementation in mind.
2. The interface enables a test fake that cannot be expressed by composing the real class (e.g., an external service with no in-process mode).
3. The interface is the public surface of a library you ship to others, and you need the freedom to evolve the implementation independently.

If none of those apply, keep it concrete.

### Verification

`grep` for `interface` (or `abstract class`) in the codebase. For each, count the implementations. One implementation should be a small, justifiable list with a one-line reason next to each entry.

## Principle 4: Encapsulate behavior, not state

State: a class that exposes its data and asks callers to operate on it has not encapsulated anything. Move the behavior to the data's owner.

### What goes wrong without it

Business logic spreads across every caller. The class becomes a passive bag, and the same operation gets re-implemented (subtly differently) in three places. The rule "an order is overdue if not paid 30 days after invoice" becomes:

- `if (order.invoiceDate + 30 < today && !order.paid)` in one route
- `if ((today - order.invoiceDate).days > 30 && order.status != 'paid')` in another
- `if (order.invoiceDate.add(days=30).before(today) && !order.isPaid())` in a third

Three implementations, three subtle bugs, three places to fix when the rule changes.

### Anti-pattern

```python
class Order:
    def __init__(self, invoice_date, status):
        self.invoice_date = invoice_date
        self.status = status

# Spread across the codebase:
def show_overdue_warning(order, today):
    if order.invoice_date + timedelta(days=30) < today and order.status != "paid":
        render("overdue_warning.html")

def send_late_fee_email(order, today):
    if (today - order.invoice_date).days > 30 and order.status != "paid":
        emailer.send_late_fee(order)

def export_overdue_report(orders, today):
    overdue = [o for o in orders if o.invoice_date.add(days=30).before(today) and not o.is_paid()]
    return overdue
```

Three callers, three implementations of the same business rule, three tests that disagree on edge cases.

### Better approach

```python
class Order:
    def __init__(self, invoice_date, status):
        self.invoice_date = invoice_date
        self.status = status

    def is_overdue(self, as_of):
        days_since_invoice = (as_of - self.invoice_date).days
        return days_since_invoice > 30 and self.status != "paid"

# Callers become readable:
def show_overdue_warning(order, today):
    if order.is_overdue(today):
        render("overdue_warning.html")

def send_late_fee_email(order, today):
    if order.is_overdue(today):
        emailer.send_late_fee(order)

def export_overdue_report(orders, today):
    return [o for o in orders if o.is_overdue(today)]
```

One rule, one place, three callers. When the rule changes ("90 days for enterprise customers, 30 days for everyone else"), one method changes.

### Why this wins

- Business rules live near the data they operate on, where the rules will be looked for.
- Three subtly different implementations collapse into one tested truth.
- Changes to the rule are local, not cross-cutting.

### Why the alternative loses

- Rules drift apart. Each caller implements them slightly differently, and tests that exist for one path do not protect the others.
- Refactoring the data shape becomes a 30-file diff.
- New team members re-implement the rule a fourth time because they did not know about the other three.

### When this principle yields

When the operation genuinely belongs to a different concern (e.g., rendering an order in HTML belongs to a view layer, not the domain model). The test is whether the operation depends only on the data of the object plus its arguments. If yes, it is a method on the object. If it depends on rendering, transport, or persistence concerns, it lives elsewhere.

### Verification

Search the codebase for repeated patterns of "access fields of class X and apply the same conditional." Each cluster is a candidate method on X.

## Principle 5: Reduce before you add

State: before adding a config option, a helper, a wrapper, an abstraction, or a dependency, ask what can be removed instead.

### What goes wrong without it

Codebases grow monotonically when no one is asked to subtract. After two years, the team has 47 config options, most of which are set the same in every environment, and three of which interact in ways no one fully understands.

### Anti-pattern

```yaml
# config/production.yml — six months in:
api:
  enable_v2_routes: true
  enable_legacy_compat: false
  enable_strict_validation: true
  enable_request_logging: true
  enable_request_logging_v2: false  # added because v1 had a bug, never removed
  enable_response_compression: true
  enable_response_compression_brotli: true  # supersedes brotli flag below
  enable_brotli: false
  enable_metrics_export: true
  enable_legacy_metrics_export: true  # nobody knows if this matters
  ...
```

Each option started as a careful rollout flag. None were removed after rollout completed. The configuration file is now archaeology — half the flags are dead, but no one has the time to prove which half safely.

### Better approach

The professional habit: every flag has a removal trigger from the day it is added.

```yaml
# Instead of adding `enable_v2_routes: true` indefinitely,
# the PR that adds it also adds:
#
#   .deprecation/enable_v2_routes.md:
#     Trigger to remove: 100% rollout for 7 days with no incidents
#     Owner: @platform-team
#     Removal includes: config key, code branch, related tests
```

When the rollout completes, a follow-up PR removes the flag, the legacy code branch, and the tests for the legacy branch. The config file shrinks instead of growing.

### Why this wins

- The system stays understandable. A new contributor does not have to read 47 dead flags to understand the live behavior.
- Bugs from flag interaction stop appearing because the surface is bounded.
- The team's time is spent on real work, not flag archaeology.

### Why the alternative loses

- Flag interaction bugs are some of the hardest to diagnose because they reproduce only in specific config combinations.
- Documentation describing what each flag does goes stale immediately.
- The system's behavior is not knowable from reading the code; you must also read the config and the deployment.

### When this principle yields

When the flag protects a genuine kill switch for a system that cannot be safely modified post-deployment (e.g., a flag that disables an outbound integration during a known incident pattern). Such flags should be tagged "permanent" with an explicit reason.

### Verification

The number of config options trends down or stays flat over time, not up. A periodic audit (quarterly, or via a `LAST_USED` annotation in code) removes flags that are not exercised in any current path.

## Principle 6: Layout and names beat comments

State: if you reach for a comment to explain what code does, your first instinct should be to rename or restructure. Comments belong where code cannot reach: external context, why-not-what, surprising tradeoffs.

### What goes wrong without it

Comments drift. Code is checked by the compiler and tests; comments are checked only by goodwill. Six months after a refactor, the comment still describes the old behavior, and a new contributor reads the comment, trusts it, and ships a bug.

### Anti-pattern

```javascript
// Increment counter
function inc(c) {
  return c + 1
}

// Loop through users and check if each one is active
// If so, send them the daily digest
function processUsers(users) {
  for (let i = 0; i < users.length; i++) {
    const u = users[i]
    if (u.s === "a") {  // status active
      // call email service
      es.send(u.e, makeDigest(u))  // u.e is email
    }
  }
}
```

Every comment is restating what the code already says — at the cost of being wrong if the code changes. The variable names are doing zero work; the comments are doing all of it.

### Better approach

```javascript
function sendDailyDigestToActiveUsers(users, emailService) {
  for (const user of users) {
    if (user.status === "active") {
      emailService.send(user.email, buildDailyDigest(user))
    }
  }
}
```

No comments. The function name says what it does, the variable names say what they hold, and the loop body is one readable sentence. If `processUsers` ever did something subtler, the comment was the wrong fix — the right fix was always renaming.

The comments that remain in this file are now meaningful:

```javascript
// We send digests in alphabetical order of email so that customer support
// can replay a day's batch by re-running with the same input. Do not change
// the iteration order without coordinating with the support runbook.
function sendDailyDigestToActiveUsers(users, emailService) { ... }
```

That comment explains *why*, mentions an external constraint (the support runbook), and would not be obvious from the code alone.

### Why this wins

- Names and structure are checked by the compiler and reviewers; they cannot lie for long.
- The reading flow stays unbroken — no need to constantly compare prose against code.
- The comments that survive carry real information, so readers actually trust them.

### Why the alternative loses

- Inline restating-comments rot the moment the code changes, and they rarely get updated.
- Readers learn to ignore comments because most are noise, then miss the rare important ones.
- A wrong comment is worse than no comment: it actively misleads.

### When this principle yields

Comments are the right tool for: external context (RFC numbers, ticket links), explanations of *why* a non-obvious choice was made, mathematical proofs, performance notes, and warnings about constraints not visible in code (deployment order, concurrent caller assumptions).

### Verification

Inline comments in the codebase are mostly *why*, not *what*. A reviewer reading a diff with new inline comments asks: would a rename or extract have made this comment unnecessary? If yes, do that instead.

## Routing

Use `@tank/clean-code` for detailed function, naming, modularity, and refactoring smells.

Use `@tank/ast-linter-codemod` when a design rule needs to be enforced at scale (e.g., banning a specific pattern across the codebase).

Use `js-tools` for TypeScript moves, renames, import organization, and file splits — structural refactors are safer with symbol-aware tooling.

Use `references/refactoring-and-removal.md` when the right move is to remove or reshape existing code, not to add a better design.

Use `references/conflict-resolution.md` when simplicity conflicts with extensibility, performance, or compatibility.
