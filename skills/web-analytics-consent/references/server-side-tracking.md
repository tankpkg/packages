# Server-Side Tracking and Ad Blocker Resilience

Sources: PostHog documentation (posthog.com/docs), Google Analytics Measurement Protocol v2 docs, Plausible Analytics API docs, Vercel Edge Middleware docs, Cloudflare Workers documentation, Next.js rewrites documentation.

---

## The Ad Blocker Problem

Roughly 30-40% of technical users block analytics. Developer-focused SaaS products can exceed 50%. This creates systematic data loss that skews funnels, attribution, and product decisions.

| Analytics Tool | No Proxy | With Reverse Proxy | Notes |
|---|---|---|---|
| Google Analytics 4 | Very high (40-60%) | Medium (15-25%) | Brave blocks aggressively |
| PostHog Cloud | High (30-45%) | Low (5-10%) | Proxy eliminates most extension blocking |
| Plausible Cloud | Low (10-20%) | Very low (2-5%) | Not on most filter lists yet |
| Umami self-hosted | Very low (2-8%) | Near zero | Custom domain, no known fingerprint |

**Three blocking layers:**

1. **DNS-level (Pi-hole, NextDNS)** — Blocks entire domains before any HTTP request. A reverse proxy on your own domain bypasses this completely.
2. **Browser extensions (uBlock Origin, AdBlock Plus)** — Match URLs against filter lists. A proxy path on your own domain avoids these patterns until the path gets added to lists — which happens if you use obvious names.
3. **Browser built-in (Brave Shields, Safari ITP)** — Brave blocks known tracker domains. Safari ITP caps JS-set cookies to 7 days. Server-set cookies are not affected.

**Combined data loss:** A technical SaaS with no mitigation loses 35-55% of events. With a reverse proxy: 10-20%. With full server-side for critical events: 2-5%.

---

## Reverse Proxy Pattern

Route analytics requests through your own domain so they are indistinguishable from your own API calls.

**Critical naming rule:** Never use `/analytics`, `/posthog`, `/tracking`, `/stats`, or `/metrics` as proxy paths — these are on filter lists. Use opaque paths like `/ingest`, `/relay`, or `/api/ph`.

### Next.js rewrites (next.config.js)

```js
const nextConfig = {
  async rewrites() {
    return [
      // PostHog US region
      {
        source: '/ingest/static/:path*',
        destination: 'https://us-assets.i.posthog.com/static/:path*',
      },
      {
        source: '/ingest/:path*',
        destination: 'https://us.i.posthog.com/:path*',
      },
      // EU region: swap destination to eu-assets.i.posthog.com / eu.i.posthog.com
    ]
  },
  skipTrailingSlashRedirect: true, // required — prevents host header stripping
}
module.exports = nextConfig
```

PostHog client init pointing at the proxy:

```ts
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: '/ingest',
  ui_host: 'https://us.posthog.com',
})
```

### Nginx reverse proxy

```nginx
location /ingest/ {
    proxy_pass https://us.i.posthog.com/;
    proxy_ssl_server_name on;
    proxy_set_header Host us.i.posthog.com;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    rewrite ^/ingest/(.*) /$1 break;
}
```

### Cloudflare Workers proxy

```ts
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url)
    if (!url.pathname.startsWith('/ingest')) return new Response('Not found', { status: 404 })
    const targetPath = url.pathname.replace('/ingest', '')
    const proxied = new Request(`https://us.i.posthog.com${targetPath}${url.search}`, {
      method: request.method,
      headers: { ...Object.fromEntries(request.headers), host: 'us.i.posthog.com' },
      body: request.body,
    })
    return fetch(proxied)
  },
}
```

### Vercel rewrites (vercel.json)

```json
{
  "rewrites": [
    { "source": "/ingest/static/:path*", "destination": "https://us-assets.i.posthog.com/static/:path*" },
    { "source": "/ingest/:path*", "destination": "https://us.i.posthog.com/:path*" }
  ]
}
```

Vercel rewrites run at the CDN edge and cannot add server-side secrets. For tools requiring API keys in headers, use a Next.js API route instead.

---

## Server-Side SDKs

Use server-side tracking when the event involves payments or subscriptions, the user may have JavaScript disabled, or the event originates from a backend process (webhook, cron, API call).

### PostHog Node.js SDK

**Singleton pattern** — create once, reuse across requests:

```ts
// lib/posthog-server.ts
import { PostHog } from 'posthog-node'

let client: PostHog | null = null

export function getPostHogClient(): PostHog {
  if (!client) {
    client = new PostHog(process.env.POSTHOG_KEY!, {
      host: 'https://us.i.posthog.com',
      flushAt: 20,
      flushInterval: 10000,
    })
  }
  return client
}
```

**Core operations:**

```ts
const ph = getPostHogClient()

ph.capture({ distinctId: userId, event: 'payment_completed',
  properties: { plan: 'pro', amount_cents: 2900, currency: 'usd' } })

ph.identify({ distinctId: userId,
  properties: { email: user.email, name: user.name } })

ph.groupIdentify({ groupType: 'company', groupKey: orgId,
  properties: { name: org.name, plan: org.plan } })

const flagEnabled = await ph.isFeatureEnabled('new-dashboard', userId)
```

**Serverless shutdown** — flush before the function exits:

```ts
export async function POST(request: Request) {
  const ph = getPostHogClient()
  ph.capture({ distinctId: userId, event: 'api_called', properties: {} })
  await ph.shutdown() // flush remaining events before cold function exits
  return Response.json({ ok: true })
}
```

### GA4 Measurement Protocol

```ts
export async function sendGA4Event(clientId: string, events: Array<{ name: string; params?: Record<string, unknown> }>) {
  const url = new URL('https://www.google-analytics.com/mp/collect')
  url.searchParams.set('api_secret', process.env.GA4_API_SECRET!)
  url.searchParams.set('measurement_id', process.env.NEXT_PUBLIC_GA4_ID!)

  await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: clientId, events: events.slice(0, 25) }),
    // GA4 limits: 25 events/request, 25 params/event, param values max 100 chars
  })
}
```

Use `/debug/mp/collect` during development — it returns validation errors.

### Plausible server-side

```ts
export async function trackPlausibleEvent(
  request: Request, eventName: string, url: string, props?: Record<string, string>
) {
  await fetch('https://plausible.io/api/event', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': request.headers.get('user-agent') ?? '',
      'X-Forwarded-For': request.headers.get('x-forwarded-for')?.split(',')[0].trim() ?? '',
    },
    body: JSON.stringify({ domain: process.env.PLAUSIBLE_DOMAIN!, name: eventName, url, props }),
  })
}
```

Pass the original `User-Agent` and `X-Forwarded-For` from the incoming request so Plausible can attribute geo and browser. Plausible hashes and discards the IP immediately.

---

## Hybrid Architecture

```
Browser                        Your Server                  Analytics Vendor
  |                                 |                              |
  |-- page view (PostHog JS) -----> | /ingest proxy ------------>  |
  |-- button click (PostHog JS) --> | /ingest proxy ------------>  |
  |-- session recording ----------> | /ingest proxy ------------>  |
  |                                 |                              |
  |-- POST /api/checkout ---------> |                              |
  |                                 |-- ph.capture(payment) -----> |
  |                                 |<-- Stripe webhook ---------- |
  |                                 |-- ph.capture(renewal) -----> |
```

**Event routing decision table:**

| Event Type | Client-side | Server-side | Reason |
|---|---|---|---|
| Page view, scroll depth | Yes | Optional | Browser has full URL and referrer |
| UI click / interaction | Yes | No | Only meaningful in browser context |
| Session recording | Yes | No | Requires DOM access |
| Payment completed | No | Yes | Must not be blocked or lost |
| Subscription created/cancelled | No | Yes | Stripe webhook is authoritative |
| API usage / quota events | No | Yes | No browser involved |
| Feature flag evaluated (SSR) | No | Yes | Flag evaluated before HTML sent |
| Signup completed | Yes | Yes | Duplicate for reliability |

---

## First-Party Cookies

Safari ITP caps JavaScript-set cookies to 7 days when the script domain differs from the page domain. Cookies set by your server via `Set-Cookie` response headers are treated as genuine first-party cookies and are not capped.

| Approach | Safari ITP | XSS Protection | Ad Blocker Resilience | Persistence |
|---|---|---|---|---|
| JS-set (document.cookie) | 7-day cap | None | Blocked if script blocked | Up to 7 days (Safari) |
| Server-set HttpOnly | Not capped | Full | Not affected | Up to 400 days |
| localStorage | 7-day cap (Safari) | None | Cleared if script blocked | Indefinite |

**Next.js middleware — persistent first-party session cookie:**

```ts
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'
import { randomUUID } from 'crypto'

const SESSION_COOKIE = '__ph_sid' // avoid 'analytics' or 'tracking' in the name
const ONE_YEAR = 60 * 60 * 24 * 365

export function middleware(request: NextRequest): NextResponse {
  const response = NextResponse.next()
  if (!request.cookies.has(SESSION_COOKIE)) {
    response.cookies.set(SESSION_COOKIE, randomUUID(), {
      httpOnly: true, sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      maxAge: ONE_YEAR, path: '/',
    })
  }
  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
```

---

## Edge and Middleware Tracking

Track page views at the edge before the page renders. This captures visits even when JavaScript is disabled or blocked.

**Vercel `after()` for non-blocking analytics (Next.js 15+):**

```ts
// app/api/checkout/route.ts
import { after } from 'next/server'

export async function POST(request: Request): Promise<Response> {
  const result = await processCheckout(await request.json())

  after(async () => {
    const ph = getPostHogClient()
    ph.capture({ distinctId: result.userId, event: 'checkout_completed',
      properties: { plan: result.plan, amount: result.amount } })
    await ph.shutdown()
  })

  return Response.json({ success: true, orderId: result.orderId })
}
```

**Cloudflare Workers `waitUntil`:**

```ts
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const response = await handleRequest(request, env)
    ctx.waitUntil(trackEvent(env, { event: 'request_handled', path: new URL(request.url).pathname }))
    return response
  },
}
```

---

## Performance Patterns

Never await analytics calls in the critical response path.

```ts
// Correct — fire and forget
ph.capture({ distinctId: userId, event: 'action_taken', properties: {} })
return Response.json({ ok: true })

// Wrong — adds analytics latency to every user response
await ph.capture({ distinctId: userId, event: 'action_taken', properties: {} })
return Response.json({ ok: true })
```

Tune PostHog SDK batching to match your traffic:

```ts
new PostHog(key, {
  flushAt: 20,          // send when 20 events queued
  flushInterval: 10000, // or every 10 seconds, whichever comes first
})
```

---

## Self-Hosting Quick Reference

| Tool | License | Min RAM | Database | Complexity |
|---|---|---|---|---|
| PostHog | MIT (core) | 4 GB | ClickHouse + PostgreSQL | High |
| Plausible | AGPL | 512 MB | ClickHouse | Low |
| Umami | MIT | 256 MB | PostgreSQL or MySQL | Very low |
| Matomo | GPL | 512 MB | MySQL | Medium |

```bash
# Plausible
docker run -d -e BASE_URL=https://analytics.yourdomain.com \
  -e SECRET_KEY_BASE=$(openssl rand -hex 64) -p 8000:8000 \
  ghcr.io/plausible/community-edition:v2

# Umami
docker run -d -e DATABASE_URL=postgresql://user:pass@host/umami \
  -e APP_SECRET=$(openssl rand -hex 32) -p 3000:3000 \
  ghcr.io/umami-software/umami:postgresql-latest
```

| Situation | Recommendation |
|---|---|
| Early stage, moving fast | Cloud (PostHog free tier, Plausible) |
| GDPR strict, no third-party transfers | Self-host Plausible or Umami |
| Need feature flags + replays + analytics | PostHog cloud or self-hosted |
| High event volume (>1M events/month) | Self-host to control costs |
| Air-gapped or regulated environment | Self-host |

---

## Data Accuracy Comparison

| Architecture | Typical Accuracy | Complexity |
|---|---|---|
| Client-side only, no proxy | 55-70% | Low |
| Client-side + reverse proxy | 75-85% | Low-medium |
| Server-side only | 95-99% | Medium |
| Hybrid (proxy + server-side critical events) | 90-98% | Medium-high |
| Self-hosted + hybrid | 97-99% | High |

**Recommended architecture by stage:**

| Stage | Architecture |
|---|---|
| Startup (0-10k users) | PostHog cloud + Next.js rewrites proxy |
| Growth (10k-100k users) | PostHog cloud + proxy + server-side for payments |
| Scale (100k+ users) | Self-hosted PostHog or Plausible + full hybrid |
| Enterprise | Self-hosted + server-side primary + client-side supplemental |

The proxy pattern alone recovers 15-25 percentage points of lost data with minimal engineering effort. Add server-side tracking for payment and subscription events regardless of stage — these are the events where data loss has direct revenue impact.
