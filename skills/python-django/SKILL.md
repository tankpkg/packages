---
name: "@tank/python-django"
description: |
  Production Django development across server-rendered apps and APIs. Covers
  Django models, QuerySet optimization (`select_related`, `prefetch_related`),
  views (class-based and function-based), forms, templates, authentication,
  Django REST Framework, Celery integration, HTMX patterns, Django Ninja,
  testing, migrations, caching, and deployment workflows.

  Synthesizes Django official documentation, Django REST Framework docs,
  Django Ninja docs, HTMX+Django practices, Celery docs, and community
  production patterns.

  Trigger phrases: "django", "django tutorial", "django best practices",
  "django orm", "django rest framework", "drf", "django celery",
  "django testing", "django htmx", "django ninja", "django models",
  "django views", "django forms", "django deployment", "django migrations"
---

# Python Django

## Core Philosophy

1. **Use Django conventions first** — The framework already solves most web-application structure problems well. Override conventions only when there is clear value.
2. **Treat the ORM as a query builder, not magic** — Know when `select_related`, `prefetch_related`, annotations, and transactions matter.
3. **Keep views thin and workflows explicit** — Move heavy orchestration into services, tasks, or domain helpers when complexity grows.
4. **Server-rendered and API paths can coexist** — Django is strong at HTML, JSON, and mixed architectures when boundaries stay clear.
5. **Operational discipline matters** — Migrations, Celery, caching, and deployment decisions shape reliability as much as application code.

## Quick-Start: Common Problems

### "My Django pages are slow"

1. Inspect query count first
2. Add `select_related` for foreign-key joins
3. Add `prefetch_related` for collections
4. Avoid template-level hidden ORM work
-> See `references/models-and-orm.md`

### "Should I use CBVs or FBVs?"

| Need | Use |
|------|-----|
| straightforward request flow | FBV |
| repeated CRUD/list/detail patterns | CBV |
| REST APIs | DRF views/viewsets as appropriate |
-> See `references/views-and-routing.md`

### "How do I add async/background work?"

1. Keep request path synchronous only for user-critical work
2. Push email/webhooks/reporting to Celery
3. Make tasks idempotent when possible
-> See `references/operations-and-deployment.md`

## Decision Trees

### Surface Selection

| Signal | Recommendation |
|--------|----------------|
| mostly server-rendered app | Django templates/forms |
| API-first backend | DRF or Django Ninja |
| progressively enhanced HTML interactions | HTMX + Django |
| mixed app + API | keep boundaries explicit |

### Query Optimization Choice

| Signal | Use |
|--------|-----|
| one-to-one / foreign key join | `select_related` |
| many-to-many or reverse relation | `prefetch_related` |
| aggregate values needed | annotations / aggregation |

## Reference Index

| File | Contents |
|------|----------|
| `references/models-and-orm.md` | Models, QuerySets, relations, select_related, prefetch_related, annotations, migrations, managers |
| `references/views-and-routing.md` | FBVs, CBVs, URL routing, forms, middleware, auth boundaries, request/response structure |
| `references/apis-and-htmx.md` | DRF, serializers, viewsets, permissions, Django Ninja, HTMX integration, mixed app/API patterns |
| `references/testing-and-auth.md` | Django testing, DRF testing, auth flows, permissions, factories, fixtures, request testing |
| `references/operations-and-deployment.md` | Celery, caching, static/media, deployment, environment config, production operations |
