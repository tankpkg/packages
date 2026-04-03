---
name: "@tank/drizzle-orm-mastery"
description: |
  Drizzle ORM patterns for TypeScript projects targeting PostgreSQL, MySQL, and
  SQLite. Covers schema definition (tables, columns, relations, indexes, enums),
  drizzle-kit migrations (generate, push, migrate, introspect), query builder
  (select, insert, update, delete, joins, subqueries, prepared statements),
  relational queries API, transactions, type inference from schema, connection
  pooling, performance optimization, and framework integration (Next.js, Supabase,
  Cloudflare D1, Neon, Turso, TanStack Start).

  Synthesizes Drizzle ORM v1.x documentation (orm.drizzle.team), drizzle-kit CLI
  reference, PlanetScale/Neon/Turso integration guides, and 2025-2026 community
  production patterns.

  Trigger phrases: "drizzle orm", "drizzle schema", "drizzle migrations",
  "drizzle-kit", "drizzle relations", "drizzle query", "drizzle select",
  "drizzle insert", "drizzle join", "drizzle transaction", "drizzle supabase",
  "drizzle next.js", "drizzle d1", "drizzle vs prisma", "drizzle connection pool",
  "drizzle push vs migrate", "drizzle prepared statement", "drizzle type inference",
  "drizzle postgresql", "drizzle sqlite", "drizzle neon", "drizzle turso"
---

# Drizzle ORM Mastery

## Core Philosophy

1. **SQL-first, not SQL-hidden** -- Drizzle maps 1:1 to SQL. Learn SQL patterns and Drizzle follows. If the query builder feels awkward, write the SQL first, then translate.
2. **Schema is the source of truth** -- TypeScript schema definitions drive migrations, queries, and type inference. Change the schema, regenerate migrations, never hand-edit SQL files.
3. **Push for prototyping, migrate for production** -- Use `drizzle-kit push` during development for instant schema sync. Switch to `drizzle-kit generate` + `migrate` before deploying to shared environments.
4. **Infer types, never duplicate them** -- Extract types from schema with `typeof` and `$inferSelect` / `$inferInsert`. Manually typed interfaces drift from the actual schema.
5. **Choose the right query API** -- Use the SQL-like query builder (`db.select()`) for complex queries with joins and subqueries. Use the relational queries API (`db.query`) for nested object fetching with `with`.

## Quick-Start: Common Problems

### "How do I define a schema?"

```typescript
import { pgTable, integer, varchar, timestamp } from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: integer().primaryKey().generatedAlwaysAsIdentity(),
  name: varchar({ length: 255 }).notNull(),
  email: varchar({ length: 255 }).notNull().unique(),
  createdAt: timestamp().defaultNow().notNull(),
});
```

-> See `references/schema-definition.md`

### "Push or migrate?"

| Situation | Command |
|-----------|---------|
| Local dev, solo, iterating fast | `drizzle-kit push` |
| Team project, staging/prod | `drizzle-kit generate` then `drizzle-kit migrate` |
| Pull existing DB into Drizzle | `drizzle-kit introspect` |
| Preview SQL without applying | `drizzle-kit generate` then read SQL files |

-> See `references/migrations-workflow.md`

### "How do I query with joins?"

```typescript
const result = await db
  .select({ userName: users.name, postTitle: posts.title })
  .from(users)
  .innerJoin(posts, eq(posts.authorId, users.id))
  .where(eq(users.id, 1));
```

-> See `references/query-builder.md`

### "Drizzle or Prisma?"

| Factor | Drizzle | Prisma |
|--------|---------|--------|
| Philosophy | SQL-first, thin abstraction | Schema-first, thick abstraction |
| Bundle size | ~50KB | ~2MB+ (engine binary) |
| Performance | 3-5x faster in benchmarks | Improved in Prisma 7 |
| Type inference | From TypeScript schema | From generated client |
| Edge/serverless | Native support | Requires adapter |
| Learning curve | Need SQL knowledge | Lower barrier, DSL-based |

-> See `references/drizzle-vs-prisma.md`

### "How do I connect to Supabase / Neon / D1?"

-> See `references/framework-integration.md` for driver-specific setup patterns.

## Decision Trees

### Dialect Selection

| Database | Import From | Driver |
|----------|-------------|--------|
| PostgreSQL (node-postgres) | `drizzle-orm/node-postgres` | `pg` |
| PostgreSQL (Neon serverless) | `drizzle-orm/neon-http` | `@neondatabase/serverless` |
| PostgreSQL (Supabase) | `drizzle-orm/postgres-js` | `postgres` (postgres.js) |
| MySQL | `drizzle-orm/mysql2` | `mysql2` |
| SQLite (local) | `drizzle-orm/better-sqlite3` | `better-sqlite3` |
| SQLite (Turso) | `drizzle-orm/libsql` | `@libsql/client` |
| SQLite (Cloudflare D1) | `drizzle-orm/d1` | D1 binding |

### Query API Selection

| Need | API | Reason |
|------|-----|--------|
| Complex joins, subqueries, aggregates | `db.select().from()` | Full SQL control |
| Nested object loading (posts with comments) | `db.query.posts.findMany()` | Automatic relation resolution |
| Raw SQL escape hatch | `db.execute(sql`...`)` | Unsupported features |
| Bulk insert/upsert | `db.insert().values([...])` | Batch operations |

## Reference Index

| File | Contents |
|------|----------|
| `references/schema-definition.md` | Table definitions, column types, constraints, indexes, enums, relations, multi-file schema organization, reusable column patterns |
| `references/migrations-workflow.md` | drizzle-kit CLI (generate, push, migrate, introspect, studio), drizzle.config.ts, migration strategies, CI/CD, troubleshooting |
| `references/query-builder.md` | Select, insert, update, delete, joins (inner/left/right/full), where clauses, aggregations, subqueries, raw SQL, dynamic queries |
| `references/relational-queries.md` | Relational queries API (db.query), findMany/findFirst, with (eager loading), columns selection, where/orderBy/limit, relations setup |
| `references/transactions-performance.md` | Transactions, savepoints, rollback, isolation levels, prepared statements, connection pooling, query logging, performance patterns |
| `references/type-inference.md` | $inferSelect, $inferInsert, typeof patterns, Zod integration, partial types, custom type helpers, type-safe dynamic queries |
| `references/framework-integration.md` | Next.js App Router, Supabase, Neon serverless, Cloudflare D1, Turso/libSQL, TanStack Start, connection patterns per environment |
| `references/drizzle-vs-prisma.md` | Feature comparison, performance benchmarks, migration paths, when to choose each, ecosystem maturity, edge runtime support |
