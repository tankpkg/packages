---
name: "@tank/go-api-patterns"
description: |
  Production Go HTTP API development covering the full stack: net/http and
  ServeMux routing (Go 1.22+), third-party routers (Chi, Gin, Echo, Fiber),
  middleware patterns (logging, auth, recovery, CORS, rate limiting),
  context.Context propagation, structured logging with slog, error handling
  strategies, database access (pgx, sqlx, ent), configuration management
  (environment variables, Viper), graceful shutdown, project layout
  (cmd/internal/pkg), testing with httptest and table-driven tests, OpenAPI
  integration, and Docker multi-stage deployment.

  Synthesizes Donovan/Kernighan (The Go Programming Language), go.dev official
  documentation (Effective Go, Module Layout), Chi/Gin/Echo documentation,
  Mat Ryer API patterns, and Go standard library reference.

  Trigger phrases: "go api", "go rest api", "go http server", "go backend",
  "go middleware", "go chi", "go gin", "go echo", "go fiber", "go router",
  "go project structure", "go project layout", "go slog", "go pgx", "go sqlx",
  "go httptest", "go graceful shutdown", "go context", "go error handling",
  "go docker", "go api testing", "go ServeMux", "net/http", "go api patterns"
---

# Go API Patterns

## Core Philosophy

1. **Standard library first** — net/http is production-grade. Reach for a framework only when it saves significant boilerplate (route groups, parameter binding). A thin router like Chi adds value; a full framework adds coupling.
2. **Explicit over magic** — Pass dependencies as constructor arguments, not globals. Use context.Context for request-scoped values, not package-level state. Wire things visibly in main().
3. **Errors are values** — Return errors, wrap them with %w for context, handle them at the boundary. Panics are for programmer bugs, not business logic. Middleware recovers from panics; handlers return errors.
4. **Composition over inheritance** — Build middleware as func(http.Handler) http.Handler. Stack behaviors by chaining, not by inheriting from a base controller. The http.Handler interface is the universal contract.
5. **Fail fast at startup, gracefully at runtime** — Validate configuration, ping databases, and bind ports at startup. At runtime, drain connections on SIGTERM, respect context cancellation, and shut down cleanly.

## Quick-Start: Common Problems

### "How do I structure a Go API project?"

```
cmd/api/main.go          # Wiring, server startup, graceful shutdown
internal/handler/         # HTTP handlers (transport layer)
internal/service/         # Business logic
internal/repository/      # Database access
internal/middleware/       # Custom middleware
internal/config/          # Configuration loading
```

Keep all Go packages in `internal/` to prevent external imports.
-> See `references/project-layout.md`

### "Which router should I use?"

| Need | Router |
|------|--------|
| Minimal API, Go 1.22+ | net/http ServeMux with method patterns |
| Route groups, middleware chain, chi ecosystem | Chi |
| Maximum performance, binding, validation | Gin |
| Balanced API, middleware, WebSocket | Echo |
| Fiber/Express-like, fasthttp-based | Fiber |

-> See `references/routing-and-handlers.md`

### "How do I write middleware?"

```go
func Logger(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        next.ServeHTTP(w, r)
        slog.Info("request", "method", r.Method, "path", r.URL.Path, "dur", time.Since(start))
    })
}
```

-> See `references/middleware-and-errors.md`

### "How do I handle errors consistently?"

1. Define an AppError type with status code + message + underlying error
2. Write a handler adapter that returns error instead of writing directly
3. Convert AppError to JSON response in the adapter
-> See `references/middleware-and-errors.md`

### "How do I test my API?"

1. Use httptest.NewRecorder() for unit tests
2. Use httptest.NewServer() for integration tests
3. Table-driven tests with subtests for each endpoint
-> See `references/data-and-testing.md`

## Decision Trees

### Router Selection

| Signal | Choice |
|--------|--------|
| Go 1.22+, simple CRUD, few routes | net/http ServeMux |
| Need route groups, param middleware | Chi (net/http compatible) |
| High-throughput, JSON binding/validation built-in | Gin |
| WebSocket support, HTTP/2, clean API | Echo |
| Coming from Node/Express, want fasthttp | Fiber |

### Database Library

| Signal | Choice |
|--------|--------|
| Maximum control, raw SQL, connection pool tuning | pgx (PostgreSQL) |
| Multiple databases, struct scanning, named params | sqlx |
| Code-generated type-safe queries | sqlc |
| ORM with schema-as-code, graph traversal | ent |
| Simple key-value or document store | database/sql + driver |

### Error Strategy

| Signal | Approach |
|--------|----------|
| Simple API, few error types | Sentinel errors + HTTP status mapping |
| Complex domain, rich errors | Custom AppError type with codes |
| Multi-service, error chaining | Wrapped errors with errors.Is/As |

## Reference Index

| File | Contents |
|------|----------|
| `references/project-layout.md` | Directory structure, cmd/internal separation, package design, dependency injection, and composition rules |
| `references/routing-and-handlers.md` | net/http ServeMux (Go 1.22+), Chi, Gin, Echo, Fiber comparison, handler signatures, request decoding, response writing, route organization |
| `references/middleware-and-errors.md` | Middleware chaining, logging, auth, recovery, CORS, timeouts, AppError design, panic recovery, consistent HTTP error responses |
| `references/data-and-testing.md` | pgx, sqlx, sqlc, ent, repository boundaries, transactions, connection pools, httptest, table-driven tests, integration tests, and testcontainers |
| `references/operations-and-deployment.md` | Environment config, slog, request IDs, graceful shutdown, health probes, Docker builds, runtime tuning, and observability basics |
