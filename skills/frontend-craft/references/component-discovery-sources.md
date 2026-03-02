# Component Discovery Sources — Unified Guide

Sources: 21st.dev, reactbits.dev, ui.aceternity.com, fancycomponents.dev, shadcnspace.com, and the full shadcn registry ecosystem (~50 quality registries)

Covers: External component sources with catalogs, install methods, agent workflows, and the unified "always search external first" decision framework. All sources are installable via `npx shadcn@latest add`. For Aceternity's detailed component catalog, see `references/aceternity-ui-catalog.md`.

## Core Principle: Always Search External Sources First

**Never build from scratch when a production-ready component exists.** Before writing custom code for ANY UI element — including primitives like buttons, inputs, and cards — search these sources. They offer animated, polished, battle-tested variants that would take hours to build manually.

This applies to everything: hero sections, backgrounds, buttons, inputs, toggles, navbars, cards, modals, text effects, loaders, pricing tables, dashboards.

## Agent Discovery Workflow

When the user needs ANY UI component or section:

1. **Identify the need** — What kind of component? What visual style?
2. **Search the sources below** — Check 2-3 most relevant sources for the component type
3. **Compare options** — Pick the best match for quality, animation level, and project fit
4. **Install or copy** — Use CLI when available, copy-paste otherwise
5. **Customize** — Adapt colors, spacing, content to match the project
6. **Only build custom** if no external source has what's needed

## Source Quick Reference

| Source | Best For | Install Method | URL |
|--------|----------|----------------|-----|
| **21st.dev** | Largest catalog (1500+), community components, MCP server | shadcn CLI | `21st.dev/s/<category>` |
| **React Bits** | Creative animations (110+), text effects, backgrounds | shadcn CLI | `reactbits.dev` |
| **Aceternity UI** | Visual effects, 3D, parallax, ambient backgrounds | shadcn CLI | `ui.aceternity.com` |
| **Fancy Components** | Playful physics, unique text effects, award-site recreations (40) | shadcn CLI | `fancycomponents.dev` |
| **Shadcn Space** | Marketing/dashboard blocks (199+), Base UI primitives | shadcn CLI | `shadcnspace.com` |
| **Shadcn Registries** | 50+ quality registries (11K+ components total) | shadcn CLI | `ui.shadcn.com/r/registries.json` |

---

## 21st.dev — Community Component Marketplace

**What**: The largest community-built component marketplace. YC-backed. 1500+ components across marketing blocks and UI primitives. Has an **MCP server** for AI agent integration.

**Install**: `npx shadcn@latest add <component-url>` (shadcn CLI compatible)
**Browse**: `https://21st.dev/s/<category-slug>`
**MCP**: Built-in MCP server for component search & creation from AI agents.

### Marketing Blocks (20 categories, 400+ components)

| Category | Slug | Count |
|----------|------|-------|
| Heroes | `hero` | 73 |
| Texts | `text` | 58 |
| Features | `features` | 36 |
| CTAs | `call-to-action` | 34 |
| Backgrounds | `background` | 33 |
| Hooks (utilities) | `hook` | 31 |
| Images | `image` | 26 |
| Scroll Areas | `scroll-area` | 24 |
| Pricing | `pricing-section` | 17 |
| Clients / Logos | `clients` | 16 |
| Testimonials | `testimonials` | 15 |
| Shaders | `shader` | 15 |
| Footers | `footer` | 14 |
| Borders | `border` | 12 |
| Navbars | `navbar-navigation` | 11 |
| Announcements | `announcement` | 10 |
| Videos | `video` | 9 |
| Comparisons | `comparison` | 6 |
| Docks | `dock` | 6 |
| Maps | `map` | 2 |

### UI Components (38 categories, 1100+ components)

| Category | Slug | Count |
|----------|------|-------|
| Buttons | `button` | 130 |
| Inputs | `input` | 102 |
| Cards | `card` | 79 |
| Selects | `select` | 62 |
| Sliders | `slider` | 45 |
| Accordions | `accordion` | 40 |
| Tabs | `tabs` | 38 |
| Dialogs/Modals | `modal-dialog` | 37 |
| Calendars | `calendar` | 34 |
| Tables | `table` | 30 |
| AI Chats | `ai-chat` | 30 |
| Tooltips | `tooltip` | 28 |
| Badges | `badge` | 25 |
| Dropdowns | `dropdown` | 25 |
| Alerts | `alert` | 23 |
| Popovers | `popover` | 23 |
| Forms | `form` | 23 |
| Radio Groups | `radio-group` | 22 |
| Text Areas | `textarea` | 22 |
| Spinner Loaders | `spinner-loader` | 21 |
| Paginations | `pagination` | 20 |
| Checkboxes | `checkbox` | 19 |
| Numbers | `number` | 18 |
| Menus | `menu` | 18 |
| Avatars | `avatar` | 17 |
| Links | `link` | 13 |
| Toggles | `toggle` | 12 |
| Date Pickers | `date-picker` | 12 |
| Carousels | `carousel` | 16 |
| Icons | `icons` | 10 |
| Sidebars | `sidebar` | 10 |
| File Uploads | `upload-download` | 7 |
| Tags | `chip-tag` | 6 |
| Notifications | `notification` | 5 |
| Sign Ins | `sign-in` | 4 |
| Sign Ups | `registration-signup` | 4 |
| File Trees | `file-tree` | 2 |
| Toasts | `toast` | 2 |

---

## React Bits — Creative Animation Library

**What**: 110+ highly creative animated React components. 36K+ GitHub stars. Text animations, backgrounds, UI elements. Endorsed by shadcn himself. 4 code variants per component (JS/TS × CSS/Tailwind).

**Install**: `npx shadcn@latest add @react-bits/<ComponentName>-<variant>`
  Variants: `TS-TW` (TypeScript+Tailwind), `TS-CSS`, `JS-TW`, `JS-CSS`
**Browse**: `https://reactbits.dev`
**GitHub**: `github.com/DavidHDev/react-bits` (36K+ stars, MIT)

### Categories

| Category | What's in it |
|----------|-------------|
| **Text Animations** | Blur text, split text, gradient text, typewriter, count-up, scroll reveal text |
| **Animations** | Magnet effect, splash cursor, blob cursor, trail effect, pixel transitions |
| **Components** | Dock menu, stack cards, tilted scroll, infinite scroll, ribbons, star rating |
| **Backgrounds** | Hyperspeed, aurora, grid motion, particles, noise, lightning, waves, orbit images |

### Tools (free utilities)
- **Background Studio**: Explore/customize animated backgrounds, export as video/image/code
- **Shape Magic**: Create inner rounded corners between shapes, export as SVG/React
- **Texture Lab**: Apply 20+ effects (noise, dithering, halftone, ASCII) to images

---

## Fancy Components — Playful Physics & Creative Micro-Interactions

**What**: 40 "fun and weird" components recreating effects from award-winning websites. Unique focus on physics-based interactions, variable font animations, and creative text effects. React + TypeScript + Tailwind + Motion.

**Install**: `npx shadcn add @fancy/<component-name>` (shadcn CLI)
**Browse**: `https://www.fancycomponents.dev/docs/components/<category>/<name>`
**GitHub**: `github.com/danielpetho/fancy` (2.8K stars, MIT)
**LLM-friendly**: Has `/llms.txt` for AI consumption.

### Text (20 components — strongest category)
| Component | Slug |
|-----------|------|
| Letter Swap Hover | `letter-swap` |
| Letter 3D Swap | `letter-3d-swap` |
| Random Letter Swap Hover | `random-letter-swap` |
| Vertical Cut Reveal | `vertical-cut-reveal` |
| Text Rotate | `text-rotate` |
| Variable Font Hover By Letter | `variable-font-hover-by-letter` |
| Variable Font Hover By Random Letter | `variable-font-hover-by-random-letter` |
| Scroll And Swap | `scroll-and-swap` |
| Text Cursor Proximity | `text-cursor-proximity` |
| Variable Font & Cursor | `variable-font-and-cursor` |
| Variable Font Cursor Proximity | `variable-font-cursor-proximity` |
| Breathing Text | `breathing-text` |
| Underline Animation | `underline-animation` |
| Underline To Background | `underline-to-background` |
| Basic Number Ticker | `basic-number-ticker` |
| Typewriter | `typewriter` |
| Scramble Hover | `scramble-hover` |
| Text Highlighter | `text-highlighter` |
| Scramble In | `scramble-in` |
| Text Along Path | `text-along-path` |

### Physics (3) — unique to this library
- **Elastic Line** — spring-physics line that reacts to cursor
- **Gravity** — elements affected by gravity simulation
- **Cursor Attractor & Gravity** — elements attracted to/repelled by cursor

### Blocks (10)
Drag Elements, Circling Elements, Media Between Text, CSS Box, Screensaver, Sticky Footer, Float, Stacking Cards, Simple Marquee, Marquee Along SVG Path.

### Other Categories
- **Background (2)**: Animated Gradient SVG, Pixel Trail
- **Image (2)**: Image Trail, Parallax Floating
- **Filter (2)**: Gooey SVG Filter, Pixelate SVG Filter
- **Carousel (1)**: Box Carousel

### When to Use Fancy Components
- Need **variable font animations** (cursor-reactive typography) — unique to this library
- Need **physics-based interactions** (gravity, elastic, attractor) — unique to this library
- Need **creative text hover effects** (letter swap, scramble, 3D swap)
- Want to recreate effects from **Awwwards/FWA winning sites**

---

## Shadcn Space — Marketing & Dashboard Blocks

**What**: 199+ blocks, 130+ components built on shadcn/ui + Base UI. Strongest for complete page sections and dashboard UI. Has MCP server.

**Install**: shadcn CLI or copy-paste from GitHub
**Browse**: `https://shadcnspace.com/blocks` and `/components`
**GitHub**: `github.com/shadcnspace/shadcnspace` (MIT)

### Marketing Blocks (25 categories)
Hero (11+), Features (10+), Pricing (4+), Testimonials (5+), CTA (3+), About Us (4+), Team (3+), Services (4+), Contact (3+), Blog (4+), FAQ (2+), Footer (1+), Navbar (1+), Logo Cloud (4+), Portfolio (4+), Newsletter (1+), Bento Grid, Gallery, Login (5+), Register (4+), Forgot Password (5+), 2FA (2+), Verify Email (2+).

### Dashboard Blocks (10 categories)
Dashboard Shell (3+), Charts (13+), Statistics (16+), Widgets (15+), Tables (10+), Sidebars (4+), Topbars, Dialog, Dropdown, Forms.

### Components (25 categories, 130+)
Button (15), Input (18), Textarea (9), Tooltip (7), Select (9), Checkbox (9), Switch (6), Radio Group (6), Card (6), Badge (6), Avatar (6), Calendar (5), Button Group (6), Animated Text (5), Tabs (4), Accordion (2), Marquee (2), Date Picker (2), plus others.

---

## Shadcn Registry Ecosystem

**What**: 50+ quality third-party registries indexed at `ui.shadcn.com/r/registries.json`, all compatible with `npx shadcn@latest add`. Includes Magic UI (20K★), React Bits (36K★), Plate (16K★), Cult UI (3.3K★), Kibo UI (3.6K★), and many more.

**Install**: `npx shadcn@latest add @registry-name/component-name`
**Search**: `python scripts/search-components.py <query>` (offline, 11K+ components cached)
**Pull**: `python scripts/pull-all-registries.py` (parallel fetch of all registries)

### Notable Registries

| Registry | Stars | Strength |
|----------|-------|----------|
| `@magicui` | 20.3K | Animated UI components, landing page effects |
| `@react-bits` | 36.3K | Creative animations, text effects, backgrounds |
| `@plate` | 16K | Rich text editor framework |
| `@aceternity` | — | Visual effects, 3D, parallax, backgrounds |
| `@cult-ui` | 3.3K | Polished UI component variants |
| `@kibo-ui` | 3.6K | Production UI kit |
| `@animate-ui` | 3.4K | Animation-focused components |
| `@ui-layouts` | 3.2K | Layout and section components |
| `@hooks` | 5K | React hooks collection |
| `@mapcn` | 6.1K | Map components |
| `@react-aria` | — | Adobe's accessible component primitives |
| `@supabase` | — | Official Supabase UI components |

---

## Source Selection by Component Type

**The rule: Always check external sources before building custom.** Includes primitives.

### Backgrounds & Ambient Effects
1. **Aceternity UI** (primary) — sparkles, beams, aurora, gradients, meteors
2. **React Bits** — hyperspeed, aurora, grid motion, particles, waves
3. **21st.dev** — 33 background components, 15 shaders
4. **Fancy Components** — animated gradient SVG, pixel trail

### Hero Sections
1. **21st.dev** (73 heroes!) — largest selection
2. **Aceternity UI** — hero-parallax, lamp, spotlight, aurora
3. **Shadcn Space** — 11+ clean marketing heroes
4. **Shadcn Registries** — search `hero` across 50+ registries

### Cards
1. **21st.dev** — 79 card variants
2. **Aceternity UI** — 3D cards, hover effects, glare, spotlight
3. **Shadcn Registries** — search `card` across 50+ registries

### Buttons
1. **21st.dev** — 130 button variants
2. **Shadcn Space** — 15 clean button variants
3. **React Bits** — animated button effects
4. **Shadcn Registries** — search `button` across 50+ registries

### Inputs & Forms
1. **21st.dev** — 102 input variants, 23 forms
2. **Shadcn Space** — 18 inputs, 9 textareas, 9 selects
3. **Aceternity UI** — vanish input, signup form, file upload

### Text Animations
1. **Fancy Components** — 20 unique text effects (variable font, letter swap, scramble, cursor proximity)
2. **Aceternity UI** — text-generate, typewriter, flip-words, colourful text
3. **React Bits** — blur text, split text, gradient text, count-up
4. **21st.dev** — 58 text components

### Navigation
1. **21st.dev** — 11 navbars, 18 menus, 10 sidebars
2. **Aceternity UI** — floating navbar, sidebar, floating dock, tabs
3. **Shadcn Space** — navbar and sidebar blocks

### Pricing / Testimonials / Features Sections
1. **21st.dev** — pricing (17), testimonials (15), features (36)
2. **Shadcn Space** — pricing (4+), testimonials (5+), features (10+)
3. **Aceternity UI** — paid blocks for these categories

### Dashboard UI
1. **Shadcn Space** (primary) — charts, stats, widgets, tables, sidebars
2. **21st.dev** — tables (30), sidebars (10), dialogs (37)

### Loaders & Spinners
1. **21st.dev** — 21 spinner/loader variants
2. **React Bits** — animated loading effects
3. **Aceternity UI** — multi-step loader

### Modals & Dialogs
1. **21st.dev** — 37 dialog/modal variants
2. **Aceternity UI** — animated modal
3. **Shadcn Space** — dialog blocks

### Toggles, Checkboxes, Radio Buttons
1. **21st.dev** — toggles (12), checkboxes (19), radio groups (22)
2. **Shadcn Registries** — search `toggle`, `checkbox`, `radio`

## Anti-Patterns

| Mistake | Fix |
|---------|-----|
| Building a custom button animation from scratch | Search registries first: `python scripts/search-components.py button` |
| Only using shadcn/ui defaults without checking for enhanced variants | Always search registries for animated alternatives |
| Using 3+ animation libraries on one page | Stick to Framer Motion (motion) as the primary animation engine |
| Mixing sources without consistent design tokens | All installed components should be adapted to your project's Tailwind theme |
| Manual copy-paste instead of CLI install | All sources use `npx shadcn@latest add` — always prefer CLI |
