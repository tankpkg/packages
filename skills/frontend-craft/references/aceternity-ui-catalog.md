# Aceternity UI — Component Catalog & Registry API

Sources: ui.aceternity.com documentation, Aceternity registry API

Covers: Aceternity UI component discovery, installation via shadcn CLI, registry API for programmatic access, full component catalog by category. For the unified source selection guide across all 6 component sources, see `references/component-discovery-sources.md`.

## What Is Aceternity UI

Aceternity UI is a **copy-paste component library** focused on premium animated effects, micro-interactions, and visual "wow factor" components. It extends the shadcn/ui ecosystem — same CLI, same `cn()` utility, same Tailwind + Radix foundation — but specializes in animation-heavy, visually striking components that shadcn/ui doesn't offer.

**Key distinction**: shadcn/ui provides functional UI primitives (Button, Dialog, Table). Aceternity UI provides visual effect components (3D cards, parallax scrolls, animated backgrounds, text effects). They are complementary, not competing.

### Dependencies
- `motion` (Framer Motion) — most components require this
- `clsx` + `tailwind-merge` — via the standard `cn()` utility
- `tailwindcss` — utility-first styling
- Some components require additional deps: `three`, `@react-three/fiber`, `@tsparticles/react`, `simplex-noise`, `@tabler/icons-react`

## How Agents Should Discover & Install Components

### Step 1: Identify the Need
When a user asks for visual effects, animations, hero sections, card effects, text animations, or background effects — check the Aceternity catalog below BEFORE writing custom code.

### Step 2: Install via shadcn CLI
Every Aceternity component uses the same CLI as shadcn/ui:
```bash
npx shadcn@latest add @aceternity/<component-name>
```
This copies the component source into `components/ui/<component-name>.tsx` and installs required dependencies automatically.

### Step 3: Fetch Source Code (for customization or reference)
Each component's full source is available as JSON from the registry:
```
https://ui.aceternity.com/registry/<component-name>.json
```
This returns `{ name, type, files: [{ path, content, target }], dependencies }`.

Use `webfetch` or `crawl_url` on this endpoint to get the exact source code for any component.

### Step 4: View Documentation & Examples
Component documentation with live previews and usage examples:
```
https://ui.aceternity.com/components/<component-slug>
```

### Registry Index (All Components)
The full machine-readable index of all available components:
```
https://ui.aceternity.com/registry/index.json
```
Returns an array of `{ name, type, dependencies, files }` for every component.

## When to Use Aceternity vs shadcn/ui vs Custom

| Need | Use | Why |
|------|-----|-----|
| Button, Input, Dialog, Select, Form | **shadcn/ui** | Functional primitives with accessibility |
| Data Table, Command Palette | **shadcn/ui** + TanStack/cmdk | Headless logic components |
| Animated background effect | **Aceternity UI** | Pre-built, tested animations |
| 3D card / hover effect | **Aceternity UI** | Complex transform math already solved |
| Text animation (typewriter, generate) | **Aceternity UI** | Polished, production-ready |
| Parallax scroll / hero section | **Aceternity UI** | Scroll-linked animations |
| Toast notifications | **Sonner** | Purpose-built for toasts |
| Simple hover/tap animation | **Custom Framer Motion** | Too simple to warrant a library component |
| Unique brand-specific animation | **Custom** | Not available in any library |

**Rule of thumb**: If Aceternity has a component for it, use it. It saves 50-200 lines of animation code per component and handles edge cases (reduced motion, performance, mobile).

## Component Catalog

### Backgrounds & Effects
Visual effects for page backgrounds, hero sections, and ambient decoration.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| Sparkles | `sparkles` | Particle sparkle effect | tsparticles, motion |
| Background Gradient | `background-gradient` | Animated gradient overlay | motion |
| Gradient Animation | `background-gradient-animation` | Full-page animated gradient | — |
| Wavy Background | `wavy-background` | Procedural wave pattern | simplex-noise |
| Background Boxes | `background-boxes` | Grid of animated boxes | motion |
| Background Beams | `background-beams` | Animated light beams | motion |
| Background Beams Collision | `background-beams-with-collision` | Beams that collide | motion |
| Background Lines | `background-lines` | Animated line pattern | motion |
| Aurora Background | `aurora-background` | Northern lights effect | — |
| Meteors | `meteors` | Falling meteor particles | — |
| Glowing Stars | `glowing-stars` | Twinkling star field | motion |
| Shooting Stars | `shooting-stars` | Shooting star trails | — |
| Vortex | `vortex` | Spiral vortex animation | motion |
| Spotlight | `spotlight` | Mouse-following spotlight | motion |
| Canvas Reveal | `canvas-reveal-effect` | Canvas-based reveal | three, react-three |
| SVG Mask Effect | `svg-mask-effect` | SVG-based mask reveal | motion |
| Tracing Beam | `tracing-beam` | Scroll-linked tracing line | motion |
| Lamp Effect | `lamp` | Dramatic top-down light | motion |
| Grid/Dot Backgrounds | `grid` | Grid and dot patterns | — |
| Glowing Effect | `glowing-effect` | Element glow on hover | motion |
| Google Gemini Effect | `google-gemini-effect` | Gemini-style line animation | motion |
| Background Ripple | `background-ripple-effect` | Ripple expanding effect | motion |
| Dotted Glow Background | `dotted-glow-background` | Glowing dotted pattern | — |

### Card Components
Interactive cards with hover effects, 3D transforms, and visual flair.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| 3D Card Effect | `3d-card` | Perspective tilt on hover | — |
| Evervault Card | `evervault-card` | Encrypted-style hover effect | motion |
| Card Stack | `card-stack` | Stacked cards with flip | motion |
| Card Hover Effect | `card-hover-effect` | Animated hover highlight | motion |
| Wobble Card | `wobble-card` | Wobbly tilt interaction | motion |
| Expandable Card | `expandable-card` | Card that expands to modal | motion |
| Card Spotlight | `card-spotlight` | Mouse-tracking spotlight | motion |
| Focus Cards | `focus-cards` | Cards that blur siblings | motion |
| Infinite Moving Cards | `infinite-moving-cards` | Auto-scrolling card ticker | — |
| Draggable Card | `draggable-card` | Drag-to-dismiss card | motion |
| Glare Card | `glare-card` | Holographic glare on hover | motion |
| Direction Aware Hover | `direction-aware-hover` | Overlay from mouse direction | motion |
| Comet Card | `comet-card` | Card with comet trail border | motion |
| Tooltip Card | `tooltip-card` | Card that follows cursor | motion |

### Scroll & Parallax
Scroll-driven animations and parallax effects.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| Parallax Scroll | `parallax-scroll` | Multi-layer parallax grid | motion |
| Sticky Scroll Reveal | `sticky-scroll-reveal` | Content revealed on scroll | motion |
| Macbook Scroll | `macbook-scroll` | Image emerges from laptop | motion, tabler-icons |
| Container Scroll | `container-scroll-animation` | Perspective scroll effect | motion |
| Hero Parallax | `hero-parallax` | Product showcase parallax | motion |
| Parallax Hero Images | `parallax-hero-images` | Mouse-driven parallax | motion |

### Text Components
Animated text effects for headings, hero copy, and content.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| Text Generate Effect | `text-generate-effect` | Words appear one by one | motion |
| Typewriter Effect | `typewriter-effect` | Classic typewriter animation | motion |
| Flip Words | `flip-words` | Words flip/rotate in place | motion |
| Text Hover Effect | `text-hover-effect` | SVG text with hover reveal | motion |
| Container Text Flip | `container-text-flip` | Text flips on scroll | motion |
| Hero Highlight | `hero-highlight` | Highlighted text with gradient | motion |
| Text Reveal Card | `text-reveal-card` | Card reveals text on hover | motion |
| Colourful Text | `colourful-text` | Per-character color animation | motion |
| Encrypted Text | `encrypted-text` | Matrix-style text decode | — |
| Layout Text Flip | `layout-text-flip` | Layout-animated text swap | motion |
| Canvas Text | `canvas-text` | Canvas-rendered text effects | — |

### Navigation
Animated navbars, sidebars, tabs, and docks.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| Floating Navbar | `floating-navbar` | Scroll-reactive floating nav | motion |
| Navbar Menu | `navbar-menu` | Animated dropdown menus | motion |
| Sidebar | `sidebar` | Collapsible animated sidebar | motion |
| Floating Dock | `floating-dock` | macOS dock-style toolbar | motion |
| Tabs | `tabs` | Animated tab switcher | radix-tabs |
| Resizable Navbar | `resizable-navbar` | Navbar that resizes on scroll | motion |
| Sticky Banner | `sticky-banner` | Fixed promotional banner | motion |

### Buttons
Animated button styles and border effects.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| Tailwind CSS Buttons | `tailwindcss-buttons` | Collection of button styles | tabler-icons |
| Hover Border Gradient | `hover-border-gradient` | Animated gradient border | motion |
| Moving Border | `moving-border` | Rotating border animation | motion |
| Stateful Button | `stateful-button` | Loading/success/error states | motion |

### Carousels & Sliders
Image sliders and content carousels.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| Images Slider | `images-slider` | Full-screen image slider | motion |
| Carousel | `carousel` | General-purpose carousel | motion |
| Apple Cards Carousel | `apple-cards-carousel` | Apple-style card carousel | motion |
| Animated Testimonials | `animated-testimonials` | Testimonial slider | motion |

### Layout & Grid
Grid systems and layout components.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| Layout Grid | `layout-grid` | Animated masonry grid | motion |
| Bento Grid | `bento-grid` | Dashboard-style bento layout | tabler-icons |
| Container Cover | `container-cover` | Expanding container effect | motion |

### Data & Visualization
Interactive data displays and visualizations.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| GitHub Globe | `globe` | Interactive 3D globe | three, three-globe, react-three |
| World Map | `world-map` | Animated world map | motion |
| Timeline | `timeline` | Vertical timeline component | motion |
| Compare | `compare` | Before/after image slider | motion |
| Codeblock | `code-block` | Syntax-highlighted code | — |

### Inputs & Forms
Animated form components.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| Signup Form | `signup-form` | Animated signup form | motion |
| Vanish Input | `placeholders-and-vanish-input` | Input with animated placeholders | motion |
| File Upload | `file-upload` | Animated file upload zone | motion |

### Overlays & Popovers
Modal, tooltip, and preview components.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| Animated Modal | `animated-modal` | Spring-animated modal | motion |
| Animated Tooltip | `animated-tooltip` | Avatar tooltip on hover | motion |
| Link Preview | `link-preview` | URL preview on hover | motion |

### Cursor & Pointer
Mouse-tracking and cursor effects.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| Following Pointer | `following-pointer` | Element follows cursor | motion |
| Pointer Highlight | `pointer-highlight` | Spotlight follows pointer | motion |
| Lens | `lens` | Magnifying lens effect | motion |

### 3D Components
Three.js-based 3D elements (heavier dependencies).

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| 3D Globe | `3d-globe` | Full 3D interactive globe | three, react-three |
| 3D Pin | `3d-pin` | 3D location pin animation | motion |
| 3D Marquee | `3d-marquee` | 3D perspective marquee | motion |

### Loaders
Loading state components.

| Component | Slug | Description | Key Deps |
|-----------|------|-------------|----------|
| Multi Step Loader | `multi-step-loader` | Step-by-step loading animation | motion, tabler-icons |
| Loader | `loader` | Animated loader variants | motion |

## Blocks & Sections (Paid All-Access)
Pre-built full-page sections. These are paid but worth knowing about:

| Block Category | Count | Typical Use |
|----------------|-------|-------------|
| Hero Sections | 17+ | Landing page hero |
| Feature Sections | 10+ | Product features |
| Pricing Sections | 8+ | Pricing tables |
| Testimonials | 6+ | Social proof |
| CTA Sections | 6+ | Call to action |
| Bento Grids | 5+ | Dashboard layouts |
| Logo Clouds | 5+ | Partner logos |
| Cards | 8+ | Content cards |
| Navbars | 5+ | Navigation bars |
| Footers | 5+ | Page footers |
| Login/Signup | 5+ | Auth forms |
| Contact Sections | 4+ | Contact forms |
| FAQs | 4+ | FAQ accordions |

Free section components: `feature-sections-free`, `cards-free`, `hero-sections-free`.

## Agent Workflow: Using Aceternity Components

### When user asks for visual effects:

1. **Check this catalog** for a matching component
2. **Install**: `npx shadcn@latest add @aceternity/<slug>`
3. **If customization needed**: Fetch source from `https://ui.aceternity.com/registry/<slug>.json`
4. **If no match found**: Build custom with Framer Motion using patterns from `references/micro-interactions.md`

### When user asks for a landing page / hero section:

1. Start with Aceternity hero components: `hero-parallax`, `spotlight`, `lamp`, `aurora-background`
2. Add text effects: `text-generate-effect`, `typewriter-effect`, `colourful-text`, `flip-words`
3. Layer with background effects: `sparkles`, `background-beams`, `background-gradient-animation`
4. Use shadcn/ui for functional elements (buttons, forms, dialogs)

### Performance Considerations

| Dep Weight | Components | Notes |
|------------|------------|-------|
| **Light** (motion only) | Most components | Safe for all projects |
| **Medium** (motion + icons) | Bento Grid, Macbook Scroll, Buttons | Small additional bundle |
| **Heavy** (three.js) | Globe, 3D Globe, Canvas Reveal | +200KB+ gzipped. Use dynamic import |

For heavy components, always use dynamic imports:
```tsx
const Globe = dynamic(() => import("@/components/ui/globe"), { ssr: false });
```

## Anti-Patterns

| Mistake | Fix |
|---------|-----|
| Using 3+ background effects on one page | Pick ONE hero effect. Less is more. |
| Loading Three.js components without code splitting | Always `dynamic(() => import(...), { ssr: false })` |
| Ignoring reduced motion preferences | Most Aceternity components respect `prefers-reduced-motion` via Framer Motion |
| Mixing Aceternity animations with custom Framer Motion on same element | Let Aceternity own the animation; style only via className |
| Using Aceternity for functional UI (forms, tables) | Use shadcn/ui for functional primitives. Aceternity is for visual effects. |

For all other component sources (hover.dev, Shadcn Space, 21st.dev, React Bits, Uiverse.io) and the unified source selection guide, see `references/component-discovery-sources.md`.
