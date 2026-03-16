# Character Sheet Prompt Templates

Sources: fal.ai prompt guides (2026), Flux Kontext documentation, production character sheet generation research, nanoprompts.org

Covers: prompt anatomy, Character DNA blocks, turnaround view prompts, expression sheet prompts, pose sheet prompts, style-specific variants, negative constraints, iteration diagnosis, and a complete worked example.

---

## 1. Prompt Anatomy for Character Sheets

Character sheet prompts differ from general image prompts in one critical way: consistency across multiple generations matters more than any single image's quality. Every prompt in a sheet set must anchor to the same character description.

The four-part formula:

```
[Character DNA] + [View/Pose] + [Style descriptor] + [Technical constraints]
```

**Character DNA**: The fixed, verbatim description of who this character is — physical traits, clothing, distinguishing features. This block is copied unchanged into every prompt in the set.

**View/Pose**: What the character is doing and from what angle — front view, 3/4 view, expression, action pose.

**Style descriptor**: The visual treatment — anime, realistic, cartoon, pixel art. Must be consistent across all prompts in the set.

**Technical constraints**: Sheet-specific production requirements — T-pose, orthographic camera, flat lighting, neutral background, grid layout.

### Formula in Practice

| Sheet Type | Example Assembled Prompt |
|------------|--------------------------|
| Turnaround front | `[DNA], front view, T-pose, anime style, orthographic camera, flat lighting, grey background, character design sheet` |
| Expression grid | `[DNA], expression sheet, 6 expressions in 3x2 grid, bust crop, anime style, white background, same outfit` |
| Action pose | `[DNA], dynamic combat stance, sword raised, anime style, full body, white background` |
| Silhouette | `[DNA], solid black silhouette, front view, white background, no detail, shape only` |

---

## 2. The Character DNA Block

The DNA block is the single most important element in a character sheet pipeline. It is a 50-80 word description of the character's fixed visual identity. Paste it verbatim at the start of every prompt. Never paraphrase, summarize, or abbreviate it between prompts — any variation introduces drift.

### Template

```
[GENDER/AGE descriptor] [BUILD descriptor] [SPECIES/RACE if non-human], [HAIR COLOR] [HAIR STYLE] hair, [EYE COLOR] eyes, [SKIN TONE] skin, wearing [PRIMARY OUTFIT DESCRIPTION], [SECONDARY OUTFIT DETAIL], [NOTABLE ACCESSORY OR WEAPON], [ONE DISTINGUISHING PHYSICAL FEATURE]
```

Rules:
- Keep the block between 50 and 80 words.
- Describe only what is visually observable — no backstory, no personality.
- Prioritize features that distinguish this character from others: unusual hair color, a scar, a specific weapon, a unique garment.
- Avoid vague modifiers like "beautiful" or "cool" — they add no visual information.
- Write in noun-phrase form, not sentences. Commas separate features.

### Worked Example 1: Fantasy Warrior

```
Young adult human woman, athletic build, long silver hair worn in a high ponytail, violet eyes, light brown skin, wearing battered steel plate armor with a red tabard, a large two-handed greatsword strapped across her back, a jagged scar running from her left eyebrow to her cheekbone
```

Word count: 55. Distinguishing features: silver hair, violet eyes, scar, greatsword.

### Worked Example 2: Sci-Fi Pilot

```
Middle-aged human man, lean and wiry, short-cropped black hair with grey temples, amber eyes, dark brown skin, wearing a worn orange flight suit with a cracked visor helmet tucked under one arm, a holographic wristband on his left forearm, a small tattoo of a comet on his neck
```

Word count: 57. Distinguishing features: grey temples, orange flight suit, cracked visor, comet tattoo.

### Worked Example 3: Cartoon Animal

```
Small anthropomorphic red fox, large round ears, bushy tail with a white tip, bright green eyes, wearing a tiny brown leather satchel across the chest, a pair of oversized round spectacles, a green knitted scarf wrapped twice around the neck, short and round-bodied with oversized paws
```

Word count: 52. Distinguishing features: green eyes, spectacles, green scarf, oversized paws.

---

## 3. Turnaround View Prompts (for Flux Kontext)

Turnaround sheets show the same character from multiple angles on a single canvas or as a sequence of images. Use Flux Kontext for turnarounds — it accepts a reference image and generates the same character from a new angle.

Diagram Mode keywords are required for clean turnaround output. Include all of them: `T-pose, orthographic camera, flat lighting, neutral background`.

### Front View Template

```
[CHARACTER DNA], front view, T-pose, arms slightly away from body, [STYLE DESCRIPTOR], orthographic camera, flat even lighting, neutral grey background, full body, character design sheet, no shadows
```

### Side / Profile View Template

```
[CHARACTER DNA], side profile view, T-pose, facing right, [STYLE DESCRIPTOR], orthographic camera, flat even lighting, neutral grey background, full body, character design sheet, no shadows
```

### 3/4 Front View Template

```
[CHARACTER DNA], three-quarter front view, slight turn to the right, relaxed stance, [STYLE DESCRIPTOR], orthographic camera, flat even lighting, neutral grey background, full body, character design sheet, no shadows
```

### Back View Template

```
[CHARACTER DNA], back view, T-pose, facing away from camera, [STYLE DESCRIPTOR], orthographic camera, flat even lighting, neutral grey background, full body, character design sheet, no shadows
```

### Multi-View Sheet Template (Single Image)

```
[CHARACTER DNA], character turnaround sheet, front side back views arranged left to right, T-pose in all views, [STYLE DESCRIPTOR], orthographic camera, flat even lighting, neutral grey background, full body, labeled views, no shadows
```

Note: Single-image multi-view sheets are less reliable than chained single-view generations. Use the multi-view template for quick drafts; use chained Flux Kontext calls for production output.

---

## 4. Expression Sheet Prompts

Expression sheets capture the character's face across a range of emotional states. All expressions must use the same bust crop, same outfit, and same art style. The DNA block anchors the face.

### 6-Expression Grid Template

```
[CHARACTER DNA], expression sheet, six expressions arranged in a 3x2 grid, bust crop from shoulders up, expressions: neutral, happy, sad, angry, surprised, fearful, [STYLE DESCRIPTOR], white background, same outfit in all panels, labeled expressions, no body below shoulders
```

### Individual Expression Templates

Use these when generating expressions one at a time for higher quality or when the grid prompt produces inconsistent results.

**Neutral**
```
[CHARACTER DNA], neutral expression, relaxed face, slight closed-mouth, bust portrait, shoulders visible, [STYLE DESCRIPTOR], white background, front-facing
```

**Happy**
```
[CHARACTER DNA], happy expression, wide genuine smile, eyes slightly squinted with joy, bust portrait, shoulders visible, [STYLE DESCRIPTOR], white background, front-facing
```

**Sad**
```
[CHARACTER DNA], sad expression, downturned mouth, eyebrows raised and drawn together, eyes slightly wet, bust portrait, shoulders visible, [STYLE DESCRIPTOR], white background, front-facing
```

**Angry**
```
[CHARACTER DNA], angry expression, furrowed brow, clenched jaw, narrowed eyes, bust portrait, shoulders visible, [STYLE DESCRIPTOR], white background, front-facing
```

**Surprised**
```
[CHARACTER DNA], surprised expression, wide open eyes, raised eyebrows, open mouth, bust portrait, shoulders visible, [STYLE DESCRIPTOR], white background, front-facing
```

**Fearful**
```
[CHARACTER DNA], fearful expression, wide eyes, pupils dilated, mouth slightly open, eyebrows raised and pulled together, bust portrait, shoulders visible, [STYLE DESCRIPTOR], white background, front-facing
```

### Extended Expression Templates

**Disgusted**
```
[CHARACTER DNA], disgusted expression, nose wrinkled, upper lip curled, one eyebrow raised, bust portrait, shoulders visible, [STYLE DESCRIPTOR], white background, front-facing
```

**Confused**
```
[CHARACTER DNA], confused expression, one eyebrow raised higher than the other, head tilted slightly, mouth slightly open, bust portrait, shoulders visible, [STYLE DESCRIPTOR], white background, front-facing
```

**Determined**
```
[CHARACTER DNA], determined expression, set jaw, narrowed focused eyes, slight forward lean, bust portrait, shoulders visible, [STYLE DESCRIPTOR], white background, front-facing
```

**Smug**
```
[CHARACTER DNA], smug expression, one corner of mouth raised in a half-smile, one eyebrow slightly raised, eyes half-lidded, bust portrait, shoulders visible, [STYLE DESCRIPTOR], white background, front-facing
```

### Bust Crop Specification

Specify crop consistently: `bust portrait, crop from mid-chest to top of head, shoulders fully visible`. This prevents the model from generating full-body or head-only crops that break grid alignment.

---

## 5. Pose Sheet Prompts

Pose sheets show the character in functional stances used for animation, rigging, and game asset reference.

### T-Pose / A-Pose (Rigging Reference)

```
[CHARACTER DNA], T-pose, arms extended horizontally at shoulder height, legs shoulder-width apart, facing forward, [STYLE DESCRIPTOR], orthographic camera, flat even lighting, white background, full body, rigging reference pose, no shadows
```

For A-pose, replace `arms extended horizontally` with `arms angled down at 45 degrees from shoulders`.

### Idle / Personality Pose

```
[CHARACTER DNA], relaxed idle stance, weight shifted to one hip, arms in a natural resting position, [PERSONALITY ADJECTIVE: e.g. confident / nervous / casual], [STYLE DESCRIPTOR], white background, full body, no shadows
```

### Action Pose Templates

**Combat Stance**
```
[CHARACTER DNA], combat ready stance, knees slightly bent, weight forward, [WEAPON] raised and ready, [STYLE DESCRIPTOR], white background, full body, dynamic pose, no shadows
```

**Running**
```
[CHARACTER DNA], running pose, mid-stride, one foot off the ground, arms pumping, leaning forward, [STYLE DESCRIPTOR], white background, full body, dynamic motion, no shadows
```

**Casting / Magic**
```
[CHARACTER DNA], spellcasting pose, one arm extended forward with open palm, magical energy gathering at fingertips, other hand drawn back, [STYLE DESCRIPTOR], white background, full body, dynamic pose, no shadows
```

**Jumping / Airborne**
```
[CHARACTER DNA], jumping pose, both feet off the ground, arms spread for balance, expression of exertion, [STYLE DESCRIPTOR], white background, full body, dynamic pose, no shadows
```

**Crouching / Stealth**
```
[CHARACTER DNA], crouching stealth pose, low to the ground, weight on the balls of the feet, one hand touching the floor, head turned to look sideways, [STYLE DESCRIPTOR], white background, full body, no shadows
```

### Silhouette View Template

```
[CHARACTER DNA], solid black silhouette, front view, standing neutral pose, white background, no internal detail, no color, shape recognition test, full body
```

Silhouettes are used to evaluate whether the character reads as a distinct shape. A strong character silhouette is recognizable without any internal detail. Generate this after the front turnaround view.

---

## 6. Style-Specific Prompt Variants

The style descriptor slot in the formula must be consistent across every prompt in a sheet set. Swap the style block as a unit — do not mix style words from different rows.

### Style Reference Table

| Style | Key Prompt Words | Proportion Adjustment | Color Approach |
|-------|-----------------|----------------------|----------------|
| Anime / Manga | `anime style, cel shading, clean linework, large expressive eyes` | Tall and slender, large head-to-body ratio, small nose and mouth | Flat cel colors, strong outlines, limited shadow passes |
| Realistic / Semi-realistic | `semi-realistic style, detailed rendering, anatomically proportionate, volumetric lighting` | Standard human proportions, no exaggeration | Full value range, skin subsurface, fabric texture |
| Cartoon / Stylized | `cartoon style, bold outlines, exaggerated features, flat colors, playful proportions` | Large head, small body, simplified hands, rubbery limbs | Flat fills, bold outlines, limited palette |
| Pixel Art | `pixel art style, limited color palette, retro game aesthetic, clean pixels, no anti-aliasing` | Compact and blocky, simplified silhouette | Indexed palette, dithering acceptable, no gradients |
| Vector / Flat Design | `flat design, solid colors, no gradients, clean geometric shapes, SVG-ready` | Simplified and geometric, minimal detail | Solid fills only, no shadows, brand palette |
| Painterly / Concept Art | `painterly style, visible brushstrokes, rich values, concept art quality, textured` | Realistic proportions, expressive rendering | Full tonal range, color temperature variation |

### Style Descriptor Blocks (Copy-Paste)

**Anime / Manga**
```
anime style, cel shading, clean black linework, large expressive eyes, simplified nose and mouth
```

**Realistic / Semi-realistic**
```
semi-realistic style, detailed rendering, anatomically proportionate, volumetric lighting, textured surfaces
```

**Cartoon / Stylized**
```
cartoon style, bold black outlines, exaggerated proportions, flat colors, playful and expressive
```

**Pixel Art**
```
pixel art style, 32x32 base sprite scale, limited color palette, retro game aesthetic, clean pixels, no anti-aliasing
```

**Vector / Flat Design**
```
flat design, solid colors only, no gradients, clean geometric shapes, minimal detail, SVG-ready
```

**Painterly / Concept Art**
```
painterly concept art style, visible brushstrokes, rich tonal values, textured, professional game concept quality
```

---

## 7. Negative Constraints

Negative constraints prevent the model from introducing elements that break sheet consistency or production usability.

### Standard Exclusion Set

Append to every character sheet prompt:

```
no background clutter, no text, no watermarks, no multiple characters, no cropped limbs, no extra fingers, no floating elements
```

### Words to Avoid

Photorealism triggers — omit these unless using the Realistic style:
- `photorealistic`, `photo`, `photograph`, `lifelike`, `3D render`, `CGI`
- `bokeh`, `depth of field`, `lens flare`, `film grain`, `HDRI`
- `hyperdetailed`, `8K`, `cinematic`, `dramatic lighting`

Complexity triggers — avoid unless intentional:
- `complex`, `intricate`, `elaborate`, `ornate`, `highly detailed`
- `drop shadow` — use `no shadows` explicitly
- `gradient` — use `no gradients` explicitly
- `glow`, `bloom`, `luminous` — introduces raster-like effects that break flat styles

Consistency breakers — never include:
- `random`, `varied`, `different outfit`, `alternate version`
- `background scene`, `environment`, `landscape` — use `neutral background` or `white background`

### Per-Style Negative Constraints

| Style | Additional Negatives |
|-------|---------------------|
| Anime / Manga | `no realistic proportions, no photographic shading, no western cartoon style` |
| Realistic | `no cartoon exaggeration, no flat colors, no cel shading` |
| Cartoon / Stylized | `no realistic proportions, no photographic detail, no fine linework` |
| Pixel Art | `no anti-aliasing, no smooth gradients, no high resolution detail, no blurry edges` |
| Vector / Flat | `no gradients, no shadows, no textures, no photographic elements, no fine detail` |
| Painterly | `no flat colors, no cel shading, no pixel art, no vector look` |

---

## 8. Iteration Diagnosis Table

When a generated image misses the target, diagnose the specific failure before rewriting the prompt. Change one variable per iteration.

| Symptom | Likely Cause | Prompt Fix |
|---------|-------------|------------|
| Wrong art style | Style descriptor missing or contradicted | Replace style block with the correct style descriptor block from Section 6 |
| Character looks different between prompts | DNA block was paraphrased | Copy the DNA block verbatim; do not rephrase any word |
| Wrong pose or angle | View/pose description too vague | Use the exact view template from Section 3 or 5 |
| Expression is ambiguous or wrong | Expression description too brief | Use the individual expression template from Section 4 |
| Background clutter appearing | No background constraint | Add `neutral grey background` or `white background` |
| Multiple characters generated | Ambiguous subject | Add `single character, one person only` |
| Cropped limbs or partial body | No crop specification | Add `full body, no cropping` or `bust portrait, crop from mid-chest` |
| Extra fingers or malformed hands | Common model failure | Add `correct hand anatomy, five fingers` or hide hands in pose |
| Outfit changed between views | DNA block too vague on clothing | Add more specific clothing detail to the DNA block |
| Shadows breaking flat style | No shadow constraint | Add `no shadows, flat even lighting` |
| Gradients appearing in flat/vector style | No gradient constraint | Add `no gradients, solid colors only` |
| Proportions wrong for style | Style and proportion mismatch | Add proportion note from the Style Reference Table in Section 6 |
| Grid layout broken in expression sheet | Grid prompt not specific enough | Switch to individual expression prompts from Section 4 |

### When to Change the Prompt vs. When to Change the API

| Failure | Action |
|---------|--------|
| Style is wrong | Fix the prompt style descriptor first; switch model only if the model cannot produce that style |
| Character inconsistency across views | Use Flux Kontext with reference image chaining instead of text-only generation |
| Expression sheet grid is misaligned | Switch to GPT-Image-1 multi-turn conversation for expression sets |
| Pose anatomy is broken | Add a ControlNet pose template via the pipeline; do not try to fix anatomy through prompt alone |
| Output is raster when SVG is needed | Switch to Recraft V4 text-to-vector or the vector pipeline |

---

## 9. Complete Worked Example

This section shows a full prompt set for one character — the fantasy warrior from Section 2 — assembled from the DNA block through all sheet types.

### The DNA Block (Fixed for All Prompts)

```
Young adult human woman, athletic build, long silver hair worn in a high ponytail, violet eyes, light brown skin, wearing battered steel plate armor with a red tabard, a large two-handed greatsword strapped across her back, a jagged scar running from her left eyebrow to her cheekbone
```

### Style Choice

Anime / Manga style descriptor:
```
anime style, cel shading, clean black linework, large expressive eyes, simplified nose and mouth
```

### Turnaround Sheet Prompts

**Front view:**
```
Young adult human woman, athletic build, long silver hair worn in a high ponytail, violet eyes, light brown skin, wearing battered steel plate armor with a red tabard, a large two-handed greatsword strapped across her back, a jagged scar running from her left eyebrow to her cheekbone, front view, T-pose, arms slightly away from body, anime style, cel shading, clean black linework, large expressive eyes, simplified nose and mouth, orthographic camera, flat even lighting, neutral grey background, full body, character design sheet, no shadows, no text, no background clutter
```

**Side view:**
```
Young adult human woman, athletic build, long silver hair worn in a high ponytail, violet eyes, light brown skin, wearing battered steel plate armor with a red tabard, a large two-handed greatsword strapped across her back, a jagged scar running from her left eyebrow to her cheekbone, side profile view, T-pose, facing right, anime style, cel shading, clean black linework, large expressive eyes, simplified nose and mouth, orthographic camera, flat even lighting, neutral grey background, full body, character design sheet, no shadows, no text
```

**Back view:**
```
Young adult human woman, athletic build, long silver hair worn in a high ponytail, violet eyes, light brown skin, wearing battered steel plate armor with a red tabard, a large two-handed greatsword strapped across her back, a jagged scar running from her left eyebrow to her cheekbone, back view, T-pose, facing away from camera, anime style, cel shading, clean black linework, orthographic camera, flat even lighting, neutral grey background, full body, character design sheet, no shadows, no text
```

### Expression Sheet Prompts

**6-expression grid:**
```
Young adult human woman, athletic build, long silver hair worn in a high ponytail, violet eyes, light brown skin, wearing battered steel plate armor with a red tabard, a large two-handed greatsword strapped across her back, a jagged scar running from her left eyebrow to her cheekbone, expression sheet, six expressions arranged in a 3x2 grid, bust crop from shoulders up, expressions: neutral, happy, sad, angry, surprised, fearful, anime style, cel shading, clean black linework, large expressive eyes, white background, same outfit in all panels, labeled expressions, no body below shoulders, no text labels outside panels
```

**Individual: Angry (for higher quality):**
```
Young adult human woman, athletic build, long silver hair worn in a high ponytail, violet eyes, light brown skin, wearing battered steel plate armor with a red tabard, a jagged scar running from her left eyebrow to her cheekbone, angry expression, furrowed brow, clenched jaw, narrowed eyes, bust portrait, shoulders visible, anime style, cel shading, clean black linework, large expressive eyes, white background, front-facing, no text, no background clutter
```

### Pose Sheet Prompts

**Combat stance:**
```
Young adult human woman, athletic build, long silver hair worn in a high ponytail, violet eyes, light brown skin, wearing battered steel plate armor with a red tabard, a large two-handed greatsword strapped across her back, a jagged scar running from her left eyebrow to her cheekbone, combat ready stance, knees slightly bent, weight forward, greatsword raised and ready in both hands, anime style, cel shading, clean black linework, large expressive eyes, white background, full body, dynamic pose, no shadows, no text
```

**Silhouette:**
```
Young adult human woman, athletic build, long silver hair worn in a high ponytail, wearing plate armor, a large two-handed greatsword strapped across her back, solid black silhouette, front view, standing neutral pose, white background, no internal detail, no color, shape recognition test, full body
```

Note how the silhouette prompt strips the DNA block to its most shape-defining elements only — hair, armor, and weapon. Color and facial features are irrelevant for silhouette evaluation.
