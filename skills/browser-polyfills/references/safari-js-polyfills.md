# Safari JavaScript API Polyfills

Sources: caniuse.com (2026), MDN Web Docs, WebKit Bug Tracker, Next.js documentation

Safari's release cadence (tied to macOS/iOS releases) means features land months or years after Chrome and Firefox. iOS Safari compounds this: every browser on iOS must use WebKit, so Chrome and Firefox on iPhone are Safari under the hood. A polyfill gap on Safari is a gap for all iOS users.

Next.js 15/16 default browserslist targets: `chrome 111, safari 16.4, firefox 111`. APIs that shipped after Safari 16.4 require explicit polyfilling.

---

## Compatibility Matrix

| API | Chrome | Safari | iOS Safari | Polyfill Needed? | Polyfill Package |
|-----|--------|--------|------------|-----------------|-----------------|
| `requestIdleCallback` | 47 | Never | Never | Yes — critical | `requestidlecallback-polyfill` |
| `structuredClone()` | 98 | 15.4 | 15.4 | Partial (streams bug) | `core-js` |
| `AbortSignal.timeout()` | 103 | 16.0 | 16.0 | Conditional | inline shim |
| `Promise.withResolvers()` | 119 | 17.4 | 17.4 | Yes | `core-js` |
| `Set.prototype.union()` etc. | 122 | 17.0 | 17.0 | Yes | `core-js` |
| Iterator helpers | 122 | 17.2 | 17.2 | Yes | `core-js` |
| Temporal API | 127 | Never | Never | Yes | `@js-temporal/polyfill` |
| `scrollTo` smooth behavior | 61 | 15.4 | 15.4 | Conditional | `smoothscroll-polyfill` |
| View Transitions API | 111 | 18.0 | 18.0 | Yes | CSS fallback only |
| Navigation API | 102 | 26.2 | 26.2 | Yes | `@virtualstate/navigation` |
| `Array.at()` | 92 | 15.4 | 15.4 | No (safe at 16.4 target) | — |
| `Object.hasOwn()` | 93 | 15.4 | 15.4 | No (safe at 16.4 target) | — |
| `crypto.randomUUID()` | 92 | 15.4 | 15.4 | No (safe at 16.4 target) | — |
| `globalThis` | 71 | 12.1 | 12.2 | No | — |
| `queueMicrotask` | 71 | 12.1 | 12.2 | No | — |
| `ResizeObserver` | 64 | 13.1 | 13.4 | No | — |
| `IntersectionObserver` | 51 | 12.1 | 12.2 | No | — |
| `WeakRef` | 84 | 14.5 | 14.5 | No | — |
| `TextEncoder` / `TextDecoder` | 38 | 10.1 | 10.3 | No | — |
| `fetch()` | 42 | 10.1 | 10.3 | No (Next.js auto-polyfills) | — |
| `URL` | 32 | 10.0 | 10.0 | No (Next.js auto-polyfills) | — |
| `Object.assign()` | 45 | 9.0 | 9.0 | No (Next.js auto-polyfills) | — |

---

## What Next.js Auto-Polyfills

Next.js injects these polyfills automatically — do not add them manually:

- **`fetch()`** — injected via `node-fetch` on the server, browser-native on client. Deduplicated; adding a second polyfill causes double-fetch bugs.
- **`URL` and `URLSearchParams`** — injected for both server and client runtimes.
- **`Object.assign()`** — injected as part of the core transform pipeline.

Attempting to polyfill these yourself in `instrumentation-client.ts` will conflict with Next.js's own injection and produce unpredictable behavior.

---

## API-by-API Polyfill Guide

### requestIdleCallback — Critical

Safari has never shipped `requestIdleCallback`. React's scheduler uses it internally, and many performance patterns (deferred analytics, lazy hydration, background prefetch) depend on it. This is the single most common Safari breakage in production Next.js apps.

**Install:**

```bash
npm install requestidlecallback-polyfill
```

**Implementation in `instrumentation-client.ts`:**

```typescript
// instrumentation-client.ts
import 'requestidlecallback-polyfill';
```

The polyfill falls back to `setTimeout(callback, 1)` and provides a `cancelIdleCallback` stub. It does not replicate the `deadline.timeRemaining()` budget accurately, but it prevents crashes and allows code to run.

---

### structuredClone — Streams Bug

`structuredClone()` shipped in Safari 15.4 and is safe for plain objects, arrays, Maps, Sets, and Dates. However, cloning a `ReadableStream`, `WritableStream`, or `TransformStream` throws `DataCloneError` in all Safari versions. Chrome handles stream cloning correctly.

If your code clones streams (common in streaming SSR, fetch response piping, or Web Streams API usage), use a conditional:

```typescript
// Safe clone that avoids the Safari streams bug
function safeClone<T>(value: T): T {
  if (
    typeof ReadableStream !== 'undefined' &&
    value instanceof ReadableStream
  ) {
    // Cannot clone streams in Safari — return as-is or handle separately
    throw new Error('Stream cloning not supported in this browser');
  }
  return structuredClone(value);
}
```

For full `structuredClone` compatibility including streams, use `core-js`:

```bash
npm install core-js
```

```typescript
// instrumentation-client.ts
import 'core-js/actual/structured-clone';
```

---

### AbortSignal.timeout()

`AbortSignal.timeout(ms)` creates an AbortSignal that fires after a delay — useful for fetch timeouts without manual cleanup. It shipped in Safari 16.0, which is within the 16.4 target, but verify your actual user distribution before relying on it.

For apps that must support Safari 15.x, use an inline shim:

```typescript
// lib/abort-signal-timeout.ts
export function abortSignalTimeout(ms: number): AbortSignal {
  if (typeof AbortSignal.timeout === 'function') {
    return AbortSignal.timeout(ms);
  }
  const controller = new AbortController();
  setTimeout(() => controller.abort(new DOMException('TimeoutError', 'TimeoutError')), ms);
  return controller.signal;
}
```

Import this utility instead of calling `AbortSignal.timeout()` directly.

---

### Promise.withResolvers()

`Promise.withResolvers()` returns `{ promise, resolve, reject }` — a convenience over the manual executor pattern. It shipped in Safari 17.4 (March 2024), which is above the 16.4 target.

**Install:**

```bash
npm install core-js
```

**Implementation in `instrumentation-client.ts`:**

```typescript
import 'core-js/actual/promise/with-resolvers';
```

---

### Set Methods

Safari 17.0 added `Set.prototype.union()`, `intersection()`, `difference()`, `symmetricDifference()`, `isSubsetOf()`, `isSupersetOf()`, and `isDisjointFrom()`. These are above the 16.4 target.

**Install:**

```bash
npm install core-js
```

**Implementation in `instrumentation-client.ts`:**

```typescript
import 'core-js/actual/set';
```

This imports all Set method polyfills. Import individually (`core-js/actual/set/union`, etc.) if bundle size is a concern.

---

### Iterator Helpers

Iterator helpers (`Iterator.prototype.map`, `.filter`, `.take`, `.drop`, `.flatMap`, `.reduce`, `.toArray`, `.forEach`, `.some`, `.every`, `.find`) shipped in Safari 17.2. They allow lazy transformation of iterables without materializing intermediate arrays.

**Install:**

```bash
npm install core-js
```

**Implementation in `instrumentation-client.ts`:**

```typescript
import 'core-js/actual/iterator';
```

---

### Temporal API

The Temporal API is a complete replacement for `Date` with proper timezone, calendar, and duration support. It is Stage 3 and has no Safari implementation as of March 2026. Global support is approximately 64.3%.

**Install:**

```bash
npm install @js-temporal/polyfill
```

**Implementation in `instrumentation-client.ts`:**

```typescript
import { Temporal, Intl, toTemporalInstant } from '@js-temporal/polyfill';

// Attach to globalThis for code that uses Temporal directly
if (typeof globalThis.Temporal === 'undefined') {
  Object.defineProperty(globalThis, 'Temporal', {
    value: Temporal,
    writable: false,
    configurable: false,
  });
}
```

The `@js-temporal/polyfill` package is approximately 200 KB minified. Load it with a dynamic `import('@js-temporal/polyfill')` in routes that need it rather than globally if Temporal usage is limited.

---

### scrollTo Smooth Behavior

`scroll-behavior: smooth` and `scrollTo({ behavior: 'smooth' })` shipped in iOS Safari 15.4. For apps that must support older iOS, use `smoothscroll-polyfill`:

**Install:**

```bash
npm install smoothscroll-polyfill
```

**Implementation in `instrumentation-client.ts`:**

```typescript
import smoothscroll from 'smoothscroll-polyfill';
smoothscroll.polyfill();
```

**Feature detection:**

```typescript
const supportsSmoothScroll = 'scrollBehavior' in document.documentElement.style;
```

---

### View Transitions API

The View Transitions API shipped in Safari 18.0 (September 2024), above the 16.4 target. There is no JavaScript polyfill that replicates the full API. The correct approach is feature detection with a graceful fallback:

```typescript
// lib/view-transition.ts
export function startViewTransition(callback: () => void | Promise<void>): void {
  if (typeof document.startViewTransition === 'function') {
    document.startViewTransition(callback);
  } else {
    // Fallback: execute immediately without transition
    Promise.resolve(callback()).catch(console.error);
  }
}
```

Do not attempt to polyfill View Transitions with JavaScript animation libraries — the result will not match the native behavior and will add significant bundle weight.

---

### Navigation API

The Navigation API is very new in Safari (26.2, early 2026). Use `@virtualstate/navigation` (`npm install @virtualstate/navigation`) and import `'@virtualstate/navigation/polyfill'` in `instrumentation-client.ts`. This polyfill is ~50 KB — evaluate whether the Next.js router's built-in events (`usePathname` + `useEffect`) cover your use case before adding it.

---

## Feature Detection Patterns

Use these patterns to guard polyfill-dependent code at runtime. Prefer detection over user-agent sniffing.

```typescript
// requestIdleCallback
const hasIdleCallback = typeof requestIdleCallback === 'function';

// structuredClone
const hasStructuredClone = typeof structuredClone === 'function';

// AbortSignal.timeout
const hasAbortSignalTimeout = typeof AbortSignal !== 'undefined' &&
  typeof AbortSignal.timeout === 'function';

// Promise.withResolvers
const hasPromiseWithResolvers = typeof Promise.withResolvers === 'function';

// Set methods
const hasSetUnion = typeof Set.prototype.union === 'function';

// Iterator helpers
const hasIteratorHelpers = typeof Iterator !== 'undefined' &&
  typeof Iterator.prototype.map === 'function';

// Temporal
const hasTemporal = typeof globalThis.Temporal !== 'undefined';

// View Transitions
const hasViewTransitions = typeof document !== 'undefined' &&
  typeof document.startViewTransition === 'function';

// Smooth scroll
const hasSmoothScroll = typeof document !== 'undefined' &&
  'scrollBehavior' in document.documentElement.style;
```

For server-side code, guard all browser API checks with `typeof document !== 'undefined'` or `typeof window !== 'undefined'` to prevent SSR crashes.

---

## Placement in Next.js

All client-side polyfills belong in `instrumentation-client.ts` at the project root (App Router). This file runs once before any application code on the client. For Pages Router, use `pages/_app.tsx` with the same imports at the top of the file.

```typescript
// instrumentation-client.ts (App Router — project root)

// Critical: requestIdleCallback — never in Safari
import 'requestidlecallback-polyfill';

// Promise.withResolvers — Safari 17.4+
import 'core-js/actual/promise/with-resolvers';

// Set methods — Safari 17.0+
import 'core-js/actual/set';

// Iterator helpers — Safari 17.2+
import 'core-js/actual/iterator';

// structuredClone streams fix — all Safari versions
import 'core-js/actual/structured-clone';

// Smooth scroll — iOS Safari < 15.4
import smoothscroll from 'smoothscroll-polyfill';
smoothscroll.polyfill();

// Temporal — no Safari support
import { Temporal } from '@js-temporal/polyfill';
if (typeof globalThis.Temporal === 'undefined') {
  Object.defineProperty(globalThis, 'Temporal', { value: Temporal });
}
```

Do not import polyfills in `layout.tsx` or individual page components. Those locations cause polyfills to load after application code has already executed.

---

## core-js Import Strategy

`core-js` supports three import styles. Use `actual` for production polyfills:

| Import path | Behavior |
|-------------|----------|
| `core-js/stable/...` | Stable proposals only, no Stage 3+ |
| `core-js/actual/...` | Stable + actively developed proposals (recommended) |
| `core-js/full/...` | Everything including experimental proposals |

Avoid `import 'core-js'` (the full bundle) — it adds ~100 KB to your client bundle. Import only the specific modules you need.

**Verify installed version:**

```bash
npm list core-js
```

Use core-js 3.x. Version 2.x does not include ES2022+ polyfills.

---

## Debugging Safari Polyfill Issues

When a feature works in Chrome but fails in Safari, follow this sequence:

1. Open Safari Technology Preview or use BrowserStack for iOS testing.
2. Open Web Inspector (Develop menu on macOS, or Settings > Safari > Advanced > Web Inspector on iOS).
3. In the Console, run the feature detection snippet for the failing API.
4. If detection returns `false`, the polyfill is not loading — check that `instrumentation-client.ts` is present and that the import path is correct.
5. If detection returns `true` but behavior is wrong, the polyfill has a known limitation — check the package's GitHub issues.
6. For iOS Safari specifically, use a physical device when possible. The iOS Simulator does not replicate all WebKit bugs.

**Common mistake:** Importing polyfills inside a `useEffect` hook. By the time `useEffect` runs, other code may have already attempted to use the missing API. Always load polyfills at the module entry point.
