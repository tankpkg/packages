# Core Web Vitals

Sources: Google Web Vitals documentation (2024-2026), Chromium performance team publications, web.dev, CrUX methodology documentation

Covers: LCP, INP, and CLS measurement, diagnosis, and optimization. Field data vs lab data interpretation. Threshold targets and regression prevention.

## The Three Vitals

| Metric | Full Name | Measures | Good | Needs Work | Poor |
| --- | --- | --- | --- | --- | --- |
| LCP | Largest Contentful Paint | Loading performance | < 2.5s | 2.5-4.0s | > 4.0s |
| INP | Interaction to Next Paint | Responsiveness | < 200ms | 200-500ms | > 500ms |
| CLS | Cumulative Layout Shift | Visual stability | < 0.1 | 0.1-0.25 | > 0.25 |

All thresholds are measured at the 75th percentile of page loads across both mobile and desktop.

## Field Data vs Lab Data

| Aspect | Field (RUM) | Lab (Synthetic) |
| --- | --- | --- |
| Source | Real users (CrUX, RUM providers) | Controlled test (Lighthouse, WebPageTest) |
| Variability | High (devices, networks, geography) | Low (consistent environment) |
| Use for | Pass/fail ranking decisions | Debugging, development iteration |
| INP accuracy | Accurate (real interactions) | Simulated only (TBT as proxy) |
| CLS accuracy | Full session (accurate) | Single page load (partial) |

Always prioritize field data for performance assessment. Use lab data for debugging root causes.

### Measurement Tools

| Tool | Type | Best For |
| --- | --- | --- |
| Chrome UX Report (CrUX) | Field | Origin-level real-user data, BigQuery analysis |
| `web-vitals` JS library | Field | Custom RUM collection, per-page granularity |
| Lighthouse | Lab | Development auditing, CI integration |
| Chrome DevTools Performance | Lab | Frame-by-frame debugging, long task identification |
| WebPageTest | Lab | Waterfall analysis, filmstrip comparison, third-party impact |
| PageSpeed Insights | Both | Quick field + lab snapshot for any URL |

### Implementing RUM Collection

```javascript
import { onLCP, onINP, onCLS } from 'web-vitals';

function sendToAnalytics(metric) {
  const body = JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating,
    delta: metric.delta,
    id: metric.id,
    navigationType: metric.navigationType,
    url: location.href,
  });
  // Use sendBeacon for reliability during page unload
  navigator.sendBeacon('/analytics', body);
}

onLCP(sendToAnalytics);
onINP(sendToAnalytics);
onCLS(sendToAnalytics);
```

## Largest Contentful Paint (LCP)

### What Counts as LCP

- `<img>` elements (including inside `<picture>`)
- `<image>` inside SVG
- `<video>` poster image or first displayed frame
- Block-level elements with background images via `url()`
- Text blocks (`<p>`, `<h1>`, etc.) rendered with web fonts

### LCP Breakdown

Per Google's web.dev decomposition model:

LCP = TTFB + Resource Load Delay + Resource Load Time + Element Render Delay

| Sub-metric | Cause | Optimization |
| --- | --- | --- |
| TTFB | Slow server, no CDN, no caching | CDN, edge rendering, server caching, preconnect |
| Resource Load Delay | Late discovery of LCP resource | `<link rel="preload">`, inline critical CSS, avoid JS-dependent image loading |
| Resource Load Time | Large image, slow network | Compress images, serve modern formats (AVIF/WebP), use responsive `srcset` |
| Element Render Delay | Render-blocking JS/CSS | Defer non-critical JS, inline critical CSS, `font-display: swap` |

### LCP Optimization Checklist

1. Identify the LCP element: DevTools > Performance panel > Timings track > LCP marker.
2. Ensure the LCP resource is discoverable in the HTML source (not injected by JS).
3. Add `fetchpriority="high"` to the LCP image.
4. Remove `loading="lazy"` from above-fold images.
5. Preload the LCP image if it is a CSS background or loaded via JS:

```html
<link rel="preload" as="image" href="/hero.webp"
      imagesrcset="/hero-400.webp 400w, /hero-800.webp 800w"
      imagesizes="100vw">
```

6. Inline critical CSS (above-fold styles) in `<head>`. Load remaining CSS asynchronously.
7. Use `font-display: swap` or `font-display: optional` for web fonts.
8. Preconnect to required origins:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://cdn.example.com" crossorigin>
```

### Common LCP Mistakes

| Mistake | Impact | Fix |
| --- | --- | --- |
| `loading="lazy"` on hero image | Delays LCP by deferring load | Remove lazy, add `fetchpriority="high"` |
| LCP image set via JS or CSS | Browser cannot discover early | Use `<img>` in HTML, or `<link rel="preload">` |
| Render-blocking Google Fonts | Blocks text rendering | Use `font-display: swap`, preconnect, or self-host |
| Full-page client-side rendering | Empty HTML until JS executes | SSR, SSG, or streaming HTML |
| Massive uncompressed hero image | Slow download | Compress, serve WebP/AVIF, use `srcset` |

## Interaction to Next Paint (INP)

### How INP Works

INP measures the latency from user input (click, tap, keypress) to the next visual update. It tracks all interactions during the page lifecycle and reports the worst (or near-worst) interaction latency.

Per Google's web.dev decomposition model:

INP = Input Delay + Processing Time + Presentation Delay

| Sub-metric | Cause | Optimization |
| --- | --- | --- |
| Input Delay | Main thread busy with other work | Break long tasks, yield to main thread |
| Processing Time | Slow event handler | Optimize handler logic, defer non-visual work |
| Presentation Delay | Expensive layout/paint after handler | Reduce DOM size, avoid forced reflow, use `content-visibility` |

### INP Optimization Strategies

1. **Identify slow interactions:** DevTools > Performance > record an interaction > inspect "Interactions" track.
2. **Break long tasks (>50ms):** Use `scheduler.yield()` or manual yielding:

```javascript
async function processLargeList(items) {
  for (let i = 0; i < items.length; i++) {
    processItem(items[i]);
    if (i % 100 === 0) {
      // Yield to let browser handle pending input
      await new Promise(resolve => setTimeout(resolve, 0));
    }
  }
}
```

3. **Move computation off main thread:** Use Web Workers for data processing, sorting, filtering.
4. **Debounce high-frequency handlers:** Especially `input`, `scroll`, `mousemove`.
5. **Use `requestAnimationFrame` for visual updates:** Never modify DOM in response to events without batching.
6. **Reduce DOM size:** Target < 1,500 elements. Deep DOM trees increase style recalculation cost.
7. **Use `content-visibility: auto`** on off-screen sections to skip rendering work.

### Long Task Detection

```javascript
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.warn('Long task detected:', entry.duration, 'ms', entry);
  }
});
observer.observe({ type: 'longtask', buffered: true });
```

## Cumulative Layout Shift (CLS)

### What Causes Layout Shifts

| Cause | Frequency | Fix |
| --- | --- | --- |
| Images without dimensions | Very common | Always set `width` and `height` attributes |
| Ads/embeds without reserved space | Common | Use `min-height` or aspect-ratio containers |
| Dynamically injected content | Common | Reserve space before injection, use `content-visibility` |
| Web fonts causing text reflow | Common | `font-display: optional`, size-adjust, font metric overrides |
| Late-loading CSS | Occasional | Inline critical CSS, avoid CSS-in-JS flash |
| Animations using layout properties | Occasional | Animate `transform`/`opacity` only, never `top`/`left`/`width`/`height` |

### CLS Debugging

1. Open DevTools > Performance panel > enable "Layout Shifts" checkbox.
2. Record a page load. Examine blue markers in the timeline.
3. Click a shift to see the affected elements highlighted.
4. Use the Layout Instability API for production monitoring:

```javascript
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (!entry.hadRecentInput) {
      console.log('Layout shift:', entry.value, entry.sources);
    }
  }
});
observer.observe({ type: 'layout-shift', buffered: true });
```

### CLS Prevention Patterns

Reserve space for dynamic content:

```css
/* Aspect ratio container for images */
.image-container {
  aspect-ratio: 16 / 9;
  width: 100%;
  background: #f0f0f0; /* placeholder color */
}

/* Fixed-height ad slot */
.ad-slot {
  min-height: 250px;
  contain: layout;
}

/* Font metric override to prevent reflow */
@font-face {
  font-family: 'CustomFont';
  src: url('/font.woff2') format('woff2');
  font-display: optional;
  size-adjust: 105%;
  ascent-override: 90%;
  descent-override: 20%;
}
```

## Performance Regression Prevention

### CI Integration

Run Lighthouse in CI on every PR. Fail the build when Core Web Vitals budgets are exceeded.

```yaml
# Example: Lighthouse CI budget
- url: https://staging.example.com
  budgets:
    - metric: largest-contentful-paint
      budget: 2500
    - metric: cumulative-layout-shift
      budget: 0.1
    - metric: total-blocking-time
      budget: 200
    - metric: interactive
      budget: 3500
```

### Monitoring Strategy

| Layer | Tool | Frequency |
| --- | --- | --- |
| Real User Monitoring | `web-vitals` + analytics pipeline | Every page load |
| Synthetic monitoring | Lighthouse CI, WebPageTest | Every deploy + hourly |
| CrUX dashboard | BigQuery or PageSpeed Insights | Weekly review |
| Alerting | Custom thresholds on RUM p75 | Real-time |

Set alerts at the 75th percentile. Investigate when any vital crosses from "good" to "needs improvement."
