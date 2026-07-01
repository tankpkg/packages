# Renderer Architecture

Sources: unified documentation, Mermaid documentation, KaTeX documentation, Graphviz WASM documentation, GitHub Markdown behavior, 2025-2026 markdown tooling research.

Covers: Two-phase architecture for extended markdown rendering, module boundaries, adapter contracts, client versus static export modes, and extension rules that keep the renderer small and verifiable.

## 1. Architecture Goal

The renderer exists to turn extended markdown into real output, not just tokenized placeholders. The architecture must separate work that is deterministic in Node from work that only becomes real in a browser.

Use this split:

| Phase | Environment | Responsibility |
| --- | --- | --- |
| Compile | Node | Parse markdown, render deterministic transforms, sanitize raw content, emit HTML and placeholders |
| Execute | Real browser | Turn browser-only placeholders into final SVG/HTML |
| Serialize | Node after browser run | Save final HTML for export or verification |

This avoids three common mistakes:

1. Pretending browser-only renderers are already final during compile time.
2. Mixing sanitization with runtime DOM mutation.
3. Shipping a preview-only system that cannot prove its exported output.

## 2. Module Boundaries

Keep the prototype small and explicit.

| Module | Job | Must stay ignorant of |
| --- | --- | --- |
| `src/index.js` | Public API orchestration | CLI parsing details |
| `src/cli.js` | File in/out wrapper | AST internals |
| Compile pipeline | Markdown parsing and HTML generation | Browser page lifecycle |
| Mermaid execute step | Browser-side SVG materialization | Markdown parsing rules |
| Graphviz adapter | DOT to SVG conversion | Browser execution |
| Verification tests | Assert behavior | Internal implementation shortcuts |

When these boundaries blur, the renderer becomes hard to debug. The CLI should not know how Mermaid works. The browser executor should not know how the markdown parser tokenized lists. Each part should only see its own boundary contract.

## 3. Public API Shape

Start with a tiny API surface.

| Function | Purpose | Return |
| --- | --- | --- |
| `renderToHtmlDocument(markdown, options)` | Compile markdown into a client-ready HTML document | HTML string |
| `renderToStaticHtmlDocument(markdown, options)` | Compile markdown, run browser-only renderers, serialize final output | HTML string |

Do not introduce more API surface until a real use case demands it. Most markdown renderers over-design early and end up carrying too many half-used options.

## 4. Adapter Contract

Every extension should answer the same questions.

| Question | Compile-time adapter | Execute-phase adapter |
| --- | --- | --- |
| What input does it read? | Fence text or markdown node | Placeholder DOM node |
| What output does it produce? | Final HTML or SVG string | Final SVG/HTML inside placeholder |
| Does it need browser APIs? | No | Yes |
| Can verification assert final output in Node only? | Usually yes | No, requires real browser |

Use a fenced-language map rather than a chain of special cases. Example:

| Fence language | Strategy |
| --- | --- |
| `mermaid` | Placeholder now, render in browser later |
| `dot` | Render to SVG during compile |
| `svg` | Parse as raw trusted markup, then sanitize |
| `math` | Usually unnecessary; prefer inline or block math syntax |

## 5. Client Mode vs Static Export Mode

These modes are not optional polish. They are separate products inside the same renderer.

### Client mode

Client mode emits HTML that still contains placeholders for browser-only engines. Use it when:

- previewing inside a browser page
- embedding output in an app that will execute diagram code at runtime
- debugging adapter state before final serialization

### Static export mode

Static export mode is the proof path. It must:

1. compile the markdown
2. open the result in a real browser
3. execute browser-only renderers
4. remove runtime-only script artifacts
5. serialize final HTML

If the team only tests client mode, they will miss export regressions. Static export is the stronger guarantee and should drive acceptance.

## 6. Placeholder Design

Placeholders must be boring and inspectable.

Use data attributes that reveal:

| Attribute | Meaning |
| --- | --- |
| `data-render-kind` | Which adapter owns this block |
| `data-render-state` | `pending`, `rendered`, or `failed` |

Store the source in a hidden child node, not in a magic JavaScript registry. That keeps the browser executor stateless and lets tests inspect the DOM without privileged hooks.

Bad placeholder patterns:

- custom inline script tags per block
- global mutable window registries
- encoded JSON blobs when plain text would do

Good placeholder pattern:

```html
<div class="mdr-render-block" data-render-kind="mermaid" data-render-state="pending">
  <pre class="mdr-source">flowchart TD
  A --> B</pre>
</div>
```

## 7. Why unified/remark/rehype fits this skill

The renderer should be teachable, extensible, and safe. The unified family is the best fit because it gives clear AST phases and predictable extension points.

| Need | unified fit |
| --- | --- |
| GFM support | `remark-gfm` |
| Math parsing | `remark-math` |
| Raw HTML handling | `rehype-raw` |
| Sanitization | `rehype-sanitize` |
| Final string output | `rehype-stringify` |

This ecosystem also makes it easy to explain the renderer in skill docs because each transformation stage has a name and a purpose.

## 8. Why Mermaid belongs in execute phase

Mermaid is browser-oriented. Even when libraries expose programmatic rendering, the most trustworthy proof path is still real browser execution.

Put Mermaid in execute phase when:

- the renderer promises final SVG output
- your tests need to prove the browser can materialize diagrams
- your exported HTML must not depend on a live runtime after generation

Keep Mermaid out of compile phase if doing so would require a brittle or fake environment. Use the real browser instead.

## 9. Why Graphviz is a good first extra adapter

Graphviz gives you a strong second rendering family without introducing a hosted service.

Benefits:

- deterministic SVG output
- no extra browser step required
- materially different from Mermaid
- proves the adapter model is not hard-coded to one engine

Graphviz is a better first extra adapter than code playgrounds, maps, or whiteboard tools because it adds expressive power without dragging in heavy runtime complexity.

## 10. Failure Boundaries

When something breaks, ask where it failed.

| Symptom | Likely layer |
| --- | --- |
| Markdown text missing | Compile pipeline |
| Mermaid placeholder present but no SVG in static export | Execute phase |
| Unsafe attribute survived | Sanitization configuration |
| Graphviz fence visible as raw code | Adapter interception failed |
| Runtime script leaked into final export | Serialization cleanup |

This table should guide debugging before you open unrelated code.

## 11. Keep the v1 scope narrow

V1 should prove the architecture, not win every markdown feature war.

Recommended v1 capabilities:

- CommonMark and GFM
- KaTeX inline and block math
- Mermaid static export via real browser
- trusted SVG and narrow raw HTML support
- DOT to SVG

Recommended later capabilities:

- WaveDrom
- PlantUML
- SMILES chemistry diagrams
- ABC music notation
- maps and code playgrounds

The architecture is good when later adapters plug in without changing the compile/execute contract.
