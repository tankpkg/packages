---
name: "@tank/web-performance"
description: |
  Web performance optimization for modern JavaScript applications. Covers
  Core Web Vitals measurement and diagnosis (LCP, INP, CLS), loading
  strategies (static/dynamic import, route-based splitting, import-on-
  interaction, import-on-visibility), bundle optimization (tree-shaking,
  code splitting, chunk strategies, bundle analysis), resource hints
  (preload, prefetch, preconnect, modulepreload), runtime performance
  (DOM batch reads/writes, requestAnimationFrame, Web Workers, virtual
  lists, event delegation, debounce/throttle), network optimization
  (compression, HTTP/2+, caching headers, CDN, service workers), image
  optimization (modern formats, responsive images, lazy loading, LQIP),
  and third-party script management. Framework-agnostic.

  Synthesizes Grigorik (High Performance Browser Networking), Wagner
  (Web Performance in Action), Google Web Vitals documentation, Chromium
  performance guides, web.dev, MDN Web Docs.

  Trigger phrases: "web performance", "Core Web Vitals", "LCP", "INP",
  "CLS", "page speed", "slow page", "Lighthouse score", "bundle size",
  "code splitting", "tree shaking", "lazy loading", "preload", "prefetch",
  "cache strategy", "service worker", "image optimization", "web worker",
  "runtime performance", "layout shift", "first contentful paint",
  "loading performance", "bundle analysis", "performance budget",
  "third party scripts", "resource hints", "HTTP caching"
---

# Web Performance

Measure first. Fix the bottleneck. Ship smaller, faster, leaner.

## Core Philosophy

1. **Measure before optimizing.** Lighthouse, CrUX, and DevTools profiling dictate priorities, not hunches.
2. **Ship less JavaScript.** Every kilobyte costs parse time, compile time, and execution time on every device.
3. **Critical path is king.** Identify what blocks first paint and first interaction. Eliminate everything else from that path.
4. **Perceived performance beats raw speed.** Skeleton screens, optimistic updates, and progressive rendering make 3s feel like 1s.
5. **Performance is a budget, not a task.** Set thresholds, automate enforcement, fail the build when budgets break.

## Quick-Start: Symptom to Fix

### "LCP is slow (>2.5s)"

1. Identify the LCP element (DevTools > Performance > Timings).
2. If image: add `fetchpriority="high"`, ensure no lazy-loading, use responsive `srcset`.
3. If text: eliminate render-blocking CSS/fonts. Inline critical CSS. Use `font-display: swap`.
4. If server-slow: check TTFB. Preconnect to origins. Consider CDN or edge rendering.
5. -> See `references/core-web-vitals.md`

### "INP is high (>200ms)"

1. Profile with DevTools > Performance. Find long tasks (>50ms).
2. Break long tasks: `yield()` via `scheduler.yield()` or `setTimeout(0)`.
3. Move heavy computation to Web Workers.
4. Debounce rapid-fire input handlers. Use `requestAnimationFrame` for visual updates.
5. -> See `references/runtime-performance.md`

### "CLS is bad (>0.1)"

1. Set explicit `width`/`height` on images and videos.
2. Reserve space for dynamic content (ads, embeds, lazy-loaded sections).
3. Avoid injecting content above the fold after initial render.
4. Use `contain: layout` on containers with dynamic children.
5. -> See `references/core-web-vitals.md`

### "Bundle is too large"

1. Run bundle analyzer (`webpack-bundle-analyzer`, `vite-bundle-visualizer`, `source-map-explorer`).
2. Identify largest chunks. Apply dynamic `import()` for below-fold and interaction-gated features.
3. Audit dependencies: replace heavy libraries (moment -> date-fns, lodash -> lodash-es or native).
4. Verify tree-shaking: use ESM imports, check `sideEffects` in package.json.
5. -> See `references/bundle-optimization.md`

### "Third-party scripts block rendering"

1. Audit all third-party scripts. Move non-critical to `async` or `defer`.
2. Implement facades for heavy embeds (YouTube, chat widgets, maps).
3. Delay non-essential scripts until after user interaction or idle.
4. -> See `references/network-and-caching.md`

## Loading Strategy Decision Tree

| Signal | Strategy |
| --- | --- |
| Above-fold, critical path | Static import, inline critical CSS |
| Below-fold component | `import()` on visibility (IntersectionObserver) |
| Triggered by user action (modal, dropdown) | `import()` on interaction (click/hover) |
| Entire route/page | Route-based code splitting |
| Large library used in one feature | Dynamic import, separate chunk |
| Third-party embed (YouTube, maps) | Facade pattern with lazy load |

## Resource Hint Decision Tree

| Scenario | Hint | Example |
| --- | --- | --- |
| LCP image or critical font | `<link rel="preload">` | `<link rel="preload" as="image" href="hero.webp">` |
| Next-page navigation likely | `<link rel="prefetch">` | `<link rel="prefetch" href="/dashboard.js">` |
| Third-party origin needed soon | `<link rel="preconnect">` | `<link rel="preconnect" href="https://cdn.example.com">` |
| ES module in critical path | `<link rel="modulepreload">` | `<link rel="modulepreload" href="/app.js">` |
| Many possible next origins | `<link rel="dns-prefetch">` | `<link rel="dns-prefetch" href="https://api.example.com">` |

See `references/loading-strategies.md` for import patterns and splitting techniques.

## Image Format Decision Tree

| Content Type | Format | Fallback |
| --- | --- | --- |
| Photographic content | AVIF > WebP > JPEG | `<picture>` with source sets |
| Graphics, logos, icons | SVG (vector) or WebP | PNG-8 for simple graphics |
| Animated content | Animated WebP or short video | GIF (last resort) |
| Thumbnails / placeholders | LQIP (blurred tiny image) or CSS gradient | Solid color placeholder |

See `references/image-optimization.md` for responsive images, lazy loading, and LQIP patterns.

## Performance Budget Template

| Metric | Target | Action |
| --- | --- | --- |
| LCP | < 2.5s (p75) | Block deploy if exceeded |
| INP | < 200ms (p75) | Alert, investigate |
| CLS | < 0.1 (p75) | Block deploy if exceeded |
| Total JS (compressed) | < 200 KB | Fail CI build |
| Total CSS (compressed) | < 50 KB | Warn in CI |
| Largest single chunk | < 100 KB | Warn, suggest splitting |
| Hero image | < 200 KB | Warn, suggest compression |

## Anti-Patterns

| Anti-Pattern | Impact | Fix |
| --- | --- | --- |
| Importing entire lodash | +70 KB bundle | Cherry-pick or use `lodash-es` |
| Synchronous `<script>` in `<head>` | Blocks parsing | Move to body end, add `defer` |
| Unoptimized hero image (5 MB PNG) | LCP > 5s | Compress, serve WebP/AVIF, use `srcset` |
| Layout reads interleaved with writes | Forced synchronous layout | Batch reads then writes, use `rAF` |
| No `width`/`height` on images | CLS spikes | Always set intrinsic dimensions |
| Polling instead of event-driven | Wasted CPU, battery drain | Use MutationObserver, IntersectionObserver, SSE |
| Bundling unused polyfills | +30-50 KB | Use `browserslist` and differential serving |
| Inlining everything | Defeats caching | Inline only critical CSS; externalize the rest |

## Reference Index

| File | Contents |
| --- | --- |
| `references/core-web-vitals.md` | LCP, INP, CLS measurement, diagnosis workflows, optimization patterns, field vs lab data |
| `references/loading-strategies.md` | Static/dynamic imports, route splitting, import-on-interaction, import-on-visibility, resource hints |
| `references/bundle-optimization.md` | Tree-shaking, code splitting, chunk strategies, bundle analysis tools, dependency auditing |
| `references/runtime-performance.md` | DOM batching, requestAnimationFrame, Web Workers, virtual lists, event delegation, long tasks |
| `references/network-and-caching.md` | Compression, HTTP/2+, caching headers, CDN strategy, service workers, third-party script management |
| `references/image-optimization.md` | Modern formats (AVIF, WebP), responsive images, lazy loading, LQIP, video replacement, CDN transforms |
