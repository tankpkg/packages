# Consistency and Drift

Sources: Makko (How to Write a Game Art Bible, 2026), OpenAI GPT Image prompting guide (2026), Midjourney Style Reference documentation (2026), Albers (Interaction of Color, 50th anniversary ed.), Wheeler (Designing Brand Identity, 5th ed.)

Covers: why generated images drift from a design bible, the prevention practices that stop it, a review rubric that scores each image against the bible, a drift diagnosis table, a correction strategy (edit, regenerate, composite, or revise the bible), and the golden-set protocol that catches drift when a model changes.

## Why Drift Happens

Drift is the gap that grows between the bible and the images as work accumulates. The makko.ai guide names three leaks between the page and the asset, and generators add a fourth.

| Leak | Mechanism | Example |
|------|-----------|---------|
| Interpretation | Prose rules mean different things to different people | "Warm, muted palette" produces two different looks |
| Recall | Nobody re-reads the bible before each asset | Week six images use a memory of the bible, not the bible |
| Anchor drift | New assets are anchored to the previous asset, not the bible | Each image is slightly more saturated than the last, and the error compounds |
| Tool change | The model or platform changes under the same prompt | Same anchor, new output after an update |

The first three leaks are fixed by the bible's enforceable form and the practices below. The fourth needs a golden set.

Anchor drift is the most dangerous leak because no single image looks wrong. Each step is small. The defense is to anchor to the approved reference set, not to the last output.

## Prevention Practices

| Practice | Why it works | Cost |
|----------|--------------|------|
| Paste the anchor verbatim, never retype it | Prevents paraphrase creep | Near zero |
| Anchor to approved references (section 15), not to the last image | Stops compounding drift | Keep the reference set current |
| Save parameters with every approved image | Makes the look reproducible | One metadata record per image |
| Keep a golden set of 3 to 5 approved images | Gives a fixed comparison for new prompts and new models | Maintain it when the bible changes |
| Put a preserve list on every edit | Prevents silent changes to the identity or geometry of the subject | A few lines per edit |
| Version the bible and log changes | Lets reviewers know which rules applied to which image | A dated entry per change |
| Run the cross-context check on one asset per batch | Catches rules that only work in one scene | One asset per batch |

## Review Rubric

Score every generated image against the bible. Use this rubric for approvals and for the golden set.

### Criteria

Each criterion scores 0, 1, or 2.

| # | Criterion | 0 | 1 | 2 |
|---|-----------|---|---|---|
| 1 | Medium matches | Wrong medium | Close but drifting | Medium matches the bible |
| 2 | Light direction and quality | Direction wrong or missing | Direction right, quality off | Direction, quality, and shadow color match |
| 3 | Palette roles | Signal or reserved color misused | Roles mostly right | Every color in its role, ground dominant |
| 4 | Lens and framing | Framing outside the stated range | Close to the framing rule | Subject share and headroom match |
| 5 | Materials and wear | Gloss or wear wrong for the subject | Finish right, wear off by a level | Finish and wear match the scale |
| 6 | Subject rules | Subject class rule broken (likeness, scale, geometry) | Rule mostly kept | Every subject rule kept |
| 7 | Text (if allowed) | Misspelled or extra text | Legible, placement off | Exact copy, placement and font match |
| 8 | Composition and negative space | Focal zone lost, margin violated | Margin close | Margin and focal zone match |
| 9 | Do-not-do list | Any item present | Not applicable to the item | No items present |
| 10 | Technical spec | Wrong size, missing alpha, wrong format | One value off | Size, alpha, format match |

### Hard Criteria

Criteria 6 (subject rules), 9 (do-not-do list), and 10 (technical spec) are hard. An image scoring 0 on any hard criterion fails regardless of total.

### Pass Rule

An image passes when no hard criterion scores 0, every hard criterion scores 2, and the total is 16 or more of 20. The thresholds are a working convention; the team may tune them, but should record the change in the bible's change log.

### Scoring Practice

- Score with the bible open, not from memory.
- Score each image once in a fixed order. Re-scoring after a reroll is a new score, not an update.
- Record the score next to the image's parameters (see `delivery-and-maintenance.md`).
- Write one line of reason for every criterion scored 0 or 1.

## Consistency Test Protocol

Use this protocol to measure whether the anchor holds, before the team trusts it on a live batch:

1. Choose three subjects from the bible's subject classes (for example, a person, a product, an environment).
2. Generate each subject with the anchor, twice, using different seeds or rerolls. Record parameters.
3. Lay the six images side by side at the same size, in a grid, on a neutral background.
4. Score each image with the rubric.
5. Compare the two images of the same subject, and then compare across subjects.

Read the results as follows:

| Observation | Meaning | Next step |
|-------------|---------|-----------|
| Same subject, two seeds, different palette | Anchor under-specifies the palette | Add palette roles or saturation band |
| Different subjects, same palette, different light | Light rule is adjective-based | Replace with direction, quality, and temperature |
| All six share the look, one scores 0 on subject rules | Subject rule missing or unclear | Fix the subject class rule, not the anchor |
| All six share the look, all score under 16 | Anchor is correct but the rubric is strict | Check the rubric criteria against the bible text |

Side-by-side grids reveal drift that single images hide. Compare images at the same display size; a large image makes a palette shift look bigger than it is.

## Drift Diagnosis

Use this table when an image or a batch looks off. Find the symptom, check the likely cause, apply the fix.

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Palette warms gradually over weeks | Anchor retyped with "warm" or paraphrased | Restore the anchor verbatim from the bible; add palette roles |
| Each new image is more saturated | Anchored to the last output, not the reference set | Re-anchor to approved references; check saturation band |
| Light direction flips between images | Light described as an adjective ("moody") | Replace with direction, hardness, temperature, shadow color |
| Shadows go black | Shadow color not stated | Add shadow color; forbid pure black |
| Face or product shape changes across edits | Repeated edits without a preserve list | Use the identity-preservation pattern; composite the approved region |
| Text misspelled or altered | Long text, small size, text not quoted | Quote, shorten, raise quality to `high`, check after each generation |
| Midjourney look changed after a platform update | Code used without its `--sv` value, or a pre-June 2025 code on a newer version | Record `--sv` with the code; use `--sv 4` for older codes, or switch to V6 |
| Images look generic | Anchor describes the category, not the look | Add physical properties: material, finish, light, lens |
| Clutter creeps into frames | No negative-space rule | Add margin and focal-zone numbers |
| Same prompt, new output after a model update | Tool or model change | Run the golden set before adopting the new model |
| Subject wrong scale against environment | No scale references | Add scale references to the environment rules |
| Two artists' outputs disagree on mood | Mood stated as an adjective | Rewrite the mood as properties; add a golden-set example |

## Correcting an Off-Model Image

Choose the correction by what is wrong. Do not default to regeneration.

| Problem | Correction | Why |
|---------|------------|-----|
| One local detail is wrong (a color, a stray object) | Edit with a preserve list | Keeps the rest of the approved image intact |
| The global palette or light is wrong | Regenerate from the anchor and approved references | Editing a whole-image look compounds drift |
| A region must stay pixel-identical | Composite the approved edit into the original | Prompting alone does not guarantee pixel identity (per the OpenAI guide) |
| Text is wrong | Regenerate the text-bearing element, or set the type in a design tool | Text edits are the least reliable |
| The same failure repeats twice | Revise the bible rule, not the prompt | A repeated failure means the rule is unclear or missing |

### The Two-Failure Rule

If the same failure appears in two images from different prompts, stop prompting around it. The fault is in the bible: a missing rule, an ambiguous value, or a conflict between two rules. Fix the bible, bump its version, and re-run the golden set. Prompt-level fixes for a bible-level problem create the anchor drift described above.

## Iteration Discipline

- Change one thing per iteration. The GPT Image guide recommends refining one thing at a time and inspecting each result. Changing light, palette, and framing in one step makes the cause of any improvement or regression unknowable.
- Compare each new output against the last passing image, not against memory.
- Log each change: what changed, why, and what result it produced.
- Generate several variants per subject, score them, and pick the best. Do not tune the anchor per image to rescue one output. Per-image tuning is how anchors fork.

## Golden Set and Model Updates

A golden set is 3 to 5 approved images, each with its prompt, parameters, reference IDs, and rubric scores. It is the regression suite for the bible.

Use it when:

- A new model version is released, or the team considers switching models (for example, from Flare to Sunburst, or to a new Nano Banana variant).
- The bible's version changes.
- A new tool joins the workflow.
- Batch results start to look off and the cause is unclear.

Protocol:

1. Re-generate each golden-set prompt with the candidate model or bible version.
2. Score each new image with the rubric, side by side with its approved original.
3. Pass the candidate only if every golden image still passes and no hard criterion drops.
4. Record the result in the change log, including any image that now fails and why.

A model change that passes the golden set is safe to adopt. A change that fails should be rejected, or the anchor adjusted and the golden set re-run.

## Batch Review

For a batch of images:

| Step | Action |
|------|--------|
| 1 | Generate the batch from one anchor version |
| 2 | Lay out the batch in a grid at one display size |
| 3 | Scan for outliers: one image that stands out in palette, light, or framing |
| 4 | Score the outliers and a random sample of the rest |
| 5 | Regenerate or correct the failures using the correction table |
| 6 | Approve the batch only when the sample passes the rubric |

Scan the grid before scoring each image. Outliers are visible in a grid and invisible in a list.

## Multi-Person and Character Consistency

Consistency of a specific recurring person or character is a separate problem. Per-character sheets, pose sets, and expression sets belong to the character-creator skill, which produces the character bible. This skill owns the project-wide look. When a character appears in the project's images, the design bible governs the palette, light, and medium; the character sheet governs the face, costume, and proportions. Name the character sheet in the subject rules and reference set.

## Diagnosing Without a Tool

When the team lacks a measurement tool, use these checks:

| Check | How |
|-------|-----|
| Palette | Eyedropper on the focal zone and the ground, compare hex to the bible |
| Light direction | Note which side highlights and shadows fall on |
| Shadow color | Sample a shadow area; it should not read as pure black |
| Framing | Count the frame fraction the subject occupies |
| Text | Zoom to 200 percent and read every word |

The bundled `scripts/check_bible.py` checks the bible itself, not images. Image checks are manual, or use a color tool the team already has.

## Worked Scoring Example

A generated product image for the fictional brand in `tool-translation.md` is scored against the bible. The reviewer records one reason for every criterion below 2.

| # | Criterion | Score | Reason |
|---|-----------|-------|--------|
| 1 | Medium matches | 2 | Reads as a 35mm film photograph, light grain |
| 2 | Light direction and quality | 1 | Key from camera-left, correct; shadows read neutral grey, not blue-grey |
| 3 | Palette roles | 2 | Sand ground dominant, spruce on the strap, one ember accent on the buckle |
| 4 | Lens and framing | 2 | Subject fills the lower two-thirds, top third clear |
| 5 | Materials and wear | 1 | Strap finish correct; wear reads as level 1, the default is level 2 |
| 6 | Subject rules | 2 | Product geometry matches the reference image R03 |
| 7 | Text (if allowed) | 2 | No text; none allowed in this set |
| 8 | Composition and negative space | 2 | Margin and focal zone match |
| 9 | Do-not-do list | 2 | None present |
| 10 | Technical spec | 2 | 1536x1024, opaque background, PNG |

Total: 18 of 20. Hard criteria (6, 9, 10) all score 2, so the image passes. The two 1s are recorded for the next batch: the shadow line in the light rule needs a sharper test ("shadow pixels read blue-grey, saturation at least 8 percent"), and the wear default needs its level restated in the prompt.

The example shows the rubric's purpose. A pass is not a claim that the image is perfect; it is a claim that no hard rule broke and that the soft rules are measurable enough to improve.

## Reading Scores Over Batches

Single scores hide trends. Track the average score for each criterion across batches, in the generation log (see `delivery-and-maintenance.md`).

| Pattern across three batches | Meaning | Action |
|------------------------------|---------|--------|
| One criterion falls steadily | Anchor drift on that property | Restore the anchor for that slot; check for paraphrase |
| One criterion stays at 1 across batches | Rule is ambiguous, not drifting | Rewrite the rule with a test, as in the worked example |
| Criteria all rise after a bible change | The change worked | Keep it; add to the change log |
| Hard criterion dips once and recovers | Single bad generation | Log it; no bible change |
| Total rises while one soft criterion's average falls | Reviewers are trading points between criteria | Recalibrate reviewers (see below) |

A criterion that averages below 1.5 across a batch is the first candidate for a bible revision. Revise the rule before changing the prompt.

## Reviewer Calibration

Two reviewers scoring the same image will disagree. That is normal. Persistent disagreement on one criterion means the rule is unclear.

Calibration protocol:

1. Pick five images from the golden set, plus one image that is known to fail.
2. Each reviewer scores all six independently, with the bible open.
3. Compare the scores criterion by criterion.
4. Any criterion where the reviewers differ by more than one point needs a discussion. The discussion ends with one of two outcomes: the rule is rewritten with a test, or the reviewers agree on the reading and write it into the bible's do-not-do list or worked example.

Run calibration when a new reviewer joins, after any major bible change, and at least once per quarter. Record the result in the change log.

Calibration works because it turns subjective scoring into a rule-quality signal. A rule that two experienced reviewers cannot score the same way is not a rule the generator can follow either.

## Batch Failure Triage

When a batch fails, sort the failures before fixing anything:

| Failure type | Example | Fix location |
|--------------|---------|--------------|
| Generation noise | One image off, siblings fine | Reroll or regenerate that image |
| Subject problem | Product geometry wrong across the batch | Subject rules and the reference set |
| Anchor problem | Palette wrong across the batch | Anchor for that tool |
| Bible problem | Two rules conflict, or a rule is untestable | Bible revision with version bump |
| Tool problem | Batch was fine before a model change | Golden set, then model rollback or anchor change |

Fixing at the wrong level is the most expensive mistake in this workflow. A bible problem fixed in the prompt comes back in the next batch, and a generation-noise failure fixed in the bible loosens a rule that was working.

## Reference Cross-Links

- Bible sections referenced by the rubric: `bible-structure.md`
- Rules the rubric checks, with vocabulary: `visual-system-rules.md`
- Anchors and per-tool corrections: `tool-translation.md`
- Storing scores, parameters, and the golden set: `delivery-and-maintenance.md`
