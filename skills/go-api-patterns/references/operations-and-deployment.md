# Operations and Deployment

Sources: go.dev (slog, os/signal, net/http), Alex Edwards (Let's Go Further), Docker documentation, Twelve-Factor App methodology, OpenTelemetry documentation, Prometheus instrumentation guides

Covers: configuration loading, structured logging with slog, request IDs, health endpoints, graceful shutdown, Docker builds, runtime tuning, observability basics, and deployment checklists for Go APIs.

## Configuration Rules

Load configuration once at startup, validate it, and pass a typed struct through your application.

```go
type Config struct {
    Addr        string
    DatabaseURL string
    LogLevel    string
    Environment string
}
```

### Configuration priorities

| Source | Use for |
|-------|---------|
| Environment variables | Production runtime config |
| `.env` files | Local development only |
| Flags | Ad-hoc overrides, CLIs |
| Config files | Large local/dev settings if truly needed |

Prefer env vars for services. Add Viper only if you genuinely need file formats, env expansion, and multiple config sources.

## Validation at Startup

Fail startup if critical config is missing.

| Config | Validate |
|-------|----------|
| `ADDR` | non-empty, parsable host:port |
| `DATABASE_URL` | non-empty, expected scheme |
| `LOG_LEVEL` | one of debug/info/warn/error |
| `ENVIRONMENT` | known environment value |

Do not let the server boot half-configured.

## slog Defaults

Use `log/slog` unless you have a strong reason otherwise.

```go
func newLogger(level slog.Level) *slog.Logger {
    opts := &slog.HandlerOptions{Level: level}
    return slog.New(slog.NewJSONHandler(os.Stdout, opts))
}
```

### JSON vs text logging

| Format | Use when |
|-------|----------|
| JSON | Production, log aggregation, structured analysis |
| Text | Local development |

### Standard fields to include

| Field | Why |
|------|-----|
| service | Multi-service log aggregation |
| environment | Filter by env |
| version | Release diagnosis |
| request_id | Request traceability |
| user_id | Authenticated debugging |

## Request ID Strategy

Generate or propagate a request ID at the edge.

### Rules

1. Accept upstream request ID headers from trusted gateways
2. Generate one if missing
3. Store it in context
4. Include it in every log line and error response if appropriate

### Minimal pattern

| Concern | Recommendation |
|--------|----------------|
| Header name | `X-Request-ID` |
| Generation | UUID or ULID |
| Context storage | typed key |
| Logging | include on every request-complete log |

## Health Endpoints

Expose separate liveness and readiness endpoints.

| Endpoint | Purpose |
|---------|---------|
| `/healthz` | Process is alive |
| `/readyz` | Process can serve traffic |

### What readiness should check

| Dependency | Check |
|-----------|-------|
| DB | lightweight ping or query |
| Cache | optional, if critical |
| Queue | optional, only if serving depends on it |

Liveness should remain cheap. Do not make it depend on every downstream service.

## Graceful Shutdown

Handle SIGTERM and SIGINT explicitly.

```go
ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
defer stop()

go func() {
    <-ctx.Done()
    shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    _ = srv.Shutdown(shutdownCtx)
}()
```

### Shutdown checklist

1. Stop accepting new requests
2. Allow in-flight requests to finish within timeout
3. Close DB pool
4. Flush logs/traces if needed
5. Exit non-zero only on real failure

### Common mistakes

| Mistake | Consequence |
|--------|-------------|
| Using `Close()` instead of `Shutdown()` | In-flight requests dropped |
| Too short timeout | Valid work interrupted |
| No signal handling | K8s or systemd kills abruptly |

## Dockerfile Pattern

```dockerfile
FROM golang:1.24 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/api ./cmd/api

FROM gcr.io/distroless/static-debian12
COPY --from=build /out/api /api
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/api"]
```

### Build rules

| Rule | Why |
|------|-----|
| Multi-stage build | Smaller runtime image |
| `CGO_ENABLED=0` when possible | Easier static binary |
| Non-root runtime user | Better container security |
| Copy only built binary | Smaller attack surface |

## Runtime Environment Patterns

| Environment | Typical deployment |
|------------|--------------------|
| Local dev | `go run` or air/reflex hot reload |
| CI | `go test ./...`, lint, race detector as needed |
| Containerized prod | Docker/Kubernetes/ECS |
| PaaS | Render/Fly/Heroku-like |
| Binary deploy | systemd on VM |

Go gives you flexibility. Keep runtime assumptions minimal.

## Metrics Basics

Start with low-cardinality service metrics.

### Minimum useful metrics

| Metric | Type |
|-------|------|
| request count by route/method/status | counter |
| request duration by route/method | histogram |
| active DB pool stats | gauge |
| background job failures | counter |

### Cardinality warnings

| Bad label | Why bad |
|---------|---------|
| raw URL path with IDs | Explodes metric series |
| user ID | Unbounded cardinality |
| email | PII and huge series count |

Prefer route templates (`/users/{id}`), not concrete paths.

## Tracing Basics

Distributed tracing matters once your request crosses service boundaries.

| Use tracing when | Example |
|------------------|---------|
| One request hits DB + queue + external API | checkout flow |
| Multiple internal services cooperate | microservices |
| Latency debugging is difficult from logs alone | sporadic slow requests |

Use OpenTelemetry if your org already standardizes on it.

## OpenAPI and Contract Ops

Choose a single contract workflow:

| Workflow | Best for |
|---------|----------|
| Annotation-driven generation | Handler-first teams |
| Contract-first generation | Public APIs and platform teams |
| Minimal hand-written spec | Small services |

Whichever you choose, include it in CI. Broken docs are production bugs.

## Release Pipeline Checklist

1. `go test ./...`
2. `go vet ./...`
3. Lint (e.g. `golangci-lint run`)
4. Optional race detector in slower CI job
5. Build binary
6. Build container
7. Run smoke test against container

### Recommended CI split

| Stage | Purpose |
|------|---------|
| Fast PR checks | unit tests, lint, build |
| Slower merge checks | integration tests, race detector |
| Release | tag, image build, deploy |

## Common Ops Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| Logging in plain text in production | Hard to search/aggregate | Use JSON handler |
| No readiness endpoint | Bad rollouts | Add `/readyz` |
| Environment variables read ad hoc across packages | Config drift | Centralize in config package |
| No request ID propagation | Hard incident triage | Generate at edge and log it |
| Huge all-in-one Docker image | Slow deploys and larger attack surface | Multi-stage minimal runtime |

## Production Defaults Worth Copying

| Concern | Default |
|--------|---------|
| Listen address | `:8080` |
| Shutdown timeout | 10 seconds |
| Log format | JSON in prod |
| Health endpoints | `/healthz`, `/readyz` |
| Timeout middleware | 1-5 seconds by route class |
| Request ID header | `X-Request-ID` |

## Release Readiness Checklist

- [ ] Config is loaded once and validated at startup
- [ ] `slog` is configured with structured fields
- [ ] Request IDs are generated or propagated
- [ ] Liveness and readiness endpoints exist
- [ ] Server handles SIGTERM with graceful shutdown
- [ ] Docker image is multi-stage and non-root
- [ ] Metrics avoid high-cardinality labels
- [ ] OpenAPI workflow is automated if the API is public
