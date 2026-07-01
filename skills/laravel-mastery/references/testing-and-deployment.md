# Testing and Deployment

Sources: Laravel official documentation (testing, HTTP tests, database testing, mocking, parallel tests, deployment, Octane), Pest documentation, Forge documentation, Vapor documentation, Docker deployment best practices

Covers: Pest and PHPUnit, HTTP and feature tests, factories, mocking, database testing, parallel test execution, Forge, Vapor, Docker, Octane, optimization commands, and zero-downtime deployment concerns.

## Test Behavior, Not Framework Internals

Laravel’s testing surface is strong because it lets you test behavior close to how users and clients experience the app.

| Test level | Use for |
|-----------|---------|
| unit | isolated domain logic |
| feature / HTTP | routes, middleware, validation, responses |
| integration | DB-heavy or external-boundary behavior |
| browser/E2E | only the most critical flows |

Most Laravel confidence comes from feature tests, not giant unit-test suites.

## Pest vs PHPUnit

| Tool | Best for |
|-----|----------|
| Pest | expressive feature and unit tests |
| PHPUnit | underlying runner and classic style |

Use Pest when the team values concise, readable tests. Keep PHPUnit compatibility where needed.

## Feature Test Defaults

Feature tests should be your main weapon.

### Good feature test targets

| Flow | Example |
|-----|---------|
| auth | login/logout/password reset |
| CRUD | create/update/delete resources |
| policies | forbidden vs allowed behavior |
| queues/events | dispatched or not dispatched |
| API resources | response shape and status codes |

### Example

```php
it('creates a post', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->post(route('posts.store'), [
            'title' => 'Hello',
            'body' => 'World',
        ])
        ->assertRedirect();

    expect(Post::where('title', 'Hello')->exists())->toBeTrue();
});
```

## Database Testing Rules

| Trait / strategy | Use |
|-----------------|-----|
| `RefreshDatabase` | safe default for most suites |
| `DatabaseTransactions` | quick reset in specific cases |
| SQLite in-memory | fast local tests when behavior matches enough |
| real DB engine in CI | catch engine-specific issues |

If production depends on MySQL/PostgreSQL-specific behavior, at least some tests should run against the real engine.

## Factories

Factories should make valid domain states cheap to create.

| Good factory feature | Why |
|---------------------|-----|
| sensible defaults | less noise per test |
| named states | readable intent |
| relations | realistic scenarios |

Avoid factories that create giant unrelated graphs by default.

## Fakes and Mocks

Laravel provides strong fakes for common boundaries.

| Fake | Use for |
|-----|---------|
| `Queue::fake()` | job dispatch assertions |
| `Bus::fake()` | chain/batch assertions |
| `Event::fake()` | event dispatch checks |
| `Mail::fake()` | email assertions |
| `Notification::fake()` | notification assertions |
| `Http::fake()` | external HTTP API boundaries |

### Mocking rule

Mock external boundaries and side effects. Avoid mocking the framework itself or your own code so aggressively that tests lose meaning.

## Validation and Auth Testing

| Concern | Test |
|--------|------|
| validation errors | assert session errors / JSON validation output |
| authorization | assert 403 / redirect behavior |
| guest access | assert redirect to login or 401 |

Feature tests are the best place to prove route middleware, Form Requests, and policies work together.

## API Testing

For JSON APIs, assert stable response contracts.

### Common checks

1. status code
2. JSON structure
3. key fields and types
4. auth requirements
5. pagination/meta consistency

Use API resources so tests target explicit shape instead of ad hoc arrays everywhere.

## Parallel Testing

Parallel tests can dramatically reduce suite time.

| Good fit | Watch out for |
|---------|----------------|
| large feature suites | tests depending on shared external state |
| database-backed tests | filesystem/shared singleton assumptions |

Ensure test setup is isolated before enabling broad parallelism.

## Deployment Targets

| Target | Best for |
|-------|----------|
| Forge | traditional VM/server management |
| Vapor | AWS serverless Laravel |
| Docker | portable infra, k8s/ECS/containers |
| Octane | high-throughput apps needing persistent workers |

Choose the deployment path that matches team operations, not trendiness.

## Forge Pattern

Forge is strong for teams that want managed server operations without building their whole own platform.

### Good fit

| Scenario | Why |
|---------|-----|
| conventional Laravel app on servers | simple operational model |
| queue workers + scheduler + DB-backed app | strong Laravel-native support |

## Vapor Pattern

Vapor fits serverless-first teams willing to embrace AWS constraints.

| Benefit | Trade-off |
|--------|-----------|
| auto-scaling and serverless ops | runtime/platform constraints |
| strong Laravel integration | vendor/platform coupling |

Use Vapor when serverless is a product and ops decision, not just curiosity.

## Docker Pattern

Containerized Laravel works well when the org already runs Docker-based infrastructure.

### Deployment checklist

1. build production image with Composer deps optimized
2. run `php artisan config:cache`, `route:cache`, `view:cache` as appropriate
3. run migrations explicitly during deploy flow
4. separate web, queue, scheduler processes intentionally

## Octane Rules

Octane changes execution assumptions because workers persist between requests.

| Rule | Why |
|-----|-----|
| avoid request-specific singleton leakage | persistent workers keep memory |
| reset mutable state carefully | stale data risk |
| review packages for Octane safety | not everything is worker-safe |

Do not turn on Octane without understanding the persistent worker model.

## Zero-Downtime Deployment Concerns

| Concern | Recommendation |
|--------|----------------|
| migrations | avoid breaking old+new code overlap |
| queue workers | restart safely after deploy |
| config cache | rebuild during release |
| symlink / release switching | atomic cutover where platform supports it |

Prefer additive database changes before destructive ones in rolling deploys.

## Common Testing/Deployment Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| too many unit tests for HTTP app behavior | low confidence in integration | add feature tests |
| no real DB coverage | migration/query surprises | run some tests on real engine |
| mocking internal domain logic heavily | brittle, low-signal tests | mock boundaries, not everything |
| deploying without optimize/cache strategy | slower boot or stale config confusion | explicit deploy steps |
| enabling Octane without state review | request bleed and subtle bugs | audit mutable state first |

## Deployment Pipeline Stages

| Stage | Checks |
|------|--------|
| PR | tests, static analysis, code style |
| pre-release | real DB migrations, smoke checks |
| release | artifact/image build, deploy, queue restart, cache warmup |

Keep deployment steps scripted and repeatable.

## Post-Deploy Checks

1. Hit health endpoints
2. Confirm queue workers are running
3. Confirm scheduler is active if required
4. Review logs for migration or boot errors
5. Smoke critical auth and CRUD flows

## CI Baseline for Laravel Apps

| Step | Purpose |
|-----|---------|
| code style / Pint | formatting consistency |
| static analysis | catch obvious correctness issues |
| feature tests | app behavior confidence |
| build artifact/image | deployment readiness |

Keep CI short enough for frequent use, but broad enough to catch route, model, and deployment regressions.

## Octane-Specific Review

| Concern | Why |
|--------|-----|
| singleton mutable state | persists across requests |
| service instances with request data | cross-request contamination |
| package compatibility | some packages assume request-per-process model |

Octane should be introduced with a deliberate compatibility review, not flipped on casually.

## Release Readiness Checklist

- [ ] Feature tests cover critical auth, validation, and CRUD flows
- [ ] Factories provide readable test setup with named states
- [ ] External side effects are faked cleanly where appropriate
- [ ] Parallel test execution is enabled only after isolation issues are solved
- [ ] Deployment target (Forge, Vapor, Docker, Octane) matches team operations
- [ ] Optimization and migration steps are explicit in deployment workflow
- [ ] Zero-downtime and worker restart concerns are accounted for
