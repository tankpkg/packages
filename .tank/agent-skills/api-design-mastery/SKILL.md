---
name: "@tank/api-design-mastery"
description: |
  REST, GraphQL, and tRPC API design for backend engineers. Covers endpoint
  design (resource modeling, HTTP methods, status codes), API versioning
  strategies (URL path, header, media type, deprecation), error contracts
  (RFC 7807/9457 Problem Details, field validation errors), pagination
  (offset, cursor, keyset, GraphQL Relay connections), filtering and sorting,
  authentication patterns (API keys, JWT, OAuth 2.0 flows with PKCE, Client
  Credentials), and authorization (RBAC, scopes, rate limiting).

  Synthesizes Lauret (The Design of Web APIs), Giroux (Production-Ready
  GraphQL), Madden (API Security in Action), Richer & Sanso (OAuth 2.0 in
  Action), tRPC v11 documentation, RFC 7807/9457, and Relay connections spec.

  Trigger phrases: "REST API", "GraphQL schema", "tRPC", "API design",
  "endpoint design", "API versioning", "deprecate API", "error response",
  "problem details", "RFC 7807", "API errors", "pagination", "cursor pagination",
  "offset pagination", "GraphQL connections", "Relay spec", "API auth",
  "API keys", "JWT", "OAuth 2.0", "PKCE", "Client Credentials", "rate limiting",
  "RBAC", "API security", "HTTP status codes", "REST resource", "GraphQL N+1",
  "DataLoader", "tRPC middleware", "tRPC context", "tRPC procedures",
  "breaking changes", "backward compatible", "Sunset header", "field validation",
  "filter API", "sort API", "API contract"
---
# API Design Mastery

## Core Philosophy

1. **Design for the consumer, not the database** — API shape reflects use cases, not schema structure. Consumers should not need to understand your internals.
2. **Consistency over cleverness** — Uniform patterns across all endpoints reduce cognitive load more than any individual optimization.
3. **Additive by default** — Plan for backward compatibility from day one. Adding is safe; removing breaks clients.
4. **Errors are first-class citizens** — Error contracts deserve the same design care as success responses. Use RFC 9457.
5. **Pick the right tool** — REST for public APIs, GraphQL for multi-client data graphs, tRPC for TypeScript monorepos.

## Quick-Start: Common Problems

### "Which API style should I use?"

| Signal | Choose |
|--------|--------|
| Public API, third-party consumers, any client language | REST + OpenAPI |
| Multiple clients needing different data shapes (web + mobile + partner) | GraphQL |
| TypeScript monorepo, internal full-stack app (Next.js/Remix) | tRPC |
| Real-time data streams + existing REST/GraphQL | Add subscriptions (GraphQL / tRPC) |
| → See `references/trpc-patterns.md` for the REST vs GraphQL vs tRPC comparison table |

### "How do I design this endpoint?"

1. What is the resource (noun)? → `/orders`, not `/createOrder`
2. What HTTP method? → GET (read) / POST (create) / PUT (replace) / PATCH (partial) / DELETE
3. What status code on success? → 200/201/204
4. What is the error contract? → RFC 7807 `application/problem+json`
5. Does it change anything observable? → If yes, it must be POST/PUT/PATCH/DELETE
→ See `references/rest-endpoint-design.md`

### "My API returns errors inconsistently"

1. Adopt RFC 7807 Problem Details — `type`, `title`, `status`, `detail`, `instance`
2. Use `Content-Type: application/problem+json`
3. Add machine-readable `code` extension (SCREAMING_SNAKE_CASE)
4. Add `errors[]` array for field validation failures
5. Include `requestId` for server-side correlation
→ See `references/error-contracts.md`

### "Clients are breaking when I change the API"

1. Was it a breaking change? → See breaking vs non-breaking table in `references/api-versioning.md`
2. If breaking: add new version; run old version in parallel
3. Announce deprecation: `Deprecation: true` + `Sunset:` header (RFC 8594)
4. Give clients ≥ 6 months; contact high-traffic users directly
→ See `references/api-versioning.md`

### "Pagination is slow at deep pages"

1. Offset/limit past page 100? → Switch to cursor pagination
2. Need GraphQL? → Use Relay Cursor Connections spec
3. REST? → Keyset pagination with opaque base64 cursor
4. Index must cover all ORDER BY columns
→ See `references/pagination-filtering.md`

### "Auth isn't secure"

1. Server-to-server: API key (hashed, Authorization header, never URL param)
2. User-delegated: OAuth 2.0 Authorization Code + PKCE
3. Service-to-service: OAuth 2.0 Client Credentials
4. All JWT access tokens: ≤ 15 min expiry; refresh tokens in httpOnly cookie
→ See `references/auth-patterns.md`

## Decision Trees

### HTTP Method Selection

| Operation | Method | Idempotent? | Notes |
|-----------|--------|-------------|-------|
| Fetch resource or list | GET | Yes | Never has side effects |
| Create new resource | POST | No | Returns 201 + Location header |
| Full replace (client provides all fields) | PUT | Yes | Client sends complete representation |
| Partial update (only changed fields) | PATCH | No (unless designed) | Client sends delta only |
| Remove resource | DELETE | Yes | Returns 204 No Content |
| Trigger action (not a CRUD op) | POST | Depends | `/orders/42/cancel` |

### Error Status Code Selection

| Situation | Code |
|-----------|------|
| Can't parse request body | 400 |
| Valid syntax, fails business validation | 422 |
| No credentials provided | 401 |
| Credentials valid, lacks permission | 403 |
| Resource doesn't exist | 404 |
| Duplicate / state conflict | 409 |
| Permanently removed | 410 |
| Rate limit exceeded | 429 |

### GraphQL vs REST Error Handling

| Layer | REST | GraphQL | tRPC |
|-------|------|---------|------|
| Transport errors | HTTP status + Problem Details | HTTP 200 (partial) or 400 | HTTP status via TRPCError code |
| Field errors | `errors[]` in Problem Details | `errors[]` array + `extensions.code` | Zod error formatter |

## Reference Files

| File | Contents |
|------|----------|
| `references/rest-endpoint-design.md` | Resource modeling, URL naming, HTTP methods, status codes, idempotency, HATEOAS, request/response design |
| `references/graphql-schema-design.md` | Type system, queries/mutations/subscriptions, N+1 problem, DataLoader, Relay connections spec, complexity limiting, security |
| `references/trpc-patterns.md` | initTRPC setup, procedure types, Zod validation, middleware, context, router composition, error codes, subscriptions, adapters |
| `references/api-versioning.md` | Breaking vs non-breaking changes, URL/header/media-type strategies, deprecation workflow, Sunset header, Stripe versioning model |
| `references/error-contracts.md` | RFC 7807/9457 Problem Details, status code decision trees, field validation errors, error tracing, GraphQL and tRPC error formats |
| `references/pagination-filtering.md` | Offset, cursor, keyset pagination, Relay connections spec, sorting patterns, filtering operators, field selection |
| `references/auth-patterns.md` | API key design, JWT access+refresh pattern, OAuth 2.0 flows (Auth Code+PKCE, Client Credentials), RBAC, rate limiting algorithms |
