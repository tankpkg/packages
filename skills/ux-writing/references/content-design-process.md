# Content Design Process

Sources: Winters/Edwards (Content Design), Ben-David (The Business of UX Writing), Metts/Welfle (Writing Is Designing), Podmajersky (Strategic Writing for UX)

Covers: The end-to-end content design workflow — from research and discovery through drafting, testing, and measurement — plus collaboration models, style guide creation, and organizational maturity.

## Content-First Design

Design the conversation before designing the screen. Visual layout follows content structure, not the other way around.

### The Conversation-First Approach

Podmajersky frames every interface as a dialogue between the product and the user. Before opening a design tool, write out the exchange:

1. What does the user need to accomplish?
2. What does the product need to communicate?
3. What is the minimum exchange that satisfies both?

Write this exchange as a script — literal back-and-forth dialogue — then extract the content model from it.

### Why Content Precedes Layout

| Content-first advantage | What it prevents |
|---|---|
| Reveals actual information hierarchy | Designers guessing at content length with lorem ipsum |
| Exposes missing states early | "We forgot what happens when..." discovered in dev |
| Forces scope decisions | Feature creep hidden behind placeholder copy |
| Aligns stakeholders on messaging | Late-stage rewrites that break layouts |
| Surfaces terminology conflicts | Engineering naming leaking into user-facing text |

Metts and Welfle reinforce this: writing IS a design activity. Treat words as a design material with the same weight as color, type, and layout. Content and visual design happen in parallel, not sequentially.

### Content-First in Practice

- Write real content into wireframes from the first iteration
- Use content to drive component selection, not the reverse
- Prototype with words before pixels — a text-only flow test catches logic gaps faster than a clickable mockup
- Maintain a content model (structured inventory of what text appears where) alongside the design system

## Content Discovery

Research what users need to read before deciding what to write.

### User Stories for Content

Winters and Edwards adapt user stories specifically for content decisions:

```
As a [user type],
I need to know [information],
So that I can [action/decision].
```

Examples:
- "As a first-time buyer, I need to know shipping costs before checkout, so that I can decide whether to purchase."
- "As a returning user, I need to know what changed since my last visit, so that I can act on new information."

These stories map directly to content requirements — each one generates specific microcopy needs.

### Job Stories for Content

Job stories add situational context that user stories miss:

```
When [situation],
I want to [motivation],
So I can [expected outcome].
```

Example: "When I see an error after submitting a form, I want to understand what went wrong, so I can fix it without starting over."

### Content Audit

Inventory existing content before creating new content:

| Audit dimension | What to evaluate |
|---|---|
| Accuracy | Is the information correct and current? |
| Completeness | Are any user questions unanswered? |
| Consistency | Does terminology match across surfaces? |
| Clarity | Can users understand this on first read? |
| Tone alignment | Does it match the intended voice? |
| Redundancy | Is the same information repeated unnecessarily? |
| Accessibility | Does it work for screen readers and low literacy? |

Tag each content item with a disposition: keep, revise, remove, or create.

### Competitive Content Analysis

Study how competitors and adjacent products communicate:

1. Screenshot the same flow (signup, checkout, error handling) across 3-5 competitors
2. Catalog word choices, tone, information density, and help patterns
3. Identify gaps — what do competitors fail to explain?
4. Note conventions users expect from the category (do not break established patterns without cause)

## Content Design Workflow

A six-stage loop. Each stage produces an artifact that feeds the next.

| Stage | Activity | Output |
|---|---|---|
| 1. Research | User interviews, analytics review, support ticket analysis, content audit | Content brief: user needs, business goals, constraints |
| 2. Content model | Map information architecture, define content types, identify reuse | Structured content inventory with hierarchy and relationships |
| 3. Draft | Write real copy in context (wireframes, prototypes, spreadsheets) | First-pass content in situ, flagged questions for design/eng |
| 4. Review | Content crit, stakeholder review, legal/compliance check | Revised draft with resolved feedback |
| 5. Test | Comprehension testing, A/B tests, tree testing, usability sessions | Test results with confidence levels and recommendations |
| 6. Iterate | Revise based on test data, update content model, document decisions | Final copy, updated style guide entries, measurement baseline |

### Stage Details

**Research:** Pull from three sources simultaneously — qualitative (interviews, usability sessions), quantitative (analytics, funnel data), and support (ticket themes, chat logs, FAQ traffic). Prioritize by frequency and severity.

**Content model:** Define each content type: what fields it has, where it appears, what triggers it, what variations exist. This prevents one-off copy that cannot scale.

**Draft:** Write in the actual interface, not in a document. Use the real constraints — character limits, layout boundaries, responsive breakpoints. Flag every assumption explicitly.

**Review:** Use the content crit format described below. Separate review rounds: first for content accuracy and strategy, then for voice/tone polish.

**Test:** Match the test method to the question. Comprehension testing for clarity, A/B testing for conversion impact, tree testing for navigation labels.

**Iterate:** Treat published content as a hypothesis. Schedule post-launch reviews at 2 weeks and 6 weeks.

## Pair Writing

Winters and Edwards formalize collaborative writing as a core practice, not an occasional activity.

### What Pair Writing Is

Two people write together in real time — one drives (types), one navigates (challenges, suggests, checks). Rotate roles every 15-20 minutes.

### Pair Combinations and Their Value

| Pair | What the combination produces |
|---|---|
| Writer + Designer | Content and layout evolve together; prevents "make the copy fit" problems |
| Writer + Engineer | Surfaces technical constraints early; aligns variable names with user-facing terms |
| Writer + PM | Ensures copy reflects product strategy; resolves scope questions in real time |
| Writer + Researcher | Grounds every word choice in evidence; prevents assumption-driven writing |
| Writer + Writer | Catches blind spots; produces more consistent voice across flows |

### Running a Pair Writing Session

1. Define the scope: one flow, one screen, or one component — never "the whole feature"
2. Share context: user research, business requirements, technical constraints
3. Write together for 45-60 minutes maximum
4. The navigator reads every draft aloud — spoken text reveals rhythm problems that silent reading misses
5. Document decisions and rationale, not just the final copy

## Content Crits

Structured review sessions modeled on design critiques. Replace ad-hoc Slack feedback with disciplined evaluation.

### Crit Format

| Element | Detail |
|---|---|
| Duration | 30 minutes maximum |
| Group size | 3-6 people (writer, designer, PM minimum) |
| Presenter | The content designer — frames the context and specific questions |
| Materials | Content in context (mockup, prototype, or annotated wireframe) |
| Ground rules | Feedback on the work, not the person; questions before suggestions |

### What to Evaluate

Use Podmajersky's heuristics scorecard as a framework:

1. **Purposeful** — Does every word earn its place?
2. **Concise** — Is this the minimum effective copy?
3. **Conversational** — Does it sound like a helpful human?
4. **Clear** — Can the target user understand this immediately?
5. **Consistent** — Does it match the voice chart and existing patterns?
6. **Accessible** — Does it work across reading levels and assistive technology?
7. **Actionable** — Does the user know exactly what to do next?
8. **Appropriate** — Does the tone match the emotional context?
9. **On-brand** — Does it reinforce the product's personality?

### Feedback Framework

Structure feedback as observations, not directives:

- "I notice [observation]" — state what you see
- "I wonder [question]" — probe the intent
- "What if [suggestion]" — offer an alternative without prescribing

Avoid: "Change this to..." or "This is wrong." The writer retains final decision authority.

## UX Copy Testing

Treat copy as a design hypothesis. Test it with the same rigor applied to visual design.

### Testing Methods

| Method | Best for | Sample size | Effort |
|---|---|---|---|
| A/B testing | Conversion impact of copy variants | 1000+ per variant | Medium (needs traffic) |
| Comprehension testing | Whether users understand the message | 5-8 users | Low |
| Cloze testing | Whether users can predict content | 15-20 users | Low |
| Tree testing | Navigation label effectiveness | 50+ users | Medium |
| Preference testing | Which variant users prefer (and why) | 20-30 users | Low |
| Highlighter testing | Which parts users find confusing or helpful | 8-12 users | Low |
| First-click testing | Whether labels guide users to correct targets | 30+ users | Medium |

### A/B Testing Microcopy

Test one variable at a time. Common high-impact tests:

- CTA button labels (specific verb vs. generic)
- Error message wording (technical vs. plain language)
- Onboarding headline framing (benefit vs. feature)
- Form field labels (noun vs. question format)
- Confirmation message detail level

Run tests for a minimum of 2 full business cycles. Do not call results early on partial data.

### Comprehension Testing

Ask users to read the copy, then:

1. Explain what they just read in their own words
2. Describe what action they would take next
3. Identify anything confusing or unclear
4. Rate their confidence in understanding (1-5 scale)

If more than 1 in 5 users misinterpret the message, revise and retest.

## Measuring UX Writing Impact

Ben-David's core argument: writing must prove its value in business terms, not subjective quality assessments.

### Primary Metrics

| Metric | What it measures | How to capture |
|---|---|---|
| Task completion rate | Can users finish the flow? | Analytics funnel tracking |
| Error rate | How often users make mistakes | Form validation logs, analytics events |
| Time-on-task | How long the flow takes | Session recording tools, analytics |
| Support ticket deflection | Did clearer copy reduce support load? | Ticket volume before/after, topic tagging |
| Comprehension score | Do users understand the content? | Comprehension testing sessions |
| Drop-off rate | Where do users abandon? | Funnel analytics per step |
| Satisfaction (CSAT/SUS) | How do users feel about the experience? | Post-task surveys |

### Building a Measurement Baseline

1. Capture current metrics before any copy changes
2. Document what copy exists at each measurement point
3. Make one change at a time (isolate variables)
4. Measure at the same points after the change
5. Allow sufficient time for statistical significance
6. Report results as deltas: "Error rate dropped from 12% to 4% after revising the password requirements copy"

### Communicating Results to Stakeholders

Frame every result in business impact:

- Not: "We improved the error message clarity score by 40%"
- Instead: "Revised error messages reduced password reset support tickets by 30%, saving approximately 15 support hours per week"

Pair qualitative evidence (user quotes, session clips) with quantitative data. Numbers persuade executives; user stories persuade designers and engineers.

## Content Style Guide Creation

A living reference that scales content quality beyond individual writers.

### Style Guide Structure

| Section | Contents |
|---|---|
| Voice principles | 3-5 attributes with definitions and examples (see `references/voice-and-tone.md`) |
| Word list | Approved/rejected terms with rationale |
| Grammar conventions | Sentence case, contractions, serial comma, abbreviations |
| Component patterns | Standard copy for buttons, labels, errors, confirmations, empty states |
| Glossary | Product-specific terms with definitions |
| Examples | Before/after rewrites showing principles in action |
| Anti-patterns | Common mistakes with corrections |

### Building the Guide

1. Audit existing content for patterns (both good and bad)
2. Document decisions already made — do not invent rules that contradict shipped product
3. Start with the 10 most common content decisions writers face
4. Write each entry as a rule + rationale + example — never a rule alone
5. Publish where people already work (design system docs, not a PDF)
6. Assign an owner who reviews and updates quarterly

### Maintaining the Guide

- Review every new component type for style guide implications
- Add entries when the same question gets asked twice
- Remove entries that no one references (measure page views)
- Version the guide — teams need to know what changed and when
- Run a quarterly "style guide health check" with the content team

## Content Design Maturity Model

Ben-David maps organizational maturity across five levels.

| Level | Description | Content design role | Typical signals |
|---|---|---|---|
| 1. Ad-hoc | No dedicated writing role; engineers or PMs write copy | None — copy is an afterthought | Inconsistent terminology, no style guide, copy bugs filed as "low priority" |
| 2. Reactive | Writer exists but is consulted late in the process | Copy editor — polishes after design is final | Writer reviews mockups, limited to word-level changes |
| 3. Integrated | Writer joins the product team as a peer | Content designer — contributes from discovery | Writer participates in research, writes content briefs, runs content crits |
| 4. Strategic | Content design influences product decisions | Content strategist — shapes product direction | Content model drives feature scoping, writing metrics in product KPIs |
| 5. Embedded | Content design is indistinguishable from product design | Design partner — equal to visual design lead | Content-first workflow is default, voice is a competitive advantage |

### Moving Up the Maturity Curve

- **1 to 2:** Hire or designate a writer. Create a basic style guide. Start measuring one content metric.
- **2 to 3:** Move the writer into the product squad. Include writing in sprint planning. Establish content crits.
- **3 to 4:** Build a content model. Tie writing work to business metrics. Give writing a seat in product roadmap discussions.
- **4 to 5:** Content-first design is the default workflow. Writing quality is a product differentiator. Content design has a career ladder.

## Working with Stakeholders

Content design sits at the intersection of product, design, engineering, marketing, and legal. Navigating competing feedback is a core skill.

### Handling Feedback

| Feedback type | Response strategy |
|---|---|
| Subjective preference ("I don't like this word") | Ask what outcome they want — redirect from opinion to objective |
| Scope expansion ("Can we also mention...") | Refer to the content brief — if it was not in scope, it requires a new decision |
| Legal/compliance requirement | Accept the constraint, then find the clearest expression within it |
| Executive override | Document the decision and rationale; revisit with data after launch |
| Contradictory feedback from multiple reviewers | Escalate to the decision-maker with both positions and a recommendation |

### Managing Review Cycles

1. Set expectations early: define who reviews, when, and how many rounds
2. Consolidate feedback — never iterate on conflicting comments from separate threads
3. Distinguish between "must change" (factual errors, legal issues) and "nice to have" (style preferences)
4. Time-box reviews: 48 hours maximum per round
5. Final approval comes from the content designer, not the loudest stakeholder

### Proving Writing Value

Build a portfolio of evidence over time:

- Track every copy change alongside its metric impact
- Collect user quotes that reference content quality
- Document time saved by having a style guide (fewer review cycles, less back-and-forth)
- Calculate support ticket deflection savings in hours and dollars
- Present quarterly impact reports to leadership — small, consistent proof beats annual grand presentations
