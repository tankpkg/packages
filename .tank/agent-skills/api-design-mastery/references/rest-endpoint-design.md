# REST Endpoint Design

Sources: IETF RFC 7231 (HTTP/1.1 Semantics), RFC 9110 (HTTP Semantics), RFC 5988 (Web Linking), OpenAPI Specification 3.1, Roy Fielding REST dissertation (2000, public)

Covers: resource modeling, URL naming, HTTP method semantics, status codes, idempotency, content negotiation, request/response conventions.

## Resource Modeling

REST organizes APIs around resources — things, not actions. A resource is any concept worth naming: a user, an order, a document, a search result.

### URL Structure Rules

Use nouns, not verbs. The HTTP method expresses the action; the URL identifies the resource:

```
✅  GET /orders/42
✅  DELETE /orders/42
❌  GET /getOrder?id=42
❌  POST /deleteOrder
```

Hierarchy in URLs expresses ownership, not nesting for its own sake:

```
/users/{userId}/orders       → orders belonging to a user
/orders/{orderId}/items      → line items within an order
/orders/{orderId}            → flat form — use when order stands alone
```

Avoid nesting deeper than two levels. Past two levels, use a flat resource with a filter parameter:

```
❌  /users/{id}/orders/{id}/items/{id}/reviews
✅  /reviews?item_id={id}
```

| Resource Type | URL Pattern | Example |
|--------------|-------------|---------|
| Collection | `/resources` | `/users` |
| Singleton | `/resources/{id}` | `/users/42` |
| Sub-collection | `/resources/{id}/sub` | `/users/42/orders` |
| Action on resource | `/resources/{id}/action` | `/orders/42/cancel` |
| Search / filter | `/resources?param=val` | `/users?status=active` |

### Naming Conventions

- Lowercase, hyphen-separated: `/user-profiles`, not `/UserProfiles` or `/user_profiles`
- Plural nouns for collections: `/orders`, not `/order`
- No trailing slash: `/users/42`, not `/users/42/`
- No file extensions: `/users/42`, not `/users/42.json`
- IDs in path for specific resources; query params for filtering, sorting, pagination

## HTTP Method Semantics

| Method | Purpose | Idempotent | Safe | Body |
|--------|---------|-----------|------|------|
| GET | Retrieve resource or collection | Yes | Yes | No |
| POST | Create resource or submit data | No | No | Yes |
| PUT | Full replacement of resource | Yes | No | Yes |
| PATCH | Partial update | No (by default) | No | Yes |
| DELETE | Remove resource | Yes | No | No |
| HEAD | Same as GET but no response body | Yes | Yes | No |
| OPTIONS | Describe supported methods (CORS) | Yes | Yes | No |

**PUT vs PATCH:**

PUT requires the client to send the complete resource representation. The server replaces the stored resource entirely. Use PUT when the client controls the full state.

PATCH sends only the fields to change. Use PATCH for partial updates where sending the whole object is impractical.

**POST for actions:**

When an operation doesn't map cleanly to CRUD, model it as an action resource:

```http
POST /orders/42/cancel
POST /invoices/99/send
POST /users/7/verify-email
```

Return the updated resource in the response body so clients don't need a follow-up GET.

**Idempotency keys for POST:**

POST is not idempotent by default. For operations where duplicate execution is harmful (payments, order creation), support an idempotency key:

```http
POST /payments
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{ "amount": 5000, "currency": "usd" }
```

Cache the response keyed by the Idempotency-Key value for at least 24 hours. Return the cached response on duplicate requests.

## HTTP Status Codes

### 2xx Success

| Code | Name | When to Use |
|------|------|-------------|
| 200 | OK | GET, PUT, PATCH success with response body |
| 201 | Created | POST created a new resource; include `Location` header with new resource URL |
| 202 | Accepted | Async operation queued; include polling URL in body or `Location` |
| 204 | No Content | DELETE success; PUT/PATCH when no body needed |

Always include a `Location` header with 201:

```http
HTTP/1.1 201 Created
Location: /orders/42
Content-Type: application/json

{ "id": 42, "status": "pending", ... }
```

### 3xx Redirection

| Code | Name | When to Use |
|------|------|-------------|
| 301 | Moved Permanently | URL permanently changed; update bookmarks |
| 304 | Not Modified | Conditional GET — cached response is still valid |

### 4xx Client Errors

| Code | Name | When to Use |
|------|------|-------------|
| 400 | Bad Request | Malformed syntax, unparseable JSON |
| 401 | Unauthorized | Missing or invalid credentials (not authenticated) |
| 403 | Forbidden | Authenticated but lacks permission for this resource |
| 404 | Not Found | Resource doesn't exist (or hidden for privacy) |
| 405 | Method Not Allowed | HTTP method not supported; include `Allow` header |
| 409 | Conflict | State conflict — duplicate email, optimistic lock mismatch |
| 410 | Gone | Resource existed and was permanently removed |
| 422 | Unprocessable Entity | Valid syntax but fails business validation |
| 429 | Too Many Requests | Rate limit exceeded; include `Retry-After` |

**401 vs 403:** 401 means the request lacks valid credentials — the user is not authenticated. 403 means the user is authenticated but doesn't have permission. Never return 401 for an authenticated user who lacks access.

**404 vs 410:** Use 404 when the resource never existed at this URL or its existence shouldn't be revealed. Use 410 when the resource definitively existed and has been permanently deleted.

**400 vs 422:** Use 400 for requests the server cannot parse. Use 422 when the JSON is valid but the content violates business rules (missing required field, invalid enum value, duplicate entry).

### 5xx Server Errors

| Code | Name | When to Use |
|------|------|-------------|
| 500 | Internal Server Error | Unexpected server failure — log with trace ID, return safe message |
| 502 | Bad Gateway | Upstream dependency failed |
| 503 | Service Unavailable | Overloaded or in maintenance; include `Retry-After` |
| 504 | Gateway Timeout | Upstream timed out |

Never leak stack traces, file paths, or SQL errors in 5xx responses.

## Content Negotiation

Clients declare what they can accept via the `Accept` header; servers declare what they're sending via `Content-Type`:

```http
GET /reports/42
Accept: application/json, application/xml;q=0.9
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

Return `406 Not Acceptable` if the server cannot satisfy the `Accept` header.

Default to `application/json` when no `Accept` is specified.

For error responses, use `Content-Type: application/problem+json` (RFC 9457).

## Request and Response Conventions

### Field Naming

Pick one casing convention and apply it uniformly across the entire API:

- `snake_case` — common in Python/Ruby ecosystems and JSON APIs
- `camelCase` — common in JavaScript ecosystems

Mixing within the same API breaks client code generators and creates confusing SDK APIs.

### Timestamps

Always use ISO 8601 in UTC:

```json
{ "created_at": "2024-03-15T10:30:00Z", "expires_at": "2024-04-15T10:30:00Z" }
```

Never return Unix timestamps as the primary format — they lose timezone context and are unreadable.

### Empty Collections

Always return an empty array, never `null`, for empty collections:

```json
{ "orders": [] }      ✅
{ "orders": null }    ❌
```

### Response Envelopes

Return single resources directly, without a wrapper:

```json
{ "id": 42, "name": "Alice", "email": "alice@example.com" }
```

Use an envelope for collections only when pagination metadata is needed:

```json
{
  "data": [ { "id": 1 }, { "id": 2 } ],
  "pagination": { "has_next": true, "next_cursor": "..." }
}
```

Do not add envelopes just for consistency — they add nesting without value on single resources.

### Conditional Requests and Caching

Support ETags for cacheable resources:

```http
HTTP/1.1 200 OK
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d"
Cache-Control: max-age=3600
```

On subsequent request:

```http
GET /users/42
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d"
```

Server returns `304 Not Modified` if unchanged, saving bandwidth and processing.

## HATEOAS (Hypermedia Links)

Level 3 REST includes links to related actions in the response, enabling clients to discover API operations without hardcoded URLs:

```json
{
  "id": 42,
  "status": "pending",
  "_links": {
    "self": { "href": "/orders/42" },
    "cancel": { "href": "/orders/42/cancel", "method": "POST" },
    "items": { "href": "/orders/42/items" }
  }
}
```

Only include links to actions that are currently available (e.g., don't include `cancel` if status is `shipped`). This is the most valuable aspect of hypermedia — encoding current valid state transitions.

Use the `Link` header for pagination to avoid requiring clients to construct URLs:

```http
Link: </users?after=eyJpZCI6NDJ9>; rel="next", </users?before=eyJpZCI6MX0=>; rel="prev"
```

Hypermedia adds value in stable, long-lived APIs. For rapid internal APIs, skip it.

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Verbs in URLs (`/getUser`, `/createOrder`) | Redundant with HTTP method | Nouns only: `/users`, `/orders` |
| `POST /users/delete` | Wrong method for semantics | `DELETE /users/{id}` |
| Nesting 3+ levels deep | Fragile, hard to consume | Flatten with query params |
| Returning `200 OK` with error body | Breaks HTTP clients, proxies, caches | Correct status code always |
| `null` instead of `[]` for empty lists | Forces null checks in every client | Always return empty array |
| Inconsistent field naming (mixed `camelCase` and `snake_case`) | Breaks code generators | One convention, applied everywhere |
| API key in URL query param | Logged in access logs, cached by proxies | `Authorization` header only |
| Different error format per endpoint | Clients must special-case every route | Uniform error format (see `references/error-contracts.md`) |
