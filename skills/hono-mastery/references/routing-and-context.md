# Routing and Context API

Sources: Hono official documentation (hono.dev, 2024-2026), honojs/hono GitHub repository

Covers: routing patterns (basic, params, regex, wildcards, grouping, chaining, basePath, priority), Context object (c.req, c.json, c.html, c.text, c.redirect, c.set/get, c.var, c.env, c.header, c.status), request handling, and response helpers.

## Basic Routing

Register handlers for HTTP methods directly on the Hono instance:

```typescript
import { Hono } from 'hono'
const app = new Hono()

app.get('/', (c) => c.text('GET /'))
app.post('/', (c) => c.text('POST /'))
app.put('/', (c) => c.text('PUT /'))
app.delete('/', (c) => c.text('DELETE /'))

// Any HTTP method
app.all('/hello', (c) => c.text('Any method'))

// Custom HTTP method
app.on('PURGE', '/cache', (c) => c.text('PURGE'))

// Multiple methods on same path
app.on(['PUT', 'DELETE'], '/post', (c) => c.text('PUT or DELETE'))

// Multiple paths for same handler
app.on('GET', ['/hello', '/ja/hello', '/en/hello'], (c) => c.text('Hello'))
```

## Path Parameters

### Named Parameters

```typescript
app.get('/user/:name', (c) => {
  const name = c.req.param('name') // TypeScript infers string type
  return c.json({ name })
})

// Multiple params — destructure all at once
app.get('/posts/:id/comment/:commentId', (c) => {
  const { id, commentId } = c.req.param()
  return c.json({ id, commentId })
})
```

### Optional Parameters

```typescript
// Matches both /api/animal and /api/animal/dog
app.get('/api/animal/:type?', (c) => c.text('Animal!'))
```

### Regex-Constrained Parameters

Restrict parameter format inline with curly-brace regex:

```typescript
app.get('/post/:date{[0-9]+}/:title{[a-z]+}', (c) => {
  const { date, title } = c.req.param()
  return c.json({ date, title })
})

// Match paths containing slashes
app.get('/posts/:filename{.+\\.png}', (c) => {
  const { filename } = c.req.param()
  return c.json({ filename })
})
```

### Wildcard Routes

```typescript
app.get('/wild/*/card', (c) => c.text('Wildcard matched'))
```

## Route Chaining

Chain methods on the same path for cleaner code and RPC type inference:

```typescript
app
  .get('/endpoint', (c) => c.text('GET'))
  .post((c) => c.text('POST'))
  .delete((c) => c.text('DELETE'))
```

Chaining is critical for RPC — types propagate through the chain. Breaking the chain into separate `app.get()` calls loses type inference for the hc client.

## Route Grouping

### Sub-Apps with route()

Create modular sub-applications and mount them:

```typescript
const books = new Hono()
books.get('/', (c) => c.json('list books'))       // GET /books
books.get('/:id', (c) => c.json(`get ${c.req.param('id')}`)) // GET /books/:id
books.post('/', (c) => c.json('create book'))      // POST /books

const app = new Hono()
app.route('/books', books)
```

### basePath

Set a prefix for all routes in an instance:

```typescript
const api = new Hono().basePath('/api')
api.get('/book', (c) => c.json('list')) // GET /api/book
```

### Grouping Without Changing Base

```typescript
const book = new Hono()
book.get('/book', (c) => c.text('List Books'))

const user = new Hono().basePath('/user')
user.get('/', (c) => c.text('List Users'))

const app = new Hono()
app.route('/', book) // /book
app.route('/', user) // /user
```

### Grouping Order Matters

Mount routes AFTER defining handlers in sub-apps. Mounting before handlers are registered returns 404:

```typescript
// Correct order
const sub = new Hono()
sub.get('/hi', (c) => c.text('hi'))
app.route('/sub', sub) // Works: GET /sub/hi -> 200

// Wrong order
app.route('/sub', sub) // sub has no routes yet
sub.get('/hi', (c) => c.text('hi'))
// GET /sub/hi -> 404
```

## Routing Priority

Handlers execute in registration order. The first matching handler returns the response:

```typescript
app.get('/book/a', (c) => c.text('specific'))  // GET /book/a -> 'specific'
app.get('/book/:slug', (c) => c.text('generic')) // GET /book/b -> 'generic'
```

Register static paths before parameterized paths. Register middleware above handlers. Register fallback handlers below specific ones:

```typescript
app.use(logger())                             // Middleware first
app.get('/bar', (c) => c.text('bar'))         // Specific routes
app.get('*', (c) => c.text('fallback'))       // Fallback last
```

## Hostname-Based Routing

Route by hostname using a custom `getPath`:

```typescript
const app = new Hono({
  getPath: (req) => '/' + req.headers.get('host') + new URL(req.url).pathname,
})

app.get('/www1.example.com/hello', (c) => c.text('hello www1'))
app.get('/www2.example.com/hello', (c) => c.text('hello www2'))
```

## Context Object

The Context (`c`) object is created per-request and provides all request/response interaction.

### Response Helpers

| Method | Content-Type | Usage |
|--------|-------------|-------|
| `c.text(str)` | `text/plain` | Plain text responses |
| `c.json(obj)` | `application/json` | JSON API responses |
| `c.html(str)` | `text/html` | HTML responses |
| `c.redirect(url, status?)` | — | Redirect (default 302) |
| `c.body(data)` | Manual | Raw response body |
| `c.notFound()` | — | Trigger 404 handler |

### Setting Status and Headers

```typescript
app.post('/posts', (c) => {
  c.status(201)
  c.header('X-Request-Id', crypto.randomUUID())
  return c.json({ message: 'Created' })
})

// Or pass status and headers inline
app.get('/', (c) => {
  return c.json({ ok: true }, 200, { 'Cache-Control': 'max-age=60' })
})
```

### Request Object (c.req)

`c.req` is a `HonoRequest` wrapping the standard `Request`:

```typescript
app.get('/api', (c) => {
  const userAgent = c.req.header('User-Agent')
  const method = c.req.method
  const url = c.req.url
  const query = c.req.query('page')       // Single query param
  const queries = c.req.queries('tags')    // Array of values
  return c.json({ userAgent, method, url, query })
})

// Parse body
app.post('/api', async (c) => {
  const body = await c.req.json()          // JSON body
  const formData = await c.req.formData()  // Form data
  const text = await c.req.text()          // Raw text
  return c.json(body)
})
```

### Context Variables (c.set / c.get / c.var)

Pass data between middleware and handlers within a single request:

```typescript
type Variables = {
  user: { id: string; name: string }
}

const app = new Hono<{ Variables: Variables }>()

app.use(async (c, next) => {
  c.set('user', { id: '1', name: 'Alice' })
  await next()
})

app.get('/', (c) => {
  const user = c.get('user')    // Type: { id: string; name: string }
  // Or use c.var shorthand:
  const name = c.var.user.name
  return c.json({ user })
})
```

Variables live only for the current request. They are not shared across requests.

### Environment Bindings (c.env)

Access runtime-specific bindings (Cloudflare Workers KV, D1, R2, secrets):

```typescript
type Bindings = {
  DB: D1Database
  KV: KVNamespace
  SECRET: string
}

const app = new Hono<{ Bindings: Bindings }>()

app.get('/', async (c) => {
  const result = await c.env.DB.prepare('SELECT * FROM users').all()
  return c.json(result)
})
```

See `references/cloudflare-integration.md` for full Bindings patterns.

### Execution Context (c.executionCtx)

On Cloudflare Workers, access `waitUntil` for background tasks:

```typescript
app.get('/', async (c) => {
  c.executionCtx.waitUntil(
    c.env.KV.put('last-visit', new Date().toISOString())
  )
  return c.text('OK')
})
```

### Renderer (c.setRenderer / c.render)

Set a layout template in middleware, use it in handlers:

```typescript
app.use(async (c, next) => {
  c.setRenderer((content) => {
    return c.html(`<html><body>${content}</body></html>`)
  })
  await next()
})

app.get('/', (c) => c.render('<h1>Hello</h1>'))
// Output: <html><body><h1>Hello</h1></body></html>
```

### Accessing the Raw Response

Modify the Response after middleware chain completes:

```typescript
app.use(async (c, next) => {
  await next()
  c.res.headers.append('X-Response-Time', '42ms')
})
```

### Error Object

Access caught errors in middleware:

```typescript
app.use(async (c, next) => {
  await next()
  if (c.error) {
    console.error('Handler threw:', c.error.message)
  }
})
```

## Strict Mode

By default, Hono distinguishes `/hello` from `/hello/`. Disable strict mode to treat them as equivalent:

```typescript
const app = new Hono({ strict: false })
```

## Router Selection

Hono ships multiple router implementations:

| Router | Best For |
|--------|----------|
| `SmartRouter` (default) | Automatic selection — good default |
| `RegExpRouter` | Maximum performance — single regex match |
| `LinearRouter` | Fast registration, per-request init (edge cold starts) |
| `PatternRouter` | Smallest bundle size |

```typescript
import { RegExpRouter } from 'hono/router/reg-exp-router'
const app = new Hono({ router: new RegExpRouter() })
```

## Building Larger Applications

Avoid "Rails-like controllers" — they break type inference:

```typescript
// Breaks type inference (id param not inferred)
const getBook = (c: Context) => c.json(c.req.param('id'))
app.get('/books/:id', getBook)

// Correct: inline handler preserves types
app.get('/books/:id', (c) => c.json(c.req.param('id')))
```

For large apps, use `factory.createHandlers()` if handler separation is required:

```typescript
import { createFactory } from 'hono/factory'
const factory = createFactory()

const handlers = factory.createHandlers(logger(), (c) => {
  return c.json({ ok: true })
})
app.get('/api', ...handlers)
```

See `references/rpc-and-client.md` for RPC-compatible large app patterns.
