# Routing Patterns

Sources:
- Next.js Docs: App Router, Routing, Middleware, Metadata API

## App Router File Conventions
Use file conventions to express intent and keep routing predictable.

| File | Purpose | When to Use |
| --- | --- | --- |
| `page.tsx` | Route entry | Render a segment UI |
| `layout.tsx` | Shared shell | Persist across child segments |
| `template.tsx` | Remounting shell | Reset state on navigation |
| `loading.tsx` | Suspense fallback | Stream partial UI |
| `error.tsx` | Error boundary | Catch segment errors |
| `not-found.tsx` | 404 view | Missing data or route |
| `route.ts` | Route Handler | API routes and webhooks |
| `middleware.ts` | Edge routing | Auth, rewrites, redirects |
| `default.tsx` | Parallel default | Provide fallback for slot |

## Layouts vs Templates
Use layouts for persistent UI and templates for resets.

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[240px_1fr]">
      <aside className="border-r">Sidebar</aside>
      <main className="p-6">{children}</main>
    </div>
  );
}
```

```tsx
// app/onboarding/template.tsx
export default function OnboardingTemplate({ children }: { children: React.ReactNode }) {
  return <div className="animate-fade-in">{children}</div>;
}
```

## Route Groups
Use route groups to organize without affecting the URL.

```
app/
  (marketing)/
    page.tsx
  (app)/
    dashboard/
      page.tsx
```

## Dynamic Routes
Use `[slug]` for single params, `[...slug]` for catch-all, `[[...slug]]` for optional.

```tsx
// app/blog/[slug]/page.tsx
export default async function BlogPost({ params }: { params: { slug: string } }) {
  const post = await fetch(`https://api.example.com/posts/${params.slug}`).then((r) => r.json());
  return <article>{post.title}</article>;
}
```

```tsx
// app/docs/[...slug]/page.tsx
export default async function Docs({ params }: { params: { slug: string[] } }) {
  const path = params.slug.join("/");
  const doc = await fetch(`https://api.example.com/docs/${path}`).then((r) => r.json());
  return <article>{doc.title}</article>;
}
```

```tsx
// app/[[...filters]]/page.tsx
export default function Filters({ params }: { params: { filters?: string[] } }) {
  const filters = params.filters ?? [];
  return <pre>{JSON.stringify(filters)}</pre>;
}
```

## Parallel Routes
Use parallel routes for dashboards, side panels, and modals.

```
app/
  dashboard/
    layout.tsx
    @stats/
      page.tsx
    @activity/
      page.tsx
    page.tsx
```

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  stats,
  activity,
}: {
  children: React.ReactNode;
  stats: React.ReactNode;
  activity: React.ReactNode;
}) {
  return (
    <div className="grid gap-6 md:grid-cols-3">
      <section className="md:col-span-2">{children}</section>
      <aside className="space-y-6">
        <div>{stats}</div>
        <div>{activity}</div>
      </aside>
    </div>
  );
}
```

## Intercepting Routes for Modals
Use intercepting routes to overlay modals without losing context.

```
app/
  products/
    page.tsx
    @modal/
      (.)[id]/page.tsx
```

```tsx
// app/products/@modal/(.)[id]/page.tsx
export default function ProductModal({ params }: { params: { id: string } }) {
  return (
    <div className="fixed inset-0 bg-black/50">
      <div className="mx-auto mt-20 max-w-xl bg-white p-6">Modal {params.id}</div>
    </div>
  );
}
```

Use `(..)` to intercept from parent, `(..)(..)` from grandparent, and `(...)` from root.

## Route Handlers
Use Route Handlers for external clients, webhooks, or edge runtime APIs.

```ts
// app/api/checkout/route.ts
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const payload = await req.json();
  await db.checkout.create(payload);
  return NextResponse.json({ ok: true }, { status: 201 });
}
```

## Middleware Patterns
Keep middleware short and routing-focused.

```ts
// middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const token = req.cookies.get("session")?.value;
  if (!token && req.nextUrl.pathname.startsWith("/dashboard")) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
```

```ts
// middleware.ts (geo routing)
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const country = req.geo?.country || "US";
  if (country === "FR") {
    const url = req.nextUrl.clone();
    url.pathname = "/fr" + req.nextUrl.pathname;
    return NextResponse.rewrite(url);
  }
  return NextResponse.next();
}
```

```ts
// middleware.ts (A/B testing)
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const bucket = req.cookies.get("ab")?.value || "a";
  const url = req.nextUrl.clone();
  url.searchParams.set("variant", bucket);
  return NextResponse.rewrite(url);
}
```

## next/navigation Hooks
Use hooks only inside Client Components.

```tsx
"use client";

import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";

export function RouteInfo() {
  const params = useParams();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();

  return (
    <div className="space-y-2">
      <div>Path: {pathname}</div>
      <div>Params: {JSON.stringify(params)}</div>
      <div>Query: {searchParams.toString()}</div>
      <button onClick={() => router.push("/dashboard")} className="border px-3 py-2">
        Go to dashboard
      </button>
    </div>
  );
}
```

## Metadata API
Use static `metadata` for fixed values and `generateMetadata` for dynamic.

```ts
// app/blog/[slug]/page.tsx
import type { Metadata } from "next";

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const post = await fetch(`https://api.example.com/posts/${params.slug}`).then((r) => r.json());
  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      images: [post.ogImage],
    },
  };
}
```

```tsx
// app/blog/[slug]/page.tsx
export default async function BlogPost({ params }: { params: { slug: string } }) {
  const post = await fetch(`https://api.example.com/posts/${params.slug}`).then((r) => r.json());
  return (
    <article>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Article",
            headline: post.title,
            datePublished: post.publishedAt,
          }),
        }}
      />
      <h1>{post.title}</h1>
    </article>
  );
}
```

## Anti-Patterns
| Anti-Pattern | Replace With |
| --- | --- |
| Using route groups to hide data dependencies | Move data into page or layout |
| Putting heavy logic in middleware | Use Route Handlers or Server Actions |
| Overusing catch-all routes for simple paths | Use specific segments |
| Mixing templates for persistent UI | Use layouts for persistence |
| Using parallel routes without defaults | Add `default.tsx` |
| Using Client Components for navigation state | Use `usePathname` and `useSearchParams` |
| Hardcoding metadata in client code | Use `metadata` or `generateMetadata` |
| Treating route handlers as primary UI data source | Prefer RSC fetch |
