# Template Literal Types

Sources: TypeScript Handbook -- Template Literal Types (typescriptlang.org, 2026), Vanderkam (Effective TypeScript, 2nd ed., 2024), TypeScript 4.1-4.7 Release Notes (microsoft/TypeScript)

Covers: string type construction, union expansion, intrinsic string manipulation types, pattern matching with infer, event emitter typing, and route/path parameter extraction.

## Template Literal Syntax

Template literal types use backtick syntax to construct string types from other string literal types:

```typescript
type World = "world";
type Greeting = `hello ${World}`; // "hello world"
```

Interpolated positions accept any type that can be represented as a string: `string`, `number`, `bigint`, `boolean`, `null`, `undefined`, and unions of these.

## Union Expansion

When a union is used in an interpolated position, the result is the cross product of all combinations:

```typescript
type Color = "red" | "blue";
type Size = "sm" | "lg";
type ColorSize = `${Color}-${Size}`;
// "red-sm" | "red-lg" | "blue-sm" | "blue-lg"
```

Multiple interpolation positions multiply:

```typescript
type A = "a" | "b";      // 2 members
type B = "1" | "2" | "3"; // 3 members
type AB = `${A}${B}`;     // 6 members: "a1" | "a2" | "a3" | "b1" | "b2" | "b3"
```

### Expansion Limits

Large unions produce exponentially large result types. TypeScript limits template literal types to ~100,000 members. Keep source unions small or generate ahead-of-time.

## Intrinsic String Manipulation Types

TypeScript provides four built-in types for string case manipulation:

| Type | Effect | Example |
|------|--------|---------|
| `Uppercase<S>` | All uppercase | `Uppercase<"hello">` = `"HELLO"` |
| `Lowercase<S>` | All lowercase | `Lowercase<"HELLO">` = `"hello"` |
| `Capitalize<S>` | First char uppercase | `Capitalize<"hello">` = `"Hello"` |
| `Uncapitalize<S>` | First char lowercase | `Uncapitalize<"Hello">` = `"hello"` |

These are compiler intrinsics -- they use JavaScript's runtime string methods at the type level. They are not locale-aware.

### Combining Intrinsic Types

```typescript
type ScreamingSnake<S extends string> = Uppercase<S>;
type CamelToKebab<S extends string> = S extends `${infer Head}${infer Tail}`
  ? Tail extends Uncapitalize<Tail>
    ? `${Lowercase<Head>}${CamelToKebab<Tail>}`
    : `${Lowercase<Head>}-${CamelToKebab<Tail>}`
  : S;

type Result = CamelToKebab<"backgroundColor">; // "background-color"
```

## Pattern Matching with infer

Use template literals with conditional types and `infer` to parse string types:

```typescript
// Extract parts from a dot-separated path
type Split<S extends string, D extends string> =
  S extends `${infer Head}${D}${infer Tail}`
    ? [Head, ...Split<Tail, D>]
    : [S];

type Parts = Split<"a.b.c", ".">; // ["a", "b", "c"]
```

### Common Pattern Matching Recipes

#### Extract Route Parameters

```typescript
type ExtractParams<T extends string> =
  T extends `${string}:${infer Param}/${infer Rest}`
    ? Param | ExtractParams<`/${Rest}`>
    : T extends `${string}:${infer Param}`
      ? Param
      : never;

type Params = ExtractParams<"/users/:userId/posts/:postId">;
// "userId" | "postId"
```

#### Parse Key-Value Pairs

```typescript
type ParsePair<S extends string> =
  S extends `${infer Key}=${infer Value}` ? { key: Key; value: Value } : never;

type Pair = ParsePair<"name=Alice">; // { key: "name"; value: "Alice" }
```

#### Trim Whitespace

```typescript
type TrimLeft<S extends string> =
  S extends ` ${infer Rest}` ? TrimLeft<Rest> : S;

type TrimRight<S extends string> =
  S extends `${infer Rest} ` ? TrimRight<Rest> : S;

type Trim<S extends string> = TrimLeft<TrimRight<S>>;

type Trimmed = Trim<"  hello  ">; // "hello"
```

## Type-Safe Event Emitter Pattern

Template literals enable type-safe event systems where event names derive from object properties:

```typescript
type PropEventSource<T> = {
  on<K extends string & keyof T>(
    eventName: `${K}Changed`,
    callback: (newValue: T[K]) => void
  ): void;
};

declare function makeWatchable<T>(obj: T): T & PropEventSource<T>;

const person = makeWatchable({ name: "Alice", age: 30 });

// Type-safe: callback receives string
person.on("nameChanged", (newName) => {
  console.log(newName.toUpperCase()); // OK: newName is string
});

// Type-safe: callback receives number
person.on("ageChanged", (newAge) => {
  console.log(newAge.toFixed(2)); // OK: newAge is number
});

// Error: "emailChanged" is not valid
person.on("emailChanged", () => {}); // Error
```

### Key Insight

The generic method `on<K>` captures the literal event name. TypeScript:
1. Matches `"nameChanged"` against the pattern `` `${K}Changed` ``
2. Infers `K = "name"`
3. Looks up `T["name"]` to type the callback argument as `string`

## CSS-Style Property Typing

```typescript
type CSSProperty = "margin" | "padding" | "border";
type CSSDirection = "top" | "right" | "bottom" | "left";
type CSSUnit = "px" | "rem" | "em" | "%";

type CSSDirectionalProp = `${CSSProperty}-${CSSDirection}`;
// "margin-top" | "margin-right" | ... (12 combinations)

type CSSValue = `${number}${CSSUnit}`;
// `${number}px` | `${number}rem` | `${number}em` | `${number}%`
```

## HTTP Method Typing

```typescript
type HTTPMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

type APIRoute<M extends HTTPMethod, P extends string> = `${M} ${P}`;

type Routes =
  | APIRoute<"GET", "/users">
  | APIRoute<"POST", "/users">
  | APIRoute<"GET", "/users/:id">
  | APIRoute<"DELETE", "/users/:id">;
```

## Combining Template Literals with Mapped Types

Generate getter/setter interfaces from property names:

```typescript
type Accessors<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
} & {
  [K in keyof T as `set${Capitalize<string & K>}`]: (value: T[K]) => void;
};

interface State {
  count: number;
  name: string;
}

type StateAccessors = Accessors<State>;
// {
//   getCount: () => number;
//   getName: () => string;
//   setCount: (value: number) => void;
//   setName: (value: string) => void;
// }
```

## SQL-Style Type-Safe Queries

```typescript
type Table = "users" | "posts" | "comments";
type SelectQuery = `SELECT * FROM ${Table}`;
type JoinQuery = `SELECT * FROM ${Table} JOIN ${Table} ON ${string}`;

// Only valid table names accepted
function query(sql: SelectQuery): void { /* ... */ }

query("SELECT * FROM users");   // OK
query("SELECT * FROM animals"); // Error
```

## Recursive String Manipulation

### Replace All Occurrences

```typescript
type ReplaceAll<
  S extends string,
  From extends string,
  To extends string
> = From extends ""
  ? S
  : S extends `${infer Before}${From}${infer After}`
    ? `${Before}${To}${ReplaceAll<After, From, To>}`
    : S;

type Result = ReplaceAll<"hello-world-foo", "-", "_">;
// "hello_world_foo"
```

### Join Tuple to String

```typescript
type Join<T extends readonly string[], D extends string> =
  T extends readonly [infer F extends string, ...infer R extends string[]]
    ? R["length"] extends 0
      ? F
      : `${F}${D}${Join<R, D>}`
    : "";

type Path = Join<["users", "123", "posts"], "/">;
// "users/123/posts"
```

## Performance and Limits

| Factor | Limit | Guidance |
|--------|-------|---------|
| Cross-product expansion | ~100,000 members | Keep source unions under ~50 members each |
| Recursive depth | ~50 levels | Add explicit base cases early |
| Template literal inference | Greedy left-to-right | Structure patterns to avoid ambiguity |
| String length | No hard limit | Practical limit from union expansion |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Huge union in interpolation | Exponential type expansion, slow IDE | Pre-compute or use `string` |
| Deeply recursive string parsing | Hits depth limit | Use iterative approach or limit input |
| Template literal where simple union works | Over-engineering | Use explicit union for small fixed sets |
| Forgetting `string &` in mapped key | Symbols cause error | `[K in keyof T as \`get${Capitalize<string & K>}\`]` |
| Using template literals for runtime validation | Types erased at runtime | Add runtime checks separately |
