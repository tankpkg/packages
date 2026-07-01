# RPC and Client

Sources: Hono official documentation (hono.dev, 2024-2026), honojs/hono GitHub repository, Catalin Pit (Hono RPC in Monorepos, 2025)

Covers: hc client setup, type inference from server to client, InferRequestType/InferResponseType, path and query parameters in RPC, status-code-based typing, ApplyGlobalResponse, $url/$path helpers, monorepo patterns, IDE performance tips, and large application architecture.

## Core Concept

Hono RPC shares API type specifications between server and client at compile time. The server defines routes with validators, exports the app type, and the client imports it to get fully typed API calls with zero runtime overhead.

```
Server: Hono app + Zod validators -> export typeof app
Client: hc<AppType>() -> typed methods matching every route
```

No code generation. No schema files. Pure TypeScript type inference.

## Server Setup

Define routes with validators and capture the route chain in a variable:

```typescript
import { Hono } from 'hono'
import { zValidator } from '@hono/zod-validator'
import { z } from 'zod'

const app = new Hono()

const route = app
  .get('/posts', (c) => {
    return c.json({ posts: [{ id: '1', title: 'Hello' }] }, 200)
  })
  .post(
    '/posts',
    zValidator('json', z.object({
      title: z.string(),
      body: z.string(),
    })),
    (c) => {
      const data = c.req.valid('json')
      return c.json({ id: crypto.randomUUID(), ...data }, 201)
    }
  )
  .get('/posts/:id', (c) => {
    return c.json({ id: c.req.param('id'), title: 'Post' }, 200)
  })

export default app
export type AppType = typeof route
```

Chain handlers directly (`.get().post().get()`) to preserve type information. Separate `app.get(...)` calls lose the accumulated type.

## Client Setup

```typescript
import { hc } from 'hono/client'
import type { AppType } from './server'

const client = hc<AppType>('http://localhost:8787/')
```

Call methods matching the route pattern:

```typescript
// GET /posts
const res = await client.posts.$get()
const data = await res.json()
// data type: { posts: { id: string; title: string }[] }

// POST /posts
const res2 = await client.posts.$post({
  json: { title: 'Hello', body: 'World' },
})
const created = await res2.json()
// created type: { id: string; title: string; body: string }
```

## Path Parameters

Access parameterized routes with bracket notation:

```typescript
// GET /posts/:id
const res = await client.posts[':id'].$get({
  param: { id: '123' },
})

// Multiple params: /posts/:postId/comments/:commentId
const res = await client.posts[':postId'].comments[':commentId'].$get({
  param: { postId: '1', commentId: '42' },
})
```

All param values must be strings, even for numeric IDs. The server-side validator handles coercion.

## Query Parameters

```typescript
// Server
const route = app.get(
  '/posts',
  zValidator('query', z.object({
    page: z.coerce.number().optional(),
    limit: z.coerce.number().optional(),
  })),
  (c) => {
    const { page, limit } = c.req.valid('query')
    return c.json({ page, limit })
  }
)

// Client — query values must be strings
const res = await client.posts.$get({
  query: { page: '1', limit: '20' },
})
```

## Request Headers

```typescript
// Per-request headers
const res = await client.posts.$get({}, {
  headers: { 'X-Custom': 'value' },
})

// Global headers for all requests
const client = hc<AppType>('http://localhost:8787/', {
  headers: { Authorization: 'Bearer TOKEN' },
})
```

## Cookies

Enable cookie sending with credentials:

```typescript
const client = hc<AppType>('http://localhost:8787/', {
  init: { credentials: 'include' },
})
```

## Status-Code-Based Typing

Specify explicit status codes in `c.json()` to get discriminated response types:

```typescript
// Server
const route = app.get('/posts/:id',
  zValidator('param', z.object({ id: z.string() })),
  async (c) => {
    const post = await getPost(c.req.valid('param').id)
    if (!post) {
      return c.json({ error: 'Not found' }, 404)
    }
    return c.json({ post }, 200)
  }
)

// Client
const res = await client.posts[':id'].$get({ param: { id: '123' } })

if (res.status === 404) {
  const data = await res.json() // { error: string }
}
if (res.ok) {
  const data = await res.json() // { post: Post }
}
```

Do NOT use `c.notFound()` in RPC routes — it returns `unknown` type. Always use `c.json()` with explicit status codes.

## InferRequestType and InferResponseType

Extract types from route definitions for use in frontend code:

```typescript
import type { InferRequestType, InferResponseType } from 'hono/client'

const $post = client.posts.$post

// Input type
type CreatePostInput = InferRequestType<typeof $post>['json']
// { title: string; body: string }

// Response type (all status codes)
type PostResponse = InferResponseType<typeof $post>
// { id: string; title: string; body: string }

// Response type (specific status code)
type PostResponse200 = InferResponseType<typeof $post, 200>
```

## ApplyGlobalResponse

Merge global error handler types into all routes:

```typescript
import type { ApplyGlobalResponse } from 'hono/client'

const app = new Hono()
  .get('/users', (c) => c.json({ users: [] }, 200))
  .onError((err, c) => c.json({ error: err.message }, 500))

type AppWithErrors = ApplyGlobalResponse<typeof app, {
  500: { json: { error: string } }
  401: { json: { error: string; message: string } }
}>

const client = hc<AppWithErrors>('http://localhost')
```

## $url() and $path() Helpers

Get URLs and paths without making requests:

```typescript
const client = hc<AppType>('http://localhost:8787/')

// Full URL object (requires absolute base URL)
const url = client.posts[':id'].$url({ param: { id: '123' } })
console.log(url.pathname) // /posts/123

// Path string (works with any base URL)
const path = client.posts.$path({ query: { page: '1' } })
console.log(path) // /posts?page=1
```

Useful for integrating with SWR or React Query as cache keys.

## File Uploads

```typescript
// Client
const res = await client.upload.$post({
  form: {
    file: new File([blob], 'photo.png', { type: 'image/png' }),
    description: 'Profile photo',
  },
})

// Server
const route = app.post('/upload',
  zValidator('form', z.object({
    file: z.instanceof(File),
    description: z.string().optional(),
  })),
  async (c) => {
    const { file } = c.req.valid('form')
    return c.json({ size: file.size })
  }
)
```

## Custom fetch

Override the fetch function for service bindings or testing:

```typescript
// Cloudflare Service Bindings
const client = hc<AppType>('http://localhost', {
  fetch: c.env.AUTH_SERVICE.fetch.bind(c.env.AUTH_SERVICE),
})

// Custom query serializer
const client = hc<AppType>('http://localhost', {
  buildSearchParams: (query) => {
    const params = new URLSearchParams()
    for (const [k, v] of Object.entries(query)) {
      if (Array.isArray(v)) {
        v.forEach((item) => params.append(`${k}[]`, item))
      } else if (v !== undefined) {
        params.set(k, v)
      }
    }
    return params
  },
})
```

## Large Application Architecture

Split into sub-apps and chain route mounting for type inference:

```typescript
// authors.ts
import { Hono } from 'hono'
const app = new Hono()
  .get('/', (c) => c.json('list authors'))
  .post('/', (c) => c.json('create author', 201))
  .get('/:id', (c) => c.json(`get ${c.req.param('id')}`))
export default app

// books.ts — same pattern

// index.ts
import authors from './authors'
import books from './books'

const app = new Hono()
const routes = app.route('/authors', authors).route('/books', books)

export default app
export type AppType = typeof routes
```

Chain `.route()` calls on the same variable so types accumulate.

## IDE Performance Tips

RPC type inference slows IDEs with many routes. Mitigations in priority order:

### 1. Compile Types First (Recommended)

```typescript
// client-factory.ts
import { app } from './app'
import { hc } from 'hono/client'

export type Client = ReturnType<typeof hc<typeof app>>
export const hcWithType = (...args: Parameters<typeof hc>): Client =>
  hc<typeof app>(...args)
```

Compile with `tsc`, then import `hcWithType` in frontend code. The type is pre-calculated.

### 2. Split Clients Per Sub-App

```typescript
import type { AuthorsApp } from './authors'
import type { BooksApp } from './books'

const authorsClient = hc<AuthorsApp>('/authors')
const booksClient = hc<BooksApp>('/books')
```

### 3. Ensure Version Consistency

Mismatched Hono versions between server and client packages cause "Type instantiation is excessively deep" errors. Pin identical versions everywhere.

### 4. Use TypeScript Project References

In monorepos, configure `tsconfig.json` project references so the client project can reference server types without re-instantiating them.

## Using with React Query / SWR

```typescript
import useSWR from 'swr'
import type { InferRequestType } from 'hono/client'

const $get = client.posts.$get

const fetcher = (arg: InferRequestType<typeof $get>) => async () => {
  const res = await $get(arg)
  return res.json()
}

function Posts() {
  const { data } = useSWR('posts', fetcher({ query: { page: '1' } }))
  return <div>{data?.posts.map((p) => <p key={p.id}>{p.title}</p>)}</div>
}
```

## parseResponse Helper

Type-safe response parsing with automatic error throwing:

```typescript
import { parseResponse, DetailedError } from 'hono/client'

const result = await parseResponse(client.posts.$get()).catch(
  (e: DetailedError) => console.error(e)
)
```
