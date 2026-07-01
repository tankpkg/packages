# Version Migration — Caching Defaults Across Next.js 14, 15, and 16

Sources: Next.js official documentation, Next.js 15 release blog, Next.js 16 release notes, Vercel engineering blog, Next.js upgrade guide

Covers: caching default differences between Next.js 14, 15, and 16, breaking changes, migration strategies, staleTimes configuration, async request APIs, and compatibility paths.

## Caching Default Comparison

### fetch() Behavior

| Behavior | Next.js 14 | Next.js 15 | Next.js 16 |
|----------|-----------|-----------|-----------|
| `fetch(url)` (no options) | Cached (`force-cache`) | **Not cached** (`no-store`) | Not cached (same as 15) |
| `fetch(url, { cache: 'force-cache' })` | Cached | Cached | Cached |
| `fetch(url, { cache: 'no-store' })` | Not cached | Not cached | Not cached |
| `fetch(url, { next: { revalidate: N } })` | Cached, revalidated | Cached, revalidated | Cached, revalidated |

**The breaking change**: In Next.js 14, fetch was cached by default. In Next.js 15+, fetch is NOT cached by default. Code that relied on implicit caching breaks silently — pages become dynamic and slower without any code change.

### GET Route Handlers

| Behavior | Next.js 14 | Next.js 15+ |
|----------|-----------|------------|
| `GET` handler (no dynamic APIs) | Cached by default | **Not cached** by default |
| Opt into caching | Default behavior | `export const dynamic = 'force-static'` |

### Router Cache (Client-Side)

| Behavior | Next.js 14 | Next.js 15+ |
|----------|-----------|------------|
| Dynamic page staleTime | 30 seconds | **0 seconds** |
| Static page staleTime | 5 minutes | 5 minutes (unchanged) |
| `loading.js` staleTime | 5 minutes | 5 minutes (unchanged) |
| Shared layout data | Cached (partial rendering) | Cached (unchanged) |
| Back/forward navigation | From cache | From cache (unchanged) |

### Request APIs

| API | Next.js 14 | Next.js 15+ |
|-----|-----------|------------|
| `cookies()` | Synchronous | **Async** (`await cookies()`) |
| `headers()` | Synchronous | **Async** (`await headers()`) |
| `params` | Synchronous | **Async** (`await params`) |
| `searchParams` | Synchronous | **Async** (`await searchParams`) |
| `draftMode()` | Synchronous | **Async** (`await draftMode()`) |

### Caching Model

| Model | Next.js 14-15 | Next.js 16+ |
|-------|-------------|------------|
| Primary caching API | `fetch` options + `unstable_cache` | `use cache` directive (Cache Components) |
| Non-fetch caching | `unstable_cache(fn, keys, opts)` | `'use cache'` + `cacheLife` + `cacheTag` |
| Cache key generation | Manual (key array) | Automatic (args + closure) |
| Tag invalidation | `revalidateTag` | `updateTag` (new) + `revalidateTag` (still works) |
| Activation | Always available | Requires `cacheComponents: true` |

## Migration: Next.js 14 to 15

### Step 1: Run the Upgrade CLI

```bash
npx @next/codemod@canary upgrade latest
```

This handles the async request API migration automatically.

### Step 2: Fix Implicit Caching

Find all `fetch` calls that relied on implicit caching (no `cache` option) and add explicit caching:

```typescript
// Before (Next.js 14 — implicitly cached)
const data = await fetch('https://api.example.com/products')

// After (Next.js 15 — explicit caching)
const data = await fetch('https://api.example.com/products', {
  cache: 'force-cache'
})

// Or, better — with revalidation
const data = await fetch('https://api.example.com/products', {
  next: { revalidate: 300, tags: ['products'] }
})
```

### Step 3: Audit Route Handlers

GET Route Handlers that were previously cached now run dynamically. Add static config if caching is desired:

```typescript
// app/api/products/route.ts
export const dynamic = 'force-static'
export const revalidate = 3600

export async function GET() {
  const products = await db.product.findMany()
  return Response.json(products)
}
```

### Step 4: Restore Router Cache Behavior (Optional)

If the app relied on client-side caching of dynamic pages:

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  experimental: {
    staleTimes: {
      dynamic: 30,  // Restore 30-second client cache for dynamic pages
      static: 300,  // Keep 5-minute cache for static pages
    },
  },
}
```

### Step 5: Handle Async Request APIs

The codemod handles most cases. Manual fixes needed for:

```typescript
// Before (Next.js 14)
import { cookies } from 'next/headers'

export default function Page() {
  const token = cookies().get('token')?.value
  return <div>{token}</div>
}

// After (Next.js 15)
import { cookies } from 'next/headers'

export default async function Page() {
  const cookieStore = await cookies()
  const token = cookieStore.get('token')?.value
  return <div>{token}</div>
}
```

## Migration: Next.js 15 to 16 (Cache Components)

### Step 1: Enable Cache Components

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  cacheComponents: true,
}
```

### Step 2: Replace unstable_cache with use cache

```typescript
// Before (unstable_cache)
import { unstable_cache } from 'next/cache'

export const getProducts = unstable_cache(
  async () => db.product.findMany(),
  ['products'],
  { revalidate: 300, tags: ['products'] }
)

// After (use cache)
import { cacheLife, cacheTag } from 'next/cache'

export async function getProducts() {
  'use cache'
  cacheLife('minutes')
  cacheTag('products')
  return db.product.findMany()
}
```

### Step 3: Migrate fetch Caching to use cache (Optional)

The fetch cache model still works, but `use cache` provides a unified approach:

```typescript
// Before (fetch with next options)
async function getProducts() {
  return fetch('https://api.example.com/products', {
    next: { revalidate: 300, tags: ['products'] }
  }).then(r => r.json())
}

// After (use cache wrapping fetch)
async function getProducts() {
  'use cache'
  cacheLife('minutes')
  cacheTag('products')
  return fetch('https://api.example.com/products').then(r => r.json())
}
```

### Step 4: Handle Request-Time API Migration

Move `cookies()`/`headers()` reads outside `use cache` boundaries:

```typescript
// Before: unstable_cache that reads cookies inside
export const getUserData = unstable_cache(
  async () => {
    const token = (await cookies()).get('token')?.value
    return fetchWithToken(token)
  },
  ['user'],
  { tags: ['user'] }
)

// After: read cookies outside, pass as argument
export default async function Page() {
  const token = (await cookies()).get('token')?.value
  const data = await getUserData(token)
  return <div>{data}</div>
}

async function getUserData(token: string) {
  'use cache'
  cacheTag('user')
  return fetchWithToken(token)
}
```

## Compatibility Matrix

| Feature | Next.js 14 | Next.js 15 | Next.js 16 |
|---------|-----------|-----------|-----------|
| `fetch` cache options | Yes | Yes | Yes |
| `unstable_cache` | Yes | Yes | Yes (deprecated) |
| `use cache` directive | No | Experimental | Stable |
| `cacheLife` / `cacheTag` | No | Experimental | Stable |
| `updateTag` | No | No | Yes |
| `revalidateTag` | Yes | Yes | Yes |
| `revalidatePath` | Yes | Yes | Yes |
| Route segment `revalidate` | Yes | Yes | Yes |
| Route segment `dynamic` | Yes | Yes | Yes |
| `staleTimes` config | No | Yes (experimental) | Yes |
| PPR | No | Experimental | Experimental |
| Async request APIs | No | Yes (required) | Yes (required) |

## Common Migration Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| No explicit `cache` on fetch after upgrading to 15 | Pages unexpectedly dynamic, slow | Add `force-cache` or `next.revalidate` |
| Using sync `cookies()` in Next.js 15 | Runtime error or deprecation warning | Add `await` |
| `unstable_cache` key mismatch after code move | Cache misses, stale data | With `use cache`, keys are automatic |
| Enabling `cacheComponents` without migrating | `unstable_cache` and `use cache` coexist but differ in behavior | Migrate incrementally, test each function |
| Assuming fetch is cached in Next.js 15 test env | Tests pass (dev mode), production serves uncached | Test with `next build && next start` |
| Calling `revalidateTag` during render in Next.js 15+ | Throws error (was warning in 14) | Move to Server Action or Route Handler |

## Version Detection in Code

```typescript
// Detect Next.js version at build time for conditional logic
const nextVersion = parseInt(process.env.__NEXT_VERSION?.split('.')[0] ?? '0')

// Runtime check (less reliable)
if (typeof globalThis.__next_require__ !== 'undefined') {
  // Running in Next.js
}
```

For the new caching model details, see `references/use-cache-directive.md`.
For fetch-specific options, see `references/fetch-cache-options.md`.
