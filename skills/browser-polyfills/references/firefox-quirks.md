# Firefox Compatibility Quirks

Sources: MDN Web Docs, caniuse.com (2026), Bugzilla bug tracker

Firefox is generally the most standards-compliant of the major browsers. Most
compatibility work in Next.js apps targets Safari, not Firefox. This file covers
the specific areas where Firefox diverges from Chrome/Safari behavior, arrived
late to a feature, or requires a different CSS approach.

Next.js default target: Firefox 111+.

---

## 1. FormData Quirks

### Empty File Input Behavior

When a file `<input>` has no file selected, Chrome and Firefox handle the
resulting `FormData` entry differently:

- **Chrome**: Appends an entry with an empty `File` object (`name: ""`, `size: 0`).
- **Firefox**: Appends an entry with an empty string `""` instead of a `File` object.

This difference surfaces when you inspect `formData.get('avatar')` on the server:
`Chrome` returns an empty `File` object; `Firefox` returns `""`.

### Safe Cross-Browser FormData Pattern

```ts
function getFileFromFormData(formData: FormData, field: string): File | null {
  const value = formData.get(field);
  // Covers both Firefox empty string and Chrome empty File
  if (!value || typeof value === 'string') return null;
  if (value.size === 0) return null;
  return value;
}
```

---

## 2. Custom Scrollbar Styling

Firefox and Chrome/Safari use entirely different CSS properties for scrollbar
customization. The WebKit pseudo-element approach is non-standard; Firefox has
never implemented it.

| Property | Firefox | Chrome / Edge | Safari |
|----------|---------|---------------|--------|
| `scrollbar-width` | Yes (FF 64+) | Yes (Chrome 121+) | No |
| `scrollbar-color` | Yes (FF 64+) | Yes (Chrome 121+) | No |
| `::-webkit-scrollbar` | No | Yes | Yes |
| `::-webkit-scrollbar-thumb` | No | Yes | Yes |

### Dual-Pattern Implementation

Write both patterns. Browsers ignore rules they do not understand — no `@supports` guard needed:

```css
/* Standard: Firefox and Chrome 121+ */
.scrollable {
  scrollbar-width: thin;
  scrollbar-color: #6b7280 transparent; /* thumb track */
}

/* Non-standard: Chrome < 121, Safari, Edge legacy */
.scrollable::-webkit-scrollbar {
  width: 6px;
}

.scrollable::-webkit-scrollbar-track {
  background: transparent;
}

.scrollable::-webkit-scrollbar-thumb {
  background-color: #6b7280;
  border-radius: 3px;
}
```

To hide scrollbars while preserving scroll behavior:

```css
.hide-scrollbar { scrollbar-width: none; }                    /* Firefox */
.hide-scrollbar::-webkit-scrollbar { display: none; }         /* Chrome, Safari */
```

---

## 3. CSS Houdini (Paint Worklet / registerProperty)

Firefox does not support the CSS Houdini APIs. Both `CSS.paintWorklet` and
`CSS.registerProperty` are absent as of Firefox 127 (Bugzilla #1505364 and
#1273706 remain open).

| API | Chrome | Firefox | Safari |
|-----|--------|---------|--------|
| `CSS.paintWorklet.addModule()` | 65+ | No | No |
| `CSS.registerProperty()` | 78+ | No | No |
| `@property` rule | 85+ | 128+ | 16.4+ |

`@property` (the CSS at-rule) landed in Firefox 128 — safe for registered custom
properties. The JS `CSS.registerProperty()` method is the gap.

### Feature Detection Pattern

```ts
if ('paintWorklet' in CSS) {
  CSS.paintWorklet.addModule('/worklets/my-painter.js');
}

if ('registerProperty' in CSS) {
  CSS.registerProperty({
    name: '--highlight-color',
    syntax: '<color>',
    inherits: false,
    initialValue: 'transparent',
  });
}
```

For animated custom properties, use `@property` in CSS and skip the JS
registration entirely when possible:

```css
@property --gradient-angle {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}
```

---

## 4. Smooth Scrolling and prefers-reduced-motion

Firefox suppresses CSS smooth scrolling when the OS "Reduce motion" preference
is enabled, even when `scroll-behavior: smooth` is set. Chrome does not always
honor this. Implement the check explicitly rather than relying on browser behavior:

```css
@media (prefers-reduced-motion: no-preference) {
  html {
    scroll-behavior: smooth;
  }
}
```

For JavaScript-driven scroll:

```ts
function scrollToElement(element: HTMLElement) {
  const prefersReduced = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches;

  element.scrollIntoView({
    behavior: prefersReduced ? 'instant' : 'smooth',
    block: 'start',
  });
}
```

---

## 5. Features Where Firefox Arrived Late

Firefox support arrived significantly later than Chrome and Safari for these
features. Users on Firefox 111–120 (within the default Next.js target range)
may lack them — always use feature detection.

| Feature | Chrome | Safari | Firefox | Notes |
|---------|--------|--------|---------|-------|
| CSS `:has()` | 105 | 15.4 | **121** | Safe from FF 121+ |
| View Transitions API | 111 | 18.0 | **144** | Always needs detection |
| Navigation API | 102 | 26.2 | **147** | Very recent everywhere |
| `@starting-style` | 117 | 17.5 | **129** | Safe from FF 129+ |
| Popover API | 114 | 17.0 | **125** | Safe from FF 125+ |

### Feature Detection Patterns

**View Transitions** — the most commonly needed guard:

```ts
function navigateWithTransition(callback: () => void) {
  if (!document.startViewTransition) {
    callback();
    return;
  }
  document.startViewTransition(callback);
}
```

**Navigation API**:

```ts
if ('navigation' in window) {
  window.navigation.addEventListener('navigate', (event) => {
    // intercept navigation
  });
}
```

**CSS `:has()`** — check before relying on it in JS-driven style logic:

```ts
const supportsHas = CSS.supports('selector(:has(*))');
```

---

## 6. Features Where Firefox Was First

These are safe to use without polyfills. Firefox shipped them well before
Chrome and Safari caught up.

| Feature | Firefox | Chrome | Safari | Notes |
|---------|---------|--------|--------|-------|
| CSS Subgrid | **71** (2019) | 117 (2023) | 16.0 | All modern browsers now |
| `requestIdleCallback` | **55** (2016) | 47 | Never | Polyfill required for Safari |

CSS Subgrid is safe — the constraint is Chrome < 117 and Safari < 16.0, both
below the Next.js default target. `requestIdleCallback` is the inverse: Firefox
has it, Safari never will. Polyfill for Safari; Firefox gets the real implementation.

---

## 7. Firefox DevTools: Debugging Compatibility

### Checking CSS Property Support

Firefox DevTools marks unsupported CSS properties with a yellow warning triangle
in the Rules panel. Open DevTools (F12), select the element in the Inspector,
and hover any triangle for the reason (unsupported, overridden, invalid).

### Checking JavaScript API Support

In the Browser Console, type the API name to check availability:

```js
typeof CSS.paintWorklet              // "undefined" in Firefox
typeof document.startViewTransition  // "undefined" in Firefox < 144
'navigation' in window               // false in Firefox < 147
```

### Network Conditions Simulation

Firefox DevTools Network panel includes throttling presets under the
"No Throttling" dropdown. Use "Regular 3G" or "Good 3G" to test polyfill
load performance. Unlike Chrome, Firefox does not have a built-in CPU
throttle slider — use the Performance panel's recording settings instead.

---

## 8. Firefox-Specific CSS Differences

| Property | Firefox Syntax | Chrome / Safari Syntax | Notes |
|----------|---------------|----------------------|-------|
| Scrollbar width | `scrollbar-width: thin` | `::-webkit-scrollbar { width: 6px }` | Write both |
| Scrollbar color | `scrollbar-color: thumb track` | `::-webkit-scrollbar-thumb { background }` | Write both |
| Form appearance | `-moz-appearance: none` | `-webkit-appearance: none` | Use `appearance: none` + both prefixes |
| Text size adjust | Not needed | `-webkit-text-size-adjust: 100%` | Firefox ignores this property |
| Tap highlight | Not applicable | `-webkit-tap-highlight-color: transparent` | Firefox has no tap highlight |
| Font smoothing | Not supported | `-webkit-font-smoothing: antialiased` | Firefox ignores this property |

For `appearance` on form elements, use all three:

```css
select,
input[type='checkbox'],
input[type='radio'] {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
}
```

---

## 9. Firefox for Android

Firefox for Android (Fenix) uses the same SpiderMonkey and Gecko engines as
desktop Firefox. A feature available in desktop Firefox 111 is available in
Firefox for Android 111.

Key differences from desktop:

- **Touch events** behave identically to Chrome for Android. No iOS-specific
  scroll quirks.
- **Viewport behavior**: No dynamic address bar viewport issue. `100vh` works
  as expected — unlike iOS Safari.
- **Font rendering**: Subpixel antialiasing is unavailable on Android regardless
  of browser. `-webkit-font-smoothing` has no effect.

Firefox for Android market share is under 1% globally. Treat it as equivalent
to desktop Firefox for compatibility purposes.

---

## Summary: Firefox Action Checklist

| Area | Action Required |
|------|----------------|
| FormData file inputs | Guard against empty string vs empty File |
| Custom scrollbars | Write both `scrollbar-width` and `::-webkit-scrollbar` |
| CSS Houdini | Feature-detect `CSS.paintWorklet` and `CSS.registerProperty` |
| Smooth scroll | Wrap in `prefers-reduced-motion: no-preference` media query |
| View Transitions | Always guard with `document.startViewTransition` check |
| Navigation API | Always guard with `'navigation' in window` check |
| CSS Subgrid | Safe to use — Firefox had it first |
| `requestIdleCallback` | Polyfill for Safari, not Firefox |
| Form appearance reset | Include `-moz-appearance: none` alongside `-webkit-appearance` |
