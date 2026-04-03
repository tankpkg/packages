# Project Layout

Sources: go.dev (Organizing a Go module), Donovan/Kernighan (The Go Programming Language), golang-standards/project-layout community convention, Mat Ryer (How I write HTTP services in Go), Bill Kennedy (Ardan Labs Service patterns)

Covers: directory structure for Go API servers, cmd/internal separation, package design principles, dependency injection without frameworks, and main() wiring patterns.

## Recommended Server Layout

```
myapi/
  cmd/
    api/
      main.go              # Entry point: wiring, server start, graceful shutdown
  internal/
    config/
      config.go            # Configuration loading
    handler/
      handler.go           # HTTP handler constructors
      user.go              # User-related handlers
      health.go            # Health/readiness endpoints
    service/
      user.go              # Business logic layer
    repository/
      user.go              # Database access layer
      postgres.go          # Database connection setup
    middleware/
      logging.go           # Request logging
      auth.go              # Authentication middleware
      recover.go           # Panic recovery
    model/
      user.go              # Domain types
      errors.go            # Application error types
  migrations/
    001_create_users.up.sql
    001_create_users.down.sql
  go.mod
  go.sum
  Dockerfile
  Makefile
```

## Why This Structure

### cmd/ Directory

Each subdirectory under `cmd/` is a separate `package main` binary. A single repository can produce multiple binaries:

```
cmd/
  api/main.go        # HTTP API server
  worker/main.go     # Background job processor
  migrate/main.go    # Database migration CLI
```

Keep main.go thin — it wires dependencies and starts the server. Business logic never lives here.

```go
// cmd/api/main.go
package main

import (
    "context"
    "log/slog"
    "os"

    "myapi/internal/config"
    "myapi/internal/handler"
    "myapi/internal/repository"
    "myapi/internal/service"
)

func main() {
    logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

    cfg, err := config.Load()
    if err != nil {
        logger.Error("failed to load config", "error", err)
        os.Exit(1)
    }

    db, err := repository.NewPostgresPool(context.Background(), cfg.DatabaseURL)
    if err != nil {
        logger.Error("failed to connect to database", "error", err)
        os.Exit(1)
    }
    defer db.Close()

    userRepo := repository.NewUserRepository(db)
    userSvc := service.NewUserService(userRepo, logger)
    h := handler.New(userSvc, logger)

    // Start server with graceful shutdown (see config-and-deployment.md)
    runServer(context.Background(), cfg, h.Routes(), logger)
}
```

### internal/ Directory

The `internal/` directory is enforced by the Go toolchain — packages inside `internal/` cannot be imported by code outside the module. Use it for everything that is not a reusable library.

| Subdirectory | Responsibility | Depends On |
|-------------|----------------|------------|
| `config/` | Load and validate configuration | Nothing |
| `model/` | Domain types, error types | Nothing |
| `repository/` | Database queries, data access | `model/` |
| `service/` | Business rules, orchestration | `model/`, `repository/` |
| `handler/` | HTTP request/response translation | `model/`, `service/` |
| `middleware/` | Cross-cutting HTTP concerns | `model/` (for context keys) |

### Dependency Direction

Dependencies flow inward: handler -> service -> repository -> database.

```
HTTP Request
    |
    v
[middleware] -> cross-cutting (logging, auth, recovery)
    |
    v
[handler]   -> parses request, calls service, writes response
    |
    v
[service]   -> business logic, validation, orchestration
    |
    v
[repository] -> database queries, external API calls
    |
    v
[database/external]
```

Never import handler from service, or service from repository.

## Package Design Principles

### Accept Interfaces, Return Structs

Define interfaces at the consumer side, not the provider side:

```go
// internal/service/user.go
package service

// UserStore defines what the service needs — declared HERE, not in repository
type UserStore interface {
    GetByID(ctx context.Context, id int64) (model.User, error)
    Create(ctx context.Context, u model.User) (int64, error)
}

type UserService struct {
    store  UserStore
    logger *slog.Logger
}

func NewUserService(store UserStore, logger *slog.Logger) *UserService {
    return &UserService{store: store, logger: logger}
}
```

The repository package returns a concrete struct that happens to satisfy the interface:

```go
// internal/repository/user.go
package repository

type UserRepository struct {
    db *pgxpool.Pool
}

func NewUserRepository(db *pgxpool.Pool) *UserRepository {
    return &UserRepository{db: db}
}

func (r *UserRepository) GetByID(ctx context.Context, id int64) (model.User, error) {
    // query implementation
}
```

### One Package Per Concept

Avoid packages named `util`, `common`, or `helpers`. Each package should have a clear, singular purpose. If a function does not belong to an existing package, it likely deserves its own.

| Bad | Good |
|-----|------|
| `util.FormatTime()` | `timeutil.Format()` or method on domain type |
| `common.Validate()` | `validate.Email()` |
| `helpers.GenerateID()` | `idgen.New()` |

### Avoid Package-Level State

Package-level variables create hidden coupling and make testing difficult:

```go
// Bad: package-level database connection
var db *sql.DB

func init() {
    db, _ = sql.Open("postgres", os.Getenv("DB_URL"))
}

// Good: explicit dependency injection
type Repository struct {
    db *sql.DB
}

func NewRepository(db *sql.DB) *Repository {
    return &Repository{db: db}
}
```

## Dependency Injection Without Frameworks

Go does not need DI frameworks. Constructor injection through main() is sufficient for most applications:

```go
func main() {
    // 1. Load config
    cfg := config.MustLoad()

    // 2. Create infrastructure
    db := mustConnectDB(cfg.DatabaseURL)
    cache := mustConnectRedis(cfg.RedisURL)
    logger := newLogger(cfg.LogLevel)

    // 3. Create repositories
    userRepo := repository.NewUserRepository(db)
    orderRepo := repository.NewOrderRepository(db, cache)

    // 4. Create services
    userSvc := service.NewUserService(userRepo, logger)
    orderSvc := service.NewOrderService(orderRepo, userSvc, logger)

    // 5. Create handlers
    h := handler.New(handler.Deps{
        Users:  userSvc,
        Orders: orderSvc,
        Logger: logger,
    })

    // 6. Start server
    srv := &http.Server{Addr: cfg.Addr, Handler: h.Routes()}
    // ... graceful shutdown
}
```

For large applications with 20+ dependencies, consider a struct to group related dependencies:

```go
type Deps struct {
    Users  service.UserService
    Orders service.OrderService
    Logger *slog.Logger
}
```

## When to Break This Layout

| Signal | Action |
|--------|--------|
| Tiny microservice (1-2 endpoints) | Flatten to single `main.go` + handlers in root |
| Library, not server | No `cmd/`, export packages from root |
| Monorepo with shared packages | Use top-level `pkg/` for shared code between modules |
| Rapid prototype | Start flat, refactor to layers when >500 lines |
| gRPC + HTTP in same service | Separate `internal/grpc/` and `internal/http/` transports |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Business logic in handlers | Handlers become untestable blobs | Extract to service layer |
| Global database variable | Hidden coupling, test interference | Inject via constructor |
| Circular imports | Package A imports B, B imports A | Introduce interface at boundary |
| Massive `main.go` (500+ lines) | Hard to navigate | Extract setup into helper functions |
| `models` package with 50 types | Grab-bag anti-pattern | Group by domain concept |
| Premature `pkg/` directory | Exported package nobody uses | Keep in `internal/` until needed externally |
