# Client-Side Rendering and SPA Patterns

Sources: Osmani (Learning JavaScript Design Patterns), Google Chrome team (web.dev), MDN Web Docs, Grigorik (High Performance Browser Networking), Miller (Web Performance in Action)

Covers: SPA architecture, CSR tradeoffs, when CSR is appropriate, code splitting, lazy loading, app shell pattern, SEO strategies for SPAs, and client-side performance optimization.

## Client-Side Rendering (CSR)

CSR renders the entire application in the browser. The server sends a minimal HTML document with a JavaScript bundle. The browser executes the JS to build the DOM, fetch data, and render content.

### CSR Request Flow

1. Browser requests the page
2. Server returns a minimal HTML shell (often just a `<div id="root">`)
3. Browser downloads the JavaScript bundle(s)
4. JS executes, renders the application into the DOM
5. Application makes API calls to fetch data
6. Content renders after data returns (First Contentful Paint)
7. Application is immediately interactive (no hydration gap)

### CSR Performance Characteristics

| Metric | CSR Behavior |
|---|---|
| TTFB | Fast (tiny HTML document) |
| FCP | Slow (blocked by JS download + execution + data fetch) |
| LCP | Slow (content depends on JS + API calls) |
| TTI | Once FCP occurs, TTI is immediate (no hydration) |
| CLS | Risk of layout shift as data loads asynchronously |
| INP | Good (full client-side interactivity, no server round-trips) |

### CSR Tradeoffs

| Advantage | Cost |
|---|---|
| No server runtime needed (static hosting) | Blank page until JS loads and executes |
| Rich, app-like interactivity | Poor SEO for content-dependent pages |
| Smooth client-side navigation (no full page reload) | Slow initial load (JS bundle + data waterfall) |
| Simplified deployment (CDN only) | Heavy JS burden on low-end devices |
| No hydration mismatch possible | Accessibility depends entirely on client JS |
| Full control over rendering timing | Crawlers may not execute JS reliably |

## When CSR Is the Right Choice

CSR is appropriate when the following conditions align:

### Strong Signals for CSR

| Signal | Why CSR Fits |
|---|---|
| Behind authentication | No SEO needed; user waits for login anyway |
| Highly interactive (dashboards, editors, tools) | Continuous state management benefits from client-side model |
| Real-time collaborative features | WebSocket/SSE state lives client-side |
| Offline-capable (PWA) | Service worker caches the app shell and data |
| Internal enterprise tools | Controlled environment, predictable devices |
| Canvas/WebGL applications | Rendering is inherently client-side |

### Weak Signals (Reconsider CSR)

| Signal | Better Alternative |
|---|---|
| Content must be indexed by search engines | SSR or SSG |
| Fast first load is critical (e-commerce, media) | SSR with streaming or SSG |
| Target audience uses low-end mobile devices | SSR to reduce client JS |
| Marketing/landing pages | SSG for fastest possible load |
| Content-heavy with minimal interactivity | SSG or islands architecture |

## The App Shell Pattern

The app shell pattern separates the UI shell (navigation, layout, chrome) from the dynamic content. The shell is cached aggressively, providing instant visual structure while content loads.

### App Shell Architecture

```
App Shell (cached in Service Worker)
  |-- Navigation bar (static, cached)
  |-- Sidebar (static, cached)
  |-- Content area (dynamic, loaded per route)
  |-- Footer (static, cached)
```

### App Shell Implementation

1. Pre-render or inline the shell HTML in the initial document
2. Register a Service Worker that caches the shell and core assets
3. On subsequent visits, the shell loads from cache instantly
4. Route-specific content loads dynamically into the content area
5. Offline mode displays the shell with a "no connection" message in content area

### App Shell Tradeoffs

| Advantage | Cost |
|---|---|
| Instant repeat-visit loading | First visit still requires full download |
| Offline capability | Service Worker complexity |
| Perceived performance (shell appears immediately) | Content area still depends on network |
| Cacheable static assets | Cache invalidation for shell updates |

## Code Splitting Strategies

Code splitting divides the JavaScript bundle into smaller chunks loaded on demand. This is the most impactful optimization for CSR applications.

### Splitting Strategies

| Strategy | How | When to Use |
|---|---|---|
| Route-based splitting | Each route is a separate chunk | Default for most SPAs |
| Component-based splitting | Heavy components loaded on demand | Modals, charts, editors, admin panels |
| Vendor splitting | Third-party libraries in a separate chunk | When vendor code changes less than app code |
| Feature-based splitting | Feature flags determine which code loads | A/B testing, progressive rollout |

### Dynamic Import Pattern

```javascript
// Route-based: load component when route is visited
const Dashboard = lazy(() => import('./pages/Dashboard'));

// Component-based: load heavy library on interaction
const openEditor = async () => {
  const { Editor } = await import('./components/Editor');
  mountEditor(Editor);
};
```

### Code Splitting Targets

| Target | Threshold | Action |
|---|---|---|
| Initial JS bundle | > 200KB compressed | Split aggressively |
| Individual chunk | > 100KB compressed | Consider further splitting |
| Third-party dependency | > 50KB | Evaluate alternatives or lazy load |
| Total page JS | > 500KB compressed | Audit necessity of each dependency |

## Lazy Loading Patterns

### Component Lazy Loading

| Pattern | Implementation | Use Case |
|---|---|---|
| Route-level lazy | Dynamic import at router level | Every route after the initial one |
| Below-fold lazy | IntersectionObserver triggers import | Long scrolling pages |
| Interaction-triggered | Import on hover, click, or focus | Heavy widgets (chat, video, maps) |
| Conditional lazy | Import based on feature flag or user role | Admin panels, premium features |

### Image Lazy Loading

| Approach | Method | Browser Support |
|---|---|---|
| Native lazy loading | `loading="lazy"` attribute | All modern browsers |
| IntersectionObserver | JS-based, more control | All modern browsers |
| CSS `content-visibility` | Defers rendering of off-screen content | Chromium-based |

### Prefetching and Preloading

| Technique | When | Effect |
|---|---|---|
| `<link rel="prefetch">` | Idle time | Fetch resource for likely next navigation |
| `<link rel="preload">` | Immediately | Fetch critical resource for current page |
| `<link rel="modulepreload">` | Immediately | Preload JS module with dependency resolution |
| Route prefetch on hover | User hovers a link | Load the route chunk before click |
| Predictive prefetch | Based on analytics | Preload likely next pages |

## SEO Strategies for SPAs

### SEO Mitigation Options

| Strategy | How | Tradeoff |
|---|---|---|
| Pre-rendering | Generate static HTML at build time for known routes | Only works for routes known at build time |
| Dynamic rendering | Serve pre-rendered HTML to bots, SPA to users | Cloaking risk, maintenance burden |
| SSR for critical pages | Hybrid: SSR for landing/product pages, CSR for app | Architecture complexity |
| Meta framework migration | Move to Next.js, Nuxt, SvelteKit | Full SSR/SSG with SPA-like navigation |

### Search Engine JS Rendering

| Search Engine | JS Rendering Support |
|---|---|
| Google | Renders JS but with delay (hours to days for indexing) |
| Bing | Limited JS rendering |
| DuckDuckGo | Relies on Bing's index |
| Social crawlers (Twitter, Facebook) | No JS rendering (Open Graph tags must be in initial HTML) |

### Minimum SEO for SPAs

1. Set unique `<title>` and `<meta name="description">` per route (via document head management)
2. Use `history.pushState` for clean URLs (no hash routing)
3. Provide a sitemap.xml for all indexable routes
4. Include Open Graph and Twitter Card meta tags in server-rendered HTML or pre-rendered pages
5. Implement canonical URLs to prevent duplicate content

## Client-Side Performance Optimization

### Rendering Performance

| Technique | Effect |
|---|---|
| Virtualize long lists | Only render visible items (react-window, TanStack Virtual) |
| Debounce expensive renders | Avoid re-rendering on every keystroke |
| Memoize computed values | Prevent redundant calculations |
| Use CSS transforms for animations | Avoid layout/paint triggers |
| Batch DOM updates | Minimize reflows |
| Avoid forced synchronous layouts | Read layout properties before writing |

### Network Performance

| Technique | Effect |
|---|---|
| Request deduplication | Avoid redundant API calls for the same data |
| Stale-while-revalidate | Show cached data, refresh in background |
| Optimistic updates | Update UI before server confirms |
| Request batching | Combine multiple API calls into one |
| Compression (Brotli/gzip) | Reduce transfer size |
| CDN for static assets | Serve from nearest edge |

### Bundle Size Management

| Practice | Why |
|---|---|
| Analyze with bundlephobia or bundlewatch | Know what you ship |
| Tree-shake unused exports | Remove dead code |
| Replace heavy libraries with lighter alternatives | moment -> date-fns/dayjs, lodash -> native |
| Use `sideEffects: false` in package.json | Enable tree shaking for your code |
| Set size budgets in CI | Prevent bundle regression |

### Client-Side Data Caching

| Pattern | Implementation | Use Case |
|---|---|---|
| In-memory cache | TanStack Query, SWR, Apollo Client | API response caching with staleness |
| Service Worker cache | Cache API in SW | Offline-first, repeat visits |
| IndexedDB | Structured client-side storage | Large datasets, offline data |
| LocalStorage | Key-value string storage | Small config, user preferences |

## SPA Navigation Patterns

### Client-Side Routing

| Pattern | Characteristic |
|---|---|
| History API (`pushState`) | Clean URLs, SEO-friendly, requires server fallback |
| Hash routing (`#/path`) | No server config needed, not SEO-friendly |
| File-system routing | Convention-based (Next.js, Nuxt, SvelteKit) |

### Navigation Performance

| Technique | Effect |
|---|---|
| Route-level code splitting | Only load JS for the target route |
| Prefetch on link hover | Start loading before click |
| Skeleton screens during transition | Perceived instant navigation |
| Optimistic navigation | Show target layout before data loads |
| Back/forward cache | Restore previous page state from memory |
| View Transitions API | Animated transitions between navigations |
