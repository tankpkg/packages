# Transactions and Raw SQL

Sources: Prisma ORM Documentation (prisma.io/docs), Prisma Blog engineering posts, PostgreSQL documentation (postgresql.org/docs), 2025-2026 production patterns

Covers: Sequential and interactive transactions, isolation levels, nested writes as transactions, optimistic concurrency control, raw SQL methods ($queryRaw, $executeRaw, unsafe variants), TypedSQL, SQL injection prevention, and transaction retry patterns.

## Transaction Types

Prisma Client supports three approaches to transactions, each suited to different scenarios:

| Approach | Mechanism | Use Case |
|----------|-----------|----------|
| Nested writes | Single Prisma operation with related records | Create/update parent + children atomically |
| `$transaction([])` | Array of independent Prisma operations | Multiple unrelated writes that must all succeed |
| Interactive `$transaction(async (tx) => {})` | Callback with transaction client | Read-modify-write, conditional logic between queries |

### Nested Writes (Implicit Transaction)

Every nested write runs in a single transaction automatically:

```typescript
const user = await prisma.user.create({
  data: {
    email: 'alice@example.com',
    posts: {
      create: [
        { title: 'Post 1' },
        { title: 'Post 2' },
      ],
    },
    profile: {
      create: { bio: 'Hello' },
    },
  },
})
// All three records created atomically -- if any fails, all roll back
```

Prefer nested writes when operations are dependent (child needs parent ID). The `$transaction([])` API cannot pass generated IDs between operations.

### Sequential Transaction

Pass an array of Prisma Client operations. They execute sequentially in a single transaction:

```typescript
const [posts, totalPosts] = await prisma.$transaction([
  prisma.post.findMany({ where: { published: true } }),
  prisma.post.count({ where: { published: true } }),
])
```

Use for independent writes that must succeed or fail together:

```typescript
const deletePosts = prisma.post.deleteMany({ where: { authorId: 7 } })
const deleteMessages = prisma.message.deleteMany({ where: { userId: 7 } })
const deleteUser = prisma.user.delete({ where: { id: 7 } })

await prisma.$transaction([deletePosts, deleteMessages, deleteUser])
```

Operations execute in array order. Place deletes of child records before parent records.

### Interactive Transaction

For read-modify-write patterns where logic runs between database calls:

```typescript
const result = await prisma.$transaction(async (tx) => {
  // 1. Read
  const sender = await tx.account.update({
    data: { balance: { decrement: 100 } },
    where: { email: 'alice@example.com' },
  })

  // 2. Validate
  if (sender.balance < 0) {
    throw new Error('Insufficient funds')  // Rolls back entire transaction
  }

  // 3. Write
  const recipient = await tx.account.update({
    data: { balance: { increment: 100 } },
    where: { email: 'bob@example.com' },
  })

  return recipient
})
```

The `tx` parameter is a transaction-scoped Prisma Client. All queries through `tx` share the same database transaction. If the callback throws, the transaction rolls back.

### Transaction Options

```typescript
await prisma.$transaction(
  async (tx) => { /* ... */ },
  {
    maxWait: 5000,       // Max ms to wait to acquire transaction (default: 2000)
    timeout: 10000,      // Max ms for transaction to complete (default: 5000)
    isolationLevel: Prisma.TransactionIsolationLevel.Serializable,
  }
)
```

Keep transactions short. Long-running transactions hold database locks, degrade performance, and risk deadlocks. Avoid network calls or slow computations inside transaction callbacks.

## Isolation Levels

| Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Use Case |
|-------|------------|---------------------|---------------|----------|
| `ReadUncommitted` | Possible | Possible | Possible | Analytics (rare) |
| `ReadCommitted` | No | Possible | Possible | PostgreSQL default |
| `RepeatableRead` | No | No | Possible | MySQL default |
| `Serializable` | No | No | No | Financial, booking systems |

Set per-transaction when the default is insufficient:

```typescript
await prisma.$transaction(
  [prisma.seat.updateMany({ /* ... */ })],
  { isolationLevel: Prisma.TransactionIsolationLevel.Serializable }
)
```

### Handling Write Conflicts

At `ReadCommitted` (PostgreSQL default), concurrent transactions can cause write conflicts. When using `Serializable`, Prisma returns error code `P2034` on conflict. Implement retry logic:

```typescript
async function withRetry<T>(fn: () => Promise<T>, maxRetries = 5): Promise<T> {
  let retries = 0
  while (retries < maxRetries) {
    try {
      return await fn()
    } catch (error) {
      if (error.code === 'P2034') {
        retries++
        continue
      }
      throw error
    }
  }
  throw new Error(`Transaction failed after ${maxRetries} retries`)
}
```

## Optimistic Concurrency Control

For high-concurrency scenarios (booking systems, inventory), avoid database locks. Add a `version` field and check it during updates:

```typescript
// Schema: model Seat { ... version Int }

const seat = await prisma.seat.findFirst({
  where: { movieId: 1, claimedBy: null },
})

if (!seat) throw new Error('No seats available')

const result = await prisma.seat.updateMany({
  data: {
    claimedBy: userId,
    version: { increment: 1 },
  },
  where: {
    id: seat.id,
    version: seat.version,  // Only update if version matches
  },
})

if (result.count === 0) {
  throw new Error('Seat already booked -- try again')
}
```

`updateMany` returns `{ count: 0 }` if the version changed (another transaction modified the row). This avoids double-booking without database locks.

## Raw SQL

### When to Use Raw SQL

| Scenario | Method |
|----------|--------|
| Complex queries (CTEs, window functions) | `$queryRaw` |
| Bulk operations (ON CONFLICT, COPY) | `$executeRaw` |
| DDL statements (CREATE INDEX CONCURRENTLY) | `$executeRawUnsafe` |
| Dynamic table/column names | `$queryRawUnsafe` with parameterized values |
| Type-safe raw SQL | TypedSQL (`.sql` files) |

### $queryRaw (Safe -- Tagged Template)

```typescript
const email = 'alice@example.com'
const users = await prisma.$queryRaw`
  SELECT id, name, email FROM "User" WHERE email = ${email}
`
```

Tagged templates create prepared statements -- variables are automatically escaped. The template handles parameterization per database (`$1` for PostgreSQL, `?` for MySQL).

Type the result:

```typescript
type UserResult = { id: number; name: string; email: string }
const users = await prisma.$queryRaw<UserResult[]>`
  SELECT id, name, email FROM "User" WHERE email = ${email}
`
```

### Template Helpers

```typescript
import { Prisma } from '@prisma/client'

// Join a list of values
const ids = [1, 3, 5, 10]
const users = await prisma.$queryRaw`
  SELECT * FROM "User" WHERE id IN (${Prisma.join(ids)})
`

// Conditional clauses
const name = ''
const users = await prisma.$queryRaw`
  SELECT * FROM "User"
  ${name ? Prisma.sql`WHERE name = ${name}` : Prisma.empty}
`
```

### $executeRaw (Safe -- Returns Affected Row Count)

```typescript
const count = await prisma.$executeRaw`
  UPDATE "User" SET active = true WHERE "emailValidated" = true
`
// count: number (rows affected)
```

### Unsafe Variants

`$queryRawUnsafe` and `$executeRawUnsafe` accept raw strings. Use parameterized queries to prevent SQL injection:

```typescript
// SAFE: parameterized
const users = await prisma.$queryRawUnsafe(
  'SELECT * FROM "User" WHERE email = $1 AND role = $2',
  'alice@example.com',
  'ADMIN'
)

// DANGEROUS: string interpolation -- never use with user input
const users = await prisma.$queryRawUnsafe(
  `SELECT * FROM "User" WHERE email = '${userInput}'`  // SQL injection risk
)
```

### Template Variable Limitations

Variables in tagged templates can only represent data values, not identifiers:

```typescript
// Works: data value
const email = 'alice@example.com'
await prisma.$queryRaw`SELECT * FROM "User" WHERE email = ${email}`

// Fails: table name cannot be a variable
const table = 'User'
await prisma.$queryRaw`SELECT * FROM ${table}`  // Error
```

For dynamic identifiers, use `$queryRawUnsafe` with an allowlist:

```typescript
const allowedTables = ['User', 'Post', 'Comment'] as const
function queryTable(table: typeof allowedTables[number]) {
  if (!allowedTables.includes(table)) throw new Error('Invalid table')
  return prisma.$queryRawUnsafe(`SELECT * FROM "${table}"`)
}
```

### TypedSQL

Write SQL in `.sql` files and get type-safe results:

```sql
-- prisma/sql/getUserPosts.sql
SELECT u.id, u.name, COUNT(p.id) as "postCount"
FROM "User" u
LEFT JOIN "Post" p ON p."authorId" = u.id
WHERE u.id = $1
GROUP BY u.id, u.name
```

```typescript
import { getUserPosts } from '@prisma/client/sql'

const result = await prisma.$queryRawTyped(getUserPosts(userId))
// result is fully typed based on the SQL query
```

Run `prisma generate --sql` to generate types from `.sql` files. TypedSQL provides the safety of Prisma Client with the power of raw SQL.

## Raw SQL in Transactions

Combine raw SQL with Prisma Client operations in transactions:

```typescript
await prisma.$transaction([
  prisma.user.create({ data: { email: 'alice@example.com' } }),
  prisma.$executeRaw`UPDATE "stats" SET "userCount" = "userCount" + 1`,
])
```

Interactive transactions also support raw SQL through the `tx` client:

```typescript
await prisma.$transaction(async (tx) => {
  const user = await tx.user.create({ data: { email: 'alice@example.com' } })
  await tx.$executeRaw`
    INSERT INTO "audit_log" ("action", "userId") VALUES ('create', ${user.id})
  `
})
```

## SQL Injection Prevention

| Method | Safety | Use When |
|--------|--------|----------|
| `$queryRaw` (tagged template) | Safe by default | Standard raw queries |
| `$executeRaw` (tagged template) | Safe by default | DML operations |
| `$queryRawUnsafe` + parameters | Safe with parameterization | Dynamic identifiers needed |
| `$queryRawUnsafe` + interpolation | Dangerous | Never with user input |
| `Prisma.sql` helper | Safe | Building queries programmatically |
| `Prisma.raw()` | Dangerous if misused | Only with trusted content |

Always prefer tagged templates. Use `Prisma.join()` for IN clauses and `Prisma.sql` for dynamic query composition. Never concatenate user input into raw strings.
