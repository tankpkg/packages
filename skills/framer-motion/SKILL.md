---
name: framer-motion
description: |
  Motion for React (formerly Framer Motion) animation mastery. Covers the
  complete API: motion component, AnimatePresence, layout animations, spring
  physics, scroll-linked animations, gestures, motion values, useAnimate,
  variants/orchestration, SVG animation, drag, performance optimization,
  LazyMotion code splitting, and accessibility (reduced motion). Includes
  production-ready recipes for page transitions, modals, staggered lists,
  shared element transitions, parallax, and interactive components.
  Synthesizes Motion.dev documentation (2025-2026), Nabors (Animation at
  Work), Head (Designing Interface Animation), Saffer (Microinteractions),
  Kowalski (Animations on the Web), and production patterns from Linear,
  Vercel, and Notion.

  Trigger phrases: "framer motion", "motion/react", "motion component",
  "animate", "AnimatePresence", "exit animation", "layout animation",
  "layoutId", "shared layout", "spring animation", "spring physics",
  "useAnimate", "useScroll", "useMotionValue", "useTransform", "useSpring",
  "scroll animation", "parallax", "whileHover", "whileTap", "whileInView",
  "whileDrag", "gesture animation", "drag animation", "variants",
  "staggerChildren", "page transition", "modal animation", "enter animation",
  "exit animation", "keyframes", "motion value", "LazyMotion", "MotionConfig",
  "Reorder", "SVG path animation", "pathLength", "reduced motion",
  "animation performance", "layout animation gotcha", "spring preset",
  "tween", "easing", "stagger", "orchestration", "animate presence",
  "motion react", "framer-motion to motion", "motion library react"
---

# Motion for React

## Core Philosophy

1. **Springs over tweens** — Spring physics feel natural because they
   incorporate velocity. Default to springs for movement (x, y, scale),
   tweens for visual properties (opacity, color).
2. **Motion values over React state** — Motion values update the DOM
   directly without re-renders. Use them for anything that changes rapidly
   (scroll, mouse, continuous animation).
3. **Declarative first, imperative when needed** — Use `animate`, `whileHover`,
   `variants` for 90% of work. Reach for `useAnimate` only for sequences,
   timeline scrubbing, or event-driven triggers.
4. **Layout animations are magic** — The `layout` prop and `layoutId`
   handle FLIP animations with scale-distortion correction. Use them for
   any position/size change.
5. **Respect the user** — Always check `useReducedMotion()`. Replace
   movement with opacity-only transitions when reduced motion is preferred.

## Quick-Start

### "How do I animate something?"

```tsx
import { motion } from "motion/react"

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ type: "spring", stiffness: 400, damping: 30 }}
/>
```
-> See `references/core-animation-api.md`

### "How do I animate exit/removal?"

Wrap conditionally rendered elements in `AnimatePresence`:
```tsx
<AnimatePresence mode="wait">
  {show && <motion.div key="item" exit={{ opacity: 0 }} />}
</AnimatePresence>
```
-> See `references/core-animation-api.md`

### "How do I tune spring feel?"

| Feel | Config | Use Case |
|------|--------|----------|
| Snappy | stiffness: 400, damping: 30 | Buttons, toggles |
| Bouncy | stiffness: 300, damping: 12 | Notifications, playful UI |
| Smooth | stiffness: 200, damping: 20 | Dialogs, drawers |
| Gentle | stiffness: 120, damping: 14 | Background, subtle shifts |

-> See `references/transitions-and-springs.md`

### "How do I do shared element transitions?"

Use `layoutId` to morph between different components:
```tsx
<motion.div layoutId={`card-${id}`} />
```
-> See `references/layout-animations.md`

### "How do I animate on scroll?"

```tsx
const { scrollYProgress } = useScroll()
const opacity = useTransform(scrollYProgress, [0, 1], [0, 1])
```
-> See `references/scroll-and-viewport.md`

### "I need a complete animation recipe"

Copy-paste production patterns for modals, page transitions, staggered
lists, button states, drag-to-dismiss, SVG drawing, and more.
-> See `references/production-recipes.md`

## Decision Trees

### Which Transition Type?

| Property Type | Default | Override To |
|--------------|---------|-------------|
| Physical (x, y, scale, rotate) | Spring | Tween only if duration matters |
| Visual (opacity, color, filter) | Tween (0.3s) | Spring for bouncy feel |
| Layout (layout prop) | Spring | Tween for controlled timing |
| Exit animations | Same as animate | Faster duration (0.15-0.2s) |

### Which Animation Approach?

| Need | Approach | API |
|------|----------|-----|
| Simple state change | Declarative | `animate={{ }}` |
| Gesture feedback | Declarative | `whileHover`, `whileTap` |
| Enter/exit the DOM | Declarative | `AnimatePresence` + `exit` |
| Coordinated children | Declarative | `variants` + `staggerChildren` |
| Position/size change | Declarative | `layout` / `layoutId` |
| Scroll-linked | Reactive | `useScroll` + `useTransform` |
| Complex sequence | Imperative | `useAnimate` |
| Continuous/high-freq | Reactive | `useMotionValue` |

### When NOT to Use Motion

| Situation | Use Instead |
|-----------|-------------|
| Simple hover color change | CSS `transition` |
| Single property opacity fade | CSS `transition` |
| Continuous keyframe loop (non-interactive) | CSS `@keyframes` |
| Canvas/WebGL animation | Three.js / PixiJS |
| 60fps scroll effects on 100+ elements | CSS `scroll-timeline` |

## Import Note

The library was renamed from `framer-motion` to `motion`. Use the new import:
```tsx
// Correct (v11+)
import { motion, AnimatePresence } from "motion/react"

// Legacy (still works but deprecated)
import { motion, AnimatePresence } from "framer-motion"
```

## Reference Files

| File | Contents |
|------|----------|
| `references/core-animation-api.md` | motion component, animate/initial/exit, AnimatePresence, keyframes, variants, orchestration, useAnimate, animatable values |
| `references/transitions-and-springs.md` | Spring physics (stiffness/damping/mass vs bounce/duration), tween easing, inertia, spring presets, tuning guide, orchestration timing |
| `references/layout-animations.md` | layout prop, layoutId, LayoutGroup, shared element transitions, Reorder component, FLIP correction, common gotchas |
| `references/gestures-and-drag.md` | whileHover/whileTap/whileFocus/whileDrag/whileInView, drag constraints, useDragControls, event propagation, accessibility |
| `references/scroll-and-viewport.md` | useScroll, scroll-linked animations, parallax, progress bars, useInView, viewport options |
| `references/motion-values-and-hooks.md` | useMotionValue, useTransform, useSpring, useVelocity, useMotionTemplate, useMotionValueEvent, useAnimate, useAnimationFrame, useReducedMotion |
| `references/production-recipes.md` | Page transitions, modal animations, staggered lists, tab switchers, accordions, SVG path drawing, drag-to-dismiss, button states, shared elements |
| `references/performance-and-accessibility.md` | GPU acceleration tiers, LazyMotion code splitting, MotionConfig, bundle size, reduced motion, animation duration guidelines, anti-patterns, SSR/RSC |
