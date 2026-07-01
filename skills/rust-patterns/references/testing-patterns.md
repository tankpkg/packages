# Testing Patterns

Sources: Klabnik/Nichols (The Rust Programming Language 3rd ed.), Gjengset (Rust for Rustaceans), Rust Reference, proptest documentation, mockall documentation

Covers: unit tests, integration tests, test organization, fixtures, property-based testing, mocking, async test patterns, and test utilities.

## Test Organization

Rust has two categories of tests with distinct placement:

| Type | Location | Accesses Private Items | Compiled |
|------|----------|----------------------|----------|
| Unit tests | Same file, `#[cfg(test)]` module | Yes | Only during `cargo test` |
| Integration tests | `tests/` directory | No (public API only) | Only during `cargo test` |

### Unit Test Structure

```rust
// src/lib.rs or src/module.rs
pub fn add(a: i32, b: i32) -> i32 { a + b }

fn internal_helper(x: i32) -> i32 { x * 2 }

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
    }

    #[test]
    fn test_internal_helper() {
        // Can test private functions
        assert_eq!(internal_helper(3), 6);
    }

    #[test]
    #[should_panic(expected = "overflow")]
    fn test_overflow_panics() {
        add(i32::MAX, 1);
    }

    #[test]
    fn test_with_result() -> Result<(), Box<dyn std::error::Error>> {
        let result = parse_config("valid = true")?;
        assert_eq!(result.valid, true);
        Ok(())
    }
}
```

### Integration Test Structure

```
project/
├── src/
│   └── lib.rs
└── tests/
    ├── api_tests.rs         # each file is a separate test binary
    ├── db_tests.rs
    └── common/
        └── mod.rs           # shared helpers (not a test file)
```

```rust
// tests/api_tests.rs
use my_crate::ApiClient;

mod common;

#[test]
fn test_create_user() {
    let client = common::setup_test_client();
    let user = client.create_user("alice").unwrap();
    assert_eq!(user.name, "alice");
}
```

### Shared Test Helpers

Place shared code in `tests/common/mod.rs` (not `tests/common.rs`, which Cargo treats as a test file):

```rust
// tests/common/mod.rs
pub fn setup_test_db() -> TestDb {
    TestDb::new("test_db")
}

pub fn random_user() -> User {
    User {
        name: format!("user_{}", rand::random::<u32>()),
        email: format!("{}@test.com", rand::random::<u32>()),
    }
}
```

## Assertion Patterns

### Standard Assertions

| Macro | Purpose |
|-------|---------|
| `assert!(expr)` | Assert expression is true |
| `assert_eq!(left, right)` | Assert equality (shows both on failure) |
| `assert_ne!(left, right)` | Assert inequality |
| `assert!(expr, "message {}", val)` | Custom failure message |
| `debug_assert!(expr)` | Only in debug builds |

### Custom Assertion Helpers

```rust
#[cfg(test)]
fn assert_approx_eq(a: f64, b: f64, epsilon: f64) {
    assert!(
        (a - b).abs() < epsilon,
        "assertion failed: |{a} - {b}| = {} >= {epsilon}",
        (a - b).abs()
    );
}

#[test]
fn test_calculation() {
    assert_approx_eq(calculate_pi(), 3.14159, 0.001);
}
```

### Testing Error Cases

```rust
#[test]
fn test_invalid_input_returns_error() {
    let result = parse_port("not_a_number");
    assert!(result.is_err());

    let err = result.unwrap_err();
    assert!(err.to_string().contains("invalid port"));
}

#[test]
fn test_specific_error_variant() {
    let result = fetch_user(0);
    assert!(matches!(result, Err(AppError::NotFound { .. })));
}
```

### The matches! Macro

```rust
let value = Some(42);
assert!(matches!(value, Some(x) if x > 0));

let result: Result<i32, String> = Err("oops".into());
assert!(matches!(result, Err(ref e) if e.contains("oops")));
```

## Test Configuration

### Running Specific Tests

```bash
cargo test                          # all tests
cargo test test_name                # tests matching name
cargo test --lib                    # unit tests only
cargo test --test api_tests         # specific integration test file
cargo test -- --ignored             # run ignored tests
cargo test -- --nocapture           # show println output
cargo test -- --test-threads=1      # serial execution
```

### Ignoring Tests

```rust
#[test]
#[ignore = "requires running database"]
fn test_database_integration() {
    // Only runs with: cargo test -- --ignored
}
```

### Conditional Compilation in Tests

```rust
#[cfg(test)]
mod tests {
    #[test]
    #[cfg(target_os = "linux")]
    fn test_linux_specific() { /* ... */ }

    #[test]
    #[cfg(feature = "advanced")]
    fn test_advanced_feature() { /* ... */ }
}
```

## Fixtures and Setup

### Setup/Teardown with Drop

```rust
struct TestFixture {
    db: TestDatabase,
    temp_dir: tempfile::TempDir,
}

impl TestFixture {
    fn new() -> Self {
        Self {
            db: TestDatabase::create(),
            temp_dir: tempfile::tempdir().unwrap(),
        }
    }
}

impl Drop for TestFixture {
    fn drop(&mut self) {
        self.db.cleanup();
        // temp_dir cleaned up automatically by TempDir's Drop
    }
}

#[test]
fn test_with_fixture() {
    let fixture = TestFixture::new();
    // ... test using fixture.db and fixture.temp_dir
}  // Drop runs cleanup automatically
```

### once_cell for Expensive Setup

```rust
use std::sync::OnceLock;

static TEST_CONFIG: OnceLock<Config> = OnceLock::new();

fn get_test_config() -> &'static Config {
    TEST_CONFIG.get_or_init(|| {
        Config::from_file("tests/fixtures/test_config.toml").unwrap()
    })
}
```

## Property-Based Testing with proptest

Generate random inputs and verify properties hold for all of them:

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_roundtrip_serialization(s in "\\PC{1,100}") {
        let serialized = serde_json::to_string(&s).unwrap();
        let deserialized: String = serde_json::from_str(&serialized).unwrap();
        assert_eq!(s, deserialized);
    }

    #[test]
    fn test_sort_is_idempotent(mut v in prop::collection::vec(any::<i32>(), 0..100)) {
        v.sort();
        let sorted = v.clone();
        v.sort();
        assert_eq!(v, sorted);
    }

    #[test]
    fn test_reverse_reverse_is_identity(v in prop::collection::vec(any::<i32>(), 0..50)) {
        let mut reversed = v.clone();
        reversed.reverse();
        reversed.reverse();
        assert_eq!(v, reversed);
    }
}
```

### Custom Strategies

```rust
fn valid_email() -> impl Strategy<Value = String> {
    ("[a-z]{3,10}", "[a-z]{2,5}").prop_map(|(user, domain)| {
        format!("{user}@{domain}.com")
    })
}

proptest! {
    #[test]
    fn test_email_parsing(email in valid_email()) {
        let parsed = Email::parse(&email);
        assert!(parsed.is_ok(), "Failed to parse: {email}");
    }
}
```

### When to Use Property Testing

| Signal | Use proptest |
|--------|-------------|
| Parsing / serialization roundtrips | Verify encode(decode(x)) == x |
| Mathematical properties | Commutativity, associativity, idempotency |
| Boundary conditions | Fuzzing with random edge cases |
| State machines | Verify invariants hold across operations |
| Data structure invariants | Sorted, balanced, size constraints |

## Mocking with mockall

```rust
use mockall::automock;

#[automock]
trait UserRepository {
    fn find_by_id(&self, id: u64) -> Option<User>;
    fn save(&self, user: &User) -> Result<(), DbError>;
}

#[test]
fn test_user_service() {
    let mut mock = MockUserRepository::new();
    mock.expect_find_by_id()
        .with(eq(42))
        .returning(|_| Some(User { id: 42, name: "alice".into() }));

    let service = UserService::new(Box::new(mock));
    let user = service.get_user(42).unwrap();
    assert_eq!(user.name, "alice");
}
```

### When to Mock

| Situation | Approach |
|-----------|----------|
| External service (HTTP, DB) | Mock the trait / interface boundary |
| Pure logic | Test directly, no mocking needed |
| File system | Use tempfile crate, mock only if slow |
| Time-dependent | Inject clock trait, mock in tests |

Prefer real implementations when practical. Mock only at boundaries you do not control.

## Async Test Patterns

```rust
#[tokio::test]
async fn test_async_operation() {
    let result = fetch_data("https://api.example.com/data").await;
    assert!(result.is_ok());
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn test_concurrent_operations() {
    let (a, b) = tokio::join!(task_a(), task_b());
    assert!(a.is_ok());
    assert!(b.is_ok());
}
```

### Testing with Timeouts

```rust
#[tokio::test]
async fn test_with_timeout() {
    let result = tokio::time::timeout(
        std::time::Duration::from_secs(5),
        slow_operation(),
    ).await;
    assert!(result.is_ok(), "Operation timed out");
}
```

## Documentation Tests

Code blocks in doc comments are compiled and run as tests:

```rust
/// Adds two numbers.
///
/// # Examples
///
/// ```
/// use my_crate::add;
/// assert_eq!(add(2, 3), 5);
/// ```
///
/// # Panics
///
/// Panics on integer overflow in debug mode.
pub fn add(a: i32, b: i32) -> i32 { a + b }
```

Run doc tests: `cargo test --doc`

### Hiding Setup in Doc Tests

```rust
/// ```
/// # use my_crate::Config;
/// # fn main() -> Result<(), Box<dyn std::error::Error>> {
/// let config = Config::from_str("port = 8080")?;
/// assert_eq!(config.port, 8080);
/// # Ok(())
/// # }
/// ```
```

Lines starting with `#` are compiled but not shown in documentation.

## Test Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Testing implementation details | Brittle, breaks on refactor | Test behavior and outputs |
| One giant test | Hard to diagnose failures | One assertion per test, descriptive names |
| No error case tests | Bugs in error paths | Test both Ok and Err paths |
| Sleeping in tests | Slow, flaky | Use channels, condvars, or mocked clocks |
| Shared mutable test state | Tests interfere with each other | Each test creates its own state |
| Ignoring test output quality | Poor failure messages | Use assert_eq! with descriptive messages |
