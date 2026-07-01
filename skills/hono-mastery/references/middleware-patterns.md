# Middleware Patterns

Sources: Hono official documentation (hono.dev, 2024-2026), honojs/middleware GitHub repository

Covers: built-in middleware catalog, custom middleware with createMiddleware, execution order (onion model), type-safe context variables, third-party middleware, and middleware composition patterns.

## Middleware Fundamentals

Middleware runs before and/or after the route handler. Two rules:

- **Handler**: Returns a `Response`. Only one handler executes per request.
- **Middleware**: Calls `await next()` to pass to the next middleware, or returns a `Response` to short-circuit.

Register middleware with `app.use()`:

```typescript
// All routes, all methods
app.use(logger())

// Path-scoped
app.use('/api/*', cors())

// Method-scoped
app.post('/api/*', basicAuth({ username: 'admin', password: 'secret' }))
```

## Execution Order (Onion Model)

Middleware executes in registration order. Pre-handler code runs top-down, post-handler code runs bottom-up:

```typescript
app.use(async (_, next) => {
  console.log('1 start')
  await next()
  console.log('1 end')
})
app.use(async (_, next) => {
  console.log('2 start')
  await next()
  console.log('2 end')
})
app.get('/', (c) => {
  console.log('handler')
  return c.text('OK')
})

// Output:
// 1 start
//   2 start
//     handler
//   2 end
// 1 end
```

`next()` never throws — Hono catches handler errors and passes them to `app.onError()`. No try/catch needed around `next()`.

## Built-in Middleware Catalog

### Authentication

| Middleware | Import | Purpose |
|-----------|--------|---------|
| Basic Auth | `hono/basic-auth` | Username/password with HTTP Basic |
| Bearer Auth | `hono/bearer-auth` | Token-based Bearer authentication |
| JWT | `hono/jwt` | JWT verification and decoding |

```typescript
import { basicAuth } from 'hono/basic-auth'
import { bearerAuth } from 'hono/bearer-auth'
import { jwt } from 'hono/jwt'

// Basic Auth
app.use('/admin/*', basicAuth({
  username: 'admin',
  password: 'secret',
}))

// Bearer Auth
app.use('/api/*', bearerAuth({
  token: 'my-secret-token',
}))

// JWT verification
app.use('/api/*', jwt({
  secret: 'my-jwt-secret',
}))
// Access decoded payload:
app.get('/api/me', (c) => {
  const payload = c.get('jwtPayload')
  return c.json(payload)
})
```

### Security

| Middleware | Import | Purpose |
|-----------|--------|---------|
| CORS | `hono/cors` | Cross-Origin Resource Sharing headers |
| CSRF Protection | `hono/csrf` | Cross-Site Request Forgery prevention |
| Secure Headers | `hono/secure-headers` | Security headers (CSP, HSTS, X-Frame-Options) |

```typescript
import { cors } from 'hono/cors'
import { csrf } from 'hono/csrf'
import { secureHeaders } from 'hono/secure-headers'

app.use(cors({
  origin: ['https://example.com'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowHeaders: ['Content-Type', 'Authorization'],
  maxAge: 86400,
}))

app.use(csrf({ origin: 'https://example.com' }))

app.use(secureHeaders({
  contentSecurityPolicy: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'", "'unsafe-inline'"],
  },
}))
```

### Performance

| Middleware | Import | Purpose |
|-----------|--------|---------|
| Compress | `hono/compress` | Gzip/Brotli response compression |
| Cache | `hono/cache` | Cache-Control with Cloudflare Cache API |
| ETag | `hono/etag` | ETag-based conditional responses |
| Body Limit | `hono/body-limit` | Limit request body size |

```typescript
import { compress } from 'hono/compress'
import { cache } from 'hono/cache'
import { etag } from 'hono/etag'
import { bodyLimit } from 'hono/body-limit'

app.use(compress())
app.use(etag())

// Cache API (Cloudflare Workers)
app.get('/api/data', cache({
  cacheName: 'my-app',
  cacheControl: 'max-age=3600',
}))

// Limit body to 1MB
app.post('/upload', bodyLimit({
  maxSize: 1024 * 1024,
  onError: (c) => c.text('Body too large', 413),
}))
```

### Observability

| Middleware | Import | Purpose |
|-----------|--------|---------|
| Logger | `hono/logger` | Request/response logging |
| Timing | `hono/timing` | Server-Timing header |
| Pretty JSON | `hono/pretty-json` | Formatted JSON with `?pretty` |
| Powered By | `hono/powered-by` | X-Powered-By header |

```typescript
import { logger } from 'hono/logger'
import { timing, startTime, endTime } from 'hono/timing'
import { prettyJSON } from 'hono/pretty-json'

app.use(logger())
app.use(timing())
app.use(prettyJSON())

app.get('/api', async (c) => {
  startTime(c, 'db')
  const data = await fetchFromDB()
  endTime(c, 'db')
  return c.json(data)
})
```

### Utilities

| Middleware | Import | Purpose |
|-----------|--------|---------|
| Context Storage | `hono/context-storage` | Async-local storage for context |
| IP Restriction | `hono/ip-restriction` | Allow/deny by IP address |
| Request ID | `hono/request-id` | Unique request identifier |
| Language | `hono/language` | Accept-Language detection |

## Custom Middleware

### Inline Middleware

```typescript
app.use(async (c, next) => {
  const start = Date.now()
  await next()
  const ms = Date.now() - start
  c.header('X-Response-Time', `${ms}ms`)
})
```

### Reusable Middleware with createMiddleware

Use `createMiddleware()` for type-safe, reusable middleware:

```typescript
import { createMiddleware } from 'hono/factory'

type Env = {
  Variables: {
    user: { id: string; role: string }
  }
}

const authMiddleware = createMiddleware<Env>(async (c, next) => {
  const token = c.req.header('Authorization')?.replace('Bearer ', '')
  if (!token) {
    return c.json({ error: 'Unauthorized' }, 401)
  }
  const user = await verifyToken(token)
  c.set('user', user)
  await next()
})

app.use('/api/*', authMiddleware)

app.get('/api/profile', (c) => {
  const user = c.var.user // Type: { id: string; role: string }
  return c.json(user)
})
```

### Modifying Response in Middleware

```typescript
const stripResponseMiddleware = createMiddleware(async (c, next) => {
  await next()
  // Replace the entire response
  c.res = undefined
  c.res = new Response('Modified response')
})
```

### Dynamic Middleware Configuration from Environment

Access `c.env` inside middleware arguments by wrapping in an inline handler:

```typescript
app.use('/api/*', async (c, next) => {
  const middleware = cors({
    origin: c.env.CORS_ORIGIN,  // Read from environment
  })
  return middleware(c, next)
})
```

This pattern is required on Cloudflare Workers where env values are not available at module scope.

## Type Inference Across Middleware Chains

Chain `.use()` calls to accumulate `Variables` types automatically:

```typescript
const authMiddleware = createMiddleware<{
  Variables: { user: { id: string; name: string } }
}>(async (c, next) => {
  c.set('user', { id: '123', name: 'Alice' })
  await next()
})

const dbMiddleware = createMiddleware<{
  Variables: { db: Database }
}>(async (c, next) => {
  c.set('db', createDbConnection())
  await next()
})

const app = new Hono()
  .use(authMiddleware)
  .use(dbMiddleware)
  .get('/', (c) => {
    const user = c.var.user  // { id: string; name: string }
    const db = c.var.db      // Database
    return c.json({ user })
  })
```

Each `.use()` returns a new Hono instance with merged types. No manual `Env` type declaration needed.

## ContextVariableMap (Module Augmentation)

For middleware used globally, extend the type map via module augmentation:

```typescript
declare module 'hono' {
  interface ContextVariableMap {
    requestId: string
    startTime: number
  }
}

const requestIdMiddleware = createMiddleware(async (c, next) => {
  c.set('requestId', crypto.randomUUID())
  c.set('startTime', Date.now())
  await next()
})
```

All handlers automatically see `requestId` and `startTime` on `c.var` and `c.get()`.

## Third-Party Middleware

Notable third-party packages from `@hono/` namespace:

| Package | Purpose |
|---------|---------|
| `@hono/zod-validator` | Zod schema validation as middleware |
| `@hono/zod-openapi` | OpenAPI spec generation from Zod schemas |
| `@hono/standard-validator` | Standard Schema compatible validator |
| `@hono/graphql-server` | GraphQL endpoint middleware |
| `@hono/firebase-auth` | Firebase Authentication verification |
| `@hono/sentry` | Sentry error reporting |
| `@hono/clerk-auth` | Clerk authentication |
| `@hono/prometheus` | Prometheus metrics |

Install from npm: `npm i @hono/{package-name}`

## Middleware Composition Patterns

### Guard Pattern (Early Return)

```typescript
const requireAdmin = createMiddleware(async (c, next) => {
  const user = c.var.user
  if (user.role !== 'admin') {
    return c.json({ error: 'Forbidden' }, 403)
  }
  await next()
})

app.delete('/users/:id', authMiddleware, requireAdmin, (c) => {
  // Only admin reaches here
  return c.json({ deleted: true })
})
```

### Middleware per Route

Pass middleware directly in the handler chain:

```typescript
app.get('/public', (c) => c.text('Public'))
app.get('/private', authMiddleware, (c) => c.text('Private'))
app.post('/upload', authMiddleware, bodyLimit({ maxSize: 5_000_000 }), handler)
```

### Conditional Middleware

Apply middleware based on request properties:

```typescript
app.use(async (c, next) => {
  if (c.req.path.startsWith('/api/')) {
    const corsMiddleware = cors({ origin: '*' })
    return corsMiddleware(c, next)
  }
  await next()
})
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Forgetting `await next()` | Downstream handlers never execute | Always call `await next()` in middleware |
| Registering catch-all before specific | Specific routes never match | Register specific routes first, catch-all last |
| Using env in module scope on CF Workers | Env not available at import time | Wrap in inline middleware, access `c.env` |
| Different Hono versions in middleware | Type incompatibility, runtime bugs | Pin identical Hono version everywhere |
| Not chaining `.use()` for RPC types | Variables types not merged | Chain: `new Hono().use(a).use(b).get(...)` |
