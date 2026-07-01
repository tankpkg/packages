# Math And Mermaid

Sources: KaTeX documentation, Mermaid documentation, GitHub Markdown feature behavior, browser-based rendering practices, 2025-2026 ecosystem research.

Covers: Compile-time math rendering, execute-phase Mermaid rendering, export strategy, versioning, and the sharp edges that usually break mixed markdown documents.

## 1. Treat math and Mermaid differently

Math and Mermaid often appear together in docs, but they do not belong in the same phase.

| Feature | Best phase | Why |
| --- | --- | --- |
| KaTeX math | Compile | deterministic HTML output |
| Mermaid | Execute | browser-oriented runtime and SVG materialization |

If you force them into the same phase, one of them gets worse.

## 2. KaTeX compile-time pattern

KaTeX is ideal for compile phase because it can turn math into HTML immediately.

Recommended pattern:

1. parse inline and block math syntax
2. call `katex.renderToString`
3. inject HTML into the markdown AST transform
4. carry the output through sanitization and final stringification

This produces stable output in both client and static-export modes.

## 3. KaTeX options that matter

Use the smallest safe option set first.

| Option | Recommendation | Why |
| --- | --- | --- |
| `throwOnError` | `false` | renderer should not crash on bad input |
| `strict` | `ignore` or `warn` | reduce brittle user-facing failures |
| `displayMode` | match node type | correct block vs inline layout |
| `output` | `html` for simple sanitization | avoids extra MathML complexity in v1 |

If you need accessibility-first MathML later, revisit the sanitize schema and verification rules together.

## 4. Mermaid execute-phase pattern

Mermaid should be carried as a placeholder until a real browser can render it.

Recommended sequence:

1. replace Mermaid fences with placeholder DOM
2. open the compiled document in a browser
3. load Mermaid runtime
4. call Mermaid render for each placeholder
5. replace placeholder content with SVG
6. mark the block as rendered or failed
7. remove runtime-only scripts before serialization

This sequence gives you inspectable state and exportable output.

## 5. Placeholder format for Mermaid

Keep the placeholder simple.

```html
<div class="mdr-render-block" data-render-kind="mermaid" data-render-state="pending">
  <pre class="mdr-source">flowchart TD
  A --> B</pre>
</div>
```

Why this works:

- source survives intact
- tests can assert state changes
- no hidden JSON or global registries are needed

## 6. Mermaid initialization rules

Initialize Mermaid deliberately.

Use these defaults unless you have a reason not to:

| Setting | Recommendation |
| --- | --- |
| `startOnLoad` | `false` |
| `securityLevel` | `strict` by default |
| unique IDs | generate per block |

`startOnLoad` should stay off because the renderer owns execution timing. Letting Mermaid auto-run makes tests and export behavior less predictable.

## 7. Static export requirements

A static export path is complete only when all of the following are true:

1. Mermaid placeholders become SVGs
2. KaTeX output is already present
3. runtime scripts are removed from final HTML
4. no execution errors are left in console or DOM state

Do not confuse “the page previewed correctly” with “the exported document is correct.” Static export is the stronger product.

## 8. Failure modes to expect

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Mermaid block remains empty | runtime did not execute | was Mermaid script loaded? |
| Placeholder still `pending` | render loop skipped block | selector and state handling |
| KaTeX missing entirely | math nodes not transformed | markdown AST transform |
| Mermaid script survives in final HTML | serialization cleanup missing | export cleanup step |
| Diagram renders in preview but not export | browser execution path differs | compare client vs static mode |

## 9. Version pinning matters more for Mermaid

Math output is usually stable enough within a narrow KaTeX version band. Mermaid output can shift more visibly.

Pin Mermaid deliberately and avoid broad version drift if:

- screenshot comparisons matter
- downstream consumers depend on SVG structure
- tests assert on labels or class names

When upgrading Mermaid:

1. run the static export fixtures
2. compare SVG shape and labels
3. update docs if diagram syntax support changed

## 10. What to assert in tests

Avoid brittle full-SVG equality for v1.

Better assertions:

| Feature | Assert |
| --- | --- |
| KaTeX | `.katex` exists and is visible |
| Mermaid | placeholder contains exactly one `svg` after export |
| Mermaid state | `data-render-state="rendered"` |
| Mixed document | headings, lists, and diagrams all coexist |

This catches real regressions without overfitting to implementation noise.

## 11. Mermaid is not the only diagram type

Mermaid is great for broad doc usability, but it should not become the only mental model for extensions.

Teach this distinction:

| Need | Better choice |
| --- | --- |
| flow, sequence, state, timeline | Mermaid |
| precise node-edge graph with DOT syntax | Graphviz |
| digital timing diagram | WaveDrom |
| lightweight UML-ish sketch | nomnoml |

This helps users choose the right renderer instead of forcing everything into Mermaid syntax.

## 12. Good defaults for mixed documents

For docs containing both math and diagrams:

1. render math during compile
2. defer Mermaid to browser execution
3. keep CSS minimal
4. do not hide errors silently

If Mermaid fails, mark the block failed. If KaTeX fails, preserve readable fallback output and keep the document alive.

The goal is resilient docs, not perfect silence.
