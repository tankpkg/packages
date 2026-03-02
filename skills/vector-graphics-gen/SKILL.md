---
name: "@tank/vector-graphics-gen"
description: |
  Generate vector graphics (SVG) for websites and apps using AI APIs.
  Primary platforms: QuiverAI Arrow (highest quality, #1 SVG Arena) and
  fal.ai with Recraft V4 for native SVG generation, plus image-to-SVG
  conversion. Covers text-to-vector generation, image vectorization,
  prompt engineering for clean vector output, SVG optimization (SVGO),
  and web integration patterns (React, Vue, sprites, dark mode).
  Synthesizes QuiverAI documentation, fal.ai documentation, Recraft AI
  documentation, SVGO docs, and SVG specification.

  Trigger phrases: "vector graphic", "generate SVG", "SVG icon",
  "vector illustration", "AI vector", "fal.ai", "FAL_KEY", "recraft",
  "recraft v4", "text to SVG", "image to SVG", "quiver", "quiverai",
  "arrow model", "vectorize image", "SVG generation", "vector logo",
  "AI illustration", "icon generation", "SVG for web", "vector art API",
  "fal-ai/recraft", "generate icon", "web illustration", "SVG background",
  "vector pattern", "clean SVG", "production SVG", "text-to-vector"
---

# Vector Graphics Generation

## Core Philosophy

1. **Pick the right model for the job.** QuiverAI Arrow produces the
   highest-quality SVGs (1583 Elo, #1 SVG Arena). Recraft V4 on fal.ai
   is the best option when you need sub-style control or cost efficiency.
2. **Every SVG must be production-ready.** Run SVGO, verify viewBox,
   check file size, remove embedded rasters. Never ship raw AI output.
3. **Prompt quality determines output quality.** Specific, structured
   prompts with style keywords and color control produce clean vectors.
   Vague prompts produce unusable output.
4. **Match the tool to the task.** Icons need different models, prompts,
   and optimization than hero illustrations or logos. Select deliberately.
5. **Cost awareness matters.** Arrow is free tier (20/week) or paid API.
   Recraft V4 SVG costs $0.08, V4 Pro $0.30. Choose accordingly.

## Quick-Start: Generate Vector Graphics

### "I need an SVG icon"

1. Set `FAL_KEY` environment variable (for fal.ai) or `QUIVER_API_KEY` (for QuiverAI).
2. Call Recraft V4 text-to-vector for fast, cost-effective icons:
   ```javascript
   const result = await fal.subscribe("fal-ai/recraft/v4/text-to-vector", {
     input: {
       prompt: "minimal settings gear icon, flat design, monochrome black, centered",
       image_size: "square_hd"
     }
   });
   ```
   Or use QuiverAI Arrow for highest quality:
   ```javascript
   const response = await quiver.svgs.generate({
     model: "arrow-1",
     prompt: "minimal settings gear icon, flat design, monochrome black, centered"
   });
   ```
3. Download SVG from the response URL.
4. Optimize with SVGO: `svgo --precision 1 --multipass icon.svg`
   -> See `references/text-to-vector-models.md` for all model options
   -> See `references/prompt-engineering.md` for icon prompt patterns

### "I need a hero illustration"

1. Use Recraft V4 Pro for high-detail native SVG:
   ```javascript
   const result = await fal.subscribe("fal-ai/recraft/v4/pro/text-to-vector", {
     input: {
       prompt: "team collaboration workspace illustration, people at desks with laptops, editorial flat style",
       image_size: "landscape_16_9",
       colors: [{ r: 99, g: 102, b: 241 }, { r: 249, g: 115, b: 22 }]
     }
   });
   ```
2. Or use V3 two-step pipeline for specific sub-style control (22 styles).
3. Optimize with SVGO.
   -> See `references/prompt-engineering.md` for illustration prompts
   -> See `references/image-to-svg-conversion.md` for vectorization

### "I need to convert an existing image to SVG"

1. Use `fal-ai/image2svg` for cheapest conversion ($0.005):
   ```javascript
   const result = await fal.subscribe("fal-ai/image2svg", {
     input: { image_url: "https://example.com/logo.png" }
   });
   ```
2. Or use `fal-ai/recraft/vectorize` for higher quality ($0.01).
3. Download and optimize.
   -> See `references/image-to-svg-conversion.md` for all options

### "I need a batch of consistent assets"

1. Use the `colors` parameter to enforce brand palette across all generations.
2. Use the same model and sub-style for visual consistency.
3. Generate in a loop, optimize each output.
   -> See `references/use-case-recipes.md` for batch pipeline code

## Decision Trees

### Model Selection (March 2026)

| Need | Model | Endpoint / SDK | Cost | SVG Arena Elo |
|------|-------|----------------|------|---------------|
| Highest quality SVG | QuiverAI Arrow 1 | `@quiverai/sdk` | Free tier / paid | 1583 (#1) |
| Native SVG (fal.ai) | Recraft V4 | `fal-ai/recraft/v4/text-to-vector` | $0.08 | — |
| High-res native SVG | Recraft V4 Pro | `fal-ai/recraft/v4/pro/text-to-vector` | $0.30 | — |
| Styled illustration SVG | Recraft V3 + vectorize | `fal-ai/recraft/v3/text-to-image` → vectorize | $0.09 | — |
| Convert image to SVG | Recraft Vectorize | `fal-ai/recraft/vectorize` | $0.01 | — |
| Cheap image to SVG | Image2SVG | `fal-ai/image2svg` | $0.005 | — |

### Pipeline Selection

| Scenario | Pipeline | Total Cost |
|----------|----------|------------|
| Simple icon/logo (best quality) | QuiverAI Arrow → SVGO | Free tier |
| Simple icon/logo (fal.ai) | V4 text-to-vector → SVGO | $0.08 |
| Styled illustration (specific sub-style) | V3 vector_illustration → vectorize → SVGO | $0.09 |
| Existing image | image2svg → SVGO | $0.005 |
| Highest quality (fal.ai) | V4 Pro text-to-vector → SVGO | $0.30 |

### Vector Sub-Style Selection (Recraft V3 Pipeline)

Use the V3 two-step pipeline when you need a specific illustration style.

| Use Case | Recommended Sub-Style |
|----------|----------------------|
| UI icons | `line_art`, `thin`, `sharp_contrast` |
| App icons | `roundish_flat`, `bold_stroke`, `vivid_shapes` |
| Editorial illustrations | `editorial`, `emotional_flat`, `infographical` |
| Logo marks | `bold_stroke`, `cutout`, `sharp_contrast` |
| Technical diagrams | `line_circuit`, `infographical`, `thin` |
| Artistic illustrations | `cosmics`, `mosaic`, `naiveart` |
| Print/engraving | `engraving`, `linocut`, `colored_stencil` |

### SVG Type File Size Targets

| SVG Type | Target Size | Max Paths |
|----------|-------------|-----------|
| UI icon (24px) | < 1 KB | 1-5 |
| Feature icon (48px) | < 2 KB | 5-15 |
| Logo | < 10 KB | 5-30 |
| Illustration | < 30 KB | 20-100 |
| Background pattern | < 5 KB | 5-20 |

## Authentication

**fal.ai** — Set the `FAL_KEY` environment variable:

```bash
export FAL_KEY="YOUR_FAL_KEY"
```

Install: `npm install @fal-ai/client` (JS) or `pip install fal-client` (Python).

**QuiverAI** — Set the `QUIVER_API_KEY` environment variable:

```bash
export QUIVER_API_KEY="YOUR_QUIVER_KEY"
```

Install: `npm install @quiverai/sdk`

-> See `references/fal-api-reference.md` for complete fal.ai setup
-> See `references/text-to-vector-models.md` for QuiverAI Arrow setup

## Reference Files

| File | Contents |
|------|----------|
| `references/fal-api-reference.md` | fal.ai authentication, client setup (JS/Python/REST), request patterns (subscribe, queue, sync), response format, file upload, error handling, downloading SVG results |
| `references/text-to-vector-models.md` | QuiverAI Arrow 1 (#1 SVG Arena), Recraft V4/V4 Pro text-to-vector, Recraft V3 sub-style catalog (22 styles), model comparison with SVG Arena rankings, pricing |
| `references/image-to-svg-conversion.md` | recraft/vectorize, image2svg, star-vector endpoints, two-step pipeline, Potrace CLI, input preparation, quality comparison, limitations |
| `references/prompt-engineering.md` | Prompt structure formula, icon/illustration/logo/pattern prompt templates, style keyword catalog, negative prompts, color control, sub-style mapping, common mistakes |
| `references/svg-optimization.md` | AI-generated SVG issues and fixes, SVGO setup and config, manual cleanup checklist, path simplification, file size targets, accessibility, batch processing |
| `references/svg-integration-patterns.md` | React/Vue SVG components, icon system architecture, SVG sprite sheets, CSS background SVGs, responsive SVGs, dark mode adaptation, animation basics, bundler config |
| `references/use-case-recipes.md` | Complete end-to-end recipes: icon sets, hero illustrations, empty states, logo variations, background patterns, image-to-SVG conversion, brand-consistent assets, batch generation pipeline |
