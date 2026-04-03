# Next.js Integration

Sources: Supabase SSR Documentation (@supabase/ssr), Supabase Next.js Quickstart Guide, Next.js App Router Documentation, Supabase Auth Helpers Migration Guide (auth-helpers to ssr), supabase-js v2 Reference

Covers: @supabase/ssr package setup, server and browser client creation, middleware for session refresh, protected routes, Server Actions with Supabase, OAuth callback handling, and common Next.js patterns.

## Package Setup

```bash
npm install @supabase/supabase-js @supabase/ssr
```

Environment variables:

```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOi...
```

The `NEXT_PUBLIC_` prefix exposes these to the browser. The anon key is safe to expose -- RLS protects data.

## Client Utilities

### Server Client

```typescript
// lib/supabase/server.ts
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          } catch {
            // setAll called from Server Component -- ignore
            // Middleware handles cookie refresh
          }
        },
      },
    }
  );
}
```

### Browser Client

```typescript
// lib/supabase/client.ts
import { createBrowserClient } from '@supabase/ssr';

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
```

### When to Use Which Client

| Context | Client | Import From |
|---------|--------|-------------|
| Server Component | `createServerClient` | `lib/supabase/server` |
| Route Handler (`route.ts`) | `createServerClient` | `lib/supabase/server` |
| Server Action | `createServerClient` | `lib/supabase/server` |
| Middleware | `createServerClient` (inline) | `@supabase/ssr` |
| Client Component (`'use client'`) | `createBrowserClient` | `lib/supabase/client` |

## Middleware (Session Refresh)

Middleware refreshes the auth session on every request by reading and rewriting cookies. Without middleware, sessions expire and users get logged out unexpectedly.

```typescript
// middleware.ts
import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            request.cookies.set(name, value)
          );
          supabaseResponse = NextResponse.next({
            request,
          });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // Refresh session -- important for Server Components
  const { data: { user } } = await supabase.auth.getUser();

  return supabaseResponse;
}

export const config = {
  matcher: [
    // Match all paths except static files and images
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
```

### Why Middleware Matters

- Server Components cannot set cookies directly
- Without middleware, the auth token expires and is never refreshed
- The middleware reads the auth cookie, refreshes it if needed, and writes the new cookie to the response
- Place the `supabase.auth.getUser()` call in middleware to trigger the refresh

## Protected Routes

### Server Component Protection

```typescript
// app/dashboard/page.tsx
import { createClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect('/login');
  }

  const { data: posts } = await supabase
    .from('posts')
    .select('*')
    .order('created_at', { ascending: false });

  return (
    <div>
      <h1>Welcome, {user.email}</h1>
      {/* render posts */}
    </div>
  );
}
```

### Middleware-Level Protection

```typescript
// Inside middleware.ts, after getUser()
const { data: { user } } = await supabase.auth.getUser();

// Protect dashboard routes
if (!user && request.nextUrl.pathname.startsWith('/dashboard')) {
  const url = request.nextUrl.clone();
  url.pathname = '/login';
  return NextResponse.redirect(url);
}

// Redirect logged-in users away from auth pages
if (user && request.nextUrl.pathname.startsWith('/login')) {
  const url = request.nextUrl.clone();
  url.pathname = '/dashboard';
  return NextResponse.redirect(url);
}
```

## Server Actions

```typescript
// app/posts/actions.ts
'use server';

import { createClient } from '@/lib/supabase/server';
import { revalidatePath } from 'next/cache';

export async function createPost(formData: FormData) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return { error: 'Not authenticated' };
  }

  const title = formData.get('title') as string;
  const body = formData.get('body') as string;

  const { error } = await supabase.from('posts').insert({
    title,
    body,
    user_id: user.id,
  });

  if (error) {
    return { error: error.message };
  }

  revalidatePath('/posts');
  return { success: true };
}
```

### Using Server Actions in Client Components

```typescript
'use client';

import { createPost } from './actions';

export function NewPostForm() {
  async function handleSubmit(formData: FormData) {
    const result = await createPost(formData);
    if (result.error) {
      alert(result.error);
    }
  }

  return (
    <form action={handleSubmit}>
      <input name="title" placeholder="Title" required />
      <textarea name="body" placeholder="Content" required />
      <button type="submit">Create Post</button>
    </form>
  );
}
```

## Auth UI Patterns

### Login Page

```typescript
// app/login/page.tsx
import { LoginForm } from './login-form';

export default function LoginPage() {
  return (
    <div>
      <h1>Sign In</h1>
      <LoginForm />
    </div>
  );
}
```

```typescript
// app/login/login-form.tsx
'use client';

import { createClient } from '@/lib/supabase/client';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const supabase = createClient();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      setError(error.message);
    } else {
      router.push('/dashboard');
      router.refresh(); // refresh Server Components
    }
  }

  async function handleOAuth() {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${location.origin}/auth/callback`,
      },
    });
  }

  return (
    <form onSubmit={handleLogin}>
      {error && <p>{error}</p>}
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Sign In</button>
      <button type="button" onClick={handleOAuth}>Sign in with Google</button>
    </form>
  );
}
```

### OAuth Callback Route

```typescript
// app/auth/callback/route.ts
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get('code');
  const next = searchParams.get('next') ?? '/dashboard';

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

## Sign Out

```typescript
// app/auth/signout/route.ts
import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const supabase = await createClient();
  await supabase.auth.signOut();

  return NextResponse.redirect(new URL('/login', request.url), {
    status: 302,
  });
}
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Using `getSession()` for server auth checks | JWT not validated -- attacker can forge | Use `getUser()` which validates with auth server |
| Missing middleware | Sessions expire, users randomly logged out | Add middleware that calls `getUser()` |
| Creating supabase client outside async context | `cookies()` needs request context | Always create client inside the handler function |
| Using server client in Client Component | `cookies()` not available in browser | Use `createBrowserClient` for Client Components |
| Not calling `router.refresh()` after auth change | Server Components show stale data | Call `router.refresh()` after sign in/out |
| Forgetting `redirectTo` in OAuth | Callback goes to wrong URL | Always set `redirectTo` to your callback route |
| Service role key in browser | Full database access exposed | Service role key in server-side code only |
| Not handling the `try/catch` in `setAll` | Server Component errors on cookie write | Wrap `setAll` in try/catch (middleware handles it) |
