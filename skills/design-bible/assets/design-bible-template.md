# {{Project name}} Design Bible

Version: {{1.0.0}}
Status: {{draft | approved | superseded}}
Owner: {{name or role}}
Tools: {{GPT Image model, Midjourney, Nano Banana, open pipeline}}
Last updated: {{YYYY-MM-DD}}

Replace every placeholder in double braces before approval. Run `uv run scripts/check_bible.py` on the finished file; it fails on any placeholder that remains, which is intended.

## 1. Thematic statement

{{One paragraph with a point of view. Name what the images feel like, what they refuse to be, and what the viewer should conclude. A stranger must pick the on-brief image from two options using only this paragraph.}}

## 2. Purpose and use

| Channel | Size | Audience | Notes |
|---------|------|----------|-------|
| {{Social square}} | {{1024x1024}} | {{audience}} | {{notes}} |
| {{Web banner}} | {{1536x1024}} | {{audience}} | {{notes}} |

Never used in: {{contexts where generated imagery must not appear}}.

## 3. Palette

| Name | Hex | Role | Share of frame | Never used for |
|------|-----|------|----------------|----------------|
| {{Name}} | {{#RRGGBB}} | Ground | {{50-60%}} | {{use}} |
| {{Name}} | {{#RRGGBB}} | Support | {{25-35%}} | {{use}} |
| {{Name}} | {{#RRGGBB}} | Signal | Under 10% | Backgrounds |
| {{Name}} | {{#RRGGBB}} | Ink | {{varies}} | Pure black surfaces |

Saturation band: {{class: mean range, measured how}}.
Maximum hue families per image: {{number}}.
Shadow color: {{hue family, never pure black}}.

## 4. Light

- Direction: {{compass or clock position, height}}
- Quality: {{hard or soft, source type}}
- Temperature: {{Kelvin or named source}}
- Shadow color: {{named hue family}}
- Fill ratio: {{key to fill}}
- Rim light: {{allowed subjects, or forbidden}}

## 5. Lens, camera, and framing

- Focal feel: {{24mm, 35mm, 50mm, 85mm, with the effect}}
- Depth of field: {{f-range and effect}}
- Camera height: {{eye level, low, high, aerial}}
- Subject share of frame: {{percentage}}
- Headroom and placement: {{rule}}
- Crop rule: {{what must never be cut off}}

## 6. Rendering and medium

Medium: {{photograph, 3D render, flat vector, painterly, cel shading, pixel art}}
Specify: {{grain level, stroke width, tone bands, shader family, as applicable}}
Forbidden: {{effects that break the medium}}
Mixing mediums: {{forbidden, or the rule for each part}}

## 7. Materials and wear

- Default finish: {{matte, satin, gloss, per material}}
- Wear scale default: {{level 0 to 3 per subject class}}
- Named materials: {{list of material nouns with finish}}

## 8. Subjects

### People

- Age range: {{range}}
- Skin tone range: {{range the project shows}}
- Wardrobe palette: {{palette roles}}
- Expressions and gaze: {{permitted set}}
- Likeness rule: {{no real people, or the rights basis}}

### Products

- Reference geometry: {{reference ID from section 15}}
- Required angles: {{list}}
- Finish and color: {{palette roles and finish}}
- Scale cue: {{object of known size}}

### Environments

- Era and location type: {{text}}
- Scale references: {{door height, shelf depth, and so on}}
- Weather and time states allowed: {{list}}

## 9. Typography in images

Text allowed: {{none | headline | label | both}}
Maximum words per image: {{number}}
Placement zones: {{named zones}}
Font descriptor: {{style, weight, era}}
Quoting rule: exact copy in quotes; spelling checked on every output.

## 10. Line, silhouette, and proportion

Illustrative work only. Mark as not applicable for photographic work.

- Outline: {{present or not; weight; color; ground break}}
- Silhouette test size: {{pixels}}
- Proportion ratio: {{ratio}}
- Projection: {{side-on, three-quarter, isometric angle, top-down tilt}}

## 11. Technical spec

| Item | Value |
|------|-------|
| Output sizes | {{per channel}} |
| Aspect ratios | {{list}} |
| Transparency | {{required or not; PNG or WebP}} |
| Quality, draft and final | {{values per tool}} |
| File naming | {{pattern}} |
| Reproducibility fields | {{model, parameters, seed or style code, version}} |

## 12. Composition and negative space

- Margin: {{percentage clear on each edge}}
- Focal zone: {{where the subject sits}}
- Competition rule: {{value contrast rule, with the number of steps}}

## 13. Level of detail

| Tier | Subjects | Detail budget |
|------|----------|---------------|
| Hero | {{subjects}} | {{budget in words}} |
| Secondary | {{subjects}} | {{budget in words}} |
| Background | {{subjects}} | {{budget in words}} |

## 14. Do-not-do list

Each item states what is forbidden and why. Aim for 6 to 12 items.

- {{Forbidden item, because reason.}}
- {{Forbidden item, because reason.}}
- {{Forbidden item, because reason.}}
- {{Forbidden item, because reason.}}
- {{Forbidden item, because reason.}}
- {{Forbidden item, because reason.}}

## 15. Reference set

### Approved

| ID | File or URL | Source | Rights | Proves |
|----|-------------|--------|--------|--------|
| R01 | {{path}} | {{source}} | {{status}} | {{what it proves}} |
| R02 | {{path}} | {{source}} | {{status}} | {{what it proves}} |
| R03 | {{path}} | {{source}} | {{status}} | {{what it proves}} |

### Rejected

| ID | File or URL | Proves not |
|----|-------------|------------|
| A01 | {{path}} | {{what it proves is out of bounds}} |

## 16. Style anchors

One block per tool. Paste verbatim into every prompt for that tool. Do not paraphrase. Change only with a version bump.

### GPT Image

```text
{{Anchor for GPT Image: medium first, then light, lens and framing, palette with roles, materials and finish, exclusions. 80 to 200 words, no subject.}}
```

### Midjourney

```text
{{--sref reference URL --sw weight --sv version, plus one or two matching words}}
```

### Google Nano Banana

```text
{{Anchor mapped onto the style and composition slots of the formula.}}
```

## 17. Cross-context check

Run on at least one generated asset before approval.

- [ ] Subject reads and keeps palette roles in the lightest allowed scene.
- [ ] Subject reads and keeps palette roles in the darkest allowed scene.
- [ ] Silhouette and key detail read at the smallest output size.
- [ ] Focal zone holds in the busiest layout.
- [ ] Focal zone holds in the emptiest layout.

## 18. Change log

### {{version}} ({{date}})

- Changed: {{what}}
- Reason: {{why}}
- Test: {{golden set result}}
- Approved by: {{name}}
