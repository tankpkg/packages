# Cache Debugging

Sources: Next.js official documentation (v14-16), Vercel engineering blog, Next.js GitHub issues and discussions

Covers: verbose cache logging, response header inspection, static route indicator, build output analysis, production cache verification, and systematic debugging workflow for stale data.

## Verbose Cache Logging

Enable detailed cache logging with the `NEXT_PRIVATE_DEBUG_CACHE` environment variable:

```bash
# Development
NEXT_PRIVATE_DEBUG_CACHE=1 npm run dev

# Production (self-hosted)
NEXT_PRIVATE_DEBUG_CACHE=1 npm run start

# Production (Docker)
ENV NEXT_PRIVATE_DEBUG_CACHE=1
```

### What the Logs Show

| Log Entry | Meaning |
|-----------|---------|
| `cache HIT` | Data served from Data Cache |
| `cache MISS` | Data fetched from origin |
| `cache STALE` | Stale data served, background revalidation triggered |
| `cache REVALIDATED` | Background revalidation completed successfully |
| `cache SET` | New entry written to Data Cache |

### Cache Prefix in Development

When using `use cache` (Cache Components), console logs from cached functions display with a `Cache` prefix in development. Check for this prefix to confirm a function is executing within a cache boundary.

## Response Headers

### Headers to Inspect

| Header | Values | Meaning |
|--------|--------|---------|
| `x-nextjs-cache` | `HIT`, `MISS`, `STALE` | Full Route Cache status |
| `x-nextjs-stale-time` | seconds | Client-side stale duration from use cache |
| `Cache-Control` | `s-maxage=N, stale-while-revalidate=M` | ISR timing |
| `x-vercel-cache` | `HIT`, `MISS`, `STALE`, `PRERENDER` | Vercel CDN cache status |
| `age` | seconds | How old the cached response is |

### Inspecting in Browser

```bash
# Using curl
curl -I https://your-app.com/page

# Key headers to look for
x-nextjs-cache: HIT
cache-control: s-maxage=300, stale-while-revalidate=31536000
age: 45
```

### Inspecting in Code

```typescript
// app/api/debug-cache/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const res = await fetch('https://api.example.com/data', {
    next: { revalidate: 60, tags: ['debug-test'] }
  })

  return NextResponse.json({
    data: await res.json(),
    cacheStatus: res.headers.get('x-nextjs-cache'),
    age: res.headers.get('age'),
    fetchedAt: new Date().toISOString(),
  })
}
```

## Static Route Indicator

Next.js 15+ displays a visual indicator during development showing whether each route is static or dynamic.

### What to Look For

- Static routes show a lightning bolt icon in the bottom-left corner during development
- Dynamic routes show no indicator
- Use this to verify that routes are rendering as expected before deploying

### Disabling the Indicator

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  devIndicators: {
    appIsrStatus: false,
  },
}
```

## Build Output Analysis

Run `next build` and inspect the output for route rendering information:

```
Route (app)                           Size     First Load JS
+ /                                   5.2 kB   98.3 kB
+ /about                              2.1 kB   95.2 kB
+ /blog                               3.4 kB   96.5 kB
+ /blog/[slug]                        4.1 kB   97.2 kB
+ /dashboard                          6.3 kB   99.4 kB

Route Type Legend:
  O  Static     - prerendered as static content
  f  Dynamic    - server-rendered on demand
  λ  Streaming  - server-rendered with streaming
```

| Symbol | Meaning | Caching |
|--------|---------|---------|
| `O` (circle) | Static | Full Route Cache active |
| `f` | Dynamic | Rendered per request |
| `λ` (lambda) | Dynamic with streaming | Rendered per request, streamed |

### Unexpected Dynamic Routes

If a route shows as `f` (dynamic) when expecting static:

1. Search for `cookies()`, `headers()`, `searchParams` usage in the route tree
2. Check for `cache: 'no-store'` in any fetch call
3. Check for `export const dynamic = 'force-dynamic'` in parent layouts
4. Check if a dependency calls dynamic APIs internally

## Production Cache Verification

### Verifying ISR

```bash
# Request 1: Initial fetch (MISS or PRERENDER)
curl -s -o /dev/null -w "%{http_code}" -D - https://your-app.com/blog | grep -i cache

# Wait for revalidation period
sleep 65

# Request 2: Should trigger revalidation (STALE)
curl -s -o /dev/null -w "%{http_code}" -D - https://your-app.com/blog | grep -i cache

# Request 3: Should be fresh (HIT with age: 0)
curl -s -o /dev/null -w "%{http_code}" -D - https://your-app.com/blog | grep -i cache
```

### Verifying On-Demand Revalidation

```bash
# Step 1: Fetch page, note content
curl -s https://your-app.com/products | head -20

# Step 2: Trigger revalidation
curl -X POST https://your-app.com/api/revalidate \
  -H "Content-Type: application/json" \
  -H "x-revalidation-secret: $SECRET" \
  -d '{"tag": "products"}'

# Step 3: Fetch again, verify content updated
curl -s https://your-app.com/products | head -20
```

### Verifying Router Cache

In the browser console:

```javascript
// Check if client-side navigation serves cached content
performance.getEntriesByType('navigation')
  .forEach(e => console.log(e.type, e.transferSize))

// Force Router Cache clear
// Navigate away, then back — should see fresh data
```

## Systematic Debugging Workflow

When a user reports "the page shows old data", follow this sequence:

### Step 1: Identify the Layer

```
Hard refresh (Cmd+Shift+R) fixes it?
├── Yes → Router Cache issue
│   Fix: Add router.refresh() after mutations
└── No → Server-side cache issue
    │
    Check response headers (x-nextjs-cache)
    ├── HIT with old age → Data Cache stale
    │   Fix: Check revalidate intervals, trigger revalidateTag
    ├── MISS → No caching, check origin data
    │   Fix: Verify database/API has correct data
    └── STALE → Revalidation triggered but not complete
        Fix: Wait and retry, or check revalidation logs
```

### Step 2: Verify Revalidation Fires

```bash
# Enable debug logging
NEXT_PRIVATE_DEBUG_CACHE=1 npm run start

# Trigger the mutation
# Watch logs for:
#   "revalidateTag: products" or
#   "revalidatePath: /blog"
```

### Step 3: Check the Invalidation Chain

| Question | Where to Check |
|----------|---------------|
| Does the Server Action call revalidateTag/Path? | Server Action code |
| Does the tag match what the fetch uses? | Compare `next.tags` in fetch with `revalidateTag` argument |
| Is the path correct? | Compare `revalidatePath` argument with actual route |
| Does the client refresh after mutation? | Client component code (router.refresh) |
| Is there a CDN/edge cache in front? | CDN headers, purge rules |

### Step 4: Common Root Causes

| Root Cause | Diagnosis | Fix |
|-----------|-----------|-----|
| Tag mismatch | Fetch uses `tags: ['product']`, action uses `revalidateTag('products')` | Align tag names exactly |
| Missing revalidation call | Mutation updates DB but never invalidates cache | Add revalidateTag/Path to every mutation path |
| CDN caching over Next.js | CDN serves stale, Next.js never sees the request | Configure CDN cache rules, reduce TTL |
| Layout-level force-dynamic | Accidentally set on parent layout | Move to specific pages |
| Development vs production difference | Dev always renders fresh, production uses cache | Test with `next build && next start` locally |
| Race condition in revalidation | Data written but revalidation fetches before write propagates | Add small delay or use transactional writes |

## Debugging Fetch Wrapper

Create a reusable wrapper that logs fetch cache behavior:

```typescript
// lib/fetcher.ts
export async function cachedFetch(url: string, options?: RequestInit & { next?: NextFetchRequestConfig }) {
  const start = Date.now()
  const res = await fetch(url, options)
  const duration = Date.now() - start

  if (process.env.NODE_ENV === 'development') {
    console.log(
      `[fetch] ${url}`,
      `cache: ${options?.cache ?? 'default'}`,
      `revalidate: ${options?.next?.revalidate ?? 'none'}`,
      `tags: ${options?.next?.tags?.join(',') ?? 'none'}`,
      `status: ${res.status}`,
      `${duration}ms`
    )
  }

  return res
}
```

## Development vs Production Caveats

| Behavior | Development | Production |
|----------|-------------|------------|
| Data Cache | Active (fetch results cached) | Active |
| Full Route Cache | Not active (pages always re-render) | Active for static routes |
| Request Memoization | Active | Active |
| Router Cache | Active | Active |
| `loading.tsx` caching | Not cached | Cached for 5 minutes |
| Static route indicator | Visible | Not applicable |

Development mode always re-renders pages to show changes immediately. This means cache bugs often only appear in production. Always test with `next build && next start` before deploying.

## Cache Debugging Review Questions

1. Which cache layer is actually stale right now?
2. Did the mutation path invalidate the same tags or paths that the read path uses?
3. Is the stale result coming from Next.js or from infrastructure in front of it?

## Common Debugging Smells

| Smell | Why it matters |
|------|----------------|
| adding `force-dynamic` before identifying the stale layer | hides root cause |
| testing only in dev | misses production-only cache behavior |
| no tag naming convention | revalidation drift |

For cache layer details, see `references/four-cache-layers.md`.
For self-hosting cache configuration, see `references/self-hosting-cdn.md`.
