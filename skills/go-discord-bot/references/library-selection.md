# Library Selection

Sources: discordgo v0.29.0 docs, arikawa v3.6.0 docs, disgo docs, Discord API reference (2026), production bot analysis (YAGPDB, discordo, disgolink)

The Go Discord ecosystem has three actively maintained libraries. Each targets a different point on the simplicity-vs-safety spectrum. Choose once at project start — migration is painful.

## The Three Libraries

### discordgo

The oldest and most popular Go Discord library. Import path: `github.com/bwmarrin/discordgo`.

discordgo wraps the Discord API as a single `Session` struct. All REST calls, gateway management, state caching, and voice connections live on this one type. The design is intentionally flat: no sub-packages, no interfaces to implement, no routing abstractions. You register handlers with `AddHandler`, which uses reflection to match your function signature to an event type.

**Critical gotcha:** discordgo targets Discord API **v9**, not v10. The `APIVersion` constant in `endpoints.go` is `"9"`. You can override it, but the library is not tested against v10 and some v10-only features (forum channels, message polls, updated permission model) may behave incorrectly. If your bot requires v10 features, use disgo instead.

Voice support is mature. `ChannelVoiceJoin` returns a `*VoiceConnection` with `OpusSend` and `OpusRecv` channels. The companion libraries `dgVoice` (ffmpeg pipeline) and `dca` (Opus encoding) are widely used and well-documented.

Rate limiting is fully automatic. Per-endpoint token buckets and a global rate limit are managed transparently. `ShouldRetryOnRateLimit` defaults to `true`.

**Weaknesses:** No `context.Context` support anywhere in the API. Handlers run in separate goroutines by default (`SyncEvents=false`), so shared state requires explicit synchronization. Panics inside handlers are silent unless you wrap them with `recover()`. The lack of typed IDs means passing a `string` where a channel ID is expected compiles without error.

**Best for:** Bots where community examples matter, teams new to Discord bots, projects that need mature voice support, and cases where the large body of existing discordgo tutorials is an asset.

### arikawa

A modular, type-safe library. Import path: `github.com/diamondburned/arikawa/v3`.

arikawa splits functionality across focused packages rather than concentrating everything in one struct. Each package has a narrow responsibility and can be used independently. The library targets Discord API **v9** but is more current on v9 features than discordgo.

The defining feature is typed Snowflakes. Instead of bare `string` or `uint64`, arikawa defines `discord.ChannelID`, `discord.UserID`, `discord.GuildID`, and so on. Passing the wrong ID type is a compile-time error. This eliminates an entire class of runtime bugs common in large bots.

`cmdroute.Router` provides built-in slash command routing with middleware support. Options are unmarshaled into structs via field tags rather than manual `GetByName` calls. `cmdroute.Deferrable` wraps a handler to automatically send a deferred response if the handler takes longer than 2.5 seconds.

`context.Context` is threaded through the entire API. Every REST call accepts a context, enabling proper timeout and cancellation handling.

The state package is pluggable. The default in-memory state can be replaced with a Redis-backed implementation or a custom store, which matters for sharded bots that need shared state across processes.

arikawa can run as a gateway bot or as an HTTP webhook server (for interactions-only bots that do not need a persistent gateway connection).

**Weaknesses:** Smaller community than discordgo. Fewer tutorials and Stack Overflow answers. The modular package structure has a steeper initial learning curve.

**Best for:** Bots where compile-time correctness matters, teams comfortable with Go idioms, projects that need pluggable state for sharding, and bots that may need to switch between gateway and webhook modes.

### disgo

The only Go library targeting Discord API **v10**. Import path: `github.com/disgoorg/disgo`.

disgo is the newest of the three. It was built specifically to support v10 features: forum channels, the updated permission system, message polls, and the revised interaction model. If your bot depends on any v10-only API surface, disgo is the correct choice.

The interaction routing model is inspired by chi. A `handler.Mux` routes slash commands and component interactions by path. Component custom IDs support variable segments (`/ticket/{id}/close`), which eliminates the manual string parsing that discordgo and arikawa bots typically implement. Middleware is composed functionally.

The architecture is modular: REST, gateway, sharding, and voice are separate modules that can be composed as needed. This makes it straightforward to build bots that use only REST (no gateway) or that add sharding later without restructuring.

**Weaknesses:** Smallest community of the three. Fewer production examples. Some APIs are still stabilizing as v10 features are added.

**Best for:** Bots that require Discord API v10 features, projects starting fresh that want the most current API surface, and teams that prefer chi-style routing for interactions.

---

## Decision Matrix

| Factor | discordgo | arikawa | disgo |
|--------|-----------|---------|-------|
| GitHub stars (Mar 2026) | 5,829 | 579 | 516 |
| Discord API version | v9 | v9 | v10 |
| Maintenance status | Active | Active | Active |
| Voice support | v1 (mature) | v4 | v4 |
| Type-safe IDs | No | Yes | Partial |
| context.Context support | No | Yes | Yes |
| Built-in command routing | No | Yes (cmdroute) | Yes (handler.Mux) |
| Middleware support | No (use ken) | Yes | Yes |
| Pluggable state | No | Yes | No |
| HTTP webhook mode | No | Yes | Yes |
| Community examples | Extensive | Moderate | Limited |
| Forum channels (v10) | Partial | Partial | Full |
| Variable component IDs | Manual | Manual | Yes (/path/{var}) |
| Production bots using it | YAGPDB, many | discordo | disgolink |

---

## Quick Decision

Start here and follow the branches:

```
Does your bot require Discord API v10 features?
  (forum channels, updated permissions, message polls)
  YES → disgo
  NO  → continue

Do you need pluggable state for multi-process sharding?
  YES → arikawa
  NO  → continue

Do you need context.Context for timeout/cancellation?
  YES → arikawa
  NO  → continue

Is compile-time ID type safety important to your team?
  YES → arikawa
  NO  → continue

Do you want the largest community and most tutorials?
  YES → discordgo
  NO  → arikawa (better defaults, worth the smaller community)
```

Default recommendation for new projects with no special requirements: **discordgo** if the team is new to Discord bots (community support matters), **arikawa** if the team is experienced with Go (better idioms, safer defaults).

---

## go.mod Configuration

### discordgo

```go
module github.com/yourorg/yourbot

go 1.22

require (
    github.com/bwmarrin/discordgo v0.29.0
)
```

For voice with ffmpeg pipeline:

```go
require (
    github.com/bwmarrin/discordgo v0.29.0
    github.com/bwmarrin/dgvoice v0.0.0-20210225172318-caaac756e02e
    github.com/jonas747/dca v0.0.0-20210930103944-155f5e5f0cc7
)
```

### arikawa

```go
module github.com/yourorg/yourbot

go 1.22

require (
    github.com/diamondburned/arikawa/v3 v3.6.0
)
```

arikawa bundles all sub-packages in a single module. You do not need separate imports for `api`, `gateway`, or `state` — they are all under `v3`.

### disgo

```go
module github.com/yourorg/yourbot

go 1.22

require (
    github.com/disgoorg/disgo v0.18.14
    github.com/disgoorg/snowflake/v2 v2.0.3
)
```

disgo uses `github.com/disgoorg/snowflake/v2` for its ID types. This is a separate module and must be listed explicitly.

---

## discordgo Feature Flags and Configuration

Set these on the `Session` before calling `Open()`. Changing them after the gateway connects has no effect.

```go
s, err := discordgo.New("Bot " + token)

// Gateway intents — required for most events
// IntentsAllWithoutPrivileged is the default
s.Identify.Intents = discordgo.IntentsGuilds |
    discordgo.IntentsGuildMessages |
    discordgo.IntentsGuildVoiceStates

// Privileged intents — must be enabled in Developer Portal
s.Identify.Intents |= discordgo.IntentsGuildMembers    // member join/leave
s.Identify.Intents |= discordgo.IntentsMessageContent  // message body text

// Sharding
s.ShardID = 0
s.ShardCount = 4

// State cache — enabled by default
s.StateEnabled = true

// Sync event handlers (run sequentially, not in goroutines)
// Use only for debugging — hurts throughput
s.SyncEvents = false

// Compression for gateway payloads
s.Compress = true

// Retry behavior
s.ShouldReconnectOnError = true
s.ShouldRetryOnRateLimit = true
s.MaxRestRetries = 3
```

**Intent reference:**

| Intent constant | Bit | Privileged |
|----------------|-----|-----------|
| `IntentsGuilds` | 1<<0 | No |
| `IntentsGuildMembers` | 1<<1 | Yes |
| `IntentsGuildPresences` | 1<<8 | Yes |
| `IntentsGuildMessages` | 1<<9 | No |
| `IntentsMessageContent` | 1<<15 | Yes |
| `IntentsGuildVoiceStates` | 1<<7 | No |
| `IntentsDirectMessages` | 1<<12 | No |

Privileged intents require explicit enablement in the Discord Developer Portal under your application's Bot settings. Requesting them without portal approval causes the gateway connection to fail.

---

## arikawa Package Architecture

arikawa is organized into focused packages. Understanding the boundaries helps you import only what you need.

```
github.com/diamondburned/arikawa/v3/
├── api/          REST API client — all HTTP calls to Discord
├── gateway/      Gateway client — WebSocket connection and event dispatch
├── session/      Combines api + gateway into a usable bot session
├── state/        In-memory cache built on top of session
├── voice/        Voice gateway and UDP audio transport
├── discord/      Types — all Discord objects, typed Snowflakes
├── utils/
│   ├── json/     JSON helpers
│   ├── ws/       WebSocket abstraction
│   └── httputil/ HTTP client utilities
└── app/
    └── cmdroute/ Slash command router with middleware
```

**Typical import pattern for a full bot:**

```go
import (
    "github.com/diamondburned/arikawa/v3/state"
    "github.com/diamondburned/arikawa/v3/discord"
    "github.com/diamondburned/arikawa/v3/app/cmdroute"
    "github.com/diamondburned/arikawa/v3/api"
)
```

Use `state.New` rather than `session.New` for most bots — the state package wraps session and adds the in-memory cache. Use `session.New` only when you are providing your own state backend.

The `discord` package is the type layer. `discord.ChannelID`, `discord.UserID`, `discord.GuildID`, `discord.RoleID`, and `discord.MessageID` are distinct types backed by `uint64`. They do not convert implicitly, which is the point.

`cmdroute.Router` handles slash command dispatch:

```go
r := cmdroute.NewRouter()
r.Use(cmdroute.Deferrable(state, cmdroute.DeferOpts{}))
r.AddFunc("ping", handlePing)
r.Sub("admin", func(r *cmdroute.Router) {
    r.AddFunc("ban", handleBan)
})
state.AddInteractionHandler(r)
```

---

## disgo Module Architecture

disgo separates concerns into distinct top-level packages within the module:

```
github.com/disgoorg/disgo/
├── bot/          Bot client — entry point, combines all modules
├── discord/      Types — all Discord v10 objects
├── rest/         REST API client
├── gateway/      Gateway client and shard manager
├── sharding/     Multi-shard manager
├── voice/        Voice gateway and UDP transport
├── handler/      Interaction routing (Mux, middleware)
└── cache/        In-memory cache with configurable policies
```

**Entry point:**

```go
import "github.com/disgoorg/disgo/bot"

client, err := disgo.New(token,
    bot.WithGatewayConfigOpts(
        gateway.WithIntents(gateway.IntentGuilds, gateway.IntentGuildMessages),
    ),
    bot.WithCacheConfigOpts(
        cache.WithCaches(cache.FlagGuilds, cache.FlagChannels),
    ),
)
```

The `handler.Mux` routes interactions by command name or component custom ID:

```go
mux := handler.New()
mux.Command("/ping", handlePing)
mux.Component("/ticket/{id}/close", handleTicketClose)
mux.Autocomplete("/search", handleSearchAutocomplete)
client.AddEventListeners(mux)
```

Variable segments in component custom IDs (`{id}`) are extracted and available in the handler context, eliminating the manual `strings.Split` parsing that other libraries require.

---

## Common Companion Packages

These packages appear consistently across production Go Discord bots regardless of which Discord library is used.

| Category | Package | Notes |
|----------|---------|-------|
| Structured logging | `go.uber.org/zap` | Used by YAGPDB, ops-bot-iii; fast, structured |
| Structured logging | `github.com/rs/zerolog` | Zero-allocation; common in smaller bots |
| Configuration | `github.com/spf13/viper` | YAML/env/flags; hot-reload via fsnotify |
| Configuration | `github.com/joho/godotenv` | `.env` file loading for local dev |
| PostgreSQL | `github.com/jackc/pgx/v5` | Preferred over `database/sql` for Postgres |
| PostgreSQL ORM | `github.com/volatiletech/sqlboiler` | Code-generated from schema; used by YAGPDB |
| Type-safe ORM | `entgo.io/ent` | Code-generated graph ORM; used by ops-bot-iii |
| Redis | `github.com/mediocregopher/radix/v4` | Used by YAGPDB for caching and pub/sub |
| SQLite | `github.com/mattn/go-sqlite3` | CGo; or `modernc.org/sqlite` for pure Go |
| Testing | `github.com/stretchr/testify` | Assert/require; standard across all bots |
| Metrics | `github.com/prometheus/client_golang` | Prometheus metrics; used by YAGPDB |
| APM | `gopkg.in/DataDog/dd-trace-go.v1` | DataDog tracing; used by ops-bot-iii |
| Opus encoding | `github.com/jonas747/dca` | Opus encoding for discordgo voice |
| Voice pipeline | `github.com/bwmarrin/dgvoice` | ffmpeg pipeline for discordgo |

---

## Migration Notes

### discordgo → arikawa

The conceptual shift is from a single `*Session` to composed packages. The `state.State` type is the closest equivalent to `discordgo.Session`.

| discordgo | arikawa equivalent |
|-----------|-------------------|
| `discordgo.New(token)` | `state.New("Bot " + token)` |
| `s.AddHandler(fn)` | `s.AddHandler(fn)` (same pattern) |
| `s.Open()` | `s.Connect(ctx)` |
| `s.Close()` | `s.Close()` |
| `s.ChannelMessage(cID, mID)` | `s.Message(channelID, messageID)` |
| `s.GuildRoles(gID)` | `s.Roles(guildID)` |
| `i.ApplicationCommandData().Name` | `e.Data.Name` (typed) |
| `i.ApplicationCommandData().Options` | `e.Data.Options` (unmarshal to struct) |
| `string` channel/user IDs | `discord.ChannelID`, `discord.UserID` |

The largest migration effort is converting bare string IDs to typed Snowflakes. This is mechanical but touches every database query, every REST call, and every event handler that reads IDs.

Event handler signatures change. discordgo uses `func(s *discordgo.Session, e *discordgo.MessageCreate)`. arikawa uses `func(*gateway.MessageCreateEvent)` — the session is not passed; use a closure to capture it.

### discordgo → disgo

disgo's `bot.Client` replaces `discordgo.Session`. The gateway intent system uses the same bit values but different constant names.

| discordgo | disgo equivalent |
|-----------|-----------------|
| `discordgo.New(token)` | `disgo.New(token, ...)` |
| `s.Identify.Intents = ...` | `gateway.WithIntents(...)` option |
| `s.AddHandler(fn)` | `client.AddEventListeners(fn)` |
| `s.Open()` | `client.OpenGateway(ctx)` |
| `s.Close()` | `client.Close(ctx)` |
| Manual custom ID parsing | `mux.Component("/path/{var}", fn)` |
| `s.ApplicationCommandCreate(...)` | `client.Rest().CreateApplicationCommand(...)` |

The interaction routing model changes substantially. discordgo bots typically use a map dispatch pattern (`commandHandlers[name](s, i)`). disgo bots use the `handler.Mux` with path-based routing. Rewriting the interaction layer is the bulk of the migration work.

---

## disgord Is Archived

`github.com/andersfylling/disgord` has not received meaningful updates in over a year and is effectively unmaintained. The repository is archived. Do not start new projects with disgord. If you are maintaining an existing disgord bot, plan a migration to discordgo, arikawa, or disgo. The API surface is different enough from all three that migration requires a rewrite of the bot layer, not a find-and-replace.
