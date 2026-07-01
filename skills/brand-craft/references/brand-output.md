# Brand Identity Output Formats

Sources: Wheeler (Designing Brand Identity), modern design systems patterns, Tailwind CSS conventions

This file covers every output format for brand identity deliverables. It does not cover how to choose colors (color-strategy.md), how to generate logos (logo-creation.md), or brand strategy (brand-sprint.md).

---

## 1. Brand Identity JSON Schema

The canonical machine-readable format. Every downstream output — CSS tokens, Tailwind config, HTML guidelines, AI prompts — derives from this schema. Store as `brand.json` at the project root.

```json
{
  "brand": {
    "name": "Meridian",
    "tagline": "Navigate with confidence",
    "archetype": "Sage",
    "personality": ["authoritative", "clear", "trustworthy", "precise"],
    "positioning": "For professionals who need reliable data, Meridian is the analytics platform that turns complexity into clarity because our algorithms surface signal, not noise."
  },
  "colors": {
    "primary": {
      "50":"#EFF8FF","100":"#DBEFFE","200":"#BAE0FD","300":"#7CC8FB","400":"#38AEF8",
      "500":"#0E96E8","600":"#0278C7","700":"#035FA0","800":"#074F82","900":"#0C3D61"
    },
    "secondary": { "500":"#0F172A","600":"#0A1020" },
    "accent":    { "400":"#FFA040","500":"#FF7A00","600":"#CC6200" },
    "neutral": {
      "50":"#F8FAFC","100":"#F1F5F9","200":"#E2E8F0","400":"#94A3B8",
      "600":"#475569","700":"#334155","800":"#1E293B","900":"#0F172A"
    },
    "semantic": {
      "success":"#10B981","warning":"#F59E0B","error":"#EF4444","info":"#3B82F6"
    }
  },
  "typography": {
    "heading": {
      "family": "Sora", "weights": [400, 600, 700],
      "googleFontsUrl": "https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap"
    },
    "body": {
      "family": "Inter", "weights": [400, 500],
      "googleFontsUrl": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap"
    },
    "scaleRatio": 1.333,
    "hierarchy": {
      "display":"3.998rem","h1":"2.998rem","h2":"2.249rem",
      "h3":"1.688rem","h4":"1.266rem","body":"1rem","small":"0.75rem"
    }
  },
  "logo": {
    "description": "Geometric compass rose, four cardinal triangles, two in primary-500, two in neutral-900.",
    "promptTemplates": {
      "mark":   "Geometric compass rose, four triangular points, flat vector, #0E96E8 and #0F172A, symmetrical, no text, no gradients, white background",
      "lockup": "Professional logo for 'Meridian'. Compass symbol left, wordmark right. Flat vector, minimal, two colors, white background, no gradients",
      "icon":   "Minimal compass icon, four-point star, flat vector, single color #0E96E8, centered, white background"
    },
    "variants": ["full", "icon", "mono", "reversed"],
    "clearSpace": "Equal to the cap-height of the wordmark on all four sides",
    "minSize": "24px height digital; 8mm height print"
  },
  "voice": {
    "tone": ["precise", "confident", "direct", "never condescending"],
    "do":   ["Use active voice","Lead with the insight","Quantify claims when possible"],
    "dont": ["Use jargon without definition","Hedge with 'might' or 'could'","Use exclamation marks"]
  }
}
```

---

## 2. CSS Design Tokens

Generate CSS custom properties from the brand JSON. These tokens are the single source of truth for all web implementations.

```css
/* brand-tokens.css */
:root {
  --brand-primary-50: #EFF8FF;  --brand-primary-100: #DBEFFE;
  --brand-primary-200: #BAE0FD; --brand-primary-300: #7CC8FB;
  --brand-primary-400: #38AEF8; --brand-primary-500: #0E96E8;
  --brand-primary-600: #0278C7; --brand-primary-700: #035FA0;
  --brand-primary-800: #074F82; --brand-primary-900: #0C3D61;

  --brand-accent-400: #FFA040; --brand-accent-500: #FF7A00; --brand-accent-600: #CC6200;

  --brand-neutral-50: #F8FAFC;  --brand-neutral-100: #F1F5F9;
  --brand-neutral-200: #E2E8F0; --brand-neutral-400: #94A3B8;
  --brand-neutral-600: #475569; --brand-neutral-800: #1E293B;
  --brand-neutral-900: #0F172A;

  --brand-success: #10B981; --brand-warning: #F59E0B;
  --brand-error:   #EF4444; --brand-info:    #3B82F6;

  --font-heading: 'Sora', system-ui, sans-serif;
  --font-body:    'Inter', system-ui, sans-serif;

  /* Type scale — Perfect Fourth (1.333) */
  --text-sm:  0.75rem;  --text-base: 1rem;     --text-lg:  1.266rem;
  --text-xl:  1.688rem; --text-2xl:  2.249rem; --text-3xl: 2.998rem;
  --text-4xl: 3.998rem;

  /* Spacing — 4px base unit */
  --space-1: 0.25rem; --space-2: 0.5rem;  --space-4: 1rem;
  --space-6: 1.5rem;  --space-8: 2rem;    --space-12: 3rem;
  --space-16: 4rem;   --space-24: 6rem;
}
```

---

## 3. Tailwind CSS Theme

Generate the `extend` block for `tailwind.config.js` from the brand JSON.

```js
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{html,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:'#EFF8FF', 100:'#DBEFFE', 200:'#BAE0FD', 300:'#7CC8FB', 400:'#38AEF8',
          500:'#0E96E8', 600:'#0278C7', 700:'#035FA0', 800:'#074F82', 900:'#0C3D61',
        },
        accent: { 400:'#FFA040', 500:'#FF7A00', 600:'#CC6200' },
      },
      fontFamily: {
        heading: ['Sora', 'system-ui', 'sans-serif'],
        body:    ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'display': ['3.998rem', { lineHeight:'1.1',  letterSpacing:'-0.02em' }],
        'h1':      ['2.998rem', { lineHeight:'1.15', letterSpacing:'-0.015em' }],
        'h2':      ['2.249rem', { lineHeight:'1.2',  letterSpacing:'-0.01em' }],
        'h3':      ['1.688rem', { lineHeight:'1.3' }],
      },
    },
  },
};
```

Usage: `<h1 class="font-heading text-h1 text-brand-900">`, `<button class="bg-accent-500 hover:bg-accent-600">`.

---

## 4. Markdown Brand Guidelines Document

Output a complete brand guideline as Markdown for client delivery or repository storage.

```markdown
# [Brand Name] Brand Guidelines — Version 1.0

## Brand Story
[Brand name] exists to [mission]. Archetype: **[Archetype]** — [one sentence].
**Positioning:** [positioning statement]

## Logo
| Variant | File | Use When |
|---------|------|----------|
| Full lockup | `logo-full.svg` | Default; wherever space allows |
| Icon mark | `logo-icon.svg` | App icons, favicons, square contexts |
| Monochrome | `logo-mono.svg` | Single-color print, embossing |
| Reversed | `logo-reversed.svg` | Dark backgrounds |

Clear space: [rule]. Minimum size: [digital] / [print].
Do not: stretch, rotate, apply effects, use unapproved colors, or place on busy backgrounds.

## Color Palette
| Role | Hex | Use |
|------|-----|-----|
| Primary 500 | `#0E96E8` | Main brand color, CTAs |
| Accent 500  | `#FF7A00` | Highlights, secondary CTAs |
| Neutral 600 | `#475569` | Body text |
| Neutral 900 | `#0F172A` | Headings |
| Success | `#10B981` | Confirmations |
| Warning | `#F59E0B` | Cautions |
| Error   | `#EF4444` | Errors |

## Typography
**Heading:** [family], weights [weights]  **Body:** [family], weights [weights]

| Level | Size | Weight | Use |
|-------|------|--------|-----|
| Display | 3.998rem | 700 | Hero headlines |
| H1 | 2.998rem | 700 | Page titles |
| H2 | 2.249rem | 600 | Section headings |
| Body | 1rem | 400 | Running text |

## Voice and Tone
**Tone:** [adjectives]

| Do | Do Not |
|----|--------|
| Use active voice | Use jargon without definition |
| Lead with the insight | Hedge with "might" or "could" |
| Quantify claims when possible | Use exclamation marks |
```

---

## 5. HTML Brand Guidelines Page

A self-contained single-page HTML document. Deliver as `brand-guidelines.html`. Replace `[LOGO_SVG_*]` with inline SVG content. Inline SVG is preferred over `<img>` tags: it inherits CSS color, scales without HTTP requests, and supports dark mode via `currentColor`.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>[Brand Name] Brand Guidelines</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=Inter:wght@400;500&display=swap">
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    :root{--p:#0E96E8;--p-lt:#EFF8FF;--acc:#FF7A00;
          --n50:#F8FAFC;--n200:#E2E8F0;--n600:#475569;--n900:#0F172A;
          --fh:'Sora',system-ui,sans-serif;--fb:'Inter',system-ui,sans-serif}
    body{font-family:var(--fb);color:var(--n900);background:var(--n50);line-height:1.6}
    .wrap{max-width:960px;margin:0 auto;padding:3rem 2rem}
    h1,h2,h3{font-family:var(--fh)}
    .cover{background:var(--n900);color:#fff;padding:4rem 2rem;margin-bottom:3rem}
    .cover h1{font-size:2.5rem;font-weight:700}
    .cover p{color:var(--n600);margin-top:.5rem}
    section{margin-bottom:3rem}
    section>h2{font-size:1.2rem;font-weight:600;border-bottom:2px solid var(--p);
               padding-bottom:.4rem;margin-bottom:1.5rem}
    .logo-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem}
    .logo-card{border:1px solid var(--n200);border-radius:8px;padding:1.5rem;
               display:flex;flex-direction:column;align-items:center;gap:.75rem}
    .logo-card.dark{background:var(--n900)}
    .logo-card.brand{background:var(--p)}
    .logo-card span{font-size:.7rem;color:var(--n600)}
    .logo-card.dark span,.logo-card.brand span{color:rgba(255,255,255,.6)}
    .swatches{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1.5rem}
    .sw{width:72px;border-radius:6px;overflow:hidden;border:1px solid var(--n200)}
    .sw-c{height:52px}
    .sw-l{padding:.3rem .4rem;font-size:.6rem;line-height:1.4}
    .sw-l strong{display:block}
    .specimen{margin-bottom:1rem;padding:1.25rem;background:#fff;
              border-radius:8px;border:1px solid var(--n200)}
    .specimen-meta{font-size:.7rem;color:var(--n600);margin-bottom:.5rem}
    table{width:100%;border-collapse:collapse}
    th,td{text-align:left;padding:.6rem .75rem;border-bottom:1px solid var(--n200);font-size:.875rem}
    th{font-weight:600;background:var(--p-lt)}
  </style>
</head>
<body>
<div class="cover"><div class="wrap" style="padding-top:0;padding-bottom:0">
  <h1>[Brand Name]</h1><p>Brand Guidelines — Version 1.0</p>
</div></div>
<div class="wrap">
  <section>
    <h2>Logo</h2>
    <div class="logo-grid">
      <div class="logo-card">[LOGO_SVG_FULL]<span>Full lockup — light</span></div>
      <div class="logo-card dark">[LOGO_SVG_REVERSED]<span>Reversed — dark</span></div>
      <div class="logo-card brand">[LOGO_SVG_ICON]<span>Icon — brand bg</span></div>
      <div class="logo-card">[LOGO_SVG_MONO]<span>Monochrome</span></div>
    </div>
  </section>
  <section>
    <h2>Color Palette</h2>
    <!-- Repeat .sw for each color stop. bg = hex value. -->
    <div class="swatches">
      <div class="sw"><div class="sw-c" style="background:#EFF8FF"></div><div class="sw-l"><strong>50</strong>#EFF8FF</div></div>
      <div class="sw"><div class="sw-c" style="background:#0E96E8"></div><div class="sw-l"><strong>500</strong>#0E96E8</div></div>
      <div class="sw"><div class="sw-c" style="background:#0C3D61"></div><div class="sw-l" style="background:#0C3D61;color:#fff"><strong>900</strong>#0C3D61</div></div>
      <div class="sw"><div class="sw-c" style="background:#FF7A00"></div><div class="sw-l"><strong>Accent</strong>#FF7A00</div></div>
      <div class="sw"><div class="sw-c" style="background:#10B981"></div><div class="sw-l"><strong>Success</strong>#10B981</div></div>
      <div class="sw"><div class="sw-c" style="background:#EF4444"></div><div class="sw-l"><strong>Error</strong>#EF4444</div></div>
    </div>
  </section>
  <section>
    <h2>Typography</h2>
    <div class="specimen">
      <div class="specimen-meta">Display — Sora 700 — 3.998rem</div>
      <div style="font-family:'Sora',sans-serif;font-size:2.5rem;font-weight:700;
                  line-height:1.1;letter-spacing:-.02em">The quick brown fox</div>
    </div>
    <div class="specimen">
      <div class="specimen-meta">H1 — Sora 700 — 2.998rem</div>
      <div style="font-family:'Sora',sans-serif;font-size:2rem;font-weight:700">Page Title Heading</div>
    </div>
    <div class="specimen">
      <div class="specimen-meta">Body — Inter 400 — 1rem / 1.6</div>
      <div style="font-family:'Inter',sans-serif">The quick brown fox jumps over the lazy dog.
        Brand typography should be legible at all sizes and convey personality through weight and proportion.</div>
    </div>
  </section>
  <section>
    <h2>Voice and Tone</h2>
    <table>
      <thead><tr><th>Do</th><th>Do Not</th></tr></thead>
      <tbody>
        <tr><td>Use active voice</td><td>Use jargon without definition</td></tr>
        <tr><td>Lead with the insight</td><td>Hedge with "might" or "could"</td></tr>
        <tr><td>Quantify claims when possible</td><td>Use exclamation marks</td></tr>
      </tbody>
    </table>
  </section>
</div>
</body>
</html>
```

---

## 6. Dark Mode Specifications

Derive dark mode values from the brand palette by inverting the neutral lightness axis and shifting the primary to a lighter shade for interactive elements.

```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg-page:    #0F172A;  /* neutral-900 */
    --bg-surface: #1E293B;  /* neutral-800 */
    --bg-raised:  #334155;  /* neutral-700 */

    --text-primary:   #F1F5F9;  /* neutral-100 */
    --text-secondary: #94A3B8;  /* neutral-400 */
    --text-muted:     #64748B;  /* neutral-500 */
    --border:         #334155;  /* neutral-700 */

    /* Shift primary from 500 to 400 for legibility on dark backgrounds */
    --brand-interactive:       #38AEF8;  /* primary-400 */
    --brand-interactive-hover: #7CC8FB;  /* primary-300 */

    /* Warm accent reads well on dark without adjustment */
    --accent-interactive: #FF7A00;

    /* Semantic: shift one step lighter */
    --brand-success: #34D399;
    --brand-warning: #FCD34D;
    --brand-error:   #F87171;
  }
}
```

Never use primary-500 as text on dark backgrounds without verifying contrast (WCAG AA: 4.5:1 for body text, 3:1 for large text).

---

## 7. Programmatic Color Scale Generation

Generate a 9-shade scale from a single hex using culori and OKLCH. OKLCH is perceptually uniform — equal numeric steps produce equal perceived lightness changes, avoiding the "blue hump" problem in HSL.

```javascript
import { oklch, formatHex } from "culori"; // npm install culori

// Input color anchors at 500. Returns { 50, 100, 200, 300, 400, 500, 600, 700, 800, 900 }.
function generateColorScale(baseHex) {
  const base = oklch(baseHex);
  if (!base) throw new Error(`Invalid hex: ${baseHex}`);

  const stops     = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900];
  const lightness = [0.97, 0.94, 0.88, 0.79, 0.68, base.l,
                     base.l * 0.82, base.l * 0.65, base.l * 0.48, base.l * 0.32];
  const chroma    = [0.08, 0.15, 0.30, 0.55, 0.78, 1.0,
                     0.92, 0.80, 0.65, 0.50].map(f => base.c * f);

  return Object.fromEntries(stops.map((stop, i) => [
    stop,
    formatHex({ mode: "oklch", l: lightness[i], c: chroma[i], h: base.h })
  ]));
}

/** Near-neutral scale with a subtle brand hue tint. */
function generateNeutralScale(brandHex) {
  const base = oklch(brandHex);
  const stops     = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900];
  const lightness = [0.98, 0.96, 0.92, 0.84, 0.70, 0.55, 0.42, 0.32, 0.22, 0.13];
  return Object.fromEntries(stops.map((stop, i) => [
    stop,
    formatHex({ mode: "oklch", l: lightness[i], c: 0.012, h: base.h })
  ]));
}

// Usage — outputs hex values ready to paste into brand.json
const primary = generateColorScale("#0E96E8");
const neutral = generateNeutralScale("#0E96E8");
```

---

## 8. Brand Asset Checklist

A complete brand kit includes these files. Verify each before delivery.

**Logo files** (SVG + PNG for each variant)
- `logo-full.svg` / `logo-full-reversed.svg` / `logo-full-mono.svg`
- `logo-icon.svg` / `logo-icon-reversed.svg` / `logo-icon-mono.svg`
- `logo-full-512.png`, `logo-icon-512.png`, `logo-icon-192.png`
- `favicon.ico` (16×16 + 32×32), `apple-touch-icon.png` (180×180)

**Token and config files**
- `brand.json` — Master brand schema
- `brand-tokens.css` — CSS custom properties
- `tailwind.config.js` — Tailwind theme extension

**Guideline documents**
- `brand-guidelines.html` — Standalone HTML page
- `brand-guidelines.md` — Markdown version for repositories

**Font files** (if self-hosting)
- `fonts/[HeadingFamily]-[weight].woff2`
- `fonts/[BodyFamily]-[weight].woff2`

**Mockup exports**
- `mockup-business-card.png`, `mockup-website-header.png`
- `mockup-social-og.png` — 1200×630 Open Graph template

**SVG validation before delivery**
- Contains `viewBox` attribute; no embedded raster data (`data:image/`)
- No `<script>` elements; no external `href` references
- Under 15KB for full lockup; under 3KB for icon mark
