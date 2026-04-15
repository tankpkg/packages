---
name: "@tank/markdown-renderer"
description: |
  Render extended markdown into real HTML and SVG using a practical Node/Web pipeline.
  Covers CommonMark/GFM, Mermaid, KaTeX math, trusted SVG/custom HTML,
  sanitization, static export with a real browser, and extension patterns for
  DOT/Graphviz and other diagram families. Synthesizes unified/remark/rehype,
  Mermaid, KaTeX, Graphviz WASM, GitHub Markdown behavior, and browser-based
  verification workflows. The standalone package and CLI are published as
  `markdown-renderer-cli`:
  https://github.com/elad12390/markdown-renderer

  Trigger phrases: "markdown renderer", "render markdown", "markdown to html",
  "mermaid markdown", "latex in markdown", "katex markdown", "custom html in markdown",
  "svg in markdown", "extended markdown", "diagram rendering", "graphviz markdown",
  "static markdown export", "safe markdown html", "markdown preview engine", "npx markdown-renderer",
  "render mermaid to svg", "markdown pipeline"
---

# Markdown Renderer

## Core Philosophy

1. **Separate compile from execute.** Parse markdown and sanitize HTML in Node. Run browser-only renderers such as Mermaid in a real browser.
2. **Use native markdown first.** Tables, task lists, footnotes, `diff`, `kbd`, and `<details>` do not need custom engines.
3. **Treat raw HTML as unsafe by default.** Allow only the tags and attributes the renderer truly needs.
4. **Prefer fenced-language adapters.** New capabilities should plug in by code fence language, not by ad-hoc string hacks.
5. **Static export is the proof path.** If the browser-backed export does not materialize the final HTML or SVG, the renderer is not done.

## Quick-Start: Common Problems

### "I want to run the renderer right now"

1. Use the standalone package, not the skill repo internals.
2. Run `npx markdown-renderer-cli render --in input.md --out output.html --mode static`.
3. Or run `bunx markdown-renderer-cli render --in input.md --out output.html --mode static`.
4. Use this skill to choose the right renderer strategy and debug failures.

### "I need markdown, Mermaid, and math in one renderer"

1. Use the unified pipeline from `references/markdown-pipeline.md`.
2. Parse GFM and math first.
3. Turn Mermaid fences into placeholders at compile time.
4. Render final Mermaid SVG in a real browser during static export.
   -> See `references/math-and-mermaid.md`

### "My markdown supports raw HTML and SVG"

1. Decide whether raw HTML is trusted.
2. If not trusted, sanitize aggressively before stringifying.
3. Extend the allowlist only for required SVG tags and attributes.
4. Prove unsafe `script`, `on*`, and dangerous URL content gets removed.
   -> See `references/svg-html-and-security.md`

### "I want more than Mermaid diagrams"

1. Check whether the need is already native markdown or GFM.
2. For text-to-diagram formats, prefer a fenced-language adapter.
3. Start with Graphviz/DOT before heavier engines.
4. Add browser-only adapters only when the static export path can verify them.
   -> See `references/extended-renderers.md`

### "The preview looks fine, but exported output is wrong"

1. Compare client mode vs static export mode.
2. Check whether a renderer only executed in the browser.
3. Inspect placeholder state and final SVG presence.
4. Fail the verification if runtime scripts leak into exported HTML.
   -> See `references/verification-and-debugging.md`

## Decision Trees

### Choose the Rendering Path

| Input Type | Recommendation |
| --- | --- |
| CommonMark/GFM only | Parse and stringify directly |
| Inline or block math | Render at compile time with KaTeX |
| Mermaid | Compile to placeholder, execute in browser |
| Trusted raw SVG | Preserve through sanitization allowlist |
| Untrusted raw HTML | Sanitize before output |
| DOT / Graphviz | Render to SVG with WASM during compile |
| Heavier interactive embed | Defer unless browser execution and verification are clear |

### Choose the Extension Type

| Need | Extension shape |
| --- | --- |
| Rich text feature already in GFM | No new adapter |
| Code fence to deterministic SVG | Compile-time adapter |
| Browser-only diagram engine | Placeholder + execute-phase adapter |
| Potentially unsafe embedded HTML | Sanitization rule first, adapter second |

### Choose Verification Depth

| Change | Verification |
| --- | --- |
| Markdown or sanitize rule | Fixture assertion + browser smoke test |
| Mermaid or browser-only renderer | Real Playwright static export |
| New fence adapter | Positive fixture + negative failure fixture |
| Security-sensitive HTML/SVG change | Sanitization regression fixture |

## Published Package

| Artifact | Location |
| --- | --- |
| GitHub repo | `https://github.com/elad12390/markdown-renderer` |
| npm package | `markdown-renderer-cli` |
| CLI commands | `npx markdown-renderer-cli ...`, `bunx markdown-renderer-cli ...` |

## Reference Index

| File | Contents |
| --- | --- |
| `references/renderer-architecture.md` | Two-phase renderer architecture, module boundaries, adapter contracts, client vs static export |
| `references/markdown-pipeline.md` | unified/remark/rehype pipeline design, GFM handling, raw HTML parsing, fence interception |
| `references/math-and-mermaid.md` | KaTeX compile-time rendering, Mermaid execute-phase rendering, versioning, export concerns |
| `references/svg-html-and-security.md` | Trusted vs untrusted raw content, SVG allowlists, dangerous attribute stripping, security defaults |
| `references/extended-renderers.md` | Graphviz, PlantUML, WaveDrom, ABC notation, SMILES, maps, playgrounds, and renderer selection matrix |
| `references/verification-and-debugging.md` | Bulletproof verification flow, fixture strategy, Playwright checks, failure diagnosis, regression discipline |
