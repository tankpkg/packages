---
name: "@tank/rendering-patterns"
description: |
  Framework-agnostic rendering and hydration patterns for the modern web.
  Covers Client-Side Rendering (SPA architecture, tradeoffs, when appropriate),
  Server-Side Rendering (request-time HTML, streaming SSR, chunked transfer),
  Static Site Generation (build-time HTML, limitations), Incremental Static
  Regeneration (on-demand + timed revalidation), Progressive Hydration (partial,
  lazy, scheduled hydration), Islands Architecture (isolated interactive regions
  in static pages), React Server Components (server-only rendering without
  hydration cost), Selective Hydration (priority-based with concurrent features),
  Resumability (serialize state instead of replay, Qwik model), and the View
  Transitions API (cross-document and same-document transitions).

  Synthesizes Osmani (Learning JavaScript Design Patterns), Google Chrome team articles,
  web.dev performance guides, Astro documentation, Qwik documentation,
  React documentation, Archibald (Streaming rendering), Miller & Patterson
  (Islands Architecture), and Kleppmann (data-intensive applications).

  Trigger phrases: "rendering pattern", "SSR vs CSR", "SSG vs SSR",
  "server-side rendering", "client-side rendering", "static site generation",
  "incremental static regeneration", "ISR", "streaming SSR",
  "progressive hydration", "partial hydration", "islands architecture",
  "React Server Components", "RSC", "selective hydration",
  "resumability", "Qwik", "View Transitions", "hydration cost",
  "time to interactive", "which rendering strategy",
  "SPA vs MPA", "multi-page app", "single-page app",
  "slow first load", "too much JavaScript", "hydration mismatch",
  "TTFB optimization", "FCP optimization", "LCP optimization",
  "rendering tradeoffs", "when to use SSR", "when to use SSG"
---

# Web Rendering and Hydration Patterns

## Core Philosophy

1. **Rendering is a spectrum, not a binary.** No application is purely "CSR" or "SSR." Modern architectures mix strategies per route, per component, and per interaction boundary.
2. **Ship less JavaScript to the client.** Every kilobyte of client JS has a hydration cost, a parse cost, and an interactivity delay. Minimize what the browser must execute.
3. **Match the pattern to the content's dynamism.** Static content deserves build-time rendering. Personalized content needs server rendering. Interactive widgets need client hydration. Apply each where it fits.
4. **Measure real user impact.** Core Web Vitals (LCP, FID/INP, CLS) are the arbiters. A pattern that improves TTFB but worsens INP is not a net win.

## Quick-Start: Common Problems

### "My app is slow to load"

1. Profile with Lighthouse and WebPageTest to identify the bottleneck (TTFB? FCP? LCP? TTI?)
2. High TTFB? -> Server is slow or no edge caching. Consider SSG/ISR for cacheable pages.
3. High FCP but low TTFB? -> HTML is fast but render-blocking JS. Consider streaming SSR.
4. High TTI with good FCP? -> Too much hydration JS. Consider islands, progressive hydration, or RSC.
5. Large JS bundle? -> Audit client components. Move data-fetching to server, use code splitting.
-> See `references/strategy-selection.md`

### "When should I use SSR vs SSG?"

1. Does every user see the same content? -> SSG (build-time) or ISR (stale-while-revalidate)
2. Is the data user-specific or real-time? -> SSR (request-time)
3. Can you tolerate stale data for seconds/minutes? -> ISR with revalidation interval
4. Do you have thousands of pages? -> On-demand SSG (generate on first request, cache after)
-> See `references/server-rendering.md`

### "My SPA has poor SEO and slow initial loads"

1. Add SSR or SSG for the initial paint, then hydrate for interactivity
2. Use streaming SSR to send HTML progressively while data loads
3. Consider islands architecture if most of the page is static
4. Evaluate RSC to eliminate hydration cost for non-interactive parts
-> See `references/client-rendering.md` and `references/hydration-patterns.md`

### "Hydration is making my page janky"

1. Audit which components actually need client-side interactivity
2. Apply progressive hydration to defer non-visible component hydration
3. Use selective hydration to prioritize user-interacted regions
4. Consider islands architecture to hydrate only interactive widgets
5. Evaluate resumability (Qwik) to eliminate replay entirely
-> See `references/hydration-patterns.md`

## Decision Trees

### Rendering Strategy Selection

| Content Type | Update Frequency | Personalized | Recommended Pattern |
|---|---|---|---|
| Marketing pages, docs, blog | Rarely | No | SSG |
| Product listings, CMS pages | Hourly/daily | No | ISR |
| Dashboards, feeds | Real-time | Yes | SSR (streaming) |
| Interactive tools, editors | N/A (client state) | Yes | CSR with SSR shell |
| Mixed (static layout + dynamic widgets) | Varies | Partial | Islands or RSC |
| E-commerce PDP | Minutes | Partial | ISR + client-side personalization |

### Hydration Strategy Selection

| Scenario | Pattern | Why |
|---|---|---|
| Mostly static page, few interactive widgets | Islands | Hydrate only what needs it |
| Large app, many components, prioritize above-fold | Progressive hydration | Defer below-fold hydration |
| User clicks before hydration completes | Selective hydration | Prioritize interacted component |
| Server-heavy data fetching, minimal client interaction | RSC | No hydration for server components |
| Extreme performance requirements, no hydration budget | Resumability | No replay, instant interactivity |
| Full interactivity needed everywhere | Full hydration | Standard, but minimize JS payload |

### Framework Alignment

| Pattern | Framework Examples |
|---|---|
| SSR + streaming | Next.js, Nuxt 3, SvelteKit, Remix, SolidStart |
| SSG + ISR | Next.js, Nuxt 3, Astro, Eleventy |
| Islands | Astro, Fresh (Deno), Marko |
| RSC | Next.js (App Router), Waku |
| Resumability | Qwik, QwikCity |
| View Transitions | Astro, any MPA with the API, SPA frameworks via router |
| CSR (SPA) | React (CRA/Vite), Vue (Vite), Angular, Svelte (SPA mode) |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Full CSR for content sites | Poor SEO, slow FCP, blank screen | SSG or SSR for initial HTML |
| SSR everything including static content | Unnecessary server load per request | SSG/ISR for static, SSR for dynamic |
| Hydrating the entire page | TTI blocked by full JS bundle parse | Islands, progressive hydration, or RSC |
| Ignoring streaming | Users wait for slowest data query | Stream HTML, use Suspense boundaries |
| ISR with no fallback strategy | First visitor gets a cache miss | Use fallback: "blocking" or stale-while-revalidate |
| Client-side data fetching for above-fold | Layout shift, waterfall requests | Fetch on server, stream the result |
| Hydration mismatch | Console errors, visual flicker | Ensure server and client render identical initial HTML |

## Reference Index

| File | Contents |
|------|----------|
| `references/server-rendering.md` | SSR request flow, streaming SSR (chunked transfer, out-of-order streaming, Suspense boundaries), SSG build-time generation, ISR (timed + on-demand revalidation), edge rendering, cache strategies |
| `references/hydration-patterns.md` | Full hydration cost model, progressive hydration (idle-until-urgent, visible, interaction), selective hydration (concurrent React), islands architecture (Astro model), resumability (Qwik model), RSC server/client boundaries |
| `references/client-rendering.md` | SPA architecture, CSR tradeoffs, code splitting, lazy loading, shell pattern, SEO mitigation, when CSR is the right choice, performance optimization for SPAs |
| `references/view-transitions.md` | View Transitions API (same-document, cross-document), animation control, fallback strategies, MPA vs SPA transitions, framework integration patterns, accessibility |
| `references/strategy-selection.md` | Detailed tradeoff matrix (TTFB, FCP, LCP, TTI, SEO, server cost, complexity), decision flowchart, migration paths between patterns, hybrid architectures, Core Web Vitals impact per pattern |
