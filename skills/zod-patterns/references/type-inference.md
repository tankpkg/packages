# Type Inference, Branded Types, and Zod 4 Features

Sources: Zod v4 official documentation (zod.dev), colinhacks/zod GitHub, TypeScript handbook

Covers: z.infer, z.input, z.output, branded types, readonly schemas, JSON Schema conversion, metadata registries, Zod Mini, and Zod 4 architecture.

## Type Inference

### z.infer — Extract Output Type

```typescript
import * as z from "zod";

const User = z.object({
  name: z.string(),
  email: z.email(),
  age: z.number().optional(),
});

type User = z.infer<typeof User>;
// { name: string; email: string; age?: number }
```

The `z.infer<>` utility extracts the output type — the type returned by `.parse()` or `.safeParse()`.

### z.input vs z.output

When transforms are involved, input and output types diverge:

```typescript
const StringToNum = z.string().transform((s) => s.length);

type In = z.input<typeof StringToNum>;   // string
type Out = z.output<typeof StringToNum>; // number

// z.infer is an alias for z.output
type Same = z.infer<typeof StringToNum>; // number
```

### When to Use Each

| Utility | Use Case |
|---------|----------|
| `z.infer<typeof S>` | Function return types, component props, DB row types |
| `z.input<typeof S>` | Form data types, API request body types, raw input |
| `z.output<typeof S>` | Identical to `z.infer` — validated + transformed data |

### Pattern: Schema as Single Source of Truth

Define the schema once, derive all types from it:

```typescript
// Schema is the source of truth
const CreateUserInput = z.object({
  name: z.string().min(1).max(100),
  email: z.email(),
  role: z.enum(["admin", "user"]),
});

// Derive types from schema
type CreateUserInput = z.infer<typeof CreateUserInput>;

// Use derived type in functions
function createUser(input: CreateUserInput): Promise<User> {
  // input is fully typed
  return db.users.create(input);
}

// Use schema for runtime validation
const validated = CreateUserInput.parse(requestBody);
```

Never manually define a TypeScript interface and a Zod schema separately — they will drift apart.

### Extracting Object Shape Type

```typescript
const User = z.object({ name: z.string(), age: z.number() });

// Access shape for composition
User.shape.name; // ZodString
User.shape.age;  // ZodNumber

// Keyof
type UserKeys = keyof z.infer<typeof User>; // "name" | "age"
```

## Branded Types

Branded types prevent mixing structurally identical but semantically different types. Zod's `.brand()` adds a unique phantom type tag.

### Why Brand?

```typescript
// Without branding: these are interchangeable (unsafe)
type UserId = string;
type PostId = string;

function getUser(id: UserId) { /* ... */ }
const postId: PostId = "post-123";
getUser(postId); // TypeScript allows this — bug!
```

### Creating Branded Types

```typescript
const UserId = z.string().uuid().brand<"UserId">();
const PostId = z.string().uuid().brand<"PostId">();

type UserId = z.infer<typeof UserId>; // string & { __brand: "UserId" }
type PostId = z.infer<typeof PostId>; // string & { __brand: "PostId" }

function getUser(id: UserId) { /* ... */ }

const userId = UserId.parse("550e8400-e29b-41d4-a716-446655440000");
const postId = PostId.parse("660e8400-e29b-41d4-a716-446655440000");

getUser(userId); // works
getUser(postId); // TypeScript error: PostId is not assignable to UserId
```

### Branded Type Patterns

| Pattern | Use Case |
|---------|----------|
| `z.string().uuid().brand<"UserId">()` | Entity IDs |
| `z.string().email().brand<"Email">()` | Validated email addresses |
| `z.number().positive().brand<"PositiveInt">()` | Domain constraints |
| `z.string().min(1).brand<"NonEmpty">()` | Non-empty strings |

### Branding Does Not Affect Runtime

`.brand()` only adds a compile-time tag. At runtime, the value is still a plain string/number. The brand is erased — it is purely a TypeScript feature.

## Readonly Schemas

```typescript
const Config = z.object({
  host: z.string(),
  port: z.number(),
}).readonly();

type Config = z.infer<typeof Config>;
// { readonly host: string; readonly port: number }

const config = Config.parse({ host: "localhost", port: 3000 });
config.host = "other"; // TypeScript error: readonly
```

Arrays can also be made readonly:

```typescript
const Tags = z.array(z.string()).readonly();
type Tags = z.infer<typeof Tags>; // readonly string[]
```

## Metadata and Registries (Zod 4)

Zod 4 introduces typed metadata registries — a way to attach metadata to schemas without polluting the schema itself.

### Custom Registry

```typescript
const myRegistry = z.registry<{ title: string; description: string }>();

const emailSchema = z.email();
myRegistry.add(emailSchema, {
  title: "Email",
  description: "User's email address",
});

myRegistry.get(emailSchema);
// => { title: "Email", description: "User's email address" }
```

### Global Registry

```typescript
z.globalRegistry.add(z.string(), {
  id: "user_name",
  title: "Username",
  description: "The user's display name",
  examples: ["alice", "bob"],
});
```

### .meta() Shorthand

```typescript
const Name = z.string().meta({
  id: "user_name",
  title: "Username",
  description: "Display name",
  examples: ["alice"],
});

// .describe() is still available (adds to globalRegistry)
const Email = z.email().describe("User's email address");
```

## JSON Schema Conversion (Zod 4)

Zod 4 provides first-party JSON Schema conversion:

```typescript
const UserSchema = z.object({
  name: z.string().describe("User's name"),
  email: z.email().meta({ title: "email_address" }),
  age: z.number().int().min(0).max(150),
});

const jsonSchema = z.toJSONSchema(UserSchema);
// {
//   type: "object",
//   properties: {
//     name: { type: "string", description: "User's name" },
//     email: { type: "string", format: "email", title: "email_address" },
//     age: { type: "integer", minimum: 0, maximum: 150 },
//   },
//   required: ["name", "email", "age"],
// }
```

Metadata from `z.globalRegistry` (via `.meta()` or `.describe()`) is automatically included in JSON Schema output.

### JSON Schema Use Cases

| Use Case | Pattern |
|----------|---------|
| OpenAPI spec generation | `z.toJSONSchema()` on request/response schemas |
| AI/LLM structured output | JSON Schema as function parameter definition |
| Form generation | Derive form fields from JSON Schema |
| Documentation | Auto-generate API docs from schemas |

## Zod Mini

Zod Mini is a tree-shakable variant with a functional API. Same validation engine, smaller bundle.

### Bundle Size Comparison

| Package | Core Bundle (gzip) |
|---------|-------------------|
| Zod 3 | 12.47kb |
| Zod 4 | 5.36kb |
| Zod 4 Mini | 1.88kb |

### API Differences

```typescript
// Zod (method-based)
import * as z from "zod";
z.string().optional();
z.string().array();
z.object({ a: z.string() }).extend({ b: z.number() });

// Zod Mini (function-based)
import * as z from "zod/mini";
z.optional(z.string());
z.array(z.string());
z.extend(z.object({ a: z.string() }), { b: z.number() });
```

### When to Use Zod Mini

| Signal | Choice |
|--------|--------|
| Standard app, DX priority | `zod` |
| Bundle size critical (widget, library) | `zod/mini` |
| Building a shared library | `zod/mini` or `zod/v4/core` |

### Shared APIs

Parsing methods are identical in both:

```typescript
schema.parse(data);
schema.safeParse(data);
await schema.parseAsync(data);
await schema.safeParseAsync(data);
```

## Zod 4 Performance Improvements

| Benchmark | Zod 3 | Zod 4 | Speedup |
|-----------|-------|-------|---------|
| String parsing | 363us | 25ns | 14x |
| Array parsing | 147us | 20ns | 7x |
| Object parsing | 805us | 124us | 6.5x |
| TypeScript instantiations (`.extend()`) | 25,000 | 175 | 100x |

### Key Zod 4 Architectural Changes

- Refinements stored inside schemas (not wrapped in `ZodEffects`)
- `.overwrite()` preserves schema class (unlike `.transform()`)
- Recursive objects via getters (no `z.lazy()` needed)
- `z.discriminatedUnion()` supports nesting and composition
- Top-level string formats for tree-shaking (`z.email()` instead of `z.string().email()`)
- `z.literal()` accepts arrays for multi-value literals

## Utility Types Quick Reference

| Utility | Returns |
|---------|---------|
| `z.infer<typeof S>` | Output type (after transforms) |
| `z.input<typeof S>` | Input type (before transforms) |
| `z.output<typeof S>` | Same as `z.infer` |
| `z.ZodType` | Base class for all schemas |
| `z.ZodObject<Shape>` | Object schema with typed shape |
| `z.ZodError` | Error class with `.issues` |
| `z.ZodIssue` | Single validation issue |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Manual `interface` + separate Zod schema | Types drift apart | Use `z.infer<>` as single source |
| `as any` after parse | Defeats the purpose of validation | Trust the inferred type |
| Branding runtime-critical values | Brand is compile-time only | Use refinements for runtime checks |
| Using `z.lazy()` in Zod 4 | Unnecessary — use getter syntax | Replace with `get prop() { return schema }` |
| Importing full `zod` in a widget | Bundle too large | Use `zod/mini` |
