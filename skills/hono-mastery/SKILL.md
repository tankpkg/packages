---
name: "@tank/hono-mastery"
description: |
  Build and deploy multi-runtime TypeScript APIs with Hono. Covers routing
  (grouping, regex params, wildcards, chaining, basePath), Context API
  (c.req, c.json, c.html, c.set/get, c.env), built-in middleware (cors,
  jwt, basicAuth, bearerAuth, logger, compress, secureHeaders, cache, etag,
  csrf, bodyLimit), custom middleware with createMiddleware, validation
  (Zod, Valibot, ArkType via Standard Schema), RPC mode with hc client
  (type-safe client-server, InferRequestType/ResponseType), JSX/streaming,
  WebSockets, OpenAPI integration (@hono/zod-openapi), testing (app.request,
  testClient), error handling (onError, HTTPException), and deployment to
  Cloudflare Workers (D1/R2/KV bindings), Bun, Deno, Node.js, AWS Lambda,
  and Vercel. Synthesizes Hono official documentation (hono.dev, 2024-2026),
  honojs/middleware repository, and production Hono patterns.

  Trigger phrases: "hono", "hono js", "hono framework", "hono tutorial",
  "hono vs express", "hono cloudflare workers", "hono rpc", "hono middleware",
  "hono typescript", "hono deno", "hono bun", "hono zod openapi",
  "hono d1", "hono validation", "hono testing", "hono deployment",
  "hono context", "hono routing", "hono jwt", "hono node.js"
---

# Hono Mastery

## Core Philosophy

1. **Web Standards first** — Hono uses only Web Standard APIs (Request, Response, fetch). Code written for one runtime runs on every runtime without adaptation.
2. **TypeScript types are the contract** — Chain handlers to preserve type inference. Avoid separating handlers into "controllers" because path params and middleware types break. Use `c.req.param()` inline where types flow.
3. **Middleware is the composition layer** — Every cross-cutting concern (auth, CORS, logging, validation) is middleware. Register with `app.use()` by path, compose with `createMiddleware()` for type safety.
4. **RPC replaces hand-written API clients** — Export `typeof app` and use `hc<AppType>()` on the client. The Zod validator schema becomes the single source of truth for both request validation and client types.
5. **Adapters bridge runtimes** — Write one Hono app, deploy anywhere. Each runtime adapter translates its entry point to Hono's `fetch(request, env, ctx)` signature.

## Quick-Start: Common Problems

### "How do I structure a larger Hono app?"

1. Create sub-apps per domain: `const users = new Hono()` with chained handlers
2. Mount with `app.route('/users', users)` in the main entry
3. For RPC, chain routes: `const routes = app.route('/users', users).route('/posts', posts)`
4. Export the type: `export type AppType = typeof routes`
-> See `references/routing-and-context.md`

### "My Cloudflare bindings have no types"

1. Define: `type Bindings = { DB: D1Database; KV: KVNamespace }`
2. Pass: `new Hono<{ Bindings: Bindings }>()`
3. Access: `c.env.DB.prepare(...)` with full autocomplete
4. For middleware using env values, wrap: `const auth = basicAuth({ username: c.env.USERNAME, password: c.env.PASSWORD }); return auth(c, next)`
-> See `references/cloudflare-integration.md`

### "How do I add Zod validation with OpenAPI?"

1. Install: `@hono/zod-validator` or `@hono/zod-openapi`
2. Use `zValidator('json', schema)` as middleware before the handler
3. Access validated data: `c.req.valid('json')`
4. For OpenAPI: use `createRoute()` with request/response schemas, then `app.openapi(route, handler)`
-> See `references/validation-and-openapi.md`

### "RPC types are not working across packages"

1. Ensure identical Hono versions in server and client packages
2. Chain all handlers: `const app = new Hono().get(...)` not `app.get(...)`
3. Export: `export type AppType = typeof app`
4. For monorepos: use TypeScript project references or compile with `tsc` first
-> See `references/rpc-and-client.md`

## Decision Trees

### Runtime Selection

| Signal | Runtime |
|--------|---------|
| Edge deployment on Cloudflare | Cloudflare Workers |
| Fast startup, modern server | Bun |
| Secure sandbox, Deno Deploy | Deno |
| Existing Node.js infrastructure | Node.js via `@hono/node-server` |
| Serverless on AWS | AWS Lambda via adapter |
| Vercel serverless/edge | Vercel adapter |

### Validation Approach

| Signal | Approach |
|--------|----------|
| Need OpenAPI docs from schemas | `@hono/zod-openapi` |
| Simple request validation | `zValidator` from `@hono/zod-validator` |
| Want smallest bundle | Valibot via `@hono/standard-validator` |
| Framework-agnostic validators | Standard Schema (`sValidator`) |
| Minimal, no dependencies | Manual `validator()` from `hono/validator` |

### Auth Strategy

| Signal | Approach |
|--------|----------|
| Simple API key / password gate | `basicAuth()` or `bearerAuth()` built-in |
| JWT token verification | `jwt()` built-in middleware |
| Custom session / OAuth | Custom middleware with `createMiddleware()` |
| Cloudflare Access / Zero Trust | Check `CF-Access-JWT-Assertion` header |

## Reference Index

| File | Contents |
|------|----------|
| `references/routing-and-context.md` | Routing patterns (params, regex, groups, basePath, chaining, priority), Context API (c.req, c.json, c.html, c.redirect, c.set/get, c.var, c.env), request/response handling |
| `references/middleware-patterns.md` | Built-in middleware catalog (cors, jwt, basicAuth, bearerAuth, logger, compress, secureHeaders, cache, etag, csrf, bodyLimit), custom middleware with createMiddleware, execution order, type-safe variables |
| `references/validation-and-openapi.md` | Manual validator, Zod/Valibot/ArkType integration, Standard Schema, @hono/zod-openapi, Swagger UI setup, validation targets (json, form, query, param, header, cookie) |
| `references/rpc-and-client.md` | hc client setup, type inference, InferRequestType/ResponseType, path parameters in RPC, status-code-based typing, $url/$path helpers, monorepo patterns, IDE performance tips |
| `references/cloudflare-integration.md` | Workers setup, typed Bindings (D1, R2, KV, Durable Objects), executionCtx.waitUntil, env variables, static assets, GitHub Actions deployment, scheduled events |
| `references/multi-runtime-deployment.md` | Bun, Deno, Node.js (@hono/node-server), AWS Lambda, Vercel, Fastly adapters, entry point patterns, environment differences, migration from Express |
| `references/testing-and-error-handling.md` | app.request testing, testClient helper, env mocking, onError handler, notFound handler, HTTPException, error propagation in middleware, Vitest setup |
