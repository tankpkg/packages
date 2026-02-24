# Caching and Data Fetching

Sources:
- Next.js Docs: Caching, Data Fetching, Route Segment Config
- Vercel Blog: Caching deep dives and performance patterns

## Mental Model of the Four Cache Layers
- Treat caching as a stack; each layer builds on the one below it.
- Keep request memoization in mind for deduplicating fetches within a render.
- Use the Data Cache for durable fetch results across requests.
- Use the Full Route Cache for static HTML and RSC payloads.
- Use the Router Cache for client-side navigation speedups.

## Cache Layer Quick Table
| Cache Layer | Duration | Revalidation | Opt Out |
| --- | --- | --- | --- |
| Request Memoization | Per request | N/A | `cache: "no-store"` |
| Data Cache | Persistent until revalidate | `next.revalidate`, `revalidateTag` | `cache: "no-store"` |
| Full Route Cache | Persistent until revalidate | `revalidatePath`, segment `revalidate` | `export const dynamic = "force-dynamic"` |
| Router Cache | Client session | `router.refresh()` | `router.refresh()` after mutations |

## Request Memoization
- Use memoization to prevent duplicate fetches inside a single render.
- Keep identical `fetch` calls in one render frame to benefit.
- Avoid mixing `no-store` with `force-cache` in the same request path.

```ts
// app/reports/page.tsx
async function getReport() {
  return fetch("https://api.example.com/report").then((r) => r.json());
}

export default async function ReportsPage() {
  const reportA = await getReport();
  const reportB = await getReport();
  return <pre>{JSON.stringify({ reportA, reportB }, null, 2)}</pre>;
}
```

## Data Cache
- Treat Data Cache as the durable store for fetch results.
- Use `next.revalidate` to time-box staleness.
- Use tags for targeted invalidation after mutations.
- Use `cache: "no-store"` to bypass Data Cache.

```ts
// app/products/page.tsx
async function getProducts() {
  const res = await fetch("https://api.example.com/products", {
    next: { revalidate: 120, tags: ["products"] },
  });
  if (!res.ok) throw new Error("Failed to fetch products");
  return res.json();
}
```

## Full Route Cache
- Use static rendering to cache the entire route output.
- Keep dynamic APIs (cookies, headers) out of static routes.
- Revalidate with `revalidatePath` or per-segment `revalidate`.

```ts
// app/blog/page.tsx
export const revalidate = 300;

export default async function BlogIndex() {
  const posts = await fetch("https://api.example.com/posts", {
    next: { revalidate: 300 },
  }).then((r) => r.json());
  return <ul>{posts.map((p: any) => <li key={p.id}>{p.title}</li>)}</ul>;
}
```

## Router Cache
- Use Router Cache for faster client navigation between segments.
- Trigger `router.refresh()` after a mutation to sync stale UI.
- Avoid calling `router.refresh()` on every interaction.

```tsx
"use client";

import { useRouter } from "next/navigation";

export function RefreshButton() {
  const router = useRouter();
  return (
    <button onClick={() => router.refresh()} className="border px-3 py-2">
      Refresh
    </button>
  );
}
```

## fetch() Options
- Use `cache` for opt-out or forced caching.
- Use `next.revalidate` for time-based ISR.
- Use `next.tags` for targeted invalidation.

```ts
// app/catalog/page.tsx
const res = await fetch("https://api.example.com/catalog", {
  cache: "force-cache",
  next: { revalidate: 600, tags: ["catalog"] },
});
```

```ts
// app/profile/page.tsx
const res = await fetch("https://api.example.com/profile", {
  cache: "no-store",
});
```

## revalidatePath() and revalidateTag()
Use path invalidation for UI segments, tag invalidation for shared data.

```ts
// app/posts/actions.ts
"use server";

import { revalidatePath, revalidateTag } from "next/cache";

export async function publishPost(id: string) {
  await db.post.publish(id);
  revalidateTag("posts");
  revalidatePath("/blog");
}
```

## Static vs Dynamic Rendering
- Treat static rendering as the default.
- Trigger dynamic rendering with cookies, headers, or `no-store` fetch.
- Force dynamic if you must read per-request data.
- Force static if you want deterministic ISR.

```ts
// app/account/page.tsx
export const dynamic = "force-dynamic";

import { cookies } from "next/headers";

export default async function AccountPage() {
  const session = cookies().get("session")?.value;
  const data = await fetch(`https://api.example.com/account?session=${session}`, {
    cache: "no-store",
  }).then((r) => r.json());
  return <pre>{JSON.stringify(data, null, 2)}</pre>;
}
```

```ts
// app/marketing/page.tsx
export const dynamic = "force-static";
export const revalidate = 3600;
```

## generateStaticParams()
Use static params to prebuild dynamic routes.

```ts
// app/docs/[slug]/page.tsx
export async function generateStaticParams() {
  const slugs = await fetch("https://api.example.com/docs/slugs").then((r) => r.json());
  return slugs.map((slug: string) => ({ slug }));
}

export default async function DocPage({ params }: { params: { slug: string } }) {
  const doc = await fetch(`https://api.example.com/docs/${params.slug}`, {
    next: { revalidate: 86400 },
  }).then((r) => r.json());
  return <article>{doc.content}</article>;
}
```

## Incremental Static Regeneration (ISR)
- Use ISR for mostly static content with occasional updates.
- Combine `revalidate` with tags for targeted updates.
- Keep ISR intervals aligned with actual data freshness.

```ts
// app/pricing/page.tsx
export const revalidate = 900;

export default async function PricingPage() {
  const plans = await fetch("https://api.example.com/plans", {
    next: { revalidate: 900, tags: ["plans"] },
  }).then((r) => r.json());
  return <pre>{JSON.stringify(plans, null, 2)}</pre>;
}
```

## Route Segment Config Options
- Use `dynamic` for rendering mode selection.
- Use `revalidate` for ISR per segment.
- Use `fetchCache` for cross-fetch behavior.
- Use `runtime` for edge vs node.

```ts
// app/store/page.tsx
export const dynamic = "auto";
export const revalidate = 300;
export const fetchCache = "auto";
export const runtime = "nodejs";
```

## Database Queries (No fetch)
Use `unstable_cache` to cache DB results with tags.

```ts
// app/lib/db.ts
import { unstable_cache } from "next/cache";

export const getFeaturedProducts = unstable_cache(
  async () => {
    return db.product.findMany({ where: { featured: true } });
  },
  ["featured-products"],
  { revalidate: 300, tags: ["products"] }
);
```

```ts
// app/home/page.tsx
import { getFeaturedProducts } from "../lib/db";

export default async function HomePage() {
  const products = await getFeaturedProducts();
  return <pre>{JSON.stringify(products, null, 2)}</pre>;
}
```

## Common Patterns
- Use tags for shared data across routes.
- Use per-route `revalidate` for content pages.
- Use `no-store` for user-specific data.
- Use `force-dynamic` sparingly for personalization.

## Debugging Cache Behavior
- Log `cache` and `next` options in fetch wrappers.
- Inspect response headers for cache hints.
- Use `router.refresh()` to verify Router Cache updates.

## Anti-Patterns
| Anti-Pattern | Replace With |
| --- | --- |
| Using `no-store` everywhere | Use `revalidate` or tags |
| Tagging data without invalidation | Use `revalidateTag` on writes |
| Global `force-dynamic` to fix stale data | Scope dynamic to specific routes |
| Overusing `router.refresh()` | Targeted invalidation + RSC fetch |
| ISR interval mismatched to data change | Align revalidate to reality |
| Fetching inside middleware | Use RSC or Route Handler |
| Caching private data in Data Cache | Use `no-store` |
| Ignoring Router Cache after mutations | Call `router.refresh()` |
