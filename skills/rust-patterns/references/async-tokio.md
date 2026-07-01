# Async Rust and Tokio

Sources: Gjengset (Rust for Rustaceans), Tokio documentation (tokio.rs), Rust Async Book (rust-lang.github.io/async-book), Blandy/Orendorff/Tindall (Programming Rust 2nd ed.)

Covers: Tokio runtime configuration, task spawning, channels, select!, timeouts, cancellation, stream processing, and common async pitfalls.

## Async Fundamentals

Rust async functions return a `Future` -- a lazy value that does nothing until polled. An async runtime (Tokio, async-std) drives futures to completion.

```rust
// async fn returns impl Future<Output = String>
async fn fetch_data(url: &str) -> Result<String, reqwest::Error> {
    let response = reqwest::get(url).await?;
    response.text().await
}
```

Key mental model: `.await` suspends the current task and yields control to the runtime. The runtime polls other tasks while this one waits.

## Tokio Runtime Setup

### Multi-Threaded Runtime (Default)

```rust
#[tokio::main]
async fn main() {
    // Spawns a thread pool sized to available cores
    run_server().await;
}
```

### Single-Threaded Runtime

```rust
#[tokio::main(flavor = "current_thread")]
async fn main() {
    // Single-threaded -- useful for testing or simple CLIs
    run_task().await;
}
```

### Manual Runtime Construction

```rust
fn main() {
    let rt = tokio::runtime::Builder::new_multi_thread()
        .worker_threads(4)
        .enable_all()
        .build()
        .unwrap();

    rt.block_on(async {
        run_server().await;
    });
}
```

Use manual construction when you need fine-grained control over thread count, or when integrating async into a synchronous application.

## Task Spawning

### tokio::spawn -- Concurrent Tasks

```rust
let handle = tokio::spawn(async {
    expensive_computation().await
});

// Do other work concurrently...

let result = handle.await?;  // JoinHandle returns Result<T, JoinError>
```

Spawned tasks run concurrently. They must be `Send + 'static` because they may run on any thread.

### spawn_blocking -- CPU-Bound Work

Never run CPU-intensive or blocking I/O on the async runtime. Use `spawn_blocking`:

```rust
let result = tokio::task::spawn_blocking(|| {
    // This runs on a dedicated thread pool, not the async runtime
    compute_hash(&large_data)
}).await?;
```

### When to Use Each

| Work Type | Use | Rationale |
|-----------|-----|-----------|
| Network I/O, timers, async | `tokio::spawn` | Cooperative scheduling on runtime threads |
| CPU-bound computation | `spawn_blocking` | Prevents starving async tasks |
| Synchronous file I/O | `spawn_blocking` or `tokio::fs` | std::fs blocks the thread |
| Database queries (async driver) | `tokio::spawn` | sqlx/tokio-postgres are async-native |

## Channels

Tokio provides four channel types for inter-task communication:

### mpsc -- Multiple Producer, Single Consumer

```rust
use tokio::sync::mpsc;

let (tx, mut rx) = mpsc::channel(100);  // bounded, capacity 100

tokio::spawn(async move {
    tx.send("hello".to_string()).await.unwrap();
});

while let Some(msg) = rx.recv().await {
    println!("Received: {msg}");
}
```

### oneshot -- Single Value, Single Use

```rust
use tokio::sync::oneshot;

let (tx, rx) = oneshot::channel();

tokio::spawn(async move {
    let result = compute().await;
    tx.send(result).unwrap();  // send exactly once
});

let value = rx.await?;  // receive exactly once
```

Use for request-response patterns: spawn a task, receive the result via oneshot.

### broadcast -- Multiple Producers, Multiple Consumers

```rust
use tokio::sync::broadcast;

let (tx, _) = broadcast::channel(16);
let mut rx1 = tx.subscribe();
let mut rx2 = tx.subscribe();

tx.send("event".to_string())?;
// Both rx1 and rx2 receive "event"
```

Use for event distribution where every subscriber needs every message.

### watch -- Latest Value Observer

```rust
use tokio::sync::watch;

let (tx, mut rx) = watch::channel("initial".to_string());

tokio::spawn(async move {
    tx.send("updated".to_string()).unwrap();
});

rx.changed().await?;
let value = rx.borrow().clone();
```

Use for configuration updates, health status, or any "latest value" pattern where intermediate values can be skipped.

### Channel Selection Guide

| Pattern | Channel | Bounded? |
|---------|---------|----------|
| Work queue (fan-out) | `mpsc` | Yes -- set capacity to control backpressure |
| Request-response | `oneshot` | N/A -- exactly one message |
| Event broadcast | `broadcast` | Yes -- slow receivers lose messages |
| Latest state | `watch` | N/A -- always holds latest value |
| Unbounded queue (careful) | `mpsc::unbounded_channel` | No -- can OOM under load |

## select! -- Racing Futures

Wait for the first of multiple futures to complete:

```rust
use tokio::select;
use tokio::time::{sleep, Duration};

async fn fetch_with_timeout() -> Result<String, &'static str> {
    select! {
        result = fetch_data() => result.map_err(|_| "fetch failed"),
        _ = sleep(Duration::from_secs(5)) => Err("timeout"),
    }
}
```

### select! Rules

1. All branches are polled concurrently
2. First branch to complete wins; others are cancelled (dropped)
3. Use `biased;` as the first token to poll in declaration order instead of randomly
4. Every branch must return the same type

### Loop + select Pattern

```rust
loop {
    select! {
        Some(msg) = rx.recv() => handle_message(msg).await,
        _ = shutdown.recv() => {
            println!("Shutting down");
            break;
        }
    }
}
```

## Timeouts and Cancellation

### Timeout Wrapper

```rust
use tokio::time::{timeout, Duration};

match timeout(Duration::from_secs(10), long_operation()).await {
    Ok(result) => handle(result),
    Err(_) => eprintln!("Operation timed out"),
}
```

### Graceful Shutdown

```rust
use tokio::signal;
use tokio::sync::watch;

let (shutdown_tx, shutdown_rx) = watch::channel(false);

// Signal handler
tokio::spawn(async move {
    signal::ctrl_c().await.unwrap();
    shutdown_tx.send(true).unwrap();
});

// Worker checks shutdown
async fn worker(mut shutdown: watch::Receiver<bool>) {
    loop {
        select! {
            _ = do_work() => {},
            _ = shutdown.changed() => {
                if *shutdown.borrow() { break; }
            }
        }
    }
    cleanup().await;
}
```

### CancellationToken (tokio-util)

```rust
use tokio_util::sync::CancellationToken;

let token = CancellationToken::new();
let child_token = token.child_token();

tokio::spawn(async move {
    select! {
        _ = work() => {},
        _ = child_token.cancelled() => { /* cleanup */ }
    }
});

// Later: cancel all tasks
token.cancel();
```

## Common Async Pitfalls

### Holding a Lock Across .await

```rust
// WRONG: std::sync::Mutex held across await -- blocks runtime thread
let guard = mutex.lock().unwrap();
do_async_work().await;  // runtime thread blocked while awaiting
drop(guard);

// CORRECT: drop lock before awaiting
{
    let mut guard = mutex.lock().unwrap();
    *guard += 1;
}  // lock released here
do_async_work().await;

// OR: use tokio::sync::Mutex (designed for async)
let guard = async_mutex.lock().await;
do_async_work().await;
drop(guard);
```

### Blocking the Runtime

```rust
// WRONG: blocks the async runtime thread
let data = std::fs::read_to_string("large_file.txt")?;

// CORRECT: use async file I/O or spawn_blocking
let data = tokio::fs::read_to_string("large_file.txt").await?;
```

### Non-Send Types in Spawned Tasks

Spawned tasks must be `Send`. Types like `Rc`, `RefCell`, and `MutexGuard` (std) are not Send:

```rust
// WRONG: Rc is not Send
let data = Rc::new(42);
tokio::spawn(async move { println!("{data}"); }); // compile error

// CORRECT: use Arc for shared ownership across tasks
let data = Arc::new(42);
tokio::spawn(async move { println!("{data}"); });
```

### Forgetting to .await

```rust
// WRONG: future created but never awaited -- does nothing
async fn process() { /* ... */ }
process();  // warning: unused future

// CORRECT: await the future
process().await;
```

## Async Trait Methods

Use the `async-trait` crate or native async trait methods (stabilized in Rust 1.75+):

```rust
// Native (Rust 1.75+) -- preferred
trait Service {
    async fn call(&self, req: Request) -> Response;
}

// With async-trait crate (older code)
#[async_trait::async_trait]
trait Service {
    async fn call(&self, req: Request) -> Response;
}
```

Native async trait methods do not allocate. The `async-trait` crate boxes the future (heap allocation per call). Prefer native syntax in new code.

## Stream Processing

Use `tokio-stream` or `futures::Stream` for async iterators:

```rust
use tokio_stream::StreamExt;

let mut stream = tokio_stream::iter(vec![1, 2, 3, 4, 5]);

while let Some(value) = stream.next().await {
    process(value).await;
}
```

### Concurrent Stream Processing

```rust
use futures::stream::{self, StreamExt};

stream::iter(urls)
    .map(|url| async move { fetch(url).await })
    .buffer_unordered(10)  // up to 10 concurrent fetches
    .for_each(|result| async {
        handle(result);
    })
    .await;
```

`buffer_unordered(n)` limits concurrency to n simultaneous futures -- essential for controlling resource usage.

## Async Review Questions

1. Is this task model genuinely concurrent, or just more complex than needed?
2. Are cancellation and shutdown semantics explicit enough for production?
3. Could locks, channels, or spawned tasks be simplified before adding more async machinery?

## Async Smells

| Smell | Why it matters |
|------|----------------|
| holding locks across `.await` | deadlocks and runtime contention |
| spawning tasks with unclear ownership | leaks and shutdown pain |
| mixing blocking work into async paths casually | stalls runtime progress |

## Final Async Checklist

- [ ] cancellation and shutdown are intentional
- [ ] blocking work is isolated or moved off the async runtime
- [ ] spawn, channel, and lock choices reflect actual concurrency needs
