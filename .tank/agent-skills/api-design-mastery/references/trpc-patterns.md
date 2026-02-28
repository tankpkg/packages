# tRPC Patterns

Sources: tRPC v11 official documentation (trpc.io, MIT license), Zod documentation (zod.dev, MIT license), TanStack Query documentation (tanstack.com/query, MIT license)

Covers: initTRPC setup, procedure types (query/mutation/subscription), input/output validation with Zod, middleware, context, router composition, error handling, deployment adapters, when to use tRPC vs REST vs GraphQL.

## What tRPC Is (and Isn't)

tRPC provides end-to-end type safety between a TypeScript server and TypeScript client — without code generation, without a schema language, without a spec file. The server's TypeScript types flow directly to the client through the `AppRouter` type export.

```typescript
// Server defines a procedure
const usersRouter = t.router({
  getById: t.procedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => db.users.findById(input.id)),
});

// Client gets full type inference — no codegen step
const user = await trpc.users.getById.query({ id: '42' });
//     ^? User | null — inferred from server return type
```

**Use tRPC when:**
- All clients are TypeScript (web, mobile, server)
- You control both client and server (same team, same repo)
- You're building a Next.js, Remix, or similar full-stack TypeScript app

**Do not use tRPC when:**
- Clients are non-TypeScript (mobile native, third-party)
- You need a public API consumed by external developers
- You need HTTP caching at the CDN level for read-heavy endpoints
- You're building a microservice that multiple teams will call

## Core Setup

```typescript
// server/trpc.ts
import { initTRPC, TRPCError } from '@trpc/server';
import superjson from 'superjson';
import { ZodError } from 'zod';

const t = initTRPC.context<Context>().create({
  transformer: superjson,  // Enables Date, Map, Set, BigInt serialization
  errorFormatter({ shape, error }) {
    return {
      ...shape,
      data: {
        ...shape.data,
        // Expose Zod validation details to client for field-level form errors
        zodError: error.cause instanceof ZodError
          ? error.cause.flatten()
          : null,
      },
    };
  },
});

export const router = t.router;
export const publicProcedure = t.procedure;
export const middleware = t.middleware;
```

Use `superjson` as the transformer when the client is also TypeScript — it handles `Date`, `Map`, `Set`, and `BigInt` transparently. Omit it for non-JavaScript clients.

## Context

Context is a per-request object injected into every procedure. Attach database clients, the authenticated user, loggers, and any other request-scoped dependencies.

```typescript
// server/context.ts
import type { inferAsyncReturnType } from '@trpc/server';
import type { CreateExpressContextOptions } from '@trpc/server/adapters/express';

export async function createContext({ req, res }: CreateExpressContextOptions) {
  // Keep context creation cheap — don't fetch user data here unless needed by most procedures
  const token = req.headers.authorization?.replace('Bearer ', '') ?? null;
  
  return {
    db,
    req,
    res,
    token,  // Raw token — middleware validates it and adds the user
  };
}

export type Context = inferAsyncReturnType<typeof createContext>;
```

## Procedures

### Query (Read Operations)

```typescript
import { z } from 'zod';

export const usersRouter = router({
  getById: publicProcedure
    .input(z.object({ id: z.string().uuid() }))
    .output(z.object({        // Optional but recommended for public procedures
      id: z.string(),
      name: z.string(),
      email: z.string(),
    }).nullable())
    .query(async ({ input, ctx }) => {
      return ctx.db.users.findById(input.id);
    }),

  list: publicProcedure
    .input(z.object({
      limit: z.number().int().min(1).max(100).default(20),
      cursor: z.string().optional(),
    }))
    .query(async ({ input, ctx }) => {
      const users = await ctx.db.users.findMany({
        take: input.limit + 1,  // Fetch one extra to determine hasNext
        cursor: input.cursor ? { id: input.cursor } : undefined,
        orderBy: { createdAt: 'desc' },
      });
      
      const hasNext = users.length > input.limit;
      return {
        items: hasNext ? users.slice(0, -1) : users,
        nextCursor: hasNext ? users[users.length - 2].id : null,
      };
    }),
});
```

### Mutation (Write Operations)

```typescript
create: protectedProcedure
  .input(z.object({
    name: z.string().min(1).max(100).trim(),
    email: z.string().email().toLowerCase(),
    role: z.enum(['VIEWER', 'EDITOR', 'ADMIN']).default('VIEWER'),
  }))
  .mutation(async ({ input, ctx }) => {
    const existing = await ctx.db.users.findByEmail(input.email);
    if (existing) {
      throw new TRPCError({
        code: 'CONFLICT',
        message: 'A user with this email already exists.',
      });
    }
    return ctx.db.users.create({ data: input });
  }),
```

### Input Validation with Zod

Zod schemas are the primary validation layer. tRPC automatically throws `BAD_REQUEST` with Zod error details if `.input()` validation fails.

```typescript
// Compose schemas from reusable pieces
const PaginationSchema = z.object({
  limit: z.number().int().min(1).max(100).default(20),
  cursor: z.string().optional(),
});

const UserFilterSchema = z.object({
  status: z.enum(['ACTIVE', 'INACTIVE']).optional(),
  search: z.string().max(200).optional(),
});

// Use Zod transforms for normalization
const EmailSchema = z.string().email().toLowerCase().trim();

// Refine for cross-field validation
const DateRangeSchema = z.object({
  from: z.date(),
  to: z.date(),
}).refine(({ from, to }) => to >= from, {
  message: 'to must be after from',
  path: ['to'],
});
```

### Output Validation

`.output()` strips unknown fields and validates the return shape. Use it for all publicly-facing procedures:

```typescript
.output(
  z.object({
    id: z.string(),
    name: z.string(),
    email: z.string(),
    createdAt: z.date(),
  })
)
```

## Middleware

Middleware runs before the procedure handler. It can read context, augment it with new values, or throw to halt execution.

```typescript
// Narrow context: user becomes non-null after this middleware
const isAuthenticated = middleware(({ ctx, next }) => {
  if (!ctx.token) {
    throw new TRPCError({ code: 'UNAUTHORIZED', message: 'Authentication required.' });
  }
  
  const user = validateToken(ctx.token);
  if (!user) {
    throw new TRPCError({ code: 'UNAUTHORIZED', message: 'Invalid or expired token.' });
  }
  
  // Pass augmented context to procedure — TypeScript narrows user to non-null
  return next({ ctx: { ...ctx, user } });
});

const isAdmin = middleware(({ ctx, next }) => {
  if (ctx.user?.role !== 'ADMIN') {
    throw new TRPCError({ code: 'FORBIDDEN', message: 'Admin role required.' });
  }
  return next({ ctx });
});

// Compose into reusable procedure builders
export const protectedProcedure = publicProcedure.use(isAuthenticated);
export const adminProcedure = protectedProcedure.use(isAdmin);
```

Middleware ordering: `.use(a).use(b)` — `a` wraps `b`; `a` runs first, calls `next()` which runs `b`, which calls `next()` which runs the handler.

### Logging Middleware

```typescript
const withTiming = middleware(async ({ path, type, next }) => {
  const start = Date.now();
  const result = await next();
  const ms = Date.now() - start;
  console.log(`[tRPC] ${type} ${path} ${result.ok ? 'OK' : 'ERR'} ${ms}ms`);
  return result;
});

// Apply globally by wrapping the base procedure
export const publicProcedure = t.procedure.use(withTiming);
```

## Router Composition

Organize procedures into domain routers, then merge into a single app router:

```typescript
// server/routers/index.ts
import { router } from '../trpc';
import { usersRouter } from './users';
import { ordersRouter } from './orders';
import { productsRouter } from './products';
import { notificationsRouter } from './notifications';

export const appRouter = router({
  users: usersRouter,
  orders: ordersRouter,
  products: productsRouter,
  notifications: notificationsRouter,
});

// Export the type — this is imported by the client
export type AppRouter = typeof appRouter;
```

Client usage:

```typescript
import type { AppRouter } from '../server/routers';
import { createTRPCReact } from '@trpc/react-query';

export const trpc = createTRPCReact<AppRouter>();

// Full type inference — no codegen
const { data: user } = trpc.users.getById.useQuery({ id: '42' });
const mutation = trpc.orders.create.useMutation();
```

### Server-Side Calls

Call procedures from server-side code (Server Actions, tests, cron jobs) using `createCallerFactory`:

```typescript
import { createCallerFactory } from '@trpc/server';
import { appRouter } from './routers';

const createCaller = createCallerFactory(appRouter);

// In a Server Action or background job
const caller = createCaller({
  db,
  user: systemUser,
  token: null,
  req: null,
  res: null,
});

const orders = await caller.orders.list({ limit: 50 });
```

## Error Handling

Throw `TRPCError` with a specific code. tRPC maps codes to HTTP status codes automatically:

```typescript
throw new TRPCError({
  code: 'NOT_FOUND',
  message: 'Order not found.',
  cause: originalError,  // Logged server-side, NOT sent to client
});
```

### Error Code Reference

| TRPCError code | HTTP Status | Use When |
|---------------|------------|---------|
| `BAD_REQUEST` | 400 | Input validation failed (Zod auto-throws) |
| `UNAUTHORIZED` | 401 | No credentials or invalid token |
| `FORBIDDEN` | 403 | Authenticated but lacks permission |
| `NOT_FOUND` | 404 | Resource doesn't exist |
| `CONFLICT` | 409 | Duplicate, concurrent write conflict |
| `PRECONDITION_FAILED` | 412 | Required condition not met |
| `PAYLOAD_TOO_LARGE` | 413 | Input exceeds size limit |
| `TOO_MANY_REQUESTS` | 429 | Rate limit exceeded |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |
| `NOT_IMPLEMENTED` | 501 | Feature not yet built |
| `TIMEOUT` | 408 | Operation exceeded time limit |

## Subscriptions

```typescript
import { observable } from '@trpc/server/observable';
import { EventEmitter } from 'events';

const ee = new EventEmitter();

export const notificationsRouter = router({
  onNew: protectedProcedure
    .input(z.object({ userId: z.string() }))
    .subscription(({ input, ctx }) => {
      // Must return an Observable
      return observable<Notification>((emit) => {
        const onNotification = (notification: Notification) => {
          emit.next(notification);
        };
        
        ee.on(`notifications:${input.userId}`, onNotification);
        
        // Return cleanup function — called when client disconnects
        return () => {
          ee.off(`notifications:${input.userId}`, onNotification);
        };
      });
    }),
});
```

Subscriptions require WebSocket transport. Configure `wsLink` on the client and `createWSServer` on the server.

## Deployment Adapters

| Adapter Import | Runtime |
|---------------|---------|
| `@trpc/server/adapters/express` | Node.js (Express, Fastify with adapter) |
| `@trpc/server/adapters/fetch` | Edge runtimes, Cloudflare Workers, Next.js App Router |
| `@trpc/server/adapters/standalone` | Plain Node.js HTTP |
| `@trpc/server/adapters/aws-lambda` | AWS Lambda |

### Next.js App Router

```typescript
// app/api/trpc/[trpc]/route.ts
import { fetchRequestHandler } from '@trpc/server/adapters/fetch';
import { appRouter } from '@/server/routers';
import { createContext } from '@/server/context';

const handler = (req: Request) =>
  fetchRequestHandler({
    endpoint: '/api/trpc',
    req,
    router: appRouter,
    createContext: () => createContext({ req }),
    onError: ({ error, path }) => {
      if (error.code === 'INTERNAL_SERVER_ERROR') {
        console.error(`tRPC error on ${path}:`, error);
      }
    },
  });

export { handler as GET, handler as POST };
```

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Using tRPC for a public API | No OpenAPI spec; non-TS clients can't use it | REST + OpenAPI for public APIs |
| Sharing `AppRouter` type across separate services | Tight coupling; breaks if router changes | One tRPC app router per service boundary |
| Business logic inside procedure handlers | Untestable; hard to reuse | Extract to service functions; call from handler |
| Single giant router file | Hard to navigate, merge conflicts | One router file per domain (users, orders, etc.) |
| Skipping `.output()` on external procedures | Type drift between actual response and declared type | Define output schema for all public procedures |
| DataLoader singletons at module level | Cache shared across requests; stale data, memory leak | Create DataLoaders inside `createContext` |
| Catching all errors and rethrowing as 500 | Hides useful error codes from client | Only catch and rethrow unexpected errors; let TRPCErrors pass through |
