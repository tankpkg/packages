# Tool Translation

Sources: OpenAI GPT Image prompting guide (2026), Midjourney Style Reference and Parameter documentation (2026), Google Cloud Nano Banana prompting guide (March 2026), Makko (How to Write a Game Art Bible, 2026), FLUX and Stable Diffusion community practice (verify on the build you run)

Covers: how a design bible becomes a portable style anchor, then per-tool prompts for GPT Image (ChatGPT, Codex, and the API), Midjourney, Google Nano Banana (Gemini image models), and open pipelines such as FLUX and Stable Diffusion, with reference-role patterns, parameter placement, and the gotchas the official guides call out.

## The Style Anchor

A style anchor is the portable core of the bible. It is a fixed block of text (plus optional reference images) that every prompt for one tool shares. The subject changes from prompt to prompt. The anchor does not.

### Build It from the Bible

Write the anchor from the invariants in `bible-structure.md`, in this fixed order:

| Slot | Source section | Why this position |
|------|----------------|-------------------|
| 1. Medium | Rendering and medium | Sets the most visual decisions, so it leads |
| 2. Light | Light | Direction and quality, stated as physical properties |
| 3. Lens and framing | Lens, camera, framing | Feel and framing, stated as terms |
| 4. Palette | Palette with roles | Names with roles, not hex alone |
| 5. Materials and finish | Materials and wear | Default finish and wear level |
| 6. Exclusions | Do-not-do list | Only the exclusions that a tool can act on |

Keep the order identical across every prompt. A block that reads the same way each time gives the model the same frame each time, and makes drift visible when someone edits it.

### Length and Content

- Aim for 80 to 200 words. Longer anchors dilute the subject text in most tools, and the block gets edited inconsistently.
- Use names and properties, not adjectives. "Key light camera-left, 45 degrees, soft" beats "beautiful soft light".
- Leave out the subject. The anchor describes how the image looks, never what it shows.
- Include the hex in the bible for QA, but name the color in the anchor. Tools do not guarantee an exact hex match.

### Worked Anchor

A fictional outdoor brand, "Harbor and Pine", with a palette of sand, spruce, ember, and slate:

```text
Photograph, 35mm film look, light natural grain, true-to-life color with no heavy retouching.
Key light from camera-left at 45 degrees, soft large window source, neutral to slightly cool daylight. Shadows are cool blue-grey, never black. No rim light unless the subject is the hero.
Eye-level camera, 50mm feel, subject fills the lower two-thirds of the frame, one third of the frame kept clear.
Palette: dune sand background and surfaces, spruce green for garments and props, one small ember orange accent per image, harbor slate for shadows and text. No pure black or white.
Worn surfaces show working wear: faint scuffs on high-contact points. No gloss highlights on metal or ceramic; satin or matte finishes only.
No studio high-key lighting, no neon, no text in the image.
```

This block is about 110 words. The subject goes in a separate line, such as "A hand adjusts a canvas strap on a trail bag, dusk".

## Per-Tool Translation

| Tool | Style mechanism | Anchor placement | Reference handling | Exclusions | Main gotcha |
|------|-----------------|------------------|--------------------|------------|-------------|
| GPT Image (ChatGPT, Codex, Images API) | Labeled prompt sections plus numbered reference images | Anchor as a labeled STYLE section | Numbered, each with an explicit role | State "no text", "no logos" explicitly | Re-state preserved details on every edit |
| Midjourney | Style reference images or style codes, with a weight | Reference image plus one or two matching words | `--sref` with a public image URL | Negative-term parameter, confirm its syntax | Keep text simple; conflicting words fight the reference |
| Google Nano Banana (Gemini image) | Formula prompts plus reference images | Anchor maps onto the formula's style and composition slots | Up to 14 reference object images per prompt | Positive framing preferred | Quote text; start with a verb |
| FLUX, Stable Diffusion (open pipelines) | LoRA, IP-Adapter, ControlNet | Anchor as positive prompt; LoRA carries the style | IP-Adapter for image-conditioned style | Negative prompt only where the pipeline reads it | Pipeline-specific; record every setting |

## GPT Image

GPT Image is the OpenAI image model family used through ChatGPT, Codex, and the Images API. The OpenAI prompting guide (GPT Image 2.5) gives these rules, which the translation follows.

### Structure the Prompt in Labeled Sections

The guide recommends organizing complex prompts as scene, subject, details, and constraints, using labeled sections. Put the anchor under a STYLE label and keep the subject separate:

```text
SCENE
Outdoor trail at dusk, mid-ground, sparse pine trees out of focus behind.

SUBJECT
A hand adjusts a canvas strap on a trail bag. Hand is relaxed, fingers visible, no rings.

STYLE
Photograph, 35mm film look, light natural grain, true-to-life color with no heavy retouching.
Key light from camera-left at 45 degrees, soft large source, neutral to slightly cool daylight.
Shadows cool blue-grey, never black. Palette: dune sand background, spruce green canvas, one ember accent on the buckle only.

CONSTRAINTS
Subject fills the lower two-thirds of the frame; keep one third clear. No text, no logos, no watermarks.
```

### Describe Visible Details, Not Adjectives

The guide asks for materials, lighting, colors, and the visual medium, and for explicit words such as "photorealistic" or "real photograph" when that is the goal. It also says camera specifications are appearance cues, not exact physics. Put those specifications in the STYLE block as cues, and expect them to shift the look rather than specify it.

### Assign Roles to Reference Images

Number the inputs and state each one's role. The guide's pattern is "Image 1 is the subject; Image 2 is a style reference". For style-only references, say which properties to take:

```text
Image 1 is the product. Keep its geometry, color, and label exactly as shown.
Image 2 is the style reference. Match its palette, grain, and light direction. Do not copy its objects.
```

OpenAI's ChatGPT image guide notes that a small set of uploaded images is usually easier to manage than a large one. Use the approved references from section 15 of the bible, and keep the set to what each prompt needs.

### Exact Text

The guide's rules for text:

- Put required wording in quotes.
- Describe the text's position and typography.
- Spell unusual words or brand names letter by letter when needed.
- Ask for no extra text, then check spelling and legibility.
- Use `medium` or `high` quality for small text, dense information, or several fonts.

### Parameters Belong Outside the Prompt

Set these as request parameters, not inside the text:

| Parameter | Values from the guide | Bible rule |
|-----------|----------------------|------------|
| `model` | `gpt-image-2.5-flare` (small, speed) or `gpt-image-2.5-sunburst` (base, quality) | Record which one passed review |
| `quality` | `auto`, `low`, `medium`, `high`, `xhigh`, `max` | Draft at `medium`; finals at `high` when text or detail matters |
| `size` | `auto` or a custom `WIDTHxHEIGHT`; common sizes include 1024x1024, 1536x1024, 1024x1536, 2048x2048, 3840x2160 | Match the bible's technical spec |
| `background` | `auto`, `opaque`, `transparent` | `transparent` for cutouts, with PNG or WebP output |

Custom sizes must satisfy the guide's constraints: each edge at most 3840 pixels, both edges multiples of 16, aspect ratio at most 3 to 1, and total pixels between 655,360 and 8,294,400. Outputs above 3,686,400 pixels (2560x1440) are marked experimental in the guide.

Check the model names against the current model list before writing them into the bible. The guide names these two variants as of this writing, but model names change.

### Transparent Assets

Request `background="transparent"` explicitly, use PNG or WebP, and check the alpha channel at hair, glass, and shadow edges. Use `output_compression` only for JPEG or WebP, not PNG.

### Model Choice

The guide recommends testing the same prompt and inputs on both variants. Start with Flare when speed matters and the output passes the bible review. Keep Sunburst when its quality advantage is needed. Measure response time and quality on the project's own prompts; a speed gain on one workload does not carry over to another.

### Edits with Preserve Lists

Edits are how GPT Image keeps a product or person recognizable. The pattern from the guide is "change only X, and keep Y exactly":

```text
Edit the image to change the jacket color from spruce green to ember orange.
Do not change the face, hair, pose, background, camera angle, or lighting.
Do not add text, logos, or accessories.
```

For identity-preserving edits, list what must stay fixed: face, skin tone, body shape, pose, hairstyle, and proportions. Match lighting and shadows to the original so the edit does not look pasted on.

Repeated edits compound drift. The guide says to restate constraints and inspect each result, and to test the complete edit sequence, not only single steps. If a region must stay pixel-identical, composite the approved edit into the original instead of relying on the prompt alone.

## Midjourney

Midjourney's Style Reference documentation gives these facts, which the translation follows.

### Style Reference Images

- Add `--sref` followed by a public image URL. The file must end in `.png`, `.gif`, `.webp`, `.jpg`, or `.jpeg`, and the image must already be online.
- A text prompt is required with a style reference.
- Multiple URLs are separated by spaces. Discord also accepts weights: `--sref URL1::2 URL2::1`.
- The doc says a style reference captures color, medium, texture, and lighting, not objects or people. This is why the bible's approved reference is the right input, and why a reference with a clear medium works better than a busy one.

### Style Weight

`--sw` sets how strongly the reference influences the result. The range is 0 to 1000, and the default is 100. Record the weight in the bible's anchor line for Midjourney so every prompt uses the same value. The doc notes that `--sw` has more impact with style codes in V7 than with images.

### Keep Text Prompts to Content

The doc gives these best practices, which become the Midjourney anchor rule:

- Keep the text prompt simple. Style words that conflict with the reference's look fight it.
- Add style words only when the reference alone does not get the look, and make them match the reference.
- Describe what to see, not how to change the reference.

| Weak | Strong |
|------|--------|
| The look of this image but a dog | Detailed portrait of a dog |
| Copy this style and make a bunny | Ballpoint pen sketch of a bunny |

Practical result: the Midjourney anchor is mostly the reference image plus the weight, plus at most one or two words that match it. Most of the bible's palette and light rules are carried by the reference, so the approved reference set (section 15) must be chosen with that in mind.

### Style Codes

A style code replaces an uploaded reference with a code from Midjourney's library. Use `--sref <code>`. Key facts:

- `--sref random` generates a random code after submission. Save the code it produces, because the code is what makes the look repeatable.
- Rerolls, reruns, and variations keep the same code.
- Codes cannot be created from an uploaded image. Use an image reference for that case.
- Codes can be mixed, and combined with image references.

### Version Parameter

`--sv` selects the style reference version. In V7 the default is `--sv 6`. The doc says `--sv 4` is the earlier V7 model, used before June 16, 2025. Codes made before that date may look different without `--sv 4`, or may need V6.

Record the `--sv` value next to the code in the bible. A code without its version can silently change look after a platform update. Check the Version article for the current default before writing it down.

### Incompatibilities

`--sw` and `--sv` are not compatible with Moodboards. Choose one method per project: style reference images, style codes, or Moodboards. Mixing them produces results the bible cannot describe.

### Exclusions

Midjourney supports a negative-term parameter. Confirm its current syntax in the Parameter List before writing it into the anchor. Do not copy syntax from older guides.

### Midjourney Anchor Template

```text
--sref <approved reference URL> --sw <value> --sv <version>
<subject line>, <one or two matching style words>
```

## Google Nano Banana (Gemini Image Models)

Google's Nano Banana guide (March 2026) covers Nano Banana 2 and Nano Banana Pro. The model list includes newer variants, so check the current list before choosing a model.

### Text-to-Image Formula

The guide's formula is:

```text
[Subject] + [Action] + [Location/context] + [Composition] + [Style]
```

The bible maps onto it directly:

| Formula slot | Bible source |
|--------------|--------------|
| Subject | Subject rules (section 8) |
| Action | Subject rules: pose language, interaction |
| Location | Environment rules and scale references |
| Composition | Lens, camera, framing, and composition (sections 5 and 12) |
| Style | The style anchor |

The guide also says to start the prompt with a strong verb that names the main operation. Lead with a verb such as "Photograph", "Render", or "Create".

### Reference Formula

```text
[Reference images] + [Relationship instruction] + [New scenario]
```

The guide's example uses a napkin sketch for structure, a fabric sample for texture, and a new room for the scene. Map the same pattern to the bible: approved references for palette and light, a product reference for geometry, and the subject line for the new scene. The guide states Nano Banana 2 and Nano Banana Pro accept up to 14 reference object images in one prompt. Keep the set small anyway; more references mean more conflicting instructions.

### Positive Framing

The guide says to describe what should be present, not what should be absent. "Empty street" works better than "no cars". Translate the bible's do-not-do list into positive phrasing where possible, and keep literal exclusions only where the tool needs them.

| Do-not-do item | Positive phrasing |
|----------------|-------------------|
| No cars in the background | Empty street, no vehicles visible |
| No gradient on the product | Flat studio ground in one solid color |
| No clutter | Clean surfaces with one object per area |

### Camera and Light Vocabulary

The guide recommends photographic and cinematic terms, lighting setups named explicitly (three-point softbox, chiaroscuro, golden hour backlight), and material names precise enough to render (navy blue tweed, minimalist ceramic coffee mug). These map to bible sections 4, 5, and 7 without translation.

### Text Rendering

The guide's rules:

- Enclose the words in quotes.
- Name the font style or family.
- Use the "text-first" step: converse to generate the text concept, then ask for the image with that text.
- Write the prompt in one language and name the target language for the text output when a translation is needed.

### Editing

The guide says editing needs a different mindset: focus on what changes and what stays. For conversational edits, state what must remain exactly the same. The same preserve-list pattern used for GPT Image applies.

## FLUX and Stable Diffusion (Open Pipelines)

Open pipelines differ by checkpoint, node graph, and version. The notes below are the common patterns. Verify every parameter and behavior on the pipeline the team runs.

### Consistency Tools

| Tool | Role in the bible | Notes |
|------|-------------------|-------|
| LoRA | Carries a trained style from the approved reference set | Train on the approved references only. Record the LoRA weight. |
| IP-Adapter | Conditions generation on a reference image for style or subject | Common choice for style-from-image without training |
| ControlNet | Locks composition, pose, or edges | Use for layout consistency, not for style |
| Seed | Makes a single generation reproducible | Record the seed with every approved image |

Common community guides present IP-Adapter and LoRA as the main consistency tools for these pipelines. Test which one holds the bible's palette and light on the team's checkpoint before standardizing.

### Negative Prompts

Stable Diffusion pipelines commonly accept a negative prompt. Not every FLUX build does, and behavior differs by pipeline. Before putting the do-not-do list in a negative field, check that the pipeline reads it. If it does not, write positive phrasing, as for Nano Banana.

### Record Every Setting

For reproducibility, the bible's technical spec should record for each approved image: checkpoint name, LoRA name and weight, IP-Adapter weight and reference ID, sampler, step count, guidance value, seed, and resolution. Without these, a visually matching image cannot be regenerated later.

## Tool Matrix

| Need | GPT Image | Midjourney | Nano Banana | Open pipeline |
|------|-----------|------------|-------------|---------------|
| Style from one image | Numbered reference with a role | `--sref` with `--sw` | Reference formula | IP-Adapter |
| Repeatable look without an image | Anchor text in STYLE section | Style code with `--sv` recorded | Anchor mapped to formula | LoRA |
| Exact text | Quoted, spelled, checked | Avoid or overlay; verify tool behavior | Quoted, font named, text-first step | Overlay in design tool |
| Transparent cutout | `background="transparent"` plus PNG | Verify current behavior | Verify current behavior | Pipeline-dependent |
| Keep a product recognizable | Edit with preserve list | Reference plus product description | Product as reference object | ControlNet or IP-Adapter |
| Negative exclusions | Stated in constraints | Negative-term parameter (confirm syntax) | Positive phrasing | Only if the pipeline reads it |

Cells marked "verify" are areas where the fetched docs were not conclusive. Test them on the project's own prompts before writing a rule.

## Prompt Structure Rules

These apply to every tool:

1. Anchor first or in its own labeled block, never mixed into the subject sentence.
2. Subject line states what is in the frame, with action and placement.
3. Exclusions stated as the tool supports them: positive phrasing, explicit "no" constraints, or negative parameters.
4. Numbers for sizes, weights, and seeds go in parameters or in the labeled block, not woven into prose.
5. Keep the anchor word-for-word identical across prompts. Edit only when the bible version changes.

## Readiness Checklist per Tool

A tool's anchor is ready to use when:

| Check | Pass |
|-------|------|
| Anchor built from the current bible version | Version number recorded |
| Anchor is 80 to 200 words, or a reference plus parameters for Midjourney | Length checked |
| No vague quality words without a physical property | Checked with `scripts/check_bible.py` |
| Reference IDs or URLs resolve | Each reference opens |
| Tool parameters are the current syntax | Checked against the tool's current docs |
| Test on three subjects shows the look holds | Recorded in the golden set |

## Reference Cross-Links

- Bible sections the anchor is built from: `bible-structure.md`
- Rules the anchor carries: `visual-system-rules.md`
- Checking tool output against the anchor: `consistency-and-drift.md`
- Storing anchors and parameters with approved images: `delivery-and-maintenance.md`
