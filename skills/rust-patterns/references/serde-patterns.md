# Serde Patterns

Sources: Serde documentation (serde.rs), Gjengset (Rust for Rustaceans), Klabnik/Nichols (The Rust Programming Language 3rd ed.), serde_with crate documentation

Covers: derive attributes, field-level configuration, enum representations, custom serialization, flattening, skip/default patterns, and integration with JSON, TOML, and other formats.

## Basics

Add serde with derive support:

```toml
[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
toml = "0.8"
```

Derive `Serialize` and `Deserialize` on structs and enums:

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct User {
    name: String,
    email: String,
    age: u32,
}

let json = serde_json::to_string(&user)?;
let user: User = serde_json::from_str(&json)?;
```

## Container Attributes

Apply to the struct or enum:

| Attribute | Effect | Example |
|-----------|--------|---------|
| `#[serde(rename_all = "...")]` | Rename all fields | `camelCase`, `snake_case`, `SCREAMING_SNAKE_CASE`, `kebab-case`, `PascalCase` |
| `#[serde(deny_unknown_fields)]` | Error on extra fields | Strict deserialization |
| `#[serde(default)]` | Use `Default::default()` for missing fields | Lenient deserialization |
| `#[serde(transparent)]` | Serialize/deserialize as the inner type | Newtype wrappers |
| `#[serde(bound = "...")]` | Custom trait bounds | Generic types |
| `#[serde(crate = "...")]` | Alternate serde path | Re-exported serde |

### rename_all for API Compatibility

```rust
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ApiResponse {
    user_name: String,       // serializes as "userName"
    created_at: String,      // serializes as "createdAt"
    is_active: bool,         // serializes as "isActive"
}
```

## Field Attributes

Apply to individual fields:

| Attribute | Effect |
|-----------|--------|
| `#[serde(rename = "name")]` | Rename this field |
| `#[serde(alias = "name")]` | Accept alternate name during deserialization |
| `#[serde(default)]` | Use Default if missing |
| `#[serde(default = "path")]` | Use custom function if missing |
| `#[serde(skip)]` | Skip this field entirely |
| `#[serde(skip_serializing)]` | Include in deserialize, skip in serialize |
| `#[serde(skip_serializing_if = "...")]` | Conditionally skip |
| `#[serde(flatten)]` | Inline fields from nested struct |
| `#[serde(with = "module")]` | Custom serialize/deserialize module |
| `#[serde(deserialize_with = "fn")]` | Custom deserialize function |
| `#[serde(serialize_with = "fn")]` | Custom serialize function |

### skip_serializing_if Patterns

```rust
#[derive(Serialize, Deserialize)]
struct Config {
    name: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    description: Option<String>,      // omitted if None

    #[serde(skip_serializing_if = "Vec::is_empty")]
    tags: Vec<String>,                // omitted if empty

    #[serde(skip_serializing_if = "is_default")]
    retries: u32,                     // omitted if 0
}

fn is_default<T: Default + PartialEq>(value: &T) -> bool {
    *value == T::default()
}
```

### default Patterns

```rust
#[derive(Serialize, Deserialize)]
struct ServerConfig {
    host: String,

    #[serde(default = "default_port")]
    port: u16,

    #[serde(default)]
    debug: bool,            // defaults to false

    #[serde(default)]
    tags: Vec<String>,      // defaults to empty vec
}

fn default_port() -> u16 { 8080 }
```

## Flatten for Composition

Inline fields from one struct into another:

```rust
#[derive(Serialize, Deserialize)]
struct Pagination {
    page: u32,
    per_page: u32,
}

#[derive(Serialize, Deserialize)]
struct UserQuery {
    name_filter: Option<String>,

    #[serde(flatten)]
    pagination: Pagination,
}

// JSON: { "name_filter": "alice", "page": 1, "per_page": 20 }
// Fields from Pagination appear at the top level
```

### Catch-All with Flatten

Capture unknown fields into a map:

```rust
use std::collections::HashMap;
use serde_json::Value;

#[derive(Serialize, Deserialize)]
struct Event {
    event_type: String,
    timestamp: String,

    #[serde(flatten)]
    extra: HashMap<String, Value>,  // captures all other fields
}
```

## Enum Representations

Serde supports four enum representations:

### Externally Tagged (Default)

```rust
#[derive(Serialize, Deserialize)]
enum Message {
    Text(String),
    Image { url: String, width: u32 },
}
// JSON: {"Text": "hello"} or {"Image": {"url": "...", "width": 100}}
```

### Internally Tagged

```rust
#[derive(Serialize, Deserialize)]
#[serde(tag = "type")]
enum Event {
    Click { x: u32, y: u32 },
    Scroll { delta: f64 },
}
// JSON: {"type": "Click", "x": 10, "y": 20}
```

Most common for APIs. The tag field is a sibling of other fields.

### Adjacently Tagged

```rust
#[derive(Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
enum ApiResponse {
    Success(UserData),
    Error(ErrorInfo),
}
// JSON: {"type": "Success", "data": {"name": "alice"}}
```

### Untagged

```rust
#[derive(Serialize, Deserialize)]
#[serde(untagged)]
enum Value {
    Integer(i64),
    Float(f64),
    Text(String),
}
// JSON: 42 or 3.14 or "hello" (no tag, tries each variant in order)
```

Untagged tries variants in declaration order. Place more specific variants first.

### Enum Representation Selection

| Representation | When to Use |
|----------------|-------------|
| Externally tagged | Internal use, Rust-to-Rust communication |
| Internally tagged | REST APIs, event systems, polymorphic types |
| Adjacently tagged | Typed wrapper + payload pattern |
| Untagged | Parsing multiple formats, loosely typed inputs |

## Custom Serialization

### Module-Level Custom with `#[serde(with)]`

```rust
mod date_format {
    use chrono::NaiveDate;
    use serde::{self, Deserialize, Deserializer, Serializer};

    const FORMAT: &str = "%Y-%m-%d";

    pub fn serialize<S>(date: &NaiveDate, serializer: S) -> Result<S::Ok, S::Error>
    where S: Serializer {
        let s = date.format(FORMAT).to_string();
        serializer.serialize_str(&s)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<NaiveDate, D::Error>
    where D: Deserializer<'de> {
        let s = String::deserialize(deserializer)?;
        NaiveDate::parse_from_str(&s, FORMAT).map_err(serde::de::Error::custom)
    }
}

#[derive(Serialize, Deserialize)]
struct Event {
    name: String,
    #[serde(with = "date_format")]
    date: NaiveDate,
}
```

### serde_with Crate

Reduces boilerplate for common custom serialization patterns:

```rust
use serde_with::{serde_as, DisplayFromStr, DurationSeconds};

#[serde_as]
#[derive(Serialize, Deserialize)]
struct Config {
    #[serde_as(as = "DisplayFromStr")]
    port: u16,                          // serialize as string "8080"

    #[serde_as(as = "DurationSeconds<u64>")]
    timeout: std::time::Duration,       // serialize as seconds number

    #[serde_as(as = "Vec<DisplayFromStr>")]
    ports: Vec<u16>,                    // ["8080", "8081"]
}
```

## Format-Specific Patterns

### JSON

```rust
// Pretty-print
let json = serde_json::to_string_pretty(&value)?;

// From reader
let value: Config = serde_json::from_reader(file)?;

// Untyped parsing
let v: serde_json::Value = serde_json::from_str(raw)?;
let name = v["users"][0]["name"].as_str().unwrap_or("unknown");
```

### TOML

```rust
let config: Config = toml::from_str(&content)?;
let toml_string = toml::to_string_pretty(&config)?;
```

TOML does not support all serde features (no adjacently tagged enums, limited nesting). Test TOML round-trips explicitly.

### Multiple Format Support

Design types to work across formats by avoiding format-specific features:

```rust
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
struct Config {
    // Works in JSON, TOML, YAML
    database_url: String,
    port: u16,
    features: Vec<String>,
}
```

## Common Patterns

### Optional Fields with Defaults

```rust
#[derive(Serialize, Deserialize)]
struct Pagination {
    #[serde(default = "default_page")]
    page: u32,
    #[serde(default = "default_per_page")]
    per_page: u32,
}

fn default_page() -> u32 { 1 }
fn default_per_page() -> u32 { 25 }
```

### Versioned Configuration

```rust
#[derive(Serialize, Deserialize)]
#[serde(tag = "version")]
enum Config {
    #[serde(rename = "1")]
    V1(ConfigV1),
    #[serde(rename = "2")]
    V2(ConfigV2),
}
```

### String-or-Struct Pattern

Accept either a simple string or a full struct:

```rust
#[derive(Serialize, Deserialize)]
#[serde(untagged)]
enum DatabaseConfig {
    Url(String),                             // "postgres://..."
    Full { host: String, port: u16, db: String }, // full config
}
```

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `#[serde(deny_unknown_fields)]` on public API types | Breaks forward compatibility | Silently ignore unknown fields |
| Untagged enums with overlapping types | Ambiguous deserialization | Use tagged enums |
| Deriving Serialize on types with secrets | Secrets end up in logs | Implement Display manually, skip secret fields |
| No `#[serde(default)]` on optional config | Missing fields = error | Add defaults for optional fields |
