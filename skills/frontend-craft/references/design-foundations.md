# Design Foundations

Sources: Butterick (Practical Typography), Wathan/Schoger (Refactoring UI), Itten (Art of Color), CSS Color Level 4 specification

Covers: vertical rhythm, modular type scales, font selection, web font loading, OpenType features, fluid type, color theory with OKLCH, palette structure, contrast requirements, spatial design, grid systems, touch targets, z-index semantics.

---

## Typography

### Vertical Rhythm

Vertical rhythm treats line-height as the base unit for all vertical spacing. When every spacing value is a multiple of the base line-height, text and layout elements fall on a consistent grid — the page feels ordered even when the reader can't articulate why.

```css
:root {
  font-size: 16px;
  line-height: 1.5;       /* base unit = 16 × 1.5 = 24px */
  --rhythm: 1.5rem;       /* 24px */
  --rhythm-half: 0.75rem; /* 12px */
  --rhythm-2x: 3rem;      /* 48px */
}
```

Apply rhythm to `margin-block-end`, `padding-block`, and `gap`. Headings should sit at a rhythm multiple above the paragraph they introduce. When something looks "off" in a layout, check whether vertical spacing is on-rhythm — off-rhythm gaps are the most common source of that vague "unpolished" feeling.

---

### Modular Type Scale

A modular scale generates harmonious size steps from a single ratio. Five named sizes cover most interfaces.

| Token | Ratio 1.25 | Ratio 1.333 | Ratio 1.5 | Typical Role |
|-------|-----------|-------------|-----------|--------------|
| `--text-xs` | ~10px | ~9px | ~7px | Captions, timestamps |
| `--text-sm` | ~13px | ~12px | ~11px | Labels, helper text |
| `--text-base` | 16px | 16px | 16px | Body copy, default UI |
| `--text-lg` | ~20px | ~21px | ~24px | Subheadings, card titles |
| `--text-xl` | ~25px | ~28px | ~36px | Section headings |
| `--text-2xl+` | ~31px+ | ~37px+ | ~54px+ | Hero headlines |

**Ratio selection:** 1.25 (major third) for dense dashboards; 1.333 (perfect fourth) for general apps; 1.5 (perfect fifth) for editorial. Pick one and derive all sizes from it — arbitrary values like 15px or 22px break the harmonic relationship.

---

### Font Selection

The most overused fonts signal "default" to trained eyes. Swapping to a less-familiar but equally legible alternative costs nothing and immediately elevates perceived quality.

| Overused | Distinctive Alternatives | Character |
|----------|--------------------------|-----------|
| Inter | Instrument Sans, Plus Jakarta Sans, Outfit | Geometric-neutral, modern |
| Roboto | Onest, Figtree, Urbanist | Friendly, contemporary |
| Open Sans | Source Sans 3, Nunito Sans, DM Sans | Humanist, approachable |

**For editorial and premium contexts:** Fraunces (display, brand moments), Newsreader (long-form reading), Lora (editorial, approachable serif).

**Do you need a second font?** Usually no. A single typeface with varied weight, size, and color creates sufficient hierarchy for most products. Add a second font only when you need a clear editorial/UI contrast.

**When pairing, contrast on multiple axes simultaneously:**

| Axis | Example |
|------|---------|
| Classification | Serif headline + sans body |
| Geometry | Geometric display + humanist text |
| Width | Condensed heading + regular body |

Never pair two fonts that are similar but not identical (e.g., two geometric sans-serifs). The result reads as a mistake, not a choice.

---

### Web Font Loading

**`font-display: swap`** shows fallback immediately, swaps when font loads. Prevents invisible text but causes a reflow.

**Metric overrides** eliminate reflow by adjusting the fallback font's metrics to match the web font:

```css
@font-face {
  font-family: 'Instrument Sans Fallback';
  src: local('Arial');
  size-adjust: 98.5%;
  ascent-override: 95%;
  descent-override: 25%;
  line-gap-override: 0%;
}

body {
  font-family: 'Instrument Sans', 'Instrument Sans Fallback', sans-serif;
}
```

**Fontaine** (npm) automates metric override generation for Next.js and Nuxt. Loading strategy: preload the primary weight, only load weights you use, prefer variable fonts, self-host when possible.

---

### OpenType Features

| Feature | CSS | Use Case | Avoid When |
|---------|-----|----------|------------|
| Tabular numerals | `font-variant-numeric: tabular-nums` | Tables, prices, counters | Running prose |
| Diagonal fractions | `font-variant-numeric: diagonal-fractions` | Recipes, measurements | Most UI |
| All small caps | `font-variant-caps: all-small-caps` | Abbreviations (API, URL) | Body text |
| No ligatures | `font-variant-ligatures: no-common-ligatures` | Code blocks | — |
| Oldstyle figures | `font-variant-numeric: oldstyle-nums` | Running text with numbers | Tables |

Check support before using: [Wakamai Fondue](https://wakamaifondue.com) — drop a font file to see every feature it supports.

---

### Fluid Type with `clamp()`

```css
/* Hero headline: 2rem at 320px, scales to 5rem at 1280px */
.hero-title   { font-size: clamp(2rem, 1rem + 4vw, 5rem); }
.section-head { font-size: clamp(1.5rem, 0.75rem + 2.5vw, 2.5rem); }
```

**Use for:** hero headlines, display text, section headings — elements where dramatic size change is intentional. **Do NOT use for:** buttons, labels, navigation, form inputs, body text — UI elements need predictable sizes, and fluid body text breaks vertical rhythm.

[Utopia.fyi](https://utopia.fyi) calculates clamp values from min/max viewport and font size. Use it rather than guessing the vw coefficient.

---

### Readability Fundamentals

| Rule | Value | Reasoning |
|------|-------|-----------|
| Line length | `max-width: 65ch` | 45–75 characters per line is optimal |
| Minimum body size | 16px (1rem) | Below this, reading requires effort |
| Units | `rem` for font-size, `em` for relative spacing | Respects user browser settings |
| Light-on-dark line-height | +0.05–0.1 above light-mode value | Dark backgrounds reduce perceived line contrast |
| Viewport meta | Never `user-scalable=no` | Breaks accessibility; illegal in some jurisdictions |

---

## Color and OKLCH

### Why OKLCH Replaces HSL

HSL is not perceptually uniform. Two colors at identical HSL lightness values look dramatically different — yellow at `hsl(60, 100%, 50%)` appears far brighter than blue at `hsl(240, 100%, 50%)`. OKLCH (Oklab Lightness, Chroma, Hue) is perceptually uniform: equal steps in L produce equal-looking steps in brightness.

```css
/* oklch(lightness% chroma hue) */
.primary       { color: oklch(55% 0.18 250); }  /* medium blue */
.primary-light { color: oklch(75% 0.12 250); }  /* lighter, less chroma */
.primary-dark  { color: oklch(35% 0.14 250); }  /* darker, less chroma */
```

**The chroma rule:** Reduce chroma as lightness approaches 0% or 100%. High chroma at extreme lightness looks garish — colors in the real world desaturate near white and black:

```css
--blue-100: oklch(93% 0.04 250);  /* very light, low chroma */
--blue-500: oklch(55% 0.18 250);  /* mid-tone, full chroma */
--blue-900: oklch(22% 0.06 250);  /* very dark, low chroma */
```

---

### Tinted Neutrals

Pure gray (`oklch(50% 0 0)`) reads as lifeless. Adding a tiny amount of brand hue to all neutrals creates cohesion without visible color — a chroma of 0.01–0.02 is invisible in isolation but creates harmony next to brand colors.

```css
--neutral-500: oklch(50% 0.01 250);  /* cool-tinted (blue hue) */
--neutral-500: oklch(50% 0.01 80);   /* warm-tinted (orange hue) */
```

---

### Palette Structure

| Role | Purpose | OKLCH Range |
|------|---------|-------------|
| Primary | CTAs, links, focus rings | L: 45–65%, C: 0.12–0.22 |
| Neutral | Text, borders, surfaces | L: 10–97%, C: 0.01–0.02 |
| Semantic | Success, warning, error, info | Varies by hue |
| Surface | Page bg, card bg, overlays | L: 95–99% light / 8–18% dark |

Resist adding secondary and tertiary accents until the design genuinely requires them — each additional accent dilutes the primary's impact.

---

### The 60-30-10 Rule

Visual weight distribution, not pixel count:
- **60% Neutral** — backgrounds, large surfaces, whitespace. The canvas.
- **30% Secondary** — body text, borders, secondary UI. The structure.
- **10% Accent** — primary buttons, active states, key highlights. The signal.

The accent works *because* it's rare. When accent appears everywhere, it stops signaling importance. If you want more accent, the problem is usually insufficient hierarchy in the neutral layer.

---

### Contrast Requirements

| Context | AA Minimum | AAA Target |
|---------|-----------|------------|
| Body text (< 18px) | 4.5:1 | 7:1 |
| Large text (≥ 18px or 14px bold) | 3:1 | 4.5:1 |
| UI components, icons | 3:1 | — |
| Placeholder text | 4.5:1 | — |
| Disabled states | None required | Aim for 3:1 |

Placeholder text is the most commonly overlooked — it still needs 4.5:1 despite being "secondary."

---

### Dangerous Color Combinations

| Combination | Problem | Fix |
|-------------|---------|-----|
| Light gray on white | Most common contrast failure | Darken text to 4.5:1 |
| Gray on colored background | Background hue shifts perceived contrast | Always check on actual background |
| Red on green | Invisible to ~8% of men | Add shape/icon differentiation |
| Blue on red | Chromatic aberration — edges vibrate | Separate with neutral |
| Yellow on white | Extremely low contrast | Yellow needs dark backgrounds |

---

### Dark Mode Is Not Inverted Light Mode

| Aspect | Light Mode | Dark Mode |
|--------|-----------|-----------|
| Shadows | Darken downward | Lighter surface = higher elevation |
| Accent colors | Full chroma | Reduce chroma 20–30%; high chroma looks neon |
| Backgrounds | `oklch(99% 0.01 hue)` | `oklch(12–18% 0.01 hue)` — never pure black |
| Text | Dark on light | `oklch(92–95% 0.01 hue)` — never pure white |

```css
@media (prefers-color-scheme: dark) {
  :root {
    --surface-base:    oklch(12% 0.01 250);
    --surface-raised:  oklch(16% 0.01 250);
    --surface-overlay: oklch(20% 0.01 250);
    --surface-highest: oklch(24% 0.01 250);
  }
}
```

Each step is +4% lightness. The difference is subtle but creates clear depth without shadows.

---

### Token Hierarchy

Two-layer architecture separates raw values from semantic meaning. Dark mode only redefines the semantic layer.

```css
/* Layer 1: Primitives — never used directly in components */
:root {
  --blue-500: oklch(55% 0.18 250);
  --blue-400: oklch(65% 0.16 250);
  --neutral-900: oklch(14% 0.01 250);
}

/* Layer 2: Semantic — used in components */
:root {
  --color-primary:   var(--blue-500);
  --color-text:      var(--neutral-900);
}

/* Dark mode: only redefine semantic layer */
@media (prefers-color-scheme: dark) {
  :root {
    --color-primary: var(--blue-400);
    --color-text:    oklch(92% 0.01 250);
  }
}
```

Components reference only semantic tokens. Dark mode becomes a single block of overrides, not scattered `@media` queries throughout the codebase.

---

### Alpha Is a Design Smell

Heavy use of `rgba` or `oklch(... / 0.5)` usually signals an incomplete palette. Transparent colors shift appearance depending on what's behind them.

```css
/* Smell: unpredictable on different backgrounds */
.badge { background: oklch(55% 0.18 250 / 0.15); }

/* Better: explicit surface-aware color */
.badge { background: var(--color-primary-subtle); }
/* light: oklch(93% 0.04 250) / dark: oklch(22% 0.06 250) */
```

Legitimate uses: scrim overlays behind modals, focus rings, drag-and-drop indicators where the background must show through.

---

## Spatial Design

### The 4pt Base Grid

8pt grids are too coarse — you frequently need values between 8px and 16px. A 4pt base provides those intermediate steps without arbitrary values.

**Scale:** 4, 8, 12, 16, 24, 32, 48, 64, 96px

Never use: 5px, 7px, 10px, 15px, 18px, 20px, 22px. These break the grid and signal "I eyeballed it."

**Semantic token naming** — name by relationship, not value:

```css
:root {
  --space-1:  0.25rem;  /* 4px  — icon gap, tight inline */
  --space-2:  0.5rem;   /* 8px  — input padding, list gap */
  --space-3:  0.75rem;  /* 12px — button padding, form gap */
  --space-4:  1rem;     /* 16px — card padding */
  --space-6:  1.5rem;   /* 24px — component separation */
  --space-8:  2rem;     /* 32px — section padding */
  --space-12: 3rem;     /* 48px — major section break */
  --space-16: 4rem;     /* 64px — hero padding */
}
```

Use `gap` for siblings, not margins. `gap` in flex/grid is symmetric and doesn't collapse. Margins between siblings create asymmetric spacing that breaks when items reorder.

---

### Self-Adjusting Grid

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
}
```

Cards are at least 280px wide. When the viewport can't fit two cards at 280px, it drops to one column automatically. No media queries needed. Adjust `280px` to match your content's minimum readable width.

---

### The Squint Test

Blur your eyes or apply a Gaussian blur to a screenshot. You should be able to answer:
1. What is the most important element?
2. What is the second most important?
3. Are related elements visually grouped?

If everything has the same visual weight after blurring, you have a hierarchy problem — not a color or font problem. Hierarchy must be established before polish.

---

### Hierarchy Through Multiple Dimensions

Strong hierarchy uses 2–3 dimensions simultaneously. One dimension alone creates weak differentiation.

| Dimension | Strong Signal | Weak Signal |
|-----------|--------------|-------------|
| Size | 32px vs 14px | 18px vs 16px |
| Weight | 700 vs 400 | 500 vs 400 |
| Color | Brand color vs neutral-400 | neutral-700 vs neutral-500 |
| Position | Top-left vs bottom-right | Slight indent |
| Space | 48px above vs 8px above | 24px vs 16px |

A primary button uses size + color + weight simultaneously — three dimensions make it unmistakable.

---

### Cards: When to Use

Use cards when content items are **distinct and independently actionable**, users need to **visually compare** items, or items need **clear interaction boundaries**. Do not use cards for simple lists, non-actionable content, or purely decorative grouping.

**Never nest cards inside cards.** Visual hierarchy collapses and the interaction model becomes ambiguous. Use a divider or subtle background tint for sub-grouping instead.

---

### Container Queries

Use container queries for components that appear in multiple layout contexts. Viewport queries are for page-level layout; container queries are for component-level adaptation.

```css
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card { display: grid; grid-template-columns: 120px 1fr; }
}

@container card (max-width: 399px) {
  .card { display: flex; flex-direction: column; }
}
```

The same component works correctly in a sidebar (narrow) or main content area (wide) without JavaScript or prop drilling.

---

### Optical Adjustments

Geometric precision and optical precision differ. Trust your eyes over the numbers.

| Situation | Optical Fix |
|-----------|-------------|
| Text at container edge | Looks indented at `padding-left: 16px`; reduce to 12–14px |
| Play/arrow icons | Shift 1–2px right; leftward visual weight |
| Circular icon buttons | Shift icon 1px up; optical center is above geometric center |
| All-caps text | Add `letter-spacing: 0.05–0.1em` |

These adjustments are 1–4px but the difference between "something feels off" and "this feels right" is often exactly here.

---

### Touch Targets

Minimum touch target: 44×44px (Apple HIG) or 48×48dp (Material). The visual element can be smaller — expand the tap area with a pseudo-element.

```css
/* Visual size: 20px icon. Tap area: 44px */
.icon-button {
  position: relative;
  width: 20px;
  height: 20px;
}

.icon-button::before {
  content: '';
  position: absolute;
  inset: -12px; /* 20 + 24 = 44px tap area */
}
```

Particularly important for close buttons, icon-only actions, and inline links in dense layouts.

---

### Z-Index Semantic Scale

Arbitrary z-index values (`999`, `9999`) create fragile stacking contexts. Define a semantic scale and use only those values.

```css
:root {
  --z-base:           0;
  --z-raised:         10;   /* sticky headers, raised cards */
  --z-dropdown:       100;  /* menus, autocomplete */
  --z-sticky:         200;  /* sticky nav */
  --z-modal-backdrop: 300;  /* overlay behind modal */
  --z-modal:          400;  /* modal dialog */
  --z-toast:          500;  /* toast notifications */
  --z-tooltip:        600;  /* tooltips */
}
```

If you need a value not in this scale, add it with a name — don't use a raw number. The name forces you to think about where it belongs in the stacking hierarchy. **On depth:** if you can clearly identify a shadow as a shadow, it's too strong. The most effective shadows are the ones users don't consciously notice.
