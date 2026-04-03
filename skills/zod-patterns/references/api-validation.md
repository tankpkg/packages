# API Validation and tRPC Integration

Sources: Zod v4 official documentation (zod.dev), tRPC documentation (trpc.io), Hono documentation (hono.dev), Express.js documentation

Covers: request/response validation middleware for Express, Hono, and Next.js, tRPC input/output validation, OpenAPI generation from Zod schemas, and API boundary patterns.

## Principle: Validate at the Boundary

Parse untrusted data exactly once — at the system boundary where it enters your application. After parsing, the interior code operates on typed, trusted data without re-validation.

```
Untrusted Input ──→ [Zod Parse] ──→ Typed Data ──→ Business Logic
                        │
                   400 + errors
```

## Express Middleware

### Validation Middleware Factory

```typescript
import * as z from "zod";
import { Request, Response, NextFunction } from "express";

function validate<T extends z.ZodType>(schema: T) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      return res.status(400).json({
        success: false,
        errors: result.error.issues.map((i) => ({
          path: i.path.join("."),
          message: i.message,
        })),
      });
    }
    req.body = result.data;
    next();
  };
}
```

### Usage

```typescript
const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.email(),
  role: z.enum(["admin", "user"]).default("user"),
});

app.post("/users", validate(CreateUserSchema), (req, res) => {
  // req.body is typed as { name: string; email: string; role: "admin" | "user" }
  const user = await createUser(req.body);
  res.json(user);
});
```

### Validating Query, Params, and Headers

```typescript
function validateRequest<
  TBody extends z.ZodType,
  TQuery extends z.ZodType,
  TParams extends z.ZodType,
>(schemas: { body?: TBody; query?: TQuery; params?: TParams }) {
  return (req: Request, res: Response, next: NextFunction) => {
    const errors: { location: string; issues: z.ZodIssue[] }[] = [];

    if (schemas.body) {
      const result = schemas.body.safeParse(req.body);
      if (!result.success) errors.push({ location: "body", issues: result.error.issues });
      else req.body = result.data;
    }
    if (schemas.query) {
      const result = schemas.query.safeParse(req.query);
      if (!result.success) errors.push({ location: "query", issues: result.error.issues });
      else (req as any).validatedQuery = result.data;
    }
    if (schemas.params) {
      const result = schemas.params.safeParse(req.params);
      if (!result.success) errors.push({ location: "params", issues: result.error.issues });
      else (req as any).validatedParams = result.data;
    }

    if (errors.length > 0) {
      return res.status(400).json({ success: false, errors });
    }
    next();
  };
}
```

### Common Query Parameter Patterns

```typescript
const PaginationQuery = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sort: z.enum(["asc", "desc"]).default("desc"),
  search: z.string().optional(),
});
```

## Hono Middleware

Hono has first-class Zod support via `@hono/zod-validator`:

```typescript
import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import * as z from "zod";

const app = new Hono();

const CreatePostSchema = z.object({
  title: z.string().min(1).max(200),
  body: z.string().min(1),
  tags: z.array(z.string()).max(10).default([]),
});

app.post(
  "/posts",
  zValidator("json", CreatePostSchema),
  async (c) => {
    const data = c.req.valid("json");
    // data: { title: string; body: string; tags: string[] }
    const post = await createPost(data);
    return c.json(post, 201);
  }
);
```

### Validating Multiple Sources

```typescript
app.get(
  "/posts/:id",
  zValidator("param", z.object({ id: z.string().uuid() })),
  zValidator("query", z.object({ include: z.enum(["author", "comments"]).optional() })),
  async (c) => {
    const { id } = c.req.valid("param");
    const { include } = c.req.valid("query");
    // Both fully typed
  }
);
```

### Custom Error Handler

```typescript
app.post(
  "/posts",
  zValidator("json", CreatePostSchema, (result, c) => {
    if (!result.success) {
      return c.json(
        { errors: result.error.flatten().fieldErrors },
        400
      );
    }
  }),
  handler
);
```

## Next.js API Routes

### App Router Route Handlers

```typescript
// app/api/users/route.ts
import * as z from "zod";
import { NextResponse } from "next/server";

const CreateUserSchema = z.object({
  name: z.string().min(1),
  email: z.email(),
});

export async function POST(request: Request) {
  const body = await request.json();
  const result = CreateUserSchema.safeParse(body);

  if (!result.success) {
    return NextResponse.json(
      { errors: result.error.flatten().fieldErrors },
      { status: 400 }
    );
  }

  const user = await db.users.create({ data: result.data });
  return NextResponse.json(user, { status: 201 });
}
```

### Reusable Validation Helper

```typescript
async function parseBody<T extends z.ZodType>(
  request: Request,
  schema: T
): Promise<
  | { success: true; data: z.infer<T> }
  | { success: false; response: NextResponse }
> {
  const body = await request.json().catch(() => null);
  const result = schema.safeParse(body);

  if (!result.success) {
    return {
      success: false,
      response: NextResponse.json(
        { errors: result.error.flatten().fieldErrors },
        { status: 400 }
      ),
    };
  }
  return { success: true, data: result.data };
}

// Usage
export async function POST(request: Request) {
  const parsed = await parseBody(request, CreateUserSchema);
  if (!parsed.success) return parsed.response;

  const user = await db.users.create({ data: parsed.data });
  return NextResponse.json(user, { status: 201 });
}
```

## tRPC Integration

tRPC uses Zod schemas natively for input and output validation, providing end-to-end type safety from client to server.

### Basic Router

```typescript
import { initTRPC } from "@trpc/server";
import * as z from "zod";

const t = initTRPC.create();

const appRouter = t.router({
  getUser: t.procedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      // input: { id: string } — fully typed
      return db.users.findUnique({ where: { id: input.id } });
    }),

  createUser: t.procedure
    .input(z.object({
      name: z.string().min(1).max(100),
      email: z.email(),
    }))
    .mutation(async ({ input }) => {
      return db.users.create({ data: input });
    }),
});

export type AppRouter = typeof appRouter;
```

### Output Validation

```typescript
const UserOutput = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string(),
  // No password field — schema enforces what the client sees
});

t.procedure
  .input(z.object({ id: z.string() }))
  .output(UserOutput)
  .query(async ({ input }) => {
    const user = await db.users.findUnique({ where: { id: input.id } });
    return user; // stripped to match UserOutput — no password leak
  });
```

### Input Reuse Between Client and Server

```typescript
// shared/schemas.ts
export const CreatePostInput = z.object({
  title: z.string().min(1).max(200),
  body: z.string().min(1),
  tags: z.array(z.string()).max(10),
});

export type CreatePostInput = z.infer<typeof CreatePostInput>;
```

Both the tRPC router and client form use the same schema — changes propagate automatically.

### Middleware with Validated Context

```typescript
const authedProcedure = t.procedure.use(async ({ ctx, next }) => {
  if (!ctx.session?.user) {
    throw new TRPCError({ code: "UNAUTHORIZED" });
  }
  return next({ ctx: { user: ctx.session.user } });
});

authedProcedure
  .input(z.object({ postId: z.string() }))
  .mutation(async ({ input, ctx }) => {
    // ctx.user is typed and guaranteed to exist
    return deletePost(input.postId, ctx.user.id);
  });
```

## Response Validation Pattern

Validate data coming FROM external APIs to ensure contract compliance:

```typescript
const ExternalApiResponse = z.object({
  results: z.array(z.object({
    id: z.number(),
    name: z.string(),
    status: z.enum(["active", "inactive"]),
  })),
  total: z.number(),
});

async function fetchExternalData() {
  const res = await fetch("https://api.example.com/data");
  const json = await res.json();

  const result = ExternalApiResponse.safeParse(json);
  if (!result.success) {
    logger.error("External API contract violation", result.error.issues);
    throw new Error("Unexpected API response format");
  }
  return result.data;
}
```

## OpenAPI Generation

Use Zod schemas as the source of truth for OpenAPI specifications:

```typescript
import * as z from "zod";

// Use z.toJSONSchema() for individual schemas
const schema = z.object({
  name: z.string().describe("User's full name"),
  email: z.email().describe("Email address"),
});

const jsonSchema = z.toJSONSchema(schema);
// Use in OpenAPI spec as requestBody schema
```

Libraries that generate OpenAPI from Zod:

| Library | Framework |
|---------|-----------|
| `zod-openapi` | Framework-agnostic |
| `@hono/zod-openapi` | Hono |
| `trpc-openapi` | tRPC |
| `ts-rest` | Any (contract-first) |

## API Validation Checklist

| Checkpoint | Pattern |
|-----------|---------|
| Request body | `safeParse(req.body)` with 400 response |
| Query parameters | Coerce types (`z.coerce.number()`) since all are strings |
| Path parameters | Validate format (UUID, slug, etc.) |
| Response data | Output schema strips sensitive fields |
| External API responses | `safeParse` + log violations |
| Error response format | Consistent structure across endpoints |
| Content-Type | Verify JSON before parsing body |
