# Event Handling and Gateway Intents

Sources: serenity-rs v0.12.5 gateway docs, Discord API gateway reference (2026), production bot patterns

Covers: gateway intents configuration, privileged intents, event handler patterns,
FullEvent variants, message processing, reaction handling, member events.

## Gateway Intents

Intents control which events the bot receives from Discord's gateway. Configure
them at client creation — events not covered by selected intents are silently
dropped.

### Intent Configuration

```rust
use serenity::model::gateway::GatewayIntents;

// Minimal (slash commands only — no message content needed)
let intents = GatewayIntents::empty();

// Standard non-privileged (recommended starting point)
let intents = GatewayIntents::non_privileged();

// With message content (prefix commands — requires privileged intent)
let intents = GatewayIntents::non_privileged()
    | GatewayIntents::MESSAGE_CONTENT;

// Voice bot
let intents = GatewayIntents::non_privileged()
    | GatewayIntents::GUILD_VOICE_STATES;

// Moderation bot (member tracking)
let intents = GatewayIntents::non_privileged()
    | GatewayIntents::GUILD_MEMBERS;
```

### Intent Reference

| Intent | Privileged? | Events Enabled |
|--------|------------|----------------|
| `GUILDS` | No | Guild create/update/delete, channel/role changes |
| `GUILD_MEMBERS` | **Yes** | Member add/remove/update |
| `GUILD_MODERATION` | No | Ban add/remove, audit log |
| `GUILD_EMOJIS_AND_STICKERS` | No | Emoji/sticker updates |
| `GUILD_INTEGRATIONS` | No | Integration updates |
| `GUILD_WEBHOOKS` | No | Webhook updates |
| `GUILD_INVITES` | No | Invite create/delete |
| `GUILD_VOICE_STATES` | No | Voice state updates (required for Songbird) |
| `GUILD_PRESENCES` | **Yes** | Online/offline/activity status |
| `GUILD_MESSAGES` | No | Message create/update/delete in guilds |
| `GUILD_MESSAGE_REACTIONS` | No | Reaction add/remove in guilds |
| `GUILD_MESSAGE_TYPING` | No | Typing indicators |
| `DIRECT_MESSAGES` | No | DM message events |
| `DIRECT_MESSAGE_REACTIONS` | No | DM reaction events |
| `MESSAGE_CONTENT` | **Yes** | Access to message content, embeds, attachments |
| `GUILD_SCHEDULED_EVENTS` | No | Scheduled event CRUD |
| `AUTO_MODERATION_CONFIG` | No | AutoMod rule changes |
| `AUTO_MODERATION_EXECUTION` | No | AutoMod actions taken |
| `GUILD_MESSAGE_POLLS` | No | Poll create/vote events |

### Privileged Intents

Three intents require explicit enablement in the Discord Developer Portal:

1. **GUILD_MEMBERS** — Member join/leave/update events. Needed for welcome
   messages, member tracking, role management.
2. **GUILD_PRESENCES** — User online status and activity. Rarely needed.
3. **MESSAGE_CONTENT** — Access to message text. Required for prefix commands.
   Without it, `msg.content` is empty for bot messages in guilds.

**Verification requirement**: Bots in 100+ guilds must be verified by Discord
to use privileged intents. Justification required for each intent.

**Recommendation**: Use slash commands to avoid MESSAGE_CONTENT. Only request
GUILD_MEMBERS if the bot needs member event tracking.

## Poise Event Handler

Poise provides a single event handler function that receives all gateway events
not handled by the command framework.

### Setup

```rust
let framework = poise::Framework::builder()
    .options(poise::FrameworkOptions {
        commands: vec![/* ... */],
        event_handler: |ctx, event, framework, data| {
            Box::pin(event_handler(ctx, event, framework, data))
        },
        ..Default::default()
    })
    // ...
```

### Event Handler Function

```rust
async fn event_handler(
    ctx: &serenity::Context,
    event: &serenity::FullEvent,
    _framework: poise::FrameworkContext<'_, Data, Error>,
    data: &Data,
) -> Result<(), Error> {
    match event {
        serenity::FullEvent::Ready { data_about_bot } => {
            tracing::info!("Connected as {}", data_about_bot.user.name);
        }

        serenity::FullEvent::Message { new_message } => {
            // Non-command message processing
            if new_message.author.bot {
                return Ok(());  // Ignore bot messages
            }
            handle_message(ctx, new_message, data).await?;
        }

        serenity::FullEvent::GuildMemberAddition { new_member } => {
            send_welcome(ctx, new_member, data).await?;
        }

        serenity::FullEvent::GuildMemberRemoval { guild_id, user, .. } => {
            log_member_leave(ctx, *guild_id, user, data).await?;
        }

        serenity::FullEvent::ReactionAdd { add_reaction } => {
            handle_reaction(ctx, add_reaction, data).await?;
        }

        serenity::FullEvent::InteractionCreate { interaction } => {
            // Handle modal submissions and non-command interactions
            if let serenity::Interaction::Modal(modal) = interaction {
                handle_modal_submit(ctx, modal, data).await?;
            }
        }

        serenity::FullEvent::VoiceStateUpdate { old, new } => {
            handle_voice_update(ctx, old.as_ref(), new, data).await?;
        }

        _ => {}  // Ignore unhandled events
    }
    Ok(())
}
```

### Common FullEvent Variants

| Event | Trigger | Common Use |
|-------|---------|------------|
| `Ready` | Bot connected | Log startup, set activity |
| `Resume` | Reconnected after disconnect | Log reconnection |
| `Message` | Message created | Auto-moderation, keyword tracking |
| `MessageUpdate` | Message edited | Edit logging |
| `MessageDelete` | Message deleted | Delete logging |
| `ReactionAdd` | Reaction added | Reaction roles, polls |
| `ReactionRemove` | Reaction removed | Undo reaction roles |
| `GuildMemberAddition` | Member joined | Welcome messages, auto-roles |
| `GuildMemberRemoval` | Member left/kicked | Leave logging |
| `GuildMemberUpdate` | Role/nick changed | Role tracking |
| `GuildCreate` | Bot joins guild | Setup, logging |
| `GuildDelete` | Bot leaves guild | Cleanup |
| `InteractionCreate` | Any interaction | Modal submits, custom components |
| `VoiceStateUpdate` | Voice state changed | Voice tracking, auto-disconnect |
| `PresenceUpdate` | Status changed | Activity tracking (privileged) |
| `ChannelCreate/Update/Delete` | Channel modified | Channel logging |
| `GuildBanAddition/Removal` | Ban added/removed | Moderation logging |

## Raw Serenity Event Handler

Without poise, implement the `EventHandler` trait directly:

```rust
struct Handler;

#[serenity::async_trait]
impl serenity::EventHandler for Handler {
    async fn message(&self, ctx: serenity::Context, msg: serenity::Message) {
        if msg.content == "!ping" {
            if let Err(e) = msg.channel_id.say(&ctx.http, "Pong!").await {
                tracing::error!("Failed to send message: {:?}", e);
            }
        }
    }

    async fn ready(&self, _ctx: serenity::Context, ready: serenity::Ready) {
        tracing::info!("{} is connected!", ready.user.name);
    }

    async fn interaction_create(
        &self,
        ctx: serenity::Context,
        interaction: serenity::Interaction,
    ) {
        if let serenity::Interaction::Command(command) = interaction {
            let content = match command.data.name.as_str() {
                "ping" => "Pong!".to_string(),
                _ => "Unknown command".to_string(),
            };

            let data = serenity::CreateInteractionResponseMessage::new()
                .content(content);
            let builder = serenity::CreateInteractionResponse::Message(data);
            if let Err(e) = command.create_response(&ctx.http, builder).await {
                tracing::error!("Interaction response failed: {:?}", e);
            }
        }
    }
}

// Usage
let client = serenity::ClientBuilder::new(token, intents)
    .event_handler(Handler)
    .await?;
```

## Setting Bot Activity/Presence

```rust
serenity::FullEvent::Ready { data_about_bot } => {
    let activity = serenity::ActivityData::watching("for /help");
    ctx.set_activity(Some(activity));

    // Other activity types:
    // ActivityData::playing("with Rust")
    // ActivityData::listening("music")
    // ActivityData::competing("a tournament")
    // ActivityData::custom("Custom status text")
}
```

## Handling Component Interactions in Events

When components (buttons, selects) are used outside poise commands — for
example in welcome messages or persistent menus — handle them in the
event handler:

```rust
serenity::FullEvent::InteractionCreate { interaction } => {
    if let serenity::Interaction::Component(component) = interaction {
        match component.data.custom_id.as_str() {
            "role_select" => {
                // Handle role selection
                let values = match &component.data.kind {
                    serenity::ComponentInteractionDataKind::StringSelect { values } => values,
                    _ => return Ok(()),
                };
                // Process selected values
                component.create_response(
                    ctx,
                    serenity::CreateInteractionResponse::Message(
                        serenity::CreateInteractionResponseMessage::new()
                            .content("Roles updated!")
                            .ephemeral(true)
                    ),
                ).await?;
            }
            "verify_button" => {
                // Handle verification button
            }
            _ => {}
        }
    }
}
```

## Interaction Response Types

When responding to any interaction (command, component, modal):

| Response Type | When to Use |
|--------------|-------------|
| `Message` | Send a new message |
| `DeferredMessage` | Need >3 seconds to respond, edit later |
| `UpdateMessage` | Edit the message the component was on |
| `DeferredUpdateMessage` | Defer component update, edit later |
| `Modal` | Show a modal form (cannot respond to modal with modal) |

**Critical**: Respond within 3 seconds or the interaction fails. Use
`DeferredMessage` for long operations, then follow up with
`interaction.edit_response()`.

```rust
// Defer for long operations
command.create_response(
    ctx,
    serenity::CreateInteractionResponse::Defer(
        serenity::CreateInteractionResponseMessage::new()
    ),
).await?;

// Later, edit the deferred response
command.edit_response(
    ctx,
    serenity::EditInteractionResponse::new().content("Done!")
).await?;
```
