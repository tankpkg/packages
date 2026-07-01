# Edge Functions

Sources: Supabase Edge Functions Documentation (2024-2026), Deno Runtime Documentation, Supabase Edge Runtime GitHub (supabase/edge-runtime), Supabase CLI Reference (functions commands)

Covers: Deno runtime basics, Edge Function project structure, environment variables and secrets, CORS handling, invoking from client, connecting to the database, common patterns (webhooks, scheduled tasks), testing locally, and deployment.

## Edge Functions Overview

Edge Functions are server-side TypeScript functions that run on the Supabase Edge Runtime (Deno-compatible). They execute globally at the edge for low latency.

### When to Use Edge Functions

| Use Case | Fit |
|----------|-----|
| Webhook receiver (Stripe, GitHub) | Ideal |
| Custom API endpoint with complex logic | Ideal |
| Third-party API orchestration | Ideal |
| Sending emails / notifications | Ideal |
| OG image generation | Good |
| AI/LLM API calls | Good |
| Simple CRUD operations | Use supabase-js + RLS instead |
| Long-running jobs (>60s) | Use background tasks or external worker |

## Project Structure

```
supabase/
  functions/
    _shared/            # Shared modules (imported by functions)
      cors.ts
      supabase-client.ts
    my-function/
      index.ts          # Entry point (required)
    another-function/
      index.ts
```

### Basic Function

```typescript
// supabase/functions/hello-world/index.ts
import "jsr:@supabase/functions-js/edge-runtime.d.ts";

Deno.serve(async (req: Request) => {
  const { name } = await req.json();

  return new Response(
    JSON.stringify({ message: `Hello, ${name}!` }),
    {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    }
  );
});
```

### Shared CORS Handler

```typescript
// supabase/functions/_shared/cors.ts
export const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers':
    'authorization, x-client-info, apikey, content-type',
};

export function handleCors(req: Request): Response | null {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }
  return null;
}
```

### Function with CORS

```typescript
// supabase/functions/api-handler/index.ts
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { corsHeaders, handleCors } from "../_shared/cors.ts";

Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  const corsResponse = handleCors(req);
  if (corsResponse) return corsResponse;

  try {
    const data = await processRequest(req);
    return new Response(JSON.stringify(data), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    });
  }
});
```

## Environment Variables and Secrets

### Built-in Variables

| Variable | Content |
|----------|---------|
| `SUPABASE_URL` | Project URL (auto-set) |
| `SUPABASE_ANON_KEY` | Public anon key (auto-set) |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (auto-set) |
| `SUPABASE_DB_URL` | Direct database connection string (auto-set) |

### Custom Secrets

```bash
# Set a secret
supabase secrets set STRIPE_SECRET_KEY=sk_live_xxx

# Set multiple secrets
supabase secrets set RESEND_API_KEY=re_xxx OPENAI_KEY=sk-xxx

# List secrets (names only, not values)
supabase secrets list

# Unset a secret
supabase secrets unset STRIPE_SECRET_KEY
```

### Accessing Secrets in Code

```typescript
const stripeKey = Deno.env.get('STRIPE_SECRET_KEY');
if (!stripeKey) {
  throw new Error('STRIPE_SECRET_KEY not configured');
}
```

### Local Development Secrets

Create `.env.local` in `supabase/functions/` for local secrets:

```bash
# supabase/functions/.env.local
STRIPE_SECRET_KEY=sk_test_xxx
RESEND_API_KEY=re_test_xxx
```

This file is gitignored by default.

## Connecting to Database

### Using supabase-js (Recommended)

```typescript
// supabase/functions/_shared/supabase-client.ts
import { createClient } from "jsr:@supabase/supabase-js@2";

export function createSupabaseClient(req: Request) {
  return createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_ANON_KEY')!,
    {
      global: {
        headers: {
          Authorization: req.headers.get('Authorization')!,
        },
      },
    }
  );
}

export function createSupabaseAdmin() {
  return createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );
}
```

Pass the user's `Authorization` header to `createClient` to execute queries with the user's RLS context. Use `createSupabaseAdmin` only for server-side operations that must bypass RLS.

### Direct Postgres Connection

```typescript
import postgres from "https://deno.land/x/postgresjs/mod.js";

const sql = postgres(Deno.env.get('SUPABASE_DB_URL')!, {
  // Use transaction pooler for Edge Functions
  prepare: false, // required for transaction pooling mode
});

const result = await sql`select * from posts where status = 'published'`;
```

Use the transaction pooler connection string (port 6543) for Edge Functions.

## Invoking from Client

### Standard Invocation

```typescript
const { data, error } = await supabase.functions.invoke('hello-world', {
  body: { name: 'World' },
});
```

### With Custom Headers

```typescript
const { data, error } = await supabase.functions.invoke('process-payment', {
  body: { amount: 2999, currency: 'usd' },
  headers: { 'x-custom-header': 'value' },
});
```

### Direct HTTP Invocation

```bash
curl -X POST \
  'https://<project-ref>.supabase.co/functions/v1/hello-world' \
  -H 'Authorization: Bearer <anon-key-or-user-jwt>' \
  -H 'Content-Type: application/json' \
  -d '{"name": "World"}'
```

## Common Patterns

### Stripe Webhook Handler

```typescript
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import Stripe from "https://esm.sh/stripe@14?target=deno";

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY')!, {
  apiVersion: '2024-04-10',
});

const webhookSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET')!;

Deno.serve(async (req: Request) => {
  const signature = req.headers.get('stripe-signature')!;
  const body = await req.text();

  let event: Stripe.Event;
  try {
    event = await stripe.webhooks.constructEventAsync(
      body, signature, webhookSecret
    );
  } catch (err) {
    return new Response(`Webhook Error: ${err.message}`, { status: 400 });
  }

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object;
      // Update subscription in database
      const supabase = createSupabaseAdmin();
      await supabase
        .from('subscriptions')
        .upsert({
          user_id: session.client_reference_id,
          stripe_customer_id: session.customer,
          status: 'active',
        });
      break;
    }
    case 'customer.subscription.deleted': {
      const subscription = event.data.object;
      const supabase = createSupabaseAdmin();
      await supabase
        .from('subscriptions')
        .update({ status: 'cancelled' })
        .eq('stripe_customer_id', subscription.customer);
      break;
    }
  }

  return new Response(JSON.stringify({ received: true }), { status: 200 });
});
```

### Sending Email with Resend

```typescript
import "jsr:@supabase/functions-js/edge-runtime.d.ts";

Deno.serve(async (req: Request) => {
  const { to, subject, html } = await req.json();

  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${Deno.env.get('RESEND_API_KEY')}`,
    },
    body: JSON.stringify({
      from: 'noreply@yourdomain.com',
      to,
      subject,
      html,
    }),
  });

  const data = await res.json();
  return new Response(JSON.stringify(data), {
    headers: { 'Content-Type': 'application/json' },
    status: res.ok ? 200 : 500,
  });
});
```

### Background Tasks

For operations that may exceed the request timeout:

```typescript
import "jsr:@supabase/functions-js/edge-runtime.d.ts";

Deno.serve(async (req: Request) => {
  // Return immediately
  EdgeRuntime.waitUntil(processInBackground(req));

  return new Response(JSON.stringify({ status: 'processing' }), {
    headers: { 'Content-Type': 'application/json' },
  });
});

async function processInBackground(req: Request) {
  // Long-running work happens here
  // Runs after the response is sent
}
```

## Local Development

```bash
# Start local Supabase (includes Edge Runtime)
supabase start

# Serve functions locally (hot reload)
supabase functions serve

# Serve a specific function
supabase functions serve hello-world

# Serve with custom env file
supabase functions serve --env-file supabase/functions/.env.local

# Test locally
curl -X POST http://localhost:54321/functions/v1/hello-world \
  -H 'Authorization: Bearer <local-anon-key>' \
  -H 'Content-Type: application/json' \
  -d '{"name": "test"}'
```

The local anon key is printed when `supabase start` completes.

## Deployment

```bash
# Deploy all functions
supabase functions deploy

# Deploy a specific function
supabase functions deploy hello-world

# Deploy with no JWT verification (public endpoint)
supabase functions deploy hello-world --no-verify-jwt
```

### Deployment via GitHub Actions

```yaml
# .github/workflows/deploy-functions.yml
name: Deploy Edge Functions
on:
  push:
    branches: [main]
    paths: ['supabase/functions/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
      - run: supabase functions deploy --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

## Limitations

| Constraint | Limit |
|-----------|-------|
| Request timeout | 60 seconds (150s on Pro) |
| Memory | 256MB (512MB on Pro) |
| Payload size | 6MB request, 6MB response |
| Deploy size | 20MB per function (after bundling) |
| Cold starts | Possible -- design for idempotent, short-lived operations |
| WebSocket | Not supported (use Realtime instead) |
| File system | Read-only (use Storage for file persistence) |
