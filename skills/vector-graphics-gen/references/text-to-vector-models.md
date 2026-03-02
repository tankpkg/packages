# Text-to-Vector Models

Sources: fal.ai documentation (2026), Recraft API docs, QuiverAI Arrow documentation, SVG Arena benchmarks (March 2026)

Covers: All text-to-vector endpoints as of March 2026 — QuiverAI Arrow 1 (standalone API), Recraft V4/V4 Pro/V3 on fal.ai — with complete parameter references, model comparison, SVG Arena rankings, code examples, and the two-step raster-to-SVG pipeline.

## Model Overview

Four primary paths to vector output:

1. **QuiverAI Arrow 1** — purpose-built SVG model, #1 on SVG Arena, standalone API (not on fal.ai)
2. **Native SVG via fal.ai** — Recraft V4 and V4 Pro produce true SVG files directly from text
3. **Vector-style raster** — Recraft V3 with `vector_illustration` style produces raster images optimized for vectorization
4. **Two-step pipeline** — Generate with V3 vector style, then convert to SVG via `fal-ai/recraft/vectorize`

For image-to-SVG conversion endpoints, see `references/image-to-svg-conversion.md`.

## SVG Arena Rankings

SVG Arena is the primary benchmark for text-to-SVG quality as of March 2026. Rankings use Elo scoring from head-to-head comparisons.

| Rank | Model | Elo | Type |
|------|-------|-----|------|
| #1 | QuiverAI Arrow 1 | 1583 | Purpose-built SVG model |
| #2 | Gemini 3.1 Pro | 1421 | General LLM (generates SVG code) |
| #3 | Claude Opus 4.1 | ~1350 | General LLM (generates SVG code) |
| #4 | GPT-5 | ~1340 | General LLM (generates SVG code) |

Note: LLMs generate SVG as text code. Arrow 1 and Recraft produce true vector paths natively — better path quality, editability, and file size.

## Model Comparison Table

| Model | Platform | Output | Price | SVG Arena Elo | Best For |
|-------|----------|--------|-------|---------------|----------|
| QuiverAI Arrow 1 | api.quiver.ai | True SVG | Free tier (20/week) / paid | 1583 (#1) | Highest quality SVGs |
| Recraft V4 Pro | fal.ai | True SVG | $0.30/image | — | High-detail production SVG on fal.ai |
| Recraft V4 | fal.ai | True SVG | $0.08/image | — | Cost-effective native SVG on fal.ai |
| Recraft V3 | fal.ai | Raster PNG | $0.08/image (vector style) | — | Sub-style control (22 styles) |

**Default choice**: Arrow 1 for highest quality SVG. Use Recraft V4 for cost-effective SVG on fal.ai. Use V4 Pro when quality is critical within fal.ai. Use V3 + vectorize pipeline for fine-grained style control.

---

## QuiverAI Arrow 1

**API**: `api.quiver.ai`
**SDK**: `@quiverai/sdk` (npm)
**Output**: True SVG (clean, layered, editable paths)
**Price**: Free tier — 20 SVGs/week; paid plans for higher volume
**Released**: February 25, 2026
**SVG Arena Elo**: 1583 (#1)

Arrow 1 is a purpose-built vector-native model, not a general LLM adapted for SVG. It generates from text prompts and images (multimodal), outputs clean layered SVG with editable paths, and supports real-time streaming. Not available on fal.ai — use the standalone API directly.

### Installation

```bash
npm install @quiverai/sdk
```

Set `QUIVER_API_KEY` in your environment. Obtain a key at `api.quiver.ai`.

### JavaScript Example

```javascript
import QuiverAI from "@quiverai/sdk";

const quiver = new QuiverAI({ apiKey: process.env.QUIVER_API_KEY });

const response = await quiver.svgs.generate({
  model: "arrow-1",
  prompt: "A minimalist mountain logo with clean geometric shapes"
});

const svgUrl = response.data[0].url;
const res = await fetch(svgUrl);
const svgContent = await res.text();
```

### When to Use Arrow 1 vs Recraft

| Scenario | Use |
|----------|-----|
| Highest quality SVG, platform-agnostic | Arrow 1 |
| Already using fal.ai infrastructure | Recraft V4 or V4 Pro |
| Need 22 illustration sub-styles | Recraft V3 + vectorize |
| Free tier sufficient (20 SVGs/week) | Arrow 1 free tier |
| Batch generation at scale on fal.ai | Recraft V4 ($0.08) |

---

## Recraft V4 Text-to-Vector

**Endpoint**: `fal-ai/recraft/v4/text-to-vector`
**Output**: True SVG (`content_type: "image/svg+xml"`)
**Price**: $0.08/image

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | Yes | — | Text description of the desired vector graphic |
| `image_size` | string or object | No | `square_hd` | Output dimensions (see size options below) |
| `colors` | array | No | — | Brand palette as array of `{r, g, b}` objects |
| `background_color` | object | No | — | Background fill as `{r, g, b}` |
| `enable_safety_checker` | boolean | No | `true` | Enable content safety filtering |

### Image Size Options

| Value | Dimensions | Use Case |
|-------|-----------|----------|
| `square` | 512×512 | Icons, avatars |
| `square_hd` | 1024×1024 | Logos, general use (default) |
| `portrait_4_3` | 768×1024 | Tall illustrations |
| `portrait_16_9` | 576×1024 | Mobile-oriented |
| `landscape_4_3` | 1024×768 | Wide illustrations |
| `landscape_16_9` | 1024×576 | Banner graphics |
| `{width, height}` | Custom | Specify exact pixel dimensions |

### Response Format

```json
{
  "images": [
    {
      "url": "https://fal.media/files/...",
      "file_size": 24680,
      "file_name": "image.svg",
      "content_type": "image/svg+xml"
    }
  ]
}
```

### JavaScript Example

```javascript
import { fal } from "@fal-ai/client";

const result = await fal.subscribe("fal-ai/recraft/v4/text-to-vector", {
  input: {
    prompt: "A minimalist mountain logo with clean geometric shapes",
    image_size: "square_hd",
    colors: [
      { r: 59, g: 130, b: 246 },
      { r: 30, g: 64, b: 175 }
    ],
    background_color: { r: 255, g: 255, b: 255 }
  },
  logs: true,
  onQueueUpdate: (update) => {
    if (update.status === "IN_PROGRESS") {
      update.logs.map((log) => log.message).forEach(console.log);
    }
  },
});

const svgUrl = result.data.images[0].url;
const response = await fetch(svgUrl);
const svgContent = await response.text();
```

---

## Recraft V4 Pro Text-to-Vector

**Endpoint**: `fal-ai/recraft/v4/pro/text-to-vector`
**Output**: True SVG (`content_type: "image/svg+xml"`)
**Price**: $0.30/image

The Pro variant uses an enhanced model with higher fidelity output, more complex path structures, and better adherence to detailed prompts. Use when the standard V4 output lacks sufficient detail or when the asset will be used at large scale.

Parameters are identical to Recraft V4 — replace the endpoint string with `fal-ai/recraft/v4/pro/text-to-vector`. All `prompt`, `image_size`, `colors`, `background_color`, and `enable_safety_checker` parameters apply unchanged.

### When to Use V4 Pro vs V4

| Scenario | Use |
|----------|-----|
| Prototyping, iteration, batch generation | V4 ($0.08) |
| Final production asset, client deliverable | V4 Pro ($0.30) |
| Complex illustration with fine detail | V4 Pro |
| Simple icon or logo | V4 |
| Budget-constrained project | V4 |
| Quality is the only constraint within fal.ai | V4 Pro |

---

## Recraft V3 Text-to-Image (Vector Style)

**Endpoint**: `fal-ai/recraft/v3/text-to-image`
**Output**: Raster PNG (NOT true SVG)
**Price**: $0.04/image (raster styles), $0.08/image (vector_illustration style)

V3 produces raster images but with 22 vector-optimized sub-styles that produce clean, flat artwork ideal for downstream vectorization. Use V3 when you need a specific illustration style not available in V4, or as the first step in the two-step pipeline.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | Yes | — | Text description |
| `style` | string | No | `realistic_image` | Top-level style category |
| `style_id` | string | No | — | Sub-style within the category |
| `image_size` | string or object | No | `square_hd` | Output dimensions |
| `colors` | array | No | — | Brand palette as array of `{r, g, b}` objects |
| `enable_safety_checker` | boolean | No | `true` | Enable content safety filtering |

### Top-Level Style Values

| Value | Description | Price |
|-------|-------------|-------|
| `realistic_image` | Photorealistic output | $0.04 |
| `digital_illustration` | Digital art, painterly | $0.04 |
| `vector_illustration` | Flat, clean, vector-optimized | $0.08 |

Set `style: "vector_illustration"` to access all 22 vector sub-styles.

### Vector Illustration Sub-Styles (22 Total)

Set `style_id` to one of these values when `style` is `"vector_illustration"`:

| Sub-style | Visual Character | Best For |
|-----------|-----------------|----------|
| `bold_stroke` | Thick outlines, high contrast | Stickers, badges, bold branding |
| `chemistry` | Technical diagram aesthetic | Scientific, educational content |
| `colored_sticker` | Bright fills with outline | Sticker packs, emoji-style assets |
| `contour` | Outline-focused, minimal fill | Line art, coloring book style |
| `cosmetics` | Soft, elegant, beauty-adjacent | Beauty brands, lifestyle |
| `cutout` | Paper-cut layered look | Collage, editorial illustration |
| `engraving` | Cross-hatch, etched texture | Vintage, premium, certificates |
| `editorial` | Clean, publication-ready | Magazine, news, infographics |
| `ethnic` | Cultural pattern motifs | Decorative, cultural content |
| `line_art` | Pure line drawing, no fill | Sketches, technical illustration |
| `line_circuit` | Circuit board line patterns | Tech, electronics, data |
| `linocut` | Woodblock print texture | Artisan, handmade aesthetic |
| `marker` | Marker pen strokes | Casual, hand-drawn feel |
| `mosaic` | Tile/fragment composition | Decorative, abstract |
| `naiveart` | Childlike, folk art style | Playful, approachable brands |
| `outline` | Simple outline shapes | Icons, UI elements |
| `outline_details` | Outline with interior detail lines | Detailed icons, technical |
| `paper_cut_style` | Layered paper silhouettes | Craft aesthetic, depth |
| `pointilism` | Dot-based texture | Artistic, textured illustration |
| `pop_art` | Bold color, halftone influence | Retro, vibrant branding |
| `psychedelic` | Swirling, surreal patterns | Music, festival, creative |
| `seamless_pattern` | Tileable repeat pattern | Backgrounds, textiles, packaging |
| `thin` | Hairline strokes, delicate | Elegant, minimal, luxury |
| `watercolor` | Soft washes, organic edges | Lifestyle, organic brands |

### JavaScript Example

```javascript
import { fal } from "@fal-ai/client";

const result = await fal.subscribe("fal-ai/recraft/v3/text-to-image", {
  input: {
    prompt: "A coffee cup with steam rising, flat design",
    style: "vector_illustration",
    style_id: "bold_stroke",
    image_size: "square_hd",
    colors: [
      { r: 120, g: 53, b: 15 },
      { r: 254, g: 243, b: 199 }
    ]
  },
  logs: true,
  onQueueUpdate: (update) => {
    if (update.status === "IN_PROGRESS") {
      update.logs.map((log) => log.message).forEach(console.log);
    }
  },
});

const imageUrl = result.data.images[0].url;
// This is a raster PNG — pass to vectorize endpoint to get SVG
```

---

## Two-Step Pipeline: V3 Vector Style + Vectorize

Use this pipeline when you need a specific V3 sub-style (e.g., `engraving`, `linocut`, `seamless_pattern`) and require true SVG output. Total cost: $0.08 (V3) + $0.01 (vectorize) = $0.09/image.

### When to Use the Pipeline vs Direct Options

| Scenario | Approach |
|----------|----------|
| Need a specific V3 sub-style (e.g., linocut, engraving) | V3 + vectorize |
| Need true SVG on fal.ai, style doesn't matter | V4 direct ($0.08) |
| Need highest quality SVG, any platform | Arrow 1 |
| Need seamless/tileable pattern as SVG | V3 seamless_pattern + vectorize |
| Iterating on style before committing to SVG | V3 raster first, vectorize when satisfied |

### Step 1: Generate Raster with V3 Vector Style

```javascript
import { fal } from "@fal-ai/client";

const rasterResult = await fal.subscribe("fal-ai/recraft/v3/text-to-image", {
  input: {
    prompt: "A vintage compass rose, engraving style",
    style: "vector_illustration",
    style_id: "engraving",
    image_size: "square_hd"
  }
});

const rasterUrl = rasterResult.data.images[0].url;
```

### Step 2: Vectorize the Raster

```javascript
const svgResult = await fal.subscribe("fal-ai/recraft/vectorize", {
  input: { image_url: rasterUrl }
});

const svgUrl = svgResult.data.image.url;
const response = await fetch(svgUrl);
const svgContent = await response.text();
```

### Complete Pipeline (Python)

```python
import fal_client
import requests

def generate_vector_svg(prompt: str, style_id: str, colors: list = None) -> str:
    raster_args = {
        "prompt": prompt,
        "style": "vector_illustration",
        "style_id": style_id,
        "image_size": "square_hd"
    }
    if colors:
        raster_args["colors"] = colors

    raster_result = fal_client.subscribe(
        "fal-ai/recraft/v3/text-to-image",
        arguments=raster_args
    )
    raster_url = raster_result["images"][0]["url"]

    svg_result = fal_client.subscribe(
        "fal-ai/recraft/vectorize",
        arguments={"image_url": raster_url}
    )
    svg_url = svg_result["image"]["url"]

    return requests.get(svg_url).text

svg = generate_vector_svg(
    prompt="A vintage compass rose",
    style_id="engraving",
    colors=[{"r": 30, "g": 30, "b": 30}]
)
with open("compass.svg", "w") as f:
    f.write(svg)
```

---

## Colors Parameter Reference

All Recraft endpoints accept a `colors` array to constrain the model's palette to brand colors. Pass up to 5 colors for best results. QuiverAI Arrow 1 does not use this parameter — guide palette through the prompt instead.

```javascript
colors: [
  { r: 59, g: 130, b: 246 },   // primary blue
  { r: 30, g: 64, b: 175 },    // dark blue
  { r: 255, g: 255, b: 255 },  // white
  { r: 15, g: 23, b: 42 }      // near-black
]
```

Convert hex to RGB for the API:

```javascript
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

const brandColors = ["#3b82f6", "#1e40af", "#ffffff"].map(hexToRgb);
```

---

## Model Selection Guide

### By Output Requirement

| You need... | Use |
|-------------|-----|
| Absolute best SVG quality | QuiverAI Arrow 1 (`api.quiver.ai`) |
| True SVG on fal.ai, standard quality | `fal-ai/recraft/v4/text-to-vector` |
| True SVG on fal.ai, maximum quality | `fal-ai/recraft/v4/pro/text-to-vector` |
| SVG with specific illustration style | V3 + `fal-ai/recraft/vectorize` pipeline |

### By Budget

| Budget per asset | Approach |
|-----------------|----------|
| Free (up to 20/week) | Arrow 1 free tier |
| Under $0.05 | V3 raster only ($0.04), no SVG |
| $0.08-0.09 | V4 direct SVG or V3 + vectorize pipeline |
| $0.30 | V4 Pro for highest quality SVG on fal.ai |

### By Style Need

| Style | Endpoint | style_id |
|-------|----------|----------|
| Clean logo/icon, best quality | Arrow 1 | — |
| Clean logo/icon on fal.ai | V4 direct | — |
| Vintage/etched | V3 + vectorize | `engraving` or `linocut` |
| Sticker/badge | V3 + vectorize | `bold_stroke` or `colored_sticker` |
| Seamless pattern | V3 + vectorize | `seamless_pattern` |
| Technical diagram | V3 + vectorize | `line_circuit` or `chemistry` |
| Minimal line art | V3 + vectorize | `line_art` or `thin` |
| Pop/retro | V3 + vectorize | `pop_art` |
| Watercolor-style | V3 + vectorize | `watercolor` |

---

## Error Handling

| HTTP Status | Cause | Action |
|-------------|-------|--------|
| 401 | Invalid or missing API key | Check `FAL_KEY` (fal.ai) or `QUIVER_API_KEY` (Arrow 1) |
| 422 | Invalid parameter type or value | Check `style_id` spelling, `colors` format `{r,g,b}`, `image_size` value |
| 429 | Rate limit exceeded | Implement exponential backoff; Arrow 1 free tier limit returns quota message |
| 500 | Model inference failure | Retry once; if persistent, simplify prompt or switch endpoint |

Wrap `fal.subscribe()` calls in try/catch and inspect `error.status` and `error.body` for validation details. The `422` body typically names the offending field.

For fal.ai client setup, authentication, and queue management patterns, see `references/fal-api-reference.md`.
For prompt engineering strategies specific to vector output, see `references/prompt-engineering.md`.
