# Commands and Interactions

Sources: discordgo v0.29.0 examples, arikawa v3 cmdroute docs, ken framework, Discord API reference (2026), production bot analysis (YAGPDB, CJ, ops-bot-iii)


## Slash Command Definition

Every slash command is an `ApplicationCommand` struct registered with Discord's API. Discord stores the definition; your bot handles the resulting interaction events.

```go
var adminPerms int64 = discordgo.PermissionBanMembers
var noDM bool = false

var commands = []*discordgo.ApplicationCommand{
    {Name: "ping", Description: "Responds with pong"},
    {
        Name:                     "ban",
        Description:              "Ban a member from the server",
        DefaultMemberPermissions: &adminPerms,
        DMPermission:             &noDM,
        Options: []*discordgo.ApplicationCommandOption{
            {Type: discordgo.ApplicationCommandOptionUser, Name: "user", Description: "The user to ban", Required: true},
            {Type: discordgo.ApplicationCommandOptionString, Name: "reason", Description: "Reason for the ban"},
        },
    },
}
```

Register commands after `s.Open()`. Use `GuildID = ""` for global commands (up to 1-hour propagation); use a guild ID for instant registration during development. Prefer `ApplicationCommandBulkOverwrite` in production for atomic updates — it replaces all commands in one API call.

### All 11 Option Types

| Constant | Value | Go Type After Parsing |
|---|---|---|
| `ApplicationCommandOptionSubCommand` | 1 | — (routing only) |
| `ApplicationCommandOptionSubCommandGroup` | 2 | — (routing only) |
| `ApplicationCommandOptionString` | 3 | `string` |
| `ApplicationCommandOptionInteger` | 4 | `int64` |
| `ApplicationCommandOptionBoolean` | 5 | `bool` |
| `ApplicationCommandOptionUser` | 6 | `*discordgo.User` |
| `ApplicationCommandOptionChannel` | 7 | `*discordgo.Channel` |
| `ApplicationCommandOptionRole` | 8 | `*discordgo.Role` |
| `ApplicationCommandOptionMentionable` | 9 | `*discordgo.User` or `*discordgo.Role` |
| `ApplicationCommandOptionNumber` | 10 | `float64` |
| `ApplicationCommandOptionAttachment` | 11 | `*discordgo.MessageAttachment` |


## Command Handler Patterns

### Pattern 1: Map-Based Dispatch

The dominant pattern across all official discordgo examples and most production bots. A `map[string]func` routes by command name; a single `AddHandler` call handles all interaction types via a type switch.

```go
var commandHandlers = map[string]func(s *discordgo.Session, i *discordgo.InteractionCreate){
    "ping": handlePing,
    "ban":  handleBan,
}

s.AddHandler(func(s *discordgo.Session, i *discordgo.InteractionCreate) {
    switch i.Type {
    case discordgo.InteractionApplicationCommand:
        if h, ok := commandHandlers[i.ApplicationCommandData().Name]; ok {
            h(s, i)
        }
    case discordgo.InteractionApplicationCommandAutocomplete:
        if h, ok := autocompleteHandlers[i.ApplicationCommandData().Name]; ok {
            h(s, i)
        }
    }
})
```

Build an options map for named access inside handlers:

```go
func handleBan(s *discordgo.Session, i *discordgo.InteractionCreate) {
    data := i.ApplicationCommandData()
    opts := make(map[string]*discordgo.ApplicationCommandInteractionDataOption, len(data.Options))
    for _, o := range data.Options { opts[o.Name] = o }

    target := opts["user"].UserValue(s)
    reason := "No reason provided"
    if r, ok := opts["reason"]; ok { reason = r.StringValue() }

    if err := s.GuildBanCreateWithReason(i.GuildID, target.ID, reason, 0); err != nil {
        respondEphemeral(s, i, "Failed to ban: "+err.Error())
        return
    }
    s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
        Type: discordgo.InteractionResponseChannelMessageWithSource,
        Data: &discordgo.InteractionResponseData{
            Content: fmt.Sprintf("Banned %s: %s", target.Username, reason),
        },
    })
}
```

### Pattern 2: Interface-Based Commands

Used by CJ, ops-bot-iii, and ken. Encapsulates definition and handler in one type, enabling self-registration and dependency injection.

```go
type Command interface {
    Definition() *discordgo.ApplicationCommand
    Handle(s *discordgo.Session, i *discordgo.InteractionCreate)
}

// Registry maps name → Command, exposes a single AddHandler-compatible func.
type CommandRegistry struct{ commands map[string]Command }

func (r *CommandRegistry) Register(cmd Command) { r.commands[cmd.Definition().Name] = cmd }

func (r *CommandRegistry) Handler() func(*discordgo.Session, *discordgo.InteractionCreate) {
    return func(s *discordgo.Session, i *discordgo.InteractionCreate) {
        if i.Type == discordgo.InteractionApplicationCommand {
            if cmd, ok := r.commands[i.ApplicationCommandData().Name]; ok {
                cmd.Handle(s, i)
            }
        }
    }
}
```

### Pattern 3: arikawa cmdroute

arikawa's `cmdroute.Router` provides typed routing with struct-tag option unmarshaling and built-in middleware. Options unmarshal directly into structs via `data.Options.Unmarshal(&opts)`, eliminating manual option iteration.

```go
// Options struct — field names match Discord option names via `discord:` tags
type BanOptions struct {
    User   discord.UserID `discord:"user"`
    Reason string         `discord:"reason"`
}

r := cmdroute.NewRouter()
r.Use(cmdroute.Deferrable(s, cmdroute.DeferOpts{})) // auto-defer all commands

r.AddFunc("ban", func(ctx context.Context, data cmdroute.CommandData) *api.InteractionResponseData {
    var opts BanOptions
    if err := data.Options.Unmarshal(&opts); err != nil {
        return cmdroute.Error(err)
    }
    return &api.InteractionResponseData{Content: option.NewNullableString("Banned.")}
})
```

### Pattern 4: ken Framework

ken wraps discordgo with OOP-style commands, object pooling (safepool), and Before/After middleware hooks.

```go
type BanCommand struct{}

func (c *BanCommand) Name() string        { return "ban" }
func (c *BanCommand) Version() string     { return "1.0.0" }
func (c *BanCommand) Description() string { return "Ban a member" }
func (c *BanCommand) Options() []*discordgo.ApplicationCommandOption {
    return []*discordgo.ApplicationCommandOption{
        {Type: discordgo.ApplicationCommandOptionUser, Name: "user", Required: true},
    }
}
func (c *BanCommand) Run(ctx ken.Context) error {
    user := ctx.Options().Get("user").UserValue(ctx)
    return ctx.RespondMessage("Banned: " + user.Username)
}

type AuthMiddleware struct{}

func (m *AuthMiddleware) Before(ctx ken.Context) (bool, error) {
    if !isAdmin(ctx.GetEvent().Member) {
        return false, ctx.RespondError("Insufficient permissions", "Access Denied")
    }
    return true, nil
}

k, _ := ken.New(session, ken.Options{})
k.RegisterMiddlewares(&AuthMiddleware{})
k.Register(&BanCommand{})
```


## Parameter Types

Retrieve option values using typed methods on `*discordgo.ApplicationCommandInteractionDataOption`:

| Option Type | Method | Returns |
|---|---|---|
| String | `.StringValue()` | `string` |
| Integer | `.IntValue()` | `int64` |
| Boolean | `.BoolValue()` | `bool` |
| Number | `.FloatValue()` | `float64` |
| User | `.UserValue(s)` | `*discordgo.User` |
| Channel | `.ChannelValue(s)` | `*discordgo.Channel` |
| Role | `.RoleValue(s, guildID)` | `*discordgo.Role` |
| Mentionable | `.UserValue(s)` or `.RoleValue(s, guildID)` | depends on resolved type |
| Attachment | `data.Resolved.Attachments[id]` | `*discordgo.MessageAttachment` |


## Autocomplete

Autocomplete fires when a user types in an option marked `Autocomplete: true`. Respond within 3 seconds with up to 25 choices. The focused option has `opt.Focused == true`.

```go
// In the option definition: Autocomplete: true (omit Choices when using autocomplete)

func handleDeployAutocomplete(s *discordgo.Session, i *discordgo.InteractionCreate) {
    data := i.ApplicationCommandData()
    var query string
    for _, opt := range data.Options {
        if opt.Focused {
            query = opt.StringValue()
            break
        }
    }

    all := []string{"production", "staging", "development", "preview"}
    var choices []*discordgo.ApplicationCommandOptionChoice
    for _, srv := range all {
        if strings.Contains(srv, query) {
            choices = append(choices, &discordgo.ApplicationCommandOptionChoice{Name: srv, Value: srv})
        }
    }

    s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
        Type: discordgo.InteractionApplicationCommandAutocompleteResult,
        Data: &discordgo.InteractionResponseData{Choices: choices},
    })
}
```


## Subcommands and Subcommand Groups

Subcommands nest under a parent command. `data.Options[0]` is the selected subcommand; its own `Options` hold the subcommand's parameters.

```go
var deployCommand = &discordgo.ApplicationCommand{
    Name: "deploy", Description: "Deployment commands",
    Options: []*discordgo.ApplicationCommandOption{
        {
            Type: discordgo.ApplicationCommandOptionSubCommand,
            Name: "start", Description: "Start a deployment",
            Options: []*discordgo.ApplicationCommandOption{
                {Type: discordgo.ApplicationCommandOptionString, Name: "env", Required: true},
            },
        },
        {Type: discordgo.ApplicationCommandOptionSubCommand, Name: "rollback", Description: "Roll back"},
    },
}

func handleDeploy(s *discordgo.Session, i *discordgo.InteractionCreate) {
    sub := i.ApplicationCommandData().Options[0]
    switch sub.Name {
    case "start":
        handleDeployStart(s, i, sub.Options[0].StringValue())
    case "rollback":
        handleDeployRollback(s, i)
    }
}
```

For subcommand groups (two levels deep): `data.Options[0]` is the group, `group.Options[0]` is the subcommand, and `subCmd.Options` holds its parameters.


## Permission Checks

### DefaultMemberPermissions (Discord-native)

Set `DefaultMemberPermissions` on the `ApplicationCommand` to let Discord enforce permissions before the interaction reaches your bot. Discord hides the command from users who lack the required permissions.

```go
var modPerms   int64 = discordgo.PermissionManageMessages | discordgo.PermissionKickMembers
var adminPerms int64 = discordgo.PermissionAdministrator

var kickCommand = &discordgo.ApplicationCommand{
    Name:                     "kick",
    Description:              "Kick a member",
    DefaultMemberPermissions: &modPerms,
}
```

Pass a pointer to `int64`. A value of `0` means no permissions required; `nil` inherits from integration settings.

### Custom Permission Middleware (Go pattern)

For role-based or database-driven checks, wrap handlers with a higher-order function. This composes cleanly with the map-dispatch pattern:

```go
type PermLevel int
const (PermUser PermLevel = iota; PermMod; PermAdmin)

func requirePerm(level PermLevel, h func(*discordgo.Session, *discordgo.InteractionCreate)) func(*discordgo.Session, *discordgo.InteractionCreate) {
    return func(s *discordgo.Session, i *discordgo.InteractionCreate) {
        if i.Member == nil {
            respondEphemeral(s, i, "Server-only command.")
            return
        }
        if getUserPermLevel(s, i.GuildID, i.Member) < level {
            respondEphemeral(s, i, "Insufficient permissions.")
            return
        }
        h(s, i)
    }
}

var commandHandlers = map[string]func(*discordgo.Session, *discordgo.InteractionCreate){
    "ping": handlePing,
    "ban":  requirePerm(PermMod, handleBan),
    "nuke": requirePerm(PermAdmin, handleNuke),
}
```


## Context Menu Commands

Context menu commands appear when a user right-clicks a user or message. They have no options; the target is accessed via `data.TargetID` and `data.Resolved`.

```go
// Registration — Type 2 = User, Type 3 = Message:
{Name: "Get User Info",   Type: discordgo.UserApplicationCommand}
{Name: "Report Message",  Type: discordgo.MessageApplicationCommand}

func handleUserInfo(s *discordgo.Session, i *discordgo.InteractionCreate) {
    data := i.ApplicationCommandData()
    user := data.Resolved.Users[data.TargetID]
    s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
        Type: discordgo.InteractionResponseChannelMessageWithSource,
        Data: &discordgo.InteractionResponseData{
            Content: fmt.Sprintf("User: %s (ID: %s)", user.Username, user.ID),
            Flags:   discordgo.MessageFlagsEphemeral,
        },
    })
}

func handleReportMessage(s *discordgo.Session, i *discordgo.InteractionCreate) {
    msg := i.ApplicationCommandData().Resolved.Messages[i.ApplicationCommandData().TargetID]
    // Forward to moderation channel, log to database, etc.
    _ = msg
}
```


## Embeds

Build embeds via `discordgo.MessageEmbed` and pass them in `InteractionResponseData.Embeds`. Up to 10 embeds per message; `Color` is a 24-bit RGB integer.

```go
embed := &discordgo.MessageEmbed{
    Title:     "User Information",
    Color:     0x5865F2, // Discord blurple
    Thumbnail: &discordgo.MessageEmbedThumbnail{URL: user.AvatarURL("256")},
    Fields: []*discordgo.MessageEmbedField{
        {Name: "Username", Value: user.Username, Inline: true},
        {Name: "ID", Value: user.ID, Inline: true},
    },
    Footer:    &discordgo.MessageEmbedFooter{Text: "Requested via /info"},
    Timestamp: time.Now().Format(time.RFC3339),
}
// Pass in response:
Data: &discordgo.InteractionResponseData{Embeds: []*discordgo.MessageEmbed{embed}}
```

### Embed Field Limits

| Field | Limit |
|---|---|
| Title | 256 chars |
| Description | 4096 chars |
| Fields per embed | 25 |
| Field name / value | 256 / 1024 chars |
| Total chars per embed | 6000 |
| Embeds per message | 10 |


## Responding to Interactions

### Immediate Response (within 3 seconds)

```go
s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
    Type: discordgo.InteractionResponseChannelMessageWithSource,
    Data: &discordgo.InteractionResponseData{Content: "Done!"},
})
```

### Deferred Response (thinking... then followup)

When the handler needs more than 3 seconds, acknowledge immediately then send the real response as a followup. The followup window extends to 15 minutes.

```go
s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
    Type: discordgo.InteractionResponseDeferredChannelMessageWithSource,
})
go func() {
    result, err := callExternalAPI()
    if err != nil {
        s.FollowupMessageCreate(i.Interaction, true, &discordgo.WebhookParams{
            Content: "Failed: " + err.Error(), Flags: discordgo.MessageFlagsEphemeral,
        })
        return
    }
    s.FollowupMessageCreate(i.Interaction, true, &discordgo.WebhookParams{Content: result})
}()
```

Spawning a goroutine after deferring is safe — the webhook token remains valid for 15 minutes.

### Ephemeral Messages

Set `Flags: discordgo.MessageFlagsEphemeral` on any `InteractionResponseData` or `WebhookParams` to make the message visible only to the invoking user. Ephemeral responses cannot be deleted by the bot after sending; use them for errors, confirmations, and sensitive output.

### Followup Messages

After any response (immediate or deferred), send, edit, or delete additional messages via the webhook token. The token is valid for 15 minutes.

```go
msg, _ := s.FollowupMessageCreate(i.Interaction, true, &discordgo.WebhookParams{Content: "Step 1."})
s.FollowupMessageEdit(i.Interaction, msg.ID, &discordgo.WebhookEdit{Content: stringPtr("Step 2.")})
s.FollowupMessageDelete(i.Interaction, msg.ID)
```


## Interaction Response Types

| Constant | Value | Use Case |
|---|---|---|
| `InteractionResponsePong` | 1 | Health check ping |
| `InteractionResponseChannelMessageWithSource` | 4 | Standard slash command response |
| `InteractionResponseDeferredChannelMessageWithSource` | 5 | Acknowledge; followup later |
| `InteractionResponseDeferredMessageUpdate` | 6 | Acknowledge component; update later |
| `InteractionResponseUpdateMessage` | 7 | Edit original message (components) |
| `InteractionApplicationCommandAutocompleteResult` | 8 | Return autocomplete choices |
| `InteractionResponseModal` | 9 | Open a modal dialog |


## The 3-Second Deadline

Discord requires an interaction response within 3 seconds. Missing this deadline shows "This interaction failed" to the user.

**Respond immediately** (`InteractionResponseChannelMessageWithSource`) for simple lookups, in-memory operations, and fast database reads.

**Defer then followup** (`InteractionResponseDeferredChannelMessageWithSource`) for any handler that touches external services, performs writes, or has unpredictable latency. The defer is a fast HTTP acknowledgment; the followup window extends to 15 minutes.

A practical rule: always defer for any command that makes an outbound network call. The cost is one extra round-trip; the benefit is eliminating the entire class of timeout failures.
