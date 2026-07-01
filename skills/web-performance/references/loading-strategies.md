# Loading Strategies and Code Splitting

Sources: Grigorik (High Performance Browser Networking), Osmani (Learning JavaScript Design Patterns), Google web.dev loading documentation, Webpack/Vite/Rollup documentation

Covers: Static and dynamic imports, route-based splitting, import-on-interaction, import-on-visibility, resource hints (preload, prefetch, preconnect, modulepreload), and critical rendering path optimization.

## Import Strategy Decision Tree

| Context | Strategy | Mechanism |
| --- | --- | --- |
| Core app logic, always needed | Static import | `import { x } from 'mod'` |
| Entire route/page | Route-based split | Framework router + dynamic import |
| Below-fold component | Import on visibility | IntersectionObserver + dynamic import |
| Triggered by user action | Import on interaction | Event handler + dynamic import |
| Large library, single feature | Feature-based split | Dynamic import at usage point |
| Unlikely-needed future page | Prefetch | `<link rel="prefetch">` or router prefetch |

## Static Imports

The default. Bundler includes the module in the initial bundle.

```javascript
import { formatDate } from './utils/date';
import { Button } from './components/Button';
```

Use static imports for:
- App shell and layout components
- Routing infrastructure
- Authentication logic
- Above-fold UI components
- Tiny utilities (< 2 KB)

## Dynamic Imports

Create separate chunks loaded on demand. Return a Promise.

```javascript
// Basic dynamic import
const module = await import('./heavy-feature');
module.init();

// With named exports
const { Chart } = await import('./Chart');

// Error handling
try {
  const { editor } = await import('./CodeEditor');
  editor.mount(container);
} catch (err) {
  showFallback('Editor failed to load');
}
```

### Chunk Naming (Webpack)

```javascript
// Named chunks for debugging and caching
const Chart = await import(/* webpackChunkName: "chart" */ './Chart');

// Prefetch hint (load during idle)
const Analytics = await import(/* webpackPrefetch: true */ './Analytics');

// Preload hint (load in parallel with current chunk)
const Modal = await import(/* webpackPreload: true */ './Modal');
```

### Chunk Naming (Vite/Rollup)

Vite uses `manualChunks` in the Rollup config:

```javascript
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['recharts', 'd3-scale'],
        },
      },
    },
  },
};
```

## Route-Based Code Splitting

Every route becomes its own chunk. The router loads the chunk when the user navigates.

### Generic Pattern (Framework-Agnostic)

```javascript
const routes = {
  '/': () => import('./pages/Home'),
  '/dashboard': () => import('./pages/Dashboard'),
  '/settings': () => import('./pages/Settings'),
  '/reports': () => import('./pages/Reports'),
};

async function navigate(path) {
  const loader = routes[path];
  if (!loader) return show404();
  const { default: Page } = await loader();
  render(Page);
}
```

### Prefetching Next Routes

Prefetch likely next pages during idle time:

```javascript
function prefetchRoute(path) {
  const loader = routes[path];
  if (loader) loader(); // Trigger fetch, cache the promise
}

// Prefetch on link hover
document.querySelectorAll('a[data-route]').forEach(link => {
  link.addEventListener('mouseenter', () => {
    prefetchRoute(link.dataset.route);
  }, { once: true });
});
```

## Import on Interaction

Load code only when the user triggers an action. Ideal for modals, dropdowns, rich editors, and settings panels.

```javascript
// Load a modal on button click
document.getElementById('open-editor').addEventListener('click', async () => {
  const { CodeEditor } = await import('./CodeEditor');
  const editor = new CodeEditor();
  editor.mount(document.getElementById('editor-container'));
}, { once: true });
```

### Hover-Triggered Preloading

Start loading on hover, mount on click. Reduces perceived latency.

```javascript
let editorPromise = null;

button.addEventListener('pointerenter', () => {
  editorPromise = editorPromise || import('./CodeEditor');
}, { once: true });

button.addEventListener('click', async () => {
  const { CodeEditor } = await editorPromise || import('./CodeEditor');
  new CodeEditor().mount(container);
});
```

## Import on Visibility

Load components when they scroll into view. Ideal for below-fold content, image galleries, charts, and comment sections.

```javascript
function loadOnVisible(element, loader) {
  const observer = new IntersectionObserver(
    async (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          observer.unobserve(entry.target);
          const module = await loader();
          module.default.mount(entry.target);
        }
      }
    },
    { rootMargin: '200px' } // Start loading 200px before visible
  );
  observer.observe(element);
}

// Usage
loadOnVisible(
  document.getElementById('chart-container'),
  () => import('./HeavyChart')
);
```

### rootMargin Strategy

| Content Type | rootMargin | Rationale |
| --- | --- | --- |
| Images | 200-300px | Start decoding before viewport |
| Heavy components (charts, editors) | 400-600px | Extra time for JS parse + init |
| Below-fold sections | 100px | Minimal overhead |
| Infinite scroll items | 500-1000px | Prefetch next batch early |

## Resource Hints

### Preload

Forces immediate high-priority fetch. Use for resources needed in the current page that the browser discovers late.

```html
<!-- LCP image -->
<link rel="preload" as="image" href="/hero.webp"
      imagesrcset="/hero-400.webp 400w, /hero-800.webp 800w"
      imagesizes="(max-width: 600px) 400px, 800px">

<!-- Critical font -->
<link rel="preload" as="font" type="font/woff2"
      href="/fonts/main.woff2" crossorigin>

<!-- Critical CSS loaded async -->
<link rel="preload" as="style" href="/above-fold.css">
```

**Warnings:**
- Preload too many resources and they compete, slowing everything.
- Chrome warns if a preloaded resource is not used within 3 seconds.
- Limit preloads to 2-3 critical resources maximum.

### Prefetch

Low-priority fetch for resources likely needed on the next navigation.

```html
<!-- Next page JS bundle -->
<link rel="prefetch" href="/dashboard-chunk.js">

<!-- Next page data -->
<link rel="prefetch" href="/api/dashboard-data" as="fetch" crossorigin>
```

Prefetch does not execute the resource. It only caches it. Execution happens when the resource is actually requested.

### Preconnect

Establishes connection (DNS + TCP + TLS) to a third-party origin before it is needed.

```html
<!-- CDN for images -->
<link rel="preconnect" href="https://images.cdn.com" crossorigin>

<!-- API server -->
<link rel="preconnect" href="https://api.example.com" crossorigin>

<!-- Analytics (lower priority, use dns-prefetch) -->
<link rel="dns-prefetch" href="https://analytics.example.com">
```

**Limit preconnect to 2-4 origins.** Each connection consumes CPU and memory. Use `dns-prefetch` for less critical origins.

### Modulepreload

Like preload, but for ES modules. Fetches, parses, and compiles the module and its dependencies.

```html
<link rel="modulepreload" href="/app.js">
<link rel="modulepreload" href="/vendor.js">
```

Use for critical-path ES modules in applications using native ESM or Vite.

## Critical Rendering Path

The sequence: HTML parse -> DOM construction -> CSS parse -> CSSOM construction -> Render tree -> Layout -> Paint.

### Render-Blocking Resources

| Resource | Default Behavior | Optimization |
| --- | --- | --- |
| `<link rel="stylesheet">` | Blocks rendering | Inline critical CSS, load rest async |
| `<script>` (no attribute) | Blocks parsing + rendering | Add `defer` or `async` |
| `<script defer>` | Defers execution until DOM ready | Maintains order, does not block parsing |
| `<script async>` | Executes as soon as downloaded | No order guarantee, does not block parsing |
| `<script type="module">` | Deferred by default | Same as `defer` behavior |

### Critical CSS Extraction

Inline the CSS needed for above-fold content. Load the rest asynchronously.

```html
<head>
  <!-- Inline critical styles -->
  <style>
    /* Only above-fold layout and typography */
    body { margin: 0; font-family: system-ui; }
    .header { height: 64px; display: flex; }
    .hero { min-height: 50vh; }
  </style>

  <!-- Load full stylesheet asynchronously -->
  <link rel="preload" as="style" href="/styles.css"
        onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="/styles.css"></noscript>
</head>
```

### Script Loading Strategy

| Script Type | Attribute | When to Use |
| --- | --- | --- |
| App bootstrap | `<script type="module">` or `defer` | Main application entry point |
| Non-critical feature | `async` + conditional | Analytics, A/B testing |
| Third-party (critical) | `async` | Payment SDK, auth provider |
| Third-party (non-critical) | Manual delayed load | Chat widget, feedback tool |
| Inline handler | None (must be sync) | Avoid; move to external file with `defer` |

## Waterfall Analysis

When debugging loading performance, read the network waterfall:

1. HTML document arrives (TTFB).
2. Parser discovers `<link>` and `<script>` tags -> initiates fetches.
3. CSS blocks rendering until CSSOM is built.
4. `defer` scripts execute after DOM is ready.
5. `DOMContentLoaded` fires.
6. Images, fonts, and async resources load.
7. `load` event fires.

**Optimization principle:** Push critical resources as close to step 2 as possible. Defer everything else to step 6 or later.
