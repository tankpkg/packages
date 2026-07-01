---
name: "@tank/supabase-mastery"
description: |
  Full-stack Supabase development patterns for production applications.
  Covers Row Level Security (RLS policy syntax, multi-tenant patterns,
  performance optimization), Auth (email/password, OAuth, magic link, phone,
  MFA/TOTP, custom claims, session management, auth hooks), Database
  (PostgreSQL functions, triggers, views, migrations, type generation),
  Realtime (Postgres Changes, Broadcast, Presence), Edge Functions (Deno
  runtime, webhooks, secrets, CORS), Storage (uploads, signed URLs, image
  transforms, storage policies), supabase-js v2 client (query builder,
  TypeScript generics, error handling), CLI and local development (migrations,
  branching, seeding, type generation), framework integration (@supabase/ssr
  with Next.js App Router, React, React Native), and self-hosting.

  Synthesizes Supabase official documentation (2024-2026), PostgreSQL Row
  Level Security specification, Deno runtime documentation, and production
  community patterns from MakerKit, Supabase GitHub discussions, and the
  supabase-js v2 reference.

  Trigger phrases: "supabase", "supabase auth", "supabase rls",
  "row level security", "supabase realtime", "supabase edge functions",
  "supabase storage", "supabase next.js", "supabase typescript",
  "supabase-js", "supabase cli", "supabase migration", "supabase policy",
  "supabase self-host", "supabase react native", "supabase vs firebase",
  "supabase mfa", "supabase webhook", "supabase local dev",
  "createBrowserClient", "createServerClient", "@supabase/ssr",
  "auth.uid()", "auth.jwt()", "supabase gen types", "supabase storage policy"
---

# Supabase Mastery

## Core Philosophy

1. **RLS is your authorization layer** -- Row Level Security replaces application-level permission checks. Every table exposed to the API must have RLS enabled with policies, or data is either fully open (no RLS) or fully blocked (RLS on, no policies).
2. **Auth and database are one system** -- Supabase Auth writes to `auth.users` in the same PostgreSQL instance. Use `auth.uid()` and `auth.jwt()` directly in RLS policies -- no separate authorization service needed.
3. **Type safety from database to client** -- Run `supabase gen types typescript` to generate types from your schema. Pass the generated `Database` type to `createClient<Database>()` for end-to-end type safety with zero manual type maintenance.
4. **Server-side client for server code** -- Use `createServerClient` (from `@supabase/ssr`) in Next.js Server Components, Route Handlers, and Server Actions. Use `createBrowserClient` only in Client Components. Never expose the service role key to the browser.
5. **Wrap auth helper calls in `(select ...)` for RLS performance** -- `(select auth.uid()) = user_id` caches the function result per statement. Without `select`, PostgreSQL calls `auth.uid()` per row, causing orders-of-magnitude slowdowns on large tables.

## Quick-Start: Common Problems

### "How do I set up auth with Next.js?"

1. Install `@supabase/ssr` and `@supabase/supabase-js`
2. Create server client utility using `createServerClient` with cookie handlers
3. Create browser client utility using `createBrowserClient`
4. Add middleware to refresh sessions on every request
5. Use server client in Server Components, browser client in Client Components
-> See `references/nextjs-integration.md`

### "My RLS policy blocks everything (or allows everything)"

1. Verify RLS is enabled: `alter table <name> enable row level security`
2. Check policy targets correct operation (SELECT/INSERT/UPDATE/DELETE)
3. For SELECT, use `using (...)`. For INSERT, use `with check (...)`
4. For UPDATE, supply both `using (...)` and `with check (...)`
5. Always specify the role with `to authenticated` or `to anon`
6. Test with `supabase.auth.getUser()` -- not `getSession()` -- for server-side validation
-> See `references/rls-patterns.md`

### "Realtime subscriptions are not receiving events"

1. Confirm RLS policies allow SELECT for the subscribing user
2. Check that `supabase_realtime` publication includes the table
3. Verify the channel filter matches (schema, table, filter)
4. For Postgres Changes, use `.on('postgres_changes', { event: '*', schema: 'public', table: 'messages' }, callback)`
-> See `references/realtime.md`

### "How do I structure a multi-tenant app?"

1. Add `org_id` column to every tenant-scoped table
2. Store tenant membership in `app_metadata` via auth hooks or admin API
3. Write RLS policies using `auth.jwt()->'app_metadata'->>'org_id'`
4. Use security definer functions for cross-tenant admin queries
-> See `references/rls-patterns.md` and `references/auth-patterns.md`

## Decision Trees

### Client Type Selection

| Context | Client | Package |
|---------|--------|---------|
| Next.js Server Component / Route Handler | `createServerClient` | `@supabase/ssr` |
| Next.js Client Component | `createBrowserClient` | `@supabase/ssr` |
| Next.js Middleware | `createServerClient` (with cookie middleware) | `@supabase/ssr` |
| Edge Function | `createClient` with `Authorization` header | `@supabase/supabase-js` |
| React SPA (no SSR) | `createClient` | `@supabase/supabase-js` |
| Admin / service role | `createClient` with service role key | `@supabase/supabase-js` |

### Auth Method Selection

| Requirement | Method |
|-------------|--------|
| Standard email + password | `signUp` / `signInWithPassword` |
| Passwordless | Magic link (`signInWithOtp`) or OAuth |
| Social login (Google, GitHub, etc.) | `signInWithOAuth` with PKCE |
| Phone-based | `signInWithOtp` with phone |
| Enterprise SSO | SAML via Supabase SSO |
| Additional security factor | TOTP MFA enrollment + verification |

### Data Access Method

| Need | Approach |
|------|----------|
| CRUD from client with RLS | supabase-js query builder (`.from().select()`) |
| Complex query / aggregation | Database function + `.rpc()` |
| Webhook / external trigger | Edge Function |
| Scheduled job | Edge Function + `pg_cron` or external cron |
| File upload | Supabase Storage with RLS policies |
| Real-time updates | Realtime channel subscription |

## Reference Index

| File | Contents |
|------|----------|
| `references/rls-patterns.md` | RLS policy syntax, CRUD policies, multi-tenant patterns, performance optimization, debugging, common mistakes |
| `references/auth-patterns.md` | Email/OAuth/magic link/phone auth, MFA/TOTP, custom claims, auth hooks, session management, JWTs in Supabase |
| `references/database-patterns.md` | PostgreSQL functions, triggers, views, generated columns, migrations, type generation, query patterns |
| `references/realtime.md` | Postgres Changes, Broadcast, Presence, channel management, filtering, RLS interaction, performance |
| `references/edge-functions.md` | Deno runtime, project structure, secrets, CORS, invoking from client, webhooks, testing, deployment |
| `references/storage.md` | Bucket types, upload patterns, signed URLs, image transforms, storage RLS policies, CDN |
| `references/nextjs-integration.md` | @supabase/ssr setup, server/browser clients, middleware, protected routes, Server Actions, cookie auth |
| `references/client-library.md` | supabase-js v2 query builder, TypeScript generics, filtering, joins, pagination, error handling, realtime subscriptions |
