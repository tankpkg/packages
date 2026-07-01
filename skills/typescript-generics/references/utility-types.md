# Utility Types Deep Dive

Sources: TypeScript Handbook -- Utility Types (typescriptlang.org, 2026), Vanderkam (Effective TypeScript, 2nd ed., 2024), TypeScript lib.es5.d.ts source definitions

Covers: all built-in utility types with internal implementation, selection guide, composition patterns, and custom utility type construction.

## Object Transformation Utilities

### Partial<T>

Make all properties optional:

```typescript
// Implementation
type Partial<T> = { [P in keyof T]?: T[P] };

// Use: update functions, patch objects
function updateUser(id: string, fields: Partial<User>): User { /* ... */ }
updateUser("1", { name: "Bob" }); // Only update name
```

### Required<T>

Make all properties required (remove `?`):

```typescript
// Implementation
type Required<T> = { [P in keyof T]-?: T[P] };

// Use: enforce completeness after optional construction
interface Config {
  host?: string;
  port?: number;
}
function startServer(config: Required<Config>) { /* ... */ }
```

### Readonly<T>

Make all properties readonly:

```typescript
// Implementation
type Readonly<T> = { readonly [P in keyof T]: T[P] };

// Use: immutable snapshots, frozen objects
const state: Readonly<AppState> = getState();
state.count = 5; // Error: cannot assign to readonly
```

### Record<K, V>

Create an object type with keys K and values V:

```typescript
// Implementation
type Record<K extends keyof any, T> = { [P in K]: T };

// Use: dictionaries, lookup maps
type StatusMap = Record<"active" | "inactive" | "pending", number>;
// { active: number; inactive: number; pending: number }
```

`keyof any` resolves to `string | number | symbol` -- any valid property key.

## Property Selection Utilities

### Pick<T, K>

Select a subset of properties:

```typescript
// Implementation
type Pick<T, K extends keyof T> = { [P in K]: T[P] };

// Use: narrow an interface for specific contexts
type UserPreview = Pick<User, "id" | "name" | "avatar">;
```

### Omit<T, K>

Remove specific properties:

```typescript
// Implementation
type Omit<T, K extends keyof any> = Pick<T, Exclude<keyof T, K>>;

// Use: exclude internal fields
type PublicUser = Omit<User, "password" | "salt">;
```

Note: `Omit` accepts keys not in `T` without error. Use `Pick` for compile-time key validation.

### Pick vs Omit Decision

| Situation | Choose |
|-----------|--------|
| Need 1-3 properties from large interface | `Pick` |
| Need all but 1-3 properties | `Omit` |
| Keys must be validated against T | `Pick` (errors on invalid keys) |
| Keys may not exist on T | `Omit` (accepts any string) |

## Union Manipulation Utilities

### Exclude<T, U>

Remove union members assignable to U:

```typescript
// Implementation
type Exclude<T, U> = T extends U ? never : T;

// Use: filter union members
type NonBooleanPrimitive = Exclude<string | number | boolean, boolean>;
// string | number
```

### Extract<T, U>

Keep union members assignable to U:

```typescript
// Implementation
type Extract<T, U> = T extends U ? T : never;

// Use: select specific union members
type NumericLike = Extract<string | number | bigint, number | bigint>;
// number | bigint
```

### NonNullable<T>

Remove null and undefined:

```typescript
// Implementation
type NonNullable<T> = T & {};
// Simplified from: T extends null | undefined ? never : T

// Use: assert value is defined
type DefiniteString = NonNullable<string | null | undefined>;
// string
```

## Function Utilities

### ReturnType<T>

Extract function return type:

```typescript
// Implementation
type ReturnType<T extends (...args: any) => any> =
  T extends (...args: any) => infer R ? R : any;

// Use: derive types from existing functions
function fetchUser() { return { id: "1", name: "Alice" }; }
type User = ReturnType<typeof fetchUser>;
// { id: string; name: string }
```

### Parameters<T>

Extract function parameter types as a tuple:

```typescript
// Implementation
type Parameters<T extends (...args: any) => any> =
  T extends (...args: infer P) => any ? P : never;

// Use: forward arguments with type safety
function log(...args: Parameters<typeof console.log>) {
  console.log("[APP]", ...args);
}
```

### ConstructorParameters<T>

Extract constructor parameter types:

```typescript
// Implementation
type ConstructorParameters<T extends abstract new (...args: any) => any> =
  T extends abstract new (...args: infer P) => any ? P : never;

// Use: factory functions
type DateArgs = ConstructorParameters<typeof Date>;
// [value: string | number | Date]
```

### InstanceType<T>

Extract the instance type from a constructor:

```typescript
// Implementation
type InstanceType<T extends abstract new (...args: any) => any> =
  T extends abstract new (...args: any) => infer R ? R : any;

// Use: when you have class reference not instance
function create<T extends new (...args: any[]) => any>(
  Ctor: T
): InstanceType<T> {
  return new Ctor();
}
```

## Async Utilities

### Awaited<T>

Recursively unwrap Promise types:

```typescript
// Simplified implementation
type Awaited<T> = T extends Promise<infer U> ? Awaited<U> : T;

// Use: derive the resolved type of async operations
type UserData = Awaited<ReturnType<typeof fetchUser>>;
// If fetchUser returns Promise<User>, UserData = User
```

Handles nested promises: `Awaited<Promise<Promise<string>>>` = `string`.

## Inference Control

### NoInfer<T> (TypeScript 5.4+)

Block inference from a specific position without changing the type:

```typescript
// Implementation (compiler intrinsic)
// Prevents T from being inferred at this position

function createStreetLight<C extends string>(
  colors: C[],
  defaultColor?: NoInfer<C>
) { /* ... */ }

createStreetLight(["red", "yellow", "green"], "red");   // OK
createStreetLight(["red", "yellow", "green"], "blue");  // Error
// Without NoInfer, "blue" would widen C to include it
```

## this Utilities

### ThisParameterType<T>

Extract the `this` parameter type from a function:

```typescript
function greet(this: { name: string }) {
  return `Hello, ${this.name}`;
}
type GreetThis = ThisParameterType<typeof greet>;
// { name: string }
```

### OmitThisParameter<T>

Remove the `this` parameter to get a bindable function type:

```typescript
type BoundGreet = OmitThisParameter<typeof greet>;
// () => string

const bound: BoundGreet = greet.bind({ name: "Alice" });
```

### ThisType<T>

Marker interface for contextual `this` typing in object literals:

```typescript
type ObjectDescriptor<D, M> = {
  data?: D;
  methods?: M & ThisType<D & M>;
};

function makeObject<D, M>(desc: ObjectDescriptor<D, M>): D & M {
  return { ...desc.data, ...desc.methods } as D & M;
}

const obj = makeObject({
  data: { x: 0, y: 0 },
  methods: {
    moveBy(dx: number, dy: number) {
      this.x += dx; // this: { x: number; y: number; moveBy(...): void }
      this.y += dy;
    },
  },
});
```

Requires `noImplicitThis` compiler option.

## Utility Type Composition Patterns

### Composing Built-in Types

```typescript
// Pick + Partial: make specific fields optional
type OptionalPick<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Omit + Required: make specific fields required
type RequiredOmit<T, K extends keyof T> = Required<Pick<T, K>> & Omit<T, K>;

// Readonly subset
type ReadonlyPick<T, K extends keyof T> = Readonly<Pick<T, K>> & Omit<T, K>;
```

### Create Input Type

```typescript
// Common pattern: "create" type = full type minus auto-generated fields
type CreateInput<T, AutoFields extends keyof T = "id" | "createdAt" | "updatedAt"> =
  Omit<T, AutoFields>;

interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
  updatedAt: Date;
}

type CreateUserInput = CreateInput<User>;
// { name: string; email: string }
```

### Update Input Type

```typescript
// Update = partial of non-generated fields + required id
type UpdateInput<T, IdField extends keyof T = "id"> =
  Pick<T, IdField> & Partial<Omit<T, IdField>>;

type UpdateUserInput = UpdateInput<User>;
// { id: string; name?: string; email?: string; createdAt?: Date; updatedAt?: Date }
```

## Utility Type Selection Guide

| Task | Utility | Notes |
|------|---------|-------|
| Make all optional | `Partial<T>` | Shallow only |
| Make all required | `Required<T>` | Shallow only |
| Make all readonly | `Readonly<T>` | Shallow only |
| Select properties | `Pick<T, K>` | Validates keys |
| Remove properties | `Omit<T, K>` | Does not validate keys |
| Dictionary type | `Record<K, V>` | Keys must be string/number/symbol |
| Filter union | `Exclude<T, U>` / `Extract<T, U>` | Distributive |
| Remove null/undefined | `NonNullable<T>` | |
| Function return | `ReturnType<T>` | Last overload only |
| Function params | `Parameters<T>` | Returns tuple |
| Unwrap Promise | `Awaited<T>` | Recursive unwrap |
| Constructor instance | `InstanceType<T>` | Needs `typeof Class` |
| Block inference | `NoInfer<T>` | TS 5.4+ |

## Custom Utility Types Worth Having

```typescript
// Deep versions
type DeepPartial<T> = { [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P] };
type DeepReadonly<T> = { readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P] };

// Make specific keys required
type RequireKeys<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Mutable (remove readonly)
type Mutable<T> = { -readonly [P in keyof T]: T[P] };

// Strict Omit (validates keys exist)
type StrictOmit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;

// Union to Intersection
type UnionToIntersection<U> = (U extends any ? (x: U) => void : never) extends (x: infer I) => void ? I : never;

// Value types of an object
type ValueOf<T> = T[keyof T];
```
