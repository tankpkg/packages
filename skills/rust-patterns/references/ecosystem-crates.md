# Ecosystem and Crate Recommendations

Sources: Tokio documentation (tokio.rs), Axum documentation, SQLx documentation, Clap documentation, Rust API Guidelines, blessed.rs, lib.rs, 2025-2026 ecosystem analysis

Covers: axum web framework, sqlx database, clap CLI, tracing observability, reqwest HTTP client, indicatif progress bars, Cargo workspaces, module organization, and feature flags.

## Axum Web Framework

Axum is the standard Rust web framework, built by the Tokio team. It uses type-safe extractors and integrates with the Tower middleware ecosystem.

### Minimal Server

```rust
use axum::{routing::get, Router, Json};
use serde::Serialize;

#[derive(Serialize)]
struct Health { status: String }

async fn health() -> Json<Health> {
    Json(Health { status: "ok".into() })
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/health", get(health));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
```

### Extractors

```rust
use axum::extract::{Path, Query, State, Json};

async fn get_user(
    State(db): State<Database>,
    Path(id): Path<u64>,
) -> Result<Json<User>, AppError> {
    let user = db.find_user(id).await?;
    Ok(Json(user))
}

#[derive(Deserialize)]
struct Pagination { page: Option<u32>, per_page: Option<u32> }

async fn list_users(
    State(db): State<Database>,
    Query(params): Query<Pagination>,
) -> Result<Json<Vec<User>>, AppError> {
    let users = db.list_users(params.page.unwrap_or(1), params.per_page.unwrap_or(25)).await?;
    Ok(Json(users))
}
```

### Shared State

```rust
#[derive(Clone)]
struct AppState {
    db: sqlx::PgPool,
    config: Arc<Config>,
}

let state = AppState {
    db: PgPool::connect(&database_url).await?,
    config: Arc::new(config),
};

let app = Router::new()
    .route("/users", get(list_users).post(create_user))
    .with_state(state);
```

### Error Handling in Axum

Implement `IntoResponse` for custom error types:

```rust
use axum::response::{IntoResponse, Response};
use axum::http::StatusCode;

enum AppError {
    NotFound(String),
    Internal(anyhow::Error),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        match self {
            Self::NotFound(msg) => (StatusCode::NOT_FOUND, msg).into_response(),
            Self::Internal(err) => {
                tracing::error!("Internal error: {err:?}");
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal error").into_response()
            }
        }
    }
}

impl<E: Into<anyhow::Error>> From<E> for AppError {
    fn from(err: E) -> Self { Self::Internal(err.into()) }
}
```

### Tower Middleware

```rust
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use tower_http::compression::CompressionLayer;

let app = Router::new()
    .route("/api/users", get(list_users))
    .layer(TraceLayer::new_for_http())
    .layer(CompressionLayer::new())
    .layer(CorsLayer::permissive());
```

## SQLx Database Toolkit

Compile-time checked SQL queries with async support:

```rust
// Compile-time verified query
let users = sqlx::query_as!(
    User,
    "SELECT id, name, email FROM users WHERE active = $1 LIMIT $2",
    true,
    limit as i64
)
.fetch_all(&pool)
.await?;
```

### Connection Pool

```rust
use sqlx::postgres::PgPoolOptions;

let pool = PgPoolOptions::new()
    .max_connections(20)
    .acquire_timeout(std::time::Duration::from_secs(3))
    .connect(&database_url)
    .await?;
```

### Transactions

```rust
let mut tx = pool.begin().await?;

sqlx::query!("INSERT INTO users (name) VALUES ($1)", name)
    .execute(&mut *tx)
    .await?;

sqlx::query!("INSERT INTO audit_log (action) VALUES ($1)", "user_created")
    .execute(&mut *tx)
    .await?;

tx.commit().await?;
// On error, tx is dropped and rolled back automatically
```

## Clap CLI Parsing

Derive-based argument parsing:

```rust
use clap::Parser;

#[derive(Parser)]
#[command(name = "myapp", version, about = "A sample CLI tool")]
struct Cli {
    /// Input file path
    #[arg(short, long)]
    input: String,

    /// Output file path
    #[arg(short, long, default_value = "output.txt")]
    output: String,

    /// Verbosity level (-v, -vv, -vvv)
    #[arg(short, long, action = clap::ArgAction::Count)]
    verbose: u8,

    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(clap::Subcommand)]
enum Commands {
    /// Process input data
    Process {
        #[arg(long)]
        dry_run: bool,
    },
    /// Validate configuration
    Validate,
}

fn main() {
    let cli = Cli::parse();
    match cli.command {
        Some(Commands::Process { dry_run }) => { /* ... */ }
        Some(Commands::Validate) => { /* ... */ }
        None => { /* default behavior */ }
    }
}
```

## Tracing Observability

Structured logging for async Rust:

```rust
use tracing::{info, warn, error, instrument, Level};
use tracing_subscriber::{fmt, EnvFilter};

fn init_tracing() {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())  // RUST_LOG=info,my_crate=debug
        .with_target(true)
        .json()  // structured JSON output for production
        .init();
}

#[instrument(skip(db))]
async fn create_user(db: &Database, name: &str) -> Result<User, AppError> {
    info!(user_name = name, "Creating user");
    let user = db.insert_user(name).await.map_err(|e| {
        error!(error = ?e, "Failed to create user");
        e
    })?;
    info!(user_id = user.id, "User created successfully");
    Ok(user)
}
```

### Span Hierarchy

```rust
use tracing::info_span;

async fn handle_request(req: Request) -> Response {
    let span = info_span!("request", method = %req.method(), path = %req.uri());
    async {
        let user = authenticate(&req).await?;
        let _guard = info_span!("handler", user_id = user.id).entered();
        process(req).await
    }
    .instrument(span)
    .await
}
```

## Reqwest HTTP Client

```rust
let client = reqwest::Client::builder()
    .timeout(std::time::Duration::from_secs(10))
    .user_agent("my-app/1.0")
    .build()?;

let response = client.get("https://api.example.com/data")
    .bearer_auth(&token)
    .query(&[("page", "1")])
    .send()
    .await?
    .error_for_status()?  // convert 4xx/5xx to errors
    .json::<ApiResponse>()
    .await?;
```

## Cargo Workspaces

Organize multi-crate projects:

```toml
# Cargo.toml (workspace root)
[workspace]
members = ["crates/*"]
resolver = "2"

[workspace.dependencies]
serde = { version = "1", features = ["derive"] }
tokio = { version = "1", features = ["full"] }
anyhow = "1"
```

```toml
# crates/api/Cargo.toml
[package]
name = "my-api"

[dependencies]
serde = { workspace = true }
tokio = { workspace = true }
my-core = { path = "../core" }
```

### Workspace Organization

```
project/
├── Cargo.toml           # workspace definition
├── crates/
│   ├── core/            # shared types, traits, domain logic
│   ├── api/             # web server
│   ├── cli/             # command-line tool
│   └── worker/          # background job processor
└── tests/               # workspace-level integration tests
```

## Module Organization

```rust
// src/lib.rs -- re-export public API
pub mod models;
pub mod services;
pub mod errors;

pub use errors::AppError;
pub use models::User;
```

### Visibility Guidelines

| Visibility | Use |
|-----------|-----|
| `pub` | Part of the crate's public API |
| `pub(crate)` | Shared within the crate, not public |
| `pub(super)` | Shared with parent module only |
| (default private) | Internal to the module |

## Feature Flags

```toml
[features]
default = ["json"]
json = ["dep:serde_json"]
toml = ["dep:toml"]
full = ["json", "toml"]
```

```rust
#[cfg(feature = "json")]
pub fn to_json<T: Serialize>(value: &T) -> Result<String, serde_json::Error> {
    serde_json::to_string(value)
}
```

Use features for optional functionality. Keep `default` minimal. Never use features to gate breaking API changes.

## Crate Recommendations by Category

| Category | Primary | Alternative |
|----------|---------|------------|
| Async runtime | `tokio` | `async-std` (smaller, simpler) |
| Web framework | `axum` | `actix-web` (actor model) |
| HTTP client | `reqwest` | `hyper` (lower-level) |
| Database | `sqlx` | `diesel` (ORM), `sea-orm` (ActiveRecord) |
| Serialization | `serde` | --- (effectively required) |
| CLI | `clap` (derive) | `argh` (minimal) |
| Logging/tracing | `tracing` | `log` + `env_logger` (simpler) |
| Error (library) | `thiserror` | manual impl |
| Error (application) | `anyhow` | `eyre` (custom reports) |
| Testing | `proptest` | `quickcheck` |
| Mocking | `mockall` | `mockito` (HTTP) |
| Date/time | `chrono` | `time` (lighter) |
| UUID | `uuid` | --- |
| Random | `rand` | --- |
| Regex | `regex` | --- |
| Progress bars | `indicatif` | --- |
| Temp files | `tempfile` | --- |
| Config files | `config` | `figment` |
