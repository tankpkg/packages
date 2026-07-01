# Database Patterns

Sources: Supabase Official Docs (Database, Functions, Triggers), PostgreSQL Documentation (CREATE FUNCTION, CREATE TRIGGER, Views), Supabase CLI Reference (migrations, gen types), supabase-js v2 Reference

Covers: PostgreSQL functions, triggers, views, generated columns, migration workflow, type generation, foreign key patterns, and database-level patterns specific to Supabase projects.

## PostgreSQL Functions

### Basic Function

```sql
create or replace function public.get_user_profile(user_uuid uuid)
returns jsonb
language plpgsql
security invoker  -- runs as the calling user (respects RLS)
set search_path = ''
as $$
declare
  result jsonb;
begin
  select jsonb_build_object(
    'id', u.id,
    'email', u.email,
    'display_name', u.raw_user_meta_data->>'display_name'
  ) into result
  from auth.users u
  where u.id = user_uuid;

  return result;
end;
$$;
```

### Security Definer vs Security Invoker

| Attribute | `security invoker` | `security definer` |
|-----------|-------------------|-------------------|
| RLS | Respects caller's policies | Bypasses RLS (runs as function owner) |
| Use when | Standard user-facing queries | Admin lookups, cross-tenant reads, helper functions for RLS |
| Risk | None -- standard behavior | Elevated privilege -- restrict access |
| Best practice | Default choice | Place in non-exposed schema (`private`), restrict with `revoke` |

### Security Definer Safety Pattern

```sql
-- Create in a non-exposed schema
create or replace function private.is_org_member(check_org_id uuid)
returns boolean
language plpgsql
security definer
set search_path = ''  -- prevents search_path injection
as $$
begin
  return exists (
    select 1 from public.org_members
    where user_id = (select auth.uid())
    and org_id = check_org_id
  );
end;
$$;

-- Revoke access from API roles
revoke execute on function private.is_org_member from public;
revoke execute on function private.is_org_member from anon;
revoke execute on function private.is_org_member from authenticated;
```

### Calling Functions from Client

```typescript
// Simple function call
const { data, error } = await supabase.rpc('get_user_profile', {
  user_uuid: userId,
});

// Function returning a set of rows
const { data, error } = await supabase
  .rpc('search_posts', { search_term: 'supabase' })
  .select('id, title, created_at')
  .order('created_at', { ascending: false })
  .limit(10);
```

Functions exposed via `.rpc()` must be in the `public` schema (or whichever schema is configured in API settings).

## Triggers

### Trigger to Auto-Set Timestamps

```sql
-- Reusable trigger function
create or replace function public.handle_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- Attach to a table
create trigger set_updated_at
before update on public.posts
for each row
execute function public.handle_updated_at();
```

### Trigger to Create Profile on Signup

```sql
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, display_name, avatar_url)
  values (
    new.id,
    new.raw_user_meta_data->>'display_name',
    new.raw_user_meta_data->>'avatar_url'
  );
  return new;
end;
$$;

create trigger on_auth_user_created
after insert on auth.users
for each row
execute function public.handle_new_user();
```

This trigger fires when a new user signs up via any method (email, OAuth, phone). The profile row is created automatically.

### Trigger to Sync Deleted Users

```sql
create or replace function public.handle_user_deleted()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  delete from public.profiles where id = old.id;
  return old;
end;
$$;

create trigger on_auth_user_deleted
after delete on auth.users
for each row
execute function public.handle_user_deleted();
```

### Trigger Patterns

| Timing | Use Case |
|--------|----------|
| `before insert` | Set defaults, validate data, generate slugs |
| `after insert` | Create related records, send notifications |
| `before update` | Set `updated_at`, validate state transitions |
| `after update` | Audit logging, sync to external systems |
| `before delete` | Cascade soft-deletes, validation |
| `after delete` | Cleanup related records, audit trail |

## Views

### Standard View

```sql
create view public.post_summaries as
select
  p.id,
  p.title,
  p.created_at,
  pr.display_name as author_name,
  count(c.id) as comment_count
from public.posts p
left join public.profiles pr on p.user_id = pr.id
left join public.comments c on c.post_id = p.id
group by p.id, p.title, p.created_at, pr.display_name;
```

Views bypass RLS by default. For views that should respect calling user's policies:

```sql
create view public.my_posts
with (security_invoker = true)
as select * from public.posts;
```

### Materialized Views for Performance

```sql
create materialized view public.popular_posts as
select p.*, count(l.id) as like_count
from public.posts p
left join public.likes l on l.post_id = p.id
group by p.id
order by like_count desc
limit 100;

-- Refresh periodically (via pg_cron or Edge Function)
refresh materialized view concurrently public.popular_posts;
```

## Generated Columns

```sql
create table public.posts (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  body text,
  slug text generated always as (
    lower(regexp_replace(title, '[^a-zA-Z0-9]+', '-', 'g'))
  ) stored,
  word_count int generated always as (
    array_length(regexp_split_to_array(coalesce(body, ''), '\s+'), 1)
  ) stored,
  search_vector tsvector generated always as (
    to_tsvector('english', coalesce(title, '') || ' ' || coalesce(body, ''))
  ) stored
);

-- Index the generated column for full-text search
create index idx_posts_search on posts using gin (search_vector);
```

## Migration Workflow

### Create and Apply Migrations

```bash
# Initialize Supabase locally (creates supabase/ directory)
supabase init

# Link to remote project
supabase link --project-ref <project-id>

# Create a new migration
supabase migration new create_posts_table
# Edit supabase/migrations/<timestamp>_create_posts_table.sql

# Apply migrations locally
supabase db reset  # drops and recreates from migrations

# Push migrations to remote
supabase db push

# Pull remote schema changes (dashboard edits) into a migration
supabase db pull
# Creates a new migration file capturing remote schema diff
```

### Migration File Structure

```
supabase/
  migrations/
    20240101000000_create_profiles.sql
    20240102000000_create_posts.sql
    20240103000000_add_rls_policies.sql
  seed.sql         -- seed data for local development
  config.toml      -- local configuration
```

### Seed Data

```sql
-- supabase/seed.sql (runs after migrations on db reset)
insert into public.profiles (id, display_name)
values
  ('00000000-0000-0000-0000-000000000001', 'Test User'),
  ('00000000-0000-0000-0000-000000000002', 'Admin User');

insert into public.posts (title, user_id, status)
values
  ('First Post', '00000000-0000-0000-0000-000000000001', 'published'),
  ('Draft Post', '00000000-0000-0000-0000-000000000001', 'draft');
```

### Diffing and Generating Migrations

```bash
# Compare local schema with a migration-generated schema
supabase db diff --use-migra -f add_comments_table

# This generates a migration file with the SQL diff
# Review before applying
```

## Type Generation

### Generate Types from Database Schema

```bash
# Generate types from remote project
supabase gen types typescript --project-id <ref> > src/types/database.ts

# Generate from local database
supabase gen types typescript --local > src/types/database.ts
```

### Use Generated Types

```typescript
import { createClient } from '@supabase/supabase-js';
import type { Database } from '@/types/database';

const supabase = createClient<Database>(url, anonKey);

// Fully typed -- IDE autocompletes table names, columns, return types
const { data } = await supabase
  .from('posts')           // autocompletes table names
  .select('id, title')     // autocompletes column names
  .eq('status', 'published');

// data is typed as Pick<Database['public']['Tables']['posts']['Row'], 'id' | 'title'>[]
```

### Type Helpers

```typescript
import type { Database } from '@/types/database';

// Extract row type
type Post = Database['public']['Tables']['posts']['Row'];

// Extract insert type (columns with defaults become optional)
type NewPost = Database['public']['Tables']['posts']['Insert'];

// Extract update type (all columns optional)
type PostUpdate = Database['public']['Tables']['posts']['Update'];

// Function return type
type SearchResult = Database['public']['Functions']['search_posts']['Returns'];
```

### Automate Type Generation

```json
// package.json
{
  "scripts": {
    "db:types": "supabase gen types typescript --project-id $PROJECT_REF > src/types/database.ts",
    "db:push": "supabase db push && npm run db:types"
  }
}
```

Run `db:types` after every migration to keep client types in sync with the schema.

## Foreign Key Patterns

### Reference auth.users

```sql
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  bio text,
  created_at timestamptz default now()
);
```

Use `on delete cascade` to clean up profile when a user is deleted via the admin API.

### Querying Relationships

```typescript
// Foreign key join (automatic via PostgREST)
const { data } = await supabase
  .from('posts')
  .select(`
    id,
    title,
    profiles!posts_user_id_fkey (
      display_name,
      avatar_url
    )
  `);

// Shorthand when only one FK exists between tables
const { data } = await supabase
  .from('posts')
  .select('id, title, profiles(display_name)');
```

### Self-Referencing Foreign Keys

```sql
create table public.comments (
  id uuid primary key default gen_random_uuid(),
  post_id uuid references public.posts(id) on delete cascade,
  parent_id uuid references public.comments(id) on delete cascade,
  user_id uuid references auth.users(id),
  body text not null,
  created_at timestamptz default now()
);
```

## Database Configuration

### Connection Pooling (Supavisor)

Supabase uses Supavisor for connection pooling. Connection strings:

| Mode | Port | Use Case |
|------|------|----------|
| Transaction | 6543 | Serverless, Edge Functions, short-lived connections |
| Session | 5432 | Long-lived connections, prepared statements |

Edge Functions and serverless platforms should always use the transaction pooler (port 6543) to avoid exhausting connections.

### Extensions

```sql
-- Enable commonly used extensions
create extension if not exists "uuid-ossp";     -- uuid_generate_v4()
create extension if not exists "pgcrypto";       -- gen_random_uuid() (built-in from PG13)
create extension if not exists "pg_trgm";        -- trigram similarity for fuzzy search
create extension if not exists "pgroonga";       -- full-text search (multilingual)
create extension if not exists "pg_cron";        -- scheduled jobs
create extension if not exists "vector";         -- pgvector for embeddings
```

Enable extensions via SQL Editor or include in migrations.
