# Design Patterns

Sources: rust-unofficial/patterns (Rust Design Patterns book), Gjengset (Rust for Rustaceans), Blandy/Orendorff/Tindall (Programming Rust 2nd ed.), Rust API Guidelines

Covers: newtype, typestate, builder, From/Into conversions, enum dispatch, strategy via closures, RAII guards, and Rust-specific pattern adaptations.

## Newtype Pattern

Wrap a primitive or foreign type to add semantic meaning, enforce invariants, or work around the orphan rule:

```rust
struct EmailAddress(String);

impl EmailAddress {
    pub fn new(raw: &str) -> Result<Self, ValidationError> {
        if raw.contains('@') && raw.contains('.') {
            Ok(Self(raw.to_lowercase()))
        } else {
            Err(ValidationError::InvalidEmail)
        }
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}
```

### Newtype Benefits

| Benefit | Example |
|---------|---------|
| Type safety | `UserId(u64)` vs `OrderId(u64)` -- prevents mixing IDs |
| Validation at construction | `Port::new(n)` validates 1-65535 |
| Orphan rule workaround | Wrap `Vec<T>` to implement `Display` |
| Encapsulation | Hide internal representation |
| Unit conversion safety | `Meters(f64)` vs `Feet(f64)` |

### Making Newtypes Ergonomic

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct UserId(u64);

impl From<u64> for UserId {
    fn from(id: u64) -> Self { Self(id) }
}

impl std::fmt::Display for UserId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "user:{}", self.0)
    }
}
```

Implement `Deref` only when the newtype genuinely acts as a smart pointer to the inner type. Overusing `Deref` erodes the type safety that newtypes provide.

## Typestate Pattern

Encode valid state transitions in the type system so invalid transitions cannot compile:

```rust
// State markers -- zero-sized types (no runtime cost)
struct Draft;
struct Published;

struct Article<State> {
    title: String,
    body: String,
    _state: std::marker::PhantomData<State>,
}

impl Article<Draft> {
    fn new(title: String) -> Self {
        Self { title, body: String::new(), _state: std::marker::PhantomData }
    }

    fn set_body(mut self, body: String) -> Self {
        self.body = body;
        self
    }

    fn publish(self) -> Article<Published> {
        Article {
            title: self.title,
            body: self.body,
            _state: std::marker::PhantomData,
        }
    }
}

impl Article<Published> {
    fn url(&self) -> String {
        format!("/articles/{}", self.title.to_lowercase().replace(' ', "-"))
    }
    // Cannot call set_body() on Published -- method does not exist
}
```

### When to Use Typestate

| Signal | Use Typestate |
|--------|-------------|
| Protocol with ordered steps | Connection: Disconnected -> Connected -> Authenticated |
| Resource lifecycle | File: Open -> Reading/Writing -> Closed |
| Build process with required fields | Builder that guarantees required fields are set |
| State machine with invalid transitions | Prevent calling methods in wrong order |

Avoid typestate when: the number of states is large (>5), states change dynamically at runtime, or transitions depend on runtime data.

## Builder Pattern

Construct complex objects step by step. In Rust, two approaches:

### Option-Based Builder

```rust
#[derive(Default)]
struct ServerBuilder {
    host: Option<String>,
    port: Option<u16>,
    max_connections: Option<usize>,
    tls: bool,
}

impl ServerBuilder {
    fn new() -> Self { Self::default() }

    fn host(mut self, host: impl Into<String>) -> Self {
        self.host = Some(host.into());
        self
    }

    fn port(mut self, port: u16) -> Self {
        self.port = Some(port);
        self
    }

    fn max_connections(mut self, n: usize) -> Self {
        self.max_connections = Some(n);
        self
    }

    fn tls(mut self, enabled: bool) -> Self {
        self.tls = enabled;
        self
    }

    fn build(self) -> Result<Server, BuildError> {
        Ok(Server {
            host: self.host.ok_or(BuildError::MissingField("host"))?,
            port: self.port.unwrap_or(8080),
            max_connections: self.max_connections.unwrap_or(100),
            tls: self.tls,
        })
    }
}

let server = ServerBuilder::new()
    .host("0.0.0.0")
    .port(3000)
    .tls(true)
    .build()?;
```

### Typestate Builder

Combine builder with typestate to enforce required fields at compile time. Use when missing a required field should be a compile error rather than a runtime error. See typestate pattern above for the technique.

### Builder via derive Macros

The `derive_builder` and `typed-builder` crates generate builders automatically:

```rust
use typed_builder::TypedBuilder;

#[derive(TypedBuilder)]
struct Config {
    host: String,
    #[builder(default = 8080)]
    port: u16,
    #[builder(default)]
    debug: bool,
}

let cfg = Config::builder()
    .host("localhost".into())
    .build();  // port = 8080, debug = false
```

## Enum Dispatch

Replace trait objects with enums for known, finite sets of types:

```rust
enum Shape {
    Circle(Circle),
    Rectangle(Rectangle),
    Triangle(Triangle),
}

impl Shape {
    fn area(&self) -> f64 {
        match self {
            Shape::Circle(c) => std::f64::consts::PI * c.radius * c.radius,
            Shape::Rectangle(r) => r.width * r.height,
            Shape::Triangle(t) => 0.5 * t.base * t.height,
        }
    }
}
```

### Enum Dispatch vs Trait Object

| Factor | Enum Dispatch | Trait Object |
|--------|--------------|-------------|
| Known variants | Yes -- closed set | No -- open set |
| Performance | Stack-allocated, no vtable | Heap-allocated, vtable indirection |
| Extensibility | Add variant = modify enum | Add impl = no existing code changes |
| Pattern matching | Full exhaustive matching | Not available |

Use enum dispatch when: all variants are known at compile time and the set rarely changes. Use trait objects when: new types will be added by downstream code.

## Strategy Pattern via Closures

Replace strategy objects with closures:

```rust
struct Processor {
    transform: Box<dyn Fn(String) -> String>,
}

impl Processor {
    fn new(transform: impl Fn(String) -> String + 'static) -> Self {
        Self { transform: Box::new(transform) }
    }

    fn process(&self, input: String) -> String {
        (self.transform)(input)
    }
}

let upper = Processor::new(|s| s.to_uppercase());
let trimmed = Processor::new(|s| s.trim().to_string());
```

For simple strategies, closures are lighter than trait objects. For complex strategies with state, define a trait.

## RAII Guard Pattern

Tie resource cleanup to scope exit:

```rust
struct Timer {
    label: String,
    start: std::time::Instant,
}

impl Timer {
    fn new(label: &str) -> Self {
        Self {
            label: label.to_string(),
            start: std::time::Instant::now(),
        }
    }
}

impl Drop for Timer {
    fn drop(&mut self) {
        let elapsed = self.start.elapsed();
        println!("{}: {elapsed:?}", self.label);
    }
}

fn process_data() {
    let _timer = Timer::new("process_data");  // times the entire function
    // ... work happens here ...
}  // Timer::drop prints elapsed time
```

Standard library examples: `MutexGuard` (releases lock), `File` (closes handle), `TempDir` (deletes directory).

## From/Into Conversion Pattern

Implement `From` to define type conversions. `Into` is provided automatically:

```rust
#[derive(Debug)]
struct Rgb { r: u8, g: u8, b: u8 }

impl From<(u8, u8, u8)> for Rgb {
    fn from((r, g, b): (u8, u8, u8)) -> Self {
        Self { r, g, b }
    }
}

impl From<u32> for Rgb {
    fn from(hex: u32) -> Self {
        Self {
            r: ((hex >> 16) & 0xFF) as u8,
            g: ((hex >> 8) & 0xFF) as u8,
            b: (hex & 0xFF) as u8,
        }
    }
}

let color: Rgb = (255, 128, 0).into();
let color2: Rgb = 0xFF8000.into();
```

Use `TryFrom` when conversion can fail:

```rust
impl TryFrom<&str> for Rgb {
    type Error = ParseColorError;

    fn try_from(s: &str) -> Result<Self, Self::Error> {
        let hex = u32::from_str_radix(s.trim_start_matches('#'), 16)
            .map_err(|_| ParseColorError::InvalidHex)?;
        Ok(Self::from(hex))
    }
}
```

## Extension Trait Pattern

Add methods to foreign types without modifying them:

```rust
pub trait StringExt {
    fn truncate_with_ellipsis(&self, max_len: usize) -> String;
}

impl StringExt for str {
    fn truncate_with_ellipsis(&self, max_len: usize) -> String {
        if self.len() <= max_len {
            self.to_string()
        } else {
            format!("{}...", &self[..max_len.saturating_sub(3)])
        }
    }
}

// Usage: "hello world".truncate_with_ellipsis(8) -> "hello..."
```

Name extension traits `{Type}Ext` by convention. Import the trait to use the methods.

## Anti-Patterns

| Anti-Pattern | Problem | Alternative |
|-------------|---------|-------------|
| `Deref` for inheritance | Surprising implicit coercions | Explicit delegation or composition |
| God enum with 50 variants | Unmanageable match arms | Trait objects or module separation |
| Boolean parameters | `process(true, false, true)` unreadable | Enums or builder pattern |
| Stringly typed APIs | No compile-time validation | Newtypes or enums |
| Clone everything | Hidden performance costs | Analyze ownership, use references |
| Unwrap in library code | Panics in caller's code | Return Result |
