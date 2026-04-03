# Error Handling

Sources: Gjengset (Rust for Rustaceans), Klabnik/Nichols (The Rust Programming Language 3rd ed.), Rust API Guidelines, thiserror/anyhow documentation, Rust Error Handling Working Group recommendations

Covers: Result and Option combinators, the ? operator, thiserror for libraries, anyhow for applications, custom error types, error conversion patterns, and context propagation.

## Result and Option Fundamentals

```rust
enum Result<T, E> {
    Ok(T),
    Err(E),
}

enum Option<T> {
    Some(T),
    None,
}
```

Both are enums. Pattern match or use combinators. Never use `.unwrap()` in production code paths -- it panics on error.

### The ? Operator

Propagate errors with `?` -- returns early on `Err`, unwraps `Ok`:

```rust
fn read_config(path: &str) -> Result<Config, Box<dyn std::error::Error>> {
    let content = std::fs::read_to_string(path)?;  // returns Err if file read fails
    let config: Config = toml::from_str(&content)?; // returns Err if parse fails
    Ok(config)
}
```

`?` calls `From::from()` on the error, enabling automatic conversion between error types.

### When to Use Option vs Result

| Situation | Use |
|-----------|-----|
| Value may or may not exist (no error context) | `Option<T>` |
| Operation can fail with error information | `Result<T, E>` |
| Converting Option to Result | `.ok_or(error)` or `.ok_or_else(|| error)` |
| Converting Result to Option | `.ok()` (discards error) |

## Combinator Patterns

### Result Combinators

| Combinator | Purpose | Example |
|------------|---------|---------|
| `map(f)` | Transform Ok value | `result.map(|v| v * 2)` |
| `map_err(f)` | Transform Err value | `result.map_err(|e| MyError::from(e))` |
| `and_then(f)` | Chain fallible operations | `result.and_then(|v| parse(v))` |
| `or_else(f)` | Recover from error | `result.or_else(|_| fallback())` |
| `unwrap_or(default)` | Default on error | `result.unwrap_or(0)` |
| `unwrap_or_else(f)` | Compute default on error | `result.unwrap_or_else(|e| handle(e))` |
| `context("msg")` | Add context (anyhow) | `result.context("loading config")?` |

### Option Combinators

| Combinator | Purpose | Example |
|------------|---------|---------|
| `map(f)` | Transform Some value | `opt.map(|v| v.to_string())` |
| `and_then(f)` | Chain optional operations | `opt.and_then(|v| v.checked_add(1))` |
| `or(other)` | Fallback Option | `primary.or(secondary)` |
| `filter(pred)` | Keep if predicate holds | `opt.filter(|v| v > &0)` |
| `unwrap_or_default()` | Default trait value | `opt.unwrap_or_default()` |
| `flatten()` | Unwrap nested Option | `Some(Some(42)).flatten()` -> `Some(42)` |

### Chaining Pattern

```rust
fn find_user_email(db: &Database, id: u64) -> Option<String> {
    db.find_user(id)             // Option<User>
        .filter(|u| u.active)    // Option<User> (only active)
        .and_then(|u| u.email)   // Option<String>
}
```

## thiserror -- Library Error Types

Use `thiserror` in library crates to define typed error enums with minimal boilerplate:

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum DataError {
    #[error("record not found: {id}")]
    NotFound { id: u64 },

    #[error("validation failed: {0}")]
    Validation(String),

    #[error("database error")]
    Database(#[from] sqlx::Error),

    #[error("serialization error")]
    Serialization(#[from] serde_json::Error),

    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
}
```

### thiserror Key Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `#[error("...")]` | Display message (supports format args) | `#[error("not found: {id}")]` |
| `#[from]` | Auto-implement `From` for conversion | `Database(#[from] sqlx::Error)` |
| `#[source]` | Mark source error without From impl | `#[source] inner: io::Error` |
| `#[backtrace]` | Capture backtrace | `backtrace: std::backtrace::Backtrace` |

### Error Enum Design Guidelines

1. One variant per failure category, not per callsite
2. Include enough context to debug without the stack trace
3. Use `#[from]` for direct 1:1 mappings between error types
4. Use manual `From` impls when conversion needs context
5. Keep error types `Send + Sync + 'static` for async compatibility

## anyhow -- Application Error Handling

Use `anyhow` in application binaries for ergonomic error propagation:

```rust
use anyhow::{Context, Result};

fn main() -> Result<()> {
    let config = load_config("app.toml")
        .context("failed to load application configuration")?;

    let db = connect_db(&config.database_url)
        .context("failed to connect to database")?;

    run_server(db).context("server crashed")?;
    Ok(())
}
```

### anyhow Key Features

| Feature | Usage |
|---------|-------|
| `anyhow::Result<T>` | Alias for `Result<T, anyhow::Error>` |
| `.context("msg")` | Wrap error with string context |
| `.with_context(|| format!(...))` | Lazy context for expensive formatting |
| `anyhow!("msg")` | Create ad-hoc error |
| `bail!("msg")` | Return early with error |
| `ensure!(cond, "msg")` | Assert with error return |
| `downcast_ref::<T>()` | Recover original typed error |

### Library vs Application Decision

| Context | Crate | Rationale |
|---------|-------|-----------|
| Library crate (published) | `thiserror` | Callers need typed errors to match on and handle specifically |
| Application binary | `anyhow` | Applications log errors; they rarely match on specific types |
| Internal module in large app | Either | Use thiserror if other modules match on the errors |
| Prototype / script | `anyhow` | Speed of development, add types later |

## Custom Error Types (Without Macros)

For full control, implement the error traits manually:

```rust
use std::fmt;

#[derive(Debug)]
pub enum AppError {
    Config(String),
    Database(sqlx::Error),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Config(msg) => write!(f, "configuration error: {msg}"),
            Self::Database(e) => write!(f, "database error: {e}"),
        }
    }
}

impl std::error::Error for AppError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Database(e) => Some(e),
            _ => None,
        }
    }
}

impl From<sqlx::Error> for AppError {
    fn from(e: sqlx::Error) -> Self {
        Self::Database(e)
    }
}
```

This is what `thiserror` generates. Write manually only when the macro's capabilities are insufficient.

## Error Context Patterns

### Adding Context at Call Sites

```rust
// Without context -- opaque error
let file = File::open(path)?;

// With context -- debuggable error
let file = File::open(path)
    .with_context(|| format!("failed to open config at {}", path.display()))?;
```

### Error Chain Walking

```rust
fn print_error_chain(err: &dyn std::error::Error) {
    eprintln!("Error: {err}");
    let mut source = err.source();
    while let Some(cause) = source {
        eprintln!("  Caused by: {cause}");
        source = cause.source();
    }
}
```

## Panic vs Result

| Use `Result` | Use `panic!` |
|-------------|-------------|
| File not found | Index out of bounds (programming bug) |
| Network timeout | Unrecoverable invariant violation |
| Invalid user input | Failed assertion in tests |
| Parse failure | Uninitialized state that should be impossible |
| Permission denied | Compiler plugin / proc macro errors |

Set `panic = "abort"` in release profiles to reduce binary size when panics should never be caught.

## Error Handling Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `.unwrap()` in production | Panics on error | Use `?`, `.unwrap_or()`, or match |
| `Box<dyn Error>` everywhere | Loses type information | Use thiserror enum |
| Ignoring errors with `let _ = ...` | Silent failures | Handle or log explicitly |
| String errors (`Err("failed".into())`) | No structured handling | Define typed error variants |
| Matching on Display output | Fragile, breaks on message changes | Match on error variants |
| Wrapping every error in new context | Noise in error chain | Add context only at boundaries |
