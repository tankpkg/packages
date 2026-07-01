# AI Generation Pipeline

Sources: fal.ai documentation (2026), OpenAI API reference (2026), Flux Kontext documentation, production character sheet generation research

Covers: The complete API-driven pipeline for generating a character sheet — canonical image, turnaround views, expression sheet, pose sheet, and final assembly. Includes API selection, authentication, JavaScript code examples, consistency techniques, cost estimation, and troubleshooting. Visual decisions (archetype, shape language, color) come from upstream files; prompt templates are in `references/prompt-templates.md`.

---

## 1. Pipeline Overview

A complete character sheet requires five sequential steps. Each step depends on the output of the previous one — the canonical front-view image anchors every subsequent generation.

| Step | Output | Primary API | Cost |
|------|--------|-------------|------|
| 1 | Canonical front-view image | GPT-Image-1 or Flux Dev | $0.04–0.17 |
| 2 | Turnaround views (side, 3/4, back) | Flux Kontext Pro | $0.12 (3 images) |
| 3 | Expression sheet (6 expressions) | GPT-Image-1 | $0.06–0.12 |
| 4 | Pose sheet (4–6 poses) | Flux Kontext Pro | $0.16–0.24 |
| 5 | Assembly and delivery | Local compositing | $0.00 |

**Total cost per character: approximately $0.20–0.50** depending on quality tier and number of poses.

### Step 1: Generate Canonical Front-View Image

Generate a single, high-quality front-facing image of the character in a neutral T-pose or A-pose against a flat background. This image becomes the reference anchor for all subsequent steps. Save the image URL and write the Character DNA block (see Section 4) before proceeding.

### Step 2: Generate Turnaround Views

Using the canonical image as a reference input, generate the side view (90 degrees), three-quarter view (45 degrees), and back view (180 degrees) separately. Generate each view as an independent call — do not attempt to generate all views in a single image, as multi-view layouts degrade per-view quality and break downstream compositing.

### Step 3: Generate Expression Sheet

Using GPT-Image-1's conversational context (or Flux Kontext with the canonical image as reference), generate six expressions: neutral, happy, sad, angry, surprised, and fearful. Crop to bust level. Keep the same outfit, lighting, and background across all expressions.

### Step 4: Generate Pose Sheet

Using Flux Kontext with the canonical image as reference, generate action poses: T-pose (rigging reference), idle pose (personality), and two to four action poses appropriate to the character's role. Each pose is a separate API call.

### Step 5: Assemble and Deliver

Composite all generated images into a single character sheet using a local image processing library (sharp, Jimp, or Pillow). Arrange panels according to the layout spec from `references/character-sheet-components.md`. Export at 300 DPI for print or 72 DPI at 2x resolution for screen.

---

## 2. API Selection Table

| API | Endpoint | Consistency Score | Cost | Best For |
|-----|----------|-------------------|------|----------|
| Flux Kontext Pro | `fal-ai/flux-pro/kontext` | High (reference image input) | $0.04/image | Turnarounds, pose variations |
| GPT-Image-1 | OpenAI `/v1/images/generations` | High (conversational context) | $0.01–0.17/image | Initial generation, expression sheets |
| Flux-PuLID | `fal-ai/bytedance/flux-pulid` | Very high (face embedding) | $0.005/image | Face identity locking across poses |
| Recraft V4 | `fal-ai/recraft/v4/text-to-image` | Low (prompt-only) | $0.04/image | Vector/stylized output, no reference input |

**Default pipeline**: GPT-Image-1 for Step 1, Flux Kontext Pro for Steps 2 and 4, GPT-Image-1 for Step 3.

**When to substitute**: Use Flux-PuLID in Step 2 or 4 when face consistency is failing across turnarounds. Use Recraft V4 when the project requires a flat vector art style and consistency is enforced through prompt engineering alone.

---

## 3. Authentication Setup

### fal.ai

```bash
npm install @fal-ai/client
export FAL_KEY="your_fal_key_here"
```

```javascript
import { fal } from "@fal-ai/client";

fal.config({ credentials: process.env.FAL_KEY });
```

### OpenAI

```bash
npm install openai
export OPENAI_API_KEY="your_openai_key_here"
```

```javascript
import OpenAI from "openai";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
```

Both keys should be stored as environment variables and never committed to source control. For CI/CD pipelines, inject them as secrets.

---

## 4. Step 1: Canonical Image Generation

The canonical image is the single most important generation in the pipeline. Every subsequent step references it. Invest in quality here — use a higher-quality tier and regenerate if the result is ambiguous or inconsistent.

### Generating the Hero Front-View Image

Use GPT-Image-1 at `high` quality for the canonical image. Specify orthographic camera, flat neutral lighting, and a solid grey or white background. The character must be fully visible from head to toe.

```javascript
import OpenAI from "openai";
import fs from "node:fs";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const response = await openai.images.generate({
  model: "gpt-image-1",
  prompt: "Full-body character design, front view, T-pose, orthographic camera, flat neutral lighting, solid grey background. [CHARACTER_DNA_BLOCK]",
  size: "1024x1024",
  quality: "high",
  n: 1,
});

const imageUrl = response.data[0].url;
fs.writeFileSync("./canonical.json", JSON.stringify({ url: imageUrl }));
```

Replace `[CHARACTER_DNA_BLOCK]` with the 50+ word description assembled from the visual decisions in `references/archetype-visual-system.md`.

### Locking the Character DNA Block

After generating the canonical image, write a Character DNA block — a verbatim, reusable description of the character's fixed visual properties. This block is pasted into every subsequent prompt without modification.

A Character DNA block covers: gender presentation, approximate age, body type, skin tone, hair color and style, eye color, distinctive facial features, outfit description (colors, materials, silhouette), and any signature accessories or markings.

Example structure (fill in specifics):

```
[CHARACTER_DNA_BLOCK]
Young adult woman, athletic build, warm brown skin, shoulder-length natural
black hair with loose curls, amber eyes, small scar above left eyebrow.
Wearing a deep teal tactical jacket with orange trim, dark grey cargo pants,
worn leather boots. Carries a worn leather satchel over her right shoulder.
```

Save this block to a variable or file. Paste it verbatim into every prompt in Steps 2–4.

---

## 5. Step 2: Turnaround Generation

Flux Kontext Pro accepts a reference image URL alongside a text prompt and generates a new image of the same subject from a different angle. This is the most reliable method for turnaround consistency without LoRA training.

### Uploading the Canonical Image

If the canonical image URL is a temporary OpenAI URL, upload it to fal.ai storage first to ensure it remains accessible during the pipeline run.

```javascript
import { fal } from "@fal-ai/client";
import fs from "node:fs";

const buffer = fs.readFileSync("./canonical.png");
const file = new File([buffer], "canonical.png", { type: "image/png" });
const canonicalFalUrl = await fal.storage.upload(file);
```

### Generating Each Turnaround View

Generate each view as a separate call. Pass the canonical image URL as `image_url` and include the Character DNA block in the prompt.

```javascript
const views = [
  { angle: "side_view", prompt: "character design sheet, exact side view, 90 degrees, T-pose, orthographic camera, flat lighting, grey background" },
  { angle: "three_quarter_view", prompt: "character design sheet, three-quarter view, 45 degrees, T-pose, orthographic camera, flat lighting, grey background" },
  { angle: "back_view", prompt: "character design sheet, back view, 180 degrees, T-pose, orthographic camera, flat lighting, grey background" },
];

const turnarounds = {};

for (const view of views) {
  const result = await fal.subscribe("fal-ai/flux-pro/kontext", {
    input: {
      prompt: `${view.prompt}. ${CHARACTER_DNA_BLOCK}`,
      image_url: canonicalFalUrl,
    },
    logs: false,
  });
  turnarounds[view.angle] = result.data.images[0].url;
}
```

Each prompt ends with the Character DNA block. The `image_url` parameter is what drives visual consistency — the text prompt controls the camera angle and framing.

---

## 6. Step 3: Expression Sheet

GPT-Image-1's conversational context maintains character consistency across multiple turns within a single session. Use this for expression sheets: generate the canonical image in turn 1, then request each expression in subsequent turns.

### Using GPT-Image-1 Conversational Context

```javascript
import OpenAI from "openai";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const expressions = ["neutral", "happy", "sad", "angry", "surprised", "fearful"];
const expressionImages = {};

for (const expression of expressions) {
  const response = await openai.images.generate({
    model: "gpt-image-1",
    prompt: `Same character, bust crop, ${expression} expression, same outfit and hair, flat neutral lighting, grey background. ${CHARACTER_DNA_BLOCK}`,
    size: "1024x1024",
    quality: "medium",
    n: 1,
  });
  expressionImages[expression] = response.data[0].url;
}
```

### Alternative: Flux Kontext for Expressions

If GPT-Image-1 conversational context is unavailable or inconsistent, use Flux Kontext with the canonical image as reference. Replace the endpoint and add `image_url: canonicalFalUrl` to the input, following the same pattern as Step 2.

The six required expressions are: neutral, happy, sad, angry, surprised, and fearful. These cover the six basic emotions from Ekman's model and are sufficient for most animation and game pipelines. Add additional expressions (disgusted, contemptuous, determined) only if the project brief specifies them.

---

## 7. Step 4: Pose Sheet

Use Flux Kontext Pro for pose generation. The canonical image provides the visual anchor; the prompt specifies the pose. Generate each pose as a separate call.

### Required Poses

| Pose | Purpose | Notes |
|------|---------|-------|
| T-pose | Rigging reference | Arms horizontal, palms down, feet shoulder-width |
| A-pose | Alternative rigging reference | Arms at 45 degrees, preferred for some rigs |
| Idle pose | Personality and resting state | Relaxed, characteristic stance |
| Action pose 1 | Primary combat or skill action | Specific to character role |
| Action pose 2 | Secondary action or reaction | Running, jumping, or defensive |

```javascript
const poses = [
  { name: "t_pose", prompt: "T-pose, arms horizontal, palms facing down, feet shoulder-width apart, full body, orthographic camera, flat lighting, grey background" },
  { name: "idle", prompt: "relaxed idle stance, weight on one hip, arms loosely at sides, full body, flat lighting, grey background" },
  { name: "action_1", prompt: "dynamic action pose, mid-stride running, full body, flat lighting, grey background" },
];

const poseImages = {};

for (const pose of poses) {
  const result = await fal.subscribe("fal-ai/flux-pro/kontext", {
    input: {
      prompt: `${pose.prompt}. ${CHARACTER_DNA_BLOCK}`,
      image_url: canonicalFalUrl,
    },
    logs: false,
  });
  poseImages[pose.name] = result.data.images[0].url;
}
```

---

## 8. Consistency Techniques

Apply these techniques in order of reliability. Reference image chaining is the baseline for this pipeline. Add additional techniques when consistency is failing.

| Technique | Reliability | Cost Impact | Setup Effort | When to Use |
|-----------|-------------|-------------|--------------|-------------|
| Reference image chaining | High | None (built into pipeline) | Low | Always — baseline technique |
| Character DNA block | Medium-High | None | Low | Always — paste into every prompt |
| Flux-PuLID face embedding | Very high (face only) | +$0.005/image | Low | When face drifts across turnarounds |
| LoRA training | Very high (full character) | $2–5 one-time training | High | Production projects, 10+ images needed |
| Seed locking | Low (minor variations only) | None | Low | Generating multiple options of one view |

### Technique 1: Reference Image Chaining (Most Reliable)

Pass the canonical image URL as `image_url` in every Flux Kontext call. The model uses the reference image as a visual constraint, not just the text prompt. This is the primary consistency mechanism in this pipeline.

### Technique 2: Character DNA Block

Write the Character DNA block once after Step 1 and paste it verbatim into every subsequent prompt. Do not paraphrase or abbreviate it. Consistency degrades when the description varies between calls.

### Technique 3: Flux-PuLID Face Embedding

When face identity is drifting across turnarounds or poses, add a Flux-PuLID pass. Upload a close-cropped face image from the canonical output and use it as the identity reference.

```javascript
const result = await fal.subscribe("fal-ai/bytedance/flux-pulid", {
  input: {
    prompt: `${posePrompt}. ${CHARACTER_DNA_BLOCK}`,
    reference_image_url: faceCloseupUrl,
    id_scale: 0.8,
  },
});
```

Set `id_scale` between 0.7 and 0.9. Higher values lock the face more tightly but reduce pose flexibility.

### Technique 4: LoRA Training

For production projects requiring 10 or more character images at 95%+ consistency, train a character LoRA using `fal-ai/flux-lora-fast-training`. Provide 10–20 images of the character from varied angles. Training costs approximately $2–5 and takes 10–20 minutes. Once trained, use the LoRA URL in any Flux endpoint via the `loras` parameter.

### Technique 5: Seed Locking

Pass a fixed `seed` integer to generate minor variations of the same composition. Seed locking does not enforce character consistency across different prompts — it only reproduces the same stochastic result for an identical prompt. Use it when generating multiple options of a single view for client selection.

---

## 9. Step 5: Assembly

Composite all generated images into a single character sheet layout. Use a local image processing library — no additional API calls are required for standard assembly.

### Recommended Libraries

| Language | Library | Install |
|----------|---------|---------|
| JavaScript | sharp | `npm install sharp` |
| Python | Pillow | `pip install Pillow` |

### Assembly Steps

1. Download all generated images from their URLs to local disk.
2. Resize each image to a consistent panel size (512x512 or 1024x1024 per panel).
3. Composite panels onto a canvas according to the layout spec in `references/character-sheet-components.md`.
4. Add labels (view names, expression names) using a monospace font at 14–16px.
5. Export the final sheet.

```javascript
import sharp from "sharp";

async function downloadImage(url, path) {
  const res = await fetch(url);
  const buffer = Buffer.from(await res.arrayBuffer());
  await sharp(buffer).resize(512, 512, { fit: "contain", background: "#e5e5e5" }).toFile(path);
}
```

### File Format and Resolution

| Use Case | Format | Resolution | DPI |
|----------|--------|------------|-----|
| Game asset pipeline | PNG | 2048x2048 per panel | 72 |
| Print / portfolio | PNG or TIFF | 4096x4096 per panel | 300 |
| Web / presentation | JPEG (90%) | 1024x1024 per panel | 72 |
| Vector output | SVG (Recraft V4) | — | — |

### Upscaling

If the generated images are too small for the target resolution, upscale before compositing using `fal-ai/aura-sr` (4x upscaler, $0.01/image) or a local tool such as Real-ESRGAN. Upscale after generation, before assembly.

---

## 10. Cost Estimation Table

### Per-Component Costs

| Component | API | Images | Cost (Standard) | Cost (Premium) |
|-----------|-----|--------|-----------------|----------------|
| Canonical front view | GPT-Image-1 | 1 | $0.04 (medium) | $0.17 (high) |
| Turnaround views (3) | Flux Kontext Pro | 3 | $0.12 | $0.12 |
| Expression sheet (6) | GPT-Image-1 | 6 | $0.06 (low) | $0.24 (medium) |
| Pose sheet (4) | Flux Kontext Pro | 4 | $0.16 | $0.16 |
| Upscaling (optional) | fal-ai/aura-sr | 14 | $0.14 | $0.14 |
| Assembly | Local | — | $0.00 | $0.00 |

### Budget Tiers

| Tier | Configuration | Estimated Total |
|------|---------------|-----------------|
| Budget | GPT-Image-1 low quality, 3 turnarounds, 4 expressions, 2 poses, no upscaling | ~$0.20 |
| Standard | GPT-Image-1 medium quality, 3 turnarounds, 6 expressions, 4 poses, no upscaling | ~$0.38 |
| Premium | GPT-Image-1 high quality, 3 turnarounds, 6 expressions, 6 poses, upscaling | ~$0.75 |
| Production | LoRA training + Flux Kontext, 3 turnarounds, 6 expressions, 6 poses, upscaling | ~$3.00 (includes one-time LoRA) |

---

## 11. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Face changes between turnarounds | Reference image chaining insufficient | Add Flux-PuLID face embedding (Technique 3) |
| Outfit color shifts between views | Character DNA block too vague on colors | Add exact hex color descriptions to DNA block |
| Character scale inconsistent across panels | No explicit framing instruction | Add "full body, head to toe, centered" to every prompt |
| Hair style changes between expressions | Expression prompt overrides hair description | Append full DNA block after expression keyword, not before |
| Background bleeds into character silhouette | Flat background not specified | Add "solid flat grey background, no shadows, no gradients" |
| Flux Kontext ignores reference image | `image_url` is an expired temporary URL | Re-upload to fal.ai storage and use the persistent URL |
| GPT-Image-1 returns 400 on long prompts | Prompt exceeds token limit | Trim DNA block to 40 words; move detail to style prefix |
| Pose sheet figures look stiff | Orthographic framing too rigid | Remove "orthographic camera" from pose prompts; keep it only for turnarounds |
| LoRA training produces blurry output | Training images too few or too similar | Provide 15–20 images with varied angles and lighting |
| Assembly panels misaligned | Images generated at different aspect ratios | Normalize all images to the same canvas size before compositing |

### When to Switch APIs

Switch from GPT-Image-1 to Flux Kontext when: the project requires strict reference image chaining, the conversational context is producing drift after 4+ turns, or the output style is too photorealistic for the target art direction.

Switch from Flux Kontext to GPT-Image-1 when: the project requires iterative refinement through natural language, the character has complex clothing details that benefit from conversational correction, or the budget favors lower per-image cost at medium quality.

Switch to LoRA training when: the character will appear in more than 10 images, consistency requirements exceed 90%, or the project is a commercial game or animation pipeline where reshoots are not acceptable.
