# Document Navigation and Layout

Sources: Google Technical Writing Courses, Steve Krug (Don't Make Me Think), Jeff Johnson (Designing with the Mind in Mind), Robin Williams (The Non-Designer's Design Book), W3C Web Content Accessibility Guidelines, and task-centered documentation practice.

Covers: Arrange technical content after its purpose is defined. Choose structures by document type, support scanning, close reading, and lookup, create semantic chunks, select headings and content forms, and test navigation, responsive behavior, accessibility, and task completion.

## Structure Follows Purpose

Define the reader, situation, and outcome before arranging the page. Structure cannot compensate for an unclear purpose.

Write a one-sentence contract:

> This runbook helps an on-call engineer restore queue processing without duplicating jobs.

Use that contract to choose the document type, opening, sequence, navigation, and depth. Do not begin with a universal page template.

Ask:

- What brought the reader here?
- Will they scan, learn, decide, execute, or look up a fact?
- Must they follow a sequence?
- Which information is safety-critical?
- Which paths apply only to some readers?
- Will they return repeatedly or read once?
- Where and on what device will they use the document?

Let the strongest use case govern the primary path. Support secondary use cases without making every reader traverse them.

## Choose a Structure by Document Type

Different documents create different reading contracts.

| Document type | Primary reader intent | Useful structure |
| --- | --- | --- |
| Tutorial | Learn by completing a guided experience | Goal, setup, staged actions, checkpoints, reflection |
| How-to guide | Complete a known task | Preconditions, task steps, verification, recovery |
| Concept explanation | Build a mental model | Governing idea, parts, relationships, example, implications |
| Reference | Retrieve exact facts | Scope, stable categories, searchable entries, constraints |
| Decision record | Understand a choice | Context, decision, alternatives, consequences, status |
| Proposal | Decide whether to act | Recommendation, value, evidence, tradeoffs, requested decision |
| Runbook | Respond safely under pressure | Trigger, diagnosis, safe actions, checks, escalation, rollback |
| Troubleshooting guide | Recover from a symptom | Symptom, discriminating checks, causes, fixes, verification |
| Release note | Learn what changed and what to do | Change, affected users, impact, required action, references |
| API guide | Integrate correctly | Mental model, authentication, common flow, errors, linked reference |

Do not force one document to serve incompatible intents. Split a tutorial from exhaustive reference when the combined page makes both harder to use. Keep related documents connected with explicit links and shared terminology.

### Safety-Critical Runbook Blueprint

Use one visible operational spine:

1. State purpose, authority, roles, and the exact trigger.
2. Put the irreversible hazard and governing safety invariant first.
3. List prerequisites, required evidence, and explicit stop conditions.
4. Separate phases with decision gates and named approvers.
5. For every consequential action, show expected state and failure response.
6. Distinguish rollback before commitment from recovery or failback afterward.
7. Define escalation thresholds and who owns the decision.
8. Verify the system invariant, user-visible result, monitoring, and follow-up state.

Provide a concise fast path and an expanded path when expertise varies. Keep hazards, stop conditions, authority, and verification identical in both.

## Support Three Reading Modes

Design for movement between scanning, close reading, and lookup.

### Scan Mode

Help readers decide relevance and locate a path. Expose descriptive headings, meaningful lead sentences, visible steps, and recognizable terms.

### Close-Read Mode

Preserve coherent prose, reasoning, examples, and qualifications. Avoid fragmenting every thought into labels and bullets.

### Lookup Mode

Provide stable names, predictable categories, searchable literal strings, anchors, and compact reference forms.

Readers switch modes within one session. An engineer may scan for the right error, close-read its explanation, then look up a parameter. Keep those transitions easy.

Test each mode separately. A page can scan well but fail to explain, or explain well but make a known fact difficult to retrieve.

## Design the First View

Use the first view to establish orientation, relevance, and a plausible next move.

Include only what this document needs:

- A specific title
- A concise statement of purpose or result
- A critical prerequisite or warning
- The main action, recommendation, or navigation choice
- Context needed to interpret what follows

Do not require a summary block on every page. A short reference entry may need only a precise title and signature. A proposal may need its recommendation first. A tutorial may need a goal and setup. A runbook may need an emergency warning before context.

Avoid ceremonial openings such as "This document will discuss." Use the space to clarify scope or help the reader begin.

## Create Semantic Chunks

Group content by meaning and task, not by a fixed item count.

A chunk should answer one recognizable question or support one coherent action. Its boundaries should help readers predict what belongs together.

Useful chunk boundaries include:

- A change in reader goal
- A new stage in a process
- A switch from rule to exception
- A distinct option or platform path
- A move from explanation to execution
- A new lookup category

Keep tightly coupled information together even when the section becomes long. Split a section when readers need different labels, can skip one part independently, or would benefit from a direct link to one part.

Do not treat memory research as a mandate for a universal number of sections or list items. Complexity, familiarity, and task context determine useful grouping.

## Make Headings Carry Information Scent

Write headings that predict the content and help readers choose a path.

Weak headings:

- Overview
- Details
- Other
- Advanced

Stronger headings:

- How Lease Revocation Prevents Duplicate Writes
- Rotate Credentials Without Interrupting Traffic
- Errors Caused by an Expired Signing Key
- Optional Controls for Regulated Workloads

Use a consistent hierarchy. Do not skip levels for visual styling. Let heading levels express containment, then use CSS to control appearance.

Prefer headings that match reader vocabulary. Include literal product names, error text, commands, or concepts when readers are likely to search for them.

Apply the heading-only test: scan the headings in order and determine whether they reveal the page's scope and path. Do not demand that headings reproduce the entire argument; require them to make navigation predictable.

## Select Prose, Lists, or Tables Deliberately

Choose the form that matches the relationship among ideas.

| Content relationship | Preferred form |
| --- | --- |
| Reasoning, causality, or narrative | Prose |
| Ordered actions or ranked sequence | Numbered list |
| Parallel choices or attributes | Bulleted list |
| Comparison across shared dimensions | Table |
| Term-to-definition lookup | Definition list or compact reference entries |
| Branching decision | Decision table, flowchart, or conditional subsections |
| Spatial or system relationship | Diagram with text alternative |

Keep connected reasoning in prose. Lists expose parallelism but can hide causality and qualification.

Use numbered lists only when order matters or when readers must refer to step numbers. Use bullets when items are peers and sequence is irrelevant.

Use tables when readers compare cells across rows or columns. Avoid tables for long narrative text, sequential procedures, or content that becomes unusable on narrow screens.

Give each list a grammatical lead-in. Keep list items parallel enough that readers can compare them without reinterpreting the syntax.

## Sequence Procedures Around the Task

Place prerequisites before the first step, but include only conditions that must be true before the reader begins.

Distinguish prerequisite types:

| Type | Example |
| --- | --- |
| Access | Permission to deploy the service |
| Environment | CLI connected to the production project |
| State | Migration completed in the primary region |
| Knowledge | Familiarity with the service's traffic model |
| Input | Revision name and rollback target |

Move optional preparation into the relevant branch instead of blocking all readers with it.

For each consequential step, consider four elements:

1. Action: what the reader does.
2. Context: where or under which condition.
3. Result: what should become visible.
4. Recovery: what to do when the result differs.

Place verification near the action it verifies. Do not collect all expected results at the distant end of a long procedure.

Separate alternative paths before their steps diverge. Label the choice with the condition that determines it, such as "If traffic is already split" rather than "Option B."

## Use Callouts for Interruptions With Consequence

Reserve callouts for content that must stand apart from the main flow.

| Callout purpose | Use when |
| --- | --- |
| Note | Context helps interpretation but does not alter the action |
| Tip | An optional technique improves efficiency or quality |
| Warning | A plausible action can cause loss, exposure, or difficult recovery |
| Important | A condition changes whether the procedure succeeds |
| Example | A concrete case benefits from visual separation |

Label callouts with words, not color or icons alone. State the consequence before elaboration in warnings.

Place a warning before the hazardous action. Keep a prerequisite in the prerequisite flow rather than disguising it as a callout.

Avoid stacking callouts. If several adjacent notices are essential, revise the main structure so the information becomes part of the task path.

Use this accessible HTML pattern when custom markup is appropriate:

```html
<aside class="callout callout-warning" aria-labelledby="delete-warning">
  <h3 id="delete-warning">Warning: deletion cannot be undone</h3>
  <p>Export the audit records before removing the workspace.</p>
</aside>
```

## Present Code Samples According to Purpose

Decide what each sample demonstrates.

| Sample purpose | Include |
| --- | --- |
| Command to execute | Exact command, required substitutions, expected signal |
| Focused API pattern | Relevant context and omitted-code markers |
| Complete starter | Imports, setup, execution, and dependency versions |
| Configuration fragment | File location, surrounding key path, valid syntax |
| Diagnostic output | Command that produced it and lines that matter |
| Concept illustration | Minimal code plus an explicit non-production label |

Do not require every code block to run independently. A focused fragment can explain an idea more clearly than a complete application. Mark omissions and dependencies so readers understand the boundary.

Annotate fenced blocks with the language when supported. Identify the file or shell context when ambiguity is likely.

Keep explanations beside the relevant lines. Highlight sparingly and provide a text explanation; do not depend on color alone.

Show expected output when it helps readers verify success or distinguish states. Omit predictable output that adds noise.

Test executable samples in the environment they claim to support. Treat illustrative pseudocode as illustration, not as a tested command.

## Add Tables of Contents Conditionally

Use a table of contents when it reduces navigation cost.

Add one when readers are likely to:

- Jump among independent sections
- Revisit the page as reference
- Share links to subsections
- Encounter a long or branching page
- Need a quick map of unfamiliar territory

Omit one when the page is short, strictly sequential, or already has a compact local navigation system.

Keep TOC labels synchronized with headings. Link only to destinations worth choosing independently. Avoid a TOC that is nearly as long as the content it precedes.

Use a local mini-TOC for a dense section when a page-level TOC would not help.

## Build Links That Preserve Context

Write link text that predicts the destination or action.

Prefer:

> Review the `Token rotation failure modes` section in the product documentation.

Avoid:

> For more information, open the related page.

Link at the point of need. Do not interrupt every term with a link if the destination is optional and the repeated visual noise harms reading.

Distinguish related purposes:

- Prerequisite link: read or complete before proceeding
- Supporting link: consult for deeper explanation
- Reference link: verify exact syntax or values
- Next-step link: continue a workflow

Preserve stable anchors for frequently shared sections. Check internal and external links as part of maintenance.

## Apply Progressive Disclosure Carefully

Keep the primary path visible. Hide only optional depth that readers can identify accurately from its label.

Good candidates for disclosure controls include verbose traces, platform-specific variants, background derivations, and uncommon edge cases.

Poor candidates include safety warnings, required steps, core definitions, and information readers do not know they need.

Use native controls when possible:

```html
<details>
  <summary>Show the full timeout trace</summary>
  <pre><code>...</code></pre>
</details>
```

Make the summary describe the hidden content. Ensure controls work by keyboard, expose state to assistive technology, and remain understandable when printing or exporting.

Use tabs only for genuinely parallel paths. Keep shared steps outside tabs, use persistent labels, and ensure each path can be linked and copied without losing context.

## Use Visual Design to Reinforce Relationships

Retain four adaptable principles from Robin Williams:

| Principle | Apply it by |
| --- | --- |
| Contrast | Making heading, body, code, and warning roles visibly distinct |
| Repetition | Reusing patterns for the same semantic role |
| Alignment | Placing elements on a coherent visual axis |
| Proximity | Keeping labels, examples, captions, and consequences near what they describe |

Do not convert these principles into fixed whitespace percentages or decorative rules. Evaluate whether the layout reveals grouping, priority, and sequence.

Use whitespace to separate semantic groups. Reduce spacing inside a group and increase it across a boundary. Maintain enough density for lookup-heavy pages without turning them into an undifferentiated wall.

Keep emphasis scarce and consistent. If bold, color, borders, and callouts all compete, simplify the hierarchy.

## Design for Responsive Reading

Test the actual document at narrow and wide widths, with zoom, and with increased text size.

Use flexible patterns:

- Set media with responsive dimensions and preserve aspect ratios.
- Give SVGs a `viewBox` and meaningful text alternatives.
- Allow code blocks to scroll without shrinking text into illegibility.
- Wrap wide tables in a labeled scroll region or provide a stacked alternative.
- Keep controls large enough to operate by touch and keyboard.
- Avoid layouts that depend on hover or precise pointing.
- Prevent side navigation from obscuring the main reading path.

Do not assume wrapping code is always wrong or always right. Preserve significant whitespace and long tokens where wrapping would alter meaning; offer line wrapping where it improves reading without corrupting the sample.

Ensure anchor navigation does not hide headings beneath sticky headers.

## Build Accessibility Into Structure

Use semantic HTML before adding ARIA.

- Provide one descriptive page title and a logical heading hierarchy.
- Use real lists for lists and real tables for tabular relationships.
- Associate table headers with their data cells.
- Give images and diagrams alternatives that convey their purpose.
- Keep link text meaningful outside its surrounding sentence.
- Preserve visible keyboard focus.
- Avoid conveying meaning through color, position, or shape alone.
- Identify the language of the page and unusual language changes.
- Support reflow and text enlargement without loss of content or function.

Write diagram alternatives at the level the task requires. A decorative image may need empty alternative text. A system diagram may need a concise summary plus a structured description of nodes, direction, and exceptions.

Check exported PDF and print views when readers rely on them. Interactive disclosure, sticky navigation, and color-coded states may disappear outside the browser.

## Strengthen Information Scent

Give readers cues that accurately predict where a path leads.

Use task language in navigation labels. Distinguish "Configure retries" from "Retry behavior" when one destination is procedural and the other conceptual.

Place high-value choices where readers expect them. Keep terminology aligned across page titles, navigation, search results, and in-page headings.

Avoid vague clusters such as "Resources," "Learn more," and "Miscellaneous" when specific labels are possible.

Cross-link sibling paths when readers commonly arrive at the wrong one. Explain the distinction briefly:

> To retry a failed job, use this runbook. To change automatic retry policy, open the `Configure retry limits` guide.

## Test the First View

Show representative readers only the initial viewport or rendered opening, without explaining it.

Ask:

- What is this document for?
- Who is it for?
- What would you do next?
- What risk or prerequisite is visible?
- Where would you go for your specific case?

Do not impose a universal time limit. Observe whether readers orient confidently under realistic conditions. Record incorrect interpretations, not merely speed.

Revise the title, lead, labels, or priority when readers choose the wrong path. Do not add more elements automatically; often the fix is to remove competing signals.

## Run Task and Retrieval Tests

Give readers realistic goals and let the document carry the interaction.

For a task test, observe whether they can:

1. Choose the correct path.
2. Satisfy the prerequisites.
3. Complete the actions in order.
4. Recognize success or failure.
5. Recover from a plausible problem.

For a lookup test, ask them to find a known parameter, limit, error, or exception. Note where they begin, which labels they follow, and whether the answer includes enough context to use safely.

For a scan test, ask them to identify which sections apply without reading every paragraph.

Test on the target medium. Include mobile, keyboard-only, screen reader, print, or constrained operational contexts when those surfaces matter.

Distinguish structural failures from prose failures. If readers cannot find the right paragraph, change navigation or grouping. If they find it but misunderstand it, revise the writing using `writing-clarity.md`.

## Review Structural Quality

- [ ] Define the page purpose and primary reader path before arranging it.
- [ ] Match the organization to the document type and reader intent.
- [ ] Support scanning, close reading, and lookup where each is needed.
- [ ] Make the first view establish orientation and a useful next move.
- [ ] Group content by semantic relationship rather than fixed quotas.
- [ ] Use headings with accurate information scent and logical hierarchy.
- [ ] Choose prose, lists, tables, and diagrams by relationship.
- [ ] Put prerequisites, warnings, verification, and recovery near the action.
- [ ] Scope code samples according to what they teach or enable.
- [ ] Add TOCs, links, and disclosure controls only when they reduce effort.
- [ ] Preserve responsive behavior, semantic HTML, and accessible alternatives.
- [ ] Test first-view orientation, task completion, scanning, and retrieval.

## Relationship to Writing Clarity

Use this reference after defining what the reader should achieve and drafting the necessary ideas. Use `writing-clarity.md` to improve reader outcomes, sentence geometry, coherence, concrete language, action friction, and behavioral testing within each structural unit.
