# Relational Queries

Sources: Drizzle ORM v1.x documentation (orm.drizzle.team), drizzle-team/drizzle-orm GitHub, 2025-2026 production patterns

Covers: the relational queries API (db.query), findMany/findFirst, eager loading with `with`, column selection, filtering/ordering/limiting nested data, relation setup requirements, and comparison with the SQL-like query builder.

## When to Use Relational Queries

The relational queries API (`db.query`) fetches nested, structured data automatically. Choose it when the output shape is "entity with related entities" rather than a flat row set.

| Need | Use |
|------|-----|
| Users with their posts and comments | `db.query.users.findMany({ with: { posts: { with: { comments: true } } } })` |
| Flat join with specific columns | `db.select().from(users).innerJoin(...)` |
| Aggregations, GROUP BY, HAVING | SQL-like query builder |
| Complex subqueries | SQL-like query builder or raw SQL |
| Nested object graphs for API responses | Relational queries |

## Setup Requirements

### 1. Define Schema Tables

```typescript
// src/db/schema.ts
import { pgTable, integer, varchar, text, timestamp } from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  name: varchar({ length: 255 }).notNull(),
  email: varchar({ length: 255 }).notNull().unique(),
});

export const posts = pgTable("posts", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  title: varchar({ length: 255 }).notNull(),
  content: text(),
  authorId: integer("author_id").notNull().references(() => users.id),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const comments = pgTable("comments", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  text: text().notNull(),
  postId: integer("post_id").notNull().references(() => posts.id),
  authorId: integer("author_id").notNull().references(() => users.id),
});
```

### 2. Define Relations

Relations are mandatory for `db.query` to work. They tell Drizzle how to resolve nested data.

```typescript
import { relations } from "drizzle-orm";

export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
  comments: many(comments),
}));

export const postsRelations = relations(posts, ({ one, many }) => ({
  author: one(users, {
    fields: [posts.authorId],
    references: [users.id],
  }),
  comments: many(comments),
}));

export const commentsRelations = relations(comments, ({ one }) => ({
  post: one(posts, {
    fields: [comments.postId],
    references: [posts.id],
  }),
  author: one(users, {
    fields: [comments.authorId],
    references: [users.id],
  }),
}));
```

### 3. Pass Schema to drizzle()

```typescript
import { drizzle } from "drizzle-orm/node-postgres";
import * as schema from "./schema";

const db = drizzle({
  connection: process.env.DATABASE_URL!,
  schema,  // required for db.query to work
});
```

Without passing `schema`, `db.query` throws a runtime error. The schema object must include both tables and relations.

## findMany

Fetch multiple records with optional filtering, ordering, and eager loading.

### Basic Usage

```typescript
// All users
const allUsers = await db.query.users.findMany();

// With limit and offset
const page = await db.query.users.findMany({
  limit: 20,
  offset: 40,
});
```

### Column Selection

```typescript
const names = await db.query.users.findMany({
  columns: {
    id: true,
    name: true,
    // email is excluded
  },
});

// Exclude specific columns
const withoutEmail = await db.query.users.findMany({
  columns: {
    email: false,  // include all except email
  },
});
```

### Filtering with where

```typescript
import { eq, and, gt, like } from "drizzle-orm";

const activeAdmins = await db.query.users.findMany({
  where: and(eq(users.role, "admin"), eq(users.isActive, true)),
});

// Callback form (access to table columns and operators)
const recent = await db.query.users.findMany({
  where: (users, { gt }) => gt(users.createdAt, new Date("2024-01-01")),
});
```

### Ordering

```typescript
import { asc, desc } from "drizzle-orm";

const sorted = await db.query.users.findMany({
  orderBy: [desc(users.createdAt)],
});

// Callback form
const sorted2 = await db.query.users.findMany({
  orderBy: (users, { desc }) => [desc(users.createdAt)],
});
```

## findFirst

Fetch a single record. Returns `undefined` if not found (not an array).

```typescript
const user = await db.query.users.findFirst({
  where: eq(users.id, 1),
});

if (!user) {
  throw new Error("User not found");
}
```

`findFirst` automatically adds `LIMIT 1` to the query.

## Eager Loading with `with`

The primary power of relational queries. Fetch nested related data in a single call.

### One Level Deep

```typescript
// Users with their posts
const usersWithPosts = await db.query.users.findMany({
  with: {
    posts: true,  // loads all posts for each user
  },
});
// Result: [{ id: 1, name: "Alice", posts: [{ id: 1, title: "Hello" }, ...] }]
```

### Multi-Level Nesting

```typescript
// Users -> posts -> comments
const deep = await db.query.users.findMany({
  with: {
    posts: {
      with: {
        comments: true,
      },
    },
  },
});
// Result: [{ id: 1, name: "Alice", posts: [{ id: 1, title: "Hello", comments: [...] }] }]
```

### Filtering and Limiting Nested Data

```typescript
const usersWithRecentPosts = await db.query.users.findMany({
  with: {
    posts: {
      where: gt(posts.createdAt, new Date("2024-01-01")),
      orderBy: [desc(posts.createdAt)],
      limit: 5,
      columns: {
        id: true,
        title: true,
      },
      with: {
        comments: {
          limit: 3,
          orderBy: [desc(comments.createdAt)],
        },
      },
    },
  },
});
```

### Selecting Columns in Nested Relations

```typescript
const result = await db.query.users.findMany({
  columns: {
    id: true,
    name: true,
  },
  with: {
    posts: {
      columns: {
        title: true,
        createdAt: true,
      },
    },
  },
});
```

## Extras (Computed Columns)

Add computed fields to query results:

```typescript
import { sql } from "drizzle-orm";

const usersWithPostCount = await db.query.users.findMany({
  extras: {
    fullName: sql<string>`${users.firstName} || ' ' || ${users.lastName}`.as("full_name"),
  },
});
```

## Relation Types in Depth

### one() -- Many-to-One / One-to-One

The side that holds the foreign key declares the `one()` with `fields` and `references`:

```typescript
export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, {
    fields: [posts.authorId],       // FK column on this table
    references: [users.id],         // PK column on the related table
  }),
}));
```

### many() -- One-to-Many

The parent side declares `many()` without field config:

```typescript
export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));
```

Drizzle resolves the join by finding the matching `one()` declaration on the other side.

### Named Relations for Multiple FKs

When a table has multiple foreign keys to the same table, use `relationName`:

```typescript
export const messages = pgTable("messages", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  senderId: integer("sender_id").references(() => users.id),
  receiverId: integer("receiver_id").references(() => users.id),
  text: text().notNull(),
});

export const messagesRelations = relations(messages, ({ one }) => ({
  sender: one(users, {
    fields: [messages.senderId],
    references: [users.id],
    relationName: "sender",
  }),
  receiver: one(users, {
    fields: [messages.receiverId],
    references: [users.id],
    relationName: "receiver",
  }),
}));

export const usersRelations = relations(users, ({ many }) => ({
  sentMessages: many(messages, { relationName: "sender" }),
  receivedMessages: many(messages, { relationName: "receiver" }),
}));
```

### Many-to-Many

Model with a junction table. Each side has `many()` to the junction, and the junction has `one()` to each side:

```typescript
export const usersToGroups = pgTable("users_to_groups", {
  userId: integer("user_id").notNull().references(() => users.id),
  groupId: integer("group_id").notNull().references(() => groups.id),
}, (t) => [primaryKey({ columns: [t.userId, t.groupId] })]);

export const usersRelations = relations(users, ({ many }) => ({
  groups: many(usersToGroups),
}));

export const groupsRelations = relations(groups, ({ many }) => ({
  members: many(usersToGroups),
}));

export const usersToGroupsRelations = relations(usersToGroups, ({ one }) => ({
  user: one(users, { fields: [usersToGroups.userId], references: [users.id] }),
  group: one(groups, { fields: [usersToGroups.groupId], references: [groups.id] }),
}));
```

Query through junction:

```typescript
const usersWithGroups = await db.query.users.findMany({
  with: {
    groups: {
      with: {
        group: true,
      },
    },
  },
});
```

## How Relational Queries Execute

Drizzle relational queries do NOT use SQL joins. They execute multiple queries under the hood:

1. First query fetches the parent rows
2. Subsequent queries fetch related data using `WHERE id IN (...)` from parent results
3. Results are assembled into nested objects in JavaScript

This means:
- No Cartesian product explosion (safe for deeply nested queries)
- Multiple round-trips to the database (slightly more latency than a single join)
- Works well within a transaction for consistency

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Missing `schema` in `drizzle()` call | `db.query` throws at runtime | Pass `schema` with tables + relations |
| Relations not exported | Drizzle cannot resolve nested data | Export all relation declarations |
| Ambiguous relations (multiple FKs) | Runtime error about ambiguous reference | Add `relationName` to distinguish |
| Expecting SQL JOIN behavior | RQ uses separate queries, not joins | Use `db.select().innerJoin()` for true SQL joins |
| Over-fetching nested data | Loading all columns for all relations | Use `columns` to select only needed fields |
| Not passing `with` | Related data not loaded | Specify `with: { relation: true }` explicitly |
