# Common Errors and Performance Tuning

Sources: TypeScript compiler source (microsoft/TypeScript), Vanderkam (Effective TypeScript, 2nd ed., 2024), TypeScript GitHub Issues (recursive type limits, performance), Stack Overflow common patterns

Covers: common generic error messages with diagnosis and fix, recursive type depth limits, type-checking performance optimization, NoInfer usage, debugging strategies, and tsconfig flags that affect generics.

## Common Error Messages

### ts(2322): Type 'X' is not assignable to type 'Y'

The most frequent error with generics. Read the message from bottom to top -- the deepest line shows the actual constraint violation.

| Cause | Fix |
|-------|-----|
| Generic function returns wrong type | Check return type matches `T` or derived type |
| Missing property on generic | Add `extends` constraint to require the property |
| Literal type expected, got wider type | Use `as const` or `const` type parameter |
| Union member mismatch | Narrow with type guard before assignment |

```typescript
// Error: Type 'string' is not assignable to type 'T'
function make<T extends string>(): T {
  return "hello"; // Error: "hello" is string, not T
  // T could be "goodbye" -- "hello" is not assignable
}

// Fix: return the correct type
function make<T extends string>(value: T): T {
  return value; // OK: value IS T
}
```

### ts(2345): Argument of type 'X' is not assignable to parameter of type 'Y'

Passing wrong type to a generic function:

```typescript
function first<T>(arr: readonly T[]): T | undefined {
  return arr[0];
}

first("hello"); // Error: string not assignable to readonly T[]
first(["hello"]); // OK
```

### ts(2344): Type 'X' does not satisfy the constraint 'Y'

The type argument violates the generic constraint:

```typescript
function getLength<T extends { length: number }>(arg: T): number {
  return arg.length;
}

getLength(42); // Error: number does not satisfy { length: number }
getLength("hello"); // OK: string has .length
```

### ts(2536): Type 'X' cannot be used to index type 'Y'

Trying to access a property that may not exist on the generic type:

```typescript
// Error
type GetProp<T> = T["name"]; // Error: "name" cannot index T

// Fix 1: constrain T
type GetProp<T extends { name: unknown }> = T["name"];

// Fix 2: use conditional
type GetProp<T> = T extends { name: infer N } ? N : never;
```

### ts(2589): Type instantiation is excessively deep and possibly infinite

The type checker exceeded its recursion depth limit (~50 for conditional types, ~1000 for type aliases):

```typescript
// Triggers depth error with large inputs
type DeepFlatten<T> = T extends readonly (infer E)[]
  ? DeepFlatten<E>
  : T;

type Deep = DeepFlatten<number[][][][][][][][][][]>; // Error at depth ~50
```

#### Fixes for ts(2589)

| Strategy | How |
|----------|-----|
| Add explicit base case | Check for primitive before recursing |
| Limit recursion with counter | Accumulate in tuple, check length |
| Use iterative mapped type | Replace recursion with mapping |
| Break into smaller types | Named intermediate aliases |
| Add type annotations | Stop inference chains |

```typescript
// Tail-call pattern with accumulator (avoids depth issues)
type TupleOf<T, N extends number, R extends T[] = []> =
  R["length"] extends N ? R : TupleOf<T, N, [T, ...R]>;

type Five = TupleOf<string, 5>; // [string, string, string, string, string]
```

### ts(2590): Expression produces a union type that is too complex to represent

Union has too many members (typically > 100,000 from template literal expansion):

```typescript
// Error: cross product too large
type AllRoutes = `/${string}/${string}/${string}`; // Infinite
```

Fix: use `string` for the variable parts and validate at runtime, or constrain the unions.

### ts(7056): The inferred type of this node exceeds the maximum length the compiler will serialize

A type is too large to display in error messages or .d.ts output:

Fix: add explicit type annotations to break the inference chain.

## Generic Inference Debugging

### Strategy: Hover and Trace

1. Hover over the variable/expression in IDE to see inferred type
2. If type is `unknown` or `any` where specific type expected, the inference site is missing
3. Add explicit type argument temporarily to isolate the problem
4. Remove once root cause is fixed

### Strategy: Simplify and Isolate

1. Create a minimal reproduction (3-5 lines)
2. Remove constraints one at a time
3. Replace complex types with simple ones
4. Identify which specific part causes the error

### Strategy: Intermediate Type Aliases

```typescript
// Hard to debug: one giant expression
type Result = ComplexType<DeepGeneric<Input, Transform<Config>>>;

// Easier: named intermediates
type Step1 = Transform<Config>;
type Step2 = DeepGeneric<Input, Step1>;
type Result = ComplexType<Step2>;
// Now hover each step to find where it breaks
```

### The @ts-expect-error Technique

Use `@ts-expect-error` to verify that a type error IS expected:

```typescript
// Verify that wrong types ARE rejected
// @ts-expect-error: number should not be assignable to UserId
const bad: UserId = 42;

// If this line does NOT error, the @ts-expect-error itself errors
// signaling that your branded type is broken
```

## Performance Optimization

### Measuring Type-Checking Performance

```bash
# Generate trace for analysis
tsc --generateTrace ./trace-output

# Analyze with @anthropic/trace-viewer or chrome://tracing
# Look for: checkTypeRelatedTo, isTypeAssignableTo, getConditionalType
```

### Performance Impact by Feature

| Feature | Cost | When to Worry |
|---------|------|---------------|
| Simple generics | Low | Never |
| Mapped types | Low-Medium | Over 100 properties |
| Conditional types | Medium | Deep nesting (> 5 levels) |
| Recursive types | High | Depth > 10, wide unions |
| Template literal unions | High | Cross products > 1000 |
| Distributive conditionals | High | Union > 50 members |
| `infer` chains | Medium | Multiple infer in one conditional |

### Performance Best Practices

| Practice | Impact |
|----------|--------|
| Use type aliases to cache results | Prevents re-computation of same type |
| Prefer `interface` over `type` for object shapes | Interfaces are cached by name |
| Avoid unnecessary generic indirection | Each layer adds inference work |
| Constrain generics tightly | Fewer candidates to check |
| Use `NoInfer` to block unnecessary inference | Fewer inference sites = faster |
| Limit union sizes | Each member multiplies checks |
| Prefer iterative over recursive types | Lower depth = faster resolution |
| Add explicit annotations at boundaries | Stops inference chains early |

### interface vs type Performance

```typescript
// Preferred: interface (named, cached, extensible)
interface User {
  id: string;
  name: string;
}

// Avoid for object shapes: type alias (computed each time)
type User = {
  id: string;
  name: string;
};
```

Interfaces are stored by name and compared by identity first. Type aliases with mapped/conditional types are structurally expanded at each use site.

## NoInfer Deep Dive

`NoInfer<T>` (TypeScript 5.4+) blocks type inference from a specific parameter position:

### Problem It Solves

```typescript
// Without NoInfer: T inferred from both arguments
function filter<T>(items: T[], predicate: (item: T) => boolean): T[] {
  return items.filter(predicate);
}

// T inferred as string | number (unwanted widening)
filter(["a", "b"], (item) => typeof item === "number");
```

### With NoInfer

```typescript
function filter<T>(items: T[], predicate: (item: NoInfer<T>) => boolean): T[] {
  return items.filter(predicate);
}

// T inferred from items only: string
// predicate item parameter: string
filter(["a", "b"], (item) => item.length > 1); // OK
```

### When to Use NoInfer

| Situation | Use NoInfer |
|-----------|-------------|
| Default value parameter | Prevent default from widening T |
| Callback parameter | Infer T from primary data, not callbacks |
| Multiple parameters of type T | Control which parameter drives inference |
| Options object | Prevent options from influencing T |

## tsconfig Flags Affecting Generics

| Flag | Effect on Generics |
|------|-------------------|
| `strict: true` | Enables all strict checks below |
| `strictFunctionTypes` | Contravariant function params (not methods) |
| `strictNullChecks` | `T` does not include null/undefined implicitly |
| `noImplicitAny` | Requires explicit types when inference produces any |
| `exactOptionalPropertyTypes` | `T?` means `T \| undefined`, not `T \| undefined \| missing` |
| `noUncheckedIndexedAccess` | `T[K]` returns `T[K] \| undefined` for index signatures |
| `noPropertyAccessFromIndexSignature` | Must use bracket notation for index signatures |

Enable `strict: true` for all new projects. Each flag catches different classes of generic type errors.

## Debugging Checklist

| Step | Action |
|------|--------|
| 1 | Read error from bottom up |
| 2 | Hover to see inferred types |
| 3 | Add explicit type arguments temporarily |
| 4 | Create named intermediate aliases |
| 5 | Simplify to minimal reproduction |
| 6 | Check constraint satisfaction |
| 7 | Verify inference positions (parameter vs return) |
| 8 | Test with edge cases: never, unknown, any, union |
| 9 | Check if recursive type exceeds depth |
| 10 | Profile with --generateTrace if slow |
