# The Four Cache Layers

Sources: Next.js official documentation (v14-16), Vercel engineering blog, Lee Robinson (Next.js caching deep dives)

Covers: Request Memoization, Data Cache, Full Route Cache, and Router Cache — mechanics, duration, interaction between layers, and opt-out mechanisms.

## Mental Model

Next.js caching operates as a four-layer stack. Each layer serves a different purpose and has independent lifecycle. Understanding which layer is responsible for stale content is the prerequisite for fixing it.

```
Request enters
    |
    v
[1. Router Cache]       ← Client-side, in-memory during session
    |
    v
[2. Full Route Cache]   ← Server-side, pre-rendered HTML + RSC payload
    |
    v
[3. Data Cache]         ← Server-side, persistent fetch/query results
    |
    v
[4. Request Memoization] ← Per-render, deduplicates identical fetches
    |
    v
Origin (API, DB, CMS)
```

A request may be served from any layer without reaching the layers below it. Fixing stale data requires identifying which layer holds the stale entry.

## Layer 1: Request Memoization

### What It Does

Deduplicates identical `fetch` calls within a single React server render. When multiple components call the same fetch URL with the same options, the actual HTTP request fires once and all callers share the result.

### Duration

One render cycle only. Destroyed when the response finishes streaming.

### How It Works

React extends the `fetch` API to automatically memoize requests during the render tree traversal. The memoization key is the URL + fetch options combination.

```typescript
// app/dashboard/page.tsx
// Both calls to getUser produce ONE actual fetch request
async function UserName() {
  const user = await getUser() // fetch fires here
  return <h1>{user.name}</h1>
}

async function UserEmail() {
  const user = await getUser() // returns memoized result
  return <p>{user.email}</p>
}

async function getUser() {
  return fetch('https://api.example.com/user/1').then(r => r.json())
}
```

### Key Properties

| Property | Value |
|----------|-------|
| Scope | Single render pass |
| Storage | In-memory (React internals) |
| Applies to | `fetch` calls in Server Components |
| Does NOT apply to | Route Handlers, non-fetch data access |
| Opt out | Not typically needed; use `AbortController` for different semantics |

### Deduplication for Non-fetch

For database queries or other non-fetch data access, use `React.cache` for render-scoped dedup:

```typescript
import { cache } from 'react'

export const getUser = cache(async (id: string) => {
  return db.user.findUnique({ where: { id } })
})
```

`React.cache` provides deduplication only — it does not persist across requests. For cross-request caching, use `use cache` or `unstable_cache`.

## Layer 2: Data Cache

### What It Does

Persists the results of `fetch` requests (and `unstable_cache`/`use cache` functions) across multiple incoming requests and deployments. This is the server-side cache that survives beyond a single render.

### Duration

Persistent until revalidated or the cache entry expires. Survives across deployments unless explicitly invalidated.

### Storage

On Vercel: distributed edge cache. Self-hosted: filesystem-based cache in `.next/cache/fetch-cache/` by default, configurable via custom cache handlers.

### Caching Fetch Results

```typescript
// Cached with time-based revalidation
const data = await fetch('https://api.example.com/products', {
  next: { revalidate: 3600, tags: ['products'] }
})

// Explicitly opted into caching (required in Next.js 15+)
const data = await fetch('https://api.example.com/products', {
  cache: 'force-cache'
})

// Bypasses Data Cache entirely
const data = await fetch('https://api.example.com/user', {
  cache: 'no-store'
})
```

### Revalidation Mechanisms

| Mechanism | API | Scope |
|-----------|-----|-------|
| Time-based | `next: { revalidate: seconds }` | Per fetch call |
| Tag-based (on-demand) | `revalidateTag('tag')` | All entries with that tag |
| Path-based (on-demand) | `revalidatePath('/path')` | All data for that route |

### Stale-While-Revalidate Behavior

When a revalidation period expires, the next request still receives the stale cached response immediately. The revalidation happens in the background. The subsequent request receives the fresh data.

```
Timeline:
t=0    Data cached (revalidate: 60)
t=30   Request → cached response (fresh)
t=61   Request → cached response (stale), background revalidation starts
t=62   Revalidation completes, cache updated
t=63   Request → fresh cached response
```

## Layer 3: Full Route Cache

### What It Does

Caches the rendered HTML and React Server Component (RSC) payload for routes that qualify as static. Generated at build time (`next build`) and reused across requests.

### Duration

Persistent until revalidated via `revalidatePath`, segment-level `revalidate`, or a new build.

### Static vs Dynamic

A route is static if it does not use any dynamic APIs during rendering:

| Dynamic API | Triggers Dynamic Rendering |
|-------------|---------------------------|
| `cookies()` | Yes |
| `headers()` | Yes |
| `searchParams` | Yes |
| `fetch` with `cache: 'no-store'` | Yes |
| `connection()` | Yes |
| `draftMode()` | Yes |

If none of these are called during rendering, the route is statically rendered at build time and the Full Route Cache stores both the HTML and the RSC payload.

### ISR (Incremental Static Regeneration)

ISR is the combination of Full Route Cache + time-based revalidation:

```typescript
// app/blog/page.tsx
export const revalidate = 300 // revalidate every 5 minutes

export default async function BlogPage() {
  const posts = await fetch('https://api.example.com/posts', {
    next: { revalidate: 300 }
  }).then(r => r.json())
  return <PostList posts={posts} />
}
```

The page is statically generated at build time. After 300 seconds, the next visitor triggers a background regeneration. Stale content is served until regeneration completes.

### On-Demand ISR

Trigger regeneration immediately after a mutation instead of waiting for a timer:

```typescript
// app/actions.ts
'use server'
import { revalidatePath, revalidateTag } from 'next/cache'

export async function publishPost(id: string) {
  await db.post.publish(id)
  revalidateTag('posts')       // Invalidates Data Cache entries tagged 'posts'
  revalidatePath('/blog')       // Invalidates Full Route Cache for /blog
}
```

## Layer 4: Router Cache

### What It Does

Caches RSC payloads on the client during a browser session. Enables instant back/forward navigation and preserves client state during navigations.

### Duration (Next.js 15+)

| Content Type | Default staleTime | Notes |
|-------------|------------------|-------|
| Dynamic pages | 0 seconds | Always refetched on navigation |
| Static pages (loading.js) | 5 minutes | Prefetched shell cached |
| Shared layouts | Session duration | Preserved for partial rendering |
| Back/forward | Session duration | Restored from cache (scroll position preserved) |

### Clearing the Router Cache

```typescript
'use client'
import { useRouter } from 'next/navigation'

function MutationButton() {
  const router = useRouter()

  async function handleMutation() {
    await updateData()
    router.refresh() // Clears Router Cache, refetches current route
  }

  return <button onClick={handleMutation}>Update</button>
}
```

### Important Behavior

- `router.refresh()` does NOT cause a full page reload — it refetches the RSC payload for the current route while preserving client state
- `router.push()` to the same URL does not clear the Router Cache — use `router.refresh()` instead
- Hard navigation (browser refresh, clicking `<a>` instead of `<Link>`) bypasses Router Cache entirely

## Layer Interaction

### Cache Miss Cascade

When data is not found in a higher layer, the request falls through to the next:

```
Client navigation
  → Router Cache: MISS (staleTime expired)
    → Full Route Cache: MISS (dynamic route)
      → Data Cache: HIT (revalidate not expired)
        → Return cached data, render on server, update Router Cache
```

### Invalidation Propagation

| Action | Data Cache | Full Route Cache | Router Cache |
|--------|-----------|-----------------|-------------|
| `revalidateTag('x')` | Invalidates tagged entries | Invalidates routes using tagged data | Not affected (client) |
| `revalidatePath('/x')` | Invalidates data for path | Invalidates route | Not affected (client) |
| `router.refresh()` | Not affected | Not affected | Clears current route |
| Deploy (new build) | Preserved (unless tag/path) | Regenerated | Cleared (new session) |

### Common Mistake: Forgetting the Client Layer

After a Server Action that calls `revalidateTag`, the server-side caches are updated. But the client Router Cache may still hold stale data. Always pair server revalidation with `router.refresh()` in the calling client component, or use the automatic revalidation that Server Actions provide when called from `<form action={...}>`.

For related invalidation strategies, see `references/revalidation-strategies.md`.
For fetch-level cache configuration, see `references/fetch-cache-options.md`.
