# Framework Selection

Sources: serenity-rs v0.12.5 docs, poise v0.6.1 docs, twilight-rs v0.17.1 docs, production bot analysis (2026)

Covers: choosing between serenity, poise, and twilight; Cargo.toml configuration;
feature flags; crate ecosystem; migration paths.

## The Three Frameworks

Rust has three major Discord library ecosystems. They are not interchangeable —
each serves a different audience and architecture style.

### Serenity (Low-Level Foundation)

Full-featured Discord API wrapper. Provides event handlers, caching, HTTP
client, and gateway management. Most bots build on serenity indirectly
through poise.

- **Version**: v0.12.5 (December 2025, last planned 0.12.x release)
- **GitHub**: serenity-rs/serenity (5.4k stars)
- **Runtime**: tokio multi-thread
- **TLS**: rustls (default) or native-tls

Use raw serenity only when poise's abstractions get in the way — custom
interaction flows, webhook-only bots, or non-command-driven architectures.

### Poise (Command Framework on Serenity)

Opinionated command framework built on serenity. Recommended for all new bots.

- **Version**: v0.6.1 (January 2024)
- **Requires**: serenity 0.12.5
- **MSRV**: Rust 1.74.0

Key features over raw serenity:
- Single function defines both slash and prefix commands
- Automatic argument parsing from Rust types
- Edit tracking (bot response updates when user edits message)
- Built-in help generation, cooldowns, permission checks
- Centralized error handling

### Twilight (Modular Low-Level)

Modular crate ecosystem for experienced Rust developers who need fine-grained
control. Each component (gateway, HTTP, cache, models) is a separate crate.

- **Version**: v0.17.1 (December 2025)
- **GitHub**: twilight-rs/twilight (813 stars)
- **MSRV**: Rust 1.89

Use twilight for:
- Multi-service architectures (gateway clusters, HTTP proxies)
- Bots serving thousands of guilds with custom infrastructure
- Interaction-only bots (no gateway needed via webhook mode)
- When you need to cache only specific resource types

## Decision Matrix

| Factor | Poise + Serenity | Raw Serenity | Twilight |
|--------|------------------|--------------|----------|
| Learning curve | Low | Medium | High |
| Time to first bot | Minutes | Hours | Days |
| Command framework | Built-in | Manual dispatch | Build your own |
| Architectural freedom | Medium | High | Maximum |
| Memory footprint | Medium | Medium | Low (configurable) |
| Bundle size | ~15-25 MB | ~15-25 MB | ~10-20 MB |
| Sharding complexity | Handled | Handled | Manual (flexible) |
| Multi-process deploy | Possible | Possible | Designed for it |
| Community/examples | Large | Large | Small |
| Production bots | ~80% of Rust bots | ~5% | ~15% |
| Best for | Most bots | Custom interaction flows | Large-scale infra |

### Quick Decision

```
Do you need custom gateway/HTTP infrastructure?
  YES → Twilight
  NO →
    Do you want command framework with slash + prefix support?
      YES → Poise + Serenity (recommended default)
      NO → Raw Serenity
```

## Cargo.toml Configuration

### Poise + Serenity (Recommended)

```toml
[dependencies]
poise = "0.6"
serenity = { version = "0.12", features = [
    "builder",
    "cache",
    "client",
    "collector",
    "framework",
    "gateway",
    "http",
    "model",
    "utils",
    "rustls_backend",
] }
tokio = { version = "1", features = ["rt-multi-thread", "macros", "signal"] }
```

### Minimal Serenity (No Poise)

```toml
[dependencies]
serenity = { version = "0.12", default-features = false, features = [
    "client",
    "gateway",
    "model",
    "http",
    "rustls_backend",
] }
tokio = { version = "1", features = ["rt-multi-thread", "macros"] }
```

### Twilight

```toml
[dependencies]
twilight-gateway = { version = "0.16", features = ["rustls-webpki-roots", "zstd"] }
twilight-http = { version = "0.16", features = ["rustls-webpki-roots"] }
twilight-model = "0.16"
twilight-cache-inmemory = "0.16"
twilight-standby = "0.16"
tokio = { version = "1", features = ["rt-multi-thread", "macros", "signal"] }
```

## Serenity Feature Flags

| Feature | Purpose | Default? |
|---------|---------|----------|
| `builder` | Builder structs for HTTP requests | Yes |
| `cache` | In-memory event-driven cache | Yes |
| `client` | High-level client wrapper | Yes |
| `collector` | Await interactions without event handlers | No |
| `framework` | Framework trait (needed for poise) | Yes |
| `gateway` | WebSocket gateway connection | Yes |
| `http` | REST API client | Yes |
| `model` | Discord model types with helper methods | Yes |
| `utils` | Utility functions | Yes |
| `voice` | Voice state tracking (for Songbird) | No |
| `temp_cache` | TTL-based temporary message cache (mini-moka) | No |
| `simd_json` | SIMD-accelerated JSON parsing | No |
| `rustls_backend` | Rustls TLS (default, recommended) | Yes |
| `native_tls_backend` | Native TLS (mutually exclusive with rustls) | No |
| `unstable_discord_api` | Unstable Discord API features | No |

### Recommended Feature Sets

**Standard bot**:
```toml
features = ["builder", "cache", "client", "collector", "framework",
            "gateway", "http", "model", "utils", "rustls_backend"]
```

**Voice bot** (add to standard):
```toml
features = ["voice"]  # Plus songbird dependency
```

**Minimal memory**:
```toml
default-features = false
features = ["client", "gateway", "model", "http", "rustls_backend"]
```

**High throughput**:
```toml
features = ["simd_json", "temp_cache"]  # Add to standard set
```

## Twilight Crate Ecosystem

| Crate | Purpose | When to Include |
|-------|---------|-----------------|
| `twilight-model` | Discord data structures | Always |
| `twilight-gateway` | WebSocket gateway | Event-driven bots |
| `twilight-http` | REST API client | Always |
| `twilight-cache-inmemory` | In-process cache | When caching needed |
| `twilight-standby` | Wait for specific events | Reaction menus, confirmations |
| `twilight-gateway-queue` | Shard identify ratelimiting | Multi-process sharding |
| `twilight-http-ratelimiting` | HTTP ratelimit tracking | API proxies |
| `twilight-validate` | Request validation | Custom request building |
| `twilight-util` | Utilities and builders | Message/embed building |

## Common Companion Crates

These crates appear in 90%+ of production Rust Discord bots regardless of
framework choice:

```toml
# Serialization
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# Error handling (pick one combo)
anyhow = "1"           # Application errors (simple)
thiserror = "2"        # Library error types (typed)

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# HTTP client (external APIs)
reqwest = { version = "0.12", features = ["rustls-tls", "json"] }

# Database (pick one)
sqlx = { version = "0.8", features = ["postgres", "runtime-tokio-rustls", "macros"] }
# OR for SQLite:
sqlx = { version = "0.8", features = ["sqlite", "runtime-tokio-rustls", "macros"] }

# Concurrency
dashmap = "6"          # Lock-free concurrent HashMap
parking_lot = "0.12"   # Faster Mutex/RwLock than std

# Caching
mini-moka = "0.10"     # TTL-based in-memory cache

# Configuration
toml = "0.8"           # Config file parsing
dotenvy = "0.15"       # .env file loading
```

## Migration Notes

### Standard Framework → Poise

Serenity's built-in standard framework was deprecated in v0.12.1. Migrate
prefix commands to poise. Poise commands can serve both slash and prefix
simultaneously with `#[poise::command(slash_command, prefix_command)]`.

### Serenity v0.12 → v0.13

v0.13 is in development on the `next` branch. Expect breaking changes to
builder APIs and interaction handling. Pin to `0.12` for stability.

### Discriminators Removed

Discord removed discriminators (the `#1234` suffix). Use `User::global_name`
or `User::display_name` instead of `User::tag()`. The `Member::distinct`
method is deprecated.

### Gateway Intents Changes

Discord enforces privileged intents for `MESSAGE_CONTENT`, `GUILD_MEMBERS`,
and `GUILD_PRESENCES`. Enable these in the Developer Portal first, then in
code. Without `MESSAGE_CONTENT`, prefix commands cannot read message text —
this is why slash commands are the recommended default.
