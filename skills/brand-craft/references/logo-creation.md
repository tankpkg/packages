# Logo Creation

Sources: Airey (Logo Design Love), Peters (Logos That Last), Wheeler (Designing Brand Identity), fal.ai documentation, QuiverAI documentation

Covers: logo type taxonomy, selection decision tree, design principles, responsive systems, AI generation with code, variant generation, SVG optimization, iteration strategy, negative space techniques.

Does not cover: general SVG optimization deep-dives (see @tank/vector-graphics-gen), color palette construction (see color-strategy.md), typography selection (see typography-system.md).

---

## 1. Logo Type Taxonomy

Seven distinct logo types. Each has a structural definition, a natural fit, and failure modes. Choosing the wrong type is the most common early mistake — it forces the brand to fight its own identity system.

| Type | Definition | Best For | Strengths | Weaknesses |
|------|-----------|----------|-----------|------------|
| **Wordmark** | Brand name in distinctive custom typography | Unique or short names; brands where the name IS the identity | Direct name recognition; scales cleanly; no ambiguity | Requires exceptional typography; fails if name is long or generic |
| **Lettermark** | Initials or abbreviation only | Long company names; established brands with existing recognition | Compact; works at small sizes; professional | Requires prior brand recognition to function; initials may conflict with competitors |
| **Brandmark (Pictorial)** | Recognizable image or icon, no text | Globally recognized brands; brands transcending language | Instantly recognizable at any size; language-independent | Risky for new brands — symbol means nothing without prior exposure |
| **Abstract Mark** | Non-representational geometric form | Brands wanting a unique, ownable shape with no literal meaning | Fully ownable; no literal interpretation limits; works globally | Meaning must be built through marketing investment; can feel arbitrary |
| **Mascot** | Character or illustrated figure | Consumer brands, food/beverage, family audiences, sports | High emotional connection; storytelling vehicle; memorable | Can feel dated; difficult to update; inappropriate for professional services |
| **Emblem** | Text integrated within a badge, seal, or shape | Heritage brands, institutions, automotive, craft beverages | Rich, prestigious, detailed | Poor scalability at small sizes; complex to reproduce in embroidery or embossing |
| **Combination Mark** | Symbol + wordmark together, designed to work separately | Most businesses, especially new ones | Maximum versatility; builds recognition for both elements simultaneously | More complex to manage proportions; requires clear usage rules |

**Selection criteria summary:**

- **Name recognition is low** → use combination mark or wordmark; avoid brandmark alone
- **Name is long (4+ words)** → lettermark or combination mark
- **Global audience, multiple languages** → abstract mark or brandmark
- **Heritage, institutional, craft** → emblem
- **New brand, maximum flexibility** → combination mark (default choice)
- **Scalability is critical (app icon, favicon)** → avoid emblem; favor brandmark or lettermark

---

## 2. Logo Type Selection Decision Tree

Map brand characteristics to the recommended logo type before generating anything.

| Signal | Recommendation | Rationale |
|--------|---------------|-----------|
| Brand is less than 3 years old | Combination mark | Builds both symbol and name recognition simultaneously |
| Name is 1-2 short words, distinctive | Wordmark | The name itself is the asset; let typography carry it |
| Name is 3+ words or an acronym | Lettermark or combination | Long names fail at small sizes |
| Brand operates in multiple countries | Abstract mark or brandmark | Transcends language; no translation issues |
| Industry is finance, law, consulting | Wordmark or lettermark | Professionalism; type-based marks signal authority |
| Industry is food, consumer goods, sports | Combination mark or mascot | Personality and recognition matter more than formality |
| Brand is a heritage institution (50+ years) | Emblem | Signals tradition, authority, permanence |
| Primary use is digital (app, SaaS) | Combination mark with strong icon | Icon works as app icon; full mark works in marketing |
| Budget is limited, fast launch needed | Wordmark | Simplest to execute well; no symbol to explain |
| Brand has a strong visual metaphor | Brandmark or abstract mark | Lean into the metaphor; make it ownable |

---

## 3. Airey's 7 Principles of Iconic Logo Design

From David Airey's *Logo Design Love* — the practitioner standard for evaluating whether a logo will endure.

**1. Keep it simple.**
Complexity reduces memorability and scalability. A logo must communicate its core idea in a single glance. Remove every element that does not carry meaning. The FedEx logo is two colors and one typeface. The Nike Swoosh is a single path.

**2. Make it relevant.**
The logo must connect to the brand's essence — its industry, audience, and personality. A playful mascot is wrong for a law firm. A formal serif wordmark is wrong for a children's toy brand. Relevance is not decoration; it is the primary function.

**3. Incorporate tradition.**
Timeless beats trendy. Logos designed around current visual trends (gradients, 3D effects, specific typeface fashions) age visibly. Design for a 20-year lifespan. Ask: will this still feel appropriate in 2040?

**4. Aim for distinction.**
The logo must be ownable — different enough from every competitor that it cannot be confused. Research the competitive landscape before designing. Distinction is not novelty for its own sake; it is strategic differentiation made visible.

**5. Commit to memory.**
A logo that cannot be recalled after a single exposure has failed. Memorability comes from simplicity, distinctiveness, and a single dominant idea. Test by asking someone to sketch the logo from memory 24 hours after seeing it.

**6. Think small.**
Design at billboard scale, but test at favicon scale (16×16px). If the logo loses its identity at small sizes, it will fail in the most common digital contexts: browser tabs, app icons, social media avatars. Emblems and complex combination marks frequently fail this test.

**7. Focus on one thing.**
One dominant idea, not many. The FedEx arrow. The Amazon smile. The Apple bite. Logos that try to communicate multiple ideas communicate none of them clearly. Identify the single most important thing the brand needs to say visually, and say only that.

---

## 4. Responsive Logo Systems

Modern brands do not have a single logo — they have a logo system. Every brand needs at minimum four lockups, designed together from the start.

| Lockup | Use Case | Composition |
|--------|----------|-------------|
| **Full combination** | Website header, presentations, print collateral, large formats | Symbol + wordmark, horizontal or stacked |
| **Icon only** | App icon, favicon, social media avatar, embossing, small formats | Symbol alone, no wordmark |
| **Wordmark only** | Horizontal banners, co-branding contexts, text-heavy layouts | Name only, no symbol |
| **Stacked** | Square formats, packaging, profile images | Symbol above wordmark, centered |
| **Favicon** | Browser tab, bookmark, PWA manifest | Extreme simplification — single letter or minimal symbol |

Design rules for the system:

- The icon must be legible at 16×16px without the wordmark present.
- The wordmark must be legible without the symbol present.
- All lockups share the same color palette and typographic treatment.
- Define minimum size for each lockup (e.g., full combination: 120px wide minimum; icon: 24px minimum).
- Define clear space rules: minimum padding equal to the cap-height of the wordmark on all sides.

---

## 5. AI Logo Generation

### Model Selection

| Need | Model | Cost |
|------|-------|------|
| Highest quality SVG logo | QuiverAI Arrow 1 | Free tier (20/week) |
| Logo on fal.ai, standard | Recraft V4 text-to-vector | $0.08 |
| Logo on fal.ai, production | Recraft V4 Pro text-to-vector | $0.30 |
| Specific illustration style (engraving, bold stroke) | Recraft V3 + vectorize | $0.09 |

QuiverAI Arrow 1 is purpose-built for SVG — it produces clean, layered, editable paths. Use it for logo marks when quality matters most. Recraft V4 on fal.ai is the best option when you need the `colors` parameter for brand palette enforcement or are already using the fal.ai ecosystem.

### QuiverAI Arrow — Logo Mark Generation

```javascript
import QuiverAI from "@quiverai/sdk";

const quiver = new QuiverAI({ apiKey: process.env.QUIVER_API_KEY });

const response = await quiver.svgs.generate({
  model: "arrow-1",
  prompt: "abstract mountain peak, geometric, symmetrical, two colors, no text, no gradients, vector logo mark"
});

const svgUrl = response.data[0].url;
const svgContent = await fetch(svgUrl).then(r => r.text());
```

### Recraft V4 — Full Lockup with Brand Colors

```javascript
import { fal } from "@fal-ai/client";

fal.config({ credentials: process.env.FAL_KEY });

const result = await fal.subscribe("fal-ai/recraft/v4/text-to-vector", {
  input: {
    prompt: 'Professional logo for "Meridian" navigation software. Symbol left, company name right. Clean vector, flat, minimal, 2 colors, white background, no gradients',
    image_size: { width: 800, height: 300 },
    colors: [
      { r: 14, g: 165, b: 233 },   // primary blue
      { r: 15, g: 23, b: 42 }      // dark navy
    ],
    background_color: { r: 255, g: 255, b: 255 }
  }
});

const svgUrl = result.data.images[0].url;
const svgContent = await fetch(svgUrl).then(r => r.text());
```

Convert brand hex values to RGB before passing: `#0EA5E9` → `{ r: 14, g: 165, b: 233 }`. Parse each two-character hex pair as a base-16 integer.

### Prompt Templates

**Logo mark (symbol only):**
```
[shape/concept], geometric, symmetrical, [N] colors, no text, no gradients, vector logo mark
```

Examples:
- `abstract letter A formed from two triangles, geometric, symmetrical, single color, no text, no gradients, vector logo mark`
- `stylized fox head, minimal geometric, facing forward, two colors, no text, no gradients, vector logo mark`
- `mountain peak with sun rays, geometric, centered, navy and gold, no text, no gradients, vector logo mark`

**Full combination lockup:**
```
Professional logo for "[Brand Name]" — [tagline or descriptor]. Symbol left, company name right. Clean vector, flat, minimal, [N] colors, white background, no gradients
```

**Favicon / app icon:**
```
[single bold shape], ultra minimal, bold, [1-2 colors], no fine detail, no text, no gradients
```

**Image size by lockup type:**

| Lockup | `image_size` value | Dimensions |
|--------|-------------------|------------|
| Icon mark | `"square_hd"` | 1024×1024 |
| Horizontal combination | `{ width: 800, height: 300 }` | Custom |
| Stacked combination | `{ width: 600, height: 600 }` | Custom |
| Wide lockup with tagline | `"landscape_4_3"` | 1024×768 |

---

## 6. Logo Variant Generation

Generate all required lockups in a single pipeline. Run the full lockup and icon mark in parallel, then derive mono and reversed variants programmatically.

```javascript
import { fal } from "@fal-ai/client";
import { optimize } from "svgo";

function hexToRgb(hex) {
  const r = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return r ? { r: parseInt(r[1], 16), g: parseInt(r[2], 16), b: parseInt(r[3], 16) } : null;
}

async function fetchAndOptimize(url) {
  const raw = await fetch(url).then(r => r.text());
  return optimize(raw, {
    multipass: true,
    plugins: [{ name: "preset-default", params: { overrides: { removeViewBox: false } } }]
  }).data;
}

async function generateLogoVariants({ name, tagline, primaryHex, secondaryHex }) {
  const primary = hexToRgb(primaryHex);
  const secondary = hexToRgb(secondaryHex);

  const [fullResult, iconResult] = await Promise.all([
    fal.subscribe("fal-ai/recraft/v4/text-to-vector", {
      input: {
        prompt: `Professional logo for "${name}" — ${tagline}. Symbol left, company name right. Clean vector, flat, minimal, 2 colors, white background, no gradients`,
        image_size: { width: 800, height: 300 },
        colors: [primary, secondary],
        background_color: { r: 255, g: 255, b: 255 }
      }
    }),
    fal.subscribe("fal-ai/recraft/v4/text-to-vector", {
      input: {
        prompt: `Logo symbol only for "${name}". No text, centered geometric symbol, flat vector, white background, no gradients`,
        image_size: "square_hd",
        colors: [primary],
        background_color: { r: 255, g: 255, b: 255 }
      }
    })
  ]);

  const fullSvg = await fetchAndOptimize(fullResult.data.images[0].url);
  const iconSvg = await fetchAndOptimize(iconResult.data.images[0].url);

  return {
    full: fullSvg,
    icon: iconSvg,
    mono: iconSvg.replace(/fill="[^"]*"/g, 'fill="#1a1a1a"'),
    reversed: iconSvg.replace(/fill="[^"]*"/g, 'fill="white"')
  };
}
```

The `mono` and `reversed` variants are derived by replacing fill values — no additional API calls required. For dark mode support, convert single-color logos to `currentColor`:

```javascript
function prepareForDarkMode(svgString) {
  return svgString.replace(/fill="#[0-9a-fA-F]{3,6}"/g, 'fill="currentColor"');
}
// CSS: .logo { color: #1a1a1a; }
// @media (prefers-color-scheme: dark) { .logo { color: #f5f5f5; } }
```

---

## 7. SVG Optimization for Logos

AI-generated SVGs always require post-processing. Raw output contains redundant metadata, excessive decimal precision, and unnecessary attributes that inflate file size and complicate editing.

### SVGO Configuration

```javascript
// svgo.config.js — tuned for AI-generated logo SVGs
module.exports = {
  multipass: true,
  js2svg: { pretty: false },
  plugins: [
    { name: "removeDoctype" },
    { name: "removeXMLProcInst" },
    { name: "removeComments" },
    { name: "removeMetadata" },
    { name: "removeEditorsNSData" },
    { name: "removeViewBox", active: false },   // never remove viewBox
    { name: "removeEmptyAttrs" },
    { name: "removeEmptyContainers" },
    { name: "cleanupIds", params: { minify: true } },
    { name: "cleanupNumericValues", params: { floatPrecision: 2 } },
    { name: "convertPathData", params: { floatPrecision: 2 } },
    { name: "convertTransform" },
    { name: "convertColors", params: { shorthex: true } },
    { name: "mergePaths" },
    { name: "collapseGroups" },
    { name: "convertShapeToPath" }
  ]
};
```

Run via CLI: `npx svgo --config svgo.config.js --multipass input.svg -o output.svg`

### File Size Targets

| Logo Type | Target | Maximum | Path Count |
|-----------|--------|---------|------------|
| Simple logo mark | < 3 KB | 5 KB | 5–20 paths |
| Complex logo mark | < 8 KB | 15 KB | 20–60 paths |
| Full combination lockup | < 10 KB | 20 KB | 10–40 paths |
| Favicon | < 1 KB | 2 KB | 1–5 paths |

If a logo mark exceeds 15 KB after SVGO, the AI generated too much detail. Regenerate with a simpler prompt — add "minimal", "few shapes", "simple geometry".

### Validation Checklist

Before delivering any logo SVG:

```javascript
function validateLogoSVG(svgString) {
  const errors = [];
  if (!/<svg[^>]+viewBox/.test(svgString))
    errors.push("Missing viewBox — required for responsive scaling");
  if (/data:image\//.test(svgString))
    errors.push("Embedded raster data — not truly vector");
  if (/<script/.test(svgString))
    errors.push("Script element — security risk, strip before delivery");
  if (/href="https?:\/\//.test(svgString))
    errors.push("External reference — breaks offline use");

  const pathCount = (svgString.match(/<path/g) || []).length;
  if (pathCount > 60)
    errors.push(`Too many paths (${pathCount}) — simplify or regenerate`);

  const sizeKB = Buffer.byteLength(svgString, "utf8") / 1024;
  if (sizeKB > 15)
    errors.push(`File too large (${sizeKB.toFixed(1)} KB) — target < 10 KB`);

  return { valid: errors.length === 0, errors, pathCount, sizeKB };
}
```

For deeper SVG optimization techniques — path simplification, sprite sheets, animation — see @tank/vector-graphics-gen.

---

## 8. Logo Iteration Strategy

When the first generation misses the mark, diagnose the specific failure before rewriting the prompt. Changing multiple variables simultaneously makes it impossible to identify what improved the result.

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Wrong visual style (too illustrative, too flat) | Sub-style mismatch | Change model or add style words: "geometric", "flat", "editorial" |
| Colors are wrong | `colors` parameter not set or incorrect | Convert hex to RGB and pass explicit `colors` array |
| Too complex, too many paths | Prompt too vague | Add "minimal", "simple", "few shapes", "clean geometry" |
| Gradients appearing | No constraint | Add "no gradients, solid colors only" |
| Text appearing in symbol | No constraint | Add "no text" explicitly |
| Symbol not recognizable | Subject too abstract | Use a concrete noun: "padlock" not "security"; "mountain" not "ambition" |
| Full lockup looks like clip art | Prompt too generic | Add brand name, industry, and specific style words |
| Icon fails at small sizes | Too much detail | Regenerate with "ultra minimal", "bold shapes", "no fine detail" |
| Combination mark feels unbalanced | Symbol and wordmark generated separately | Generate together in one prompt with explicit layout instruction |

**Iteration order:** Fix the visual language first (style words, model choice). Then fix the subject. Then adjust colors. Then add negative constraints. One change per iteration.

**When to switch models:**

- Needs highest quality SVG paths → QuiverAI Arrow 1
- Needs specific illustration style (engraving, bold stroke) → Recraft V3 + vectorize
- Needs production-quality fal.ai output → Recraft V4 Pro

---

## 9. Negative Space Techniques

Negative space uses the background or empty area between shapes to create a secondary meaning. When executed well, it rewards attention — viewers feel a moment of discovery when they "see" the hidden element. That discovery moment makes the logo memorable.

**Classic examples:**

- **FedEx** — The gap between the capital E and lowercase x forms a forward-pointing arrow. The arrow communicates speed and precision without adding any element to the mark.
- **Amazon** — The curved arrow beneath the wordmark runs from the letter A to the letter Z, communicating "everything from A to Z" and forming a smile simultaneously.
- **NBC** — The peacock's colorful feathers create the bird shape; the negative space between feathers defines the form.
- **WWF** — The panda is formed entirely by black shapes on white; the white negative space creates the face and body.

**Construction method:**

1. Identify two shapes that share a boundary or overlap.
2. Let that boundary serve both shapes simultaneously — one shape's edge is the other shape's form.
3. Ensure both readings are clear without prompting. If you have to explain it, it is not working.
4. Test: show the logo to someone unfamiliar with it. Can they find the hidden element within 30 seconds?

**Prompting for negative space in AI generation:**

AI models rarely produce intentional negative space without explicit direction. Describe the hidden element directly:

```
abstract letter E and X forming an arrow in the negative space between them, geometric, flat, two colors, vector logo mark, no gradients
```

Expect to iterate. Negative space is one of the hardest logo techniques to generate reliably with AI — it often requires manual refinement in a vector editor after generation.

---

## 10. Peters' Longevity Principle

Allan Peters' *Logos That Last* identifies the relationship between simplicity and longevity as the central insight of logo design. Logos that endure share one characteristic: they communicate a single idea with the minimum number of elements required.

The practical test: remove one element from the logo. If the logo still communicates its core idea, that element was unnecessary. Keep removing until removal would break the meaning. What remains is the logo.

This principle applies directly to AI generation. The temptation is to add — more detail, more color, more complexity. Resist it. Generate simple, then evaluate whether anything is missing. Adding is easier than removing.

**Longevity checklist before finalizing:**

- Does the logo work in a single flat color?
- Does it work at 16×16px?
- Does it avoid any visual trend that will date it within 5 years?
- Can someone sketch it from memory after seeing it once?
- Does it communicate one idea, not several?

If any answer is no, the logo is not finished.
