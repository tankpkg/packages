# Routing and Load

Sources: SvelteKit official documentation (routing, layouts, load, page options, server-only modules), Svelte 5 documentation, adapter documentation, community production patterns from 2024-2026

Covers: filesystem routing, layouts, params, route groups, universal vs server load functions, invalidation, streaming, page options, and server-only module boundaries in SvelteKit.

## Filesystem Routing Is the Primary API

SvelteKit routing is file-driven. The directory tree is not just organization — it defines URL structure, layout boundaries, and data-loading scope.

| File | Meaning |
|-----|---------|
| `+page.svelte` | UI for a route |
| `+page.ts` / `+page.js` | Universal load function |
| `+page.server.ts` | Server-only load + actions |
| `+layout.svelte` | Shared UI wrapper |
| `+layout.ts` / `.server.ts` | Shared data for subtree |
| `+server.ts` | Endpoint / request handler |
| `+error.svelte` | Route error boundary |

Treat the tree as the first architecture decision for any SvelteKit app.

## Basic Route Shapes

| Need | Folder structure |
|-----|------------------|
| Static page | `src/routes/about/+page.svelte` |
| Param route | `src/routes/blog/[slug]/+page.svelte` |
| Nested dashboard | `src/routes/app/settings/+page.svelte` |
| JSON endpoint | `src/routes/api/users/+server.ts` |

### Example

```text
src/routes/
  +layout.svelte
  +page.svelte
  blog/
    [slug]/
      +page.ts
      +page.svelte
  api/
    posts/
      +server.ts
```

## Layout Hierarchies

Layouts wrap all child routes below them.

### Typical layout layering

| Level | Responsibility |
|------|----------------|
| Root layout | app shell, theme, auth session, global nav |
| Section layout | dashboard sidebar, docs nav, settings tabs |
| Page | route-specific UI |

### Good layout usage

1. Put persistent shell UI in layouts
2. Load shared data at the highest level that actually needs it
3. Avoid loading everything in the root layout by default

### Bad layout usage

| Anti-pattern | Why it hurts |
|-------------|--------------|
| Fetching every feature’s data in root layout | Over-fetching on every navigation |
| Deeply nested layouts for trivial markup | Hard-to-follow route tree |
| Duplicating shared shell in pages | Loss of reuse and state continuity |

## Layout Groups and Organization

Use route groups to organize folders without affecting the URL.

```text
src/routes/
  (marketing)/
    +layout.svelte
    pricing/+page.svelte
  (app)/
    +layout.svelte
    dashboard/+page.svelte
```

The `(marketing)` and `(app)` folder names do not appear in the URL, but they create separate layout trees.

### Use route groups for

| Use case | Why |
|---------|-----|
| Public vs authenticated shells | Different layout hierarchies |
| Docs vs app UI | Distinct nav and data |
| Large route organization | Keep tree understandable |

## Param Routes and Matchers

### Standard params

| Pattern | Meaning |
|--------|---------|
| `[slug]` | One required segment |
| `[id]` | One required segment |
| `[...rest]` | Rest/wildcard segments |
| `[[optional]]` | Optional segment |

### Matchers

Use param matchers when the parameter format matters.

| Example | Use |
|--------|-----|
| `[id=integer]` | Numeric IDs only |
| `[locale=lang]` | Limited locale segments |

Matchers reduce invalid routes early and make route intent clearer.

## Universal vs Server Load

This is one of the most important SvelteKit distinctions.

| File | Runs where | Use for |
|-----|------------|---------|
| `+page.ts` | Server on first render, browser on navigation | Public fetches, client-safe data |
| `+page.server.ts` | Server only | DB access, secrets, auth-only data |
| `+layout.ts` | Same as page universal | Shared public data |
| `+layout.server.ts` | Server only | Shared secure data |

### Default rule

If data needs secrets, private env vars, DB access, or internal services, use `*.server.ts`.

## Universal Load Pattern

```ts
export async function load({ fetch, params }) {
  const res = await fetch(`/api/posts/${params.slug}`)
  const post = await res.json()
  return { post }
}
```

Use universal load when browser-side navigations should refetch without a full server roundtrip to page code.

## Server Load Pattern

```ts
export async function load({ params, locals }) {
  const post = await locals.db.post.findUnique({ where: { slug: params.slug } })
  if (!post) error(404, 'Not found')
  return { post }
}
```

Use server load for anything private or sensitive.

## Load Return Values

Returned data becomes the page or layout `data` prop.

| Source | Access pattern |
|-------|----------------|
| Page load | `$props().data` in page |
| Parent layout load | inherited into child `data` |
| `await parent()` in child load | access parent load result during loading |

Keep returned objects serializable and focused.

## Parent Data Composition

```ts
export async function load({ parent }) {
  const { session } = await parent()
  return { canEdit: session?.role === 'admin' }
}
```

Use `parent()` to compose shared layout data without duplicating queries.

## Invalidation and Re-running Loads

SvelteKit can re-run loads when navigation or invalidation occurs.

| Mechanism | Use for |
|----------|---------|
| Navigation | Normal route changes |
| `invalidate(url)` | Re-fetch one dependency |
| `invalidateAll()` | Broad refresh after mutation |
| `depends('key')` | Custom dependency tracking |

### Good invalidation practice

1. Use targeted invalidation when possible
2. Avoid `invalidateAll()` unless state has changed broadly
3. Keep load functions deterministic and restart-safe

## Streaming and Progressive Data

SvelteKit supports streaming data for slower async pieces.

| Good fit | Example |
|---------|---------|
| Fast shell + slow secondary data | dashboard summary + analytics charts |
| Non-blocking related data | main article + recommendations |
| Server-rendered UI with deferred segments | product page + reviews |

Use streaming when the user benefits from seeing partial UI sooner.

## `+server.ts` Endpoints

Use `+server.ts` for API-like endpoints, webhooks, or binary responses.

```ts
export async function GET() {
  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'content-type': 'application/json' }
  })
}
```

### Good endpoint use cases

| Use case | Why |
|---------|-----|
| JSON endpoints | simple API inside app |
| Webhooks | explicit request handlers |
| Form/file helpers | browser-friendly server path |
| Non-HTML output | CSV, image, RSS, robots.txt |

## Server-only Modules

Use server-only files for secrets and private runtime logic.

| Pattern | Safe? |
|--------|-------|
| import DB client in `+page.server.ts` | Yes |
| import private env vars in `+page.server.ts` | Yes |
| import DB client in universal `+page.ts` | No |
| import private env in client component | No |

SvelteKit enforces server/client boundaries, but write code as if you must explain those boundaries to a reviewer.

## Page Options

These options control rendering and behavior.

| Option | Meaning |
|-------|---------|
| `prerender = true` | Build static output |
| `ssr = false` | SPA-style route |
| `csr = false` | Disable client-side JS |
| `trailingSlash` | URL slash behavior |

### Common patterns

| Route type | Suggested options |
|-----------|-------------------|
| Marketing page | `prerender = true` |
| Dashboard | default SSR or `ssr = false` if SPA-only |
| Static docs | `prerender = true` |
| Read-only content page | `csr = false` if no interactivity needed |

Do not disable SSR casually. It changes your data-flow model.

## Error Handling in Load

### Expected vs unexpected errors

| Situation | Response |
|----------|----------|
| Missing record | `error(404, 'Not found')` |
| Unauthorized access | `redirect(303, '/login')` or `error(403, ...)` |
| Unexpected DB failure | throw and let `handleError` report |

Keep expected user-facing errors explicit. Let unexpected failures surface to your error pipeline.

## Data-loading Anti-patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| Putting secret fetches in universal load | Leaks capabilities into browser | move to server load |
| Duplicating same query in layout and page | Waste and drift | lift or compose via `parent()` |
| Returning giant data blobs | Slow serialization and hydration | shape smaller payloads |
| Using `load` for mutation | Wrong lifecycle | use form actions or `+server` endpoint |
| Loading everything at root | All navigations get heavier | fetch closer to where data is used |

## Release Readiness Checklist

- [ ] Route tree reflects shell/layout boundaries clearly
- [ ] Server-only data lives in `*.server.ts`
- [ ] Load functions return only necessary serialized data
- [ ] `parent()` is used deliberately, not recursively everywhere
- [ ] Invalidation strategy is explicit after mutations
- [ ] `+server.ts` endpoints are used where response type is not page HTML
- [ ] Page options (`prerender`, `ssr`, `csr`) are chosen intentionally per route
