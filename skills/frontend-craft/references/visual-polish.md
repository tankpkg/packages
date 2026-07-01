# Visual Polish

Sources: Wathan/Schoger (Refactoring UI), Yablonski (Laws of UX), shadcn/ui conventions

Covers: shadow elevation systems, spacing scales, typography scales, gradient patterns, backdrop blur, dark mode transitions, focus-visible, selection color, border radius systems, AI slop detection.

> **For deeper color theory (OKLCH, tinted neutrals, palette architecture, dark mode) and typography (font selection, pairing, OpenType features), see `references/design-foundations.md`.**

Visual polish represents the "last 5%" of the development cycle where a functional interface is transformed into a premium product. It focuses on consistency, depth, and refinement of the smallest details.

## Shadow Elevation System

Shadows are used to communicate depth and hierarchy along the Z-axis. Avoid using a single shadow for all elements; instead, implement a system of elevation levels that correspond to the component's distance from the background.

### Elevation Levels

| Level | Tailwind Class | Use Case | Visual Characteristic |
|-------|----------------|----------|------------------------|
| Level 1 | `shadow-sm` | Buttons, small inputs | Subtle border-like depth |
| Level 2 | `shadow` | Cards, dropdown menus | Standard resting state |
| Level 3 | `shadow-md` | Modals, popovers | Clear separation from surface |
| Level 4 | `shadow-lg` | Large dialogs, floating panels | High elevation, soft spread |
| Level 5 | `shadow-2xl` | Command palettes, tooltips | Peak elevation, very soft |

### Premium Shadow Pattern
Standard box-shadows often look "muddy" because they use pure black at high opacity. For a premium look, use multiple layered shadows or shadows tinted with the brand color.

```css
/* Custom layered shadow for depth without muddiness */
.shadow-premium {
  box-shadow: 
    0 1px 2px 0 rgb(0 0 0 / 0.05),
    0 4px 6px -1px rgb(0 0 0 / 0.1),
    0 10px 15px -3px rgb(0 0 0 / 0.1);
}

/* Tinted shadow for brand cohesion */
.shadow-brand {
  box-shadow: 0 10px 15px -3px var(--brand-color-opacity-20);
}
```

## Spacing System

Consistency in spacing is the foundation of a professional layout. Utilize a fixed spacing scale based on a 4px or 8px grid. This eliminates "magic numbers" and ensures visual rhythm.

### Spacing Scale (8px Grid)

| Value | PX | Tailwind | Usage |
|-------|----|----------|-------|
| 1 | 4px | `p-1` | Tight clusters, small icons |
| 2 | 8px | `p-2` | Inner button padding, small gaps |
| 4 | 16px | `p-4` | Standard card padding, small margins |
| 6 | 24px | `p-6` | Comfortable card padding, section gaps |
| 8 | 32px | `p-8` | Large section spacing |
| 12 | 48px | `p-12` | Major layout breaks |
| 16 | 64px | `p-16` | Hero section padding |

### Implementation Rules
1. **The 4px rule**: Use 4px for fine-tuning small components (icons, labels).
2. **The 8px rule**: Use 8px increments for layout and large component spacing.
3. **Internal vs. External**: Ensure padding (internal) is always larger than or equal to the space between siblings (external) within the same container.
4. **Optical Alignment**: Sometimes a mathematical center is not a visual center. Adjust icons or text by 1-2px if they look "off" despite being technically centered.

## Typography Scale

A modular typography scale ensures that font sizes have a harmonious relationship. Avoid arbitrary pixel values.

### Modular Scale (Major Second - 1.125)

| Tag | Tailwind | Size | Use Case |
|-----|----------|------|----------|
| h1 | `text-4xl` | 2.25rem | Hero Headlines |
| h2 | `text-3xl` | 1.875rem | Section Headers |
| h3 | `text-2xl` | 1.5rem | Subsection Headers |
| h4 | `text-xl` | 1.25rem | Card Titles |
| p | `text-base` | 1rem | Main Body Copy |
| small | `text-sm` | 0.875rem | Secondary Info, Metadata |
| tiny | `text-xs` | 0.75rem | Labels, Captions |

### Tracking and Line Height
Fine-tuning the space between lines and letters is critical for a premium feel.

- **Tighten Large Headers**: As font size increases, the relative space between letters increases. Tighten headers slightly.
  - `tracking-tight` (-0.025em) or `tracking-tighter` (-0.05em).
- **Loosen Small Text**: Very small text (xs/sm) needs more breathing room to be legible.
  - `tracking-wide` (0.025em).
- **Line Height (Leading)**:
  - Headers: `leading-tight` (1.2) or `leading-none` (1).
  - Body: `leading-relaxed` (1.6) for readability.
  - UI Elements (Buttons): `leading-none` to center text vertically within fixed-height boxes.

### Fluid Typography
Use `clamp()` to create typography that scales smoothly between mobile and desktop without breakpoints.

```css
/* Fluid H1: Min 2rem, Max 4rem, scales with viewport */
h1 {
  font-size: clamp(2rem, 5vw + 1rem, 4rem);
  line-height: 1.1;
  letter-spacing: -0.02em;
}
```

## Color Polish

Premium UIs avoid flat, default colors. Use subtle gradients, tinted neutrals, and OKLCH for perceptually accurate palettes. See `references/design-foundations.md` for the complete OKLCH color system.

### Subtle Gradients
Replace flat backgrounds with very subtle "barely there" gradients.

```html
<!-- Premium Gradient Card -->
<div class="bg-gradient-to-br from-white to-slate-50 border border-slate-200 shadow-sm">
  <!-- Content -->
</div>
```

### Modern Color with OKLCH
Prefer `oklch()` over `hsl()` for new projects — it's perceptually uniform, meaning equal lightness steps actually look equal. At minimum, tint your neutrals toward your brand hue (even 0.01 chroma creates subconscious cohesion):

```css
:root {
  /* Old approach: pure gray */
  /* --bg-subtle: hsl(0 0% 97%); */

  /* Better: OKLCH with brand tint */
  --bg-subtle: oklch(97% 0.01 250); /* cool tech tint */
}
```

### Semantic Color Polish
Avoid using 100% saturation for status colors (Success Green, Error Red). Soften them slightly and use them at low opacity for backgrounds.

- **Success**: `bg-emerald-50 text-emerald-700 border-emerald-200`
- **Error**: `bg-rose-50 text-rose-700 border-rose-200`
- **Warning**: `bg-amber-50 text-amber-700 border-amber-200`

## Backdrop Blur and Glassmorphism

Backdrop blur adds depth by simulating frosted glass. It is effective for sticky headers, sidebars, and overlays.

### Implementation
Use `backdrop-blur` in combination with a semi-transparent background.

```html
<!-- Glassmorphic Header -->
<header class="sticky top-0 bg-white/70 backdrop-blur-md border-b border-white/20">
  <nav>...</nav>
</header>
```

### Performance Notes
- Limit usage on mobile devices as blur is computationally expensive.
- Always provide a fallback background color for browsers that do not support `backdrop-filter`.
- Use `will-change: transform` if the blurred element is animated to trigger GPU acceleration.

## Dark Mode Transitions

Moving between light and dark modes should feel fluid, not jarring.

### Smooth Theme Switching
Implement transitions for color-related properties, but exclude layout-shifting properties like `width` or `height`.

```css
/* Apply transition to all color-related properties */
* {
  transition-property: color, background-color, border-color, text-decoration-color, fill, stroke;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

/* Ensure no transition on page load to prevent flash */
.no-transitions * {
  transition: none !important;
}
```

### CSS Custom Properties for Themes
Define tokens that change based on a data attribute or class.

```css
:root {
  --bg-app: #ffffff;
  --text-primary: #0f172a;
}

[data-theme='dark'] {
  --bg-app: #020617;
  --text-primary: #f8fafc;
}

body {
  background-color: var(--bg-app);
  color: var(--text-primary);
}
```

## Focus and Selection

Accessible UIs should still feel premium. Customize the browser defaults to match your design system.

### Focus-Visible Patterns
Only show focus rings when the user navigates via keyboard. This keeps the UI clean for mouse users while maintaining accessibility.

```html
<!-- Tailwind focus-visible -->
<button class="focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
  Action
</button>
```

### Custom Selection Color
Match the text selection highlight to your brand identity.

```css
::selection {
  background-color: var(--brand-primary-opacity-30);
  color: var(--brand-primary-dark);
}
```

## Border Radius System

A consistent radius system prevents the "Frankenstein" look where different components have mismatched corner shapes.

### Radius Scale

| Type | Value | Tailwind | Use Case |
|------|-------|----------|----------|
| Sharp | 0px | `rounded-none` | Precise, technical layouts |
| Subtle | 4px | `rounded-sm` | Small inputs, nested items |
| Standard | 8px | `rounded-md` | Buttons, default cards |
| Large | 12px | `rounded-lg` | Modals, main cards |
| Extra | 24px | `rounded-3xl` | Promotional banners |
| Pill | 9999px | `rounded-full` | Tags, circular buttons |

### Nested Corner Rule
When nesting a rounded element inside another, the inner radius should be smaller than the outer radius to maintain a consistent gap.
`inner_radius = outer_radius - padding`

## State Polish (Hover/Active/Disabled)

The feedback given when interacting with an element defines the "feel" of the UI.

### Hover States
Avoid binary "on/off" hovers. Use transitions and subtle color shifts.
- **Background Shift**: Lighten or darken the background by 5-10%.
- **Lift Effect**: Combine `translate-y-[-1px]` with a slightly larger shadow.
- **Ring Inset**: Use `ring-inset` for buttons to add internal depth on hover.

### Active (Pressed) States
Give immediate tactile feedback.
- **Scale Down**: `active:scale-[0.98]` creates a "pressed" feeling.
- **Shadow Inset**: Replace external shadows with `shadow-inner`.

### Disabled States
Disabled elements should look inactive but remain legible.
- **Opacity**: Use `opacity-50` or `opacity-40`.
- **Cursor**: Use `cursor-not-allowed`.
- **Contrast**: Ensure text still meets minimum contrast ratios if the element conveys important information.

## Layout and Constraints

Visual polish includes how content sits within the viewport.

### Reading Length
Limit the width of text blocks to 45-75 characters per line (approx 600-800px) for optimal readability.
- `max-w-prose` or `max-w-2xl`.

### Centering and Max-Widths
Never let content stretch to the edges of a 4K monitor. Always use a max-width container with auto margins.
- `max-w-screen-xl mx-auto px-4`.

## Anti-Patterns

### Too Many Shadows
Shadows should represent hierarchy. Applying a shadow to every element flattens the UI and creates visual noise. Use borders for separation on the same plane; reserve shadows for elevation changes.

### Inconsistent Spacing
Mixing 4px, 5px, and 10px spacing makes a layout feel "off" even if the user can't pinpoint why. Strictly adhere to the 4px/8px grid.

### Pure White Backgrounds
Pure `#ffffff` on large screens can cause eye strain. Use a very subtle off-white (e.g., `#fafafa` or `slate-50`) for a more "printed" and premium feel.

### Decorative Gradients
Gradients should be used to add depth, not just for the sake of decoration. Avoid high-contrast gradients (e.g., red to blue) unless it is a core brand element. Stick to analogous colors (e.g., blue to indigo).

### Over-rounding
Rounding everything to the maximum (`rounded-2xl`) can make a UI look childish or "bubbly." Balance rounded components with structured, straight edges for a professional look.

### Focus Ring Removal
Never use `outline: none` without providing a high-visibility `focus-visible` alternative. Accessibility is a requirement of premium software.

### Default Scrollbars
On desktop, default scrollbars often break the visual theme. Use `scrollbar-gutter: stable` to prevent layout shifts and customize the scrollbar appearance to match the UI.

```css
::-webkit-scrollbar {
  width: 10px;
}
::-webkit-scrollbar-thumb {
  background: var(--slate-300);
  border-radius: 5px;
  border: 2px solid transparent;
  background-clip: content-box;
}
```

## The AI Slop Test

Every LLM trained on the same templates produces the same predictable mistakes. If someone saw your interface and immediately thought "AI made this," the design has failed. A distinctive interface makes people ask *"how was this made?"* not *"which AI made this?"*

### AI-Generated Design Fingerprints to Avoid

**Typography**:
- Inter, Roboto, Arial, Open Sans as default choices — use distinctive alternatives (see `references/design-foundations.md`)
- Monospace font as shorthand for "technical/developer" aesthetic
- Large rounded-corner icons above every heading (makes sites look templated)

**Color**:
- The AI palette: cyan-on-dark, purple-to-blue gradients, neon accents on dark backgrounds
- Gray text on colored backgrounds (looks washed out — use a shade of the background color)
- Pure black `#000` or pure white `#fff` (tint everything — pure values don't exist in nature)
- Gradient text on headings or metrics for "impact" (decorative noise, not meaningful emphasis)
- Defaulting to dark mode with glowing accents (avoids real design decisions)

**Layout**:
- Wrapping everything in cards — spacing and alignment create grouping naturally
- Nesting cards inside cards — flatten the hierarchy with typography and dividers
- Identical card grids: same-sized cards with icon + heading + text, repeated endlessly
- The "hero metric" template: big number, small label, supporting stats, gradient accent
- Centering everything — left-aligned text with asymmetric layouts feels more intentional
- Uniform spacing everywhere — without rhythm variation, layouts feel monotonous

**Visual Details**:
- Glassmorphism used decoratively (blur effects, glass cards, glow borders without purpose)
- Rounded rectangles with a thick colored border on one side (lazy accent)
- Sparklines as decoration (tiny charts that convey nothing meaningful)
- Generic drop shadows on rounded rectangles (safe, forgettable, could be any AI output)

**Motion**:
- Bounce or elastic easing (dated — real objects decelerate smoothly)
- Animating layout properties (width, height, padding) instead of transform/opacity

### The Fix

Commit to a design direction before writing code. Ask: What problem does this solve? Who is the audience? What tone — brutalist, editorial, playful, luxury, organic? What's the ONE thing someone will remember? Bold maximalism and refined minimalism both work; the failure mode is timid middle-ground that looks like every other AI output.
