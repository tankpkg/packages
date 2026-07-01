# Client Extensions and Middleware

Sources: Prisma ORM Documentation (prisma.io/docs), Prisma Client Extensions API reference, Prisma Blog (prisma.io/blog), 2025-2026 production extension patterns

Covers: Prisma Client extensions ($extends), model/query/result/client component types, soft delete implementation, audit logging, row-level security (RLS), computed fields, middleware chaining, and shared extension patterns.

## Client Extensions Overview

Prisma Client extensions (`$extends`) replace the deprecated middleware API with a type-safe, composable system for adding behavior to Prisma Client. Extensions create lightweight extended clients that share the same connection pool.

### Extension Components

| Component | Purpose | Example Use Cases |
|-----------|---------|-------------------|
| `model` | Add custom methods to models | `user.signUp()`, `post.publish()` |
| `query` | Intercept and modify queries | Soft delete, audit logging, caching |
| `result` | Add computed fields to results | `fullName`, `formattedDate` |
| `client` | Add top-level client methods | `prisma.$log()`, `prisma.$audit()` |

### Basic Extension

```typescript
const prisma = new PrismaClient().$extends({
  name: 'myExtension',  // Shows in error logs
  model: { /* ... */ },
  query: { /* ... */ },
  result: { /* ... */ },
  client: { /* ... */ },
})
```

### Defining Extensions Separately

```typescript
import { Prisma } from '@prisma/client'

const softDelete = Prisma.defineExtension({
  name: 'softDelete',
  query: { /* ... */ },
})

const auditLog = Prisma.defineExtension({
  name: 'auditLog',
  query: { /* ... */ },
})

const prisma = new PrismaClient()
  .$extends(softDelete)
  .$extends(auditLog)
```

Extensions execute in order -- first in, first out. The last extension takes precedence if methods conflict.

## Model Extensions

Add custom methods to specific models or all models:

### Model-Specific Method

```typescript
const prisma = new PrismaClient().$extends({
  model: {
    user: {
      async signUp(email: string, name: string) {
        return prisma.user.create({
          data: { email, name, role: 'USER' },
        })
      },
      async findByEmail(email: string) {
        return prisma.user.findUnique({ where: { email } })
      },
    },
  },
})

// Usage
const user = await prisma.user.signUp('alice@example.com', 'Alice')
const found = await prisma.user.findByEmail('alice@example.com')
```

### Methods on All Models

```typescript
const prisma = new PrismaClient().$extends({
  model: {
    $allModels: {
      async exists<T>(this: T, where: Prisma.Args<T, 'findFirst'>['where']): Promise<boolean> {
        const context = Prisma.getExtensionContext(this)
        const result = await (context as any).findFirst({ where })
        return result !== null
      },
    },
  },
})

// Usage
const exists = await prisma.user.exists({ email: 'alice@example.com' })
```

## Query Extensions

Intercept queries before and after execution. The primary mechanism for cross-cutting concerns.

### Soft Delete

Intercept `delete` and `findMany` to implement soft delete without changing application code:

```typescript
const softDelete = Prisma.defineExtension({
  name: 'softDelete',
  query: {
    $allModels: {
      async delete({ model, operation, args, query }) {
        return query({
          ...args,
          data: { deletedAt: new Date() },
        } as any)  // Convert delete to update
      },
      async deleteMany({ model, operation, args, query }) {
        return (Prisma.getExtensionContext(this) as any).updateMany({
          ...args,
          data: { deletedAt: new Date() },
        })
      },
      async findMany({ model, operation, args, query }) {
        args.where = { ...args.where, deletedAt: null }
        return query(args)
      },
      async findFirst({ model, operation, args, query }) {
        args.where = { ...args.where, deletedAt: null }
        return query(args)
      },
      async findUnique({ model, operation, args, query }) {
        // findUnique cannot filter by deletedAt directly
        // Convert to findFirst
        return (Prisma.getExtensionContext(this) as any).findFirst({
          where: { ...args.where, deletedAt: null },
        })
      },
    },
  },
})
```

This requires a `deletedAt DateTime?` field on soft-deletable models. The extension transparently filters deleted records from all reads and converts deletes to timestamp updates.

### Audit Logging

Log all write operations:

```typescript
const auditLog = Prisma.defineExtension({
  name: 'auditLog',
  query: {
    $allModels: {
      async $allOperations({ model, operation, args, query }) {
        const start = Date.now()
        const result = await query(args)
        const duration = Date.now() - start

        if (['create', 'update', 'delete', 'upsert'].includes(operation)) {
          console.log(JSON.stringify({
            timestamp: new Date().toISOString(),
            model,
            operation,
            args: JSON.stringify(args),
            duration,
          }))
        }

        return result
      },
    },
  },
})
```

### Query Timing

```typescript
const queryTiming = Prisma.defineExtension({
  name: 'queryTiming',
  query: {
    $allModels: {
      async $allOperations({ model, operation, args, query }) {
        const start = performance.now()
        const result = await query(args)
        const duration = performance.now() - start

        if (duration > 100) {
          console.warn(`Slow query: ${model}.${operation} took ${duration.toFixed(1)}ms`)
        }

        return result
      },
    },
  },
})
```

### Row-Level Security (RLS)

Create tenant-scoped clients for multi-tenant applications:

```typescript
function forTenant(tenantId: string) {
  return new PrismaClient().$extends({
    name: `tenant-${tenantId}`,
    query: {
      $allModels: {
        async $allOperations({ model, operation, args, query }) {
          // Inject tenantId into all WHERE clauses
          if (['findMany', 'findFirst', 'findUnique', 'count'].includes(operation)) {
            args.where = { ...args.where, tenantId }
          }
          // Inject tenantId into all CREATE data
          if (['create', 'createMany'].includes(operation)) {
            if (Array.isArray(args.data)) {
              args.data = args.data.map(d => ({ ...d, tenantId }))
            } else {
              args.data = { ...args.data, tenantId }
            }
          }
          return query(args)
        },
      },
    },
  })
}

// Usage: each request gets a tenant-scoped client
app.use((req, res, next) => {
  req.prisma = forTenant(req.headers['x-tenant-id'])
  next()
})
```

Each tenant-scoped client is isolated but shares the underlying connection pool.

## Result Extensions

Add computed fields to query results:

```typescript
const prisma = new PrismaClient().$extends({
  result: {
    user: {
      fullName: {
        needs: { firstName: true, lastName: true },
        compute(user) {
          return `${user.firstName} ${user.lastName}`
        },
      },
      profileUrl: {
        needs: { id: true },
        compute(user) {
          return `/users/${user.id}`
        },
      },
    },
  },
})

const user = await prisma.user.findUnique({
  where: { id: 1 },
  select: { fullName: true, profileUrl: true },  // Computed fields available in select
})
// { fullName: 'Alice Smith', profileUrl: '/users/1' }
```

The `needs` object declares which database fields are required for the computation. Prisma automatically fetches them even if not in the `select`.

## Client Extensions

Add methods to the Prisma Client instance itself:

```typescript
const prisma = new PrismaClient().$extends({
  client: {
    async $truncateAll() {
      const tableNames = await prisma.$queryRaw<{ tablename: string }[]>`
        SELECT tablename FROM pg_tables WHERE schemaname = 'public'
      `
      const tables = tableNames
        .map(t => t.tablename)
        .filter(name => name !== '_prisma_migrations')
        .map(name => `"public"."${name}"`)
        .join(', ')

      await prisma.$executeRawUnsafe(`TRUNCATE TABLE ${tables} CASCADE`)
    },
  },
})

// Usage (e.g., in test setup)
await prisma.$truncateAll()
```

## Composing Multiple Extensions

Chain extensions to build up functionality:

```typescript
const prisma = new PrismaClient()
  .$extends(softDelete)
  .$extends(auditLog)
  .$extends(queryTiming)
  .$extends(computedFields)
```

Extensions execute in declaration order. For query extensions, the first extension wraps the query, the second wraps the first, and so on -- like middleware layers.

### Typing Extended Clients

```typescript
// Infer the type of an extended client
const extendedPrisma = new PrismaClient()
  .$extends(softDelete)
  .$extends(auditLog)

type ExtendedPrismaClient = typeof extendedPrisma

// For singleton pattern
function getExtendedClient() {
  return new PrismaClient()
    .$extends(softDelete)
    .$extends(auditLog)
}

type ExtendedPrismaClient = ReturnType<typeof getExtendedClient>
```

## Shared Extensions

Publish reusable extensions as npm packages:

```typescript
// my-prisma-extension/index.ts
import { Prisma } from '@prisma/client'

export const myExtension = Prisma.defineExtension({
  name: 'my-extension',
  query: { /* ... */ },
})
```

Notable community extensions:

| Extension | Purpose |
|-----------|---------|
| `prisma-extension-caching` | Query result caching (Redis, in-memory) |
| `prisma-extension-read-replicas` | Route reads to replicas |
| `prisma-extension-pagination` | Cursor-based pagination helpers |
| `prisma-extension-bark` | Nested set (tree) operations |

## Migration from Middleware

Replace deprecated `$use` middleware with query extensions:

```typescript
// OLD: Deprecated middleware
prisma.$use(async (params, next) => {
  const start = Date.now()
  const result = await next(params)
  console.log(`${params.model}.${params.action}: ${Date.now() - start}ms`)
  return result
})

// NEW: Query extension (recommended)
const prisma = new PrismaClient().$extends({
  query: {
    $allModels: {
      async $allOperations({ model, operation, args, query }) {
        const start = Date.now()
        const result = await query(args)
        console.log(`${model}.${operation}: ${Date.now() - start}ms`)
        return result
      },
    },
  },
})
```

Key differences:
- Extensions are type-safe; middleware was not
- Extensions create new client instances; middleware mutated the original
- Extensions compose cleanly; middleware order was implicit
- Extensions support `result` and `model` components; middleware only intercepted queries
