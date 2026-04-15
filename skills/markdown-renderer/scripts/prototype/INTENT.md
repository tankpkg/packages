# Markdown Renderer Prototype Intent

## Anchor

Build a real Node/Web markdown renderer prototype that can turn extended markdown into verified HTML output, including browser-executed diagram rendering where needed.

## Modes

| Mode | Purpose | Output |
| --- | --- | --- |
| Client | Produce HTML that still contains executable placeholders for browser-only renderers | HTML document |
| Static export | Produce final HTML after running browser-side renderers in a real browser | HTML document |

## Required Behaviors

| Input | Expected behavior |
| --- | --- |
| Normal markdown | Render through a CommonMark/GFM pipeline |
| Mermaid fence | Become a real rendered SVG in static export mode |
| Inline and block math | Render through KaTeX output |
| Raw trusted SVG | Survive sanitization and remain visible |
| Safe custom HTML | Survive sanitization if allowed by policy |
| Dangerous raw HTML/SVG | Be stripped or neutralized by sanitization |
| DOT fence | Render to SVG without requiring an external binary |

## Constraints

1. Use real libraries and a real browser for verification. Do not mock Mermaid, KaTeX, Graphviz, or DOM execution.
2. Default to a safe sanitization policy. Treat raw HTML as unsafe unless explicitly allowed.
3. Keep the prototype self-contained under `scripts/prototype/`.
4. Prefer the smallest architecture that supports extension by fenced language.
5. The static-export path is the proof path. If client placeholders exist but static export cannot materialize them, the prototype is incomplete.

## Acceptance Examples

### Example: mixed document

Given a markdown document containing:
- headings, lists, task lists, footnotes, `diff`, and `<details>`
- a Mermaid flowchart
- inline and block math
- a raw SVG block
- a Graphviz DOT fence

When static export runs

Then the resulting HTML document contains:
- rendered markdown structure
- at least one Mermaid SVG
- KaTeX-rendered math markup
- preserved SVG markup for the trusted SVG block
- rendered Graphviz SVG
- no `<script>` tag from user content

### Example: unsafe content

Given markdown containing raw HTML with script tags, event handler attributes, or dangerous links

When rendering runs

Then dangerous content is removed or neutralized and does not execute in the verification browser.
