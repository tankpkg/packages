# Voice and Audio

Sources: Songbird v0.4 docs, serenity voice examples, Discord voice gateway API (2026)

Covers: Songbird setup, joining/leaving voice channels, audio playback, queue
management, voice events, audio sources, voice receive.

## Songbird Overview

Serenity does not handle voice connections directly. Use **Songbird** — the
official voice library for the serenity ecosystem.

Songbird provides:
- Voice channel join/leave
- Audio playback (files, URLs, streams)
- Queue management
- Voice event hooks (speaking, silence, disconnect)
- Audio receive (speech-to-text, recording)

## Setup

### Dependencies

```toml
[dependencies]
serenity = { version = "0.12", features = ["voice", "client", "gateway", "cache"] }
songbird = "0.4"
symphonia = { version = "0.5", features = ["mp3", "ogg", "wav", "aac"] }
tokio = { version = "1", features = ["rt-multi-thread", "macros", "signal"] }
```

The `voice` feature in serenity enables voice state tracking. Symphonia provides
audio codec support.

### Required Intent

```rust
let intents = GatewayIntents::non_privileged()
    | GatewayIntents::GUILD_VOICE_STATES;  // MANDATORY for voice
```

Without `GUILD_VOICE_STATES`, the bot cannot detect voice channel membership
or join voice channels.

### Registration

```rust
use songbird::SerenityInit;

let client = serenity::ClientBuilder::new(token, intents)
    .framework(framework)
    .register_songbird()  // Register voice manager
    .await?;
```

For poise, store the Songbird manager in your Data struct:

```rust
pub struct Data {
    pub songbird: std::sync::Arc<songbird::Songbird>,
    // ...
}

// In setup:
.setup(|ctx, _ready, framework| {
    Box::pin(async move {
        let songbird = songbird::Songbird::serenity();
        Ok(Data {
            songbird,
            // ...
        })
    })
})

// Register with client builder:
let client = serenity::ClientBuilder::new(token, intents)
    .framework(framework)
    .voice_manager::<songbird::Songbird>(data.songbird.clone())
    .await?;
```

## Joining and Leaving Voice Channels

### Join

```rust
#[poise::command(slash_command, guild_only)]
async fn join(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();

    // Get the user's current voice channel
    let channel_id = {
        let guild = ctx.guild().unwrap();
        guild.voice_states
            .get(&ctx.author().id)
            .and_then(|vs| vs.channel_id)
    };

    let channel_id = match channel_id {
        Some(id) => id,
        None => {
            ctx.say("You must be in a voice channel.").await?;
            return Ok(());
        }
    };

    let manager = songbird::get(ctx.serenity_context()).await.unwrap();
    let (handler_lock, result) = manager.join(guild_id, channel_id).await;

    if result.is_ok() {
        ctx.say(format!("Joined <#{}>", channel_id)).await?;
    } else {
        ctx.say("Failed to join voice channel.").await?;
    }

    Ok(())
}
```

### Leave

```rust
#[poise::command(slash_command, guild_only)]
async fn leave(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();
    let manager = songbird::get(ctx.serenity_context()).await.unwrap();

    if manager.get(guild_id).is_some() {
        manager.remove(guild_id).await?;
        ctx.say("Left voice channel.").await?;
    } else {
        ctx.say("Not in a voice channel.").await?;
    }

    Ok(())
}
```

## Audio Playback

### Play a Local File

```rust
#[poise::command(slash_command, guild_only)]
async fn play_file(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();
    let manager = songbird::get(ctx.serenity_context()).await.unwrap();

    if let Some(handler_lock) = manager.get(guild_id) {
        let mut handler = handler_lock.lock().await;

        let source = songbird::input::File::new("audio/notification.mp3");
        let track_handle = handler.play_input(source.into());

        ctx.say("Playing audio!").await?;
    } else {
        ctx.say("Not in a voice channel. Use /join first.").await?;
    }

    Ok(())
}
```

### Play from URL (YouTube/HTTP)

For URL-based playback, use `yt-dlp` or `youtube-dl` as a source:

```rust
use songbird::input::YoutubeDl;

#[poise::command(slash_command, guild_only)]
async fn play(
    ctx: Context<'_>,
    #[description = "URL to play"] url: String,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();
    let manager = songbird::get(ctx.serenity_context()).await.unwrap();

    if let Some(handler_lock) = manager.get(guild_id) {
        let mut handler = handler_lock.lock().await;

        // Requires yt-dlp installed on system
        let source = YoutubeDl::new(
            ctx.data().reqwest.clone(),
            url,
        );
        handler.enqueue_input(source.into()).await;

        let queue_len = handler.queue().len();
        ctx.say(format!("Added to queue (position {})", queue_len)).await?;
    }

    Ok(())
}
```

**Prerequisite**: Install `yt-dlp` on the host system:
```bash
# Ubuntu/Debian
sudo apt install yt-dlp

# macOS
brew install yt-dlp

# Or via pip
pip install yt-dlp
```

### Queue Management

```rust
#[poise::command(slash_command, guild_only)]
async fn skip(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();
    let manager = songbird::get(ctx.serenity_context()).await.unwrap();

    if let Some(handler_lock) = manager.get(guild_id) {
        let handler = handler_lock.lock().await;
        let queue = handler.queue();
        let _ = queue.skip();
        ctx.say("Skipped current track.").await?;
    }
    Ok(())
}

#[poise::command(slash_command, guild_only)]
async fn stop(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();
    let manager = songbird::get(ctx.serenity_context()).await.unwrap();

    if let Some(handler_lock) = manager.get(guild_id) {
        let handler = handler_lock.lock().await;
        handler.queue().stop();
        ctx.say("Stopped playback and cleared queue.").await?;
    }
    Ok(())
}

#[poise::command(slash_command, guild_only)]
async fn pause(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();
    let manager = songbird::get(ctx.serenity_context()).await.unwrap();

    if let Some(handler_lock) = manager.get(guild_id) {
        let handler = handler_lock.lock().await;
        let _ = handler.queue().pause();
        ctx.say("Paused.").await?;
    }
    Ok(())
}

#[poise::command(slash_command, guild_only)]
async fn resume(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();
    let manager = songbird::get(ctx.serenity_context()).await.unwrap();

    if let Some(handler_lock) = manager.get(guild_id) {
        let handler = handler_lock.lock().await;
        let _ = handler.queue().resume();
        ctx.say("Resumed.").await?;
    }
    Ok(())
}
```

## Voice Events

### Track End / Error Events

```rust
use songbird::{Event, EventContext, EventHandler as VoiceEventHandler, TrackEvent};

struct TrackEndNotifier {
    channel_id: serenity::ChannelId,
    http: std::sync::Arc<serenity::Http>,
}

#[serenity::async_trait]
impl VoiceEventHandler for TrackEndNotifier {
    async fn act(&self, ctx: &EventContext<'_>) -> Option<Event> {
        if let EventContext::Track(track_list) = ctx {
            self.channel_id
                .say(&self.http, "Track finished playing.")
                .await
                .ok();
        }
        None
    }
}

// Register in handler
let mut handler = handler_lock.lock().await;
handler.add_global_event(
    Event::Track(TrackEvent::End),
    TrackEndNotifier {
        channel_id: ctx.channel_id(),
        http: ctx.serenity_context().http.clone(),
    },
);
```

### Auto-Disconnect on Empty Channel

```rust
struct EmptyChannelHandler {
    guild_id: serenity::GuildId,
    manager: std::sync::Arc<songbird::Songbird>,
}

#[serenity::async_trait]
impl VoiceEventHandler for EmptyChannelHandler {
    async fn act(&self, _ctx: &EventContext<'_>) -> Option<Event> {
        // Check if bot is alone in the channel
        // If so, disconnect after a delay
        let _ = self.manager.remove(self.guild_id).await;
        None
    }
}
```

## Audio Encoding Requirements

Discord voice uses:
- **Codec**: Opus
- **Sample rate**: 48 kHz
- **Channels**: 2 (stereo)
- **Frame size**: 20 ms (960 samples)

Songbird handles encoding automatically. Symphonia handles decoding from
common formats (MP3, OGG, WAV, AAC, FLAC).

## Volume Control

```rust
// Set volume on current track (0.0 to 2.0)
if let Some(track) = handler.queue().current() {
    track.set_volume(0.5)?;  // 50% volume
}
```

## Voice Receive (Advanced)

Songbird can receive audio from voice channels for recording or
speech-to-text:

```rust
use songbird::{CoreEvent, EventContext, EventHandler as VoiceEventHandler};

struct VoiceReceiver;

#[serenity::async_trait]
impl VoiceEventHandler for VoiceReceiver {
    async fn act(&self, ctx: &EventContext<'_>) -> Option<songbird::Event> {
        if let EventContext::SpeakingStateUpdate(speaking) = ctx {
            tracing::info!(
                "User {} {} speaking",
                speaking.ssrc,
                if speaking.speaking { "started" } else { "stopped" }
            );
        }
        None
    }
}

// Register
handler.add_global_event(
    songbird::Event::Core(CoreEvent::SpeakingStateUpdate),
    VoiceReceiver,
);
```

## Common Voice Bot Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Forget `GUILD_VOICE_STATES` intent | Always include it | Bot cannot join voice without it |
| Block handler lock | Release lock quickly | Other operations wait |
| Ignore empty channels | Auto-disconnect after timeout | Wastes resources |
| Play without checking queue | Use `enqueue_input` | Prevents overlapping audio |
| Hardcode `yt-dlp` path | Use `which` or config | Portability |
| Skip error handling on join | Check `result.is_ok()` | May lack permissions |
