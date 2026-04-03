# Transactions and Performance

Sources: Drizzle ORM v1.x documentation (orm.drizzle.team), PostgreSQL documentation (postgresql.org), 2025-2026 serverless deployment patterns

Covers: transactions (basic, nested/savepoints, rollback, isolation levels), prepared statements, connection pooling, query logging, performance optimization patterns, and serverless considerations.

## Transactions

### Basic Transaction

```typescript
await db.transaction(async (tx) => {
  await tx.update(accounts).set({ balance: sql`${accounts.balance} - 100` }).where(eq(accounts.id, 1));
  await tx.update(accounts).set({ balance: sql`${accounts.balance} + 100` }).where(eq(accounts.id, 2));
});
```

All statements inside the callback execute within a single database transaction. If any statement throws, the entire transaction rolls back.

### Returning Values from Transactions

```typescript
const newBalance = await db.transaction(async (tx) => {
  await tx.update(accounts)
    .set({ balance: sql`${accounts.balance} - 100` })
    .where(eq(accounts.id, 1));

  const [account] = await tx.select({ balance: accounts.balance })
    .from(accounts).where(eq(accounts.id, 1));

  return account.balance;
});
```

### Manual Rollback

```typescript
await db.transaction(async (tx) => {
  const [account] = await tx.select({ balance: accounts.balance })
    .from(accounts).where(eq(accounts.id, 1));

  if (account.balance < 100) {
    tx.rollback();  // throws internally, rolls back all changes
    return;         // unreachable, but satisfies TypeScript
  }

  await tx.update(accounts)
    .set({ balance: sql`${accounts.balance} - 100` })
    .where(eq(accounts.id, 1));
});
```

`tx.rollback()` throws an exception caught by the transaction wrapper. Do not catch it inside the callback.

### Nested Transactions (Savepoints)

```typescript
await db.transaction(async (tx) => {
  await tx.insert(orders).values({ userId: 1, total: 200 });

  await tx.transaction(async (tx2) => {
    // This creates a SAVEPOINT
    await tx2.insert(orderItems).values({ orderId: 1, productId: 5, quantity: 2 });
    // If tx2 fails, only the savepoint rolls back, not the outer transaction
  });

  await tx.update(users).set({ orderCount: sql`${users.orderCount} + 1` }).where(eq(users.id, 1));
});
```

### Transaction Isolation Levels

Configure isolation per transaction (PostgreSQL example):

```typescript
await db.transaction(async (tx) => {
  const [row] = await tx.select().from(inventory).where(eq(inventory.id, 1));
  await tx.update(inventory)
    .set({ stock: row.stock - 1 })
    .where(eq(inventory.id, 1));
}, {
  isolationLevel: "serializable",
  accessMode: "read write",
});
```

#### PostgreSQL Isolation Levels

| Level | Dirty Read | Non-Repeatable Read | Phantom Read | Use Case |
|-------|-----------|-------------------|-------------|----------|
| `read uncommitted` | Possible | Possible | Possible | PG treats as read committed |
| `read committed` | No | Possible | Possible | Default. Good for most OLTP |
| `repeatable read` | No | No | Possible* | Consistent reads within transaction |
| `serializable` | No | No | No | Financial operations, inventory |

*PostgreSQL's repeatable read actually prevents phantom reads via snapshot isolation.

#### MySQL Isolation Levels

```typescript
await db.transaction(async (tx) => { /* ... */ }, {
  isolationLevel: "repeatable read",
  accessMode: "read write",
  withConsistentSnapshot: true,
});
```

#### SQLite Transaction Behavior

```typescript
await db.transaction(async (tx) => { /* ... */ }, {
  behavior: "immediate",  // "deferred" | "immediate" | "exclusive"
});
```

| Behavior | Lock Acquired | Use Case |
|----------|--------------|----------|
| `deferred` | On first write | Default, read-mostly |
| `immediate` | On transaction start | Write-heavy, prevents SQLITE_BUSY |
| `exclusive` | Exclusive lock | Full isolation, blocks all other connections |

## Using Transactions with Relational Queries

```typescript
const db = drizzle({ connection: process.env.DATABASE_URL!, schema });

await db.transaction(async (tx) => {
  const user = await tx.query.users.findFirst({
    where: eq(users.id, 1),
    with: { posts: true },
  });
  // use user data within the same transaction
});
```

## Prepared Statements

Prepare statements once, execute many times with different parameters. Eliminates repeated query planning overhead.

```typescript
const getUserById = db.select().from(users).where(eq(users.id, sql.placeholder("id"))).prepare("get_user_by_id");

// Execute multiple times with different parameters
const user1 = await getUserById.execute({ id: 1 });
const user2 = await getUserById.execute({ id: 2 });
const user3 = await getUserById.execute({ id: 3 });
```

### Multiple Placeholders

```typescript
const getFilteredUsers = db.select().from(users)
  .where(and(
    eq(users.role, sql.placeholder("role")),
    gt(users.age, sql.placeholder("minAge")),
  ))
  .limit(sql.placeholder("limit"))
  .prepare("get_filtered_users");

const admins = await getFilteredUsers.execute({ role: "admin", minAge: 18, limit: 50 });
```

### When to Use Prepared Statements

| Scenario | Benefit |
|----------|---------|
| Hot queries executed thousands of times | Skip query planning on each call |
| Parameterized filters in API endpoints | Consistent plan reuse |
| Serverless with connection pooling | Less overhead per invocation |
| Queries with static structure | Plan cached across executions |

For most applications, the performance difference is negligible. Prefer prepared statements for high-traffic endpoints.

## Connection Pooling

### node-postgres Pool

```typescript
import { Pool } from "pg";
import { drizzle } from "drizzle-orm/node-postgres";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,              // maximum pool size
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

const db = drizzle({ client: pool });
```

### postgres.js (Supabase / General PG)

```typescript
import postgres from "postgres";
import { drizzle } from "drizzle-orm/postgres-js";

const client = postgres(process.env.DATABASE_URL!, {
  max: 10,
  idle_timeout: 20,
  connect_timeout: 10,
});

const db = drizzle({ client });
```

### Pool Sizing Guidelines

| Environment | Recommended Max | Rationale |
|-------------|----------------|-----------|
| Single server app | 10-30 | Matches typical CPU core count |
| Serverless (per function) | 1-3 | Each invocation gets its own pool |
| Serverless with pooler (PgBouncer/Supavisor) | 5-10 per instance | Pooler manages total connections |
| Edge runtime (Neon/D1) | HTTP-based, no pool | Each query is an HTTP request |

### Connection Pooling Services

| Service | Pooler | Connection Pattern |
|---------|--------|--------------------|
| Supabase | Supavisor (built-in) | Use pooler URL (port 6543) for serverless |
| Neon | Neon Proxy (built-in) | HTTP driver for serverless, TCP for long-lived |
| Self-hosted PG | PgBouncer | Place between app and database |
| AWS RDS | RDS Proxy | Managed connection pooling |

## Query Logging

### Built-in Logger

```typescript
const db = drizzle({
  connection: process.env.DATABASE_URL!,
  logger: true,  // logs all queries to console
});
```

### Custom Logger

```typescript
import { DefaultLogger, LogWriter } from "drizzle-orm";

class CustomLogWriter implements LogWriter {
  write(message: string) {
    // send to your logging service
    myLogger.info(message);
  }
}

const db = drizzle({
  connection: process.env.DATABASE_URL!,
  logger: new DefaultLogger({ writer: new CustomLogWriter() }),
});
```

## Performance Patterns

### Select Only Needed Columns

```typescript
// Avoid: fetches all columns
const users = await db.select().from(users);

// Prefer: fetch only what the API response needs
const users = await db.select({ id: users.id, name: users.name }).from(users);
```

### Use Indexes Effectively

Define indexes in the schema for frequently queried columns:

```typescript
export const posts = pgTable("posts", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  authorId: integer("author_id").notNull(),
  status: varchar({ length: 50 }).notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
}, (table) => [
  index("posts_author_idx").on(table.authorId),
  index("posts_status_created_idx").on(table.status, table.createdAt),
]);
```

### Batch Inserts Over Individual Inserts

```typescript
// Slow: N individual INSERT statements
for (const item of items) {
  await db.insert(products).values(item);
}

// Fast: single INSERT with multiple values
await db.insert(products).values(items);
```

### Cursor-Based Pagination

```typescript
// Offset pagination (slow for large offsets)
const page = await db.select().from(posts).limit(20).offset(1000);

// Cursor pagination (consistent performance)
const page = await db.select().from(posts)
  .where(gt(posts.id, lastSeenId))
  .orderBy(asc(posts.id))
  .limit(20);
```

### Avoid N+1 in Loops

```typescript
// N+1 problem: 1 query for users + N queries for posts
const users = await db.select().from(users);
for (const user of users) {
  const posts = await db.select().from(posts).where(eq(posts.authorId, user.id));
}

// Fix: use relational query or a single join
const usersWithPosts = await db.query.users.findMany({
  with: { posts: true },
});
```

## Performance Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| No connection pooling | Opens new connection per query | Use `Pool` or `postgres()` with `max` |
| `SELECT *` on wide tables | Transfers unnecessary data | Select specific columns |
| Missing indexes on FK columns | Slow joins and lookups | Add index on every foreign key |
| Large OFFSET pagination | Full table scan up to offset | Switch to cursor-based pagination |
| Synchronous migrations at cold start | Slow serverless cold start | Run migrations in build step |
| Not using prepared statements on hot paths | Repeated query planning | Prepare frequently-used queries |
| Logging in production without filtering | I/O overhead from verbose logging | Use custom logger with sampling |
