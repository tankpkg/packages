---
name: "@tank/character-creator"
description: |
  Create complete characters — AI-generated visual sheets (turnarounds,
  expressions, poses) plus written character bibles. Discovery interview,
  archetype-to-visual mapping, AI generation via Flux Kontext and
  GPT-Image-1. Any style: anime, realistic, pixel art, cartoon, vector.
  Triggers: character design, character sheet, create a character,
  expression sheet, character bible, OC design, game character, NPC
  design, villain design, pose sheet, model sheet.
---

# Character Creator

## Core Philosophy

1. **Personality first, aesthetics second.** Every visual decision — shape,
   color, silhouette, costume — flows from the character's personality and
   archetype. Design without personality produces forgettable characters.
2. **Generate, don't describe.** Use AI image generation to produce actual
   character art — turnarounds, expressions, poses. Ship reference sheets,
   not text descriptions of what a character could look like.
3. **Separate views, composite later.** Generate each pose/angle at full
   resolution independently. Multi-view single-image generations lose face
   detail and consistency. Assemble the final sheet in post.
4. **Consistency through reference chaining.** Generate the canonical front
   view first, then use it as the reference image for every subsequent
   generation. The front view is the source of truth.
5. **Complete package or nothing.** A character is not done until it has both
   visual sheets (turnaround + expressions minimum) and a written spec
   (character bible). One without the other is incomplete.

## Quick-Start: Create a Character

### "I have a character idea"

1. **Discover** — Run the discovery interview (5-10 questions) to extract
   personality, motivation, role, world, and visual direction.
   -> See `references/character-discovery.md`
2. **Define** — Map personality to archetype, then archetype to visual DNA:
   shape language, color palette, silhouette, proportions.
   -> See `references/archetype-visual-system.md`
   -> See `references/shape-color-theory.md`
3. **Design** — Specify the visual deliverables: which sheet types, how many
   views, expression count, pose selection.
   -> See `references/character-sheet-components.md`
4. **Generate** — Create the character art using AI image generation:
   canonical image → turnarounds → expressions → poses.
   -> See `references/ai-generation-pipeline.md`
   -> See `references/prompt-templates.md`
5. **Deliver** — Write the character bible and assemble the final package:
   visual sheets + written spec + structured data.
   -> See `references/character-bible-output.md`

### "I need a character sheet for an existing character"

1. Skip discovery — gather the character's existing description, personality,
   and visual references.
2. Write the Character DNA block (50-80 word visual description).
   -> See `references/prompt-templates.md` for DNA block template
3. Generate sheets directly using the AI pipeline.
   -> See `references/ai-generation-pipeline.md`

### "I need a quick NPC or minor character"

1. Run the abbreviated interview (Q1, Q2, Q3, Q4, Q9 only).
2. Use the Quick Character Card format instead of full bible.
   -> See `references/character-bible-output.md` for quick card template

## Decision Trees

### Art Style Selection

| User Signal | Recommended Style | Prompt Approach |
|-------------|-------------------|-----------------|
| Game characters, stylized | Cartoon / Stylized | Bold outlines, exaggerated features, flat colors |
| Anime or manga project | Anime | Cel shading, large eyes, clean linework |
| AAA game or film concept | Realistic | Detailed rendering, anatomical proportions |
| Mobile or retro game | Pixel Art | Limited palette, clean pixels, retro aesthetic |
| Web/app mascot, icons | Vector / Flat | Solid colors, no gradients, SVG-ready |
| Concept art, illustration | Painterly | Visible brushstrokes, rich values |

### Sheet Type Selection

| Need | Minimum Deliverable | Full Deliverable |
|------|--------------------|--------------------|
| Game character | Turnaround (3 views) + T-pose | 5-view turnaround + expressions + poses + props |
| Animation character | 5-view turnaround + expressions | + lip sync chart + hair physics notes |
| Story/novel character | Expression sheet + character bible | + turnaround + costume variants |
| NPC / minor character | Front view + quick card | + idle pose + 2 expressions |
| Mascot / brand character | Turnaround + expression sheet | + pose library + style guide |

### API Selection

| Task | Recommended API | Cost | Why |
|------|----------------|------|-----|
| Canonical front view | GPT-Image-1 or Flux | $0.04-0.10 | Best initial generation quality |
| Turnaround views | Flux Kontext Pro (fal.ai) | $0.04/view | Best character consistency from reference |
| Expression sheet | GPT-Image-1 | $0.04-0.10 | Conversational context preserves identity |
| Pose variations | Flux Kontext Pro (fal.ai) | $0.04/pose | Reference chaining maintains consistency |
| Vector/SVG output | Recraft V4 (fal.ai) | $0.08 | Native SVG generation |
| Face identity lock | Flux-PuLID (fal.ai) | $0.005 | When face drifts between views |

### Scope Selection

| Character Importance | Interview Depth | Visual Package | Written Spec |
|---------------------|-----------------|----------------|--------------|
| Protagonist / Antagonist | Full (10 questions) | Full sheet set | Full character bible |
| Supporting character | Standard (7 questions) | Turnaround + expressions | Standard bible |
| NPC / minor character | Quick (5 questions) | Front view + 2 expressions | Quick character card |
| Background / extra | Skip interview | Front view only | One-line description |

## Authentication

**fal.ai** (Flux Kontext, Recraft, Flux-PuLID):

```bash
export FAL_KEY="YOUR_FAL_KEY"
npm install @fal-ai/client
```

**OpenAI** (GPT-Image-1):

```bash
export OPENAI_API_KEY="YOUR_KEY"
npm install openai
```

## Reference Files

| File | Contents |
|------|----------|
| `references/character-discovery.md` | Discovery interview (10 questions), personality profiling (5 dimensions), archetype quick-select, character essence statement formula, red flags, quality gates |
| `references/archetype-visual-system.md` | All 12 Jungian archetypes with complete visual DNA: shape language, color palettes (hex), silhouette, proportions, costume, movement, AI prompt hints, blending rules, cast-level design |
| `references/shape-color-theory.md` | Shape language (circle/square/triangle), combining shapes, silhouette design, color psychology per color, 60-30-10 palette rule, palette construction from archetype, professional color tests, color scripting for arcs |
| `references/character-sheet-components.md` | Turnaround specs (3-5 views), expression sheet (6-12 emotions), proportion guide, pose sheet, detail callouts, props, color palette documentation, annotations, industry format differences (games/animation/comics), complete deliverable checklist |
| `references/ai-generation-pipeline.md` | 5-step generation pipeline, API selection and auth setup, canonical image generation, turnaround/expression/pose generation with Flux Kontext and GPT-Image-1 code examples, consistency techniques (ranked), assembly, cost estimation, troubleshooting |
| `references/prompt-templates.md` | Character DNA block template, turnaround/expression/pose prompt templates, style-specific variants (anime/realistic/cartoon/pixel/vector/painterly), negative constraints, iteration diagnosis, complete worked example |
| `references/character-bible-output.md` | 10-section character bible template, JSON schema, Markdown spec template, quick character card format, output file organization, medium-specific adaptations (games/animation/comics/TTRPG), quality checklist |
