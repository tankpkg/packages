# Routing and Controllers

Sources: Laravel official documentation (routing, controllers, middleware, requests, authorization, rate limiting, API resources), Matt Stauffer (Laravel Up & Running), Laravel community best practices

Covers: route organization, controllers, middleware, route model binding, form requests, policies, rate limiting, and endpoint structure patterns for Laravel apps and APIs.

## Routes Should Express Application Surface Area

Laravel routing is expressive enough that your route files often become one of the clearest architectural maps in the project.

| Goal | Pattern |
|-----|---------|
| Small app | `routes/web.php` + `routes/api.php` |
| Larger app | split route files by domain and include them |
| Admin vs public separation | middleware groups + prefixed files |

Keep route definitions readable. Do not hide your whole route tree behind excessive magic.

## Web vs API Routes

| File | Typical use |
|-----|-------------|
| `routes/web.php` | session-backed browser pages |
| `routes/api.php` | stateless API endpoints |
| custom included route files | domain segmentation in large apps |

The main distinction is middleware stack and usage style, not whether the endpoint returns HTML or JSON exclusively.

## Route Grouping Patterns

### Basic grouping

```php
Route::middleware(['auth', 'verified'])
    ->prefix('dashboard')
    ->name('dashboard.')
    ->group(function () {
        Route::get('/', DashboardController::class)->name('index');
        Route::resource('posts', PostController::class);
    });
```

### Why groups matter

| Benefit | Meaning |
|--------|---------|
| Shared middleware | fewer repeated declarations |
| Shared prefixes | cleaner organization |
| Shared names | easier route generation |

Use groups to reduce duplication, not to create deeply nested routing puzzles.

## Controller Design Rules

Controllers should translate HTTP requests into application actions.

### Good controller responsibilities

1. Receive request + route params
2. Validate via Form Request or small explicit validation
3. Authorize request
4. Call action/service/domain operation
5. Return response/resource/redirect

### Bad controller responsibilities

| Anti-pattern | Better move |
|-------------|-------------|
| Complex query assembly mixed with business decisions | service/query object |
| External API orchestration | service/job |
| Huge validation arrays inline in every method | Form Request |
| Permission logic duplicated in methods | policies/gates/middleware |

## Single-Action vs Resource Controllers

| Pattern | Use when |
|--------|----------|
| Invokable controller | one focused endpoint |
| Resource controller | standard CRUD set |
| Traditional multi-method controller | bounded set of related endpoints |

### Single-action example

```php
class PublishPostController
{
    public function __invoke(PublishPostRequest $request, Post $post)
    {
        $this->authorize('publish', $post);
        $post->publish();
        return redirect()->route('posts.show', $post);
    }
}
```

Use invokable controllers when the operation has one clear purpose.

## Route Model Binding

Route model binding removes repetitive lookup code and centralizes 404 behavior.

```php
Route::get('/posts/{post}', [PostController::class, 'show']);

public function show(Post $post)
{
    return new PostResource($post);
}
```

### Explicit binding rules

| Need | Pattern |
|-----|---------|
| default lookup by ID | implicit binding |
| lookup by slug | `getRouteKeyName()` or explicit binding |
| scoped nested resources | scoped bindings |

### Slug binding example

```php
public function getRouteKeyName(): string
{
    return 'slug';
}
```

## Nested and Scoped Bindings

Use scoped bindings when child resources must belong to the parent route context.

```php
Route::scopeBindings()->group(function () {
    Route::get('/users/{user}/posts/{post}', [UserPostController::class, 'show']);
});
```

This prevents retrieving a post that does not belong to the given user.

## Form Requests

Form Requests are the default place for request validation and request-level authorization.

```php
class StorePostRequest extends FormRequest
{
    public function authorize(): bool
    {
        return $this->user()->can('create', Post::class);
    }

    public function rules(): array
    {
        return [
            'title' => ['required', 'string', 'max:255'],
            'body' => ['required', 'string'],
        ];
    }
}
```

### Why Form Requests help

| Benefit | Meaning |
|--------|---------|
| Cleaner controllers | validation out of method body |
| Reuse | central request contract |
| Authorization hook | `authorize()` close to request semantics |

## Authorization Placement

| Need | Tool |
|-----|------|
| model-specific permission | policy |
| simple application-wide check | gate |
| route-level broad protection | middleware |
| request-specific validation + auth | Form Request `authorize()` |

### Policy example

```php
public function update(User $user, Post $post): bool
{
    return $user->id === $post->user_id;
}
```

Keep policy logic simple and explicit. Complex policy workflows often signal domain rules that should live in services.

## Middleware Selection

### Good middleware use cases

| Use case | Example |
|---------|---------|
| authentication | `auth`, `auth:sanctum` |
| email verification | `verified` |
| throttle | `throttle:api` |
| tenant resolution | custom middleware |
| locale setting | custom middleware |

### Bad middleware use cases

| Anti-pattern | Why |
|-------------|-----|
| heavy business workflows | hidden execution path |
| model mutation side effects | surprising behavior |
| complex permission branching | use policy or service |

Middleware should stay request-wide and cross-cutting.

## Rate Limiting

Laravel rate limiting is expressive and should be explicit for sensitive endpoints.

| Endpoint type | Strategy |
|--------------|----------|
| login / password reset | strict IP or user/email throttle |
| public API | token/IP quota |
| authenticated API | user-based limiter |

### Limiter example

```php
RateLimiter::for('api', function (Request $request) {
    return Limit::perMinute(60)->by($request->user()?->id ?: $request->ip());
});
```

## Response Patterns

| Surface | Return |
|--------|--------|
| Browser form submit | redirect + flash or validation errors |
| JSON API | resource / resource collection / structured JSON |
| Action endpoint | `response()->noContent()` for empty success |

Be consistent inside each surface area.

## API Resource Patterns

Use API Resources to control output shape.

```php
return new PostResource($post->load('author'));
```

### Resource rules

1. Keep serialization explicit
2. Pair resources with eager loading
3. Avoid dumping whole models with hidden surprises

## Controller Extraction Signals

| Signal | Extract into |
|-------|--------------|
| 50+ lines of orchestration | action/service |
| repeated query building | query object / scope |
| repeated mutation workflow | action class |
| repeated response formatting | resource / response helper |

## Common Routing Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| giant route files with no grouping | unreadable surface area | group by domain |
| inline closures everywhere in large apps | hard testing and reuse | use controllers |
| authorization inside every method body | duplication | policies or Form Requests |
| hidden binding assumptions | wrong records returned | explicit scoped binding |
| using middleware for feature logic | poor visibility | move to service/controller |

## Release Readiness Checklist

- [ ] Route files reflect domain boundaries clearly
- [ ] Controllers stay transport-focused and thin
- [ ] Validation lives in Form Requests or explicit request validators
- [ ] Policies and gates handle permission logic consistently
- [ ] Route model binding is explicit for IDs vs slugs vs scoped resources
- [ ] Rate limiting is configured for sensitive endpoints
- [ ] API responses use resources or a stable response contract
