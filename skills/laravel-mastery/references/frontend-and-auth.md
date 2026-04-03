# Frontend and Auth

Sources: Laravel official documentation (Blade, Livewire, Inertia, Sanctum, Breeze, Fortify, Jetstream, Socialite, authorization), Livewire documentation, Inertia documentation, Laravel community best practices

Covers: Blade, Livewire, Inertia frontend stacks, Sanctum, Breeze, Fortify, Jetstream, guards, gates, policies, and Socialite integration patterns in Laravel applications.

## Pick the Smallest Frontend Stack That Solves the Problem

Laravel gives you multiple UI approaches. Start with the simplest stack that fits your UX and team skills.

| Need | Stack |
|-----|-------|
| Mostly server-rendered pages | Blade + Alpine |
| Dynamic interactions without leaving PHP | Livewire |
| SPA-like experience with React/Vue | Inertia |
| Pure API backend for separate frontend/mobile | Sanctum + external app |

Avoid choosing the fanciest stack by default. Complexity compounds fast.

## Blade Rules

Blade is still the fastest path for many apps.

### Good Blade use cases

| Use case | Why |
|---------|-----|
| admin CRUD screens | simple, fast to ship |
| settings pages | server-rendered, SEO-friendly |
| forms and dashboards with light interactivity | pairs well with Alpine |

### Blade practices

1. Extract repeated UI into components
2. Keep heavy data loading out of views
3. Use view models/resources when templates get noisy

## Livewire Rules

Livewire is ideal when you want interactive UI while staying in the Laravel mental model.

| Good fit | Watch out for |
|---------|----------------|
| multi-step forms | hidden complexity if component grows huge |
| admin tables and filters | server round-trips on every interaction |
| dashboards with moderate interactivity | overusing one mega-component |

### Livewire guidelines

| Rule | Why |
|-----|-----|
| Keep components focused | easier state reasoning |
| Validate input in actions | consistent server truth |
| Push heavy side effects to jobs/services | cleaner components |

## Inertia Rules

Inertia is a good bridge when the team wants React/Vue ergonomics without building a full API-first backend.

### Use Inertia when

| Signal | Why |
|-------|-----|
| team is strong in React/Vue | leverage frontend skills |
| app needs richer client interactivity | SPA-like feel |
| you still want Laravel routing/auth/controllers | keeps backend conventions |

### Inertia caution points

| Mistake | Problem |
|--------|---------|
| treating it like a fully separate frontend and backend | duplicate complexity |
| oversharing giant props | slower pages and poor boundaries |
| mixing heavy business logic into controllers | maintainability problems |

## Sanctum Selection Guide

Sanctum supports two major modes.

| Mode | Use for |
|-----|---------|
| Cookie/session auth | SPA on same top-level domain |
| Token auth | mobile apps, third-party clients, simple API tokens |

### Rule of thumb

If your frontend and Laravel app live on the same main domain and browser auth is primary, prefer Sanctum cookie auth over hand-rolled JWT flows.

## Breeze vs Fortify vs Jetstream

| Package | Best for |
|--------|----------|
| Breeze | small/simple auth scaffolding |
| Fortify | headless auth backend without UI |
| Jetstream | teams, 2FA, sessions, richer account features |

### Selection rules

| Need | Package |
|-----|---------|
| login/register/reset only | Breeze |
| custom frontend but Laravel auth backend | Fortify |
| account management + teams + 2FA | Jetstream |

Do not install Jetstream if you only need a login form.

## Guards and Providers

Guards define **how** authentication happens. Providers define **where users come from**.

| Concern | Config area |
|--------|-------------|
| session vs token | guard |
| user source model/table | provider |
| route protection | middleware + guard |

Use explicit guards when mixing admin, API, and web entry points.

## Gates and Policies

| Tool | Use for |
|-----|---------|
| Gate | small app-wide checks |
| Policy | model/resource-level authorization |

### Policy example

```php
public function update(User $user, Post $post): bool
{
    return $user->id === $post->user_id;
}
```

Policies keep authorization close to the resource rather than scattered across controllers and views.

## Frontend Stack Decision Tree

| Signal | Recommendation |
|--------|----------------|
| Mostly forms and CRUD | Blade + Alpine |
| Complex interactions but PHP-first team | Livewire |
| Strong frontend team wants React/Vue | Inertia |
| Mobile + web clients with separate UI stacks | API + Sanctum |

## Social Login with Socialite

Use Socialite when you need OAuth providers like Google or GitHub.

### Checklist

1. Map provider user to internal account carefully
2. Handle existing email collisions explicitly
3. Store provider ID, not just email
4. Treat account linking as a deliberate workflow

### Common mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| trusting email alone | account hijack risk | store provider subject/ID |
| silent auto-linking | surprise account merges | explicit linking flow |
| provider logic in controllers everywhere | hard maintenance | auth service / callback handler class |

## Auth Flow Patterns

| Flow | Best for |
|-----|----------|
| session-based browser auth | Blade, Livewire, Inertia on same site |
| token auth | mobile clients, personal access tokens |
| social login | consumer-facing apps |
| 2FA / richer account settings | Jetstream or custom Fortify flow |

## CSRF and Session Safety

Laravel handles a lot for you, but only if you stay inside the conventions.

| Rule | Why |
|-----|-----|
| Keep stateful browser auth behind sessions/cookies | simpler and safer than ad hoc tokens |
| Use built-in CSRF protection for form routes | prevent request forgery |
| Do not disable CSRF casually | high-risk shortcut |
| Keep session config environment-specific and secure | correct cookie behavior |

## Common Frontend/Auth Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| picking Jetstream for a tiny app | unnecessary complexity | use Breeze |
| overusing Livewire for giant dashboards | bloated server-driven state | split components or use Inertia |
| building a separate API with Inertia anyway | duplicate architecture | choose one model clearly |
| custom auth before evaluating Sanctum/Fortify | needless security risk | use built-ins first |
| duplicating policy checks in Blade and controllers inconsistently | authorization drift | centralize in policies/gates |

## Session and Guard Boundaries

When the same app serves browser users, API consumers, and admins, auth boundaries must stay explicit.

| Surface | Recommended guard |
|--------|-------------------|
| standard browser app | `web` |
| SPA using Sanctum cookies | `web` + Sanctum middleware support |
| token-based API | `sanctum` or custom API guard |
| separate admin area | dedicated guard only if the domain truly differs |

Do not create extra guards unless the authentication model actually changes.

## Blade vs Livewire vs Inertia Trade-offs

| Concern | Blade | Livewire | Inertia |
|--------|-------|----------|---------|
| onboarding complexity | lowest | medium | medium-high |
| frontend JS fluency required | low | low-medium | medium-high |
| server-first ergonomics | high | high | medium |
| rich SPA interactions | limited | moderate | high |

This table should drive stack selection more than hype cycles.

## Team Workflow Considerations

| Team profile | Likely best fit |
|-------------|------------------|
| PHP-heavy backend team | Blade or Livewire |
| mixed backend/frontend team | Inertia |
| product needs separate mobile/web consumers | API + Sanctum |

Choose the stack that matches maintenance reality after launch.

## Release Readiness Checklist

- [ ] Frontend stack matches team skills and UI complexity
- [ ] Auth package selection is intentional: Breeze, Fortify, Jetstream, Sanctum
- [ ] Guards and providers are explicit when multiple auth surfaces exist
- [ ] Policies/gates centralize authorization rules
- [ ] Social login stores stable provider identifiers, not only emails
- [ ] CSRF/session protection remains inside Laravel conventions
