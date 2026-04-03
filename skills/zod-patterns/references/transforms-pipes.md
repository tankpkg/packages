# Transforms, Pipes, and Refinements

Sources: Zod v4 official documentation (zod.dev), colinhacks/zod GitHub, TypeScript handbook

Covers: transforms, pipes, coercion, preprocess, overwrite, refinements, superRefine, custom validators, async validation, and default values.

## Transforms

Transforms change the output type of a schema. The input is validated first, then the transform function runs on the validated data.

### Basic Transform

```typescript
import * as z from "zod";

// string input -> number output
const StringToNumber = z.string().transform((val) => val.length);
type Input = z.input<typeof StringToNumber>;   // string
type Output = z.output<typeof StringToNumber>; // number

StringToNumber.parse("hello"); // => 5
```

### Chaining Transforms

```typescript
const TrimmedLower = z.string()
  .transform((s) => s.trim())
  .transform((s) => s.toLowerCase());

TrimmedLower.parse("  HELLO  "); // => "hello"
```

### Transform with Validation

Throw inside a transform to reject the value:

```typescript
const SafeJson = z.string().transform((str, ctx) => {
  try {
    return JSON.parse(str);
  } catch {
    ctx.addIssue({
      code: "custom",
      message: "Invalid JSON string",
    });
    return z.NEVER; // signals to Zod that parsing failed
  }
});
```

### Common Transform Patterns

| Pattern | Code |
|---------|------|
| Trim whitespace | `z.string().trim()` |
| Lowercase | `z.string().toLowerCase()` |
| Uppercase | `z.string().toUpperCase()` |
| Parse date | `z.string().transform(s => new Date(s))` |
| Parse JSON | `z.string().transform(s => JSON.parse(s))` |
| Split CSV | `z.string().transform(s => s.split(","))` |
| Coerce to number | `z.coerce.number()` |

## Pipes

Pipes chain two schemas together: the output of the first becomes the input of the second. Unlike transforms (which use arbitrary functions), pipes use Zod schemas for both stages, preserving introspectability.

### Basic Pipe

```typescript
// Validate as string, then validate the parsed number
const StringToInt = z.string()
  .transform((val) => parseInt(val, 10))
  .pipe(z.number().int().positive());

StringToInt.parse("42");   // => 42
StringToInt.parse("-5");   // throws (not positive)
StringToInt.parse("abc");  // throws (NaN fails number check)
```

### Pipe vs Transform

| Feature | `.transform()` | `.pipe()` |
|---------|---------------|-----------|
| Output validation | None (returns whatever the function returns) | Validates output against second schema |
| Type safety | Function return type | Both schemas are typed |
| JSON Schema compatible | No (black box function) | Yes (both schemas introspectable) |
| Use case | Arbitrary data manipulation | Schema-to-schema chaining |

### Real-World Pipe Example

```typescript
// Parse a comma-separated string into a validated array of emails
const EmailList = z.string()
  .transform((s) => s.split(",").map((e) => e.trim()))
  .pipe(z.array(z.email()).min(1).max(10));

EmailList.parse("[email protected],[email protected]");
// => ["[email protected]", "[email protected]"]
```

## Coercion

Coercion converts input to the target type before validation, using JavaScript's built-in constructors:

```typescript
z.coerce.string();    // String(input) -> then validate
z.coerce.number();    // Number(input) -> then validate
z.coerce.boolean();   // Boolean(input) -> then validate
z.coerce.bigint();    // BigInt(input) -> then validate
z.coerce.date();      // new Date(input) -> then validate
```

### Coercion Behavior

```typescript
z.coerce.string().parse(42);      // => "42"
z.coerce.string().parse(true);    // => "true"
z.coerce.string().parse(null);    // => "null"

z.coerce.number().parse("42");    // => 42
z.coerce.number().parse("");      // => 0
z.coerce.number().parse(null);    // => 0

z.coerce.boolean().parse("true"); // => true (truthy)
z.coerce.boolean().parse("");     // => false (falsy)
z.coerce.boolean().parse(0);      // => false (falsy)
z.coerce.boolean().parse("yes");  // => true (truthy! not a boolean "yes")
```

### Coercion vs Stringbool

| API | Input `"false"` | Input `""` | Input `"0"` |
|-----|----------------|------------|-------------|
| `z.coerce.boolean()` | `true` (truthy string) | `false` | `false` |
| `z.stringbool()` | `false` (recognized) | Error | `false` (recognized) |

Use `z.stringbool()` for env var booleans. Use `z.coerce.boolean()` only when JavaScript truthiness semantics are intended.

### Narrowing Coercion Input Type

```typescript
const A = z.coerce.number();
type AIn = z.input<typeof A>; // unknown

const B = z.coerce.number<string>();
type BIn = z.input<typeof B>; // string
```

## Overwrite (Zod 4)

`.overwrite()` mutates the value without changing the inferred type. Unlike `.transform()`, it preserves the original schema class, so JSON Schema conversion and other introspection still work:

```typescript
const Score = z.number().overwrite((val) => Math.round(val)).max(100);
// still ZodNumber (not ZodPipe)

Score.parse(99.7); // => 100
```

The built-in `.trim()`, `.toLowerCase()`, and `.toUpperCase()` methods use `.overwrite()` internally.

## Default Values

```typescript
z.string().default("hello");
// if input is undefined -> "hello"

z.number().default(() => Math.random());
// dynamic default via function

z.string().optional().default("fallback");
// undefined -> "fallback"
```

### Default vs Catch

| Method | Behavior |
|--------|----------|
| `.default(val)` | Uses `val` when input is `undefined` |
| `.catch(val)` | Uses `val` when validation fails (any error) |

```typescript
z.number().default(0).parse(undefined);   // => 0
z.number().default(0).parse("hello");     // throws!

z.number().catch(0).parse(undefined);     // => 0
z.number().catch(0).parse("hello");       // => 0 (caught the error)
```

## Refinements

Refinements add custom validation logic that runs after the base schema validates. They narrow the type at runtime without changing it in TypeScript.

### Basic Refine

```typescript
const NonEmpty = z.string().refine((val) => val.length > 0, {
  message: "String must not be empty",
});

const EvenNumber = z.number().refine((val) => val % 2 === 0, {
  message: "Must be even",
});
```

### Refine with Custom Error

```typescript
const PasswordStrength = z.string().refine(
  (val) => /[A-Z]/.test(val) && /[0-9]/.test(val) && val.length >= 8,
  { message: "Password must contain uppercase, digit, and be 8+ chars" }
);
```

### Zod 4: Refinements Live Inside Schemas

In Zod 4, refinements no longer wrap the schema in `ZodEffects`. Chain freely:

```typescript
// Zod 4: this works (refinement is stored inside the schema)
z.string()
  .refine((val) => val.includes("@"))
  .min(5)
  .max(100);

// Zod 3: this would fail (.min() not available on ZodEffects)
```

### Object-Level Refinements

Validate relationships between fields:

```typescript
const PasswordForm = z.object({
  password: z.string().min(8),
  confirm: z.string(),
}).refine((data) => data.password === data.confirm, {
  message: "Passwords don't match",
  path: ["confirm"], // attach error to the confirm field
});
```

## SuperRefine

`superRefine` gives full control over the issues array. Use when a single refinement produces multiple errors or needs different error codes:

```typescript
const ComplexPassword = z.string().superRefine((val, ctx) => {
  if (val.length < 8) {
    ctx.addIssue({
      code: z.ZodIssueCode.too_small,
      minimum: 8,
      type: "string",
      inclusive: true,
      message: "At least 8 characters",
    });
  }
  if (!/[A-Z]/.test(val)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Must contain uppercase letter",
    });
  }
  if (!/[0-9]/.test(val)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Must contain a digit",
    });
  }
});
```

### Early Termination

Return `z.NEVER` from superRefine to abort further validation:

```typescript
const StrictInput = z.unknown().superRefine((val, ctx) => {
  if (typeof val !== "object" || val === null) {
    ctx.addIssue({ code: "custom", message: "Expected object" });
    return z.NEVER;
  }
  // further checks only run if val is an object
});
```

## Custom Schemas with z.custom()

Create a schema from a type guard function:

```typescript
// Type guard
function isFile(val: unknown): val is File {
  return val instanceof File;
}

const FileSchema = z.custom<File>(isFile, { message: "Expected a File" });
```

## Async Validation

Some refinements need asynchronous checks (database uniqueness, API calls):

```typescript
const UniqueEmail = z.email().refine(
  async (email) => {
    const exists = await db.user.findByEmail(email);
    return !exists;
  },
  { message: "Email already registered" }
);

// Must use parseAsync / safeParseAsync
const result = await UniqueEmail.safeParseAsync("[email protected]");
```

### Async Rules

| Method | Sync refinements | Async refinements |
|--------|-----------------|-------------------|
| `.parse()` | Works | Throws error |
| `.safeParse()` | Works | Throws error |
| `.parseAsync()` | Works | Works |
| `.safeParseAsync()` | Works | Works |

Always use `parseAsync` / `safeParseAsync` when any schema in the chain uses async refinements or transforms.

## Refinement vs Transform Decision

| Need | Use |
|------|-----|
| Validate without changing type | `.refine()` or `.superRefine()` |
| Change the output type | `.transform()` |
| Change value, keep same type | `.overwrite()` (Zod 4) |
| Validate output of transform | `.pipe()` |
| Multiple validation errors at once | `.superRefine()` |
| Cross-field validation | `.refine()` on parent object |
| Async check (DB, API) | `.refine(async ...)` + `parseAsync` |

## Preprocess (Zod 3 Pattern)

In Zod 3, `z.preprocess()` runs a function before validation:

```typescript
// Zod 3 pattern
const TrimmedString = z.preprocess(
  (val) => (typeof val === "string" ? val.trim() : val),
  z.string().min(1)
);
```

In Zod 4, prefer `.overwrite()` or `.pipe()` instead — `preprocess` is still available but less idiomatic.

## Composition Patterns

### Reusable Refinements

```typescript
const nonEmpty = <T extends z.ZodString>(schema: T) =>
  schema.refine((val) => val.trim().length > 0, {
    message: "Must not be empty or whitespace",
  });

const Name = nonEmpty(z.string().max(100));
const Title = nonEmpty(z.string().max(200));
```

### Schema Factory

```typescript
function paginatedResponse<T extends z.ZodType>(itemSchema: T) {
  return z.object({
    items: z.array(itemSchema),
    total: z.number().int().nonnegative(),
    page: z.number().int().positive(),
    pageSize: z.number().int().positive().max(100),
  });
}

const UserPage = paginatedResponse(UserSchema);
const PostPage = paginatedResponse(PostSchema);
```
