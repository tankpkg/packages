# Gestures and Drag

Sources: Motion.dev documentation (2025-2026), Saffer (Microinteractions)

Covers: gesture animation props, hover, tap, pan, focus, drag, useDragControls, whileInView, event propagation, accessibility, and production recipes.

## Gesture Animation Props Overview

Motion for React provides five `while-` props that apply animation targets whenever a gesture is active. Each accepts an inline animation object or a variant label string.

```tsx
import { motion } from "motion/react";

<motion.div
  whileHover="hovered"
  whileTap="pressed"
  whileFocus="focused"
  whileDrag="dragging"
  whileInView="visible"
  variants={{
    hovered: { scale: 1.04, boxShadow: "0 8px 24px rgba(0,0,0,0.12)" },
    pressed: { scale: 0.97 },
    focused: { outline: "2px solid var(--ring)" },
    dragging: { opacity: 0.85, cursor: "grabbing" },
    visible: { opacity: 1, y: 0 },
  }}
  initial={{ opacity: 0, y: 20 }}
/>
```

When a variant label is used, the animation propagates to all descendant `motion` components that share the same variant map — enabling complex hover states across card layouts without prop drilling.

| Prop | Gesture | Events |
|------|---------|--------|
| `whileHover` | Pointer enters element | `onHoverStart`, `onHoverEnd` |
| `whileTap` | Pointer pressed down | `onTap`, `onTapStart`, `onTapCancel` |
| `whileFocus` | Element receives focus | — |
| `whileDrag` | Element is being dragged | `onDrag`, `onDragStart`, `onDragEnd` |
| `whileInView` | Element enters viewport | `onViewportEnter`, `onViewportLeave` |

---

## Hover

`whileHover` activates while the pointer is over the element. Use `onHoverStart` and `onHoverEnd` for side effects such as prefetching data.

```tsx
<motion.div
  whileHover={{ y: -4, boxShadow: "0 12px 32px rgba(0,0,0,0.15)" }}
  transition={{ type: "spring", stiffness: 400, damping: 28 }}
  onHoverStart={() => prefetchRoute("/detail")}
/>
```

For card hover states that reveal multiple child elements, use variant propagation:

```tsx
const card = { rest: { scale: 1 }, hover: { scale: 1.02 } };
const overlay = { rest: { opacity: 0 }, hover: { opacity: 1 } };

<motion.div variants={card} initial="rest" whileHover="hover" className="relative">
  <img src={src} alt={alt} className="w-full h-48 object-cover" />
  <motion.div variants={overlay} transition={{ duration: 0.2 }}
    className="absolute inset-0 bg-black/40 flex items-center justify-center">
    <span className="text-white font-semibold">View Details</span>
  </motion.div>
</motion.div>
```

---

## Tap

`whileTap` activates while the pointer is held down and reverses on release. Pressing Enter on a focused element also triggers tap events, making keyboard accessibility automatic for `<button>` and `role="button"` elements.

```tsx
<motion.button
  whileTap={{ scale: 0.96 }}
  transition={{ type: "spring", stiffness: 500, damping: 35 }}
>
  Confirm
</motion.button>
```

`onTapCancel` fires when the pointer is released outside the element, or when the element is inside a draggable container and the pointer moves more than 3px — preventing accidental taps during scroll.

---

## Pan

Pan tracks pointer movement after the initial press without moving the element. Use it for custom sliders or drawing surfaces. There is no `whilePan` prop — respond to events directly.

```tsx
<motion.div
  onPan={(event, info) => updateValue(info.offset.x)}
  onPanEnd={(event, info) => commitValue(info.velocity.x)}
  style={{ touchAction: "none" }} // required for touch devices
/>
```

`info` contains `point` (absolute), `delta` (since last event), `offset` (total from start), and `velocity`. Set `touch-action: none` via inline style or CSS — without it, the browser intercepts touch events for scrolling.

---

## Focus

`whileFocus` activates when the element receives focus. Motion follows `:focus-visible` rules — the animation triggers for keyboard navigation but not mouse clicks on most browsers.

```tsx
<motion.input
  whileFocus={{ scale: 1.01, borderColor: "var(--ring)" }}
  transition={{ duration: 0.15 }}
/>
```

---

## Drag

Enable dragging with the `drag` prop: `true` for free movement, `"x"` for horizontal, `"y"` for vertical.

```tsx
<motion.div
  drag="x"
  dragConstraints={{ left: -200, right: 200 }}
  dragElastic={0.2}
  dragMomentum={true}
  whileDrag={{ scale: 1.05, cursor: "grabbing" }}
/>
```

| Prop | Type | Description |
|------|------|-------------|
| `drag` | `true \| "x" \| "y"` | Enables drag and constrains axis |
| `dragConstraints` | `object \| ref` | Bounding box or container ref |
| `dragElastic` | `number` | Resistance beyond constraints (0–1, default 0.5) |
| `dragMomentum` | `boolean` | Continue moving after release (default true) |
| `dragTransition` | `InertiaOptions` | Tune post-release deceleration |
| `dragSnapToOrigin` | `boolean` | Snap back to starting position on release |

Constrain drag to a parent container by passing a ref — Motion reads the bounding box at drag start:

```tsx
const constraintsRef = useRef(null);

<div ref={constraintsRef} className="relative w-full h-64">
  <motion.div drag dragConstraints={constraintsRef} dragElastic={0.1}
    className="absolute w-16 h-16 bg-indigo-500 rounded-full cursor-grab" />
</div>
```

Snap to a grid with `dragTransition.modifyTarget`:

```tsx
<motion.div
  drag="x"
  dragTransition={{ modifyTarget: (t) => Math.round(t / 100) * 100 }}
/>
```

---

## useDragControls

Start a drag from an external element — useful for drag handles separate from the draggable content.

```tsx
import { motion, useDragControls } from "motion/react";

function DraggablePanel() {
  const controls = useDragControls();

  return (
    <motion.div drag dragControls={controls} dragListener={false} className="panel">
      <div onPointerDown={(e) => controls.start(e)}
        className="drag-handle cursor-grab px-4 py-2 bg-slate-100 rounded-t-lg">
        ⠿ Drag here
      </div>
      <div className="p-4">Panel content</div>
    </motion.div>
  );
}
```

Set `dragListener={false}` to prevent the element body from initiating drags — only the handle triggers `controls.start(e)`.

---

## whileInView

`whileInView` activates when the element enters the viewport. Configure detection with the `viewport` prop.

```tsx
<motion.section
  initial={{ opacity: 0, y: 40 }}
  whileInView={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.5, ease: "easeOut" }}
  viewport={{ once: true, amount: 0.3 }}
/>
```

| Option | Type | Description |
|--------|------|-------------|
| `once` | `boolean` | Animate only the first time element enters |
| `amount` | `number \| "some" \| "all"` | Fraction of element visible to trigger |
| `margin` | `string` | Expand/contract detection zone, e.g. `"-100px 0px"` |
| `root` | `ref` | Scroll container ref (default: browser viewport) |

Use `onViewportEnter` and `onViewportLeave` for side effects such as tracking impressions or pausing video.

---

## Event Propagation

Gesture events bubble by default. In nested interactive elements, stop propagation at the pointer level using the capture phase:

```tsx
<motion.div whileTap={{ scale: 0.98 }} className="card">
  <button
    onPointerDownCapture={(e) => e.stopPropagation()}
    onClick={handleAction}
  >
    Action
  </button>
</motion.div>
```

When both parent and child are `motion` elements, use the `propagate` prop:

```tsx
<motion.div whileTap={{ scale: 0.97 }}>
  <motion.button whileTap={{ scale: 0.94 }} propagate={{ tap: false }}>
    Nested Button
  </motion.button>
</motion.div>
```

---

## SVG Filter Note

Gesture recognition does not work on SVG `<filter>` elements. Apply gesture props to a parent element and propagate via variants:

```tsx
// Incorrect
<motion.feGaussianBlur whileHover={{ stdDeviation: 0 }} />

// Correct
<motion.g whileHover="hovered" variants={{ hovered: {} }}>
  <motion.feGaussianBlur
    variants={{ hovered: { stdDeviation: 0 }, rest: { stdDeviation: 4 } }}
    initial="rest"
  />
</motion.g>
```

---

## Gesture Recipes

### Button with Hover Lift and Tap Shrink

```tsx
<motion.button
  whileHover={{ y: -2, boxShadow: "0 6px 20px rgba(99,102,241,0.35)" }}
  whileTap={{ scale: 0.97, y: 0 }}
  transition={{ type: "spring", stiffness: 400, damping: 28 }}
  className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg font-medium"
>
  Get Started
</motion.button>
```

### Swipe-to-Dismiss Card

```tsx
<motion.div
  drag="x"
  dragConstraints={{ left: 0, right: 0 }}
  dragElastic={0.4}
  onDragEnd={(_, info) => { if (Math.abs(info.offset.x) > 120) onDismiss(); }}
  whileDrag={{ scale: 1.02 }}
  className="card cursor-grab active:cursor-grabbing"
>
  Swipe to dismiss
</motion.div>
```

### Scroll-Reveal Stagger

```tsx
const container = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

<motion.ul variants={container} initial="hidden" whileInView="visible"
  viewport={{ once: true, amount: 0.2 }}>
  {items.map((i) => <motion.li key={i.id} variants={item}>{i.content}</motion.li>)}
</motion.ul>
```

### Interactive Card with Propagated Hover

```tsx
const cardV = { rest: { scale: 1, y: 0 }, hover: { scale: 1.02, y: -4 } };
const badgeV = { rest: { opacity: 0, scale: 0.8 }, hover: { opacity: 1, scale: 1 } };
const arrowV = { rest: { x: 0 }, hover: { x: 4 } };

function FeatureCard({ title, description, badge }: FeatureCardProps) {
  return (
    <motion.div variants={cardV} initial="rest" whileHover="hover"
      transition={{ type: "spring", stiffness: 350, damping: 25 }}
      className="relative p-6 bg-white rounded-2xl border border-slate-200 shadow-sm cursor-pointer">
      <motion.span variants={badgeV}
        className="absolute top-4 right-4 text-xs px-2 py-1 bg-indigo-50 text-indigo-600 rounded-full">
        {badge}
      </motion.span>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-slate-500 text-sm mb-4">{description}</p>
      <div className="flex items-center gap-1 text-indigo-600 text-sm font-medium">
        Learn more <motion.span variants={arrowV} transition={{ duration: 0.15 }}>→</motion.span>
      </div>
    </motion.div>
  );
}
```

---

## Accessibility

Tap events fire on keyboard Enter for `<button>` and `role="button"` elements automatically. For custom non-interactive elements, add `role="button"` and `tabIndex={0}`:

```tsx
<motion.div role="button" tabIndex={0} whileTap={{ scale: 0.97 }} onTap={handleAction}>
  Activate
</motion.div>
```

Respect reduced motion preferences by disabling gesture animations:

```tsx
import { useReducedMotion } from "motion/react";

function AccessibleCard() {
  const reduce = useReducedMotion();
  return (
    <motion.div
      whileHover={reduce ? {} : { y: -4, scale: 1.02 }}
      whileTap={reduce ? {} : { scale: 0.97 }}
    />
  );
}
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Correction |
|--------------|---------|------------|
| Drag without `touch-action: none` | Browser intercepts touch for scroll | Add `style={{ touchAction: "none" }}` |
| `dragMomentum` on tightly constrained axis | Element slams into boundary | Set `dragMomentum={false}` or tune `dragTransition` |
| Nested tap without propagation control | Parent and child both animate | Use `onPointerDownCapture` + `stopPropagation` |
| Gestures on SVG filter elements | Events not recognized | Apply to parent, propagate via variants |
| High `dragElastic` on desktop UIs | Rubber-band feel is unexpected | Keep `dragElastic` below 0.2 for desktop |
| `whileInView` without `once: true` on entry animations | Re-animates on scroll back | Set `viewport={{ once: true }}` |
