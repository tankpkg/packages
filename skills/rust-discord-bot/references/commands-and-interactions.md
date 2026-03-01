# Commands and Interactions

Sources: poise v0.6.1 docs, serenity v0.12.5 interaction examples, Discord API reference (2026)

Covers: poise command macros, slash commands, prefix commands, context menus,
parameter types, autocomplete, cooldowns, permission checks, message components
(buttons, select menus, modals), embeds.

## Poise Command Definition

Every command is an `async fn` annotated with `#[poise::command(...)]`. The
function signature defines the command's parameters automatically.

### Basic Command

```rust
/// Responds with "Pong!" and gateway latency
#[poise::command(slash_command, prefix_command)]
async fn ping(ctx: Context<'_>) -> Result<(), Error> {
    let latency = ctx.ping().await;
    ctx.say(format!("Pong! Latency: {:.0?}", latency)).await?;
    Ok(())
}
```

The doc comment becomes the command description in Discord's UI.

### Command Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `slash_command` | Enable as slash command | Always include |
| `prefix_command` | Enable as prefix command | Include if prefix needed |
| `context_menu_command` | Right-click menu command | `= "User Info"` |
| `guild_only` | Restrict to servers | Moderation commands |
| `dm_only` | Restrict to DMs | Private commands |
| `nsfw_only` | Restrict to NSFW channels | Adult content |
| `owners_only` | Restrict to bot owners | Admin/debug commands |
| `required_permissions` | User must have permissions | `= "MANAGE_MESSAGES"` |
| `required_bot_permissions` | Bot must have permissions | `= "BAN_MEMBERS"` |
| `track_edits` | Update response on message edit | Prefix commands |
| `rename` | Override command name | `= "my-command"` |
| `aliases` | Prefix command aliases | `("b", "prohibit")` |
| `subcommands` | Nested commands | `("add", "remove", "list")` |
| `check` | Custom check function | `= "is_moderator"` |
| `global_cooldown` | Seconds between uses (global) | `= 5` |
| `user_cooldown` | Seconds between uses per user | `= 10` |
| `guild_cooldown` | Seconds between uses per guild | `= 3` |
| `channel_cooldown` | Seconds per channel | `= 2` |
| `member_cooldown` | Seconds per member | `= 5` |
| `ephemeral` | Response visible only to invoker | Sensitive data |

## Parameter Types

Poise parses parameters from Rust types. Each parameter becomes a slash command
option or a prefix command argument.

### Supported Types

| Rust Type | Discord Option | Notes |
|-----------|---------------|-------|
| `String` | String | Free text |
| `i32`, `i64`, `u32`, `u64` | Integer | Min/max supported |
| `f32`, `f64` | Number | Min/max supported |
| `bool` | Boolean | True/false toggle |
| `serenity::User` | User | User picker |
| `serenity::Member` | User | Guild member (guild_only) |
| `serenity::Role` | Role | Role picker |
| `serenity::GuildChannel` | Channel | Channel picker |
| `serenity::Message` | String | Message link/ID (prefix only) |
| `serenity::Attachment` | Attachment | File upload |
| `Option<T>` | (any, optional) | Makes parameter optional |
| `Vec<T>` | (variadic) | Prefix only, collects remaining |

### Parameter Attributes

```rust
#[poise::command(slash_command, prefix_command)]
async fn example(
    ctx: Context<'_>,
    #[description = "The target user"]
    user: serenity::User,
    #[description = "Amount to give"]
    #[min = 1]
    #[max = 1000]
    amount: i32,
    #[description = "Reason for action"]
    #[rest]  // Consumes rest of message (prefix only)
    reason: Option<String>,
    #[description = "Target channel"]
    #[channel_types("Text", "News")]
    channel: Option<serenity::GuildChannel>,
) -> Result<(), Error> {
    // ...
    Ok(())
}
```

### Choice Parameters

```rust
#[derive(Debug, poise::ChoiceParameter)]
pub enum TimeUnit {
    #[name = "Seconds"]
    Seconds,
    #[name = "Minutes"]
    Minutes,
    #[name = "Hours"]
    Hours,
    #[name = "Days"]
    Days,
}

#[poise::command(slash_command)]
async fn remind(
    ctx: Context<'_>,
    #[description = "Time amount"] amount: u32,
    #[description = "Time unit"] unit: TimeUnit,
    #[description = "Reminder text"] text: String,
) -> Result<(), Error> {
    // unit is strongly typed
    Ok(())
}
```

## Autocomplete

Provide dynamic suggestions as the user types.

```rust
async fn autocomplete_city(
    _ctx: Context<'_>,
    partial: &str,
) -> impl Iterator<Item = String> {
    let cities = ["New York", "London", "Tokyo", "Paris", "Berlin"];
    cities.iter()
        .filter(move |c| c.to_lowercase().contains(&partial.to_lowercase()))
        .map(|c| c.to_string())
}

#[poise::command(slash_command)]
async fn weather(
    ctx: Context<'_>,
    #[description = "City name"]
    #[autocomplete = "autocomplete_city"]
    city: String,
) -> Result<(), Error> {
    ctx.say(format!("Weather in {city}: Sunny")).await?;
    Ok(())
}
```

Autocomplete functions can return `Iterator`, `Stream`, `Vec<String>`,
or `Vec<serenity::AutocompleteChoice>` for custom display labels.

## Subcommands

```rust
/// Settings management
#[poise::command(slash_command, prefix_command, subcommands("get", "set"))]
async fn settings(ctx: Context<'_>) -> Result<(), Error> {
    ctx.say("Use `/settings get` or `/settings set`").await?;
    Ok(())
}

/// Get a setting value
#[poise::command(slash_command, prefix_command)]
async fn get(
    ctx: Context<'_>,
    #[description = "Setting key"] key: String,
) -> Result<(), Error> {
    // lookup key
    Ok(())
}

/// Set a setting value
#[poise::command(slash_command, prefix_command)]
async fn set(
    ctx: Context<'_>,
    #[description = "Setting key"] key: String,
    #[description = "New value"] value: String,
) -> Result<(), Error> {
    // update key
    Ok(())
}
```

Register only the parent: `commands: vec![settings()]`. Subcommands register
automatically. Slash commands cannot invoke the parent directly — only
subcommands. Prefix commands can invoke either.

## Custom Permission Checks

```rust
async fn is_moderator(ctx: Context<'_>) -> Result<bool, Error> {
    let guild_id = ctx.guild_id().ok_or("Must be in a guild")?;
    let member = ctx.author_member().await.ok_or("Not a member")?;
    let permissions = member.permissions(ctx)?;
    Ok(permissions.contains(serenity::Permissions::MANAGE_MESSAGES))
}

#[poise::command(slash_command, check = "is_moderator")]
async fn purge(
    ctx: Context<'_>,
    #[description = "Number of messages"] count: u32,
) -> Result<(), Error> {
    // Only runs if is_moderator returns true
    Ok(())
}
```

## Context Menu Commands

```rust
/// Get info about a user (right-click → Apps → User Info)
#[poise::command(context_menu_command = "User Info")]
async fn user_info(
    ctx: Context<'_>,
    user: serenity::User,
) -> Result<(), Error> {
    let response = format!(
        "**{}**\nID: {}\nCreated: {}",
        user.name, user.id, user.created_at()
    );
    ctx.say(response).await?;
    Ok(())
}

/// Report a message (right-click → Apps → Report)
#[poise::command(context_menu_command = "Report Message")]
async fn report_message(
    ctx: Context<'_>,
    msg: serenity::Message,
) -> Result<(), Error> {
    ctx.say("Message reported to moderators.").await?;
    Ok(())
}
```

## Embeds

```rust
use serenity::builder::{CreateEmbed, CreateEmbedFooter, CreateEmbedAuthor};

#[poise::command(slash_command)]
async fn info(ctx: Context<'_>) -> Result<(), Error> {
    let embed = CreateEmbed::new()
        .title("Bot Information")
        .description("A high-performance Discord bot written in Rust")
        .color(0x5865F2)
        .field("Language", "Rust", true)
        .field("Framework", "Poise + Serenity", true)
        .field("Uptime", format_uptime(ctx.data()), false)
        .thumbnail(ctx.cache().current_user().face())
        .footer(CreateEmbedFooter::new("Built with ❤️"))
        .timestamp(serenity::Timestamp::now());

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}
```

**Embed limits**: Title 256 chars, description 4096 chars, 25 fields max,
field name 256 chars, field value 1024 chars, footer 2048 chars, total 6000
chars across all fields.

## Message Components

### Buttons

```rust
use serenity::builder::{CreateButton, CreateMessage, CreateActionRow};

#[poise::command(slash_command)]
async fn confirm(ctx: Context<'_>) -> Result<(), Error> {
    let reply = ctx.send(
        poise::CreateReply::default()
            .content("Are you sure?")
            .components(vec![CreateActionRow::Buttons(vec![
                CreateButton::new("confirm_yes")
                    .label("Yes")
                    .style(serenity::ButtonStyle::Success),
                CreateButton::new("confirm_no")
                    .label("No")
                    .style(serenity::ButtonStyle::Danger),
            ])])
    ).await?;

    // Wait for button click (60 second timeout)
    let interaction = reply.message().await?
        .await_component_interaction(ctx.serenity_context().shard.clone())
        .timeout(std::time::Duration::from_secs(60))
        .await;

    if let Some(interaction) = interaction {
        let choice = &interaction.data.custom_id;
        interaction.create_response(
            ctx,
            serenity::CreateInteractionResponse::UpdateMessage(
                serenity::CreateInteractionResponseMessage::new()
                    .content(format!("You chose: {choice}"))
                    .components(vec![])  // Remove buttons
            ),
        ).await?;
    }
    Ok(())
}
```

### Select Menus

```rust
use serenity::builder::{CreateSelectMenu, CreateSelectMenuKind, CreateSelectMenuOption};

let menu = CreateSelectMenu::new(
    "role_select",
    CreateSelectMenuKind::String {
        options: vec![
            CreateSelectMenuOption::new("Rust", "rust").emoji('🦀'),
            CreateSelectMenuOption::new("Python", "python").emoji('🐍'),
            CreateSelectMenuOption::new("Go", "go").emoji('🐹'),
        ],
    },
).placeholder("Pick your language");
```

### Modals

```rust
use serenity::builder::{CreateModal, CreateInputText, CreateActionRow};

#[poise::command(slash_command)]
async fn feedback(ctx: poise::ApplicationContext<'_, Data, Error>) -> Result<(), Error> {
    let modal = CreateModal::new("feedback_modal", "Send Feedback")
        .components(vec![
            CreateActionRow::InputText(
                CreateInputText::new(
                    serenity::InputTextStyle::Short,
                    "Subject",
                    "feedback_subject",
                ).placeholder("Brief subject")
            ),
            CreateActionRow::InputText(
                CreateInputText::new(
                    serenity::InputTextStyle::Paragraph,
                    "Details",
                    "feedback_details",
                ).placeholder("Describe your feedback...")
                 .required(true)
            ),
        ]);

    ctx.interaction.create_response(
        ctx,
        serenity::CreateInteractionResponse::Modal(modal),
    ).await?;

    // Handle modal submit in event_handler via FullEvent::InteractionCreate
    Ok(())
}
```

Modals can only be shown from application command or component interactions.
Handle the modal submission in the `event_handler`, matching on
`FullEvent::InteractionCreate` with `InteractionType::Modal`.

## Help Command

Poise provides built-in help commands:

```rust
commands: vec![
    poise::builtins::help(),        // Simple text-based help
    poise::builtins::pretty_help(), // Embed-based help
    // ... your commands
]
```

The help commands automatically use doc comments and parameter descriptions
from your command definitions. No manual help text needed.
