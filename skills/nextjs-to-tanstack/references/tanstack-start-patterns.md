# TanStack Start Patterns

Sources: TanStack Router docs, TkDodo blog (context inheritance), official examples, mugnavo/tanstarter

These patterns are native to TanStack Start and have no direct Next.js equivalent. They represent the mental model shift required to work effectively with the framework — not conversions from Next.js concepts, but new capabilities to learn.

---

## 1. Type-Safe Navigation

TanStack Router infers the full route tree at build time. Every `to` prop, every `params` object, and every `search` argument is checked against the actual route definitions.

```tsx
const navigate = useNavigate()

// TypeScript error if '/posts/$slug' does not exist in the route tree
// TypeScript error if params.slug is missing or mistyped
navigate({ to: '/posts/$slug', params: { slug: 'hello-world' } })
```

Links receive the same treatment:

```tsx
<Link to="/posts/$slug" params={{ slug: post.slug }}>
  Read more
</Link>
```

The `to` prop is typed to the union of all valid route paths. Rename a route file and every broken `Link` and `navigate` call becomes a compile error. This eliminates an entire class of runtime 404s that Next.js cannot catch.

Use `from` to scope relative navigation and get narrower param types:

```tsx
const navigate = useNavigate({ from: '/posts/$slug' })
navigate({ to: '.', params: { slug: 'new-slug' } })
```

---

## 2. Search Params as First-Class State

Next.js exposes search params as `Record<string, string | string[]>` — untyped, unvalidated, and disconnected from the component tree. TanStack Router treats search params as typed, validated state that participates in the route lifecycle.

Define the schema on the route:

```tsx
export const Route = createFileRoute('/search')({
  validateSearch: (search) => ({
    q: (search.q as string) ?? '',
    page: Number(search.page ?? 1),
    sort: (search.sort as 'asc' | 'desc') ?? 'desc',
  }),
})
```

Read and update from any component under that route:

```tsx
function SearchPage() {
  const { q, page, sort } = Route.useSearch()
  const navigate = useNavigate({ from: Route.fullPath })

  function nextPage() {
    navigate({ search: (prev) => ({ ...prev, page: prev.page + 1 }) })
  }
}
```

The functional updater form (`(prev) => ...`) preserves existing params while changing only the ones you specify — no manual `URLSearchParams` construction.

Use Zod for richer validation and coercion:

```tsx
import { zodSearchValidator } from '@tanstack/router-zod-adapter'
import { z } from 'zod'

const searchSchema = z.object({
  q: z.string().default(''),
  page: z.number().int().positive().default(1),
  sort: z.enum(['asc', 'desc']).default('desc'),
})

export const Route = createFileRoute('/search')({
  validateSearch: zodSearchValidator(searchSchema),
})
```

Invalid search params are coerced to defaults rather than crashing. The schema serves as documentation, validation, and type source simultaneously.

---

## 3. Preloading

TanStack Router can run a route's `loader` before the user navigates — triggered by hover or focus on a `Link`. By the time the user clicks, data is already in cache.

Configure globally:

```tsx
const router = createRouter({
  routeTree,
  defaultPreload: 'intent',       // preload on hover/focus
  defaultPreloadStaleTime: 0,     // always revalidate on preload
})
```

Override per link:

```tsx
<Link to="/posts" preload="intent">Posts</Link>
<Link to="/about" preload={false}>About</Link>
```

`defaultPreloadStaleTime: 0` means preloaded data is always fresh. Set a positive value (milliseconds) to reuse cached data within that window — useful for data that changes infrequently.

Preloading is what makes TanStack Start apps feel instant. The network round-trip happens during the hover dwell time, not after the click.

---

## 4. beforeLoad vs loader

Both hooks run during navigation, but they serve distinct purposes and execute in different phases.

| | `beforeLoad` | `loader` |
|---|---|---|
| Phase | Pre-loading | Loading (after all `beforeLoad`s) |
| Purpose | Auth checks, redirects, context injection | Data fetching |
| Return value | Merged into route context | Available via `Route.useLoaderData()` |
| Execution order | Sequential, parent before child | Can run in parallel across siblings |
| Can redirect | Yes — `throw redirect()` | Yes |
| Receives context | Yes — including parent `beforeLoad` returns | Yes — including all `beforeLoad` returns |

The canonical pattern: guard access in `beforeLoad`, fetch data in `loader`.

```tsx
export const Route = createFileRoute('/dashboard')({
  beforeLoad: async ({ context }) => {
    if (!context.auth?.user) {
      throw redirect({ to: '/login', search: { returnTo: '/dashboard' } })
    }
    return { user: context.auth.user }
  },
  loader: async ({ context }) => {
    // context.user is typed — injected by beforeLoad above
    return fetchDashboardData(context.user.id)
  },
})
```

Parent `beforeLoad` returns are available in child `beforeLoad` and `loader` calls. This is how auth context flows down the route tree without prop drilling or React Context.

---

## 5. Router Context (Dependency Injection)

Router context is the mechanism for injecting shared services — `QueryClient`, auth state, feature flags — into every route in the tree. It replaces React Context for route-level concerns and is fully type-safe.

Define the context shape and provide initial values when creating the router:

```tsx
// router.tsx
export function getRouter() {
  const queryClient = new QueryClient()

  const router = createRouter({
    routeTree,
    context: {
      queryClient,
      user: null as User | null,
    },
  })

  return router
}
```

Declare the expected context type on the root route:

```tsx
// routes/__root.tsx
import type { QueryClient } from '@tanstack/react-query'

interface RouterContext {
  queryClient: QueryClient
  user: User | null
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootComponent,
})
```

Access context in any route's `beforeLoad` or `loader`:

```tsx
export const Route = createFileRoute('/dashboard')({
  loader: ({ context }) => {
    // context.queryClient is typed — no casting required
    return context.queryClient.ensureQueryData(dashboardQuery())
  },
})
```

Add a field to `RouterContext` and it becomes available everywhere in the tree immediately. This is the primary pattern for passing the `QueryClient` to loaders — the TkDodo blog documents this as the recommended integration point between TanStack Router and TanStack Query.

---

## 6. The getRouter() Factory Pattern

TanStack Start requires an explicit router factory function rather than a module-level singleton. This is a deliberate design choice: a new router instance per SSR request prevents cross-request data leakage.

```tsx
// router.tsx
export function getRouter() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { staleTime: 60 * 1000 },
    },
  })

  const router = createRouter({
    routeTree,
    context: { queryClient, user: null },
    defaultPreload: 'intent',
    scrollRestoration: true,
    defaultErrorComponent: DefaultCatchBoundary,
    defaultNotFoundComponent: DefaultNotFound,
    defaultPendingComponent: DefaultSpinner,
    defaultPendingMs: 300,
    defaultPendingMinMs: 500,
  })

  return router
}
```

On the server, `getRouter()` is called once per request. On the client, it is called once at startup and the instance is reused. The framework handles this distinction — you write one factory, it behaves correctly in both environments.

Register the router type globally so TypeScript can infer it across the codebase:

```tsx
declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof getRouter>
  }
}
```

---

## 7. SSR + TanStack Query Integration

When loaders use `queryClient.ensureQueryData()`, the fetched data must be dehydrated into the HTML response and rehydrated on the client. Without this wiring, the client re-fetches data it already received — defeating SSR.

```tsx
import { setupRouterSsrQueryIntegration } from '@tanstack/react-router-ssr-query'

export function getRouter() {
  const queryClient = new QueryClient()

  const router = createRouter({
    routeTree,
    context: { queryClient },
  })

  setupRouterSsrQueryIntegration({
    router,
    queryClient,
    handleRedirects: true,
    wrapQueryClient: true,
  })

  return router
}
```

`setupRouterSsrQueryIntegration` hooks into the router's serialization lifecycle. On the server it dehydrates the query cache into the router state. On the client it rehydrates that state into the `QueryClient` before any components render. The result: components that call `useSuspenseQuery` with the same query key as the loader find data already in cache — no loading state, no network request.

---

## 8. Default Error, NotFound, and Pending Components

Set fallback UI components at the router level. Individual routes can override these defaults, but having sensible defaults means every route is covered without explicit configuration.

```tsx
const router = createRouter({
  routeTree,
  defaultErrorComponent: DefaultCatchBoundary,
  defaultNotFoundComponent: DefaultNotFound,
  defaultPendingComponent: DefaultSpinner,
  defaultPendingMs: 300,    // wait 300ms before showing pending UI
  defaultPendingMinMs: 500, // show pending UI for at least 500ms if shown
})
```

`defaultPendingMs` prevents spinner flicker on fast connections — the pending component only appears if loading takes longer than the threshold. `defaultPendingMinMs` prevents the spinner from flashing briefly on medium-speed connections — once shown, it stays for at least this duration.

Override on a specific route:

```tsx
export const Route = createFileRoute('/dashboard')({
  pendingComponent: DashboardSkeleton,
  errorComponent: DashboardError,
})
```

---

## 9. Scroll Restoration

Enable scroll restoration in the router config:

```tsx
const router = createRouter({
  routeTree,
  scrollRestoration: true,
})
```

With this enabled, the router saves scroll position when navigating away and restores it when navigating back — including browser back/forward. This works correctly with TanStack Router's loader-based data fetching because the router waits for data before restoring scroll position.

For custom scroll containers (virtualized lists, modal sheets), use the `useScrollRestoration` hook with a custom key:

```tsx
import { useScrollRestoration } from '@tanstack/react-router'

function VirtualList() {
  const scrollRef = useScrollRestoration({ key: 'virtual-list' })
  return <div ref={scrollRef}>...</div>
}
```

---

## 10. Active Link Styling

`Link` accepts `activeProps` and `inactiveProps` for declarative active state styling — no manual `pathname` comparison required.

```tsx
<Link
  to="/posts"
  activeProps={{ className: 'font-bold text-blue-600' }}
  inactiveProps={{ className: 'text-gray-500 hover:text-gray-700' }}
>
  Posts
</Link>
```

By default, a link is active if the current path starts with `to`. Use `activeOptions` for exact matching:

```tsx
<Link
  to="/"
  activeOptions={{ exact: true }}
  activeProps={{ className: 'font-bold' }}
>
  Home
</Link>
```

`activeOptions` also accepts `includeSearch: true` to require search params to match for the link to be considered active — useful for filter tabs that encode state in the URL.

---

## 11. Devtools

TanStack Router ships a devtools panel that visualizes the route tree, loader data, search params, and cache state. Add it to the root component during development.

```tsx
import { TanStackRouterDevtools } from '@tanstack/router-devtools'

function RootComponent() {
  return (
    <>
      <Outlet />
      <TanStackRouterDevtools position="bottom-right" />
    </>
  )
}
```

The devtools panel shows:
- The full route tree with active route highlighted
- Current loader data for each matched route
- Validated search params with their types
- Pending navigation state
- Router context values

Gate it behind an environment check to exclude from production builds:

```tsx
{import.meta.env.DEV && <TanStackRouterDevtools />}
```

---

## 12. createServerOnlyFn

`createServerFn` creates an HTTP endpoint callable from the client. `createServerOnlyFn` does not — it creates a function that can only be called from other server-side code (loaders, other server functions). Use it for internal helpers that should never be exposed as endpoints.

```tsx
import { createServerOnlyFn } from '@tanstack/react-start'

// No HTTP endpoint is created. Cannot be called from client code.
export const _getSessionUser = createServerOnlyFn(async () => {
  const session = await auth.api.getSession({
    headers: getWebRequest().headers,
  })
  return session?.user ?? null
})
```

Call it from a `beforeLoad` or `loader`:

```tsx
export const Route = createRootRoute({
  beforeLoad: async () => {
    const user = await _getSessionUser()
    return { user }
  },
})
```

The underscore prefix on `_getSessionUser` is a convention from the tanstarter template — it signals that the function is server-only and not a public API.

---

## 13. Import Protection

TanStack Start enforces server/client boundaries at the module level, stricter than Next.js.

| Mechanism | Behavior |
|---|---|
| `.server.ts` / `.server.tsx` suffix | Build error if imported from client code |
| `@tanstack/react-start/server-only` | Runtime guard — throws if module reaches client bundle |
| `createServerOnlyFn` | Function-level guard — no HTTP endpoint, server execution only |
| `createServerFn` | Creates HTTP endpoint — callable from client, but body runs on server |

Place database clients, secret-dependent utilities, and internal auth helpers in `.server.ts` files. The build will fail if any client-side import path reaches them — accidental secret leakage becomes a compile error rather than a runtime vulnerability.

```
lib/
  db.server.ts          // Drizzle client — cannot reach client bundle
  auth.server.ts        // Auth helpers — cannot reach client bundle
  utils.ts              // Shared utilities — available everywhere
```

This is the primary mechanism for enforcing the server/client boundary in TanStack Start. Rely on it rather than manual discipline.

---

## 13. Route Masking

Route masking lets you display a different URL in the browser than the actual route being rendered. This is useful for modal routes that should appear as overlays but have shareable URLs.

```tsx
<Link
  to="/photos/$id"
  params={{ id: photo.id }}
  mask={{ to: '/photos', unmaskOnReload: true }}
>
  <img src={photo.thumbnail} />
</Link>
```

When the user clicks, the browser shows `/photos` in the address bar but the router renders `/photos/$id`. If the user copies the URL and opens it in a new tab, they see the full photo page at `/photos/$id`. `unmaskOnReload: true` reveals the real URL on page reload.

This pattern replaces the Next.js `as` prop on `Link` (removed in the App Router) and the intercepting routes pattern for modals.

---

## Summary: Patterns by Category

| Category | Pattern | Key Benefit |
|---|---|---|
| Type safety | Type-safe navigation | Compile-time route validation |
| Type safety | Typed search params | Validated URL state |
| Performance | Preloading | Data ready before click |
| Lifecycle | `beforeLoad` vs `loader` | Separation of auth and data |
| Architecture | Router context | Type-safe dependency injection |
| Architecture | `getRouter()` factory | Safe SSR, no request leakage |
| SSR | Query integration | No double-fetch on hydration |
| DX | Devtools | Route tree and cache visibility |
| UX | Scroll restoration | Correct back/forward behavior |
| UX | Active link props | Declarative nav state |
| Security | `createServerOnlyFn` | No accidental HTTP exposure |
| Security | Import protection | Build-time secret boundary |
| UX | Route masking | Shareable modal URLs |
