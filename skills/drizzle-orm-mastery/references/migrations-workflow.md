# Migrations Workflow

Sources: Drizzle ORM v1.x documentation (orm.drizzle.team), drizzle-kit CLI reference, 2025-2026 production deployment patterns

Covers: drizzle-kit CLI commands (generate, push, migrate, introspect, studio), drizzle.config.ts configuration, migration strategies for development and production, CI/CD integration, and common troubleshooting.

## drizzle.config.ts

Every drizzle-kit command reads configuration from this file. Place it at the project root.

```typescript
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  dialect: "postgresql",         // "postgresql" | "mysql" | "sqlite" | "turso"
  schema: "./src/db/schema.ts",  // path to schema file or folder
  out: "./drizzle",              // migration output directory
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
  verbose: true,                 // log SQL statements
  strict: true,                  // require confirmation for destructive changes
});
```

### Configuration Options

| Option | Type | Purpose |
|--------|------|---------|
| `dialect` | string | Target database dialect |
| `schema` | string or string[] | Schema file/folder path(s) |
| `out` | string | Migration output directory (default: `./drizzle`) |
| `dbCredentials` | object | Database connection for push/migrate/introspect |
| `verbose` | boolean | Print SQL during operations |
| `strict` | boolean | Prompt before destructive changes |
| `tablesFilter` | string[] | Glob patterns to include/exclude tables |
| `schemaFilter` | string[] | PostgreSQL schemas to include |
| `casing` | string | Column name mapping (`"snake_case"` or `"camelCase"`) |

### Multiple Configs

For projects with multiple databases, create separate config files:

```bash
drizzle-kit generate --config=drizzle-pg.config.ts
drizzle-kit generate --config=drizzle-sqlite.config.ts
```

## Core Commands

### drizzle-kit generate

Reads the TypeScript schema and produces SQL migration files by diffing against the previous migration state.

```bash
npx drizzle-kit generate
```

Output structure:

```
drizzle/
  0000_initial.sql          # first migration
  0001_add_posts.sql        # subsequent migration
  meta/
    _journal.json           # migration history journal
    0000_snapshot.json      # schema snapshot per migration
    0001_snapshot.json
```

Key behaviors:
- Detects column renames and table renames (prompts for confirmation)
- Generates `CREATE TABLE`, `ALTER TABLE`, `CREATE INDEX` statements
- Never modifies existing migration files
- Each `generate` creates exactly one new SQL file

### drizzle-kit migrate

Applies pending migrations from the output directory to the database. Tracks applied migrations in a `__drizzle_migrations` table.

```bash
npx drizzle-kit migrate
```

Alternatively, run migrations programmatically at application startup:

```typescript
import { drizzle } from "drizzle-orm/node-postgres";
import { migrate } from "drizzle-orm/node-postgres/migrator";

const db = drizzle(process.env.DATABASE_URL!);

await migrate(db, { migrationsFolder: "./drizzle" });
```

| Dialect | Migrator Import |
|---------|----------------|
| node-postgres | `drizzle-orm/node-postgres/migrator` |
| postgres-js | `drizzle-orm/postgres-js/migrator` |
| neon-http | `drizzle-orm/neon-http/migrator` |
| mysql2 | `drizzle-orm/mysql2/migrator` |
| better-sqlite3 | `drizzle-orm/better-sqlite3/migrator` |
| libsql | `drizzle-orm/libsql/migrator` |
| d1 | `drizzle-orm/d1/migrator` |

### drizzle-kit push

Pushes schema changes directly to the database without generating SQL files. Compares the live database schema to the TypeScript schema and applies diffs.

```bash
npx drizzle-kit push
```

| Aspect | push | generate + migrate |
|--------|------|-------------------|
| SQL files generated | No | Yes |
| Reversible | No (apply-only) | Yes (via manual SQL) |
| Team coordination | Poor (no shared history) | Good (migrations in git) |
| Speed | Instant | Two-step |
| Use case | Solo prototyping | Team/production |

Push is ideal for rapid local iteration. Switch to generate + migrate before merging to shared branches.

### drizzle-kit introspect

Reads an existing database and generates a TypeScript schema file. Use when adopting Drizzle on an existing database.

```bash
npx drizzle-kit introspect
```

Outputs `schema.ts` in the configured `out` directory. Review and move to the schema folder. Manually add relations declarations since introspect only generates table definitions.

### drizzle-kit studio

Launches Drizzle Studio, a browser-based database GUI for browsing and editing data.

```bash
npx drizzle-kit studio
```

Opens at `https://local.drizzle.studio`. Supports all dialects.

## Migration Strategies

### Development Workflow

```
1. Edit TypeScript schema
2. Run `drizzle-kit push` (fast iteration)
3. Repeat until schema is stable
4. Run `drizzle-kit generate` (create migration file)
5. Commit migration to git
6. Run `drizzle-kit migrate` on staging
```

### Production Workflow

```
1. Edit TypeScript schema on feature branch
2. Run `drizzle-kit generate` to create migration SQL
3. Review generated SQL in the PR
4. Merge to main
5. CI/CD runs `drizzle-kit migrate` against production
```

### Handling Renames

drizzle-kit detects potential renames and prompts interactively:

```
Is users.name renamed to users.full_name? [y/N]
```

If running in CI (non-interactive), pre-approve renames by reviewing the generated SQL before deployment.

### Data Migrations

drizzle-kit handles schema migrations (DDL) only. For data migrations (backfills, transforms), create a separate script:

```typescript
// scripts/backfill-display-name.ts
import { db } from "../src/db";
import { users } from "../src/db/schema";
import { sql } from "drizzle-orm";

await db.update(users).set({
  displayName: sql`${users.firstName} || ' ' || ${users.lastName}`,
});
```

Run data migrations after the schema migration that adds the new column.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Migrate Database
on:
  push:
    branches: [main]
    paths: ["drizzle/**"]

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx drizzle-kit migrate
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### Migration Safety Checklist

| Check | Why |
|-------|-----|
| Review generated SQL before merge | Catch destructive changes early |
| Run migrations in a transaction | Atomic apply or rollback (PG/MySQL) |
| Back up database before production migrate | Recovery path for failures |
| Test migrations against staging first | Catch data-dependent failures |
| Never edit committed migration files | Breaks the migration journal |
| Keep migrations small and focused | Easier to review and debug |

## Programmatic Migration API

```typescript
import { drizzle } from "drizzle-orm/node-postgres";
import { migrate } from "drizzle-orm/node-postgres/migrator";

async function runMigrations() {
  const db = drizzle(process.env.DATABASE_URL!);
  console.log("Running migrations...");

  await migrate(db, {
    migrationsFolder: "./drizzle",
  });

  console.log("Migrations complete.");
}

runMigrations().catch(console.error);
```

For serverless environments (Neon, D1), run migrations during build or in a separate deployment step rather than at cold start.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `generate` produces empty migration | No schema changes detected | Verify schema file is exported and config path is correct |
| `push` throws "column does not exist" | Schema references column before creation | Run `generate` + `migrate` instead for complex changes |
| `push` drops and recreates table | Renamed table detected as drop + create | Use `generate` (prompts for renames interactively) |
| Migration fails with FK constraint | Referenced table not yet created | Reorder migration or split into multiple steps |
| `__drizzle_migrations` table missing | First time running migrate | Table is auto-created on first `migrate` call |
| "No config found" error | Missing or misnamed config file | Ensure `drizzle.config.ts` exists at project root |
| Introspect generates wrong types | Database column types map differently | Manually adjust the generated schema file |
| Journal hash mismatch | Migration file was edited after apply | Never edit committed migration files. If needed, create a new migration |

## Custom Migration Behavior

### Running Specific Migrations

drizzle-kit applies all pending migrations. To skip or reorder:

1. Manually update `__drizzle_migrations` table to mark migrations as applied
2. Or use the programmatic API with custom logic

### Seeding

Drizzle does not have built-in seeding. Create seed scripts using the query builder:

```typescript
// scripts/seed.ts
import { db } from "../src/db";
import { users } from "../src/db/schema";

await db.insert(users).values([
  { name: "Alice", email: "alice@example.com" },
  { name: "Bob", email: "bob@example.com" },
]);
```

Add to package.json:

```json
{
  "scripts": {
    "db:seed": "tsx scripts/seed.ts",
    "db:migrate": "drizzle-kit migrate",
    "db:push": "drizzle-kit push",
    "db:generate": "drizzle-kit generate",
    "db:studio": "drizzle-kit studio"
  }
}
```
