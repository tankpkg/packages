---
name: "@tank/rust-discord-bot"
description: |
  Build high-performance Discord bots in Rust using serenity, poise, and
  twilight. Covers framework selection (serenity vs poise vs twilight),
  project scaffolding (workspace, Cargo.toml, feature flags), slash commands
  and prefix commands (poise macros, parameters, autocomplete, cooldowns,
  subcommands), message components (buttons, select menus, modals), embeds,
  gateway intents and event handling, state management and database
  integration (sqlx, DashMap, moka caching), voice and audio (Songbird),
  performance optimization (tokio tuning, sharding, zero-copy, Cargo release
  profiles), and deployment (Docker, systemd, tracing). Synthesizes
  serenity-rs v0.12.5 docs, poise v0.6.1 docs, twilight-rs v0.17.1 docs,
  Discord API reference (2026), and production patterns from Discord-TTS,
  robbb, Bathbot, and rustbot.

  Trigger phrases: "discord bot rust", "rust discord", "serenity-rs",
  "serenity bot", "poise discord", "poise command", "twilight discord",
  "twilight-rs", "discord bot", "rust bot", "slash command rust",
  "discord gateway", "discord intents", "songbird voice", "discord music bot",
  "discord interaction rust", "discord embed rust", "discord button rust",
  "discord modal rust", "discord select menu", "poise framework",
  "serenity event handler", "discord sharding rust", "discord sqlx",
  "discord deployment rust", "discord bot docker", "discord bot systemd"
---

# Rust Discord Bot Development

Build Discord bots in Rust for maximum performance and reliability. The
ecosystem centers on three libraries: **serenity** (API wrapper), **poise**
(command framework), and **twilight** (modular low-level). Most bots use
poise + serenity.

## Core Philosophy

1. **Poise is the default** — Use poise + serenity for all new bots. Only
   drop to raw serenity for custom interaction flows. Only use twilight for
   large-scale multi-service architectures.
2. **Slash commands first** — Prefer slash commands over prefix commands.
   Prefix commands require the privileged MESSAGE_CONTENT intent.
3. **Server owns state** — Shared state lives in the `Data` struct, accessed
   via `ctx.data()`. Use `DashMap` for concurrent collections, `sqlx` for
   persistence, `moka` for TTL caching.
4. **Async everything** — Never block the tokio runtime. Use `spawn_blocking`
   for CPU-heavy work. Use `Semaphore` to bound concurrent tasks.
5. **Intents are permissions** — Only request gateway intents the bot needs.
   Privileged intents (GUILD_MEMBERS, MESSAGE_CONTENT, PRESENCES) require
   Discord verification at 100+ guilds.

## Quick-Start

### "I want to build a Discord bot from scratch"

| Step | Action | Reference |
|------|--------|-----------|
| 1 | Choose framework (poise recommended) | `references/framework-selection.md` |
| 2 | Scaffold project (Cargo.toml, main.rs, .env) | `references/project-setup.md` |
| 3 | Define commands with `#[poise::command]` | `references/commands-and-interactions.md` |
| 4 | Configure gateway intents | `references/event-handling.md` |
| 5 | Add database and shared state | `references/state-and-data.md` |
| 6 | Optimize for production | `references/performance-and-concurrency.md` |
| 7 | Deploy with Docker or systemd | `references/deployment-and-ops.md` |

### "I need to add a slash command"

| Step | Action |
|------|--------|
| 1 | Write `async fn` with `#[poise::command(slash_command)]` |
| 2 | Add parameters as typed function arguments |
| 3 | Register in `commands: vec![my_command()]` |
| 4 | Commands auto-register on startup via `register_globally` |
-> See `references/commands-and-interactions.md`

### "I want to add voice/music support"

| Step | Action |
|------|--------|
| 1 | Add `songbird` and `symphonia` to Cargo.toml |
| 2 | Enable `GUILD_VOICE_STATES` intent |
| 3 | Register Songbird with `.register_songbird()` |
| 4 | Join channel, play audio with `handler.enqueue_input()` |
-> See `references/voice-and-audio.md`

### "I need buttons, select menus, or modals"

| Step | Action |
|------|--------|
| 1 | Build components with `CreateButton`, `CreateSelectMenu`, or `CreateModal` |
| 2 | Send with `ctx.send()` including `.components()` |
| 3 | Await interaction with `.await_component_interaction()` |
| 4 | Respond within 3 seconds (or defer) |
-> See `references/commands-and-interactions.md`

## Decision Trees

### Framework Selection

| Signal | Use |
|--------|-----|
| New bot, want to ship fast | Poise + Serenity |
| Custom interaction flows, webhook-only | Raw Serenity |
| 10,000+ guilds, microservice architecture | Twilight |
| Voice/music bot | Poise + Serenity + Songbird |

### Database Selection

| Scale | Use |
|-------|-----|
| Prototype / small bot (<100 guilds) | SQLite via sqlx |
| Production / growing bot | PostgreSQL via sqlx |
| No persistence needed | In-memory only (DashMap) |

### Intent Selection

| Feature | Required Intents |
|---------|-----------------|
| Slash commands only | `GatewayIntents::empty()` |
| Basic guild events | `GatewayIntents::non_privileged()` |
| Prefix commands | + `MESSAGE_CONTENT` (privileged) |
| Welcome messages | + `GUILD_MEMBERS` (privileged) |
| Voice bot | + `GUILD_VOICE_STATES` |
| Status tracking | + `GUILD_PRESENCES` (privileged) |

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Use standard framework | Use poise | Standard framework deprecated in v0.12.1 |
| Request `GatewayIntents::all()` | Request only needed intents | Fails verification at 100+ guilds |
| Block the tokio runtime | Use `spawn_blocking` | Freezes all event processing |
| Clone strings unnecessarily | Borrow `&str` | Allocations hurt throughput |
| Use `Arc<RwLock<HashMap>>` | Use `DashMap` | 3-5x faster for concurrent access |
| Skip error handling in on_error | Handle all FrameworkError variants | Silent failures in production |
| Register guild commands in prod | Use `register_globally` | Guild commands are for development |
| Ignore rate limits | Let serenity handle them | Bot gets banned by Discord |

## Reference Files

| File | Contents |
|------|----------|
| `references/framework-selection.md` | Serenity vs Poise vs Twilight decision matrix, Cargo.toml configs, feature flags, crate ecosystem, companion crates |
| `references/project-setup.md` | Directory structure (simple and workspace), main.rs bootstrapping, command registration, configuration, .env handling |
| `references/commands-and-interactions.md` | Poise command macros, slash/prefix/context menu commands, parameter types, autocomplete, subcommands, permission checks, embeds, buttons, select menus, modals |
| `references/event-handling.md` | Gateway intents (standard and privileged), poise event handler, FullEvent variants, raw serenity EventHandler, presence/activity, component interaction handling |
| `references/state-and-data.md` | Data struct pattern, database integration (sqlx, PostgreSQL, SQLite), migrations, DashMap, moka caching, serenity cache, TypeMap, background tasks |
| `references/performance-and-concurrency.md` | Tokio runtime tuning, memory optimization, sharding, concurrency patterns (Semaphore, channels, select), Cargo release profiles, SIMD JSON, gateway compression |
| `references/voice-and-audio.md` | Songbird setup, join/leave voice, audio playback (files, URLs, yt-dlp), queue management, voice events, volume control, voice receive |
| `references/deployment-and-ops.md` | Docker multi-stage builds, systemd services, structured logging (tracing), error handling strategies, graceful shutdown, cross-compilation, CI/CD, monitoring |
