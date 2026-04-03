# Revalidation Strategies

Sources: Next.js official documentation (v14-16), Vercel engineering blog, Next.js GitHub discussions, production ISR patterns

Covers: time-based revalidation, on-demand invalidation with revalidateTag and revalidatePath, ISR patterns (time-based and on-demand), webhook-triggered invalidation, and revalidation in Server Actions.

## Two Approaches to Revalidation

| Approach | Mechanism | When Data Updates |
|----------|-----------|-------------------|
| Time-based | `next: { revalidate: N }` | After N seconds, on next request |
| On-demand | `revalidateTag()` / `revalidatePath()` | Immediately after mutation |

Most production apps use both: time-based as a safety net (data refreshes even if invalidation fails) and on-demand for immediate freshness after writes.

## Time-Based Revalidation

### Per-Fetch Revalidation

Set a revalidation interval on individual fetch calls:

```typescript
// Revalidate this specific data every 60 seconds
const products = await fetch('https://api.example.com/products', {
  next: { revalidate: 60 }
})
```

### Route Segment Revalidation

Set a default revalidation interval for all data in a route:

```typescript
// app/blog/page.tsx
export const revalidate = 300 // 5 minutes

// All fetch calls in this route default to 300s revalidation
// Individual fetches can override with a LOWER value, not higher
export default async function BlogPage() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json())
  return <PostList posts={posts} />
}
```

### Revalidation Interval Rules

| Rule | Behavior |
|------|----------|
| Lowest wins across route | If layout has `revalidate: 300` and page has `revalidate: 60`, the route revalidates every 60s |
| Per-fetch can go lower | A fetch with `revalidate: 30` in a route with `revalidate: 300` revalidates that data at 30s |
| Per-fetch cannot go higher | A fetch cannot set a longer interval than the route segment default |
| `revalidate: 0` | Equivalent to dynamic rendering — data never cached |
| `revalidate: false` | Cache indefinitely (default for static routes) |
| Must be statically analyzable | `revalidate = 60 * 10` fails — use `revalidate = 600` |

### Stale-While-Revalidate Flow

```
1. Request arrives, cached data exists, revalidation timer expired
2. Serve STALE cached data immediately (user sees instant response)
3. Trigger background revalidation (fetch fresh data)
4. Store fresh data in cache
5. Next request gets fresh data
```

The first visitor after expiry gets stale data. The second visitor gets fresh data. This trade-off favors speed over absolute freshness.

### Choosing Revalidation Intervals

| Data Type | Suggested Interval | Reasoning |
|-----------|--------------------|-----------|
| Marketing pages | 3600 (1 hour) | Rarely changes, high traffic |
| Blog posts | 300-900 (5-15 min) | Updated occasionally |
| Product catalog | 60-300 (1-5 min) | Changes during business hours |
| Pricing | 60-120 (1-2 min) | Sensitive to staleness |
| Dashboards | 10-30 seconds | Near-real-time needed |
| User-specific data | 0 or no-store | Cannot be shared across users |

## On-Demand Revalidation

### revalidateTag

Invalidates all cache entries (Data Cache + Full Route Cache) associated with a specific tag. Tags follow data, not routes — one tag can invalidate content across multiple pages.

```typescript
// Step 1: Tag data when fetching
async function getProducts() {
  return fetch('https://api.example.com/products', {
    next: { tags: ['products'] }
  }).then(r => r.json())
}

// Step 2: Invalidate by tag after mutation
'use server'
import { revalidateTag } from 'next/cache'

export async function addProduct(formData: FormData) {
  await db.product.create({ data: parseFormData(formData) })
  revalidateTag('products')
}
```

#### Multiple Tags

A single fetch can have multiple tags. Invalidating any one of them revalidates the entry:

```typescript
const product = await fetch(`https://api.example.com/products/${id}`, {
  next: { tags: ['products', `product-${id}`, 'catalog'] }
})

// Any of these invalidates the cached product:
revalidateTag('products')       // All products
revalidateTag(`product-${id}`)  // This specific product
revalidateTag('catalog')        // Everything in catalog
```

### revalidatePath

Invalidates the Full Route Cache for a specific URL path. Also clears associated Data Cache entries for that route.

```typescript
'use server'
import { revalidatePath } from 'next/cache'

export async function updateProfile(formData: FormData) {
  await db.user.update({ data: parseFormData(formData) })
  revalidatePath('/profile')
}
```

#### Path Variants

```typescript
// Revalidate a specific page
revalidatePath('/blog')

// Revalidate a dynamic route
revalidatePath('/blog/my-post')

// Revalidate all pages matching a route pattern
revalidatePath('/blog/[slug]', 'page')

// Revalidate a layout (and all pages using it)
revalidatePath('/blog', 'layout')

// Revalidate everything
revalidatePath('/')
```

### revalidateTag vs revalidatePath

| Factor | revalidateTag | revalidatePath |
|--------|--------------|----------------|
| Targets | Data across any route | Specific route path |
| Granularity | Data-centric | Route-centric |
| Cross-route | One call, all routes using tag | Must call per path |
| Setup required | Tag fetches with `next.tags` | None (uses URL) |
| Best for | Shared data (products, posts, config) | Single-page refresh |
| Precision | Surgical (only tagged data) | Broad (entire route) |

**Rule of thumb**: Prefer `revalidateTag` for data mutations. Use `revalidatePath` when the route itself needs refreshing regardless of specific data changes (layout change, deploy verification).

## ISR Patterns

### Time-Based ISR

Static generation at build time with automatic background regeneration:

```typescript
// app/blog/[slug]/page.tsx
export const revalidate = 900 // 15 minutes

export async function generateStaticParams() {
  const slugs = await db.post.findMany({ select: { slug: true } })
  return slugs.map(({ slug }) => ({ slug }))
}

export default async function PostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = await fetch(`https://api.example.com/posts/${slug}`, {
    next: { revalidate: 900, tags: [`post-${slug}`] }
  }).then(r => r.json())
  return <Article post={post} />
}
```

### On-Demand ISR

Regenerate pages immediately when content changes, typically via webhook from a CMS:

```typescript
// app/api/revalidate/route.ts
import { revalidateTag } from 'next/cache'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const secret = request.headers.get('x-revalidation-secret')
  if (secret !== process.env.REVALIDATION_SECRET) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const body = await request.json()
  const { tag } = body

  if (!tag || typeof tag !== 'string') {
    return NextResponse.json({ error: 'Missing tag' }, { status: 400 })
  }

  revalidateTag(tag)
  return NextResponse.json({ revalidated: true, tag })
}
```

### Hybrid Pattern: Time-Based + On-Demand

Combine both for maximum reliability:

```typescript
// Fetch with time-based revalidation as safety net
const posts = await fetch('https://api.example.com/posts', {
  next: { revalidate: 3600, tags: ['posts'] } // 1 hour fallback
})

// On-demand revalidation for immediate updates
// Called from Server Actions and webhooks
revalidateTag('posts')
```

The time-based interval catches cases where on-demand invalidation fails (webhook missed, server error). The on-demand path ensures immediate freshness after known mutations.

## Revalidation in Server Actions

Server Actions that call `revalidateTag` or `revalidatePath` automatically trigger cache updates and Router Cache invalidation for the calling client:

```typescript
// app/actions.ts
'use server'
import { revalidateTag } from 'next/cache'

export async function createPost(formData: FormData) {
  await db.post.create({ data: parseFormData(formData) })
  revalidateTag('posts')
  // Router Cache is automatically cleared for routes affected by this tag
  // when the action is called from a <form action={createPost}>
}
```

When called via `startTransition` in a Client Component, pair with `router.refresh()`:

```typescript
'use client'
import { useRouter } from 'next/navigation'
import { createPost } from './actions'

function CreatePostForm() {
  const router = useRouter()

  return (
    <form action={async (formData) => {
      await createPost(formData)
      router.refresh() // Ensure Router Cache updates
    }}>
      {/* ... */}
    </form>
  )
}
```

## Revalidation Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Calling `revalidateTag` during render | Throws error in Next.js 15+ | Move to Server Action or Route Handler |
| Forgetting `router.refresh()` on client | Client shows stale data after mutation | Add refresh after Server Action call |
| Tagging data but never invalidating | Data stays cached forever | Set up revalidation in every mutation path |
| Using `revalidatePath('/')` as catch-all | Invalidates everything, defeats caching purpose | Use specific tags instead |
| Time-based only, no on-demand | Users see stale data after their own writes | Add tag-based invalidation for mutations |
| Revalidation secret in client code | Anyone can trigger revalidation | Keep secret server-side only |

For cache layer details, see `references/four-cache-layers.md`.
For use cache tag integration, see `references/use-cache-directive.md`.
