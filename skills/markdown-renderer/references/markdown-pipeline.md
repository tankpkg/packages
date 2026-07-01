# Markdown Pipeline

Sources: unified documentation, remark documentation, rehype documentation, GitHub Flavored Markdown specification, 2025-2026 markdown parser ecosystem research.

Covers: Markdown parsing stages, GFM handling, raw HTML parsing, fence interception, compile-time versus execute-time transforms, and practical patterns for keeping an extended markdown pipeline understandable.

## 1. Pipeline shape

Use a pipeline with explicit phases.

```txt
markdown string
  -> remark-parse
  -> remark-gfm
  -> remark-math
  -> custom mdast transforms
  -> remark-rehype
  -> rehype-raw
  -> rehype-sanitize
  -> rehype-stringify
  -> HTML document wrapper
```

If the pipeline cannot be drawn in one screen, it is too complicated for a v1 skill.

## 2. What each stage owns

| Stage | Owns | Should not own |
| --- | --- | --- |
| `remark-parse` | raw markdown tokenization | HTML sanitization |
| `remark-gfm` | tables, task lists, footnotes, autolinks, strikethrough | diagram rendering |
| `remark-math` | math node detection | KaTeX output generation policy |
| Custom remark transforms | fence interception, math HTML injection, adapter routing | browser execution |
| `remark-rehype` | markdown AST to HTML AST conversion | safety policy |
| `rehype-raw` | raw HTML parsing | trusted-vs-untrusted business logic |
| `rehype-sanitize` | allowlist enforcement | runtime rendering |
| `rehype-stringify` | final HTML string output | browser-only transforms |

When a stage starts owning another stage’s job, complexity spikes.

## 3. Use GFM before inventing features

A lot of “extended markdown” is already solved by GFM.

| Feature | Native via GFM or HTML? | Needs custom adapter? |
| --- | --- | --- |
| Tables | Yes | No |
| Task lists | Yes | No |
| Footnotes | Yes | No |
| Autolinks | Yes | No |
| `diff` blocks | Yes, standard code fence | No |
| `<details>` / `<summary>` | Yes, raw HTML | No |
| Mermaid | No | Yes |
| DOT / Graphviz | No | Yes |

Do not write adapters for features the markdown parser already gives you. Save adapters for truly new behavior.

## 4. Fence interception pattern

Custom fenced languages should be intercepted while the tree is still in markdown AST form.

Why:

- the original fence language is still visible
- the original source text is still intact
- replacing nodes is simpler before HTML conversion

Recommended fence workflow:

1. find `code` nodes
2. inspect `node.lang`
3. route to a small adapter map
4. replace the node with HTML or a placeholder

This keeps extensions local and discoverable.

## 5. Compile-time vs execute-time choice

Every renderer extension should answer one question first: can it produce final output without a browser?

| Extension | Preferred phase | Reason |
| --- | --- | --- |
| KaTeX | Compile | Deterministic HTML output |
| Graphviz/DOT | Compile | Deterministic SVG from WASM |
| Mermaid | Execute | Real browser rendering is safer to verify |
| Interactive maps | Execute | Needs browser runtime |
| Code playgrounds | Execute | Browser runtime and possibly sandboxing |

This table is more important than the specific library choice. Phase placement determines the whole system shape.

## 6. Raw HTML parsing rule

If raw HTML is allowed, parse it after the markdown AST is converted to HTML AST.

That is why `rehype-raw` exists. It turns embedded HTML strings into real HAST nodes, which sanitization can then inspect structurally.

Do not sanitize raw HTML with brittle string regexes alone. Structural parsing gives safer and more predictable results.

## 7. Sanitization placement

Sanitization belongs after unsafe content enters the HTML AST and before final output is trusted.

Use this rule:

- anything coming from the markdown author is unsafe
- anything produced by trusted libraries during compile can be allowed by policy

Practical consequence:

- parse raw author HTML
- sanitize it
- stringify it

For library-generated content such as KaTeX output, either:

1. generate it before sanitize and allow the needed tags/classes, or
2. generate it after sanitize if the generated HTML is fully trusted

Both can work. Pick one and keep it consistent.

## 8. Math handling pattern

Math is usually cleaner when parsed as markdown syntax and rendered in compile phase. That keeps math out of the browser execution queue and avoids runtime dependencies for something deterministic.

Good pattern:

- `remark-math` finds inline and block math
- custom transform or `rehype-katex` renders HTML
- output is already final in both client and static-export modes

This lets the browser execution phase focus on what really needs it.

## 9. Placeholder rules

If a renderer defers to execute phase, the placeholder must preserve enough data to finish the job later.

Minimum contract:

| Field | Why |
| --- | --- |
| renderer kind | so execute phase knows which engine to run |
| source text | so the engine can render without hidden globals |
| state marker | so tests and debugging can inspect lifecycle |

Keep placeholders HTML-based rather than JavaScript-based. A DOM node is easier to inspect, easier to sanitize around, and easier to verify in Playwright.

## 10. Document wrapper rule

Return a full HTML document from the public render functions, not just a fragment.

Why:

- Playwright can load it directly
- CLI output is immediately inspectable
- static export and client mode can share the same wrapper

The wrapper should include only:

- metadata
- small baseline styles
- the rendered main content

Avoid embedding runtime scripts in the client-mode HTML unless that is the explicit product. Keep execution under the renderer’s control.

## 11. Add new adapters safely

When adding a new fenced language:

1. define a fixture first
2. decide compile or execute phase
3. add one adapter function
4. add one positive and one negative test
5. update the skill docs and decision tree

If an adapter needs special cases spread across multiple files, the architecture is drifting.

## 12. Common pipeline mistakes

| Mistake | Why it hurts | Better move |
| --- | --- | --- |
| Running Mermaid during parse time with a fake DOM | brittle, hard to trust | use real browser execute phase |
| Sanitizing after export-time script injection | leaks runtime artifacts | remove runtime scripts before serialization |
| Treating all raw HTML as trusted | XSS and layout risks | explicit allowlist and safe default |
| Replacing code fences after HTML stringification | hard to reason about | intercept code fences in mdast |
| Cramming all logic into one function | hard to extend and debug | separate compile and execute helpers |

## 13. Selection guidance

Choose unified/remark/rehype when:

- you need AST-level control
- you need to explain the pipeline to others
- you plan to support several renderer families

Choose a simpler parser only when:

- your scope is plain markdown with minimal extension
- you do not need raw HTML policy control
- you do not need AST transforms

For this skill, the AST-first model is the right tradeoff.
