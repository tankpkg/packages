# Fetch Cache Options and Route Segment Config

Sources: Next.js official documentation (v14-16), Next.js GitHub codebase, Vercel engineering blog

Covers: fetch() cache and next options, route segment configuration exports (dynamic, revalidate, fetchCache, runtime), unstable_cache for non-fetch data, and React.cache for render-scoped deduplication.

## fetch() Extended Options

Next.js extends the native `fetch` API with caching controls. These options determine how fetch results interact with the Data Cache.

### cache Option

```typescript
// Force caching (opt-in required in Next.js 15+)
const data = await fetch(url, { cache: 'force-cache' })

// Skip cache entirely
const data = await fetch(url, { cache: 'no-store' })

// Default behavior (version-dependent)
const data = await fetch(url)
```

| Value | Behavior |
|-------|----------|
| `'force-cache'` | Cache the response in the Data Cache. Serve from cache until revalidated. |
| `'no-store'` | Skip the Data Cache. Fetch fresh on every request. Makes the route dynamic. |
| (not set) | **Next.js 14**: defaults to `'force-cache'` (cached). **Next.js 15+**: defaults to `'no-store'` (uncached). |

### next.revalidate

Set a time-based revalidation interval in seconds:

```typescript
const data = await fetch(url, {
  next: { revalidate: 3600 } // Revalidate every hour
})
```

| Value | Behavior |
|-------|----------|
| `0` | Fetch fresh on every request (equivalent to `no-store`) |
| `number` | Revalidate after N seconds using stale-while-revalidate |
| `false` | Cache indefinitely (until manual invalidation) |

### next.tags

Tag a fetch result for on-demand invalidation:

```typescript
const data = await fetch(url, {
  next: { tags: ['products', 'catalog'] }
})
```

Tags can be invalidated with `revalidateTag('products')`. Multiple tags per fetch enable multi-dimensional invalidation.

### Combining Options

```typescript
// Cache with time-based revalidation AND tags for on-demand
const products = await fetch('https://api.example.com/products', {
  cache: 'force-cache',
  next: {
    revalidate: 3600,
    tags: ['products']
  }
})
```

When both `revalidate` and tags are set, whichever fires first triggers revalidation — time expiry or `revalidateTag()`.

### fetch + cache: 'force-cache' vs next.revalidate

| Config | Data Cache | Full Route Cache |
|--------|-----------|-----------------|
| `cache: 'force-cache'` only | Cached indefinitely | Static |
| `next: { revalidate: N }` | Revalidated every N seconds | ISR |
| `cache: 'force-cache'` + `revalidate: N` | Revalidated every N seconds | ISR |
| `cache: 'no-store'` | Bypassed | Dynamic |
| Neither (Next.js 15+) | Not cached | Dynamic |

## Route Segment Config

Export configuration constants from `page.tsx`, `layout.tsx`, or `route.ts` to control caching behavior at the route level.

### dynamic

Controls whether the route is static or dynamic:

```typescript
export const dynamic = 'auto'
// 'auto' | 'force-dynamic' | 'error' | 'force-static'
```

| Value | Behavior |
|-------|----------|
| `'auto'` | Default. Next.js decides based on dynamic API usage. |
| `'force-dynamic'` | Always render dynamically. Sets all fetches to `no-store`. |
| `'error'` | Force static. Error if dynamic APIs are used. |
| `'force-static'` | Force static. `cookies()`, `headers()` return empty values. |

**Cascading warning**: Setting `force-dynamic` on a layout makes ALL child routes dynamic. Place it on specific pages, not shared layouts.

### revalidate

Set the default revalidation interval for the entire route:

```typescript
export const revalidate = 300 // 5 minutes
// false | 0 | number
```

| Value | Behavior |
|-------|----------|
| `false` | Default. Cache indefinitely (static). |
| `0` | Always dynamic. Fetches default to `no-store`. |
| `number` | ISR with N-second interval. |

The lowest `revalidate` value across nested layouts and pages determines the route's revalidation frequency.

### fetchCache

Advanced option to override fetch caching behavior across a route:

```typescript
export const fetchCache = 'auto'
// 'auto' | 'default-cache' | 'only-cache' | 'force-cache'
// 'default-no-store' | 'only-no-store' | 'force-no-store'
```

| Value | Effect |
|-------|--------|
| `'auto'` | Default. Fetches before dynamic APIs are cached; after are not. |
| `'default-cache'` | Fetches without explicit cache option default to `force-cache`. |
| `'force-cache'` | All fetches forced to `force-cache`, overriding individual options. |
| `'default-no-store'` | Fetches without explicit option default to `no-store`. |
| `'force-no-store'` | All fetches forced to `no-store`, overriding individual options. |
| `'only-cache'` | Default to `force-cache`; error if any fetch uses `no-store`. |
| `'only-no-store'` | Default to `no-store`; error if any fetch uses `force-cache`. |

**Cross-route compatibility**: Parent and child segment `fetchCache` values must be compatible. `force-*` wins over `only-*`. Mixing `only-cache` and `only-no-store` in the same route is an error.

### runtime

```typescript
export const runtime = 'nodejs' // 'nodejs' | 'edge'
```

Note: `revalidate` is not available with `runtime = 'edge'`.

## unstable_cache (Pre-Cache Components)

For non-fetch async functions (database queries, computations), `unstable_cache` provides Data Cache integration:

```typescript
import { unstable_cache } from 'next/cache'

export const getUser = unstable_cache(
  async (id: string) => {
    return db.user.findUnique({ where: { id } })
  },
  ['user'],                              // Cache key prefix
  { revalidate: 3600, tags: ['users'] }  // Options
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `fn` | `(...args) => Promise<T>` | The async function to cache |
| `keyParts` | `string[]` | Array of strings forming the cache key (combined with fn arguments) |
| `options.revalidate` | `number` | Seconds before revalidation |
| `options.tags` | `string[]` | Tags for on-demand invalidation |

### Important Behaviors

- Cache key = `keyParts` joined + serialized arguments
- Tags work with `revalidateTag()` identically to fetch tags
- Does NOT benefit from Request Memoization (no automatic dedup)
- Available since Next.js 14, still works in 15+
- Replaced by `use cache` in Next.js 16+ (Cache Components)

## React.cache (Render Deduplication)

`React.cache` provides per-render deduplication for any function, not just fetch. It does NOT persist data across requests.

```typescript
import { cache } from 'react'

export const getUser = cache(async (id: string) => {
  return db.user.findUnique({ where: { id } })
})
```

### When to Use React.cache

| Scenario | Use |
|----------|-----|
| Same DB query called in multiple components during one render | `React.cache` |
| DB query result needed across multiple requests | `unstable_cache` or `use cache` |
| fetch() called multiple times with same URL | Automatic (fetch is memoized) |
| Need both dedup AND cross-request caching | `React.cache` wrapping `unstable_cache` |

### Combining Dedup + Caching

```typescript
import { cache } from 'react'
import { unstable_cache } from 'next/cache'

// Layer 1: unstable_cache for cross-request persistence
const getCachedUser = unstable_cache(
  async (id: string) => db.user.findUnique({ where: { id } }),
  ['user'],
  { revalidate: 300, tags: ['users'] }
)

// Layer 2: React.cache for per-render deduplication
export const getUser = cache(getCachedUser)
```

## Configuration Interaction Matrix

| fetch option | Route segment | Resulting behavior |
|-------------|---------------|--------------------|
| `cache: 'force-cache'` | `dynamic: 'auto'` | Cached, static route |
| `cache: 'no-store'` | `dynamic: 'auto'` | Uncached, dynamic route |
| (none, Next.js 15+) | `dynamic: 'auto'` | Uncached, dynamic route |
| `cache: 'force-cache'` | `dynamic: 'force-dynamic'` | Overridden to `no-store` |
| `next: { revalidate: 60 }` | `revalidate: 300` | Fetch revalidates at 60s, route at 60s (lowest wins) |
| `cache: 'no-store'` | `revalidate: 300` | Fetch uncached, route becomes dynamic |

## Preloading Data

For expensive data fetches that block rendering, combine `React.cache` with a preload pattern to start fetching early:

```typescript
// lib/data.ts
import { cache } from 'react'
import 'server-only'

export const getProduct = cache(async (id: string) => {
  return db.product.findUnique({ where: { id } })
})

export const preloadProduct = (id: string) => {
  void getProduct(id)
}
```

```typescript
// app/product/[id]/page.tsx
import { getProduct, preloadProduct } from '@/lib/data'

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  preloadProduct(id)               // Start loading immediately
  const isAvailable = await checkAvailability(id)  // Parallel work
  const product = await getProduct(id)              // Already resolved
  return <ProductView product={product} available={isAvailable} />
}
```

This pattern fires the data fetch before any blocking work. By the time `getProduct(id)` is awaited, the data is already available.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Relying on fetch being cached by default | Broke in Next.js 15 upgrade | Explicit `force-cache` or `next.revalidate` |
| `force-dynamic` on a layout | Makes all child routes dynamic | Move to specific pages that need it |
| `fetchCache: 'force-no-store'` on root layout | Entire app uncached | Use only on specific routes |
| Mixing `only-cache` and `only-no-store` in same route | Build error | Choose one strategy per route |
| Using `revalidate = 60 * 10` | Not statically analyzable, fails | Use `revalidate = 600` |
| Forgetting `unstable_cache` for DB queries | DB calls not cached | Wrap with `unstable_cache` or migrate to `use cache` |
| Preloading without `React.cache` | Multiple callers fetch independently | Wrap in `React.cache` for dedup |

For cache layer fundamentals, see `references/four-cache-layers.md`.
For version-specific defaults, see `references/version-migration.md`.
