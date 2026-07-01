---
name: brand-craft
description: |
  Create complete brand identities — logo, colors, typography, and guidelines
  — in minutes. Covers discovery interviews, archetype selection, color
  psychology, font pairing, AI logo generation (QuiverAI Arrow, Recraft V4),
  and brand guideline output (JSON, CSS tokens, Markdown, HTML).
  Synthesizes Wheeler (Designing Brand Identity), Airey (Logo Design Love),
  Mark & Pearson (The Hero and the Outlaw), Adams (Color Design Workbook),
  Lupton (Thinking with Type), Johnson (Branding: In Five and a Half Steps).

  Trigger phrases: "brand identity", "create a brand", "brand design",
  "logo design", "logo creation", "color palette", "brand colors",
  "brand guidelines", "brand style guide", "typography for brand",
  "font pairing", "brand archetype", "brand personality",
  "visual identity", "brand kit", "design system colors",
  "startup brand", "rebrand", "brand refresh",
  "color scheme", "brand book", "logo concept"
---

# Brand Craft

## Core Philosophy

1. **Archetype first, aesthetics second.** Every visual decision flows from
   the brand's archetype and personality. Colors, fonts, and logos that
   don't reinforce the archetype create cognitive dissonance.
2. **Constraint breeds quality.** A brand needs 1 primary color, 2 fonts,
   and 1 logo type — not endless options. Decisive constraints produce
   cohesive identities; optionality produces mush.
3. **Machine-readable over PDF-pretty.** Output brand identity as structured
   JSON with CSS tokens. PDFs look nice but can't feed design tools, theme
   generators, or other AI agents.
4. **Generate, don't describe.** Use AI vector generation (QuiverAI Arrow,
   Recraft V4) to produce actual logo SVGs — not descriptions of what a
   logo could look like. Ship assets, not briefs.
5. **60-30-10 always.** Primary color 60%, secondary 30%, accent 10%.
   This ratio prevents visual chaos in any brand system.

## Quick-Start: The Brand Sprint

### "I need a brand from scratch"

1. **Discover** — Ask 5 key questions to understand the brand:
   - What does the brand do and for whom?
   - What 3 words describe the desired personality?
   - Who are the top 3 competitors?
   - What brands (any industry) feel like what you want?
   - What must the brand absolutely NOT feel like?
2. **Define** — Map answers to archetype + personality profile
   -> See `references/brand-sprint.md` for the full discovery framework
   -> See `references/archetype-visual-map.md` to select archetype
3. **Direct** — Derive visual direction from archetype:
   - Select primary color from archetype palette
   - Build full color system (9-shade scale + neutrals + accent)
   -> See `references/color-strategy.md`
   - Select heading + body fonts matching archetype personality
   -> See `references/typography-system.md`
4. **Design** — Generate logo concepts:
   - Choose logo type (wordmark, combination mark, abstract, etc.)
   - Generate SVG logos via QuiverAI Arrow or Recraft V4
   - Create variants (full, icon, mono, reversed)
   -> See `references/logo-creation.md`
5. **Deliver** — Output complete brand identity:
   - Brand identity JSON (machine-readable)
   - CSS design tokens
   - Brand guidelines document (Markdown or HTML)
   -> See `references/brand-output.md`

### "I need a color palette for my brand"

1. Identify archetype or personality direction
2. Select primary color using color psychology table
3. Derive full palette: primary scale (9 shades) + secondary + accent + neutrals
4. Validate WCAG contrast (4.5:1 minimum for text)
   -> See `references/color-strategy.md`
   -> See `references/archetype-visual-map.md` for archetype-specific palettes

### "I need a logo"

1. Determine logo type from brand characteristics
2. Craft prompt using logo prompt template
3. Generate via QuiverAI Arrow (best quality) or Recraft V4 (cost-effective)
4. Optimize SVG with SVGO, generate variants
   -> See `references/logo-creation.md`

### "I need brand guidelines"

1. Collect brand decisions (archetype, colors, fonts, logo)
2. Generate brand identity JSON
3. Output as Markdown brand guide, HTML page, or CSS design tokens
   -> See `references/brand-output.md`

## Decision Trees

### Archetype Quick-Select

| Brand Personality | Primary Archetype | Secondary Option |
|-------------------|-------------------|------------------|
| Trustworthy, expert, knowledgeable | Sage | Ruler |
| Bold, achievement-oriented, strong | Hero | Explorer |
| Disruptive, rebellious, authentic | Outlaw | Creator |
| Innovative, transformative, visionary | Magician | Creator |
| Warm, nurturing, supportive | Caregiver | Innocent |
| Fun, playful, irreverent | Jester | Explorer |
| Elegant, sensual, premium | Lover | Ruler |
| Down-to-earth, relatable, honest | Everyman | Caregiver |
| Free-spirited, adventurous, independent | Explorer | Outlaw |
| Pure, simple, optimistic | Innocent | Caregiver |
| Authoritative, prestigious, exclusive | Ruler | Sage |
| Creative, imaginative, original | Creator | Magician |

### Logo Type Selection

| Signal | Recommended Logo Type |
|--------|----------------------|
| Short, unique name (1-2 words) | Wordmark |
| Long name or acronym | Lettermark |
| Global brand, language-neutral needed | Abstract mark or Brandmark |
| New brand building recognition | Combination mark |
| Heritage, institutional feel | Emblem |
| Family/consumer audience | Mascot |
| Maximum flexibility needed | Combination mark |

### Color Strategy Selection

| Brand Direction | Color Harmony | Why |
|-----------------|---------------|-----|
| Professional, corporate | Monochromatic (blue) | Trust, cohesion |
| Bold, energetic | Complementary | Maximum contrast |
| Natural, approachable | Analogous | Harmonious, calm |
| Playful, diverse | Triadic | Vibrant, balanced |
| Balanced with pop | Split-complementary | Contrast without tension |
| Luxury, minimal | Monochromatic (dark) | Sophistication |

## Reference Files

| File | Contents |
|------|----------|
| `references/brand-sprint.md` | Rapid brand creation process, discovery questions framework, personality profiling (Aaker dimensions), positioning statement formula, archetype quick-select, creative brief output |
| `references/archetype-visual-map.md` | All 12 brand archetypes with complete visual DNA: colors (hex values), shapes, typography direction, imagery style, brand examples, SVG prompt hints, blending rules |
| `references/color-strategy.md` | Color psychology, industry conventions, cultural considerations, 6 harmony rules, 60-30-10, palette construction from single hex, neutral scales, WCAG accessibility, programmatic generation |
| `references/typography-system.md` | Type personality associations, font selection by brand personality, Google Fonts recommendations (6 categories), pairing rules, hierarchy system, type scale ratios |
| `references/logo-creation.md` | Logo taxonomy (7 types), selection criteria, design principles, AI generation with QuiverAI Arrow and Recraft V4 (code + prompts), variant generation, SVG optimization, iteration strategy |
| `references/brand-output.md` | Brand identity JSON schema, CSS design tokens, Tailwind theme generation, Markdown brand guide template, HTML brand page template, dark mode specs, color scale generation code |
