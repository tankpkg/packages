# State Management and Database Integration

Sources: poise data patterns, serenity TypeMap, Discord-TTS Bot, robbb, sqlx docs, DashMap/moka crate docs

Covers: Data struct pattern, shared state, database integration with sqlx,
connection pooling, migrations, concurrent collections, caching strategies.

## The Data Struct Pattern

Every poise bot shares state across commands through a user-defined `Data`
struct. This is the central state container for the entire bot.

### Basic Data Struct

```rust
pub struct Data {
    pub pool: sqlx::PgPool,
    pub reqwest: reqwest::Client,
    pub start_time: std::time::Instant,
}
```

### Production Data Struct

```rust
use dashmap::DashMap;
use mini_moka::sync::Cache;
use std::sync::Arc;
use tokio::sync::RwLock;

pub struct Data {
    // Database
    pub pool: sqlx::PgPool,

    // HTTP clients
    pub reqwest: reqwest::Client,

    // Concurrent state (no lock needed)
    pub guild_prefixes: DashMap<serenity::GuildId, String>,
    pub cooldowns: DashMap<serenity::UserId, std::time::Instant>,

    // TTL-based cache
    pub user_cache: Cache<serenity::UserId, CachedUser>,

    // Rarely-updated shared state
    pub config: Arc<RwLock<BotConfig>>,

    // Metrics
    pub start_time: std::time::Instant,
    pub commands_executed: std::sync::atomic::AtomicU64,
}
```

### Accessing Data in Commands

```rust
#[poise::command(slash_command)]
async fn stats(ctx: Context<'_>) -> Result<(), Error> {
    let data = ctx.data();
    let uptime = data.start_time.elapsed();
    let commands = data.commands_executed.load(std::sync::atomic::Ordering::Relaxed);
    ctx.say(format!("Uptime: {:.0?}, Commands: {}", uptime, commands)).await?;
    Ok(())
}
```

### Initialization

```rust
.setup(|ctx, _ready, framework| {
    Box::pin(async move {
        poise::builtins::register_globally(ctx, &framework.options().commands).await?;

        let pool = sqlx::PgPool::connect(&std::env::var("DATABASE_URL")?).await?;
        sqlx::migrate!("./migrations").run(&pool).await?;

        Ok(Data {
            pool,
            reqwest: reqwest::Client::new(),
            guild_prefixes: DashMap::new(),
            cooldowns: DashMap::new(),
            user_cache: Cache::builder()
                .time_to_live(std::time::Duration::from_secs(300))
                .max_capacity(10_000)
                .build(),
            config: Arc::new(RwLock::new(BotConfig::load()?)),
            start_time: std::time::Instant::now(),
            commands_executed: std::sync::atomic::AtomicU64::new(0),
        })
    })
})
```

## Database Integration with sqlx

### Connection Pool Setup

```rust
use sqlx::postgres::PgPoolOptions;

let pool = PgPoolOptions::new()
    .max_connections(20)     // 10-20 for most Discord bots
    .min_connections(5)      // Keep warm connections
    .acquire_timeout(std::time::Duration::from_secs(5))
    .idle_timeout(std::time::Duration::from_secs(600))
    .max_lifetime(std::time::Duration::from_secs(1800))
    .connect(&database_url)
    .await?;
```

### SQLite Alternative

```toml
sqlx = { version = "0.8", features = ["sqlite", "runtime-tokio-rustls", "macros"] }
```

```rust
let pool = sqlx::SqlitePool::connect("sqlite:bot.db").await?;
```

### Compile-Time Checked Queries

sqlx validates queries against the database at compile time:

```rust
#[derive(sqlx::FromRow)]
struct GuildConfig {
    guild_id: i64,
    prefix: String,
    welcome_channel: Option<i64>,
    log_channel: Option<i64>,
}

async fn get_guild_config(
    pool: &sqlx::PgPool,
    guild_id: i64,
) -> Result<Option<GuildConfig>, sqlx::Error> {
    sqlx::query_as!(
        GuildConfig,
        "SELECT guild_id, prefix, welcome_channel, log_channel
         FROM guild_configs WHERE guild_id = $1",
        guild_id
    )
    .fetch_optional(pool)
    .await
}

async fn upsert_guild_prefix(
    pool: &sqlx::PgPool,
    guild_id: i64,
    prefix: &str,
) -> Result<(), sqlx::Error> {
    sqlx::query!(
        "INSERT INTO guild_configs (guild_id, prefix)
         VALUES ($1, $2)
         ON CONFLICT (guild_id) DO UPDATE SET prefix = $2",
        guild_id,
        prefix
    )
    .execute(pool)
    .await?;
    Ok(())
}
```

### Migrations

```bash
# Create migration
sqlx migrate add initial_schema

# migrations/001_initial_schema.sql
CREATE TABLE guild_configs (
    guild_id BIGINT PRIMARY KEY,
    prefix VARCHAR(10) NOT NULL DEFAULT '!',
    welcome_channel BIGINT,
    log_channel BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE user_data (
    user_id BIGINT PRIMARY KEY,
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    last_message TIMESTAMPTZ
);

CREATE TABLE warnings (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    moderator_id BIGINT NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_warnings_guild_user ON warnings(guild_id, user_id);
```

Run migrations in code:

```rust
sqlx::migrate!("./migrations").run(&pool).await?;
```

### Transaction Pattern

```rust
async fn transfer_xp(
    pool: &sqlx::PgPool,
    from: i64,
    to: i64,
    amount: i32,
) -> Result<(), sqlx::Error> {
    let mut tx = pool.begin().await?;

    sqlx::query!("UPDATE user_data SET xp = xp - $1 WHERE user_id = $2", amount, from)
        .execute(&mut *tx).await?;
    sqlx::query!("UPDATE user_data SET xp = xp + $1 WHERE user_id = $2", amount, to)
        .execute(&mut *tx).await?;

    tx.commit().await?;
    Ok(())
}
```

## Concurrent Collections

### DashMap (Lock-Free Concurrent HashMap)

3-5x faster than `Arc<RwLock<HashMap>>` for concurrent workloads.

```rust
use dashmap::DashMap;

let prefixes: DashMap<GuildId, String> = DashMap::new();

// Insert
prefixes.insert(guild_id, "!".to_string());

// Read (returns Ref guard, not clone)
if let Some(prefix) = prefixes.get(&guild_id) {
    println!("Prefix: {}", prefix.value());
}

// Atomic update
prefixes.entry(guild_id)
    .and_modify(|p| *p = "?".to_string())
    .or_insert_with(|| "!".to_string());

// Remove
prefixes.remove(&guild_id);
```

### When to Use Each Collection

| Collection | Use Case |
|-----------|----------|
| `DashMap<K, V>` | Frequent concurrent reads/writes, per-guild/user state |
| `Arc<RwLock<T>>` | Read-heavy, rarely updated config or global state |
| `Arc<Mutex<T>>` | Write-heavy or simple exclusive access |
| `AtomicU64` | Counters, flags |
| `tokio::sync::mpsc` | Message passing between tasks |
| `tokio::sync::broadcast` | Event bus (multiple consumers) |

## Caching with mini-moka

TTL-based in-memory cache. Entries auto-expire, preventing memory leaks.

```rust
use mini_moka::sync::Cache;
use std::time::Duration;

let cache: Cache<UserId, UserProfile> = Cache::builder()
    .max_capacity(10_000)
    .time_to_live(Duration::from_secs(300))    // Expire after 5 min
    .time_to_idle(Duration::from_secs(120))    // Expire if unused for 2 min
    .build();

// Cache-aside pattern
async fn get_profile(
    data: &Data,
    user_id: UserId,
) -> Result<UserProfile, Error> {
    // Check cache
    if let Some(profile) = data.user_cache.get(&user_id) {
        return Ok(profile);
    }

    // Cache miss — fetch from DB
    let profile = sqlx::query_as!(
        UserProfile,
        "SELECT * FROM user_profiles WHERE user_id = $1",
        user_id.get() as i64
    )
    .fetch_one(&data.pool)
    .await?;

    // Store in cache
    data.user_cache.insert(user_id, profile.clone());
    Ok(profile)
}
```

## Serenity Cache

Serenity maintains an in-memory cache of Discord state (guilds, channels,
members, roles) populated from gateway events.

```rust
// Access cached guild
if let Some(guild) = ctx.cache().guild(guild_id) {
    println!("Guild: {} ({} members)", guild.name, guild.member_count);
}

// Access cached channel
if let Some(channel) = ctx.cache().channel(channel_id) {
    println!("Channel: {}", channel.name);
}

// Current user
let me = ctx.cache().current_user().clone();

// Cache settings (limit memory)
use serenity::cache::Settings as CacheSettings;

let settings = CacheSettings::default()
    .max_messages(100);  // Cap message cache

let client = serenity::ClientBuilder::new(token, intents)
    .cache_settings(settings)
    .await?;
```

### Cache vs HTTP

| Operation | Use Cache | Use HTTP |
|-----------|-----------|----------|
| Guild/channel/role info | Frequently accessed, OK if slightly stale | Need guaranteed-fresh data |
| Permission calculations | Cache provides member/role data | — |
| Member list | If GUILD_MEMBERS intent enabled | Large guilds, paginated |
| Message history | Only if temp_cache enabled, limited | Full history needed |
| Creating/modifying resources | — | Always (mutations require HTTP) |

## Serenity TypeMap (Raw Serenity)

For raw serenity (without poise), use TypeMap for shared state:

```rust
use serenity::prelude::TypeMapKey;

struct DatabasePool;
impl TypeMapKey for DatabasePool {
    type Value = sqlx::PgPool;
}

// Store in client setup
let client = Client::builder(token, intents)
    .type_map_insert::<DatabasePool>(pool)
    .await?;

// Access in event handler
async fn message(&self, ctx: Context, msg: Message) {
    let data = ctx.data.read().await;
    let pool = data.get::<DatabasePool>().unwrap();
    // use pool...
}
```

With poise, prefer the Data struct — it is type-safe and avoids runtime
downcast errors.

## Background Tasks

For periodic operations (cache cleanup, status rotation, scheduled unmutes):

```rust
// In setup, spawn background tasks
.setup(|ctx, _ready, framework| {
    Box::pin(async move {
        let data = Data { /* ... */ };

        // Status rotation
        let ctx_clone = ctx.clone();
        tokio::spawn(async move {
            let statuses = [
                serenity::ActivityData::watching("for /help"),
                serenity::ActivityData::playing("with Rust"),
            ];
            let mut i = 0;
            loop {
                ctx_clone.set_activity(Some(statuses[i % statuses.len()].clone()));
                i += 1;
                tokio::time::sleep(std::time::Duration::from_secs(60)).await;
            }
        });

        // Database cleanup
        let pool = data.pool.clone();
        tokio::spawn(async move {
            loop {
                tokio::time::sleep(std::time::Duration::from_secs(3600)).await;
                let _ = sqlx::query!("DELETE FROM temp_data WHERE expires_at < NOW()")
                    .execute(&pool).await;
            }
        });

        Ok(data)
    })
})
```
