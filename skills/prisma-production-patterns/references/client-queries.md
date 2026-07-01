# Client Queries

Sources: Prisma ORM Documentation (prisma.io/docs), Prisma Client API Reference, 2025-2026 production query patterns

Covers: CRUD operations, filtering and sorting, pagination (cursor vs offset), field selection (select/include), nested reads and writes, relation queries, aggregation, grouping, and the fluent API.

## Prisma Client Setup

### Singleton Pattern (Recommended)

Instantiate one Prisma Client per application. Multiple instances create separate connection pools, exhausting database connections.

```typescript
// lib/prisma.ts
import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient }

export const prisma = globalForPrisma.prisma ?? new PrismaClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma
```

The `globalThis` trick prevents hot-reload in development from creating new instances. In production, the module cache handles singleton behavior naturally.

### Logging Configuration

```typescript
const prisma = new PrismaClient({
  log: [
    { level: 'query', emit: 'event' },
    { level: 'error', emit: 'stdout' },
    { level: 'warn', emit: 'stdout' },
  ],
})

prisma.$on('query', (e) => {
  console.log(`Query: ${e.query}`)
  console.log(`Duration: ${e.duration}ms`)
})
```

Enable `query` logging during development to inspect generated SQL. Remove in production to avoid performance overhead.

## CRUD Operations

### Create

```typescript
// Single record
const user = await prisma.user.create({
  data: { email: 'alice@example.com', name: 'Alice' },
})

// Multiple records (returns count)
const { count } = await prisma.user.createMany({
  data: [
    { email: 'bob@example.com', name: 'Bob' },
    { email: 'carol@example.com', name: 'Carol' },
  ],
  skipDuplicates: true,  // Skip on unique constraint violation
})

// Multiple records with return (PostgreSQL, CockroachDB, SQLite)
const users = await prisma.user.createManyAndReturn({
  data: [
    { email: 'dave@example.com', name: 'Dave' },
    { email: 'eve@example.com', name: 'Eve' },
  ],
})
```

### Read

```typescript
// By unique field
const user = await prisma.user.findUnique({
  where: { email: 'alice@example.com' },
})

// First match (non-unique fields, with ordering)
const post = await prisma.post.findFirst({
  where: { published: true },
  orderBy: { createdAt: 'desc' },
})

// findUniqueOrThrow / findFirstOrThrow -- throw if not found
const user = await prisma.user.findUniqueOrThrow({
  where: { id: 1 },
})

// All matching records
const posts = await prisma.post.findMany({
  where: { published: true },
  orderBy: { createdAt: 'desc' },
  take: 20,
})
```

Use `findUniqueOrThrow` and `findFirstOrThrow` to avoid null checks when the record must exist. They throw `PrismaClientKnownRequestError` with code `P2025`.

### Update

```typescript
// Single record (must match unique field)
const user = await prisma.user.update({
  where: { email: 'alice@example.com' },
  data: { name: 'Alice Updated' },
})

// Multiple records (returns count)
const { count } = await prisma.user.updateMany({
  where: { role: 'USER' },
  data: { active: true },
})

// Atomic number operations
await prisma.post.update({
  where: { id: 1 },
  data: {
    views:    { increment: 1 },
    likes:    { increment: 1 },
    priority: { multiply: 2 },
  },
})
```

### Upsert

```typescript
const user = await prisma.user.upsert({
  where: { email: 'alice@example.com' },
  update: { name: 'Alice Updated' },
  create: { email: 'alice@example.com', name: 'Alice' },
})
```

Upsert is atomic -- use it instead of `findUnique` + conditional `create`/`update` to avoid race conditions. Emulate `findOrCreate` by passing an empty `update: {}`.

### Delete

```typescript
// Single record
await prisma.user.delete({ where: { id: 1 } })

// Multiple records
await prisma.post.deleteMany({ where: { published: false } })

// All records in a table
await prisma.post.deleteMany({})
```

Deletion fails if related records exist with `Restrict` referential action. Either delete children first in a transaction, or configure `onDelete: Cascade` in the schema.

## Filtering

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `equals` | Exact match (default) | `{ email: 'a@b.com' }` |
| `not` | Negation | `{ role: { not: 'ADMIN' } }` |
| `in` | In list | `{ id: { in: [1, 2, 3] } }` |
| `notIn` | Not in list | `{ id: { notIn: [1, 2] } }` |
| `lt`, `lte`, `gt`, `gte` | Comparisons | `{ age: { gte: 18 } }` |
| `contains` | String contains | `{ name: { contains: 'ali', mode: 'insensitive' } }` |
| `startsWith`, `endsWith` | String prefix/suffix | `{ email: { endsWith: '@example.com' } }` |
| `has` (array) | Array contains value | `{ tags: { has: 'prisma' } }` |
| `hasEvery`, `hasSome` | Array intersection | `{ tags: { hasSome: ['prisma', 'orm'] } }` |

### Combining Conditions

```typescript
const users = await prisma.user.findMany({
  where: {
    AND: [
      { email: { endsWith: '@example.com' } },
      { role: 'ADMIN' },
    ],
    OR: [
      { name: { contains: 'Alice' } },
      { name: { contains: 'Bob' } },
    ],
    NOT: { suspended: true },
  },
})
```

### Relation Filters

```typescript
// Users who have at least one published post
const users = await prisma.user.findMany({
  where: {
    posts: { some: { published: true } },
  },
})

// Users with NO posts
const users = await prisma.user.findMany({
  where: {
    posts: { none: {} },
  },
})

// Users where ALL posts are published
const users = await prisma.user.findMany({
  where: {
    posts: { every: { published: true } },
  },
})
```

## Field Selection

### select -- Include Only Specific Fields

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  select: {
    id: true,
    email: true,
    posts: {
      select: { title: true },
      where: { published: true },
      take: 5,
    },
  },
})
// Type: { id: number; email: string; posts: { title: string }[] }
```

### include -- Add Relations to Full Model

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  include: {
    posts: true,          // All fields of related posts
    profile: true,        // Include 1:1 relation
  },
})
```

`select` and `include` cannot be used together at the same level. Use `select` when you need to limit fields; use `include` when you want the full model plus relations.

## Pagination

### Offset Pagination

```typescript
const page = 2
const pageSize = 20

const posts = await prisma.post.findMany({
  skip: (page - 1) * pageSize,
  take: pageSize,
  orderBy: { createdAt: 'desc' },
})
```

Simple but degrades on large datasets -- the database still scans skipped rows. Acceptable for small tables or admin UIs.

### Cursor-Based Pagination (Recommended for Large Datasets)

```typescript
const posts = await prisma.post.findMany({
  take: 20,
  skip: 1,              // Skip the cursor record itself
  cursor: { id: lastPostId },
  orderBy: { id: 'asc' },
})
```

Cursor pagination maintains consistent performance regardless of page depth. Requires a unique, sequential field as cursor (typically `id` or `createdAt` + `id`).

### Count for Pagination Metadata

```typescript
const [posts, total] = await prisma.$transaction([
  prisma.post.findMany({ skip: 0, take: 20, orderBy: { id: 'desc' } }),
  prisma.post.count({ where: { published: true } }),
])
```

Combine `findMany` with `count` in a transaction to get both results and total count atomically.

## Nested Writes

Create or modify related records in a single atomic operation:

```typescript
const user = await prisma.user.create({
  data: {
    email: 'alice@example.com',
    profile: { create: { bio: 'Hello world' } },
    posts: {
      create: [
        { title: 'First Post' },
        { title: 'Second Post' },
      ],
    },
  },
  include: { profile: true, posts: true },
})
```

### Nested Write Operations

| Operation | Description |
|-----------|-------------|
| `create` | Create related record(s) |
| `createMany` | Bulk create related records |
| `connect` | Link existing record by unique field |
| `connectOrCreate` | Connect if exists, create if not |
| `disconnect` | Unlink a related record |
| `set` | Replace all related records |
| `update` | Update a connected related record |
| `upsert` | Update if connected, create if not |
| `delete` | Delete a connected related record |

## Aggregation and Grouping

```typescript
// Aggregate
const stats = await prisma.post.aggregate({
  _count: true,
  _avg: { views: true },
  _max: { views: true },
  where: { published: true },
})

// Group by
const byStatus = await prisma.post.groupBy({
  by: ['status'],
  _count: true,
  _avg: { views: true },
  orderBy: { _count: { status: 'desc' } },
})

// Distinct
const emails = await prisma.user.findMany({
  distinct: ['email'],
  select: { email: true },
})
```

## Fluent API

Navigate relations from a query result:

```typescript
// Get posts by a specific user (via fluent API)
const posts = await prisma.user
  .findUnique({ where: { id: 1 } })
  .posts()

// Chain deeper
const categories = await prisma.user
  .findUnique({ where: { id: 1 } })
  .posts()
  // Cannot chain further -- fluent API is one level deep per call
```

The fluent API is syntactic sugar that translates to a query with `include`. It does not trigger additional database queries beyond what `include` would generate.
