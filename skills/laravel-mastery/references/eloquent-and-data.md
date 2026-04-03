# Eloquent and Data

Sources: Laravel official documentation (Eloquent ORM, relationships, mutators/casts, resources, factories, migrations), Matt Stauffer (Laravel Up & Running), Jonathan Reinink (Eloquent Performance Patterns), Laravel community best practices

Covers: Eloquent relationships, scopes, observers, casts, eager loading, query optimization, migrations, factories, API resources, and practical data-layer patterns for Laravel applications.

## Eloquent Is an ORM, Not Your Architecture

Eloquent makes persistence pleasant, but it should not become the place where every business rule, query, and side effect ends up living.

| Good use | Anti-pattern |
|---------|--------------|
| relationships, scopes, casts, simple model behavior | 800-line god models |
| query composition | embedding every business workflow in model methods |
| expressive resource loading | hidden side effects in accessors and boot methods |

Use Eloquent for data modeling and query composition. Move business workflows into services, actions, jobs, or domain-specific classes when complexity grows.

## Relationship Selection Guide

| Need | Relationship |
|-----|--------------|
| Parent owns many children | `hasMany` |
| Child belongs to one parent | `belongsTo` |
| One-to-one related row | `hasOne` / `belongsTo` |
| Many-to-many pivot | `belongsToMany` |
| Polymorphic ownership | `morphTo`, `morphMany`, etc. |

### Example

```php
class Post extends Model
{
    public function author(): BelongsTo
    {
        return $this->belongsTo(User::class, 'user_id');
    }

    public function comments(): HasMany
    {
        return $this->hasMany(Comment::class);
    }
}
```

Keep relationship names semantic and pluralize collection relationships naturally.

## Eager Loading Rules

N+1 problems are one of the most common Laravel production mistakes.

| Pattern | Use |
|--------|-----|
| `with()` | eager load known related models |
| `load()` | lazy eager load after retrieval |
| `loadMissing()` | add related data without duplicating loads |
| `withCount()` | aggregate relation count without loading collection |

### Example

```php
$posts = Post::query()
    ->with(['author', 'comments.user'])
    ->withCount('comments')
    ->latest()
    ->paginate();
```

### Good eager loading heuristics

1. If the view or API serializer accesses a relation inside a loop, eager load it
2. Prefer `withCount()` and aggregate subqueries for counts/sums
3. Limit selected columns when loading large related models

### Common eager loading mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| Loading relations in Blade loops | N+1 explosions | move to controller/query |
| Eager loading huge graphs by default | memory blowup | load only what page needs |
| Using accessors that hit relations implicitly | hidden DB work | make loading explicit |

## Query Scope Patterns

Scopes keep query logic reusable and readable.

### Local scope example

```php
class Post extends Model
{
    public function scopePublished(Builder $query): Builder
    {
        return $query->whereNotNull('published_at');
    }

    public function scopeVisibleTo(Builder $query, User $user): Builder
    {
        return $query->where('team_id', $user->team_id);
    }
}
```

### Scope rules

| Rule | Why |
|-----|-----|
| Keep scopes composable | chain cleanly |
| Use verb-like names | improve readability |
| Return `Builder` | preserve fluent use |
| Avoid hidden side effects | scopes should shape queries only |

### Good scope examples

| Scope | Meaning |
|------|---------|
| `published()` | only published records |
| `forTenant($tenantId)` | tenant partition |
| `active()` | not soft-deleted / enabled |
| `search($term)` | reusable text filter |

## Casts and Value Normalization

Use casts to normalize types and improve correctness.

| Cast | Use for |
|-----|---------|
| `boolean` | flags |
| `array` / `json` | structured JSON fields |
| `datetime` / immutable datetime | timestamps |
| enum casts | finite domain values |
| custom casts | rich value objects |

### Example

```php
protected function casts(): array
{
    return [
        'published_at' => 'immutable_datetime',
        'settings' => 'array',
        'status' => PostStatus::class,
        'is_featured' => 'boolean',
    ];
}
```

Do not use casts to hide expensive transformations or unrelated business logic.

## Accessors and Mutators

Accessors should stay lightweight and deterministic.

| Good accessor | Bad accessor |
|--------------|--------------|
| format a display name | query another model |
| combine local fields | hit an external API |
| map enum to label | trigger side effects |

### Mutator example

```php
protected function email(): Attribute
{
    return Attribute::make(
        set: fn (string $value) => strtolower(trim($value)),
    );
}
```

Normalize input close to the model when the rule is universal.

## Observer Guidelines

Observers are powerful but easy to abuse.

### Use observers for

| Good fit | Example |
|---------|---------|
| universal side effects tied to persistence | slug generation, audit events |
| cache invalidation tied to model changes | clear tagged cache on save |
| small persistence lifecycle hooks | set defaults on create |

### Avoid observers for

| Anti-pattern | Better move |
|-------------|-------------|
| big business workflows | explicit service/action |
| API calls | queue/job or service |
| permission-sensitive logic | service/controller/policy |

Observers are hidden execution paths. If a side effect needs high visibility, keep it explicit.

## Mass Assignment and Fillable Rules

Guard against accidental unsafe writes.

| Strategy | Use |
|---------|-----|
| `$fillable` | explicit allowed assignment |
| `$guarded = []` | only in tightly controlled internal models |

Prefer explicit `$fillable` for user-facing applications.

## Migrations: Practical Patterns

Keep migrations small, reversible when possible, and aligned with deployment constraints.

### Good migration rules

1. Add indexes for foreign keys and common filters
2. Avoid giant destructive schema changes during peak traffic
3. Split data backfills from schema changes when large datasets are involved
4. Name constraints and indexes clearly

### Example

```php
Schema::create('posts', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->constrained()->cascadeOnDelete();
    $table->string('title');
    $table->string('slug')->unique();
    $table->timestamp('published_at')->nullable()->index();
    $table->softDeletes();
    $table->timestamps();
});
```

## Indexing Strategy

| Query pattern | Index suggestion |
|--------------|------------------|
| `where user_id = ?` | index or foreign key index |
| `where status = ? and published_at < ?` | composite index |
| sort by `created_at` for recent records | index on `created_at` |
| lookup by slug | unique index |

Monitor real queries before adding speculative indexes everywhere.

## API Resources

Resources keep response shape consistent and decouple transport from raw model serialization.

```php
class PostResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'author' => new UserResource($this->whenLoaded('author')),
            'comments_count' => $this->whenCounted('comments'),
        ];
    }
}
```

### Resource rules

| Rule | Why |
|-----|-----|
| Use `whenLoaded` | avoid accidental lazy loads |
| Use `whenCounted` | pair with `withCount()` |
| Keep resource shape explicit | stable API contracts |
| Avoid leaking hidden columns accidentally | safer serialization |

## Factories and Test Data

Factories should create valid defaults and expose states for meaningful variants.

```php
Post::factory()->published()->create();
User::factory()->admin()->create();
```

### Factory state guidelines

| State | Example |
|------|---------|
| lifecycle state | `published`, `archived` |
| permissions state | `admin`, `editor` |
| edge case | `unverified`, `suspended` |

Avoid huge factories with dozens of random fields that do not help tests communicate intent.

## Query Optimization Checklist

1. Eager load all relations needed by the response
2. Replace collection loops with SQL aggregation where possible
3. Select only needed columns
4. Paginate large result sets
5. Add indexes based on actual query patterns

### Useful query tools

| Tool | Use |
|-----|-----|
| Debugbar / Telescope | local query inspection |
| `DB::listen()` | capture SQL timing |
| database EXPLAIN | understand planner choices |
| Telescope slow query review | production-ish diagnostics |

## Soft Deletes

Soft deletes can simplify recovery but complicate queries.

| Concern | Recommendation |
|--------|----------------|
| user-facing deleted records | usually exclude by default |
| admin recovery workflow | use `withTrashed()` intentionally |
| unique constraints | account for soft-deleted rows |

Do not enable soft deletes by reflex on every model.

## Common Eloquent Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| Loading relations in API resources without `whenLoaded` | hidden N+1 | eager load + conditional resource output |
| Fat models with services hidden inside | hard maintenance | extract actions/services |
| Overusing observers | invisible behavior | keep workflows explicit |
| Blindly using `Model::all()` | memory blowups | paginate, chunk, cursor |
| Random accessor logic with queries | surprise DB traffic | explicit query/service layer |

## Release Readiness Checklist

- [ ] Relationship loading is explicit for every heavy response path
- [ ] Scopes compose cleanly and stay query-focused
- [ ] Accessors and casts remain lightweight and predictable
- [ ] Observers handle only small universal persistence hooks
- [ ] Migrations are incremental and indexed for real access patterns
- [ ] API resources avoid lazy-loading surprises
- [ ] Factories and states communicate test intent clearly
