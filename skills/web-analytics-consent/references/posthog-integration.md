# PostHog Integration

Sources: PostHog JS SDK (posthog-js), PostHog Node SDK (posthog-node), PostHog documentation (posthog.com/docs), Next.js documentation (nextjs.org/docs)

---

## Next.js Integration via instrumentation-client.ts

The modern pattern for initializing PostHog in Next.js App Router projects uses `instrumentation-client.ts`. This file runs once on the client before any React component mounts, replacing the older `<PHProvider>` wrapper pattern.

Enable the instrumentation hook in `next.config.js`:

```js
const nextConfig = {
  experimental: { instrumentationHook: true },
}
module.exports = nextConfig
```

Create `instrumentation-client.ts` at the project root:

```ts
// instrumentation-client.ts
import posthog from 'posthog-js'

export function register() {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: '/ingest',
    ui_host: 'https://us.posthog.com',
    capture_pageview: 'history_change',
    capture_pageleave: true,
    persistence: 'localStorage+cookie',
  })
}
```

After initialization, import and use `posthog` directly from `posthog-js` in any client component. React hooks from `posthog-js/react` (such as `useFeatureFlagEnabled`) work automatically without additional provider setup.

---

## posthog.init() Key Options

| Option | Type | Default | Purpose |
|--------|------|---------|---------|
| `api_host` | string | `'https://us.posthog.com'` | Ingestion endpoint; set to `/ingest` with reverse proxy |
| `ui_host` | string | — | PostHog UI host; required when `api_host` is a proxy path |
| `persistence` | string | `'localStorage+cookie'` | Storage mode for identity and flags |
| `capture_pageview` | boolean \| `'history_change'` | `true` | Use `'history_change'` for SPA routing |
| `autocapture` | boolean | `true` | Capture clicks, inputs, form submissions automatically |
| `disable_session_recording` | boolean | `false` | Prevent session recordings from starting |
| `maskAllInputs` | boolean | `true` | Mask all input field values in recordings |
| `maskTextSelector` | string | — | CSS selector for text nodes to mask |
| `opt_out_capturing_by_default` | boolean | `false` | Start opted out; no data sent until `opt_in_capturing()` called |
| `loaded` | function | — | Callback fired after initialization with the PostHog instance |

---

## Persistence Modes

PostHog stores identity, feature flags, and session data locally. The `persistence` option controls where:

**`'localStorage+cookie'`** (default) — Writes to both `localStorage` and a cookie. Most durable identity across sessions and subdomains. Requires consent under GDPR.

**`'localStorage'`** — Writes only to `localStorage`. No cross-subdomain identity. Requires consent under GDPR.

**`'cookie'`** — Writes only to a cookie. Enables cross-subdomain identity. Requires consent.

**`'memory'`** — Stores state in JavaScript memory only. Lost on page reload. No data written to the user's device. The only mode that does not require prior consent under a strict GDPR interpretation.

Use `'memory'` as the initial mode before consent is granted, then switch to a durable mode after the user accepts.

---

## Consent-Gated Initialization Pattern

Initialize PostHog immediately in `'memory'` mode with capturing disabled, then upgrade persistence and enable capturing after the user grants consent. This avoids deferring initialization while ensuring no persistent data is written before consent.

```ts
// instrumentation-client.ts
import posthog from 'posthog-js'

export function register() {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: '/ingest',
    ui_host: 'https://us.posthog.com',
    capture_pageview: false,
    persistence: 'memory',
    opt_out_capturing_by_default: true,
    loaded: () => {
      const hasConsent = localStorage.getItem('analytics_consent') === 'granted'
      if (hasConsent) enableAnalytics()
    },
  })
}

export function enableAnalytics() {
  posthog.set_config({ persistence: 'localStorage+cookie' })
  posthog.opt_in_capturing()
  posthog.capture('$pageview')
}

export function disableAnalytics() {
  posthog.opt_out_capturing()
  posthog.set_config({ persistence: 'memory' })
  posthog.reset()
}
```

---

## opt_in_capturing() and opt_out_capturing()

**`posthog.opt_in_capturing(options?)`** — Marks the user as opted in. Resumes event capture and session recording. Optional `options`:
- `capture_event_name`: event to fire on opt-in (default: `'$opt_in'`)
- `enable_persistence`: whether to re-enable persistence (default: `true`)

**`posthog.opt_out_capturing()`** — Stops all event capture immediately. Clears queued events. Does not delete previously sent data from PostHog servers.

**`posthog.has_opted_in_capturing()`** — Returns `true` if the user has explicitly opted in.

**`posthog.has_opted_out_capturing()`** — Returns `true` if the user has explicitly opted out.

**`posthog.clear_opt_in_out_capturing()`** — Removes the opt-in/opt-out flag. PostHog reverts to the default behavior defined by `opt_out_capturing_by_default`.

**`posthog.reset()`** — Generates a new anonymous distinct ID and clears the identified user. Call this when consent is revoked to sever the link to the previous identity.

---

## Reverse Proxy for Ad-Blocker Bypass

Ad blockers commonly block requests to `us.posthog.com`. Route PostHog traffic through your own domain using Next.js rewrites:

```js
// next.config.js
async rewrites() {
  return [
    {
      source: '/ingest/static/:path*',
      destination: 'https://us-assets.posthog.com/static/:path*',
    },
    {
      source: '/ingest/:path*',
      destination: 'https://us.posthog.com/:path*',
    },
  ]
},
```

Set `api_host: '/ingest'` and `ui_host: 'https://us.posthog.com'` in `posthog.init()`. The `/ingest/static/` rewrite serves the PostHog JS bundle from your domain, preventing the script tag itself from being blocked.

For EU region, replace `us.posthog.com` with `eu.posthog.com` and `us-assets.posthog.com` with `eu-assets.posthog.com`.

---

## EU Region Setup

PostHog operates a Frankfurt-based EU cloud for data residency compliance. Use the EU ingestion endpoint:

```ts
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: '/ingest',          // via reverse proxy pointing to eu.posthog.com
  ui_host: 'https://eu.posthog.com',
})
```

The EU cloud API key is distinct from the US cloud key. Create a separate project in the EU region.

---

## Privacy Masking Controls

**`maskAllInputs`** (default: `true`) — Replaces all input field values with asterisks in recordings. Disable only after reviewing all inputs for sensitive data.

**`maskTextSelector`** — CSS selector targeting text nodes to mask. Use `"*"` to mask all text content, leaving only structural layout visible in recordings.

**`ph-no-capture` CSS class** — Add to any HTML element to exclude it and its children from recordings entirely. No configuration required:

```html
<div class="ph-no-capture">
  <input type="text" placeholder="Sensitive field" />
</div>
```

**`maskInputFn`** — Custom function to transform input values before capture. Receives the input element and returns the string to record:

```ts
posthog.init(key, {
  session_recording: {
    maskInputFn: (text, element) => {
      if (element?.dataset.sensitive === 'true') return '*'.repeat(text.length)
      return text
    },
  },
})
```

**`maskTextFn`** — Custom function to transform text node content before capture. Useful for masking patterns like email addresses across all text nodes:

```ts
session_recording: {
  maskTextFn: (text) =>
    text.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[email]'),
},
```

**Remote masking configuration** (since March 2025) — Configure masking rules from the PostHog dashboard without redeploying. Remote configuration overrides local `maskTextSelector` settings.

---

## Session Recording Controls

**`disable_session_recording: true`** — Disable recordings at initialization. Enable selectively after consent with `posthog.startSessionRecording()`.

**`sampleRate`** — Record only a fraction of sessions. Set between `0` (none) and `1` (all):

```ts
session_recording: { sampleRate: 0.2 } // Record 20% of sessions
```

**URL triggers** — Configure from the PostHog dashboard under Session Replay > Settings > URL Triggers. Recordings start when the user navigates to a matching URL and stop when they leave.

**Exception triggers** — Configure recordings to start automatically when a JavaScript exception occurs. Useful for capturing error context without recording all sessions. Configure from the PostHog dashboard.

**Minimum duration filter** — Discard sessions shorter than a configured threshold. Configure from the PostHog dashboard.

---

## Integration with vanilla-cookieconsent

Connect PostHog opt-in/opt-out to vanilla-cookieconsent's `onConsent` and `onChange` callbacks:

```ts
// instrumentation-client.ts
import posthog from 'posthog-js'
import * as CookieConsent from 'vanilla-cookieconsent'

export function register() {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: '/ingest',
    ui_host: 'https://us.posthog.com',
    persistence: 'memory',
    opt_out_capturing_by_default: true,
    capture_pageview: false,
  })

  CookieConsent.run({
    // ... cookieconsent configuration in vanilla-cookieconsent.md ...
    onConsent: () => syncPostHogConsent(),
    onChange: () => syncPostHogConsent(),
  })
}

function syncPostHogConsent() {
  if (CookieConsent.acceptedCategory('analytics')) {
    posthog.set_config({ persistence: 'localStorage+cookie' })
    posthog.opt_in_capturing()
    posthog.capture('$pageview')
  } else {
    posthog.opt_out_capturing()
    posthog.set_config({ persistence: 'memory' })
    posthog.reset()
  }
}
```

Use `CookieConsent.acceptedCategory('analytics')` to check consent status rather than inspecting the cookie object directly. Both `onConsent` (first decision) and `onChange` (preference update) must call the same sync function.

---

## PostHog identify() and Consent Implications

`posthog.identify(userId, properties?)` links the anonymous PostHog distinct ID to a known user identity. This constitutes processing of personal data under GDPR. Call `identify()` only after analytics consent is granted:

```ts
import posthog from 'posthog-js'

export function onUserLogin(user: { id: string; email: string; plan: string }) {
  if (posthog.has_opted_in_capturing()) {
    posthog.identify(user.id, { email: user.email, plan: user.plan })
  }
}
```

When consent is revoked, call `posthog.reset()` to generate a new anonymous distinct ID and sever the link to the identified profile. `reset()` does not delete data already sent to PostHog servers.

---

## Server-Side Analytics with PostHog Node SDK

Install the Node SDK separately:

```bash
npm install posthog-node
```

Create a singleton client to avoid multiple instantiations:

```ts
// lib/posthog-server.ts
import { PostHog } from 'posthog-node'

let client: PostHog | null = null

export function getPostHogClient(): PostHog {
  if (!client) {
    client = new PostHog(process.env.POSTHOG_KEY!, {
      host: 'https://us.posthog.com', // or 'https://eu.posthog.com'
    })
  }
  return client
}
```

Capture events from Server Actions or API routes. In serverless environments, call `flushAsync()` before the function returns:

```ts
// app/api/webhook/route.ts
import { getPostHogClient } from '@/lib/posthog-server'
import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const ph = getPostHogClient()
  ph.capture({
    distinctId: 'server',
    event: 'webhook_received',
    properties: { source: 'stripe' },
  })
  await ph.flushAsync() // Required in serverless; process may terminate before auto-flush
  return NextResponse.json({ received: true })
}
```

Use the same `distinctId` as client-side events to merge server and client activity into a single user timeline. Server-side events bypass ad blockers entirely because requests originate from your server infrastructure.
