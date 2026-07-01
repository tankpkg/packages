# README Anatomy
Sources: React, tRPC, Got, Bun, Drizzle, Biome README analysis, Diátaxis framework, awesome-readme patterns

## The F-Pattern Scanning Model
The F-Pattern describes the visual path developers take when landing on a repository page. Understanding this behavior is critical for structuring information to maximize comprehension and retention.

### Eye-Tracking Behavior
1. First Horizontal Scan: Users read across the top of the page. This is where the Hero section resides. They look for the project name and a high-level summary to determine if they are in the right place.
2. Vertical Scan: Users move down the left edge of the content, looking for visual markers. Headlines, list markers (bullets/numbers), and the start of code blocks serve as anchors.
3. Second Horizontal Scan: Users focus on specific elements that catch their eye, typically the first code block or a bolded feature name. This is where they assess technical viability.

### Implications for README Design
To support scannable reading:
- Front-load value: Place the core value proposition in the first two sentences of the document.
- Use visual anchors: Headings, bold text, and code blocks break the "wall of text" and provide resting points for the eye.
- Optimize the "Gutter": Ensure the left margin of the README is clean. Bullet points and headings should be easily distinguishable from body text.
- Use bolding for emphasis: Bold keywords within sentences to allow users to grasp the meaning without reading the full sentence.
- Strategic code placement: Position the first code block within the first screen height to satisfy technical curiosity immediately.
- Minimize cognitive load: Avoid using complex sentence structures or excessive jargon in scannable sections like the Features list.
- Consistent rhythm: Maintain a predictable pattern of headings and spacing to guide the reader's eye naturally down the page.

## Section Ordering and Rationale
Follow this exact sequence to guide users from high-level discovery to low-level implementation details. This order minimizes friction and builds trust progressively.

### 1. Hero Section
The Hero section provides immediate context, branding, and trust signals.
- Purpose: Establish identity and credibility within seconds.
- Content: Centered logo, project name, one-sentence tagline, and a bar of shields.io badges.
- Rationale: First impressions happen in milliseconds. A professional hero section communicates that the project is well-maintained and serious.
- Implementation Tip: Use high-resolution SVGs for logos and ensure they support both dark and light mode themes on GitHub.

### 2. "What is X?" Section
Define the project in 2-3 sentences max.
- Purpose: Provide a clear, technical definition of the tool and its primary use case.
- Content: A brief description that identifies the problem domain and the solution provided.
- Rationale: Visitors need to confirm the project's purpose instantly. Use technical terminology that identifies the problem domain.
- Implementation Tip: Use a single paragraph with active verbs to describe what the tool enables for the developer.

### 3. Features List
Highlight the core capabilities using the "bold + one-liner" format.
- Purpose: Allow for rapid technical evaluation and comparison.
- Content: A list of 5-8 key features, each starting with an emoji and a bolded title.
- Rationale: Features allow users to quickly compare the tool against their requirements without reading through long paragraphs.
- Implementation Tip: Group features into logical categories if the library is large enough to warrant it.

### 4. Quick Start
A copy-pasteable code block showing a 5-minute success path.
- Purpose: Demonstrate technical simplicity and immediate value.
- Content: The most basic code example required to see a result. Include imports and a comment showing the output.
- Rationale: Code is the primary language of developers. Seeing the tool in action provides more clarity than prose.
- Implementation Tip: Use the most common entry point for the library to ensure the example is representative.

### 5. Installation
Instructions for supported platforms and package managers.
- Purpose: Provide the entry point for technical implementation and setup.
- Content: Commands for npm, yarn, pnpm, and bun. List any prerequisites like Node.js versions.
- Rationale: Users who are convinced by the Quick Start will immediately want to know how to add it to their project.
- Implementation Tip: Use a standard code block for the command and clearly state if it should be a dev dependency.

### 6. Usage and Examples
Common use cases with self-contained, commented code.
- Purpose: Educate the user on common implementation patterns and best practices.
- Content: 2-3 snippets covering the most frequent tasks the library handles.
- Rationale: Real-world patterns help users understand how to integrate the tool into their existing workflows.
- Implementation Tip: Link to a dedicated examples folder for complex, multi-file use cases.

### 7. API Reference
High-level summary of core functions and signatures.
- Purpose: Provide a quick lookup for technical details and function parameters.
- Content: A list of the main exported functions, their parameters, and return types.
- Rationale: Provides a quick lookup for users who are already familiar with the tool but need a syntax reminder.
- Implementation Tip: Use a table for small APIs and link to a separate file for larger ones to avoid cluttering the README.

### 8. Configuration
Document properties, environment variables, and defaults.
- Purpose: Explain how to customize the tool's behavior and settings.
- Content: A markdown table listing configuration keys, types, default values, and descriptions.
- Rationale: Essential for users who need to customize the tool's behavior beyond the defaults.
- Implementation Tip: Use backticks for variable names and code blocks for complex default objects.

### 9. Comparison Table
Contrast the project against primary alternatives in the ecosystem.
- Purpose: Help the user differentiate the project from the competition.
- Content: A table comparing features, performance, or philosophy against 2-3 known alternatives.
- Rationale: Helps users justify choosing this tool over others they might be considering.
- Implementation Tip: Be objective and fair; link to the homepages of the projects being compared.

### 10. Contributing
Link to CONTRIBUTING.md and basic workflow steps.
- Purpose: Invite community participation and outline the process for reporting bugs.
- Content: Links to the contribution guide, issue tracker, and a brief mention of the PR process.
- Rationale: Encourages community involvement by lowering the barrier to entry for potential contributors.
- Implementation Tip: Mention the required branch name or commit message format if the project enforces one.

### 11. Sponsors and Acknowledgments
Recognize financial and technical supporters who make the project possible.
- Purpose: Build trust and show community support and sustainability.
- Content: Logos or names of sponsors and significant contributors.
- Rationale: Builds trust and shows project sustainability and institutional backing.
- Implementation Tip: Ensure all sponsor links are properly formatted to prevent broken navigation.

### 12. License
State the license and link to the file.
- Purpose: Provide legal clarity for users and companies.
- Content: The name of the license (e.g., MIT) and a link to the full LICENSE file in the repository.
- Rationale: Legal clarity is mandatory for enterprise adoption and open-source compliance.
- Implementation Tip: Use a standard license identifier that is recognized by automated compliance tools.

## Progressive Disclosure Strategy
Progressive disclosure is the practice of revealing information only as it becomes necessary. This keeps the README focused while still providing access to deep technical details.

### Distribution of Content
- README.md: High-level overview, quick start, core features, and links to deeper documentation.
- /docs directory: In-depth guides, edge cases, full API specifications, and tutorials.
- /examples directory: Large, multi-file demonstrations of complex patterns.
- /scripts directory: Maintenance and build scripts used by developers and maintainers.

### Rules for Disclosure
- Limit README length: If a section requires more than two screen heights of scrolling, move it to a dedicated file in /docs.
- One-way detail flow: The README summarizes; the /docs files expand. Do not duplicate large sections of documentation across multiple files.
- Anchor links: Use internal links in the README to point to specific sections in the /docs folder.
- Modularize: Group related advanced topics into their own files within the /docs directory to prevent large, unmanageable files.
- Maintain a hierarchy: The README acts as the entry point; all deeper documentation must be reachable from it within 2 clicks.
- Visual cues: Use icons or arrows to indicate when a summary has a more detailed counterpart elsewhere in the repository.

## Decision Matrix: README vs Dedicated Docs Site
Choosing the right documentation architecture depends on the complexity of the API surface and the intended audience size.

| Criterion | README-only | Dedicated Docs Site |
|-----------|-------------|---------------------|
| API Surface | < 10 exports | > 50 exports |
| User Base | Small/Experimental | Large/Enterprise |
| Tutorials | 1-2 short guides | Multiple long-form courses |
| Search Needs | Browser (Cmd+F) | Integrated Algolia/Full-text |
| Versioning | Single version | Multiple versions (v1, v2) |
| Maintenance | Low overhead | High overhead (hosting, CI) |
| SEO | Repository search | Search engine optimization |
| Layout | GitHub Standard | Custom components / UI |
| Interactivity | Static code blocks | Live playgrounds / REPLs |

### When to Upgrade
Move to a dedicated site when the README exceeds 1,000 lines or when the /docs directory contains more than 10 files. A dedicated site improves SEO and provides a better user experience for long-form reading and structured learning paths.

## Hero Section Anatomy
The Hero section is the "landing page" of the repository. It must be visually balanced and informative.

### Layout Requirements
- Centered alignment: Header text, tagline, and badges should all be centered for a modern aesthetic.
- Logo: Use a clear logo. If possible, use the `<picture>` tag to support dark and light mode specific versions.
- Tagline: A single sentence starting with a verb or a defining noun. Avoid vague marketing terms.
- Badge Bar: Group badges by category (e.g., Status, Stats, License). Limit to 5-7 badges to avoid visual clutter.
- Action Links: Provide 3-4 HTML links for common paths (e.g., [Get Started], [API Reference], [Examples]).
- Consistency: Ensure the font sizes and weights in the hero section create a clear visual hierarchy.

## Feature List Patterns
Feature lists should be formatted to be scanned in seconds. Use the "Emoji + Bold + One-liner" pattern.

### The Pattern
- [Emoji] **[Feature]**: [Benefit-oriented description]

### Principles of Effective Descriptions
- Be specific: Focus on technical differentiators, not generic qualities.
- Be concise: Keep the description to one sentence.
- Focus on value: Explain how the feature helps the user (e.g., "reduces bundle size" vs "is small").
- Maintain consistency: Use the same tone and grammatical structure for every item in the list.
- Accuracy: Ensure that every listed feature is currently available in the latest release.

### Example Feature List
- Fast: Built with a compiled core for maximum throughput.
- Typed: Comprehensive TypeScript definitions generated at build time.
- Modular: Opt-in to only the components you need to minimize overhead.

## Quick Start Patterns
The Quick Start is the most important technical section. It must follow the "5-minute success" principle.

### Success Moment Characteristics
- Immediate: The user should be able to run the code after a single `npm install`.
- Visual: The code should produce an output that verifies the library is working correctly.
- Relevant: The example should represent the most common use case for the tool.
- Verifiable: Include the expected result as a comment so users can compare their local output.

### Formatting Rules
- Language Tag: Always specify the language in the code block (e.g., ```typescript).
- Imports: Include all necessary imports; do not assume the user knows which modules to pull in.
- Comments: Use comments to explain the "why" of specific parameters or lines.
- Result: Explicitly show the output of the code block as a trailing comment for verification.
- Conciseness: Keep the snippet as short as possible without sacrificing clarity or functionality.

## README Length Guidelines
Length is a proxy for complexity. A README that is too long is intimidating; one that is too short is unhelpful.

- Target Length: 300-400 lines of Markdown text.
- Section Limits: Each section should be manageable in a single vertical scroll.
- Nesting: Limit heading levels to H2 (##) and H3 (###). Avoid H4 and below as they disappear into body text.
- Paragraph Length: Keep paragraphs under 4 lines. If a paragraph is longer, break it into a list or sub-headings.
- Code Density: Use code blocks liberally but keep each block under 30 lines.
- White Space: Use single empty lines between sections and paragraphs to maintain a clean layout.

## Table of Contents
A Table of Contents is necessary for any README with more than six major sections.

- Automated vs Manual: Use GitHub's built-in ToC feature for simple projects. Use a manual ToC if you need to provide specific guidance.
- Placement: Position the ToC immediately after the "What is X?" section.
- Depth: List only H2 (##) headings. Do not include H3 or H4 headers in the ToC to keep it focused.
- Visuals: Use a simple list format; avoid complex nesting or icons in the ToC.
- Usefulness: Ensure that the ToC links are correctly anchored to the corresponding headings.

## The "Every Page is Page One" Principle
Technical documentation is non-linear. Users land on pages from search results, deep links, or issue trackers.

- Context: Every page in the /docs directory should start with a brief context sentence or a link back to the main README.
- Navigation: Provide clear "Up" or "Home" links on every page that isn't the primary README.
- Self-Containment: Avoid using "as mentioned before" unless referencing a section within the same page. Link directly to external sections.
- Searchability: Use descriptive headers that include keywords relevant to the content of that specific page.
- Accessibility: Ensure that every page can be understood without having read the previous page in a linear sequence.
- Freshness: Explicitly state if a sub-page applies only to specific versions of the library.

## Audience Analysis
Tailor your content to the three primary groups that visit your repository.

### 1. Evaluators (End Users)
- Primary Goal: Determine if the tool solves their specific technical problem.
- Key Sections: Hero, Features, Quick Start, Comparison Table.
- Focus: Value proposition, high-level features, and ease of use.
- Tone: Encouraging and benefit-oriented.

### 2. Implementers (Active Users)
- Primary Goal: Understand how to implement specific features or handle edge cases.
- Key Sections: Usage, API Reference, Configuration, Examples.
- Focus: Syntax, parameters, configuration options, and real-world patterns.
- Tone: Technical, precise, and neutral.

### 3. Maintainers and Contributors
- Primary Goal: Understand the internal logic to fix bugs or add new capabilities.
- Key Sections: Installation (development mode), Contributing guide, License.
- Focus: Build scripts, test suites, internal architecture, and PR requirements.
- Tone: Instructional and structural.

## Accessibility in READMEs
Accessibility is a core component of high-quality documentation. A README that is inaccessible excludes a portion of the developer community and reduces the project's overall reach.

### Semantic Header Structure
- Rule: Always use headers in sequential order (H1, then H2, then H3). Never skip levels (e.g., jumping from H1 to H3) as this confuses screen readers and breaks the document outline.
- Rationale: Assistive technologies rely on a logical heading hierarchy to navigate long documents. Proper nesting allows users to jump directly to the section they need.

### Alternative Text for Images
- Rule: Every image, including logos and badges, must have descriptive alt text.
- Rationale: Users with visual impairments cannot see logos or status badges. Alt text ensures they receive the same information (e.g., "Build Status: Passing").

### Color Contrast
- Rule: When using images or diagrams (like Mermaid), ensure high color contrast between text and background.
- Rationale: Users with low vision or color blindness must be able to distinguish between different elements in your visual aids.

### Link Descriptions
- Rule: Avoid "Click here" or "Read more" as link text. Use descriptive phrases like "View the full API Reference" or "Read the Contributing Guide."
- Rationale: Screen readers often provide a list of links on a page. Contextless link text is useless in this view.

## Visual Hierarchy Deep Dive
Beyond the F-Pattern, a clear visual hierarchy helps users prioritize information and reduces cognitive fatigue.

- High Priority: Title, Tagline, Primary Quick Start code block.
- Medium Priority: Feature list, Installation commands, Usage examples.
- Low Priority: Acknowledgments, Sponsors, License details.

### Using White Space
- Vertical Spacing: Use double line breaks between major sections (##) and single line breaks between sub-sections (###).
- Padding: Ensure that code blocks and tables have sufficient space around them to stand out as distinct elements.

### Typography for Scanning
- Bold Keywords: Bold the first 2-3 words of a list item to summarize the point.
- Italics for Emphasis: Use italics sparingly for secondary emphasis or to denote technical terms that aren't code.
- Backticks for Code: Always wrap file paths, variable names, and small commands in backticks to distinguish them from standard prose.

## Maintenance and Lifecycle
A README is a living document that must evolve alongside the project's code.

### Regular Audits
- Broken Links: Use automated tools to check for broken internal and external links every month.
- Version Updates: Ensure that installation commands and badges reflect the latest stable version of the library.
- Documentation Sync: Every time a feature is added or deprecated, the README and /docs must be updated immediately.

### Deprecation Notices
- Rule: Use a "WARNING" alert at the top of the README if a project is no longer maintained or if a major breaking change is imminent.
- Rationale: Prevents new users from adopting a project that is reaching its end-of-life.

### Roadmap and History
- Rule: Keep the roadmap high-level in the README and link to a separate ROADMAP.md for detailed quarterly goals.
- Rationale: Users want to know the project's direction but shouldn't be overwhelmed by internal planning details.

## Common Section Anti-patterns
Avoid these mistakes to maintain a professional and helpful repository experience.

### Wall of Text
Long blocks of prose are ignored by users scanning for information. Use lists, tables, and code blocks to create white space.

### Buried Prerequisites
If the tool requires a specific runtime version or a global dependency, state this at the very top of the Installation section.

### Missing Examples
Describing an API without showing a code example is a major friction point. Always include a brief snippet for every major function.

### Jargon Without Context
Avoid using internal terms or acronyms without defining them first. Provide links to external resources for complex architectural patterns.

### Non-functional Quick Starts
Code examples that throw errors or are missing steps destroy user trust. Every snippet must be tested against the latest version.

### No License Information
Users in corporate environments cannot use a library without a clear license. Place the license at the bottom and link to the LICENSE file.

### Hidden Links
Ensure that links to deeper documentation or external sites are clearly visible and not buried in long paragraphs.

### Over-explaining
Avoid detailed explanations of basic concepts (e.g., how to install npm). Focus on the unique aspects of your project.

### Inconsistent Formatting
Using different styles for headings or code blocks throughout the README makes the project appear unprofessional and disorganized.

### Marketing Fluff
Avoid hyperbolic claims like "the world's fastest" unless backed by reproducible benchmarks linked in the README.

### Missing Context
Failing to explain what the library is for on the first screen forces the user to dig through code to understand the project.

### Broken Anchors
Ensure that all links in the Table of Contents and internal navigation correctly point to existing sections without triggering 404s.

### Ignored Mobile View
Always verify that the README renders correctly on the GitHub mobile app, especially tables and large images which can break layouts.
