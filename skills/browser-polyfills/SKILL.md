---
name: browser-polyfills
description: |
  Diagnose and fix browser compatibility issues in Next.js apps targeting
  Safari, iOS Safari, and Firefox. Covers JavaScript API polyfills,
  CSS workarounds, Next.js polyfill configuration (App Router and Pages
  Router), browserslist setup, feature detection, and safe polyfill
  delivery. Synthesizes caniuse.com data, WebKit Bug Tracker, MDN Web
  Docs, and production Next.js codebase patterns.

  Trigger phrases: "polyfill", "Safari broken", "works in Chrome not Safari",
  "iOS Safari bug", "WebKit issue", "browserslist", "browser compatibility",
  "cross-browser", "caniuse", "feature detection", "@supports",
  "CSS.supports", "requestIdleCallback", "100vh Safari", "dvh", "svh",
  "input zoom iOS", "backdrop-filter Safari", "Safari date parsing",
  "scroll lock iOS", "position sticky Safari", "gap flexbox Safari",
  "@next/polyfill", "polyfill.io alternative", "Safari PWA",
  "smooth scroll Safari", "Safari service worker"
---

# Browser Polyfills for Next.js

## Core Philosophy

- Fix what's broken, not what's theoretical. Check caniuse before adding polyfills.
- Load polyfills conditionally. Modern browsers should not pay for Safari's gaps.
- Safari on iOS is the primary target. All iOS browsers use WebKit, so a Safari bug affects Chrome on iPhone too.
- Prefer CSS workarounds over JavaScript polyfills when possible — zero runtime cost.
- Never use polyfill.io — it was compromised in 2024. Self-host or use Cloudflare's mirror.

## Quick-Start: Diagnosing What Broke

### "My app works in Chrome but breaks in Safari"

1. Open Safari DevTools (or WebKit Inspector on iOS via Mac)
2. Check the Console for errors — note the API name
3. Look up the API in `references/safari-js-polyfills.md` for the compatibility matrix
4. If it's a CSS issue (layout, styling), check `references/safari-css-workarounds.md`
5. Add the polyfill via `instrumentation-client.ts` (App Router) or `_app.tsx` (Pages Router)
6. See `references/nextjs-polyfill-config.md` for configuration

### "Dates show as Invalid Date on Safari"

Safari is strict about date string formats. `new Date('2025-01-15')` works in Chrome but
can break in Safari without the `T` separator.
-> See `references/safari-react-bugs.md` for safe patterns and `date-fns` usage.

### "Input fields zoom the page on iOS"

Any `<input>` with `font-size < 16px` triggers iOS auto-zoom on focus.
-> See `references/safari-react-bugs.md` for the CSS fix.

### "100vh doesn't work right on iOS"

iOS Safari's dynamic address bar causes `100vh` to include the hidden chrome.
-> See `references/safari-react-bugs.md` for the layered CSS + JS fallback.

### "I need to set up polyfills from scratch in Next.js"

-> See `references/nextjs-polyfill-config.md` for the full configuration guide.

## Decision Trees

### What to Polyfill

| Symptom | Likely Cause | Reference |
|---------|-------------|-----------|
| JS error in Safari console | Missing API | `references/safari-js-polyfills.md` |
| Layout broken on iOS only | CSS gap / viewport | `references/safari-css-workarounds.md` |
| Date shows NaN or Invalid | Date parsing | `references/safari-react-bugs.md` |
| Page zooms on input focus | Font-size < 16px | `references/safari-react-bugs.md` |
| Scroll doesn't lock on modal | iOS body overflow bug | `references/safari-react-bugs.md` |
| Firefox-specific layout issue | Scrollbar / Houdini | `references/firefox-quirks.md` |
| Bundle too large | Unnecessary polyfills | `references/polyfill-delivery.md` |

### Where to Add Polyfills in Next.js

| Router | Entry Point | When |
|--------|------------|------|
| App Router | `instrumentation-client.ts` | Runs before hydration — best for global polyfills |
| App Router | Dynamic `import()` in `useEffect` | Heavy polyfills needed by specific components only |
| Pages Router | `import '../polyfills'` in `_app.tsx` | Top-level import, runs before anything else |
| Either | `<Script strategy="beforeInteractive">` | External CDN polyfill scripts |

### How to Load Polyfills

| Strategy | When to Use | Bundle Impact |
|----------|-------------|---------------|
| Static import in entry file | Always-needed polyfills (requestIdleCallback) | Always loaded |
| Dynamic import with feature detection | Heavy polyfills for older browsers only | Loaded on demand |
| CDN script tag | Third-party polyfill service | External, cached |
| browserslist narrowing | Eliminate auto-injected polyfills | Reduces bundle 10-15 KiB |

## Priority Polyfills for Safari (2026)

| Priority | API / Feature | Action |
|----------|---------------|--------|
| Critical | `requestIdleCallback` | Always polyfill — Safari will never ship this |
| Critical | Date string parsing | Use ISO 8601 with `T` separator, or use `date-fns` |
| Critical | Input zoom prevention | CSS: `font-size: 16px` on inputs |
| Critical | polyfill.io removal | Replace with Cloudflare mirror or self-host |
| High | `-webkit-backdrop-filter` | Add prefix alongside standard property |
| High | `dvh` / viewport height | Layered fallback: `100vh` then `100dvh` then JS |
| High | iOS scroll lock | Use `position: fixed` pattern, not `overflow: hidden` |
| Medium | `smoothscroll-polyfill` | For Safari < 15.4 smooth scroll support |
| Medium | Firefox scrollbar styling | Dual `scrollbar-width` + `::-webkit-scrollbar` |
| Low | `Temporal` API | Do not use — Safari has no timeline. Use `date-fns` |

## Reference Files

| File | Contents |
|------|----------|
| `references/safari-js-polyfills.md` | JS API compatibility matrix, polyfill packages, feature detection code |
| `references/safari-css-workarounds.md` | CSS bugs, vendor prefixes, viewport units, sticky positioning |
| `references/nextjs-polyfill-config.md` | instrumentation-client.ts, browserslist, SWC, App/Pages Router setup |
| `references/safari-react-bugs.md` | Date parsing, input zoom, 100vh, scroll lock, modal bugs, PWA issues |
| `references/polyfill-delivery.md` | polyfill.io alternative, feature detection, bundle impact, security |
| `references/firefox-quirks.md` | Scrollbar styling, Houdini gaps, FormData quirks, late feature support |
