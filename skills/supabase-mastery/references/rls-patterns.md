# RLS Patterns

Sources: Supabase Official Docs (Row Level Security), PostgreSQL Documentation (CREATE POLICY), GaryAustin1/RLS-Performance benchmarks, MakerKit (Supabase RLS Best Practices, 2026), Supabase GitHub Discussions #14576

Covers: RLS policy syntax, CRUD policy patterns, multi-tenant authorization, performance optimization with benchmarks, debugging techniques, and common security mistakes.

## RLS Fundamentals

Row Level Security adds a `WHERE` clause to every query automatically. When RLS is enabled on a table with no policies, all access is denied. Policies define who can do what.

### Enabling RLS

```sql
-- Enable RLS (required for every table exposed to the API)
alter table public.posts enable row level security;

-- Force RLS even for table owner (recommended for defense-in-depth)
alter table public.posts force row level security;
```

Tables created via the Supabase Dashboard Table Editor have RLS enabled by default. Tables created with raw SQL do not -- enable RLS manually.

### Policy Anatomy

```sql
create policy "policy_name"
on schema.table
as permissive                     -- or restrictive
for select | insert | update | delete | all
to role_name                      -- anon, authenticated, or custom role
using ( <boolean_expression> )    -- filters existing rows (SELECT/UPDATE/DELETE)
with check ( <boolean_expression> ); -- validates new/modified rows (INSERT/UPDATE)
```

### Which Clause for Which Operation

| Operation | `using` | `with check` | Notes |
|-----------|---------|--------------|-------|
| SELECT | Required | N/A | Filters visible rows |
| INSERT | N/A | Required | Validates new row data |
| UPDATE | Required | Optional | `using` filters rows; `with check` validates new values. If omitted, `using` applies to both |
| DELETE | Required | N/A | Filters which rows can be deleted |

### Permissive vs Restrictive

```sql
-- Permissive (default): policies OR together
-- If ANY permissive policy passes, access is granted
create policy "users_read_own" on posts as permissive
for select to authenticated
using ( (select auth.uid()) = author_id );

-- Restrictive: policies AND together with permissive policies
-- ALL restrictive policies must pass IN ADDITION to a permissive policy
create policy "mfa_required" on posts as restrictive
for update to authenticated
using ( (select auth.jwt()->>'aal') = 'aal2' );
```

Use restrictive policies for cross-cutting concerns (MFA enforcement, tenant isolation) that must always apply regardless of other access rules.

## CRUD Policy Patterns

### User Owns Row

The most common pattern -- users access only their own data:

```sql
-- SELECT: see own rows
create policy "users_select_own" on posts
for select to authenticated
using ( (select auth.uid()) = user_id );

-- INSERT: create rows assigned to self
create policy "users_insert_own" on posts
for insert to authenticated
with check ( (select auth.uid()) = user_id );

-- UPDATE: modify own rows, cannot reassign to another user
create policy "users_update_own" on posts
for update to authenticated
using ( (select auth.uid()) = user_id )
with check ( (select auth.uid()) = user_id );

-- DELETE: remove own rows
create policy "users_delete_own" on posts
for delete to authenticated
using ( (select auth.uid()) = user_id );
```

### Public Read, Authenticated Write

```sql
create policy "anyone_can_read" on posts
for select to anon, authenticated
using ( true );

create policy "authenticated_can_insert" on posts
for insert to authenticated
with check ( (select auth.uid()) = user_id );
```

### Role-Based Access

Store roles in `app_metadata` (not `user_metadata` -- users can modify their own `user_metadata`):

```sql
-- Admin can do everything
create policy "admin_all" on posts
for all to authenticated
using (
  (select auth.jwt()->'app_metadata'->>'role') = 'admin'
);

-- Moderator can update any post
create policy "moderator_update" on posts
for update to authenticated
using (
  (select auth.jwt()->'app_metadata'->>'role') in ('admin', 'moderator')
);
```

### Row-Level Visibility (Published/Draft)

```sql
create policy "public_sees_published" on posts
for select to anon, authenticated
using ( status = 'published' );

create policy "author_sees_own_drafts" on posts
for select to authenticated
using ( (select auth.uid()) = user_id );
```

Multiple permissive SELECT policies OR together, so users see published posts AND their own drafts.

## Multi-Tenant Patterns

### Tenant Isolation via app_metadata

```sql
-- Store org_id in app_metadata when user joins organization
-- (set via admin API or auth hook, never by the user)

create policy "tenant_isolation" on projects
for all to authenticated
using (
  org_id = (select auth.jwt()->'app_metadata'->>'org_id')::uuid
)
with check (
  org_id = (select auth.jwt()->'app_metadata'->>'org_id')::uuid
);
```

### Tenant Isolation via Membership Table

For users belonging to multiple organizations:

```sql
create policy "member_access" on projects
for select to authenticated
using (
  org_id in (
    select org_id from org_members
    where user_id = (select auth.uid())
  )
);
```

### Security Definer for Membership Lookup

Avoid RLS on the membership table itself slowing down the policy:

```sql
create or replace function private.get_user_org_ids()
returns setof uuid
language sql
security definer
set search_path = ''
as $$
  select org_id from public.org_members
  where user_id = (select auth.uid());
$$;

create policy "member_access_fast" on projects
for select to authenticated
using (
  org_id in (select private.get_user_org_ids())
);
```

Place security definer functions in a non-exposed schema (like `private`) to prevent direct API invocation.

## Performance Optimization

### The `(select ...)` Wrapper (Critical)

Wrapping function calls in `(select ...)` enables PostgreSQL to cache the result as an `initPlan`, called once per statement instead of once per row:

| Pattern | Performance |
|---------|-------------|
| `auth.uid() = user_id` | Calls `auth.uid()` per row -- slow |
| `(select auth.uid()) = user_id` | Calls once, caches result -- fast |

Benchmark: 179ms to 9ms (95% improvement) on a 100K-row table.

For security definer functions the improvement is even more dramatic -- 178,000ms to 12ms (99.99% improvement).

### Index Columns Used in Policies

```sql
-- If your policy filters on user_id, index it
create index idx_posts_user_id on posts using btree (user_id);

-- For multi-tenant, index org_id
create index idx_projects_org_id on projects using btree (org_id);
```

Benchmark: 171ms to <0.1ms (99.94% improvement) with index on policy column.

### Always Add Client-Side Filters

Even though RLS adds implicit WHERE clauses, duplicate the filter in the client query so PostgreSQL can build a better query plan:

```typescript
// Slow: relies only on RLS policy
const { data } = await supabase.from('posts').select();

// Fast: helps query planner use index
const { data } = await supabase.from('posts').select().eq('user_id', userId);
```

Benchmark: 171ms to 9ms (95% improvement).

### Specify Roles with `to`

```sql
-- Without role: policy evaluates for ALL roles including anon
create policy "bad" on posts using ( (select auth.uid()) = user_id );

-- With role: skips evaluation entirely for anon requests
create policy "good" on posts
for select to authenticated
using ( (select auth.uid()) = user_id );
```

Benchmark: 170ms to <0.1ms when an `anon` request hits a policy that specifies `to authenticated`.

### Avoid Joins in Policies

```sql
-- Slow: joins source table to target table
create policy "slow" on test_table to authenticated
using (
  (select auth.uid()) in (
    select user_id from team_user
    where team_user.team_id = team_id  -- references source row
  )
);

-- Fast: select into a set, no join to source
create policy "fast" on test_table to authenticated
using (
  team_id in (
    select team_id from team_user
    where user_id = (select auth.uid())  -- no join to source
  )
);
```

Benchmark: 9,000ms to 20ms (99.78% improvement).

## Debugging RLS

### Testing Policies Locally

```sql
-- Simulate authenticated user
set request.jwt.claims to '{"sub": "user-uuid-here", "role": "authenticated"}';
set role authenticated;

-- Run query
select * from posts;

-- Reset
reset role;
reset request.jwt.claims;
```

### Common Debug Checks

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Query returns empty array | RLS enabled, no matching policy | Add permissive policy for the operation |
| INSERT returns `new row violates RLS` | `with check` fails | Verify the inserted data matches policy |
| UPDATE has no effect | Missing SELECT policy | UPDATE requires a corresponding SELECT policy |
| Realtime not receiving events | RLS blocks SELECT for subscriber | Add SELECT policy for the subscribed user |
| `auth.uid()` returns null | No valid JWT / unauthenticated | Check auth state, verify token not expired |

### Views and RLS

Views bypass RLS by default (created with `security definer` implicitly). To enforce RLS through views:

```sql
create view public_posts
with (security_invoker = true)  -- Postgres 15+
as select * from posts where status = 'published';
```

## Common Mistakes

| Mistake | Risk | Fix |
|---------|------|-----|
| Forgetting to enable RLS on new table | Full data exposure via API | Always `alter table ... enable row level security` |
| Using `user_metadata` in policies | Users can modify it via `auth.update()` | Use `app_metadata` for authorization data |
| Not wrapping `auth.uid()` in `(select ...)` | Per-row function execution, massive slowdown | Always use `(select auth.uid())` |
| Missing index on policy column | Full table scan on every request | Add btree index on columns used in policies |
| No `to` clause on policy | Policy evaluates for all roles | Always specify `to authenticated` or `to anon` |
| Trusting `auth.jwt()` claims as "fresh" | JWT may be stale until refreshed | Keep JWTs short-lived, re-verify for sensitive ops |
| Missing `with check` on UPDATE | Users can change `user_id` to hijack rows | Add `with check` to prevent ownership transfer |
| Using `for all` without thinking | Grants SELECT+INSERT+UPDATE+DELETE | Write separate policies per operation for clarity |
| No RLS on storage buckets | Files accessible without authorization | Create storage policies, not just table policies |
