# Delivery and Maintenance

Sources: Wheeler (Designing Brand Identity, 5th ed., brand standards and guidelines), Makko (How to Write a Game Art Bible, 2026), OpenAI GPT Image prompting guide (2026), Midjourney Style Reference documentation (2026)

Covers: the files a design bible project produces, where to store them so coding agents such as Codex pick them up, how to link the bible from AGENTS.md without copying it there, versioning and change control, per-image metadata, sharing with non-engineers, and the handoff checklist.

## Deliverables

A complete design bible project has a small set of files. Only the first is required for a one-off set; the rest are required once images are generated at scale.

| Deliverable | Path (suggested) | Purpose | Required |
|-------------|------------------|---------|----------|
| Design bible | `docs/design/DESIGN-BIBLE.md` | The rules, sections 1 to 17 | Yes |
| Reference set | `docs/design/references/` with an index file | Approved and rejected images with IDs | Yes, once generation starts |
| Reference index | `docs/design/references/INDEX.md` | ID, file, source, rights, what it proves | Yes with the reference set |
| Golden set | `docs/design/golden/` | Approved images, prompts, parameters, rubric scores | Yes for model or bible changes |
| Generation log | `docs/design/generation-log.csv` or a sidecar per image | Parameters and scores per image | Recommended |
| Change log | Inside the bible, section 18 | Dated version history | Yes |

Paths are suggestions. Keep one canonical bible. Put it where the people who generate images will look, and where the coding agent that edits the repository will read it.

## Where to Keep It

### In a Repository

When the project is a repository and coding agents such as Codex, Claude Code, or Cursor work in it, keep the bible in the repository. Agents read repository files, so the bible stays visible during work on any asset-related code, prompt, or documentation.

Link it from the repository's agent instructions, not by copying it there. The pointer should name the file, name the anchor section, and state the one rule an agent must follow: use the anchor verbatim.

Example section for AGENTS.md (or the tool's equivalent instruction file):

```markdown
## Image generation

When generating or editing project images, follow `docs/design/DESIGN-BIBLE.md`.
Paste the style anchor for the tool from section 16 verbatim into every prompt.
Do not restate palette or light values from memory. Check outputs against the
rubric in `docs/design/golden/` before proposing an image for review.
```

This keeps the agent instructions short, which matters because the bible is long and loads in full only when needed. The agents-md skill covers the instruction file formats for each tool.

### Outside a Repository

When no repository exists, keep the bible as a Markdown file in a shared drive, or as a page in the team's document tool. Keep exactly one canonical copy. Copies in chat messages and slide decks go stale within weeks.

### Shared Document Tools

If the team uses a shared document tool, the bible can live there. Keep the reference images and the anchors as attachments or embedded blocks, not as links only: a link that breaks removes the anchor's source. Note the tool and the page ID in the bible's header so any future editor finds the canonical version.

## Bible Header

Every bible starts with a header that a tool can read and a reviewer can check at a glance:

```markdown
# Harbor and Pine Design Bible

Version: 1.2.0
Status: approved
Owner: Creative lead
Tools: GPT Image 2.5 Sunburst (finals), GPT Image 2.5 Flare (drafts)
Last updated: 2026-10-21
```

The version is required. Every generated image records the version it used. A reviewer who sees an image without a version cannot judge it against the right rules.

## Versioning

Use three levels, in the spirit of semantic versioning:

| Level | Change | Example |
|-------|--------|---------|
| Major | Palette roles, medium, or do-not-do list changes in a way that alters existing images | Switching from photo to illustration |
| Minor | New subject class, new look within the same medium, new tool anchor | Adding an environment class with its own scale references |
| Patch | Wording fixes that do not change the look | Clarifying a shadow color value |

A major change does not invalidate old images. It means old images are off-model for the new bible. Mark them rather than deleting them, so the team can see the look that changed.

## Change Control

Every change follows the same steps:

1. Propose the change in writing with the reason and the expected visual effect.
2. Generate a test set with the change applied to the golden-set prompts.
3. Score the test set with the rubric, side by side with the approved golden set.
4. Approve or reject. Name the approver in the change log.
5. Publish the new version: update the header, add the change log entry, and update the anchors.
6. Re-anchor any active batches to the new version, or finish them on the old version and say so.

Skipping step 2 is the most common cause of silent drift. A change that looks right in the bible often looks different in the output.

### Change Log Entry

```markdown
### 1.2.0 (2026-10-21)
- Changed: shadow color from cool grey to cool blue-grey, value unchanged.
- Reason: outdoor shots read too neutral on mobile screens.
- Test: golden set re-run, 5 of 5 pass, rubric totals 17 to 19.
- Approved by: creative lead.
- Images affected: none approved on the old value; batch 14 re-generated.
```

## Per-Image Metadata

Each approved image needs enough metadata to regenerate it or explain why it looks the way it does. Record:

| Field | Example |
|-------|---------|
| Image ID | `IMG-0412` |
| Bible version | `1.2.0` |
| Tool and model | `GPT Image`, `gpt-image-2.5-sunburst` |
| Parameters | `size=1536x1024`, `quality=high`, `background=opaque` |
| Anchor ID | `gpt-anchor-v3` |
| Reference IDs | `R01, R03` |
| Seed or style code | `--sref 3187264` with `--sv 6` (Midjourney) or seed value (open pipeline) |
| Subject line | One line, as sent |
| Rubric total and hard scores | `18/20`, hard criteria `2, 2, 2` |
| Reviewer and date | Name and date |

Keep the metadata in a CSV or a sidecar file next to the image. A missing field makes the image hard to regenerate, and an image that cannot be regenerated cannot be fixed later without a new look.

### Logging Format

```csv
image_id,bible_version,tool,model,size,quality,anchor_id,references,seed_or_code,rubric_total,hard_scores,reviewer,date
IMG-0412,1.2.0,gpt-image,gpt-image-2.5-sunburst,1536x1024,high,gpt-anchor-v3,"R01,R03",,18,"2,2,2",creative lead,2026-10-21
```

## Asset Naming

Use a predictable pattern that encodes the project, subject, version, and ID:

```text
{project}_{subject-class}_{bible-version}_{image-id}.{ext}
harbor-pine_product_v1.2.0_IMG-0412.png
```

The bible's technical spec (section 11) defines the pattern. The version in the file name lets a reviewer see which rules applied without opening the metadata.

## Reference Index

The reference index is a table, not a folder listing. Each row names the reference, its source, its rights status, and what it proves:

| ID | File | Source | Rights | Proves |
|----|------|--------|--------|--------|
| R01 | `refs/R01-hand-strap.jpg` | Team photo, shoot 2026-03 | Owned | Light direction, wear level 2 |
| R02 | `refs/R02-trail-dusk.jpg` | Licensed stock, ID on file | Licensed for reference use | Environment scale, cool shadows |
| A01 | `refs/A01-studio-highkey.jpg` | Competitor catalog | Reference only, not used as style | High-key light is out of bounds |

Keep anti-references in the same index with the `A` prefix. The index is the place a new team member looks first.

## Sharing

### With Engineers and Agents

Markdown is the default. It diffs cleanly, it loads into agent context, and it lives beside the code. Keep the reference images out of the Markdown file and link them by path.

### With Non-Technical Reviewers

Non-technical reviewers need the reference images next to the rules. Offer an HTML page that renders the bible with the references inline. Generate it from the Markdown so there is still one source. Keep the page readable on a phone: reviewers often check images on mobile.

Do not keep a separate, hand-edited copy for reviewers. Two copies diverge within a month.

### Exports

If other tools need the anchors (a team's image pipeline, a plugin, or a generator's configuration), export them as plain text files, one per tool, generated from section 16. Put a header line in each export naming the bible version it came from. Re-export on every version change.

## Ownership and Approval

Name three roles in the header:

| Role | Responsibility |
|------|----------------|
| Owner | Keeps the bible current and approves changes |
| Generator | Produces images with the anchors and logs metadata |
| Reviewer | Scores images with the rubric and approves batches |

One person can hold more than one role on a small team. The roles must still be named, so a change has an approver and a batch has a reviewer.

## Handoff Checklist

Use this checklist before the bible is marked approved and handed to the people who will generate images:

| Check | Pass |
|-------|------|
| Header complete, version set | Yes |
| All required sections present | `scripts/check_bible.py` exits with no errors |
| Palette has roles, hex, and forbidden uses | Checked |
| Light has direction, quality, temperature, shadow color | Checked |
| Subject rules include scale references | Checked |
| Do-not-do list has 6 to 12 reasoned items | Checked |
| Reference index complete with rights status | Checked |
| Anchors built for every tool in use | One block per tool |
| Golden set created: 3 to 5 approved images with metadata | Checked |
| Cross-context check run on at least one asset | Recorded |
| Pointer added to repository agent instructions, if a repository exists | Checked |
| Change log started with the first version | Checked |
| Owner, generator, and reviewer named | Checked |

## Maintenance Rhythm

| Cadence | Action |
|---------|--------|
| Each batch | Score the sample, log metadata, note any new failure type |
| Monthly | Review the change log and the drift diagnosis table against recent failures |
| On every tool or model change | Re-run the golden set before adopting the change |
| On every new subject class | Add subject rules, reference IDs, and at least one golden image |
| Quarterly | Retire references that no longer match the look; mark them as retired, do not delete |

Retire references rather than deleting them. A retired reference explains a rule that a future team member may question.

## Common Delivery Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Bible copied into agent instructions | Instructions balloon; two copies diverge | Point to the bible; keep only the rule in instructions |
| Anchors copied from memory | Anchors differ across people | Export anchors from section 16 only |
| No version on images | Impossible to tell which rules applied | Require the version in the file name and metadata |
| Reference links only | Anchor source disappears when a link breaks | Store the image in the reference folder |
| Silent model switch | Look changes with no change-log entry | Golden set and change log for every model switch |
| Metadata skipped | Good images cannot be regenerated | Make the metadata row part of the approval step |

## Onboarding a New Generator

A new person or agent who will generate images follows the same steps every time:

| Step | Action | Done when |
|------|--------|-----------|
| 1 | Read the bible header and the thematic statement | They can state the version and the intent |
| 2 | Read the do-not-do list | They can name three forbidden items |
| 3 | Copy the anchor for their tool from section 16 | Their prompt starts with the anchor, verbatim |
| 4 | Generate one golden-set prompt | Output compares to the approved golden image |
| 5 | Score it with the rubric | Their score is within two points of the reviewer's |
| 6 | Log the metadata for that image | The row is complete, including the version |

Step 4 is the important one. A generator who reproduces a golden image from the anchor has learned the look. A generator who cannot reproduce one has a question for the owner, and the answer usually reveals an ambiguous rule.

## Stakeholder Review

Stakeholders who did not write the bible often review images against it. Give them three things, in this order:

1. The thematic statement and the do-not-do list, so they judge against the intent and the boundaries.
2. A grid of the batch at one display size, with image IDs visible.
3. The rubric, with the criteria they are asked to judge.

Ask stakeholders to judge the criteria they can see (usually medium, mood, framing, and subject), and leave technical criteria (alpha, size, parameters) to the generator. A stakeholder who scores the shadow color on a phone screen will disagree with a reviewer on a calibrated monitor. Record which display the review used when it matters.

When a stakeholder requests a change that the bible does not cover, treat it as a change request, not a prompt tweak. Follow the change control steps, even when the change is small.

## Retiring a Bible Version

Retire a version when a major change replaces it. Retirement is a record, not a deletion:

| Step | Action |
|------|--------|
| 1 | Mark the old version as superseded in the header, with a link to the new version |
| 2 | Keep the old file in the repository history, or in an archive folder if it is a document tool |
| 3 | Mark images generated on the old version with their version in the metadata; do not re-tag them |
| 4 | Decide which old images stay in use, and record the decision in the change log |
| 5 | Remove the old anchors from the export folder, and re-export the new ones |

Images generated on a retired version stay valid for their original context. The new bible governs new images. Old images used in a live channel are either replaced or explicitly accepted, and that decision is logged.

## Reference Cross-Links

- The bible sections this project produces: `bible-structure.md`
- Discovery and reference curation that feeds the reference index: `discovery-and-references.md`
- Anchors and parameters recorded in metadata: `tool-translation.md`
- Rubric scores and golden set protocol: `consistency-and-drift.md`
