# Rendering Strategy Selection Guide

Sources: Osmani (Learning JavaScript Design Patterns), Google Chrome team (web.dev), Vercel engineering blog, Shopify engineering blog, Kleppmann (Designing Data-Intensive Applications), Grigorik (High Performance Browser Networking)

Covers: detailed tradeoff matrices, Core Web Vitals impact per pattern, decision flowcharts, hybrid architectures, migration paths between patterns, and capacity/cost analysis.

## Core Web Vitals Impact by Pattern

Each rendering pattern affects Core Web Vitals differently. Use this matrix to select a pattern based on which metrics matter most for the use case.

### Metric Impact Matrix

| Pattern | TTFB | FCP | LCP | TTI/INP | CLS | SEO |
|---|---|---|---|---|---|---|
| CSR (SPA) | Excellent | Poor | Poor | Good (post-load) | Risk | Poor |
| SSR | Moderate | Good | Good | Moderate (hydration gap) | Low | Excellent |
| Streaming SSR | Good | Excellent | Good | Moderate | Low | Excellent |
| SSG | Excellent | Excellent | Excellent | Good | Low | Excellent |
| ISR | Good (cached) | Excellent | Excellent | Good | Low | Excellent |
| Islands | Excellent | Excellent | Excellent | Excellent | Low | Excellent |
| RSC | Good | Good | Good | Good | Low | Excellent |
| Resumability | Good | Good | Good | Excellent | Low | Excellent |

### Rating Definitions

| Rating | Meaning |
|---|---|
| Excellent | Consistently meets "good" thresholds with minimal effort |
| Good | Meets thresholds with standard implementation |
| Moderate | May need optimization to meet thresholds |
| Poor | Difficult to meet thresholds without significant mitigation |
| Risk | Prone to issues without explicit handling |

## Decision Flowchart

Follow this sequence to select a rendering strategy:

### Step 1: Content Dynamism

| Question | If Yes | If No |
|---|---|---|
| Is content identical for all users? | Go to Step 2 (static path) | Go to Step 3 (dynamic path) |

### Step 2: Static Content Path

| Question | If Yes | If No |
|---|---|---|
| Does content change less than daily? | SSG | ISR |
| Are there more than 10,000 pages? | ISR (on-demand generation) | SSG |
| Must content update within seconds of source change? | ISR (on-demand revalidation) | SSG or ISR (time-based) |

### Step 3: Dynamic Content Path

| Question | If Yes | If No |
|---|---|---|
| Is the page primarily interactive (dashboard, editor, tool)? | CSR or SSR + heavy client | SSR or streaming SSR |
| Is the page behind authentication? | CSR is acceptable; SSR if SEO/FCP matters | SSR or streaming SSR |
| Is the page content-heavy with isolated interactive elements? | Islands architecture | Continue |
| Does the page have server-heavy data with minimal client interaction? | RSC | Continue |
| Must TTI equal FCP (zero hydration budget)? | Resumability (Qwik) | SSR with progressive hydration |

### Step 4: Hybrid Considerations

| Scenario | Hybrid Approach |
|---|---|
| Static layout with personalized widget | SSG/ISR for page + client-side fetch for personalization |
| Dashboard with cacheable overview | ISR for overview + SSR for real-time drilldowns |
| E-commerce product page | ISR for product info + client-side for cart, reviews |
| Content site with interactive features | Islands (static content + interactive islands) |
| Large app with mixed interactivity | RSC (server components for data, client components for interaction) |

## Detailed Pattern Tradeoff Analysis

### Server Cost

| Pattern | Server Requirement | Cost Profile |
|---|---|---|
| CSR | Static file hosting only | Lowest (CDN cost only) |
| SSG | Build server + static hosting | Low (build cost only) |
| ISR | Runtime server + CDN | Moderate (regeneration compute) |
| SSR | Runtime server, always on | Higher (per-request compute) |
| Streaming SSR | Runtime server with streaming support | Higher (per-request, longer connections) |
| Edge SSR | Edge compute (V8 isolates) | Moderate (per-request, but distributed) |
| Islands | Build server + static hosting | Low (similar to SSG) |
| RSC | Runtime server with RSC support | Moderate (server component rendering) |

### Complexity

| Pattern | Implementation Complexity | Why |
|---|---|---|
| CSR | Low | Standard SPA, well-understood |
| SSG | Low | Build step generates static files |
| ISR | Moderate | Revalidation logic, cache management |
| SSR | Moderate | Server runtime, state management, caching |
| Streaming SSR | High | Suspense boundaries, error handling, header management |
| Islands | Moderate | Component boundary decisions, inter-island communication |
| RSC | High | Server/client boundary, serialization rules, mental model |
| Resumability | Moderate (framework handles it) | Qwik framework, different mental model from React/Vue |

### Scalability

| Pattern | Scaling Characteristic |
|---|---|
| CSR | Scales infinitely (static files on CDN) |
| SSG | Scales infinitely (static files on CDN), build time is the bottleneck |
| ISR | Scales well (CDN-served after first generation, regeneration is bounded) |
| SSR | Scales with server capacity (requires auto-scaling, caching, edge) |
| Streaming SSR | Similar to SSR, but longer-lived connections increase concurrency needs |
| Islands | Scales like SSG (static pages with cached islands) |
| RSC | Scales with server capacity (server components add rendering load) |

## Per-Route Strategy (Hybrid Architecture)

Modern frameworks support per-route rendering configuration. Apply the right pattern to each route:

### Example Application Architecture

| Route | Content Type | Pattern | Why |
|---|---|---|---|
| `/` | Marketing landing | SSG | Static, cached, fastest possible |
| `/blog/:slug` | Blog posts | SSG or ISR | Content changes infrequently |
| `/products` | Product listing | ISR (60s) | Changes with inventory, staleness acceptable |
| `/products/:id` | Product detail | ISR (on-demand) | Update on CMS publish webhook |
| `/dashboard` | User dashboard | SSR (streaming) | Personalized, real-time data |
| `/editor` | Rich text editor | CSR | Purely interactive, no SEO needed |
| `/docs` | Documentation | SSG | Static content, maximum performance |
| `/search` | Search results | SSR | Query-dependent, must be fresh |

### Route Configuration Pattern

```
// Conceptual (framework-agnostic)
routes:
  - path: "/"
    rendering: static
    revalidate: false

  - path: "/blog/:slug"
    rendering: static
    revalidate: 3600  // ISR: 1 hour

  - path: "/dashboard"
    rendering: server
    streaming: true

  - path: "/editor"
    rendering: client
```

## Migration Paths

### CSR to SSR

| Step | Action | Risk |
|---|---|---|
| 1 | Audit client-side data fetching | Low |
| 2 | Move data fetching to server (getServerSideProps, loader, etc.) | Medium (API refactoring) |
| 3 | Handle server/client state differences | Medium (hydration mismatches) |
| 4 | Add streaming for slow data sources | Low (incremental improvement) |
| 5 | Optimize server response caching | Low |

### SSR to SSG/ISR

| Step | Action | Risk |
|---|---|---|
| 1 | Identify pages that do not need request-time data | Low |
| 2 | Move those pages to static generation | Low |
| 3 | Add ISR for pages that need periodic freshness | Low |
| 4 | Keep SSR only for pages that require request context | Low |
| 5 | Add on-demand revalidation for CMS-driven content | Low |

### Monolithic CSR to Islands

| Step | Action | Risk |
|---|---|---|
| 1 | Identify interactive vs static regions | Low |
| 2 | Extract interactive regions into island components | Medium (architecture change) |
| 3 | Render the page as static HTML with island placeholders | Medium |
| 4 | Each island loads its own JS bundle independently | Low |
| 5 | Remove the global app shell and client-side router | High (significant refactor) |

### SSR to RSC

| Step | Action | Risk |
|---|---|---|
| 1 | Identify components that do not use hooks or browser APIs | Low |
| 2 | Mark those as Server Components (remove "use client") | Low |
| 3 | Move data fetching into Server Components (direct DB/API access) | Medium |
| 4 | Define clear server/client boundaries | Medium |
| 5 | Audit bundle size reduction | Low |

## Capacity and Performance Budgets

### Performance Budget by Pattern

| Metric | Budget (Mobile 3G) | Budget (Desktop) |
|---|---|---|
| TTFB | < 800ms | < 200ms |
| FCP | < 1.8s | < 1.0s |
| LCP | < 2.5s | < 1.5s |
| TTI | < 3.8s | < 2.0s |
| TBT | < 200ms | < 100ms |
| CLS | < 0.1 | < 0.1 |
| INP | < 200ms | < 100ms |

### JS Budget Guidelines

| Page Type | Max JS (compressed) | Rationale |
|---|---|---|
| Static content page | < 50KB | Minimal interactivity needed |
| Standard web page | < 150KB | Balance of features and performance |
| Interactive application | < 300KB | Code-split aggressively beyond this |
| Complex SPA (dashboard) | < 500KB | Accept slower initial load for functionality |

### Server Capacity Planning for SSR

| Factor | Estimation Approach |
|---|---|
| Render time per page | Benchmark: measure P50 and P99 render times |
| Concurrent requests | Server CPUs x (1000ms / render_time_ms) |
| Cache hit ratio target | 80-95% for ISR, reduces origin load proportionally |
| Edge compute | Reduces origin load, adds per-request cost at edge |
| Streaming overhead | Longer-lived connections, plan for higher concurrency |

## Pattern Comparison Summary

| Dimension | CSR | SSR | Streaming | SSG | ISR | Islands | RSC | Resumability |
|---|---|---|---|---|---|---|---|---|
| First load speed | Slow | Moderate | Fast | Fastest | Fast | Fastest | Fast | Fast |
| Interactivity | Instant | Delayed | Delayed | Fast | Fast | Instant (islands) | Fast | Instant |
| SEO | Poor | Good | Good | Good | Good | Good | Good | Good |
| Server cost | None | High | High | None | Low | None | Moderate | Low |
| Complexity | Low | Moderate | High | Low | Moderate | Moderate | High | Moderate |
| JS shipped | All | All | All | Minimal | Minimal | Islands only | Client only | Per-interaction |
| Data freshness | Real-time | Real-time | Real-time | Build time | Configurable | Build/server | Real-time | Real-time |
| Best for | Apps | Dynamic pages | Slow data | Static sites | Hybrid | Content sites | React apps | Perf-critical |

## Common Mistakes by Application Type

### E-Commerce

| Mistake | Why It Hurts | Correct Approach |
|---|---|---|
| CSR for product pages | Poor SEO, slow LCP, lost sales | ISR for product pages, SSR for search |
| SSR for every page including static ones | Unnecessary server cost | SSG/ISR for marketing, SSR for dynamic |
| No streaming for checkout | Slow payment form load | Stream checkout form, prefetch payment SDK |

### Content/Media Sites

| Mistake | Why It Hurts | Correct Approach |
|---|---|---|
| SSR for articles that rarely change | Wasted server compute | SSG or ISR with long revalidation |
| Full hydration for read-only content | Unnecessary JS for non-interactive pages | Islands for interactive widgets only |
| No edge caching | High TTFB for global audiences | CDN with aggressive caching, ISR |

### SaaS Dashboards

| Mistake | Why It Hurts | Correct Approach |
|---|---|---|
| SSG for personalized dashboards | Cannot use request-time data | SSR with streaming for data-heavy views |
| No code splitting | Entire app loads on first page | Route-based splitting, lazy load heavy views |
| Hydrating the entire dashboard shell | Slow TTI on complex layouts | Progressive hydration, RSC for data display |

## Framework Selection by Pattern Priority

| If Primary Pattern Is | Consider These Frameworks |
|---|---|
| SSG-first | Astro, Eleventy, Hugo |
| ISR-first | Next.js, Nuxt 3 |
| SSR + Streaming | Next.js (App Router), Remix, SolidStart |
| Islands | Astro, Fresh (Deno), Marko |
| RSC | Next.js (App Router), Waku |
| Resumability | Qwik, QwikCity |
| CSR/SPA | React (Vite), Vue (Vite), Angular, Svelte |
| MPA with transitions | Astro, any framework + View Transitions API |
