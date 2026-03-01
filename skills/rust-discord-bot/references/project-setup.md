# Project Setup and Structure

Sources: serenity-rs examples, poise quickstart, Discord-TTS Bot, robbb, Bathbot architecture analysis

Covers: directory layout, workspace configuration, main.rs bootstrapping, configuration
management, environment variables, .env handling.

## Project Structure Patterns

### Simple Bot (Single Crate)

For bots with fewer than 20 commands and no complex state:

```
my-bot/
├── Cargo.toml
├── .env                    # Secrets (DISCORD_TOKEN, DATABASE_URL)
├── .gitignore
├── src/
│   ├── main.rs             # Entry point, framework setup
│   ├── commands/
│   │   ├── mod.rs           # Re-exports all commands
│   │   ├── general.rs       # ping, help, about
│   │   ├── moderation.rs    # ban, kick, mute
│   │   └── fun.rs           # Custom commands
│   └── events.rs            # Non-command event handling
└── migrations/              # SQL migrations (if using database)
    └── 001_initial.sql
```

### Production Bot (Workspace)

For bots with 20+ commands, database, voice, or background tasks. Split into
crates for faster incremental compilation and cleaner architecture:

```
my-bot/
├── Cargo.toml               # Workspace root
├── .env
├── config.toml              # Non-secret configuration
├── bot/                     # Main binary
│   ├── Cargo.toml
│   └── src/
│       └── main.rs
├── bot_core/                # Shared types, database, errors
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── data.rs           # Data struct (shared state)
│       ├── database.rs       # Database layer
│       ├── errors.rs         # Error types
│       └── config.rs         # Configuration loading
├── bot_commands/             # Command definitions
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs            # pub fn commands() -> Vec<Command>
│       ├── general.rs
│       ├── moderation.rs
│       └── settings/
│           ├── mod.rs
│           └── prefix.rs
├── bot_events/               # Event handlers
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       └── handlers.rs
└── migrations/
    ├── 001_initial.sql
    └── 002_add_settings.sql
```

### Workspace Cargo.toml

```toml
[workspace]
members = ["bot", "bot_core", "bot_commands", "bot_events"]
resolver = "2"

[workspace.dependencies]
serenity = { version = "0.12", features = [
    "builder", "cache", "client", "collector", "framework",
    "gateway", "http", "model", "utils", "rustls_backend",
] }
poise = "0.6"
tokio = { version = "1", features = ["rt-multi-thread", "macros", "signal"] }
sqlx = { version = "0.8", features = ["postgres", "runtime-tokio-rustls", "macros"] }
serde = { version = "1", features = ["derive"] }
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
anyhow = "1"
```

Each member crate references workspace dependencies:

```toml
# bot_commands/Cargo.toml
[package]
name = "bot_commands"
version = "0.1.0"
edition = "2024"

[dependencies]
serenity = { workspace = true }
poise = { workspace = true }
bot_core = { path = "../bot_core" }
```

## Main.rs Bootstrapping

### Poise Quickstart (Minimal)

```rust
use poise::serenity_prelude as serenity;

struct Data {}
type Error = Box<dyn std::error::Error + Send + Sync>;
type Context<'a> = poise::Context<'a, Data, Error>;

/// Responds with "Pong!"
#[poise::command(slash_command, prefix_command)]
async fn ping(ctx: Context<'_>) -> Result<(), Error> {
    ctx.say("Pong!").await?;
    Ok(())
}

#[tokio::main]
async fn main() {
    let token = std::env::var("DISCORD_TOKEN").expect("missing DISCORD_TOKEN");
    let intents = serenity::GatewayIntents::non_privileged();

    let framework = poise::Framework::builder()
        .options(poise::FrameworkOptions {
            commands: vec![ping()],
            ..Default::default()
        })
        .setup(|ctx, _ready, framework| {
            Box::pin(async move {
                poise::builtins::register_globally(ctx, &framework.options().commands).await?;
                Ok(Data {})
            })
        })
        .build();

    let client = serenity::ClientBuilder::new(token, intents)
        .framework(framework)
        .await;

    client.unwrap().start().await.unwrap();
}
```

### Production Main.rs

```rust
use std::sync::Arc;
use poise::serenity_prelude as serenity;
use tracing_subscriber::{fmt, EnvFilter};

mod commands;
mod events;

pub struct Data {
    pub pool: sqlx::PgPool,
    pub reqwest: reqwest::Client,
    pub start_time: std::time::Instant,
}

pub type Error = Box<dyn std::error::Error + Send + Sync>;
pub type Context<'a> = poise::Context<'a, Data, Error>;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Load .env
    dotenvy::dotenv().ok();

    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::from_default_env()
                .add_directive("my_bot=debug".parse()?)
                .add_directive("serenity=info".parse()?)
        )
        .init();

    // Database
    let database_url = std::env::var("DATABASE_URL")?;
    let pool = sqlx::PgPool::connect(&database_url).await?;
    sqlx::migrate!("./migrations").run(&pool).await?;

    // Discord token and intents
    let token = std::env::var("DISCORD_TOKEN")?;
    let intents = serenity::GatewayIntents::non_privileged()
        | serenity::GatewayIntents::MESSAGE_CONTENT;

    // Framework
    let framework = poise::Framework::builder()
        .options(poise::FrameworkOptions {
            commands: commands::all(),
            event_handler: |ctx, event, framework, data| {
                Box::pin(events::handler(ctx, event, framework, data))
            },
            on_error: |error| {
                Box::pin(async move {
                    if let Err(e) = on_error(error).await {
                        tracing::error!("Error handler failed: {:?}", e);
                    }
                })
            },
            prefix_options: poise::PrefixFrameworkOptions {
                prefix: Some("!".into()),
                ..Default::default()
            },
            ..Default::default()
        })
        .setup(|ctx, _ready, framework| {
            Box::pin(async move {
                poise::builtins::register_globally(
                    ctx,
                    &framework.options().commands,
                ).await?;
                tracing::info!("Bot is ready!");
                Ok(Data {
                    pool,
                    reqwest: reqwest::Client::new(),
                    start_time: std::time::Instant::now(),
                })
            })
        })
        .build();

    let mut client = serenity::ClientBuilder::new(token, intents)
        .framework(framework)
        .await?;

    // Graceful shutdown on Ctrl+C
    let shard_manager = client.shard_manager.clone();
    tokio::spawn(async move {
        tokio::signal::ctrl_c().await.unwrap();
        tracing::info!("Shutting down...");
        shard_manager.shutdown_all().await;
    });

    client.start().await?;
    Ok(())
}

async fn on_error(error: poise::FrameworkError<'_, Data, Error>) -> Result<(), Error> {
    match error {
        poise::FrameworkError::Command { error, ctx, .. } => {
            tracing::error!("Command error: {:?}", error);
            ctx.say("An error occurred while executing this command.").await?;
        }
        poise::FrameworkError::ArgumentParse { error, ctx, .. } => {
            ctx.say(format!("Invalid argument: {}", error)).await?;
        }
        other => poise::builtins::on_error(other).await?,
    }
    Ok(())
}
```

## Command Registration

### Guild Commands (Instant, for Development)

```rust
.setup(|ctx, _ready, framework| {
    Box::pin(async move {
        let guild_id = serenity::GuildId::new(123456789); // Your test server
        poise::builtins::register_in_guild(
            ctx,
            &framework.options().commands,
            guild_id,
        ).await?;
        Ok(Data {})
    })
})
```

### Global Commands (Up to 1 Hour Propagation, for Production)

```rust
poise::builtins::register_globally(ctx, &framework.options().commands).await?;
```

### Command Collection Pattern

```rust
// commands/mod.rs
mod general;
mod moderation;
mod fun;

pub fn all() -> Vec<poise::Command<crate::Data, crate::Error>> {
    vec![
        general::ping(),
        general::about(),
        general::help(),
        moderation::ban(),
        moderation::kick(),
        moderation::mute(),
        fun::roll(),
        fun::quote(),
    ]
}
```

## Configuration Management

### Environment Variables (.env)

```bash
# .env (never commit this file)
DISCORD_TOKEN=Bot MTk...
DATABASE_URL=postgresql://user:pass@localhost/botdb
RUST_LOG=my_bot=debug,serenity=info
```

### TOML Configuration File

```toml
# config.toml (safe to commit, no secrets)
[bot]
prefix = "!"
default_color = 0x5865F2  # Discord blurple

[features]
voice_enabled = true
max_queue_size = 50

[limits]
max_embed_fields = 25
cooldown_seconds = 5
```

```rust
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Config {
    pub bot: BotConfig,
    pub features: FeaturesConfig,
    pub limits: LimitsConfig,
}

#[derive(Debug, Deserialize)]
pub struct BotConfig {
    pub prefix: String,
    pub default_color: u32,
}

pub fn load_config() -> anyhow::Result<Config> {
    let content = std::fs::read_to_string("config.toml")?;
    Ok(toml::from_str(&content)?)
}
```

### Docker vs Self-Host Configuration

Production bots often use separate config files per environment:

```
config/
├── config.docker.toml
├── config.selfhost.toml
└── config.dev.toml
```

Select at runtime:

```rust
let config_path = std::env::var("CONFIG_PATH")
    .unwrap_or_else(|_| "config/config.dev.toml".to_string());
let config = load_config(&config_path)?;
```

## .gitignore

```gitignore
/target
.env
*.db
*.sqlite
config/config.dev.toml
```

## Type Aliases Convention

Every poise bot defines these three types at the crate root:

```rust
pub struct Data { /* shared state */ }
pub type Error = Box<dyn std::error::Error + Send + Sync>;
pub type Context<'a> = poise::Context<'a, Data, Error>;
```

All commands use `Context<'_>` and return `Result<(), Error>`. This convention
is universal across the poise ecosystem — follow it exactly.
