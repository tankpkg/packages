# Refactoring and Removal

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Fowler (Refactoring); Martin's Boy Scout Rule; Beck (Tidy First?); Tank clean-code, ast-linter-codemod, and js-tools skills

Covers: how to change code structure without changing behavior, how to delete code safely, when to leave duplication alone, and how to keep refactors reviewable.

## Operating Standard

Refactoring is not "make it pretty." It is the disciplined practice of changing the structure of code without changing the behavior that anyone — users, callers, downstream systems — depends on. The discipline is what separates a refactor from a rewrite.

Two truths shape the work. First, every refactor risks behavior change. The author thinks the change is structural; sometimes the test suite proves them right and sometimes it doesn't. The professional habit is to assume "I might be wrong about which behaviors matter" and let evidence (tests, characterization data, customer reports) settle the question. Second, removed code is the cheapest code: zero bugs, zero maintenance, zero onboarding cost. The professional habit is to subtract before adding.

A coding agent's refactor work is judged by the same bar as a senior engineer's pull request: is the diff atomic, is behavior preserved (with evidence), is the change reviewable in isolation, and does the result reduce future cost more than the present cost of the change? If any answer is "I'm not sure," the answer is to slow down, slice the change, and add evidence — not to ship and hope.

## Quick Routing

| Situation | Principle to apply |
| --------- | ------------------ |
| About to "clean up while I'm here" inside a feature commit | Principle 1: Refactor and feature commits are separate |
| About to refactor untested legacy code | Principle 2: Characterize before changing |
| Tempted to fix a small unrelated thing during a bigger change | Principle 3: Boy Scout rule, with proportion |
| Adding a wrapper, helper, or abstraction | Principle 4: Removal beats addition |
| Two functions look similar — should they be merged? | Principle 5: Same shape is not same concept |
| Done refactoring? Tempted to keep going? | Principle 6: Stop at the boring part |

## Principle 1: Refactor and feature commits stay separate

State: a single commit should do one of: change behavior (feature/fix) or preserve behavior (refactor). Mixing them makes both unreviewable and unrevertable.

### What goes wrong without it

The PR description says "fix login redirect." The diff has 47 files. Five of them contain the actual fix; 42 are unrelated cleanup. The reviewer either rubber-stamps the whole thing (accepting unknown risk) or blocks on the cleanup (delaying the fix). When a regression appears two weeks later, `git revert` undoes both the fix and the cleanup — and the cleanup might have included something the team now depends on.

### Anti-pattern

```
Branch: fix/login-redirect
Commit message: "fix: login redirect after timeout"
Diff:
  src/auth/login.ts                    (the actual 5-line fix)
  src/auth/middleware.ts               (renamed three variables)
  src/auth/session.ts                  (extracted a helper)
  src/users/repository.ts              (replaced any with proper types — 30 lines)
  src/users/types.ts                   (new file, generated DTOs)
  package.json                         (upgraded date-fns)
  package-lock.json
  .eslintrc.json                       (added new rule)
  src/auth/login.test.ts               (test for the fix)
  src/users/*.test.ts                  (12 test files updated for new types)
```

The commit's stated purpose is "fix login redirect." Almost none of the diff is about that. A reviewer cannot focus on the actual fix without scrolling through unrelated work. A revert undoes everything.

### Better approach

Six commits, six PRs, in dependency order:

```
1. refactor(users): replace any with explicit DTOs
   - src/users/repository.ts, src/users/types.ts, src/users/*.test.ts (renamed types only)
   - Behavior preserved; tests pass with the same assertions on the same data.

2. chore(deps): upgrade date-fns to 3.x
   - package.json, package-lock.json
   - Behavior preserved; date-fns 3 is API-compatible for our usage; tests pass.

3. chore(eslint): enable no-floating-promises
   - .eslintrc.json
   - One existing violation suppressed with an issue link; not in this PR's scope to fix.

4. refactor(auth): extract session helper
   - src/auth/session.ts only
   - Behavior preserved; same call sites get same results.

5. refactor(auth): rename middleware locals for clarity
   - src/auth/middleware.ts only
   - No behavior change; reviewer can read in 30 seconds.

6. fix(auth): redirect to original URL after login timeout
   - src/auth/login.ts, src/auth/login.test.ts
   - Reproduces the bug in a failing test, fixes it, test passes.
```

Each is independently reviewable. The fix can ship today. The dependency upgrade can ship tomorrow with proper review. A revert touches one commit and one concern.

### Why this wins

- Reviewers engage at the right level for each change. Refactors get reviewed for behavior preservation; the fix gets reviewed for correctness.
- Bisecting later (when "something broke around the login work") points at the exact commit responsible.
- Reverting a regression undoes only the broken change.
- The team can ship the fix on a tight timeline without blocking on the cleanup.

### Why the alternative loses

- Wide diffs hide regressions inside unrelated work. A bug introduced by the dependency upgrade looks like a bug in the fix.
- Reverting a wide diff is destructive: rolling back the fix also rolls back the type improvements that other PRs now depend on.
- Cleanup work becomes coupled to feature timelines, so cleanup gets blocked or rushed.

### When this principle yields

When two changes are genuinely inseparable — a type definition added in the same commit as the only file that uses it, a database migration plus the model change that depends on it — they belong together. The test is whether one could be reverted without breaking the other. If revert-of-A leaves the system in a worse state than before-A-was-added, A and B are one commit.

### Verification

`git log --oneline` shows commits with single-purpose messages. Each commit's diff is reviewable in under 5 minutes. Reverting any commit produces a system that still builds and still passes the tests for the behaviors not being reverted.

## Principle 2: Characterize before changing untested legacy

State: untested code is not "code that doesn't have tests yet." It is code whose actual behavior is unknown to anyone except the runtime. Add tests that pin down current behavior before you change anything.

### What goes wrong without it

The team refactors a 300-line shipping-cost calculator that has no tests. The new version is shorter and clearer. Six weeks later, an enterprise customer reports that international shipments to certain countries are being charged $3.49 too much. The bug is in the refactor — it changed an edge case the original handled by accident. The fix requires reading both the old and new code (the old one is in `git log`, the new one is in production), figuring out which behavior is "correct," and shipping a third version. The original "harmless cleanup" cost two engineer-weeks and one customer escalation.

### Anti-pattern

```python
# Old code: 300 lines, no tests, "messy but works."
def calculate_shipping_cost(order, destination):
    # Layered conditionals, magic numbers, a few comments referencing 2019 tickets,
    # special cases for "AK", "HI", "PR", "GU", a pricing override for orders over
    # $500 to certain countries, and a /16-digit lookup table for ZIP code zones.
    ...

# Refactor PR: "Clean up shipping calculation."
def calculate_shipping_cost(order, destination):
    return ShippingCalculator(destination).calculate(order)  # 5 lines, much cleaner!
```

The new code might handle 99% of orders identically. The team has no way to know which 1% changed.

### Better approach

```python
# Step 1: Capture current behavior with a parameterized characterization test,
#         using representative orders from production data (anonymized).
import json
import pytest

# Pulled from production logs: 200 representative (order, destination, expected_cost) tuples.
with open("tests/fixtures/shipping_characterization.json") as f:
    CHARACTERIZATION_CASES = json.load(f)

@pytest.mark.parametrize("case", CHARACTERIZATION_CASES, ids=lambda c: c["description"])
def test_shipping_cost_preserves_existing_behavior(case):
    actual = calculate_shipping_cost(case["order"], case["destination"])
    assert actual == case["expected_cost_cents"], (
        f"behavior changed for {case['description']!r}: "
        f"old behavior was {case['expected_cost_cents']}, new behavior is {actual}"
    )

# Step 2: Run against the OLD code to confirm all 200 cases pass.
#         This proves the fixture data correctly captures current behavior.

# Step 3: Refactor.

# Step 4: Run again. Tests fail? Each failure is a behavior change.
#         For each, decide: was the old behavior a bug to fix, or a contract to preserve?
#         Document the decision in the commit message.
```

The characterization tests aren't beautiful. Many of them codify behavior that is genuinely wrong (the $3.49 overcharge to certain countries was an actual bug nobody knew about). That's fine — the point is that *change is now visible*. The team can decide which "bugs" to fix and which to preserve, with full evidence.

### Why this wins

- Behavior changes during refactor are explicit, not accidental.
- "Should we fix this old bug while we're here?" becomes a deliberate decision with customer-impact evaluation, not a silent surprise weeks later.
- The commit history shows exactly which behaviors changed and why, so future maintainers can trace customer-reported issues back to specific decisions.
- Customers depending on the existing behavior (which often includes its bugs) are not blindsided.

### Why the alternative loses

- Untested refactors silently change behavior. The bugs surface as customer reports months later, by which time the change is buried under unrelated work and bisecting is expensive.
- "We refactored it; it's cleaner" is not a defense when production behavior changed in ways nobody anticipated.
- The original code's intent — including its bugs — is lost, with no paper trail of what was deliberately preserved vs. accidentally changed.

### When this principle yields

When the legacy code is provably broken in obvious ways (it crashes on most inputs, returns nonsense, was never used in production), characterization is pointless. In that case, write tests for the *desired* behavior and frame the change as a fix, not a refactor. The test is whether you can prove that nobody depends on current behavior. If you cannot prove it, characterize.

### Verification

The characterization fixture contains representative inputs from production data — not just the cases the original author thought of. Tests pass against the old code before any refactor begins. Test failures during the refactor map to deliberate decisions documented in commit messages.

## Principle 3: Boy Scout rule, with proportion

State: leave code better than you found it — but the improvement should be proportional to the task. A typo fix is fine; a 200-line restructuring of an unrelated module is not.

### What goes wrong without it

"Boy Scout" becomes license for unbounded scope creep. A one-line bug fix turns into a six-PR cleanup spree because the author "noticed some things while in there." Reviewers cannot tell which changes are necessary and which are incidental. The original bug fix is delayed. Other team members reviewing the PR push back, the author feels their initiative is being punished, and the team learns that improvement is socially expensive.

### Anti-pattern

```
Original task: "Fix the typo in the error message."
Branch: fix/typo

Commit 1: "fix: correct typo in InvalidEmail error message"
Commit 2: "refactor: extract email validation to its own module"
Commit 3: "refactor: replace regex email validation with mature library"
Commit 4: "test: add 47 new email validation test cases"
Commit 5: "refactor: also fix the phone number validation since it had the same problem"
Commit 6: "chore: upgrade test framework while I'm in the test files"

Total: 312 lines changed across 18 files for a typo fix.
```

Most of the work is genuinely improvement. None of it is what the team agreed to ship today. The reviewer cannot say "yes, ship the typo fix" without also saying "yes, ship a new dependency, a refactor, and a major test refactor."

### Better approach

The Boy Scout move is to leave a small bread crumb, not to undertake the larger work mid-task:

```
Commit: "fix: correct typo in InvalidEmail error message"
  - 1 line changed in src/auth/errors.ts
  - 1 test updated to match new message

Follow-up issue created: "Email validation has multiple inconsistencies"
  - Includes notes from this PR on what was noticed (regex vs library mismatch,
    similar issue in phone number validation, gaps in test coverage).
  - Triaged into the team backlog.
```

The typo fix ships today. The improvements are recorded with full context, owned, and prioritized — not lost, not coupled to an urgent fix.

### Why this wins

- The original task ships on time without scope creep blocking it.
- The improvements are not lost; they enter the backlog with the context the original author noticed.
- Future work on the email validation module benefits from a clear, focused PR rather than archaeology.

### Why the alternative loses

- Wide PRs increase the chance that some unrelated change introduces a regression that gets attributed to the original task.
- Reviewers either become rubber-stampers (accepting risk) or blockers (delaying everything).
- The team learns that improvement is socially expensive, so smaller improvements stop happening.

### When this principle yields

For genuinely trivial cleanups directly adjacent to the change — fixing a typo two lines below the line you're editing, removing a dead variable that the linter was already flagging — the Boy Scout move is fine. The test is whether the cleanup would have been worth its own commit. If yes, give it one. If no, just do it inline.

### Verification

The PR's diff stays roughly aligned with the title and description. If the diff is much larger than the title implies, either the title is wrong or the diff has too much in it.

## Principle 4: Removal beats addition

State: before adding code, check whether existing code can be removed. Deleted code has zero bugs, zero maintenance cost, and zero onboarding burden.

### What goes wrong without it

Codebases grow monotonically. Every team member adds; nobody is asked to subtract. After two years, the codebase has 47 helper functions that are wrappers around 12 underlying operations, six "utility" modules with overlapping responsibilities, and twelve config flags that have been on for everyone for a year. A new contributor's first month is spent learning all of it.

### Anti-pattern

```typescript
// Existing code, organically grown:
export function getUserById(id: string) { return db.users.findById(id) }
export function fetchUserById(id: string) { return getUserById(id) }
export function loadUser(id: string) { return fetchUserById(id) }
export function getUser(id: string) { return loadUser(id) }
export function findUser(id: string) { return getUser(id) }
export function userById(id: string) { return findUser(id) }

// New PR adds:
export function lookupUser(id: string) { return userById(id) }
//        ^ author needed "lookup" to match a different module's naming convention.
```

Seven functions, one underlying call. Each was added because the author needed a slightly different name. Nobody removed anything because removal "might break a caller."

### Better approach

Audit and delete:

```typescript
// Step 1: Find all callers of each helper. (LSP, grep, or symbol-finder.)
// Step 2: Pick the one name that fits the codebase's domain language.
//         Suppose `findUser` is the convention used in surrounding modules.
// Step 3: Migrate all callers to that one name (codemod or LSP rename).
// Step 4: Delete the rest.

export function findUser(id: string): User | null {
  return db.users.findById(id)
}

// All other helpers deleted. Lock files, docs, tests updated.
// PR description: "Removed six redundant user-lookup helpers; standardize on findUser."
```

The codebase shrinks. New contributors learn one name. Future "I need this with a slightly different name" PRs are blocked at review with a pointer to the convention.

### Why this wins

- The cognitive surface of the codebase shrinks. Every new contributor's onboarding gets cheaper.
- Bugs from "which helper does what subtly differently?" disappear.
- The codebase has fewer places to look when tracing a bug, fewer test files to maintain, fewer docs to keep in sync.

### Why the alternative loses

- Adding without removing is a one-way ratchet that compounds over years.
- Each helper has its own subtle behaviors that drift over time, even if they started as wrappers.
- The team's collective time is spent on archaeology and convention disagreements rather than user-visible work.

### When this principle yields

When the existing helpers genuinely encapsulate different concerns (`fetchUserFromCache` vs `fetchUserFromDB`), removal is the wrong move; what's needed is clearer names. The test is whether the helpers do different things or just have different names. If different names, delete. If different things, rename for clarity.

### Verification

Periodically (quarterly, or as part of larger refactors) the team audits a module and lists helpers that wrap a single operation. Each one without a distinct purpose gets a removal PR.

## Principle 5: Same shape is not same concept

State: two functions that look alike are not necessarily duplications worth merging. If they encode different business concepts, they will diverge — and if they have been merged, the merge will become an awkward conditional later.

### What goes wrong without it

Two functions that compute "30 days" — one for a payment grace period, one for a subscription renewal window — get merged because they look alike. Six months later, finance asks for the payment grace period to extend to 60 days for enterprise customers. The merged helper now has an `if isPayment` branch. A year later, subscriptions need quarterly renewals (90 days) for some plans; another `if isSubscription` branch is added. The "DRY" helper is now the messiest part of the codebase, and the team is afraid to touch it because both billing and subscription logic depend on it.

### Anti-pattern

```python
# Original code: two functions, same shape, different concepts.
def days_until_payment_overdue(invoice):
    return (invoice.due_date + timedelta(days=30) - today()).days

def days_until_subscription_renewal(subscription):
    return (subscription.last_renewed + timedelta(days=30) - today()).days

# "DRY violation!" — merged into:
def days_until(record, days=30):
    return (record.reference_date + timedelta(days=days) - today()).days
```

Two business concepts (overdue grace period; renewal cadence) are now hidden behind one parameter. When billing wants 60 days for enterprise, the change has to thread a `days` argument through every caller — including subscription callers that should not be affected. The conceptual coupling is now mechanical coupling.

### Better approach

Keep them separate. The shape is similar; the concepts are not:

```python
PAYMENT_GRACE_DAYS = 30  # business rule from the AR team
SUBSCRIPTION_RENEWAL_DAYS = 30  # business rule from the product team

def days_until_payment_overdue(invoice):
    return (invoice.due_date + timedelta(days=PAYMENT_GRACE_DAYS) - today()).days

def days_until_subscription_renewal(subscription):
    return (subscription.last_renewed + timedelta(days=SUBSCRIPTION_RENEWAL_DAYS) - today()).days
```

When billing wants 60 days for enterprise customers, only `PAYMENT_GRACE_DAYS` (or the related logic) changes. Subscription behavior is untouched and untouchable. The two domains evolve independently because they were never coupled.

### Why this wins

- Each function changes for one reason. Adding "60-day grace for enterprise" does not require thinking about subscription behavior.
- The business owner of each concept (AR team for payments, product team for subscriptions) can request changes without negotiating with the other team.
- Tests for each domain are independent. A bug in one doesn't risk regressing the other.

### Why the alternative loses

- The "DRY" merge couples two business concepts that have nothing to do with each other.
- Every future change that affects one concept has to be evaluated against the other ("does this break subscriptions?"), slowing every change.
- The merged helper accumulates conditionals over time and becomes the worst part of the codebase to read.

### When this principle yields

When the two functions genuinely encode the same business rule expressed in different places (e.g., two routes both implement "user must be active to perform this action"), they should be merged — the rule is one concept being repeated. The test is whether the rule for one is the rule for the other. If a change to one would also be a change to the other, merge. If not, leave them.

### Verification

For each "DRY violation" candidate, ask: "if requirements changed for case A but not case B, would the merged helper still work?" If yes, merge. If no, leave them separate and document why above each.

## Principle 6: Stop at the boring part

State: refactoring has a natural stopping point. When the next change becomes "I could keep going but the value is marginal," stop, ship, and let real future work guide the next round.

### What goes wrong without it

The author keeps refactoring. Each change feels worth it in isolation, but the PR grows from 30 lines to 300 to 800. Reviewers lose context. The original goal is buried. A regression slips in because the author was focused on aesthetics rather than behavior. The team loses two weeks reviewing a change that should have shipped on day one.

### Anti-pattern

```
Day 1: "Refactor the OrderService to extract a helper."
       Diff: +30, -20. PR is reviewable.

Day 2: "I noticed we could rename these methods for consistency."
       Diff: +30, -20. PR still reviewable.

Day 3: "Now I'm going to extract the payment logic into its own service."
       Diff: +200, -150. PR getting big.

Day 4: "And the inventory logic too."
       Diff: +400, -300.

Day 5: "Now that the services are split, let me update the tests."
       Diff: +600, -450.

Day 7: "I had to update the API documentation. And the OpenAPI spec. And...
       Diff: +1200, -800.

Reviewers at this point: nobody can confidently approve this.
```

The original change was good. Each subsequent change was defensible. But the cumulative result is a PR that no reviewer can fully audit, and any regression in production will be impossible to bisect.

### Better approach

```
Day 1: "Refactor the OrderService to extract a helper."
       Ship it. Reviewers approve in 30 minutes. Merged.

Day 2: New PR: "Rename methods in OrderService for consistency."
       Ship it.

Day 3: New PR: "Extract payment logic into PaymentService."
       Ship it. (Or pause: is this work justified by a real near-term change?
       If not, it can wait until the change motivates it.)

...
```

Each PR is reviewable. Each can be merged or rolled back independently. The team builds confidence in each step before moving to the next.

### Why this wins

- Every PR is mergeable. Production gets the early benefits without waiting for the long tail.
- A regression in any step is bisected to one commit.
- The author can stop at any point and the work delivered so far is still valuable.
- Reviewers stay engaged because they can review meaningfully in a reasonable amount of time.

### Why the alternative loses

- Long-running refactor branches go stale, conflict with main, and become permanently expensive to merge.
- The author burns out before finishing. The branch is abandoned. The work is lost.
- A regression that ships in a 1200-line PR is nobody's fault and everyone's problem.

### When this principle yields

When a change genuinely cannot be split — a database migration that requires a coordinated schema and data change in one transaction — keep them together. The test is whether each step leaves the system in a working state. If every step is independently shippable, ship them independently. If some intermediate state would break production, group only the inseparable parts.

### Verification

PRs land within hours or days, not weeks. Each commit is independently revertable. The author can describe what each commit accomplishes in one sentence.

## Routing

Use `@tank/clean-code` for the smell-by-smell refactoring catalog (extract method, replace conditional with polymorphism, etc.).

Use `@tank/ast-linter-codemod` when the same mechanical refactor needs to be applied across many files — codemods are safer than hand-edits at scale.

Use `js-tools` for TypeScript-specific structural operations: rename, move, organize imports, extract symbol, find references.

Use `references/testing-and-verification.md` for the characterization-test patterns that make refactors safe.

Use `references/conflict-resolution.md` when refactor goals conflict with deadlines, performance, or compatibility.
