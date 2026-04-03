# Branded Types, Discriminated Unions, and Type Narrowing

Sources: Vanderkam (Effective TypeScript, 2nd ed., 2024), TypeScript Handbook -- Narrowing (typescriptlang.org, 2026), Cherny (Programming TypeScript, 2019)

Covers: branded/opaque types for domain primitives, discriminated unions for state modeling, type guards, assertion functions, the satisfies operator, and type narrowing patterns.

## Branded Types (Opaque Types)

A branded type adds a phantom property to a primitive to make it nominally distinct. This prevents mixing values that share the same underlying type:

```typescript
type UserId = string & { readonly __brand: unique symbol };
type OrderId = string & { readonly __brand: unique symbol };

function createUserId(id: string): UserId {
  return id as UserId;
}

function createOrderId(id: string): OrderId {
  return id as OrderId;
}

function getUser(id: UserId): User { /* ... */ }

const userId = createUserId("user-123");
const orderId = createOrderId("order-456");

getUser(userId);   // OK
getUser(orderId);  // Error: OrderId not assignable to UserId
getUser("raw");    // Error: string not assignable to UserId
```

### Brand Patterns

| Pattern | Syntax | Use Case |
|---------|--------|----------|
| Unique symbol | `string & { __brand: unique symbol }` | Different types per declaration |
| Literal brand | `number & { __brand: "USD" }` | Readable, explicit brand name |
| Interface brand | `interface UserId extends String { __brand: "UserId" }` | Class-style declaration |
| Intersection brand | `type Email = string & Brand<"Email">` | Generic brand helper |

### Generic Brand Helper

```typescript
declare const __brand: unique symbol;
type Brand<B extends string> = { [__brand]: B };

type UserId = string & Brand<"UserId">;
type Email = string & Brand<"Email">;
type USD = number & Brand<"USD">;
type EUR = number & Brand<"EUR">;
```

### Branded Types with Validation

Combine branding with runtime validation for domain primitives:

```typescript
type Email = string & Brand<"Email">;

function parseEmail(input: string): Email {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input)) {
    throw new Error(`Invalid email: ${input}`);
  }
  return input as Email;
}

// Now Email carries both type safety AND validation guarantee
function sendEmail(to: Email, subject: string): void { /* ... */ }

sendEmail(parseEmail("alice@example.com"), "Hello"); // OK
sendEmail("alice@example.com", "Hello"); // Error: string is not Email
```

### When to Use Branded Types

| Signal | Use Branded Type |
|--------|-----------------|
| Two string/number values must not be mixed | Always |
| Domain has units (USD, EUR, px, rem) | Prevent unit mixing |
| IDs from different entities | Prevent wrong-entity lookups |
| Validated vs unvalidated data | Parse once, trust thereafter |
| API boundaries | Distinguish external vs internal strings |

## Discriminated Unions

A discriminated union is a union of types that share a common literal property (the discriminant). TypeScript narrows the type based on the discriminant value:

```typescript
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "square"; side: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2; // shape narrowed to circle
    case "square":
      return shape.side ** 2;              // shape narrowed to square
    case "triangle":
      return (shape.base * shape.height) / 2;
  }
}
```

### Discriminant Requirements

| Requirement | Details |
|-------------|---------|
| Shared property name | All members must have the same property (e.g., `kind`, `type`, `status`) |
| Literal type values | Values must be string/number/boolean literals, not `string` |
| Unique per member | Each union member must have a distinct discriminant value |

### Exhaustiveness Checking

Use `never` to ensure all cases are handled:

```typescript
function assertNever(x: never): never {
  throw new Error(`Unexpected value: ${x}`);
}

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle": return Math.PI * shape.radius ** 2;
    case "square": return shape.side ** 2;
    case "triangle": return (shape.base * shape.height) / 2;
    default: return assertNever(shape);
    // Error if a new Shape member is added but not handled
  }
}
```

### State Machine Modeling

Discriminated unions model state machines where each state has different available data:

```typescript
type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: Error };

function renderData<T>(state: AsyncState<T>): string {
  switch (state.status) {
    case "idle": return "Ready";
    case "loading": return "Loading...";
    case "success": return `Data: ${state.data}`; // data available
    case "error": return `Error: ${state.error.message}`; // error available
  }
}
```

### Discriminated Union vs Class Hierarchy

| Factor | Discriminated Union | Class Hierarchy |
|--------|-------------------|-----------------|
| Adding new variants | Add to union (open) | Add subclass (open) |
| Adding new operations | Modify all switch/match (closed) | Add method to each class (open) |
| Pattern matching | switch/if narrowing | Visitor pattern |
| Serialization | Plain objects (JSON-friendly) | Requires hydration |
| Runtime overhead | None (just objects) | Prototype chain |

Prefer discriminated unions for data-oriented models (API responses, Redux actions, events). Prefer classes for behavior-oriented models with polymorphic methods.

## Type Guards

### typeof Guards

```typescript
function padLeft(value: string, padding: string | number): string {
  if (typeof padding === "number") {
    return " ".repeat(padding) + value; // padding: number
  }
  return padding + value; // padding: string
}
```

### instanceof Guards

```typescript
function logError(error: Error | string): void {
  if (error instanceof Error) {
    console.error(error.message); // error: Error
  } else {
    console.error(error); // error: string
  }
}
```

### Custom Type Guards (is)

Define a function whose return type is a type predicate:

```typescript
interface Fish { swim(): void }
interface Bird { fly(): void }

function isFish(pet: Fish | Bird): pet is Fish {
  return (pet as Fish).swim !== undefined;
}

function move(pet: Fish | Bird) {
  if (isFish(pet)) {
    pet.swim(); // pet: Fish
  } else {
    pet.fly();  // pet: Bird
  }
}
```

### Type Guard Patterns

| Pattern | Syntax | Narrows |
|---------|--------|---------|
| typeof | `typeof x === "string"` | Primitives only |
| instanceof | `x instanceof Date` | Class instances |
| in operator | `"swim" in x` | Property existence |
| Custom guard | `(x): x is Type` | Any predicate |
| Equality | `x === null` | Literal/null/undefined |
| Truthiness | `if (x)` | Removes null/undefined/false/0/"" |

## Assertion Functions (asserts)

An assertion function narrows the type for all code after the call (not just the if-branch):

```typescript
function assertIsString(val: unknown): asserts val is string {
  if (typeof val !== "string") {
    throw new Error(`Expected string, got ${typeof val}`);
  }
}

function processInput(input: unknown) {
  assertIsString(input);
  // input is string from here onward
  console.log(input.toUpperCase());
}
```

### Assert Non-Null

```typescript
function assertDefined<T>(val: T | null | undefined, msg?: string): asserts val is T {
  if (val === null || val === undefined) {
    throw new Error(msg ?? "Value is null or undefined");
  }
}
```

## The satisfies Operator (TypeScript 4.9+)

`satisfies` validates that an expression matches a type without widening it:

```typescript
type Color = "red" | "green" | "blue";
type ColorMap = Record<Color, string | number[]>;

const palette = {
  red: "#ff0000",       // keeps literal type
  green: [0, 255, 0],   // keeps tuple type
  blue: "#0000ff",
} satisfies ColorMap;

// Precise types preserved:
palette.red.toUpperCase();   // OK: string
palette.green.map(x => x);  // OK: number[]

// But validated against ColorMap:
const bad = {
  red: "#ff0000",
  green: [0, 255, 0],
  purple: "#800080", // Error: 'purple' not in Color
} satisfies ColorMap;
```

### satisfies vs Type Annotation

| Feature | `const x: Type = ...` | `const x = ... satisfies Type` |
|---------|----------------------|-------------------------------|
| Validation | Yes | Yes |
| Type widening | Widens to Type | Keeps literal/narrow type |
| Excess property check | Yes | Yes |
| Autocomplete at declaration | Yes | No (infers) |
| Autocomplete at usage | Based on Type | Based on inferred type |

Use `satisfies` when you want validation without losing the narrow inferred type.

## const Type Parameters (TypeScript 5.0+)

Add `const` modifier to a type parameter to infer literal types instead of widened types:

```typescript
function routes<const T extends readonly { path: string; method: string }[]>(
  config: T
): T {
  return config;
}

const r = routes([
  { path: "/users", method: "GET" },
  { path: "/users", method: "POST" },
]);
// r: readonly [{ path: "/users"; method: "GET" }, { path: "/users"; method: "POST" }]
// Without const: { path: string; method: string }[]
```

## Narrowing Best Practices

| Practice | Rationale |
|----------|-----------|
| Use discriminated unions over type guards | Compiler narrowing is more reliable than manual guards |
| Prefer `in` operator for structural checks | Works without casting |
| Use `satisfies` for config objects | Validates without widening |
| Use assertion functions for preconditions | Narrows for all subsequent code |
| Avoid `as` casts -- use guards instead | Casts bypass type checking |
| Test exhaustiveness with `never` | Catches missing cases at compile time |
| Use branded types for domain IDs | Prevents cross-entity confusion |
