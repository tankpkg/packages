# Middleware and Errors

Sources: go.dev (net/http, context, errors), Mat Ryer (How I write HTTP services in Go), Alex Edwards (Let's Go Further), Chi documentation, Gin documentation, Uber Go style guide

Covers: middleware chaining, request-scoped values, logging, auth, recovery, timeouts, CORS, rate limiting, AppError design, error mapping, and panic recovery patterns for Go APIs.

## Middleware Contract

The standard contract is simple and powerful:

```go
type Middleware func(http.Handler) http.Handler
```

### Why this contract wins

| Reason | Benefit |
|-------|---------|
| Uses stdlib `http.Handler` | Works with ServeMux and most routers |
| Composable | Chain behaviors predictably |
| Testable | Wrap a stub handler and assert result |
| Portable | Middleware can move between frameworks |

Avoid framework-specific middleware when your service could outlive the framework choice.

## Recommended Middleware Order

Order matters. A good default stack is:

1. Request ID
2. Real IP / proxy correction
3. Logger
4. Recovery
5. Timeout
6. CORS
7. Authentication
8. Authorization (route-scoped where possible)
9. Rate limiting

### Why this order

| Middleware | Why it sits here |
|-----------|-------------------|
| Request ID | Every later log line should include it |
| Logger | Should observe the full request lifecycle |
| Recovery | Must catch panics from everything after it |
| Timeout | Should wrap expensive work downstream |
| Auth | Should run before business logic |
| Rate limiting | Before auth for public endpoints, after auth for per-user quotas |

## Chain Helpers

```go
func Chain(h http.Handler, mws ...Middleware) http.Handler {
    for i := len(mws) - 1; i >= 0; i-- {
        h = mws[i](h)
    }
    return h
}
```

Use helper composition instead of manually nesting handlers in `main()`.

## Context Rules

Use `context.Context` only for request-scoped values.

### Good context values

| Value | Okay? |
|------|-------|
| request ID | Yes |
| authenticated user ID | Yes |
| trace/span info | Yes |
| cancellation/deadline | Yes |

### Bad context values

| Value | Why not |
|------|---------|
| database pool | dependency, not request data |
| logger root instance | inject directly |
| config struct | dependency, not request data |
| feature flags service | dependency, not request data |

### Context key pattern

```go
type contextKey string

const requestIDKey contextKey = "request_id"

func WithRequestID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, requestIDKey, id)
}
```

Do not use raw strings as keys in shared packages.

## Logging Middleware

### What to log for every request

| Field | Why |
|------|-----|
| method | Debugging and dashboards |
| path | Route-specific analysis |
| status | Error rate and health |
| duration | Latency tracking |
| request_id | Traceability |
| remote_ip | Security and abuse review |
| user_id (if authenticated) | User-specific debugging |

```go
func Logger(log *slog.Logger) Middleware {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            start := time.Now()
            rw := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
            next.ServeHTTP(rw, r)
            log.Info("request_complete",
                "method", r.Method,
                "path", r.URL.Path,
                "status", rw.status,
                "duration_ms", time.Since(start).Milliseconds(),
            )
        })
    }
}
```

## Recovery Middleware

Recovery is the last line of defense, not your normal error path.

```go
func Recover(log *slog.Logger) Middleware {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            defer func() {
                if rec := recover(); rec != nil {
                    log.Error("panic_recovered", "panic", rec)
                    writeJSON(w, http.StatusInternalServerError, map[string]any{
                        "error": map[string]string{"code": "internal_error", "message": "internal server error"},
                    })
                }
            }()
            next.ServeHTTP(w, r)
        })
    }
}
```

### Panic policy

| Situation | Correct action |
|----------|----------------|
| JSON validation failure | return error |
| DB not found | return error |
| Nil pointer bug | panic + recover middleware logs it |
| Impossible invariant broken | panic or fatal at startup |

## Authentication Middleware

Auth middleware should do one thing: establish identity or reject.

### Responsibilities

1. Read token/cookie/header
2. Validate signature and claims
3. Put identity into context
4. Stop request on failure

### Non-responsibilities

| Anti-pattern | Better place |
|-------------|--------------|
| permission checks | handler/service authorization logic |
| role-to-policy mapping | domain service or policy layer |
| DB-heavy user hydration on every route | lazy-load only when needed |

## Timeout Middleware

Use `context.WithTimeout` or `http.TimeoutHandler` carefully.

| Approach | Use when | Caveat |
|---------|----------|--------|
| `context.WithTimeout` in middleware | Your handlers respect context | Best control |
| `http.TimeoutHandler` | Simple handlers, coarse timeout | Generic timeout body only |
| Per-operation timeout inside service | External calls vary | More granular |

Timeouts are useless if DB queries or downstream HTTP calls ignore context.

## CORS Rules

### Safe defaults

| Setting | Recommendation |
|--------|----------------|
| Allowed origins | Explicit allowlist |
| Methods | Exact methods used |
| Headers | Exact headers used |
| Credentials | Only when needed |
| Wildcard with credentials | Never |

Do not ship `Access-Control-Allow-Origin: *` together with credentials.

## Rate Limiting Patterns

| Strategy | Good for |
|---------|----------|
| IP-based fixed window | Public unauthenticated endpoints |
| User-based token bucket | Authenticated APIs |
| Route-specific limits | Login, signup, password reset |
| Global upstream gateway limits | Edge protection |

Keep rate limiting close to the edge when possible, but preserve app-level controls for sensitive endpoints.

## Error Design Goals

Your API error system should satisfy four constraints:

1. Stable machine-readable code
2. Human-readable message
3. HTTP status mapping
4. Underlying error retained for logs and wrapping

### AppError pattern

```go
type AppError struct {
    Code    string
    Message string
    Status  int
    Err     error
}

func (e *AppError) Error() string { return e.Message }
func (e *AppError) Unwrap() error { return e.Err }
```

### Constructor helper

```go
func NewAppError(status int, code, message string, err error) *AppError {
    return &AppError{Status: status, Code: code, Message: message, Err: err}
}
```

## Error Mapping Table

| Situation | Status | Code |
|----------|--------|------|
| Invalid JSON | 400 | `invalid_json` |
| Validation failure | 400 | `validation_failed` |
| Missing auth | 401 | `unauthorized` |
| Permission denied | 403 | `forbidden` |
| Resource not found | 404 | `not_found` |
| Unique conflict | 409 | `conflict` |
| Downstream dependency timeout | 504 | `upstream_timeout` |
| Unknown internal problem | 500 | `internal_error` |

Do not overload `400` for everything.

## Sentinel vs typed errors

| Pattern | Use when |
|--------|----------|
| Sentinel error (`var ErrNotFound`) | Simple, shared conditions |
| Typed errors | Need structured metadata |
| AppError wrapper | HTTP boundary translation |

Use `errors.Is` and `errors.As`, not string matching.

## Error Adapter Pattern

```go
func writeError(w http.ResponseWriter, err error) {
    var appErr *AppError
    if errors.As(err, &appErr) {
        writeJSON(w, appErr.Status, map[string]any{
            "error": map[string]string{
                "code": appErr.Code,
                "message": appErr.Message,
            },
        })
        return
    }

    writeJSON(w, http.StatusInternalServerError, map[string]any{
        "error": map[string]string{
            "code": "internal_error",
            "message": "internal server error",
        },
    })
}
```

This keeps handlers focused on domain outcomes rather than response formatting.

## Logging and Error Interaction

### Log once at the boundary

| Layer | Log? |
|------|------|
| repository | Only on unusual low-level diagnostics |
| service | Usually no |
| handler/adapter | Yes, final request failure |

Double-logging the same error bloats logs and confuses alerts.

## Common Middleware Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| Writing response after `next` without recorder | No status/body visibility | Wrap ResponseWriter |
| Swallowing panic without logging stack | Impossible postmortems | Log stack or structured panic details |
| Injecting dependencies via context | Hidden coupling | Constructor injection |
| Returning raw DB errors to clients | Leaks internals | Map to AppError |
| Putting auth and authz in same middleware | Hard reuse and testing | Split identity from permission checks |

## Release Readiness Checklist

- [ ] Middleware order is intentional and documented
- [ ] Request IDs exist before logging starts
- [ ] Recovery middleware turns panics into safe 500 responses
- [ ] Context carries only request-scoped values
- [ ] Auth middleware establishes identity only
- [ ] Error codes are stable and machine-readable
- [ ] Logs record failures once at the HTTP boundary
