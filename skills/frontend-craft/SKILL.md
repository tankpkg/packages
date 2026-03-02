---
name: frontend-craft
description: |
  Expert frontend craft for building apps that make users go "wow, this is
  fast and easy." Covers micro-interactions, perceived performance, premium
  component patterns, visual polish, state choreography, component
  architecture, and shadcn registry discovery via the CLI.
  Synthesizes Saffer (Microinteractions), Wathan/Schoger (Refactoring UI),
  Krug (Don't Make Me Think), Yablonski (Laws of UX), Nabors (Animation at
  Work), Tidwell (Designing Interfaces), plus production patterns from
  Linear, Vercel, Notion, and the external component ecosystem.

  Trigger phrases: "micro-interaction", "make it feel fast", "loading state",
  "skeleton screen", "optimistic update", "framer motion", "animation",
  "command palette", "data table", "TanStack Table", "toast notification",
  "sonner", "cmdk", "shadcn", "UI polish", "wow factor", "delightful UI",
  "premium feel", "perceived performance", "empty state", "page transition",
  "error state", "form UX", "modal pattern", "visual polish", "spring animation",
  "aceternity", "aceternity ui", "3d card", "parallax scroll", "text effect",
  "animated background", "hero section", "spotlight effect", "aurora background",
  "bento grid", "card hover", "typewriter effect", "text generate",
  "floating navbar", "background beams", "lamp effect", "sparkles",
  "shadcn space", "shadcnspace", "dashboard blocks", "marketing blocks",
  "landing page blocks", "pricing section", "testimonials", "feature section",
  "animated button", "animated component", "21st.dev", "21st dev",
  "react bits", "reactbits", "fancy components", "fancycomponents",
  "physics animation",
  "variable font", "letter swap", "gravity effect", "elastic line",
  "scramble text", "pixel trail", "css buttons", "neumorphism"
---

# Frontend Craft

## Core Philosophy

1. **Speed is a feeling, not a metric** — Users judge speed by perceived
   responsiveness. Optimistic updates, skeleton screens, and instant feedback
   matter more than raw milliseconds.
2. **Every interaction deserves feedback** — Buttons press, toggles snap,
   lists stagger. Silent UI feels broken. Animated UI feels alive.
3. **Polish compounds** — One shadow system, one spacing scale, one motion
   language. Consistency across details creates the "premium" feeling.
4. **States are first-class UI** — Loading, empty, error, and success states
   are not afterthoughts. Design them with the same care as the happy path.
5. **Accessibility is not optional** — Reduced motion, focus management,
   keyboard navigation, screen readers. Premium means premium for everyone.

## Quick-Start: Make It Feel Fast

### Problem: "The app feels slow"

1. Add skeleton screens matching content layout for anything over 200ms.
   -> See `references/perceived-performance.md`
2. Implement optimistic updates for user-initiated mutations.
   -> See `references/perceived-performance.md`
3. Prefetch routes on hover with `router.prefetch(href)`.
   -> See `references/perceived-performance.md`

### Problem: "The UI feels dead"

1. Check Aceternity UI catalog for pre-built animated components first.
   -> See `references/aceternity-ui-catalog.md`
2. Add `whileHover` scale 1.02 and `whileTap` scale 0.98 to buttons.
3. Use staggered entrance animations for lists (staggerChildren: 0.05).
4. Animate page transitions with `AnimatePresence mode="wait"`.
   -> See `references/micro-interactions.md`

### Problem: "I need a premium data table"

1. Use TanStack Table v8 (headless) with virtual scrolling for 100+ rows.
2. Add column resizing, faceted filtering, and inline editing.
3. Wrap in shadcn/ui DataTable component pattern.
   -> See `references/premium-components.md`

### Problem: "I need an animated hero / landing section"

1. Browse Aceternity components: `hero-parallax`, `lamp`, `spotlight`,
   `aurora-background`, `background-beams`, `background-gradient-animation`.
2. Add text effects: `text-generate-effect`, `typewriter-effect`, `flip-words`.
3. Install via `npx shadcn@latest add @aceternity/<component>`.
4. Fetch source from `https://ui.aceternity.com/registry/<name>.json`.
   -> See `references/aceternity-ui-catalog.md`

### Problem: "I need a specific component type (button, card, hero, etc.)"

1. Run the search script to find components across shadcn registries:
   `python scripts/search-components.py button`
   `python scripts/search-components.py "text animation"`
2. Filter by group (27 categories):
   `python scripts/search-components.py --group animation`
   `python scripts/search-components.py button --group forms`
3. Filter by tag (3,500+ granular tags):
   `python scripts/search-components.py --tag glassmorphism`
   `python scripts/search-components.py --tag parallax --group backgrounds`
4. List available groups and tags:
   `python scripts/search-components.py --groups`
   `python scripts/search-components.py --tags`
5. Install directly: `python scripts/search-components.py --install @acme/ui:hero-parallax`
6. First run pulls registries via shadcn CLI. Cache refreshes every 24 hours.
   -> See `scripts/search-components.py --help`

### Problem: "I need ready-made page sections / blocks"

1. Search blocks: `python scripts/search-components.py hero`
2. Use registries that focus on marketing and dashboard blocks.
3. Use Aceternity blocks for visual-heavy sections (paid all-access).
   -> See `references/aceternity-ui-catalog.md`

### Problem: "The design looks amateur"

1. Apply a 5-level shadow elevation system consistently.
2. Stick to 4px/8px spacing grid — no arbitrary values.
3. Use HSL-based design tokens with CSS custom properties.
   -> See `references/visual-polish.md`

## Decision Trees

### When to Animate

| Trigger | Animate? | Pattern |
|---------|----------|---------|
| User clicks/taps | Yes | Scale 0.98 + spring (400/30) |
| User hovers | Yes | Subtle lift + shadow increase |
| Content loads | Yes | Skeleton → fade-in with stagger |
| Page navigates | Yes | Fade + slide (150ms ease-out) |
| Error appears | Yes | Shake or red border pulse |
| Background data refresh | No | Silent update, no flash |
| Resize/reflow | No | Instant, no transition |

### Loading State Selection

| Wait Time | Pattern | Example |
|-----------|---------|---------|
| < 100ms | Nothing | Instant response |
| 100-300ms | Subtle spinner | Button loading state |
| 300ms-1s | Content placeholder | Inline skeleton |
| 1-3s | Full skeleton screen | Page-level loading |
| 3s+ | Progress indicator | File upload, export |

### Component Selection

| Need | Use | Library |
|------|-----|---------|
| Data display with sort/filter | TanStack Table | @tanstack/react-table |
| Global search / command menu | Command Palette | cmdk |
| User notifications | Toast | sonner |
| Form with validation | React Hook Form | react-hook-form + zod |
| Overlay requiring action | Dialog | @radix-ui/react-dialog |
| Contextual side panel | Sheet | @radix-ui/react-dialog (side) |
| Destructive confirmation | AlertDialog | @radix-ui/react-alert-dialog |
| Component variants | CVA | class-variance-authority |
| Animated background effects | Aceternity UI | @aceternity/* via shadcn CLI |
| 3D card / hover effects | Aceternity UI | @aceternity/3d-card, card-hover-effect |
| Text animations | Aceternity UI | @aceternity/text-generate-effect, etc. |
| Parallax / scroll effects | Aceternity UI | @aceternity/parallax-scroll, hero-parallax |
| Hero section with wow factor | Aceternity UI | @aceternity/lamp, spotlight, aurora |
| Ready-made marketing blocks | Shadcn registries | shadcn CLI registry search |
| Ready-made dashboard blocks | Shadcn registries | shadcn CLI registry search |
| Animated interaction components | React Bits | shadcn CLI registry search |
| Physics / variable font effects | Fancy Components | shadcn CLI registry search |

-> Full catalogs: `references/component-discovery-sources.md`

### Visual Polish Priority

| Impact | Action | Effort |
|--------|--------|--------|
| Highest | Consistent spacing (4px grid) | Low |
| High | Shadow elevation system | Low |
| High | Focus-visible keyboard rings | Low |
| Medium | Skeleton loading states | Medium |
| Medium | Dark mode with smooth transition | Medium |
| Lower | Backdrop blur / glassmorphism | Low |
| Lower | Custom selection color | Trivial |

## The Premium Stack

```
Radix UI             → Accessible, unstyled primitives
  + shadcn/ui        → Styled component library (copy-paste)
  + Registry ecosystem → 50+ registries, 11K+ components (see below)
  + CVA              → Type-safe variant system
  + Tailwind         → Utility CSS with design tokens
  + Framer Motion    → Animation and gestures
  + TanStack         → Headless table, virtual scrolling
  + cmdk             → Command palette
  + Sonner           → Toast notifications
  + React Hook Form + Zod → Forms with schema validation
```

**Always search external sources first** — even for primitives.

| Source | Strength | Install |
|--------|----------|---------|
| Shadcn registries | 50+ quality registries, 11K+ components | `npx shadcn@latest add @registry/name` |
| 21st.dev | Largest single catalog (1500+), MCP server | shadcn CLI |
| React Bits | Creative animations (110+), 36K stars | shadcn CLI |
| Aceternity UI | Visual effects, 3D, parallax, backgrounds | shadcn CLI |
| Magic UI | Animated UI components, 20K stars | shadcn CLI |
| Fancy Components | Physics, variable fonts, award-site effects | shadcn CLI |

-> Full details: `references/component-discovery-sources.md`

## Reference Files

| File | Contents |
|------|----------|
| `references/micro-interactions.md` | Framer Motion patterns, spring physics, gesture interactions, CSS transitions, timing, reduced motion |
| `references/perceived-performance.md` | Skeleton screens, optimistic updates, progressive loading, prefetch, SWR, loading thresholds |
| `references/premium-components.md` | TanStack Table, cmdk command palettes, React Hook Form + Zod, modals/sheets, Sonner toasts |
| `references/visual-polish.md` | Shadow systems, spacing scales, typography, gradients, backdrop blur, dark mode, focus states |
| `references/state-choreography.md` | Loading/error/empty/success states, page transitions, layout animations, skeleton reveals |
| `references/component-architecture.md` | shadcn/ui + Radix + CVA patterns, design tokens, variant systems, composition, accessibility |
| `references/aceternity-ui-catalog.md` | Aceternity UI detailed component catalog with registry API endpoints |
| `references/component-discovery-sources.md` | Shadcn registry ecosystem — 50+ quality registries, install methods, source selection by component type |
| `scripts/search-components.py` | **CLI tool** — offline-first search across 50+ shadcn registries (8K+ components). Supports `--group` (27 categories) and `--tag` (3,500+ tags) filters. Install via shadcn CLI. Cache auto-refreshes every 24h. |
| `scripts/pull-all-registries.py` | **Data puller** — parallel fetch of all shadcn registries into one JSON cache with auto-generated groups and tags. Run with `--help` for options. |
