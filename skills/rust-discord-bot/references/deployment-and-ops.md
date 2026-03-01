# Deployment and Operations

Sources: production bot deployment patterns (2026), Docker best practices, systemd docs, tracing crate docs

Covers: Docker multi-stage builds, systemd services, structured logging with
tracing, error handling strategies, CI/CD, graceful shutdown, monitoring.

## Docker Deployment

### Multi-Stage Build (Recommended)

```dockerfile
# Stage 1: Build
FROM rust:1.84-slim AS builder
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Cache dependencies
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm -rf src

# Build application
COPY . .
RUN cargo build --release

# Stage 2: Runtime
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y \
    ca-certificates libssl3 yt-dlp \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/my-bot /usr/local/bin/

# Non-root user
RUN useradd -m -u 1000 botuser
USER botuser

ENV RUST_LOG=my_bot=info,serenity=warn
CMD ["my-bot"]
```

### Minimal Alpine Build (Smaller Image)

```dockerfile
FROM rust:1.84-alpine AS builder
RUN apk add --no-cache musl-dev openssl-dev pkgconfig
WORKDIR /app
COPY . .
RUN cargo build --release --target x86_64-unknown-linux-musl

FROM alpine:3.21
RUN apk add --no-cache ca-certificates
COPY --from=builder /app/target/x86_64-unknown-linux-musl/release/my-bot /usr/local/bin/
RUN adduser -D -u 1000 botuser
USER botuser
CMD ["my-bot"]
```

### Docker Compose

```yaml
version: "3.8"
services:
  bot:
    build: .
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - DATABASE_URL=postgresql://bot:password@db:5432/botdb
      - RUST_LOG=my_bot=info,serenity=warn
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: bot
      POSTGRES_PASSWORD: password
      POSTGRES_DB: botdb
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bot"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

## systemd Service

### Service File

```ini
# /etc/systemd/system/discord-bot.service
[Unit]
Description=Discord Bot
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=simple
User=botuser
Group=botuser
WorkingDirectory=/opt/discord-bot
EnvironmentFile=/opt/discord-bot/.env
ExecStart=/opt/discord-bot/my-bot
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=discord-bot

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/discord-bot/data

[Install]
WantedBy=multi-user.target
```

### Management Commands

```bash
sudo systemctl enable discord-bot    # Enable on boot
sudo systemctl start discord-bot     # Start
sudo systemctl stop discord-bot      # Stop
sudo systemctl restart discord-bot   # Restart
sudo systemctl status discord-bot    # Status
journalctl -u discord-bot -f         # Live logs
journalctl -u discord-bot --since "1 hour ago"  # Recent logs
```

## Structured Logging with tracing

### Basic Setup

```rust
use tracing_subscriber::{fmt, EnvFilter};

fn init_tracing() {
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::from_default_env()
                .add_directive("my_bot=debug".parse().unwrap())
                .add_directive("serenity=info".parse().unwrap())
                .add_directive("sqlx=warn".parse().unwrap())
                .add_directive("h2=warn".parse().unwrap())
        )
        .with_target(true)
        .with_thread_ids(false)
        .init();
}
```

### JSON Logging (Production)

```rust
fn init_json_logging() {
    tracing_subscriber::fmt()
        .json()
        .with_current_span(true)
        .with_target(true)
        .with_env_filter(EnvFilter::from_default_env())
        .init();
}
```

### Structured Fields in Commands

```rust
use tracing::{info, warn, error, instrument};

#[instrument(skip(ctx), fields(
    user_id = %ctx.author().id,
    guild_id = ?ctx.guild_id(),
    command = "ban"
))]
async fn ban_command(ctx: Context<'_>, user: serenity::User, reason: String) -> Result<(), Error> {
    info!(target_user = %user.id, %reason, "Executing ban");

    match execute_ban(ctx, &user, &reason).await {
        Ok(_) => {
            info!("Ban successful");
            ctx.say(format!("Banned {} for: {}", user.name, reason)).await?;
        }
        Err(e) => {
            error!(error = %e, "Ban failed");
            ctx.say("Failed to ban user.").await?;
        }
    }

    Ok(())
}
```

### Log Level Guidelines

| Level | Use For | Example |
|-------|---------|---------|
| `error!` | Failures that need attention | Database down, API errors |
| `warn!` | Recoverable issues | Rate limited, missing permissions |
| `info!` | Normal operations | Command executed, bot started |
| `debug!` | Development details | Cache hit/miss, query params |
| `trace!` | Verbose internals | Event payload, raw data |

## Error Handling Strategies

### Poise Error Handler

```rust
async fn on_error(error: poise::FrameworkError<'_, Data, Error>) -> Result<(), Error> {
    match error {
        poise::FrameworkError::Command { error, ctx, .. } => {
            tracing::error!("Command error: {:?}", error);
            let _ = ctx.say("An error occurred. Please try again.").await;
        }
        poise::FrameworkError::ArgumentParse { error, ctx, .. } => {
            let _ = ctx.say(format!("Invalid argument: {error}")).await;
        }
        poise::FrameworkError::CommandCheckFailed { error, ctx, .. } => {
            if let Some(error) = error {
                let _ = ctx.say(format!("Check failed: {error}")).await;
            }
        }
        poise::FrameworkError::CooldownHit { remaining_cooldown, ctx, .. } => {
            let _ = ctx.say(format!(
                "Please wait {:.1} seconds before using this command again.",
                remaining_cooldown.as_secs_f32()
            )).await;
        }
        poise::FrameworkError::MissingBotPermissions { missing_permissions, ctx, .. } => {
            let _ = ctx.say(format!(
                "I need these permissions: {}",
                missing_permissions
            )).await;
        }
        poise::FrameworkError::MissingUserPermissions { missing_permissions, ctx, .. } => {
            if let Some(perms) = missing_permissions {
                let _ = ctx.say(format!("You need: {perms}")).await;
            }
        }
        other => {
            if let Err(e) = poise::builtins::on_error(other).await {
                tracing::error!("Fallback error handler failed: {:?}", e);
            }
        }
    }
    Ok(())
}
```

### Custom Error Types

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum BotError {
    #[error("Discord API error: {0}")]
    Serenity(#[from] serenity::Error),

    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("HTTP request failed: {0}")]
    Http(#[from] reqwest::Error),

    #[error("User {0} not found")]
    UserNotFound(String),

    #[error("Insufficient permissions")]
    InsufficientPermissions,

    #[error("Rate limited, retry after {0} seconds")]
    RateLimited(u64),
}
```

## Graceful Shutdown

```rust
// In main, after client is built:
let shard_manager = client.shard_manager.clone();
let pool = data.pool.clone();

tokio::spawn(async move {
    tokio::signal::ctrl_c().await.unwrap();
    tracing::info!("Received shutdown signal");

    // Stop accepting new gateway events
    shard_manager.shutdown_all().await;

    // Close database connections
    pool.close().await;

    tracing::info!("Shutdown complete");
});

client.start().await?;
```

## Cross-Compilation

Build for Linux from macOS or Windows:

```bash
# Install target
rustup target add x86_64-unknown-linux-musl

# Build static binary
cargo build --release --target x86_64-unknown-linux-musl

# Using cross (handles toolchain setup)
cargo install cross
cross build --release --target x86_64-unknown-linux-gnu
```

## CI/CD (GitHub Actions)

```yaml
name: Build and Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: dtolnay/rust-toolchain@stable

      - uses: Swatinem/rust-cache@v2

      - name: Build
        run: cargo build --release

      - name: Test
        run: cargo test

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: discord-bot
          path: target/release/my-bot
```

## Health Monitoring

### Uptime Tracking

```rust
pub struct Data {
    pub start_time: std::time::Instant,
    pub commands_executed: std::sync::atomic::AtomicU64,
    pub errors_count: std::sync::atomic::AtomicU64,
}

#[poise::command(slash_command)]
async fn status(ctx: Context<'_>) -> Result<(), Error> {
    let data = ctx.data();
    let uptime = data.start_time.elapsed();
    let commands = data.commands_executed.load(Ordering::Relaxed);
    let errors = data.errors_count.load(Ordering::Relaxed);

    let embed = serenity::CreateEmbed::new()
        .title("Bot Status")
        .field("Uptime", format_duration(uptime), true)
        .field("Commands", commands.to_string(), true)
        .field("Errors", errors.to_string(), true)
        .field("Guilds", ctx.cache().guilds().len().to_string(), true)
        .color(0x57F287);

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}
```

### Shard Health

```rust
#[poise::command(slash_command, owners_only)]
async fn shards(ctx: Context<'_>) -> Result<(), Error> {
    let manager = ctx.framework().shard_manager();
    let runners = manager.runners.lock().await;

    let mut status = String::new();
    for (id, runner) in runners.iter() {
        status.push_str(&format!(
            "Shard {}: {:?} (latency: {:?})\n",
            id, runner.stage, runner.latency
        ));
    }

    ctx.say(format!("```\n{status}```")).await?;
    Ok(())
}
```

## Environment Variable Checklist

| Variable | Required | Example |
|----------|----------|---------|
| `DISCORD_TOKEN` | Yes | `Bot MTk...` |
| `DATABASE_URL` | If using DB | `postgresql://user:pass@host/db` |
| `RUST_LOG` | Recommended | `my_bot=info,serenity=warn` |
| `GUILD_ID` | Dev only | `123456789` (for guild command registration) |

## Production Checklist

- [ ] Use `non_privileged()` intents, add only what is needed
- [ ] Register commands globally (not per-guild) for production
- [ ] Enable structured logging (JSON for production)
- [ ] Implement graceful shutdown (SIGTERM handling)
- [ ] Set up database migrations
- [ ] Configure rate limiting for custom features
- [ ] Set Cargo release profile optimizations
- [ ] Run as non-root user (Docker/systemd)
- [ ] Monitor shard health
- [ ] Handle all poise error variants
- [ ] Strip debug symbols in release builds
- [ ] Set up CI/CD pipeline
