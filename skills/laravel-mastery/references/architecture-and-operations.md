# Architecture and Operations

Sources: Laravel official documentation (service container, providers, queues, events, cache, Artisan, application structure), Matt Stauffer (Laravel Up & Running), Laravel community practices from Spatie, Laracasts, and production teams

Covers: service container, providers, actions/services, jobs, queues, Horizon, events, listeners, cache strategy, Artisan workflows, and Laravel 11 slim bootstrap/application structure.

## Default Structure First, Extraction Second

Laravel’s defaults are good. Keep them until clear pressure appears.

| Signal | Move |
|-------|------|
| small app, limited domain complexity | stick to default structure |
| repeated orchestration in controllers | extract actions/services |
| many queue workflows | dedicated jobs/domain folders |
| growing domain with many models | feature/domain grouping |

Do not start with a hyper-custom directory layout unless the team already operates that way consistently.

## Service Container Rules

The container is most useful for wiring dependencies, interfaces, and framework-level composition.

### Good container uses

| Use case | Example |
|---------|---------|
| interface to implementation binding | repository or gateway interface |
| singleton infrastructure object | API client, SDK wrapper |
| contextual bindings | different implementations in different contexts |

### Bad container uses

| Anti-pattern | Why |
|-------------|-----|
| resolving everything ad hoc from deep inside methods | hidden dependencies |
| container-as-global-service-locator | poor testability |
| binding every concrete class unnecessarily | noise without value |

Prefer constructor injection whenever practical.

## Providers

Providers bootstrap app-wide configuration and bindings.

| Good provider responsibility | Example |
|---------------------------|---------|
| register container bindings | repo interface -> implementation |
| boot framework hooks | morph maps, rate limiters, view composers |
| configure package defaults | 3rd-party package integration |

Keep providers slim. If a provider becomes a dumping ground, move domain behavior elsewhere.

## Actions and Services

As controllers grow, extract orchestration into explicit classes.

### Action pattern

| Good fit | Example |
|---------|---------|
| one focused business operation | PublishPostAction |
| mutation with multiple side effects | InviteUserToTeamAction |
| controller logic repeated in console/jobs | shared operation class |

### Service pattern

| Good fit | Example |
|---------|---------|
| broader domain capability set | BillingService |
| external API integration | CRMService |
| reusable business orchestration | SubscriptionService |

Use actions for single workflows, services for broader capability areas.

## Queue Strategy

Queues are essential once work extends beyond a quick request cycle.

| Push to queue when | Example |
|-------------------|---------|
| task is slow | report generation |
| task hits external APIs | email/SMS/provider sync |
| task can fail/retry independently | webhooks, imports, image processing |

### Driver choices

| Driver | Best for |
|-------|----------|
| sync | local dev or trivial apps |
| database | simple production baseline |
| redis | high-throughput production with Horizon |
| sqs | cloud-native serverless setups |

## Job Design Rules

| Rule | Why |
|-----|-----|
| keep job payloads small | serialization safety |
| pass IDs instead of huge model graphs | reduce stale model issues |
| make jobs idempotent when possible | safe retries |
| define retries/timeouts intentionally | operational clarity |

### Good job example

Pass `userId`, reload current state in `handle()`, and guard against duplicate execution.

## Horizon and Queue Operations

Use Horizon when Redis-backed queues matter operationally.

| Benefit | Why |
|--------|-----|
| dashboard visibility | job throughput and failures |
| balancing strategies | better worker utilization |
| failed job visibility | operational triage |

Horizon is valuable when queues become part of daily operations, not just an occasional background tool.

## Events and Listeners

Events are useful for decoupling, but overuse creates invisible systems.

### Good event use cases

| Use case | Example |
|---------|---------|
| domain milestone | UserRegistered |
| multiple independent reactions | send email, analytics, onboarding |
| loosely coupled side effects | audit log + notification |

### Bad event use cases

| Anti-pattern | Why |
|-------------|-----|
| core workflow hidden behind listeners | hard to reason about execution |
| one event with mandatory linear listeners | just call a service directly |
| listener chains that feel like business process engine | debugging nightmare |

If the step is required for correctness, keep it explicit in the main workflow.

## Cache Strategy

Cache should be intentional, measured, and invalidated predictably.

| Data type | Pattern |
|----------|---------|
| expensive read model | `Cache::remember()` with TTL |
| per-user data | user-keyed cache entries |
| taggable related data | tagged cache invalidation |
| route/config/view bootstrap | optimize on deploy |

### Cache rules

1. Cache reads, not confusion
2. Invalidate close to write operations
3. Do not cache highly volatile or permission-sensitive data without a clear key strategy

## Artisan as Operational Surface

Custom Artisan commands are great for repeated operational workflows.

| Good command | Why |
|-------------|-----|
| data backfill | operationally repeatable |
| maintenance/repair task | runbook-friendly |
| reporting/export | explicit operator tool |

Avoid hiding important one-off ops in random scripts if the team already uses Artisan operationally.

## Laravel 11 Slim Bootstrap

Laravel 11 moved more app wiring into `bootstrap/app.php`.

### Architectural implication

| Concern | Pattern |
|--------|---------|
| middleware registration | bootstrap app config |
| exception config | centralized bootstrap setup |
| route registration | fluent bootstrap API |

This keeps the surface smaller, but it means bootstrap configuration deserves deliberate review during upgrades.

## Common Architecture Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| stuffing business logic into controllers | weak reuse and testability | extract actions/services |
| container lookups everywhere | hidden dependencies | constructor injection |
| using events for mandatory workflow steps | invisible control flow | explicit service calls |
| queueing non-idempotent jobs without thought | duplicate side effects | make jobs safe to retry |
| broad cache keys with unclear invalidation | stale/wrong data | narrow keys + explicit invalidation |

## Cache Invalidation Patterns

| Write operation | Invalidation move |
|---------------|-------------------|
| model updated | forget model-specific cache key |
| list membership changes | bust list/index keys or tags |
| aggregate changes | recompute or expire aggregate cache |

Tagged caches are useful when a set of related records must be invalidated together.

## Queue Failure Strategy

| Failure mode | Response |
|-------------|----------|
| transient network failure | retry with backoff |
| validation/business rule failure | fail fast, do not retry forever |
| third-party outage | alert + bounded retries |

Retries are a product decision, not just an infrastructure toggle.

## Laravel 11 Bootstrap Review Checklist

1. Middleware registration is explicit and minimal
2. Exception handling stays centralized
3. Route registration reflects app surfaces clearly
4. Package and custom bindings are not scattered across unrelated files

These checks catch drift as the slim skeleton evolves.

## Queue Operational Checkpoints

| Check | Why |
|------|-----|
| failed jobs are visible and monitored | recovery requires visibility |
| queue workers restart on deploy | code and container consistency |
| timeouts and backoff are explicit | avoid runaway retries |

Operational maturity matters more than just “we use queues”.

## Command Scheduling Notes

Use the scheduler for periodic, deterministic operational work.

| Good fit | Example |
|---------|---------|
| cache warmups | rebuild summary cache |
| report generation | daily exports |
| data hygiene | cleanup stale drafts |

Prefer idempotent scheduled commands and make logging visible.

## Release Readiness Checklist

- [ ] Default Laravel structure is preserved unless clear pressure justified extraction
- [ ] Actions/services own business orchestration, not controllers
- [ ] Container bindings are focused and explicit
- [ ] Queue driver and retry policy are chosen intentionally
- [ ] Events are used for decoupling, not core hidden workflow
- [ ] Cache strategy has explicit invalidation points
- [ ] Operational commands and Horizon setup reflect real production needs
