# Deployment and Operations

Sources: discordgo v0.29.0 docs, YAGPDB deployment patterns, production bot analysis (2026), Go best practices

## Docker Deployment

### Multi-Stage Build (complete Dockerfile — Go builder + alpine)

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
# CGO_ENABLED=0 = statically linked; -ldflags="-s -w" strips debug info (~30% smaller)
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /bot ./cmd/bot

FROM alpine:3.19
RUN apk --no-cache add ca-certificates tzdata && \
    addgroup -S bot && adduser -S bot -G bot
USER bot
COPY --from=builder /bot /app/bot
ENTRYPOINT ["/app/bot"]
```

### Alpine vs Scratch vs Distroless

| Image | Size | Shell | CA Certs | Recommended For |
|-------|------|-------|----------|-----------------|
| Alpine | ~8 MB | Yes | Add manually | Development, debugging |
| Scratch | ~0 MB | No | Copy manually | Minimal production |
| Distroless (gcr.io/distroless/static) | ~2 MB | No | Included | Production default |

Distroless is the recommended production choice: no shell reduces attack surface, CA certificates are bundled, non-root by default. For scratch, copy `/etc/ssl/certs/ca-certificates.crt` from the builder stage.

### Docker Compose (bot + PostgreSQL + Redis)

```yaml
version: "3.9"
services:
  bot:
    build: .
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - DATABASE_URL=postgres://bot:${DB_PASSWORD}@postgres:5432/botdb?sslmode=disable
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres: { condition: service_healthy }
    networks: [bot-net]
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment: { POSTGRES_USER: bot, POSTGRES_PASSWORD: "${DB_PASSWORD}", POSTGRES_DB: botdb }
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U bot"], interval: 10s, timeout: 5s, retries: 5 }
    networks: [bot-net]
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes: [redisdata:/data]
    networks: [bot-net]
volumes: { pgdata: {}, redisdata: {} }
networks: { bot-net: {} }
```

## systemd Service

### Service File Template

Place at `/etc/systemd/system/discord-bot.service`. Store secrets in `/etc/discord-bot/env` (mode 0600, owned by root).

```ini
[Unit]
Description=Discord Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=discord-bot
WorkingDirectory=/opt/discord-bot
ExecStart=/opt/discord-bot/bot
Restart=on-failure
RestartSec=5s
EnvironmentFile=/etc/discord-bot/env
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/discord-bot/data
StandardOutput=journal
StandardError=journal
SyslogIdentifier=discord-bot

[Install]
WantedBy=multi-user.target
```

### Management Commands

```bash
sudo systemctl enable --now discord-bot
sudo journalctl -u discord-bot -f        # follow logs
sudo systemctl restart discord-bot       # after binary update
```

## Structured Logging

### log/slog (Go 1.21+ stdlib — recommended)

```go
// JSON for production aggregators; NewTextHandler for development
logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
slog.SetDefault(logger)
slog.Info("bot starting", "version", version, "shard_id", shardID)
slog.Error("command failed", "command", cmdName, "guild_id", guildID, "error", err)
```

### zap (high-performance structured logging)

```go
logger, _ := zap.NewProduction(); defer logger.Sync()
logger.Info("bot starting", zap.String("version", version), zap.Int("shard_id", shardID))
logger.Sugar().Infow("command executed", "command", name, "latency_ms", latency)
```

zap's zero-allocation design is 5-10x faster than slog. Use it when log throughput is a bottleneck (>10k events/sec).

### logrus (popular, compatible)

```go
log.SetFormatter(&log.JSONFormatter{})
log.WithFields(log.Fields{"guild_id": guildID, "command": cmdName}).Info("command executed")
```

logrus is in maintenance mode — prefer slog for new projects.

### Logging Best Practices for Discord Bots

Log at the interaction boundary, not inside every helper. Include guild ID, user ID, and command name on every entry. Never log message content — it may contain PII and violates Discord's developer policy.

```go
slog.Info("interaction handled", "command", i.ApplicationCommandData().Name,
    "guild_id", i.GuildID, "user_id", i.Member.User.ID,
    "duration_ms", time.Since(start).Milliseconds())
```

## Error Handling

### discordgo RESTError (error codes, type assertion)

Discord API errors return `*discordgo.RESTError`. Type-assert to inspect HTTP status and Discord error code.

```go
var restErr *discordgo.RESTError
if errors.As(err, &restErr) {
    slog.Error("discord api error", "status", restErr.Response.StatusCode, "code", restErr.Message.Code)
}
```

Common codes: 10003 (unknown channel), 10008 (unknown message), 50013 (missing permissions), 50035 (invalid form body).

### Always Respond to Interactions (even on error)

Discord requires a response within 3 seconds. If the handler returns without responding, the user sees "This interaction failed." Send an ephemeral error rather than silently failing.

```go
func respondWithError(s *discordgo.Session, i *discordgo.InteractionCreate, msg string) {
    s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
        Type: discordgo.InteractionResponseChannelMessageWithSource,
        Data: &discordgo.InteractionResponseData{Content: msg, Flags: discordgo.MessageFlagsEphemeral}})
}
```

For deferred interactions, use `FollowupMessageCreate` to deliver the error.

### Safe Handler Wrapper with recover() (critical for goroutine safety)

Handlers run in goroutines (`SyncEvents=false` default). A panic silently kills that goroutine — the interaction times out and the panic is invisible without recovery.

```go
func safeHandler(s *discordgo.Session, i *discordgo.InteractionCreate,
    fn func(*discordgo.Session, *discordgo.InteractionCreate)) {
    defer func() {
        if r := recover(); r != nil {
            slog.Error("handler panic", "panic", r, "stack", string(debug.Stack()),
                "command", i.ApplicationCommandData().Name, "guild_id", i.GuildID)
            respondWithError(s, i, "An internal error occurred.")
        }
    }()
    fn(s, i)
}
// Wrap every dispatch point
s.AddHandler(func(s *discordgo.Session, i *discordgo.InteractionCreate) {
    if h, ok := commandHandlers[i.ApplicationCommandData().Name]; ok {
        safeHandler(s, i, h)
    }
})
```

Apply the same pattern to non-interaction handlers. A panic in a `MessageCreate` handler silently drops that event.

### Custom Error Types

```go
type BotError struct {
    Code    string
    Message string // shown to user
    Err     error  // internal cause, logged not shown
}
func (e *BotError) Error() string { return e.Message }
func (e *BotError) Unwrap() error { return e.Err }
```

## Graceful Shutdown

### Signal Handling (os.Signal, signal.Notify)

Handle both `os.Interrupt` (Ctrl+C) and `syscall.SIGTERM` (Docker/systemd stop):

```go
stop := make(chan os.Signal, 1)
signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
<-stop; slog.Info("shutting down"); cleanup(s); s.Close()
```

### Command Cleanup on Shutdown (guild commands)

Guild-scoped commands persist across restarts. Delete them on shutdown during development; in production use `ApplicationCommandBulkOverwrite` at startup instead.

```go
for _, cmd := range registered {
    s.ApplicationCommandDelete(s.State.User.ID, guildID, cmd.ID)
}
```

### Context-Based Shutdown (arikawa pattern)

arikawa propagates `context.Context` throughout. Cancel the root context to trigger shutdown across all components.

```go
ctx, cancel := context.WithCancel(context.Background())
go func() {
    stop := make(chan os.Signal, 1)
    signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
    <-stop; cancel()
}()
if err := bot.Run(ctx); err != nil && !errors.Is(err, context.Canceled) {
    slog.Error("bot exited", "error", err); os.Exit(1)
}
```

### WaitGroup for Plugin Cleanup (YAGPDB pattern)

```go
var wg sync.WaitGroup
func startPlugin(ctx context.Context, p Plugin) {
    wg.Add(1)
    go func() { defer wg.Done(); p.Run(ctx); p.Stop() }()
}
// Shutdown: cancel() → wg.Wait() → s.Close()
```

## Goroutine Safety

### Handlers Run in Goroutines (SyncEvents=false)

discordgo dispatches each event to a new goroutine by default. Two `MessageCreate` events can execute simultaneously — any shared state must be protected. `SyncEvents=true` serializes all events; use only for debugging.

### Panic Recovery (recover + debug.Stack)

A panic in an unrecovered goroutine terminates the entire process. discordgo does not recover panics in handlers. Wrap every `go func()` call:

```go
go func() {
    defer func() {
        if r := recover(); r != nil {
            slog.Error("goroutine panic", "panic", r, "stack", string(debug.Stack()))
        }
    }()
    doWork()
}()
```

### Shared State Protection (sync.RWMutex)

```go
type Cache struct {
    mu     sync.RWMutex
    guilds map[string]*GuildData
}
func (c *Cache) Get(id string) (*GuildData, bool) {
    c.mu.RLock(); defer c.mu.RUnlock(); return c.guilds[id], c.guilds[id] != nil
}
func (c *Cache) Set(id string, data *GuildData) {
    c.mu.Lock(); defer c.mu.Unlock(); c.guilds[id] = data
}
```

Avoid holding locks across I/O operations.

### Channel-Based Communication

For serialized work (e.g., image generation queue), use a buffered channel:

```go
type Job struct{ Interaction *discordgo.InteractionCreate; Prompt string }
queue := make(chan Job, 100)
go func() { for job := range queue { sendResult(s, job.Interaction, processJob(job.Prompt)) } }()
queue <- Job{Interaction: i, Prompt: prompt}
```

## Sharding

### discordgo Built-In (ShardID, ShardCount)

```go
s, _ := discordgo.New("Bot " + token)
s.ShardID = shardID        // 0-indexed
s.ShardCount = totalShards // must match across all shards
s.Open()
```

Each shard maintains its own gateway connection.

### Multi-Process Sharding (YAGPDB dshardorchestrator)

YAGPDB uses `dshardorchestrator` to coordinate shards across multiple processes. The orchestrator assigns shard IDs, monitors health, and restarts failed shards. Use this pattern for bots in thousands of guilds where a single process cannot handle all gateway traffic.

### Shard Selection Formula ((guild_id >> 22) % total_shards)

Discord assigns guilds to shards deterministically: `shard_id = (guild_id >> 22) % total_shards`. Use this to route guild-specific operations to the correct shard process.

### When to Shard (2,500+ guilds)

Discord requires sharding at 2,500 guilds. Request the recommended count from `/gateway/bot`:
```go
gw, _ := s.GatewayBot() // gw.Shards is Discord's recommendation
```

## Rate Limit Handling

### Built-In Rate Limiter (per-bucket, global)

discordgo manages rate limits automatically via per-endpoint buckets and a global atomic int64 counter (50 req/sec). When a bucket is exhausted, discordgo sleeps until reset. `ShouldRetryOnRateLimit` defaults to `true`.

### Reaction Rate Limit (1/200ms hardcoded)

Discord enforces a hardcoded 1 reaction per 200ms not reflected in standard headers. discordgo applies this internally. Space bulk reactions with a 250ms sleep.

### ShouldRetryOnRateLimit
```go
s.ShouldRetryOnRateLimit = true // default
s.MaxRestRetries = 3            // retries on 5xx and rate limits
```
Increase `MaxRestRetries` for critical operations (moderation logs). Decrease for latency-sensitive paths.

## CI/CD (GitHub Actions)

### Build and Test Workflow

```yaml
name: CI
on: { push: { branches: [main] }, pull_request: {} }
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with: { go-version: "1.22", cache: true }
      - run: go mod download && go vet ./...
      - run: go test -race -coverprofile=coverage.out ./...
      - run: CGO_ENABLED=0 go build -o /dev/null ./cmd/bot
```

### Docker Build and Push

```yaml
name: Docker
on:
  push:
    branches: [main]
    tags: ["v*"]
jobs:
  docker:
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: "${{ github.actor }}", password: "${{ secrets.GITHUB_TOKEN }}" }
      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Environment Variable Checklist

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | Yes | Bot token from Discord Developer Portal |
| `DISCORD_APP_ID` | Yes | Application ID for command registration |
| `DISCORD_GUILD_ID` | Dev only | Guild ID for fast guild-scoped command registration |
| `DATABASE_URL` | If using DB | PostgreSQL connection string |
| `REDIS_URL` | If using Redis | Redis connection string |
| `LOG_LEVEL` | No | `debug`, `info`, `warn`, `error` (default: `info`) |
| `SHARD_ID` | If sharding | 0-indexed shard ID |
| `SHARD_COUNT` | If sharding | Total number of shards |
| `PORT` | If HTTP | Port for health check or webhook server |

## Production Checklist

- [ ] Token stored in environment variable or secrets manager, not in source
- [ ] Multi-stage Docker build with non-root user
- [ ] `restart: unless-stopped` in Compose or `Restart=on-failure` in systemd
- [ ] Graceful shutdown handles both `SIGTERM` and `SIGINT`
- [ ] All interaction handlers respond within 3 seconds or defer immediately
- [ ] `recover()` wraps every handler and manually spawned goroutine
- [ ] Shared state protected with `sync.RWMutex` or channel-based serialization
- [ ] Structured logging with guild ID and user ID on every entry
- [ ] No message content logged (PII / policy compliance)
- [ ] `ShouldRetryOnRateLimit=true` (default — verify it has not been disabled)
- [ ] Health check endpoint or liveness probe configured
- [ ] Database migrations run before bot starts (not inside bot process)
- [ ] `ApplicationCommandBulkOverwrite` used at startup instead of per-command registration
- [ ] Shard count requested from `/gateway/bot` for bots approaching 2,500 guilds
- [ ] CI pipeline runs `go vet` and `go test -race` on every pull request
