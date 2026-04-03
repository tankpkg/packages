# Testing and Error Handling

Sources: Hono official documentation (hono.dev, 2024-2026), Vitest documentation (vitest.dev), @cloudflare/vitest-pool-workers documentation

Covers: app.request testing, testClient helper, environment mocking, onError handler, notFound handler, HTTPException, error propagation in middleware, Vitest setup for Cloudflare Workers, and testing patterns.

## Testing with app.request()

Hono applications are tested by sending requests and asserting on responses. No HTTP server needed — `app.request()` processes requests in-memory:

```typescript
import { Hono } from 'hono'
import { describe, it, expect } from 'vitest'

const app = new Hono()
app.get('/hello', (c) => c.text('Hello!'))
app.post('/posts', (c) => c.json({ message: 'Created' }, 201))

describe('API', () => {
  it('GET /hello returns 200', async () => {
    const res = await app.request('/hello')
    expect(res.status).toBe(200)
    expect(await res.text()).toBe('Hello!')
  })

  it('POST /posts returns 201', async () => {
    const res = await app.request('/posts', { method: 'POST' })
    expect(res.status).toBe(201)
    expect(await res.json()).toEqual({ message: 'Created' })
  })
})
```

### Sending JSON Body

```typescript
it('POST /posts with JSON body', async () => {
  const res = await app.request('/posts', {
    method: 'POST',
    body: JSON.stringify({ title: 'Test', body: 'Content' }),
    headers: { 'Content-Type': 'application/json' },
  })
  expect(res.status).toBe(201)
  expect(await res.json()).toEqual({ message: 'Created' })
})
```

The `Content-Type: application/json` header is required when the route uses `json` validation. Without it, the validator receives an empty object.

### Sending Form Data

```typescript
it('POST /upload with form data', async () => {
  const formData = new FormData()
  formData.append('name', 'test')
  formData.append('file', new File(['content'], 'test.txt'))

  const res = await app.request('/upload', {
    method: 'POST',
    body: formData,
  })
  expect(res.status).toBe(200)
})
```

### Using a Request Object

```typescript
it('accepts Request object', async () => {
  const req = new Request('http://localhost/hello', { method: 'GET' })
  const res = await app.request(req)
  expect(res.status).toBe(200)
})
```

### Checking Headers

```typescript
it('returns custom headers', async () => {
  const res = await app.request('/api/data')
  expect(res.headers.get('X-Custom')).toBe('value')
  expect(res.headers.get('Content-Type')).toContain('application/json')
})
```

## Mocking Environment Bindings

Pass environment bindings as the third argument to `app.request()`:

```typescript
type Bindings = {
  API_KEY: string
  DB: D1Database
}

const app = new Hono<{ Bindings: Bindings }>()

app.get('/data', async (c) => {
  if (c.env.API_KEY !== 'valid') {
    return c.json({ error: 'Unauthorized' }, 401)
  }
  return c.json({ data: 'secret' })
})

// Test with mocked env
it('rejects invalid API key', async () => {
  const res = await app.request('/data', {}, { API_KEY: 'invalid' })
  expect(res.status).toBe(401)
})

it('accepts valid API key', async () => {
  const res = await app.request('/data', {}, { API_KEY: 'valid' })
  expect(res.status).toBe(200)
})
```

### Mocking D1 Database

```typescript
const mockDB = {
  prepare: (sql: string) => ({
    bind: (...args: unknown[]) => ({
      all: async () => ({ results: [{ id: 1, name: 'Test' }] }),
      first: async () => ({ id: 1, name: 'Test' }),
      run: async () => ({ meta: { changes: 1 } }),
    }),
  }),
}

it('queries users', async () => {
  const res = await app.request('/users', {}, {
    DB: mockDB as unknown as D1Database,
    API_KEY: 'valid',
  })
  expect(res.status).toBe(200)
})
```

## testClient Helper

Use the typed test client for RPC-style testing:

```typescript
import { testClient } from 'hono/testing'

const app = new Hono()
  .get('/posts', (c) => c.json({ posts: [] }))
  .post('/posts',
    zValidator('json', z.object({ title: z.string() })),
    (c) => c.json({ created: true }, 201)
  )

it('GET /posts', async () => {
  const client = testClient(app)
  const res = await client.posts.$get()
  expect(res.status).toBe(200)
  const data = await res.json()
  expect(data).toEqual({ posts: [] })
})

it('POST /posts', async () => {
  const client = testClient(app)
  const res = await client.posts.$post({
    json: { title: 'Hello' },
  })
  expect(res.status).toBe(201)
})
```

`testClient` provides the same typed interface as `hc` but operates in-memory without a network call.

### testClient with Environment

```typescript
const client = testClient(app, {
  API_KEY: 'test-key',
  DB: mockDB,
})
```

## Vitest Setup for Cloudflare Workers

For Workers-specific testing with real D1/KV/R2:

```bash
npm i -D vitest @cloudflare/vitest-pool-workers
```

```typescript
// vitest.config.ts
import { defineWorkersConfig } from '@cloudflare/vitest-pool-workers/config'

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: './wrangler.toml' },
      },
    },
  },
})
```

This runs tests inside the Workers runtime with real bindings available.

## Error Handling

### app.onError()

Global error handler for uncaught exceptions:

```typescript
app.onError((err, c) => {
  console.error(`Error: ${err.message}`)

  if (err instanceof HTTPException) {
    return err.getResponse()
  }

  return c.json(
    {
      error: 'Internal Server Error',
      message: process.env.NODE_ENV === 'development' ? err.message : undefined,
    },
    500
  )
})
```

If both a parent app and sub-apps have `onError`, the sub-app handler takes priority.

### app.notFound()

Custom 404 handler:

```typescript
app.notFound((c) => {
  return c.json(
    {
      error: 'Not Found',
      path: c.req.path,
      method: c.req.method,
    },
    404
  )
})
```

The `notFound` handler is only invoked from the top-level app, not from sub-apps mounted with `.route()`.

### HTTPException

Throw structured HTTP errors from handlers and middleware:

```typescript
import { HTTPException } from 'hono/http-exception'

app.get('/protected', async (c) => {
  const token = c.req.header('Authorization')
  if (!token) {
    throw new HTTPException(401, { message: 'Authentication required' })
  }

  const user = await verifyToken(token)
  if (!user) {
    throw new HTTPException(403, { message: 'Invalid token' })
  }

  return c.json({ user })
})
```

HTTPException accepts options:

```typescript
throw new HTTPException(status, {
  message: 'Human-readable message',
  res: new Response('Custom body', { status: 400 }),  // Optional custom Response
  cause: originalError,  // Optional cause for error chaining
})
```

### Custom Error Response from HTTPException

```typescript
// Create a reusable error factory
function apiError(status: number, code: string, message: string): HTTPException {
  return new HTTPException(status, {
    res: new Response(
      JSON.stringify({ error: { code, message } }),
      {
        status,
        headers: { 'Content-Type': 'application/json' },
      }
    ),
  })
}

app.get('/users/:id', async (c) => {
  const user = await findUser(c.req.param('id'))
  if (!user) {
    throw apiError(404, 'USER_NOT_FOUND', 'User does not exist')
  }
  return c.json(user)
})
```

## Error Propagation in Middleware

Hono catches all errors from handlers and middleware. The `next()` function never throws:

```typescript
app.use(async (c, next) => {
  console.log('Before handler')
  await next()
  // If handler threw, c.error is set, but next() did not throw
  console.log('After handler')
  if (c.error) {
    console.error('Handler error:', c.error.message)
  }
})
```

No `try/catch` around `next()` is needed. Access the error via `c.error` in middleware that runs after the handler.

## Testing Error Handling

```typescript
const app = new Hono()

app.onError((err, c) => {
  return c.json({ error: err.message }, 500)
})

app.get('/fail', () => {
  throw new Error('Something broke')
})

app.get('/forbidden', () => {
  throw new HTTPException(403, { message: 'No access' })
})

describe('Error handling', () => {
  it('handles thrown errors', async () => {
    const res = await app.request('/fail')
    expect(res.status).toBe(500)
    expect(await res.json()).toEqual({ error: 'Something broke' })
  })

  it('handles HTTPException', async () => {
    const res = await app.request('/forbidden')
    expect(res.status).toBe(403)
  })

  it('returns 404 for unknown routes', async () => {
    const res = await app.request('/nonexistent')
    expect(res.status).toBe(404)
  })
})
```

## Testing Middleware

Test middleware by creating a minimal app with the middleware applied:

```typescript
import { createMiddleware } from 'hono/factory'

const authMiddleware = createMiddleware(async (c, next) => {
  const token = c.req.header('Authorization')
  if (!token) throw new HTTPException(401, { message: 'No token' })
  c.set('userId', 'user-123')
  await next()
})

describe('authMiddleware', () => {
  const testApp = new Hono()
    .use(authMiddleware)
    .get('/', (c) => c.json({ userId: c.get('userId') }))

  it('rejects without token', async () => {
    const res = await testApp.request('/')
    expect(res.status).toBe(401)
  })

  it('passes with token', async () => {
    const res = await testApp.request('/', {
      headers: { Authorization: 'Bearer test' },
    })
    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ userId: 'user-123' })
  })
})
```

## Testing Sub-Apps

Test sub-apps in isolation, then test the mounted app:

```typescript
// users.ts
export const usersApp = new Hono()
  .get('/', (c) => c.json([{ id: '1', name: 'Alice' }]))
  .get('/:id', (c) => c.json({ id: c.req.param('id'), name: 'Alice' }))

// users.test.ts — test in isolation
it('lists users', async () => {
  const res = await usersApp.request('/')
  expect(res.status).toBe(200)
})

// app.test.ts — test mounted
const app = new Hono().route('/users', usersApp)

it('lists users via mount', async () => {
  const res = await app.request('/users')
  expect(res.status).toBe(200)
})
```

## Common Testing Patterns

| Pattern | Implementation |
|---------|---------------|
| Assert JSON structure | `expect(await res.json()).toMatchObject({...})` |
| Assert status code | `expect(res.status).toBe(200)` |
| Assert header | `expect(res.headers.get('X-Key')).toBe('value')` |
| Assert redirect | `expect(res.status).toBe(302); expect(res.headers.get('Location')).toBe('/new')` |
| Assert content type | `expect(res.headers.get('Content-Type')).toContain('application/json')` |
| Send auth header | `headers: { Authorization: 'Bearer token' }` |
| Send cookies | `headers: { Cookie: 'session=abc123' }` |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Missing Content-Type in POST tests | Validator gets empty object | Add `'Content-Type': 'application/json'` |
| Using `supertest` | Designed for Express/Node HTTP | Use `app.request()` or `testClient()` |
| Not mocking env in tests | `c.env` is undefined, crashes | Pass env as third arg: `app.request(path, opts, env)` |
| Try/catch around `next()` | Unnecessary — Hono catches errors | Check `c.error` instead, or use `app.onError()` |
| Testing `notFound` on sub-app | `notFound` only fires on top-level app | Test on the root app instance |
| Expecting `c.notFound()` to work with RPC | Returns `unknown` type | Use `c.json({ error: '...' }, 404)` |
