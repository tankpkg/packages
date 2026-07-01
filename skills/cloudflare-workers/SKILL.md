---
name: "@tank/cloudflare-workers"
description: |
  Cloudflare Workers edge application development and platform patterns. Covers
  Workers runtime fundamentals (fetch handlers, Request/Response/Web APIs),
  Wrangler CLI workflows, bindings (KV, R2, D1, Durable Objects, Queues,
  Vectorize, Workers AI), Pages Functions, Cron Triggers, service bindings,
  Hono integration, testing with Miniflare/Vitest, observability, performance,
  security, and deployment across preview and production environments.

  Synthesizes Cloudflare official documentation, Wrangler documentation, Hono
  documentation, Workers platform references, and production community patterns.

  Trigger phrases: "cloudflare workers", "workers kv", "d1 database", "r2 storage",
  "durable objects", "wrangler", "workers ai", "cloudflare pages", "edge runtime",
  "cloudflare queues", "cron trigger", "service binding", "miniflare",
  "hono workers", "cloudflare edge", "workers deploy", "cloudflare d1",
  "workers runtime", "pages functions", "cloudflare r2"
---

# Cloudflare Workers

## Core Philosophy

1. **Edge-first means Web API-first** — Write to the standard Fetch runtime model (`Request`, `Response`, `fetch`, `URL`) instead of assuming Node APIs exist.
2. **Bindings are the platform contract** — KV, D1, R2, Durable Objects, Queues, and AI are not ad hoc SDK calls; they are explicit runtime capabilities passed into your worker.
3. **Latency beats distance** — Keep hot request paths short, cache aggressively, and move coordination-heavy logic out of the edge path when possible.
4. **State belongs in the right primitive** — KV for simple global reads, D1 for relational queries, R2 for blobs, Durable Objects for coordination, Queues for async work.
5. **Deploy safely with environments** — Separate preview, staging, and production config in Wrangler; edge mistakes propagate globally fast.

## Quick-Start: Common Problems

### "Which Cloudflare storage primitive should I use?"

| Need | Primitive |
|------|-----------|
| Small globally replicated key/value reads | KV |
| Relational data and SQL | D1 |
| Files and large objects | R2 |
| Coordinated per-key state / rooms / locks | Durable Objects |
| Async background processing | Queues |
-> See `references/platform-primitives.md`

### "How do I structure a Worker app?"

1. Keep the fetch handler thin
2. Parse request, call domain logic, return `Response`
3. Keep bindings explicit in env typing
4. Split route logic from persistence/AI integrations
-> See `references/runtime-and-routing.md`

### "How do I deploy safely with Wrangler?"

1. Define environments in `wrangler.toml`
2. Keep secrets per-environment
3. Test locally with Miniflare / Wrangler dev
4. Promote through preview/staging before production
-> See `references/wrangler-and-deployment.md`

### "When should I use Hono on Workers?"

| Signal | Recommendation |
|--------|----------------|
| Very small worker, one route | plain fetch handler |
| Many routes, middleware, validation | Hono |
| Need typed RPC client and route composition | Hono |
-> See `references/runtime-and-routing.md`

## Decision Trees

### Coordination Primitive

| Signal | Use |
|--------|-----|
| Read-heavy, eventually consistent data | KV |
| Relational queries and transactions | D1 |
| Stateful single-entity coordination | Durable Objects |
| File/object serving | R2 |
| Deferred processing | Queues |

### Compute Surface

| Signal | Surface |
|--------|---------|
| Main request handling | Worker fetch handler |
| Static site plus edge functions | Pages Functions |
| Scheduled jobs | Cron Trigger |
| AI inference path | Workers AI + Worker orchestration |

### Testing Strategy

| Need | Tool |
|------|------|
| Local runtime simulation | Wrangler dev / Miniflare |
| Unit-level handler tests | Vitest |
| Binding-integrated tests | Miniflare with configured env |

## Reference Index

| File | Contents |
|------|----------|
| `references/runtime-and-routing.md` | Fetch runtime, Request/Response patterns, routing, Hono integration, middleware, Pages Functions |
| `references/platform-primitives.md` | KV, D1, R2, Durable Objects, Queues, Vectorize, Workers AI selection and usage patterns |
| `references/wrangler-and-deployment.md` | Wrangler config, environments, secrets, preview/prod rollout, CI/CD, observability hooks |
| `references/testing-and-debugging.md` | Miniflare, Wrangler dev, Vitest patterns, logs, traces, debugging runtime mismatches |
| `references/performance-and-security.md` | Caching, latency, cold starts, auth, secrets, edge-safe dependencies, common security pitfalls |
