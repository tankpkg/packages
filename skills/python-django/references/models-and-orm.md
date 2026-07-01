# Models and ORM

Sources: Django official documentation (models, QuerySets, managers, migrations), Django REST Framework docs, community Django performance guidance, production ORM best practices

Covers: model design, QuerySet usage, `select_related`, `prefetch_related`, managers, annotations, aggregation, migrations, and practical ORM performance patterns in Django.

## The ORM Is Powerful, Not Magic

Django’s ORM makes relational querying expressive, but it still maps to real SQL with real costs.

| Strength | Risk |
|---------|------|
| readable query composition | hidden N+1 and query fanout |
| composable filters and annotations | accidental heavy joins |
| migration-backed schema evolution | complacency around DB behavior |

Use the ORM deliberately, not blindly.

## Model Design Rules

| Rule | Why |
|-----|-----|
| model the domain clearly first | easier query semantics |
| index common filters and joins | predictable performance |
| avoid giant all-purpose models | lower maintenance cost |

Keep fields, relations, and constraints aligned with actual access patterns.

## QuerySet Fundamentals

| Operation | Use |
|----------|-----|
| `filter()` | narrow rows |
| `exclude()` | remove rows |
| `select_related()` | eager load FK / one-to-one |
| `prefetch_related()` | eager load collections |
| `annotate()` | computed columns |
| `aggregate()` | summary results |

### Lazy evaluation matters

QuerySets are lazy until evaluated. That is powerful, but it means template loops and helper functions can accidentally trigger queries where you do not expect them.

## `select_related` vs `prefetch_related`

| Need | Use |
|------|-----|
| single related object via FK / one-to-one | `select_related` |
| many-to-many or reverse FK collections | `prefetch_related` |

### Rule of thumb

If the relation can be joined in one SQL query, `select_related` is usually right. If it needs separate collection loading, `prefetch_related` is the tool.

## N+1 Review Questions

1. Is a template, serializer, or loop touching relations repeatedly?
2. Are nested related objects loaded intentionally?
3. Could counts or aggregates replace full collection loads?

## Managers and QuerySet Reuse

Custom managers and QuerySet methods help reuse filtering logic cleanly.

```python
class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(published_at__isnull=False)


class Post(models.Model):
    objects = PostQuerySet.as_manager()
```

Keep manager/queryset helpers query-focused, not workflow-heavy.

## Annotations and Aggregation

| Need | Tool |
|------|------|
| computed count per row | `annotate(Count(...))` |
| total across queryset | `aggregate()` |
| conditional metrics | filtered annotations |

Push work into the database when it simplifies response shape and avoids Python loops over many rows.

## Migration Rules

1. small, reviewable schema changes
2. additive changes before destructive ones where possible
3. index intentionally
4. separate large data backfills from fragile schema operations when needed

Migrations are operational artifacts, not just development output.

## ORM Anti-Patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| template loops causing hidden queries | poor page performance | eager load explicitly |
| huge fat model methods mixing workflows | weak maintainability | extract services/helpers |
| defaulting to `.all()` on large tables | memory and latency risk | paginate and shape queries |

## Model Field Design Questions

1. Is this field queried often enough to justify an index?
2. Does this belong in the primary table or a related model?
3. Is the null/default behavior explicit and correct?

Field decisions become query and migration decisions later.

## Relation Loading Checklist

| Question | Tool |
|---------|------|
| one related object accessed repeatedly? | `select_related` |
| collection or reverse relation accessed repeatedly? | `prefetch_related` |
| count only needed? | `annotate(Count(...))` or `aggregate()` |

## QuerySet Review Heuristics

| Signal | Review focus |
|-------|--------------|
| admin page feels slow | query count and relation loading |
| API serializer deeply nests data | eager loading + payload shape |
| list endpoint returns huge rows | field selection, pagination |

## Manager and QuerySet Smells

| Smell | Why it matters |
|------|----------------|
| manager method with side effects | hidden behavior |
| scope-like logic scattered across views | weak reuse |
| giant custom manager as service layer replacement | poor boundaries |

## Annotation Use Cases

| Use case | Example |
|---------|---------|
| count comments per post | `annotate(Count('comments'))` |
| sum order totals | `annotate(Sum('items__price'))` |
| conditional metrics | filtered annotations |

Annotations are often better than Python loops over many rows.

## Transaction Questions

1. Must these writes succeed or fail together?
2. Is there external I/O inside the transaction that should move out?
3. Are you locking more rows than needed?

## Migration Review Checklist

| Check | Why |
|------|-----|
| index changes intentional | query performance |
| destructive changes staged carefully | safer rollout |
| data migrations separated when large | lower operational risk |

## ORM Review Questions

1. What SQL does this queryset likely emit?
2. Are relation loads explicit?
3. Can this result set grow large enough to require pagination or chunking?

## Practical Performance Discipline

Measure query count and query shape before inventing caching or premature service abstraction.

## QuerySet Composition Rules

| Rule | Why |
|-----|-----|
| compose filters incrementally | easier reuse and testing |
| keep expensive annotations visible | query clarity |
| avoid surprise evaluation in helpers | predictable performance |

## Model Method Boundaries

| Good model method | Bad model method |
|------------------|------------------|
| small domain behavior tied to one model | cross-system orchestration |
| convenience query helpers | external API workflows |
| simple state transition helpers | hidden multi-step business process |

## Aggregation and Annotation Questions

1. Can the database compute this more efficiently than Python?
2. Do we need the full related set, or only counts/sums?
3. Will this annotation change ordering or pagination semantics?

## Pagination Review

| Concern | Recommendation |
|--------|----------------|
| large result sets | paginate explicitly |
| admin/report screens | avoid loading everything by default |
| API lists | keep page size bounded and predictable |

## ORM Smells

| Smell | Why it matters |
|------|----------------|
| lots of `.all()` calls in views | likely under-shaped queries |
| serializers/templates causing relation queries | hidden performance regressions |
| managers acting like service layer | boundary confusion |

## Data Modeling Questions

1. Is this relation cardinality correct for the actual domain?
2. Do constraints reflect business truth or just convenience?
3. Will this schema shape make common queries cheap or awkward?

## Bulk Operations

| Operation | Guidance |
|----------|----------|
| `bulk_create` | great for inserts, but skips some model hooks |
| `bulk_update` | useful for mass updates, but validate side effects carefully |
| queryset `update()` | efficient when model `save()` hooks are not required |

Bulk operations are powerful, but they bypass parts of the model lifecycle many teams implicitly rely on.

## Save Hooks and Signals Caution

| Tool | Good for | Risk |
|-----|----------|------|
| model `save()` override | tightly local persistence behavior | hidden side effects |
| signals | loose coupling for app-wide reactions | hard-to-trace execution |

Default to explicit workflows before introducing model lifecycle magic.

## `select_for_update` and Concurrency

Use row locks intentionally when concurrent writes can corrupt business invariants.

| Need | Pattern |
|-----|---------|
| serialized financial/accounting update | transaction + `select_for_update()` |
| simple eventually-correct counters | maybe avoid lock and redesign |

Locks solve real problems, but they also add contention and deadlock risk.

## Query Review Checklist

1. What SQL shape does this queryset produce?
2. Are joins and prefetches explicit and proportionate?
3. Does pagination happen before large materialization?
4. Are indexes aligned to the filter/order pattern?

## ORM Safety Heuristics

| Heuristic | Why |
|----------|-----|
| avoid hiding queries in properties/template tags | performance predictability |
| keep query helpers composable | cleaner reuse |
| favor explicitness over “clever” manager magic | maintainability |

## Final ORM Questions

1. Could this view/API path be fixed by query shaping before caching?
2. Are you pulling more fields or rows than needed?
3. Does the schema encourage or fight the most common read path?

## Release Readiness Checklist

- [ ] common relation access paths use `select_related` or `prefetch_related` intentionally
- [ ] managers/querysets keep reusable query logic clear
- [ ] annotations/aggregates replace Python loops where appropriate
- [ ] migrations are operationally safe and indexed for real access patterns
