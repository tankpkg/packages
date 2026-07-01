# Multi-Runtime Deployment

Sources: Hono official documentation (hono.dev, 2024-2026), @hono/node-server documentation, Bun documentation (bun.sh), Deno documentation (deno.com)

Covers: deployment patterns for Bun, Deno, Node.js (via @hono/node-server), AWS Lambda, Vercel, Fastly Compute, entry point differences per runtime, environment variable handling, and migration from Express.

## Web Standards Foundation

Hono runs on any JavaScript runtime that supports Web Standard APIs (Request, Response, fetch). The same Hono application code works across all runtimes — only the entry point differs.

| Runtime | Entry Point Pattern | Cold Start | Best For |
|---------|-------------------|------------|----------|
| Cloudflare Workers | `export default app` | ~0ms (pre-warmed) | Edge APIs, globally distributed |
| Bun | `export default app` or `Bun.serve()` | ~10ms | Fast server, local dev, single-region |
| Deno | `Deno.serve(app.fetch)` | ~15ms | Secure sandbox, Deno Deploy |
| Node.js | `serve(app)` via adapter | ~50ms | Existing Node infrastructure |
| AWS Lambda | Adapter wrapper | ~100-500ms | Serverless on AWS |
| Vercel | Edge/Serverless adapter | ~50-200ms | Frontend + API on Vercel |
| Fastly Compute | `app.fire()` | ~0ms | Fastly CDN edge |

## Bun

### Setup

```bash
bun create hono@latest my-app
# Select "bun" template
cd my-app && bun install
```

### Entry Point

```typescript
// src/index.ts
import { Hono } from 'hono'

const app = new Hono()
app.get('/', (c) => c.text('Hello Bun!'))

export default app
```

Bun auto-detects the default export and serves it. To customize port:

```typescript
export default {
  port: 3000,
  fetch: app.fetch,
}
```

### Static Files on Bun

```typescript
import { serveStatic } from 'hono/bun'

app.use('/static/*', serveStatic({ root: './' }))
// Serves files from ./static/
```

### Environment Variables

Bun reads `.env` files automatically:

```typescript
app.get('/', (c) => {
  const key = process.env.API_KEY // Available via process.env
  return c.text(`Key: ${key}`)
})
```

Or use Bun-specific env access:

```typescript
const key = Bun.env.API_KEY
```

## Deno

### Setup

```bash
deno init --npm hono@latest my-app
cd my-app
```

### Entry Point

```typescript
// main.ts
import { Hono } from 'hono'

const app = new Hono()
app.get('/', (c) => c.text('Hello Deno!'))

Deno.serve(app.fetch)
```

Custom port:

```typescript
Deno.serve({ port: 8000 }, app.fetch)
```

### Static Files on Deno

```typescript
import { serveStatic } from 'hono/deno'

app.use('/static/*', serveStatic({ root: './' }))
```

### Environment Variables

```typescript
app.get('/', (c) => {
  const key = Deno.env.get('API_KEY')
  return c.text(`Key: ${key}`)
})
```

### Deno Deploy

Deploy directly to Deno Deploy edge network. Hono works with zero configuration.

```bash
deployctl deploy --project=my-app main.ts
```

### Version Pinning

Use consistent Hono versions across imports. Mixing versions causes runtime bugs:

```typescript
// Correct: same version everywhere
import { Hono } from 'jsr:@hono/hono@4.6.0'
import { logger } from 'jsr:@hono/hono@4.6.0/logger'

// Wrong: version mismatch
import { Hono } from 'jsr:@hono/hono@4.6.0'
import { logger } from 'jsr:@hono/hono@4.4.0/logger' // Different version!
```

## Node.js

Hono does not run on Node.js natively — use the `@hono/node-server` adapter.

### Setup

```bash
npm create hono@latest my-app
# Select "nodejs" template
cd my-app && npm install
```

Or add to existing project:

```bash
npm i hono @hono/node-server
```

### Entry Point

```typescript
// src/index.ts
import { serve } from '@hono/node-server'
import { Hono } from 'hono'

const app = new Hono()
app.get('/', (c) => c.text('Hello Node.js!'))

serve({
  fetch: app.fetch,
  port: 3000,
}, (info) => {
  console.log(`Listening on http://localhost:${info.port}`)
})
```

### Static Files on Node.js

```typescript
import { serveStatic } from '@hono/node-server/serve-static'

app.use('/static/*', serveStatic({ root: './' }))
```

### Environment Variables

Use `process.env` directly or libraries like `dotenv`:

```typescript
import 'dotenv/config'

app.get('/', (c) => {
  return c.text(process.env.API_KEY || 'no key')
})
```

### Node.js Compatibility Notes

| Feature | Status |
|---------|--------|
| Request/Response APIs | Polyfilled by adapter |
| WebSocket | Use `@hono/node-ws` |
| Streams | Supported via Web Streams API |
| File uploads | Supported (multipart) |
| process.env | Available natively |

## AWS Lambda

### Setup

```bash
npm create hono@latest my-app
# Select "aws-lambda" template
```

### Entry Point

```typescript
// src/index.ts
import { Hono } from 'hono'
import { handle } from 'hono/aws-lambda'

const app = new Hono()
app.get('/', (c) => c.json({ message: 'Hello Lambda!' }))

export const handler = handle(app)
```

### Lambda with API Gateway

The adapter automatically handles API Gateway v1 and v2 event formats. Access Lambda-specific context:

```typescript
import type { LambdaContext } from 'hono/aws-lambda'

app.get('/', (c) => {
  const lambdaContext = c.env as LambdaContext
  return c.json({
    requestId: lambdaContext.requestContext?.requestId,
  })
})
```

## Vercel

### Edge Functions

```typescript
// app/api/[[...route]]/route.ts
import { Hono } from 'hono'
import { handle } from 'hono/vercel'

export const runtime = 'edge'

const app = new Hono().basePath('/api')
app.get('/hello', (c) => c.json({ message: 'Hello Vercel Edge!' }))

export const GET = handle(app)
export const POST = handle(app)
```

### Serverless Functions

```typescript
export const runtime = 'nodejs' // Use Node.js runtime instead of edge
```

## Fastly Compute

```typescript
import { Hono } from 'hono'

const app = new Hono()
app.get('/', (c) => c.text('Hello Fastly!'))

app.fire() // Registers global fetch event listener
```

## Migration from Express

### Route Mapping

| Express | Hono |
|---------|------|
| `app.get('/path', handler)` | `app.get('/path', (c) => ...)` |
| `req.params.id` | `c.req.param('id')` |
| `req.query.page` | `c.req.query('page')` |
| `req.body` | `await c.req.json()` or `await c.req.parseBody()` |
| `req.headers['x-key']` | `c.req.header('x-key')` |
| `res.json({ ok: true })` | `return c.json({ ok: true })` |
| `res.status(201).json(data)` | `return c.json(data, 201)` |
| `res.redirect('/new')` | `return c.redirect('/new')` |
| `res.send('text')` | `return c.text('text')` |
| `res.sendFile('index.html')` | Use `serveStatic` middleware |

### Middleware Mapping

| Express Middleware | Hono Equivalent |
|-------------------|-----------------|
| `cors()` | `cors()` from `hono/cors` |
| `helmet()` | `secureHeaders()` from `hono/secure-headers` |
| `morgan()` | `logger()` from `hono/logger` |
| `express.json()` | Built-in (use `c.req.json()`) |
| `express-rate-limit` | Custom middleware or third-party |
| `passport-jwt` | `jwt()` from `hono/jwt` |
| `compression` | `compress()` from `hono/compress` |

### Key Differences

| Aspect | Express | Hono |
|--------|---------|------|
| Response pattern | Mutate `res`, call `res.send()` | Return `Response` from handler |
| Middleware | `next()` callback | `await next()` async |
| Body parsing | Separate middleware | Built into `c.req` |
| TypeScript | Added via `@types/express` | First-class, built-in |
| Runtime | Node.js only | Any JS runtime |
| Bundle size | ~572KB | ~14KB (hono/tiny) |
| Performance | Moderate | 2-5x faster routing |

### Migration Strategy

1. Start with routing — convert Express routes to Hono handlers
2. Replace middleware one by one with Hono built-ins
3. Change `req`/`res` patterns to Context (`c`) patterns
4. Update tests to use `app.request()` instead of `supertest`
5. Choose target runtime and configure entry point
6. Deploy and verify

## Mounting Express in Hono

Use `app.mount()` for incremental migration:

```typescript
import express from 'express'
import { Hono } from 'hono'

const expressApp = express()
expressApp.get('/legacy', (req, res) => res.json({ legacy: true }))

const app = new Hono()
app.get('/new', (c) => c.json({ new: true }))
app.mount('/express', expressApp)
```

## Environment Variables by Runtime

| Runtime | Access Pattern | File |
|---------|---------------|------|
| Cloudflare Workers | `c.env.KEY` | `.dev.vars` |
| Bun | `process.env.KEY` / `Bun.env.KEY` | `.env` |
| Deno | `Deno.env.get('KEY')` | `.env` (with `--allow-env`) |
| Node.js | `process.env.KEY` | `.env` + `dotenv` |
| AWS Lambda | `process.env.KEY` | Lambda config |
| Vercel | `process.env.KEY` | Vercel dashboard |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Using Node.js APIs in edge code | `fs`, `path` unavailable on Workers/Deno | Use Web Standard APIs only |
| Express-style `res.send()` | Hono handlers must return Response | `return c.json(data)` |
| Forgetting `@hono/node-server` | `export default app` fails on Node | Use `serve({ fetch: app.fetch })` |
| `process.env` on Cloudflare | Not available by default | Use `c.env` |
| Mutating response after return | No effect in Hono | Set headers before returning response |
