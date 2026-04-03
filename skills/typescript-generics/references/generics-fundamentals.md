# Generics Fundamentals

Sources: TypeScript Handbook (typescriptlang.org, 2026), Vanderkam (Effective TypeScript, 2nd ed., 2024), Cherny (Programming TypeScript, 2019)

Covers: type parameters, constraints, defaults, inference, generic functions, generic classes, generic interfaces, and when to use generics vs alternatives.

## Type Parameters

A type parameter is a placeholder that captures a type at the call site. Declare with angle brackets after the function/class/interface name:

```typescript
function identity<T>(arg: T): T {
  return arg;
}

// Explicit type argument
const a = identity<string>("hello"); // a: string

// Inferred type argument (preferred)
const b = identity("hello"); // b: "hello" (literal type inferred)
```

### Naming Conventions

| Convention | When |
|-----------|------|
| `T` | Single unconstrained parameter |
| `T`, `U`, `V` | Multiple parameters in order |
| `TKey`, `TValue` | Descriptive when role matters |
| `K extends keyof T` | Key parameter constrained to object keys |
| `E` | Element/entry type (arrays, collections) |
| `R` | Return/result type |

Avoid single-letter names in complex signatures with 3+ parameters. Use descriptive names when the role is not obvious from position.

## Generic Constraints

Constrain a type parameter with `extends` to restrict what types can be passed:

```typescript
// Must have a length property
interface HasLength {
  length: number;
}

function logLength<T extends HasLength>(arg: T): T {
  console.log(arg.length);
  return arg;
}

logLength("hello");      // OK: string has .length
logLength([1, 2, 3]);    // OK: array has .length
logLength(42);           // Error: number has no .length
```

### Constraint Patterns

| Pattern | Syntax | Use Case |
|---------|--------|----------|
| Interface constraint | `T extends SomeInterface` | Must have specific shape |
| Key constraint | `K extends keyof T` | Must be a key of another param |
| Union constraint | `T extends string \| number` | Must be one of several types |
| Constructor constraint | `T extends new (...args: any[]) => any` | Must be instantiable |
| Callable constraint | `T extends (...args: any[]) => any` | Must be a function |
| Recursive constraint | `T extends Comparable<T>` | F-bounded polymorphism |
| Multiple constraints | `T extends A & B` | Must satisfy both interfaces |

### Using Type Parameters in Constraints

One type parameter can constrain another. This creates relationships between parameters:

```typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const person = { name: "Alice", age: 30 };
getProperty(person, "name");  // OK, returns string
getProperty(person, "email"); // Error: "email" not in keyof person
```

## Generic Defaults

Provide default types for optional type parameters. Defaults must satisfy any constraint:

```typescript
interface ApiResponse<TData = unknown, TError = Error> {
  data: TData | null;
  error: TError | null;
  status: number;
}

// Uses defaults
const res1: ApiResponse = { data: null, error: null, status: 200 };

// Overrides TData only
const res2: ApiResponse<User> = { data: user, error: null, status: 200 };

// Overrides both
const res3: ApiResponse<User, AppError> = { data: null, error: appErr, status: 500 };
```

### Default Rules

- Required parameters must come before optional (defaulted) parameters
- Defaults must satisfy constraints: `T extends Base = SpecificBase` requires `SpecificBase extends Base`
- When inference fails, the default is used as the fallback type
- Useful for API evolution: add new parameters with defaults to avoid breaking callers

## Type Inference

TypeScript infers generic type arguments from the values passed to a function:

```typescript
function map<T, U>(arr: T[], fn: (item: T) => U): U[] {
  return arr.map(fn);
}

// T inferred as number, U inferred as string
const result = map([1, 2, 3], (n) => n.toString());
```

### Inference Positions

TypeScript infers types from specific positions in a function signature:

| Position | Inference Behavior |
|----------|-------------------|
| Parameter type | Primary inference site |
| Return type | Does not drive inference (consumed, not inferred) |
| Constraint | Not an inference site |
| Default | Fallback when inference fails |

### When Inference Fails

| Symptom | Fix |
|---------|-----|
| Type widens to base constraint | Add explicit type argument |
| Returns `unknown` instead of specific type | Check parameter position provides inference |
| Infers union when you want specific | Use `const` assertion or `as const` on argument |
| Conflicting inferences from multiple params | Split into multiple generic calls |

### NoInfer (TypeScript 5.4+)

Block inference from specific positions without changing the type:

```typescript
function createList<T>(items: T[], defaultItem: NoInfer<T>): T[] {
  return [...items, defaultItem];
}

// T inferred from first argument only
createList(["a", "b"], "c");    // OK: T is string
createList(["a", "b"], 42);     // Error: number not assignable to string
```

Without `NoInfer`, TypeScript would infer `T` as `string | number` from both arguments.

## Generic Functions

### Function Declarations

```typescript
function first<T>(arr: T[]): T | undefined {
  return arr[0];
}
```

### Arrow Functions

```typescript
const first = <T,>(arr: T[]): T | undefined => arr[0];
// Note: trailing comma after T avoids JSX ambiguity in .tsx files
```

### Method Signatures

```typescript
interface Collection<T> {
  add(item: T): void;
  find<U extends T>(predicate: (item: T) => item is U): U | undefined;
}
```

### Generic vs Overloads Decision

| Factor | Generic | Overloads |
|--------|---------|-----------|
| Relates input to output type | Preferred | Unnecessary complexity |
| Few fixed type mappings | Over-general | Preferred |
| Return varies by argument count | Cannot express | Required |
| API consumed by external users | Simpler signatures | Clearer intent per case |

Prefer generics when the return type is a function of the input type. Prefer overloads when you have 2-3 discrete cases with unrelated types.

## Generic Classes

```typescript
class Stack<T> {
  private items: T[] = [];

  push(item: T): void {
    this.items.push(item);
  }

  pop(): T | undefined {
    return this.items.pop();
  }

  peek(): T | undefined {
    return this.items[this.items.length - 1];
  }
}

const nums = new Stack<number>();
nums.push(1);
nums.push("a"); // Error: string not assignable to number
```

### Static Members Cannot Use Class Type Parameters

Static members belong to the class constructor, not instances. They cannot reference instance-level type parameters:

```typescript
class Box<T> {
  static defaultValue: T; // Error: cannot use T in static context
  value: T;               // OK: instance member
}
```

## Generic Interfaces

```typescript
interface Repository<T> {
  findById(id: string): Promise<T | null>;
  findAll(): Promise<T[]>;
  create(data: Omit<T, "id">): Promise<T>;
  update(id: string, data: Partial<T>): Promise<T>;
  delete(id: string): Promise<void>;
}

// Concrete implementation
class UserRepository implements Repository<User> {
  async findById(id: string): Promise<User | null> { /* ... */ }
  // ...
}
```

### Interface-Level vs Method-Level Type Parameters

| Placement | Meaning | Example |
|-----------|---------|---------|
| `interface Repo<T>` | Type fixed for the entire interface | `Repository<User>` |
| `find<U>(pred): U` | Type varies per method call | Different return per invocation |

Place the parameter at the interface level when all methods operate on the same type. Place at method level when each call may produce a different type.

## When NOT to Use Generics

| Situation | Alternative |
|-----------|-------------|
| Only one concrete type ever used | Use the concrete type directly |
| Type parameter used only once | Remove it -- it adds no relationship |
| Complex nested generics hurt readability | Simplify with type aliases |
| Runtime type checking needed | Use discriminated unions or classes |

### The "Used Only Once" Rule

If a type parameter appears only once in a signature, it is not creating a relationship. Remove it:

```typescript
// Bad: T used only once -- adds no value
function greet<T extends string>(name: T): void {
  console.log(`Hello, ${name}`);
}

// Good: concrete type is clearer
function greet(name: string): void {
  console.log(`Hello, ${name}`);
}
```

Exception: when you want the return type to be the narrower literal type, a single-use generic preserves it. Evaluate case by case.

## Generic Best Practices

| Practice | Rationale |
|----------|-----------|
| Use fewest type parameters possible | Each parameter is cognitive overhead |
| Constrain as tightly as the use case requires | Prevents misuse, improves error messages |
| Let inference work | Explicit type args are noise when inference succeeds |
| Name parameters descriptively for 3+ params | `<T, U, V>` is unreadable; `<TInput, TOutput, TError>` is clear |
| Avoid nesting generics beyond 2 levels | `Map<string, Array<Pair<K, V>>>` is a readability problem |
| Test generic types with edge cases | Pass `never`, `unknown`, `any`, union types |
| Document constraints in JSDoc | `@template T - Must implement Serializable` |
