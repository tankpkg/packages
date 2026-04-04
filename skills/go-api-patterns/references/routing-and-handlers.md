# Routing and Handlers

Sources: go.dev (net/http, ServeMux, context, encoding/json), Chi documentation, Gin documentation, Echo documentation, Fiber documentation, Mat Ryer (How I write HTTP services in Go), Alex Edwards (Let's Go Further)

Covers: ServeMux and router selection, handler design, request decoding, response writing, route organization, versioning, validation boundaries, and transport-layer patterns for Go APIs.

## Start With net/http and ServeMux

Go 1.22 made `http.ServeMux` dramatically more capable. Method-aware patterns and wildcards remove most reasons to add a third-party router on day one.

```go
mux := http.NewServeMux()

mux.HandleFunc("GET /healthz", healthHandler)
mux.HandleFunc("GET /users/{id}", getUser)
mux.HandleFunc("POST /users", createUser)
mux.HandleFunc("PATCH /users/{id}", updateUser)
```

### What ServeMux Gives You Now

| Capability | ServeMux 1.22+ | Notes |
|-----------|----------------|-------|
| Method matching | Yes | `GET /path`, `POST /path` |
| Path params | Yes | `r.PathValue("id")` |
| Wildcards | Yes | `{path...}` patterns |
| Middleware | Yes | Wrap handlers with functions |
| Route groups | No | Emulate with helper functions |
| Named routes | No | Usually unnecessary in APIs |
| Ecosystem plugins | Limited | Prefer stdlib-compatible packages if needed |

Use ServeMux when you want portability, minimum dependencies, and easy onboarding for Go engineers.

## When to Add a Router

Use a third-party router only when it solves a real pain point.

| Signal | Use |
|--------|-----|
| Simple CRUD API, few route groups | ServeMux |
| Need nested route groups and per-group middleware | Chi |
| Want binding helpers and framework conventions | Gin |
| Need a balanced batteries-included router | Echo |
| Team strongly prefers Express-like ergonomics | Fiber |

### Framework Trade-offs

| Router | Strength | Cost |
|--------|----------|------|
| ServeMux | Zero deps, stdlib, portable | Fewer helper abstractions |
| Chi | Thin wrapper over net/http, composable middleware | Slightly more router DSL |
| Gin | Fast, many examples, binding helpers | Framework-specific context type |
| Echo | Pleasant API, solid middleware | More framework coupling |
| Fiber | Familiar to Node teams, fasthttp performance | Not stdlib-compatible |

If your service might move between frameworks, keep handlers framework-agnostic and adapt at the edge.

## Route Organization Patterns

### Pattern 1: Flat registration in small services

```go
func Routes(h *Handler) http.Handler {
    mux := http.NewServeMux()
    mux.HandleFunc("GET /healthz", h.Health)
    mux.HandleFunc("GET /users/{id}", h.GetUser)
    mux.HandleFunc("POST /users", h.CreateUser)
    return mux
}
```

### Pattern 2: Feature registrars in medium services

```go
func Routes(h *Handler) http.Handler {
    mux := http.NewServeMux()
    registerHealthRoutes(mux, h)
    registerUserRoutes(mux, h)
    registerOrderRoutes(mux, h)
    return mux
}
```

### Pattern 3: Router group packages in larger services

| Pattern | Use when | Benefit |
|--------|----------|---------|
| Flat `Routes()` | Under 15 endpoints | Fastest to understand |
| Feature registrar functions | 15-50 endpoints | Keeps packages cohesive |
| Dedicated route package per domain | 50+ endpoints, multiple teams | Reduces merge conflicts |

Do not build a giant `routes.go` file with 300 registrations.

## Handler Responsibilities

Handlers translate HTTP into application calls. Keep them thin.

### Handler should do

1. Read path/query/header/body input
2. Validate transport-level shape
3. Call one service method
4. Map result or error to HTTP response

### Handler should not do

| Anti-pattern | Move to |
|-------------|---------|
| Business rules | service package |
| SQL queries | repository package |
| Global state mutation | explicit dependency |
| Reusable auth logic | middleware |
| Cross-request caching | repository/service layer |

## Recommended Handler Signatures

### net/http

```go
func (h *Handler) GetUser(w http.ResponseWriter, r *http.Request) {
    id := r.PathValue("id")
    user, err := h.users.GetByID(r.Context(), id)
    if err != nil {
        writeError(w, err)
        return
    }
    writeJSON(w, http.StatusOK, user)
}
```

### Error-returning adapter pattern

```go
type AppHandler func(http.ResponseWriter, *http.Request) error

func Adapt(fn AppHandler) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        if err := fn(w, r); err != nil {
            writeError(w, err)
        }
    }
}
```

This pattern centralizes error translation and reduces duplicate boilerplate.

## Request Decoding Rules

Decode deliberately. Bad decoding logic is a common source of production bugs.

### JSON body decoding checklist

| Rule | Why |
|------|-----|
| Limit body size with `http.MaxBytesReader` | Prevent oversized payload abuse |
| Disallow unknown fields when schema is strict | Catch client drift early |
| Validate `Content-Type` | Avoid decoding the wrong payload |
| Decode once | Double-read causes empty bodies |
| Separate transport DTO from domain model | Prevent accidental field coupling |

```go
func decodeJSON[T any](w http.ResponseWriter, r *http.Request, dst *T) error {
    r.Body = http.MaxBytesReader(w, r.Body, 1<<20)

    if ct := r.Header.Get("Content-Type"); !strings.HasPrefix(ct, "application/json") {
        return NewAppError(http.StatusUnsupportedMediaType, "unsupported_media_type", "content type must be application/json", nil)
    }

    dec := json.NewDecoder(r.Body)
    dec.DisallowUnknownFields()

    if err := dec.Decode(dst); err != nil {
        return NewAppError(http.StatusBadRequest, "invalid_json", "invalid JSON body", err)
    }
    return nil
}
```

### Query parameter parsing

| Input type | Pattern |
|-----------|---------|
| Optional string | `r.URL.Query().Get("q")` |
| Integer | `strconv.Atoi(query.Get("page"))` with default |
| Boolean | `strconv.ParseBool(query.Get("active"))` |
| Repeated values | `r.URL.Query()["status"]` |
| Time | `time.Parse(time.RFC3339, value)` |

Wrap parsing in small helpers when repeated.

## Response Writing Rules

### Always set these deliberately

| Concern | Recommendation |
|---------|----------------|
| Content type | `application/json; charset=utf-8` |
| Status code | Write before body |
| Error shape | Stable envelope across endpoints |
| Empty success | `204 No Content` for deletes/no-body success |
| IDs for created resources | Return `201 Created` + resource or location |

```go
func writeJSON(w http.ResponseWriter, status int, v any) {
    w.Header().Set("Content-Type", "application/json; charset=utf-8")
    w.WriteHeader(status)
    _ = json.NewEncoder(w).Encode(v)
}
```

### Error envelope example

```json
{
  "error": {
    "code": "validation_failed",
    "message": "email is required"
  }
}
```

Do not invent a different error shape per endpoint.

## Versioning Strategies

| Strategy | Use when | Example |
|---------|----------|---------|
| URI versioning | Public APIs, simple rollout | `/v1/users` |
| Header versioning | Internal APIs with stable path conventions | `Accept-Version: 2` |
| No versioning | Internal services that change in lockstep | `/users` |

For most teams, URI versioning is the least surprising.

## Validation Boundary Rules

### Split validation into two layers

| Layer | What to validate |
|------|-------------------|
| Handler / transport | Required fields, field shape, enum membership, pagination limits |
| Service / domain | Business rules, uniqueness, authorization, cross-entity invariants |

Examples:

| Rule | Layer |
|------|------|
| `email` is not empty | Handler |
| `page` must be >= 1 | Handler |
| user cannot delete themselves | Service |
| order total must equal line-item sum | Service |

## Route-Level Anti-patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| Handlers call DB directly | Hard to test and reuse | Introduce service/repository |
| Shared mutable request globals | Data races, hidden coupling | Use context and explicit deps |
| Massive generic `HandleCRUD` functions | Impossible customization | Write explicit handlers |
| Framework-specific business logic | Hard migration path | Keep logic in services |
| Auto-binding domain structs directly from JSON | Security and coupling risk | Use request DTOs |

## Chi Example

```go
r := chi.NewRouter()
r.Use(RequestID)
r.Use(Logger)
r.Use(Recoverer)

r.Route("/users", func(r chi.Router) {
    r.Get("/", h.ListUsers)
    r.Post("/", h.CreateUser)
    r.Route("/{userID}", func(r chi.Router) {
        r.Get("/", h.GetUser)
        r.Patch("/", h.UpdateUser)
        r.Delete("/", h.DeleteUser)
    })
})
```

Chi is ideal when you want stdlib compatibility plus nicer grouping.

## Gin Example

```go
r := gin.New()
r.Use(gin.Recovery())
r.Use(GinLogger())

api := r.Group("/api")
users := api.Group("/users")
users.GET("/:id", getUser)
users.POST("", createUser)
```

Gin is productive, but avoid letting `*gin.Context` leak into service code.

## OpenAPI Integration Choices

| Approach | Best for |
|---------|----------|
| Generate from code annotations | Existing handler-first codebase |
| Define OpenAPI first, generate server stubs | Contract-first teams |
| Hand-maintained small spec | Simple public API |

Popular tools include `swag`, `oapi-codegen`, and `ogen`. Choose one and standardize.

## Routing Review Questions

1. Is this router choice solving a real problem or just team familiarity?
2. Are handlers still thin enough to stay transport-focused?
3. Would a route/group split improve reviewability before adding more abstractions?

## Handler Design Smells

| Smell | Why it matters |
|------|----------------|
| handler builds SQL and business logic together | weak maintainability |
| route tree hides auth or versioning semantics | poor API clarity |
| OpenAPI approach chosen ad hoc per endpoint | contract drift |

## Release Readiness Checklist

- [ ] Router choice matches actual complexity
- [ ] Handlers are thin and call services
- [ ] Request decoding limits body size and validates content type
- [ ] Response envelope is consistent across endpoints
- [ ] Validation boundaries are split between transport and domain
- [ ] Versioning strategy is explicit
- [ ] OpenAPI generation strategy is chosen if API is external
