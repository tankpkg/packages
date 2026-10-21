# Visual System Rules

Sources: Albers (Interaction of Color, 50th anniversary ed.), Gurney (Color and Light, 2010), Wathan and Schoger (Refactoring UI, 2018), Makko (How to Write a Game Art Bible, 2026), Google Nano Banana prompting guide (2026), OpenAI GPT Image prompting guide (2026)

Covers: how to write enforceable rules for color, light, lens and framing, rendering, materials, subjects, typography, and silhouette, with the vocabulary each tool responds to, the test that makes each rule checkable, and the vague-to-enforceable rewrites that turn taste into rules.

## The Enforceable Form

Every rule in the bible follows one pattern: property, value, location, test.

| Part | Question it answers | Example |
|------|---------------------|---------|
| Property | What is being decided? | Shadow color |
| Value | What exactly is it? | Cool blue-grey, around 6500K ambient |
| Location | Where does it apply? | All subject shots, outdoor and indoor |
| Test | How does a reviewer check it? | Shadow pixels read blue-grey on a calibrated display; no pixel near pure black |

A rule without a test drifts. Reviewers disagree about "warm" but agree on whether a shadow is blue-grey.

### Vague to Enforceable

| Vague (fails) | Enforceable (passes) |
|---------------|----------------------|
| Warm, cozy light | Key light from camera-left, 45 degrees, 3200K tungsten, fill ratio 3 to 1 |
| Earthy palette | Ground Dune Sand #E8DCC4, support Spruce #3E5A4B, signal Ember #D9642B |
| Moody lighting | Key from above and behind, hard source, shadow falls toward camera |
| Clean background | Plain ground color, no gradient, value within two steps of the ground |
| Premium feel | Matte finish, no gloss highlights, one detail per surface |
| Cinematic | 35mm lens, shallow depth of field at f/2, anamorphic flare forbidden |
| Vintage | Film grain at a stated level, faded shadows lifted 5 percent, warm highlights |
| Dramatic | Single key light, no fill, shadow covers half the subject |

The left column is what most teams write first. The right column is what makes two generations match. Words like "beautiful", "stunning", "epic", and "masterpiece" describe the reviewer's reaction, not the image, and the scoring tool in `scripts/check_bible.py` flags them.

## Color

### Build the Palette from Roles

Every color has one role (see `bible-structure.md`, section 3). Build a palette in this order:

1. Pick the ground first. It sets the frame, so it is the largest area and the most constrained.
2. Pick one or two support colors that sit within the same hue family or a neighboring one.
3. Pick the signal color last, and make it differ from the ground in hue or value.
4. Pick ink for shadows and type. Tint it toward the ground's hue. Do not use pure black.
5. Check the reserved colors. A reserved color is one the subject owns; it must never appear in backgrounds.

### Use Shade Scales Sparingly

Wathan and Schoger build interface palettes from a shade scale, typically nine steps per hue, and then use only a few of them. Apply the same discipline to image palettes: each role gets three to five shades. Name them (Dune Sand light, Dune Sand mid, Dune Sand deep) so prompts can refer to them without inventing new ones.

Neutrals should carry a tint of the primary hue. A neutral grey that is pure and cold will fight a warm palette in every image.

### Set Saturation Bands

Saturation drives how a palette reads more than hue does. State a mean saturation band for each image class, and specify how it is measured. The makko.ai example sets a crew saturation of 42 to 56 percent mean and a room ceiling of 31 percent mean, which keeps characters visually separate from their environment.

Measurement options, in order of rigor:

| Method | Use when |
|--------|----------|
| Mean HSL saturation over the whole image (image editor histogram or script) | Reviewing a finished asset |
| Sampled swatches from the focal zone and the background | Quick checks on generated images |
| Visual comparison against the approved references | Early exploration, before measurement |

Write the band into the palette section and the anchor only when the team can measure it. A band nobody can check is a suggestion.

### Respect Color Relativity

Albers showed that the same color looks different against different neighbors. A subject color that looks correct on one background looks wrong on another. A palette rule that gives colors without context is incomplete.

Write each color rule with its context: "Signal Ember appears only on a Dune Sand or Spruce ground." Then the rule holds across scenes.

### Shadow Color

Shadows are colored. Gurney describes how shadows pick up the ambient light and the color of nearby surfaces. A bible that specifies only the key light still produces drift in the shadows.

State:

- The hue family of shadows (cool, neutral, or warm).
- That shadows are never pure black.
- Whether bounce color from nearby surfaces is allowed, and which surface colors it may carry.

### Hue-Shift Rules

Some looks shift hue with value: highlights lean warm, shadows lean cool. This is a rule to state, not a default to assume. If the bible uses hue shift, give the direction and the amount ("highlights shift toward amber, shadows toward blue-grey, 5 degrees on the hue wheel at most"). Without a stated amount, reviewers will disagree on whether the shift is present.

### Color Rules Table

| Rule | Write it as | Check |
|------|-------------|-------|
| Ground dominance | Ground covers 50 to 60 percent of the frame | Visual area estimate |
| Signal scarcity | One signal element per image | Count signal-colored areas |
| No pure black or white | Ink and surface values bounded | Histogram endpoints above 0 and below 255 |
| Reserved colors | Named subject owns the hue | Reserved hue absent from backgrounds |
| Hue families | Three families maximum | Count families visually |

## Light

### The Four Properties

| Property | Options to name | Why it matters |
|----------|-----------------|----------------|
| Direction | Camera-left, camera-right, top, back, front, compass angle | Decides where shadows fall, and the most common drift |
| Quality | Hard (sharp shadow edge) or soft (gradual edge) | Changes the mood more than color does |
| Temperature | Kelvin, or a named source (tungsten, daylight, overcast, neon) | Sets the whole palette's warmth |
| Shadow color | Named hue family | Keeps shadows from drifting toward black |

Add two optional properties when relevant: fill ratio (key-to-fill, such as 2 to 1 or 4 to 1) and rim light (allowed on which subjects, or forbidden).

### Vocabulary That Tools Respond To

The Google Nano Banana guide recommends naming the lighting setup explicitly: a three-point softbox setup for product work, chiaroscuro with harsh high-contrast light for drama, golden hour backlight for long shadows. The OpenAI guide asks for materials, lighting, colors, and the visual medium. Use setup names where they exist and describe direction and quality where they do not.

| Setup name | Meaning | Typical use |
|------------|---------|-------------|
| Three-point softbox | Key, fill, and back light, all soft | Product, catalog |
| Window light | Single large soft source from one side | Lifestyle, portrait |
| Overcast daylight | Large, even, low-contrast source | Outdoor documentary |
| Golden hour backlight | Low sun behind subject, long shadows | Editorial, hero shots |
| Chiaroscuro | Single hard source, deep shadows | Drama, product mood |
| Practical lamp | Visible light source in frame | Interiors, night scenes |

### Light Rules Checklist

- Direction stated in degrees or clock position, and the same across all subject shots unless the bible names an exception.
- Quality stated as hard or soft, and the source named.
- Temperature stated in Kelvin or with a named source.
- Shadow color stated.
- Rim light allowed or forbidden, per subject class.
- Practical sources in frame allowed or forbidden.
- Time of day and weather fixed, or listed as the allowed set.

## Lens, Camera, and Framing

### Focal Length and Depth of Field

Use focal length as a feel, not a spec. The OpenAI guide says camera specifications are cues for appearance, not guarantees of physical simulation. Pair each lens term with its visual effect in the bible.

| Term | Visual effect | Assign to |
|------|---------------|-----------|
| 24mm wide | Space and environment dominate, edges stretch | Interiors, landscapes |
| 35mm | Natural environmental context | Editorial, lifestyle |
| 50mm | Close to human vision, neutral | Documentary, product in use |
| 85mm | Compressed background, flattering faces | Portraits, hero people |
| f/1.8 to f/2.8 | Shallow focus, soft background | Subject isolation |
| f/8 and above | Broad focus, most of the frame sharp | Product grids, technical scenes |

### Camera Height

Camera height changes the read more than most adjectives. Name it:

| Height | Read | Use |
|--------|------|-----|
| Eye level | Neutral, peer | Documentary, portrait |
| Low angle | Power, scale | Hero products, figures |
| High angle | Smallness, overview | Layouts, environments |
| Aerial or top-down | Map-like, graphic | Flat lays, landscapes |

### Framing Rules

State the subject's share of the frame (for example, "subject fills 60 to 70 percent of frame height for portraits"), the headroom rule, the placement (thirds, center, or lower-two-thirds), and the crop rule (for example, "never crop the product's defining edge"). Framing rules are among the easiest to check: a reviewer can count the frame fractions in seconds.

## Rendering and Medium

### Name the Medium First

The medium decides more visual properties than any other choice. State it first in the anchor, in plain words: "35mm film photograph", "flat vector illustration with 2-pixel strokes", "cel-shaded 3D render with two tone bands".

### What Each Medium Implies

| Medium | Specify | Forbid |
|--------|---------|--------|
| Photograph | Film or sensor feel, grain level, color science, retouch level | HDR halos, heavy skin smoothing, stylized color |
| 3D render | Shader family, lighting model, roughness range | Mixed shading models, photoreal textures on stylized forms |
| Flat vector | Stroke width, corner radius, fill count | Gradients, drop shadows, texture |
| Painterly | Brush texture visibility, edge softness | Photographic detail on faces |
| Cel shading | Number of tone bands, outline rule | Smooth gradients inside bands |
| Pixel art | Grid size, palette cap | Anti-aliasing, sub-pixel placement |

### Mixed Mediums

Forbid mixing unless the bible names the mix and gives a rule for each part. A common accepted mix is photographic product plus flat vector annotations; state which parts of the frame use which medium and forbid crossover.

### Grain and Texture

Grain is a medium property with a level. Define three levels (none, fine, visible) and the default for each medium. Without a grain level, generations drift between clean and noisy, and reviewers disagree on whether the difference matters.

## Materials and Surfaces

Name the material and the finish:

| Weak | Strong |
|------|--------|
| Wool jacket | Navy wool twill jacket, matte finish, visible stitching |
| Metal bottle | Brushed aluminum bottle, satin finish, fingerprint-free |
| Wood table | Oiled white oak table, grain visible, no gloss |

Finish words (matte, satin, gloss) change how light reacts. State the finish whenever the light setup matters, which is almost always.

Wear is a scale, not an adjective. The wear levels from `bible-structure.md` (0 new, 1 light use, 2 working use, 3 weathered) let a reviewer check every surface the same way.

Saturation on worn surfaces: some looks deliberately increase saturation on worn parts (the makko.ai example requires worn surfaces to carry more saturation than new ones). If the bible uses this, state the direction and the amount.

## Subjects

### People

| Element | Write |
|---------|-------|
| Age range | A numeric range or a stated default |
| Skin tone range | Inclusive range the project will show, stated plainly |
| Wardrobe palette | Colors drawn from the palette roles |
| Expression range | Two or three permitted expressions |
| Gaze | Camera, off-frame, or on the task |
| Pose language | Relaxed, working, pausing; no posed stock gestures if the look is documentary |

Rights and likeness: do not use real people's likeness, named celebrities, or real customers' faces in subject prompts. If the project needs a recurring person, the character should be designed from scratch and documented in a character sheet (see the character-creator skill).

### Products

A generator invents product geometry unless it sees the real object. For product subjects, the bible must say:

- The reference photo that defines the geometry (reference ID from section 15).
- Required angles and the default angle.
- Finish and color, named from the palette roles.
- Scale cue (for example, "next to a standard 330ml can").

For edits that keep a product recognizable, use the identity-preservation pattern in `tool-translation.md`.

### Environments

Scale references keep rooms and objects consistent. Write the references the bible uses ("doorway height 2.1 meters", "shelf depth 30 centimeters"). State the era and location type, and the weather states allowed. An environment rule with no scale reference drifts within a few images: a table becomes a bench, a window becomes a door.

## Typography in Images

Decide whether text appears at all. Generated text is the most failure-prone element. If text is allowed, specify:

| Element | Rule |
|---------|------|
| Allowed text types | Headline, label, none |
| Maximum words per image | A number, such as 6 |
| Placement | Named zones, such as top-left, lower third |
| Font descriptor | Style, weight, era (for example, "bold condensed sans-serif") |
| Quoting | Exact copy in quotes |
| Verification | Spelling and legibility checked after each generation |

Practice from the guides:

- The Google guide recommends quoting the words and naming the font style. It also recommends a text-first step: converse for the text concept, then ask for the image with that text.
- The OpenAI guide recommends quoting exact text, stating its position and typography, spelling unusual words letter by letter, and asking for no extra text. Use a higher quality setting for small or dense text.

When exact typography matters, generate without text and set the type in a design tool. No image tool guarantees a specific typeface.

## Line, Silhouette, and Proportion

Use this section for illustrated or game assets only.

### Four Outline Questions

Answer once and apply to every asset:

1. Outline present? Yes or no.
2. Weight: constant or variable.
3. Color: black, darkened local hue, or a shared warm or cool brown.
4. Ground: wraps the full silhouette, or breaks at the ground contact.

### Silhouette Test

Render or view the subject as a solid black shape at a stated size (for example, 64 pixels tall). The silhouette must read as the intended object. The makko.ai guide cites the Team Fortress 2 approach: distinct silhouettes per character, rim highlights in place of dark outlines, and clothing folds that echo the silhouette. Write the test size into the bible and check it on every hero asset.

### Proportion and Projection

State the proportion ratio (for example, head to body) and the projection (side-on, three-quarter, isometric at a stated angle, top-down with a tilt). Projection is a design decision before it is an art decision: a mix of projections on one screen reads as an error.

## Composition and Negative Space

| Element | Rule |
|---------|------|
| Margin | A percentage clear on each edge, such as 10 percent for banners |
| Focal zone | Where the subject sits, such as lower two-thirds |
| Competition | What may compete with the focal zone, usually value contrast |

Value contrast decides competition more than hue. Write the value rule: "background values stay at least two steps darker or lighter than the subject". This is checkable with an image editor's value readout.

## Level of Detail

Assign each asset class to a tier:

| Tier | Typical subjects | Detail rule |
|------|------------------|-------------|
| Hero | Main product, primary person | Full detail, textures visible |
| Secondary | Supporting props, secondary people | Simplified surfaces, fewer props |
| Background | Environment dressing | Silhouettes and value only |

The makko.ai guide gives an example of the principle: omit high-frequency detail wherever possible so the important information survives. Write the detail budget per tier in words ("background: no more than three distinct props per frame").

## Visual Rule Checklist

Use this list when reviewing a draft of sections 3 to 13:

| Area | Check |
|------|-------|
| Color | Every color has a name, hex, role, and forbidden use |
| Color | Shadow color stated; no pure black or white in surfaces |
| Light | Direction, quality, temperature, and shadow color all stated |
| Lens | Focal length and depth of field given as feel and effect |
| Framing | Subject share of frame and headroom rule stated |
| Medium | Medium named first; mixing forbidden or defined |
| Materials | Named materials with finish; wear scale used |
| Subjects | Each class has its own rules and scale references |
| Text | Allowed or forbidden stated; quoting rule given |
| Composition | Margin and focal zone numbers given |
| Vague words | No "beautiful", "stunning", "moody", or "cinematic" without a property beside it |

## Reference Cross-Links

- Section anatomy and placement of these rules: `bible-structure.md`
- How the invariants were extracted: `discovery-and-references.md`
- Converting these rules into anchors per tool: `tool-translation.md`
- Checking outputs against these rules: `consistency-and-drift.md`
