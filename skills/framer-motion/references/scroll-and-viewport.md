# Scroll and Viewport Animations

Sources: Motion.dev documentation (2025-2026), Nabors (Animation at Work)

## useScroll Hook

`useScroll` returns four MotionValues that update as the page or a tracked element scrolls.

```tsx
import { useScroll } from "motion/react"

function Component() {
  const { scrollX, scrollY, scrollXProgress, scrollYProgress } = useScroll()
  // scrollX / scrollY: absolute pixel position
  // scrollXProgress / scrollYProgress: normalized 0–1 range
}
```

`scrollXProgress` and `scrollYProgress` are the primary values for scroll-linked animations — 0 at the start, 1 at the end of the scrollable range.

## useScroll Options

Pass an options object to track a specific element or container instead of the page.

```tsx
import { useRef } from "react"
import { useScroll } from "motion/react"

function TrackedSection() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  })
  return <div ref={ref}>...</div>
}
```

| Option | Type | Description |
|--------|------|-------------|
| `target` | `RefObject` | Element to track. Progress reflects element position in viewport. |
| `container` | `RefObject` | Scrollable container to observe instead of the window. |
| `offset` | `[string, string]` | Define start and end of the scroll range. |
| `axis` | `"x" \| "y"` | Which axis to track. Defaults to `"y"`. |

**Offset syntax** — each value is `"<subject> <container>"`:

- `"start end"` — subject's start edge meets container's end edge (element enters from bottom)
- `"end start"` — subject's end edge meets container's start edge (element exits at top)
- `"start start"` — subject's start aligns with container's start (element reaches top)
- `"center center"` — centers align

The pair `["start end", "end start"]` covers the full time an element is visible in the viewport.

## Scroll Progress Patterns

### Page Scroll Progress Bar

```tsx
import { motion, useScroll } from "motion/react"

function ProgressBar() {
  const { scrollYProgress } = useScroll()
  return (
    <motion.div
      style={{
        scaleX: scrollYProgress,
        transformOrigin: "left",
        position: "fixed",
        top: 0, left: 0, right: 0,
        height: 4,
        background: "hsl(220 90% 56%)",
      }}
    />
  )
}
```

### Element Reveal on Scroll

Track an element's scroll progress and derive opacity and y from it.

```tsx
import { useRef } from "react"
import { motion, useScroll, useTransform } from "motion/react"

function RevealCard() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start 0.9", "start 0.4"],
  })
  const opacity = useTransform(scrollYProgress, [0, 1], [0, 1])
  const y = useTransform(scrollYProgress, [0, 1], [40, 0])

  return (
    <motion.div ref={ref} style={{ opacity, y }}>
      Content revealed on scroll
    </motion.div>
  )
}
```

### Section-Based Scroll Snapping

Combine CSS scroll snapping with `whileInView` for section-by-section reveals.

```tsx
function SnapSection({ children }: { children: React.ReactNode }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 60 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      viewport={{ once: true, amount: 0.4 }}
      style={{ scrollSnapAlign: "start", minHeight: "100vh" }}
    >
      {children}
    </motion.section>
  )
}
// Parent: scroll-snap-type: y mandatory
```

## Parallax Effects

Map scroll progress to translate values at different rates per layer.

```tsx
import { useRef } from "react"
import { motion, useScroll, useTransform } from "motion/react"

function ParallaxHero() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  })

  const backgroundY = useTransform(scrollYProgress, [0, 1], ["0%", "30%"])
  const midgroundY  = useTransform(scrollYProgress, [0, 1], ["0%", "15%"])
  const foregroundY = useTransform(scrollYProgress, [0, 1], ["0%", "5%"])

  return (
    <div ref={ref} style={{ position: "relative", height: "100vh", overflow: "hidden" }}>
      <motion.div style={{ y: backgroundY, position: "absolute", inset: 0 }} className="bg-layer" />
      <motion.div style={{ y: midgroundY,  position: "absolute", inset: 0 }} className="mid-layer" />
      <motion.div style={{ y: foregroundY, position: "absolute", inset: 0 }} className="fg-layer" />
    </div>
  )
}
```

Background moves less than foreground relative to scroll speed, creating depth.

## useTransform with Scroll

Map a MotionValue from one range to another to derive any animatable property.

```tsx
import { motion, useScroll, useTransform } from "motion/react"

function MultiTransform() {
  const { scrollYProgress } = useScroll()

  const scale   = useTransform(scrollYProgress, [0, 0.3], [1, 1.4])
  const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [1, 1, 0, 0])
  const rotate  = useTransform(scrollYProgress, [0, 1], [0, 360])
  const x       = useTransform(scrollYProgress, [0, 0.5], ["0%", "-50%"])

  return <motion.div style={{ scale, opacity, rotate, x }}>...</motion.div>
}
```

Input and output arrays must have equal length. Use multiple breakpoints to create easing curves — hold a value steady across a range, then transition.

## useSpring with Scroll

Raw scroll MotionValues update on every scroll event and can feel mechanical. Wrap with `useSpring` to add physics-based smoothing.

```tsx
import { motion, useScroll, useSpring } from "motion/react"

function SmoothProgressBar() {
  const { scrollYProgress } = useScroll()
  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001,
  })

  return (
    <motion.div
      style={{ scaleX: smoothProgress, transformOrigin: "left" }}
      className="fixed top-0 h-1 w-full bg-blue-500"
    />
  )
}
```

| Feel | stiffness | damping |
|------|-----------|---------|
| Snappy | 200 | 20 |
| Balanced | 100 | 30 |
| Smooth / laggy | 50 | 40 |

`restDelta: 0.001` prevents the spring from never fully settling at the end of the scroll range.

## whileInView

Trigger animations when an element enters the viewport. Animates from `initial` to `whileInView` on entry, reverting on exit unless `once: true`.

```tsx
import { motion } from "motion/react"

function Card() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      viewport={{
        once: true,
        amount: 0.3,
        margin: "0px 0px -100px 0px",
      }}
    >
      Animates into view
    </motion.div>
  )
}
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `once` | `boolean` | `false` | Animate only on first intersection. |
| `amount` | `number \| "some" \| "all"` | `"some"` | Fraction of element visible before triggering. |
| `margin` | `string` | `"0px"` | Expand or shrink detection area. CSS margin syntax. |
| `root` | `RefObject` | window | Custom scroll container as intersection root. |

Negative bottom margin (`"0px 0px -100px 0px"`) delays triggering until the element is well into view, preventing premature animations near the fold.

## useInView Hook

`useInView` provides imperative viewport detection, returning a boolean. Accepts the same options as `whileInView`.

```tsx
import { useRef } from "react"
import { useInView } from "motion/react"

function Section() {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, amount: 0.5 })

  return (
    <div
      ref={ref}
      style={{
        opacity: isInView ? 1 : 0,
        transform: isInView ? "none" : "translateY(40px)",
        transition: "opacity 0.6s ease, transform 0.6s ease",
      }}
    >
      Controlled with useInView
    </div>
  )
}
```

Use `useInView` when triggering non-Motion effects (CSS transitions, class toggling, data fetching) based on visibility, or when coordinating multiple elements from a parent.

## Scroll-Triggered Recipes

### Horizontal Scroll-Linked Animation

```tsx
import { useRef } from "react"
import { motion, useScroll, useTransform } from "motion/react"

export function HorizontalScroller() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end end"],
  })
  const x = useTransform(scrollYProgress, [0, 1], ["0%", "-75%"])

  return (
    <section ref={ref} style={{ height: "400vh" }}>
      <div className="sticky top-0 h-screen overflow-hidden">
        <motion.div style={{ x }} className="flex w-[400%] h-full">
          {["Panel 1", "Panel 2", "Panel 3", "Panel 4"].map((panel) => (
            <div key={panel} className="w-screen h-full flex items-center justify-center">
              <h2 className="text-4xl">{panel}</h2>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
```

### Text Reveal with Clip-Path

```tsx
import { useRef } from "react"
import { motion, useScroll, useTransform } from "motion/react"

export function TextReveal({ text }: { text: string }) {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start 0.8", "start 0.3"],
  })
  const clipPath = useTransform(
    scrollYProgress,
    [0, 1],
    ["inset(0 100% 0 0)", "inset(0 0% 0 0)"]
  )

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <span style={{ opacity: 0.15 }}>{text}</span>
      <motion.span style={{ clipPath, position: "absolute", left: 0, top: 0 }}>
        {text}
      </motion.span>
    </div>
  )
}
```

### Sticky Header That Transforms on Scroll

```tsx
import { motion, useScroll, useTransform, useSpring } from "motion/react"

export function StickyHeader() {
  const { scrollY } = useScroll()
  const smoothY = useSpring(scrollY, { stiffness: 100, damping: 30 })

  const height     = useTransform(smoothY, [0, 80], [80, 56])
  const background = useTransform(smoothY, [0, 80], ["rgba(255,255,255,0)", "rgba(255,255,255,0.95)"])
  const boxShadow  = useTransform(smoothY, [0, 80], ["0 0 0 rgba(0,0,0,0)", "0 2px 20px rgba(0,0,0,0.1)"])

  return (
    <motion.header style={{ height, background, boxShadow, position: "fixed", top: 0, width: "100%" }}>
      <nav>Navigation content</nav>
    </motion.header>
  )
}
```

## Performance Considerations

**Animate only transform and opacity on scroll.** Layout properties (`width`, `height`, `top`, `left`, `margin`) trigger reflow on every scroll event and cause jank.

```tsx
// Correct — GPU-composited properties
const y       = useTransform(scrollYProgress, [0, 1], [0, -100])
const opacity = useTransform(scrollYProgress, [0, 1], [1, 0])
const scale   = useTransform(scrollYProgress, [0, 1], [1, 1.2])

// Avoid on scroll — triggers layout
const height    = useTransform(scrollYProgress, [0, 1], [100, 200])
const marginTop = useTransform(scrollYProgress, [0, 1], [0, 50])
```

**Use `useSpring` to smooth scroll-linked values.** Raw MotionValues update synchronously on every scroll event. Spring smoothing reduces perceived jank without sacrificing responsiveness.

**Prefer `whileInView` over scroll-linked opacity for simple reveals.** `whileInView` uses IntersectionObserver (efficient, fires only on state change) rather than a continuous scroll listener. Reserve `useScroll` + `useTransform` for continuous parallax and progress effects.

**Limit per-item `useScroll` calls in lists.** Each call creates an IntersectionObserver and scroll listener. For lists of items, use `whileInView` on each item rather than individual `useScroll` tracking.

**Call hooks at the top level only.** `useScroll`, `useTransform`, and `useSpring` must not be called inside loops or conditionals. Creating them inside render causes new subscriptions on every render cycle.
