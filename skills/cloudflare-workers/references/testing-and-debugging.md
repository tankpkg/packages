# Testing and Debugging

Sources: Wrangler documentation, Miniflare documentation, Vitest documentation, Cloudflare Workers testing guides, community production debugging practices

Covers: local testing with Wrangler and Miniflare, Vitest patterns, binding-aware tests, logs, debugging runtime mismatches, and practical verification flows for Cloudflare Workers.

## Local Runtime Fidelity Matters

Workers code can fail when local assumptions differ from the real edge runtime.

| Tool | Use |
|-----|-----|
| `wrangler dev` | realistic local iteration |
| Miniflare | controlled test/runtime simulation |
| Vitest | unit and integration-style tests |

Prefer testing against the Workers-like runtime, not plain Node assumptions.

## Test Layers

| Layer | Best for |
|------|----------|
| unit | helper functions, pure transforms |
| worker integration | fetch handler behavior with env bindings |
| staging smoke | real binding + deployment validation |

## Binding-Aware Tests

Workers often fail at the seams between handler logic and bindings.

| Binding | Test concern |
|--------|--------------|
| KV | miss/put/read logic |
| D1 | SQL correctness |
| R2 | object existence / response shape |
| Durable Objects | routing and coordination behavior |

## Debugging Checklist

1. confirm binding names match Wrangler config
2. inspect logs and response status
3. reproduce in Wrangler dev or Miniflare
4. verify edge-safe dependency assumptions

## Common Runtime Mismatch Bugs

| Bug | Cause |
|----|-------|
| Node builtin missing | package/runtime incompatibility |
| binding undefined | env config mismatch |
| behavior differs from local | edge runtime assumption drift |

## Useful Smoke Tests

| Test | Why |
|-----|-----|
| health endpoint | confirms basic runtime boots |
| one binding-backed read path | verifies env wiring |
| one write or queue path in staging | catches permission/config issues |

## Debugging Workflow

1. reproduce with smallest possible request
2. inspect Wrangler/Worker logs
3. compare local env bindings to deployed env
4. isolate dependency/runtime assumptions

Fast reduction beats guessing at edge-specific failures.

## Test Focus Areas

| Area | Why it matters |
|-----|----------------|
| request parsing | edge handlers often fail on malformed assumptions |
| auth and secrets | public edge exposure raises abuse risk |
| binding-backed operations | config drift is common |
| caching branches | stale vs fresh behavior must be intentional |

## Log Review Questions

1. Did the request reach the expected route?
2. Did binding access fail or return unexpected data?
3. Did a dependency/runtime assumption break only after deployment?

Debugging gets faster when you ask concrete questions instead of scanning logs aimlessly.

## Local vs Deployed Behavior Checklist

| Question | Why |
|---------|-----|
| Are the same bindings available locally and remotely? | config parity |
| Is the dependency edge-compatible in both contexts? | runtime parity |
| Does the route behave differently behind Cloudflare edge features? | deployment realism |

## Minimal Regression Suite

| Test | Scope |
|-----|-------|
| one happy-path request per critical route | route sanity |
| one auth failure path | security boundary |
| one binding-backed data path | config/runtime integration |

You do not need a huge suite to catch the most common Worker deployment failures.

## Test Data Patterns

| Pattern | Benefit |
|--------|---------|
| fixed sample requests | reproducible failures |
| env-specific binding fixtures | realistic local coverage |
| minimal smoke payloads | easy debugging |

Keep your test data tiny and intentional; edge bugs often hide in config and flow, not large fixtures.

## Failure Classification

| Failure type | First suspicion |
|-------------|-----------------|
| local-only failure | test/runtime simulation issue |
| deployed-only failure | env config, binding, or runtime mismatch |
| intermittent failure | race, upstream dependency, or eventual-consistency assumption |

Classify first. It saves time compared with random debugging.

## Local Tool Selection

| Need | Tool |
|-----|------|
| quick manual route iteration | `wrangler dev` |
| repeatable automated runtime tests | Miniflare |
| pure helper/unit tests | Vitest |

Pick the smallest tool that still reproduces the edge-specific behavior you care about.

## Debugging Anti-Patterns

| Anti-pattern | Better move |
|-------------|-------------|
| guessing at runtime mismatch | compare env and runtime assumptions explicitly |
| logging huge payloads everywhere | add targeted diagnostics |
| skipping staging smoke tests | add one high-value deployed check |

Edge debugging gets expensive when the feedback loop is noisy.

## Post-Fix Verification

| Check | Why |
|------|-----|
| rerun minimal regression route set | confirm fix really worked |
| compare logs before/after | validate diagnosis |
| test one binding-backed path | catch partial config regressions |

Do not stop at "the error disappeared locally".

## Runtime-Safe Test Design

| Rule | Why |
|-----|-----|
| keep tests edge-runtime aware | avoid Node-only false confidence |
| isolate binding assumptions explicitly | easier diagnosis |
| keep smoke routes tiny and deterministic | faster validation |

## Debug Session Checklist

1. capture exact failing route and status
2. note env/binding context
3. reproduce in the smallest local runtime setup possible
4. compare deployed vs local assumptions

Systematic reduction beats intuition on edge-runtime bugs.

## Smoke Test Priorities

| Priority | Example |
|---------|---------|
| highest | auth gate + binding-backed route |
| medium | cache or queue handoff path |
| lower | non-critical informational route |

Start with the route most likely to prove the runtime and config are sane.

## Local Reproduction Questions

1. Can this fail without the real binding present?
2. Is the issue in request parsing, env wiring, or downstream behavior?
3. Does the bug reproduce under Wrangler dev, Miniflare, or only deployed?

These questions narrow debugging time significantly.

## Regression Guardrails

| Guardrail | Benefit |
|----------|---------|
| keep one smoke test per critical binding path | catches config regressions |
| keep one auth failure test | catches accidental exposure |
| rerun deployed smoke after fixes | validates real-world behavior |

Small, stable guardrails beat giant fragile suites for most Worker services.

## Minimal Incident Notes Template

| Field | Example |
|------|---------|
| failing route | `POST /api/messages` |
| environment | staging / production |
| affected binding | `DB`, `CACHE`, or none |

Even a tiny incident template speeds repeated debugging work.

## Final Validation Habit

After a fix, validate at three levels:

1. local runtime reproduction is gone
2. deployed smoke test passes
3. logs no longer show the original failure signature

Stopping after level 1 is how regressions survive.

## Quick Triage Matrix

| Symptom | First place to look |
|--------|----------------------|
| binding undefined | Wrangler env config |
| route mismatch | URL/method/router logic |
| local pass, deploy fail | runtime/env drift |

This matrix is intentionally simple because speed matters during incidents.

## Minimal Smoke Route Set

| Route type | Why include it |
|-----------|----------------|
| health route | confirms runtime boot |
| auth-protected route | checks access boundary |
| binding-backed route | proves config wiring |

Three routes can reveal a surprising amount about system health.

## Final Check Rule

After any meaningful fix, rerun the smallest useful smoke set before declaring success.

That habit catches partial fixes that only solve the local symptom.

## Release Readiness Checklist

- [ ] Unit and handler-level tests cover critical paths
- [ ] Binding names and env typing are validated
- [ ] Local runtime tooling matches production assumptions closely enough
- [ ] Staging smoke tests exist for high-risk workers
