# Harbor and Pine Design Bible

Version: 1.2.0
Status: approved
Owner: Creative lead
Tools: GPT Image 2.5 Sunburst for finals, GPT Image 2.5 Flare for drafts, Midjourney for mood tests
Last updated: 2026-10-21

This is a fictional brand used as a worked example for the design-bible skill.

## 1. Thematic statement

Field photographs of working outdoor gear, taken in the hour after the work is done. The images show evidence of use: scuffs on a strap, dust on a boot, a rolled map. They never show a showroom. Each image should make the viewer want to be outside, not want to buy a product.

## 2. Purpose and use

| Channel | Size | Audience | Notes |
|---------|------|----------|-------|
| Product page hero | 1536x1024 | Shoppers on desktop | Subject in lower two-thirds |
| Social square | 1024x1024 | Followers on mobile | One signal element only |
| Story | 1024x1536 | Followers on mobile | Keep top band clear for overlay |

Never used in: legal documents, safety instructions, or any image of a real customer.

## 3. Palette

| Name | Hex | Role | Share of frame | Never used for |
|------|-----|------|----------------|----------------|
| Dune Sand | #E8DCC4 | Ground | 55% | Garments that must stand out |
| Spruce | #3E5A4B | Support | 30% | Backgrounds |
| Ember | #D9642B | Signal | Under 8% | Backgrounds and large surfaces |
| Harbor Slate | #2F3A40 | Ink | Varies | Pure black surfaces |

Saturation band: product shots 20 to 35 percent mean; backgrounds under 25 percent mean, measured over the whole frame.
Maximum hue families per image: three.
Shadow color: cool blue-grey from Harbor Slate, never pure black.

## 4. Light

- Direction: key light from camera-left at 45 degrees, slightly above eye level.
- Quality: soft, from a large window-style source.
- Temperature: neutral to slightly cool daylight, around 5600K to 6500K.
- Shadow color: cool blue-grey, never black.
- Fill ratio: 3 to 1 key to fill.
- Rim light: allowed on hero subjects only, never on products.

## 5. Lens, camera, and framing

- Focal feel: 50mm, close to human vision, no distortion.
- Depth of field: f/4 to f/5.6, background soft but readable.
- Camera height: eye level for people; slightly above for products on a table.
- Subject share of frame: 60 to 70 percent of frame height.
- Headroom and placement: subject in the lower two-thirds; upper third kept clear.
- Crop rule: never cut the product's defining edge, such as the buckle or the spout.

## 6. Rendering and medium

Medium: photograph, 35mm film look.
Specify: light natural grain, true-to-life color, no heavy retouching.
Forbidden: HDR halos, skin smoothing, stylized color grades, lens flare.
Mixing mediums: forbidden.

## 7. Materials and wear

- Default finish: matte or satin. No gloss highlights on metal or ceramic.
- Wear scale default: level 2 (working use) for gear, level 1 for props.
- Named materials: waxed canvas, brushed aluminum, oiled white oak, stoneware.

## 8. Subjects

### People

- Age range: 25 to 60.
- Skin tone range: the full range the brand serves, shown without color correction.
- Wardrobe palette: Spruce and Dune Sand, with one Ember item at most.
- Expressions and gaze: focused on the task, calm; gaze on the task or off-frame.
- Likeness rule: no real people's likeness in prompts; characters are designed from scratch.

### Products

- Reference geometry: R03 defines the bottle; R04 defines the bag.
- Required angles: three-quarter front for hero, top-down for catalog.
- Finish and color: brushed aluminum with Spruce strap, satin finish.
- Scale cue: a standard 330 milliliter can placed nearby for bottles.

### Environments

- Era and location type: present day, trail or coastal working locations.
- Scale references: doorway 2.1 meters; picnic table 75 centimeters high.
- Weather and time states allowed: overcast, low sun, dusk. No rain, no snow.

## 9. Typography in images

Text allowed: none in images. Set all type in the layout tool.
Maximum words per image: not applicable.
Placement zones: not applicable.
Font descriptor: not applicable.
Quoting rule: not applicable.

## 10. Line, silhouette, and proportion

Not applicable: photographic work.

## 11. Technical spec

| Item | Value |
|------|-------|
| Output sizes | Hero 1536x1024; social 1024x1024; story 1024x1536 |
| Aspect ratios | 3:2, 1:1, 2:3 |
| Transparency | Required for product cutouts; PNG only |
| Quality, draft and final | Draft medium; final high |
| File naming | harbor-pine_{subject}_{version}_{id}.png |
| Reproducibility fields | Model, parameters, anchor ID, reference IDs, version |

## 12. Composition and negative space

- Margin: 10 percent clear on each edge for banners; 8 percent for social.
- Focal zone: lower two-thirds, centered horizontally on the subject.
- Competition rule: background values stay at least two steps darker or lighter than the subject.

## 13. Level of detail

| Tier | Subjects | Detail budget |
|------|----------|---------------|
| Hero | Main product, primary person | Full texture on surfaces in focus |
| Secondary | Props, secondary people | Two props or fewer per frame |
| Background | Environment dressing | Silhouette and value only |

## 14. Do-not-do list

- No studio high-key lighting. It makes the gear look like a showroom, not a field tool.
- No neon or saturated accent colors outside Ember. The signal color must stay scarce to work.
- No pure black or pure white surfaces. They read as a studio cutout, not the brand's world.
- No gradients on products. They vary between generations and break palette consistency.
- No text inside images. Generated text is unreliable; type is set in the layout tool.
- No real people's likeness. Rights and consent cannot be verified from a prompt.
- No lens flare or HDR halos. They read as effects, not as the film look the brand uses.

## 15. Reference set

### Approved

| ID | File or URL | Source | Rights | Proves |
|----|-------------|--------|--------|--------|
| R01 | https://example.com/refs/R01-hand-strap.jpg | Team photo, March shoot | Owned | Light direction and wear level 2 |
| R02 | https://example.com/refs/R02-trail-dusk.jpg | Licensed stock | Licensed for reference use | Environment scale and cool shadows |
| R03 | https://example.com/refs/R03-bottle-table.jpg | Team product photo | Owned | Bottle geometry and palette ground |

### Rejected

| ID | File or URL | Proves not |
|----|-------------|------------|
| A01 | https://example.com/refs/A01-studio-highkey.jpg | High-key studio light is out of bounds |
| A02 | https://example.com/refs/A02-neon-night.jpg | Saturated neon is outside the signal color |

## 16. Style anchors

### GPT Image

```text
Photograph, 35mm film look, light natural grain, true-to-life color with no heavy retouching.
Key light from camera-left at 45 degrees, soft large window source, neutral to slightly cool daylight. Shadows are cool blue-grey, never black. No rim light unless the subject is the hero.
Eye-level camera, 50mm feel, subject fills the lower two-thirds of the frame, one third of the frame kept clear.
Palette: dune sand background and surfaces, spruce green for garments and props, one small ember orange accent per image, harbor slate for shadows. No pure black or white.
Worn surfaces show working wear: faint scuffs on high-contact points. No gloss highlights on metal or ceramic; satin or matte finishes only.
No studio high-key lighting, no neon, no text in the image.
```

### Midjourney

```text
--sref https://example.com/refs/R01-hand-strap.jpg --sw 100 --sv 6
Photograph of a working outdoor gear scene, dusk, quiet and practical
```

### Google Nano Banana

```text
Photograph a canvas trail bag on a wooden table at dusk, camera at eye level with a 50mm feel, the subject in the lower two-thirds of the frame. Style: 35mm film look, soft camera-left light at 45 degrees, cool blue-grey shadows, dune sand and spruce palette, one small ember accent, no text.
```

## 17. Cross-context check

- [x] Subject reads and keeps palette roles in the lightest allowed scene (overcast, R01 variant).
- [x] Subject reads and keeps palette roles in the darkest allowed scene (dusk, R02 variant).
- [x] Silhouette and key detail read at the smallest output size (story thumbnail, 180 pixels wide).
- [x] Focal zone holds in the busiest layout (product page with overlay text).
- [x] Focal zone holds in the emptiest layout (social square, no overlay).

## 18. Change log

### 1.2.0 (2026-10-21)

- Changed: shadow color from neutral grey to cool blue-grey, value unchanged.
- Reason: outdoor shots read too neutral on mobile screens.
- Test: golden set re-run, 5 of 5 pass, rubric totals 17 to 19.
- Approved by: creative lead.

### 1.0.0 (2026-09-02)

- Initial approved version.
