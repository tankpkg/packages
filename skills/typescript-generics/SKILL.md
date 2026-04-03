---
name: "@tank/typescript-generics"
description: |
  Advanced TypeScript generics and type-level programming for any codebase.
  Covers generic constraints (extends, keyof, conditional bounds), type
  inference (infer keyword, inference positions, NoInfer), conditional types
  (distributive behavior, never filtering), mapped types (key remapping,
  modifier removal, homomorphic mappings), template literal types (string
  manipulation, union expansion), utility types deep dive (Partial, Required,
  Pick, Omit, Record, Exclude, Extract, Parameters, ReturnType, Awaited),
  branded/opaque types, discriminated unions, type narrowing patterns (guards,
  assertions, satisfies), variance annotations (in/out), and real-world
  generic patterns (builder, factory, registry, type-safe event emitter,
  state machines). Includes common error diagnosis and performance tuning.

  Synthesizes TypeScript Handbook (typescriptlang.org), Effective TypeScript
  (Vanderkam, 2024), Programming TypeScript (Cherny, 2019), TypeScript
  compiler source (microsoft/TypeScript), and production library patterns
  (Zod, tRPC, Drizzle, TanStack).

  Trigger phrases: "typescript generics", "generic constraint", "conditional
  type", "mapped type", "template literal type", "infer keyword",
  "utility types", "branded type", "opaque type", "discriminated union",
  "type narrowing", "typescript variance", "type-safe builder",
  "typescript advanced types", "typescript type-level", "generic function",
  "Partial Required Pick Omit", "typescript design patterns",
  "type instantiation too deep", "typescript strict mode"
---

# TypeScript Generics

## Core Philosophy

1. **Generics are functions for types** -- A generic parameter is a type-level variable. Pass types in, get types out. Think of `<T>` as the same kind of abstraction as `(x)` in value-level code.
2. **Constrain early, infer often** -- Apply the tightest constraint that satisfies the use case via `extends`. Let TypeScript infer the rest. Explicit type arguments are a code smell when inference works.
3. **Prefer composition over recursion** -- Compose built-in utility types and simple conditionals. Recursive types hit the 50-depth limit and destroy IDE performance.
4. **Types should disappear at runtime** -- The best generic code compiles to the same JavaScript as hand-written code. If generics force runtime checks, redesign the type.
5. **Read the error from the bottom** -- TypeScript error messages for generics are deeply nested. The actual constraint violation is at the bottom of the stack.

## Quick-Start: Common Problems

### "I need a function that works on multiple types"

1. Add a type parameter: `function pick<T, K extends keyof T>(obj: T, keys: K[]): Pick<T, K>`
2. Constrain with `extends` -- use `keyof`, interfaces, or unions
3. Let inference fill in `T` from the call site argument
-> See `references/generics-fundamentals.md`

### "Which utility type do I need?"

| Goal | Utility |
|------|---------|
| Make all props optional | `Partial<T>` |
| Make all props required | `Required<T>` |
| Select subset of props | `Pick<T, K>` |
| Remove specific props | `Omit<T, K>` |
| Object from key-value union | `Record<K, V>` |
| Remove members from union | `Exclude<U, M>` |
| Keep members from union | `Extract<U, M>` |
| Function return type | `ReturnType<F>` |
| Function parameter types | `Parameters<F>` |
| Unwrap Promise | `Awaited<T>` |
-> See `references/utility-types.md`

### "My conditional type doesn't distribute correctly"

1. Wrap both sides in `[T] extends [U]` to disable distribution
2. Use `never` to filter union members: `T extends U ? T : never`
3. Remember: distribution only happens on naked type parameters
-> See `references/conditional-types.md`

### "Type instantiation is excessively deep"

1. Reduce recursive depth -- flatten with tail-call patterns or iterative mapped types
2. Add explicit type annotations at intermediate steps
3. Break complex types into smaller named aliases
4. Use `NoInfer<T>` (TS 5.4+) to block unwanted inference sites
-> See `references/errors-performance.md`

### "I want types that prevent invalid states"

1. Use discriminated unions with a literal `kind`/`type` tag
2. Add branded types for domain primitives (UserId, Email)
3. Model state machines as discriminated unions
-> See `references/branded-discriminated.md`

## Decision Trees

### Generic vs Overload vs Union

| Signal | Approach |
|--------|----------|
| Return type depends on input type | Generic |
| Few fixed input-output pairs | Overloads |
| Accept several types, same return | Union parameter |
| Need to relate multiple params | Generic with multiple type params |

### Mapped vs Conditional vs Template Literal

| Need | Type Feature |
|------|-------------|
| Transform every property of an object | Mapped type |
| Branch on a type condition | Conditional type |
| Build string types from parts | Template literal type |
| Extract inner type from wrapper | `infer` in conditional |
| Remap object keys | Mapped type with `as` clause |

### Constraint Strategy

| Scenario | Constraint |
|----------|-----------|
| Must have specific property | `T extends { prop: Type }` |
| Must be object key | `K extends keyof T` |
| Must be callable | `T extends (...args: any[]) => any` |
| Must be constructable | `T extends abstract new (...args: any[]) => any` |
| Must be a string subtype | `T extends string` |
| Array element type needed | `T extends readonly any[]` then `T[number]` |

## Reference Index

| File | Contents |
|------|----------|
| `references/generics-fundamentals.md` | Type parameters, constraints, defaults, inference, generic functions, classes, and interfaces |
| `references/conditional-types.md` | Conditional syntax, distributive behavior, `infer` keyword, `never` filtering, and non-distributive patterns |
| `references/mapped-types.md` | Property iteration, modifier removal (`-readonly`, `-?`), key remapping with `as`, homomorphic mappings |
| `references/template-literal-types.md` | String type construction, union expansion, intrinsic string types, event emitter patterns |
| `references/utility-types.md` | All built-in utility types with implementation, use cases, and composition patterns |
| `references/branded-discriminated.md` | Branded/opaque types, discriminated unions, type narrowing, type guards, assertions, `satisfies` |
| `references/variance-advanced.md` | Covariance, contravariance, `in`/`out` annotations, generic classes, higher-kinded type emulation |
| `references/real-world-patterns.md` | Builder pattern, factory, registry, type-safe event emitter, state machine, Zod/tRPC patterns |
| `references/errors-performance.md` | Common error messages, recursive type limits, performance tuning, `NoInfer`, debugging strategies |
