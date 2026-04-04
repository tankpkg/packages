# Views and Routing

Sources: Django official documentation (URL dispatcher, views, generic views, forms, middleware, auth), Django community best practices, production Django application patterns

Covers: function-based views, class-based views, URL routing, forms, middleware, auth boundaries, request/response shaping, and practical route organization in Django.

## Thin Views, Explicit Workflows

Views should translate HTTP into domain operations, not become the whole application.

| Good view responsibility | Bad view responsibility |
|--------------------------|-------------------------|
| parse request input | heavy orchestration logic |
| call service/query/form | hidden cross-system side effects |
| return response/redirect | 200-line business workflow |

## FBV vs CBV

| Use case | Best fit |
|---------|----------|
| simple explicit request flow | function-based view |
| standard CRUD/list/detail patterns | class-based view |
| reusable mixins and inheritance fit | class-based view |

Start with the simpler expression of the behavior. Do not force CBVs where plain functions are clearer.

## URL Organization

| Pattern | Use |
|--------|-----|
| app-local `urls.py` | standard modular Django app |
| project-level include tree | multiple apps/features |
| namespaced routes | avoid reverse collisions |

### Example

```python
urlpatterns = [
    path("posts/", include(("posts.urls", "posts"), namespace="posts")),
    path("api/", include("api.urls")),
]
```

## Class-Based View Heuristics

| Need | View class |
|-----|------------|
| object list | `ListView` |
| detail page | `DetailView` |
| create/update forms | `CreateView` / `UpdateView` |
| delete confirmation | `DeleteView` |

Use generic CBVs when they genuinely reduce repetition. Override methods sparingly and intentionally.

## Form Handling Rules

1. Use Django forms or ModelForms for server-rendered workflows
2. Validate on server even if JS exists
3. Keep side effects out of forms unless tightly tied to validation/cleaning

## Middleware Use Cases

| Good middleware | Example |
|----------------|---------|
| auth/session enforcement | access boundaries |
| locale / tenant resolution | request-wide concern |
| correlation IDs / logging | cross-cutting ops concern |

Avoid putting product workflows in middleware.

## Auth Boundaries

| Surface | Pattern |
|--------|---------|
| server-rendered authenticated pages | login-required / permission mixins |
| APIs | explicit auth classes / DRF permissions |
| mixed apps | keep web and API auth semantics distinct |

## Common View Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| giant CBV overrides everywhere | hard reasoning | simplify or move to FBV/service |
| hidden ORM work in templates | performance drift | precompute in view/query layer |
| auth checks duplicated inconsistently | security drift | centralize permission rules |

## Response Patterns

| Surface | Return |
|--------|--------|
| HTML page | rendered template |
| mutation success | redirect |
| API | JSON / DRF response |
| HTMX partial | fragment template |

## Route Review Questions

1. Is URL structure reflecting product boundaries clearly?
2. Are auth/permission assumptions obvious?
3. Is the view primarily transport logic rather than business logic?

## Form Workflow Review

| Concern | Recommendation |
|--------|----------------|
| validation reuse | Form or FormRequest-equivalent pattern |
| mutation after valid form | explicit service/helper if non-trivial |
| redirect target | predictable post-success UX |

## Middleware Review Questions

1. Is this truly cross-cutting?
2. Could this logic be clearer in a view, decorator, or service?
3. Does it hide product-specific behavior unexpectedly?

## CBV Smells

| Smell | Why it matters |
|------|----------------|
| many overridden methods for one screen | generic view may no longer fit |
| mixins stacked without clarity | hard reasoning |
| dispatch method filled with workflow logic | weak separation |

## FBV Smells

| Smell | Why it matters |
|------|----------------|
| repeated request parsing in many functions | missing abstraction |
| auth/permission logic duplicated | weak consistency |
| giant branchy handlers | time to extract or use CBV/service |

## Route Namespace Benefits

| Benefit | Why |
|--------|-----|
| safer reverse URL usage | avoids collisions |
| app modularity | clearer boundaries |
| easier refactors | route identity stays explicit |

## Template Boundary Rule

Templates should render prepared data, not perform surprise business logic or relation traversal that changes query behavior implicitly.

## Auth Boundary Checklist

| Check | Why |
|------|-----|
| guest path tested | expected denial/redirect |
| authenticated allowed path tested | correctness |
| forbidden path tested | permission confidence |

## Response Review Heuristics

1. Is this better expressed as HTML, JSON, redirect, or fragment?
2. Does the response shape match the route surface clearly?
3. Are errors surfaced appropriately for browser vs API clients?

## Route Naming Discipline

| Pattern | Benefit |
|--------|---------|
| namespaced routes | cleaner reverse lookups |
| action-oriented names for special routes | explicit intent |
| app-level URL grouping | easier navigation in codebase |

## CBV Review Questions

1. Is inheritance still reducing repetition, or hiding behavior?
2. Would a function-based view be simpler here?
3. Are mixins clarifying or obscuring the flow?

## Form Review Questions

| Question | Why |
|---------|-----|
| does validation belong in a Form/FormClass? | keep view thin |
| is success path a redirect or fragment update? | response clarity |
| are side effects too large for the view? | extraction signal |

## Middleware vs Decorator vs View Logic

| Need | Best place |
|-----|------------|
| route-local auth/permission | decorator/mixin/view boundary |
| app-wide concern | middleware |
| business workflow | service/helper |

Choosing the right layer keeps Django apps understandable.

## Routing Smells

| Smell | Why it matters |
|------|----------------|
| huge project `urls.py` with no modularization | poor navigation |
| repeated auth wrappers everywhere | missing reusable boundary |
| route names unclear or inconsistent | reverse and maintenance pain |

## View Performance Questions

1. Are ORM queries shaped before template/rendering?
2. Are repeated lookups hidden in helpers or template tags?
3. Could simple caching or query shaping solve the bottleneck before architectural changes?

## Generic Editing Views

| View | Best for |
|-----|----------|
| `CreateView` | straightforward creation form |
| `UpdateView` | standard edit flows |
| `DeleteView` | confirmation and delete pattern |

Use generic editing views when the workflow is conventional. Once side effects or permission rules become heavily custom, explicit views often read better.

## Decorators and Mixins

| Need | Tool |
|-----|------|
| auth guard on FBV | decorator |
| auth/permission on CBV | mixin |
| cross-cutting request behavior | middleware |

Choose the narrowest layer that expresses the concern cleanly.

## Error Handling Patterns

| Surface | Pattern |
|--------|---------|
| missing object | `get_object_or_404` or equivalent |
| form validation | invalid form re-render |
| permission failure | 403 or redirect semantics matching surface |
| API-ish route | explicit JSON error response |

## Route Evolution Questions

1. Will this route need API and HTML variants later?
2. Does route naming stay stable if the implementation changes?
3. Are special-case routes grouped sanely with their feature area?

## Template Integration Notes

Keep template context small and intentional.

| Anti-pattern | Fix |
|-------------|-----|
| passing giant model graphs “just in case” | shape context tightly |
| business branching in templates | precompute in view/service |

## Final View/Routing Checklist

- [ ] route naming and namespacing are intentional
- [ ] view complexity matches FBV/CBV choice
- [ ] auth and permission boundaries are visible and testable
- [ ] templates render prepared data, not surprise ORM access

## Release Readiness Checklist

- [ ] route tree is modular and namespaced where needed
- [ ] FBV/CBV choice fits the actual complexity
- [ ] forms validate server-side and keep workflows understandable
- [ ] middleware stays cross-cutting, not product-specific
- [ ] view code remains transport-focused and testable
