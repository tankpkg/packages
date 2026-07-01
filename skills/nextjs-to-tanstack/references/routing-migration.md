# Routing Migration: Next.js to TanStack Start

Sources: TanStack Start official docs, TanStack Router docs, Inngest migration case study, community migration guides

TanStack Start uses a file-based routing system built on TanStack Router. The conventions differ from Next.js App Router in naming, nesting, and how route metadata is declared. This reference covers every structural mapping you need to migrate a Next.js app's routing layer.

---

## File Structure Mapping

The table below maps Next.js App Router file conventions to their TanStack Start equivalents. The root directory for routes is `src/routes/` by default.

| Next.js (App Router) | TanStack Start | Notes |
|---|---|---|
| `src/app/layout.tsx` | `src/routes/__root.tsx` | Root layout; uses `createRootRoute()` |
| `src/app/page.tsx` | `src/routes/index.tsx` | Index route at `/` |
| `src/app/about/page.tsx` | `src/routes/about.tsx` | Static route |
| `src/app/posts/page.tsx` | `src/routes/posts.index.tsx` | Index of `/posts` |
| `src/app/posts/layout.tsx` | `src/routes/posts.tsx` | Layout route for `/posts/*` |
| `src/app/posts/[slug]/page.tsx` | `src/routes/posts.$slug.tsx` | Dynamic segment |
| `src/app/posts/[...slug]/page.tsx` | `src/routes/posts.$.tsx` | Catch-all wildcard |
| `src/app/(group)/page.tsx` | `src/routes/_group/route.tsx` | Pathless layout (no URL segment) |
| `src/app/api/users/route.ts` | `src/routes/api/users.ts` | API / server route |

### Route Naming Conventions by URL

| URL Pattern | Filename | Route Type |
|---|---|---|
| `/` | `index.tsx` | Index route |
| `/about` | `about.tsx` | Static route |
| `/posts` | `posts.tsx` | Layout route for `/posts/*` |
| `/posts` (index) | `posts.index.tsx` or `posts/index.tsx` | Index of layout route |
| `/posts/:postId` | `posts.$postId.tsx` | Dynamic route |
| `/rest/*` | `rest/$.tsx` or `rest.$.tsx` | Wildcard / catch-all |
| (no URL segment) | `_auth/route.tsx` | Pathless layout route |

### Dynamic Segment Syntax

Next.js wraps dynamic segments in square brackets. TanStack Start prefixes them with `$`.

| Next.js | TanStack Start |
|---|---|
| `[slug]` | `$slug` |
| `[...slug]` (catch-all) | `$` (wildcard, accessed via `_splat`) |
| `[[...slug]]` (optional catch-all) | Not a direct equivalent; use wildcard + conditional |

---

## Root Route: `__root.tsx`

The root route replaces both `layout.tsx` and `_app.tsx` from Next.js. It is the single entry point that wraps every page in the application.

**Next.js `src/app/layout.tsx`:**

```tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
```

**TanStack Start `src/routes/__root.tsx`:**

```tsx
import {
  createRootRoute,
  Outlet,
  HeadContent,
  Scripts,
} from '@tanstack/react-router'
import appCss from '~/styles/app.css?url'

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { title: 'My App' },
    ],
    links: [{ rel: 'stylesheet', href: appCss }],
  }),
  errorComponent: DefaultCatchBoundary,
  notFoundComponent: () => <NotFound />,
  component: RootComponent,
})

function RootComponent() {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        <Outlet />
        <Scripts />
      </body>
    </html>
  )
}
```

**Critical requirements:**

- `<HeadContent />` must appear inside `<head>`. Omitting it causes meta tags and stylesheets to be missing.
- `<Scripts />` must appear before `</body>`. Omitting it causes the client-side JS bundle to never load, breaking hydration.
- CSS files must be imported with the `?url` suffix: `import appCss from '~/styles/app.css?url'`. A bare import does not work in this context.
- `<Outlet />` renders the matched child route. It is the direct equivalent of `{children}` in a Next.js layout.

### Root Route with Typed Context

When using TanStack Query or a shared auth context, use `createRootRouteWithContext` instead of `createRootRoute`. This makes the context type-safe across all child routes.

```tsx
import { createRootRouteWithContext } from '@tanstack/react-router'
import type { QueryClient } from '@tanstack/react-query'

interface RouterContext {
  queryClient: QueryClient
  user: AuthUser | null
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootComponent,
  // ...
})
```

Child routes can then access the context via `Route.useRouteContext()` or inside loaders via the `context` argument.

---

## Individual Routes: `createFileRoute`

Every non-root route file exports a `Route` constant created with `createFileRoute`. The path string passed to `createFileRoute` must match the file's location in the route tree — the bundler plugin validates and auto-corrects this on build.

**Next.js `src/app/posts/[postId]/page.tsx`:**

```tsx
export default async function PostPage({
  params,
}: {
  params: Promise<{ postId: string }>
}) {
  const { postId } = await params
  const post = await fetchPost(postId)
  return <div>{post.title}</div>
}
```

**TanStack Start `src/routes/posts.$postId.tsx`:**

```tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params }) => fetchPost(params.postId),
  pendingComponent: () => <Spinner />,
  errorComponent: ({ error }) => <ErrorDisplay error={error} />,
  notFoundComponent: () => <NotFound />,
  component: PostPage,
})

function PostPage() {
  const post = Route.useLoaderData()
  const { postId } = Route.useParams()
  return <div>{post.title}</div>
}
```

### Route Options Reference

| Option | Purpose | Next.js Equivalent |
|---|---|---|
| `component` | Page component | Default export |
| `loader` | Data loading before render | `generateStaticParams` / RSC fetch |
| `pendingComponent` | Shown while loader is in flight | `loading.tsx` |
| `errorComponent` | Shown when loader or component throws | `error.tsx` |
| `notFoundComponent` | Shown on 404 within this subtree | `not-found.tsx` |
| `head` | Meta tags and links for this route | `export const metadata` |
| `validateSearch` | Validate and type search params | Manual in Next.js |

---

## Accessing Route Parameters

Next.js App Router (v15+) passes `params` as a `Promise`. TanStack Start exposes params synchronously through typed hooks.

### Path Parameters

**Next.js:**

```tsx
export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  return <h1>{slug}</h1>
}
```

**TanStack Start:**

```tsx
function Page() {
  const { slug } = Route.useParams()
  return <h1>{slug}</h1>
}
```

`Route.useParams()` is fully typed based on the path string in `createFileRoute`. No generics or manual type annotations are needed.

### Catch-All / Wildcard Parameters

The catch-all segment `[...slug]` in Next.js becomes `$` in the filename and is accessed as `_splat` in TanStack Start.

**Next.js `src/app/docs/[...slug]/page.tsx`:**

```tsx
export default async function Page({
  params,
}: {
  params: Promise<{ slug: string[] }>
}) {
  const { slug } = await params
  const path = slug.join('/')
}
```

**TanStack Start `src/routes/docs.$.tsx`:**

```tsx
function Page() {
  const { _splat } = Route.useParams()
  // _splat is a string: "getting-started/installation"
  const segments = _splat?.split('/') ?? []
}
```

### Search Parameters

TanStack Start provides `validateSearch` to declare and type search params at the route level. This replaces manual `useSearchParams()` calls.

```tsx
import { z } from 'zod'

export const Route = createFileRoute('/posts')({
  validateSearch: z.object({
    page: z.number().int().min(1).default(1),
    q: z.string().optional(),
  }),
  component: PostsPage,
})

function PostsPage() {
  const { page, q } = Route.useSearch()
}
```

---

## Layout Routes

In Next.js, any `layout.tsx` file automatically wraps its sibling and child pages. In TanStack Start, a layout route is a regular route file that renders `<Outlet />` where children should appear.

**Next.js `src/app/posts/layout.tsx`:**

```tsx
export default function PostsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex">
      <nav>Posts sidebar</nav>
      <main>{children}</main>
    </div>
  )
}
```

**TanStack Start `src/routes/posts.tsx`:**

```tsx
import { createFileRoute, Outlet } from '@tanstack/react-router'

export const Route = createFileRoute('/posts')({
  component: PostsLayout,
})

function PostsLayout() {
  return (
    <div className="flex">
      <nav>Posts sidebar</nav>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
```

The file `posts.tsx` acts as the layout for all routes nested under `/posts`. The index page at `/posts` lives in `posts.index.tsx`.

---

## Pathless Layout Routes

Next.js Route Groups use parentheses — `(group)` — to group routes under a shared layout without adding a URL segment. TanStack Start uses an underscore prefix for the same purpose.

**Next.js directory structure:**

```
src/app/
├── (auth)/
│   ├── layout.tsx      ← auth guard layout
│   ├── dashboard/
│   │   └── page.tsx    ← renders at /dashboard
│   └── settings/
│       └── page.tsx    ← renders at /settings
└── (guest)/
    ├── layout.tsx      ← unauthenticated layout
    └── login/
        └── page.tsx    ← renders at /login
```

**TanStack Start directory structure:**

```
src/routes/
├── _auth/
│   ├── route.tsx       ← auth guard layout (no URL segment)
│   ├── dashboard.tsx   ← renders at /dashboard
│   └── settings.tsx    ← renders at /settings
└── _guest/
    ├── route.tsx       ← unauthenticated layout
    └── login.tsx       ← renders at /login
```

The `_auth/route.tsx` file defines the layout component and can run a loader that checks authentication. The underscore prefix is stripped from the URL — `/dashboard` is the resulting path, not `/_auth/dashboard`.

```tsx
// src/routes/_auth/route.tsx
export const Route = createFileRoute('/_auth')({
  beforeLoad: async ({ context }) => {
    if (!context.user) throw redirect({ to: '/login' })
  },
  component: () => <Outlet />,
})
```

---

## Flat vs. Directory File Organization

TanStack Start supports two equivalent file organization strategies. Both produce identical route trees and TypeScript types.

**Flat (dot notation) — preferred for small to medium apps:**

```
src/routes/
├── __root.tsx
├── index.tsx
├── about.tsx
├── posts.tsx
├── posts.index.tsx
├── posts.$postId.tsx
└── posts.$postId.edit.tsx
```

**Directory-based — preferred for large apps with many routes per section:**

```
src/routes/
├── __root.tsx
├── index.tsx
├── about.tsx
└── posts/
    ├── route.tsx        ← layout for /posts/*
    ├── index.tsx        ← /posts
    ├── $postId/
    │   ├── route.tsx    ← layout for /posts/:postId/*
    │   ├── index.tsx    ← /posts/:postId
    │   └── edit.tsx     ← /posts/:postId/edit
```

In the directory style, `route.tsx` is the layout file for that directory. In the flat style, the parent segment name (e.g., `posts.tsx`) serves the same role.

---

## Route Tree Generation

TanStack Router generates a `routeTree.gen.ts` file automatically. This file contains the full TypeScript type graph for all routes, enabling end-to-end type safety for navigation, params, and search params.

**Key facts:**

- The file is generated by the TanStack Router Bundler Plugin on `npm run dev` or `npm run build`.
- Never edit `routeTree.gen.ts` manually. Changes are overwritten on the next build.
- TypeScript errors referencing missing route types before the first `dev` run are expected. Run `npm run dev` once to generate the file.
- Add `routeTree.gen.ts` to `.gitignore` or commit it — both are valid. Committing it avoids the cold-start error in CI.
- The plugin is configured in `vite.config.ts` (or `app.config.ts` for TanStack Start):

```ts
import { tanstackStart } from '@tanstack/start/plugin/vite'

export default defineConfig({
  plugins: [tanstackStart()],
})
```

---

## API Routes

Next.js Route Handlers map to TanStack Start server route handlers. The file location convention is the same; the export format differs.

**Next.js `src/app/api/users/route.ts`:**

```ts
export async function GET() {
  const users = await db.user.findMany()
  return Response.json(users)
}

export async function POST(request: Request) {
  const body = await request.json()
  const user = await db.user.create({ data: body })
  return Response.json(user, { status: 201 })
}
```

**TanStack Start `src/routes/api/users.ts`:**

```ts
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/api/users')({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const users = await db.user.findMany()
        return Response.json(users)
      },
      POST: async ({ request }) => {
        const body = await request.json()
        const user = await db.user.create({ data: body })
        return Response.json(user, { status: 201 })
      },
    },
  },
})
```

Dynamic API routes follow the same `$param` convention — `api/users.$userId.ts` handles `GET /api/users/:userId` with `params.userId` in the handler.

---

## Complete Convention Conversion Table

For Link, navigation hooks, and search params migration, see `references/component-migration.md`.

| Next.js Concept | TanStack Start Equivalent |
|---|---|
| `app/layout.tsx` | `routes/__root.tsx` with `createRootRoute()` |
| `app/page.tsx` | `routes/index.tsx` with `createFileRoute('/')` |
| `app/about/page.tsx` | `routes/about.tsx` |
| `app/posts/layout.tsx` | `routes/posts.tsx` (renders `<Outlet />`) |
| `app/posts/page.tsx` | `routes/posts.index.tsx` |
| `app/posts/[id]/page.tsx` | `routes/posts.$id.tsx` |
| `app/posts/[...slug]/page.tsx` | `routes/posts.$.tsx` (param: `_splat`) |
| `app/(group)/layout.tsx` | `routes/_group/route.tsx` |
| `app/api/route.ts` | `routes/api/index.ts` with `server.handlers` |
| `app/loading.tsx` | `pendingComponent` in `createFileRoute` |
| `app/error.tsx` | `errorComponent` in `createFileRoute` |
| `app/not-found.tsx` | `notFoundComponent` in `createFileRoute` |
| `export const metadata` | `head()` in `createFileRoute` or `createRootRoute` |
| `params` prop (async) | `Route.useParams()` (sync, typed) |
| `useSearchParams()` | `Route.useSearch()` with `validateSearch` |
| `<Link href="...">` | `<Link to="..." params={...}>` |
| `useRouter().push()` | `useNavigate()` then `navigate({ to: '...' })` |
| `usePathname()` | `useLocation().pathname` |
| `redirect()` | `throw redirect({ to: '...' })` |
| `notFound()` | `throw notFound()` |
| Route Groups `(name)` | Pathless layouts `_name/` |
| `middleware.ts` | `beforeLoad` in route or root route |
| `next.config.js` redirects | `redirect()` in root `beforeLoad` or server middleware |
