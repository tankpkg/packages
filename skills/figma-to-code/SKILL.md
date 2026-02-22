---
name: figma-to-code
description: |
  Use when implementing UI from Figma designs with pixel-perfect fidelity.
  Covers the complete Figma-to-code pipeline: extracting design specs via
  Figma MCP tools (get_design_context, get_screenshot, get_variable_defs),
  translating every visual property to exact CSS (fonts, colors, spacing,
  shadows, gradients, border-radius, opacity), building design token systems,
  mapping Auto Layout to Flexbox/Grid, converting component variants to
  props, and verifying implementation against Figma screenshots.

  Requires: Figma desktop MCP (figma-desktop) for design extraction.

  Synthesizes Figma Dev Mode API (2024-2025), CSS Specifications (Color L4,
  Flexbox, Grid, Container Queries), WAI-ARIA Authoring Practices, Google
  Fonts Best Practices, and Playwright Visual Testing.

  Trigger phrases: "implement this Figma", "Figma to code", "pixel perfect",
  "match the design", "copy the Figma", "design implementation",
  "implement this design", "build from Figma", "Figma handoff",
  "translate design to code", "code this component from Figma",
  "design to HTML", "design to React", "design to Tailwind",
  "match Figma exactly", "implement UI from design", "Figma screenshot",
  "convert design", "make it look like Figma", "same as design",
  "design specs", "implement mockup", "from Figma file"
---

# Figma to Code — Pixel-Perfect Implementation

## Core Principles

1. **Extract, never guess** — Every value comes from Figma MCP tools or the
   screenshot. Never approximate colors, spacing, or font sizes.
2. **Validate visually, always** — Take a Figma screenshot AND a browser
   screenshot. Compare side-by-side. Code is not done until they match.
3. **Tokens over hardcodes** — Extract repeated values into CSS custom
   properties. One source of truth for colors, spacing, typography.
4. **Component by component** — Never extract an entire screen at once.
   Work top-down: page → sections → individual components.
5. **Project conventions first** — Use the project's existing design system,
   component library, and naming patterns. Only create new when nothing fits.
6. **Preserve Figma naming and layers** — Keep component layer hierarchy and
   token/variable names aligned with Figma whenever possible.

## Quick-Start: The 6-Step Workflow

### Step 1: Extract Design Context

```
get_design_context(nodeId="1:2", clientFrameworks="react", clientLanguages="typescript,css")
```

Parse Figma URL: `https://figma.com/design/:fileKey/:fileName?node-id=1-2` → nodeId `1:2`.
If branch URL, use branchKey as fileKey.

### Step 2: Capture Screenshot

```
get_screenshot(nodeId="1:2")
```

ALWAYS capture. This is your ground truth for visual validation.

### Step 3: Extract Design Tokens

```
get_variable_defs(nodeId="1:2")
```

Map returned tokens to CSS custom properties. See `references/design-tokens.md`.

### Step 4: Translate to Code

Convert MCP output to project conventions:
- Replace generated classes with project's design system tokens
- Use existing components where they match
- Apply exact CSS values from Figma (see reference files for conversion tables)
- Preserve Figma layer structure for each component (wrapper/content/icon/text
  relationships should match the Figma node tree)
- Keep token names close to Figma variable names; if renamed, record a mapping
  and explicitly note that Figma names must be updated too if parity is desired

### Step 5: Apply Pixel-Perfect CSS

Address the critical rendering differences:

| Issue | Fix |
|-------|-----|
| Text looks bolder in browser | `-webkit-font-smoothing: antialiased` globally |
| Spacing off by 1-2px | Use exact Figma values, avoid rounding |
| Colors look different | Check opacity stacking, use sRGB profile |
| Shadow too strong | Figma blur = diameter, CSS = radius — divide by 2 |
| Gradient direction wrong | Add 90° to Figma angle |
| Font weight mismatch | Figma 500 ≈ browser 400 due to rendering |

### Step 6: Validate Parity

Compare Figma screenshot against browser screenshot. Check every item on
the fidelity checklist in `references/visual-verification.md`. Iterate
until match is exact.

## Decision Trees

### What to Extract First

| Design Scope | Approach |
|-------------|----------|
| Full page | get_metadata first → identify sections → extract each component |
| Single component | get_design_context directly on component node |
| Design system | get_variable_defs → then each component variant |
| Complex/large screen | Metadata-only + screenshot → component-by-component extraction |

### Token Limit Management

| MCP Response Size | Action |
|-------------------|--------|
| < 50k tokens | Use get_design_context output directly |
| 50-100k tokens | Extract component-by-component, not full frame |
| > 100k tokens | Use get_metadata for structure, screenshot for details |

### CSS Property Quick-Reference

| Figma Property | CSS Property | Gotcha |
|----------------|-------------|--------|
| Auto Layout horizontal | `display: flex; flex-direction: row` | — |
| Auto Layout vertical | `display: flex; flex-direction: column` | — |
| Item spacing | `gap` | Not margin between children |
| Fill container | `flex: 1` | Only inside Auto Layout parent |
| Hug contents | `width: fit-content` | — |
| Fixed size | `width: Npx; height: Npx` | — |
| lineHeightPercentFontSize: 150 | `line-height: 1.5` | Unitless, divide by 100 |
| letterSpacing (%) | `letter-spacing: Nem` | Divide % by 100 |
| RGBA {r:0-1} | `rgba(r*255, g*255, b*255, a)` | Multiply RGB by 255 |
| Gradient angle 0° | `linear-gradient(90deg, ...)` | Add 90° |
| Blur radius 8 | `filter: blur(4px)` | Divide by 2 |
| DROP_SHADOW | `box-shadow` | No inset keyword |
| INNER_SHADOW | `box-shadow: inset ...` | Add inset keyword |
| Stroke INSIDE | `box-sizing: border-box; border: ...` | — |
| Stroke OUTSIDE | `outline: ...` | Not border |

## Anti-Patterns

- Selecting entire screens in one extraction (token overflow)
- Skipping screenshot validation ("the code looks right")
- Hardcoding values instead of using design tokens
- Importing icon packages instead of using Figma SVG exports
- Treating MCP-generated code as final (it needs project adaptation)
- Creating new components when project already has matching ones
- Approximating colors/spacing instead of using exact Figma values
- Renaming tokens/layers silently without a documented Figma-to-code mapping

## Reference Files

| File | Contents |
|------|----------|
| `references/figma-extraction-workflow.md` | Figma MCP tool usage, URL parsing, node selection, token limits, asset handling, metadata-only approach |
| `references/typography-fidelity.md` | Font weight mapping, line-height/letter-spacing conversion, font smoothing, OpenType features, text truncation, Google Fonts loading |
| `references/layout-and-spacing.md` | Auto Layout → Flexbox/Grid mapping, sizing modes, constraints → responsive, spacing scales, overflow, border-radius |
| `references/colors-and-effects.md` | Color format conversion, gradient translation, shadow mapping, blur effects, opacity stacking, blend modes, stroke/border |
| `references/design-tokens.md` | Token extraction, naming conventions, CSS custom properties, Tailwind config bridging, dark mode, token scales |
| `references/visual-verification.md` | Screenshot comparison workflow, fidelity checklist, Playwright visual testing, common failure patterns, regression testing |
| `references/component-translation.md` | Component variants → props, state mapping, accessibility, asset management, framework patterns, responsive components |
