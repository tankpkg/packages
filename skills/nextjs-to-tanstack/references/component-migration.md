# Component and API Migration

Sources: TanStack Start official docs, TanStack Router docs, Inngest migration case study, unpic.pics docs

This reference covers the component-level and navigation API changes required when migrating a Next.js application to TanStack Start. Routing structure, data fetching internals, authentication, and deployment are covered in separate reference files.

---

## 1. Link Component

Next.js uses `href`; TanStack Router uses `to`. The import path also changes.

```tsx
// Next.js
import Link from 'next/link'

<Link href="/dashboard">Dashboard</Link>
<Link href="/posts/hello-world">Post</Link>
```

```tsx
// TanStack Start
import { Link } from '@tanstack/react-router'

<Link to="/dashboard">Dashboard</Link>
<Link to="/posts/$slug" params={{ slug: 'hello-world' }}>Post</Link>
```

The `to` prop is typed against your actual route tree. Passing a path that does not exist in your routes is a TypeScript error at compile time — a significant improvement over Next.js where invalid `href` values are only caught at runtime.

### Additional Link Props

| Prop | Type | Purpose |
|------|------|---------|
| `to` | Route path (typed) | Destination route |
| `params` | Object (typed) | Dynamic segment values |
| `search` | Object (typed) | Query string values |
| `preload` | `"intent"` \| `false` | Preload on hover/focus |
| `activeProps` | `React.HTMLAttributes` | Applied when route is active |
| `inactiveProps` | `React.HTMLAttributes` | Applied when route is inactive |
| `replace` | `boolean` | Replace history entry instead of push |
| `resetScroll` | `boolean` | Scroll to top on navigation (default: `true`) |

```tsx
// Active state styling — replaces Next.js usePathname() pattern
<Link
  to="/dashboard"
  activeProps={{ className: 'font-bold text-blue-600' }}
  inactiveProps={{ className: 'text-gray-600' }}
  preload="intent"
>
  Dashboard
</Link>

// Type-safe dynamic route
<Link
  to="/posts/$postId/comments/$commentId"
  params={{ postId: '123', commentId: '456' }}
  search={{ highlight: true }}
>
  View Comment
</Link>
```

---

## 2. Image Component

TanStack Start has no built-in image optimization server. Choose between `@unpic/react` for CDN-aware responsive images or a plain `<img>` tag with manual attributes.

```tsx
// Next.js
import Image from 'next/image'

<Image
  src="/photo.jpg"
  alt="A descriptive caption"
  width={600}
  height={400}
  priority
/>
```

```tsx
// TanStack Start — option A: @unpic/react (recommended)
// npm install @unpic/react
import { Image } from '@unpic/react'

<Image
  src="/photo.jpg"
  alt="A descriptive caption"
  width={600}
  height={400}
  layout="constrained"
  priority
/>
```

```tsx
// TanStack Start — option B: plain <img>
<img
  src="/photo.jpg"
  alt="A descriptive caption"
  width={600}
  height={400}
  loading="lazy"
  decoding="async"
/>
```

### Image Feature Comparison

| Feature | Next.js `<Image>` | `@unpic/react` | Plain `<img>` |
|---------|-------------------|----------------|---------------|
| Lazy loading | Automatic | Automatic | Manual (`loading="lazy"`) |
| Responsive sizes | Automatic | Automatic | Manual (`srcset`) |
| WebP/AVIF conversion | Built-in server | CDN-dependent | No |
| On-the-fly resizing | Built-in server | CDN-dependent | No |
| `priority` prop | Yes | Yes | Manual (`fetchpriority="high"`) |
| Layout modes | `fill`, `responsive` | `constrained`, `fullWidth`, `fixed` | Manual CSS |

For on-the-fly format conversion and resizing without a Next.js server, use an external image CDN: Cloudinary, Imgix, or Cloudflare Images. Configure `@unpic/react` with the appropriate CDN transformer to get automatic `srcset` generation and format negotiation.

---

## 3. Head and Metadata

Next.js App Router uses exported `metadata` objects or `generateMetadata` functions. TanStack Start uses a `head()` function on the route definition, which receives loader data.

```tsx
// Next.js App Router — static metadata
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'About Us',
  description: 'Learn more about our team.',
  openGraph: { title: 'About Us' },
}
```

```tsx
// Next.js App Router — dynamic metadata
export async function generateMetadata({ params }: { params: { slug: string } }) {
  const post = await fetchPost(params.slug)
  return { title: post.title, description: post.excerpt }
}
```

```tsx
// TanStack Start — static metadata
export const Route = createFileRoute('/about')({
  head: () => ({
    meta: [
      { title: 'About Us' },
      { name: 'description', content: 'Learn more about our team.' },
      { property: 'og:title', content: 'About Us' },
    ],
    links: [
      { rel: 'canonical', href: 'https://example.com/about' },
    ],
  }),
})
```

```tsx
// TanStack Start — dynamic metadata from loader data
export const Route = createFileRoute('/posts/$slug')({
  loader: async ({ params }) => fetchPost(params.slug),
  head: ({ loaderData }) => ({
    meta: [
      { title: loaderData.title },
      { name: 'description', content: loaderData.excerpt },
      { property: 'og:title', content: loaderData.title },
      { property: 'og:image', content: loaderData.coverImage },
    ],
  }),
})
```

The root route must render `<HeadContent />` inside `<head>`. Child route `head()` values merge up the tree, with child values taking precedence. Duplicate `title` and `name` meta tags are deduplicated automatically.

### Reusable SEO Utility

Extract a helper to avoid repeating Open Graph and Twitter card tags across routes:

```tsx
// src/utils/seo.ts
export function seo({
  title,
  description,
  image,
}: {
  title: string
  description?: string
  image?: string
}) {
  return [
    { title },
    ...(description ? [{ name: 'description', content: description }] : []),
    { name: 'twitter:title', content: title },
    { property: 'og:title', content: title },
    ...(description
      ? [
          { name: 'twitter:description', content: description },
          { property: 'og:description', content: description },
        ]
      : []),
    ...(image
      ? [
          { property: 'og:image', content: image },
          { name: 'twitter:image', content: image },
          { name: 'twitter:card', content: 'summary_large_image' },
        ]
      : []),
  ]
}

// Usage in a route
export const Route = createFileRoute('/posts/$slug')({
  loader: async ({ params }) => fetchPost(params.slug),
  head: ({ loaderData }) => ({
    meta: seo({
      title: loaderData.title,
      description: loaderData.excerpt,
      image: loaderData.coverImage,
    }),
  }),
})
```

---

## 4. Font Loading

Next.js provides `next/font` for automatic subset optimization and zero-layout-shift font loading. TanStack Start has no equivalent — use Fontsource npm packages instead.

```tsx
// Next.js
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'], display: 'swap' })

export default function RootLayout({ children }) {
  return (
    <html className={inter.className}>
      <body>{children}</body>
    </html>
  )
}
```

```css
/* TanStack Start — install: npm install @fontsource-variable/inter */
/* In your global CSS file: */
@import '@fontsource-variable/inter';

body {
  font-family: 'Inter Variable', sans-serif;
}
```

Fontsource bundles font files as npm packages, served from your own origin. Variable font packages (`@fontsource-variable/*`) provide the full weight/style range in a single file. Static weight packages (`@fontsource/inter`) allow importing only the weights you need to reduce bundle size.

There is no automatic subset optimization — import only the weights and styles your design requires to keep CSS bundle size reasonable.

---

## 5. Navigation Hooks

| Next.js | TanStack Start | Notes |
|---------|----------------|-------|
| `useRouter()` from `next/navigation` | `useRouter()` from `@tanstack/react-router` | Different API surface |
| `router.push('/path')` | `navigate({ to: '/path' })` via `useNavigate()` | Type-safe destination |
| `router.replace('/path')` | `navigate({ to: '/path', replace: true })` | |
| `router.back()` | `router.history.back()` | |
| `router.refresh()` | `router.invalidate()` | Re-runs loaders |
| `usePathname()` | `useLocation().pathname` | |
| `useSearchParams()` | `Route.useSearch()` | Requires `validateSearch` on route |
| `useParams()` | `Route.useParams()` | Fully typed to route definition |
| `redirect()` from `next/navigation` | `throw redirect({ to: '/path' })` | Must be thrown, not called |
| `notFound()` from `next/navigation` | `throw notFound()` | Must be thrown, not called |

The `redirect()` and `notFound()` functions in TanStack Start are thrown as special errors, not called as functions that return. This is a common source of bugs during migration — ensure every call site uses `throw`.

---

## 6. Search Parameters

Next.js passes `searchParams` as a prop to page components with no declaration required. TanStack Start requires declaring a `validateSearch` function on the route, which parses and types the raw query string object.

```tsx
// Next.js — no declaration needed
export default function SearchPage({
  searchParams,
}: {
  searchParams: { q?: string; page?: string; sort?: string }
}) {
  const query = searchParams.q ?? ''
  const page = Number(searchParams.page ?? 1)
  return <Results query={query} page={page} />
}
```

```tsx
// TanStack Start — declare validateSearch on the route
export const Route = createFileRoute('/search')({
  validateSearch: (search: Record<string, unknown>) => ({
    q: (search.q as string) ?? '',
    page: Number(search.page ?? 1),
    sort: (search.sort as 'asc' | 'desc') ?? 'desc',
  }),
  component: SearchPage,
})

function SearchPage() {
  // Fully typed — TypeScript knows q is string, page is number, sort is 'asc' | 'desc'
  const { q, page, sort } = Route.useSearch()
  const navigate = useNavigate({ from: Route.fullPath })

  function nextPage() {
    // Type-safe partial update — prev is typed
    navigate({ search: (prev) => ({ ...prev, page: prev.page + 1 }) })
  }

  return <Results query={q} page={page} sort={sort} onNextPage={nextPage} />
}
```

Use a validation library such as Zod or Valibot inside `validateSearch` for production routes where search param integrity matters:

```tsx
import { z } from 'zod'
import { zodValidator } from '@tanstack/zod-adapter'

const searchSchema = z.object({
  q: z.string().default(''),
  page: z.number().int().positive().default(1),
  sort: z.enum(['asc', 'desc']).default('desc'),
})

export const Route = createFileRoute('/search')({
  validateSearch: zodValidator(searchSchema),
  component: SearchPage,
})
```

---

## 7. Loading, Error, and Not-Found Components

Next.js uses file-based conventions (`loading.tsx`, `error.tsx`, `not-found.tsx`). TanStack Start uses options on the route definition.

| Next.js File | TanStack Route Option | Behavior |
|-------------|----------------------|----------|
| `loading.tsx` | `pendingComponent` | Shown while the route loader is running |
| `error.tsx` | `errorComponent` | Shown when the loader or component throws |
| `not-found.tsx` | `notFoundComponent` | Shown when `throw notFound()` is called |
| N/A | `pendingMs` | Milliseconds to wait before showing `pendingComponent` |
| N/A | `pendingMinMs` | Minimum milliseconds to show `pendingComponent` once visible |

```tsx
// Next.js — separate files
// app/posts/[postId]/loading.tsx
export default function Loading() {
  return <PostSkeleton />
}

// app/posts/[postId]/error.tsx
'use client'
export default function Error({ error }: { error: Error }) {
  return <ErrorDisplay error={error} />
}
```

```tsx
// TanStack Start — co-located on the route
export const Route = createFileRoute('/posts/$postId')({
  loader: ({ params }) => fetchPost(params.postId),
  pendingComponent: PostSkeleton,
  errorComponent: ({ error }) => <ErrorDisplay error={error} />,
  notFoundComponent: () => <p>Post not found.</p>,
  pendingMs: 300,    // wait 300ms before showing skeleton (avoids flash on fast loads)
  pendingMinMs: 500, // show skeleton for at least 500ms once visible (avoids flash on completion)
})
```

The `pendingMs` and `pendingMinMs` options together prevent the "flash of loading state" problem that requires manual `setTimeout` workarounds in Next.js.

---

## 8. Programmatic Navigation

```tsx
// Next.js
import { useRouter } from 'next/navigation'

function MyComponent() {
  const router = useRouter()

  function handleSubmit() {
    router.push('/posts/123')
    router.replace('/dashboard')
  }
}
```

```tsx
// TanStack Start
import { useNavigate, redirect } from '@tanstack/react-router'

function MyComponent() {
  const navigate = useNavigate()

  function handleSubmit() {
    // Type-safe — TypeScript validates the route and params
    navigate({ to: '/posts/$postId', params: { postId: '123' } })

    // With search params
    navigate({ to: '/search', search: { q: 'tanstack', page: 1 } })

    // Replace instead of push
    navigate({ to: '/dashboard', replace: true })
  }
}
```

```tsx
// Redirect inside a loader or beforeLoad (thrown, not returned)
export const Route = createFileRoute('/dashboard')({
  beforeLoad: ({ context }) => {
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: '/login',
        search: { returnTo: '/dashboard' },
      })
    }
  },
})
```

---

## 9. Features With No Direct Equivalent

| Next.js Feature | TanStack Start Status | Recommended Approach |
|-----------------|----------------------|----------------------|
| `next/og` (OpenGraph image generation) | No built-in equivalent | Use `satori` directly, or a serverless function |
| Parallel Routes (`@slot` convention) | No equivalent | Conditional rendering or separate route trees |
| Intercepting Routes (`(.)path` convention) | No equivalent | Modal state in search params + conditional rendering |
| `template.tsx` (re-mounts on every navigation) | No direct equivalent | Use `key` prop on component tied to route path |
| Edge Runtime (`export const runtime = 'edge'`) | Not a per-route option | Cloudflare Workers via the Vite plugin adapter |
| `next/headers` (read request headers in RSC) | No equivalent | Access headers in `createServerFn` or loader context |
| `revalidatePath` / `revalidateTag` | No equivalent | Call `router.invalidate()` on the client after mutations |

---

## 10. Server vs. Client Boundaries

TanStack Start has no `'use client'` or `'use server'` directive system. All React components are standard client-capable components. The server boundary is determined by where code runs, not by file-level directives.

| Code Location | Runs On |
|---------------|---------|
| `loader` function body | Server (during SSR and client-side navigation prefetch) |
| `beforeLoad` function body | Server |
| `createServerFn` body | Server only |
| Component render function | Client (hydrated from server HTML) |
| Event handlers | Client only |

For detailed server function examples and the `createServerFn` API, see `references/data-and-server-functions.md`.

If your Next.js app relies heavily on RSC — streaming server-rendered subtrees, `use cache`, or `Suspense` fed by RSC data — plan a more substantial architectural change. The mental model shifts from "server components that render HTML" to "server functions that return data, consumed by client components."
