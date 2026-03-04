# Motion Values and Hooks

Sources: Motion.dev documentation (2025-2026)

MotionValues are the performance foundation of Motion for React. They hold animated state that updates outside React's render cycle, enabling smooth 60fps animations without triggering component re-renders.

---

## MotionValue Concept

A `MotionValue` is a reactive container for a single value. When it changes, Motion updates the DOM directly — bypassing React's reconciler entirely. Multiple MotionValues form a reactive graph: changing one propagates through derived values automatically. Pass a MotionValue to a `motion` component's `style` prop to wire it to the DOM.

---

## useMotionValue

Create a MotionValue with an initial value. Use `.get()` to read imperatively and `.set(value)` to update.

```tsx
import { motion, useMotionValue } from "motion/react"

function DraggableCard() {
  const x = useMotionValue(0)

  return (
    <motion.div
      drag="x"
      style={{ x }}
      onDrag={() => console.log("x:", x.get())}
    />
  )
}
```

---

## useTransform — Range Mapping

Derives a new MotionValue by mapping an input range to an output range.

```tsx
import { motion, useMotionValue, useTransform } from "motion/react"

function ScaleOnDrag() {
  const x = useMotionValue(0)
  const scale = useTransform(x, [-200, 0, 200], [0.5, 1, 0.5])
  const opacity = useTransform(x, [-200, 0, 200], [0, 1, 0])

  return <motion.div drag="x" style={{ x, scale, opacity }} />
}
```

Transforms chain: pass the output of one `useTransform` as the input of another.

## useTransform — Function Form

Pass a transformer function as the second argument for custom, non-linear mappings.

```tsx
const x = useMotionValue(0)

const rotate = useTransform(x, (v) => {
  const clamped = Math.max(-100, Math.min(100, v))
  return (clamped / 100) * 30
})

const background = useTransform(x, (v) => `hsl(${Math.round((v + 200) / 4)}, 70%, 60%)`)
```

---

## useSpring

Attaches spring physics to a MotionValue. The spring value smoothly follows the source.

```tsx
import { motion, useMotionValue, useSpring } from "motion/react"

function SpringCursor() {
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)
  const x = useSpring(mouseX, { stiffness: 150, damping: 20, mass: 0.5 })
  const y = useSpring(mouseY, { stiffness: 150, damping: 20, mass: 0.5 })

  return (
    <div onMouseMove={(e) => { mouseX.set(e.clientX); mouseY.set(e.clientY) }}
         style={{ position: "fixed", inset: 0 }}>
      <motion.div style={{ x, y, position: "fixed", width: 20, height: 20,
                           borderRadius: "50%", background: "white", pointerEvents: "none" }} />
    </div>
  )
}
```

Pass a static number as the first argument to create a spring driven by `.set()`.

---

## useVelocity

Returns a MotionValue representing the rate of change (units per second) of another MotionValue.

```tsx
import { motion, useMotionValue, useVelocity, useTransform, useSpring } from "motion/react"

function VelocityCard() {
  const x = useMotionValue(0)
  const xVelocity = useVelocity(x)
  // Smooth velocity before driving visuals — raw velocity is noisy
  const smoothVelocity = useSpring(xVelocity, { stiffness: 300, damping: 50 })
  const skewX = useTransform(smoothVelocity, [-3000, 0, 3000], [-15, 0, 15])

  return <motion.div drag="x" style={{ x, skewX }} />
}
```

---

## useMotionTemplate

Combines multiple MotionValues into a single string MotionValue using a tagged template literal. Essential for CSS values that cannot be expressed as a single number.

```tsx
import { motion, useMotionValue, useMotionTemplate } from "motion/react"

function GlowCard() {
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)

  const background = useMotionTemplate`
    radial-gradient(200px circle at ${mouseX}px ${mouseY}px,
      rgba(255,255,255,0.15), transparent 80%)
  `

  return (
    <motion.div
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect()
        mouseX.set(e.clientX - rect.left)
        mouseY.set(e.clientY - rect.top)
      }}
      style={{ background }}
    />
  )
}
```

Use `useMotionTemplate` for box shadows, gradients, clip-paths, and any CSS value requiring string interpolation of multiple animated numbers.

---

## useMotionValueEvent

Subscribes to MotionValue lifecycle events. Automatically cleans up on unmount.

```tsx
import { useMotionValue, useMotionValueEvent } from "motion/react"

function TrackedValue() {
  const x = useMotionValue(0)

  useMotionValueEvent(x, "change", (latest) => console.log("x:", latest))
  useMotionValueEvent(x, "animationStart", () => console.log("started"))
  useMotionValueEvent(x, "animationComplete", () => console.log("done"))
  useMotionValueEvent(x, "animationCancel", () => console.log("cancelled"))

  return <motion.div drag="x" style={{ x }} />
}
```

| Event | Fires when |
|-------|-----------|
| `change` | The value updates (every frame during animation) |
| `animationStart` | A new animation begins on this value |
| `animationComplete` | An animation reaches its target and stops |
| `animationCancel` | An animation is interrupted before completing |

Prefer `useMotionValueEvent` over calling `.on()` directly — it handles cleanup automatically.

---

## useAnimate

Returns a `[scope, animate]` tuple for imperative animations, sequences, and playback control.

```tsx
import { useAnimate, stagger } from "motion/react"

function SequenceExample() {
  const [scope, animate] = useAnimate()

  async function runSequence() {
    await animate(scope.current, { opacity: 1 }, { duration: 0.3 })
    await animate("li", { x: 0, opacity: 1 }, { delay: stagger(0.05) })
  }

  return (
    <div ref={scope}>
      <ul><li>Item 1</li><li>Item 2</li></ul>
      <button onClick={runSequence}>Animate</button>
    </div>
  )
}
```

### Sequence Syntax

Sequences are arrays of `[target, keyframes, options]` tuples. The `at` option controls timing.

```tsx
animate([
  [".box", { x: 100 }],
  [".label", { opacity: 1 }, { at: "<" }],      // same time as previous
  [".badge", { scale: 1 }, { at: "+0.2" }],     // 0.2s after previous ends
  [".footer", { opacity: 1 }, { at: 0.5 }],     // absolute time in seconds
])
```

### Playback Controls

```tsx
const animation = animate(scope.current, { x: 200 }, { duration: 2 })

animation.pause()
animation.play()
animation.stop()
animation.cancel()
await animation.complete()

animation.time = 1.0    // scrub to 1 second
animation.speed = 0.5   // half speed; -1 reverses
```

---

## useAnimationFrame

Runs a callback on every animation frame with `time` (total elapsed ms) and `delta` (ms since last frame). Cancels automatically on unmount.

```tsx
import { motion, useMotionValue, useAnimationFrame } from "motion/react"

function RotatingElement() {
  const rotation = useMotionValue(0)

  useAnimationFrame((time, delta) => {
    rotation.set(rotation.get() + (delta / 1000) * 90) // 90°/s
  })

  return <motion.div style={{ rotate: rotation }} />
}
```

Use for continuous procedural animations — physics simulations, generative art, real-time data visualization.

---

## useInView

Returns a boolean that is `true` when the referenced element is within the viewport.

```tsx
import { useRef } from "react"
import { motion, useInView } from "motion/react"

function FadeInSection() {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" })

  return (
    <motion.div
      ref={ref}
      animate={{ opacity: isInView ? 1 : 0, y: isInView ? 0 : 40 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    />
  )
}
```

| Option | Type | Description |
|--------|------|-------------|
| `once` | `boolean` | Stays true after first intersection |
| `margin` | `string` | Expand/contract detection area (CSS margin syntax) |
| `amount` | `number \| "some" \| "all"` | Fraction of element that must be visible |
| `root` | `RefObject` | Scroll container to observe within |

---

## useReducedMotion

Returns `true` if the user has enabled `prefers-reduced-motion`. Apply at the component level so each component can degrade gracefully.

```tsx
import { motion, useReducedMotion } from "motion/react"

function AnimatedHero() {
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: shouldReduceMotion ? 0.01 : 0.6 }}
    />
  )
}
```

---

## useTime

Returns a MotionValue representing elapsed milliseconds since mount. Updates every frame. Combine with `useTransform` for declarative continuous animations.

```tsx
import { motion, useTime, useTransform } from "motion/react"

function PulsingDot() {
  const time = useTime()
  const opacity = useTransform(time, [0, 500, 1000], [0.3, 1, 0.3], { clamp: false })
  const rotate = useTransform(time, (t) => (t / 1000) * 360)

  return <motion.div style={{ opacity, rotate }} />
}
```

`useTime` is the declarative alternative to `useAnimationFrame` for time-driven effects.

---

## Motion Value Reactive Graph

MotionValues form a graph outside React's render cycle:

```
useMotionValue(0)          ← source
    ├── useTransform(...)  ← derived (recomputes when source changes)
    │       └── useSpring(...)  ← smoothed (follows derived with physics)
    └── useVelocity(...)   ← velocity (rate of change of source)
```

When a source updates: derived values recompute synchronously, Motion schedules a DOM write for the next frame, React's render cycle is never invoked.

---

## Performance Patterns

Use MotionValues instead of React state for any value that animates:

```tsx
// Avoid: re-renders on every mouse move
const [x, setX] = useState(0)

// Prefer: zero re-renders
const x = useMotionValue(0)
```

Read MotionValues imperatively rather than subscribing in render — `useMotionValueEvent(x, "change", setCurrentX)` causes re-renders; prefer `x.get()` inside event handlers.

---

## Hook Selection Guide

| Goal | Hook |
|------|------|
| Create an animated value | `useMotionValue` |
| Map a value to another range | `useTransform` (array form) |
| Custom non-linear mapping | `useTransform` (function form) |
| Smooth a value with physics | `useSpring` |
| Measure rate of change | `useVelocity` |
| Build a CSS string from values | `useMotionTemplate` |
| React to value lifecycle events | `useMotionValueEvent` |
| Imperative / sequenced animation | `useAnimate` |
| Continuous per-frame logic | `useAnimationFrame` |
| Trigger on scroll into view | `useInView` |
| Respect accessibility settings | `useReducedMotion` |
| Time-driven continuous animation | `useTime` + `useTransform` |
| Scroll-linked animations | `useScroll` — see `scroll-and-viewport.md` |
