# Error Handling and Formatting

Sources: Zod v4 official documentation (zod.dev), colinhacks/zod GitHub, zod-validation-error package

Covers: safeParse vs parse, ZodError structure, error customization (schema-level, per-parse, global), error formatting, prettifyError, i18n locales, and error handling best practices.

## Parse vs SafeParse

### parse() — Throws on Failure

```typescript
import * as z from "zod";

const User = z.object({ name: z.string(), age: z.number() });

try {
  const user = User.parse(unknownData); // throws ZodError if invalid
  // user is fully typed: { name: string; age: number }
} catch (error) {
  if (error instanceof z.ZodError) {
    console.error(error.issues);
  }
}
```

### safeParse() — Returns Result Object

```typescript
const result = User.safeParse(unknownData);

if (result.success) {
  result.data; // { name: string; age: number }
} else {
  result.error; // ZodError instance
  result.error.issues; // array of issues
}
```

### When to Use Each

| Context | Method | Rationale |
|---------|--------|-----------|
| API request handlers | `safeParse` | Return structured error responses, never crash |
| Form validation | `safeParse` (via resolver) | Display per-field errors |
| CLI / build scripts | `parse` | Crash-on-invalid is the desired behavior |
| Environment variables | `parse` | App must not start with invalid config |
| Unit tests | `parse` | Failure = test failure |
| Middleware pipelines | `safeParse` | Control error response format |

### Async Variants

Use `parseAsync` / `safeParseAsync` when schemas contain async refinements or transforms:

```typescript
const result = await schema.safeParseAsync(data);
```

## ZodError Structure

A `ZodError` contains an `.issues` array. Each issue has:

```typescript
interface ZodIssue {
  code: string;       // issue type identifier
  path: (string | number)[]; // path to the invalid value
  message: string;    // human-readable error message
  // ...additional fields depending on code
}
```

### Common Issue Codes

| Code | Trigger | Additional Fields |
|------|---------|-------------------|
| `invalid_type` | Wrong type | `expected`, `received` |
| `too_small` | Below minimum | `minimum`, `inclusive`, `type` |
| `too_big` | Above maximum | `maximum`, `inclusive`, `type` |
| `invalid_string` | String validation fail | `validation` (e.g., "email") |
| `invalid_format` | String format fail | `format` (e.g., "email", "uuid") |
| `invalid_enum_value` | Not in enum | `options`, `received` |
| `unrecognized_keys` | Extra keys in strict object | `keys` |
| `invalid_union` | No union member matched | `unionErrors` |
| `invalid_union_discriminator` | Bad discriminator value | `options` |
| `custom` | From `.refine()` / `.superRefine()` | (user-defined) |
| `invalid_value` | Value not in allowed set | `values` |

### Accessing Issues

```typescript
const result = schema.safeParse(data);
if (!result.success) {
  // All issues
  result.error.issues;

  // Flatten to simple object (useful for forms)
  result.error.flatten();
  // { formErrors: string[], fieldErrors: { [key]: string[] } }

  // Format as nested object
  result.error.format();
  // { _errors: string[], fieldName: { _errors: string[] } }
}
```

### flatten() vs format()

| Method | Output Shape | Best For |
|--------|-------------|----------|
| `.flatten()` | `{ formErrors: [], fieldErrors: { field: [] } }` | Flat forms, API error responses |
| `.format()` | `{ _errors: [], field: { _errors: [] } }` | Nested forms, recursive schemas |

### flatten() Example

```typescript
const result = z.object({
  name: z.string(),
  email: z.email(),
}).safeParse({ name: 42, email: "bad" });

if (!result.success) {
  const flat = result.error.flatten();
  // {
  //   formErrors: [],
  //   fieldErrors: {
  //     name: ["Invalid input: expected string"],
  //     email: ["Invalid email"],
  //   }
  // }
}
```

## Error Customization

Zod 4 unifies all error customization under a single `error` parameter, replacing Zod 3's `message`, `required_error`, `invalid_type_error`, and `errorMap`.

### Schema-Level Custom Errors (Highest Priority)

#### Simple String

```typescript
z.string("Not a string!");
z.string().min(5, "Too short!");
z.email("Invalid email format");
z.array(z.string(), "Expected an array");
```

#### Object Syntax

```typescript
z.string({ error: "Not a string!" });
z.string().min(5, { error: "Minimum 5 characters" });
```

#### Function Syntax (Error Map)

```typescript
z.string({
  error: (issue) => {
    if (issue.input === undefined) return "Required field";
    return "Must be a string";
  },
});

z.number().min(0, {
  error: (issue) => `Must be at least ${issue.minimum}`,
});
```

#### Selective Customization

Return `undefined` to fall through to the default message:

```typescript
z.int64({
  error: (issue) => {
    if (issue.code === "too_big") {
      return `Maximum value is ${issue.maximum}`;
    }
    return undefined; // use default for other codes
  },
});
```

### Per-Parse Custom Errors (Medium Priority)

```typescript
schema.safeParse(data, {
  error: (issue) => {
    if (issue.code === "invalid_type") {
      return `Expected ${issue.expected}, got ${typeof issue.input}`;
    }
  },
});
```

Schema-level errors take precedence over per-parse errors.

### Global Error Customization (Lowest Priority)

```typescript
z.config({
  customError: (issue) => {
    if (issue.code === "invalid_type") {
      return `Invalid type: expected ${issue.expected}`;
    }
    if (issue.code === "too_small") {
      return `Minimum is ${issue.minimum}`;
    }
  },
});
```

### Error Precedence (High to Low)

1. Schema-level `error` (hardcoded on the schema)
2. Per-parse `error` (passed to `.parse()` / `.safeParse()`)
3. Global `customError` (set via `z.config()`)
4. Locale error map (set via `z.config(z.locales.en())`)

## Pretty-Printing Errors (Zod 4)

```typescript
const error = result.error;
console.log(z.prettifyError(error));
// Output:
// ✖ Invalid input: expected string, received number
//   → at username
// ✖ Too small: expected number to be >=0
//   → at favoriteNumbers[1]
```

## Internationalization (i18n)

Zod 4 provides built-in locale support for translating default error messages:

```typescript
import * as z from "zod";

// Set locale globally
z.config(z.locales.en());    // English (default)
z.config(z.locales.fr());    // French
z.config(z.locales.de());    // German
z.config(z.locales.ja());    // Japanese
z.config(z.locales.zhCN());  // Simplified Chinese
z.config(z.locales.he());    // Hebrew
```

### Lazy Loading Locales

```typescript
async function loadLocale(locale: string) {
  const mod = await import(`zod/v4/locales/${locale}.js`);
  z.config(mod.default());
}

await loadLocale("fr");
```

### Available Locales

Over 40 locales including: ar, az, be, bg, ca, cs, da, de, en, es, fa, fi, fr, frCA, he, hu, id, is, it, ja, ka, km, ko, lt, mk, ms, nl, no, pl, pt, ru, sl, sv, ta, th, tr, uk, ur, uz, vi, zhCN, zhTW, yo.

## Including Input in Issues

By default, Zod omits input data from issues to prevent accidental logging of sensitive data:

```typescript
// Opt-in per parse call
z.string().parse(12, { reportInput: true });
// Issue now includes: { input: 12, ... }
```

## API Error Response Pattern

```typescript
function formatApiErrors(error: z.ZodError) {
  return {
    success: false,
    errors: error.issues.map((issue) => ({
      field: issue.path.join("."),
      message: issue.message,
      code: issue.code,
    })),
  };
}

// Usage in handler
const result = RequestSchema.safeParse(req.body);
if (!result.success) {
  return res.status(400).json(formatApiErrors(result.error));
}
```

## Form Error Mapping Pattern

```typescript
function zodToFieldErrors(error: z.ZodError): Record<string, string> {
  const fieldErrors: Record<string, string> = {};
  for (const issue of error.issues) {
    const key = issue.path.join(".");
    if (!fieldErrors[key]) {
      fieldErrors[key] = issue.message;
    }
  }
  return fieldErrors;
}
```

## Migration: Zod 3 to Zod 4 Errors

| Zod 3 API | Zod 4 Equivalent |
|-----------|-----------------|
| `{ message: "..." }` | `{ error: "..." }` (message still works, deprecated) |
| `{ required_error: "..." }` | `{ error: (iss) => iss.input === undefined ? "..." : undefined }` |
| `{ invalid_type_error: "..." }` | `{ error: (iss) => iss.code === "invalid_type" ? "..." : undefined }` |
| `{ errorMap: fn }` | `{ error: fn }` |
| `z.setErrorMap(fn)` | `z.config({ customError: fn })` |

## Error Handling Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Catching `parse()` errors generically | Swallows non-Zod errors | Check `instanceof z.ZodError` |
| Using `parse()` in API handlers | Uncaught exception crashes server | Use `safeParse()` |
| Logging full `ZodError` to client | Leaks internal schema details | Map to user-friendly messages |
| Ignoring `path` in error responses | Client cannot identify which field failed | Include `path` or `field` in response |
| Not setting custom messages on user-facing schemas | Default messages are developer-oriented | Add `error` param on public-facing schemas |
