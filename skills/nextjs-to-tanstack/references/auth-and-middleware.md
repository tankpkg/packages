# Authentication and Middleware

Sources: TanStack Start official docs, TanStack Router docs, mugnavo/tanstarter patterns, official start-basic-auth example

## Middleware: Next.js vs TanStack Start

Next.js provides a single `middleware.ts` file that runs at the edge before any route is matched. TanStack Start replaces this with two composable mechanisms: `beforeLoad` for per-route logic and `createMiddleware` for reusable server-side middleware.

### beforeLoad (primary replacement for most middleware use cases)

`beforeLoad` runs on the server during SSR and on the client during navigation. It is the correct place for auth checks, redirects, and injecting data into route context.

```tsx
export const Route = createFileRoute('/dashboard')({
  beforeLoad: async ({ context }) => {
    if (!context.auth?.user) {
      throw redirect({ to: '/login' })
    }
    return { user: context.auth.user }
  },
})
```

The return value of `beforeLoad` is merged into the route context and made available to child routes and the `loader`.

### createMiddleware (composable server middleware)

Use `createMiddleware` when you need reusable request/response manipulation or auth enforcement across multiple server functions or API routes.

```tsx
import { createMiddleware } from '@tanstack/react-start'

const authMiddleware = createMiddleware().server(async ({ next, context }) => {
  const user = await getUser()
  if (!user) {
    setResponseStatus(401)
    throw new Error('Unauthorized')
  }
  return next({ context: { user } })
})
```

Apply middleware to a server function:

```tsx
export const getSecretData = createServerFn({ method: 'GET' })
  .middleware([authMiddleware])
  .handler(async ({ context }) => {
    return { secret: `Hello ${context.user.name}` }
  })
```

Apply middleware to an API route:

```tsx
export const Route = createFileRoute('/api/users')({
  server: {
    middleware: [authMiddleware, loggerMiddleware],
    handlers: {
      GET: async ({ request }) => Response.json(users),
    },
  },
})
```

### Middleware composition

Chain middleware by passing a parent array to `.middleware([parent])`. The parent runs first; the child can inspect or modify the response after `next()` resolves.

```tsx
const parentMiddleware = createMiddleware().server(async ({ next }) => {
  const result = await next()
  result.response.headers.set('x-parent', 'true')
  return result
})

const childMiddleware = createMiddleware()
  .middleware([parentMiddleware])
  .server(async ({ next }) => {
    const result = await next()
    result.response.headers.set('x-child', 'true')
    return result
  })
```

### Comparison table

| Aspect | Next.js middleware.ts | TanStack beforeLoad | TanStack createMiddleware |
|---|---|---|---|
| Runs at | Edge (CDN level) | Server (SSR) + Client (navigation) | Server only |
| Scope | All routes via matcher config | Per-route | Per-route or per-server-function |
| Primary use | Geo-routing, A/B testing, auth redirect | Auth checks, redirects, context injection | Request/response manipulation, auth for server functions |
| Context passing | Headers and cookies only | Return value merges into route context | `next({ context: { ... } })` |
| Composable | No | No (use layout routes instead) | Yes, via `.middleware([parent])` |

There is no TanStack Start equivalent to Next.js edge middleware for CDN-level geo-routing or A/B testing. If your `middleware.ts` only performs auth redirects, `beforeLoad` on a layout route is a complete replacement.

---

## Context Inheritance

TanStack Router accumulates context down the route tree. Each `beforeLoad` return value is merged into the context object available to all descendant routes. This is fully type-safe and inferred — no manual type assertions required.

Inject auth at the root so every route has access:

```tsx
// src/routes/__root.tsx
const fetchUser = createServerFn({ method: 'GET' }).handler(async () => {
  const session = await useAppSession()
  if (!session.data.userEmail) return null
  return { email: session.data.userEmail }
})

export const Route = createRootRoute({
  beforeLoad: async () => {
    const user = await fetchUser()
    return { user }
  },
})
```

Any child route receives `context.user` with full type inference:

```tsx
// src/routes/_authed/dashboard.tsx
export const Route = createFileRoute('/_authed/dashboard')({
  beforeLoad: ({ context }) => {
    if (!context.user) throw redirect({ to: '/login' })
  },
})
```

No React Context, no prop drilling, no manual type casting. This is one of TanStack Router's most significant advantages over file-based routing in Next.js.

---

## Auth Guard Patterns

### Pattern A: Pathless layout route (recommended)

Group protected routes under a pathless layout directory. The layout's `beforeLoad` enforces auth for every route inside it.

```
src/routes/
├── _auth/
│   ├── route.tsx        ← enforces auth, redirects to /login
│   ├── dashboard.tsx    ← /dashboard (protected)
│   └── settings.tsx     ← /settings (protected)
├── _guest/
│   ├── route.tsx        ← redirects to /app if already authenticated
│   ├── login.tsx        ← /login
│   └── signup.tsx       ← /signup
└── __root.tsx
```

Auth guard layout:

```tsx
// src/routes/_auth/route.tsx
export const Route = createFileRoute('/_auth')({
  component: Outlet,
  beforeLoad: async ({ context }) => {
    if (!context.user) {
      throw redirect({ to: '/login' })
    }
    return { user: context.user }
  },
})
```

Guest guard (prevents authenticated users from accessing login/signup):

```tsx
// src/routes/_guest/route.tsx
export const Route = createFileRoute('/_guest')({
  component: Outlet,
  beforeLoad: async ({ context }) => {
    if (context.user) {
      throw redirect({ to: '/app' })
    }
  },
})
```

The pathless prefix (`_auth`, `_guest`) means these directories do not add a URL segment. `/dashboard` remains `/dashboard`, not `/_auth/dashboard`.

### Pattern B: Inline error component

Render a login form inline rather than redirecting. Useful for modal-style auth flows or when you want to preserve the current URL.

```tsx
export const Route = createFileRoute('/_authed')({
  beforeLoad: ({ context }) => {
    if (!context.user) throw new Error('Not authenticated')
  },
  errorComponent: ({ error }) => {
    if (error.message === 'Not authenticated') return <Login />
    throw error
  },
})
```

Throw the error rather than returning it so TanStack Router's error boundary catches it. Re-throw any error that is not the expected auth error to avoid swallowing unexpected failures.

### Comparison

| Pattern | Redirect behavior | URL preserved | Best for |
|---|---|---|---|
| Pathless layout + redirect | Hard redirect to /login | No | Standard auth flows |
| Inline error component | No redirect | Yes | Modal auth, embedded login |

---

## Session-Based Auth (Official Example)

TanStack Start ships a `useSession` utility for cookie-based sessions. The official `start-basic-auth` example demonstrates this pattern.

Session utility:

```tsx
// src/utils/session.ts
import { useSession } from '@tanstack/react-start/server'

type SessionUser = {
  userEmail: string
}

export function useAppSession() {
  return useSession<SessionUser>({
    password: process.env.SESSION_SECRET!,
  })
}
```

`SESSION_SECRET` must be at least 32 characters. Rotate it to invalidate all sessions.

Login server function:

```tsx
export const loginFn = createServerFn({ method: 'POST' })
  .inputValidator((d: { email: string; password: string }) => d)
  .handler(async ({ data }) => {
    const user = await verifyCredentials(data.email, data.password)
    if (!user) throw new Error('Invalid credentials')

    const session = await useAppSession()
    await session.update({ userEmail: user.email })
    throw redirect({ href: '/dashboard' })
  })
```

Logout server function:

```tsx
export const logoutFn = createServerFn({ method: 'POST' }).handler(async () => {
  const session = await useAppSession()
  await session.clear()
  throw redirect({ href: '/login' })
})
```

Read session in root `beforeLoad`:

```tsx
const fetchUser = createServerFn({ method: 'GET' }).handler(async () => {
  const session = await useAppSession()
  if (!session.data.userEmail) return null
  return { email: session.data.userEmail }
})
```

---

## Better Auth Integration (tanstarter Pattern)

Better Auth is the most commonly used third-party auth library in the TanStack Start ecosystem. The `tanstarter` starter template demonstrates the recommended integration.

Server-side auth config. Import `'@tanstack/react-start/server-only'` to prevent this module from being bundled into the client:

```tsx
// src/lib/auth/auth.ts
import '@tanstack/react-start/server-only'
import { betterAuth } from 'better-auth/minimal'
import { tanstackStartCookies } from 'better-auth/tanstack-start'

export const auth = betterAuth({
  plugins: [tanstackStartCookies()],
  session: {
    cookieCache: { enabled: true, maxAge: 5 * 60 },
  },
  socialProviders: {
    github: {
      clientId: env.GITHUB_CLIENT_ID,
      clientSecret: env.GITHUB_CLIENT_SECRET,
    },
  },
})
```

Catch-all API route to handle all Better Auth endpoints:

```tsx
// src/routes/api/auth/$.ts
export const Route = createFileRoute('/api/auth/$')({
  server: {
    handlers: {
      GET: ({ request }) => auth.handler(request),
      POST: ({ request }) => auth.handler(request),
    },
  },
})
```

The `$` segment is a wildcard that matches any path under `/api/auth/`. Better Auth routes its own sub-paths internally.

Client-side auth instance (safe to import anywhere):

```tsx
// src/lib/auth/auth-client.ts
import { createAuthClient } from 'better-auth/react'

export const authClient = createAuthClient({
  baseURL: import.meta.env.VITE_APP_URL,
})
```

---

## TanStack Query + Auth

When using TanStack Query alongside TanStack Router, wrap the auth check in `queryOptions` so the result is cached and shared across the tree.

```tsx
// src/lib/auth/queries.ts
import { queryOptions } from '@tanstack/react-query'

export const authQueryOptions = () =>
  queryOptions({
    queryKey: ['auth'],
    queryFn: () => $getUser(),
  })
```

Use `ensureQueryData` in the root `beforeLoad` to populate the cache before rendering:

```tsx
// src/routes/__root.tsx
export const Route = createRootRouteWithContext<{
  queryClient: QueryClient
  user: User | null
}>()({
  beforeLoad: async ({ context }) => {
    const user = await context.queryClient.ensureQueryData({
      ...authQueryOptions(),
      revalidateIfStale: true,
    })
    return { user }
  },
})
```

Child routes can then call `useQuery(authQueryOptions())` and receive the already-cached result with no additional network request.

---

## Typed Router Context

Declare the shape of the router context once at the root. TypeScript infers the merged context type in all child routes.

```tsx
// src/routes/__root.tsx
import { createRootRouteWithContext } from '@tanstack/react-router'
import type { QueryClient } from '@tanstack/react-query'

type RouterContext = {
  queryClient: QueryClient
  user: User | null
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootComponent,
  beforeLoad: async ({ context }) => {
    const user = await fetchUser()
    return { user }
  },
})
```

Provide the initial context when creating the router:

```tsx
// src/router.tsx
const router = createRouter({
  routeTree,
  context: {
    queryClient,
    user: null,  // overwritten by root beforeLoad on first render
  },
})
```

Declare the router type globally so `useRouter`, `useRouteContext`, and `Link` are all typed:

```tsx
// src/routerTypes.ts
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
```

---

## Common Gotchas

### Auth library base URL

Auth libraries that relied on Next.js's implicit base URL resolution require an explicit `baseURL` in TanStack Start. Set it via an environment variable and pass it to both the server and client auth instances.

```tsx
export const auth = betterAuth({
  baseURL: process.env.APP_URL,
  // ...
})
```

### Theme injection

`next-themes` does not work in TanStack Start. Use `ScriptOnce` from `@tanstack/react-router` to inject a theme script before hydration and avoid flash of unstyled content.

```tsx
import { ScriptOnce } from '@tanstack/react-router'

function RootDocument({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <head>
        <ScriptOnce>{`
          const theme = localStorage.getItem('theme') || 'system'
          document.documentElement.setAttribute('data-theme', theme)
        `}</ScriptOnce>
      </head>
      <body>{children}</body>
    </html>
  )
}
```

### Cookie forwarding

When calling server functions from within other server functions, cookies are not automatically forwarded. Use `setResponseHeader` or the `tanstackStartCookies()` Better Auth plugin to ensure session cookies propagate correctly.

### Redirect inside server functions

Always use `throw redirect(...)` rather than `return redirect(...)` inside `beforeLoad` and server function handlers. Returning a redirect object does not halt execution; throwing does.

### Server-only imports

Any module that imports database clients, secret keys, or auth server instances must include `import '@tanstack/react-start/server-only'` at the top. Without this guard, Vite may bundle server code into the client, exposing secrets.
