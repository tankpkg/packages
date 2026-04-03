---
name: "@tank/laravel-mastery"
description: |
  Production Laravel development from v11+ onward. Covers Eloquent ORM
  (relationships, scopes, observers, casts, query optimization), routing and
  controllers (middleware, route model binding, API resources), Blade and
  Livewire/Inertia frontend stacks, queues and jobs (Horizon, retries, batches),
  events and listeners, authentication (Sanctum, Breeze, Fortify, Jetstream),
  testing with Pest and PHPUnit (factories, HTTP tests, mocking), Artisan CLI,
  service container and providers, caching strategies, and deployment (Forge,
  Vapor, Docker, Octane). Includes Laravel 11 slim application structure,
  bootstrap/app.php configuration, and Laravel 12/13 migration patterns.

  Synthesizes Laravel official documentation (laravel.com/docs), Stauffer
  (Laravel Up & Running, 3rd ed.), Rees-Carter (Laravel security), Pest PHP
  documentation, and Laravel community best practices (Laracasts, Spatie).

  Trigger phrases: "laravel", "eloquent", "laravel model", "laravel migration",
  "laravel controller", "laravel middleware", "laravel testing", "pest php",
  "laravel api", "laravel livewire", "laravel inertia", "laravel deployment",
  "laravel forge", "laravel vapor", "laravel queue", "laravel job",
  "laravel sanctum", "laravel breeze", "laravel artisan", "laravel blade",
  "laravel factory", "laravel service container", "laravel cache",
  "laravel best practices", "laravel relationships", "laravel scope",
  "laravel observer", "laravel event", "laravel horizon"
---

# Laravel Mastery

## Core Philosophy

1. **Convention over configuration** -- Laravel provides sensible defaults for everything. Override only when the default does not fit. Fighting the framework costs more than adapting to it.
2. **Eloquent is not your entire application** -- Models handle data access. Business logic belongs in services, actions, or dedicated classes. Fat models become unmaintainable past 500 lines.
3. **Test the behavior, not the implementation** -- Write feature tests that hit routes and assert responses. Reserve unit tests for complex, isolated logic. Pest makes this expressive.
4. **Queues are not optional at scale** -- Any operation over 500ms (emails, PDFs, API calls, image processing) belongs in a queue. Synchronous execution blocks users and kills throughput.
5. **Cache aggressively, invalidate precisely** -- Use tagged caches and cache keys derived from model timestamps. Stale data is worse than no cache.

## Quick-Start: Common Problems

### "Which frontend stack should I use?"

| Scenario | Stack |
|----------|-------|
| Server-rendered, minimal JS | Blade + Alpine.js |
| Interactive UI, PHP comfort | Livewire 3 |
| SPA-like UX with React/Vue | Inertia.js |
| Decoupled SPA / mobile API | Sanctum + separate frontend |
| Admin panel | Filament or Nova |
-> See `references/frontend-and-auth.md`

### "My Eloquent queries are slow"

1. Run `DB::enableQueryLog()` or install Debugbar to count queries
2. Check for N+1 -- add `->with()` for eager loading
3. Add database indexes on foreign keys and frequently-filtered columns
4. Use `->select()` to limit columns returned
5. For aggregates, use `withCount()` or subquery selects instead of loading relations
-> See `references/eloquent-and-data.md`

### "How do I structure a large Laravel project?"

1. Start with default directory layout -- do not reorganize prematurely
2. Extract business logic into Action classes (single-purpose, invokable)
3. Use Form Requests for validation, Policies for authorization
4. Group related features by domain when the app exceeds 30+ models
-> See `references/architecture-and-operations.md`

### "Setting up authentication"

1. New app with UI? Use Breeze (simple) or Jetstream (teams, 2FA)
2. API only? Run `php artisan install:api` for Sanctum
3. SPA + API on same domain? Use Sanctum cookie-based auth
4. Mobile app? Use Sanctum token-based auth
-> See `references/frontend-and-auth.md`

### "My tests are slow or flaky"

1. Use `RefreshDatabase` trait -- it wraps each test in a transaction
2. Use `LazilyRefreshDatabase` for speed with SQLite in-memory
3. Avoid hitting real APIs -- use `Http::fake()` and `Queue::fake()`
4. Run parallel tests: `php artisan test --parallel`
-> See `references/testing-and-deployment.md`

## Decision Trees

### Queue Driver Selection

| Signal | Driver |
|--------|--------|
| Local development | `sync` (immediate) or `database` |
| Production, moderate load | `database` or Redis |
| Production, high throughput | Redis + Horizon |
| Serverless (Vapor) | SQS |
| Need delayed/scheduled dispatch | Redis or SQS |

### Caching Strategy

| Data | Strategy |
|------|----------|
| Configuration, routes, views | `php artisan optimize` on deploy |
| Database queries (rarely changing) | `Cache::remember()` with TTL |
| Full-page or partial HTML | Response caching middleware |
| Computed aggregates | Scheduled command + cache store |
| User-specific data | Cache key with user ID prefix |

### Authentication Package

| Need | Package |
|------|---------|
| Simple login/register UI | Breeze |
| Teams, 2FA, profile management | Jetstream |
| Headless (API only, no UI) | Fortify |
| API tokens for SPA/mobile | Sanctum |
| OAuth provider (social login) | Socialite |

## Reference Index

| File | Contents |
|------|----------|
| `references/eloquent-and-data.md` | Eloquent relationships, scopes, observers, casts, query optimization, eager loading, migrations, factories, and API resources |
| `references/routing-and-controllers.md` | Routes, middleware, route model binding, controllers, Form Requests, policies, rate limiting, and endpoint structure |
| `references/frontend-and-auth.md` | Blade, Livewire, Inertia, Sanctum, Breeze, Fortify, Jetstream, guards, gates, policies, and Socialite integration |
| `references/architecture-and-operations.md` | Service container, providers, actions, jobs, queues, Horizon, events, listeners, cache strategy, and Laravel 11 bootstrap structure |
| `references/testing-and-deployment.md` | Pest and PHPUnit, HTTP tests, factories, mocking, parallel tests, Forge, Vapor, Docker, Octane, and zero-downtime deployment |
