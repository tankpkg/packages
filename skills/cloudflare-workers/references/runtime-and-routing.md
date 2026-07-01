# Runtime and Routing

Sources: Cloudflare Workers official documentation, Wrangler documentation, Hono documentation, Fetch API documentation, Cloudflare Pages Functions documentation

Covers: Workers runtime model, fetch handlers, Request/Response patterns, middleware and routing structure, Hono integration, Pages Functions, and edge-safe application composition.

## Workers Use the Fetch Runtime Model

Cloudflare Workers do not start from Node conventions. They start from Web Platform primitives.

| Primitive | Use |
|----------|-----|
| `Request` | incoming request data |
| `Response` | outgoing response |
| `fetch()` | downstream HTTP calls |
| `URL` | path/query parsing |
| `ExecutionContext` | async background work via `waitUntil` |

Write Worker code like edge-native web code, not like a Node server awkwardly transplanted to the edge.

## Minimal Worker Pattern

```ts
export default {
  async fetch(request, env, ctx): Promise<Response> {
    const url = new URL(request.url)

    if (url.pathname === '/healthz') {
      return new Response('ok')
    }

    return new Response('Not found', { status: 404 })
  }
}
```

Keep the top-level handler thin and delegate domain logic elsewhere.

## Env Bindings Are Typed Capabilities

Treat `env` as your platform capability surface.

```ts
interface Env {
  DB: D1Database
  CACHE: KVNamespace
  BUCKET: R2Bucket
}
```

### Binding rule

| Rule | Why |
|-----|-----|
| type every binding | safer usage and editor support |
| pass env dependencies into helpers explicitly | reduces hidden coupling |
| keep binding names stable across environments | lowers config drift |

## Routing Structure Options

| Need | Approach |
|------|----------|
| one or two routes | plain `if` / `switch` in fetch |
| moderate route count | small router helper |
| many routes + middleware + validation | Hono |
| static site with edge endpoints | Pages Functions |

### Plain routing example

```ts
const url = new URL(request.url)

switch (`${request.method} ${url.pathname}`) {
  case 'GET /users':
    return listUsers(request, env)
  case 'POST /users':
    return createUser(request, env)
  default:
    return new Response('Not found', { status: 404 })
}
```

Plain routing is fine until it stops being fine.

## When to Use Hono

Hono is a strong fit on Workers because it embraces the same runtime.

| Signal | Use Hono? |
|--------|-----------|
| route count growing fast | yes |
| middleware chain needed | yes |
| request validation desired | yes |
| tiny worker with 1-2 endpoints | maybe not |

### Hono example

```ts
import { Hono } from 'hono'

const app = new Hono<{ Bindings: Env }>()

app.get('/healthz', (c) => c.text('ok'))
app.get('/users/:id', async (c) => {
  const id = c.req.param('id')
  return c.json({ id })
})

export default app
```

## Middleware Rules

Use middleware for cross-cutting concerns, not domain workflows.

| Good middleware | Example |
|----------------|---------|
| auth extraction | parse token / attach user info |
| request logging | route, latency, status |
| CORS | browser access rules |
| correlation IDs | traceability |

### Avoid middleware for

| Anti-pattern | Better move |
|-------------|-------------|
| long business workflows | route handler or service |
| storage writes on every request | explicit route logic |
| hidden permission branching | explicit authorization logic |

## Response Design

| Response type | Pattern |
|--------------|---------|
| plain text | `new Response('ok')` |
| JSON | `Response.json(data)` or framework helper |
| binary/object | explicit headers and stream/body |
| redirect | `Response.redirect(url, 302)` |

Keep response contracts explicit and stable.

## `waitUntil` for Background Work

Workers can continue background work after responding using `ctx.waitUntil(...)`.

```ts
ctx.waitUntil(logAuditEvent(env, eventData))
return Response.json({ ok: true })
```

### Good `waitUntil` use cases

| Use case | Why |
|---------|-----|
| analytics/logging | non-blocking |
| cache warm/update | request path stays fast |
| async side notifications | user gets response sooner |

Do not put correctness-critical transactional work into `waitUntil` unless eventual execution is acceptable.

## Pages Functions vs Workers

| Surface | Best for |
|--------|----------|
| full Worker service | APIs, edge services, custom domains |
| Pages Functions | static site with dynamic edge handlers |

If most of the app is a static site and only a few routes need server logic, Pages Functions are often simpler.

## Request Parsing Checklist

1. Parse URL once
2. Check method early
3. Validate content type for JSON routes
4. Keep body parsing explicit
5. Bound payload size where needed

## Common Runtime Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| assuming Node built-ins exist | runtime failure | use edge-compatible deps |
| giant top-level fetch handler | hard maintenance | split route logic |
| hiding env usage in many modules | unclear platform dependencies | pass env explicitly |
| blocking response with non-critical side work | higher latency | use `waitUntil` |

## Release Readiness Checklist

- [ ] Runtime code is written against Fetch/Web APIs, not Node assumptions
- [ ] Routing structure matches application size
- [ ] Env bindings are typed and explicit
- [ ] Middleware is limited to cross-cutting concerns
- [ ] Background work uses `waitUntil` only where eventual execution is acceptable
- [ ] Pages Functions vs full Worker choice is intentional

## URL and Header Handling Patterns

Edge handlers often fail on small request-parsing mistakes.

| Concern | Recommendation |
|--------|----------------|
| query parsing | parse once from `new URL(request.url)` |
| header lookup | normalize expectations, do not assume presence |
| method branching | reject unsupported methods explicitly |
| content-type validation | check before JSON parsing |

Treat request parsing as a contract boundary, not boilerplate.

## Error Response Design

| Pattern | Benefit |
|--------|---------|
| stable JSON error envelope | easier client handling |
| explicit status codes | clear retry/UX logic |
| correlation/request ID in logs or response metadata | debugging |

### Example

```ts
function jsonError(message: string, status = 400) {
  return Response.json({ error: { message } }, { status })
}
```

## Route Composition in Larger Workers

When route count grows, separate by domain rather than by HTTP verb alone.

| Pattern | Example |
|--------|---------|
| users routes module | `/users/*` |
| billing routes module | `/billing/*` |
| admin routes module | `/admin/*` |

Domain grouping keeps the edge service understandable as it grows.

## Pages Functions Layout Pattern

| Need | Pattern |
|-----|---------|
| static app with a few dynamic handlers | keep most content static, add `/functions` routes |
| many API routes and bindings | plain Worker may be clearer |

Choose Pages Functions when they simplify a site, not when they complicate an API.

## Background Work Boundaries

`waitUntil` is useful, but not a transaction primitive.

| Good use | Bad use |
|---------|---------|
| analytics/audit log | required payment settlement |
| cache writes | correctness-critical primary write |
| low-risk notifications | steps that must complete before response is trusted |

## Edge Dependency Review

Before adding a package, ask:

1. Does it assume Node built-ins?
2. Does it depend on filesystem or TCP sockets?
3. Is there a Fetch/Web API-native alternative?

Many Worker failures are dependency model failures, not handler logic bugs.
