# State and Database

Sources: discordgo v0.29.0 docs, YAGPDB architecture, automuteus patterns, ops-bot-iii (entgo), SD bot (repositories), production bot analysis (2026)

## The Bot Struct Pattern

Handlers registered with `discordgo.AddHandler` receive only `*discordgo.Session` and the event. To access databases, caches, loggers, or config, close over a struct that holds all dependencies — the universal pattern across every production Go Discord bot.

### Basic Bot Struct (Session, Config)

For simple bots, two fields suffice: `session *discordgo.Session` and `config *Config`. Register handlers as methods on the struct so the config is accessible via the receiver.

### Production Bot Struct (Session, DB Pool, Redis, Logger, Config)

```go
type Bot struct {
    session  *discordgo.Session
    db       *pgxpool.Pool
    redis    *redis.Client
    log      *slog.Logger
    config   *Config
    cache    *cache.Cache   // go-cache for in-memory TTL
    mu       sync.RWMutex  // guards mutable fields below
    guilds   map[string]*GuildState
    commands map[string]CommandHandler
    queue    chan *WorkItem // buffered work queue (SD bot pattern)
}
```

Fields set once at startup (session, db, redis, log, config) need no lock. `mu` guards only fields written after construction.

### Dependency Injection via Constructor

```go
func New(cfg *Config, log *slog.Logger) (*Bot, error) {
    s, err := discordgo.New("Bot " + cfg.Token)
    if err != nil { return nil, fmt.Errorf("create session: %w", err) }
    pool, err := NewPool(context.Background(), cfg.DatabaseURL)
    if err != nil { return nil, err }
    rdb := redis.NewClient(&redis.Options{Addr: cfg.RedisAddr})
    if err := rdb.Ping(context.Background()).Err(); err != nil {
        return nil, fmt.Errorf("ping redis: %w", err)
    }
    b := &Bot{
        session: s, db: pool, redis: rdb, log: log, config: cfg,
        cache: cache.New(5*time.Minute, 10*time.Minute),
        guilds: make(map[string]*GuildState),
        commands: registerCommands(),
        queue: make(chan *WorkItem, 50),
    }
    s.AddHandler(b.onInteractionCreate)
    s.AddHandler(b.onGuildCreate)
    s.Identify.Intents = discordgo.IntentsGuilds | discordgo.IntentsGuildMessages
    return b, nil
}
```

### Accessing State in Handlers

Register methods, not standalone functions. The method receiver carries all dependencies without globals.

```go
func (b *Bot) onInteractionCreate(s *discordgo.Session, i *discordgo.InteractionCreate) {
    if i.Type != discordgo.InteractionApplicationCommand {
        return
    }
    handler, ok := b.commands[i.ApplicationCommandData().Name]
    if !ok { return }
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    if err := handler(ctx, s, i); err != nil {
        b.log.Error("command error", "err", err)
    }
}
```

## Database Integration

### database/sql + pgx (PostgreSQL)

Use `pgx/v5` as the driver with the standard `database/sql` interface for portability across ORMs and tools. For direct pgx usage without `database/sql`, use `pgxpool` (see Connection Pool Setup).

```go
import _ "github.com/jackc/pgx/v5/stdlib"

db, err := sql.Open("pgx", os.Getenv("DATABASE_URL"))
db.SetMaxOpenConns(25)
db.SetMaxIdleConns(5)
db.SetConnMaxLifetime(5 * time.Minute)
```

### sqlx (Named Queries, Struct Scanning)

`sqlx` wraps `database/sql` and adds struct scanning and named parameters — the lightest upgrade from raw SQL.

```go
type GuildConfig struct {
    GuildID string `db:"guild_id"`
    Prefix  string `db:"prefix"`
    Enabled bool   `db:"enabled"`
}

// GetContext scans a single row into a struct
var cfg GuildConfig
err := b.sqlx.GetContext(ctx, &cfg,
    `SELECT guild_id, prefix, enabled FROM guild_configs WHERE guild_id = $1`, guildID)
if errors.Is(err, sql.ErrNoRows) {
    return nil, ErrNotFound
}

// NamedExecContext maps struct fields to :param placeholders
_, err = b.sqlx.NamedExecContext(ctx, `
    INSERT INTO guild_configs (guild_id, prefix, enabled)
    VALUES (:guild_id, :prefix, :enabled)
    ON CONFLICT (guild_id) DO UPDATE SET prefix = EXCLUDED.prefix
`, cfg)
```

### GORM (Full ORM)

GORM suits bots that want ActiveRecord-style queries. Avoid `AutoMigrate` in production; use golang-migrate instead.

```go
type Warning struct {
    gorm.Model
    GuildID string `gorm:"index;not null"`
    UserID  string `gorm:"index;not null"`
    Reason  string
}

db, _ := gorm.Open(postgres.Open(dsn), &gorm.Config{})
var warnings []Warning
db.WithContext(ctx).Where("guild_id = ? AND user_id = ?", guildID, userID).Find(&warnings)
```

### entgo (Code-Generated Type-Safe ORM — ops-bot-iii Pattern)

`ent` generates a full type-safe client from schema definitions. ops-bot-iii uses this for compile-time query safety. Define fields in `ent/schema/`, run `go generate ./ent/...`, then store the generated client on the Bot struct as `b.ent`.

```go
warnings, err := b.ent.Warning.
    Query().
    Where(warning.GuildID(guildID), warning.UserID(userID)).
    All(ctx)
```

### sqlboiler (Code-Gen ORM — YAGPDB Pattern)

YAGPDB generates models from an existing database schema. The workflow is schema-first: write migrations, then regenerate with `sqlboiler psql --output internal/models`. Zero-reflection queries; the schema is the source of truth.

```go
guilds, err := models.Guilds(
    models.GuildWhere.OwnerID.EQ(userID),
    qm.Limit(10),
).All(ctx, db)
```

### SQLite for Prototypes

For single-server bots or local development, `modernc.org/sqlite` (pure Go, no CGO) is the simplest option. Enable WAL mode for concurrent reads; switch to PostgreSQL before deploying to multiple servers.

```go
import _ "modernc.org/sqlite"
db, err := sql.Open("sqlite", "bot.db?_journal=WAL&_timeout=5000")
```

## Connection Pool Setup (pgxpool)

`pgxpool` handles connection lifecycle, health checks, and context cancellation. Close on shutdown: `defer b.db.Close()`.

```go
func NewPool(ctx context.Context, dsn string) (*pgxpool.Pool, error) {
    cfg, err := pgxpool.ParseConfig(dsn)
    if err != nil { return nil, fmt.Errorf("parse dsn: %w", err) }
    cfg.MaxConns = 20
    cfg.MinConns = 2
    cfg.MaxConnLifetime = 30 * time.Minute
    cfg.MaxConnIdleTime = 5 * time.Minute
    cfg.ConnConfig.ConnectTimeout = 5 * time.Second
    pool, err := pgxpool.NewWithConfig(ctx, cfg)
    if err != nil { return nil, fmt.Errorf("create pool: %w", err) }
    pingCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
    return pool, pool.Ping(pingCtx)
}

## Migration Patterns

### golang-migrate

Run migrations programmatically at startup. Name files `000001_create_guilds.up.sql` / `000001_create_guilds.down.sql`.

```go
m, err := migrate.New("file://migrations", dsn)
if err != nil {
    return err
}
if err := m.Up(); err != nil && !errors.Is(err, migrate.ErrNoChange) {
    return fmt.Errorf("migrate: %w", err)
}
```

### Atlas

Atlas provides schema diffing and declarative migrations. Define the target schema in HCL or SQL, generate migration files with `atlas migrate diff --env local`. Integrates with entgo via `entc.WithAtlas(true)`.

## Redis Integration

### go-redis for Caching and Session State

```go
rdb := redis.NewClient(&redis.Options{
    Addr: cfg.RedisAddr, DialTimeout: 3 * time.Second, PoolSize: 10,
})

// Set with TTL
data, _ := json.Marshal(cfg)
b.redis.Set(ctx, "guild:"+cfg.GuildID+":config", data, 10*time.Minute)

// Get with miss detection
data, err := b.redis.Get(ctx, "guild:"+guildID+":config").Bytes()
if errors.Is(err, redis.Nil) {
    return nil, ErrCacheMiss
}
var cfg GuildConfig
json.Unmarshal(data, &cfg)
```

### Distributed Locking (redislock)

Prevent duplicate processing when multiple bot instances handle the same event. `redislock.ErrNotObtained` means another instance holds the lock — return nil and skip.

```go
locker := redislock.New(b.redis)

lock, err := locker.Obtain(ctx, "lock:"+key, 30*time.Second, nil)
if errors.Is(err, redislock.ErrNotObtained) {
    return nil
}
defer lock.Release(ctx)
```

### Multi-Shard State via Redis

When running multiple shards as separate processes (YAGPDB pattern), store shared state in Redis rather than in-process maps. Use `Incr` for atomic counters and `Publish`/`Subscribe` for cross-shard event fanout.

## In-Memory State

### sync.Map for Concurrent Collections

`sync.Map` suits collections with many concurrent readers and infrequent writes, such as active voice connections or per-guild rate limiters. For frequent writes, a plain `map` protected by `sync.RWMutex` is faster.

```go
b.voiceConns.Store(guildID, vc)
v, ok := b.voiceConns.Load(guildID)
if ok {
    vc := v.(*discordgo.VoiceConnection)
    _ = vc
}
```

### sync.RWMutex for Bot Struct Fields

```go
func (b *Bot) SetGuildState(guildID string, state *GuildState) {
    b.mu.Lock(); defer b.mu.Unlock()
    b.guilds[guildID] = state
}
func (b *Bot) GetGuildState(guildID string) (*GuildState, bool) {
    b.mu.RLock(); defer b.mu.RUnlock()
    return b.guilds[guildID], b.guilds[guildID] != nil
}
```

Never hold a lock while calling discordgo API methods — those make HTTP requests and will block other goroutines.

### go-cache for TTL-Based Caching

`github.com/patrickmn/go-cache` provides an in-process cache with per-item TTL and background eviction. Use it as an L1 cache in front of Redis or the database. Init with `cache.New(defaultTTL, cleanupInterval)`.

```go
if v, found := b.cache.Get("guild:" + guildID); found {
    return v.(*GuildConfig), nil
}
cfg, err := b.GetGuildConfig(ctx, guildID)
if err == nil {
    b.cache.Set("guild:"+guildID, cfg, cache.DefaultExpiration)
}
return cfg, err
```

## Background Goroutines

All background goroutines follow the same pattern: receive a `context.Context`, select on `ctx.Done()` to exit, and use a ticker or channel for work. Call them after `session.Open()`.

### Status Rotation

```go
func (b *Bot) startStatusRotation(ctx context.Context) {
    statuses := []string{"with Go", "/help", "over 42 servers"}
    ticker := time.NewTicker(30 * time.Second)
    go func() {
        defer ticker.Stop()
        for i := 0; ; i++ {
            select {
            case <-ctx.Done():
                return
            case <-ticker.C:
                b.session.UpdateGameStatus(0, statuses[i%len(statuses)])
            }
        }
    }()
}
```

### Periodic Cleanup Tasks

Same ticker pattern as status rotation. Replace `UpdateGameStatus` with the cleanup call and set the interval to `1 * time.Hour`.

### Scheduled Tasks with Auto-Restart (ops-bot-iii Pattern)

ops-bot-iii wraps each scheduled task in a restart loop so a panic or error does not kill the goroutine permanently.

```go
func runWithRestart(ctx context.Context, log *slog.Logger, name string, fn func(context.Context) error) {
    go func() {
        for {
            if err := fn(ctx); err != nil {
                log.Error("task exited", "task", name, "err", err)
            }
            select {
            case <-ctx.Done():
                return
            case <-time.After(5 * time.Second):
            }
        }
    }()
}

runWithRestart(ctx, b.log, "cleanup", b.cleanupLoop)
runWithRestart(ctx, b.log, "metrics", b.metricsLoop)
```

### Channel-Based Work Queues (SD Bot Pattern)

The Stable Diffusion Discord bot uses a buffered channel so slow operations (image generation, LLM calls) are processed serially while the interaction handler returns immediately.

```go
// Worker goroutine — started once at bot startup
func (b *Bot) startWorker(ctx context.Context) {
    go func() {
        for {
            select {
            case <-ctx.Done():
                return
            case item := <-b.queue:
                b.processItem(item)
            }
        }
    }()
}

// Handler — defers, enqueues, returns
func (b *Bot) onGenerateCommand(s *discordgo.Session, i *discordgo.InteractionCreate) {
    s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
        Type: discordgo.InteractionResponseDeferredChannelMessageWithSource,
    })
    select {
    case b.queue <- &WorkItem{Interaction: i}:
    default:
        s.FollowupMessageCreate(i.Interaction, true, &discordgo.WebhookParams{Content: "Queue is full."})
    }
}
```

The `select` default case rejects overflow without blocking. Size the buffer to the maximum acceptable backlog.

## Context Propagation

### discordgo Has No Context (Workaround with Goroutine + Timeout)

discordgo handlers receive no `context.Context`. Create a timeout context at the handler boundary and pass it into all downstream calls. For long-running operations, defer first, then do the work in a goroutine with its own context.

```go
// Short command — create context at handler boundary
func (b *Bot) onInteractionCreate(s *discordgo.Session, i *discordgo.InteractionCreate) {
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    cfg, _ := b.GetGuildConfigCached(ctx, i.GuildID) // ctx flows to db/redis
    _ = cfg
}

// Slow command — defer, then goroutine with its own context
func (b *Bot) handleSlowCommand(s *discordgo.Session, i *discordgo.InteractionCreate) {
    s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
        Type: discordgo.InteractionResponseDeferredChannelMessageWithSource,
    })
    go func() {
        ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
        defer cancel()
        result, err := b.doSlowWork(ctx)
        if err != nil {
            result = "Something went wrong."
        }
        s.FollowupMessageCreate(i.Interaction, true, &discordgo.WebhookParams{Content: result})
    }()
}
```

### arikawa Is Context-First

If context propagation is a hard requirement, arikawa passes `context.Context` through its entire API surface — every handler, REST call, and state query accepts a context. No workaround needed.

```go
func (b *Bot) onMessage(ctx context.Context, e *gateway.MessageCreateEvent) {
    cfg, _ := b.db.GetGuildConfig(ctx, e.GuildID.String()) // ctx flows naturally
    _ = cfg
}
```
Choose arikawa when building bots that require strict timeout budgets or OpenTelemetry tracing across all operations.
