# Ownership, Borrowing, and Lifetimes

Sources: Klabnik/Nichols (The Rust Programming Language 3rd ed.), Gjengset (Rust for Rustaceans), Blandy/Orendorff/Tindall (Programming Rust 2nd ed.), Rust Reference

Covers: ownership rules, borrowing semantics, lifetime annotations, elision rules, smart pointers, interior mutability, and common borrow checker error resolutions.

## The Three Ownership Rules

1. Every value has exactly one owner
2. When the owner goes out of scope, the value is dropped
3. Ownership can be transferred (moved), but not duplicated (unless the type implements `Copy`)

### Move Semantics

Assignment and function calls transfer ownership by default for non-Copy types:

```rust
let s1 = String::from("hello");
let s2 = s1;          // s1 is moved into s2 -- s1 is no longer valid
// println!("{s1}");   // compile error: value used after move
```

Types implementing `Copy` (integers, floats, bools, tuples of Copy types) are duplicated instead of moved. Implement `Copy` only for small, stack-allocated types with no heap resources.

### Drop and RAII

When a value goes out of scope, Rust calls `drop()` automatically. Use this for resource cleanup (file handles, network connections, locks). Implement the `Drop` trait for custom cleanup:

```rust
struct Connection { /* ... */ }

impl Drop for Connection {
    fn drop(&mut self) {
        // close the connection
    }
}
```

`drop()` is called in reverse declaration order. Never call `drop()` explicitly on a value -- use `std::mem::drop(value)` to drop early.

## Borrowing Rules

Two kinds of references:

| Reference | Syntax | Rules |
|-----------|--------|-------|
| Shared (immutable) | `&T` | Any number simultaneously, no mutation |
| Exclusive (mutable) | `&mut T` | Exactly one at a time, full mutation |

The borrow checker enforces: you cannot have a mutable reference while any shared references exist for the same data.

### Non-Lexical Lifetimes (NLL)

The borrow checker tracks when references are last used, not when they go out of scope:

```rust
let mut v = vec![1, 2, 3];
let first = &v[0];       // shared borrow starts
println!("{first}");      // shared borrow last used here
v.push(4);                // mutable borrow -- OK because shared borrow ended above
```

### Reborrowing

Passing `&mut T` to a function that takes `&mut T` creates a reborrow, not a move. The original mutable reference is temporarily suspended and resumes after the call.

```rust
fn process(data: &mut Vec<i32>) { data.push(42); }

let mut v = vec![1];
let r = &mut v;
process(r);     // reborrow of r
r.push(2);      // r is still valid after reborrow ends
```

## Lifetime Annotations

Lifetimes annotate how long references remain valid. The compiler infers most lifetimes; annotate only when it cannot.

### When Annotations Are Required

1. Functions returning references derived from multiple input references
2. Struct fields holding references
3. Impl blocks for types with lifetime parameters

```rust
// Compiler cannot infer which input lifetime applies to the return
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

### Lifetime Elision Rules

The compiler applies three rules automatically:

1. Each input reference gets its own lifetime parameter
2. If exactly one input lifetime, it applies to all output references
3. If one input is `&self` or `&mut self`, its lifetime applies to all output references

If these rules fully determine output lifetimes, no annotation is needed.

### Common Lifetime Patterns

| Pattern | Meaning |
|---------|---------|
| `'a` | Generic lifetime parameter |
| `'static` | Lives for the entire program (string literals, leaked allocations) |
| `'_` | Elided lifetime -- let the compiler figure it out |
| `T: 'a` | T must outlive lifetime 'a (T contains no references shorter than 'a) |
| `for<'a>` | Higher-ranked trait bound -- works for any lifetime |

### Structs with References

```rust
struct Excerpt<'a> {
    text: &'a str,   // the reference must outlive the struct
}

impl<'a> Excerpt<'a> {
    fn level(&self) -> i32 { 3 }           // elision rule 3 applies
    fn announce(&self, part: &str) -> &str { // returns &self lifetime
        self.text
    }
}
```

Prefer owned data in structs unless borrowing is specifically needed for performance. Owned structs are simpler to use and have no lifetime constraints.

## Smart Pointers

### Box<T> -- Heap Allocation

Single owner, heap-allocated. Use when:
- Type size is unknown at compile time (recursive types)
- Transferring ownership of large data without copying
- Trait objects (`Box<dyn Trait>`)

```rust
// Recursive type requires indirection
enum List {
    Cons(i32, Box<List>),
    Nil,
}
```

### Rc<T> -- Reference Counting (Single-Thread)

Multiple owners, single-threaded. Cloning an `Rc` increments the reference count. Data is dropped when the count reaches zero.

```rust
use std::rc::Rc;
let a = Rc::new(vec![1, 2, 3]);
let b = Rc::clone(&a);  // both a and b own the Vec
// Rc::strong_count(&a) == 2
```

Avoid reference cycles with `Rc` -- they leak memory. Use `Weak<T>` for back-references.

### Arc<T> -- Atomic Reference Counting (Multi-Thread)

Thread-safe version of `Rc`. Use when sharing data across threads.

```rust
use std::sync::Arc;
let data = Arc::new(vec![1, 2, 3]);
let data_clone = Arc::clone(&data);
std::thread::spawn(move || {
    println!("{:?}", data_clone);
});
```

### Cow<'a, T> -- Clone on Write

Borrows data when possible, clones only when mutation is needed:

```rust
use std::borrow::Cow;

fn normalize(input: &str) -> Cow<'_, str> {
    if input.contains(' ') {
        Cow::Owned(input.replace(' ', "_"))  // allocates only when needed
    } else {
        Cow::Borrowed(input)                 // zero-cost borrow
    }
}
```

Use `Cow` in function signatures that sometimes need to modify data and sometimes pass it through unchanged. Common in parsers and text processors.

## Interior Mutability

Allow mutation through shared references, checked at runtime instead of compile time.

| Type | Thread Safety | Check | Use Case |
|------|-------------|-------|----------|
| `Cell<T>` | No | None (Copy types) | Simple values, counters |
| `RefCell<T>` | No | Runtime borrow check | Complex single-thread mutation |
| `Mutex<T>` | Yes | Lock acquisition | Shared mutable state across threads |
| `RwLock<T>` | Yes | Read/write lock | Multiple readers, occasional writer |
| `AtomicU64` etc. | Yes | Hardware atomic | Counters, flags, simple shared state |

### RefCell Pattern

```rust
use std::cell::RefCell;
let data = RefCell::new(vec![1, 2, 3]);
data.borrow_mut().push(4);      // runtime borrow check
let snapshot = data.borrow();   // panics if borrow_mut is active
```

Prefer `try_borrow()` / `try_borrow_mut()` to avoid panics in complex code paths.

### Mutex Pattern

```rust
use std::sync::{Arc, Mutex};
let counter = Arc::new(Mutex::new(0));
let c = Arc::clone(&counter);
std::thread::spawn(move || {
    let mut num = c.lock().unwrap();
    *num += 1;
});  // MutexGuard dropped here, lock released
```

Keep lock scopes as small as possible. Never hold a lock across an `.await` point in async code -- use `tokio::sync::Mutex` instead.

## Common Borrow Checker Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "cannot borrow as mutable because also borrowed as immutable" | Overlapping shared and mutable borrows | Limit shared borrow scope, or clone the data |
| "does not live long enough" | Reference outlives the data it points to | Return owned data, use `'static`, or restructure |
| "cannot move out of borrowed content" | Trying to take ownership from a reference | Use `.clone()`, `std::mem::take()`, or `Option::take()` |
| "value moved here" | Ownership transferred, then used again | Clone before the move, or restructure to avoid the move |
| "closure may outlive the current function" | Closure captures a reference to local data | Use `move` keyword to take ownership in the closure |
| "cannot return reference to local variable" | Function creates data and tries to return a reference to it | Return the owned value instead |

### The Clone Escape Hatch

When fighting the borrow checker, `.clone()` is a valid strategy:
- Correctness first, optimize later
- Clone is O(n) but often negligible compared to I/O
- Profile before replacing clones with references -- the complexity cost of lifetimes may not be worth it

### Restructuring Ownership

When cloning feels wrong, redesign the data flow:
1. Pass owned values into functions instead of borrowing
2. Return computed values instead of references to internal state
3. Use indices into a `Vec` instead of references to elements
4. Split structs so borrows do not overlap

## The Newtype Pattern

Wrap a type to add meaning without runtime cost:

```rust
struct UserId(u64);
struct OrderId(u64);

fn get_user(id: UserId) -> User { /* ... */ }
// get_user(OrderId(42));  // compile error -- type safety
```

Derive `From`, `Deref`, or implement `Display` to make newtypes ergonomic. Use newtypes to implement foreign traits on foreign types (orphan rule workaround).
