# Discovery and References

Sources: Wheeler (Designing Brand Identity, 5th ed.), Makko (How to Write a Game Art Bible, 2026), Albers (Interaction of Color, 50th anniversary ed.), Wathan and Schoger (Refactoring UI, 2018)

Covers: the intake order and blocking questions, reference and anti-reference curation, attribute extraction from a mood board, the invariant-versus-variable split, conflict resolution between references, the no-reference path, and the approval gate before the full bible is written.

## Intake Order

Discovery produces the facts the bible needs. Ask in this order. Stop early when the answers are enough to draft.

| # | Question | Why it matters | Default if unknown |
|---|----------|----------------|--------------------|
| 1 | Where will the images appear, and at what sizes? | Sets composition, detail, and technical spec | Social square 1024x1024 and wide 1536x1024 |
| 2 | Who sees them, and what should they feel or conclude? | Drives the thematic statement | Ask again; do not guess emotion |
| 3 | Is there an existing brand (logo, colors, fonts)? | Palette and tone source | None; derive from references |
| 4 | Which 3 to 10 images already look right? | Attribute extraction and approved set | Required. Go to the no-reference path if none |
| 5 | Which 3 to 5 images or brands look wrong? | Do-not-do list and boundary | Optional but strongly recommended |
| 6 | Which image tools will generate the images? | Style anchor format per tool | GPT Image through the user's current tool |
| 7 | Which subjects recur (people, products, places)? | Subject rules | Ask; cannot be inferred |
| 8 | Are there hard constraints (real product shape, rights, no real people, legal)? | Non-negotiable rules | None stated; say so in the bible |

Two questions are blocking: question 4 (references) and question 7 (recurring subjects). Without them the bible will be generic. Everything else can be inferred and listed as an assumption.

### Asking Mechanics

Ask blocking questions one at a time, with the recommended option first. A choice that changes the output (for example, "photo or illustration") is blocking. Batch the factual questions (sizes, tools, brand assets) into one message the user can answer in a single pass.

Do not ask the user to describe their style in adjectives as the first question. Adjectives are the least enforceable input. Ask for references first and use adjectives only to label what the references already show.

## Reference Curation

### Choose Keepers

Ask for 6 to 12 keepers for a full bible, 3 for a one-off set. Quality beats quantity: each keeper should prove one specific thing the bible needs.

Check coverage. The keeper set must include every subject class the bible must handle. If the bible covers people, products, and interiors, the keepers must include at least one of each. A set of six close-up portraits cannot teach the rules for interiors.

Mark each keeper with an ID and a one-line purpose:

```text
R01  Close-up of a hand on a canvas strap. Proves: light direction, wear level 2.
R02  Wide shot of a trail at dusk. Proves: environment scale, cool shadows.
R03  Product on a plain table. Proves: palette ground color, negative space.
```

### Record Provenance and Rights

For each keeper, record the source and whether the team can use it as a reference. A reference image may be a licensed stock photo, the team's own photo, or a generated image the team approved. Do not treat a third-party image as a free style source if its rights are unclear. Do not use a reference that contains a real person's likeness as a subject guide.

Reference images used for style only (no subject copying) are the lowest-risk case. Say so in the bible.

### Choose Anti-References

Anti-references set the boundary. They show what the team rejects, which is often clearer than what it wants. Record each with an ID and what it proves.

```text
A01  High-key studio product shot. Proves: high-key light is out of bounds.
A02  Neon city night. Proves: saturated neon is forbidden outside the signal color.
```

Each anti-reference becomes a do-not-do item in the bible (see `bible-structure.md`, section 14).

## Attribute Extraction

Extraction turns a pile of images into rules. Do it for every keeper, then count across keepers.

### Record Per Keeper

| Attribute | What to record |
|-----------|----------------|
| Light | Direction, hardness, color temperature, shadow color |
| Palette | Three dominant colors, one accent if present, ground color |
| Lens | Focal length feel (wide, normal, tele), depth of field |
| Camera height | Eye level, low, high, aerial |
| Medium | Photo, render, vector, painterly, cel, pixel |
| Texture and grain | None, fine, visible; wear level 0 to 3 |
| Composition | Subject placement, margin, negative space share |
| Subject treatment | Framing, expression range, gaze, scale cues |

Use a table with one row per keeper. Fill it by looking, not by guessing: if you cannot see the light direction, write "unclear" and do not invent it.

### Count Across Keepers

Once every keeper has a row, count how many keepers share each attribute. Use these working thresholds, and confirm them with the user:

| Share of keepers | Classification | Bible treatment |
|------------------|----------------|-----------------|
| 80 percent or more | Invariant | Hard rule, goes in the anchor and the do-not-do list |
| 40 to 79 percent | Guided default | Written as a default with stated exceptions |
| Under 40 percent | Variable | Left open; the bible says it may vary and within what range |

Thresholds are a working convention, not a standard. Adjust them when the keeper set is small (three keepers make 80 percent mean all three).

### Turn Invariants into Rules

Each invariant becomes a sentence with a property, a value, a location, and a test. This is the enforceable form described in `visual-system-rules.md`.

| Extracted observation | Rule |
|-----------------------|------|
| Light comes from the left in R01, R02, R04 | Key light from camera-left, 45 degrees, in all subject shots |
| Shadows look blue in R02 and R03 | Shadows are cool blue-grey, never black |
| Every keeper has an empty third of the frame | Keep one third of the frame clear of the subject |

## Resolve Conflicts Between References

Keepers will disagree. Do not average them. Averaging produces mush: a palette between two brands that belongs to neither.

Resolve conflicts in this order:

1. **Ask the user** which keeper is the stronger signal. This is a product decision, not a technical one.
2. **Take the dominant style** when the user cannot choose. Count which look appears in most keepers and build the bible around it.
3. **Split into primary and secondary looks** when both are wanted. Give each its own palette and light rules, and state when each applies (for example, product pages use the primary look, editorial posts use the secondary look). Share the invariant that holds for both, such as the signal color or the do-not-do list.

Record each resolved conflict in the change log with the reason.

## Brand Assets Present

When the project has an existing brand, map the brand's tokens onto palette roles. Brand colors are chosen for interfaces and logos, not for photographs, so some will not work in imagery. Check each brand color for these failures:

| Failure | Symptom | Action |
|---------|---------|--------|
| Interface blue that reads harsh in photos | Overly saturated sky and clothing | Keep as signal only; choose a softer ground |
| Brand color is near-black | Shadows and ink collapse | Use it as ink, with a tinted variant for shadows |
| Brand color is pure white | Blown-out highlights | Use a warm or cool off-white for surfaces |

The brand-craft skill produces tokens (JSON, CSS) that map directly to palette roles. Use those tokens as the starting palette, then test them against the keepers.

## Multi-Look Projects

Some projects need more than one look: a product catalog and an editorial series, for example. Build a parent bible with one shared invariant (usually the signal color, the do-not-do list, or the medium), then child sections for each look with their own light, palette, and framing rules. Keep the parent short. The child looks carry most of the detail.

Do not use multiple looks to avoid a decision. If the team cannot decide between two looks, the bible has not finished discovery.

## The No-Reference Path

Sometimes the user has no reference images. Do not invent a look from adjectives alone. Use the image tool to make the references:

1. Ask for one sentence of thematic intent (the paragraph is drafted later).
2. Generate three short direction tests with the same neutral subject (for example, a plain ceramic cup on a table), each with a different light, palette, and medium. Use the same tool the project will use.
3. Show the three outputs to the user. Ask which is closest, and what is wrong with each.
4. Adopt the chosen output as R01 (provenance: generated with the recorded prompt and parameters). Continue discovery with it as the first keeper.

Limit this to one round of three. More rounds usually mean discovery is stuck on taste, and the fix is a clearer thematic statement, not more generations.

## The Approval Gate

Before writing the full bible, show the user the derived invariants and the reference coverage. A list of 8 to 12 lines is enough:

```text
Derived invariants (confirm or correct):
- Medium: natural-light photography, 35mm film feel, light grain
- Key light: camera-left, 45 degrees, soft, neutral to cool
- Shadows: cool blue-grey, never black
- Palette: sand ground, spruce support, ember signal (one per image)
- Framing: subject in lower two-thirds, one third of frame clear
- Forbidden: studio high-key light, neon, text in images
Reference coverage: people (R01), products (R03), environments (R02). Missing: interiors.
```

This is the cheapest correction point. A wrong invariant found here costs a sentence. Found after the full bible is written and tested, it costs a rewrite and a new round of images.

## Discovery Output

Save the discovery results before drafting the bible so a context reset does not lose them. Write one file that holds:

- The intake answers, with defaults marked as assumptions.
- The reference table with IDs, provenance, and what each proves.
- The anti-reference table.
- The extraction table and the invariant list.
- Any conflict resolutions and their reasons.

This file becomes the source for sections 1 to 2 and 15 of the bible. Keep it out of the final bible unless the team wants the working notes.

## Handoff to Writing

When the approval gate passes, the drafting order is:

1. Thematic statement from the intake answers (section 1).
2. Purpose and use from question 1 (section 2).
3. Palette, light, lens, rendering, and materials from the invariants (sections 3 to 7).
4. Subject rules from question 7 and the keepers (section 8).
5. Typography, technical spec, composition, and detail from the intake (sections 9, 11 to 13).
6. Do-not-do list from the anti-references and hard constraints (section 14).
7. Reference set (section 15), anchors (section 16), and cross-context check (section 17).

Write the anchors last. They depend on the invariants being final, and an anchor written too early will be rewritten several times.

## Quick Checks Before Drafting

| Check | Pass condition |
|-------|----------------|
| Keepers cover every subject class | At least one keeper per class in question 7 |
| Every invariant has at least two keepers behind it | Count is 80 percent or more of keepers, or two minimum |
| Anti-references exist or the user declined | Recorded either way |
| Rights status recorded | Every keeper has provenance |
| No invariant rests on a single adjective | Each has a property and value |
| Conflicts resolved, not averaged | Each conflict has a logged decision |

## Sample Intake Exchange

A short exchange shows the intent of the intake order. The assistant asks the blocking questions first, batches the factual ones, and states assumptions for everything it infers.

```text
Assistant: Two things block the bible, so I'll ask them one at a time.
           Which 3 to 10 images already look right for this project? Links or files are fine.

User:      Here are five: a trail shot, a product on a wooden table, a backpack
           in a car trunk, and two interior shots.

Assistant: Thanks. Next blocking question: which subjects recur in the images?
           People, products, places, or a mix?

User:      Mostly products and trail scenes. Some people, but not often.

Assistant: Got it. These facts I'll batch into one message. Answer in one pass,
           or tell me to use the defaults:
           1. Channels and sizes: social square and wide banner (defaults used if blank)
           2. Image tools: GPT Image through the user's current tool (default)
           3. Brand colors or fonts: none stated, so I will derive from the references
           4. Anti-references: none yet (I will ask again after the first draft)
           5. Hard constraints: no real people's likeness (assumed; confirm)
```

The exchange gives the user three things they can act on: the blocking answers, a complete factual batch, and explicit assumptions they can correct. It avoids the open-ended "describe your style" prompt, which produces adjectives.

## Keeper Sufficiency Check

Before the attribute extraction, check that the keeper set is enough to draft a bible:

| Condition | Enough when |
|-----------|-------------|
| Count | 3 keepers for a one-off set; 6 or more for a full bible |
| Coverage | Every subject class from question 7 has at least one keeper |
| Variety | The keepers differ in framing and distance, not only subject |
| Agreement | At least half the keepers share a medium and a light direction |
| Provenance | Every keeper has a source and a rights status |

If agreement is under half, the set is probably two looks. Go to the conflict resolution steps before extraction, or split the project into multi-look sections.

## Common Discovery Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Starting with "describe your style" | Adjectives only; no enforceable rules | Ask for references first, then label them with adjectives |
| Accepting one keeper as a style | Bible copies one image's quirks | Require three keepers minimum; check variety |
| Skipping anti-references | Do-not-do list is generic | Ask once more after the first draft |
| Inferring the subject mix | Subject rules miss the main content | Ask question 7 directly; it is blocking |
| Mixing rights and style | A licensed image treated as free to copy | Record rights; style-only use is the lowest-risk case |
| Averaging conflicting keepers | Palette belongs to no reference | Resolve the conflict or split the look |
| Drafting before approval | A full bible rewritten after one correction | Run the approval gate first |

## Reference Cross-Links

- Section anatomy and what each section must decide: `bible-structure.md`
- Writing enforceable rules from the invariants: `visual-system-rules.md`
- Turning the bible into anchors and prompts: `tool-translation.md`
- Checking outputs against the bible after discovery: `consistency-and-drift.md`
