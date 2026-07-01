# Type Inference

Sources: Drizzle ORM v1.x documentation (orm.drizzle.team), drizzle-team/drizzle-orm GitHub, drizzle-zod/drizzle-valibot integration docs, 2025-2026 TypeScript community patterns

Covers: inferring types from schema ($inferSelect, $inferInsert), typeof patterns for query results, Zod/Valibot schema generation, partial and pick types, custom type helpers, and type-safe dynamic queries.

## The Core Principle

Drizzle schema is TypeScript code. Types are inferred directly from the table definitions, eliminating the need for a separate code generation step. When the schema changes, TypeScript catches mismatches immediately.

```typescript
// Schema defines the shape
export const users = pgTable("users", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  name: varchar({ length: 255 }).notNull(),
  email: varchar({ length: 255 }).notNull(),
  bio: text(),
  createdAt: timestamp().defaultNow().notNull(),
});

// Types are inferred, not manually written
type User = typeof users.$inferSelect;
// { id: number; name: string; email: string; bio: string | null; createdAt: Date }

type NewUser = typeof users.$inferInsert;
// { id?: number; name: string; email: string; bio?: string | null; createdAt?: Date }
```

## $inferSelect vs $inferInsert

| Type Helper | Includes | Optional Fields | Use For |
|-------------|----------|-----------------|---------|
| `$inferSelect` | All columns | None (all required) | Query return types, API responses |
| `$inferInsert` | All columns | Columns with defaults, auto-increment, nullable | Insert/create payloads |

### $inferSelect

Represents a row returned from the database. Every column is present:

```typescript
type User = typeof users.$inferSelect;
// {
//   id: number;         -- always present in SELECT
//   name: string;       -- NOT NULL
//   email: string;      -- NOT NULL
//   bio: string | null; -- nullable
//   createdAt: Date;    -- NOT NULL
// }
```

### $inferInsert

Represents the data needed for an INSERT. Columns with defaults, auto-generated values, or nullable types become optional:

```typescript
type NewUser = typeof users.$inferInsert;
// {
//   id?: number;                -- generatedAlwaysAsIdentity (optional)
//   name: string;               -- NOT NULL, no default (required)
//   email: string;              -- NOT NULL, no default (required)
//   bio?: string | null;        -- nullable (optional)
//   createdAt?: Date;           -- has defaultNow() (optional)
// }
```

## Practical Type Patterns

### Typing Function Parameters

```typescript
import { eq } from "drizzle-orm";

type User = typeof users.$inferSelect;
type NewUser = typeof users.$inferInsert;

async function createUser(data: NewUser): Promise<User> {
  const [user] = await db.insert(users).values(data).returning();
  return user;
}

async function getUserById(id: number): Promise<User | undefined> {
  const [user] = await db.select().from(users).where(eq(users.id, id));
  return user;
}

async function updateUser(id: number, data: Partial<NewUser>): Promise<User> {
  const [user] = await db.update(users)
    .set(data)
    .where(eq(users.id, id))
    .returning();
  return user;
}
```

### Typing API Responses

```typescript
type UserResponse = Pick<typeof users.$inferSelect, "id" | "name" | "email">;

async function getUserProfile(id: number): Promise<UserResponse | undefined> {
  const [user] = await db.select({
    id: users.id,
    name: users.name,
    email: users.email,
  }).from(users).where(eq(users.id, id));
  return user;
}
```

### Inferring Types from Queries

Use `typeof` on the query result for precise types:

```typescript
const userQuery = db.select({
  id: users.id,
  name: users.name,
  postCount: count(posts.id),
}).from(users)
  .leftJoin(posts, eq(posts.authorId, users.id))
  .groupBy(users.id, users.name);

// Infer the exact return type from the query shape
type UserWithPostCount = Awaited<ReturnType<typeof userQuery.execute>>[number];
// { id: number; name: string; postCount: number }
```

### Partial Types for Updates

```typescript
type UserUpdate = Partial<Omit<typeof users.$inferInsert, "id" | "createdAt">>;
// { name?: string; email?: string; bio?: string | null }

async function patchUser(id: number, patch: UserUpdate) {
  await db.update(users).set(patch).where(eq(users.id, id));
}
```

## Custom Type Helpers

### InferSelectModel and InferInsertModel

Drizzle exports helper types for cleaner imports:

```typescript
import { InferSelectModel, InferInsertModel } from "drizzle-orm";

type User = InferSelectModel<typeof users>;
type NewUser = InferInsertModel<typeof users>;
```

These are functionally identical to `$inferSelect` and `$inferInsert` but can be used without accessing the table directly.

### Generic Database Helper

```typescript
import { PgTable } from "drizzle-orm/pg-core";
import { InferSelectModel, InferInsertModel, eq } from "drizzle-orm";

async function findById<T extends PgTable>(
  table: T,
  id: number,
): Promise<InferSelectModel<T> | undefined> {
  const [row] = await db.select().from(table).where(eq((table as any).id, id));
  return row as InferSelectModel<T> | undefined;
}

// Usage
const user = await findById(users, 1);
const post = await findById(posts, 42);
```

### Typing Relations Results

Relational query results include nested objects. Type them explicitly when needed:

```typescript
type UserWithPosts = typeof users.$inferSelect & {
  posts: (typeof posts.$inferSelect)[];
};

// Or infer from the query itself
const query = db.query.users.findMany({
  with: { posts: true },
});

type UserWithPosts2 = Awaited<typeof query>[number];
```

## Zod Integration (drizzle-zod)

Generate Zod validation schemas directly from Drizzle table definitions.

### Installation

```bash
npm install drizzle-zod
```

### Creating Schemas

```typescript
import { createSelectSchema, createInsertSchema, createUpdateSchema } from "drizzle-zod";

const userSelectSchema = createSelectSchema(users);
const userInsertSchema = createInsertSchema(users);
const userUpdateSchema = createUpdateSchema(users);

// Validate incoming data
const parsed = userInsertSchema.parse(req.body);
await db.insert(users).values(parsed);
```

### Refining Schemas

Override or extend generated Zod fields:

```typescript
const userInsertSchema = createInsertSchema(users, {
  email: (schema) => schema.email("Invalid email format"),
  name: (schema) => schema.min(2, "Name must be at least 2 characters"),
  bio: (schema) => schema.max(500, "Bio too long").optional(),
});
```

### Practical API Pattern

```typescript
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

const createUserSchema = createInsertSchema(users, {
  email: (schema) => schema.email(),
}).omit({ id: true, createdAt: true });

type CreateUserInput = z.infer<typeof createUserSchema>;

async function handleCreateUser(input: unknown) {
  const data = createUserSchema.parse(input);
  const [user] = await db.insert(users).values(data).returning();
  return user;
}
```

## Valibot Integration (drizzle-valibot)

Alternative to Zod with smaller bundle size:

```typescript
import { createSelectSchema, createInsertSchema } from "drizzle-valibot";

const userInsertSchema = createInsertSchema(users);
```

API mirrors drizzle-zod. Choose Valibot for edge/serverless where bundle size matters.

## Type-Safe Dynamic Queries

### Building Queries with Type Safety

```typescript
import { SQL, and, eq, ilike } from "drizzle-orm";

interface UserFilters {
  role?: string;
  search?: string;
  isActive?: boolean;
}

function buildUserFilters(filters: UserFilters): SQL | undefined {
  const conditions: SQL[] = [];

  if (filters.role) {
    conditions.push(eq(users.role, filters.role));
  }
  if (filters.search) {
    conditions.push(ilike(users.name, `%${filters.search}%`));
  }
  if (filters.isActive !== undefined) {
    conditions.push(eq(users.isActive, filters.isActive));
  }

  return conditions.length ? and(...conditions) : undefined;
}

async function getUsers(filters: UserFilters) {
  return db.select().from(users).where(buildUserFilters(filters));
}
```

### Type-Safe Column Selection

```typescript
type UserColumn = keyof typeof users.$inferSelect;

function selectUserColumns(columns: UserColumn[]) {
  const selection: Record<string, any> = {};
  for (const col of columns) {
    selection[col] = users[col as keyof typeof users];
  }
  return db.select(selection).from(users);
}
```

## Custom Column Types with $type

Override the inferred TypeScript type for a column:

```typescript
export const settings = pgTable("settings", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  config: jsonb().$type<{ theme: string; language: string }>().notNull(),
  status: text().$type<"active" | "inactive" | "suspended">().notNull(),
});

// Now TypeScript knows config is { theme: string; language: string }
// and status is a union of specific strings
```

## Branded Types for IDs

Prevent mixing up IDs from different tables:

```typescript
type UserId = number & { __brand: "UserId" };
type PostId = number & { __brand: "PostId" };

export const users = pgTable("users", {
  id: integer().primaryKey().generatedAlwaysAsIdentity().$type<UserId>(),
  name: varchar({ length: 255 }).notNull(),
});

export const posts = pgTable("posts", {
  id: integer().primaryKey().generatedAlwaysAsIdentity().$type<PostId>(),
  authorId: integer("author_id").notNull().$type<UserId>(),
});

// TypeScript now prevents: findPost(userId) when PostId is expected
```

## Common Type Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Manually typing interfaces | Types drift from schema | Use `$inferSelect` / `$inferInsert` |
| Ignoring nullable columns | Runtime null crashes | Check `$inferSelect` type includes `| null` |
| Not using `Partial<>` for updates | Requires all fields on PATCH | Use `Partial<Omit<NewUser, "id">>` |
| Casting with `as any` | Defeats type safety | Use proper generics or `$type<>()` |
| Generated code not refreshed | Stale types (Prisma problem) | Drizzle has no codegen -- types are always fresh |
| JSON columns typed as `unknown` | No type safety on JSON data | Use `.$type<YourInterface>()` |
| Missing `returning()` type | Insert returns void | Add `.returning()` to get inserted row type |
