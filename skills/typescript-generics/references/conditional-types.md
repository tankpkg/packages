# Conditional Types

Sources: TypeScript Handbook -- Conditional Types (typescriptlang.org, 2026), Vanderkam (Effective TypeScript, 2nd ed., 2024), TypeScript compiler source (microsoft/TypeScript)

Covers: conditional type syntax, distributive behavior, the `infer` keyword, `never` filtering, non-distributive patterns, and building custom type-level logic.

## Conditional Type Syntax

A conditional type selects one of two branches based on an `extends` check:

```typescript
type IsString<T> = T extends string ? true : false;

type A = IsString<"hello">; // true
type B = IsString<42>;      // false
```

The form is: `T extends U ? TrueType : FalseType`. Read as: "if T is assignable to U, resolve to TrueType; otherwise FalseType."

### extends as Subtype Check

In conditional types, `extends` means "is assignable to" -- not class inheritance. Think of it as a subset relationship:

| Check | Result | Reasoning |
|-------|--------|-----------|
| `string extends string` | true | Same type |
| `"hello" extends string` | true | Literal is subtype of string |
| `string extends "hello"` | false | String is not subtype of literal |
| `never extends string` | true | never is subtype of everything |
| `string extends unknown` | true | Everything extends unknown |
| `unknown extends string` | false | unknown is not subtype of string |
| `any extends string` | true AND false | any is special -- resolves to union of both branches |

## Distributive Conditional Types

When a conditional type acts on a naked type parameter (not wrapped in a tuple/array), it distributes over union members:

```typescript
type ToArray<T> = T extends any ? T[] : never;

// Distributes over each union member
type Result = ToArray<string | number>;
// = (string extends any ? string[] : never) | (number extends any ? number[] : never)
// = string[] | number[]
```

### Distribution Rules

| Condition | Distributes? |
|-----------|-------------|
| Naked type parameter: `T extends U` | Yes |
| Wrapped in tuple: `[T] extends [U]` | No |
| Wrapped in array: `T[] extends U[]` | No |
| Concrete type: `string extends U` | No |
| Intersection: `T & string extends U` | No |

### Disabling Distribution

Wrap both sides of `extends` in square brackets to prevent distribution:

```typescript
type ToArrayNonDist<T> = [T] extends [any] ? T[] : never;

type Result = ToArrayNonDist<string | number>;
// = (string | number)[] -- single array, not distributed
```

This is critical when you want to check the entire union as a unit rather than each member individually.

### Distribution with never

`never` is the empty union. Distributing over it produces nothing:

```typescript
type Check<T> = T extends string ? T : never;

type Result = Check<never>;
// Distributes over 0 members = never
```

This is why `Exclude<T, U>` works -- members that match `U` become `never` and vanish from the union.

## The infer Keyword

`infer` declares a type variable inside the true branch of a conditional type. It captures a portion of the type being checked:

```typescript
type GetReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

type A = GetReturnType<() => string>;    // string
type B = GetReturnType<(x: number) => boolean>; // boolean
type C = GetReturnType<string>;          // never (not a function)
```

### infer Positions

`infer` can capture types from any structural position:

```typescript
// Extract element type from array
type ElementOf<T> = T extends readonly (infer E)[] ? E : never;
type A = ElementOf<string[]>; // string

// Extract Promise inner type
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;
type B = UnwrapPromise<Promise<number>>; // number

// Extract first argument of function
type FirstArg<T> = T extends (first: infer F, ...rest: any[]) => any ? F : never;
type C = FirstArg<(a: string, b: number) => void>; // string

// Extract value type from Map
type MapValue<T> = T extends Map<any, infer V> ? V : never;
type D = MapValue<Map<string, Date>>; // Date
```

### Multiple infer in One Conditional

Extract multiple parts simultaneously:

```typescript
type FunctionParts<T> = T extends (...args: infer A) => infer R
  ? { args: A; return: R }
  : never;

type Parts = FunctionParts<(a: string, b: number) => boolean>;
// { args: [a: string, b: number]; return: boolean }
```

### infer with Constraints (TypeScript 4.7+)

Constrain the inferred type directly:

```typescript
type FirstString<T> = T extends [infer S extends string, ...unknown[]] ? S : never;

type A = FirstString<["hello", 42]>;  // "hello"
type B = FirstString<[42, "hello"]>;  // never (first element is not string)
```

## never Filtering Pattern

Use conditional types to filter union members. Members that fail the check become `never` and disappear:

```typescript
// Keep only string members
type OnlyStrings<T> = T extends string ? T : never;

type Result = OnlyStrings<"a" | 42 | "b" | true>;
// = "a" | "b"
```

### Reimplementing Built-in Utility Types

```typescript
// Exclude: remove members assignable to U
type MyExclude<T, U> = T extends U ? never : T;

// Extract: keep members assignable to U
type MyExtract<T, U> = T extends U ? T : never;

// NonNullable: remove null and undefined
type MyNonNullable<T> = T extends null | undefined ? never : T;
```

## Conditional Type Constraints

The true branch of a conditional narrows the type parameter:

```typescript
type MessageOf<T> = T extends { message: unknown } ? T["message"] : never;

// In the true branch, TypeScript knows T has a message property
type A = MessageOf<{ message: string }>; // string
type B = MessageOf<number>;              // never
```

This is structurally equivalent to adding a constraint, but more flexible because the false branch handles non-matching types gracefully.

## Nested Conditionals

Chain conditionals for multi-branch logic:

```typescript
type TypeName<T> =
  T extends string ? "string" :
  T extends number ? "number" :
  T extends boolean ? "boolean" :
  T extends undefined ? "undefined" :
  T extends Function ? "function" :
  "object";

type A = TypeName<string>;    // "string"
type B = TypeName<() => void>; // "function"
type C = TypeName<Date>;      // "object"
```

### Avoid Deep Nesting

Deeply nested conditionals hurt readability and performance. Break them apart:

```typescript
// Prefer: separate named types
type IsString<T> = T extends string ? true : false;
type IsNumber<T> = T extends number ? true : false;

// Over: deeply nested inline conditional
type DeepCheck<T> = T extends string
  ? T extends `${infer _}:${infer _}` ? "pair" : "simple"
  : T extends number ? "numeric" : "other";
```

## Recursive Conditional Types

Conditional types can reference themselves for recursive unwrapping:

```typescript
type DeepAwaited<T> = T extends Promise<infer U> ? DeepAwaited<U> : T;

type A = DeepAwaited<Promise<Promise<Promise<string>>>>; // string
```

### Recursion Limits

TypeScript enforces a depth limit (~50 levels for conditional types, ~1000 for type aliases). Exceeding it produces:

```
Type instantiation is excessively deep and possibly infinite. ts(2589)
```

Strategies for staying within limits:
- Use iterative mapped types instead of recursive conditionals where possible
- Add explicit intermediate type aliases
- Use tail-call-like patterns (accumulator in a tuple)
- Limit union sizes that feed into recursive types

## Practical Conditional Type Recipes

### Flatten Array Type

```typescript
type Flatten<T> = T extends readonly (infer E)[] ? E : T;

type A = Flatten<string[]>;   // string
type B = Flatten<number>;     // number (pass-through)
```

### Make Specific Properties Optional

```typescript
type OptionalPick<T, K extends keyof T> =
  Omit<T, K> & Partial<Pick<T, K>>;

interface User {
  id: string;
  name: string;
  email: string;
}

type CreateUserInput = OptionalPick<User, "id">;
// { name: string; email: string; id?: string }
```

### Extract Literal Type from Discriminated Union

```typescript
type ExtractByKind<T, K> = T extends { kind: K } ? T : never;

type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "square"; side: number };

type Circle = ExtractByKind<Shape, "circle">;
// { kind: "circle"; radius: number }
```

## Conditional Types with Overloaded Functions

When `infer` encounters overloaded function types, it uses the last overload signature. This is because the last overload is typically the most general catch-all:

```typescript
declare function fn(x: string): number;
declare function fn(x: number): string;
declare function fn(x: string | number): string | number;

type R = ReturnType<typeof fn>; // string | number (from last signature)
```

This behavior cannot be overridden. Design overloaded function types with the most general signature last.

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Using `any` in conditional check | `T extends any` always true | Use `unknown` or specific type |
| Expecting distribution on wrapped params | `T[]` does not distribute | Use naked `T` |
| Recursive types without base case | Infinite recursion | Add termination condition |
| Complex nested ternaries | Unreadable, slow | Break into named aliases |
| Using conditional when mapped suffices | Over-engineering | Use `{ [K in keyof T]: ... }` |
