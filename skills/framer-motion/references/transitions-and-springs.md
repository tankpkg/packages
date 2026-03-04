# Transitions and Spring Physics

Sources: Motion.dev documentation (2025-2026), Kowalski (Animations on the Web), Nabors (Animation at Work)

## Transition Types Overview

Motion supports three transition types. Each has a different mental model and default activation rule.

| Type | Mental Model | Default For |
|------|-------------|-------------|
| `tween` | Duration + easing curve | `opacity`, `color`, `backgroundColor`, `borderColor` |
| `spring` | Physics simulation (stiffness, damping, mass) | `x`, `y`, `scale`, `rotate`, `skew`, layout animations |
| `inertia` | Momentum decay after gesture release | Drag end, scroll snap |

Motion selects the default automatically based on the property being animated. Override it explicitly whenever the default does not match the desired feel.

## Setting Transitions

### Per-Component

Pass a `transition` prop directly to the motion component. Applies to all animated properties on that element.

```tsx
import { motion } from "motion/react";

<motion.div
  animate={{ x: 100, opacity: 1 }}
  transition={{ type: "spring", stiffness: 300, damping: 24 }}
/>
```

### Per-Animation-Prop (Value-Specific Transitions)

Assign different transitions to individual properties using nested objects. Use the `default` key as a fallback for any property not explicitly listed.

```tsx
<motion.div
  animate={{ x: 100, opacity: 1, scale: 1.05 }}
  transition={{
    x: { type: "spring", stiffness: 300, damping: 24 },
    opacity: { duration: 0.2, ease: "easeOut" },
    default: { duration: 0.3 }
  }}
/>
```

### Via MotionConfig

Apply a transition to every motion component in a subtree. Useful for enforcing a consistent motion language across a section or the entire app.

```tsx
import { motion, MotionConfig } from "motion/react";

<MotionConfig transition={{ type: "spring", stiffness: 260, damping: 20 }}>
  <motion.div animate={{ x: 100 }} />
  <motion.button whileTap={{ scale: 0.97 }} />
</MotionConfig>
```

### Inherit

Set `inherit: true` on a child variant to match the parent's transition without repeating the config.

```tsx
const child = { animate: { y: 0, transition: { inherit: true } } };
```

## Tween

A tween animates from one value to another over a fixed duration using an easing curve. Use it for visual properties (opacity, color) and any animation where a predictable, time-bounded duration matters.

### Duration

- Default: `0.3s` for single-value animations.
- Default: `0.8s` for keyframe arrays.

```tsx
<motion.div
  animate={{ opacity: 1 }}
  transition={{ type: "tween", duration: 0.25 }}
/>
```

### Named Ease Functions

Motion provides a full set of named easing functions. Pass them as strings.

| Name | Curve Shape | Use Case |
|------|-------------|----------|
| `"linear"` | Constant velocity | Progress bars, color shifts |
| `"easeIn"` | Slow start, fast end | Exit animations |
| `"easeOut"` | Fast start, slow end | Entry animations |
| `"easeInOut"` | Slow start and end | Cross-screen movement |
| `"circIn"` | Sharp acceleration | Dramatic exits |
| `"circOut"` | Sharp deceleration | Dramatic entries |
| `"circInOut"` | Sharp both ends | Emphasis transitions |
| `"backIn"` | Slight overshoot before start | Playful exits |
| `"backOut"` | Slight overshoot past end | Playful entries |
| `"backInOut"` | Overshoot both ends | Expressive movement |
| `"anticipate"` | Pull back then launch | Cartoon-style motion |

```tsx
<motion.div
  animate={{ y: 0 }}
  transition={{ type: "tween", duration: 0.3, ease: "easeOut" }}
/>
```

### Cubic Bezier Arrays

Pass a four-number array `[x1, y1, x2, y2]` for a custom cubic bezier curve. Matches the CSS `cubic-bezier()` format.

```tsx
transition={{ ease: [0.16, 1, 0.3, 1], duration: 0.6 }}
```

### JavaScript Easing Functions

Pass a function `(t: number) => number` for fully custom easing. The function receives a progress value from 0 to 1 and must return a value in the same range.

```tsx
const easeOutExpo = (t: number) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t));

transition={{ ease: easeOutExpo, duration: 0.5 }}
```

### Ease Arrays for Keyframes

When animating through multiple keyframe values, pass an array of ease functions — one per segment between keyframes.

```tsx
<motion.div
  animate={{ x: [0, 50, 100, 50, 0] }}
  transition={{
    duration: 2,
    ease: ["easeIn", "easeOut", "easeIn", "easeOut"],
    times: [0, 0.25, 0.5, 0.75, 1]
  }}
/>
```

## Spring

Spring physics simulate a physical spring connecting the current value to the target. The animation duration is not fixed — it runs until the value settles within `restDelta` of the target.

### Physics-Based Spring

Configure the spring by its physical properties. This approach incorporates gesture velocity automatically, making it ideal for drag-release and gesture-driven animations.

| Prop | Default | Effect |
|------|---------|--------|
| `stiffness` | `1` | Higher = faster, tighter spring |
| `damping` | `10` | Higher = less oscillation |
| `mass` | `1` | Higher = slower, heavier feel |
| `velocity` | `0` | Initial velocity (units/s); gesture velocity is injected automatically |
| `restSpeed` | `0.01` | Velocity threshold to consider animation complete |
| `restDelta` | `0.01` | Distance threshold to consider animation complete |

```tsx
<motion.div
  animate={{ x: 200 }}
  transition={{
    type: "spring",
    stiffness: 300,
    damping: 24,
    mass: 1
  }}
/>
```

### Duration-Based Spring

Specify `duration` and `bounce` instead of physical properties. Easier to reason about when you need a spring that fits a specific time budget. Does not incorporate gesture velocity.

| Prop | Range | Default | Effect |
|------|-------|---------|--------|
| `duration` | seconds | — | Total animation duration |
| `bounce` | `0` – `1` | `0.25` | `0` = no overshoot, `1` = maximum bounce |

```tsx
<motion.div
  animate={{ scale: 1 }}
  transition={{
    type: "spring",
    duration: 0.5,
    bounce: 0.3
  }}
/>
```

### visualDuration

`visualDuration` overrides `duration` for the purpose of visual coordination without changing the underlying physics. Use it when you need a spring to visually complete at the same time as a tween on another element.

```tsx
<motion.div
  animate={{ x: 100 }}
  transition={{
    type: "spring",
    stiffness: 400,
    damping: 30,
    visualDuration: 0.4
  }}
/>
```

## Spring Presets

Use these named configurations as a starting point. Adjust stiffness and damping to taste.

| Preset | Stiffness | Damping | Mass | Use Case |
|--------|-----------|---------|------|----------|
| **Snappy** | 400 | 30 | 1 | Buttons, toggles, instant feedback |
| **Bouncy** | 300 | 12 | 1 | Playful UI, notifications, pop effects |
| **Smooth** | 200 | 20 | 1 | Dialogs, drawers, dropdowns |
| **Gentle** | 120 | 14 | 1 | Subtle fades, background shifts |
| **Stiff** | 600 | 45 | 1 | Drag constraints, high-tension UI |

```tsx
// Reusable preset objects
export const springs = {
  snappy:  { type: "spring", stiffness: 400, damping: 30, mass: 1 },
  bouncy:  { type: "spring", stiffness: 300, damping: 12, mass: 1 },
  smooth:  { type: "spring", stiffness: 200, damping: 20, mass: 1 },
  gentle:  { type: "spring", stiffness: 120, damping: 14, mass: 1 },
  stiff:   { type: "spring", stiffness: 600, damping: 45, mass: 1 },
} as const;

// Usage
<motion.button
  whileTap={{ scale: 0.97 }}
  transition={springs.snappy}
/>
```

## Inertia

Inertia continues motion after a gesture ends, decelerating based on momentum. It is the default transition type applied when a drag gesture releases.

| Prop | Default | Effect |
|------|---------|--------|
| `power` | `0.8` | Multiplier on initial velocity; higher = travels further |
| `timeConstant` | `700` | Decay rate in ms; higher = longer deceleration |
| `modifyTarget` | — | Function to snap the final resting position |
| `min` / `max` | — | Constrain the final position to a range |
| `bounceStiffness` | `500` | Spring stiffness when hitting min/max boundary |
| `bounceDamping` | `10` | Spring damping when hitting min/max boundary |

```tsx
// Snap to nearest 50px grid
<motion.div
  drag="x"
  transition={{
    type: "inertia",
    power: 0.8,
    timeConstant: 700,
    modifyTarget: (target) => Math.round(target / 50) * 50
  }}
/>
```

```tsx
// Constrain with bounce
<motion.div
  drag="x"
  transition={{
    type: "inertia",
    min: 0,
    max: 400,
    bounceStiffness: 300,
    bounceDamping: 20
  }}
/>
```

## Orchestration

Orchestration props control the timing relationships between animations. They apply to the `transition` object on a parent or variant definition.

### delay

Delay the start of an animation in seconds. Negative values start the animation partway through (useful for staggered sequences that should feel simultaneous).

```tsx
<motion.div
  animate={{ opacity: 1 }}
  transition={{ delay: 0.2, duration: 0.3 }}
/>
```

### repeat, repeatType, repeatDelay

| Prop | Values | Effect |
|------|--------|--------|
| `repeat` | number or `Infinity` | Number of additional repetitions after the first |
| `repeatType` | `"loop"`, `"reverse"`, `"mirror"` | `loop` restarts from initial; `reverse` alternates direction; `mirror` alternates with easing mirrored |
| `repeatDelay` | seconds | Pause between repetitions |

```tsx
<motion.div
  animate={{ rotate: 360 }}
  transition={{
    repeat: Infinity,
    repeatType: "loop",
    duration: 2,
    ease: "linear"
  }}
/>
```

### when, delayChildren, staggerChildren

These props apply inside variant transition definitions to orchestrate parent-child timing.

| Prop | Values | Effect |
|------|--------|--------|
| `when` | `"beforeChildren"`, `"afterChildren"` | Parent animates before or after children |
| `delayChildren` | seconds | Delay before any child begins |
| `staggerChildren` | seconds | Offset between each child's start time |

```tsx
const list = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      when: "beforeChildren",
      delayChildren: 0.1,
      staggerChildren: 0.06
    }
  }
};

const item = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 }
};

<motion.ul variants={list} initial="hidden" animate="visible">
  {items.map((i) => (
    <motion.li key={i} variants={item} />
  ))}
</motion.ul>
```

### stagger() Helper

The `stagger()` function from `"motion/react"` provides a more flexible stagger API, including direction control and a range.

```tsx
import { motion, stagger, useAnimate } from "motion/react";

const [scope, animate] = useAnimate();

animate("li", { opacity: 1, y: 0 }, { delay: stagger(0.05) });
animate("li", { opacity: 1, y: 0 }, { delay: stagger(0.05, { from: "last" }) });
animate("li", { opacity: 1, y: 0 }, { delay: stagger(0.05, { from: "center" }) });
```

## Spring Tuning Guide

### How the Physics Properties Interact

- **Stiffness** controls how aggressively the spring pulls toward the target. Doubling stiffness roughly halves the time to reach the target.
- **Damping** controls how quickly oscillation dies out. Low damping produces bounce; high damping produces a smooth, overdamped glide.
- **Mass** slows everything down proportionally. Increasing mass makes the animation feel heavier without changing the spring's character.

Critical damping threshold: `damping = 2 * sqrt(stiffness * mass)`. Below this value the spring bounces; above it the spring glides without overshoot. For most UI elements, target slightly underdamped (one small overshoot) or critically damped.

### Physics-Based vs. Duration-Based

| Situation | Use |
|-----------|-----|
| Animation follows a drag or gesture release | Physics-based — velocity is injected automatically |
| Animation must complete in a fixed time budget | Duration-based |
| Coordinating with a CSS transition or tween | Duration-based with `visualDuration` |
| Matching the feel of a physical object | Physics-based |
| Onboarding or tutorial animations | Duration-based — predictable timing |

### Tuning restSpeed and restDelta

The animation ends when both conditions are met simultaneously:
- Current velocity < `restSpeed` (default `0.01` units/s)
- Distance to target < `restDelta` (default `0.01` units)

Increase these values to make the animation end earlier (useful for long-running springs that visually appear settled but technically continue). Decrease them for precision animations where the final resting position must be exact.

```tsx
transition={{
  type: "spring",
  stiffness: 200,
  damping: 20,
  restSpeed: 0.5,   // end sooner
  restDelta: 0.5
}}
```

## Default Transition Behavior

Motion selects the transition type automatically based on the property being animated. Understanding this prevents unexpected behavior.

| Property Category | Examples | Default Type |
|-------------------|----------|-------------|
| Physical / spatial | `x`, `y`, `translateX`, `scale`, `rotate`, `skew` | `spring` |
| Visual / non-spatial | `opacity`, `color`, `backgroundColor`, `borderColor` | `tween` |
| Layout animations | `layout`, `layoutId` | `spring` |
| SVG path | `pathLength`, `pathOffset` | `tween` |

Override the default by setting `type` explicitly in the `transition` prop.

## Decision Tree: Which Transition Type?

```
Is the animation triggered by a gesture (drag, swipe)?
  └─ Yes → inertia (for release) or spring (for snap-back)
  └─ No ↓

Is the property spatial (x, y, scale, rotate)?
  └─ Yes → spring (default; override with tween if duration matters)
  └─ No ↓

Is the property visual (opacity, color)?
  └─ Yes → tween (default; override with spring for tactile feel)
  └─ No ↓

Does the animation need to complete in a fixed time?
  └─ Yes → tween, or duration-based spring
  └─ No → physics-based spring

Does the animation follow a gesture with velocity?
  └─ Yes → physics-based spring (velocity is injected automatically)
  └─ No → duration-based spring or tween
```

## Anti-Patterns

| Anti-Pattern | Problem | Correction |
|--------------|---------|------------|
| High bounce on functional UI | Distracts from content; feels unprofessional | Keep `damping` above 20 for dialogs, drawers, and navigation |
| Tween on drag-release | Ignores gesture velocity; feels disconnected | Use `inertia` or physics-based `spring` after drag |
| Duration-based spring for gesture animations | Velocity is not incorporated | Use physics-based spring so gesture momentum carries through |
| `restSpeed: 0.001` on long springs | Animation runs imperceptibly for seconds | Set `restSpeed` and `restDelta` to `0.5` for springs above 500ms |
| Identical transition for all properties | Opacity springs look wrong; spatial tweens feel stiff | Use value-specific transitions with the `default` key |
| Animating `height` or `margin` with spring | Triggers layout reflow on every frame | Use `scaleY` + `transformOrigin` or the `layout` prop instead |
