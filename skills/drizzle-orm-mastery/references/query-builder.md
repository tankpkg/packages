# Query Builder

Sources: Drizzle ORM v1.x documentation (orm.drizzle.team), drizzle-team/drizzle-orm GitHub, Dave Gray (Drizzle subquery patterns), 2025-2026 community examples

Covers: SQL-like query builder API for select, insert, update, delete, joins, where clauses, aggregations, subqueries, raw SQL, and dynamic query construction.

## Select Queries

### Basic Select

```typescript
// Select all columns
const allUsers = await db.select().from(users);

// Select specific columns
const names = await db.select({ name: users.name, email: users.email }).from(users);

// Select with alias
const result = await db.select({
  userId: users.id,
  fullName: users.name,
}).from(users);
```

### Where Clauses

Import operators from `drizzle-orm`:

```typescript
import { eq, ne, gt, gte, lt, lte, like, ilike, between, inArray, notInArray, isNull, isNotNull, and, or, not, sql } from "drizzle-orm";
```

| Operator | SQL | Example |
|----------|-----|---------|
| `eq(col, val)` | `=` | `eq(users.id, 1)` |
| `ne(col, val)` | `<>` | `ne(users.status, "banned")` |
| `gt(col, val)` | `>` | `gt(users.age, 18)` |
| `gte(col, val)` | `>=` | `gte(orders.total, 100)` |
| `lt(col, val)` | `<` | `lt(posts.viewCount, 10)` |
| `lte(col, val)` | `<=` | `lte(users.loginCount, 5)` |
| `like(col, pat)` | `LIKE` | `like(users.name, "%john%")` |
| `ilike(col, pat)` | `ILIKE` (PG) | `ilike(users.email, "%@gmail.com")` |
| `between(col, a, b)` | `BETWEEN` | `between(users.age, 18, 65)` |
| `inArray(col, arr)` | `IN` | `inArray(users.role, ["admin", "mod"])` |
| `isNull(col)` | `IS NULL` | `isNull(users.deletedAt)` |
| `isNotNull(col)` | `IS NOT NULL` | `isNotNull(users.email)` |

### Combining Conditions

```typescript
// AND
const admins = await db.select().from(users)
  .where(and(eq(users.role, "admin"), eq(users.isActive, true)));

// OR
const results = await db.select().from(users)
  .where(or(eq(users.role, "admin"), eq(users.role, "moderator")));

// Complex nesting
const filtered = await db.select().from(users)
  .where(and(
    eq(users.isActive, true),
    or(eq(users.role, "admin"), gt(users.loginCount, 100)),
  ));
```

### Order By, Limit, Offset

```typescript
import { asc, desc } from "drizzle-orm";

const paginated = await db.select().from(users)
  .orderBy(desc(users.createdAt))
  .limit(20)
  .offset(40);
```

### Aggregations

```typescript
import { count, sum, avg, min, max } from "drizzle-orm";

// Count all users
const [{ total }] = await db.select({ total: count() }).from(users);

// Count with alias
const stats = await db.select({
  roleCount: count(),
  role: users.role,
}).from(users).groupBy(users.role);

// Sum, avg, min, max
const orderStats = await db.select({
  totalRevenue: sum(orders.amount),
  averageOrder: avg(orders.amount),
  largestOrder: max(orders.amount),
  smallestOrder: min(orders.amount),
}).from(orders);
```

### Group By and Having

```typescript
const popularAuthors = await db.select({
  authorId: posts.authorId,
  postCount: count(),
}).from(posts)
  .groupBy(posts.authorId)
  .having(gt(count(), 10));
```

### Distinct

```typescript
const uniqueRoles = await db.selectDistinct({ role: users.role }).from(users);

// Or use distinct on specific columns (PostgreSQL)
const result = await db.selectDistinctOn([users.role], {
  role: users.role,
  name: users.name,
}).from(users);
```

## Insert Queries

### Single Insert

```typescript
await db.insert(users).values({
  name: "Alice",
  email: "alice@example.com",
});
```

### Batch Insert

```typescript
await db.insert(users).values([
  { name: "Alice", email: "alice@example.com" },
  { name: "Bob", email: "bob@example.com" },
  { name: "Charlie", email: "charlie@example.com" },
]);
```

### Insert Returning (PostgreSQL / SQLite)

```typescript
const [newUser] = await db.insert(users).values({
  name: "Alice",
  email: "alice@example.com",
}).returning();

// Return specific columns
const [{ id }] = await db.insert(users).values({
  name: "Alice",
  email: "alice@example.com",
}).returning({ id: users.id });
```

### Upsert (ON CONFLICT)

```typescript
await db.insert(users).values({
  email: "alice@example.com",
  name: "Alice Updated",
}).onConflictDoUpdate({
  target: users.email,
  set: { name: "Alice Updated" },
});

// On conflict do nothing
await db.insert(users).values({
  email: "alice@example.com",
  name: "Alice",
}).onConflictDoNothing({ target: users.email });
```

## Update Queries

```typescript
await db.update(users)
  .set({ name: "Alice Smith", updatedAt: new Date() })
  .where(eq(users.id, 1));

// Update with returning (PG/SQLite)
const [updated] = await db.update(users)
  .set({ isActive: false })
  .where(eq(users.id, 1))
  .returning();

// Update with SQL expression
await db.update(posts)
  .set({ viewCount: sql`${posts.viewCount} + 1` })
  .where(eq(posts.id, 42));
```

## Delete Queries

```typescript
await db.delete(users).where(eq(users.id, 1));

// Delete with returning (PG/SQLite)
const [deleted] = await db.delete(users)
  .where(eq(users.id, 1))
  .returning();

// Delete all rows (dangerous)
await db.delete(users);
```

## Joins

### Join Types

```typescript
// INNER JOIN
const result = await db.select({
  userName: users.name,
  postTitle: posts.title,
}).from(users)
  .innerJoin(posts, eq(posts.authorId, users.id));

// LEFT JOIN
const usersWithPosts = await db.select({
  userName: users.name,
  postTitle: posts.title,
}).from(users)
  .leftJoin(posts, eq(posts.authorId, users.id));

// RIGHT JOIN
const postsWithUsers = await db.select().from(posts)
  .rightJoin(users, eq(posts.authorId, users.id));

// FULL JOIN
const all = await db.select().from(users)
  .fullJoin(posts, eq(posts.authorId, users.id));
```

### Multi-Table Joins

```typescript
const result = await db.select({
  userName: users.name,
  postTitle: posts.title,
  commentText: comments.text,
}).from(users)
  .innerJoin(posts, eq(posts.authorId, users.id))
  .leftJoin(comments, eq(comments.postId, posts.id))
  .where(eq(users.id, 1));
```

### Join with Aggregation

```typescript
const authorStats = await db.select({
  authorName: users.name,
  postCount: count(posts.id),
}).from(users)
  .leftJoin(posts, eq(posts.authorId, users.id))
  .groupBy(users.id, users.name);
```

## Subqueries

### Subquery in Where

```typescript
const subquery = db.select({ id: posts.authorId }).from(posts)
  .where(gt(posts.viewCount, 1000));

const popularAuthors = await db.select().from(users)
  .where(inArray(users.id, subquery));
```

### Subquery in Select (Correlated)

```typescript
const sq = db.$with("post_counts").as(
  db.select({
    authorId: posts.authorId,
    postCount: count().as("post_count"),
  }).from(posts).groupBy(posts.authorId)
);

const usersWithCounts = await db.with(sq)
  .select({
    name: users.name,
    postCount: sq.postCount,
  }).from(users)
  .leftJoin(sq, eq(users.id, sq.authorId));
```

### CTE (Common Table Expression) with $with

```typescript
const activePosts = db.$with("active_posts").as(
  db.select().from(posts).where(eq(posts.status, "published"))
);

const result = await db.with(activePosts)
  .select().from(activePosts)
  .where(gt(activePosts.viewCount, 100));
```

## Raw SQL

### sql Template Tag

```typescript
import { sql } from "drizzle-orm";

// In where clause
const result = await db.select().from(users)
  .where(sql`${users.name} ILIKE ${"%" + searchTerm + "%"}`);

// In select
const result = await db.select({
  fullName: sql<string>`${users.firstName} || ' ' || ${users.lastName}`,
}).from(users);

// Full raw query
const result = await db.execute(sql`
  SELECT * FROM users WHERE created_at > NOW() - INTERVAL '30 days'
`);
```

### sql Typed Returns

Annotate `sql` with TypeScript generics for return type safety:

```typescript
const result = await db.select({
  total: sql<number>`count(*)::int`,
  avgAge: sql<number>`avg(${users.age})::float`,
}).from(users);
```

## Dynamic Queries

Build queries conditionally using `$dynamic()`:

```typescript
function buildUserQuery(filters: { role?: string; isActive?: boolean }) {
  let query = db.select().from(users).$dynamic();

  if (filters.role) {
    query = query.where(eq(users.role, filters.role));
  }
  if (filters.isActive !== undefined) {
    query = query.where(eq(users.isActive, filters.isActive));
  }

  return query;
}

const admins = await buildUserQuery({ role: "admin" });
```

### Conditional Where Helper

```typescript
const conditions = [];
if (nameFilter) conditions.push(ilike(users.name, `%${nameFilter}%`));
if (roleFilter) conditions.push(eq(users.role, roleFilter));

const result = await db.select().from(users)
  .where(conditions.length ? and(...conditions) : undefined);
```

## Query Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Missing `await` | Query never executes | Always `await` or `.then()` |
| `select()` without `from()` | TypeScript error | Chain `.from(table)` |
| Forgetting `eq` import | Runtime error | Import operators from `drizzle-orm` |
| Joining without select fields | Returns flat merged columns | Specify explicit select fields |
| Aggregate without groupBy | SQL error | Add `.groupBy()` for non-aggregated columns |
| `sql` without type annotation | Returns `unknown` | Use `sql<number>` or `sql<string>` |
