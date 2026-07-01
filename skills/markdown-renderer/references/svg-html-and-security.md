# SVG, HTML, And Security

Sources: rehype-sanitize documentation, hast-util-sanitize documentation, SVG specification, GitHub sanitization model, 2025-2026 secure markdown rendering guidance.

Covers: Trusted versus untrusted raw content, SVG allowlists, dangerous attributes and protocols, security defaults, and practical sanitization rules for extended markdown.

## 1. Default stance

Raw HTML is not neutral. It is a security boundary.

Use this rule:

- trusted content may be preserved through a narrow allowlist
- untrusted content must be sanitized before it becomes final HTML

Do not enable raw HTML just because markdown authors asked for flexibility. The renderer owns the security boundary, not the author.

## 2. Why SVG needs explicit treatment

SVG is easy to mistake for harmless image markup. It is actually active document markup with a long history of script and URL-based abuse.

Potential problems include:

- embedded script tags
- event handler attributes such as `onload`
- dangerous links or protocol abuse
- elements you did not intend to support

Treat SVG as HTML-like markup that happens to draw pictures, not as a passive blob.

## 3. Trusted versus untrusted model

Decide which model your renderer uses.

| Model | When to use | Tradeoff |
| --- | --- | --- |
| Trusted author content | internal docs, controlled inputs | more flexibility, more responsibility |
| Untrusted user content | user-generated markdown, external content | fewer surprises, stricter output |

For a reusable skill, teach strict defaults first and opt-in trust later.

## 4. Allowlist strategy

Allow only what the renderer demonstrably needs.

Good candidates for SVG support:

- `svg`
- `g`
- `path`
- `circle`
- `ellipse`
- `rect`
- `line`
- `polyline`
- `polygon`
- `text`
- `tspan`
- `defs`
- `marker`
- `pattern`
- `clipPath`
- `title`
- `desc`

Avoid broad support for unfamiliar SVG elements until a real example justifies them.

## 5. Attribute rules

Attributes should be allowlisted with the same discipline as tags.

| Attribute type | Usually safe when scoped | Notes |
| --- | --- | --- |
| geometry (`x`, `y`, `cx`, `cy`, `r`, `d`) | Yes | necessary for shapes |
| paint (`fill`, `stroke`, `strokeWidth`) | Yes | common presentation attributes |
| accessibility (`role`, `ariaLabel`, `ariaHidden`) | Yes | useful for meaningful SVG |
| event handlers (`onload`, `onclick`) | No | remove |
| external URLs | Rarely | only allow known-safe protocols |

If you are not sure whether an attribute is needed, leave it out until a fixture proves otherwise.

## 6. Dangerous patterns to strip

Always strip or neutralize:

- `<script>`
- `on*` event handler attributes
- `javascript:` URLs
- `data:` URLs unless explicitly justified
- broad iframe or embed tags

This is where many markdown renderers quietly fail. They sanitize obvious scripts but forget URL protocols or event handlers.

## 7. Sanitization placement rule

Run sanitization after raw HTML has been parsed into a tree and before final output is trusted.

That means:

1. parse markdown
2. parse embedded raw HTML into HAST
3. sanitize
4. stringify

If you sanitize too early, dangerous content can sneak back in later. If you sanitize too late, you are serializing unsafe markup.

## 8. Allow `data-*` deliberately

Extended markdown renderers often use `data-*` attributes for placeholder state. Allow them, but only because the renderer itself uses them as part of the contract.

Examples:

- `data-render-kind`
- `data-render-state`

Do not treat this as permission to allow arbitrary inline behavior. `data-*` is for inert metadata, not for execution.

## 9. Class names are not the real threat

Many sanitization discussions get stuck on CSS classes. Classes matter less than executable or navigational attributes.

Safe default:

- allow classes needed for renderer output and styling
- stay strict on executable attributes and protocols

This is especially important for KaTeX or other library-generated markup that depends on class names for layout.

## 10. Accessibility for SVG

Meaningful SVG should carry semantic hints.

| SVG purpose | Recommendation |
| --- | --- |
| informative diagram | `role="img"` with label or title |
| decorative flourish | `aria-hidden="true"` |

Do not rely on visuals alone when the SVG communicates structure or state.

## 11. Security defaults for this skill

Use these defaults unless the user explicitly loosens them:

1. raw HTML allowed only through sanitization
2. trusted SVG tag subset only
3. no script tags in final output
4. no event handlers in final output
5. no dangerous protocols in `href` or `src`

This default profile makes the renderer useful for real docs without becoming an XSS playground.

## 12. Verification rules

Security behavior must be proven with negative fixtures.

At minimum, keep fixtures for:

- raw `<script>` tags
- inline `onclick` or `onload`
- dangerous URLs
- SVG carrying forbidden attributes

Each fixture should answer one clear question: did the dangerous thing survive or not?

## 13. Common mistakes

| Mistake | Why it is wrong | Better move |
| --- | --- | --- |
| Allowing all raw HTML because docs are “internal” | internal content becomes external over time | keep strict defaults and document opt-in trust |
| Regex-only sanitization | misses structural edge cases | use structural sanitize after raw parse |
| Forgetting exported HTML cleanup | runtime support scripts leak into final docs | remove runtime scripts before serialization |
| Allowing broad SVG features “just in case” | widens attack surface | add tags and attrs only when a fixture needs them |

## 14. When to relax the policy

Relax the policy only when all three are true:

1. the content source is controlled
2. a real use case needs the markup
3. a fixture and verification rule cover the new allowance

This keeps every exception explicit and test-backed.
