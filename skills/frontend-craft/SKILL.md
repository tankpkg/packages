---
name: "@tank/frontend-craft"
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
  "physics animation", "variable font", "letter swap", "gravity effect",
  "elastic line", "scramble text", "pixel trail", "css buttons", "neumorphism",
  "typography", "font pairing", "OKLCH", "color system", "tinted neutrals",
  "dark mode", "responsive design", "mobile first", "container query",
  "focus visible", "interaction design", "UX writing", "error message",
  "button label", "AI slop", "design looks generic", "looks like AI"
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
6. **Distinctive beats generic** — If someone immediately thinks "AI made
   this," the design failed. Avoid the AI fingerprints: Inter font, purple
   gradients, card-in-card, gray-on-color text, bounce easing.

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

### Problem: "I need a component, block, or section"

1. Search across 50+ registries: `python scripts/search-components.py <query>`
2. Filter: `--group animation`, `--tag glassmorphism`, `--groups` / `--tags` to list
3. Install: `python scripts/search-components.py --install @acme/ui:hero-parallax`
   -> See `scripts/search-components.py --help`

### Problem: "The design looks generic / like AI made it"

1. Review the AI slop fingerprints checklist and eliminate every match.
   -> See `references/visual-polish.md` (AI Slop Test section)
2. Replace overused fonts (Inter, Roboto) with distinctive alternatives.
3. Switch from HSL to OKLCH. Tint all neutrals toward brand hue.
4. Commit to a bold design direction before writing any CSS.
   -> See `references/design-foundations.md`

### Problem: "The design looks amateur"

1. Apply a 5-level shadow elevation system consistently.
2. Use exact component sizes — never eyeball button heights, padding, or spacing.
   -> See `references/ui-sizing-rules.md`
3. Stick to 4pt spacing grid with OKLCH design tokens.
   -> See `references/visual-polish.md` + `references/design-foundations.md`

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
| Visual effects, 3D, parallax, hero | Aceternity UI | `npx shadcn@latest add @aceternity/*` |
| Marketing / dashboard blocks | Shadcn registries | `python scripts/search-components.py` |
| Creative animations, physics | React Bits, Fancy Components | shadcn CLI registry search |

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

Radix UI → shadcn/ui → Registry ecosystem (50+ registries, 11K+ components) → CVA → Tailwind → Framer Motion → TanStack → cmdk → Sonner → React Hook Form + Zod.

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
| `references/design-foundations.md` | Typography (font selection, pairing, OKLCH, OpenType), Color (OKLCH, tinted neutrals, palettes, dark mode), Spatial Design (4pt grid, hierarchy, container queries) |
| `references/responsive-interaction.md` | Responsive (mobile-first, input detection, safe areas, srcset), Interaction (8 states, focus-visible, dialog, popover API, keyboard nav), UX Writing (button labels, error formulas, empty states, i18n) |
| `references/visual-polish.md` | Shadow systems, spacing scales, gradients, backdrop blur, dark mode transitions, focus states, AI slop anti-patterns |
| `references/state-choreography.md` | Loading/error/empty/success states, page transitions, layout animations, skeleton reveals |
| `references/component-architecture.md` | shadcn/ui + Radix + CVA patterns, design tokens, variant systems, composition, accessibility |
| `references/aceternity-ui-catalog.md` | Aceternity UI detailed component catalog with registry API endpoints |
| `references/ui-sizing-rules.md` | Exact component dimensions (buttons, inputs, navbars, sidebars, modals, cards, avatars, icons), padding formulas, container widths, aspect ratios, cross-system sizing data |
| `references/component-discovery-sources.md` | Shadcn registry ecosystem — 50+ quality registries, install methods, source selection by component type |
| `scripts/search-components.py` | **CLI tool** — offline-first search across 50+ shadcn registries (8K+ components). `--group`/`--tag` filters. Cache auto-refreshes 24h. `pull-all-registries.py` fetches data. |
