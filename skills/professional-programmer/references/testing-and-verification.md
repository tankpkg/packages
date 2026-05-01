# Testing and Verification

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Meszaros (xUnit Test Patterns); Beck (TDD by Example); Tank bdd-e2e-testing and bulletproof skills

Covers: behavior-focused tests, concrete test data, readable tests, CI verification, and test strategy.

## Testing Standard

Testing is engineering evidence. A professional agent uses tests to prove behavior, catch regressions, and communicate intent to future maintainers.

Test required behavior, not incidental implementation. A test should fail when users or dependent systems would care.

## Test Selection

| Situation | Test Type |
| --------- | --------- |
| Pure business rule | Unit test |
| Existing behavior before refactor | Characterization test |
| API contract | Integration or contract test |
| User journey | E2E or BDD scenario |
| Bug fix | Regression test that fails before fix |
| Concurrency/state transition | State transition and forbidden transition tests |

## Concrete Tests

Use precise data. Avoid cute placeholders that obscure the rule being tested.

Bad test data hides meaning: `foo`, `bar`, `user1`, `test@test.com`.

Better test data names the scenario: `expiredSubscriptionUser`, `declinedPayment`, `warehouseOutOfStock`.

Keep one main reason for each test failure. If a test fails for many unrelated reasons, split it or use helper setup.

## Tests for People

Tests are documentation with a compiler. Name them around behavior, not implementation mechanics.

Prefer:

```typescript
it("rejects payment capture after authorization expires", async () => {})
```

Avoid:

```typescript
it("calls validateAuthDate", async () => {})
```

## Verification Workflow

1. Identify the behavior or risk.
2. Write or locate the narrowest useful test.
3. Confirm the test fails when guarding a bug or new behavior.
4. Implement the smallest change.
5. Run the narrow test, then relevant broader tests.
6. Refactor only with tests passing.
7. Record any untested residual risk.

## Continuous Verification

Run tests while you sleep by using CI, scheduled jobs, or longer nightly suites for checks too expensive for every commit.

Keep the build clean. Warnings in CI become background noise, and background noise hides real failures.

Do not let flaky tests persist. Quarantine only with an owner and a deadline.

## Avoid Incidental Tests

| Incidental Assertion | Behavior Assertion |
| -------------------- | ------------------ |
| Function called once | User receives confirmation once |
| Component has CSS class | Error is visible and accessible |
| Internal array sorted by helper | Results appear in required order |
| Mock method called | External effect is observable or contract verified |

## Routing

Use `@tank/bdd-e2e-testing` for Gherkin, Playwright, Cucumber, multi-context flows, and real-system verification.

Use `@tank/bulletproof` when intent definition and real-system proof are both required.

## Testing Decision Catalog

| Signal | Recommended Move | Why |
| ------ | ---------------- | --- |
| New feature | Behavior test | Proves user-visible change |
| Bug fix | Regression test | Prevents recurrence |
| Refactor | Characterization test | Preserves behavior |
| External API | Contract/integration test | Proves boundary |
| User journey | BDD/E2E scenario | Proves workflow |
| Rule matrix | Table test | Covers combinations |
| Failure path | Negative test | Proves recovery |
| State machine | Transition tests | Prevents illegal moves |
| UI state | Accessibility/visible assertion | Proves user experience |
| Flaky suite | Stability test/quarantine | Restores trust |

## Test Design Examples

### Discount Rules

A discount feature should be tested with eligible, ineligible, boundary, and conflict cases. The test names should describe business behavior rather than helper functions.

### Provider Failure

A provider timeout test should prove the user receives the correct temporary failure and operators receive safe diagnostic context. A mock is acceptable only if it preserves that failure contract.

### Refactor Safety

Before refactoring a legacy parser, write characterization tests for accepted malformed inputs if production currently depends on them. Then separate compatibility decisions from cleanup.

### Flaky Test Repair

A flaky test should not be rerun into green. Identify whether the cause is time, order, shared state, network, or environment, then fix or quarantine with ownership and a deadline.

## Verification Case Patterns

| Case | Professional Move |
| ---- | ----------------- |
| Discount rules | Use table cases for eligible, ineligible, boundary, and conflict inputs. |
| Bug regression | First create the test that would have caught the bug. |
| Legacy refactor | Characterize current behavior before changing structure. |
| External contract | Use integration or contract tests for provider shape. |
| User journey | Use BDD/E2E when the risk is workflow wiring. |
| Private helper assertion | Replace with observable behavior assertion. |
| Flaky test | Fix nondeterminism or quarantine with owner and deadline. |
| Snapshot overuse | Replace broad snapshots with named expectations. |
| Invalid input | Test boundary parser and user-facing error. |
| Slow suite | Move expensive checks to the right CI cadence without ignoring them. |

