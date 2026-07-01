# Cloudflare Integration

Sources: Hono official documentation (hono.dev, 2024-2026), Cloudflare Workers documentation (developers.cloudflare.com), Wrangler CLI documentation

Covers: Cloudflare Workers setup, typed Bindings (D1, R2, KV, Durable Objects, Queues), executionCtx.waitUntil, environment variables and secrets, static assets, scheduled events, GitHub Actions deployment, and Cloudflare-specific patterns.

## Project Setup

Scaffold a new Hono project for Cloudflare Workers:

```bash
npm create hono@latest my-app
# Select "cloudflare-workers" template
cd my-app
npm install
```

Minimal entry point:

```typescript
// src/index.ts
import { Hono } from 'hono'

const app = new Hono()
app.get('/', (c) => c.text('Hello Cloudflare Workers!'))

export default app
```

Run locally with Wrangler:

```bash
npm run dev    # wrangler dev
```

Deploy:

```bash
npm run deploy # wrangler deploy
```

## Typed Bindings

Cloudflare Workers bindings (KV, D1, R2, secrets, environment variables) are accessed via `c.env`. Define types for full autocomplete:

```typescript
type Bindings = {
  // Environment variables
  API_KEY: string
  NODE_ENV: string

  // KV Namespace
  CACHE: KVNamespace

  // D1 Database
  DB: D1Database

  // R2 Bucket
  STORAGE: R2Bucket

  // Durable Object
  COUNTER: DurableObjectNamespace

  // Queue
  MY_QUEUE: Queue

  // Service Binding
  AUTH_SERVICE: Fetcher

  // AI
  AI: Ai
}

const app = new Hono<{ Bindings: Bindings }>()
```

Install Cloudflare types for full definitions:

```bash
npm i --save-dev @cloudflare/workers-types
```

## D1 Database Patterns

### Basic Queries

```typescript
app.get('/users', async (c) => {
  const { results } = await c.env.DB
    .prepare('SELECT id, name, email FROM users LIMIT ?')
    .bind(20)
    .all()
  return c.json(results)
})

app.get('/users/:id', async (c) => {
  const id = c.req.param('id')
  const user = await c.env.DB
    .prepare('SELECT * FROM users WHERE id = ?')
    .bind(id)
    .first()

  if (!user) return c.json({ error: 'Not found' }, 404)
  return c.json(user)
})
```

### D1 with Drizzle ORM

```typescript
import { drizzle } from 'drizzle-orm/d1'
import * as schema from './schema'

app.get('/users', async (c) => {
  const db = drizzle(c.env.DB, { schema })
  const users = await db.select().from(schema.users).limit(20)
  return c.json(users)
})
```

Create the Drizzle instance per request from `c.env.DB` — D1 bindings are request-scoped.

### Batch Operations

```typescript
app.post('/seed', async (c) => {
  const results = await c.env.DB.batch([
    c.env.DB.prepare('INSERT INTO users (name) VALUES (?)').bind('Alice'),
    c.env.DB.prepare('INSERT INTO users (name) VALUES (?)').bind('Bob'),
    c.env.DB.prepare('INSERT INTO users (name) VALUES (?)').bind('Charlie'),
  ])
  return c.json({ inserted: results.length })
})
```

## KV Namespace

```typescript
app.get('/cache/:key', async (c) => {
  const key = c.req.param('key')
  const value = await c.env.CACHE.get(key)
  if (!value) return c.json({ error: 'Key not found' }, 404)
  return c.json({ key, value })
})

app.put('/cache/:key', async (c) => {
  const key = c.req.param('key')
  const body = await c.req.text()
  await c.env.CACHE.put(key, body, { expirationTtl: 3600 })
  return c.json({ key, stored: true })
})
```

## R2 Object Storage

```typescript
app.get('/files/:key', async (c) => {
  const key = c.req.param('key')
  const object = await c.env.STORAGE.get(key)
  if (!object) return c.json({ error: 'Not found' }, 404)

  c.header('Content-Type', object.httpMetadata?.contentType || 'application/octet-stream')
  return c.body(object.body)
})

app.put('/files/:key', async (c) => {
  const key = c.req.param('key')
  const body = await c.req.arrayBuffer()
  await c.env.STORAGE.put(key, body, {
    httpMetadata: { contentType: c.req.header('Content-Type') || 'application/octet-stream' },
  })
  return c.json({ key, uploaded: true })
})
```

## ExecutionContext

Use `c.executionCtx.waitUntil()` for background work that should complete after the response is sent:

```typescript
app.post('/events', async (c) => {
  const event = await c.req.json()

  // Respond immediately
  const response = c.json({ received: true })

  // Process asynchronously — Worker stays alive until this completes
  c.executionCtx.waitUntil(
    (async () => {
      await c.env.DB.prepare('INSERT INTO events (data) VALUES (?)').bind(JSON.stringify(event)).run()
      await c.env.MY_QUEUE.send(event)
    })()
  )

  return response
})
```

## Middleware with Environment Variables

On Cloudflare Workers, environment variables are not available at module scope. Access them inside handlers or wrap middleware:

```typescript
import { basicAuth } from 'hono/basic-auth'
import { jwt } from 'hono/jwt'

// Correct: access c.env at request time
app.use('/admin/*', async (c, next) => {
  const auth = basicAuth({
    username: c.env.ADMIN_USER,
    password: c.env.ADMIN_PASS,
  })
  return auth(c, next)
})

app.use('/api/*', async (c, next) => {
  const jwtMiddleware = jwt({ secret: c.env.JWT_SECRET })
  return jwtMiddleware(c, next)
})

// Wrong: c.env not available here
// app.use('/api/*', jwt({ secret: c.env.JWT_SECRET }))
```

## Local Environment Variables

Create `.dev.vars` in the project root for local development:

```
API_KEY=dev-secret-key
JWT_SECRET=local-jwt-secret
ADMIN_USER=admin
ADMIN_PASS=password
```

Wrangler automatically loads these when running `wrangler dev`.

## Static Assets

Configure in `wrangler.toml`:

```toml
assets = { directory = "public" }
```

Place files in `./public/`. The file `./public/static/style.css` is served at `/static/style.css`.

```
project/
  public/
    favicon.ico
    static/
      style.css
  src/
    index.ts
  wrangler.toml
```

## Scheduled Events (Cron Triggers)

Handle cron triggers alongside the Hono app:

```typescript
const app = new Hono<{ Bindings: Bindings }>()

app.get('/', (c) => c.text('API'))

export default {
  fetch: app.fetch,
  async scheduled(event: ScheduledEvent, env: Bindings, ctx: ExecutionContext) {
    ctx.waitUntil(
      (async () => {
        await env.DB.prepare('DELETE FROM sessions WHERE expires_at < ?')
          .bind(Date.now())
          .run()
      })()
    )
  },
}
```

Configure in `wrangler.toml`:

```toml
[triggers]
crons = ["0 * * * *"]  # Every hour
```

## Durable Objects

Access Durable Objects from Hono:

```typescript
app.get('/counter/:name', async (c) => {
  const name = c.req.param('name')
  const id = c.env.COUNTER.idFromName(name)
  const stub = c.env.COUNTER.get(id)
  const res = await stub.fetch(new Request('http://internal/increment'))
  return c.json(await res.json())
})
```

## Queues

Send messages to a Cloudflare Queue:

```typescript
app.post('/enqueue', async (c) => {
  const message = await c.req.json()
  await c.env.MY_QUEUE.send(message)
  return c.json({ queued: true })
})
```

## GitHub Actions Deployment

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

Add `CLOUDFLARE_API_TOKEN` to repository secrets. Create the token from the Cloudflare dashboard with "Edit Cloudflare Workers" template.

Add to `wrangler.toml`:

```toml
main = "src/index.ts"
minify = true
```

## Wrangler Configuration Reference

```toml
name = "my-api"
main = "src/index.ts"
compatibility_date = "2024-01-01"
minify = true

# Bindings
[[kv_namespaces]]
binding = "CACHE"
id = "abc123"

[[d1_databases]]
binding = "DB"
database_name = "my-db"
database_id = "def456"

[[r2_buckets]]
binding = "STORAGE"
bucket_name = "my-bucket"

[vars]
NODE_ENV = "production"

# Static assets
assets = { directory = "public" }

# Cron triggers
[triggers]
crons = ["0 */6 * * *"]
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Accessing `c.env` at module scope | Env not available outside request | Access inside handler or inline middleware |
| Not typing Bindings generic | No autocomplete on `c.env` | `new Hono<{ Bindings: Bindings }>()` |
| Creating Drizzle/DB at module scope | Binding is request-scoped | Create per request: `drizzle(c.env.DB)` |
| Missing `@cloudflare/workers-types` | No types for KV, D1, R2 | Install as dev dependency |
| Forgetting `waitUntil` for async work | Worker terminates before work completes | Wrap in `c.executionCtx.waitUntil()` |
| Using `process.env` | Not available in Workers by default | Use `c.env` or enable `nodejs_compat_populate_process_env` |
