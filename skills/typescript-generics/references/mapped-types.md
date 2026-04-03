# Mapped Types

Sources: TypeScript Handbook -- Mapped Types (typescriptlang.org, 2026), Vanderkam (Effective TypeScript, 2nd ed., 2024), Cherny (Programming TypeScript, 2019)

Covers: mapped type syntax, property iteration with `in keyof`, modifier removal and addition, key remapping with `as`, homomorphic mappings, and practical transformation patterns.

## Mapped Type Syntax

A mapped type iterates over a set of keys and produces a new type with transformed properties:

```typescript
type OptionsFlags<T> = {
  [Property in keyof T]: boolean;
};

interface Features {
  darkMode: () => void;
  notifications: () => void;
}

type FeatureOptions = OptionsFlags<Features>;
// { darkMode: boolean; notifications: boolean }
```

The syntax `[P in K]: V` reads as: "for each key P in the key set K, create a property with value type V."

### Key Sets

| Key Set | Source | Example |
|---------|--------|---------|
| `keyof T` | All keys of type T | `[K in keyof T]` |
| String union | Explicit set | `[K in "a" \| "b" \| "c"]` |
| `string` | Any string key | `[K in string]: V` (index signature) |
| `number` | Any numeric key | `[K in number]: V` |
| Template literal | Computed strings | `` [K in `on${string}`] `` |

## Modifier Removal and Addition

Mapped types can add or remove `readonly` and `?` modifiers using `+` and `-` prefixes:

### Removing readonly (Creating Mutable)

```typescript
type Mutable<T> = {
  -readonly [P in keyof T]: T[P];
};

interface Frozen {
  readonly id: string;
  readonly name: string;
}

type Thawed = Mutable<Frozen>;
// { id: string; name: string }
```

### Removing Optional (Making Required)

```typescript
type Concrete<T> = {
  [P in keyof T]-?: T[P];
};

interface Config {
  host?: string;
  port?: number;
  debug?: boolean;
}

type RequiredConfig = Concrete<Config>;
// { host: string; port: number; debug: boolean }
```

### Adding Modifiers

```typescript
// Make all properties readonly
type ReadonlyAll<T> = {
  +readonly [P in keyof T]: T[P];
};

// Make all properties optional
type OptionalAll<T> = {
  [P in keyof T]+?: T[P];
};
```

The `+` prefix is the default and can be omitted. Writing `readonly` without prefix is equivalent to `+readonly`.

### Modifier Summary Table

| Syntax | Effect |
|--------|--------|
| `readonly [P in keyof T]` | Add readonly |
| `-readonly [P in keyof T]` | Remove readonly |
| `[P in keyof T]?` | Add optional |
| `[P in keyof T]-?` | Remove optional |
| `-readonly [P in keyof T]-?` | Remove both modifiers |

## Key Remapping with as (TypeScript 4.1+)

Transform key names during mapping using an `as` clause:

```typescript
type Getters<T> = {
  [P in keyof T as `get${Capitalize<string & P>}`]: () => T[P];
};

interface Person {
  name: string;
  age: number;
}

type PersonGetters = Getters<Person>;
// { getName: () => string; getAge: () => number }
```

### Filtering Keys with as

Return `never` from the `as` clause to exclude a key:

```typescript
type RemoveKind<T> = {
  [P in keyof T as Exclude<P, "kind">]: T[P];
};

interface Shape {
  kind: "circle";
  radius: number;
}

type KindlessShape = RemoveKind<Shape>;
// { radius: number }
```

### Remapping with Arbitrary Unions

Map over any union, not just `keyof T`:

```typescript
type EventConfig<Events extends { kind: string }> = {
  [E in Events as E["kind"]]: (event: E) => void;
};

type SquareEvent = { kind: "square"; x: number; y: number };
type CircleEvent = { kind: "circle"; radius: number };

type Config = EventConfig<SquareEvent | CircleEvent>;
// { square: (event: SquareEvent) => void; circle: (event: CircleEvent) => void }
```

## Homomorphic Mapped Types

A mapped type is homomorphic when it maps over `keyof T` where `T` is a type parameter. Homomorphic mappings preserve modifiers from the original type:

```typescript
type Nullable<T> = {
  [P in keyof T]: T[P] | null;
};

interface User {
  readonly id: string;
  name?: string;
}

type NullableUser = Nullable<User>;
// { readonly id: string | null; name?: string | null }
// Note: readonly and optional are preserved
```

### Non-Homomorphic Mapped Types

When you map over an explicit key set (not `keyof T`), modifiers are not preserved:

```typescript
type Record<K extends keyof any, T> = {
  [P in K]: T;
};

// All properties are required and mutable regardless of source
type Dict = Record<"a" | "b", number>;
// { a: number; b: number }
```

### Homomorphic vs Non-Homomorphic

| Type | Homomorphic? | Preserves Modifiers? |
|------|-------------|---------------------|
| `{ [P in keyof T]: ... }` | Yes | Yes |
| `{ [P in K]: ... }` where K is not `keyof T` | No | No |
| `Partial<T>`, `Required<T>`, `Readonly<T>` | Yes | Yes (then modifies) |
| `Record<K, V>` | No | No |

## Indexed Access in Mapped Types

Use `T[P]` to access the original property type during mapping:

```typescript
// Transform all properties to getter functions
type Getterified<T> = {
  [P in keyof T]: () => T[P];
};

// Transform all properties to Promise
type Promisified<T> = {
  [P in keyof T]: Promise<T[P]>;
};

// Wrap each property in an array
type Arrayed<T> = {
  [P in keyof T]: T[P][];
};
```

## Combining Mapped Types with Conditional Types

Apply conditional logic per-property:

```typescript
// Make only function properties optional
type OptionalMethods<T> = {
  [P in keyof T as T[P] extends Function ? P : never]?: T[P];
} & {
  [P in keyof T as T[P] extends Function ? never : P]: T[P];
};
```

### Extract Properties by Value Type

```typescript
type PropertiesOfType<T, V> = {
  [P in keyof T as T[P] extends V ? P : never]: T[P];
};

interface Mixed {
  name: string;
  age: number;
  active: boolean;
  email: string;
}

type StringProps = PropertiesOfType<Mixed, string>;
// { name: string; email: string }
```

## Practical Mapped Type Recipes

### DeepPartial

Recursively make all properties optional:

```typescript
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object
    ? T[P] extends Function
      ? T[P]
      : DeepPartial<T[P]>
    : T[P];
};
```

### DeepReadonly

Recursively make all properties readonly:

```typescript
type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object
    ? T[P] extends Function
      ? T[P]
      : DeepReadonly<T[P]>
    : T[P];
};
```

### Rename Keys with Pattern

```typescript
type PrefixKeys<T, Prefix extends string> = {
  [P in keyof T as `${Prefix}${string & P}`]: T[P];
};

type Prefixed = PrefixKeys<{ name: string; age: number }, "user_">;
// { user_name: string; user_age: number }
```

### Convert Object to Union of Entries

```typescript
type Entries<T> = {
  [K in keyof T]: [K, T[K]];
}[keyof T];

type E = Entries<{ a: string; b: number }>;
// ["a", string] | ["b", number]
```

### Swap Keys and Values

```typescript
type Flip<T extends Record<string, string>> = {
  [K in keyof T as T[K]]: K;
};

type Original = { foo: "bar"; baz: "qux" };
type Flipped = Flip<Original>;
// { bar: "foo"; qux: "baz" }
```

## Implementing Built-in Utility Types

Understanding how built-in types work as mapped types:

```typescript
// Partial
type Partial<T> = { [P in keyof T]?: T[P] };

// Required
type Required<T> = { [P in keyof T]-?: T[P] };

// Readonly
type Readonly<T> = { readonly [P in keyof T]: T[P] };

// Pick
type Pick<T, K extends keyof T> = { [P in K]: T[P] };

// Record
type Record<K extends keyof any, T> = { [P in K]: T };
```

## Performance Considerations

| Situation | Impact | Mitigation |
|-----------|--------|------------|
| Deep recursive mapped types | Exponential type expansion | Limit depth, add base case |
| Large unions as key sets | Slow property generation | Keep union size under ~100 |
| Mapped type over intersection | Each member expanded separately | Simplify input type |
| Nested mapped types | Quadratic in key count | Flatten into single mapping |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Mapping over `any` | Produces `any` | Constrain input type |
| Nested mappings when one suffices | Performance cost | Combine into single pass |
| Forgetting `string &` before `P` in template literals | Symbol keys cause errors | Always intersect: `string & P` |
| Using mapped type when `Pick`/`Omit` works | Over-engineering | Use built-in utilities first |
| Recursive without function check | Functions become `DeepPartial<Function>` | Guard with `extends Function` |
