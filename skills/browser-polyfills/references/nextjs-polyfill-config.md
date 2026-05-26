# Next.js Polyfill Configuration

Sources: Next.js documentation (2026), vercel/next.js source code, production Next.js codebases

---

## 1. Next.js Built-in Polyfills

Next.js automatically injects a small set of polyfills for every application. These run before any application code and are deduplicated — if your bundle already includes the same polyfill, Next.js suppresses the duplicate.

| Polyfill | Scope | Deduplication key |
|----------|-------|-------------------|
| `fetch()` | Browser + Node.js (server components) | `whatwg-fetch` / `node-fetch` |
| `URL` | Browser + Node.js | `whatwg-url` |
| `Object.assign` | Browser | `object-assign` |

Deduplication works by checking whether the global already exists at runtime. For `fetch`, Next.js checks `typeof globalThis.fetch === 'function'` before patching. This means you do not need to import `whatwg-fetch` manually — doing so wastes bytes.

What Next.js does **not** auto-polyfill:

- `requestIdleCallback` — absent from all Safari versions
- `Promise.withResolvers` — Safari 17.4+ only
- `Set` methods (`union`, `intersection`, `difference`) — Safari 17.0+
- `Temporal` API — not in Safari as of 2026
- `AbortSignal.timeout()` — partial Safari support
- `View Transitions API` — Safari 18.0+, Firefox 144+

These require explicit polyfills loaded through one of the entry points described below.

---

## 2. @next/polyfill-nomodule and the Module/Nomodule Pattern

Next.js ships `@next/polyfill-nomodule` as a separate script injected via the `nomodule` attribute. The module/nomodule split works as follows:

- Modern browsers that support ES modules ignore `<script nomodule>` entirely.
- Legacy browsers (IE 11, old Edge) that do not support ES modules execute the `nomodule` script and receive the full polyfill bundle.

Next.js handles this automatically. The `@next/polyfill-nomodule` package includes:

- `core-js` (ES5–ES2019 features)
- `regenerator-runtime`
- `whatwg-fetch`
- `url-polyfill`

You do not import or configure `@next/polyfill-nomodule` directly. Next.js injects it during the build. The only action required is ensuring your `browserslist` targets are accurate so Next.js knows which browsers need the legacy bundle.

---

## 3. App Router: instrumentation-client.ts

For App Router projects, the canonical polyfill entry point is `instrumentation-client.ts` at the project root. This file was merged into Next.js in August 2025 and is the recommended approach for Next.js 15+.

**Why this file runs first:** `instrumentation-client.ts` executes before React hydration begins. The module is loaded as the first client-side script, before any route segment or layout code. This guarantees polyfills are available when component code runs.

Create the file at the project root (same level as `app/`):

```typescript
// instrumentation-client.ts

// requestIdleCallback — absent from all Safari versions
if (typeof globalThis.requestIdleCallback === 'undefined') {
  globalThis.requestIdleCallback = (cb: IdleRequestCallback, opts?: IdleRequestOptions) => {
    const start = Date.now();
    return setTimeout(() => {
      cb({ didTimeout: false, timeRemaining: () => Math.max(0, 50 - (Date.now() - start)) });
    }, opts?.timeout ?? 1) as unknown as number;
  };
  globalThis.cancelIdleCallback = (id: number) => clearTimeout(id);
}

// Promise.withResolvers — Safari 17.4+ only
import 'core-js/actual/promise/with-resolvers';

// Set methods — Safari 17.0+ only (granular imports for tree-shaking)
import 'core-js/actual/set/union';
import 'core-js/actual/set/intersection';
import 'core-js/actual/set/difference';

// Array.fromAsync — not yet in Safari
import 'core-js/actual/array/from-async';
```

Enable the file in `next.config.ts`:

```typescript
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    instrumentationHook: true, // required for Next.js < 15.3
  },
};

export default nextConfig;
```

From Next.js 15.3 onward, `instrumentationHook` is enabled by default and the `experimental` flag is unnecessary.

**When to use `instrumentation-client.ts` vs dynamic loading:** Use this file for polyfills that must be synchronously available before any component renders — DOM APIs, Promise extensions, global constructors. Use dynamic loading (Section 5) for large polyfills needed only on specific routes.

---

## 4. Pages Router: polyfills.ts in _app.tsx

For Pages Router projects, create a dedicated polyfills module and import it as the first line of `_app.tsx`.

```typescript
// polyfills.ts (project root or src/)

// requestIdleCallback
if (typeof globalThis.requestIdleCallback === 'undefined') {
  globalThis.requestIdleCallback = (cb, opts) => {
    const start = Date.now();
    return setTimeout(() => {
      cb({ didTimeout: false, timeRemaining: () => Math.max(0, 50 - (Date.now() - start)) });
    }, opts?.timeout ?? 1);
  };
  globalThis.cancelIdleCallback = (id) => clearTimeout(id);
}

// ResizeObserver — not available in older Safari
import 'resize-observer-polyfill';

// smoothscroll — Safari does not support scroll-behavior: smooth on window
import smoothscroll from 'smoothscroll-polyfill';
smoothscroll.polyfill();
```

```typescript
// pages/_app.tsx
import '../polyfills'; // must be first import
import type { AppProps } from 'next/app';

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}
```

Import order matters. Webpack processes imports in declaration order, so placing `polyfills` first ensures the globals are patched before any component module initializes.

---

## 5. Conditional and Dynamic Polyfill Loading

Some polyfills are large enough that loading them unconditionally degrades performance for users on modern browsers. Use dynamic imports inside `useEffect` to load polyfills only when the feature is absent.

```typescript
// app/providers.tsx (or any client component that mounts early)
'use client';

import { useEffect } from 'react';

export function PolyfillProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const tasks: Promise<void>[] = [];

    if (!('ResizeObserver' in globalThis)) {
      tasks.push(
        import('resize-observer-polyfill').then(({ default: RO }) => {
          globalThis.ResizeObserver = RO;
        })
      );
    }

    if (!('IntersectionObserver' in globalThis)) {
      tasks.push(import('intersection-observer').then(() => {}));
    }

    // AbortController — older Safari
    if (!('AbortController' in globalThis)) {
      tasks.push(
        import('abortcontroller-polyfill/dist/abortcontroller').then(({ AbortController }) => {
          globalThis.AbortController = AbortController;
        })
      );
    }

    Promise.all(tasks).catch(console.error);
  }, []);

  return <>{children}</>;
}
```

Place `PolyfillProvider` in the root `app/layout.tsx` as a wrapper around `{children}`.

**Trade-off:** Dynamic polyfills load after hydration. Any component that uses the polyfilled API during its first render will fail on browsers that lack the feature. Reserve dynamic loading for APIs used only in response to user interaction (scroll handlers, resize callbacks, fetch calls triggered by clicks).

---

## 6. browserslist Configuration

Next.js reads `browserslist` from `package.json` to determine which syntax transforms and polyfills SWC applies. Without explicit configuration, Next.js 16 defaults to:

```json
{
  "browserslist": {
    "production": [
      "chrome 111",
      "edge 111",
      "firefox 111",
      "safari 16.4"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
```

### Widening Support (older Safari)

To support Safari 15.4 and iOS Safari 15.4 (released September 2021):

```json
{
  "browserslist": {
    "production": [
      "chrome 111",
      "edge 111",
      "firefox 111",
      "safari >= 15.4",
      "ios_saf >= 15.4"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
```

This causes SWC to inject additional `core-js` transforms for features introduced between Safari 15.4 and 16.4, including `Array.at()`, `Object.hasOwn()`, and `structuredClone`.

### Narrowing for Performance (modern-only)

If analytics confirm your audience uses only recent browsers:

```json
{
  "browserslist": {
    "production": [
      "chrome >= 120",
      "edge >= 120",
      "firefox >= 120",
      "safari >= 17.0",
      "ios_saf >= 17.0"
    ]
  }
}
```

Narrowing to Safari 17.0 eliminates the need for `Set` method polyfills and reduces the `core-js` injection surface.

### Querying Your Effective Targets

Verify what `browserslist` resolves to before deploying:

```bash
npx browserslist --env production
```

This prints the full list of browser versions your configuration covers, which is the same list SWC uses.

---

## 7. SWC and core-js Integration

SWC (Next.js's Rust-based compiler) reads your `browserslist` targets and automatically injects `core-js` polyfills for any ECMAScript built-in that your targets do not fully support. This happens at compile time — you do not import `core-js` manually for standard built-ins.

Install `core-js` as a production dependency so it is available at runtime:

```bash
npm install core-js
```

SWC injects granular imports like `import 'core-js/modules/es.array.flat'` rather than the entire `core-js/stable` bundle. This keeps bundle size minimal.

### transpilePackages for ESM-only Dependencies

Some npm packages ship only ESM with modern syntax that SWC does not transform by default (because `node_modules` are excluded from transpilation). Use `transpilePackages` to opt specific packages into the SWC transform pipeline:

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  transpilePackages: [
    'some-esm-only-package',
    '@scope/modern-library',
  ],
};
```

When a package is listed in `transpilePackages`, SWC applies the same browserslist-driven transforms to it as to your application code.

### Known Issue: Nullish Coalescing from node_modules

Prior to the October 2025 canary release, `browserslist` targets did not cause SWC to transpile nullish coalescing (`??`) and optional chaining (`?.`) operators originating from `node_modules`, even when the target browsers required it. The fix landed in `next@canary` (October 2025) and was backported to the stable channel in Next.js 16.

If you are on Next.js 15.x and encounter runtime errors from `??` in third-party packages on older browsers, add the offending package to `transpilePackages` as a workaround.

### experimental.optimizePackageImports

This flag rewrites barrel imports to named imports, reducing the number of modules SWC must process:

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons', 'date-fns'],
  },
};
```

This is a performance optimization, not a polyfill concern, but it interacts with `transpilePackages`: a package listed in both will be both transpiled and import-optimized.

---

## 8. next.config.ts Polyfill-Related Settings

```typescript
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Transpile ESM-only or modern-syntax packages through SWC
  transpilePackages: [
    // Add packages that fail with syntax errors in older browsers
  ],

  experimental: {
    // Rewrite barrel imports to reduce bundle size
    optimizePackageImports: [
      'lucide-react',
      '@radix-ui/react-icons',
    ],

    // Required for instrumentation-client.ts on Next.js < 15.3
    // instrumentationHook: true,
  },

  // output: 'standalone' is compatible with all polyfill strategies
  output: 'standalone',
};

export default nextConfig;
```

The `output: 'standalone'` mode bundles only the files needed for production. Polyfills imported through `instrumentation-client.ts` or `_app.tsx` are included in the standalone output automatically — no additional configuration is required.

---

## 9. Eliminating Unnecessary Polyfills

Shipping polyfills to browsers that do not need them wastes bytes and slows Time to Interactive. Two tools identify unnecessary polyfills.

### Lighthouse "Avoid Serving Legacy JavaScript"

Run Lighthouse against your production build:

```bash
npx next build
npx next start &
npx lighthouse http://localhost:3000 --only-audits=legacy-javascript --output=json
```

The `legacy-javascript` audit lists specific polyfills and transforms that are unnecessary for the browsers Lighthouse detects. Common findings:

| Finding | Fix |
|---------|-----|
| `Array.prototype.flat` polyfill unnecessary | Raise `browserslist` minimum or remove manual import |
| `Object.assign` polyfill unnecessary | Next.js auto-polyfill handles this; remove manual import |
| `regeneratorRuntime` unnecessary | Raise `browserslist` minimum; avoid `async/await` transpilation |
| `@babel/plugin-transform-classes` | Ensure SWC is active, not Babel |

### Bundle Analyzer

Install `@next/bundle-analyzer`, wrap `nextConfig` with it, then run:

```bash
npm install --save-dev @next/bundle-analyzer
ANALYZE=true npx next build
```

In the generated report, search for `core-js` in the client bundle. Each module appears as a separate node. If you see modules for features your `browserslist` targets already support natively, raise the minimum browser version or remove the manual `core-js` import pulling them in.

### Audit Checklist

Before shipping polyfills to production, verify:

- [ ] `browserslist` targets match actual user analytics (check Google Analytics or Plausible browser report)
- [ ] No manual `whatwg-fetch` import — Next.js auto-polyfills `fetch`
- [ ] No manual `object-assign` import — Next.js auto-polyfills `Object.assign`
- [ ] `core-js/stable` is not imported wholesale — use granular `core-js/actual/...` imports
- [ ] Dynamic polyfills (Section 5) are used for ResizeObserver and IntersectionObserver rather than unconditional imports
- [ ] Lighthouse `legacy-javascript` audit passes with no findings
- [ ] Bundle analyzer shows no unexpected `core-js` modules for natively-supported features

---

## Quick Reference: Entry Point by Router

| Router | File | Location | Runs when |
|--------|------|----------|-----------|
| App Router | `instrumentation-client.ts` | Project root | Before React hydration |
| Pages Router | `polyfills.ts` + import in `_app.tsx` | Project root or `src/` | Before page component mounts |
| Either (lazy) | `useEffect` + dynamic import | Any client component | After first render |

## Quick Reference: browserslist Impact

| Change | Effect on bundle |
|--------|-----------------|
| Raise minimum Safari from 16.4 to 17.0 | Removes Set method polyfills |
| Raise minimum Safari from 16.4 to 17.4 | Also removes Promise.withResolvers polyfill |
| Lower minimum Safari to 15.4 | Adds Array.at, Object.hasOwn, structuredClone polyfills |
| Add `ios_saf >= 15.4` | Covers iOS WebKit separately from macOS Safari |
