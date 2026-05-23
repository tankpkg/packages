# Layered Writing for Technical Documents

Sources: Barbara Minto (The Pyramid Principle, 1987), Edward Tufte (Envisioning Information, 1990), Steve Krug (Don't Make Me Think, 2000), William Zinsser (On Writing Well, 1976), Google Technical Writing Course, Randall Munroe (Thing Explainer / Up-Goer Five), Cognitive Load Theory (Sweller, 1988), Wellspoken.me Layer Cake Method.

Covers: Progressive disclosure of information from TL;DR to deep detail. Inverted pyramid structure, layered explanations, and techniques for explaining complex topics at multiple levels of resolution.

## The Inverted Pyramid

Journalists solved this problem long ago: put the most critical information first (who, what, when, where, why), then provide context, background, and nuance in descending order of importance. The structure is designed for skimmers — readers who stop at any point still get something useful.

Applied to technical docs:

| Layer | Position | Content | Reader Type |
|-------|----------|---------|-------------|
| TL;DR | Very top | One sentence summary of what this page explains | Everyone |
| Core | After TL;DR | The answer, command, configuration, step | Skimmers |
| Detail | Middle | How it works, why this approach | Curious readers |
| Deep dive | Bottom | Edge cases, alternatives, architecture | Experts |

The key insight: most readers will read the summary and example and leave satisfied. A smaller number will need the deep explanation. Almost none need to read everything.

## The Layer Cake Method

Build understanding in sequential layers where each layer is complete on its own and prepares the reader for the next. Each layer is **accurate** — you're adjusting resolution, not accuracy.

| Layer | Resolution | Length | Example |
|-------|-----------|--------|---------|
| Layer 1 | Thumbnail | 1 sentence | "JWT is a compact token that proves who you are without the server storing session state." |
| Layer 2 | Standard image | 1 paragraph | Mechanism: how it works, plain language. "When you log in, the server creates a signed token with your user ID. Your browser sends this token with every request. The server verifies the signature without a database lookup." |
| Layer 3 | High-definition | Full section | Nuance: algorithms, expiration, refresh tokens, security considerations, common attack vectors. |

### Honesty Rule

None of the layers oversimplify. If Layer 1 would lead someone to an incorrect conclusion, rewrite it. Accuracy is non-negotiable at every resolution.

## Progressively Disclosing Information

The companion principle to the inverted pyramid: reveal complexity gradually, in layers, rather than all at once.

### Page-level Progressive Disclosure

```
1. One-paragraph summary at the top
2. Short code example / quick-start
3. Deeper explanation below
4. Advanced usage, edge cases at the bottom
```

### Document-level Progressive Disclosure

```
README (one-screen overview and quickstart)
  → Guides (conceptual explanations organized by task)
    → API Reference (every parameter, every edge case)
```

### HTML/Markdown Techniques for Progressive Disclosure

- `<details>/<summary>` for expandable sections. Ideal for optional configurations, advanced settings, verbose examples.
- Accordion patterns for FAQs or grouped deep-dives.
- "Read more" links for topics a minority of readers will need.
- Tooltips for jargon definitions without breaking reading flow.
- Tabbed content: "Basic" tab vs "Advanced" tab.

## The Compression Ladder Exercise

A training technique for finding the essence of any explanation:

1. Explain a complex topic in 60 seconds. Record yourself.
2. Explain the same topic in 30 seconds. Record again.
3. Explain in 15 seconds.

Your 15-second version is the essence. The words you cut between rounds are unnecessary complexity. This works because time pressure forces prioritization.

## The One-Sentence Challenge

Reduce any complex idea to one readable sentence of 15-20 words. If you cannot say it in one sentence, you haven't found the core yet. Every document should start with this sentence.

## Up-Goer Five Technique (Constraint-Based Clarity)

Randall Munroe's method of explaining complex topics using only the 1,000 most common English words forces you to:

1. Find the core idea — you cannot hide behind jargon
2. Use analogy and metaphor — comparing to everyday experiences
3. Be creative with description — "space car" for lunar module, "sky bag air" for hydrogen

This extreme constraint is a diagnostic tool. If your explanation breaks when jargon is removed, the underlying concept wasn't clear to begin with. Use it to stress-test your TL;DR and Layer 1.

## Code-First Pattern

For technical documentation, show the code before the explanation. Many developers will read the code, understand it immediately, and never need the explanation. That's not a failure — it's efficiency. The explanation exists for those who need it.

Structure:
```
TL;DR (1 sentence)
Code example (the answer)
What this code does (1 paragraph)
Why it works this way (explanation)
Advanced variations / edge cases
```

## Anti-Patterns

| Anti-pattern | Why it fails | Fix |
|-------------|-------------|-----|
| Burying the answer under context | Readers leave before finding what they need | Lead with the answer |
| Opening with history/architecture | No one cares before they know how to use it | Quickstart first, architecture later |
| All detail on one page | Overwhelms, no self-service depth | Layer: summary → example → deep dive |
| Explaining everything before showing | Developers read code first | Show code, then explain |
| Equal-weight headings | No visual hierarchy, everything looks equally important | Tiered headings that compress information faithfully |
| Hiding instead of layering | Information buried too deep to find | Each level must make the next level's contents predictable |

## Quality Gate: Before Publishing

1. Can someone get the gist from the top level alone? (If no, rewrite the TL;DR)
2. Does each heading make the next section's contents predictable? (If it surprises, the hierarchy leaks)
3. Can a reader self-select their depth? (Can they stop at Layer 1 and leave satisfied?)
4. Does the code example work without reading the explanation? (If no, show a simpler example)

## The SCQA Framework (Minto Pyramid Principle)

Structure every introduction with Situation, Complication, Question, Answer. This mirrors how readers naturally process: "What's going on? What's the problem? What question does that raise? What's the answer?"

| Element | Role | Example |
|---------|------|---------|
| **S**ituation | Shared context the reader already knows | "Your API handles 10K requests/second with no issues." |
| **C**omplication | The problem that disrupts the situation | "At 100K requests/second, response times spike to 5+ seconds." |
| **Q**uestion | The implicit question raised by the complication | "How do we scale to 100K RPS without rewriting the entire API?" |
| **A**nswer | Your solution (the document's main point) | "Add a Redis cache layer in front of the database — here's how." |

This SCQA structure also works at the paragraph level. A paragraph's first sentence states the situation, the middle describes the complication, and the final sentence provides the answer.

## The Teach-Back Method

A technique for validating that your layered explanation works:

1. Explain a concept to someone
2. Ask them to explain it back to you
3. The delta between what you said and what they understood reveals exactly where your explanation broke down

Apply this to documentation:
- Was there a missing foundation layer? → Add a simpler Layer 1
- Was a jargon term undefined? → Define on first use
- Was a logical jump too large? → Add an intermediate layer
- Did they misunderstand a key concept? → Add a diagram or worked example

## When Layering Goes Wrong

### Hiding Instead of Layering

If information is buried so deep that users cannot find it, that's obscurity, not progressive disclosure. The fix: predictable paths. Every level should make the next level's contents obvious. If someone has to guess where to find something, the structure is broken.

### Compression Without Judgment

Generic headings like "Overview," "Details," "Additional Information" provide structure without hierarchy. Progressive disclosure requires that each level genuinely compresses the level below it. The heading must tell you what is inside AND whether you need to go inside.

### False Confidence from AI Summaries

AI-generated TL;DRs can compress without understanding — producing summaries that sound right but lose critical nuance. An executive summary that omits a key exception clause is worse than no summary at all. Every compression layer must be verified: does the short version preserve what matters?

## Horizontal and Vertical Logic (Minto)

- **Vertical logic**: Every point in the pyramid raises a question in the reader's mind, and the points directly below it answer that question. This is the question-answer dialogue that drives a reader forward.
- **Horizontal logic**: The ideas within each group must present either a deductive chain (premise → premise → therefore) or an inductive grouping (similar ideas → inference). Every grouping is one or the other — there is no third option.

Test your structure:
1. Read only the headings. Do they tell a coherent story?
2. For each heading, ask: "So what?" If the sub-content doesn't compellingly answer, restructure.
3. For each claim, ask: "Why is that true?" If the sub-content doesn't prove it, add evidence or remove the claim.

## Ordering Ideas in Layers

Present supporting ideas in one of three logical orders:

| Order Type | When to Use | Example |
|-----------|-------------|---------|
| **Time order** | Sequence of events with cause-effect | "Step 1: Install → Step 2: Configure → Step 3: Test" |
| **Structural order** | Parts of a whole, broken down | "The system has three components: frontend, API, and database" |
| **Degree order** | Ranked by importance | "Most important: security. Next: performance. Last: developer experience" |

## Transition Patterns

Smooth transitions between layers keep the reader oriented. Three techniques:

1. **Referencing backward**: Pick up a key word from the preceding section and carry it into the next. "The JWT token we generated in the previous step now needs to be stored..."
2. **Summarizing**: Consolidate complex ideas at the end of long sections before moving forward. "To recap: we've set up auth, configured the middleware, and tested the happy path."
3. **Concluding**: Create appropriate closure or call to action — but only when genuinely needed. "Now that authentication is working, the next step is to add role-based authorization."

## Building the Pyramid: Top-Down vs Bottom-Up

Minto describes two approaches to structuring your document:

### Top-Down (Preferred)
Start with the conclusion, then ask "What supports this?" The answers become the next level.

1. State your main conclusion (the answer)
2. Ask: "What questions does this raise in the reader's mind?"
3. Answer those questions — they become the next level of the pyramid
4. Repeat until every level is supported

### Bottom-Up (When You Don't Know the Conclusion Yet)
List all your points, find relationships, draw conclusions upward.

1. Brainstorm all ideas onto a page
2. Group related ideas together
3. For each group, write a summary statement that captures the insight
4. Group the summary statements under a higher-level conclusion
5. Repeat until you reach a single governing thought

Always try top-down first — it forces you to clarify your thinking before writing.

## The "So What?" and "Why?" Tests

Two questions transform communication:

- **"So what?"** — After writing any point, ask "So what?" If you cannot answer clearly with a consequence, implication, or action, the point doesn't belong. This removes unnecessary content and strengthens cause-effect relationships.
- **"Why?"** — If you make a claim, ask "Why is that true?" The answer either validates the claim or exposes its weakness. This surfaces hidden assumptions and improves credibility.

Apply these at every level: TL;DR, section headings, paragraphs, individual sentences.

## MECE Framework (Mutually Exclusive, Collectively Exhaustive)

Categories used to organize supporting arguments must be:

1. **Mutually Exclusive**: No overlap. Each item belongs to exactly one category. If a point could fit in two categories, the categories overlap — redefine them.
2. **Collectively Exhaustive**: Together, the categories cover everything. If something important doesn't fit any category, you have a gap — add a category.

**Example**: Organizing database optimization strategies
- ❌ Non-MECE: "Indexing, query optimization, caching, read replicas" (caching and read replicas are both scaling strategies — overlapping)
- ✓ MECE: "Query-level (indexing, rewriting), schema-level (normalization, partitioning), and infrastructure-level (caching, replicas)"

## The Deductive vs Inductive Choice

At the supporting argument level, choose between two reasoning structures:

| Structure | Pattern | Best For | Risk |
|-----------|---------|----------|------|
| **Deductive** | General principle → specific case → therefore conclusion | Academic, legal, formal proofs | If the reader rejects the general principle, the whole argument collapses |
| **Inductive** | Observation A + Observation B + Observation C → therefore pattern exists | Business recommendations, technical decisions | If observations are cherry-picked, the conclusion is invalid |

Minto's recommendation: at the Key Line level (the arguments directly supporting the main conclusion), prefer inductive structure. Executives find it more persuasive because they see evidence before conclusions.

## Writing Summaries That Aren't Intellectually Blank

The most common failure in technical documents: summary statements that restate without adding value.

**Intellectually blank**: "This section covered authentication." (Just restates)
**Insightful summary**: "JWT authentication eliminates server-side state, but introduces token management complexity — use it when statelessness matters more than revocability."

A good summary must state either:
- The **effect** of action ideas (what results from doing this)
- The specific **inference** drawn from situation ideas (the insight the data reveals)

## The Narrative Flow: SCQA in Practice

The introduction tells the reader a story they already know. This pushes aside competing thoughts, establishes shared context, and makes the reader receptive to your argument. A SCQA introduction should take 3-5 sentences total.

**Full example**:
> Most web APIs authenticate users with session cookies **(Situation)**. But session cookies require server-side state, which doesn't scale well across microservices **(Complication)**. How can we authenticate users across distributed services without shared state? **(Question)**. JSON Web Tokens (JWT) solve this by embedding signed user claims directly in the token — the server verifies without a database lookup **(Answer)**. This document shows you how to implement JWT auth in your Express API in under 10 minutes.

## Testing Your Document Structure

After drafting, run these tests:

1. **Read only the headings and TL;DR.** Does a coherent story emerge? Can someone understand the document's argument from headings alone?
2. **For each H2, ask its question.** "What is this section answering?" If the heading doesn't imply a question, rewrite it.
3. **Check the depth gradient.** Is there a clear progression from shallow (TL;DR) to deep (bottom)? Or does it lurch between depths?
4. **The 5-second test.** Open the page. Look away after 5 seconds. What do you remember? That's the only thing your scanning reader gets.

## Layered Writing Template

For any technical concept, fill this template:

```
## [Concept Name]

**In one sentence**: [Explain it to a product manager]

**In one paragraph**: [Explain it to a developer who will use it]

**How it works**: [Explain it to a developer who will debug it]

**Diagram**: [Mermaid or SVG showing the flow/architecture/state]

**Code example**: [Minimal, runnable, annotated]

**Common mistakes**: [What goes wrong, why, how to fix]

**When to use / when not to**: [Decision framework — this vs alternatives]

**Deep dive**: [Architecture, tradeoffs, implementation details]
```

Each section is a self-contained layer. A reader can stop at any layer and have a correct understanding.
