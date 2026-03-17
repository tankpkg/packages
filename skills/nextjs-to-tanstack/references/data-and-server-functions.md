# Data Fetching and Server Functions

Sources: TanStack Start official docs, TanStack Query docs, Inngest migration case study, official TanStack Start examples

## Mental Model Shift

Next.js is server-first. Data fetching is implicit — async Server Components fetch data inline, and `getServerSideProps` runs before the page renders. The framework decides what runs on the server based on file location and directives.

TanStack Start is client-first with explicit server capabilities. Data fetching happens in route `loader` functions and `createServerFn()` calls. There are no React Server Components. The server/client boundary is declared explicitly, not inferred from file structure or `'use server'` directives.

This distinction matters for migration: every implicit data fetch in a Next.js Server Component must become an explicit loader or server function call.

## Route Loaders

Route loaders replace both `getServerSideProps` (Pages Router) and async Server Components (App Router). Define a `loader` on the route, then read the result with `Route.useLoaderData()`.

**Before — Next.js App Router (implicit Server Component):**

```tsx
export default async function PostsPage() {
  const posts = await db.post.findMany()
  return <ul>{posts.map(p => <li key={p.id}>{p.title}</li>)}</ul>
}
```

**Before — Next.js Pages Router:**

```tsx
export async function getServerSideProps() {
  const posts = await db.post.findMany()
  return { props: { posts } }
}

export default function PostsPage({ posts }) {
  return <ul>{posts.map(p => <li key={p.id}>{p.title}</li>)}</ul>
}
```

**After — TanStack Start:**

```tsx
export const Route = createFileRoute('/posts')({
  loader: async () => fetchPosts(),
  component: PostsPage,
})

function PostsPage() {
  const posts = Route.useLoaderData()
  return <ul>{posts.map(p => <li key={p.id}>{p.title}</li>)}</ul>
}
```

The loader runs on the server during SSR and on the client during client-side navigation. `Route.useLoaderData()` is fully typed — the return type of the loader is inferred automatically with no manual annotation required.

**Comparison:**

| Aspect | TanStack Start | Next.js App Router | Next.js Pages Router |
|--------|---------------|--------------------|----------------------|
| Data fetching | Explicit `loader` function | Implicit async Server Components | `getServerSideProps` |
| Type safety | Full inference via `Route.useLoaderData()` | Manual typing | Manual typing |
| Client navigation | Loader re-runs on client | Server component re-renders | Client-side fetch |
| Caching | Manual (TanStack Query recommended) | React cache + fetch cache | Manual |
| Co-location | Loader defined on route object | Data fetch inside component | Separate export |

## createServerFn — Replacing Server Actions

`createServerFn()` is the TanStack Start equivalent of Next.js Server Actions. It creates a typed RPC function that runs exclusively on the server but can be called from anywhere — loaders, components, or other server functions.

**Basic pattern:**

```tsx
import { createServerFn } from '@tanstack/react-start'

// GET — for reads
export const getPosts = createServerFn({ method: 'GET' }).handler(async () => {
  return db.post.findMany()
})

// POST — for mutations
export const createPost = createServerFn({ method: 'POST' })
  .inputValidator((data: { title: string; body: string }) => data)
  .handler(async ({ data }) => {
    return db.post.create({ data })
  })
```

**Before — Next.js Server Action:**

```tsx
'use server'

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string
  const body = formData.get('body') as string
  return db.post.create({ data: { title, body } })
}
```

**After — TanStack Start server function:**

```tsx
import { createServerFn } from '@tanstack/react-start'

export const createPost = createServerFn({ method: 'POST' })
  .inputValidator((data: { title: string; body: string }) => data)
  .handler(async ({ data }) => {
    return db.post.create({ data })
  })
```

**Comparison:**

| Aspect | TanStack `createServerFn` | Next.js Server Actions |
|--------|--------------------------|------------------------|
| Syntax | Explicit `createServerFn()` wrapper | `'use server'` directive |
| HTTP method | Configurable (GET/POST) | Always POST |
| Input validation | `.inputValidator()` chain | Manual |
| Middleware | `.middleware([...])` chain | Separate `middleware.ts` |
| Callable from | Loaders, components, other server fns | Components, form actions |
| Type inference | Full end-to-end | Manual or inferred from action signature |

## Input Validation with Zod

Pass a Zod schema to `.inputValidator()` for runtime validation and full TypeScript inference. The validated, typed data is available as `data` in the handler.

```tsx
import { z } from 'zod'
import { createServerFn } from '@tanstack/react-start'

const CreatePostSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  body: z.string().min(10, 'Body must be at least 10 characters'),
})

export const createPost = createServerFn({ method: 'POST' })
  .inputValidator(CreatePostSchema)
  .handler(async ({ data }) => {
    // data is typed as { title: string; body: string }
    return db.post.create({ data })
  })
```

Validation errors thrown by Zod surface as 422 responses. Handle them in the calling component or let the error boundary catch them.

## Calling Server Functions

**From a loader:**

```tsx
export const Route = createFileRoute('/posts')({
  loader: () => getPosts(),
})
```

**From a component:**

```tsx
function CreatePostForm() {
  const router = useRouter()

  async function handleSubmit(formData: FormData) {
    await createPost({
      data: {
        title: formData.get('title') as string,
        body: formData.get('body') as string,
      },
    })
    router.invalidate() // re-runs all active loaders
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); handleSubmit(new FormData(e.currentTarget)) }}>
      <input name="title" />
      <textarea name="body" />
      <button type="submit">Create</button>
    </form>
  )
}
```

`router.invalidate()` is the TanStack Start equivalent of `revalidatePath()`. It signals all active loaders to re-run, refreshing stale data without a full page reload.

## Server Context and Request Handling

Access request headers, set response headers, and control status codes using helpers from `@tanstack/react-start/server`. These are only valid inside server function handlers.

```tsx
import { createServerFn } from '@tanstack/react-start'
import {
  getRequestHeader,
  setResponseHeaders,
  setResponseStatus,
} from '@tanstack/react-start/server'

export const getProtectedData = createServerFn({ method: 'GET' }).handler(async () => {
  const authHeader = getRequestHeader('Authorization')

  if (!authHeader) {
    setResponseStatus(401)
    throw new Error('Unauthorized')
  }

  setResponseHeaders(new Headers({ 'Cache-Control': 'max-age=300' }))
  return fetchData()
})
```

Available server context helpers:

| Helper | Purpose |
|--------|---------|
| `getRequest()` | Access the raw Request object |
| `getRequestHeader(name)` | Read a specific request header |
| `setResponseHeaders(headers)` | Set response headers |
| `setResponseStatus(code)` | Set the HTTP status code |
| `getCookie(name)` | Read a cookie by name |
| `setCookie(name, value, opts)` | Set a cookie |

## Error Handling in Server Functions

Throw `notFound()` or `redirect()` from `@tanstack/react-router` inside server function handlers. TanStack Router intercepts these and handles them correctly during both SSR and client navigation.

```tsx
import { createServerFn } from '@tanstack/react-start'
import { redirect, notFound } from '@tanstack/react-router'

export const getPost = createServerFn({ method: 'GET' })
  .inputValidator((d: { id: string }) => d)
  .handler(async ({ data }) => {
    const post = await db.post.findUnique({ where: { id: data.id } })
    if (!post) throw notFound()
    return post
  })

export const requireAuth = createServerFn({ method: 'GET' }).handler(async () => {
  const user = await getCurrentUser()
  if (!user) throw redirect({ to: '/login' })
  return user
})
```

For application errors (validation failures, business logic errors), throw a standard `Error` or a custom error class. Catch these in the component or route `errorComponent`.

## TanStack Query Integration

The recommended pattern for production apps combines route loaders with TanStack Query. The loader pre-fetches data on the server using `queryClient.ensureQueryData()`, and the component reads it with `useSuspenseQuery()`. This gives you server-side pre-fetching plus client-side caching, background refetching, and stale-while-revalidate behavior.

**Setup — add queryClient to router context:**

```tsx
// src/router.tsx
import { QueryClient } from '@tanstack/react-query'

export function createRouter() {
  const queryClient = new QueryClient()

  return createTanStackRouter({
    routeTree,
    context: { queryClient },
    defaultPreload: 'intent',
  })
}
```

**Define query options once, use everywhere:**

```tsx
// src/utils/posts.ts
import { queryOptions } from '@tanstack/react-query'
import { getPosts } from './posts.server'

export const postsQueryOptions = () =>
  queryOptions({
    queryKey: ['posts'],
    queryFn: () => getPosts(),
  })
```

**Route loader pre-fetches, component reads from cache:**

```tsx
export const Route = createFileRoute('/posts')({
  loader: ({ context: { queryClient } }) =>
    queryClient.ensureQueryData(postsQueryOptions()),
  component: PostsPage,
})

function PostsPage() {
  const { data: posts } = useSuspenseQuery(postsQueryOptions())
  // Data is already in cache from the loader — no loading state on first render
  // TanStack Query handles background refetching and cache invalidation
}
```

**Mutation with cache invalidation:**

```tsx
function CreatePostForm() {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (data: { title: string; body: string }) =>
      createPost({ data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })
}
```

This pattern replaces Next.js's `revalidatePath` / `revalidateTag` for client-driven cache invalidation.

## Mutations and router.invalidate()

For simpler cases that do not need TanStack Query's caching, call `router.invalidate()` after a mutation. This re-runs all active loaders and refreshes the UI.

```tsx
function CounterPage() {
  const router = useRouter()
  const count = Route.useLoaderData()

  return (
    <button
      onClick={async () => {
        await incrementCount({ data: 1 })
        router.invalidate()
      }}
    >
      Count: {count}
    </button>
  )
}
```

Use `router.invalidate()` for simple loader-based data. Use TanStack Query invalidation when you need fine-grained cache control, optimistic updates, or background refetching.

## Deferred and Streaming Data

Await critical data that must be present before the page renders. Return non-critical data as an unawaited promise — TanStack Start streams it to the client after navigation completes.

```tsx
export const Route = createFileRoute('/dashboard')({
  loader: async () => ({
    user: await getUser(),             // blocks navigation until resolved
    notifications: getNotifications(), // streams in after navigation
  }),
  component: Dashboard,
})

function Dashboard() {
  const { user, notifications } = Route.useLoaderData()

  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      <Suspense fallback={<Spinner />}>
        <Await promise={notifications}>
          {(data) => <NotificationList items={data} />}
        </Await>
      </Suspense>
    </div>
  )
}
```

This mirrors Next.js's `loading.tsx` + Suspense pattern but is explicit at the data level rather than the route level.

## File Organization Convention

Separate server-only logic from shared utilities using the `.server.ts` naming convention. Files ending in `.server.ts` cannot be imported in client bundles — the build will throw an error if you try.

```
src/utils/
├── posts.ts            # createServerFn wrappers — safe to import anywhere
├── posts.server.ts     # Server-only helpers: DB queries, internal logic
└── schemas.ts          # Shared Zod schemas — client-safe
```

**posts.server.ts — raw DB access, never imported by client code:**

```ts
// src/utils/posts.server.ts
export async function fetchPostsFromDb() {
  return db.post.findMany({ orderBy: { createdAt: 'desc' } })
}
```

**posts.ts — server function wrappers, importable anywhere:**

```ts
// src/utils/posts.ts
import { createServerFn } from '@tanstack/react-start'
import { fetchPostsFromDb } from './posts.server'

export const getPosts = createServerFn({ method: 'GET' }).handler(() =>
  fetchPostsFromDb()
)
```

This pattern prevents accidental leakage of database credentials or internal logic to the client bundle.

## What Has No Direct Equivalent

Some Next.js caching primitives have no counterpart in TanStack Start. The table below lists the gaps and recommended alternatives.

| Next.js Feature | TanStack Start Status | Recommended Alternative |
|-----------------|----------------------|-------------------------|
| `unstable_cache` / `use cache` | No equivalent | TanStack Query for client-side caching |
| `revalidatePath` / `revalidateTag` | No equivalent | `router.invalidate()` or TanStack Query invalidation |
| `fetch()` with `cache: 'force-cache'` | No equivalent | TanStack Query with `staleTime: Infinity` |
| ISR (`revalidate: 60`) | Basic support, less mature | TanStack Query with `staleTime` + background refetch |
| React Server Components | Not supported | Route loaders + `createServerFn()` |
| `next/headers` (`cookies()`, `headers()`) | Replaced | `getCookie()`, `getRequestHeader()` from `@tanstack/react-start/server` |
| `generateStaticParams` | Partial support | Static prerendering config on route |

The absence of `unstable_cache` and tag-based revalidation is the most significant gap for content-heavy applications. TanStack Query's `staleTime` and `gcTime` options cover most use cases, but server-driven cache invalidation (e.g., invalidating all pages that reference a specific post after a CMS update) requires a custom solution or a third-party caching layer.
