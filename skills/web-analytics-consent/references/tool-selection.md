# Tool Selection and Pricing Guide

Sources: PostHog documentation (posthog.com/docs), Plausible Analytics documentation (plausible.io/docs), Umami documentation (umami.is/docs), Google Analytics 4 documentation (support.google.com/analytics), Microsoft Clarity documentation (clarity.microsoft.com), Vercel Web Analytics documentation (vercel.com/docs/analytics), Fathom Analytics documentation (usefathom.com/docs), IAPP Privacy Tech Vendor Report 2024, Cookieless Tracking State of the Industry 2024.

---

## Overview

Analytics tools divide into two categories: consent-required and consent-optional. The distinction determines your compliance architecture before you write a single line of code. Consent-required tools (GA4, Microsoft Clarity) set cookies or fingerprint users in ways that require explicit opt-in under GDPR and ePrivacy. Consent-optional tools (Plausible, Fathom, Umami, Vercel Web Analytics) use aggregated, cookieless measurement that regulators accept without a banner in most EU jurisdictions.

PostHog occupies a middle position: it can operate in a cookieless mode but defaults to cookie-based identification, requiring consent in that configuration.

Choose your tool before designing your consent flow. The tool determines whether you need a consent management platform at all.

---

## Tool Profiles

### PostHog

PostHog is a product analytics platform combining event tracking, session recording, feature flags, A/B testing, and a data warehouse in a single product. Use PostHog when you need behavioral analytics beyond pageviews: funnel analysis, cohort retention, feature adoption, and user-level event streams.

**Free tier (cloud):**
- 1,000,000 events per month
- 5,000 session recordings per month
- 1,000,000 feature flag requests per month
- 100,000 exception events per month
- 1,500 survey responses per month
- 1,000,000 data warehouse rows per month
- 1 project
- 1-year data retention

**Paid tier adds:**
- 6 projects
- 7-year data retention
- SSO and advanced permissions
- Priority support

**Data residency:** US (Virginia) and EU (Frankfurt). Select region at organization creation; cannot migrate afterward.

**Cookie usage:** Uses cookies by default for cross-session user identification. Supports `persistence: 'memory'` for session-only tracking without cookies, and `disable_persistence: true` for fully stateless operation. Cookieless mode loses cross-session user stitching.

**Self-hosting:** Open-source (MIT for core). Self-hosted via Docker Compose or Kubernetes. Self-hosted removes data residency concerns but requires infrastructure management. PostHog does not provide support for self-hosted free tier.

**Consent integration:** Requires consent banner when using default cookie persistence. Call `posthog.opt_out_capturing()` before initialization for users who decline. Supports `loaded` callback to delay initialization until consent is granted.

---

### Google Analytics 4

GA4 is Google's current analytics platform, replacing Universal Analytics. Use GA4 when you need integration with Google Ads, Search Console, or BigQuery export, or when stakeholders require Google's reporting ecosystem.

**Free tier:**
- Unlimited properties (with limits per account)
- 10,000,000 events per day per property
- Data sampling applies above 500,000 sessions in standard reports
- 14 months of data retention (default); configurable to 2 months or 14 months
- BigQuery export free up to 1,000,000 events per day (then $0.05 per 1,000 events)

**GA4 360 (paid):**
- Starts at approximately $50,000/year
- Unsampled reports
- Extended data retention (up to 50 months)
- Higher BigQuery export limits
- SLA guarantees

**Data residency:** Data processed on Google servers globally. EU data residency available only through GA4 360 with a Google Cloud region selection. Standard GA4 does not guarantee EU-only processing.

**Cookie usage:** Sets `_ga` and `_ga_*` cookies for user and session identification. These are persistent cookies (2-year default expiry) requiring explicit consent under GDPR and ePrivacy Directive. Cannot operate without cookies in standard configuration.

**Self-hosting:** Not available. GA4 is a Google-hosted SaaS product exclusively.

**Consent integration:** Requires a consent management platform. Supports Consent Mode v2, which sends cookieless pings when consent is declined, allowing Google to model conversions. Without Consent Mode v2, Google Ads conversion modeling degrades significantly for EU traffic.

---

### Plausible Analytics

Plausible is a lightweight, privacy-first analytics tool focused on pageviews, referrers, and basic event tracking. Use Plausible when you need simple traffic analytics without a consent banner and want a hosted solution with EU data residency.

**Free tier:** None for hosted cloud. Plausible does not offer a free plan.

**Paid cloud pricing:**
- $9/month for up to 10,000 pageviews
- $19/month for up to 100,000 pageviews
- $49/month for up to 1,000,000 pageviews
- $99/month for up to 10,000,000 pageviews
- Annual billing provides two months free

**Data residency:** EU only. Servers in Germany (Hetzner). No data transferred to US servers.

**Cookie usage:** No cookies. No persistent identifiers. Uses a daily rotating hash of IP address, user agent, and site domain to deduplicate pageviews within a 24-hour window. This approach is accepted by most EU data protection authorities as not constituting personal data processing.

**Self-hosting:** Open-source (AGPL). Self-hosted via Docker. Community-supported. Self-hosted version is fully featured but requires a server and maintenance.

**Consent integration:** No consent banner required for standard pageview tracking in most EU jurisdictions. Adding custom events that track user behavior may require reassessment. Verify with your DPA if tracking logged-in users or combining Plausible data with other identifiers.

---

### Umami

Umami is an open-source, self-hostable analytics platform with a focus on simplicity and privacy. Use Umami when you need a free, self-hosted alternative to Plausible with no cookies and full data ownership.

**Free tier (Umami Cloud):**
- 100,000 events per month
- Unlimited websites
- 90-day data retention

**Paid cloud pricing:**
- $9/month for 1,000,000 events
- $19/month for 10,000,000 events

**Data residency:** Self-hosted: your infrastructure, your choice. Umami Cloud: US-based (Vercel infrastructure). For EU data residency, self-host on EU infrastructure.

**Cookie usage:** No cookies. No personal data stored. Uses a session-based approach that does not persist across browser sessions. Compliant with GDPR without a consent banner.

**Self-hosting:** Open-source (MIT). Runs on Node.js with PostgreSQL or MySQL. Deploy on any VPS, Railway, Render, or Vercel. Self-hosted is free with no event limits beyond your infrastructure capacity.

**Consent integration:** No consent banner required. Umami explicitly states it does not collect personal data. Suitable for privacy-first deployments where you want zero compliance overhead.

---

### Microsoft Clarity

Microsoft Clarity is a free behavioral analytics tool providing session recordings, heatmaps, and rage-click detection. Use Clarity when you need qualitative UX insights (recordings, heatmaps) at no cost and are already using Microsoft or Azure products.

**Free tier:** Completely free. No paid tiers. No event or recording limits advertised (subject to fair use).

**Paid tier:** Does not exist. Clarity is entirely free.

**Data residency:** Data stored on Microsoft Azure servers. US-based processing. No EU-only data residency option. Microsoft processes data under its standard privacy terms.

**Cookie usage:** Sets cookies for session identification and recording. Requires consent banner under GDPR. Microsoft's own documentation recommends implementing a consent mechanism before loading Clarity.

**Self-hosting:** Not available. Clarity is a Microsoft-hosted SaaS product.

**Consent integration:** Requires explicit consent. Use `clarity("consent", false)` to initialize Clarity in a non-recording state and call `clarity("consent", true)` after the user accepts. Without this, Clarity records sessions before consent is obtained, which violates GDPR.

---

### Vercel Web Analytics

Vercel Web Analytics is a privacy-compliant pageview analytics product built into the Vercel platform. Use Vercel Web Analytics when your project is deployed on Vercel and you need basic traffic analytics without a consent banner or additional tooling.

**Free tier:** Included in all Vercel plans. No separate pricing for basic analytics.

**Paid tier:** Advanced analytics (audience breakdown, custom events) available on Pro and Enterprise Vercel plans ($20/month and up for Pro).

**Data residency:** Vercel infrastructure (AWS-based). Edge network globally distributed. No guaranteed EU-only processing for standard plans.

**Cookie usage:** No cookies. Uses a hash-based approach similar to Plausible. Does not store IP addresses or personal identifiers. Privacy-compliant without a consent banner.

**Self-hosting:** Not available as a standalone product. Tied to Vercel deployment infrastructure.

**Consent integration:** No consent banner required for standard pageview tracking. Custom events that track user-specific behavior may require reassessment depending on what data is attached to those events.

---

### Fathom Analytics

Fathom is a privacy-first analytics platform similar to Plausible, with a focus on simplicity, EU data residency, and GDPR compliance. Use Fathom when you want a hosted, cookieless analytics solution with EU data residency and are willing to pay a premium for a polished product.

**Free tier:** None. Fathom does not offer a free plan.

**Paid pricing:**
- $15/month for up to 100,000 pageviews
- $25/month for up to 200,000 pageviews
- $50/month for up to 500,000 pageviews
- $100/month for up to 1,000,000 pageviews
- Annual billing provides two months free

**Data residency:** EU data residency available. Fathom routes EU visitor data through EU infrastructure. US data processed on US infrastructure. Configurable per site.

**Cookie usage:** No cookies. No personal data collected. Uses a similar daily-hash approach to Plausible. Accepted by EU regulators as not requiring a consent banner.

**Self-hosting:** Not available. Fathom is a hosted-only product.

**Consent integration:** No consent banner required. Fathom is designed to be deployed without a CMP. If you add custom event tracking that captures user-identifiable data, reassess.

---

## Comparison Tables

### Feature Comparison

| Tool | Free Tier | Cookies | Self-Host | EU Residency | Session Recording | Feature Flags |
|------|-----------|---------|-----------|--------------|-------------------|---------------|
| PostHog | Yes (1M events) | Optional | Yes | Yes (Frankfurt) | Yes (5K/mo free) | Yes |
| GA4 | Yes (10M events/day) | Required | No | 360 only | No (native) | No |
| Plausible | No | No | Yes (AGPL) | Yes (Germany) | No | No |
| Umami | Yes (100K events) | No | Yes (MIT) | Self-host only | No | No |
| Microsoft Clarity | Yes (unlimited) | Required | No | No | Yes (unlimited) | No |
| Vercel Analytics | Yes (Vercel plans) | No | No | No | No | No |
| Fathom | No | No | No | Yes | No | No |

### Pricing at Scale

| Tool | 100K pageviews/mo | 1M pageviews/mo | 10M pageviews/mo |
|------|-------------------|-----------------|------------------|
| PostHog | Free | Free | ~$450 (events vary) |
| GA4 | Free | Free | Free (sampling applies) |
| Plausible | $19/mo | $49/mo | $99/mo |
| Umami Cloud | Free | $9/mo | $19/mo |
| Microsoft Clarity | Free | Free | Free |
| Vercel Analytics | Free (Vercel Pro) | Free (Vercel Pro) | Contact sales |
| Fathom | $15/mo | $100/mo | Contact sales |

### Consent Requirement

| Tool | Consent Required | Cookieless Mode | GDPR Without Banner |
|------|-----------------|-----------------|---------------------|
| PostHog (default) | Yes | Partial (loses cross-session) | No |
| PostHog (memory mode) | No | Yes | Yes |
| GA4 | Yes | No | No |
| Plausible | No | Yes (always) | Yes |
| Umami | No | Yes (always) | Yes |
| Microsoft Clarity | Yes | No | No |
| Vercel Analytics | No | Yes (always) | Yes |
| Fathom | No | Yes (always) | Yes |

---

## Decision Tree

Start here and follow the branches to your tool recommendation.

```
Do you need session recordings or heatmaps?
|
+-- Yes --> Do you have budget?
|           |
|           +-- Yes --> PostHog (recordings + full product analytics)
|           |           Microsoft Clarity (free, recordings only, requires consent)
|           |
|           +-- No  --> Microsoft Clarity (free, requires consent banner)
|                       PostHog free tier (5K recordings/mo)
|
+-- No  --> Do you need feature flags or A/B testing?
            |
            +-- Yes --> PostHog (only tool combining analytics + flags)
            |
            +-- No  --> Do you need a consent-free deployment?
                        |
                        +-- Yes --> Are you on Vercel?
                        |           |
                        |           +-- Yes --> Vercel Web Analytics (zero setup)
                        |           |
                        |           +-- No  --> Do you have a budget?
                        |                       |
                        |                       +-- Yes --> Plausible or Fathom
                        |                       |           (Fathom if EU residency critical)
                        |                       |
                        |                       +-- No  --> Umami self-hosted
                        |                                   (free, MIT license)
                        |
                        +-- No  --> Do you need Google Ads integration?
                                    |
                                    +-- Yes --> GA4 (required for Ads ecosystem)
                                    |
                                    +-- No  --> PostHog or GA4
                                                (PostHog for product analytics,
                                                 GA4 for marketing analytics)
```

---

## Pricing Gotchas

### PostHog Event Counting

PostHog counts every distinct event call against your monthly quota. A single pageview with autocapture enabled can generate 5-15 events: `$pageview`, `$pageleave`, DOM click events, form interactions, and rage clicks. A site with 50,000 monthly visitors can consume 500,000-750,000 events before you add any custom tracking. Audit your autocapture configuration before assuming the free tier covers your traffic.

Disable autocapture in production if you only need pageviews and explicit custom events:

```javascript
posthog.init('YOUR_KEY', {
  autocapture: false,
  capture_pageview: true
})
```

Session recordings count separately from events. 5,000 recordings per month sounds generous but depletes quickly on high-traffic sites. Set `session_recording_sample_rate` to limit recording to a percentage of sessions.

### GA4 Data Sampling

GA4 applies data sampling in standard reports when a date range contains more than 500,000 sessions for a property. Sampled reports show estimated data, not actual counts. For high-traffic sites, this means your conversion rates, funnel drop-offs, and event counts are approximations. GA4 360 removes sampling but costs approximately $50,000/year. BigQuery export provides unsampled raw data but requires SQL knowledge and incurs BigQuery storage and query costs.

### Plausible No Free Tier

Plausible has no free hosted tier. The $9/month entry price is for 10,000 pageviews. Sites exceeding 10,000 pageviews move to the next tier automatically. If you need Plausible without cost, self-host it on a $5/month VPS. The self-hosted version is fully featured and has no pageview limits beyond your server capacity.

### Fathom Pageview Definition

Fathom counts pageviews, not sessions or users. A user visiting 10 pages in one session counts as 10 pageviews against your plan limit. Sites with high pages-per-session ratios (content sites, documentation, e-commerce) will hit plan limits faster than expected. Calculate your average pages-per-session before selecting a Fathom plan.

### Microsoft Clarity and GDPR

Clarity is free but requires a consent banner. Many teams deploy Clarity assuming "free = no compliance overhead." This is incorrect. Clarity sets cookies and records sessions, both of which require explicit consent under GDPR. Deploying Clarity without a consent mechanism exposes you to regulatory risk. The cost of a CMP (typically $10-50/month for small sites) must be factored into the "free" calculation.

### PostHog EU Region Lock-In

PostHog requires you to select your data region (US or EU) when creating your organization. You cannot migrate data between regions after creation. If you start on US and later need EU data residency for compliance, you must create a new organization and lose historical data. Select EU (Frankfurt) from the start if there is any possibility of EU compliance requirements.

### GA4 Consent Mode Dependency

GA4 Consent Mode v2 is now required for Google Ads conversion modeling in the EU. Without implementing Consent Mode v2 correctly, Google cannot model conversions for users who decline cookies, causing reported conversion rates to drop significantly (often 20-40% for EU traffic). Implementing Consent Mode v2 requires a certified CMP or custom implementation. This is an ongoing maintenance cost, not a one-time setup.

### Umami Cloud Data Retention

Umami Cloud's free tier retains data for only 90 days. If you need historical trend analysis beyond three months, you must upgrade to a paid plan or self-host. Self-hosted Umami retains data indefinitely (limited only by your database storage).

---

## Recommended Stacks

### Early-Stage Startup (Pre-Product-Market Fit)

**Primary:** PostHog free tier
**Rationale:** The free tier covers 1M events/month, includes session recordings, feature flags, and A/B testing. A single tool replaces Mixpanel, Hotjar, and LaunchDarkly. Consent banner required if using default cookie persistence; use memory mode to avoid it at the cost of cross-session tracking.

**Configuration:** Start with EU region. Enable autocapture selectively. Use feature flags for rollouts from day one.

**Add if needed:** Vercel Web Analytics for marketing site traffic (if deployed on Vercel), keeping PostHog for product analytics.

---

### Growth-Stage SaaS (Post-PMF, Scaling)

**Primary:** PostHog (paid) for product analytics and feature management
**Secondary:** Plausible for marketing site traffic
**Rationale:** PostHog paid tier provides multi-project support and extended retention for product analytics. Plausible handles marketing site traffic without a consent banner, keeping the marketing funnel clean. Avoid GA4 unless Google Ads integration is required.

**Add if needed:** GA4 with Consent Mode v2 if running Google Ads campaigns. Keep PostHog as the source of truth for product metrics.

---

### E-Commerce

**Primary:** GA4 with Consent Mode v2
**Secondary:** Microsoft Clarity for UX analysis
**Rationale:** GA4 integrates natively with Google Ads, Google Merchant Center, and Google Shopping. E-commerce conversion tracking requires the Google ecosystem. Clarity provides free session recordings and heatmaps for checkout funnel optimization. Both require a consent banner; implement a CMP that supports Consent Mode v2.

**Required:** A certified CMP (Cookiebot, OneTrust, Usercentrics) for Consent Mode v2 compliance.

**Add if needed:** PostHog for product analytics if you have a logged-in user experience (accounts, wishlists, subscriptions).

---

### Privacy-First / EU-Focused

**Primary:** Plausible (hosted) or Umami (self-hosted)
**Secondary:** None required
**Rationale:** No consent banner, no cookies, no personal data. Plausible provides a polished hosted experience with EU data residency. Umami self-hosted provides the same capabilities at infrastructure cost only. Neither tool provides session recordings or user-level analytics; this is a deliberate trade-off for compliance simplicity.

**When to upgrade:** If you need session recordings, add PostHog in memory mode (cookieless) with a consent banner, or accept that recordings require consent infrastructure.

---

### Internal Tools / B2B SaaS

**Primary:** PostHog (EU region)
**Rationale:** Internal tools and B2B SaaS typically have authenticated users. PostHog's user identification, group analytics (company-level tracking), and feature flags are purpose-built for this use case. Consent requirements are simpler when users are employees or authenticated customers with a terms-of-service agreement.

**Configuration:** Use `posthog.identify()` with your internal user ID. Use group analytics to track company-level feature adoption. Disable session recordings for sensitive internal tools.

---

## Tool Limitations Summary

| Tool | Primary Limitation | Secondary Limitation |
|------|-------------------|---------------------|
| PostHog | Event counting depletes free tier fast | EU region must be selected at creation |
| GA4 | Data sampling above 500K sessions | Requires Google ecosystem for full value |
| Plausible | No free hosted tier | No user-level or session analytics |
| Umami | Cloud has 90-day retention on free tier | No session recordings |
| Microsoft Clarity | Requires consent banner | No EU data residency |
| Vercel Analytics | Vercel-only deployment | Limited event customization |
| Fathom | No free tier, higher cost than Plausible | No self-hosting option |

---

## Migration Considerations

Switching analytics tools mid-project loses historical data unless you export it first. Plan your tool selection before launch when possible.

**From GA4 to PostHog:** Export GA4 data to BigQuery before switching. PostHog's data warehouse can ingest BigQuery exports for historical analysis. Event schemas differ; map GA4 event names to PostHog equivalents during migration.

**From PostHog to Plausible:** Plausible does not support event-level data import. You lose all historical behavioral data. Export PostHog data to your own storage before switching if retention matters.

**From Universal Analytics to GA4:** UA data is no longer accessible in the GA4 interface. If you have UA historical data, it must have been exported to BigQuery before the UA sunset deadline (July 2024). New GA4 properties start with no historical data.

**Self-hosted to cloud:** Umami and Plausible both support data export from self-hosted instances. Verify export format compatibility with the cloud version before migrating.
