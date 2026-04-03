---
name: "@tank/prisma-production-patterns"
description: |
  Production Prisma ORM patterns for TypeScript applications. Covers schema
  design (models, relations, enums, indexes, naming conventions), Prisma Client
  CRUD (findMany, findUnique, create, update, upsert, nested writes), relation
  queries (include, select, fluent API), N+1 prevention, transactions
  (sequential, interactive, nested writes, optimistic concurrency), raw SQL
  ($queryRaw, $executeRaw, TypedSQL), connection pooling (driver adapters,
  PgBouncer, serverless), Prisma Migrate workflows (dev, deploy, resolve,
  baselining, custom SQL), Client extensions ($extends for middleware, soft
  delete, RLS, audit logging), testing (mocking with jest-mock-extended,
  integration tests, seeding), error handling (P2002, P2025, retry patterns),
  and deployment (Docker, CI/CD, edge with Prisma Accelerate).

  Synthesizes Prisma official documentation (v6/v7), Prisma blog engineering
  posts, and production TypeScript ORM patterns.

  Trigger phrases: "prisma", "prisma client", "prisma schema", "prisma migrate",
  "prisma production", "prisma best practices", "prisma connection pooling",
  "prisma transaction", "prisma N+1", "prisma raw query", "prisma testing",
  "prisma seeding", "prisma accelerate", "prisma serverless", "prisma extension",
  "prisma relations", "prisma middleware", "prisma vs drizzle", "prisma error",
  "prisma deploy", "PgBouncer prisma", "prisma soft delete", "prisma upsert"
---

# Prisma Production Patterns

## Core Philosophy

1. **Schema is the source of truth** -- The Prisma schema drives types, migrations, and client API. Invest in schema design because every downstream operation depends on it.
2. **Use the type system, escape only when necessary** -- Prisma Client provides type-safe queries. Drop to raw SQL only for features Prisma does not support (CTEs, window functions, bulk upserts). Use TypedSQL for type-safe raw queries.
3. **Connections are finite** -- Every Prisma Client instance owns a connection pool. In serverless, use external poolers (PgBouncer, Prisma Accelerate) or share a single client instance to avoid exhausting database connections.
4. **Transactions should be short** -- Long-running interactive transactions hold database locks and cause deadlocks. Prefer nested writes for dependent operations and batch APIs for independent ones.
5. **Test against real databases** -- Unit tests with mocked Prisma Client verify logic. Integration tests against a real database (Docker + migrate reset) catch schema and query issues mocks cannot.

## Quick-Start: Common Problems

### "How do I model this relationship?"

| Relationship | Schema Pattern |
|-------------|---------------|
| User has one Profile | 1:1 -- `@unique` on FK side |
| User has many Posts | 1:n -- FK on Post, array on User |
| Post has many Tags | m:n implicit -- just list fields, Prisma manages join table |
| Post has many Tags with extra data | m:n explicit -- create a join model with payload fields |
| User follows Users | Self-relation -- disambiguate with `@relation("name")` |
-> See `references/schema-design.md`

### "My queries are slow / N+1"

1. Check for loops calling `findUnique` -- replace with `findMany` + `include`
2. Use `select` to fetch only needed fields -- reduces payload and join cost
3. Enable query logging: `new PrismaClient({ log: ['query'] })`
4. For pagination, use cursor-based over offset for large datasets
-> See `references/client-queries.md` and `references/performance.md`

### "How do I handle transactions?"

| Scenario | Technique |
|----------|-----------|
| Create parent + children together | Nested writes (automatic transaction) |
| Multiple independent writes | `$transaction([...])` sequential API |
| Read-modify-write with validation | Interactive `$transaction(async (tx) => ...)` |
| High concurrency on same row | Optimistic concurrency with `version` field |
-> See `references/transactions-raw.md`

### "Deploying to production / serverless"

1. Run `prisma migrate deploy` in CI -- never `migrate dev` in production
2. Add `prisma generate` to your build step (or Dockerfile)
3. For serverless: use Prisma Accelerate or PgBouncer with `?pgbouncer=true`
4. Set `connection_limit` low (1-5) per function instance
-> See `references/deployment-serverless.md`

## Decision Trees

### When to Use Raw SQL

| Signal | Recommendation |
|--------|---------------|
| Standard CRUD, relations, filters | Prisma Client -- stay type-safe |
| CTEs, window functions, LATERAL joins | `$queryRaw` with tagged template |
| Bulk upsert (ON CONFLICT) | `$executeRaw` or TypedSQL |
| Dynamic table/column names | `$queryRawUnsafe` with parameterized values |
| Complex reporting queries | TypedSQL (`.sql` files with type generation) |

### Prisma vs Drizzle

| Dimension | Prisma | Drizzle |
|-----------|--------|---------|
| Schema definition | Dedicated `.prisma` DSL | TypeScript code |
| Migration workflow | Declarative (schema diff) | Code-based or kit-based |
| Type safety | Generated types from schema | Inferred from TS schema |
| Raw SQL escape hatch | `$queryRaw`, TypedSQL | `sql` tagged template |
| Serverless / edge | Prisma Accelerate (proxy) | Native edge drivers |
| Ecosystem maturity | Larger (since 2019) | Growing fast (since 2022) |

## Reference Index

| File | Contents |
|------|----------|
| `references/schema-design.md` | Models, field types, relations (1:1, 1:n, m:n, self), indexes, enums, naming conventions, multi-schema, referential actions |
| `references/client-queries.md` | CRUD operations, filtering, sorting, pagination (cursor vs offset), select/include, nested reads/writes, aggregation |
| `references/transactions-raw.md` | Sequential and interactive transactions, isolation levels, nested writes, optimistic concurrency, raw SQL ($queryRaw, $executeRaw, TypedSQL), SQL injection prevention |
| `references/performance.md` | N+1 detection and prevention, connection pooling (v7 driver adapters), query logging, select optimization, batch operations, Prisma Optimize |
| `references/migrations.md` | Prisma Migrate workflow (dev, deploy, resolve), baselining existing databases, custom SQL in migrations, squashing, shadow database, CI/CD integration |
| `references/extensions-middleware.md` | Client extensions ($extends), model/query/result/client components, soft delete, audit logging, RLS patterns, computed fields |
| `references/testing-seeding.md` | Unit testing (mocking with jest-mock-extended, singleton, DI), integration testing (Docker, migrate reset), seeding (prisma db seed, faker, idempotent seeds) |
| `references/deployment-serverless.md` | Docker builds, CI/CD pipelines, serverless connection management, Prisma Accelerate, PgBouncer configuration, edge deployment, error handling (P2002, P2025, retry) |
