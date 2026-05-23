# Document Structure and Formatting

Sources: Google Developer Technical Writing Course (One + Two), Steve Krug (Don't Make Me Think, Chapters 1-5), Jakob Nielsen (Nielsen Norman Group, Progressive Disclosure research), Robin Williams (The Non-Designer's Design Book — CRAP principles), Jeff Johnson (Designing with the Mind in Mind), Microsoft UX Guidelines (Inverted Pyramid in UI text).

Covers: How to structure, format, and lay out technical documents for maximum clarity and scannability using HTML and Markdown. Heading hierarchies, callout/admonition patterns, comparison design, responsive layout, and cognitive load management.

## The Golden Rule of Document Structure

**Every page should be self-explanatory within 5 seconds.** The reader should know what this page covers, whether it's relevant to them, and how to proceed — without thinking.

## Document Opening Formula

Every document should open with:

```
# [Clear, action-oriented title]

**TL;DR**: [One sentence — what this page explains and why you'd read it]

> **Prerequisites**: [What you need to know / have installed]
> **What this covers**: [Scope — what you'll learn]
> **What this does NOT cover**: [Non-scope — prevent wasted reading]

[Quick-start code or command — the answer, immediately]

## How It Works [or: Overview]
[Layered deepening starts here]
```

## Heading Hierarchy for Progressive Disclosure

Headings must genuinely compress the content below them. A reader scanning only headings should understand the full argument.

| Level | Purpose | Rule |
|-------|---------|------|
| H1 | What the entire document is about | One per page, action-oriented |
| H2 | Major sections supporting H1 | 3-7 per page, answer "what" and "why" |
| H3 | Subsections detailing H2 | Answer "how", introduce a specific concept or step |
| H4 | Granular details within H3 | Edge cases, examples, config details |

**The compression test**: If H2 says "Overview" and the content is actually about authentication flow, the heading failed. Rewrite it as "Authentication Flow".

## Callout and Admonition Patterns

Use callouts to surface information that interrupts the linear reading flow. Choose the right type:

| Type | Icon | Color | When to Use |
|------|------|-------|-------------|
| **TL;DR** | None or 📌 | Neutral | At the very top of every page. One sentence. |
| **Info / Note** | ℹ️ | Blue | Supplementary context, "by the way" facts |
| **Tip** | 💡 | Green | Best practice, "here's a smarter way" |
| **Warning** | ⚠️ | Yellow/Amber | Potential pitfalls, gotchas, deprecated behavior |
| **Danger / Critical** | 🚫 | Red | Actions that cause data loss, security issues |
| **Example** | 📋 | Gray/Neutral | Worked example distinct from explanation |

### HTML Structure for Admonitions

```html
<div class="admonition note">
  <strong>ℹ Note:</strong>
  <p>This operation is idempotent — you can safely retry it.</p>
</div>

<div class="admonition warning">
  <strong>⚠ Warning:</strong>
  <p>This deletes all data. No undo.</p>
</div>
```

### Callout Placement Rules

- Before the action they warn about (never after)
- Never more than one callout per section (diminishing returns)
- Keep text under 3 lines (if longer, it belongs in the main content)

## Progressive Disclosure with HTML

### `<details>/<summary>` for Optional Depth

```html
## Configuration Options

<details>
<summary>Advanced: Custom timeout settings</summary>

The default timeout is 30 seconds. For long-running operations, override with:

```js
fetch('/api', { timeout: 120000 })
```

</details>
```

Use for: advanced configuration, verbose examples, edge cases, verbose error messages, platform-specific differences.

### Tabbed Content for Parallel Paths

```
### Installation

<div class="tabs">
  <div class="tab" data-tab="npm">npm install package</div>
  <div class="tab" data-tab="yarn">yarn add package</div>
  <div class="tab" data-tab="pnpm">pnpm add package</div>
</div>
```

Use for: installation methods, language-specific examples, OS-specific instructions.

## Scannability Techniques

Research shows users scan, they don't read. Design for scanning:

### Visual Hierarchy of Text Elements

Readers process in this order:
1. Headings (H1-H4)
2. Bold text within paragraphs
3. First sentence of each paragraph
4. Lists (numbered > bulleted)
5. Code blocks (developers read code before prose)
6. Body text

### Lists > Paragraphs

When you have 3+ related items, use a list instead of prose:

**Bad (wall of text):**
The system supports three authentication methods. You can use API keys, which are simple but less secure. You can use OAuth 2.0, which is more secure but requires more setup. You can use JWT tokens, which are stateless and good for microservices.

**Good (scannable list):**
- **API Keys**: Simple, less secure. Good for server-to-server.
- **OAuth 2.0**: Secure, requires setup. Good for user-facing apps.
- **JWT Tokens**: Stateless, no DB lookup. Good for microservices.

### Paragraph Design

- Opening sentence = the paragraph's thesis. Everything after = support.
- Keep paragraphs to 3-5 sentences.
- Bold key terms on first use (and define them).
- Use one paragraph per idea.

## Tables for Comparison and Reference

Tables outperform prose for:
- Feature comparisons (A vs B vs C)
- Configuration options (parameter / type / default / description)
- Error codes (code / meaning / action)
- Method signatures (method / params / returns / description)

```markdown
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | number | 30000 | Request timeout in ms |
```

## Code Block Best Practices

### Always Include Language Annotation

```python  ← Not ``` alone
def hello():
    print("hi")
```

### Show File Name When Useful

```
```javascript title="src/auth/login.js"
```
```

### Highlight Key Lines

```javascript {3,6-8}
// The important lines are highlighted for scanning
function process(data) {       // ← highlighted
  validate(data)
  return transform(data)
}
```

### Prefer Working Examples

Every code block should be copy-paste runnable. If the reader needs to fill in gaps, you've made them think. Add the boilerplate.

## Cognitive Load Management

From Jeff Johnson's "Designing with the Mind in Mind":

### Principle of Chunking

Break complex information into chunks of 5-9 items (Miller's Law). This applies to:
- Steps in a procedure
- Items in a list
- Sections on a page
- Options in a decision

### White Space as a Cognitive Tool

Generous spacing between sections gives the reader's brain time to process. Crowded content forces simultaneous processing — the reader must scan, filter, and prioritize all at once.

Rule of thumb: between 30-50% of the visible area should be white space.

### Line Length (Measure)

Optimal line length for readability: 50-75 characters. Longer lines make it harder for the eye to find the next line. Shorter lines break reading rhythm. For code, 80-100 characters is standard.

## Mobile-Responsive Documentation

- SVGs: use `viewBox` (never fixed `width`/`height`)
- Tables: horizontal scroll wrapper for narrow screens, or collapse to key-value on mobile
- Code blocks: horizontal scroll, never wrap
- Callouts: full-width, padding adjusts with viewport
- Font size: minimum 16px for body text on mobile (prevents iOS zoom on focus)

## CRAP Principles for Document Design

From Robin Williams' "The Non-Designer's Design Book":

| Principle | Meaning | Applied to Docs |
|-----------|---------|-----------------|
| **Contrast** | Make different things look very different | Heading sizes clearly distinct; callout colors clearly different from body |
| **Repetition** | Repeat visual elements for cohesion | Same admonition style throughout; consistent code block styling; consistent link color |
| **Alignment** | Every element visually connected to something | Left-align body text; consistent indent for code and lists; aligned callout borders |
| **Proximity** | Related items close together | TL;DR directly below title; code example immediately after its explanation; prerequisites near the top |

## Navigation and Wayfinding

### Table of Contents

For documents longer than 3 scroll-screens, include a TOC after the TL;DR:

```markdown
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)
```

### Internal Links

Link to related concepts when the reader might need context. A developer reading about "JWT refresh tokens" might also need to know about "token rotation" — link to it.

### Breadcrumbs (for multi-page docs)

```
Home > Authentication > JWT Tokens > Refresh Token Flow
```

Gives the reader spatial context within the documentation system.

### "What's Next" Section

End every page with:
- Where to go next (logical next step)
- Related documentation (tangential but relevant)
- "Still stuck?" → support channels

## Anti-Patterns

| Anti-pattern | Why it fails | Fix |
|-------------|-------------|-----|
| Generic headings ("Overview", "Details", "More") | Labels on opaque boxes — no predictive value | Specific, information-dense headings |
| Walls of text | Readers scan, they don't read | Break into lists, tables, diagrams |
| No TL;DR | Reader must read to determine relevance | One sentence at the top that captures the essence |
| Overuse of bold/emphasis | When everything is emphasized, nothing is | Bold only key terms, first-sentence thesis |
| Code without output | Reader can't verify behavior | Show expected output or screenshot |
| Unlabeled diagrams | Reader must decode visual without guidance | Every diagram has a caption explaining what it shows |
| Hiding key info in scroll depth | Mobile users miss content | Critical info above the fold; progressive disclosure for detail |
