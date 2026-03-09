# Components and Modals

Sources: discordgo v0.29.0 components/modals examples, Discord API reference (2026), production bot patterns

## Component Type Hierarchy

All component types are integer constants in discordgo. Components V2 (types 9–19) require the `MessageFlagsIsComponentsV2` flag on the message.

| Type | Constant | Value | Notes |
|------|----------|-------|-------|
| Actions Row | `ActionsRow` | 1 | Container for interactive components |
| Button | `Button` | 2 | Clickable button, 5 per row |
| String Select | `SelectMenu` | 3 | Dropdown with custom options |
| Text Input | `TextInput` | 4 | Modal-only input field |
| User Select | `UserSelect` | 5 | Auto-populated from guild members |
| Role Select | `RoleSelect` | 6 | Auto-populated from guild roles |
| Mentionable Select | `MentionableSelect` | 7 | Users and roles combined |
| Channel Select | `ChannelSelect` | 8 | Auto-populated from guild channels |
| Section | `Section` | 9 | Components V2: layout grouping |
| Text Display | `TextDisplay` | 10 | Components V2: formatted text block |
| Thumbnail | `Thumbnail` | 11 | Components V2: small image |
| Media Gallery | `MediaGallery` | 12 | Components V2: image grid |
| File | `File` | 13 | Components V2: file attachment |
| Separator | `Separator` | 14 | Components V2: visual divider |
| Content Inventory Entry | `ContentInventoryEntry` | 16 | Components V2: entitlement display |
| Container | `Container` | 17 | Components V2: styled wrapper |
| Input | `Input` | 18 | Components V2: standalone input |
| Label | `Label` | 19 | Components V2: wraps TextInput in modals |

## Buttons

### Button Styles

| Style | Constant | Value | Color | Use Case |
|-------|----------|-------|-------|----------|
| Primary | `ButtonStylePrimary` | 1 | Blurple | Main action |
| Secondary | `ButtonStyleSecondary` | 2 | Grey | Alternative action |
| Success | `ButtonStyleSuccess` | 3 | Green | Confirm, approve |
| Danger | `ButtonStyleDanger` | 4 | Red | Destructive action |
| Link | `ButtonStyleLink` | 5 | Grey + arrow | External URL, no CustomID |
| Premium | `ButtonStylePremium` | 6 | — | SKU purchase, requires SKUID |

Link buttons use `URL` instead of `CustomID` and do not generate an interaction event. Premium buttons use `SKUID` and also do not generate an interaction event.

### Sending Buttons

Buttons must be wrapped in an `ActionsRow`. Send the row as part of `InteractionResponseData.Components`.

```go
func handlePing(s *discordgo.Session, i *discordgo.InteractionCreate) {
    s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
        Type: discordgo.InteractionResponseChannelMessageWithSource,
        Data: &discordgo.InteractionResponseData{
            Content: "Choose an action:",
            Components: []discordgo.MessageComponent{
                discordgo.ActionsRow{
                    Components: []discordgo.MessageComponent{
                        discordgo.Button{
                            Label:    "Confirm",
                            Style:    discordgo.ButtonStyleSuccess,
                            CustomID: "confirm_action",
                        },
                        discordgo.Button{
                            Label:    "Cancel",
                            Style:    discordgo.ButtonStyleDanger,
                            CustomID: "cancel_action",
                        },
                        discordgo.Button{
                            Label: "Documentation",
                            Style: discordgo.ButtonStyleLink,
                            URL:   "https://discord.com/developers/docs",
                        },
                    },
                },
            },
        },
    })
}
```

To disable a button at creation time, set `Disabled: true` on the `Button` struct.

### Handling Button Clicks

Button clicks arrive as `InteractionMessageComponent` interactions. Route by `CustomID` using a handler map:

```go
var componentHandlers = map[string]func(s *discordgo.Session, i *discordgo.InteractionCreate){
    "confirm_action": handleConfirm,
    "cancel_action":  handleCancel,
}

s.AddHandler(func(s *discordgo.Session, i *discordgo.InteractionCreate) {
    if i.Type == discordgo.InteractionMessageComponent {
        if h, ok := componentHandlers[i.MessageComponentData().CustomID]; ok {
            h(s, i)
        }
    }
})
```

## Select Menus

### Five Select Menu Types

| Type | Constant | Options Required | Returns |
|------|----------|-----------------|---------|
| String Select | `SelectMenu` | Yes — define manually | Selected string values |
| User Select | `UserSelect` | No — auto-populated | User IDs |
| Role Select | `RoleSelect` | No — auto-populated | Role IDs |
| Mentionable Select | `MentionableSelect` | No — auto-populated | User or role IDs |
| Channel Select | `ChannelSelect` | No — auto-populated | Channel IDs |

### String Select Menu

Define options explicitly. Each option has a `Label`, `Value`, and optional `Description` and `Default` flag.

```go
discordgo.ActionsRow{
    Components: []discordgo.MessageComponent{
        discordgo.SelectMenu{
            CustomID:    "color_select",
            Placeholder: "Choose a color",
            MinValues:   discordgo.IntPtr(1),
            MaxValues:   1,
            Options: []discordgo.SelectMenuOption{
                {
                    Label:       "Red",
                    Value:       "red",
                    Description: "A warm color",
                    Default:     false,
                },
                {
                    Label: "Blue",
                    Value: "blue",
                },
                {
                    Label: "Green",
                    Value: "green",
                },
            },
        },
    },
}
```

`MinValues` takes a pointer to int. Use `discordgo.IntPtr(n)` or declare a local variable and pass its address.

### Auto-Populated Select Menus

User, Role, Mentionable, and Channel selects do not require an `Options` slice. Set `MenuType` and Discord populates choices from the guild automatically.

```go
// User select — no Options field needed
discordgo.SelectMenu{
    MenuType:    discordgo.UserSelectMenu,
    CustomID:    "target_user",
    Placeholder: "Select a user",
    MaxValues:   1,
}

// Channel select with type filter
discordgo.SelectMenu{
    MenuType:     discordgo.ChannelSelectMenu,
    CustomID:     "target_channel",
    Placeholder:  "Select a text channel",
    ChannelTypes: []discordgo.ChannelType{discordgo.ChannelTypeGuildText},
}
```

Valid `MenuType` values: `discordgo.UserSelectMenu`, `discordgo.RoleSelectMenu`, `discordgo.MentionableSelectMenu`, `discordgo.ChannelSelectMenu`. The zero value is the string select.

### Reading Selected Values

All select menu interactions arrive as `InteractionMessageComponent`. The selected values are in `MessageComponentData().Values`, a `[]string`.

```go
func handleColorSelect(s *discordgo.Session, i *discordgo.InteractionCreate) {
    data := i.MessageComponentData()
    if len(data.Values) == 0 {
        return
    }
    selected := data.Values[0] // first selected value

    s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
        Type: discordgo.InteractionResponseChannelMessageWithSource,
        Data: &discordgo.InteractionResponseData{
            Content: "You selected: " + selected,
            Flags:   discordgo.MessageFlagsEphemeral,
        },
    })
}
```

For multi-select menus (`MaxValues > 1`), iterate over `data.Values`. For User/Role/Channel selects, `data.Values` contains snowflake ID strings.

## Modals

### Opening a Modal

Respond to a slash command or button click with `InteractionResponseModal`. Modals cannot be opened from another modal.

```go
func handleOpenModal(s *discordgo.Session, i *discordgo.InteractionCreate) {
    s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
        Type: discordgo.InteractionResponseModal,
        Data: &discordgo.InteractionResponseData{
            CustomID: "feedback_modal",
            Title:    "Submit Feedback",
            Components: []discordgo.MessageComponent{
                discordgo.ActionsRow{
                    Components: []discordgo.MessageComponent{
                        discordgo.TextInput{
                            CustomID:    "subject",
                            Label:       "Subject",
                            Style:       discordgo.TextInputShort,
                            Placeholder: "Brief summary",
                            Required:    true,
                            MaxLength:   100,
                        },
                    },
                },
                discordgo.ActionsRow{
                    Components: []discordgo.MessageComponent{
                        discordgo.TextInput{
                            CustomID:    "body",
                            Label:       "Details",
                            Style:       discordgo.TextInputParagraph,
                            Placeholder: "Describe your feedback in detail",
                            Required:    false,
                            MinLength:   10,
                            MaxLength:   1000,
                        },
                    },
                },
            },
        },
    })
}
```

Each `TextInput` must be in its own `ActionsRow`. A modal supports up to 5 rows, so up to 5 text inputs.

### TextInput Styles

| Style | Constant | Appearance | Use Case |
|-------|----------|------------|----------|
| Short | `TextInputShort` | Single line | Names, titles, short answers |
| Paragraph | `TextInputParagraph` | Multi-line | Descriptions, messages, long text |

Both styles support `MinLength`, `MaxLength`, `Placeholder`, `Value` (pre-filled text), and `Required`.

### Components V2 with Label Wrapper

When using Components V2 (flag `MessageFlagsIsComponentsV2`), wrap `TextInput` in a `Label` component instead of an `ActionsRow`. This applies to modal construction under the V2 system.

```go
// Components V2 modal structure
discordgo.Label{
    Components: []discordgo.MessageComponent{
        discordgo.TextInput{
            CustomID: "name",
            Label:    "Your Name",
            Style:    discordgo.TextInputShort,
        },
    },
}
```

For standard (non-V2) modals, use `ActionsRow` wrappers as shown above.

### Handling Modal Submissions

Modal submissions arrive as `InteractionModalSubmit`. Extract field values by walking the `Components` tree with type assertions.

```go
func handleFeedbackModal(s *discordgo.Session, i *discordgo.InteractionCreate) {
    data := i.ModalSubmitData()

    var subject, body string

    for _, row := range data.Components {
        actionsRow, ok := row.(*discordgo.ActionsRow)
        if !ok {
            continue
        }
        for _, component := range actionsRow.Components {
            input, ok := component.(*discordgo.TextInput)
            if !ok {
                continue
            }
            switch input.CustomID {
            case "subject":
                subject = input.Value
            case "body":
                body = input.Value
            }
        }
    }

    s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
        Type: discordgo.InteractionResponseChannelMessageWithSource,
        Data: &discordgo.InteractionResponseData{
            Content: "Feedback received.\nSubject: " + subject + "\nDetails: " + body,
            Flags:   discordgo.MessageFlagsEphemeral,
        },
    })
}
```

### Modal Gotchas

**Type assertions are required.** `data.Components` is `[]discordgo.MessageComponent` (an interface slice). Every element must be type-asserted before accessing fields. Skipping the `ok` check causes a panic on unexpected component types.

**Components V2 flag changes the wrapper type.** If the modal was constructed with `MessageFlagsIsComponentsV2`, the row wrapper is `*discordgo.Label`, not `*discordgo.ActionsRow`. Assert accordingly.

**Modal CustomID must match the handler key.** The `CustomID` on the `InteractionResponseData` (not on individual inputs) is what you route on in `InteractionModalSubmit` handling.

**Modals cannot be opened from modals.** Attempting to respond to a modal submission with another modal returns an API error. Use a follow-up message instead.

**Three-second deadline applies.** The initial `InteractionRespond` call must complete within 3 seconds of the interaction being created. For modals triggered by buttons, the button click starts the clock.

## Component Interaction Routing

### Separate Handler Maps Pattern

Maintain distinct maps for commands, components, and modals. This keeps each concern isolated and makes adding new handlers straightforward.

```go
var (
    commandHandlers = map[string]func(*discordgo.Session, *discordgo.InteractionCreate){
        "feedback": handleOpenModal,
        "ping":     handlePing,
    }
    componentHandlers = map[string]func(*discordgo.Session, *discordgo.InteractionCreate){
        "confirm_action": handleConfirm,
        "cancel_action":  handleCancel,
        "color_select":   handleColorSelect,
    }
    modalHandlers = map[string]func(*discordgo.Session, *discordgo.InteractionCreate){
        "feedback_modal": handleFeedbackModal,
    }
)

s.AddHandler(func(s *discordgo.Session, i *discordgo.InteractionCreate) {
    switch i.Type {
    case discordgo.InteractionApplicationCommand:
        if h, ok := commandHandlers[i.ApplicationCommandData().Name]; ok {
            h(s, i)
        }
    case discordgo.InteractionMessageComponent:
        if h, ok := componentHandlers[i.MessageComponentData().CustomID]; ok {
            h(s, i)
        }
    case discordgo.InteractionModalSubmit:
        if h, ok := modalHandlers[i.ModalSubmitData().CustomID]; ok {
            h(s, i)
        }
    }
})
```

### Unified Switch Pattern

For smaller bots, nested switches inside a single handler are readable without the map overhead. Replace the map lookups in the Separate Handler Maps example with `switch i.ApplicationCommandData().Name`, `switch i.MessageComponentData().CustomID`, and `switch i.ModalSubmitData().CustomID` blocks respectively.

### CustomID Conventions

CustomIDs are arbitrary strings up to 100 characters. Use them to encode routing information and state.

**Prefix routing** — use colon-delimited segments to encode routing and state without exact-match maps:

```go
// CustomID: "ban:456789012345678901:987654321098765432"
// Format:   "action:targetUserID:requestingUserID"
parts := strings.SplitN(i.MessageComponentData().CustomID, ":", 3)
customID := fmt.Sprintf("ban:%s:%s", targetUserID, requestingUserID)
```

**Namespacing** — prefix with the feature name (`feedback:submit`, `moderation:confirm_ban`) to avoid collisions across commands.

Keep embedded data minimal. CustomIDs are not encrypted and are visible in client network traffic.

## Updating Component Messages

To replace the original message content and components after a button or select interaction, respond with `InteractionResponseUpdateMessage`.

```go
func handleConfirm(s *discordgo.Session, i *discordgo.InteractionCreate) {
    s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
        Type: discordgo.InteractionResponseUpdateMessage,
        Data: &discordgo.InteractionResponseData{
            Content:    "Action confirmed. This cannot be undone.",
            Components: []discordgo.MessageComponent{}, // empty = remove all components
        },
    })
}
```

Passing an empty `Components` slice removes all buttons and selects from the message. This prevents double-submission without requiring a separate edit call.

## Disabling Components After Use

To keep the original message layout but prevent further interaction, respond with `InteractionResponseUpdateMessage` and rebuild the component tree with `Disabled: true` on each button or select. There is no partial update API — the full component tree must be resent. Read `i.Message.Components` to preserve existing labels and styles dynamically rather than hardcoding them.

## Component Limits

Discord enforces hard limits on component counts. Exceeding them returns a 400 error from the API.

| Limit | Value |
|-------|-------|
| Buttons per ActionsRow | 5 |
| Select menus per ActionsRow | 1 (cannot mix with buttons) |
| ActionsRows per message | 5 |
| TextInputs per modal | 5 (one per ActionsRow) |
| Characters in CustomID | 100 |
| Characters in button Label | 80 |
| Options in a string select | 25 |
| Characters in modal Title | 45 |
| Characters in TextInput Value (max) | 4000 |
