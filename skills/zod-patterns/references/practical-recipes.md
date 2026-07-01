# Practical Recipes

Sources: Zod v4 official documentation (zod.dev), colinhacks/zod GitHub, t3-env documentation, production patterns

Covers: environment variable validation, config file parsing, API response validation, date handling, file uploads, discriminated union patterns, and common real-world Zod recipes.

## Environment Variable Validation

### Basic Env Schema

```typescript
import * as z from "zod";

const envSchema = z.object({
  // Required
  DATABASE_URL: z.url(),
  JWT_SECRET: z.string().min(32),
  NODE_ENV: z.enum(["development", "staging", "production"]),

  // With defaults
  PORT: z.coerce.number().int().positive().default(3000),
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),

  // Booleans from env (Zod 4)
  DEBUG: z.stringbool().default("false"),
  ENABLE_CACHE: z.stringbool().default("true"),

  // Optional
  SENTRY_DSN: z.url().optional(),
  REDIS_URL: z.url().optional(),
});

export const env = envSchema.parse(process.env);
// Crashes at startup if env is invalid — fail fast
```

### Env Schema Patterns

| Env Var Type | Schema |
|-------------|--------|
| Required string | `z.string().min(1)` |
| URL | `z.url()` |
| Port number | `z.coerce.number().int().min(1).max(65535)` |
| Boolean flag | `z.stringbool()` (Zod 4) or `z.enum(["true","false"]).transform(v => v === "true")` |
| Comma-separated list | `z.string().transform(s => s.split(","))` |
| Duration (ms) | `z.coerce.number().positive()` |
| Enum | `z.enum(["a", "b", "c"])` |
| Optional with default | `z.string().default("fallback")` |
| Secret/key | `z.string().min(32)` |

### Environment-Specific Validation

```typescript
const envSchema = z.object({
  NODE_ENV: z.enum(["development", "staging", "production"]),
  DATABASE_URL: z.url(),
  // Only required in production
  SENTRY_DSN: z.url().optional(),
}).refine(
  (env) => env.NODE_ENV !== "production" || env.SENTRY_DSN !== undefined,
  { message: "SENTRY_DSN is required in production", path: ["SENTRY_DSN"] }
);
```

### t3-env Pattern

The `@t3-oss/env-core` package builds on Zod for validated, type-safe env:

```typescript
import { createEnv } from "@t3-oss/env-core";
import * as z from "zod";

export const env = createEnv({
  server: {
    DATABASE_URL: z.url(),
    JWT_SECRET: z.string().min(32),
  },
  client: {
    NEXT_PUBLIC_API_URL: z.url(),
  },
  runtimeEnv: process.env,
});
```

## Config File Parsing

```typescript
const AppConfig = z.object({
  server: z.object({
    host: z.string().default("0.0.0.0"),
    port: z.number().int().min(1).max(65535).default(3000),
    cors: z.object({
      origins: z.array(z.string()).default(["*"]),
      credentials: z.boolean().default(false),
    }).default({}),
  }).default({}),
  database: z.object({
    url: z.url(),
    pool: z.object({
      min: z.number().int().nonnegative().default(2),
      max: z.number().int().positive().default(10),
    }).default({}),
  }),
  logging: z.object({
    level: z.enum(["debug", "info", "warn", "error"]).default("info"),
    format: z.enum(["json", "pretty"]).default("json"),
  }).default({}),
});

// Parse JSON/YAML config file
const rawConfig = JSON.parse(fs.readFileSync("config.json", "utf-8"));
const config = AppConfig.parse(rawConfig);
```

## API Response Validation

### External API Contract Validation

```typescript
const GitHubUser = z.object({
  id: z.number(),
  login: z.string(),
  name: z.string().nullable(),
  email: z.string().nullable(),
  avatar_url: z.url(),
  public_repos: z.number(),
});

async function fetchGitHubUser(username: string) {
  const res = await fetch(`https://api.github.com/users/${username}`);
  if (!res.ok) throw new Error(`GitHub API error: ${res.status}`);

  const data = await res.json();
  return GitHubUser.parse(data);
  // Throws if GitHub changes their API shape
}
```

### Paginated API Response

```typescript
function paginatedSchema<T extends z.ZodType>(itemSchema: T) {
  return z.object({
    data: z.array(itemSchema),
    pagination: z.object({
      page: z.number().int().positive(),
      perPage: z.number().int().positive(),
      total: z.number().int().nonnegative(),
      totalPages: z.number().int().nonnegative(),
    }),
  });
}

const UserListResponse = paginatedSchema(GitHubUser);
type UserListResponse = z.infer<typeof UserListResponse>;
```

### Nullable vs Optional in API Responses

| API Returns | Zod Schema | TypeScript Type |
|-------------|-----------|-----------------|
| Field always present, value or null | `.nullable()` | `string \| null` |
| Field may be missing | `.optional()` | `string \| undefined` |
| Field may be missing or null | `.nullish()` | `string \| null \| undefined` |
| Field present with default if missing | `.default("value")` | `string` |

## Date Handling Recipes

### ISO String to Date

```typescript
const DateFromISO = z.string()
  .transform((s) => new Date(s))
  .pipe(z.date());

DateFromISO.parse("2024-01-15T10:30:00Z");
// => Date object
```

### Unix Timestamp to Date

```typescript
const DateFromTimestamp = z.number()
  .transform((ts) => new Date(ts * 1000))
  .pipe(z.date());

DateFromTimestamp.parse(1705312200);
// => Date object
```

### Date Range Validation

```typescript
const DateRange = z.object({
  startDate: z.coerce.date(),
  endDate: z.coerce.date(),
}).refine(
  (data) => data.endDate > data.startDate,
  { message: "End date must be after start date", path: ["endDate"] }
);
```

### Flexible Date Input

```typescript
const FlexibleDate = z.union([
  z.date(),
  z.string().transform((s) => new Date(s)),
  z.number().transform((n) => new Date(n)),
]).pipe(z.date());
```

## Discriminated Union Patterns

### API Result Type

```typescript
const ApiResult = z.discriminatedUnion("status", [
  z.object({
    status: z.literal("success"),
    data: z.unknown(),
    timestamp: z.string(),
  }),
  z.object({
    status: z.literal("error"),
    error: z.object({
      code: z.string(),
      message: z.string(),
    }),
    timestamp: z.string(),
  }),
]);
```

### Event System

```typescript
const AppEvent = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("user.created"),
    payload: z.object({ userId: z.string(), email: z.email() }),
  }),
  z.object({
    type: z.literal("order.placed"),
    payload: z.object({ orderId: z.string(), total: z.number() }),
  }),
  z.object({
    type: z.literal("payment.failed"),
    payload: z.object({ orderId: z.string(), reason: z.string() }),
  }),
]);

type AppEvent = z.infer<typeof AppEvent>;

function handleEvent(event: AppEvent) {
  switch (event.type) {
    case "user.created":
      event.payload.email; // TypeScript knows this exists
      break;
    case "order.placed":
      event.payload.total; // TypeScript knows this exists
      break;
  }
}
```

### Nested Discriminated Union (Zod 4)

```typescript
const Shape = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("circle"), radius: z.number() }),
  z.discriminatedUnion("subKind", [
    z.object({ kind: z.literal("polygon"), subKind: z.literal("triangle"), base: z.number(), height: z.number() }),
    z.object({ kind: z.literal("polygon"), subKind: z.literal("rectangle"), width: z.number(), height: z.number() }),
  ]),
]);
```

## File Upload Validation (Zod 4)

```typescript
const ImageUpload = z.file()
  .min(1024, { error: "File too small (min 1KB)" })
  .max(5_000_000, { error: "File too large (max 5MB)" })
  .mime(["image/png", "image/jpeg", "image/webp"], {
    error: "Only PNG, JPEG, and WebP images allowed",
  });

const UploadForm = z.object({
  title: z.string().min(1).max(100),
  image: ImageUpload,
});
```

## Reusable Schema Fragments

### Base Schemas

```typescript
// Timestamps
const Timestamps = z.object({
  createdAt: z.coerce.date(),
  updatedAt: z.coerce.date(),
});

// Database row with ID
const BaseEntity = z.object({
  id: z.string().uuid(),
  ...Timestamps.shape,
});

// Build specific entities
const User = BaseEntity.extend({
  name: z.string(),
  email: z.email(),
});

const Post = BaseEntity.extend({
  title: z.string(),
  body: z.string(),
  authorId: z.string().uuid(),
});
```

### Request/Response Schema Pairs

```typescript
// Create input (no id, no timestamps)
const CreateUserInput = User.omit({ id: true, createdAt: true, updatedAt: true });

// Update input (partial, no id/timestamps)
const UpdateUserInput = CreateUserInput.partial();

// List query
const ListUsersQuery = z.object({
  page: z.coerce.number().positive().default(1),
  limit: z.coerce.number().min(1).max(100).default(20),
  search: z.string().optional(),
  role: z.enum(["admin", "user"]).optional(),
});

// Full response
type UserResponse = z.infer<typeof User>;
type CreateUserInput = z.infer<typeof CreateUserInput>;
type UpdateUserInput = z.infer<typeof UpdateUserInput>;
```

## JSON String Parsing

```typescript
const JsonString = z.string().transform((str, ctx) => {
  try {
    return JSON.parse(str);
  } catch {
    ctx.addIssue({ code: "custom", message: "Invalid JSON" });
    return z.NEVER;
  }
});

// With typed output
const TypedJson = <T extends z.ZodType>(schema: T) =>
  z.string()
    .transform((str, ctx) => {
      try { return JSON.parse(str); }
      catch { ctx.addIssue({ code: "custom", message: "Invalid JSON" }); return z.NEVER; }
    })
    .pipe(schema);

const Config = TypedJson(z.object({ host: z.string(), port: z.number() }));
Config.parse('{"host":"localhost","port":3000}');
```

## Slug and URL-Safe String

```typescript
const Slug = z.string()
  .min(1)
  .max(100)
  .regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, {
    error: "Slug must be lowercase letters, numbers, and hyphens",
  });

// Auto-generate slug from title
const WithSlug = z.object({
  title: z.string().min(1),
  slug: z.string().optional(),
}).transform((data) => ({
  ...data,
  slug: data.slug ?? data.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""),
}));
```

## Phone Number Validation

```typescript
// Basic E.164 format
const PhoneNumber = z.string().regex(
  /^\+[1-9]\d{6,14}$/,
  { error: "Phone must be in E.164 format (e.g., +14155552671)" }
);

// Or use Zod 4's built-in (if available)
// z.e164()
```

## Money / Currency

```typescript
const Money = z.object({
  amount: z.number().nonnegative().multipleOf(0.01),
  currency: z.enum(["USD", "EUR", "GBP", "JPY"]),
});

// Store as integer cents to avoid floating point
const MoneyCents = z.object({
  amountCents: z.number().int().nonnegative(),
  currency: z.enum(["USD", "EUR", "GBP", "JPY"]),
});
```
