# Deployment and Migration

Sources: SvelteKit official documentation (adapters, page options, deployment), Svelte 5 migration documentation, Vite documentation, adapter package docs for Vercel, Cloudflare, Node, and static hosting, community migration guides from 2024-2026

Covers: adapter selection, SSR/SSG/SPA trade-offs, page options, environment handling, deployment targets, performance tuning, and migration from Svelte 4 to Svelte 5 in real applications.

## Adapter Selection Is an Architecture Choice

SvelteKit adapters connect your app to a runtime target. Choose based on hosting model, runtime capabilities, and team constraints.

| Adapter | Best for |
|--------|----------|
| `adapter-node` | self-hosted Node servers, containers, VMs |
| `adapter-vercel` | Vercel hosting |
| `adapter-cloudflare` | Cloudflare Workers/Pages |
| `adapter-static` | fully prerendered sites |
| `adapter-auto` | prototypes or early-phase apps |

Use `adapter-auto` for experiments, not as a long-term production strategy when runtime behavior matters.

## Choosing SSR, SSG, or SPA Per Route

SvelteKit lets you choose rendering mode per route through page options.

| Need | Option |
|-----|--------|
| SEO + per-request freshness | SSR |
| Content known at build time | `prerender = true` |
| App-like dashboard with no SEO needs | `ssr = false` |
| Read-only page with no client JS needed | `csr = false` |

### Practical defaults

| Route type | Suggested mode |
|-----------|----------------|
| Marketing pages | prerender where possible |
| Blog/article pages | prerender or SSR depending on freshness |
| Authenticated dashboard | SSR or SPA depending on UX and infra |
| Admin tools | SSR by default unless strongly SPA-oriented |

## Page Option Interactions

| Option | Meaning | Common mistake |
|-------|---------|----------------|
| `prerender` | build to static HTML | using with truly dynamic user data |
| `ssr` | server-render route | disabling SSR too early |
| `csr` | enable client hydration | setting false on interactive pages |
| `trailingSlash` | URL slash behavior | inconsistent canonical URL strategy |

Keep route options explicit in places where deployment behavior matters.

## Node Deployment Pattern

Use `adapter-node` when you want full control or a traditional server/container model.

### Good fit

| Use case | Why |
|---------|-----|
| Docker/Kubernetes | standard Node deployment |
| Self-hosted infra | direct process ownership |
| Custom reverse proxy setup | full routing control |

### Operational notes

1. Run behind a reverse proxy/load balancer
2. Set proper trusted proxy configuration where needed
3. Handle environment variables through your platform, not checked-in `.env` secrets

## Vercel Deployment Pattern

Use `adapter-vercel` when your app fits Vercel’s serverless/edge model.

| Strength | Caveat |
|---------|--------|
| Easy deploys | platform-specific runtime assumptions |
| Smooth preview workflow | lock-in risk |
| Strong static + SSR support | cost/runtime trade-offs at scale |

Prefer explicit deployment testing if your app depends on file system, long-running work, or runtime-specific network behavior.

## Cloudflare Deployment Pattern

`adapter-cloudflare` is ideal for edge-first apps using Web Platform APIs.

| Good fit | Watch out for |
|---------|----------------|
| Fast global reads | Node-only dependencies |
| Light request handlers | unsupported server assumptions |
| Pages + Workers integration | DB drivers that need TCP |

When targeting Cloudflare, verify every dependency is edge-safe.

## Static Deployment Pattern

Use `adapter-static` only when the site can truly be prerendered.

### Good fit

| Example | Why |
|--------|-----|
| docs site | content known at build time |
| marketing site | mostly static pages |
| small blog | prebuilt content |

### Bad fit

| Anti-pattern | Why |
|-------------|-----|
| User dashboards | request-specific data |
| session-dependent pages | server logic needed |
| API-first mutation-heavy app | dynamic runtime behavior |

## Environment Variable Rules

SvelteKit distinguishes public and private env access.

| Kind | Use |
|-----|-----|
| `$env/static/private` | build-time server-only values |
| `$env/dynamic/private` | runtime server-only values |
| `$env/static/public` | build-time public values |
| `$env/dynamic/public` | runtime public values |

### Safety rule

If a variable should never reach the browser, keep it in a server-only file and use a private env module.

## Performance Tuning Checklist

| Concern | Recommendation |
|--------|----------------|
| Overfetching in layouts | load data closer to where it is used |
| Large serialized payloads | return smaller shaped objects |
| Heavy client JS | avoid unnecessary client-only libraries |
| Pages that could be static | prerender them |
| Slow server data sources | cache or stream intentionally |

### Deployment-aware performance questions

1. Does this route need SSR, or can it be prerendered?
2. Are we shipping too much client JS for mostly static content?
3. Are layout loads forcing expensive refetches on every navigation?

## Svelte 4 to Svelte 5 Migration Strategy

Migration is easier when done in controlled passes.

### Recommended order

1. Upgrade dependencies and tooling
2. Run official migration codemods where available
3. Migrate prop declarations from `export let` to `$props()`
4. Replace reactive `$:` statements with `$derived` / `$effect`
5. Migrate slots toward snippets where it improves clarity
6. Revisit shared stores only when runes clearly simplify code

Do not rewrite the entire app in one massive conceptual leap.

## Common Syntax Migrations

| Svelte 4 | Svelte 5 |
|---------|----------|
| `export let foo` | `let { foo } = $props()` |
| `$: doubled = count * 2` | `let doubled = $derived(count * 2)` |
| `$: doThing()` | `$effect(() => { doThing() })` |
| `<slot />` | snippet / `{@render ...}` |
| dispatcher-heavy child events | callback props |

## Migration Risk Areas

| Risk | Why |
|-----|-----|
| Large component libraries | many prop/event surfaces |
| Slot-heavy components | snippet migration can be conceptual work |
| Global stores woven through app | harder to decide what to convert |
| Tests written around implementation details | break during syntax shifts |

Tackle high-churn components with extra review and tests.

## Stores During Migration

You do not need to eliminate all stores.

| Situation | Recommendation |
|----------|----------------|
| Stable app-wide auth/theme store | keep it |
| Local component state in old store wrappers | migrate to runes |
| Utility modules consumed outside Svelte | keep explicit store or plain TS API |

Migration success is measured by clarity and maintainability, not by a store count of zero.

## Testing During Migration

### Protect these flows

| Flow | Why |
|-----|-----|
| navigation between layouts | routing regressions |
| form actions | request/response correctness |
| shared state transitions | migration drift |
| components with complex slots/snippets | render API changes |

Run Playwright and component tests after each migration slice, not only at the very end.

## Deployment Anti-patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| Keeping `adapter-auto` forever | hidden runtime assumptions | pick explicit adapter |
| Marking everything `prerender = true` | dynamic pages break | choose per route |
| Importing server-only code into universal/client code | build/runtime failures | separate boundaries |
| Rewriting all stores immediately during migration | risk and churn | migrate incrementally |
| Ignoring environment module distinctions | leaked secrets or brittle config | use correct `$env/*` module |

## Deployment Checklists by Target

### Node checklist

| Check | Why |
|------|-----|
| Adapter set to `adapter-node` | explicit runtime |
| Reverse proxy configured | TLS, compression, routing |
| Process manager or container restart policy | resilience |
| Health endpoint monitored | rollout safety |

### Vercel checklist

| Check | Why |
|------|-----|
| Adapter matches runtime expectations | serverless/edge correctness |
| Environment variables set in project settings | deployment reproducibility |
| Preview environment reviewed | catch runtime differences early |
| ISR/prerender assumptions validated | avoid stale content surprises |

### Cloudflare checklist

| Check | Why |
|------|-----|
| Dependencies are edge-compatible | avoid Node runtime breakage |
| Durable storage/backends chosen consciously | Workers are stateless |
| Adapter and bindings configured in Wrangler | deployment correctness |
| Request/response APIs remain platform-native | best runtime fit |

### Static checklist

| Check | Why |
|------|-----|
| All dynamic pages excluded from prerender | avoid broken builds |
| Asset paths validated | hosting correctness |
| 404 and fallback behavior defined | static host behavior varies |
| No server-only imports leak into prerendered routes | build stability |

## Migration Review Questions

Before shipping a migrated Svelte 5 codebase, ask:

1. Did we migrate syntax only, or did we also accidentally change behavior?
2. Are callback props clearer than the dispatcher patterns they replaced?
3. Did any load/data boundaries shift between server and client unexpectedly?
4. Are tests covering the routes and components with the heaviest syntax change?
5. Did we preserve accessibility and keyboard behavior while rewriting snippets and composition?

## Release Readiness Checklist

- [ ] Adapter choice matches the actual hosting runtime
- [ ] Route rendering modes are intentional per page
- [ ] Private env vars remain server-only
- [ ] Static pages are prerendered where it provides real benefit
- [ ] Migration from Svelte 4 to 5 is staged and test-backed
- [ ] Existing stores were migrated only where runes genuinely improve clarity
- [ ] Deployment configuration is documented and reproducible for the chosen target
