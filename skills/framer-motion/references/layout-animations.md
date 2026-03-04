# Layout Animations

Sources: Motion.dev documentation (2025-2026), Nabors (Animation at Work)
Covers: the `layout` prop, layout types, `layoutId` shared element transitions, `LayoutGroup`, scroll containers, the `Reorder` component, and common gotchas.

## How the Layout Engine Works

Motion detects when a component's size or position changes between renders and animates the transition using FLIP (First, Last, Invert, Play). Unlike a basic FLIP implementation, Motion corrects for scale distortion on child elements, handles border radius, and coordinates transitions across unrelated components via `layoutId`.

Layout animations use `transform` (GPU-accelerated), not layout properties like `width` or `top`. The browser calculates the final layout once, then Motion plays the transform in reverse and releases it — no layout recalculation during animation.

```tsx
import { motion } from "motion/react";

<motion.div layout>
  {isExpanded && <p>Additional content</p>}
</motion.div>
```

## The `layout` Prop

Add `layout` to any `motion` element to opt it into automatic layout animation. Motion measures the element before and after the render, then animates the difference.

```tsx
import { motion, AnimatePresence } from "motion/react";

export const ExpandableCard = ({ isOpen }: { isOpen: boolean }) => (
  <motion.div
    layout
    className="bg-white rounded-xl shadow-md p-6 cursor-pointer"
    transition={{ type: "spring", stiffness: 300, damping: 30 }}
  >
    <motion.h2 layout="position" className="text-lg font-semibold">
      Card Title
    </motion.h2>
    <AnimatePresence>
      {isOpen && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="mt-4 text-slate-600"
        >
          Expanded content that causes the card to grow.
        </motion.p>
      )}
    </AnimatePresence>
  </motion.div>
);
```

Combine `layout` with `initial`, `animate`, and `exit` freely — they operate independently.

## Layout Types

Pass a string to `layout` to constrain which dimensions animate.

| Value | Animates | Use Case |
|-------|----------|----------|
| `true` | Position + size | General-purpose, default |
| `"position"` | Position only | Headings that shift when siblings change size |
| `"size"` | Size only | Containers that grow/shrink in place |
| `"preserve-aspect"` | Size, maintaining aspect ratio | Images, video thumbnails |

Use `layout="position"` on text elements inside a layout-animated container. Without it, text scales during the animation, producing a blurry appearance.

## `layoutId` — Shared Element Transitions

`layoutId` connects two separate component instances across the React tree. When one unmounts and another with the same `layoutId` mounts, Motion animates between them as if they are the same element. Use cases: card expanding to a modal, tab underline indicator, list item morphing into a detail panel.

```tsx
import { motion, AnimatePresence } from "motion/react";
import { useState } from "react";

const CARDS = [
  { id: "a", title: "Alpha", color: "bg-indigo-500" },
  { id: "b", title: "Beta", color: "bg-rose-500" },
];

export const CardGallery = () => {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <>
      <div className="flex gap-4">
        {CARDS.map((card) => (
          <motion.div
            key={card.id}
            layoutId={`card-${card.id}`}
            onClick={() => setSelected(card.id)}
            className={`${card.color} w-32 h-20 rounded-xl cursor-pointer`}
          />
        ))}
      </div>

      <AnimatePresence>
        {selected && (
          <motion.div
            layoutId={`card-${selected}`}
            className={`fixed inset-0 z-50 ${
              CARDS.find((c) => c.id === selected)!.color
            }`}
            onClick={() => setSelected(null)}
          />
        )}
      </AnimatePresence>
    </>
  );
};
```

The `layoutId` string must be unique within the `LayoutGroup` scope. Reusing the same `layoutId` on two simultaneously mounted elements causes undefined behavior.

## `LayoutGroup` — Synchronizing Layout Animations

`LayoutGroup` coordinates layout animations across components that do not share a parent. Without it, each component animates independently, causing visual desynchronization when multiple elements shift at once.

```tsx
import { motion, LayoutGroup } from "motion/react";

export const TabBar = ({ tabs, activeTab, onChange }: TabBarProps) => (
  <LayoutGroup>
    <div className="flex gap-1 p-1 bg-slate-100 rounded-lg">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className="relative px-4 py-2 text-sm font-medium rounded-md"
        >
          {activeTab === tab.id && (
            <motion.div
              layoutId="tab-indicator"
              className="absolute inset-0 bg-white rounded-md shadow-sm"
              transition={{ type: "spring", stiffness: 400, damping: 35 }}
            />
          )}
          <span className="relative z-10">{tab.label}</span>
        </button>
      ))}
    </div>
  </LayoutGroup>
);
```

### Namespacing with the `id` Prop

When rendering multiple independent instances of the same component, give each `LayoutGroup` a unique `id`. Motion prefixes all `layoutId` values inside with the group id, preventing cross-instance interference.

```tsx
<LayoutGroup id="primary-nav"><TabBar tabs={primaryTabs} /></LayoutGroup>
<LayoutGroup id="settings-nav"><TabBar tabs={settingsTabs} /></LayoutGroup>
```

## Layout Animation Patterns

### List Reorder with Smooth Reflow

```tsx
import { motion, AnimatePresence } from "motion/react";

export const FilterableList = ({ items }: { items: Item[] }) => (
  <ul className="space-y-2">
    <AnimatePresence>
      {items.map((item) => (
        <motion.li
          key={item.id}
          layout
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ type: "spring", stiffness: 300, damping: 28 }}
          className="bg-white rounded-lg p-4 shadow-sm"
        >
          {item.name}
        </motion.li>
      ))}
    </AnimatePresence>
  </ul>
);
```

### Accordion Expand / Collapse

```tsx
import { motion, AnimatePresence } from "motion/react";
import { useState } from "react";

export const Accordion = ({ title, children }: AccordionProps) => {
  const [open, setOpen] = useState(false);

  return (
    <motion.div layout className="border border-slate-200 rounded-lg overflow-hidden">
      <motion.button
        layout="position"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex justify-between items-center px-5 py-4 text-left font-medium"
      >
        {title}
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          ▾
        </motion.span>
      </motion.button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="px-5 pb-5 text-slate-600"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
```

The outer `motion.div` carries `layout` to animate the container height. Do not add `layout` to the expanding content itself — it will fight the container animation.

### Filter / Sort Smooth Reflow

```tsx
import { motion, AnimatePresence, LayoutGroup } from "motion/react";

export const SortableGrid = ({ items }: { items: GridItem[] }) => (
  <LayoutGroup>
    <motion.div layout className="grid grid-cols-3 gap-4">
      <AnimatePresence>
        {items.map((item) => (
          <motion.div
            key={item.id}
            layout
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ layout: { type: "spring", stiffness: 350, damping: 30 } }}
            className="bg-white rounded-xl p-4 shadow-sm"
          >
            {item.label}
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  </LayoutGroup>
);
```

Pass a `transition` with a `layout` key to control only the layout animation's spring, leaving other transitions unaffected.

## `layoutScroll` and `layoutRoot`

### `layoutScroll`

Add `layoutScroll` to any scrollable container that holds layout-animated children. Without it, Motion cannot account for the scroll offset when calculating element positions, causing elements to animate from incorrect starting points.

```tsx
<motion.div layoutScroll className="overflow-y-auto h-96">
  {items.map((item) => (
    <motion.div key={item.id} layout>
      {item.content}
    </motion.div>
  ))}
</motion.div>
```

### `layoutRoot`

`layoutRoot` marks a component as the boundary for layout measurements. Use it when a layout-animated subtree is inside a transformed parent (e.g., a modal that slides in). Without `layoutRoot`, Motion measures positions relative to the viewport, which breaks when the parent has a `transform` applied.

```tsx
<motion.div animate={{ y: isOpen ? 0 : "100%" }} className="fixed bottom-0 left-0 right-0">
  <motion.div layoutRoot>
    <motion.div layout>{content}</motion.div>
  </motion.div>
</motion.div>
```

## Callbacks

`onLayoutAnimationStart` and `onLayoutAnimationComplete` coordinate side effects with layout transitions. Both fire on the element that carries `layout`, not on children.

```tsx
<motion.div
  layout
  onLayoutAnimationStart={() => setInteractive(false)}
  onLayoutAnimationComplete={() => { setInteractive(true); analytics.track("panel_expanded"); }}
>
  {children}
</motion.div>
```

## Common Gotchas

### Border Radius Distortion

When Motion scales an element during layout animation, CSS `border-radius` values scale with it, producing an oval shape mid-animation. Fix by applying `border-radius` to an inner wrapper that does not carry `layout`.

```tsx
// Broken — border-radius distorts during scale correction
<motion.div layout className="rounded-xl">
  <Content />
</motion.div>

// Fixed — border-radius lives on a non-layout child
<motion.div layout>
  <div className="rounded-xl overflow-hidden">
    <Content />
  </div>
</motion.div>
```

Motion provides automatic scale correction for `borderRadius` and `boxShadow` when set as inline styles (not Tailwind classes). Use `style={{ borderRadius: "12px" }}` directly on the layout element for automatic correction.

### Box Shadow Distortion

The same scale distortion applies to `box-shadow`. Move the shadow to an inner element or use `style={{ boxShadow: "..." }}` for automatic correction.

### Fixed Positioning

Elements with `position: fixed` inside a layout-animated parent animate incorrectly because their position is relative to the viewport. Use `layoutRoot` on the nearest non-fixed ancestor to establish a correct measurement boundary.

### Performance with Many Layout-Animated Elements

Each layout-animated element requires a DOM measurement on every render. For lists with more than ~50 items:

1. Virtualize the list and do not apply `layout` to virtualized items.
2. Apply `layout` to the container only when individual item sizes do not change.
3. Use `layout="position"` instead of `layout={true}` when size is constant.

### Forwarding the Layout Prop

When wrapping a `motion` element in a custom component, forward `layout` and other motion props explicitly.

```tsx
// Broken — layout prop is swallowed
const Card = ({ children }: CardProps) => (
  <motion.div className="card">{children}</motion.div>
);

// Fixed — spread motion props through
const Card = ({ children, ...motionProps }: CardProps & MotionProps) => (
  <motion.div className="card" {...motionProps}>{children}</motion.div>
);
```

## The `Reorder` Component

`Reorder` provides drag-to-reorder list functionality with built-in layout animations. Use `Reorder.Group` as the list container and `Reorder.Item` for each draggable row.

```tsx
import { Reorder } from "motion/react";
import { useState } from "react";

export const DraggableList = () => {
  const [items, setItems] = useState(["Task A", "Task B", "Task C", "Task D"]);

  return (
    <Reorder.Group
      axis="y"
      values={items}
      onReorder={setItems}
      className="space-y-2 list-none p-0"
    >
      {items.map((item) => (
        <Reorder.Item
          key={item}
          value={item}
          className="bg-white rounded-lg px-4 py-3 shadow-sm cursor-grab active:cursor-grabbing select-none"
        >
          {item}
        </Reorder.Item>
      ))}
    </Reorder.Group>
  );
};
```

`Reorder.Group` requires `values` (the current array) and `onReorder` (a setter). The `axis` prop accepts `"x"` or `"y"`.

### Reorder with Drag Handle

To restrict dragging to a handle, use `useDragControls`. Set `dragListener={false}` on `Reorder.Item` and call `controls.start(e)` from the handle's `onPointerDown`.

```tsx
import { Reorder, useDragControls } from "motion/react";

const ReorderItem = ({ item }: { item: string }) => {
  const controls = useDragControls();
  return (
    <Reorder.Item value={item} dragListener={false} dragControls={controls}
      className="flex items-center gap-3 bg-white rounded-lg px-4 py-3 shadow-sm">
      <span className="cursor-grab" onPointerDown={(e) => controls.start(e)}>⠿</span>
      {item}
    </Reorder.Item>
  );
};
```

## Best Practices

### When to Use `layout`

- Lists where items are added, removed, or reordered.
- Containers that grow or shrink based on content (accordions, expandable cards).
- Sidebar or panel width changes driven by user interaction.

### When to Use `layoutId`

- An element that travels between two distinct DOM locations (grid item → modal).
- A persistent indicator that moves between siblings (tab underline, selected highlight).
- Any transition where the user needs to perceive continuity between two states.

### When NOT to Use Layout Animations
- **Continuous data updates** (live charts, real-time feeds): layout animations fire on every render, causing constant measurement overhead.
- **Virtualized lists**: layout animations conflict with the mount/unmount cycle of virtualization. Animate only the container.
- **CSS-only transitions are sufficient**: if an element only changes opacity or color, `layout` adds unnecessary cost. Use `animate` with those properties directly.

### Transition Tuning

| Element | Stiffness | Damping |
|---------|-----------|---------|
| Small indicator (tab underline) | 400–500 | 35–40 |
| Card or panel | 280–350 | 28–32 |
| Full-screen expand | 200–260 | 24–28 |
| Heavy container | 150–200 | 20–24 |

Pass the transition via the `layout` key to avoid affecting other animated properties:

```tsx
<motion.div
  layout
  animate={{ opacity: 1 }}
  transition={{
    layout: { type: "spring", stiffness: 300, damping: 30 },
    opacity: { duration: 0.2 },
  }}
/>
```

## Anti-Patterns

- **Applying `layout` to every element**: adds measurement cost without benefit. Only opt in elements that actually change position or size.
- **Nesting `layoutId` elements without `LayoutGroup`**: causes cross-component interference when the same `layoutId` string appears in multiple independent component trees.
- **Animating layout properties alongside `layout`**: setting `animate={{ width: "100%" }}` on an element that also has `layout` creates conflicting animations. Use `layout` exclusively and let Motion handle the transition.
- **Missing `layoutScroll` on scroll containers**: produces incorrect start positions, making elements appear to jump from the wrong location.
- **Forgetting `AnimatePresence` around conditionally rendered `layoutId` elements**: without it, the exit animation does not play and the shared transition breaks.
