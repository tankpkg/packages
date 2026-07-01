# Verification And Debugging

Sources: Bulletproof workflow, Playwright documentation, real-browser verification patterns, deterministic export practices, 2025-2026 markdown renderer debugging experience.

Covers: RED to GREEN workflow for this renderer, fixture strategy, Playwright assertions, failure triage, regression discipline, and how to debug the correct layer instead of wandering through code.

## 1. Bulletproof loop for this skill

Use the renderer like a product, not like a documentation exercise.

The loop is:

1. write or update `INTENT.md`
2. add a fixture expressing the expected behavior
3. run a real test and watch it fail
4. implement the minimum change
5. rerun the real test until it passes

If you skip the fixture and test, you are back to shipping hope.

## 2. Why real browser verification matters

A string-based HTML assertion is not enough for browser-only renderers.

Mermaid is the clearest example:

- compile output may look plausible
- only a real browser proves the placeholder became SVG

That is why Playwright belongs in the verification path even for a markdown renderer.

## 3. Minimum fixture set

Keep one focused fixture per behavior cluster.

| Fixture | Purpose |
| --- | --- |
| mixed document | prove markdown, math, Mermaid, SVG, and DOT coexist |
| unsafe content | prove sanitization removes dangerous content |
| adapter-specific fixture | isolate one new renderer family |

Do not put every possible failure into one giant file. Smaller fixtures make failures legible.

## 4. What to assert first

Assert visible, structural outcomes before visual snapshots.

Good first assertions:

- heading text exists
- `.katex` exists
- Mermaid block contains one `svg`
- Graphviz block contains one `svg`
- dangerous script content is absent

These assertions are resilient and directly tied to the intent.

## 5. When screenshots help

Screenshots are secondary evidence.

Use them when:

- layout matters
- a renderer visually regressed but structural DOM still exists
- you need artifacts for review

Do not make screenshots the primary pass/fail signal in v1. DOM structure should drive first-line verification.

## 6. Failure triage table

When a test fails, classify the layer first.

| Failure | Likely layer | First question |
| --- | --- | --- |
| Missing heading or list | markdown pipeline | did compile output already lose content? |
| `.katex` missing | math transform | did math nodes get replaced? |
| Mermaid still pending | execute phase | did browser execution run? |
| Graphviz raw code still visible | adapter routing | was the fence intercepted? |
| `<script>` survived | sanitize/export cleanup | where did unsafe content enter or survive? |

This table should guide debugging before opening arbitrary files.

## 7. Console errors are part of the contract

For browser-executed renderers, console noise is not harmless.

Track and fail on:

- Mermaid parse errors
- runtime exceptions during export
- missing asset/runtime errors

If the page “looks fine” but logged execution failures, treat it as red until proven otherwise.

## 8. Runtime cleanup checks

Static export should remove runtime-only support artifacts after rendering.

Check for:

- stray script tags
- leftover pending placeholders
- error state blocks that should have been rendered

These checks catch a common class of “works locally, exports dirty HTML” regressions.

## 9. Add one negative test for every risky allowance

If you loosen the sanitization schema or add a new raw-content path, add a negative fixture in the same change.

Examples:

- allow a new SVG tag -> add an unsafe SVG attribute regression test
- allow new raw HTML block type -> add a script or event-handler regression test

Security changes without negative tests are incomplete.

## 10. Keep tests pointed at outcomes, not implementation trivia

Avoid assertions like:

- exact internal function names
- exact serialized whitespace
- giant full-document equality unless stable and intentional

Prefer assertions tied to user-visible behavior.

That means:

- visible structure
- final SVG presence
- sanitized dangerous content absence
- placeholder state changes

## 11. Regression discipline

When fixing a failing renderer bug:

1. reduce it to the smallest fixture that reproduces it
2. confirm the fixture fails
3. fix the renderer
4. keep the fixture forever

That is how the renderer becomes trustworthy over time.

## 12. Common debugging mistakes

| Mistake | Why it wastes time | Better move |
| --- | --- | --- |
| Reading all source files first | no behavioral target | start from the failing fixture |
| Tweaking sanitization blindly | hides root cause | identify exact tag or attr dropped or leaked |
| Comparing screenshots before DOM | expensive and fuzzy | assert DOM structure first |
| Assuming browser-only output exists in compile HTML | wrong phase model | compare client mode and static export |

## 13. Done criteria

A renderer change is done when:

1. intent is updated if behavior changed
2. fixtures cover the new behavior
3. real tests are green
4. exported HTML is clean
5. skill docs explain the new behavior or limitation

Anything less is partial progress, not completion.
