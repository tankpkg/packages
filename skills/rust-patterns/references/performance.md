# Performance Patterns

Sources: Blandy/Orendorff/Tindall (Programming Rust 2nd ed.), Gjengset (Rust for Rustaceans), The Rust Performance Book (nnethercote.github.io), Rust API Guidelines, Criterion.rs documentation

Covers: iterator patterns, zero-copy techniques, Cow, SmallVec, allocation strategies, benchmarking, compiler hints, SIMD basics, and guidelines for safe use of unsafe.

## Iterators Over Manual Loops

Iterators in Rust compile to the same machine code as manual loops (zero-cost abstraction) while being safer and often more readable:

```rust
// Prefer: iterator chain
let sum: i32 = numbers.iter()
    .filter(|&&x| x > 0)
    .map(|&x| x * 2)
    .sum();

// Avoid: manual loop with mutable accumulator
let mut sum = 0;
for &x in &numbers {
    if x > 0 {
        sum += x * 2;
    }
}
```

### Key Iterator Methods

| Method | Purpose | Lazy? |
|--------|---------|-------|
| `map(f)` | Transform each element | Yes |
| `filter(p)` | Keep elements matching predicate | Yes |
| `flat_map(f)` | Map + flatten nested iterators | Yes |
| `chain(other)` | Concatenate two iterators | Yes |
| `zip(other)` | Pair elements from two iterators | Yes |
| `enumerate()` | Add index to each element | Yes |
| `take(n)` / `skip(n)` | Limit / offset | Yes |
| `collect()` | Consume into a collection | No (terminal) |
| `fold(init, f)` | Reduce to a single value | No (terminal) |
| `for_each(f)` | Apply side effect | No (terminal) |
| `any(p)` / `all(p)` | Short-circuit boolean check | No (terminal) |
| `find(p)` | First matching element | No (terminal) |
| `position(p)` | Index of first match | No (terminal) |

### collect() Type Hints

```rust
let names: Vec<String> = users.iter().map(|u| u.name.clone()).collect();
let lookup: HashMap<u64, User> = users.into_iter().map(|u| (u.id, u)).collect();
let combined: String = words.iter().collect();
let result: Result<Vec<_>, _> = items.iter().map(parse).collect();  // short-circuits on Err
```

### Avoid Unnecessary Allocations in Chains

```rust
// BAD: allocates intermediate Vec
let result: Vec<_> = data.iter()
    .filter(|x| x.active)
    .collect::<Vec<_>>()    // unnecessary allocation
    .iter()
    .map(|x| x.name.clone())
    .collect();

// GOOD: single pass, no intermediate allocation
let result: Vec<_> = data.iter()
    .filter(|x| x.active)
    .map(|x| x.name.clone())
    .collect();
```

## Zero-Copy Patterns

### String Slices Instead of Owned Strings

```rust
// Prefer &str in function parameters
fn process(name: &str) -> bool {
    name.starts_with("admin_")
}

// Accept both String and &str
fn greet(name: impl AsRef<str>) {
    println!("Hello, {}", name.as_ref());
}
```

### Byte Slices for Binary Data

```rust
fn parse_header(data: &[u8]) -> Result<Header, ParseError> {
    let magic = &data[..4];        // zero-copy slice
    let version = data[4];
    let payload = &data[8..];      // zero-copy reference to rest
    Ok(Header { magic, version, payload })
}
```

### Borrowed Types in Structs

```rust
// Parsing without allocation
struct Token<'a> {
    kind: TokenKind,
    text: &'a str,       // borrows from source string
    span: Range<usize>,
}

fn tokenize(source: &str) -> Vec<Token<'_>> {
    // All tokens borrow from source -- no String allocations
    todo!()
}
```

## Cow -- Clone on Write

`Cow<'a, B>` borrows when possible, clones only when mutation is required:

```rust
use std::borrow::Cow;

fn escape_html(input: &str) -> Cow<'_, str> {
    if input.contains(['<', '>', '&', '"']) {
        // Only allocate when escaping is needed
        Cow::Owned(input
            .replace('&', "&amp;")
            .replace('<', "&lt;")
            .replace('>', "&gt;")
            .replace('"', "&quot;"))
    } else {
        Cow::Borrowed(input)  // zero-cost passthrough
    }
}
```

### Cow in APIs

Use `Cow` in function signatures that sometimes transform input and sometimes return it unchanged:

```rust
fn normalize_path(path: &str) -> Cow<'_, str> {
    if path.starts_with('/') {
        Cow::Borrowed(path)
    } else {
        Cow::Owned(format!("/{path}"))
    }
}
```

### When to Use Cow

| Scenario | Use Cow? |
|----------|---------|
| Most inputs pass through unchanged | Yes -- avoids allocation on the common path |
| Every input is always modified | No -- just return String |
| API compatibility (accept owned or borrowed) | Yes |
| Parsed configuration values | Yes -- most values are static strings |

## SmallVec -- Stack-Allocated Small Vectors

`SmallVec<[T; N]>` stores up to N elements on the stack, spilling to heap only when exceeded:

```rust
use smallvec::SmallVec;

// Most paths have 1-4 segments
fn split_path(path: &str) -> SmallVec<[&str; 4]> {
    path.split('/').filter(|s| !s.is_empty()).collect()
}
```

### When to Use SmallVec

| Scenario | Benefit |
|----------|---------|
| Collections with typical size < 8 | Avoids heap allocation on common case |
| Hot loop creating many small vecs | Eliminates allocator pressure |
| Parser tokens per line | Usually fits in stack buffer |

Profile before using SmallVec -- the extra complexity is only worth it in allocation-sensitive hot paths.

## Allocation Strategies

### Pre-Allocate with Capacity

```rust
// BAD: many reallocations as vec grows
let mut results = Vec::new();
for item in items {
    results.push(process(item));
}

// GOOD: single allocation
let mut results = Vec::with_capacity(items.len());
for item in items {
    results.push(process(item));
}

// BEST: collect from iterator (handles capacity automatically)
let results: Vec<_> = items.iter().map(process).collect();
```

### String Building

```rust
// BAD: many small allocations
let mut s = String::new();
for word in words {
    s += &word;
    s += " ";
}

// GOOD: pre-allocate, or use join
let s: String = words.join(" ");

// For complex building
let mut s = String::with_capacity(estimated_size);
use std::fmt::Write;
for (i, word) in words.iter().enumerate() {
    if i > 0 { s.push(' '); }
    write!(s, "{word}").unwrap();
}
```

### Reuse Allocations

```rust
let mut buffer = String::new();
for line in reader.lines() {
    buffer.clear();           // reuse the allocation
    buffer.push_str(&line?);
    process(&buffer);
}
```

## Benchmarking with Criterion

```rust
// benches/my_benchmark.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn bench_sort(c: &mut Criterion) {
    let data: Vec<i32> = (0..1000).rev().collect();

    c.bench_function("sort_1000", |b| {
        b.iter(|| {
            let mut d = black_box(data.clone());
            d.sort();
            d
        })
    });
}

criterion_group!(benches, bench_sort);
criterion_main!(benches);
```

```toml
# Cargo.toml
[[bench]]
name = "my_benchmark"
harness = false

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
```

Run benchmarks: `cargo bench`

### Benchmarking Guidelines

1. Use `black_box()` to prevent the compiler from optimizing away the computation
2. Benchmark realistic data sizes, not toy inputs
3. Run benchmarks on a quiet machine (no background load)
4. Compare before/after with statistical significance
5. Benchmark the hot path, not everything

## Compiler Optimization Hints

### Release Profile

```toml
[profile.release]
opt-level = 3        # maximum optimization
lto = true           # link-time optimization (slower build, faster binary)
codegen-units = 1    # single codegen unit (slower build, better optimization)
panic = "abort"      # smaller binary, no unwinding overhead
strip = true         # remove debug symbols
```

### #[inline] Guidance

| Annotation | Effect | When |
|-----------|--------|------|
| (none) | Compiler decides | Default -- correct 99% of the time |
| `#[inline]` | Hint to inline | Small functions called across crate boundaries |
| `#[inline(always)]` | Force inline | Performance-critical tiny functions (measure first) |
| `#[cold]` | Unlikely path | Error handling code, panic paths |

Do not sprinkle `#[inline]` everywhere. The compiler inlines aggressively within a crate. The annotation only matters across crate boundaries.

## Unsafe Guidelines

### When Unsafe Is Justified

| Scenario | Justification |
|----------|--------------|
| FFI calls to C libraries | C functions are inherently unsafe |
| Performance-critical inner loop (measured) | Skip bounds checks after proving safety |
| Implementing a data structure | Self-referential types, raw pointer manipulation |
| Interfacing with hardware / OS | MMIO, syscalls |

### Unsafe Best Practices

1. Minimize unsafe scope -- wrap in a safe API
2. Document safety invariants with `// SAFETY:` comments
3. Use `unsafe` blocks, not `unsafe fn` (unless the entire function is unsafe to call)
4. Test extensively, including with Miri (`cargo +nightly miri test`)
5. Prefer safe alternatives first (check if a crate exists)

```rust
/// Returns element at index without bounds checking.
///
/// # Safety
/// Caller must ensure `index < self.len()`.
pub unsafe fn get_unchecked(&self, index: usize) -> &T {
    // SAFETY: caller guarantees index is in bounds
    unsafe { self.data.get_unchecked(index) }
}
```

### Common Unsafe Anti-Patterns

| Anti-Pattern | Risk | Fix |
|-------------|------|-----|
| `unsafe` to silence borrow checker | Undefined behavior | Fix the ownership design |
| Raw pointers instead of references | Dangling pointers | Use references with proper lifetimes |
| Transmute between unrelated types | Memory corruption | Use From/Into or safe conversions |
| Missing `// SAFETY:` comments | Unverifiable invariants | Document every unsafe block |
| Large unsafe blocks | Hard to audit | Minimize scope, isolate unsafe |
