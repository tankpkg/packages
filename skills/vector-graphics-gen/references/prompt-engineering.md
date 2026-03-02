# Prompt Engineering for Vector Graphics

Sources: fal.ai prompt guides, Recraft documentation, production prompt testing (2025-2026)

Covers: prompt anatomy, style selection, color control, icon/logo patterns, illustration patterns, seamless patterns, negative patterns, templates, iteration strategy.

## 1. Prompt Structure Formula

Effective vector prompts follow a four-part anatomy. Each part is optional but order matters — specificity increases left to right.

The prompt quality principles in this file apply across all models — QuiverAI Arrow, Recraft V4, and Recraft V3. Model choice affects output format and available sub-styles, not the fundamentals of prompt construction. Write strong prompts first; select the model second.

```
[Subject] + [Style descriptor] + [Composition] + [Constraints]
```

**Subject**: What the image depicts. Be concrete. "coffee cup" beats "beverage container". Name the object, action, or concept directly.

**Style descriptor**: The visual treatment. For vector work, this maps to Recraft sub-styles. Include 1-2 style words that reinforce the API parameter you are passing.

**Composition**: Spatial arrangement, orientation, framing. "centered on white background", "full bleed", "isometric view", "top-down perspective".

**Constraints**: What to exclude or limit. "solid colors only", "no gradients", "two colors maximum", "no text", "no shadows".

### Formula in Practice

| Goal | Prompt |
|------|--------|
| App icon | "shield with checkmark, flat design, centered on white background, solid colors only" |
| Hero illustration | "team of people collaborating around a table, editorial illustration, balanced composition, limited palette" |
| Logo mark | "abstract mountain peak, geometric, symmetrical, single color, minimal" |
| Pattern | "small repeating leaves, flat botanical, seamless tile, two colors" |
| Badge | "star burst badge with ribbon, bold stroke, centered, no gradients" |

### Subject Specificity Rules

- Name the primary object first: "magnifying glass" not "search concept"
- Add one modifier for shape: "rounded magnifying glass", "angular shield"
- Add one modifier for state: "open envelope", "locked padlock", "spinning gear"
- Avoid metaphors: "security" is vague; "padlock with shield" is actionable

---

## 2. Style Control

Recraft V3 exposes 22 sub-styles under `vector_illustration`. Pass the sub-style as the `style_name` parameter alongside `style: "vector_illustration"`. Use V3 sub-styles via the two-step pipeline (V3 raster → vectorize) when you need specific illustration styles. For general vector generation, prefer Recraft V4 or QuiverAI Arrow.

### Sub-Style Visual Reference

| Sub-style | Visual Character | Best For |
|-----------|-----------------|----------|
| `bold_stroke` | Thick outlines, high contrast, comic-adjacent | App icons, badges, stickers |
| `line_art` | Clean single-weight lines, minimal fill | Technical diagrams, icons, logos |
| `line_circuit` | Circuit board aesthetic, geometric lines | Tech products, developer tools |
| `thin` | Hairline strokes, delicate, editorial | Premium brands, editorial spots |
| `roundish_flat` | Soft shapes, friendly, rounded corners | Consumer apps, onboarding illustrations |
| `emotional_flat` | Expressive flat characters, warm palette | Marketing illustrations, hero images |
| `editorial` | Sophisticated, magazine-quality | Long-form content, article headers |
| `infographical` | Data-friendly, clear hierarchy | Charts, explainers, process diagrams |
| `sharp_contrast` | High contrast, punchy, graphic | Posters, social media, announcements |
| `vivid_shapes` | Overlapping geometric forms, colorful | Abstract backgrounds, brand visuals |
| `segmented_colors` | Flat color blocks, stained-glass feel | Portraits, character illustrations |
| `cutout` | Paper-cut aesthetic, layered shapes | Playful brands, children's content |
| `colored_stencil` | Spray-paint texture, urban | Music, streetwear, event graphics |
| `contour_pop_art` | Pop art outlines, retro | Retro campaigns, nostalgia brands |
| `naivector` | Naive/folk art style, hand-drawn feel | Artisan brands, craft products |
| `marker_outline` | Marker pen aesthetic, sketchy | Startup pitch decks, whiteboards |
| `mosaic` | Tessellated shapes, geometric fill | Abstract art, decorative backgrounds |
| `engraving` | Cross-hatch, etching aesthetic | Luxury brands, certificates |
| `linocut` | Woodblock print texture | Artisan, organic, handmade brands |
| `chemistry` | Scientific diagram aesthetic | EdTech, science products |
| `cosmics` | Space, cosmic, nebula-inspired | Gaming, sci-fi, futuristic brands |
| `depressive` | Muted, melancholic, desaturated | Mental health, introspective content |

### Style Selection Decision Tree

| Signal | Recommended Sub-styles |
|--------|----------------------|
| Icon, scales to 16px | `line_art`, `bold_stroke` |
| Icon with personality | `roundish_flat`, `bold_stroke` |
| Playful brand | `roundish_flat`, `emotional_flat`, `cutout` |
| Professional brand | `editorial`, `thin`, `line_art` |
| Technical product | `line_circuit`, `infographical`, `chemistry` |
| Decorative / abstract | `vivid_shapes`, `mosaic`, `cosmics` |
| Functional / UI | `line_art`, `infographical`, `bold_stroke` |

### Reinforcing Style in the Prompt

Mismatched prompts and sub-styles produce inconsistent results. Reinforce the sub-style with matching text:

| Sub-style | Reinforce with prompt words |
|-----------|----------------------------|
| `bold_stroke` | "bold outlines", "high contrast", "graphic" |
| `line_art` | "line drawing", "outline only", "minimal" |
| `roundish_flat` | "flat design", "soft shapes", "friendly" |
| `editorial` | "editorial illustration", "sophisticated" |
| `infographical` | "diagram", "clear hierarchy", "labeled" |
| `engraving` | "engraved", "etched", "detailed linework" |

---

## 3. Color Control

The `colors` parameter accepts an array of `{r, g, b}` objects. The model treats these as a palette constraint — it will not introduce colors outside this set.

```json
{"colors": [{"r": 59, "g": 130, "b": 246}, {"r": 255, "g": 255, "b": 255}]}
```

Convert brand hex values before passing: `#3B82F6` → `{r: 59, g: 130, b: 246}`. Parse each hex pair as a base-16 integer.

### Palette Strategies

| Strategy | Colors Array | Use Case |
|----------|-------------|----------|
| Monochrome | 1 color + white | Icons, logos, stamps |
| Two-tone | 2 brand colors | Badges, simple illustrations |
| Brand palette | 3-5 brand colors | Marketing illustrations |
| Neutral + accent | 2 neutrals + 1 accent | UI illustrations |
| Full palette | 5-8 colors | Hero illustrations, complex scenes |

### Color Count Guidelines

- Icons: 1-2 colors. More colors reduce scalability and recognizability.
- Logos: 1-3 colors. Match brand guidelines exactly.
- Illustrations: 3-6 colors. Limit prevents visual noise.
- Patterns: 2-4 colors. Seamless tiles need restraint.

### Brand Color Matching

Pass exact hex values converted to RGB, and name the colors in the prompt. The model responds better when text and parameter agree:

```
Prompt: "abstract wave logo mark, geometric, using only navy blue and white"
Colors: [{r: 15, g: 23, b: 42}, {r: 255, g: 255, b: 255}]
```

The `background_color` parameter (Recraft V4) sets the canvas background separately. Use `{r: 255, g: 255, b: 255}` for white or `{r: 0, g: 0, b: 0}` for black.

---

## 4. Icon and Logo Generation

### Icon Prompt Pattern

```
[Shape/object], [style adjective], centered, [color constraint], no text, no gradients
```

Working examples:
- "bell notification icon, flat design, centered, single color, no gradients, no text"
- "shopping cart with plus sign, bold stroke, centered on white, two colors maximum"
- "circular progress indicator, thin line art, centered, monochrome"
- "lightning bolt inside circle, sharp contrast, centered, black and white"

### Logo Mark Pattern

```
[Abstract concept or object], [geometric/organic], [symmetry], [color count], no text, vector mark
```

Working examples:
- "abstract letter A formed from two triangles, geometric, symmetrical, single color, vector logo mark"
- "stylized fox head, minimal geometric, facing forward, two colors, no text"
- "infinity symbol made of ribbon, smooth curves, monochrome, logo mark"
- "mountain peak with sun rays, geometric, centered, navy and gold, no text"

### Favicon, Badge, and App Icon Patterns

Favicons render at 16x16 — use extreme simplicity:
- "bold letter S, rounded, single color, ultra minimal, no serifs"
- "checkmark inside square, bold stroke, green and white"

Badges and stamps:
- "circular badge with star burst edge, bold stroke, two colors, retro"
- "hexagonal badge with ribbon banner, flat design, bold, three colors"

App icons display on colored backgrounds. Use `background_color` to set the canvas, then design the foreground element in white or a contrasting color:
- `background_color: {r: 99, g: 102, b: 241}` + prompt: "white rocket ship, minimal, centered, no gradients"

---

## 5. Illustration Generation

### Hero Illustration Pattern

```
[Scene description], [style], [mood/tone], balanced composition, [color palette], no text
```

Working examples:
- "two people shaking hands across a desk, editorial illustration, professional and warm, balanced composition, blue and cream palette"
- "developer at laptop with floating code symbols, emotional flat, focused and energetic, dark background with bright accents"
- "small plant growing from a coin, roundish flat, optimistic, centered, green and gold on white"
- "team of diverse people around a circular table, editorial, collaborative, top-down view, muted warm palette"

### Spot Illustration Pattern

Spot illustrations are small, self-contained visuals used inline with text. They read at 200-400px.

```
[Single concept], [style], simple, [1-3 colors], no background, isolated
```

Working examples:
- "open book with light bulb above it, line art, simple, two colors, no background"
- "envelope with paper airplane flying out, roundish flat, playful, blue and white"
- "shield with lock, bold stroke, simple, monochrome"

### Empty State and Error Patterns

Empty states — keep light and encouraging:
- "empty inbox tray with small bird perched on edge, roundish flat, friendly, soft blue and white"
- "magnifying glass finding nothing, emotional flat, curious not sad, light gray and blue"

Error states:
- "broken chain link, bold stroke, clear, red and gray, centered"
- "disconnected plug with sad face, roundish flat, sympathetic, muted red and white"

---

## 6. Pattern and Texture Generation

### Seamless Pattern Formula

```
[Motif description], seamless pattern, [density], [style], [color count], tile-ready
```

Working examples:
- "small geometric diamonds, seamless pattern, medium density, flat design, two colors, tile-ready"
- "repeating leaf and branch motifs, seamless botanical pattern, scattered, line art, green and cream"
- "interlocking hexagons, seamless geometric pattern, tight grid, single color on white"
- "repeating circuit board traces, seamless tech pattern, medium density, line art, teal on dark"

### Background Texture Formula

```
[Texture type], subtle, [style], [very limited colors], low contrast, background texture
```

Working examples:
- "subtle dot grid, minimal, single color, very low contrast, background texture"
- "light diagonal lines, subtle, thin, single color, background"
- "soft geometric mesh, abstract, muted, two colors, background texture"

Decorative borders:
- "ornamental corner flourishes, symmetrical, line art, single color"
- "repeating geometric border strip, bold, two colors, horizontal band"

---

## 7. Negative Patterns

Certain words and phrases consistently degrade vector output quality.

### Words to Avoid

Photorealism triggers — never include:
- "photorealistic", "photo", "realistic", "lifelike", "3D render", "CGI"
- "bokeh", "depth of field", "lens flare", "film grain"
- "hyperdetailed", "8K", "cinematic", "dramatic lighting", "HDRI"

Complexity triggers — avoid unless intentional:
- "complex", "intricate", "detailed", "elaborate", "ornate"
- "shadow", "drop shadow" — use "no shadows" explicitly
- "gradient" — use "no gradients, solid colors only"
- "glow", "bloom", "luminous" — introduces raster-like effects

### Structural Anti-Patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| "A beautiful illustration of..." | Filler words dilute signal | Start with the subject directly |
| "Create a vector of..." | Instruction language confuses model | Describe the result, not the task |
| Multiple subjects without hierarchy | Model splits attention | Name primary subject first |
| Abstract concepts without visual anchor | "Success", "growth" | Anchor to object: "upward arrow", "sprouting plant" |
| Contradictory style words | "photorealistic flat design" | Pick one visual language |
| Overly long prompts (100+ words) | Model loses focus | Keep under 50 words for icons, 80 for illustrations |

### Standard Negative Constraint Set

Append to any vector prompt: `no gradients, no shadows, no textures, solid colors only, no text`

---

## 8. Prompt Templates

Copy-paste templates for common use cases. Replace bracketed placeholders.

Templates below show `fal-ai/recraft/v4/text-to-vector` for native SVG output. For sub-style control, use `fal-ai/recraft/v3/text-to-image` with the two-step pipeline. For highest quality, use QuiverAI Arrow (`@quiverai/sdk`). Size defaults to `square_hd`.

### Template 1: App Icon (Flat)
```
[object name], flat design, centered on white background, solid colors only, no gradients, no shadows, no text
```
Sub-style: `bold_stroke` or `roundish_flat`

### Template 2: App Icon (Line Art)
```
[object name], minimal line art, centered, single color, thin strokes, no fill, no text
```
Sub-style: `line_art`

### Template 3: Logo Mark (True SVG)
```
[abstract shape or object], geometric, symmetrical, vector logo mark, [N] colors, no text, no gradients
```
Model: `fal-ai/recraft/v4/text-to-vector`

### Template 4: Hero Illustration
```
[scene with people], editorial illustration, [mood] tone, balanced composition, [palette description], no text
```
Sub-style: `editorial` or `emotional_flat` | Size: `landscape_16_9`

### Template 5: Spot Illustration
```
[single concept], flat design, simple, isolated on white, [1-3 colors], no background, no text
```
Sub-style: `roundish_flat` or `line_art`

### Template 6: Seamless Pattern
```
[motif], seamless repeating pattern, [sparse/medium/dense], flat design, [N] colors, tile-ready, no gradients
```
Sub-style: `vivid_shapes` or `segmented_colors`

### Template 7: Badge or Stamp
```
[shape type] badge, [style adjective], centered, bold, [N] colors, no text, decorative border
```
Sub-style: `bold_stroke` or `contour_pop_art`

### Template 8: Technical Diagram
```
[technical concept], diagram style, clean lines, flat, [2-3 colors], no shadows, no gradients
```
Sub-style: `infographical` or `line_circuit` | Size: `landscape_4_3`

### Template 9: Subtle Background
```
[pattern type], subtle background texture, low contrast, [1-2 colors], seamless, no focal point
```
Sub-style: `thin` or `mosaic` | Size: `landscape_16_9`

### Template 10: Empty State
```
[empty or absent object], friendly illustration, [encouraging emotion], soft colors, centered, simple, no text
```
Sub-style: `roundish_flat` or `emotional_flat`

### Template 11: Favicon
```
[single bold shape], ultra minimal, bold, [1-2 colors], no fine detail, no text
```
Sub-style: `bold_stroke`

### Template 12: Icon Set (Single Generation)
```
[object 1], [object 2], [object 3] icons, flat design, consistent style, monochrome, no text, icon set
```
Sub-style: `line_art` | Size: `landscape_4_3`

---

## 9. Iteration Strategy

When the first generation misses the mark, diagnose before rewriting.

### Diagnosis Table

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Wrong visual style | Sub-style mismatch | Change sub-style parameter |
| Wrong colors | Colors parameter not set | Add `colors` array |
| Too complex / too many paths | Prompt too vague | Add "minimal", "simple", "few shapes" |
| Photorealistic output | Photorealism words in prompt | Remove them, add "flat design" |
| Wrong composition | No composition constraint | Add "centered", "balanced", "full bleed" |
| Subject not recognizable | Subject too abstract | Use more concrete noun |
| Gradients appearing | No constraint | Add "no gradients, solid colors only" |
| Text appearing | No constraint | Add "no text" |

### Iteration Order

1. Fix the sub-style if the visual language is wrong
2. Fix the prompt subject if the object is unrecognizable
3. Add or adjust the `colors` parameter
4. Add negative constraints for specific failures
5. Adjust composition words

Make one change per iteration — changing multiple variables simultaneously makes it impossible to identify what improved the result.

### Sub-Style Substitution Pairs

| Original | Too complex | Too simple | Wrong mood |
|----------|------------|------------|------------|
| `bold_stroke` | → `line_art` | → `sharp_contrast` | → `roundish_flat` |
| `roundish_flat` | → `thin` | → `bold_stroke` | → `emotional_flat` |
| `editorial` | → `thin` | → `marker_outline` | → `emotional_flat` |
| `line_art` | → `thin` | → `bold_stroke` | → `line_circuit` |
| `emotional_flat` | → `roundish_flat` | → `editorial` | → `segmented_colors` |

### Prompt Refinement Examples

| Weak prompt | Problem | Strong prompt |
|-------------|---------|---------------|
| "a security icon" | Too vague | "padlock with shield overlay, flat design, centered on white, two colors, no gradients, no text" |
| "illustration of teamwork" | Abstract concept | "three people pushing a large gear together, editorial illustration, collaborative mood, blue and gray palette" |
| "modern logo" | No subject or constraints | "abstract letter M formed from two mountain peaks, geometric, symmetrical, navy blue, vector logo mark, no text" |

### When to Switch Models

| Failure | Alternative |
|---------|------------|
| Needs true SVG output | `fal-ai/recraft/v4/text-to-vector` |
| Needs text in the image | `fal-ai/ideogram/v2a` (Ideogram has no native SVG — produces raster only, good for text-heavy images that can be vectorized) |
| Needs highest quality | `fal-ai/recraft/v4/pro/text-to-vector` |
| Need speed, raster acceptable | `fal-ai/nano-banana-2` then vectorize |

For model parameters and endpoint details, see `references/text-to-vector-models.md`.
For the two-step raster-to-SVG pipeline, see `references/fal-api-reference.md`.
