# Production Animation Recipes

Sources: Motion.dev documentation (2025-2026), Saffer (Microinteractions), production patterns from Linear, Vercel, Notion
Covers: page transitions, modals, toasts, staggered lists, tabs, accordions, shared element transitions, button state machines, SVG drawing, drag-to-dismiss, 3D tilt, reusable fade-in wrapper.

## 1. Page Transitions — `AnimatePresence mode="wait"`

Use `mode="wait"` so the outgoing page fully exits before the incoming page enters.

**Next.js App Router** — wrap `{children}` in a Client Component layout:

```tsx
"use client";
import { AnimatePresence, motion } from "motion/react";
import { usePathname } from "next/navigation";

const v = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.2, ease: "easeOut" } },
  exit:    { opacity: 0, y: -8, transition: { duration: 0.15 } },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <html><body>
      <AnimatePresence mode="wait">
        <motion.main key={path} variants={v} initial="initial" animate="animate" exit="exit">
          {children}
        </motion.main>
      </AnimatePresence>
    </body></html>
  );
}
```

**React Router v6** — pass `location` as key to `<Routes>`. The `wrap` helper applies the same fade+slide to every route element:

```tsx
import { AnimatePresence, motion } from "motion/react";
import { Routes, Route, useLocation } from "react-router-dom";

const wrap = (el: React.ReactNode) => (
  <motion.div initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: 12 }} transition={{ duration: 0.2 }}>{el}</motion.div>
);
export function AnimatedRoutes() {
  const loc = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={loc} key={loc.pathname}>
        <Route path="/" element={wrap(<Home />)} />
        <Route path="/about" element={wrap(<About />)} />
      </Routes>
    </AnimatePresence>
  );
}
```

**Gotcha:** `AnimatePresence` must live in a Client Component. The `key` must change on every route change.

## 2. Modal / Dialog Animation

Fade the overlay, spring the panel. Lock body scroll while open.

```tsx
import { AnimatePresence, motion } from "motion/react";
import { useEffect } from "react";

export function Modal({ isOpen, onClose, children }: { isOpen: boolean; onClose: () => void; children: React.ReactNode }) {
  useEffect(() => {
    document.body.style.overflow = isOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [isOpen]);
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div key="o" className="fixed inset-0 z-40 bg-black/50"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }} onClick={onClose} />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
            <motion.div className="bg-white rounded-xl shadow-2xl w-full max-w-md pointer-events-auto"
              initial={{ opacity: 0, scale: 0.95, y: 16 }} animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 16 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}>
              {children}
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
```

**Gotcha:** `pointer-events-none` on the centering wrapper, `pointer-events-auto` on the panel — otherwise overlay clicks pass through to the panel.

## 3. Toast / Notification Entry

Slide in from the right, auto-dismiss, reflow the stack with `layout`.

```tsx
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";

export function ToastStack() {
  const [toasts, setToasts] = useState<{ id: string; msg: string }[]>([]);
  const remove = (id: string) => setToasts((p) => p.filter((t) => t.id !== id));
  const add = (msg: string) => { const id = crypto.randomUUID(); setToasts((p) => [...p, { id, msg }]); setTimeout(() => remove(id), 3500); };
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 items-end">
      <AnimatePresence initial={false}>
        {toasts.map((t) => (
          <motion.div key={t.id} layout
            initial={{ opacity: 0, x: 48 }} animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 48 }} transition={{ type: "spring", stiffness: 380, damping: 28 }}
            className="bg-slate-900 text-white text-sm px-4 py-3 rounded-lg shadow-lg cursor-pointer"
            onClick={() => remove(t.id)}>
            {t.msg}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
```

**Gotcha:** `layout` on each toast makes the stack reflow smoothly on dismiss. `initial={false}` prevents entrance animations on pre-populated toasts.

## 4. Staggered List Entrance

Propagate animation state from parent to children using `variants`.

```tsx
import { AnimatePresence, motion } from "motion/react";

const list = { hidden: {}, visible: { transition: { staggerChildren: 0.06, delayChildren: 0.1 } } };
const item = {
  hidden:  { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } },
  exit:    { opacity: 0, x: -20, transition: { duration: 0.15 } },
};

export function StaggeredList({ items }: { items: { id: string; label: string }[] }) {
  return (
    <motion.ul variants={list} initial="hidden" animate="visible">
      <AnimatePresence>
        {items.map((i) => (
          <motion.li key={i.id} variants={item} layout>{i.label}</motion.li>
        ))}
      </AnimatePresence>
    </motion.ul>
  );
}
```

**Gotcha:** `staggerChildren` only works when parent and children share matching variant state names.

## 5. Tab Content Switcher

Slide content in the direction of the selected tab using `custom` to pass direction into variants.

```tsx
import { AnimatePresence, motion } from "motion/react";
import { useState, useRef } from "react";

const tabs = ["Overview", "Activity", "Settings"];

export function TabSwitcher() {
  const [active, setActive] = useState(0);
  const prev = useRef(0);
  const dir = active > prev.current ? 1 : -1;
  const change = (i: number) => { prev.current = active; setActive(i); };
  return (
    <div>
      <div className="flex gap-4 border-b mb-4">
        {tabs.map((t, i) => (
          <button key={t} onClick={() => change(i)}
            className={i === active ? "font-semibold border-b-2 border-indigo-600" : "text-slate-500"}>
            {t}
          </button>
        ))}
      </div>
      <div className="overflow-hidden">
        <AnimatePresence mode="wait" custom={dir}>
          <motion.div key={active} custom={dir}
            initial={(d: number) => ({ opacity: 0, x: d * 24 })}
            animate={{ opacity: 1, x: 0 }}
            exit={(d: number) => ({ opacity: 0, x: d * -24 })}
            transition={{ duration: 0.2, ease: "easeInOut" }}>
            <p>Content for {tabs[active]}</p>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
```

**Gotcha:** Pass `custom` to both `AnimatePresence` and the `motion.div`. Without `overflow-hidden` on the container, sliding content bleeds outside the panel.

## 6. Accordion / Collapsible

Animate `height` from `0` to `"auto"`. Keep `overflow: hidden` on the animated element.

```tsx
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";

export function AccordionItem({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-slate-200">
      <button className="w-full flex justify-between items-center py-4 font-medium text-left"
        onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        {title}
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>▾</motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25, ease: "easeInOut" }}
            style={{ overflow: "hidden" }}>
            <div className="pb-4 text-slate-600">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

**Gotcha:** `overflow: hidden` must be on the `motion.div`, not the inner wrapper. `initial={false}` skips the entrance animation on first render.

## 7. Shared Element Transition (Card → Detail)

`layoutId` morphs a card into a full-screen detail view. Keep the source card in the DOM during the transition.

```tsx
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";

const cards = [{ id: "a", title: "Alpha", color: "#6366f1" }, { id: "b", title: "Beta", color: "#f59e0b" }];

export function CardGrid() {
  const [sel, setSel] = useState<string | null>(null);
  const active = cards.find((c) => c.id === sel);
  return (
    <>
      <div className="grid grid-cols-2 gap-4">
        {cards.map((c) => (
          <motion.div key={c.id} layoutId={`card-${c.id}`} onClick={() => setSel(c.id)}
            className="h-32 rounded-xl cursor-pointer" style={{ backgroundColor: c.color }} />
        ))}
      </div>
      <AnimatePresence>
        {active && (
          <>
            <motion.div className="fixed inset-0 z-40 bg-black/60"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setSel(null)} />
            <motion.div layoutId={`card-${active.id}`}
              className="fixed inset-8 z-50 rounded-2xl flex items-end p-6"
              style={{ backgroundColor: active.color }}>
              <h2 className="text-white text-2xl font-bold">{active.title}</h2>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
```

**Gotcha:** The `layoutId` string must be identical in both the grid and expanded views. Do not unmount the grid card while the expanded view is open.

## 8. Button State Machine

Cycle idle → loading → success with `AnimatePresence mode="wait"`.

```tsx
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";

type S = "idle" | "loading" | "success";
const labels: Record<S, string> = { idle: "Submit", loading: "Saving…", success: "Saved" };

export function StatefulButton({ onSubmit }: { onSubmit: () => Promise<void> }) {
  const [s, setS] = useState<S>("idle");
  const handle = async () => {
    if (s !== "idle") return;
    setS("loading"); await onSubmit(); setS("success");
    setTimeout(() => setS("idle"), 2000);
  };
  return (
    <button onClick={handle} disabled={s !== "idle"}
      className="relative h-10 px-6 rounded-lg bg-indigo-600 text-white font-medium overflow-hidden disabled:opacity-80">
      <AnimatePresence mode="wait" initial={false}>
        <motion.span key={s} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.15 }} className="block">
          {labels[s]}
        </motion.span>
      </AnimatePresence>
    </button>
  );
}
```

**Gotcha:** `overflow-hidden` on the button clips the entering/exiting label text during the vertical slide.

## 9. SVG Path Drawing

Animate `pathLength` from `0` to `1` to draw SVG paths — checkmarks, progress rings, illustrative lines.

```tsx
import { motion } from "motion/react";

export function AnimatedCheckmark() {
  return (
    <svg viewBox="0 0 52 52" className="w-12 h-12 text-green-500" fill="none">
      <motion.circle cx="26" cy="26" r="24" stroke="currentColor" strokeWidth="3"
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.5, ease: "easeOut" }} />
      <motion.path d="M14 27l8 8L38 18" stroke="currentColor" strokeWidth="3"
        strokeLinecap="round" strokeLinejoin="round"
        initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.4, ease: "easeOut" }} />
    </svg>
  );
}
```

**Gotcha:** SVG elements must have `fill="none"` and a `stroke` for `pathLength` to be visible. Motion normalizes path length to a `0–1` range regardless of the actual SVG path length.

## 10. Drag-to-Dismiss

Drag a card horizontally; dismiss when offset exceeds a threshold.

```tsx
import { AnimatePresence, motion, useMotionValue, useTransform } from "motion/react";
import { useState } from "react";

const THRESHOLD = 120;

function Card({ id, label, onDismiss }: { id: string; label: string; onDismiss: (id: string) => void }) {
  const x = useMotionValue(0);
  const opacity = useTransform(x, [-THRESHOLD, 0, THRESHOLD], [0, 1, 0]);
  const rotate = useTransform(x, [-200, 200], [-8, 8]);
  return (
    <motion.div drag="x" dragConstraints={{ left: 0, right: 0 }} style={{ x, opacity, rotate }}
      onDragEnd={(_, i) => { if (Math.abs(i.offset.x) > THRESHOLD) onDismiss(id); }}
      className="bg-white rounded-xl shadow-md p-4 cursor-grab active:cursor-grabbing select-none">
      {label}
    </motion.div>
  );
}

export function DismissStack() {
  const [items, setItems] = useState([{ id: "1", label: "Drag to dismiss" }, { id: "2", label: "Or this one" }]);
  const remove = (id: string) => setItems((p) => p.filter((i) => i.id !== id));
  return (
    <AnimatePresence>
      {items.map((i) => <Card key={i.id} {...i} onDismiss={remove} />)}
    </AnimatePresence>
  );
}
```

**Gotcha:** `dragConstraints={{ left: 0, right: 0 }}` creates a rubber-band snap-back when the threshold is not met.

## 11. Hover Card with 3D Tilt

Map mouse position relative to the card center to `rotateX`/`rotateY`, smoothed with `useSpring`.

```tsx
import { motion, useMotionValue, useTransform, useSpring } from "motion/react";
import { useRef } from "react";

export function TiltCard({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const rotateX = useSpring(useTransform(my, [-0.5, 0.5], [8, -8]), { stiffness: 300, damping: 30 });
  const rotateY = useSpring(useTransform(mx, [-0.5, 0.5], [-8, 8]), { stiffness: 300, damping: 30 });

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;
    const r = ref.current.getBoundingClientRect();
    mx.set((e.clientX - r.left) / r.width - 0.5);
    my.set((e.clientY - r.top) / r.height - 0.5);
  };

  return (
    <motion.div ref={ref} onMouseMove={onMove} onMouseLeave={() => { mx.set(0); my.set(0); }}
      style={{ rotateX, rotateY, transformStyle: "preserve-3d", perspective: 800 }}
      className="rounded-xl bg-white shadow-lg p-6">
      {children}
    </motion.div>
  );
}
```

**Gotcha:** `transformStyle: "preserve-3d"` is required for child elements to participate in the 3D space.

## 12. Reusable FadeIn Component

Generic scroll-triggered fade-in wrapper with configurable direction, delay, and duration.

```tsx
import { motion } from "motion/react";

type Dir = "up" | "down" | "left" | "right";
const offsets: Record<Dir, object> = { up: { y: 20 }, down: { y: -20 }, left: { x: 20 }, right: { x: -20 } };

export function FadeIn({ children, direction = "up", delay = 0, duration = 0.4, className }:
  { children: React.ReactNode; direction?: Dir; delay?: number; duration?: number; className?: string }) {
  return (
    <motion.div initial={{ opacity: 0, ...offsets[direction] }} whileInView={{ opacity: 1, x: 0, y: 0 }}
      viewport={{ once: true, margin: "-60px" }} transition={{ duration, delay, ease: "easeOut" }}
      className={className}>
      {children}
    </motion.div>
  );
}

// <FadeIn direction="up" delay={0.1}><HeroHeading /></FadeIn>
// <FadeIn direction="up" delay={0.2}><HeroSubtitle /></FadeIn>
// <FadeIn direction="up" delay={0.3}><CTAButton /></FadeIn>
```

**Gotcha:** `viewport={{ once: true }}` ensures the animation fires only once. `margin: "-60px"` triggers the reveal slightly before the element is fully visible.

## Anti-Patterns

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| `from "framer-motion"` import | Breaks with Motion v11+ | Use `from "motion/react"` |
| Missing `key` on `AnimatePresence` children | Exit animations never run | Assign a unique, stable `key` to each child |
| `AnimatePresence` without `mode="wait"` on page transitions | Incoming and outgoing pages overlap | Add `mode="wait"` |
| Animating `height` without `overflow: hidden` | Content visible outside bounds | Set `overflow: hidden` on the animated element |
| `layoutId` on conditionally removed element | Shared element transition breaks | Keep source element in DOM during transition |
| Mouse tracking without `useSpring` | Jittery, mechanical tilt | Wrap transforms in `useSpring` |
| Long durations on micro-interactions | UI feels sluggish | Keep hover/tap transitions under 200ms |
| `whileInView` without `once: true` | Repeated entrance animations on scroll | Set `viewport={{ once: true }}` |
