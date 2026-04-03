# The use cache Directive

Sources: Next.js official documentation (v15-16), Next.js GitHub RFC discussions, Vercel engineering blog (Cache Components)

Covers: Cache Components model (Next.js 16+), use cache syntax at file/component/function level, cache key mechanics, cacheLife profiles, cacheTag and updateTag for invalidation, serialization rules, interleaving patterns, and migration from unstable_cache.

## Overview

The `use cache` directive is the Cache Components model introduced in Next.js 15 (experimental) and stable in Next.js 16. It replaces `unstable_cache` and the fetch-centric caching model with a unified, composable approach to caching any async function, component, or route.

## Enabling Cache Components

```typescript
// next.config.ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  cacheComponents: true,
}

export default nextConfig
```

## Three Scopes

### File-Level

All exports in the file are cached. Every exported function must be async:

```typescript
// app/data.ts
'use cache'

export async function getProducts() {
  return db.product.findMany()
}

export async function getCategories() {
  return db.category.findMany()
}
```

### Component-Level

Cache a specific Server Component's rendered output:

```typescript
export async function ProductCard({ id }: { id: string }) {
  'use cache'
  const product = await db.product.findUnique({ where: { id } })
  return (
    <div>
      <h2>{product.name}</h2>
      <p>{product.price}</p>
    </div>
  )
}
```

### Function-Level

Cache the return value of any async function:

```typescript
export async function getExpensiveData(query: string) {
  'use cache'
  const result = await heavyComputation(query)
  return result
}
```

## Cache Key Mechanics

The cache key is automatically derived from four components:

| Component | Description |
|-----------|-------------|
| Build ID | Changes per build, invalidates all entries |
| Function ID | Secure hash of function location + signature |
| Serializable arguments | Props (components) or function arguments |
| HMR hash | Development only, invalidates on hot reload |

Closure variables from outer scopes are automatically captured as part of the key:

```typescript
async function UserData({ userId }: { userId: string }) {
  const getData = async (filter: string) => {
    'use cache'
    // Cache key includes: userId (closure) + filter (argument)
    return fetch(`/api/users/${userId}/data?filter=${filter}`)
  }
  return getData('active')
}
```

Different combinations of `userId` and `filter` produce separate cache entries.

## cacheLife — Controlling Duration

Use `cacheLife` inside a `use cache` scope to control how long the entry stays valid:

```typescript
import { cacheLife } from 'next/cache'

async function getProducts() {
  'use cache'
  cacheLife('hours')
  return db.product.findMany()
}
```

### Built-in Profiles

| Profile | Stale (client) | Revalidate (server) | Expire |
|---------|---------------|--------------------| -------|
| `default` | 5 minutes | 15 minutes | Never |
| `seconds` | 0 | 1 second | 60 seconds |
| `minutes` | 5 minutes | 1 minute | 1 hour |
| `hours` | 5 minutes | 1 hour | 1 day |
| `days` | 5 minutes | 1 day | 1 week |
| `weeks` | 5 minutes | 1 week | 1 month |
| `max` | 5 minutes | 1 month | Indefinite |

### Custom Profiles

Define custom profiles in `next.config.ts`:

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  cacheComponents: true,
  cacheLife: {
    'product-data': {
      stale: 300,       // 5 min client-side
      revalidate: 900,  // 15 min server-side
      expire: 86400,    // 24 hours absolute max
    },
    'realtime': {
      stale: 0,
      revalidate: 5,
      expire: 60,
    },
  },
}
```

```typescript
async function getProducts() {
  'use cache'
  cacheLife('product-data')
  return db.product.findMany()
}
```

### Profile Semantics

| Property | Meaning |
|----------|---------|
| `stale` | How long the client serves cached content before refetching |
| `revalidate` | How long the server serves cached content before regenerating |
| `expire` | Absolute maximum age before the entry is evicted entirely |

The client enforces a minimum 30-second stale time regardless of configuration. The `x-nextjs-stale-time` header communicates the value from server to client.

## cacheTag and updateTag — On-Demand Invalidation

### Tagging Cached Entries

```typescript
import { cacheTag } from 'next/cache'

async function getProduct(id: string) {
  'use cache'
  cacheTag('products', `product-${id}`)
  return db.product.findUnique({ where: { id } })
}
```

### Invalidating by Tag

```typescript
'use server'
import { updateTag, revalidateTag } from 'next/cache'

export async function editProduct(id: string, data: ProductData) {
  await db.product.update({ where: { id }, data })
  updateTag(`product-${id}`)  // Preferred in Cache Components model
  // revalidateTag('products') also works
}
```

`updateTag` is the Cache Components companion to `revalidateTag`. Both invalidate by tag. `cacheTag` and `cacheLife` integrate across client and server layers — configure once, applied everywhere.

## Serialization Rules

Arguments and return values must be serializable, but they use different serialization systems:

### Supported Argument Types

- Primitives: `string`, `number`, `boolean`, `null`, `undefined`
- Plain objects and arrays
- `Date`, `Map`, `Set`, `TypedArray`, `ArrayBuffer`
- React elements (pass-through only)

### Unsupported Types

- Class instances
- Functions (except pass-through)
- Symbols, `WeakMap`, `WeakSet`
- `URL` instances

```typescript
// Valid: primitives and plain objects
async function UserCard({ id, config }: { id: string; config: { theme: string } }) {
  'use cache'
  return <div>{id}</div>
}

// Invalid: class instance argument
async function UserProfile({ user }: { user: UserClass }) {
  'use cache'
  // Error: Cannot serialize class instance
  return <div>{user.name}</div>
}
```

## Interleaving — Mixing Cached and Dynamic

Pass dynamic content through cached components using composition:

```typescript
export default async function Page() {
  const dynamicData = await getUncachedData()
  return (
    <CachedLayout>
      <DynamicWidget data={dynamicData} />
    </CachedLayout>
  )
}

async function CachedLayout({ children }: { children: React.ReactNode }) {
  'use cache'
  const navItems = await getNavItems() // cached
  return (
    <div>
      <nav>{/* render navItems */}</nav>
      {children} {/* dynamic, passed through */}
    </div>
  )
}
```

The `children` prop is passed through without affecting the cache entry. The cached layout and the dynamic widget are independent — the layout cache is not busted when `dynamicData` changes.

### Server Actions Through Cache

```typescript
async function CachedForm({ action }: { action: () => Promise<void> }) {
  'use cache'
  // Do NOT call action here — just pass through
  return <form action={action}>{/* fields */}</form>
}
```

## Constraints

### Cannot Access Request-Time APIs

`cookies()`, `headers()`, and `searchParams` cannot be called inside a `use cache` scope. Read them outside and pass values as arguments:

```typescript
// Wrong: cookies() inside use cache
async function UserContent() {
  'use cache'
  const token = (await cookies()).get('token') // Error
}

// Correct: pass cookie value as argument
async function UserContent({ token }: { token: string }) {
  'use cache'
  const data = await fetchWithToken(token)
  return <div>{data}</div>
}
```

### React.cache Is Isolated

`React.cache` operates in an isolated scope inside `use cache`. Data stored via `React.cache` outside a cached function is not visible inside it.

## Runtime Behavior

| Environment | Behavior |
|-------------|----------|
| Serverless (Vercel, AWS Lambda) | Cache entries may not persist across requests (each invocation = new instance) |
| Self-hosted (Node.js) | In-memory LRU cache, persists across requests, configurable via `cacheMaxMemorySize` |

For persistent runtime caching in serverless, use `use cache: remote` to connect a Redis or KV store.

## Variants

| Directive | Purpose |
|-----------|---------|
| `'use cache'` | Standard caching, cannot access request APIs |
| `'use cache: private'` | Can access request APIs (compliance edge cases) |
| `'use cache: remote'` | Delegates to platform cache handler (Redis, KV) |

## Migration from unstable_cache

| unstable_cache | use cache |
|----------------|-----------|
| `unstable_cache(fn, keys, { tags, revalidate })` | `'use cache'` + `cacheTag()` + `cacheLife()` |
| Manual cache key array | Automatic from arguments + closure |
| Separate API from fetch caching | Unified model for all async work |
| Available since Next.js 14 | Stable in Next.js 16 |

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

## Debugging

Enable verbose cache logging:

```bash
NEXT_PRIVATE_DEBUG_CACHE=1 npm run dev
NEXT_PRIVATE_DEBUG_CACHE=1 npm run start
```

In development, console logs from cached functions appear with a `Cache` prefix.

For cache layer fundamentals, see `references/four-cache-layers.md`.
For self-hosting cache configuration, see `references/self-hosting-cdn.md`.
