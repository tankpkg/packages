# Event Handling

Sources: discordgo v0.29.0 docs, arikawa v3 gateway docs, Discord API reference (2026), YAGPDB event system analysis

---

## Gateway Intents

Intents are bitmask flags that tell Discord which events to send. Declare them before `s.Open()`. Undeclared intents result in silently dropped events.

### Standard Intents (Non-Privileged)

| Intent | Bit | Key Events |
|--------|-----|------------|
| `IntentsGuilds` | `1<<0` | GuildCreate/Update/Delete, Channel/Role CRUD |
| `IntentsGuildBans` | `1<<2` | GuildBanAdd, GuildBanRemove |
| `IntentsGuildEmojis` | `1<<3` | GuildEmojisUpdate |
| `IntentsGuildWebhooks` | `1<<5` | WebhooksUpdate |
| `IntentsGuildInvites` | `1<<6` | InviteCreate, InviteDelete |
| `IntentsGuildVoiceStates` | `1<<7` | VoiceStateUpdate |
| `IntentsGuildMessages` | `1<<9` | MessageCreate, MessageUpdate, MessageDelete |
| `IntentsGuildMessageReactions` | `1<<10` | MessageReactionAdd/Remove/RemoveAll |
| `IntentsGuildMessageTyping` | `1<<11` | TypingStart (guilds) |
| `IntentsDirectMessages` | `1<<12` | MessageCreate/Update/Delete (DMs) |
| `IntentsDirectMessageReactions` | `1<<13` | MessageReactionAdd/Remove (DMs) |
| `IntentsGuildScheduledEvents` | `1<<16` | GuildScheduledEventCreate/Update/Delete |
| `IntentsAutoModerationConfiguration` | `1<<20` | AutoModerationRuleCreate/Update/Delete |
| `IntentsAutoModerationExecution` | `1<<21` | AutoModerationActionExecution |
| `IntentsGuildMessagePolls` | `1<<24` | MessagePollVoteAdd/Remove (guilds) |
| `IntentsDirectMessagePolls` | `1<<25` | MessagePollVoteAdd/Remove (DMs) |

### Privileged Intents

Three intents require explicit enablement in the Discord Developer Portal. Bots in 100+ guilds must pass a verification review before these intents are granted.

| Intent | Bit | Unlocks | Verification |
|--------|-----|---------|--------------|
| `IntentsGuildMembers` | `1<<1` | GuildMemberAdd/Update/Remove | Yes (100+ guilds) |
| `IntentsGuildPresences` | `1<<8` | PresenceUpdate | Yes (100+ guilds) |
| `IntentsMessageContent` | `1<<15` | `Message.Content`, `.Attachments`, `.Embeds` in guild messages | Yes (100+ guilds) |

**MessageContent is the most commonly missed privileged intent.** Without it, `Message.Content` is an empty string for all guild messages. Slash commands and interactions are unaffected — they do not require MessageContent. Enable privileged intents at: Discord Developer Portal → your app → Bot → Privileged Gateway Intents.

### Convenience Bundles

| Constant | Includes |
|----------|----------|
| `IntentsAllWithoutPrivileged` | All non-privileged intents (default for `New()`) |
| `IntentsAll` | All intents including all three privileged |
| `IntentsNone` | No intents — only interaction events reach the bot |

`IntentsNone` is appropriate for interaction-only bots (slash commands, buttons, modals) that never read message content.

### Setting Intents

Set intents on `s.Identify.Intents` before `s.Open()`. Combine with bitwise OR.

```go
s, _ := discordgo.New("Bot " + os.Getenv("DISCORD_TOKEN"))
s.Identify.Intents = discordgo.IntentsGuilds |
    discordgo.IntentsGuildMessages |
    discordgo.IntentsMessageContent // privileged — must be enabled in portal
s.AddHandler(onReady)
if err := s.Open(); err != nil {
    log.Fatal(err)
}
```

### Intent Selection Guide

| Feature | Required Intents |
|---------|-----------------|
| Read message text (prefix commands, moderation) | `IntentsGuildMessages` + `IntentsMessageContent` (privileged) |
| Slash commands / buttons / modals only | `IntentsNone` or `IntentsGuilds` |
| Track voice channel membership | `IntentsGuildVoiceStates` |
| Welcome new members | `IntentsGuildMembers` (privileged) |
| User presence / status | `IntentsGuildPresences` (privileged) |
| Emoji reactions | `IntentsGuildMessageReactions` |
| DM support | `IntentsDirectMessages` |

---

## Event Handler Registration

### AddHandler

`AddHandler` uses reflection to match the function signature to the correct event type. The second parameter's concrete type determines which event triggers the handler. Returns a removal function.

```go
remove := s.AddHandler(func(s *discordgo.Session, m *discordgo.MessageCreate) {
    if m.Author.Bot {
        return
    }
    log.Printf("message from %s: %s", m.Author.Username, m.Content)
})
// remove() unregisters the handler
```

Multiple handlers for the same event type are all called in registration order.

### AddHandlerOnce

Fires exactly once, then auto-removes. Use for one-time initialization that depends on gateway state (e.g., registering commands after `State.User.ID` is populated):

```go
s.AddHandlerOnce(func(s *discordgo.Session, r *discordgo.Ready) {
    registerCommands(s)
})
```

### Handler Removal

`AddHandler` returns a zero-argument removal function. Call it to unregister. Supports self-removal:

```go
var remove func()
remove = s.AddHandler(func(s *discordgo.Session, m *discordgo.MessageCreate) {
    if m.Content == "stop" {
        remove()
    }
})
```

### SyncEvents

`s.SyncEvents` controls handler concurrency:

- `false` (default): each handler runs in a new goroutine. Protect shared state with `sync.Mutex`. Panics are silent — wrap with `recover()`.
- `true`: handlers run sequentially in the gateway receive loop. A slow handler blocks all event processing.

Never set `SyncEvents = true` in production. It exists for testing only. Wrap handler bodies with `recover()` to surface panics that would otherwise be silently dropped:

```go
func safe[E any](fn func(*discordgo.Session, E)) func(*discordgo.Session, E) {
    return func(s *discordgo.Session, e E) {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("panic in handler: %v", r)
            }
        }()
        fn(s, e)
    }
}
```

---

## Common Event Types

| Event Type | Struct | Trigger |
|------------|--------|---------|
| `Ready` | `*discordgo.Ready` | Bot connects; contains initial guild list and session ID |
| `Resumed` | `*discordgo.Resumed` | Session resumes after disconnect |
| `MessageCreate` | `*discordgo.MessageCreate` | New message in any subscribed channel |
| `MessageUpdate` | `*discordgo.MessageUpdate` | Message edited; `Content` may be empty if not cached |
| `MessageDelete` | `*discordgo.MessageDelete` | Message deleted; only ID available if not cached |
| `InteractionCreate` | `*discordgo.InteractionCreate` | Slash command, button, select menu, modal, autocomplete |
| `GuildCreate` | `*discordgo.GuildCreate` | Bot joins a guild, or guild becomes available on startup |
| `GuildDelete` | `*discordgo.GuildDelete` | Bot removed from guild, or guild goes unavailable |
| `GuildMemberAdd` | `*discordgo.GuildMemberAdd` | User joins a guild (requires `IntentsGuildMembers`) |
| `GuildMemberRemove` | `*discordgo.GuildMemberRemove` | User leaves or is kicked/banned |
| `GuildMemberUpdate` | `*discordgo.GuildMemberUpdate` | Member roles, nickname, or timeout changes |
| `VoiceStateUpdate` | `*discordgo.VoiceStateUpdate` | User joins, moves, or leaves a voice channel |
| `PresenceUpdate` | `*discordgo.PresenceUpdate` | User status or activity changes (requires `IntentsGuildPresences`) |
| `ChannelCreate` | `*discordgo.ChannelCreate` | New channel created in a guild |
| `GuildBanAdd` | `*discordgo.GuildBanAdd` | User banned from guild |

### Ready, MessageCreate, GuildCreate, VoiceStateUpdate, GuildMemberAdd, PresenceUpdate

```go
// Ready — fires once per connection (not on resume)
s.AddHandler(func(s *discordgo.Session, r *discordgo.Ready) {
    log.Printf("connected as %s (session %s)", r.User.String(), r.SessionID)
})

// MessageCreate — Content is empty without IntentsMessageContent (privileged)
s.AddHandler(func(s *discordgo.Session, m *discordgo.MessageCreate) {
    if m.Author == nil || m.Author.Bot {
        return
    }
    if m.Content == "ping" {
        s.ChannelMessageSend(m.ChannelID, "pong")
    }
})

// GuildCreate — fires on startup for each existing guild and on new joins
s.AddHandler(func(s *discordgo.Session, g *discordgo.GuildCreate) {
    if g.Guild.Unavailable {
        return // outage, not a real join
    }
    log.Printf("guild available: %s", g.Guild.Name)
})

// VoiceStateUpdate — ChannelID="" means user left voice
s.AddHandler(func(s *discordgo.Session, v *discordgo.VoiceStateUpdate) {
    if v.ChannelID == "" {
        log.Printf("user %s left voice", v.UserID)
    } else {
        log.Printf("user %s joined channel %s", v.UserID, v.ChannelID)
    }
})

// GuildMemberAdd — requires IntentsGuildMembers (privileged)
s.AddHandler(func(s *discordgo.Session, m *discordgo.GuildMemberAdd) {
    s.ChannelMessageSend(welcomeChannelID, fmt.Sprintf("Welcome, <@%s>!", m.User.ID))
})

// PresenceUpdate — requires IntentsGuildPresences (privileged); fires very frequently
s.AddHandler(func(s *discordgo.Session, p *discordgo.PresenceUpdate) {
    log.Printf("user %s status: %s", p.User.ID, p.Status)
})
```

---

## Interaction Type Routing

All interactions arrive through a single `InteractionCreate` event. Route by `i.Type` before dispatching.

### The Master Switch Pattern

Four interaction types require distinct handling:

| Type Constant | Value | Data Accessor |
|---------------|-------|---------------|
| `InteractionApplicationCommand` | 2 | `i.ApplicationCommandData()` |
| `InteractionMessageComponent` | 3 | `i.MessageComponentData()` |
| `InteractionApplicationCommandAutocomplete` | 4 | `i.ApplicationCommandData()` |
| `InteractionModalSubmit` | 5 | `i.ModalSubmitData()` |

### Complete Routing Example

```go
var commandHandlers = map[string]func(*discordgo.Session, *discordgo.InteractionCreate){
    "ping": handlePing,
    "ban":  handleBan,
}

var componentHandlers = map[string]func(*discordgo.Session, *discordgo.InteractionCreate){
    "confirm-ban": handleConfirmBan,
    "cancel":      handleCancel,
}

s.AddHandler(func(s *discordgo.Session, i *discordgo.InteractionCreate) {
    switch i.Type {
    case discordgo.InteractionApplicationCommand:
        name := i.ApplicationCommandData().Name
        if h, ok := commandHandlers[name]; ok {
            h(s, i)
        }

    case discordgo.InteractionMessageComponent:
        // CustomID may encode state: "confirm-ban:123456789"
        parts := strings.SplitN(i.MessageComponentData().CustomID, ":", 2)
        if h, ok := componentHandlers[parts[0]]; ok {
            h(s, i)
        }

    case discordgo.InteractionModalSubmit:
        data := i.ModalSubmitData()
        if data.CustomID == "feedback-modal" {
            handleFeedbackModal(s, i, data)
        }

    case discordgo.InteractionApplicationCommandAutocomplete:
        choices := generateChoices(i.ApplicationCommandData())
        s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
            Type: discordgo.InteractionApplicationCommandAutocompleteResult,
            Data: &discordgo.InteractionResponseData{Choices: choices},
        })
    }
})
```

---

## discordgo State Cache

discordgo maintains an in-memory cache populated from gateway events. Enabled by default (`StateEnabled = true`).

### What's Cached

| Object | Populated By |
|--------|-------------|
| Guilds | GuildCreate, GuildUpdate, GuildDelete |
| Channels | GuildCreate, ChannelCreate/Update/Delete |
| Members | GuildCreate, GuildMemberAdd/Update/Remove |
| Roles | GuildCreate, GuildRoleCreate/Update/Delete |
| Voice states | VoiceStateUpdate |
| Messages | MessageCreate/Update/Delete (up to `MaxMessageCount` per channel) |

### Accessing State

```go
me := s.State.User // available after Ready

// All accessors return (T, error); error = not in cache → fall back to REST
guild, err := s.State.Guild(guildID)
if err != nil {
    guild, err = s.Guild(guildID)
}
channel, _ := s.State.Channel(channelID)
member, _ := s.State.Member(guildID, userID)
vs, _ := s.State.VoiceState(guildID, userID)
```

### State Configuration

```go
s.State.MaxMessageCount = 100   // per channel (default: 0 = disabled)
s.State.TrackMembers = true     // default: true
s.State.TrackPresences = false  // default: false — high memory cost
```

### Limitations

The cache is in-memory and per-process. Multi-shard bots need a shared store (Redis, database) for cross-shard lookups. Multiple bot instances do not share state. For large guilds, disable `TrackMembers` and fetch members on demand to control memory usage.

---

## arikawa Event System

arikawa provides a typed event system that eliminates reflection-based dispatch.

### Typed Events

Handlers receive concrete types from the `gateway` package — compile-time safety, no interface{} dispatch:

```go
s.AddHandler(func(e *gateway.MessageCreateEvent) {
    fmt.Println(e.Content)
})
```

### PreHandler

Intercepts events before the state cache is updated. Use for diffing old vs. new state:

```go
s.PreHandler.AddSyncHandler(func(e *gateway.GuildMemberUpdateEvent) {
    old, _ := s.Cabinet.Member(e.GuildID, e.User.ID)
    log.Printf("roles changing: %v → %v", old.RoleIDs, e.RoleIDs)
})
```

### AddIntents Helper

Accumulate intents incrementally: `s.AddIntents(gateway.IntentGuilds)`, `s.AddIntents(gateway.IntentMessageContent)`, etc.

---

## Setting Bot Presence and Activity

```go
s.AddHandler(func(s *discordgo.Session, r *discordgo.Ready) {
    s.UpdateStatusComplex(discordgo.UpdateStatusData{
        Status: "online", // online, idle, dnd, invisible
        Activities: []*discordgo.Activity{{
            Name: "/help",
            Type: discordgo.ActivityTypeListening, // Playing=0, Listening=2, Watching=3, Competing=5
        }},
    })
})
// Rate-limited to 5 updates per 20 seconds
```

---

## YAGPDB Custom Event System

YAGPDB implements a code-generated event dispatch system for large-scale bots. Key patterns:

- **Code generation**: dispatch tables generated from a schema — no reflection overhead at runtime
- **Plugin interface**: each plugin implements `func(evt *EventData) error` rather than ad-hoc handlers
- **Shard orchestrator**: events distributed across shards; each shard process handles a subset of guilds
- **Buffered dispatch**: per-plugin channels decouple event ingestion from processing, preventing slow plugins from blocking the gateway receive loop
