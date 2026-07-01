# Server Rendering Strategies

Sources: Osmani (Learning JavaScript Design Patterns), Archibald (Streaming rendering), Google Chrome team (web.dev), React documentation, Vercel engineering blog, Kleppmann (Designing Data-Intensive Applications)

Covers: Server-Side Rendering (SSR), Streaming SSR, Static Site Generation (SSG), Incremental Static Regeneration (ISR), edge rendering, and server-side caching strategies.

## Server-Side Rendering (SSR)

SSR generates HTML on the server for each incoming request. The browser receives a fully rendered document, improving First Contentful Paint (FCP) and SEO compared to client-only rendering.

### Request Flow

1. Browser sends HTTP request to the server
2. Server executes application code and data fetching
3. Server renders the component tree to an HTML string
4. Server sends the complete HTML response
5. Browser paints the HTML immediately (FCP)
6. Browser downloads and executes the JavaScript bundle
7. Hydration attaches event listeners and restores interactivity (TTI)

### SSR Tradeoffs

| Advantage | Cost |
|---|---|
| Fast FCP for content-heavy pages | Server compute cost per request |
| Full SEO crawlability | TTFB depends on server speed + data fetching |
| Access to request context (cookies, headers) | Requires a running server (not just CDN) |
| Consistent rendering across devices | Hydration gap between FCP and TTI |
| No client-side data fetching waterfall | Server-side failures affect entire page |

### When to Use SSR

- Content is personalized per user (dashboards, authenticated views)
- Data changes frequently and must be fresh on every request
- SEO is critical and content depends on request-time data
- The page requires access to request headers, cookies, or geo-location

### When to Avoid SSR

- Content is identical for all users (use SSG or ISR instead)
- The page is purely interactive with no meaningful initial HTML
- Server infrastructure costs are a constraint and traffic is high

## Streaming SSR

Streaming SSR sends HTML to the browser in chunks as the server renders, rather than waiting for the entire page to be ready. This dramatically improves TTFB and perceived performance.

### How Streaming Works

The server uses HTTP chunked transfer encoding to flush HTML progressively:

1. Send the `<head>` and page shell immediately (TTFB is fast)
2. Start rendering components top-to-bottom
3. When a component's data is ready, flush its HTML chunk
4. For components still loading, send a placeholder (Suspense fallback)
5. When data resolves, send the completed HTML with an inline `<script>` that swaps it in

### Out-of-Order Streaming

Standard streaming sends HTML in document order. Out-of-order streaming (used by React 18+) allows resolved components to stream regardless of position:

```
Time 0: Shell + header + fallback placeholders
Time 50ms: Footer data resolves -> stream footer HTML + swap script
Time 200ms: Main content resolves -> stream main HTML + swap script
Time 500ms: Sidebar data resolves -> stream sidebar HTML + swap script
```

The browser sees content appear progressively, and the slowest data source does not block faster ones.

### Suspense Boundaries

Suspense boundaries define the granularity of streaming. Each boundary is an independent streaming unit:

| Boundary Granularity | Effect |
|---|---|
| One boundary wrapping the entire page | No benefit over non-streaming SSR |
| One boundary per major section | Good balance of streaming and simplicity |
| One boundary per data-fetching component | Maximum streaming granularity, more complexity |
| Nested boundaries | Outer shell streams first, inner content fills in progressively |

### Streaming SSR Tradeoffs

| Advantage | Cost |
|---|---|
| Fast TTFB (shell streams immediately) | Requires Suspense-aware framework |
| Progressive content reveal | Headers (status code, redirects) must be set before first flush |
| Slow queries do not block fast ones | Error handling is more complex (partial page already sent) |
| Better perceived performance | Response is not cacheable in traditional CDN (chunked) |

## Static Site Generation (SSG)

SSG renders pages to HTML at build time. The output is static files served directly from a CDN with no server runtime.

### Build-Time Flow

1. Build process runs the application for each route
2. Data is fetched once during build
3. HTML files are generated and written to disk
4. Files are deployed to CDN edge locations
5. Every request is served from CDN cache (TTFB is fastest possible)

### SSG Tradeoffs

| Advantage | Cost |
|---|---|
| Fastest TTFB (CDN-served static files) | Content is stale until next build |
| No server runtime cost | Build time grows with page count |
| Inherently cacheable and scalable | Cannot use request-time data (no cookies, headers) |
| Works with any static hosting | Personalization requires client-side fetching |
| Maximum reliability (no server to fail) | Dynamic routes need enumeration at build time |

### When to Use SSG

- Content changes infrequently (docs, marketing, blog posts)
- All users see the same content
- Page count is manageable (hundreds, not millions)
- Maximum performance and reliability are priorities

### SSG Limitations

- **Build time scaling:** Thousands of pages create long build times. Mitigate with on-demand generation.
- **Stale content:** Data is frozen at build time. Users may see outdated information.
- **No request context:** Cannot tailor content based on cookies, authentication, or geo-location without client-side fetching.
- **Dynamic routes:** Pages with URL parameters that cannot be enumerated at build time require fallback strategies.

## Incremental Static Regeneration (ISR)

ISR combines the performance of SSG with the freshness of SSR. Pages are statically generated but can be revalidated after deployment without a full rebuild.

### Revalidation Strategies

#### Time-Based Revalidation

Set a `revalidate` interval (in seconds). After the interval expires:

1. The next request serves the stale page immediately (fast)
2. In the background, the server regenerates the page with fresh data
3. Subsequent requests receive the updated page

This is a stale-while-revalidate pattern applied at the page level.

#### On-Demand Revalidation

Trigger revalidation programmatically via an API endpoint or webhook:

1. CMS publishes new content and calls the revalidation endpoint
2. The server regenerates the specific page immediately
3. The CDN cache is purged for that path
4. Next request gets the fresh page

### ISR Tradeoffs

| Advantage | Cost |
|---|---|
| CDN-served (fast TTFB after first generation) | First request on uncached page may be slow |
| Pages update without full rebuild | Requires server runtime for regeneration |
| Scales to millions of pages | Brief window of stale content (time-based) |
| Per-page revalidation granularity | More complex deployment infrastructure |

### ISR vs SSG vs SSR Decision

| Factor | SSG | ISR | SSR |
|---|---|---|---|
| Data freshness | Build time only | Seconds to minutes stale | Real-time |
| TTFB (after cache) | Fastest | Fast | Depends on server |
| Server cost | None | Low (regeneration only) | Per-request |
| Personalization | None (server-side) | None (server-side) | Full |
| Build time | Grows with pages | Initial build only | No build |
| Cache strategy | CDN, immutable | CDN with revalidation | CDN with vary headers |

## Edge Rendering

Edge rendering executes server logic at CDN edge locations close to the user, reducing latency compared to origin-based SSR.

### Edge SSR Characteristics

| Aspect | Detail |
|---|---|
| Latency | Lower TTFB (server is geographically close) |
| Runtime constraints | Limited compute time, memory, and API access |
| Cold starts | Fast (lightweight runtimes like V8 isolates) |
| Data locality | Data source may still be in one region (latency for DB queries) |
| Use cases | Personalization at edge, A/B testing, geo-targeted content |

### Edge vs Origin Rendering

| Scenario | Recommended |
|---|---|
| Simple personalization (geo, cookies) | Edge |
| Heavy data processing, complex queries | Origin |
| Latency-sensitive, global audience | Edge |
| Access to regional database | Origin (or edge with data replication) |
| Static with minor dynamic elements | Edge (compute-at-edge for the dynamic parts) |

## Server-Side Caching Strategies

### Page-Level Caching

| Strategy | Headers | Use Case |
|---|---|---|
| Full static cache | `Cache-Control: public, max-age=31536000, immutable` | SSG assets, versioned files |
| Stale-while-revalidate | `Cache-Control: public, s-maxage=60, stale-while-revalidate=3600` | ISR pages |
| Private, no cache | `Cache-Control: private, no-store` | Personalized SSR pages |
| Short TTL | `Cache-Control: public, s-maxage=10` | Frequently changing pages |

### Fragment Caching

Cache individual page sections independently rather than entire pages. Useful when a page mixes static and dynamic content:

- Cache the navigation, footer, and sidebar permanently
- Cache the product listing for 60 seconds
- Never cache the user greeting or cart count

Fragment caching enables SSR pages to serve mostly-cached content with only the dynamic sections computed per request.

### Cache Invalidation Patterns

| Pattern | Mechanism | Tradeoff |
|---|---|---|
| TTL-based expiry | Time-based, automatic | Simple but stale window is fixed |
| Event-driven purge | Webhook on content change | Fresh but requires pub/sub infrastructure |
| Tag-based invalidation | Purge all pages tagged with a content ID | Granular but CDN must support tags |
| Versioned URLs | Append content hash to URL | Immutable cache, but requires URL management |

## SSR Error Handling

### Error Boundaries in Server Rendering

| Error Type | SSR Behavior | Streaming SSR Behavior |
|---|---|---|
| Data fetch failure | Return error page or fallback HTML | Stream fallback for failed Suspense boundary |
| Component render error | Catch with error boundary, render fallback | Catch per-boundary, other sections unaffected |
| Timeout | Return 504 or cached stale version | Flush what is ready, timeout remaining sections |
| Partial failure | Entire page fails (all-or-nothing) | Only the failed section shows fallback |

### Graceful Degradation Strategies

1. Wrap data-dependent sections in error boundaries with meaningful fallbacks
2. Set timeouts on all data fetches to prevent indefinite server hangs
3. Use circuit breakers for downstream services to fail fast under load
4. Return stale cached content when the origin is unavailable
5. Log server rendering errors with request context for debugging
6. Return appropriate HTTP status codes (500 for errors, 503 for overload)

## SSR Performance Optimization

### Server Render Time Reduction

| Technique | Effect |
|---|---|
| Component-level caching | Cache rendered HTML fragments for repeated components |
| Data fetch parallelization | Fetch all independent data sources concurrently |
| Database connection pooling | Reduce connection overhead per request |
| Avoid synchronous I/O in render path | Prevent blocking the event loop |
| Pre-compute expensive derivations | Move computation to build or background workers |
| Use streaming to unblock fast sections | Slow queries do not delay the entire response |

### Monitoring SSR Performance

| Metric | What to Track | Alert Threshold |
|---|---|---|
| Server render time (P50, P99) | Time from request to response complete | P99 > 500ms |
| TTFB distribution | Time to first byte across all pages | P75 > 800ms |
| Cache hit ratio | Percentage of requests served from cache | < 80% for cacheable pages |
| Error rate | Percentage of failed server renders | > 1% |
| Concurrent connections | Active SSR requests in flight | Near server capacity |
