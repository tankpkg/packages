# Testing and Auth

Sources: Django official documentation (testing, auth), DRF testing docs, community Django testing practices, factory-based testing guidance

Covers: Django tests, DRF tests, auth flows, permissions, factories, fixtures, request testing, and practical testing strategy for Django apps.

## Feature-Level Confidence Matters Most

| Test level | Best for |
|-----------|----------|
| unit | isolated helpers/domain logic |
| Django view/request tests | route and response behavior |
| DRF tests | API contracts and auth |
| browser/E2E | only highest-value flows |

## Auth Testing Basics

| Concern | Test |
|--------|------|
| guest redirect or denial | explicit response assertion |
| authenticated success | login/session or auth header path |
| permission denial | 403 or equivalent boundary |

## Factories over Giant Fixtures

Use factories or focused fixtures to keep setup clear.

| Pattern | Benefit |
|--------|---------|
| small factories | readable setup |
| named states | intent clarity |
| minimal fixtures | lower brittleness |

## DRF Testing Rules

1. assert status codes and payload shape
2. test permission/auth boundaries explicitly
3. test pagination and filtering when public contract depends on them

## Request Test Patterns

| Pattern | Use |
|--------|-----|
| Django test client | server-rendered flows |
| DRF APIClient | API auth and JSON contracts |
| RequestFactory | lower-level view testing |

## Auth Flow Matrix

| State | Expected result |
|------|------------------|
| guest | redirect or 401/403 depending on surface |
| authenticated allowed user | success |
| authenticated forbidden user | 403 |

## Factory and Fixture Discipline

1. prefer factories for most app-level state
2. keep fixtures small and purposeful when needed
3. use named factory states for role or lifecycle differences

## Permission Testing Questions

1. Is the route protected at the correct layer?
2. Does object-level access behave correctly?
3. Are negative permission paths asserted, not just happy paths?

## DRF Contract Checks

| Concern | Test |
|--------|------|
| serializer fields | exact keys/shape |
| pagination envelope | structure and metadata |
| filtering/order constraints | supported behavior only |

## Common Auth Testing Smells

| Smell | Why it matters |
|------|----------------|
| only testing allowed path | weak security confidence |
| using giant fixtures for small auth checks | hard maintenance |
| no API auth tests for token/session behavior | drift between config and code |

## Test Suite Review Checklist

| Check | Why |
|------|-----|
| route behavior tested at request layer | realistic confidence |
| auth boundaries covered | security |
| factories remain readable | maintainability |

## Session vs Token Auth Tests

| Surface | What to test |
|--------|--------------|
| browser/session auth | login, logout, redirect behavior |
| API token auth | token accepted, invalid token rejected |
| mixed app/API | boundaries stay distinct |

## Factory Strategy Notes

| Pattern | Benefit |
|--------|---------|
| role states | `admin`, `editor`, `viewer` clarity |
| lifecycle states | draft, published, archived |
| relation helpers | realistic setup with less boilerplate |

## Request Assertion Heuristics

1. assert status code first
2. assert one or two critical payload/UI elements
3. assert permission boundary when applicable

## DRF Auth Review Questions

1. Does authentication choice match the client type?
2. Are unauthenticated and unauthorized responses both covered?
3. Are permission classes doing what the route contract expects?

## Common Testing Trade-offs

| Trade-off | Guidance |
|----------|----------|
| more factories vs more fixtures | prefer factories for readability |
| more unit tests vs more request tests | bias toward request tests for web behavior |
| browser E2E vs DRF/request tests | keep browser tests narrow and high-value |

## Regression Checklist

| Regression risk | Test target |
|---------------|-------------|
| changed permission logic | auth/forbidden path test |
| serializer shape drift | API response assertion |
| template/view redirect drift | request/response test |

## Final Auth/Test Questions

1. Can a guest access what they should not?
2. Can an authorized user still complete the critical path?
3. Are API contracts asserted strongly enough to catch serializer drift?

## Auth Surface Checklist

| Surface | Test |
|--------|------|
| browser login-required page | redirect and success path |
| permissioned object view | owner/admin/non-owner cases |
| API token/session endpoint | valid, invalid, missing auth |

## Factory Review Questions

1. Do factory states reflect real business roles/lifecycles?
2. Are defaults realistic enough for request tests?
3. Could a tiny builder/helper replace a huge fixture blob?

## Testing Pyramid for Django

| Layer | Keep it for |
|------|-------------|
| unit | pure helpers, validators, domain rules |
| request/feature | main confidence layer |
| browser/E2E | only a few critical journeys |

## Regression Smells

| Smell | Why it matters |
|------|----------------|
| serializer changed but no response test failed | weak contract assertions |
| auth logic changed but only happy path tested | security blind spot |
| fixtures too large to understand | test drift |

## Final Test Discipline Notes

Readable tests are part of maintainability. If a future engineer cannot tell which boundary a test protects, the suite is losing value.

## Permission Matrix Example

| User type | Page/API action | Expected result |
|----------|------------------|-----------------|
| guest | protected route | redirect / deny |
| regular user | own object | allowed |
| regular user | other user object | forbidden |
| admin | admin-only route | allowed |

## API Client Testing Notes

| Concern | Recommendation |
|--------|----------------|
| JSON shape | assert exact keys for critical contracts |
| pagination | assert envelope metadata |
| auth boundary | assert missing/invalid/valid paths |

## Fixture and Factory Smells

| Smell | Problem |
|------|---------|
| giant fixture files | unreadable setup |
| magic factory defaults with hidden side effects | poor test clarity |
| repeated auth setup boilerplate | missing helper abstraction |

## Review Questions

1. Could a request-level test replace several weaker unit tests?
2. Are permission failures tested as explicitly as success paths?
3. Are factories making intent clearer or hiding too much?

## Practical Auth Test Checklist

1. test guest path
2. test authenticated success path
3. test forbidden path where permission matters
4. test API auth variant if the endpoint surface differs

## Contract Review Notes

Readable, explicit assertions on response shape and permission behavior are more valuable than broad vague coverage claims.

## Team Testing Heuristic

If a change alters auth, permissions, or serializers, at least one request-level regression test should change with it.

That keeps the suite aligned with real application risk.

It also prevents auth and API drift from hiding behind green unit tests.

That is one of the highest-value habits in mature Django teams.

It keeps regressions visible where they matter.

## Release Readiness Checklist

- [ ] critical auth and permission boundaries are tested
- [ ] request/response behavior is covered at the right layer
- [ ] factories or fixtures keep setup comprehensible
- [ ] DRF/API contracts are asserted explicitly
- [ ] guest, allowed, and forbidden paths are all covered where relevant

## Common Testing Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| too much unit testing for view behavior | weak integration confidence | add request tests |
| no auth boundary tests | security regressions | assert guest/auth/forbidden paths |
| giant fixtures nobody understands | hard maintenance | use factories/builders |

## Release Readiness Checklist

- [ ] critical auth and permission boundaries are tested
- [ ] request/response behavior is covered at the right layer
- [ ] factories or fixtures keep setup comprehensible
- [ ] DRF/API contracts are asserted explicitly
