# Variance and Advanced Generic Patterns

Sources: TypeScript Handbook -- Generics: Variance Annotations (typescriptlang.org, 2026), Vanderkam (Effective TypeScript, 2nd ed., 2024), TypeScript 4.7 Release Notes (Variance Annotations)

Covers: covariance, contravariance, invariance, bivariance, the `in`/`out` annotation syntax, generic class patterns, higher-kinded type emulation, and generic type parameter constraints in depth.

## Variance Fundamentals

Variance describes how subtype relationships between generic types relate to subtype relationships between their type arguments.

Given `Cat extends Animal`:

| Variance | Relationship | Example |
|----------|-------------|---------|
| Covariant | `F<Cat>` assignable to `F<Animal>` | Producers: `() => Cat` assignable to `() => Animal` |
| Contravariant | `F<Animal>` assignable to `F<Cat>` | Consumers: `(x: Animal) => void` assignable to `(x: Cat) => void` |
| Invariant | Neither direction | Both produces and consumes: `{ get(): T; set(v: T): void }` |
| Bivariant | Both directions | TypeScript method parameters (legacy) |

### Intuition

- **Covariant** (output position): producing a Cat is fine where an Animal is expected -- a Cat IS an Animal
- **Contravariant** (input position): consuming an Animal is fine where a Cat consumer is expected -- anything that handles Animals can handle Cats
- **Invariant**: when type appears in both input and output, neither direction is safe

## TypeScript's Structural Variance

TypeScript infers variance from structure. No annotation needed in most cases:

```typescript
// Covariant: T in output position only
interface Producer<T> {
  make(): T;
}
// Producer<Cat> is assignable to Producer<Animal> -- inferred covariant

// Contravariant: T in input position only
interface Consumer<T> {
  consume(arg: T): void;
}
// Consumer<Animal> is assignable to Consumer<Cat> -- inferred contravariant

// Invariant: T in both positions
interface Processor<T> {
  process(arg: T): T;
}
// Neither direction works -- inferred invariant
```

### Method vs Function Property Bivariance

TypeScript treats method signatures and function property signatures differently:

```typescript
interface WithMethod<T> {
  handle(x: T): void; // Method syntax: BIVARIANT (both directions)
}

interface WithProperty<T> {
  handle: (x: T) => void; // Property syntax: CONTRAVARIANT (with strictFunctionTypes)
}
```

With `strictFunctionTypes: true` (recommended):
- Method syntax (`handle(x: T)`) remains bivariant for compatibility with DOM APIs
- Property syntax (`handle: (x: T) => void`) is properly contravariant

Use property syntax for type-safe callback definitions.

## Variance Annotations (TypeScript 4.7+)

Explicitly declare variance with `in` (contravariant) and `out` (covariant):

```typescript
// Covariant: T only produced (output)
interface Producer<out T> {
  make(): T;
}

// Contravariant: T only consumed (input)
interface Consumer<in T> {
  consume(arg: T): void;
}

// Invariant: T both consumed and produced
interface Processor<in out T> {
  process(arg: T): T;
}
```

### When to Use Variance Annotations

| Situation | Action |
|-----------|--------|
| Normal code | Do NOT annotate -- TypeScript infers correctly |
| Circular types causing incorrect inference | Annotate to fix |
| Performance profiling shows slow variance inference | Annotate as optimization |
| Type debugging | Temporary annotations to verify expected variance |

TypeScript will error if the annotation contradicts the structural usage:

```typescript
// Error: T is used in output position but declared contravariant
interface Bad<in T> {
  make(): T; // Error: variance annotation doesn't match
}
```

### Rules for Variance Annotations

- `out T`: T must only appear in output (return) positions
- `in T`: T must only appear in input (parameter) positions
- `in out T`: T can appear anywhere (invariant)
- Annotations are checked against structural usage -- TypeScript rejects contradictions
- Annotations only affect instantiation-based comparisons, not structural comparisons
- Never write annotations that disagree with the structural reality

## Generic Classes in Depth

### Class with Multiple Type Parameters

```typescript
class KeyValueStore<K extends string | number, V> {
  private store = new Map<K, V>();

  set(key: K, value: V): void {
    this.store.set(key, value);
  }

  get(key: K): V | undefined {
    return this.store.get(key);
  }

  entries(): [K, V][] {
    return [...this.store.entries()];
  }
}

const store = new KeyValueStore<string, User>();
store.set("alice", { name: "Alice", age: 30 });
```

### Abstract Generic Classes

```typescript
abstract class Repository<T extends { id: string }> {
  abstract findById(id: string): Promise<T | null>;
  abstract save(entity: T): Promise<T>;

  async findOrFail(id: string): Promise<T> {
    const entity = await this.findById(id);
    if (!entity) throw new Error(`Entity not found: ${id}`);
    return entity;
  }
}

class UserRepository extends Repository<User> {
  async findById(id: string): Promise<User | null> { /* ... */ }
  async save(user: User): Promise<User> { /* ... */ }
}
```

### Generic Mixins

```typescript
type Constructor<T = {}> = new (...args: any[]) => T;

function Timestamped<TBase extends Constructor>(Base: TBase) {
  return class extends Base {
    createdAt = new Date();
    updatedAt = new Date();

    touch() {
      this.updatedAt = new Date();
    }
  };
}

function Activatable<TBase extends Constructor>(Base: TBase) {
  return class extends Base {
    isActive = false;

    activate() { this.isActive = true; }
    deactivate() { this.isActive = false; }
  };
}

class User {
  constructor(public name: string) {}
}

const TimestampedUser = Timestamped(User);
const FullUser = Activatable(Timestamped(User));

const user = new FullUser("Alice");
user.touch();      // From Timestamped
user.activate();   // From Activatable
user.name;         // From User
```

## Higher-Kinded Type Emulation

TypeScript does not natively support higher-kinded types (types parameterized by other generic types). Emulate with interface merging or mapped types:

### URI Pattern (fp-ts style)

```typescript
// Define a type-level registry
interface URItoKind<A> {
  Option: Option<A>;
  Array: A[];
  Promise: Promise<A>;
}

type URIS = keyof URItoKind<any>;
type Kind<URI extends URIS, A> = URItoKind<A>[URI];

// Now write generic code over "any container"
interface Functor<F extends URIS> {
  map: <A, B>(fa: Kind<F, A>, f: (a: A) => B) => Kind<F, B>;
}

// Implement for specific containers
const arrayFunctor: Functor<"Array"> = {
  map: (fa, f) => fa.map(f),
};
```

### Defunctionalization Pattern

```typescript
// Type-level "function" as an interface
interface TypeFn {
  return: unknown;
}

// "Apply" the type function
type Apply<F extends TypeFn, Arg> = (F & { arg: Arg })["return"];

// Define a specific type function
interface ToArray extends TypeFn {
  return: this["arg"] extends infer A ? A[] : never;
}

type Result = Apply<ToArray, string>; // string[]
```

## Advanced Constraint Patterns

### F-Bounded Polymorphism

A type parameter constrained by a type that references itself:

```typescript
interface Comparable<T extends Comparable<T>> {
  compareTo(other: T): number;
}

class Temperature implements Comparable<Temperature> {
  constructor(public celsius: number) {}

  compareTo(other: Temperature): number {
    return this.celsius - other.celsius;
  }
}

// Cannot compare Temperature with Distance -- type-safe
```

### Recursive Type Constraints

```typescript
type JSONValue =
  | string
  | number
  | boolean
  | null
  | JSONValue[]
  | { [key: string]: JSONValue };

function deepClone<T extends JSONValue>(value: T): T {
  return JSON.parse(JSON.stringify(value));
}
```

### Conditional Constraints

```typescript
type ArrayOrSingle<T, IsArray extends boolean> =
  IsArray extends true ? T[] : T;

function wrap<T, B extends boolean>(
  value: T,
  asArray: B
): ArrayOrSingle<T, B> {
  return (asArray ? [value] : value) as ArrayOrSingle<T, B>;
}

const a = wrap("hello", true);  // string[]
const b = wrap("hello", false); // string
```

## Generic Type Narrowing

### Narrowing Generic Parameters

TypeScript does not automatically narrow type parameters in generic functions. Use overloads or conditional return types:

```typescript
// Does NOT narrow T:
function process<T extends string | number>(value: T): T {
  if (typeof value === "string") {
    // value is still T, not string
    return value.toUpperCase() as T; // Cast needed
  }
  return (value * 2) as T;
}

// Better: use overloads
function process(value: string): string;
function process(value: number): number;
function process(value: string | number): string | number {
  if (typeof value === "string") return value.toUpperCase();
  return value * 2;
}
```

### Generic Type Guards

```typescript
function isOfType<T>(
  value: unknown,
  check: (v: any) => v is T
): value is T {
  return check(value);
}

function isString(v: any): v is string {
  return typeof v === "string";
}

function example(input: unknown) {
  if (isOfType(input, isString)) {
    input.toUpperCase(); // input: string
  }
}
```

## Variance Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Mutable array covariance | `Cat[]` assignable to `Animal[]` allows pushing Dog | Use `readonly` arrays |
| Method bivariance | Unsound for non-DOM types | Use property syntax for callbacks |
| Variance annotation mismatch | Annotation disagrees with structure | Remove annotation, let TS infer |
| Assuming annotations change behavior | They only affect specific comparisons | Annotations match, not force |
| Ignoring invariance | Mutable state must be invariant | Use readonly for covariant sharing |
