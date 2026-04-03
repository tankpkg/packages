# Static vs Dynamic Rendering

Sources: Next.js official documentation (v14-16), Vercel engineering blog (Partial Prerendering), Lee Robinson (rendering deep dives)

Covers: static and dynamic rendering mechanics, automatic detection triggers, Partial Prerendering (PPR), generateStaticParams for dynamic routes, streaming and caching interaction, and rendering decision framework.

## Rendering Modes

Next.js App Router determines rendering mode per-route based on the APIs and data access patterns used during rendering.

### Static Rendering (Default)

Routes are rendered at build time (`next build`). The HTML and RSC payload are cached in the Full Route Cache and served to all users.

**When it happens**: No dynamic APIs are used, and all data fetching is cached.

```typescript
// app/about/page.tsx — static by default
export default async function AboutPage() {
  const content = await fetch('https://api.example.com/about', {
    cache: 'force-cache'
  }).then(r => r.json())
  return <div>{content.body}</div>
}
```

### Dynamic Rendering

Routes are rendered on the server for each incoming request. The response is not cached in the Full Route Cache (Data Cache entries may still be used).

**When it happens**: Any dynamic API is called during rendering.

```typescript
// app/dashboard/page.tsx — dynamic because of cookies()
import { cookies } from 'next/headers'

export default async function Dashboard() {
  const session = (await cookies()).get('session')?.value
  const data = await fetch(`/api/user/${session}`, { cache: 'no-store' })
    .then(r => r.json())
  return <DashboardView data={data} />
}
```

## Dynamic API Triggers

Any of these APIs used during rendering force the route into dynamic mode:

| API | Why It Forces Dynamic |
|-----|----------------------|
| `cookies()` | Request-specific (different per user) |
| `headers()` | Request-specific |
| `searchParams` (in page props) | URL-specific, unknown at build time |
| `connection()` | Signals request-time execution |
| `draftMode()` | Preview/draft content |
| `fetch` with `cache: 'no-store'` | Explicit no-cache |
| `fetch` with `revalidate: 0` | Equivalent to no-store |

### Detection Is Automatic

Next.js does not require explicit configuration. The presence of any dynamic API switches the route to dynamic rendering. This is why adding `cookies()` to a previously static route can dramatically change its behavior.

### Forcing a Rendering Mode

```typescript
// Force dynamic — always render per-request
export const dynamic = 'force-dynamic'

// Force static — cookies/headers return empty
export const dynamic = 'force-static'

// Error if dynamic APIs are used
export const dynamic = 'error'
```

## generateStaticParams

Pre-render dynamic route segments at build time:

```typescript
// app/blog/[slug]/page.tsx
export async function generateStaticParams() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json())
  return posts.map((post: Post) => ({
    slug: post.slug,
  }))
}

export default async function BlogPost({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = await fetch(`https://api.example.com/posts/${slug}`, {
    next: { tags: [`post-${slug}`] }
  }).then(r => r.json())
  return <Article post={post} />
}
```

### Behavior for Non-Generated Params

| Config | Behavior for Unknown Slugs |
|--------|---------------------------|
| `dynamicParams: true` (default) | Render on-demand, cache for subsequent requests |
| `dynamicParams: false` | Return 404 for slugs not in generateStaticParams |

```typescript
// Only allow pre-generated slugs
export const dynamicParams = false
```

### When to Use generateStaticParams

| Scenario | Use generateStaticParams? |
|----------|--------------------------|
| Blog with known posts at build time | Yes — pre-render all posts |
| E-commerce with 10,000 products | Yes for top 100, let rest generate on-demand |
| User profile pages | No — too many, too dynamic |
| Documentation with known pages | Yes — all pages known at build time |

## Partial Prerendering (PPR)

PPR combines static and dynamic rendering within a single route. The static shell is served instantly from the cache, and dynamic parts stream in using Suspense boundaries.

### How PPR Works

```
1. Build time: Render the route, stop at Suspense boundaries containing dynamic code
2. Static shell (everything outside Suspense) is cached
3. Request arrives: serve static shell instantly
4. Dynamic parts render on the server and stream into the Suspense boundaries
```

### Enabling PPR

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  experimental: {
    ppr: true, // or 'incremental' for per-route opt-in
  },
}
```

Per-route opt-in with incremental mode:

```typescript
// app/dashboard/page.tsx
export const experimental_ppr = true
```

### PPR Pattern

```typescript
// app/product/[id]/page.tsx
import { Suspense } from 'react'

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const product = await getProduct(id) // cached — part of static shell

  return (
    <div>
      {/* Static shell — served from cache instantly */}
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <img src={product.image} alt={product.name} />

      {/* Dynamic — streams in after request */}
      <Suspense fallback={<PriceSkeleton />}>
        <DynamicPrice id={id} />
      </Suspense>

      <Suspense fallback={<ReviewsSkeleton />}>
        <DynamicReviews id={id} />
      </Suspense>
    </div>
  )
}

async function DynamicPrice({ id }: { id: string }) {
  const price = await fetch(`/api/price/${id}`, { cache: 'no-store' })
    .then(r => r.json())
  return <span>${price.current}</span>
}
```

### PPR Boundaries

The Suspense boundary is the dividing line between static and dynamic:

| Inside Suspense | Rendering | Caching |
|----------------|-----------|---------|
| No dynamic APIs | Static (part of shell) | Cached |
| Uses cookies/headers | Dynamic (streams in) | Not cached |
| Uses no-store fetch | Dynamic (streams in) | Not cached |

## Streaming and Caching

### How Streaming Works

React Server Components stream HTML and RSC payload progressively. Components that resolve faster appear first; slow components stream in later.

```typescript
// app/page.tsx
import { Suspense } from 'react'

export default function Page() {
  return (
    <div>
      <Header /> {/* renders immediately */}
      <Suspense fallback={<Loading />}>
        <SlowDataComponent /> {/* streams when ready */}
      </Suspense>
      <Footer /> {/* renders immediately */}
    </div>
  )
}
```

### Streaming + Caching Interaction

| Route Type | Streaming | Full Route Cache |
|-----------|-----------|-----------------|
| Fully static | No streaming needed | Entire route cached |
| Fully dynamic | Streams progressively | Not cached |
| PPR | Static shell instant, dynamic streams | Shell cached, dynamic parts not |
| ISR (static with revalidate) | No streaming (pre-rendered) | Cached until revalidation |

### loading.tsx and Caching

The `loading.tsx` file creates an automatic Suspense boundary around the page content:

```typescript
// app/dashboard/loading.tsx
export default function Loading() {
  return <DashboardSkeleton />
}
```

In the Router Cache (Next.js 15+), `loading.tsx` output is cached for 5 minutes by default, even though page data staleTime is 0. This means navigating to a loading-equipped route shows the cached skeleton instantly.

## Rendering Decision Framework

| Question | Answer → Action |
|----------|----------------|
| Same content for all users? | Yes → Static (default) |
| Reads cookies/headers/searchParams? | Yes → Dynamic (automatic) |
| Content changes rarely (blog, docs)? | Yes → Static + ISR (`revalidate: N`) |
| Mix of static and dynamic sections? | Yes → PPR (Suspense boundaries) |
| Real-time per-user data? | Yes → Dynamic + `no-store` |
| High-traffic page with occasional updates? | Yes → Static + on-demand revalidation |
| Many dynamic routes with known params? | Yes → `generateStaticParams` + ISR |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `force-dynamic` on every route | No caching, slow for every user | Use specific dynamic triggers only where needed |
| Adding `cookies()` to a shared layout | Makes all child routes dynamic | Read cookies in leaf pages or middleware |
| Not using Suspense with slow data | Entire page blocked on slowest fetch | Wrap slow components in Suspense |
| `generateStaticParams` for millions of pages | Build time explodes | Pre-generate top pages, rest on-demand |
| PPR without meaningful fallbacks | Users see empty skeletons | Design informative loading states |
| Mixing static and dynamic in same component | Whole component becomes dynamic | Split into static parent + dynamic child |

For cache layer mechanics, see `references/four-cache-layers.md`.
For revalidation after mutations, see `references/revalidation-strategies.md`.
