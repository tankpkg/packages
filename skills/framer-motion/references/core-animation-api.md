# Core Animation API

Sources: Motion.dev documentation (2025-2026), Nabors (Animation at Work)

Covers: motion component, animate/initial/exit props, animatable values, keyframes, variants, orchestration, useAnimate hook, MotionValue as child.


## The motion Component

`motion` wraps any HTML or SVG element and adds animation props. Access elements via dot notation.

```tsx
import { motion } from "motion/react";

<motion.div />
<motion.button />
<motion.svg />
<motion.path />

// Custom components — must forward refs
const MotionCard = motion.create(React.forwardRef<HTMLDivElement, Props>((props, ref) => (
  <div ref={ref} {...props} />
)));
```

### Props Added by motion

| Prop | Purpose |
|------|---------|
| `animate` | Target animation state |
| `initial` | Starting state before first animation |
| `exit` | State when removed from tree (requires AnimatePresence) |
| `variants` | Named animation states |
| `transition` | How the animation moves — see transitions file |
| `whileHover` | Animate while pointer is over element |
| `whileTap` | Animate while element is pressed |
| `whileFocus` | Animate while element has focus |
| `whileDrag` | Animate while element is being dragged |
| `whileInView` | Animate while element is in viewport |
| `layout` | Automatically animate layout changes |
| `layoutId` | Shared element transitions across components |
| `style` | Accepts MotionValues in addition to static values |

---

## animate, initial, exit

### `animate` — target state

Accepts a target object, variant name, variant array, or MotionValue.

```tsx
// Static target
<motion.div animate={{ opacity: 1, x: 0, scale: 1 }} />

// Dynamic — re-animates whenever isOpen changes
const [isOpen, setIsOpen] = useState(false);
<motion.div animate={{ height: isOpen ? "auto" : 0, opacity: isOpen ? 1 : 0 }} />
```

### `initial` — starting state

Sets the state before the first animation. Without it, the element renders at the `animate` target immediately.

```tsx
<motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} />
```

Pass `initial={false}` to skip the enter animation entirely — the element renders at the `animate` target on mount. Use when you only want exit animations.

```tsx
<AnimatePresence>
  {show && (
    <motion.div initial={false} exit={{ opacity: 0, scale: 0.9 }} />
  )}
</AnimatePresence>
```

### `exit` and AnimatePresence

React removes components from the DOM immediately. `AnimatePresence` intercepts removal and lets `exit` complete first.

```tsx
import { AnimatePresence, motion } from "motion/react";

<AnimatePresence>
  {isOpen && (
    <motion.div
      key="modal"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
    />
  )}
</AnimatePresence>
```

When swapping between components, each child needs a unique `key` — AnimatePresence uses it to distinguish enter from exit.

### AnimatePresence modes

| Mode | Behavior | Use case |
|------|----------|----------|
| `"sync"` (default) | Enter and exit play simultaneously | Overlapping fades |
| `"wait"` | Exit completes before enter starts | Page transitions, tab swap |
| `"popLayout"` | Exiting element is popped out of layout flow | List reordering, card stacks |

```tsx
<AnimatePresence mode="wait">
  <motion.div key={pathname} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
</AnimatePresence>
```

---

## Animatable Values

### CSS properties

Any CSS property accepting a numeric value or color. Use camelCase.

```tsx
<motion.div
  animate={{
    opacity: 0.8,
    borderRadius: "12px",
    backgroundColor: "#3b82f6",
    boxShadow: "0 10px 30px rgba(0,0,0,0.2)",
    filter: "blur(0px) brightness(1)",
  }}
/>
```

### Independent transforms

Motion exposes transform components as individual props — no `transform` string needed. Available: `x`, `y`, `z` (translate), `scale` / `scaleX` / `scaleY`, `rotate` / `rotateX` / `rotateY` / `rotateZ`, `skew` / `skewX` / `skewY`, `perspective`.

```tsx
<motion.div animate={{ rotate: 180, scale: 1.5, x: 50 }} />
```

### Colors

Interpolates between any valid CSS color format. Cross-format conversion is automatic.

```tsx
<motion.div animate={{ backgroundColor: "hsl(220, 90%, 60%)", borderColor: "#ef4444" }} />
```

### Special values

`display` and `visibility` are not interpolated — they switch at the end of exit or start of enter.

`height: "auto"` is supported — CSS transitions cannot animate to `auto`, Motion can.

```tsx
<motion.div
  initial={{ height: 0, overflow: "hidden" }}
  animate={{ height: "auto" }}
  exit={{ height: 0 }}
/>
```

---

## Value Type Conversion

Motion converts between units at animation start. Supported cross-unit pairs: `px` ↔ `%`, `px` ↔ `vh`/`vw`, `hex` ↔ `rgb` ↔ `hsl`, named colors. `calc()` values are supported.

```tsx
<motion.div style={{ width: "200px" }} animate={{ width: "50%" }} />
<motion.div animate={{ x: "calc(100% - 20px)" }} />
```

---

## Transform Origin and CSS Variables

### Transform origin

Set `originX`, `originY`, `originZ` in `style` (not `animate`) to control the pivot point.

```tsx
// Scale from top-left corner
<motion.div style={{ originX: 0, originY: 0 }} animate={{ scale: 1.2 }} />

// Rotate around right edge
<motion.div style={{ originX: "100%", originY: "50%" }} animate={{ rotate: 15 }} />
```

### CSS variables

```tsx
// Animate a CSS variable — affects all children using var(--hue)
<motion.div
  animate={{ "--hue": 360 } as any}
  style={{ "--hue": 0 } as React.CSSProperties}
/>

// Use a CSS variable as the target value
<motion.div animate={{ backgroundColor: "var(--brand-color)" }} />
```

The variable is resolved at animation start. Re-trigger the animation if the variable changes.

---

## Keyframes

Pass an array to animate through multiple values. Motion distributes keyframes evenly by default.

```tsx
<motion.div animate={{ x: [0, 100, 50, 150], opacity: [0, 1, 1, 0] }} />
```

### Null wildcard

`null` at index 0 means "start from the current value." Use it to chain animations without knowing the starting position.

```tsx
// Continue from wherever x currently is, animate to 200
<motion.div animate={{ x: [null, 200] }} />
```

### `times` — custom keyframe positions

Use `times` in `transition` to position keyframes explicitly. Values are 0–1.

```tsx
<motion.div
  animate={{ x: [0, 100, 0] }}
  transition={{
    times: [0, 0.8, 1],  // 80% of duration reaching 100, snap back in 20%
    duration: 1,
  }}
/>
```

---

## Variants

Named animation states defined outside JSX. Enable tree-wide orchestration and keep animation logic readable.

```tsx
const boxVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.8 },
};

<motion.div variants={boxVariants} initial="hidden" animate="visible" exit="exit" />
```

### Propagation

When a parent sets `initial` and `animate` to variant names, all `motion` children with matching variant keys inherit those states — no need to pass `initial`/`animate` to each child.

```tsx
const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

<motion.ul variants={container} initial="hidden" animate="visible">
  {items.map((i) => <motion.li key={i.id} variants={item} />)}
</motion.ul>
```

### Dynamic variants with `custom`

Pass a `custom` value to make variants data-driven. The variant function receives `custom` as its argument.

```tsx
const cardVariants = {
  hidden: (index: number) => ({
    opacity: 0,
    x: index % 2 === 0 ? -60 : 60,
  }),
  visible: { opacity: 1, x: 0 },
};

{cards.map((card, index) => (
  <motion.div key={card.id} custom={index} variants={cardVariants} initial="hidden" animate="visible" />
))}
```

`animate` also accepts an array of variant names — properties are merged, later entries win on conflict.

---

## Orchestration

Control timing relationships between parent and child animations via `transition` on the parent variant.

| Property | Effect |
|----------|--------|
| `when: "beforeChildren"` | Parent completes, then children start |
| `when: "afterChildren"` | Children complete, then parent animates |
| `delayChildren: 0.3` | Delay all children by 0.3s |
| `staggerChildren: 0.08` | Stagger each child by 0.08s |

```tsx
const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { when: "beforeChildren", staggerChildren: 0.1, delayChildren: 0.2 },
  },
};
```

### `stagger()` function

Provides fine-grained stagger control. Import from `"motion/react"`.

```tsx
import { stagger, useAnimate } from "motion/react";

const [scope, animate] = useAnimate();
animate("li", { opacity: 1 }, { delay: stagger(0.1, { from: "center" }) });
```

| `from` value | Effect |
|-------------|--------|
| `"first"` (default) | Stagger from index 0 forward |
| `"last"` | Stagger from last item backward |
| `"center"` | Stagger outward from the middle |
| `number` | Stagger outward from a specific index |

---

## useAnimate Hook

Imperative animation control. Use when declarative props are insufficient — sequencing, programmatic triggers, or animating elements outside the component tree.

```tsx
import { useAnimate, stagger } from "motion/react";

function Component() {
  const [scope, animate] = useAnimate();

  const handleClick = async () => {
    await animate(scope.current, { x: 100 });
    await animate("li", { opacity: 1 }, { delay: stagger(0.05) });
  };

  return (
    <div ref={scope}>
      <ul>{items.map((i) => <li key={i.id}>{i.label}</li>)}</ul>
      <button onClick={handleClick}>Animate</button>
    </div>
  );
}
```

`scope` scopes CSS selector queries — `"li"` finds only `li` elements inside `scope.current`.

### Sequences

Pass an array of `[target, keyframes, options]` tuples. Each step starts after the previous completes by default.

```tsx
await animate([
  [scope.current, { opacity: 1 }],
  ["h1", { x: 0 }, { duration: 0.4 }],
  ["p", { opacity: 1 }, { delay: stagger(0.05), at: "-0.2" }],
]);
```

`at` controls when a step starts relative to the sequence:
- `at: 0.5` — start at 0.5s from sequence start
- `at: "-0.2"` — start 0.2s before the previous step ends
- `at: "<"` — start at the same time as the previous step

### Playback controls

`animate()` returns `AnimationPlaybackControls`.

```tsx
import type { AnimationPlaybackControls } from "motion/react";

const animation = animate(element, { x: 100 }, { duration: 2 });

animation.pause();
animation.play();
animation.stop();
animation.complete();  // jump to end state
animation.cancel();    // revert to initial state
animation.time = 1;    // seek to 1 second
animation.speed = -1;  // play in reverse

await animation;       // resolves when complete
```

---

## MotionValue as Child

Render a `MotionValue` directly as a child of a `motion` element to display its current value as text — enables smooth counter animations without re-rendering.

```tsx
import { motion, useMotionValue, useTransform, animate } from "motion/react";

function Counter({ from = 0, to = 100 }: { from?: number; to?: number }) {
  const count = useMotionValue(from);
  const rounded = useTransform(count, (v) => Math.round(v));

  useEffect(() => {
    const controls = animate(count, to, { duration: 1.5, ease: "easeOut" });
    return controls.stop;
  }, [to]);

  return <motion.span>{rounded}</motion.span>;
}
```

`useTransform` maps one MotionValue to another — use it to format, round, or map value ranges.

```tsx
// Map scroll progress (0–1) to rotation (0–360deg)
const { scrollYProgress } = useScroll();
const rotate = useTransform(scrollYProgress, [0, 1], [0, 360]);
<motion.div style={{ rotate }} />
```

---

## Quick Reference

| Goal | Prop / API |
|------|-----------|
| Animate on mount | `initial` + `animate` |
| Animate on state change | `animate` with dynamic value |
| Animate on unmount | `exit` inside `AnimatePresence` |
| Animate on hover / press / focus | `whileHover` / `whileTap` / `whileFocus` |
| Animate on scroll into view | `whileInView` |
| Named reusable states | `variants` |
| Stagger children | `variants` + `staggerChildren` in transition |
| Imperative / sequenced | `useAnimate` |
| Smooth number display | `useMotionValue` + `useTransform` as child |
| Animate CSS variable | `animate={{ "--var": value } as any}` |
| Animate to `height: auto` | `animate={{ height: "auto" }}` |
| Skip enter animation | `initial={false}` |
| Swap components with exit | `AnimatePresence` + unique `key` |
| Control pivot point | `style={{ originX, originY }}` |
