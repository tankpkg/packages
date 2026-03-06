---
name: "@tank/web-analytics-consent"
description: "Privacy-compliant web analytics and cookie consent implementation. Covers
tool selection (PostHog, GA4, Plausible, Umami, Clarity), cookie consent banners
(vanilla-cookieconsent v3, GDPR/CCPA compliance), consent-gated script loading,
Google Consent Mode v2, funnel analysis, session recordings, heatmaps, Next.js
integration patterns, and opt-in/opt-out architecture with free-tier pricing
comparison.\n\nTrigger phrases: \"analytics\", \"cookie consent\", \"GDPR\",
\"cookie banner\", \"PostHog\", \"Google Analytics\", \"GA4\", \"Plausible\",
\"Umami\", \"Microsoft Clarity\", \"session recording\", \"heatmap\",
\"consent mode\", \"privacy compliance\", \"CCPA\", \"cookieconsent\",
\"funnel analysis\", \"event tracking\", \"opt-in\", \"opt-out\""
triggers:
- analytics
- cookie consent
- GDPR
- cookie banner
- PostHog
- Google Analytics
- GA4
- Plausible
- Umami
- Microsoft Clarity
- session recording
- heatmap
- consent mode
- privacy compliance
- CCPA
- cookieconsent
- funnel analysis
- event tracking
- opt-in
- opt-out
- vanilla-cookieconsent
- consent-gated
- ePrivacy
---

# Core Philosophy

- Consent-first architecture: no analytics script loads until the user makes a choice.
- Two valid paths: cookieless tools need no banner; cookie-based tools need full opt-in.
- Privacy is a product feature, not a legal checkbox.
- Free tiers are generous enough for most startups; know the exact numbers before choosing.

# Consent Architecture Decision Tree

```
Does the tool set cookies or access device storage?
|-- NO (Plausible, Fathom, Umami, Vercel Analytics)
|   --> No consent banner needed
|   --> Add to privacy policy, honor opt-out requests
|   --> Load script unconditionally
|
|-- YES (GA4, PostHog default, Clarity, Hotjar)
    --> Consent banner REQUIRED before loading
    --> Default all consent signals to 'denied'
    --> Load scripts ONLY after explicit opt-in
    |
    |-- Using Google advertising products?
    |   --> Implement Consent Mode v2 (mandatory since March 2024)
    |   --> Include ad_user_data and ad_personalization signals
    |
    |-- Using session recordings?
        --> ALWAYS requires explicit consent regardless of tool
```

# Tool Selection Quick Reference

| Tool | Type | Cookies | Free Tier | Banner Required |
| --- | --- | --- | --- | --- |
| Plausible | Traffic analytics | None | No free tier (paid hosted) | No |
| Umami | Traffic analytics | None | Self-host free | No |
| Vercel Analytics | Traffic analytics | None | Free (Vercel projects) | No |
| PostHog | Product analytics | Optional | 1M events, 5K recordings/mo | Depends on config |
| GA4 | Marketing analytics | Yes | Free (with limits) | Yes |
| Clarity | Session replay | Yes | Free unlimited | Yes |

# Workflow

1. **Choose analytics path**: Cookieless-only or cookie-based. See `references/tool-selection.md`.
2. **If cookie-based**: Set up consent banner with vanilla-cookieconsent v3. See `references/vanilla-cookieconsent.md`.
3. **Configure consent architecture**: Map consent categories to scripts. See `references/consent-architecture.md`.
4. **If using Google products**: Implement Consent Mode v2. See `references/google-consent-mode.md`.
5. **Integrate analytics tool**: PostHog with consent gating. See `references/posthog-integration.md`.
6. **Set up advanced features**: Funnels, session recordings, heatmaps. See `references/funnels-sessions-heatmaps.md`.

# Common Patterns

## Cookieless Path (No Banner Needed)

```tsx
// app/layout.tsx — Plausible loads unconditionally
export default function RootLayout({ children }) {
  return (
    <html>
      <head>
        <script defer data-domain="yourdomain.com"
          src="https://plausible.io/js/script.js" />
      </head>
      <body>{children}</body>
    </html>
  );
}
```

## Cookie-Based Path (Banner Required)

```tsx
// instrumentation-client.ts — PostHog waits for consent
import posthog from 'posthog-js';

posthog.init('phc_YOUR_KEY', {
  api_host: '/ingest',             // reverse proxy
  persistence: 'memory',           // no cookies until consent
  disable_session_recording: true, // no recording until consent
  loaded: (ph) => ph.opt_out_capturing(),
});
```

```tsx
// components/CookieConsent.tsx — consent gates PostHog
'use client';
import { useEffect } from 'react';
import posthog from 'posthog-js';
import * as CookieConsent from 'vanilla-cookieconsent';
import 'vanilla-cookieconsent/dist/cookieconsent.css';

export function CookieBanner() {
  useEffect(() => {
    CookieConsent.run({
      categories: {
        necessary: { enabled: true, readOnly: true },
        analytics: {
          autoClear: { cookies: [{ name: /^ph_/ }] },
        },
      },
      onConsent: () => {
        if (CookieConsent.acceptedCategory('analytics')) {
          posthog.opt_in_capturing();
        }
      },
      onChange: ({ changedCategories }) => {
        if (changedCategories.includes('analytics')) {
          CookieConsent.acceptedCategory('analytics')
            ? posthog.opt_in_capturing()
            : posthog.opt_out_capturing();
        }
      },
      language: { default: 'en', translations: { en: { /* ... */ } } },
    });
  }, []);
  return null;
}
```

# Anti-Patterns

| Anti-Pattern | Replace With |
| --- | --- |
| Loading GA4 before consent in EU | Block with Consent Mode defaults set to 'denied' |
| Pre-checking analytics toggle | All non-necessary categories disabled by default |
| No "Reject All" button | Equal-weight Accept All / Reject All buttons |
| Using PostHog with cookies but no banner | Use `persistence: 'memory'` or add consent banner |
| Ignoring ad_user_data / ad_personalization signals | Include all four Consent Mode v2 signals |
| Session recordings without consent | Always gate recordings behind explicit opt-in |
| Cookie wall (blocking site until consent) | Site must be accessible without giving consent |

# Quality Checklist

- Consent defaults to denied for all non-necessary categories.
- "Reject All" button has equal visual weight to "Accept All".
- Scripts with cookies only load after explicit opt-in.
- Consent withdrawal mechanism exists (preferences widget/link).
- Google Consent Mode v2 defaults set before GTM/GA4 loads.
- Session recordings gated behind consent.
- Privacy policy linked from consent banner.
- Cookie descriptions in plain language.
- Consent stored with timestamp and ID for audit trail.

# Reference Files

- `references/tool-selection.md` — Analytics tool comparison, pricing, and selection guide
- `references/consent-architecture.md` — GDPR/CCPA legal framework and consent patterns
- `references/vanilla-cookieconsent.md` — Cookie consent banner setup and configuration
- `references/posthog-integration.md` — PostHog with Next.js and consent gating
- `references/google-consent-mode.md` — Consent Mode v2, GA4, GTM, and Clarity
- `references/funnels-sessions-heatmaps.md` — Event taxonomy, funnels, recordings, and heatmaps
