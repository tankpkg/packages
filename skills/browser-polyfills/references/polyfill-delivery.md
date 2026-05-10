# Polyfill Delivery and Feature Detection

Sources: polyfill.io incident analysis (2024), Cloudflare security blog, core-js documentation, Next.js bundle optimization guides

---

## 1. polyfill.io Supply Chain Attack (February 2024)

In February 2024, `polyfill.io` was acquired by Funnull, a Chinese CDN company. The service began injecting malicious JavaScript into responses served to end users. Over 100,000 websites were affected. The injected code performed redirects, exfiltrated data, and executed arbitrary scripts in visitors' browsers.

The attack exploited a common pattern: a single `<script>` tag pointing to an external CDN, trusted indefinitely, never audited. Because polyfill bundles are generated dynamically per request, static SRI hashes cannot protect against this class of attack.

Remove all references to `polyfill.io` immediately.

### Detecting polyfill.io in Your Codebase

```bash
# Find all references across source files
grep -rn "polyfill\.io" . --include="*.html" --include="*.tsx" --include="*.ts" \
  --include="*.js" --include="*.jsx" --include="*.json" --include="*.env*"

# Check Next.js config and custom Document
grep -rn "polyfill\.io" . --include="*.config.*" --include="_document.*"
```

### Safe Alternatives

| Option | URL / Method | Notes |
|--------|-------------|-------|
| Cloudflare cdnjs mirror | `https://cdnjs.cloudflare.com/polyfill/v3/polyfill.min.js` | Drop-in replacement, same query params |
| Fastly mirror | `https://polyfill-fastly.net/v3/polyfill.min.js` | Maintained by original author |
| Self-hosting | Bundle with your app | Most secure; no external dependency |
| Remove entirely | Target modern browsers | Best option if browserslist is modern |

For most Next.js projects, remove the CDN script tag entirely and rely on core-js via SWC. The CDN approach predates bundler-integrated polyfilling.

---

## 2. Feature Detection Patterns (JavaScript)

Feature detection checks whether a browser API exists before using or loading a polyfill. This avoids shipping unnecessary code to browsers that already support the feature natively.

### typeof and in Checks

```typescript
// typeof: safe for globals that may not exist (accessing undefined globals throws)
if (typeof window !== 'undefined') { /* client-only code */ }
if (typeof requestIdleCallback !== 'undefined') { /* ... */ }

// in operator: check properties on known objects
if ('IntersectionObserver' in window) { /* ... */ }
if ('ResizeObserver' in window) { /* ... */ }
if ('serviceWorker' in navigator) { /* ... */ }
```

### try/catch for Behavioral Checks

```typescript
function supportsPassiveEvents(): boolean {
  let supported = false;
  try {
    const opts = Object.defineProperty({}, 'passive', { get() { supported = true; } });
    window.addEventListener('test', null as any, opts);
    window.removeEventListener('test', null as any, opts);
  } catch { /* not supported */ }
  return supported;
}
```

### Dynamic import() with Runtime Detection

Load polyfills only when needed, keeping the main bundle lean:

```typescript
// polyfills/index.ts
export async function loadPolyfills(): Promise<void> {
  if (typeof window === 'undefined') return;

  const polyfills: Promise<unknown>[] = [];

  if (!('IntersectionObserver' in window))
    polyfills.push(import('intersection-observer'));

  if (!('ResizeObserver' in window))
    polyfills.push(import('@juggle/resize-observer').then(({ ResizeObserver }) => {
      window.ResizeObserver = ResizeObserver;
    }));

  if (!('fetch' in window))
    polyfills.push(import('whatwg-fetch'));

  if (!('AbortController' in window))
    polyfills.push(import('abortcontroller-polyfill/dist/abortcontroller-polyfill-only'));

  if (typeof TextEncoder === 'undefined')
    polyfills.push(import('fast-text-encoding'));

  await Promise.all(polyfills);
}
```

Call this before rendering. In App Router, use `instrumentation-client.ts`:

```typescript
// instrumentation-client.ts (root of project)
// This file runs top-level code before hydration — no export needed.
import { loadPolyfills } from './polyfills';
loadPolyfills();
```

In Pages Router, call it at the top of `_app.tsx` before the component renders.

---

## 3. Feature Detection Patterns (CSS)

### @supports Rule

```css
@supports (display: grid) {
  .container { display: grid; grid-template-columns: repeat(3, 1fr); }
}

/* Fallback when gap is unsupported in flexbox */
@supports not (gap: 1rem) {
  .flex-container > * + * { margin-left: 1rem; }
}

/* iOS Safari detection via proprietary property */
@supports (-webkit-touch-callout: none) {
  .full-height { height: -webkit-fill-available; }
}
```

### CSS.supports() in JavaScript

```typescript
if (CSS.supports('display', 'grid')) { /* grid available */ }
if (CSS.supports('(display: grid) and (gap: 1rem)')) { /* both supported */ }
const isIOS = CSS.supports('-webkit-touch-callout', 'none');
```

### iOS 100vh Fix

The `100vh` unit includes browser chrome on iOS Safari, causing layout overflow:

```css
.full-screen { height: 100vh; } /* fallback */

@supports (-webkit-touch-callout: none) {
  .full-screen { height: -webkit-fill-available; }
}

/* For Next.js root element */
@supports (-webkit-touch-callout: none) {
  #__next { min-height: -webkit-fill-available; }
}
```

---

## 4. core-js Configuration

### Usage-Based vs Entry-Based Polyfilling

**mode: "usage"** (recommended) — The compiler scans your source and injects only polyfills for APIs you actually use. A file calling `Array.prototype.flat` gets the flat polyfill; files that do not use it are unaffected.

**mode: "entry"** — A single `import 'core-js/stable'` at your entry point is replaced with every polyfill your browserslist requires. Simpler but ships more code.

Next.js with SWC uses usage-based polyfilling automatically. Do not add `import 'core-js/stable'` to your code — it will result in duplicate polyfills.

### Tree-Shaking: Import Specific Features

When importing core-js manually (outside SWC's automatic injection):

```typescript
// Avoid: imports everything
import 'core-js/stable';

// Prefer: imports only what you need
import 'core-js/features/array/flat';
import 'core-js/features/promise/all-settled';
import 'core-js/features/object/from-entries';
```

`core-js/features/` imports the polyfill plus dependencies. `core-js/modules/` imports only the exact module — use this only when you know the full dependency graph.

---

## 5. Module/NoModule Differential Serving

Modern browsers support `<script type="module">`. Legacy browsers do not. This enables differential serving: modern JavaScript for modern browsers, a larger transpiled bundle for legacy browsers.

```html
<!-- Modern browsers execute this; legacy browsers ignore it -->
<script type="module" src="/modern-bundle.js"></script>

<!-- Legacy browsers execute this; modern browsers skip it -->
<script nomodule src="/legacy-bundle.js"></script>
```

The legacy bundle includes full ES5 transpilation and all core-js polyfills. The modern bundle ships ES2017+ syntax with minimal polyfills — typically 20-40% smaller.

Next.js handles this automatically. `@next/polyfill-nomodule` is injected as a `nomodule` script at build time. No manual configuration is required.

---

## 6. Bundle Impact Analysis

### Measuring Polyfill Weight

```bash
npm install --save-dev @next/bundle-analyzer
```

```javascript
// next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});
module.exports = withBundleAnalyzer({ /* your config */ });
```

```bash
ANALYZE=true npm run build
```

In the treemap, look for `core-js` modules, large polyfill packages, and duplicate polyfills from multiple packages.

### Typical Savings from Narrowing browserslist

| Change | Approximate Savings |
|--------|-------------------|
| Drop IE 11 support | 30–60 KiB gzipped |
| Raise minimum Chrome from 60 to 111 | 10–15 KiB gzipped |
| Raise minimum Safari from 12 to 16.4 | 5–10 KiB gzipped |
| Remove unused polyfill packages | 2–20 KiB each |

The Next.js 15+ default (`chrome 111, edge 111, firefox 111, safari 16.4`) eliminates most core-js polyfills while covering the vast majority of active users.

### Lighthouse Audit

Lighthouse includes "Avoid serving legacy JavaScript to modern browsers." It flags polyfills for natively supported features and unnecessary transpilation transforms.

```bash
npx lighthouse https://your-site.com --only-audits=legacy-javascript --output=json
```

The audit output lists specific polyfills and their estimated byte savings. Use this list to identify which browserslist targets or polyfill imports to remove.

---

## 7. Polyfill Package Recommendations

| Package | npm install | Purpose | Import pattern | Bundle size |
|---------|-------------|---------|----------------|-------------|
| `core-js` | `npm i core-js` | ES2015–ES2023 language features | Auto via SWC, or `import 'core-js/features/...'` | 0–30 KiB (usage-based) |
| `intersection-observer` | `npm i intersection-observer` | IntersectionObserver API | `import 'intersection-observer'` | ~3 KiB gzipped |
| `@juggle/resize-observer` | `npm i @juggle/resize-observer` | ResizeObserver API | `import { ResizeObserver } from '@juggle/resize-observer'` | ~4 KiB gzipped |
| `whatwg-fetch` | `npm i whatwg-fetch` | fetch API (browser only) | `import 'whatwg-fetch'` | ~2 KiB gzipped |
| `cross-fetch` | `npm i cross-fetch` | fetch API (browser + Node) | `import 'cross-fetch/polyfill'` | ~5 KiB gzipped |
| `abortcontroller-polyfill` | `npm i abortcontroller-polyfill` | AbortController | `import 'abortcontroller-polyfill/dist/abortcontroller-polyfill-only'` | ~1 KiB gzipped |
| `fast-text-encoding` | `npm i fast-text-encoding` | TextEncoder / TextDecoder | `import 'fast-text-encoding'` | ~3 KiB gzipped |
| `smoothscroll-polyfill` | `npm i smoothscroll-polyfill` | CSS scroll-behavior: smooth | `import smoothscroll from 'smoothscroll-polyfill'; smoothscroll.polyfill()` | ~2 KiB gzipped |

For ES language features, rely on core-js via SWC. For Web APIs not in core-js, use the packages above with runtime feature detection.

---

## 8. Security Best Practices

### Content Security Policy

If loading any polyfill from an external CDN, restrict it with a strict CSP:

```
Content-Security-Policy: script-src 'self' https://cdnjs.cloudflare.com;
```

Avoid `'unsafe-inline'` and `'unsafe-eval'`. For Next.js inline scripts, use nonce-based CSP:

```
Content-Security-Policy: script-src 'self' 'nonce-{random}' https://cdnjs.cloudflare.com;
```

### Subresource Integrity

SRI allows browsers to verify a fetched resource has not been tampered with:

```html
<script
  src="https://cdnjs.cloudflare.com/polyfill/v3/polyfill.min.js?features=IntersectionObserver"
  integrity="sha384-{hash}"
  crossorigin="anonymous"
></script>
```

**Limitation:** Dynamic polyfill services generate responses per `User-Agent`, so a single hash cannot cover all responses. SRI is most effective for static, versioned files. For dynamic services, generate the bundle at build time, commit it, and serve it as a static file.

### Dependency Audits

```bash
# Run in CI pipeline
npm audit --audit-level=moderate
```

Additional supply chain hygiene:

- Pin exact versions of polyfill packages in `package.json`
- Review changelogs before upgrading polyfill packages
- Monitor for ownership changes on packages you depend on (tools like `socket.dev` flag suspicious behavior)

core-js is maintained by a single developer — a supply chain concentration risk. Mitigate it by using SWC's built-in core-js integration, which pins a specific version, rather than installing and upgrading core-js independently.

### Prefer Self-Hosting

The safest polyfill delivery strategy is no external scripts. Bundle polyfills with your application:

1. Install polyfill packages as npm dependencies
2. Import them via runtime feature detection
3. Let Next.js bundle them with your application code
4. Serve everything from your own origin

This eliminates CDN availability risk, supply chain injection risk, and the need for CSP exceptions for external origins.
