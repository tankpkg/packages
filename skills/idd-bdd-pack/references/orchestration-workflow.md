# Orchestration Workflow

Sources: ArcBlock/idd three-layer model (MIT), FORGE phase-gate TDD (MIT),
BDD E2E testing patterns from @tank/bdd-e2e-testing skill.

Covers: Layer-to-Gherkin conversion, constraint-to-assertion mapping,
combined lifecycle sequence, sync checklist, directory mirroring rules,
common integration anti-patterns.

## The Bridge Model

IDD and BDD operate on different layers of the same system. The bridge
connects them at three points:

```
.idd/                                    .bdd/
┌──────────────────────┐                 ┌──────────────────────┐
│ INTENT.md            │                 │ features/            │
│                      │                 │                      │
│ Layer 3: Examples ───┼──── converts ──►│ Gherkin scenarios    │
│                      │                 │                      │
│ Layer 2: Constraints─┼──── informs ───►│ Step assertions      │
│                      │                 │                      │
│ Layer 1: Structure ──┼──── mirrors ───►│ Directory layout     │
│                      │                 │                      │
└──────────────────────┘                 └──────────────────────┘
```

The arrows are one-directional. Intent drives tests. Tests never modify
intent files — that feedback flows through the IDD sync process (Step 8).

## Layer 3 → Gherkin Scenarios

Layer 3 examples are input-output pairs. Each row in the Examples table
becomes at least one Gherkin scenario.

### Conversion Process

**1. Read the Examples table from INTENT.md**

```markdown
## Examples

| Input | Output |
|-------|--------|
| authenticate("valid@test.com", "correct") | Session { status: "active" } |
| authenticate("valid@test.com", "wrong") | AuthError { code: "INVALID_CREDENTIALS" } |
| authenticate("locked@test.com", "any") | AuthError { code: "ACCOUNT_LOCKED" } |
```

**2. Convert each row to a Gherkin scenario**

```gherkin
# .bdd/features/auth/login.feature

Feature: User Authentication
  Users authenticate with email and password to receive a session.

  Scenario: Successful login with valid credentials
    Given a registered user "valid@test.com" with password "correct"
    When the user authenticates with email "valid@test.com" and password "correct"
    Then the response contains a session with status "active"

  Scenario: Login fails with wrong password
    Given a registered user "valid@test.com" with password "correct"
    When the user authenticates with email "valid@test.com" and password "wrong"
    Then the response contains an auth error with code "INVALID_CREDENTIALS"

  Scenario: Login fails when account is locked
    Given a locked user account "locked@test.com"
    When the user authenticates with email "locked@test.com" and password "any"
    Then the response contains an auth error with code "ACCOUNT_LOCKED"
```

### Conversion Rules

| Intent Example Pattern | Gherkin Pattern |
|----------------------|-----------------|
| Single input → single output | One Scenario |
| Input with variations (same function, different args) | Scenario Outline with Examples table |
| Input → error output | Scenario with "Then the response contains an error" |
| Input → side effect ("session created in DB") | Scenario with "Then a session record exists in the database" |

### When to Use Scenario Outline

If 3+ examples share the same structure with different values, use
Scenario Outline instead of repeating the full scenario:

```gherkin
Scenario Outline: Login fails with invalid credentials
  Given a registered user "<email>"
  When the user authenticates with email "<email>" and password "<password>"
  Then the response contains an auth error with code "<error_code>"

  Examples:
    | email              | password | error_code            |
    | valid@test.com     | wrong    | INVALID_CREDENTIALS   |
    | locked@test.com    | any      | ACCOUNT_LOCKED        |
    | unknown@test.com   | any      | INVALID_CREDENTIALS   |
```

### What NOT to Convert

Not every intent example becomes a Gherkin scenario. Skip conversion when:

| Example Type | Why Skip | What to Do Instead |
|-------------|----------|--------------------|
| Internal implementation detail | BDD tests user-visible behavior | Unit test in the source tree |
| Performance assertion ("p95 < 200ms") | Gherkin is wrong tool for load tests | Performance test script |
| Static analysis rule ("no imports from X") | Not runtime behavior | CI lint rule |

## Layer 2 → Step Assertions and CI Rules

Layer 2 constraints are rules the system must obey. They map to two
BDD artifact types: step assertions (for runtime rules) and CI checks
(for static rules).

### Classifying Constraints

Read each row in the Constraints table and classify it:

| Constraint | Type | BDD Artifact |
|-----------|------|--------------|
| "All auth errors return 401, never 403" | Runtime behavior | Step assertion in `.bdd/steps/` |
| "Rate limit: 5 attempts per minute per IP" | Runtime behavior | Gherkin scenario |
| "Auth module never imports from payments" | Static/architectural | CI lint rule |
| "All DB queries use parameterized statements" | Static/code quality | Static analysis in CI |
| "Response time < 200ms at p95" | Performance | Load test script |

### Runtime Constraints → Step Assertions

Runtime constraints that apply across multiple scenarios become shared
assertion patterns in step definitions:

```typescript
// .bdd/steps/auth.steps.ts

// Constraint: "All auth errors return 401, never 403"
Then('the response contains an auth error with code {string}', async ({ page }, code: string) => {
  const response = await page.waitForResponse('**/api/auth/**');
  expect(response.status()).toBe(401);
  expect(response.status()).not.toBe(403);

  const body = await response.json();
  expect(body.code).toBe(code);
});
```

The constraint becomes an invariant inside the step — every scenario
that triggers an auth error automatically verifies the 401 rule.

### Runtime Constraints → Dedicated Scenarios

Some runtime constraints deserve their own Gherkin scenario, especially
rate limiting, timeout behavior, and concurrency rules:

```gherkin
# .bdd/features/auth/rate-limiting.feature

Feature: Authentication Rate Limiting
  The system limits login attempts to prevent brute force attacks.

  Scenario: Sixth login attempt within one minute is rate limited
    Given a registered user "user@test.com"
    When the user fails authentication 5 times within 60 seconds
    And the user attempts authentication a 6th time
    Then the response status is 429
    And the response contains an error with code "RATE_LIMITED"
```

### Static Constraints → CI Rules

Static constraints do not become BDD scenarios. They become CI pipeline
checks that run outside `.bdd/`:

```yaml
# In CI pipeline, not in .bdd/
- name: Check boundary violations
  run: |
    # Constraint: "Auth module never imports from payments"
    if grep -r "from.*payments" src/auth/ --include="*.ts"; then
      echo "VIOLATION: auth imports from payments"
      exit 1
    fi
```

Document which constraints map to CI rules vs BDD scenarios in the
intent file's Constraints table — add a "Verified by" column:

| Rule | Rationale | Verified by |
|------|-----------|-------------|
| All auth errors return 401 | Consistent client error handling | BDD step assertion |
| Auth never imports payments | Module boundary | CI lint rule |
| Rate limit 5/min per IP | Brute force prevention | BDD scenario |

## Layer 1 → Directory Mirroring

Layer 1 structure diagrams define module boundaries. These map directly
to directory organization in `.bdd/features/`.

### Mirroring Rule

Every module directory in `.idd/modules/` gets a matching directory in
`.bdd/features/`:

```
.idd/modules/          .bdd/features/
  auth/         →        auth/
  payments/     →        payments/
  notifications/→        notifications/
```

This is mandatory. A feature file in `.bdd/features/auth/` tests behavior
defined in `.idd/modules/auth/INTENT.md`. The directory name is the
traceability link.

### When Modules Don't Map 1:1

Sometimes a single intent module generates multiple feature files, or
multiple intent modules share a cross-cutting feature:

| Situation | Solution |
|-----------|----------|
| One module, many features | Multiple `.feature` files in one directory |
| Cross-module behavior | Feature in a `cross-cutting/` directory with clear module tags |
| Shared constraints | Shared step definitions in `.bdd/steps/`, referenced by multiple features |

## Combined Lifecycle

The IDD lifecycle (9 steps) and BDD verification interleave at specific
points. Do not run them in parallel — follow this sequence:

| Phase | IDD Activity | BDD Activity |
|-------|-------------|--------------|
| 1. Assess | Decide if IDD is appropriate | — |
| 2. Init | Scaffold `.idd/` | Scaffold `.bdd/` (mirror module dirs) |
| 3. Interview | Extract decisions, write INTENT.md | — |
| 4. Critique | Trim intent, enforce budget | — |
| 5. Lock | Mark stable sections | — |
| 6. Plan | Break intent into phased plan | Identify which examples become scenarios |
| 7. Build | Write code (TDD within IDD) | Write Gherkin features + step definitions |
| 8. Sync | Reconcile intent vs code | Check: every Layer 3 example has a scenario |
| 9. Audit | Measure health score | Run full E2E suite, document findings |

### When BDD Enters the Cycle

BDD work starts at **Step 6 (Plan)**. Before that, the intent is still
forming — writing scenarios against draft intent wastes effort.

At Step 6, the intent is critiqued, stable sections are locked, and
examples are concrete enough to convert to Gherkin.

### The Build Phase Handshake

During Step 7 (Build), IDD's internal TDD and BDD's E2E testing
coexist but serve different purposes:

| Test Type | Written During | Purpose | Location |
|-----------|---------------|---------|----------|
| IDD unit tests | Build phase, RED→GREEN→REFACTOR | Verify implementation against intent | Source tree (`src/`) |
| BDD E2E tests | Build phase, after unit tests pass | Verify behavior against real system | `.bdd/` |

Run IDD unit tests first. When they pass, run BDD E2E tests. If E2E
tests fail, fix the application code — never weaken the scenario.

**No mocking in either layer. This rule is non-negotiable.** Both IDD
functional tests and BDD E2E tests run against real systems — real
databases, real APIs, real services. Do not introduce mocks, stubs, fakes,
or in-memory replacements. If a dependency is unavailable, stop and tell
the user. Do not silently substitute a mock to unblock yourself. A test
suite that passes against mocks proves nothing about whether the software
actually works. When fixing bugs, add the bug as an edge case to the
intent Examples table and write a functional test — not a "regression test."

## Sync Checklist

During IDD Step 8 (Sync), extend the standard sync process with BDD
cross-checks:

### Standard IDD Sync Checks

1. Compare INTENT.md against code — categorize diffs as New/Changed/Confirmed/Removed
2. Update intent with what actually shipped
3. Add sync marker

### Additional BDD Cross-Checks

Run these after the standard sync:

| Check | How | Action on Failure |
|-------|-----|-------------------|
| Every Layer 3 example has a scenario | Compare Examples table rows to `.bdd/features/{module}/*.feature` | Write missing scenario |
| Every runtime Layer 2 constraint has a step assertion | Check Constraints table "Verified by" column | Add assertion to step definition |
| No orphan features | Check `.bdd/features/{module}/` has matching `.idd/modules/{module}/` | Delete orphan feature or create missing intent |
| Feature directory mirrors module directory | Compare directory names | Rename to match |
| BDD findings reference intent sections | Check `.bdd/qa/findings/` mention intent source | Add traceability to findings |

### Sync Report Extension

Add a BDD section to the standard sync report:

```markdown
## BDD Coverage

| Module | Layer 3 Examples | Gherkin Scenarios | Coverage |
|--------|-----------------|-------------------|----------|
| auth | 8 | 7 | 87% |
| payments | 5 | 5 | 100% |
| notifications | 3 | 1 | 33% |

### Missing Scenarios
- auth: "authenticate with expired token" — no scenario exists
- notifications: "send email on new device login" — no scenario exists
- notifications: "rate limit notification delivery" — no scenario exists

### Orphan Scenarios (no intent backing)
- None found
```

## Traceability

Every BDD artifact should trace back to an intent source. This is how:

### Feature File Header

Add a comment linking to the intent module:

```gherkin
# Intent: .idd/modules/auth/INTENT.md
# Layer: Examples (rows 1-3)

Feature: User Authentication
  ...
```

### Findings Reference

When documenting BDD findings in `.bdd/qa/findings/`, reference the
intent constraint or example that the test verifies:

```markdown
# Finding: Rate Limiting Not Enforced

**Intent source:** .idd/modules/auth/INTENT.md, Constraints table, row 3
**Constraint:** "Rate limit: 5 attempts per minute per IP"
**Expected:** 6th attempt returns 429
**Actual:** 6th attempt returns 200 (rate limiter not wired)
```

This closes the loop: intent defines the rule, BDD tests it, findings
document the gap, resolution fixes the code.

## Common Integration Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Writing scenarios before intent is critiqued | Scenarios based on draft intent get rewritten when intent changes | Wait until Step 6 (Plan) to write scenarios |
| BDD scenarios that test implementation details | Scenarios coupled to code structure, not behavior | Write declarative scenarios from Layer 3 examples |
| Modifying intent to match failing tests | Reverses the flow — intent should drive tests | Fix application code, not intent |
| Skipping the sync BDD cross-check | Layer 3 examples and scenarios drift apart | Add BDD checks to every sync cycle |
| Putting CI lint rules in `.bdd/` | Static constraints are not BDD scenarios | Keep lint rules in CI pipeline, outside `.bdd/` |
| One giant feature file per module | Hard to maintain, slow to run | One feature file per behavior cluster |
| No traceability comments in feature files | Can't trace scenario back to intent | Add intent source comment to every feature |
| Testing locked intent sections differently | Locked sections are stable — tests should be stable too | Lock corresponding BDD scenarios (don't modify without change proposal) |

---

For IDD methodology details, see the `@tank/idd` skill.
For BDD testing patterns, see the `@tank/bdd-e2e-testing` skill.
