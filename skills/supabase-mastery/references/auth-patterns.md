# Supabase Auth Patterns

Sources: Supabase Auth Documentation (2024-2026), Supabase Auth Helpers Reference, Supabase GitHub (gotrue), RFC 6238 (TOTP), OWASP Authentication Cheat Sheet

Covers: Authentication methods (email, OAuth, magic link, phone), MFA/TOTP implementation, custom claims and app_metadata, auth hooks, session management, JWT structure in Supabase, and admin operations.

## Authentication Methods

### Email/Password

```typescript
// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password',
  options: {
    data: {
      display_name: 'Jane Doe',  // stored in user_metadata
    },
    emailRedirectTo: 'https://app.example.com/welcome',
  },
});

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password',
});
```

Configure email confirmation in Dashboard > Auth > Settings. When enabled, `signUp` returns a user with `confirmed_at = null` until the user clicks the confirmation link.

### Magic Link (Passwordless)

```typescript
const { data, error } = await supabase.auth.signInWithOtp({
  email: 'user@example.com',
  options: {
    emailRedirectTo: 'https://app.example.com/auth/callback',
    shouldCreateUser: true,  // create user if not exists
  },
});
```

User receives an email with a link. Clicking it exchanges a token for a session. No password stored.

### OAuth (Social Login)

```typescript
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: 'https://app.example.com/auth/callback',
    scopes: 'email profile',
    queryParams: {
      access_type: 'offline',    // for refresh token (Google)
      prompt: 'consent',         // force consent screen
    },
  },
});
```

Supported providers: Google, GitHub, Apple, Azure, Discord, Facebook, Figma, GitLab, Kakao, Keycloak, LinkedIn, Notion, Slack, Spotify, Twitch, Twitter, WorkOS, Zoom.

### Phone Auth (OTP)

```typescript
// Send OTP
const { data, error } = await supabase.auth.signInWithOtp({
  phone: '+1234567890',
});

// Verify OTP
const { data, error } = await supabase.auth.verifyOtp({
  phone: '+1234567890',
  token: '123456',
  type: 'sms',
});
```

Requires Twilio, MessageBird, or Vonage configured in Dashboard > Auth > Providers.

### Anonymous Auth

```typescript
const { data, error } = await supabase.auth.signInAnonymously();
// data.user.is_anonymous === true
// Uses 'authenticated' role (not 'anon')
```

Anonymous users can later link to a permanent identity:

```typescript
const { data, error } = await supabase.auth.updateUser({
  email: 'user@example.com',
  password: 'new-password',
});
// Converts anonymous user to permanent user
```

## OAuth Callback Handling

The callback route exchanges the auth code for a session:

```typescript
// app/auth/callback/route.ts (Next.js App Router)
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get('code');
  const next = searchParams.get('next') ?? '/';

  if (code) {
    const cookieStore = await cookies();
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll: () => cookieStore.getAll(),
          setAll: (cookiesToSet) => {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          },
        },
      }
    );
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }
  return NextResponse.redirect(`${origin}/auth/error`);
}
```

## MFA (Multi-Factor Authentication)

### TOTP Enrollment

```typescript
// Step 1: Enroll
const { data, error } = await supabase.auth.mfa.enroll({
  factorType: 'totp',
  friendlyName: 'Authenticator App',
});
// data.totp.qr_code -- display as QR for scanning
// data.totp.secret  -- manual entry key
// data.totp.uri     -- otpauth:// URI
// data.id           -- factor ID for verification

// Step 2: Verify enrollment (user enters code from app)
const { data: challenge } = await supabase.auth.mfa.challenge({
  factorId: data.id,
});
const { data: verify, error } = await supabase.auth.mfa.verify({
  factorId: data.id,
  challengeId: challenge.id,
  code: '123456', // from authenticator app
});
```

### Enforce MFA via RLS

```sql
-- Require AAL2 (MFA verified) for sensitive operations
create policy "mfa_required_for_update" on sensitive_data
as restrictive
for update to authenticated
using ( (select auth.jwt()->>'aal') = 'aal2' );
```

### Check MFA Status Client-Side

```typescript
const { data: { currentLevel, nextLevel } } =
  await supabase.auth.mfa.getAuthenticatorAssuranceLevel();

if (currentLevel === 'aal1' && nextLevel === 'aal2') {
  // User has MFA enrolled but hasn't verified this session
  // Redirect to MFA verification page
}
```

## Custom Claims and app_metadata

### Metadata Types

| Field | Location | Mutable By User | Use For |
|-------|----------|----------------|---------|
| `user_metadata` | `raw_user_meta_data` | Yes (`auth.update()`) | Display name, avatar, preferences |
| `app_metadata` | `raw_app_meta_data` | No (admin only) | Roles, org_id, permissions, subscription tier |

### Setting app_metadata (Admin Only)

```typescript
// Server-side only -- requires service role key
const supabaseAdmin = createClient(url, serviceRoleKey);

await supabaseAdmin.auth.admin.updateUserById(userId, {
  app_metadata: {
    role: 'admin',
    org_id: 'org-uuid',
    teams: ['team-a', 'team-b'],
  },
});
```

### Reading Claims in RLS

```sql
-- Role check
(select auth.jwt()->'app_metadata'->>'role') = 'admin'

-- Org membership
org_id = (select auth.jwt()->'app_metadata'->>'org_id')::uuid

-- Team membership (array)
team_id in (
  select jsonb_array_elements_text(
    (select auth.jwt()->'app_metadata'->'teams')
  )::uuid
)
```

## Auth Hooks

Auth hooks run custom logic during authentication events. Configure via Dashboard > Auth > Hooks or as PostgreSQL functions.

### Hook Types

| Hook | Trigger | Use Case |
|------|---------|----------|
| `custom_access_token` | Before JWT is issued | Add custom claims to JWT |
| `mfa_verification_attempt` | On MFA code submission | Custom rate limiting, logging |
| `password_verification_attempt` | On password check | Custom rate limiting |
| `send_email` | Before email is sent | Custom email provider |
| `send_sms` | Before SMS is sent | Custom SMS provider |

### Custom Access Token Hook (Add Claims)

```sql
create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  claims jsonb;
  user_role text;
begin
  select role into user_role
  from public.user_roles
  where user_id = (event->>'user_id')::uuid;

  claims := event->'claims';
  claims := jsonb_set(claims, '{user_role}', to_jsonb(coalesce(user_role, 'member')));
  event := jsonb_set(event, '{claims}', claims);

  return event;
end;
$$;

grant usage on schema public to supabase_auth_admin;
grant execute on function public.custom_access_token_hook to supabase_auth_admin;
revoke execute on function public.custom_access_token_hook from authenticated, anon;
```

## Session Management

### JWT Structure in Supabase

Supabase JWTs contain:

| Claim | Content |
|-------|---------|
| `sub` | User UUID (`auth.uid()`) |
| `role` | `authenticated` or `anon` |
| `aal` | Authenticator assurance level (`aal1` or `aal2`) |
| `session_id` | Current session UUID |
| `app_metadata` | Custom application claims |
| `user_metadata` | User-editable profile data |
| `exp` | Expiry timestamp |

Default access token expiry: 3600 seconds (1 hour). Configurable in Dashboard > Auth > Settings.

### Session Refresh

```typescript
// Auto-refresh is handled by the client library
// Manual refresh (rarely needed):
const { data, error } = await supabase.auth.refreshSession();
```

### Sign Out

```typescript
// Sign out current session
await supabase.auth.signOut();

// Sign out all sessions (requires service role for other users)
await supabase.auth.signOut({ scope: 'global' });
```

### Server-Side User Validation

```typescript
// CORRECT: validates JWT with auth server
const { data: { user } } = await supabase.auth.getUser();

// WRONG for server-side: reads JWT without validation
const { data: { session } } = await supabase.auth.getSession();
```

Use `getUser()` in server-side code -- it makes a network request to validate the JWT. `getSession()` only reads the local JWT without verifying it, which is acceptable for client-side UI decisions but not for server-side authorization.

## Admin Operations

All admin operations require the service role key. Never expose this key to clients.

```typescript
const supabaseAdmin = createClient(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

// List users
const { data } = await supabaseAdmin.auth.admin.listUsers();

// Create user (bypasses email confirmation)
const { data } = await supabaseAdmin.auth.admin.createUser({
  email: 'admin@example.com',
  password: 'secure-password',
  email_confirm: true,
  app_metadata: { role: 'admin' },
});

// Delete user
await supabaseAdmin.auth.admin.deleteUser(userId);

// Generate invite link
const { data } = await supabaseAdmin.auth.admin.generateLink({
  type: 'invite',
  email: 'new@example.com',
});
```
