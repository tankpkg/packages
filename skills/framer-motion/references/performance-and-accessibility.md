# Performance and Accessibility

Sources: Motion.dev documentation (2025-2026), Head (Designing Interface Animation), Nabors (Animation at Work), W3C WCAG 2.1

Covers: animation performance tiers, motion values vs React state, LazyMotion bundle reduction, MotionConfig, reduced motion accessibility, keyboard support, duration guidelines, anti-patterns, SSR, React Server Components, will-change.


## Animation Performance Tiers

Choose animated properties by their rendering cost. The browser pipeline is: JavaScript → Style → Layout → Paint → Composite. Skipping earlier stages is always faster.

| Tier | Properties | Pipeline Stages | GPU | Use |
|------|-----------|-----------------|-----|-----|
| 1 — Best | `transform`, `opacity` | Composite only | Yes | All animations |
| 2 — OK | `filter`, `clip-path`, `background-color`, `box-shadow` | Paint + Composite | Partial | Decorative effects |
| 3 — Avoid | `width`, `height`, `top`, `left`, `margin`, `padding`, `border-width` | Layout + Paint + Composite | No | Never on scroll or loops |

**Rule:** If an animation triggers layout reflow (Tier 3), every other element on the page must be measured again. On a 60fps timeline that is 16ms per frame — layout reflow alone can consume the entire budget.

### Replacing Tier 3 with Tier 1 Equivalents

| Intent | Avoid | Use Instead |
|--------|-------|-------------|
| Move element | `left`, `top` | `x`, `y` (maps to `translateX/Y`) |
| Resize element | `width`, `height` | `scaleX`, `scaleY` + `layout` prop |
| Reveal element | `height: 0 → auto` | `scaleY` or `layout` prop |
| Fade in | `display: none → block` | `opacity: 0 → 1` |

### Hardware Acceleration

Motion automatically promotes `transform` and `opacity` animations to the compositor thread via the Web Animations API (WAAPI). No manual `will-change` or `translateZ(0)` hacks are needed for these properties. Setting `transform` directly in `animate` is sufficient.

```tsx
import { motion } from "motion/react";

// Compositor-thread animation — no layout, no paint
<motion.div animate={{ x: 100, opacity: 1 }} />

// Triggers layout reflow — avoid
<motion.div animate={{ left: 100 }} />
```


## Motion Values vs React State

Motion values are observable values that update the DOM directly, bypassing React's render cycle entirely. Use them whenever animation values change at high frequency.

| Scenario | Use | Reason |
|----------|-----|--------|
| Scroll-linked parallax | `useScroll` + `useTransform` | No re-renders on scroll |
| Mouse-tracking effects | `useMotionValue` + pointer events | 60fps without React overhead |
| Continuous loops | `useAnimate` with `repeat: Infinity` | Runs off React's scheduler |
| Toggle on user action | React state + `animate` prop | Re-render is acceptable |
| Form field visibility | React state + `AnimatePresence` | Correct lifecycle management |

```tsx
import { motion, useMotionValue, useTransform, useScroll } from "motion/react";

// High-frequency: motion value — no re-renders
const { scrollY } = useScroll();
const opacity = useTransform(scrollY, [0, 300], [1, 0]);

<motion.div style={{ opacity }} />

// Low-frequency: React state — acceptable
const [isOpen, setIsOpen] = useState(false);
<motion.div animate={{ height: isOpen ? "auto" : 0 }} />
```

**Decision rule:** If the value changes more than once per user interaction (scroll, mouse move, drag, continuous loop), use a motion value. If it changes once per user action (click, toggle, route change), React state is fine.


## LazyMotion — Bundle Size Reduction

The full `motion` component includes all features. `LazyMotion` splits the library into a small synchronous core and optional feature packages loaded on demand.

### Feature Packages

| Package | Size | Contents |
|---------|------|----------|
| `domAnimation` | ~5KB gzipped | `animate`, `initial`, `exit`, `whileHover`, `whileTap`, `whileFocus`, `whileInView`, gestures |
| `domMax` | ~15KB gzipped | All of `domAnimation` + drag, layout animations, `LayoutGroup` |

### Synchronous Loading

```tsx
import { LazyMotion, domAnimation, m } from "motion/react";

// Wrap the tree once — typically in the root layout
function App() {
  return (
    <LazyMotion features={domAnimation}>
      <m.div animate={{ opacity: 1 }} />
    </LazyMotion>
  );
}
```

Use `m` instead of `motion` inside a `LazyMotion` tree. The `m` component is a lightweight stub that receives features from the nearest `LazyMotion` provider.

### Dynamic (Async) Loading

Defer feature loading until after the initial render to reduce the critical-path bundle.

```tsx
import { LazyMotion, m } from "motion/react";

const loadFeatures = () =>
  import("motion/react").then((res) => res.domMax);

function App() {
  return (
    <LazyMotion features={loadFeatures} strict>
      <m.div layout animate={{ x: 100 }} />
    </LazyMotion>
  );
}
```

The `strict` prop throws a warning in development if a `motion` component (instead of `m`) is used inside the tree, preventing accidental full-bundle imports.

### When to Use LazyMotion

- Always use in production applications where bundle size matters.
- Use `domAnimation` unless drag or layout animations are required.
- Use dynamic import when the page has animations below the fold.
- Skip LazyMotion only in prototypes or internal tools where bundle size is irrelevant.


## MotionConfig — Global Transition Defaults

`MotionConfig` sets default transition values for all `motion` and `m` components in its subtree. Reduces repetition and enforces consistency.

```tsx
import { MotionConfig } from "motion/react";

// Apply a consistent spring to all animations in the app
<MotionConfig transition={{ type: "spring", stiffness: 300, damping: 30 }}>
  <App />
</MotionConfig>

// Override per-component as needed
<motion.div transition={{ duration: 0.15 }} animate={{ opacity: 1 }} />
```

Use `MotionConfig` to:
- Set a global easing curve that matches the design system.
- Enforce reduced motion behavior across the entire tree (see below).
- Adjust transition defaults during development without touching every component.


## Reduced Motion Accessibility

The `prefers-reduced-motion` media query signals that the user has requested minimal non-essential motion at the OS level. Ignoring it causes nausea, disorientation, and seizure risk for users with vestibular disorders.

### MotionConfig — Global Approach (Preferred)

```tsx
import { MotionConfig } from "motion/react";

<MotionConfig reducedMotion="user">
  <App />
</MotionConfig>
```

`reducedMotion="user"` reads the OS preference and automatically disables all `transform` and positional animations, preserving only `opacity` transitions. This is the lowest-effort, highest-coverage approach.

| Value | Behavior |
|-------|----------|
| `"user"` | Respect OS `prefers-reduced-motion` setting |
| `"always"` | Always disable motion (useful for testing) |
| `"never"` | Always enable motion (ignores OS setting — use with caution) |

### useReducedMotion Hook — Component-Level Control

```tsx
import { motion, useReducedMotion } from "motion/react";

function AnimatedCard() {
  const shouldReduce = useReducedMotion();

  return (
    <motion.div
      animate={shouldReduce ? { opacity: 1 } : { opacity: 1, y: 0 }}
      initial={shouldReduce ? { opacity: 0 } : { opacity: 0, y: 20 }}
    />
  );
}
```

Use `useReducedMotion` when:
- Different components need different reduced-motion fallbacks.
- The reduced-motion variant requires a fundamentally different layout.
- You need to conditionally render non-animated alternatives.

### Reduced Motion Pattern

Replace movement with opacity. Never remove feedback entirely — a user who prefers reduced motion still needs to know that an action succeeded.

```tsx
const shouldReduce = useReducedMotion();

const variants = {
  hidden: shouldReduce ? { opacity: 0 } : { opacity: 0, y: 20 },
  visible: shouldReduce ? { opacity: 1 } : { opacity: 1, y: 0 },
};
```

### CSS Fallback

For non-Motion CSS transitions, add a media query fallback:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```


## Keyboard Accessibility

Motion's gesture props include built-in keyboard support:

| Prop | Mouse/Touch | Keyboard |
|------|-------------|----------|
| `whileTap` | Pointer down | Enter key press |
| `whileHover` | Pointer enter | Focus (when `whileFocus` absent) |
| `whileFocus` | — | Focus |

`whileTap` automatically fires on Enter key for `motion.button` and any element with `role="button"`. No additional keyboard handling is required for tap feedback.

### Focus Management with AnimatePresence

When a modal or panel exits via `AnimatePresence`, focus is lost if the previously focused element is removed from the DOM. Manage focus explicitly:

```tsx
import { AnimatePresence, motion } from "motion/react";
import { useRef, useEffect } from "react";

function Modal({ isOpen, onClose }) {
  const triggerRef = useRef(null);

  return (
    <>
      <button ref={triggerRef} onClick={() => setOpen(true)}>Open</button>
      <AnimatePresence onExitComplete={() => triggerRef.current?.focus()}>
        {isOpen && (
          <motion.div
            role="dialog"
            aria-modal="true"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <button onClick={onClose}>Close</button>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
```

Use `onExitComplete` on `AnimatePresence` to return focus to the trigger element after the exit animation completes.


## Animation Duration Guidelines

Duration communicates weight and importance. Too fast feels broken; too slow feels sluggish.

| Interaction | Duration | Easing | Notes |
|-------------|----------|--------|-------|
| Hover/tap feedback | 100–150ms | ease-out | Must feel instant |
| Small element entry (icon, badge) | 200–250ms | ease-out | |
| Medium element entry (card, panel) | 250–350ms | ease-out | |
| Large element entry (modal, drawer) | 300–400ms | ease-out | |
| Exit animations | 150–200ms | ease-in | Always faster than entry |
| Page transitions | 400–500ms | ease-in-out | Only for full-page changes |
| Scroll-linked effects | — | Linear | Duration is scroll distance |

**Exit is always faster than entry.** Users initiated the exit — they are already moving on. Slow exits create friction.

**Spring transitions** do not have a fixed duration — they settle based on physics. Use `stiffness` and `damping` to control feel rather than setting `duration` explicitly on springs.


## Common Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Animating `width`, `height`, `top`, `left` on scroll | Triggers layout reflow on every frame — causes jank | Use `transform` equivalents or `layout` prop |
| Missing `key` on `AnimatePresence` children | Exit animation never fires; element is reused instead of unmounted | Add a stable, unique `key` to every direct child of `AnimatePresence` |
| React `useState` for rapidly changing animation values | Re-renders on every frame — blocks main thread | Use `useMotionValue` and `useTransform` |
| Spring with `damping < 10` | Oscillates excessively — feels uncontrolled and distracting | Use `damping` 20–30 for UI elements; reserve low damping for playful contexts |
| Infinite animation loops without purpose | Draws attention away from content; causes vestibular issues | Remove decorative loops; use loops only for loading indicators or explicit user-initiated effects |
| More than one primary animation per interaction | Competing motion splits attention and increases cognitive load | One dominant animation per interaction; secondary effects must be subtle |
| Linear easing for positional movement | Feels mechanical and unnatural | Use `ease-out` for entries, `ease-in` for exits, spring for interactive elements |
| Slow exit animations (> 300ms) | Users wait for UI to clear before proceeding | Keep exits at 150–200ms |
| No reduced motion handling | Causes nausea and disorientation for vestibular disorder users | Add `MotionConfig reducedMotion="user"` at the app root |
| Importing `motion` inside `LazyMotion` tree | Pulls in the full bundle, defeating tree-shaking | Use `m` component inside `LazyMotion` |
| Animating `box-shadow` on scroll | Paint-heavy; causes frame drops | Animate `opacity` on a pseudo-element with a fixed shadow instead |


## Server-Side Rendering

Motion components render on the server. Two common issues arise:

### Skip Enter Animation on SSR

When a page is server-rendered, the `initial` state flashes before hydration. Use `initial={false}` to skip the enter animation on first render.

```tsx
import { motion } from "motion/react";

// Skips the initial animation — element appears in its animate state immediately
<motion.div initial={false} animate={{ opacity: 1, y: 0 }} />
```

Use `initial={false}` on components that are visible on page load. Reserve `initial` animations for elements that appear after user interaction.

### Motion Values and Hydration Warnings

Motion values that derive from browser APIs (`useScroll`, `useMotionValueEvent`) produce values that differ between server and client. Suppress the mismatch warning on the containing element:

```tsx
<motion.div style={{ opacity }} suppressHydrationWarning />
```


## React Server Components

Motion components use browser APIs and React hooks. They are client components and cannot run in React Server Components.

```tsx
// page.tsx — Server Component
import { HeroSection } from "./hero-section"; // client component

export default function Page() {
  return <HeroSection />;
}

// hero-section.tsx — Client Component
"use client";

import { motion } from "motion/react";

export function HeroSection() {
  return <motion.div animate={{ opacity: 1 }} />;
}
```

**Rules:**
- Add `"use client"` to any file that imports from `"motion/react"`.
- Pass data from Server Components to animated Client Components as props.
- Keep Server Components as the outer shell; push `"use client"` boundaries as deep as possible to maximize server rendering.


## will-change Management

`will-change` hints to the browser that an element will be animated, allowing early GPU layer promotion. Overuse wastes GPU memory and can degrade performance.

| Situation | Action |
|-----------|--------|
| `transform` or `opacity` animation | Motion manages `will-change` automatically — do not set manually |
| `filter` animation on a large element | Add `will-change: filter` manually before animation starts |
| Static element that never animates | Never set `will-change` |
| Many elements with `will-change` simultaneously | Remove it — GPU memory pressure causes worse performance than no hint |

Motion automatically sets and removes `will-change: transform` and `will-change: opacity` around WAAPI animations. Manual `will-change` is only needed for Tier 2 properties (`filter`, `clip-path`) on large or complex elements.

```tsx
// Let Motion handle will-change for transform/opacity
<motion.div animate={{ x: 100, opacity: 0.5 }} />

// Manual will-change for filter animation on a large element
<motion.div
  style={{ willChange: "filter" }}
  animate={{ filter: "blur(10px)" }}
/>
```

Remove `will-change` after the animation completes if it was set manually. Leaving it on static elements permanently consumes GPU memory.
