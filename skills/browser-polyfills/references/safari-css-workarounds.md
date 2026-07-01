# Safari CSS Workarounds

Sources: WebKit Bug Tracker, caniuse.com (2026), MDN Web Docs, production Next.js/Tailwind codebases

---

## CSS Feature Support Matrix

| Feature | Safari Version | Still Needs Prefix? | Known Bugs? |
|---|---|---|---|
| `backdrop-filter` | 9+ | Yes, `-webkit-` always | CSS variables fail inside it |
| `gap` in flexbox | 14.1+ | No | Not supported < 14.1 |
| `:has()` selector | 15.4+ | No | No nesting, no pseudo-elements inside |
| `@layer` | 15.4+ | No | None significant |
| `dvh` / `svh` / `lvh` | 15.4+ | No | iOS 26 regression: gap at bottom |
| `aspect-ratio` | 15+ | No | None |
| `color-mix()` | 16.2+ | No | None |
| Container queries | 16.0+ | No | Shadow DOM boundary bug |
| `@container` style queries | 18.0+ | No | None |
| `env()` safe area insets | 11.1+ | No | None |
| `subgrid` | 16.0+ | No | None |
| `scroll-snap` | 11+ | No | Momentum scrolling conflicts on iOS |
| `position: sticky` | 13+ | No | Overflow ancestor, transform ancestor bugs |
| `scroll-behavior: smooth` | 15.4+ | No | Ignored inside overflow containers |
| `transform` / `animation` / `transition` | All | No (drop `-webkit-`) | None |

Next.js 15/16 default target: **Safari 16.4+**.

---

## backdrop-filter

Safari requires `-webkit-backdrop-filter` alongside the unprefixed property. Safari 18 still requires it.

```css
.glass-panel {
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  backdrop-filter: blur(12px) saturate(180%);
}
```

CSS custom properties do not resolve inside `backdrop-filter` in Safari. The value is treated as invalid and the filter is silently dropped.

```css
/* Broken in Safari */
:root { --blur: 12px; }
.panel { backdrop-filter: blur(var(--blur)); }

/* Fix — hardcode the value */
.panel {
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
}
```

---

## Viewport Units: dvh / svh / lvh

Safari 15.4 introduced dynamic viewport units, but iOS 26 introduced a regression where `100dvh` leaves a gap at the bottom when the address bar collapses. Use a layered fallback.

```css
.full-height {
  height: 100vh;
  height: 100dvh;
  height: -webkit-fill-available; /* iOS fallback — must be last */
}
```

Browsers that do not understand `-webkit-fill-available` ignore it and fall back to `100dvh`.

### JavaScript Visual Viewport API Workaround

For pixel-perfect iOS viewport height, use the Visual Viewport API to set a CSS custom property. This handles both the iOS 26 regression and the address-bar-collapse problem.

```ts
// utils/viewport.ts
export function initViewportHeight(): void {
  const setVh = () => {
    const vh = window.visualViewport?.height ?? window.innerHeight;
    document.documentElement.style.setProperty('--vh', `${vh * 0.01}px`);
  };
  setVh();
  window.visualViewport?.addEventListener('resize', setVh);
  window.addEventListener('resize', setVh);
}
```

```css
.full-screen-modal {
  height: calc(var(--vh, 1vh) * 100);
}
```

```tsx
// app/layout.tsx
'use client';
import { useEffect } from 'react';
import { initViewportHeight } from '@/utils/viewport';

export function ViewportInit() {
  useEffect(() => { initViewportHeight(); }, []);
  return null;
}
```

---

## gap in Flexbox

`gap` in flexbox is not supported in Safari < 14.1. For projects targeting Safari 16.4+ exclusively, `gap` is safe without a fallback. If older device support is required, use a margin-based fallback guarded by `@supports`.

```css
/* Fallback for Safari < 14.1 */
.flex-row { display: flex; flex-wrap: wrap; margin: -0.5rem; }
.flex-row > * { margin: 0.5rem; }

@supports (gap: 1rem) {
  .flex-row { margin: 0; gap: 1rem; }
  .flex-row > * { margin: 0; }
}
```

---

## scroll-snap

iOS Safari's momentum scrolling conflicts with `scroll-snap`. Without `scroll-snap-stop: always`, the container can scroll past snap points during fast swipes.

```css
.snap-container {
  overflow-x: scroll;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
}

.snap-item {
  scroll-snap-align: start;
  scroll-snap-stop: always; /* prevent skipping on fast swipes */
}
```

Avoid combining `scroll-snap-type: y mandatory` with `overflow: hidden` on ancestor elements — Safari silently disables snapping.

---

## :has() Selector Limitations

`:has()` is supported from Safari 15.4. Use it freely on the 16.4+ target, but observe these constraints.

**Nesting `:has()` inside `:has()` is not supported:**

```css
/* Broken in Safari */
.parent:has(.child:has(.grandchild)) { }

/* Fix — flatten */
.parent:has(.grandchild) { }
```

**Dynamic pseudo-classes inside `:has()` are unreliable:**

```css
/* Unreliable in Safari */
.form:has(input:focus) { }
.nav:has(a:hover) { }
/* Use JavaScript class toggling instead */
```

**Pseudo-elements inside `:has()` are not supported:**

```css
.container:has(::before) { } /* invalid */
```

---

## Container Queries: Shadow DOM Boundary Bug

Named containers do not propagate across shadow DOM boundaries in Safari. Redefine the container on `:host` inside the shadow root.

```css
/* Light DOM */
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}

/* Shadow DOM — @container card fails without this */
:host {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card-body { flex-direction: row; }
}
```

---

## -webkit- Prefixes: Keep vs Drop

### Still Required in 2026

| Property | Reason |
|---|---|
| `-webkit-backdrop-filter` | Required alongside unprefixed in all Safari versions |
| `-webkit-tap-highlight-color` | Controls tap flash on iOS; no unprefixed equivalent |
| `-webkit-text-size-adjust` | Prevents iOS from auto-scaling text in landscape |
| `-webkit-overflow-scrolling` | Legacy but harmless; enables momentum scrolling |
| `-webkit-fill-available` | Viewport height fallback on iOS |

```css
html {
  -webkit-text-size-adjust: 100%;
  text-size-adjust: 100%;
}

a, button {
  -webkit-tap-highlight-color: transparent;
}
```

### Safe to Drop

| Property | Safe since |
|---|---|
| `-webkit-transform` | Safari 9 |
| `-webkit-transition` | Safari 9 |
| `-webkit-animation` | Safari 9 |
| `-webkit-border-radius` | Safari 5 |
| `-webkit-box-shadow` | Safari 5.1 |
| `-webkit-flex` | Safari 9 |

---

## iOS-Only Style Guard

`@supports (-webkit-touch-callout: none)` targets iOS Safari exclusively. This property is recognized only by iOS WebKit.

```css
@supports (-webkit-touch-callout: none) {
  .bottom-nav {
    padding-bottom: env(safe-area-inset-bottom);
  }

  .full-height-layout {
    height: -webkit-fill-available;
  }
}

@supports not (-webkit-touch-callout: none) {
  .full-height-layout {
    height: 100dvh;
  }
}
```

---

## position: sticky Bugs

Safari has three distinct failure modes for `position: sticky`.

### Overflow Ancestor Bug

`position: sticky` stops working when any ancestor has `overflow` set to anything other than `visible`.

```css
.scroll-container { overflow: clip; } /* not hidden — clip doesn't create a scroll container */
.sticky-header { position: sticky; top: 0; }
```

### Transform Ancestor Bug

A `transform` on any ancestor creates a new stacking context that breaks `position: sticky`.

```css
/* Broken */
.animated-wrapper { transform: translateZ(0); }

/* Fix — apply will-change on the sticky element itself, not an ancestor */
.sticky-header {
  position: sticky;
  top: 0;
  will-change: transform;
}
```

### iOS 26 Displacement Bug

iOS 26 introduced a regression where sticky elements are displaced by the collapsed address bar height. Compensate with `env(safe-area-inset-top)`.

```css
.sticky-nav {
  position: sticky;
  top: 0;
}

@supports (-webkit-touch-callout: none) {
  .sticky-nav {
    top: env(safe-area-inset-top, 0px);
  }
}
```

---

## scroll-behavior: smooth

`scroll-behavior: smooth` is supported from Safari 15.4 but is silently ignored in two cases:

1. The scroll target is inside an `overflow: auto` or `overflow: scroll` container that does not itself have `scroll-behavior: smooth`.
2. The user has enabled "Reduce Motion" in iOS accessibility settings.

```css
html { scroll-behavior: smooth; }

.scroll-container {
  overflow-y: auto;
  scroll-behavior: smooth; /* must be on the scroll container */
}

@media (prefers-reduced-motion: reduce) {
  html, .scroll-container { scroll-behavior: auto; }
}
```

---

## Tailwind CSS Integration

### Tailwind v4 Base and Utility Layers

```css
/* app/globals.css */
@import "tailwindcss";

@layer base {
  html {
    -webkit-text-size-adjust: 100%;
    text-size-adjust: 100%;
  }

  a, button, [role="button"] {
    -webkit-tap-highlight-color: transparent;
  }

  :root {
    --vh: 1vh; /* populated by initViewportHeight() */
  }
}

@layer utilities {
  .h-screen-safe {
    height: 100vh;
    height: 100dvh;
    height: -webkit-fill-available;
  }

  .h-screen-ios {
    height: calc(var(--vh) * 100);
  }

  .backdrop-blur-safari {
    -webkit-backdrop-filter: blur(12px);
    backdrop-filter: blur(12px);
  }
}
```

### Tailwind v4 iOS Variant

```css
@custom-variant ios (@supports (-webkit-touch-callout: none));
```

Apply in markup:

```html
<nav class="sticky top-0 ios:top-[env(safe-area-inset-top)]">
  <!-- content -->
</nav>

<div class="h-screen-safe ios:h-screen-ios">
  <!-- full-height layout -->
</div>
```

---

## Autoprefixer Configuration

Autoprefixer does not add `-webkit-backdrop-filter` — add it manually.

```js
// postcss.config.js
module.exports = {
  plugins: {
    autoprefixer: {
      overrideBrowserslist: [
        'last 2 Chrome versions',
        'last 2 Firefox versions',
        'last 2 Edge versions',
        'Safari >= 16.4',
        'iOS >= 16.4',
      ],
    },
  },
};
```

**Autoprefixer handles automatically** (for Safari 16.4+ target):

| Property | Adds |
|---|---|
| `user-select` | `-webkit-user-select` |
| `appearance` | `-webkit-appearance` |
| `print-color-adjust` | `-webkit-print-color-adjust` |
| `mask-*` | `-webkit-mask-*` |

**Add manually (Autoprefixer does not handle):**

| Property | Manual prefix |
|---|---|
| `backdrop-filter` | `-webkit-backdrop-filter` |
| `tap-highlight-color` | `-webkit-tap-highlight-color` |
| `text-size-adjust` | `-webkit-text-size-adjust` |
| `fill-available` | `-webkit-fill-available` |

---

## Workaround Checklist

Apply to every Next.js project targeting Safari 16.4+:

1. Add `-webkit-text-size-adjust: 100%` to `html` in base styles.
2. Add `-webkit-tap-highlight-color: transparent` to interactive elements.
3. Always pair `backdrop-filter` with `-webkit-backdrop-filter`; never use CSS variables inside either.
4. Use the `h-screen-safe` layered fallback for full-height layouts; initialize `--vh` via the Visual Viewport API.
5. Add `scroll-snap-stop: always` to snap items in momentum-scrolling containers.
6. Declare `container-type` on `:host` inside Web Component shadow roots.
7. Replace `overflow: hidden` with `overflow: clip` on ancestors of `position: sticky` elements.
8. Apply `scroll-behavior: smooth` on the scroll container itself, not only on `html`.
9. Wrap iOS-specific styles in `@supports (-webkit-touch-callout: none)`.
10. Configure Autoprefixer with `Safari >= 16.4`; add unprefixable properties manually.
