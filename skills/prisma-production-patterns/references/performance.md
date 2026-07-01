# Performance Optimization

Sources: Prisma ORM Documentation (prisma.io/docs), Prisma Blog (prisma.io/blog), Prisma Optimize documentation, 2025-2026 production performance patterns

Covers: N+1 detection and prevention, connection pooling with v7 driver adapters, query logging and analysis, select optimization, batch operations, PgBouncer integration, and Prisma Optimize.

## N+1 Problem

The N+1 problem occurs when code executes one query to fetch a list (1), then one query per item to fetch related data (N). With 100 users, fetching their posts becomes 101 queries instead of 2.

### Detecting N+1

Enable query logging to spot N+1 patterns:

```typescript
const prisma = new PrismaClient({
  log: [{ level: 'query', emit: 'event' }],
})

prisma.$on('query', (e) => {
  console.log(`${e.query} [${e.duration}ms]`)
})
```

Symptoms of N+1:
- Repeated identical query patterns with different parameter values
- Response times that scale linearly with result count
- Database connection pool exhaustion under moderate load

### Common N+1 Patterns and Fixes

**Pattern 1: Loop with findUnique**

```typescript
// BAD: N+1 -- one query per user
const users = await prisma.user.findMany()
for (const user of users) {
  const posts = await prisma.post.findMany({
    where: { authorId: user.id },
  })
}

// GOOD: Single query with include
const users = await prisma.user.findMany({
  include: { posts: true },
})
```

**Pattern 2: GraphQL resolvers**

```typescript
// BAD: Each resolver triggers a separate query
const resolvers = {
  User: {
    posts: (parent) => prisma.post.findMany({
      where: { authorId: parent.id },
    }),
  },
}

// GOOD: Use dataloader or include in parent query
const resolvers = {
  Query: {
    users: () => prisma.user.findMany({
      include: { posts: true },
    }),
  },
}
```

**Pattern 3: Conditional relation loading**

```typescript
// BAD: Fetching relations only when needed, but in a loop
const users = await prisma.user.findMany()
const usersWithPosts = await Promise.all(
  users.map(async (user) => ({
    ...user,
    posts: user.role === 'AUTHOR'
      ? await prisma.post.findMany({ where: { authorId: user.id } })
      : [],
  }))
)

// GOOD: Filter at the database level
const authors = await prisma.user.findMany({
  where: { role: 'AUTHOR' },
  include: { posts: true },
})
```

### Fluent API and N+1

The fluent API does NOT cause N+1 -- it translates to a single query with a JOIN:

```typescript
// This is ONE query, not two
const posts = await prisma.user
  .findUnique({ where: { id: 1 } })
  .posts()
```

Prisma batches the `findUnique` + `.posts()` into a single query. This is safe to use.

## Select Optimization

### Fetch Only What You Need

```typescript
// BAD: Fetches all columns including large text fields
const users = await prisma.user.findMany()

// GOOD: Fetch only needed fields
const users = await prisma.user.findMany({
  select: {
    id: true,
    email: true,
    name: true,
  },
})
```

Benefits of `select`:
- Reduces data transferred from database to application
- Reduces memory usage for large result sets
- Avoids fetching large `Json` or `String` fields unnecessarily
- Improves serialization speed for API responses

### Nested Select for Relations

```typescript
const users = await prisma.user.findMany({
  select: {
    id: true,
    name: true,
    posts: {
      select: { id: true, title: true },
      where: { published: true },
      orderBy: { createdAt: 'desc' },
      take: 5,
    },
  },
})
```

Apply `where`, `orderBy`, and `take` to nested relations to limit fetched data at the database level.

## Connection Pooling

### Prisma v7 Driver Adapters

Prisma v7 uses driver adapters by default. Connection pooling is managed by the underlying Node.js driver:

```typescript
import { PrismaPg } from '@prisma/adapter-pg'
import { PrismaClient } from '@prisma/client'

const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL,
  max: 10,                      // Pool size (default: 10)
  idleTimeoutMillis: 10_000,    // Close idle connections after 10s
  connectionTimeoutMillis: 5_000, // Connection acquire timeout
})

const prisma = new PrismaClient({ adapter })
```

### Pool Size Guidelines

| Environment | Recommended Pool Size | Reasoning |
|-------------|----------------------|-----------|
| Single server app | `num_cpus * 2 + 1` | Match parallelism to hardware |
| Serverless function | 1-5 | Each invocation creates a pool |
| Multiple app instances | `db_max_connections / instances` | Divide total budget |
| Development | 2-5 | Low concurrency needs |

### Pool Size Formula

```
pool_size = db_max_connections / number_of_application_instances
```

PostgreSQL default `max_connections` is 100. With 10 serverless functions, each gets a pool of 10. Exceeding this causes `P2024` (connection pool timeout) errors.

### Connection Lifecycle

```
Application start
  -> PrismaClient instantiated (no connections yet)
  -> First query triggers $connect()
  -> Connection pool created (up to `max` connections)
  -> Queries acquire/release connections from pool
  -> Idle connections closed after idleTimeoutMillis
Application shutdown
  -> $disconnect() releases all connections
```

Always call `$disconnect()` in graceful shutdown handlers:

```typescript
process.on('SIGTERM', async () => {
  await prisma.$disconnect()
  process.exit(0)
})
```

## PgBouncer Integration

PgBouncer sits between your application and PostgreSQL, multiplexing many application connections over fewer database connections.

### When to Use PgBouncer

| Signal | Recommendation |
|--------|---------------|
| Serverless with many concurrent functions | Use PgBouncer or Prisma Accelerate |
| Connection count exceeds PostgreSQL limit | Use PgBouncer |
| Single long-running server | Direct connection (PgBouncer optional) |
| Managed database with built-in pooler | Use the managed pooler (Supabase, Neon) |

### Configuration

```
# Connection string with PgBouncer
DATABASE_URL="postgresql://user:pass@pgbouncer-host:6432/mydb?pgbouncer=true"
```

The `?pgbouncer=true` parameter tells Prisma to:
- Disable prepared statements (PgBouncer in transaction mode does not support them)
- Adjust connection handling for pooler compatibility

### PgBouncer Pool Modes

| Mode | Description | Prisma Compatible |
|------|-------------|-------------------|
| Transaction | Connection returned after each transaction | Yes (recommended) |
| Session | Connection held for entire session | Yes (but defeats purpose) |
| Statement | Connection returned after each statement | No (breaks transactions) |

Use transaction mode. Prisma's interactive transactions work correctly with PgBouncer in transaction mode.

## Batch Operations

### Batch Reads with $transaction

```typescript
// Batch multiple reads into a single round-trip
const [users, posts, stats] = await prisma.$transaction([
  prisma.user.findMany({ where: { active: true } }),
  prisma.post.findMany({ where: { published: true }, take: 10 }),
  prisma.user.count(),
])
```

### Batch Writes

```typescript
// createMany: single INSERT with multiple rows
const { count } = await prisma.user.createMany({
  data: users,
  skipDuplicates: true,
})

// updateMany: single UPDATE with WHERE clause
await prisma.post.updateMany({
  where: { authorId: deletedUserId },
  data: { authorId: fallbackUserId },
})
```

`createMany` is significantly faster than multiple `create` calls because it generates a single INSERT statement.

### Bulk Operations Performance

| Operation | Single Loop | Batch API | Improvement |
|-----------|------------|-----------|-------------|
| Insert 1000 rows | ~1000 queries, ~5s | 1 query, ~100ms | 50x |
| Update 1000 rows | ~1000 queries, ~5s | 1 query, ~50ms | 100x |
| Delete 1000 rows | ~1000 queries, ~5s | 1 query, ~30ms | 167x |

### Bulk Upsert (Raw SQL)

Prisma does not support bulk upsert natively. Use raw SQL:

```typescript
await prisma.$executeRaw`
  INSERT INTO "User" ("email", "name")
  VALUES ${Prisma.join(
    users.map(u => Prisma.sql`(${u.email}, ${u.name})`)
  )}
  ON CONFLICT ("email")
  DO UPDATE SET "name" = EXCLUDED."name"
`
```

## Query Logging and Debugging

### Log Levels

```typescript
const prisma = new PrismaClient({
  log: ['query', 'info', 'warn', 'error'],
})
```

| Level | Output |
|-------|--------|
| `query` | SQL queries with parameters and duration |
| `info` | Connection pool events |
| `warn` | Potential issues |
| `error` | Query failures |

### Event-Based Logging

```typescript
const prisma = new PrismaClient({
  log: [{ level: 'query', emit: 'event' }],
})

prisma.$on('query', (e) => {
  if (e.duration > 100) {
    console.warn(`Slow query (${e.duration}ms): ${e.query}`)
  }
})
```

Log slow queries (>100ms) in production to identify optimization targets.

### Prisma Optimize

Prisma Optimize analyzes queries and suggests improvements:

1. Add `@prisma/optimize` to your project
2. Generate a Prisma Optimize API key
3. Run with the Optimize extension to get recommendations

Recommendations include missing indexes, N+1 detection, and query restructuring suggestions.

## Performance Checklist

| Check | Action |
|-------|--------|
| N+1 queries | Use `include` or `select` with nested relations |
| Large payloads | Use `select` to fetch only needed fields |
| Slow list queries | Add database indexes on filtered/sorted columns |
| Connection exhaustion | Configure pool size, use PgBouncer for serverless |
| Bulk operations | Use `createMany`/`updateMany` instead of loops |
| Complex aggregations | Consider raw SQL or database views |
| API response time | Enable query logging, profile slow queries |
| Pagination depth | Switch from offset to cursor-based pagination |

## Performance Review Questions

1. Is the bottleneck query count, payload size, or connection management?
2. Would query shaping fix this before caching or raw SQL is needed?
3. Is the hot path serverful, serverless, or edge-adjacent?

## Performance Smells

| Smell | Why it matters |
|------|----------------|
| broad `include` trees everywhere | payload and query overhead |
| offset pagination on deep lists | scaling pain |
| one performance dashboard with no route attribution | low actionability |
