---
name: "@tank/rust-patterns"
description: |
  Idiomatic Rust patterns for production applications. Covers ownership,
  borrowing, and lifetimes (mental models, borrow checker fixes), error
  handling (Result, ?, thiserror, anyhow, custom errors), traits and
  generics (trait objects, associated types, blanket impls), async/await
  with Tokio (spawn, channels, select!, timeouts), design patterns
  (newtype, typestate, builder), serde serialization (derive, custom,
  flatten, adjacently tagged enums), testing (unit, integration, proptest,
  mocking), CLI tools (clap, tracing, indicatif), web services (axum,
  tower, sqlx), performance (zero-copy, Cow, iterators, SmallVec), Cargo
  workspaces, module organization, and common crate recommendations.

  Synthesizes Klabnik/Nichols (The Rust Programming Language 3rd ed.),
  Gjengset (Rust for Rustaceans), Blandy/Orendorff/Tindall (Programming
  Rust 2nd ed.), Rust API Guidelines, rust-unofficial/patterns, Tokio
  documentation, and Serde documentation.

  Trigger phrases: "rust", "rust ownership", "rust borrowing", "rust lifetimes",
  "rust error handling", "rust async", "rust tokio", "rust traits",
  "rust generics", "rust serde", "rust testing", "rust cli", "rust clap",
  "rust axum", "rust patterns", "rust best practices", "rust workspace",
  "borrow checker", "rust Result", "rust design patterns", "rust performance",
  "rust macros", "rust newtype", "rust typestate", "rust builder pattern",
  "rust tracing", "rust sqlx", "idiomatic rust"
---

# Rust Patterns

## Core Philosophy

1. **Ownership is the architecture** -- Every design decision flows from ownership. Decide who owns data first, then choose the borrowing strategy. Fighting the borrow checker means the ownership model is wrong.
2. **Make illegal states unrepresentable** -- Use enums, newtypes, and typestate patterns so invalid program states cannot compile. Move runtime checks to compile-time guarantees wherever possible.
3. **Errors are values, not exceptions** -- Return `Result<T, E>` for recoverable errors. Reserve `panic!` for programming bugs only. Libraries expose typed errors; applications use `anyhow` for ergonomic propagation.
4. **Zero-cost abstractions pay off** -- Prefer iterators over manual loops, generics over trait objects, stack allocation over heap. The compiler optimizes aggressively when given type information.
5. **Explicit over implicit** -- Rust rewards explicitness. Derive only what you need, annotate lifetimes when the compiler asks, prefer concrete types over dynamic dispatch unless polymorphism is required.

## Quick-Start: Common Problems

### "The borrow checker rejects my code"

| Error Pattern | Likely Fix |
|---------------|-----------|
| Cannot borrow as mutable, already borrowed | Split borrows into non-overlapping scopes or use `.clone()` |
| Does not live long enough | Move owned data instead of borrowing, or restructure ownership |
| Cannot move out of borrowed content | Use `.clone()`, `mem::take`, or redesign to avoid the move |
| Multiple mutable borrows | Use `RefCell` (single-thread) or `Mutex` (multi-thread) for interior mutability |
-> See `references/ownership-borrowing-lifetimes.md`

### "Which error handling approach?"

| Context | Use |
|---------|-----|
| Library crate | `thiserror` -- define typed error enum with `#[error]` and `#[from]` |
| Application binary | `anyhow::Result` -- ergonomic `?` propagation with context |
| Converting between error types | `impl From<SourceError> for MyError` or `#[from]` in thiserror |
| Adding context to errors | `anyhow::Context` trait -- `.context("failed to open config")` |
-> See `references/error-handling.md`

### "How do I structure async code?"

1. Use `#[tokio::main]` for the entry point with the multi-thread runtime
2. Spawn CPU-bound work with `spawn_blocking`, not `spawn`
3. Communicate between tasks via channels (`mpsc`, `oneshot`, `watch`)
4. Use `tokio::select!` for racing concurrent futures
-> See `references/async-tokio.md`

### "How do I serialize complex types?"

1. Derive `Serialize` / `Deserialize` for simple structs
2. Use `#[serde(rename_all = "camelCase")]` for API compatibility
3. Use `#[serde(tag = "type")]` for internally tagged enums
4. Implement custom serialization only when derive attributes are insufficient
-> See `references/serde-patterns.md`

## Decision Trees

### Smart Pointer Selection

| Need | Use |
|------|-----|
| Heap allocation, single owner | `Box<T>` |
| Shared ownership, single-thread | `Rc<T>` |
| Shared ownership, multi-thread | `Arc<T>` |
| Interior mutability, single-thread | `Cell<T>` (Copy) or `RefCell<T>` (non-Copy) |
| Interior mutability, multi-thread | `Mutex<T>` or `RwLock<T>` |
| Borrow or own conditionally | `Cow<'a, T>` |
| Self-referential / async pinning | `Pin<Box<T>>` |

### Trait Object vs Generic

| Signal | Use |
|--------|-----|
| Known set of types at compile time | Generic (`impl Trait` or `<T: Trait>`) |
| Heterogeneous collection at runtime | Trait object (`Box<dyn Trait>` or `&dyn Trait`) |
| Performance-critical hot path | Generic (monomorphization, zero-cost) |
| Reducing compile times / binary size | Trait object (single implementation) |
| Need object safety | Trait object (no `Self` in return position, no generics on methods) |

### Crate Selection

| Task | Recommended Crate |
|------|------------------|
| Async runtime | `tokio` |
| Web framework | `axum` |
| HTTP client | `reqwest` |
| Database | `sqlx` (compile-checked SQL) or `diesel` (query builder) |
| Serialization | `serde` + `serde_json` / `toml` |
| CLI parsing | `clap` (derive) |
| Logging / tracing | `tracing` + `tracing-subscriber` |
| Error handling (lib) | `thiserror` |
| Error handling (app) | `anyhow` |
| Property testing | `proptest` |

## Reference Index

| File | Contents |
|------|----------|
| `references/ownership-borrowing-lifetimes.md` | Ownership rules, borrowing, lifetime annotations, elision, smart pointers, interior mutability, common borrow checker fixes |
| `references/error-handling.md` | Result/Option combinators, thiserror, anyhow, custom error types, error conversion, library vs application patterns |
| `references/traits-generics.md` | Trait definitions, default methods, associated types, trait objects, blanket impls, generics, where clauses, supertraits |
| `references/async-tokio.md` | Tokio runtime, spawn, channels, select!, timeouts, cancellation, stream processing, common async pitfalls |
| `references/design-patterns.md` | Newtype, typestate, builder, From/Into conversions, enum dispatch, strategy via closures, RAII guards |
| `references/serde-patterns.md` | Derive attributes, rename, flatten, tagged enums, custom serialization, skip, default, serde_with |
| `references/testing-patterns.md` | Unit tests, integration tests, test organization, fixtures, proptest, mocking, async test patterns |
| `references/ecosystem-crates.md` | Axum, sqlx, clap, tracing, reqwest, indicatif, Cargo workspaces, module organization, feature flags |
| `references/performance.md` | Iterators, zero-copy, Cow, SmallVec, allocation strategies, benchmarking, compiler hints, SIMD, unsafe guidelines |
