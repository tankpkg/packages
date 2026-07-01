# Schema Definition

Sources: Drizzle ORM v1.x documentation (orm.drizzle.team), drizzle-team/drizzle-orm GitHub, 2025-2026 community patterns

Covers: table definitions, column types, constraints, indexes, enums, relations declarations, multi-file schema organization, and reusable column patterns across PostgreSQL, MySQL, and SQLite.

## Table Declaration

Drizzle uses dialect-specific table functions. Import from the correct core module.

```typescript
// PostgreSQL
import { pgTable, integer, varchar, text, boolean, timestamp } from "drizzle-orm/pg-core";

// MySQL
import { mysqlTable, int, varchar, text, boolean, timestamp } from "drizzle-orm/mysql-core";

// SQLite
import { sqliteTable, integer, text } from "drizzle-orm/sqlite-core";
```

### PostgreSQL Table Example

```typescript
import { pgTable, integer, varchar, timestamp, text, boolean } from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  name: varchar({ length: 255 }).notNull(),
  email: varchar({ length: 255 }).notNull().unique(),
  bio: text(),
  isActive: boolean().default(true).notNull(),
  createdAt: timestamp().defaultNow().notNull(),
  updatedAt: timestamp().$onUpdate(() => new Date()),
});
```

### Column Name Mapping

By default, the TypeScript key name maps to the database column name. Use column aliases for camelCase in TypeScript with snake_case in the database:

```typescript
// Explicit alias
export const users = pgTable("users", {
  firstName: varchar("first_name", { length: 255 }),
});

// Or use global casing option at db initialization
import { drizzle } from "drizzle-orm/node-postgres";
const db = drizzle({ connection: process.env.DATABASE_URL, casing: "snake_case" });
```

The `casing: "snake_case"` option auto-maps all camelCase TypeScript keys to snake_case columns, eliminating per-column aliases.

## Column Types by Dialect

### PostgreSQL Column Types

| TypeScript | PostgreSQL Type | Notes |
|-----------|----------------|-------|
| `integer()` | `integer` | 32-bit signed |
| `smallint()` | `smallint` | 16-bit signed |
| `bigint({ mode: "number" })` | `bigint` | Use `mode: "bigint"` for native BigInt |
| `serial()` | `serial` | Auto-incrementing (legacy, prefer `generatedAlwaysAsIdentity`) |
| `varchar({ length: N })` | `varchar(N)` | Variable-length string |
| `text()` | `text` | Unlimited text |
| `boolean()` | `boolean` | true/false |
| `timestamp()` | `timestamp` | Without timezone by default |
| `timestamp({ withTimezone: true })` | `timestamptz` | With timezone |
| `date()` | `date` | Date only |
| `json()` | `json` | Stored as text |
| `jsonb()` | `jsonb` | Binary JSON, indexable |
| `uuid()` | `uuid` | UUID type |
| `numeric({ precision: 10, scale: 2 })` | `numeric(10,2)` | Exact decimal |
| `real()` | `real` | 32-bit float |
| `doublePrecision()` | `double precision` | 64-bit float |

### SQLite Column Types

| TypeScript | SQLite Type | Notes |
|-----------|-------------|-------|
| `integer()` | `integer` | Also used for booleans |
| `text()` | `text` | All string types |
| `real()` | `real` | Floating point |
| `blob()` | `blob` | Binary data |
| `integer({ mode: "timestamp" })` | `integer` | Unix timestamp stored as integer |

## Column Constraints

```typescript
export const posts = pgTable("posts", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  title: varchar({ length: 255 }).notNull(),
  slug: varchar({ length: 255 }).notNull().unique(),
  content: text().default(""),
  authorId: integer("author_id").notNull().references(() => users.id),
  viewCount: integer("view_count").default(0).notNull(),
});
```

### Constraint Reference

| Method | Effect |
|--------|--------|
| `.primaryKey()` | Primary key constraint |
| `.notNull()` | NOT NULL constraint |
| `.unique()` | UNIQUE constraint |
| `.default(value)` | Static default value |
| `.defaultNow()` | `DEFAULT now()` for timestamps |
| `.$default(() => expr)` | Runtime default (app-level, not DB) |
| `.$onUpdate(() => expr)` | Runtime value on update (app-level) |
| `.generatedAlwaysAsIdentity()` | GENERATED ALWAYS AS IDENTITY (PG) |
| `.references(() => table.col)` | Foreign key inline |

### Foreign Keys

Inline foreign keys work for simple cases:

```typescript
authorId: integer("author_id").references(() => users.id),
```

For composite foreign keys or cascade options, use the table-level constraint:

```typescript
import { pgTable, integer, foreignKey } from "drizzle-orm/pg-core";

export const comments = pgTable("comments", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  postId: integer("post_id").notNull(),
  userId: integer("user_id").notNull(),
}, (table) => [
  foreignKey({
    columns: [table.postId],
    foreignColumns: [posts.id],
  }).onDelete("cascade").onUpdate("cascade"),
]);
```

### Self-Referencing Foreign Keys

Use `AnyPgColumn` for self-referential tables:

```typescript
import { AnyPgColumn } from "drizzle-orm/pg-core";

export const categories = pgTable("categories", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  name: varchar({ length: 255 }).notNull(),
  parentId: integer("parent_id").references((): AnyPgColumn => categories.id),
});
```

## Indexes

Define indexes in the third argument of the table function:

```typescript
import { pgTable, integer, varchar, index, uniqueIndex } from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  email: varchar({ length: 255 }).notNull(),
  name: varchar({ length: 255 }),
  status: varchar({ length: 50 }),
}, (table) => [
  uniqueIndex("users_email_idx").on(table.email),
  index("users_status_idx").on(table.status),
  index("users_name_status_idx").on(table.name, table.status),  // composite
]);
```

### Index Types (PostgreSQL)

```typescript
import { index } from "drizzle-orm/pg-core";

// B-tree (default)
index("idx_name").on(table.column),

// GIN index for jsonb
index("idx_tags").using("gin", table.tags),

// Expression index
index("idx_lower_email").on(sql`lower(${table.email})`),

// Partial index
index("idx_active").on(table.status).where(sql`${table.status} = 'active'`),
```

## Enums

### PostgreSQL Enums

```typescript
import { pgEnum, pgTable, integer } from "drizzle-orm/pg-core";

export const roleEnum = pgEnum("role", ["admin", "user", "guest"]);

export const users = pgTable("users", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  role: roleEnum().default("user").notNull(),
});
```

### MySQL Enums

```typescript
import { mysqlTable, mysqlEnum, int } from "drizzle-orm/mysql-core";

export const users = mysqlTable("users", {
  id: int().primaryKey().autoincrement(),
  role: mysqlEnum(["admin", "user", "guest"]).default("user").notNull(),
});
```

### SQLite Enums (Application-Level)

SQLite has no native enum. Use `.$type<>()` for type safety:

```typescript
export const users = sqliteTable("users", {
  role: text().$type<"admin" | "user" | "guest">().default("user").notNull(),
});
```

## Relations Declaration

Relations are separate from foreign keys. They define how Drizzle's relational query API resolves nested data. Declare them alongside the schema.

```typescript
import { relations } from "drizzle-orm";

export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, {
    fields: [posts.authorId],
    references: [users.id],
  }),
}));
```

### Relation Types

| Relation | Usage | Field Config |
|----------|-------|-------------|
| `one()` | Many-to-one or one-to-one | Requires `fields` + `references` on the FK side |
| `many()` | One-to-many | No field config needed (inferred from the other side) |

### Many-to-Many (Junction Table)

```typescript
export const usersToGroups = pgTable("users_to_groups", {
  userId: integer("user_id").notNull().references(() => users.id),
  groupId: integer("group_id").notNull().references(() => groups.id),
}, (t) => [
  primaryKey({ columns: [t.userId, t.groupId] }),
]);

export const usersToGroupsRelations = relations(usersToGroups, ({ one }) => ({
  user: one(users, { fields: [usersToGroups.userId], references: [users.id] }),
  group: one(groups, { fields: [usersToGroups.groupId], references: [groups.id] }),
}));

export const usersRelations = relations(users, ({ many }) => ({
  usersToGroups: many(usersToGroups),
}));
```

## Schema Organization

### Single File

Place all tables in `src/db/schema.ts`. Works for small projects.

### Multi-File

Split tables by domain. Configure drizzle-kit to scan the folder:

```
src/db/schema/
  users.ts
  posts.ts
  comments.ts
  relations.ts    // all relations in one file, or co-locate with tables
```

```typescript
// drizzle.config.ts
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  dialect: "postgresql",
  schema: "./src/db/schema",
  out: "./drizzle",
});
```

Export all tables from each file. Drizzle-kit recursively scans the schema directory.

## Reusable Column Patterns

Extract common columns and spread into tables:

```typescript
// src/db/schema/helpers.ts
import { timestamp } from "drizzle-orm/pg-core";

export const timestamps = {
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").$onUpdate(() => new Date()),
  deletedAt: timestamp("deleted_at"),
};
```

```typescript
// src/db/schema/users.ts
import { timestamps } from "./helpers";

export const users = pgTable("users", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  name: varchar({ length: 255 }).notNull(),
  ...timestamps,
});
```

## PostgreSQL Schemas (Namespaces)

Use `pgSchema` to place tables in non-public schemas:

```typescript
import { pgSchema, integer } from "drizzle-orm/pg-core";

export const authSchema = pgSchema("auth");

export const authUsers = authSchema.table("users", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
});
```

## Common Schema Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Using `serial()` for new tables | Legacy pattern, less control | Use `integer().generatedAlwaysAsIdentity()` |
| Missing `notNull()` on required fields | Allows unexpected nulls | Add `.notNull()` to every required column |
| Forgetting to export tables | drizzle-kit cannot detect them | Export every table and enum |
| Relations without foreign keys | No DB-level integrity | Add `.references()` alongside `relations()` |
| Timestamp without timezone | Timezone confusion in distributed apps | Use `timestamp({ withTimezone: true })` |
| Inline FK without onDelete | Orphaned rows on parent deletion | Add `.onDelete("cascade")` or handle in app |
