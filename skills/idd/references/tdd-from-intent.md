# TDD from Intent

Sources: ArcBlock/idd test categories (MIT), FORGE Generate phase TDD protocol (MIT),
Praxis intent-spec-code model (MIT), Beck (Test-Driven Development by Example).

Covers: deriving tests from intent layers, six test categories, phased TDD execution,
E2E gate scripts, commit conventions, coverage requirements, common failure modes.

## No Mocking — This Is Non-Negotiable

**You must follow this rule. There are no soft exceptions, no "just this
once," no "it's faster with mocks." Every test in IDD runs against the
real system.**

Real database. Real API. Real queue. Real file system. Real Redis. Not
an in-memory fake. Not a stub. Not a "lightweight replacement." The real
dependency, running, accessible, and behaving exactly as production does.

A test that passes against a mock proves one thing: that the mock works.
It proves nothing about whether the software works. Mocks drift from real
behavior silently — they accept any query shape, never return unexpected
fields, never timeout, never enforce constraints. When reality differs
from the mock, you find out in production. That is unacceptable.

| Situation | What you must NOT do | What you must do |
|-----------|---------------------|-----------------|
| Database needed | Use in-memory SQLite instead of PostgreSQL | Spin up real PostgreSQL (Docker, testcontainer, local) |
| External API needed | Mock the HTTP client | Call the real API (use a sandbox/test account) |
| Redis needed | Use a JS object as fake cache | Run real Redis |
| Queue needed | Use an array as a fake queue | Run real RabbitMQ/SQS/etc. |
| Service unavailable | Stub it and keep going | **Stop.** Tell the user: "dependency X is unavailable, cannot run tests." |
| "But it's slow with real deps" | Switch to mocks for speed | Optimize the real setup. Slower real tests beat fast fake ones. |

**The only exception:** The user explicitly says "mock X" or "stub Y for
now" — for a specific, named dependency. Even then, add a comment:
`// TODO: remove mock — test against real {X}`. The mock is technical
debt from the moment it's written.

**If you are an AI agent reading this: you are not permitted to introduce
mocks, stubs, fakes, spies, or in-memory replacements into the test suite.
If you find yourself about to write `jest.mock`, `sinon.stub`,
`unittest.mock.patch`, `httptest.NewServer`, or any equivalent — stop.
You are violating this rule. Use the real dependency or tell the user you
cannot proceed without it.**

## Bugs Are Edge Cases, Not Regressions

When a bug is found, do not write a "regression test." IDD does not have
regression tests. Bugs are missing edge cases in the intent specification.

**The workflow:**

1. A bug is discovered (user report, production incident, manual testing)
2. Identify which module's intent it belongs to
3. Add the bug's scenario to that module's INTENT.md Examples table as an
   edge case row — with the input that triggers the bug and the expected
   (correct) output
4. Write a functional test for that new edge case row. Run it. Confirm
   it fails (RED) against the current code
5. Fix the code. Confirm the test passes (GREEN)
6. The bug is now part of the specification permanently

**Why this matters:** A "regression test" lives in the test suite but has
no connection to the intent. It tests an implementation detail that broke
once. An edge case in the Examples table is a permanent part of the module's
contract. It survives refactors, rewrites, and team changes because it's
specification, not patch history.

```markdown
## Examples (updated after bug #247)

| Input | Output | Category |
|-------|--------|----------|
| `login("valid@test.com", "correct")` | `Session { status: "active" }` | Happy |
| `login("valid@test.com", "wrong")` | `AuthError { code: "INVALID_CREDS" }` | Error |
| `login("VALID@Test.COM", "correct")` | `Session { status: "active" }` | Edge (bug #247) |
```

The third row was a bug — case-sensitive email matching. Now it's an edge
case. Every future implementation must handle it because the intent says so.

## Deriving Tests from Intent Layers

Intent files carry three layers of information. Each layer maps to a distinct
test type. Read the intent file before writing a single test.

| Layer | Content | Maps to | Test type |
|-------|---------|---------|-----------|
| Layer 1: Structure | Directory trees, data flow diagrams, component boundaries | Integration tests | Verify modules connect at the right seams |
| Layer 2: Constraints | Constraint table (rule + rationale) | Assertion statements, lint rules | Verify invariants hold under all conditions |
| Layer 3: Examples | Input/output pairs in Examples table | Unit and acceptance tests | One row = one test case, minimum |

### Layer 1 → Integration Boundaries

Structure diagrams define where modules touch. Every arrow in a data flow
diagram is a potential integration test boundary. Do not test internals of
each box — test the connections between boxes.

From a diagram showing `Auth Middleware → Session DB` and `Rate Limiter → Redis`,
write integration tests that confirm:
- Auth Middleware calls Session DB with the correct query shape
- Rate Limiter reads from Redis before passing the request
- A request blocked by Rate Limiter never reaches Auth Middleware

### Layer 2 → Assertions and Lint Rules

Each row in the Constraints table becomes a test assertion or a static check.

| Constraint | Test form |
|------------|-----------|
| `Auth module never imports from payments` | Lint rule: `no-restricted-imports` or grep in CI |
| `All DB queries use parameterized statements` | Static analysis rule or test that raw string queries fail |
| `Response time < 200ms at p95` | Performance test with timing assertion |
| `Rate limit: 5 attempts per minute per IP` | Test that the 6th attempt within 60s returns 429 |
| `All auth errors return 401, never 403` | Test every error path returns exactly 401 |

Constraints with a "Rationale" column tell you what breaks if the constraint
fails. Use that rationale to name the test.

### Layer 3 → Test Cases

Each row in the Examples table is a test case. Copy the table, then implement
each row as a test. Do not skip rows — every example is a specification.

```typescript
// From intent Examples table:
// | authenticate("valid@test.com", "correct") | Session { status: "active" } |
it("returns active session for valid credentials", async () => {
  const session = await authenticate({ email: "valid@test.com", password: "correct" });
  expect(session.status).toBe("active");
});

// | authenticate("valid@test.com", "wrong") | AuthError { code: "INVALID_CREDENTIALS" } |
it("returns INVALID_CREDENTIALS for wrong password", async () => {
  await expect(authenticate({ email: "valid@test.com", password: "wrong" }))
    .rejects.toMatchObject({ code: "INVALID_CREDENTIALS" });
});
```

If an Examples row is ambiguous, clarify it in the intent file before writing
the test. Ambiguous examples produce ambiguous tests.

## The Six Test Categories

ArcBlock/idd defines six categories. Every module needs tests in all six.
Error paths should outnumber happy paths — production systems fail more
ways than they succeed.

### 1. Happy Path

Normal successful operations. Keep these minimal — one per distinct success mode.

| What to test | Example |
|--------------|---------|
| Primary success case | `authenticate(valid credentials)` → active session |
| Secondary success cases | `authenticate(admin credentials)` → admin session |
| Successful side effects | Session created in DB after login |
| Correct return shape | Response matches the API contract in intent |

### 2. Error Path

Known failure modes. Must outnumber happy paths. Every constraint describing
a failure condition becomes an error path test.

| What to test | Example |
|--------------|---------|
| Invalid input | Wrong password, malformed email, missing fields |
| Resource not found | User does not exist |
| Precondition failures | Account locked, email unverified |
| Downstream failures | DB unavailable, Redis timeout |
| Correct error codes | 401 not 403, 400 not 500 |
| Error message safety | Error body does not leak internal details |

```typescript
it("returns 401 when account is locked, not 403", async () => {
  const result = await authenticate({ email: "locked@test.com", password: "any" });
  expect(result.statusCode).toBe(401);
});

it("does not reveal whether email exists in error message", async () => {
  const result = await authenticate({ email: "nonexistent@test.com", password: "wrong" });
  expect(result.message).not.toContain("not found");
  expect(result.message).not.toContain("does not exist");
});
```

### 3. Edge Cases

Boundary values, empty inputs, extremes, and off-by-one conditions.

| What to test | Example |
|--------------|---------|
| Empty strings | `authenticate({ email: "", password: "" })` |
| Null / undefined | Missing fields entirely |
| Maximum length inputs | Email at 254 characters (RFC 5321 limit) |
| Unicode and special characters | Passwords with emoji, RTL text in names |
| Exactly at rate limit boundary | 5th attempt succeeds, 6th fails |

```typescript
it("accepts exactly 5 login attempts before rate limiting", async () => {
  for (let i = 0; i < 5; i++) {
    await authenticate({ email: "user@test.com", password: "wrong" });
  }
  await expect(authenticate({ email: "user@test.com", password: "wrong" }))
    .rejects.toMatchObject({ code: "RATE_LIMITED" });
});
```

### 4. Security

Auth bypass, injection, brute force, and data leakage. Security tests hit
the real system — the real auth layer, the real database, the real rate
limiter. A mocked auth layer cannot prove the defense works. This is where
violating the no-mock rule is most dangerous and most tempting. Do not
give in.

| What to test | Example |
|--------------|---------|
| SQL injection | `email: "' OR '1'='1"` |
| NoSQL injection | `password: { "$gt": "" }` |
| JWT tampering | Modified token signature |
| Privilege escalation | User token accessing admin endpoint |
| Session fixation | Session ID rotates after login |
| Timing attacks | Response time constant regardless of user existence |

### 5. Data Integrity

Concurrent access, partial failure, constraint violations, and consistency
under load.

| What to test | Example |
|--------------|---------|
| Concurrent writes | Two requests create the same resource simultaneously |
| Partial failure | DB write succeeds but cache invalidation fails |
| Transaction rollback | Failed operation leaves no partial state |
| Unique constraint enforcement | Duplicate email rejected at DB level |
| Idempotency | Retrying a request produces the same result |

```typescript
it("prevents duplicate account creation under concurrent requests", async () => {
  const email = "concurrent@test.com";
  const [r1, r2] = await Promise.allSettled([
    createAccount({ email, password: "valid" }),
    createAccount({ email, password: "valid" }),
  ]);
  const successes = [r1, r2].filter(r => r.status === "fulfilled");
  expect(successes).toHaveLength(1);
});
```

### 6. Destructive Operations

Delete, revoke, bulk operations, and irreversible actions.

| What to test | Example |
|--------------|---------|
| Delete removes correct record | Deleting user A does not affect user B |
| Revocation is immediate | Revoked token rejected on next request |
| Bulk operations are bounded | Bulk delete requires explicit limit |
| Audit trail | Destructive operations are logged |
| Confirmation required | Irreversible actions require explicit confirmation |

## Phased TDD Execution

IDD work proceeds in phases defined in `plan.md`. Each phase maps to one
TDD cycle. Do not start a new phase until all tests in the current phase pass.

For the full phase sequence, see `references/idd-lifecycle.md`.

### Phase-to-TDD Mapping

| Phase | TDD focus | What you write |
|-------|-----------|----------------|
| Interview | No tests yet | Intent file, decisions.md |
| Spec | No tests yet | Constraints, examples, API signatures |
| Generate | Full RED → GREEN → REFACTOR | Implementation code |
| Sync | Functional tests for drift | Tests covering behavior that drifted from intent |
| Audit | No new tests | Verify existing tests still pass |

### One Phase Per Session

Run one phase per focused session. Do not mix spec work with implementation.
The FORGE protocol enforces this with a phase guard — the agent refuses to
write implementation code during spec phases.

Enforce this yourself when working without tooling:
1. Read the current phase from `plan.md`
2. Refuse to write implementation code if the phase is Interview or Spec
3. Refuse to modify intent files if the phase is Generate

### RED → GREEN → REFACTOR Within Generate

The Generate phase follows strict TDD. No exceptions.

```
1. RED      — Write the test. Run it. Confirm it fails for the right reason.
2. GREEN    — Write the minimum code to make the test pass. No extras.
3. REFACTOR — Clean up. Run tests again. Confirm still green.
4. Repeat for next test case.
```

"Fails for the right reason" means the test fails because the feature
doesn't exist yet — not because of a syntax error or test setup problem.
Fix setup issues before counting a test as RED.

### Phase Gate

Before moving to the next phase, run the full test suite. All tests must pass.

```bash
npm test -- --coverage   # or: pytest --tb=short
```

If any test fails at the phase gate, fix the application code before advancing.
Do not comment out failing tests. Do not skip them.

## E2E Gate Scripts

E2E gate scripts run the full integration suite against the real system.
Run them between phases and before every commit.

```bash
#!/usr/bin/env bash
set -euo pipefail

# Guard: require real environment
[ -z "${DATABASE_URL:-}" ] && { echo "ERROR: DATABASE_URL not set"; exit 1; }

npm test -- --testPathPattern="unit"
npm test -- --testPathPattern="integration"
npm test -- --testPathPattern="e2e"
npm test -- --coverage --coverageThreshold='{"global":{"lines":80}}'

echo "Gate passed"
```

### When to Run Gate Scripts

| Trigger | Gate level |
|---------|-----------|
| Before phase transition | Full E2E gate |
| Before commit | Unit + integration |
| Before merge | Full E2E gate |
| After dependency update | Full E2E gate |
| After intent file change | Full E2E gate for affected module |

Gate scripts run against the real system. No exceptions. If the real system
is unavailable, the phase transition is blocked. Tell the user. Do not
substitute a mocked environment to unblock yourself. A gate that passes
against fakes is a gate that didn't run.

## Commit Conventions

IDD uses phase-prefixed commits. The prefix signals which phase produced
the commit and what kind of change it contains.

| Prefix | Phase | What it contains |
|--------|-------|-----------------|
| `plan:` | Planning | Intent files, decisions.md, plan.md updates |
| `build:` | Generate | Implementation code, tests written during Generate |
| `sync:` | Sync | Drift corrections, updated tests after sync check |
| `audit:` | Audit | Audit findings, constraint enforcement fixes |

### Commit Message Format

```
{prefix} {module}: {what changed}
```

Examples:
```
plan: auth — add rate limiting constraint and examples
build: auth — implement authenticate() with session creation
build: auth — add error path tests for locked accounts
sync: auth — update session TTL test after config change
audit: auth — enforce no-import-from-payments lint rule
```

Commit at the end of each phase, not during it. Squash working commits
before pushing — the commit history should read as a clean phase log.

## Coverage Requirements

Coverage is a signal, not a target. Use it to find gaps, not to hit a number.

### Minimum Coverage by Category

| Category | Minimum | Why this floor |
|----------|---------|----------------|
| Happy Path | 1 test per success mode | Proves the feature works at all |
| Error Path | 2x happy path count | Systems fail more ways than they succeed |
| Edge Cases | All boundary values from constraints | Boundaries are where bugs live |
| Security | All attack vectors in constraints | Security gaps are not acceptable |
| Data Integrity | All concurrent and partial-failure scenarios | Data corruption is catastrophic |
| Destructive Operations | All irreversible actions | No recovery from uncaught destructive bugs |

### Line Coverage Thresholds

| Module type | Line coverage floor |
|-------------|---------------------|
| Auth, payments, data access | 85% |
| Business logic | 80% |
| API handlers | 75% |
| Utilities, helpers | 70% |

### When Coverage Gaps Appear

1. Identify the uncovered lines
2. Determine which test category they belong to
3. Check the intent file — is there an example or constraint that covers this case?
4. If yes: write the missing test
5. If no: add the example or constraint to the intent file first, then write the test

Do not write tests for uncovered lines without first checking whether the
intent file specifies that behavior. Untested code that isn't in the intent
may be dead code — remove it instead of testing it.

## Common Failure Modes

| What goes wrong | Why | Fix |
|-----------------|-----|-----|
| Tests pass but behavior is wrong | Tests verify implementation, not behavior | Rewrite tests from intent Examples table, not from code |
| Error paths are missing | Developer wrote happy path first and stopped | Count error path tests — must exceed happy path count |
| Any test uses mocks without user permission | Developer or agent mocked a dependency to "simplify" or "speed up" | Remove the mock immediately. Test against the real system. This is a hard rule — not a guideline. |
| Bug fixed with a "regression test" | Test added in test suite with no corresponding intent update | Add the bug as an edge case row in the Examples table first, then write the test from that row |
| Phase gate skipped | "We'll fix it after the next phase" | Enforce gate as a hard block. No exceptions. |
| Constraints not tested | Constraints written but never converted to tests | For every constraint row, write at least one test |
| Tests break after refactor | Tests coupled to implementation details | Test behavior (inputs and outputs), not internal calls |
| Coverage number hit but gaps remain | Tests written to cover lines, not categories | Audit by category, not by line percentage |
| Commit history is noise | Many small commits without phase prefix | Squash to one commit per phase before pushing |
| Intent file and tests diverge | Code changed without updating intent | Run sync phase. Update intent or revert code. |
| Destructive tests run against production | No environment guard in gate script | Add environment check at top of every gate script |

For intent file drift detection and sync procedures, see `references/idd-lifecycle.md`.
For constraint authoring and the three-layer model, see `references/intent-standard.md`.
For quality enforcement and audit procedures, see `references/quality-enforcement.md`.
