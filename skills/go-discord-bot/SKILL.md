---
name: go-discord-bot
description: |
  Build Discord bots in Go using discordgo, arikawa, or disgo. Covers
  library selection, project scaffolding, slash commands and handler
  patterns, message components (buttons, select menus, modals), gateway
  intents, state and database integration (pgx, entgo, Redis), voice
  and audio (dgvoice, dca), goroutine safety, sharding, and deployment.
  Synthesizes discordgo v0.29.0, arikawa v3.6.0, disgo docs, and
  production patterns from YAGPDB, automuteus, CJ, ken, ops-bot-iii.

  Trigger phrases: "discord bot go", "go discord", "discordgo",
  "arikawa", "disgo", "golang discord bot", "slash command go",
  "discord gateway go", "discord intents go", "discord voice go",
  "discord music bot go", "discord embed go", "discord button go",
  "discord modal go", "discord select menu go", "discord bot golang",
  "dgvoice", "discord sharding go", "discord deployment go",
  "discord bot docker go", "discord bot systemd go",
  "go discord slash command", "discordgo handler",
  "discordgo interaction"
---

# Go Discord Bot Development

Build Discord bots in Go for simplicity and concurrency. The ecosystem
centers on three libraries: **discordgo** (low-level, dominant),
**arikawa** (typed, modular), and **disgo** (modern, API v10). Most
bots use discordgo.

## Core Philosophy

1. **discordgo is the default** — Use discordgo for all new bots unless
   you need typed snowflakes (arikawa) or API v10 (disgo). Largest
   community, most examples, most Stack Overflow answers.
2. **Slash commands first** — Prefer slash commands over message-based
   commands. Message content requires the privileged MESSAGE_CONTENT
   intent, which needs Discord verification at 100+ guilds.
3. **Goroutine safety matters** — discordgo fires each handler in its
   own goroutine. Protect shared state with `sync.RWMutex`, wrap handlers
   with `recover()` because panics in goroutines are silent and fatal.
4. **Respect the 3-second deadline** — Discord requires an interaction
   response within 3 seconds. For slow operations, always defer first
   with `InteractionResponseDeferredChannelMessageWithSource`, then edit.
5. **Intents are permissions** — Only request gateway intents the bot
   needs. Privileged intents (GUILD_MEMBERS, MESSAGE_CONTENT, PRESENCES)
   require Discord Developer Portal approval at 100+ guilds.

## Quick-Start

### "I want to build a Discord bot from scratch"

| Step | Action | Reference |
|------|--------|-----------|
| 1 | Choose library (discordgo recommended) | `references/library-selection.md` |
| 2 | Scaffold project (go.mod, main.go, .env) | `references/project-setup.md` |
| 3 | Define slash commands and handlers | `references/commands-and-interactions.md` |
| 4 | Configure gateway intents | `references/event-handling.md` |
| 5 | Add database and shared state | `references/state-and-database.md` |
| 6 | Add voice support (if needed) | `references/voice-and-audio.md` |
| 7 | Deploy with Docker or systemd | `references/deployment-and-ops.md` |

### "I need to add a slash command"

| Step | Action |
|------|--------|
| 1 | Define `*discordgo.ApplicationCommand` with name, description, options |
| 2 | Add handler to `commandHandlers` map |
| 3 | Register via `s.ApplicationCommandCreate` or `ApplicationCommandBulkOverwrite` |
| 4 | Route in `InteractionCreate` handler by `i.ApplicationCommandData().Name` |
-> See `references/commands-and-interactions.md`

### "I need buttons, select menus, or modals"

| Step | Action |
|------|--------|
| 1 | Build components with `discordgo.Button`, `discordgo.SelectMenu`, or `discordgo.TextInput` |
| 2 | Wrap in `discordgo.ActionsRow`, send via `InteractionRespond` |
| 3 | Handle clicks via `InteractionMessageComponent` or `InteractionModalSubmit` |
| 4 | Route by `i.MessageComponentData().CustomID` |
-> See `references/components-and-modals.md`

### "I want to add voice/music support"

| Step | Action |
|------|--------|
| 1 | Set `IntentGuildVoiceStates` intent |
| 2 | Join channel with `s.ChannelVoiceJoin(guildID, channelID, false, true)` |
| 3 | Encode audio to Opus via dgvoice/dca + ffmpeg |
| 4 | Send frames via `vc.OpusSend <- opusFrame` |
-> See `references/voice-and-audio.md`

## Decision Trees

### Library Selection

| Signal | Use |
|--------|-----|
| New bot, want to ship fast | discordgo |
| Need typed snowflakes, context.Context, pluggable state | arikawa |
| Need Discord API v10 features | disgo |
| Need chi-style interaction routing | disgo handler.Mux |
| Need typed command routing with struct tags | arikawa cmdroute |

### Database Selection

| Scale | Use |
|-------|-----|
| Prototype / small bot | SQLite via database/sql |
| Production / growing bot | PostgreSQL via pgxpool |
| Type-safe ORM | entgo (code-generated) |
| Multi-shard shared state | Redis (go-redis) |
| No persistence needed | In-memory (sync.Map) |

### Intent Selection

| Feature | Required Intents |
|---------|-----------------|
| Slash commands only | `IntentsGuilds` (minimal) |
| Basic guild events | `IntentsAllWithoutPrivileged` (default) |
| Read message content | + `IntentMessageContent` (privileged) |
| Welcome messages | + `IntentGuildMembers` (privileged) |
| Voice bot | + `IntentGuildVoiceStates` |
| Status tracking | + `IntentGuildPresences` (privileged) |

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Use disgord | Use discordgo, arikawa, or disgo | disgord is archived, targets API v8 |
| Request `IntentsAll` | Request only needed intents | Fails verification at 100+ guilds |
| Block in event handlers | Use goroutines for slow work | Blocks all event processing if SyncEvents=true |
| Ignore panics in handlers | Wrap with `recover()` + `debug.Stack()` | Panics in goroutines crash silently |
| Respond after 3 seconds | Defer first, then edit response | Interaction expires, user sees error |
| Use `sync.Mutex` on Bot struct fields | Use `sync.RWMutex` | Readers don't need to block each other |
| Register guild commands in production | Use global commands or `BulkOverwrite` | Guild commands are for development only |
| Skip interaction error responses | Always respond, even with error message | Silent failures confuse users |

## Reference Files

| File | Contents |
|------|----------|
| `references/library-selection.md` | discordgo vs arikawa vs disgo decision matrix, go.mod configs, companion packages, migration notes |
| `references/project-setup.md` | Directory structure (simple and production), main.go bootstrapping, configuration, .env handling, Bot struct pattern |
| `references/commands-and-interactions.md` | Slash commands, handler patterns (map dispatch, interface, cmdroute, ken), parameter types, autocomplete, subcommands, permissions, embeds |
| `references/components-and-modals.md` | Buttons, select menus, modals, Components V2, component routing by CustomID, type assertions |
| `references/event-handling.md` | Gateway intents (standard and privileged), event handler registration, common event types, state cache, interaction type routing |
| `references/state-and-database.md` | Bot struct pattern, database integration (pgx, sqlx, entgo, GORM), Redis, in-memory state, background goroutines, context propagation |
| `references/voice-and-audio.md` | discordgo VoiceConnection, OpusSend/OpusRecv, dgvoice/dca helpers, arikawa voice, ffmpeg pipeline, queue management |
| `references/deployment-and-ops.md` | Docker multi-stage builds, systemd services, structured logging (slog/zap), error handling, graceful shutdown, goroutine safety, sharding, CI/CD |
