# Error Contracts

Sources: RFC 9457 (Problem Details for HTTP APIs, 2023), RFC 7807 (Problem Details, 2016), RFC 7231 (HTTP Status Codes), OWASP API Security Top 10

Covers: RFC 9457 Problem Details format, HTTP status code selection, machine-readable error codes, field validation errors, error tracing, GraphQL error format, tRPC error mapping.

## Why Standardize Error Responses

Most APIs invent a custom error format per team, per service, or per endpoint. Clients end up writing bespoke parsing logic for every API they consume. RFC 9457 defines a standard structure — `application/problem+json` — that any client can understand without custom handling.

Adopt this format once. Every error across your entire API becomes predictable.

## RFC 9457 Problem Details

### Core Structure

```http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{
  "type": "https://api.example.com/problems/user-not-found",
  "title": "User Not Found",
  "status": 404,
  "detail": "No user with ID 42 exists in the system.",
  "instance": "/users/42"
}
```

### Field Reference

| Field | Required | Type | Purpose |
|-------|----------|------|---------|
| `type` | Yes | URI | Identifies the problem type. Must be stable — same type, same URI. Should be dereferenceable (documentation URL). |
| `title` | Yes | String | Short, stable human-readable summary. Must NOT change between occurrences of the same type. |
| `status` | Yes | Integer | HTTP status code. Must match the actual HTTP response status. |
| `detail` | No | String | Human-readable explanation specific to this occurrence. May include context (amounts, IDs, field names). |
| `instance` | No | URI | URI identifying this specific error occurrence. Useful for log correlation. Can be relative. |

**`title` is stable; `detail` is instance-specific.** The `title` for a `user-not-found` problem is always "User Not Found". The `detail` says "No user with ID 42 exists". Never put instance data in `title`.

### Custom Extensions

RFC 9457 allows additional fields beyond the core five. Add domain-specific data as top-level fields:

```json
{
  "type": "https://api.example.com/problems/insufficient-balance",
  "title": "Insufficient Balance",
  "status": 402,
  "detail": "Your balance of $30.00 is insufficient for this $50.00 charge.",
  "instance": "/accounts/123/charges/abc",
  "current_balance": 3000,
  "required_amount": 5000,
  "topup_url": "https://api.example.com/accounts/123/topup"
}
```

Document all custom extensions in your API reference under the problem type URI.

### Machine-Readable Error Codes

HTTP status codes alone aren't granular enough for client logic. Add a `code` extension with a stable, machine-readable identifier:

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation Error",
  "status": 422,
  "code": "VALIDATION_ERROR",
  "detail": "One or more fields failed validation.",
  "errors": [ ... ]
}
```

Code naming rules:
- `SCREAMING_SNAKE_CASE`
- Namespace by domain when helpful: `USER_EMAIL_TAKEN`, `ORDER_ALREADY_SHIPPED`
- Treat codes as a public API — once published, never change or remove them
- Clients may hardcode checks: `if (error.code === 'USER_EMAIL_TAKEN') { showEmailError() }`

## HTTP Status Code Selection

### Selecting a 4xx Code

| Situation | Code | Notes |
|-----------|------|-------|
| Cannot parse request (bad JSON, wrong Content-Type) | 400 | Request is structurally broken |
| Valid syntax, fails business validation | 422 | Field required, value out of range, enum invalid |
| No credentials provided or credentials invalid | 401 | User is not authenticated |
| Authenticated, lacks permission | 403 | Authenticated but forbidden |
| Resource not found | 404 | Also acceptable for hiding existence of sensitive resources |
| HTTP method not supported | 405 | Include `Allow: GET, POST` header |
| Duplicate / state conflict | 409 | Email already taken, concurrent edit collision |
| Resource permanently deleted | 410 | Existed before; now gone permanently |
| Rate limit exceeded | 429 | Include `Retry-After` header |

**400 vs 422:** Reserve 400 for requests the server cannot parse at all. Use 422 when the JSON parses correctly but the content violates validation rules. Many teams use 400 for both — pick one convention and apply it consistently.

**401 vs 403:** 401 means "I don't know who you are." 403 means "I know who you are, and you can't do this." Never return 401 for an authenticated user who lacks permission — it misleads clients into retrying with different credentials.

### Selecting a 5xx Code

| Situation | Code |
|-----------|------|
| Unhandled server exception | 500 |
| Upstream service returned an error | 502 |
| Server overloaded, in maintenance | 503 |
| Upstream timed out | 504 |

On any 5xx: log the full error server-side with a trace ID. Return only a safe message to the client — no stack traces, no file paths, no SQL queries.

## Field Validation Errors

For 422 responses with multiple invalid fields, include an `errors` array:

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation Error",
  "status": 422,
  "code": "VALIDATION_ERROR",
  "detail": "2 fields failed validation.",
  "errors": [
    {
      "field": "email",
      "code": "EMAIL_ALREADY_TAKEN",
      "message": "This email address is already registered."
    },
    {
      "field": "password",
      "code": "TOO_SHORT",
      "message": "Password must be at least 8 characters.",
      "min_length": 8,
      "actual_length": 5
    }
  ]
}
```

Field error conventions:
- `field`: JSON path to the invalid field. Use dot notation for nested fields (`address.postcode`) and bracket notation for arrays (`items[0].quantity`).
- `code`: Machine-readable, stable error code for this specific violation.
- `message`: Human-readable, field-specific explanation. Safe to display in UI.
- Add domain-relevant extensions (min/max values, allowed values list) where useful.

## Error Tracing

Generate a unique ID for every request server-side. Log the full error with that ID. Return it in both a response header and the error body:

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/problem+json
X-Request-Id: 8f14e45f-ceea-467a-a866-cd6d5e2e4d02

{
  "type": "https://api.example.com/problems/internal-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred. Quote request ID 8f14e45f-ceea-467a-a866-cd6d5e2e4d02 when contacting support.",
  "instance": "/orders/99",
  "request_id": "8f14e45f-ceea-467a-a866-cd6d5e2e4d02"
}
```

Log everything server-side: exception class, stack trace, request method, path, body, user ID, timestamp, request ID. Return nothing sensitive to the client.

## Rate Limit Error Pattern

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/problem+json
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706745600
Retry-After: 60

{
  "type": "https://api.example.com/problems/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "You have sent 1000 requests in the past minute. Try again in 60 seconds.",
  "limit": 1000,
  "window_seconds": 60,
  "retry_after_seconds": 60,
  "reset_at": "2024-02-01T12:00:00Z"
}
```

Always include `Retry-After` on 429 — clients need to know when to back off.

## GraphQL Error Format

GraphQL uses a standard `errors` array in the response body, separate from `data`:

```json
{
  "data": { "user": null, "posts": [ ... ] },
  "errors": [
    {
      "message": "User not found",
      "locations": [ { "line": 2, "column": 3 } ],
      "path": [ "user" ],
      "extensions": {
        "code": "NOT_FOUND",
        "http": { "status": 404 }
      }
    }
  ]
}
```

GraphQL error rules:
- Always include `code` in `extensions` for machine-readable handling.
- Use `extensions.http.status` to control the HTTP status code (Apollo Server respects this).
- `message` must be client-safe — no stack traces, no internal details.
- `data` and `errors` can both be present simultaneously (partial success).
- Mask unexpected server errors in production: catch unhandled exceptions and re-throw as a generic `INTERNAL_SERVER_ERROR` with a safe message.

## tRPC Error Format

tRPC serializes errors from `TRPCError` automatically:

```typescript
// Throwing
throw new TRPCError({
  code: 'NOT_FOUND',
  message: 'User not found',
  cause: originalDbError,  // logged server-side, NOT sent to client
});

// Client receives (JSON-RPC format):
// {
//   "error": {
//     "json": {
//       "message": "User not found",
//       "code": -32004,
//       "data": { "code": "NOT_FOUND", "httpStatus": 404, "path": "users.getById" }
//     }
//   }
// }
```

| TRPCError code | HTTP Status |
|---------------|------------|
| BAD_REQUEST | 400 |
| UNAUTHORIZED | 401 |
| FORBIDDEN | 403 |
| NOT_FOUND | 404 |
| CONFLICT | 409 |
| TOO_MANY_REQUESTS | 429 |
| INTERNAL_SERVER_ERROR | 500 |

Use the `errorFormatter` in `initTRPC` to expose Zod field errors to the client for form validation.

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `200 OK` with error in body | Breaks HTTP caches, proxies, monitoring | Correct status code on every error |
| No `Content-Type: application/problem+json` | Clients can't detect error format | Always set content type on error responses |
| Stack trace in response | Exposes internals, security risk | Log server-side; return opaque message |
| No request ID | Cannot correlate client report to server log | Generate UUID per request; include in response |
| Changing error codes after publishing | Breaks client code | Treat codes as immutable public API |
| Different error shape per endpoint | Forces bespoke client parsing | One format, every error, every endpoint |
| Generic message ("An error occurred") | Useless for debugging | Include specific, actionable `detail` |
| Undocumented `type` URIs | Clients can't discover meaning | Make type URIs dereferenceable (link to docs) |
