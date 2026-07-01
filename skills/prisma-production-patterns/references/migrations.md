# Migrations

Sources: Prisma ORM Documentation (prisma.io/docs), Prisma Migrate reference, Prisma Blog engineering posts, 2025-2026 production migration patterns

Covers: Prisma Migrate workflow (dev, deploy, resolve), migration history, baselining existing databases, custom SQL in migrations, shadow database, squashing migrations, CI/CD integration, and production troubleshooting.

## Migration Mental Model

Prisma Migrate uses a declarative approach: define the desired state in the schema, and Prisma generates the SQL to get there. The migration history is a sequence of SQL files that, when applied in order, recreate the database schema.

```
schema.prisma (desired state)
       |
       v
prisma migrate dev (generates SQL diff)
       |
       v
migrations/YYYYMMDDHHMMSS_name/migration.sql
       |
       v
prisma migrate deploy (applies to production)
```

### Key Commands

| Command | Environment | Purpose |
|---------|-------------|---------|
| `prisma migrate dev` | Development | Generate and apply migration |
| `prisma migrate deploy` | Production/CI | Apply pending migrations |
| `prisma migrate resolve` | Production | Mark migration as applied/rolled back |
| `prisma migrate diff` | Any | Generate SQL diff without applying |
| `prisma migrate status` | Any | Check migration status |
| `prisma migrate reset` | Development only | Drop database, re-apply all migrations, re-seed |
| `prisma db push` | Prototyping | Push schema changes without migration files |
| `prisma db pull` | Any | Introspect database into schema |

## Development Workflow

### Creating Migrations

```bash
# Generate migration from schema changes
npx prisma migrate dev --name add_user_profile

# Generate migration without applying (review first)
npx prisma migrate dev --create-only --name add_user_profile
```

`migrate dev`:
1. Detects schema changes by comparing schema to migration history
2. Generates a SQL migration file
3. Applies the migration to the development database
4. Regenerates Prisma Client

### Migration File Structure

```
prisma/
  migrations/
    20240101120000_init/
      migration.sql
    20240115090000_add_user_profile/
      migration.sql
    migration_lock.toml    # Locks the database provider
```

Each migration folder contains a `migration.sql` with the SQL statements. The folder name format is `YYYYMMDDHHMMSS_your_name`. The `migration_lock.toml` prevents switching database providers.

### Reviewing Generated SQL

Always review generated migrations before committing:

```bash
# Generate without applying
npx prisma migrate dev --create-only --name add_index

# Review the SQL
cat prisma/migrations/20240115090000_add_index/migration.sql

# Apply after review
npx prisma migrate dev
```

This is critical for:
- Destructive operations (column drops, type changes)
- Data migrations (backfilling new columns)
- Performance-sensitive changes (large table alterations)

### Schema Prototyping with db push

```bash
# Push schema changes directly (no migration files)
npx prisma db push
```

Use `db push` during early prototyping when the schema is changing rapidly. Switch to `migrate dev` once the schema stabilizes. `db push` does not create migration files and cannot be used for production deployments.

## Production Deployment

### Applying Migrations in Production

```bash
# Apply all pending migrations
npx prisma migrate deploy
```

`migrate deploy`:
- Applies only unapplied migrations from the history
- Does NOT generate new migrations
- Does NOT reset the database
- Does NOT run seed scripts
- Safe for CI/CD pipelines and production

### CI/CD Pipeline

```yaml
# GitHub Actions example
jobs:
  deploy:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npx prisma generate
      - run: npx prisma migrate deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
      - run: npm run build
      - run: npm run deploy
```

Run `prisma generate` before build (for type generation) and `prisma migrate deploy` before deployment (for schema changes).

### Deployment Order

1. Apply migrations (`prisma migrate deploy`)
2. Deploy application code
3. Roll back application if migrations fail

Never deploy application code that depends on schema changes before applying the migration. Use backward-compatible migrations when possible.

## Baselining Existing Databases

When adding Prisma Migrate to an existing database:

### Step 1: Introspect Current Schema

```bash
npx prisma db pull
```

This generates a Prisma schema matching the current database.

### Step 2: Create Baseline Migration

```bash
# Generate SQL that represents current schema
mkdir -p prisma/migrations/0_init

npx prisma migrate diff \
  --from-empty \
  --to-schema prisma/schema.prisma \
  --script > prisma/migrations/0_init/migration.sql
```

### Step 3: Mark as Applied

```bash
# Tell Prisma this migration is already applied
npx prisma migrate resolve --applied 0_init
```

This prevents Prisma from trying to re-create existing tables. Future `migrate dev` commands generate only the diff from this baseline.

## Custom SQL in Migrations

### Adding Custom SQL

Generate the migration without applying, then edit:

```bash
npx prisma migrate dev --create-only --name add_trigger
```

Edit the generated `migration.sql` to add custom SQL:

```sql
-- Generated by Prisma
ALTER TABLE "User" ADD COLUMN "searchVector" tsvector;

-- Custom: Add trigger for full-text search
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW."searchVector" = to_tsvector('english', COALESCE(NEW."name", '') || ' ' || COALESCE(NEW."email", ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_search_update
BEFORE INSERT OR UPDATE ON "User"
FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- Custom: GIN index for full-text search
CREATE INDEX "User_searchVector_idx" ON "User" USING gin("searchVector");
```

Then apply:

```bash
npx prisma migrate dev
```

### Data Migrations

For backfilling data in a new column:

```sql
-- Add column as nullable first
ALTER TABLE "Post" ADD COLUMN "slug" TEXT;

-- Backfill existing data
UPDATE "Post" SET "slug" = lower(replace("title", ' ', '-'));

-- Make column required after backfill
ALTER TABLE "Post" ALTER COLUMN "slug" SET NOT NULL;

-- Add unique constraint
ALTER TABLE "Post" ADD CONSTRAINT "Post_slug_key" UNIQUE ("slug");
```

Split data migrations into separate steps to avoid locking large tables for extended periods.

## Shadow Database

Prisma Migrate uses a shadow database during `migrate dev` to:
1. Detect schema drift (manual changes to the development database)
2. Generate accurate migration SQL

The shadow database is created, migrated, compared, and dropped automatically. Ensure the database user has CREATE DATABASE permissions, or configure a dedicated shadow database:

```prisma
datasource db {
  provider          = "postgresql"
  url               = env("DATABASE_URL")
  shadowDatabaseUrl = env("SHADOW_DATABASE_URL")
}
```

Some managed databases (e.g., Neon, PlanetScale) require a separate shadow database URL because they restrict CREATE DATABASE privileges.

## Squashing Migrations

Over time, migration history grows. Squash old migrations into a single baseline:

### Procedure

1. Ensure all environments have applied all migrations
2. Delete the `prisma/migrations` directory
3. Create a new baseline:

```bash
mkdir -p prisma/migrations/0_init

npx prisma migrate diff \
  --from-empty \
  --to-schema prisma/schema.prisma \
  --script > prisma/migrations/0_init/migration.sql
```

4. Mark as applied on all existing databases:

```bash
npx prisma migrate resolve --applied 0_init
```

5. Commit the new migration history

Only squash when all deployment targets have the same migration state. New environments use the squashed baseline.

## Troubleshooting Production Migrations

### Failed Migration

When a migration partially applies and fails:

```bash
# Check status
npx prisma migrate status

# If migration failed mid-way, fix manually then mark as applied
npx prisma migrate resolve --applied 20240115090000_add_user_profile

# If migration should be rolled back
npx prisma migrate resolve --rolled-back 20240115090000_add_user_profile
```

### Generating Fix Migrations

```bash
# Generate SQL to fix drift between schema and database
npx prisma migrate diff \
  --from-schema prisma/schema.prisma \
  --to-database \
  --script

# Apply fix SQL directly
npx prisma db execute --file fix.sql
```

### Common Migration Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `P3009` | Migration failed, database may be dirty | Fix manually, then `resolve --applied` |
| `P3006` | Migration partially applied | Fix data issues, then `resolve --applied` |
| `P3005` | Database schema not empty for baseline | Use `resolve --applied` for baseline |
| `P3014` | Shadow database creation failed | Configure `shadowDatabaseUrl` |
| `P3018` | Migration history diverged | Reset dev database or reconcile |

### Zero-Downtime Migrations

For production systems that cannot tolerate downtime:

1. Make all schema changes backward-compatible
2. Split breaking changes across multiple deployments:
   - Deploy 1: Add new nullable column
   - Deploy 2: Backfill data, update application code
   - Deploy 3: Make column required, drop old column
3. Never rename or drop columns in a single step
4. Add indexes with `CONCURRENTLY` (PostgreSQL) via custom SQL

```sql
-- Custom migration for non-blocking index creation
CREATE INDEX CONCURRENTLY "Post_slug_idx" ON "Post" ("slug");
```

`CREATE INDEX CONCURRENTLY` must run outside a transaction. Edit the migration to remove the Prisma-generated transaction wrapper if present.
