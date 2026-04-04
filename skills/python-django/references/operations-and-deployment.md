# Operations and Deployment

Sources: Django official deployment docs, Celery docs, cache docs, Gunicorn/Uvicorn deployment practices, Docker/Django community guidance

Covers: Celery integration, caching, static/media handling, environment config, deployment, and practical production operations for Django applications.

## Production Django Is More Than `runserver`

| Concern | Typical tool |
|--------|---------------|
| app server | Gunicorn / Uvicorn |
| background jobs | Celery |
| cache/session backend | Redis or similar |
| static/media strategy | CDN / object storage / web server integration |

## Celery Use Cases

| Good fit | Example |
|---------|---------|
| email/webhooks | background delivery |
| report generation | slower async work |
| import/export pipelines | task queue |

Keep tasks idempotent where possible.

## Cache Strategy

| Cache target | Pattern |
|------------|---------|
| expensive query/view result | cache with explicit invalidation/TTL |
| sessions | managed backend |
| static assets | CDN or storage-backed serving |

## Celery Review Questions

1. Is this work actually asynchronous or just delayed sync code?
2. Is the task idempotent enough for retries?
3. What happens when the worker is down?

## Static and Media Strategy

| Concern | Recommendation |
|--------|----------------|
| static assets | collect and serve predictably via CDN/web server |
| user uploads/media | define ownership and storage clearly |
| cache headers | explicit strategy for static resources |

## App Server Notes

| Concern | Pattern |
|--------|---------|
| synchronous Django app | Gunicorn baseline |
| async-capable paths or ASGI stack | Uvicorn / ASGI deployment where justified |

## Deployment Runbook Questions

1. Are migrations safe to run on live traffic?
2. Are worker and app processes version-aligned after release?
3. Is there a smoke test for one core request path and one background path?

## Caching Review Questions

| Question | Why |
|---------|-----|
| what is the invalidation path? | stale data risk |
| is this cache per-user or global? | correctness |
| could query optimization beat caching? | simpler system |

## Operational Smells

| Smell | Problem | Fix |
|------|---------|-----|
| no clear owner for media/static strategy | broken deploys | define architecture explicitly |
| Celery introduced without retry discipline | noisy failures | make task policy explicit |
| migrations treated as afterthought | fragile releases | runbook + CI discipline |

## Process Separation Review

| Process | Purpose |
|--------|---------|
| web app server | request handling |
| worker | async tasks |
| scheduler/beat | periodic tasks |

These processes often deserve separate operational thinking even when they share one codebase.

## Environment Configuration Questions

1. Which settings differ by environment?
2. Are secrets externalized cleanly?
3. Are debug-only behaviors truly disabled in production?

## Deployment Safety Notes

| Concern | Recommendation |
|--------|----------------|
| schema changes | additive-first where possible |
| worker restarts | coordinate with app deploy |
| static asset updates | ensure versioned/collected asset flow |

## Cache Review Heuristics

| Signal | Question |
|-------|----------|
| slow view | can query shaping solve this first? |
| repeated expensive page/API result | should this be cached? |
| user-specific data | is cache key scoped correctly? |

## Celery Failure Review

| Concern | Why |
|--------|-----|
| retries too broad | noisy repeated failures |
| tasks not idempotent | duplicate side effects |
| no visibility into failures | operational blind spots |

## Release Runbook Outline

1. validate env config
2. run tests/build checks
3. run migrations
4. deploy app code
5. restart/roll workers if needed
6. smoke-test one web and one async-critical flow

## Final Operations Questions

1. Could this app recover cleanly from a failed deploy?
2. Is async work observable enough to operate confidently?
3. Are assets, workers, and migrations part of one documented process?

## Static and Media Ownership

| Concern | Recommendation |
|--------|----------------|
| static files | collect and serve via clear pipeline |
| user uploads | explicit storage backend and retention model |
| CDN caching | align with asset versioning/invalidation |

## App and Worker Coordination

| Concern | Why |
|--------|-----|
| app code and Celery task version mismatch | async breakage |
| migrations ahead of workers or behind them | runtime failures |
| scheduler drift | missed periodic work |

## Deployment Review Heuristics

1. Is this deploy only app code, or also schema and worker behavior?
2. What post-deploy smoke checks prove both sync and async paths?
3. Can the team roll forward or mitigate cleanly if something fails?

## Caching Smells

| Smell | Problem |
|------|---------|
| caching to hide bad ORM paths | fragile complexity |
| no invalidation plan | stale data |
| user-specific cache with weak keying | correctness/security issues |

## Final Ops Checklist

- [ ] app server, worker, scheduler, and storage responsibilities are explicit
- [ ] static/media strategy is documented
- [ ] Celery retry/idempotency expectations are clear
- [ ] deployment runbook covers schema, assets, app, and worker rollout

## Release Pipeline Questions

1. Are migrations safe to run before new code serves traffic?
2. Do workers need a coordinated restart or drain process?
3. Is static asset publication atomic enough for the UI surface?

## Monitoring Basics

| Concern | Why |
|--------|-----|
| app errors | request-path health |
| worker/task failures | async reliability |
| cache hit/miss awareness | performance understanding |
| deploy-time smoke checks | rollout confidence |

## Common Deployment Smells

| Smell | Why it matters |
|------|----------------|
| workers treated as afterthought after deploy | async breakage |
| static/media config undocumented | environment drift |
| caching introduced without monitoring | blind stale-data risk |

## Ops Review Checklist

1. Can a new engineer explain how app, workers, cache, and storage fit together?
2. Is there one documented deploy path instead of tribal knowledge?
3. Are smoke checks defined for both sync and async-critical workflows?

## Runbook Smell

If the deploy process still depends on “ask the person who last deployed it,” the operations story is not finished.

## Practical Deployment Rule

Treat migrations, worker rollout, and static/media publication as one release system, not three unrelated chores.

Operational clarity is part of application quality.

That is especially true once Celery, caches, and multiple environments are involved.

Teams should be able to explain the deploy sequence without improvising it live.

Reliable operations are mostly disciplined repetition.

Document the path once, then keep it current.

That discipline prevents fragile releases.

It also reduces hidden dependency on one operator.

Operational simplicity is an architectural win.

## Release Readiness Checklist

- [ ] async/background work is separated from request path where appropriate
- [ ] caching strategy and invalidation assumptions are explicit
- [ ] deployment process covers migrations, assets, app server, and workers
- [ ] production config is environment-driven and documented
- [ ] Celery, caching, and static/media ownership are operationally clear

## Deployment Checklist

1. environment variables set correctly
2. migrations run safely
3. static assets built/collected appropriately
4. app server and worker processes configured
5. health/smoke checks run after deploy

## Common Ops Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| treating Celery as optional while request path grows | latency and UX pain | offload async work |
| unclear static/media ownership | broken asset serving | explicit deployment design |
| no migration/runbook discipline | fragile releases | document and automate |

## Release Readiness Checklist

- [ ] async/background work is separated from request path where appropriate
- [ ] caching strategy and invalidation assumptions are explicit
- [ ] deployment process covers migrations, assets, app server, and workers
- [ ] production config is environment-driven and documented
