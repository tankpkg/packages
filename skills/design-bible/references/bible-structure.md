# Design Bible Structure

Sources: Makko (How to Write a Game Art Bible, 2026), Wheeler (Designing Brand Identity, 5th ed.), Wathan and Schoger (Refactoring UI, 2018), animation model-sheet practice, public game art documents (0 A.D. and Thrive, as summarized by Makko)

Covers: the section-by-section anatomy of a design bible for AI image generation, what each section must decide, how to write it so a generator can enforce it, the minimum viable set per project size, and the cross-context check that proves a rule holds.

## Anatomy at a Glance

A design bible answers one question for every image the project will ever make: what must stay the same, and what is allowed to vary. Each section decides one slice of that question. The table lists the sections in the order the bible should read.

| # | Section | Decides | Generator-facing output |
|---|---------|---------|-------------------------|
| 1 | Thematic statement | The point of view behind every rule | One paragraph, traceable rules |
| 2 | Purpose and use | Where images appear and for whom | Channels, sizes, audiences |
| 3 | Palette with roles | Which colors exist and what each one is for | Named colors, hex, role, forbidden uses |
| 4 | Light | Direction, quality, temperature, shadow color | Physical light description |
| 5 | Lens, camera, framing | Focal length, depth of field, height, subject scale | Photographic or framing terms |
| 6 | Rendering and medium | Photo, render, vector, painterly, cel, pixel | Medium name plus what it forbids |
| 7 | Materials and wear | Surface vocabulary and how worn things look | Specific material nouns and wear levels |
| 8 | Subjects | Rules for people, products, environments | Per-class rules with scale references |
| 9 | Typography in images | Whether text appears, and how | Quoted copy, font descriptors, zones |
| 10 | Line, silhouette, proportion | Outline, silhouette test, proportions, projection | Yes/no answers and test sizes |
| 11 | Technical spec | Sizes, aspect ratios, transparency, format | Exact parameter values |
| 12 | Composition and negative space | Margins, focal zone, what may compete | Margin percentages and zone rules |
| 13 | Level of detail | Detail budget per asset importance | Tier names and detail rules |
| 14 | Do-not-do list | Explicit prohibitions with reasons | Short bullet list, most-read section |
| 15 | Reference set | Approved and rejected images | IDs, roles, what each proves |
| 16 | Style anchors | Portable prompt blocks per tool | Verbatim blocks, one per tool |
| 17 | Cross-context check | Whether rules hold at the extremes | Checklist with pass criteria |
| 18 | Change log | How the bible evolved | Dated entries with reasons |

The template in `assets/design-bible-template.md` follows this order. Sections 10 and 13 are optional for photographic work. Sections 15 through 17 are required for any bible that drives generation.

## Section Guide

### 1. Thematic Statement

Write one paragraph with a point of view. Avoid genre labels alone ("modern", "minimal") because they do not decide anything. Name what the images feel like, what they refuse to be, and what the viewer should conclude.

Test: a stranger shown two images should pick the on-brief one using only this paragraph.

| Weak | Strong |
|------|--------|
| Modern and clean with a warm feel | Field photographs of working outdoor gear, taken at the hour when the work is finished. The images show evidence of use, not showroom perfection. |

Every later rule should be traceable to a sentence in this paragraph. If a rule cannot be traced, either the rule is decoration or the paragraph is incomplete.

### 2. Purpose and Use

List the channels, sizes, and audiences. The bible's rules depend on where the image lands. A hero banner tolerates more negative space than a product thumbnail. A slide tolerates less detail than a print poster.

Include a "never" list of contexts: where generated imagery must not appear, such as legal documents, medical material, or real customer photos.

### 3. Palette with Roles

Every color needs a name, a hex value, a role, and a forbidden use. Colors without roles get misused, and misuse is the most common palette failure.

| Role | Typical share of image | Rule |
|------|------------------------|------|
| Ground | 50 to 60 percent | Background and large flat areas. Desaturated. |
| Support | 25 to 35 percent | Secondary surfaces, clothing, props. |
| Signal | Under 10 percent | One accent per image. Reserved for the element the viewer must act on. |
| Ink | Varies | Darkest value used for shadows and type. Tinted, not pure black. |
| Reserved | Zero in general use | Colors that identify a specific thing, such as a brand subject. Never used elsewhere. |

The 60-30-10 split is a starting ratio, not a law. Use it to sanity-check a draft palette, then adjust to the thematic statement.

Practical limits to state explicitly:

- Maximum number of hue families per image (three is a common ceiling).
- Saturation band for each image class (see `visual-system-rules.md`).
- Pure black and pure white are forbidden for surfaces unless the bible allows them.

Record hex values for QA. Generators do not guarantee an exact hex match, so name the color in prompts and use the hex to check outputs.

### 4. Light

State four properties and one optional property:

| Property | Write it as | Example |
|----------|-------------|---------|
| Direction | Compass or clock position, height | Key light from camera-left, 45 degrees, slightly above eye level |
| Quality | Hard or soft, with source type | Soft, large window source |
| Temperature | Kelvin or a named source | Overcast daylight, neutral to slightly cool |
| Shadow color | Named hue family | Cool blue-grey, never black |
| Rim light (optional) | Allowed subjects or forbidden | Allowed on hero subjects only |

Shadow color matters more than most teams expect. Shadows pick up the ambient color of the sky and surroundings, so a bible that only specifies the key light still produces drift in the shadows. See `visual-system-rules.md`.

### 5. Lens, Camera, and Framing

Use photographic terms the tools respond to. Pair each term with its effect so a reader can apply it.

| Term | Effect | Use for |
|------|--------|---------|
| 24mm wide | Exaggerated space, environment in frame | Interiors, landscapes |
| 35mm environmental | Subject in context, natural perspective | Editorial, lifestyle |
| 50mm natural | Close to human vision | Documentary, product in use |
| 85mm portrait | Compressed background, flattering faces | Portraits, hero people shots |
| Shallow depth of field, f/1.8 | Background separation | Subject focus |
| Deep depth of field, f/8 | Everything sharp | Product grids, technical scenes |

Camera height (eye level, low angle, high angle, aerial) changes the emotional read more than most adjectives. Name it.

Framing defaults belong here too: how much of the frame the subject fills, headroom, thirds versus center placement, and cropping rules (for example, never crop a product's defining edge).

### 6. Rendering and Medium

Name the medium first. Each medium implies a set of decisions and forbids others.

| Medium | Specify | Forbid |
|--------|---------|--------|
| Photograph | Film or sensor feel, grain level, color science | Heavy retouching, HDR halos, stylized skin |
| 3D render | Shader family, global lighting style, surface roughness range | Mixed shading models in one set |
| Flat vector | Stroke width, corner radius, fill count | Gradients, drop shadows |
| Painterly | Brush texture visibility, edge softness | Photographic detail on faces |
| Cel shading | Number of tone bands, outline rule | Smooth gradients |
| Pixel art | Grid size, palette cap | Anti-aliasing, sub-pixel detail |

Mixing mediums (photo plus illustration, for example) is forbidden unless the bible names the mix and gives a rule for each part.

### 7. Materials and Wear

Generic material words ("suit", "mug", "fabric") let the model choose. Name the material and the finish.

| Weak | Strong |
|------|--------|
| A nice jacket | Navy wool twill jacket, matte finish, visible stitching |
| A ceramic mug | Matte glazed stoneware mug, no gloss highlights |

Define a wear scale the team can apply to any surface:

| Level | Meaning | Example |
|-------|---------|---------|
| 0 | New, unmarked | Factory finish |
| 1 | Light use | Faint scuffs at edges |
| 2 | Working use | Visible wear on high-contact points |
| 3 | Weathered | Fading, patina, grime in seams |

State which level is the default for each subject class.

### 8. Subjects

Give each subject class its own rules. A bible that treats people, products, and environments the same will fail on at least one.

| Class | Rules to write |
|-------|----------------|
| People | Age range, skin tone range (inclusive by default), wardrobe palette, expression range, gaze direction, pose language |
| Products | Reference photo that defines geometry, required angles, allowed finish, scale cues |
| Environments | Era, location type, scale references (door height, shelf depth), weather states |
| Animals or props | Species or prop family, scale relative to people, behavior rules |

For people: never imitate a real person's likeness unless the project holds the rights. Ban named celebrities and real customers' faces in prompts. For products: a generator invents geometry unless it sees the real object, so supply a reference image and use the identity-preservation pattern in `tool-translation.md`.

### 9. Typography in Images

Decide whether text appears at all. Generated text is the most failure-prone element. If text is allowed, specify:

- Permitted text types (headline, label, none).
- Maximum words per image.
- Placement zones.
- Font descriptor (style, weight, era), not a font file name unless the tool supports it.
- Quoting rule: exact copy in quotes, spelling checked after generation.

When exact typography matters, generate the image without text and set the type in a design tool. Tools do not guarantee a specific typeface.

### 10. Line, Silhouette, and Proportion (Illustrative Work)

Skip this section for photographic work. For illustrated or game-like assets, answer these before any asset is made:

- Outline present? Yes or no.
- Outline weight: constant or variable.
- Outline color: black, a darkened local hue, or one shared warm or cool brown.
- Outline ground break: wraps the full silhouette, or breaks where the object meets the ground.

Four answers decide most of what people mean when they say two sprites do not match. Then specify the silhouette test: render the subject as a solid black shape at a stated size and check that it reads. Give the test size and the proportion ratio (for example, head to body).

Name the projection: straight side-on, three-quarter, isometric at a stated angle, or top-down with a tilt.

### 11. Technical Spec

Record exact values the generator and the pipeline both need:

| Item | Example value |
|------|---------------|
| Output sizes per channel | Hero 1536x1024, square 1024x1024, story 1024x1536 |
| Aspect ratios | 3:2, 1:1, 4:5, 9:16 |
| Transparency | Required for product cutouts; PNG or WebP only |
| Quality setting for drafts and finals | Draft medium, final high for small text |
| File naming | `{project}_{subject}_{version}_{seed}.png` |
| Reproducibility fields | Model name, parameters, style code or seed |

### 12. Composition and Negative Space

State the margins (for example, 10 percent clear on all sides for banners), the focal zone (where the subject sits), and what may compete with it. Value contrast, not hue, usually decides what competes. Write that rule explicitly: "background values stay at least two steps darker or lighter than the subject."

### 13. Level of Detail

If the pipeline has asset tiers, define them. Hero subjects get the most detail; background dressing gets the least. For each tier, state the detail budget in words: how many distinct props, how many textures, how fine the edges. Without tiers, the team will spend effort on background details nobody sees.

### 14. Do-Not-Do List

Keep this short, explicit, and reasoned. Each item says what is forbidden and why, in one line. It is usually the most-read section of the bible, and it prevents more drift than any other.

Good items:

- No pure black or pure white surfaces. The result reads as a studio cutout, not the brand's world.
- No gradients on products. Gradients vary between generations and break palette consistency.
- No text in images unless the Typography section allows it. Generated text is unreliable.
- No real people's likeness. Rights and consent cannot be verified from a prompt.

Aim for 6 to 12 items. Fewer than three usually means the team has not thought about failure modes.

### 15. Reference Set

Two lists with IDs:

- Approved references (R01, R02, ...): each with the file or URL, the rights status, and what it proves. "R03 proves the light direction and shadow color."
- Anti-references (A01, A02, ...): each with what it proves not to be. "A02 proves that high-key studio light is out of bounds."

Approved references become the anchor for image-reference workflows. Anti-references become do-not-do items.

### 16. Style Anchors

A style anchor is the portable block of text (or the reference attachment) that every prompt for a tool shares. The bible defines one anchor per tool in use. Details and per-tool rules live in `tool-translation.md`. The anchor is copied verbatim into every prompt, so it lives in the bible in a code block.

### 17. Cross-Context Check

A rule holds only if the asset survives the extremes the bible allows. Define three pairs and a pass criterion for each:

| Pair | Test | Pass |
|------|------|------|
| Lightest and darkest allowed scene | Place the subject in both | Subject reads and keeps palette roles in both |
| Smallest and largest output size | Render or view at both | Silhouette and key detail still read at the small size |
| Busiest and simplest layout | Put the subject in a crowded frame and an empty one | Focal zone holds in both |

The makko.ai art bible guide describes this as the check that belongs in the bible, because it is the check an asset can fail while looking good on its own. Run it on at least one generated asset before the bible is marked approved.

## Minimum Viable Bible by Project Size

| Project | Sections required | Notes |
|---------|-------------------|-------|
| One-off set (under 10 images) | 1, 3, 4, 8, 14 | Keep it to a page. Skip the reference set only if the user brings one reference image. |
| Ongoing campaign or product | 1 to 9, 11, 12, 14 to 17 | Full template minus illustrative sections. |
| Illustrated or game pipeline | All 18 | Include silhouette, proportion, and level of detail. |
| Multi-tool team | All 18, with one anchor per tool | Anchor drift across tools is the main hidden cost. |

## Common Structural Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Adjectives instead of properties | Two generations of "warm, moody" look different | Replace with light direction, temperature, and shadow color |
| Palette with no roles | Accent color appears as background | Add role and forbidden use to each color |
| Shadow color unspecified | Shadows drift from cool to black | Add shadow color to Light |
| Reference set missing | Each prompt reinvents the look | Add three to six approved references |
| Do-not-do list too long | Nobody reads it | Cut to the items that caused real failures |
| Anchor paraphrased per prompt | Palette creeps over weeks | Lock the anchor verbatim in section 16 |
| No cross-context check | Asset passes alone, fails in a scene | Run section 17 on one generated asset |

## Worked Fragment

A fictional outdoor gear brand, "Harbor and Pine", needs a palette and light section. The weak and strong versions show the difference:

Weak:

```text
Earthy palette with warm light. Greens and browns. Natural and calm.
```

Strong:

```text
Ground: Dune Sand #E8DCC4, used on backgrounds and large surfaces, 55 percent of frame.
Support: Spruce #3E5A4B, used on garments and props, 30 percent.
Signal: Ember #D9642B, one element per image only, never on backgrounds. Under 8 percent.
Ink: Harbor Slate #2F3A40, shadows and type. Never pure black.

Light: key from camera-left, 45 degrees, soft large source, neutral-to-cool daylight.
Shadows: cool blue-grey, never black. Rim light on hero subjects only.
```

The strong version gives a generator and a reviewer the same checkable facts.

## Reference Cross-Links

- Discovery, reference curation, and attribute extraction: `discovery-and-references.md`
- How to write enforceable rules for color, light, lens, and materials: `visual-system-rules.md`
- Turning sections into style anchors and per-tool prompts: `tool-translation.md`
- Drift diagnosis, the review rubric, and correction strategy: `consistency-and-drift.md`
- Storage, versioning, AGENTS.md integration, and handoff: `delivery-and-maintenance.md`
