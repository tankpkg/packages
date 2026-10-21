---
name: "@tank/design-bible"
description: |
  Create a design bible: a locked visual-language document that keeps AI-generated images consistent across a project. Covers reference discovery, palette roles, light, lens, medium, materials, subject rules, text in images, a do-not-do list, and a cross-context check. Builds style anchors for GPT Image (Codex, ChatGPT, API), Midjourney, Google Nano Banana, and open pipelines (FLUX, Stable Diffusion), and diagnoses drift with a review rubric. Synthesizes the game art bible tradition (Makko), Wheeler (Designing Brand Identity), Wathan and Schoger (Refactoring UI), Albers, Gurney, and official OpenAI, Midjourney, and Google image guides.

  Trigger phrases: "design bible", "art bible", "style bible", "image style guide", "style guide for images", "consistent image style", "keep images consistent", "style anchor", "Codex image generation", "GPT Image style", "Midjourney style guide", "Nano Banana style", "image drift", "off-model images", "visual language document"
---

# Design Bible

Build the document that makes every AI-generated image in a project look like it came from one art department. Image tools produce what the prompt says. The bible decides what the prompt must say, every time.

## Core Philosophy

1. **Write rules a generator can enforce.** Adjectives drift: "warm, moody" means something different on every run. State a property, a value, a location, and a test: "key light from camera-left at 45 degrees; shadows cool blue-grey, never black."
2. **Lock the invariants, free the variables.** Fix what must never change (palette roles, light, medium, the do-not-do list). Leave subject and composition open. Over-constraint produces sameness; under-constraint produces drift.
3. **Derive from references, not taste.** Read the keepers and anti-references, count what they share, and turn shared traits into rules. Never average conflicting references. Resolve the conflict or split the look.
4. **Test at the extremes.** A rule holds only if the asset survives the lightest and darkest scene, the smallest and largest size, and the busiest and emptiest layout the bible allows.
5. **Anchor, do not re-describe.** Paste one style anchor per tool, verbatim, into every prompt. Re-typed style words cause most of the drift.

## Quick-Start: Common Problems

### "I need a design bible from scratch"

1. Run intake: placement and sizes, 3 to 10 keepers, 3 to 5 anti-references, recurring subjects, tools in use. Ask blocking questions one at a time.
   -> See `references/discovery-and-references.md`
2. Extract attributes from the keepers and count which ones they share.
   -> See `references/discovery-and-references.md` (Attribute Extraction)
3. Show the derived invariants for approval before drafting anything long.
4. Draft from `assets/design-bible-template.md` in section order. Write every rule in the enforceable form.
   -> See `references/bible-structure.md` and `references/visual-system-rules.md`
5. Build one style anchor per tool in use.
   -> See `references/tool-translation.md`
6. Validate with `uv run scripts/check_bible.py path/to/DESIGN-BIBLE.md`. Fix every error and review every warning.

### "I have no reference images"

1. Do not invent a look from adjectives. Generate three short direction tests of one neutral subject with the target tool, and let the user choose.
   -> See `references/discovery-and-references.md` (The No-Reference Path)

### "Codex or GPT Image ignores my style"

1. Put the anchor in a labeled STYLE block, stated as physical properties.
2. Pass the approved reference with a role: "Image 2 is the style reference; match palette and grain, not objects."
3. Fix small problems with an edit that lists what must stay the same. Do not regenerate the whole image for a local fix.
   -> See `references/tool-translation.md` (GPT Image)

### "Midjourney looks different every time"

1. Use `--sref` with an approved reference or a saved style code. Write `--sw` and `--sv` into the anchor.
2. Keep the text prompt to content. Style words that conflict with the reference fight it.
   -> See `references/tool-translation.md` (Midjourney)

### "Images drift over weeks"

1. Score the bad image with the rubric and check the drift diagnosis table.
2. Re-anchor to the approved reference set, not to the last output. If the same failure appears twice from different prompts, fix the bible rule, not the prompt.
   -> See `references/consistency-and-drift.md`

### "A model update changed the look"

1. Re-run the golden set on the new model before adopting it. Adopt only if every golden image still passes.
   -> See `references/consistency-and-drift.md` (Golden Set and Model Updates)

## Decision Trees

### Which output format?

| Signal | Deliver |
|--------|---------|
| Project is a repository and coding agents work in it | `docs/design/DESIGN-BIBLE.md` plus a short pointer in the agent instructions |
| No repository; shared drive or document tool | One canonical Markdown or document page, anchors embedded |
| Non-technical reviewers | Markdown source plus a generated HTML view with references inline |
| Several image tools | One anchor per tool, all in section 16 |

### How deep should the bible go?

| Project | Depth |
|---------|-------|
| One-off set, under 10 images | Minimum set: sections 1, 3, 4, 8, 14 |
| Ongoing campaign or product | Full template, photographic sections |
| Illustrated or game asset pipeline | Full template, including silhouette and level of detail |

### Which image tool?

| Tool | Style control | Anchor form |
|------|---------------|-------------|
| GPT Image (ChatGPT, Codex, Images API) | Labeled sections, numbered references with roles, edits | Prose block under a STYLE label |
| Midjourney | `--sref` image or code, `--sw`, `--sv` | Reference line plus one or two matching words |
| Google Nano Banana (Gemini image) | Formula prompts, up to 14 reference images | Anchor mapped onto the formula |
| FLUX or Stable Diffusion | LoRA, IP-Adapter, ControlNet | Positive prompt block; LoRA carries the style |

### Correct, regenerate, or revise?

| Problem | Action |
|---------|--------|
| One local detail is wrong | Edit with a preserve list |
| Palette or light is wrong across the image | Regenerate from the anchor, not from the bad image |
| A region must stay pixel-identical | Composite the approved edit into the original |
| Same failure in two images from different prompts | Revise the bible rule and bump the version |

## Validation

`scripts/check_bible.py` checks a bible file for required sections, unfilled placeholders, invalid hex values, palette rows without hex, do-not-do list size, anchor length, reference IDs, cross-context checks, and vague quality words. Errors exit with code 1; warnings do not. Run it before approval and after every version change.

The template fails by design until its placeholders are replaced. `assets/example-bible.md` is a complete fictional bible that passes with no findings. Use it as the reference for depth and format.

## Boundaries

This skill owns the project-wide visual language for generated images. Hand off to other skills for:

- Logo and brand identity creation: `@tank/brand-craft`
- Per-character sheets and character bibles: `@tank/character-creator`
- SVG generation: `@tank/vector-graphics-gen`
- Agent instruction file formats (AGENTS.md, CLAUDE.md, and others): `@tank/agents-md`

## Reference Files

| File | Contents |
|------|----------|
| `references/bible-structure.md` | The 18-section anatomy, what each section decides, minimum sets by project size, cross-context check |
| `references/discovery-and-references.md` | Intake order, reference curation, attribute extraction, conflict resolution, no-reference path, approval gate |
| `references/visual-system-rules.md` | Enforceable rule form, color roles and saturation, light, lens, medium, materials, subjects, typography, silhouette |
| `references/tool-translation.md` | Style anchors and per-tool prompts for GPT Image, Midjourney, Nano Banana, and open pipelines |
| `references/consistency-and-drift.md` | Drift causes, prevention, review rubric, consistency test, drift diagnosis, golden set, reviewer calibration |
| `references/delivery-and-maintenance.md` | File layout, agent-instruction pointer, versioning, change control, per-image metadata, handoff checklist |
| `assets/design-bible-template.md` | Fillable 18-section bible template with placeholders |
| `assets/example-bible.md` | Complete fictional bible (Harbor and Pine) that passes the validator |
| `scripts/check_bible.py` | Structure, value, and wording checks for a bible file (standard library only) |
