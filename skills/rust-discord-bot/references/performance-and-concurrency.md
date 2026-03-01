# Performance and Concurrency

Sources: tokio runtime docs, serenity sharding, Rust Performance Book, production bot benchmarks (2026)

Covers: tokio runtime tuning, memory optimization, sharding, concurrency
patterns, rate limiting, Cargo release profiles, binary size optimization.

## Tokio Runtime Configuration

### Default (Recommended for Most Bots)

```rust
#[tokio::main]
async fn main() {
    // Uses multi-thread runtime with num_cpus worker threads
}
```

### Explicit Configuration

```rust
#[tokio::main(flavor = "multi_thread", worker_threads = 4)]
async fn main() {
    // 4 worker threads — good for most Discord bots
}
```

### Custom Runtime (Advanced)

```rust
fn main() {
    let runtime = tokio::runtime::Builder::new_multi_thread()
        .worker_threads(4)
        .thread_name("discord-worker")
        .thread_stack_size(3 * 1024 * 1024)  // 3 MB stack
        .enable_all()
        .build()
        .unwrap();

    runtime.block_on(async {
        // bot startup...
    });
}
```

### Worker Thread Guidelines

| Bot Size | Guilds | Workers | Rationale |
|----------|--------|---------|-----------|
| Small | <100 | 2 | I/O-bound, minimal CPU |
| Medium | 100-2,500 | 4 | Default is fine |
| Large | 2,500-10,000 | 4-8 | More shards need more threads |
| Very large | 10,000+ | 8-16 | Consider multi-process instead |

Discord bots are I/O-bound. More worker threads do not help unless the bot
performs CPU-intensive work (image processing, ML inference).

### Blocking Operations

Never block the tokio runtime. Use `spawn_blocking` for CPU-heavy or
synchronous operations:

```rust
// ❌ BAD: blocks a worker thread
let result = expensive_computation();

// ✅ GOOD: runs on blocking thread pool
let result = tokio::task::spawn_blocking(|| {
    expensive_computation()
}).await?;
```

Common blocking operations in Discord bots:
- Image generation/manipulation
- Audio encoding/decoding
- Diesel database queries (Diesel is synchronous)
- File I/O with large files
- Cryptographic operations

## Memory Optimization

### String Allocation Patterns

```rust
// ❌ BAD: unnecessary allocation
fn format_user(user: &User) -> String {
    let name = user.name.clone();  // Clones the string
    format!("User: {}", name)
}

// ✅ GOOD: borrow instead of clone
fn format_user(user: &User) -> String {
    format!("User: {}", user.name)  // Borrows &str
}

// ❌ BAD: allocates Vec<String>
let parts: Vec<String> = input.split(' ')
    .map(|s| s.to_string())
    .collect();

// ✅ GOOD: zero-copy slices
let parts: Vec<&str> = input.split(' ').collect();
```

### Arc for Shared Data

`Arc::clone()` is cheap — it increments a reference counter, not the data.
Dereference has zero overhead compared to `&T`.

```rust
let config = Arc::new(load_config()?);

// Cheap clone for spawned tasks
let config_clone = Arc::clone(&config);
tokio::spawn(async move {
    use_config(&config_clone).await;
});
```

### Cache Memory Management

```rust
// Limit serenity's message cache
let settings = serenity::cache::Settings::default()
    .max_messages(50);  // Per channel

// Disable cache entirely for minimal memory
// In Cargo.toml: default-features = false, omit "cache"

// Moka cache with capacity limit
let cache = Cache::builder()
    .max_capacity(10_000)  // Hard cap on entries
    .time_to_live(Duration::from_secs(300))  // Auto-expire
    .build();
```

## Sharding

Discord requires sharding for bots in 2,500+ guilds. Each shard handles a
subset of guilds via separate gateway connections.

### Automatic Sharding

```rust
// Discord recommends shard count
client.start_autosharded().await?;
```

### Manual Shard Count

```rust
// Fixed shard count
client.start_shards(4).await?;
```

### Distributed Sharding (Multi-Process)

Run different shard ranges on different machines:

```rust
// Process 1: shards 0-1 of 4 total
client.start_shard_range([0, 1], 4).await?;

// Process 2: shards 2-3 of 4 total
client.start_shard_range([2, 3], 4).await?;
```

### Shard Monitoring

```rust
let manager = client.shard_manager.clone();

tokio::spawn(async move {
    loop {
        tokio::time::sleep(Duration::from_secs(30)).await;
        let runners = manager.runners.lock().await;
        for (id, runner) in runners.iter() {
            tracing::info!(
                "Shard {} — latency: {:?}, stage: {:?}",
                id, runner.latency, runner.stage
            );
        }
    }
});
```

### Shard Selection Formula

Discord assigns guilds to shards:

```
shard_id = (guild_id >> 22) % total_shards
```

## Concurrency Patterns

### Bounded Task Spawning

Prevent unbounded memory growth from spawning too many tasks:

```rust
use tokio::sync::Semaphore;

let semaphore = Arc::new(Semaphore::new(10));  // Max 10 concurrent

for item in items {
    let permit = semaphore.clone().acquire_owned().await?;
    tokio::spawn(async move {
        process_item(item).await;
        drop(permit);  // Release slot
    });
}
```

### Channel-Based Task Queue

```rust
use tokio::sync::mpsc;

let (tx, mut rx) = mpsc::channel::<ModAction>(100);

// Producer (event handler)
tx.send(ModAction::Ban { user_id, reason }).await?;

// Consumer (background task)
tokio::spawn(async move {
    while let Some(action) = rx.recv().await {
        match action {
            ModAction::Ban { user_id, reason } => {
                execute_ban(user_id, &reason).await;
            }
            ModAction::Mute { user_id, duration } => {
                execute_mute(user_id, duration).await;
            }
        }
    }
});
```

### Select for Multiple Futures

```rust
tokio::select! {
    msg = rx.recv() => {
        if let Some(msg) = msg {
            handle_message(msg).await;
        }
    }
    _ = tokio::time::sleep(Duration::from_secs(60)) => {
        // Timeout — no messages for 60 seconds
        cleanup().await;
    }
    _ = tokio::signal::ctrl_c() => {
        // Shutdown signal
        break;
    }
}
```

## Rate Limit Handling

Serenity handles Discord API rate limits automatically. The HTTP client tracks
per-route buckets and delays requests when limits are hit.

### Disabling Rate Limiter (API Proxies)

```rust
let http = serenity::HttpBuilder::new(token)
    .ratelimiter_disabled(true)  // For API proxy setups
    .build();
```

### Custom Rate Limiting for Bot Features

```rust
use dashmap::DashMap;
use std::time::{Duration, Instant};

struct RateLimiter {
    limits: DashMap<(UserId, &'static str), Instant>,
}

impl RateLimiter {
    fn check(&self, user_id: UserId, command: &'static str, cooldown: Duration) -> bool {
        let key = (user_id, command);
        if let Some(last) = self.limits.get(&key) {
            if last.elapsed() < cooldown {
                return false;  // Rate limited
            }
        }
        self.limits.insert(key, Instant::now());
        true
    }
}
```

## Cargo Release Profile

### Maximum Performance

```toml
[profile.release]
opt-level = 3        # Maximum optimization
lto = "fat"          # Full link-time optimization
codegen-units = 1    # Single codegen unit (better optimization)
strip = true         # Strip debug symbols
panic = "abort"      # No unwinding (smaller binary)
```

**Trade-off**: Build time increases 3-5x. Use for final deployment builds.

### Balanced (Faster Builds)

```toml
[profile.release]
opt-level = 3
lto = "thin"         # Faster LTO
codegen-units = 16   # Faster parallel codegen
strip = true
```

### Minimum Binary Size

```toml
[profile.release]
opt-level = "z"      # Optimize for size
lto = true
codegen-units = 1
strip = true
panic = "abort"
```

### Development Optimization

Speed up dev builds by optimizing dependencies but not your code:

```toml
# Optimize deps even in debug mode
[profile.dev.package."*"]
opt-level = 2

# Faster linker
# .cargo/config.toml
[target.x86_64-unknown-linux-gnu]
linker = "clang"
rustflags = ["-C", "link-arg=-fuse-ld=lld"]
```

## SIMD JSON Parsing

Enable SIMD-accelerated JSON parsing for high-throughput bots:

```toml
serenity = { version = "0.12", features = ["simd_json"] }
```

Provides measurable improvement for bots processing thousands of events per
second. Requires a CPU with SSE2/AVX2 support (all modern x86 CPUs).

## Gateway Compression

Reduce bandwidth by enabling gateway compression:

```toml
# Zstandard (default in twilight, faster decompression)
serenity = { version = "0.12", features = ["zstd_compression"] }

# Zlib (traditional, wider support)
serenity = { version = "0.12", features = ["zlib_compression"] }
```

For twilight:
```toml
twilight-gateway = { version = "0.16", features = ["zstd"] }  # Default
```

## Performance Checklist

| Area | Action |
|------|--------|
| Runtime | Use multi-thread with 2-4 workers |
| Blocking | `spawn_blocking` for CPU work |
| Strings | Borrow `&str` instead of cloning `String` |
| Shared state | `Arc` for data, `DashMap` for concurrent maps |
| Cache | Set `max_messages`, use moka with TTL |
| Sharding | Enable at 2,000+ guilds |
| Tasks | Bound concurrency with `Semaphore` |
| Release | `lto = "fat"`, `codegen-units = 1`, `strip = true` |
| JSON | Enable `simd_json` for high throughput |
| Gateway | Enable compression (`zstd`) |
