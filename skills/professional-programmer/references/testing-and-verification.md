# Testing and Verification

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Meszaros (xUnit Test Patterns); Beck (TDD by Example); Smart/Molak (BDD in Action); Tank bdd-e2e-testing and bulletproof skills

Covers: what tests should prove, how to write tests that survive refactoring, and how to verify behavior under real failure conditions.

## Operating Standard

Tests are engineering evidence. Their job is to prove that the system behaves as users and dependent systems require, to catch regressions before production, and to communicate intent to the next maintainer. A test that does none of those things is decoration — it adds maintenance cost without adding signal.

Two failure modes dominate. First, tests that pass for the wrong reason: they assert that a function was called, not that the user got the right outcome. These tests pass when the implementation is broken in any way the mock doesn't notice. Second, tests that fail for the wrong reason: they break on harmless refactors because they couple to internal structure, training the team to "fix the test" without thinking. Both failures destroy the test's value as evidence.

A coding agent's job is to write tests that fail when users would care and pass when users would not. Test names should describe the behavior under test in domain language. Test data should make the scenario obvious from one read of the test. Test setup should match the real production wiring closely enough that "it works in the test" implies "it will work in production."

## Quick Routing

| Situation | Principle to apply |
| --------- | ------------------ |
| Test asserts that a mock was called | Principle 1: Test behavior, not implementation |
| Test data is `foo`, `bar`, `user1`, `42` | Principle 2: Concrete test data names the scenario |
| Test name describes the function instead of the behavior | Principle 3: Tests are documentation |
| You are about to refactor untested legacy code | Principle 4: Characterization tests before refactor |
| A test fails sometimes and passes if you rerun | Principle 5: Diagnose flakes, do not retry them |
| You just shipped a fix without adding a test | Principle 6: Bug fix means failing test first |

## Principle 1: Test behavior, not implementation

State: assert what users or dependent systems observe, not what your code does internally. If the test fails on a refactor that preserves user-visible behavior, the test was wrong.

### What goes wrong without it

Tests calcify the implementation. Every refactor breaks ten tests, none of which are catching real bugs. The team learns to update the tests to match the new internals, which means the tests are now passive transcripts of the code rather than active checks of behavior. Real bugs ship because the tests provide false confidence.

### Anti-pattern

```typescript
// Testing a "send password reset email" feature.
test("sendPasswordReset calls validateUser then findUserByEmail then mailer.send", async () => {
  const validateUser = jest.fn().mockResolvedValue(true)
  const findUserByEmail = jest.fn().mockResolvedValue({ id: "u_1", email: "alice@example.com" })
  const send = jest.fn().mockResolvedValue(undefined)

  await sendPasswordReset("alice@example.com", { validateUser, findUserByEmail, mailer: { send } })

  expect(validateUser).toHaveBeenCalledWith("alice@example.com")
  expect(findUserByEmail).toHaveBeenCalledAfter(validateUser)
  expect(send).toHaveBeenCalledWith(expect.objectContaining({ to: "alice@example.com" }))
})
```

This test asserts the order of internal function calls. If we refactor `sendPasswordReset` to look up the user first and validate second (functionally identical from the user's perspective), the test breaks. If we replace the three internal helpers with one consolidated function, the test breaks. None of those changes affect user behavior — but the test punishes them.

Worse: the test passes even if `mailer.send` is never actually wired to a real email provider, because the mock just records the call. The user never gets the email; the test is happy.

### Better approach

```typescript
// Test against a real mailer (in-process fake) and assert the observable outcome.
test("password reset sends an email with a usable reset link", async () => {
  const mailer = new InMemoryMailer()
  const userStore = new InMemoryUserStore([{ id: "u_1", email: "alice@example.com" }])

  await sendPasswordReset("alice@example.com", { mailer, userStore })

  const sent = mailer.lastSentTo("alice@example.com")
  expect(sent).toBeDefined()
  expect(sent.subject).toContain("Reset your password")
  const resetLink = extractResetLink(sent.body)
  expect(resetLink).toMatch(/^https:\/\/example\.com\/reset\?token=[a-f0-9]{32}$/)
  expect(await tokenStore.find(extractToken(resetLink))).toEqual({ userId: "u_1", validUntil: expect.any(Date) })
})

test("password reset is silent for unknown emails", async () => {
  const mailer = new InMemoryMailer()
  const userStore = new InMemoryUserStore([])

  await sendPasswordReset("ghost@example.com", { mailer, userStore })

  expect(mailer.allSent()).toEqual([])
})
```

Both tests assert what the user can observe: an email arrives with a working reset link, or no email arrives at all. The implementation can call helpers in any order, consolidate them, or extract them — the tests stay green as long as the user-visible behavior holds.

### Why this wins

- Refactors that preserve behavior do not break tests. Refactors that break behavior do.
- The tests double as living documentation of what the feature does for users.
- A new contributor reading the tests can describe the feature without reading the implementation.

### Why the alternative loses

- Tests that assert call order or mock invocations are coupled to today's implementation, which means they actively block tomorrow's improvements.
- Mock-based tests can pass when the integration is broken (the mock returns a fake success), so they do not protect production.
- The team learns that "fix the test" means "make it match the new code," which is the opposite of what tests are for.

### When this principle yields

When the implementation has a contractual obligation to call a specific external service (e.g., audit logs that must record a specific event), asserting the call is asserting a behavior. The test is whether the call is the user-observable behavior or just an internal step.

### Verification

Take the test suite, refactor an internal function (split it, rename it, inline it), and run the suite. Tests that fail on refactors are the ones to rewrite around behavior.

## Principle 2: Concrete test data names the scenario

State: test data should make the scenario obvious from one read. `user1`, `foo`, and `42` hide the scenario; `expiredSubscriptionUser` and `declinedTransaction` reveal it.

### What goes wrong without it

A test failure points at the test, but the test data is `user1` and `42`. To understand what the test is asserting, the reader has to navigate to the helper that creates `user1`, find what attributes it has, and infer which attribute matters for this test. With domain-named data, the failure message and the test name often suffice on their own.

### Anti-pattern

```python
def test_apply_discount():
    user = make_user()
    cart = make_cart()
    cart.items.append(make_item(price=10))
    cart.items.append(make_item(price=20))
    code = "SAVE10"

    total = apply_discount(user, cart, code)

    assert total == 27  # ?
```

Why is the answer 27? The reader has to navigate to `make_user`, `make_cart`, `make_item`, and then to `apply_discount` to figure out the discount rule. Is `SAVE10` a 10% discount? A $10 discount? Does it depend on the user being eligible? Is the user eligible? The test does not say.

### Better approach

```python
def test_save10_promo_takes_ten_percent_off_for_returning_customers():
    customer = ReturningCustomer(email="alice@example.com", first_purchase_at=days_ago(180))
    cart = Cart(items=[
        Item(name="USB cable", price_cents=1000),
        Item(name="HDMI cable", price_cents=2000),
    ])

    result = apply_discount(customer, cart, code="SAVE10")

    assert result.discount_cents == 300       # 10% of 3000
    assert result.total_cents == 2700
    assert result.discount_reason == "returning_customer_promo"

def test_save10_promo_rejected_for_first_purchase():
    customer = NewCustomer(email="bob@example.com")
    cart = Cart(items=[Item(name="USB cable", price_cents=1000)])

    result = apply_discount(customer, cart, code="SAVE10")

    assert result.discount_cents == 0
    assert result.total_cents == 1000
    assert result.rejection_reason == "first_purchase_not_eligible"
```

Now the test name announces the rule. The data names the scenario (returning vs new customer). The expected number is computable from the data and the rule, with a comment explaining the math. The rejection case is a separate test that announces a different rule.

### Why this wins

- A test failure says "save10 promo takes ten percent off for returning customers FAILED: expected 2700, got 3000," and the reader has enough context to start debugging.
- The discount rule is documented in test names. New team members learn the business rules from reading the test file.
- Adding a new rule case ("staff_promo applies on top of save10") becomes a new clearly-named test, not a modification of an opaque one.

### Why the alternative loses

- "test_apply_discount FAILED: expected 27, got 30" gives the reader nothing.
- Generic data hides the variable that matters. A bug that only triggers for returning customers might be invisible if every test uses `make_user()` which happens to return a new customer.
- New team members write more tests in the same generic style because that is what the file looks like.

### When this principle yields

For pure utility code with no domain (a date parser, a string formatter), generic-looking data is fine because there is no domain to encode. The test is whether the test data carries any business meaning. If yes, name it.

### Verification

Read the test name and the expected value. Ask: can I tell why this number is correct from those two alone? If not, the test data needs to name the scenario, or the test needs a one-line comment explaining the math.

## Principle 3: Tests are documentation

State: name tests around behavior the user or dependent system can observe, not around the function being called. Tests are the most-read piece of documentation in any codebase.

### What goes wrong without it

Tests named `test_validateUser_calls_db` and `test_validateUser_returns_object` are useless as documentation. They tell you what the function does, but only after you read the function. They do not tell you what behavior the system promises. When the function is renamed, the tests become misnamed.

### Anti-pattern

```javascript
describe("UserService", () => {
  describe("validateUser", () => {
    it("calls findById", async () => { /* ... */ })
    it("returns user object", async () => { /* ... */ })
    it("throws on not found", async () => { /* ... */ })
  })
})
```

Three tests, three internal-implementation names. To learn what `UserService` does for the system, you have to read each test body and reverse-engineer the contract.

### Better approach

```javascript
describe("user authentication", () => {
  it("accepts a valid user with the correct password", async () => { /* ... */ })
  it("rejects a valid user with an incorrect password", async () => { /* ... */ })
  it("rejects a request for an unknown email without revealing whether the email exists", async () => { /* ... */ })
  it("locks the account after five failed attempts within an hour", async () => { /* ... */ })
  it("clears the failed-attempt counter on a successful authentication", async () => { /* ... */ })
})
```

These names form a contract. A new contributor reading the test file learns the authentication rules: passwords are checked, unknown-email responses do not leak existence, accounts lock after five failures, success clears the counter. None of that requires reading the implementation.

### Why this wins

- Tests double as living documentation. The contract changes when the test names change, which they should, because the contract did.
- A failing test name names a violated rule, not a violated function.
- Renaming or restructuring the implementation does not require renaming tests.

### Why the alternative loses

- Implementation-named tests rot the moment the implementation changes name.
- The contract of the system is hidden in test bodies, so newcomers cannot scan the file to understand what the code promises.
- Test-driven development becomes "make the function I just wrote pass" instead of "describe the behavior I want."

### When this principle yields

For genuinely internal helper functions with no externally-visible behavior, a function-named test is acceptable as long as the helper itself is justified. The test is whether the test would be the same if the function were rewritten — if yes, name it after the function; if no, name it after the behavior.

### Verification

A reader who has never seen the implementation can describe the system's contract from the test file alone. If they cannot, the tests are not documentation.

## Principle 4: Characterization tests before refactor

State: before changing untested legacy code, write tests that pin down its current behavior. Then refactor with those tests as a safety net.

### What goes wrong without it

A "harmless" refactor of a 200-line tax calculation function silently changes a rounding edge case. The change ships. Three months later, an enterprise customer files a bug ("our quarterly tax report is off by $0.03 per invoice"). Tracing the bug requires bisecting the refactor, which is now buried under unrelated commits. The fix is small but the cost of finding it is large, and customer trust is now a recurring cost.

### Anti-pattern

```python
# Untested 200-line tax function. The team decides to "clean it up."
def calculate_tax(invoice):
    # 200 lines of nested conditionals, magic numbers, and historical quirks
    ...

# After refactor:
def calculate_tax(invoice):
    return InvoiceTaxCalculator(invoice).calculate()  # cleaner!
```

The new code might be cleaner. It might also have changed five edge cases that the original handled by accident. Without tests, neither the author nor the reviewer can say which of those is true.

### Better approach

```python
# Step 1: Capture current behavior with characterization tests, before any refactor.
import pytest

REPRESENTATIVE_INVOICES = [
    # (description, invoice_dict, expected_tax_cents)
    ("simple US sale, single state",
     {"items": [{"price_cents": 10000, "category": "general"}], "ship_to": "CA"}, 875),
    ("multi-state nexus, mixed categories",
     {"items": [{"price_cents": 5000, "category": "general"}, {"price_cents": 3000, "category": "food"}],
      "ship_to": "NY"}, 425),
    ("digital good, no tax",
     {"items": [{"price_cents": 9900, "category": "digital"}], "ship_to": "TX"}, 0),
    ("rounding edge: tax computes to .005",
     {"items": [{"price_cents": 5715, "category": "general"}], "ship_to": "WA"}, 565),
    # ...20-50 more representative cases covering the matrix the original code handles
]

@pytest.mark.parametrize("description,invoice,expected", REPRESENTATIVE_INVOICES)
def test_calculate_tax_preserves_existing_behavior(description, invoice, expected):
    assert calculate_tax(invoice) == expected, f"behavior changed for: {description}"

# Step 2: Refactor. The tests catch any accidental change.
# Step 3: If a test now fails, decide: was the old behavior a bug we want to fix,
#         or a contract we must preserve? Update the test or the code accordingly,
#         and document the decision in the commit message.
```

The characterization tests are not pretty. Some of them codify behavior that is genuinely wrong (an off-by-one rounding bug from 2018). That is fine — the point is to make change visible. After the refactor, the team can decide which "bugs" to fix and which to preserve, with full evidence of what changed.

### Why this wins

- The refactor's effect on behavior is visible. Tests fail when behavior changes; nothing fails when behavior is preserved.
- "Bug or feature?" decisions are made deliberately, with a customer-impact evaluation, not accidentally during cleanup.
- Customers depending on the existing behavior are not surprised by silent changes.

### Why the alternative loses

- Untested refactors silently change behavior, and the bugs surface months later as customer complaints.
- The original author's intent (good or bad) is lost, and the new code becomes the de facto truth without a paper trail.
- Bisecting customer-impacting bugs to a refactor that touched 200 lines is expensive engineering time.

### When this principle yields

When the legacy code has obvious, total bugs (it crashes on every input, or it returns nonsense), characterizing the current behavior is pointless. In that case, write tests for the desired behavior and treat the change as a bug fix. The test is whether anyone could be depending on the current behavior. If "no" is provable, skip characterization. If you can't prove "no," characterize.

### Verification

The characterization tests cover representative inputs from production data (not just the test cases the original author thought of). The refactor commit either passes those tests as-is or includes deliberate test updates with commit-message rationale.

## Principle 5: Diagnose flaky tests, do not retry them

State: a test that passes "if you rerun it" is hiding a real defect — usually concurrency, time-dependence, or shared state. Retrying conceals the defect; diagnosing fixes it.

### What goes wrong without it

CI gets a "rerun failed jobs" button, and the team uses it. A genuinely failing test gets retried into green and the bug ships. The flake count rises, trust in CI drops, and eventually engineers stop investigating real failures because "it's probably just a flake." The signal is gone.

### Anti-pattern

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    steps:
      - run: npm test
        # "test sometimes fails, just rerun it"
        retry: 3
```

CI runs the test up to three times. Most flakes pass on retry. Real bugs that match the flake's symptom also pass on retry. The team has no way to tell the difference.

### Better approach

When a flake appears, treat it as a bug:

```javascript
// Original flaky test:
test("user appears in search results after creation", async () => {
  await createUser({ name: "Alice" })
  const results = await searchUsers({ query: "Alice" })
  expect(results).toContainEqual(expect.objectContaining({ name: "Alice" }))
})
```

Diagnose: the search index is updated asynchronously. The test passes when the index update happens fast enough; it fails when it doesn't. The fix is not "retry the test" or "add a `sleep(1000)`." The fix is to make the indexing latency observable and assert on the contract:

```javascript
test("user appears in search results after creation", async () => {
  const created = await createUser({ name: "Alice" })

  // Wait for the explicit indexing signal, with a timeout that fails the test
  // (rather than letting it hang forever) and a clear error message.
  await waitFor(
    () => searchUsers({ query: "Alice" }),
    (results) => results.some((r) => r.id === created.id),
    { timeoutMs: 5000, description: "user 'Alice' indexed in search" },
  )

  const results = await searchUsers({ query: "Alice" })
  expect(results).toContainEqual(expect.objectContaining({ name: "Alice", id: created.id }))
})
```

`waitFor` waits up to a bounded timeout for the indexing to complete, fails clearly if it does not, and asserts the actual contract: "after creation, search returns the user within 5 seconds."

### Why this wins

- The test now describes the real contract (indexing latency) rather than relying on luck.
- A real indexing regression (latency exceeds 5s) fails the test — which is exactly what we want.
- CI signal is restored: a failing test means a real bug.

### Why the alternative loses

- Retrying flaky tests trains everyone to ignore failures. Real bugs slip through.
- `sleep(1000)` is brittle (slow when the system is fast, fast when the system is slow) and grows over time as people increase the timeout to "fix" intermittent failures.
- Quarantined-but-never-fixed flakes accumulate, and eventually the quarantine list is longer than the active suite.

### When this principle yields

When the test relies on a genuinely external service that is provably flaky (a third-party API with documented uptime), retrying with backoff is acceptable, but the retry should be inside the test (with a clear timeout), not at the CI level. The test is whether the flake is in *our* code or *theirs*. Ours we fix; theirs we wrap with explicit timeouts and clear failure messages.

### Verification

The CI dashboard shows zero retries on green builds and zero quarantined tests with no owner. Each retry or quarantine has a tracking issue with an owner and a deadline.

## Principle 6: A bug fix means a failing test, then a passing one

State: every bug fix begins by writing a test that reproduces the bug. The test fails (red). The fix makes it pass (green). The fix ships with the test.

### What goes wrong without it

A bug is fixed without a regression test. Six months later, an unrelated refactor reintroduces the same bug. Nobody notices until the same customer files the same ticket. The team has effectively paid for the same bug twice.

### Anti-pattern

```
Commit message: "fix: handle empty cart"
Diff:
  - return cart.items.reduce((sum, item) => sum + item.price, 0)
  + return cart.items?.length ? cart.items.reduce((sum, item) => sum + item.price, 0) : 0
```

The fix is correct. There is no test. Six months later, someone refactors `cart.items` to always be an array (no more nullable), removes the `?.length` check as "dead code," and the bug returns. Without a test, the refactor was justified ("the check is dead, the type is non-null"); with a test, the refactor would have failed CI immediately.

### Better approach

```javascript
// Step 1: Write the test that reproduces the bug. It should fail.
test("cart total is zero when there are no items", () => {
  const emptyCart = new Cart({ items: [] })
  expect(calculateCartTotal(emptyCart)).toBe(0)
})

// Run: this test fails because calculateCartTotal throws on empty cart.

// Step 2: Fix the code.
function calculateCartTotal(cart) {
  if (cart.items.length === 0) return 0
  return cart.items.reduce((sum, item) => sum + item.priceCents, 0)
}

// Run: the test passes.

// Step 3: Commit both the test and the fix together.
//   Commit message: "fix: cart total returns 0 for empty cart (was throwing)"
```

Now any future refactor that reintroduces the bug fails the test. The bug cannot recur silently.

### Why this wins

- The bug cannot regress without someone explicitly deleting the test. That is now a deliberate choice with visible cost, not an accident.
- The commit history shows the bug, the test, and the fix together. A future maintainer reading `git blame` on the line sees both the bug it was fixing and the test that protects it.
- The test names the user-visible problem ("cart total is zero when there are no items"), so it stays meaningful even if the implementation changes.

### Why the alternative loses

- Bugs without regression tests are landmines for future refactors.
- "We fixed it, we don't need a test" is the same logic that made the bug ship in the first place.
- Customers who hit the bug twice lose trust. "Didn't you already fix this?" is a conversation engineering does not want to have.

### When this principle yields

When the bug is in code being deleted in the same change, the test would be deleted too — adding it is busywork. The test is whether the affected code path will continue to exist. If yes, write the test.

### Verification

Every bug-fix commit includes a test in the same commit. A `git log -- path/to/test_file` should show the test landing alongside the fix, with a commit message that names the bug.

## Routing

Use `@tank/bdd-e2e-testing` when the right test is a Gherkin scenario, a Playwright multi-context flow, or a real-system end-to-end check.

Use `@tank/bulletproof` when the work requires both intent definition and real-system proof in one workflow.

Use `references/correctness-and-state.md` when the testing question is "what behavior must I prove?" rather than "how do I prove it?"

Use `references/refactoring-and-removal.md` for the characterization-test workflow when refactoring legacy code.
