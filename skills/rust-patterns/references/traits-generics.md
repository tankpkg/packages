# Traits and Generics

Sources: Klabnik/Nichols (The Rust Programming Language 3rd ed.), Gjengset (Rust for Rustaceans), Blandy/Orendorff/Tindall (Programming Rust 2nd ed.), Rust API Guidelines, Rust Reference

Covers: trait definitions, default methods, associated types, trait objects vs generics, blanket implementations, where clauses, supertraits, and common standard library traits.

## Trait Fundamentals

Traits define shared behavior. A type implements a trait by providing the required methods:

```rust
pub trait Summary {
    fn summarize(&self) -> String;

    // Default implementation -- overridable
    fn preview(&self) -> String {
        format!("{}...", &self.summarize()[..50])
    }
}

struct Article { title: String, body: String }

impl Summary for Article {
    fn summarize(&self) -> String {
        format!("{}: {}", self.title, &self.body[..100])
    }
    // preview() uses the default implementation
}
```

### Orphan Rule

Implement a trait for a type only if you own the trait or the type (or both). This prevents conflicting implementations across crates.

| Owned | Can Implement? |
|-------|---------------|
| Both trait and type | Yes |
| Only the trait | Yes (for any foreign type) |
| Only the type | Yes (for any foreign trait) |
| Neither | No -- use newtype wrapper |

```rust
// Newtype workaround for orphan rule
struct Wrapper(Vec<String>);

impl fmt::Display for Wrapper {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "[{}]", self.0.join(", "))
    }
}
```

## Generic Functions

### impl Trait Syntax (Argument Position)

```rust
// Shorthand -- each call uses one concrete type
fn notify(item: &impl Summary) {
    println!("Breaking: {}", item.summarize());
}

// Equivalent desugared form
fn notify<T: Summary>(item: &T) {
    println!("Breaking: {}", item.summarize());
}
```

Use `impl Trait` for simple cases. Use explicit generics when you need the same type in multiple positions:

```rust
// Both parameters must be the SAME type
fn compare<T: Summary + PartialOrd>(a: &T, b: &T) -> &T { /* ... */ }
```

### impl Trait Syntax (Return Position)

```rust
fn make_iterator() -> impl Iterator<Item = u32> {
    (0..10).filter(|x| x % 2 == 0)
}
```

Return-position `impl Trait` hides the concrete type. The function can return only one concrete type (not conditionally different types).

### Where Clauses

Move complex bounds after the signature for readability:

```rust
fn process<T, U>(t: &T, u: &U) -> String
where
    T: Summary + Clone + Send,
    U: Display + Debug,
{
    format!("{} - {}", t.summarize(), u)
}
```

### Trait Bounds Cheatsheet

| Syntax | Meaning |
|--------|---------|
| `T: Trait` | T must implement Trait |
| `T: Trait1 + Trait2` | T must implement both |
| `T: Trait<Item = u32>` | T implements Trait with associated type Item = u32 |
| `T: 'a` | T outlives lifetime 'a |
| `T: 'static` | T contains no non-static references |
| `T: ?Sized` | T may be unsized (allows `str`, `[u8]`, `dyn Trait`) |
| `T: Send + Sync` | T is safe to send/share across threads |

## Associated Types vs Generic Parameters

```rust
// Associated type -- one implementation per type
trait Iterator {
    type Item;
    fn next(&mut self) -> Option<Self::Item>;
}

// Generic parameter -- multiple implementations per type
trait Convert<T> {
    fn convert(&self) -> T;
}
```

| Use | When |
|-----|------|
| Associated type | Each implementing type has exactly one logical choice |
| Generic parameter | A type could implement the trait for multiple type arguments |

### Examples

- `Iterator::Item` -- a Vec iterator always yields the same type
- `From<T>` -- a type can implement `From` for many source types
- `Add<Rhs>` -- a type can add different right-hand-side types

## Trait Objects and Dynamic Dispatch

### Object Safety

A trait is object-safe (usable as `dyn Trait`) when all methods:
- Take `&self`, `&mut self`, or `self: Box<Self>` as receiver
- Do not use `Self` in return position
- Do not have generic type parameters

```rust
// Object-safe -- can use as dyn Draw
trait Draw {
    fn draw(&self);
}

// NOT object-safe -- returns Self
trait Clonable {
    fn clone_self(&self) -> Self;
}
```

### Using Trait Objects

```rust
// Heterogeneous collection
let shapes: Vec<Box<dyn Draw>> = vec![
    Box::new(Circle { radius: 5.0 }),
    Box::new(Rectangle { w: 3.0, h: 4.0 }),
];

for shape in &shapes {
    shape.draw();  // dynamic dispatch via vtable
}
```

### Static vs Dynamic Dispatch

| Aspect | Static (Generics) | Dynamic (Trait Objects) |
|--------|-------------------|----------------------|
| Dispatch | Monomorphized at compile time | Vtable lookup at runtime |
| Performance | Zero-cost, inlined | One pointer indirection |
| Binary size | Larger (code duplicated per type) | Smaller (single implementation) |
| Flexibility | Known types at compile time | Heterogeneous collections |
| Compile time | Slower (more codegen) | Faster |

Prefer generics for performance-critical paths. Use trait objects for plugin systems, heterogeneous collections, and reducing compile times.

## Blanket Implementations

Implement a trait for all types satisfying a bound:

```rust
// From the standard library
impl<T: Display> ToString for T {
    fn to_string(&self) -> String {
        format!("{self}")
    }
}
```

Any type implementing `Display` automatically gets `ToString`. Write blanket impls carefully -- they apply broadly and can conflict.

## Supertraits

Require another trait as a prerequisite:

```rust
trait Printable: Display + Debug {
    fn print(&self) {
        println!("{self}");     // uses Display
    }
    fn debug_print(&self) {
        println!("{self:?}");   // uses Debug
    }
}
```

Implementing `Printable` requires implementing both `Display` and `Debug` first.

## Essential Standard Library Traits

### Derivable Traits

| Trait | Purpose | When to Derive |
|-------|---------|---------------|
| `Debug` | Debug formatting (`{:?}`) | Almost always -- derive on every type |
| `Clone` | Explicit duplication | When copies are needed |
| `Copy` | Implicit duplication (bitwise) | Small, simple types only |
| `PartialEq` / `Eq` | Equality comparison | When comparing values |
| `PartialOrd` / `Ord` | Ordering comparison | When sorting |
| `Hash` | Hash value for maps/sets | When used as HashMap key |
| `Default` | Default value | When a "zero value" makes sense |

### Conversion Traits

| Trait | Direction | When to Implement |
|-------|-----------|------------------|
| `From<T>` | T -> Self | Infallible conversion; provides `Into` for free |
| `Into<T>` | Self -> T | Implement `From` instead (blanket impl provides `Into`) |
| `TryFrom<T>` | T -> Result<Self, Error> | Fallible conversion |
| `TryInto<T>` | Self -> Result<T, Error> | Implement `TryFrom` instead |
| `AsRef<T>` | &Self -> &T | Cheap reference conversion |
| `Deref<Target=T>` | &Self -> &T | Smart pointer coercion (use sparingly) |

### Implement `From`, Get `Into` Free

```rust
struct Celsius(f64);
struct Fahrenheit(f64);

impl From<Celsius> for Fahrenheit {
    fn from(c: Celsius) -> Self {
        Fahrenheit(c.0 * 9.0 / 5.0 + 32.0)
    }
}

let temp: Fahrenheit = Celsius(100.0).into(); // Into provided automatically
```

### Operator Overloading

Implement `std::ops` traits for custom operators:

```rust
use std::ops::Add;

#[derive(Debug, Clone, Copy)]
struct Point { x: f64, y: f64 }

impl Add for Point {
    type Output = Self;
    fn add(self, other: Self) -> Self {
        Point { x: self.x + other.x, y: self.y + other.y }
    }
}
```

## Trait Design Guidelines

| Guideline | Rationale |
|-----------|-----------|
| Keep traits small and focused | Easier to implement, compose, and test |
| Provide default methods for common behavior | Reduces implementor burden |
| Use associated types for "one logical choice" | Cleaner than generic parameters |
| Document trait contracts (invariants, panics) | Implementors need to know the rules |
| Prefer `&self` over `self` in trait methods | Avoids forcing ownership transfer |
| Mark traits `Send + Sync` if async usage expected | Enables use across threads |
| Seal traits if extension is not intended | Prevent downstream implementations |

### Sealed Trait Pattern

Prevent external implementations while exposing the trait publicly:

```rust
mod private {
    pub trait Sealed {}
}

pub trait MyTrait: private::Sealed {
    fn method(&self);
}

// Only types in this crate can implement Sealed -> MyTrait
impl private::Sealed for MyType {}
impl MyTrait for MyType {
    fn method(&self) { /* ... */ }
}
```
