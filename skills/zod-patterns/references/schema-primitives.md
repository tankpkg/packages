# Schema Primitives and Composition

Sources: Zod v4 official documentation (zod.dev), colinhacks/zod GitHub, TypeScript handbook

Covers: all primitive schema types, string formats, numbers, objects, arrays, enums, unions, discriminated unions, records, tuples, literals, dates, nullish handling, recursive schemas, and object composition methods.

## Primitive Types

```typescript
import * as z from "zod";

z.string();       // string
z.number();       // number (finite only, no NaN/Infinity)
z.bigint();       // bigint
z.boolean();      // boolean
z.symbol();       // symbol
z.undefined();    // undefined
z.null();         // null
z.void();         // equivalent to z.undefined()
z.any();          // any
z.unknown();      // unknown
z.never();        // never
z.nan();          // NaN specifically
```

## String Validation

### Built-in Validations

```typescript
z.string().min(1);              // non-empty
z.string().max(255);            // max length
z.string().length(10);          // exact length
z.string().regex(/^[a-z]+$/);   // pattern match
z.string().startsWith("https");
z.string().endsWith(".com");
z.string().includes("@");
z.string().uppercase();         // must be uppercase
z.string().lowercase();         // must be lowercase
```

### String Transforms

```typescript
z.string().trim();              // trim whitespace
z.string().toLowerCase();       // convert to lowercase
z.string().toUpperCase();       // convert to uppercase
z.string().normalize();         // unicode normalization
```

### String Formats (Zod 4 Top-Level)

Zod 4 promotes string formats to top-level functions for tree-shaking:

```typescript
z.email();                      // email validation (Gmail-style regex)
z.uuid();                       // any UUID version
z.uuidv4();                     // UUID v4 specifically
z.uuidv7();                     // UUID v7 specifically
z.url();                        // WHATWG URL
z.ipv4();                       // IPv4 address
z.ipv6();                       // IPv6 address
z.jwt();                        // JSON Web Token
z.emoji();                      // single emoji character
z.base64();                     // base64 string
z.base64url();                  // base64url string
z.hex();                        // hex string
z.nanoid();                     // nanoid
z.cuid();                       // cuid
z.cuid2();                      // cuid2
z.ulid();                       // ULID
z.cidrv4();                     // IPv4 CIDR block
z.cidrv6();                     // IPv6 CIDR block
z.iso.date();                   // YYYY-MM-DD
z.iso.time();                   // HH:MM[:SS[.s+]]
z.iso.datetime();               // ISO 8601 datetime
z.iso.duration();               // ISO 8601 duration
z.hash("sha256");               // cryptographic hash
```

### Custom Email Patterns

```typescript
z.email();                                    // default (Gmail-style)
z.email({ pattern: z.regexes.html5Email });   // browser input[type=email]
z.email({ pattern: z.regexes.rfc5322Email }); // RFC 5322
z.email({ pattern: z.regexes.unicodeEmail }); // intl emails
```

## Number Types

```typescript
z.number();                     // any finite number
z.number().min(0);              // >= 0 (alias: .gte(0))
z.number().max(100);            // <= 100 (alias: .lte(100))
z.number().positive();          // > 0
z.number().nonnegative();       // >= 0
z.number().negative();          // < 0
z.number().multipleOf(5);       // divisible by 5 (alias: .step(5))
z.number().int();               // integer (Zod 3 method)
z.number().finite();            // no Infinity

// Zod 4 fixed-width formats
z.int();                        // safe integer range
z.int32();                      // [-2147483648, 2147483647]
z.float32();                    // 32-bit float range
z.float64();                    // 64-bit float range
z.uint32();                     // [0, 4294967295]
z.int64();                      // bigint, 64-bit signed
z.uint64();                     // bigint, 64-bit unsigned
```

## Literals

```typescript
z.literal("admin");             // exact string
z.literal(42);                  // exact number
z.literal(true);                // exact boolean

// Zod 4: multiple literals in one call
z.literal([200, 201, 204]);     // 200 | 201 | 204
z.literal(["red", "green"]);    // "red" | "green"
```

## Enums

```typescript
// String enum (preferred)
const Role = z.enum(["admin", "user", "guest"]);
type Role = z.infer<typeof Role>; // "admin" | "user" | "guest"

Role.enum;                        // { admin: "admin", user: "user", guest: "guest" }
Role.exclude(["guest"]);          // "admin" | "user"
Role.extract(["admin"]);          // "admin"

// From const array
const roles = ["admin", "user", "guest"] as const;
const Role2 = z.enum(roles);

// Native enum (Zod 4 unified API)
enum Direction { Up = 0, Down = 1 }
const Dir = z.enum(Direction);    // validates 0 | 1

// Object literal enum
const Status = { Active: 1, Inactive: 0 } as const;
const StatusSchema = z.enum(Status);
```

## Objects

### Basic Object

```typescript
const User = z.object({
  name: z.string(),
  email: z.email(),
  age: z.number().optional(),
});
type User = z.infer<typeof User>;
// { name: string; email: string; age?: number }
```

### Strictness Levels

| Mode | Unknown Keys | Function |
|------|-------------|----------|
| Strip (default) | Silently removed | `z.object({...})` |
| Strict | Throw error | `z.strictObject({...})` |
| Passthrough | Kept in output | `z.looseObject({...})` |

### Catchall Schema

```typescript
const Config = z.object({
  name: z.string(),
}).catchall(z.string());
// { name: string; [key: string]: string }
```

### Object Composition

```typescript
const Base = z.object({ id: z.string(), createdAt: z.date() });

// Extend (add fields)
const User = Base.extend({ name: z.string(), email: z.email() });

// Spread syntax (preferred in Zod 4 for tsc performance)
const User2 = z.object({ ...Base.shape, name: z.string() });

// Pick specific fields
const UserName = User.pick({ name: true, email: true });

// Omit specific fields
const UserNoId = User.omit({ id: true });

// Make all fields optional
const PartialUser = User.partial();

// Make specific fields optional
const UpdateUser = User.partial({ name: true, email: true });

// Make all fields required
const RequiredUser = User.required();

// Safe extend (preserves refinements)
const Validated = Base.refine(d => d.id.length > 0);
const Extended = Validated.safeExtend({ name: z.string() });

// Keyof
const UserKeys = User.keyof(); // ZodEnum<["id", "createdAt", "name", "email"]>
```

## Arrays

```typescript
const Tags = z.array(z.string());
// or
const Tags2 = z.string().array();

Tags.min(1);                   // at least 1 element
Tags.max(10);                  // at most 10 elements
Tags.length(5);                // exactly 5 elements
Tags.nonempty();               // at least 1 (Zod 3)

// Access element schema
Tags.unwrap();                 // ZodString
```

## Tuples

```typescript
const Coord = z.tuple([z.number(), z.number()]);
type Coord = z.infer<typeof Coord>; // [number, number]

// Variadic (rest element)
const Row = z.tuple([z.string()], z.number());
// [string, ...number[]]
```

## Unions

```typescript
// Regular union (checks in order, returns first match)
const StringOrNumber = z.union([z.string(), z.number()]);

// Discriminated union (efficient lookup by discriminator key)
const Result = z.discriminatedUnion("status", [
  z.object({ status: z.literal("ok"), data: z.string() }),
  z.object({ status: z.literal("error"), message: z.string() }),
]);

// Exclusive union / XOR (exactly one must match)
const Payment = z.xor([
  z.object({ type: z.literal("card"), number: z.string() }),
  z.object({ type: z.literal("bank"), account: z.string() }),
]);

// Nested discriminated unions (Zod 4)
const Nested = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("a"), value: z.string() }),
  z.discriminatedUnion("subKind", [
    z.object({ kind: z.literal("b"), subKind: z.literal("b1") }),
    z.object({ kind: z.literal("b"), subKind: z.literal("b2") }),
  ]),
]);
```

## Records

```typescript
const Dict = z.record(z.string(), z.number());
// Record<string, number>

// Enum keys (exhaustive in Zod 4)
const Config = z.record(z.enum(["host", "port"]), z.string());
// { host: string; port: string }

// Partial record (non-exhaustive)
const PartialConfig = z.partialRecord(z.enum(["a", "b"]), z.string());
// { a?: string; b?: string }

// Loose record (pass through non-matching keys)
const Loose = z.looseRecord(z.string().regex(/_id$/), z.number());
```

## Nullish, Optional, Nullable

```typescript
z.string().optional();          // string | undefined
z.string().nullable();          // string | null
z.string().nullish();           // string | null | undefined

// Unwrap
z.string().optional().unwrap(); // ZodString

// Shorthand
z.optional(z.string());
z.nullable(z.string());
z.nullish(z.string());
```

## Dates

```typescript
z.date();                       // Date instance
z.date().min(new Date("2020-01-01"));
z.date().max(new Date());
```

## Recursive Schemas (Zod 4)

```typescript
const Category = z.object({
  name: z.string(),
  get children() {
    return z.array(Category);
  },
});
type Category = z.infer<typeof Category>;
// { name: string; children: Category[] }

// Mutually recursive
const User = z.object({
  name: z.string(),
  get posts() { return z.array(Post); },
});
const Post = z.object({
  title: z.string(),
  get author() { return User; },
});
```

All object methods (`.pick()`, `.omit()`, `.partial()`) work on recursive schemas.

### Circularity Errors

Add explicit return type annotations when TypeScript reports circularity:

```typescript
const Tree = z.object({
  value: z.number(),
  get children(): z.ZodArray<typeof Tree> {
    return z.array(Tree);
  },
});
```

## Template Literals (Zod 4)

```typescript
const CssValue = z.templateLiteral([z.number(), z.enum(["px", "em", "rem"])]);
// `${number}px` | `${number}em` | `${number}rem`

const Greeting = z.templateLiteral(["hello, ", z.string(), "!"]);
// `hello, ${string}!`
```

## File Schemas (Zod 4)

```typescript
z.file();
z.file().min(1024);             // min 1KB
z.file().max(5_000_000);        // max 5MB
z.file().mime(["image/png", "image/jpeg"]);
```

## Stringbool (Zod 4)

```typescript
const flag = z.stringbool();
flag.parse("true");             // => true
flag.parse("yes");              // => true
flag.parse("1");                // => true
flag.parse("false");            // => false
flag.parse("no");               // => false
flag.parse("0");                // => false

// Custom truthy/falsy
z.stringbool({ truthy: ["yes", "true"], falsy: ["no", "false"] });
```

## Intersections

Prefer `.extend()` or spread over intersections when possible — intersections return `ZodIntersection` which lacks object utility methods:

```typescript
const A = z.object({ name: z.string() });
const B = z.object({ age: z.number() });
const AB = z.intersection(A, B);
// { name: string } & { age: number }
```

## Schema Selection Quick Reference

| Data Shape | Schema |
|-----------|--------|
| Fixed set of strings | `z.enum([...])` |
| Exact value | `z.literal(value)` |
| String with format | `z.email()`, `z.uuid()`, `z.url()`, etc. |
| Object with known keys | `z.object({...})` |
| Object with dynamic keys | `z.record(keySchema, valueSchema)` |
| Homogeneous list | `z.array(schema)` |
| Fixed-length typed list | `z.tuple([...])` |
| One of several types | `z.union([...])` or `z.discriminatedUnion(...)` |
| Self-referencing data | Getter-based recursive schema |
| Binary/file upload | `z.file()` |
