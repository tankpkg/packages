# Extended Renderers

Sources: Mermaid documentation, Graphviz WASM documentation, PlantUML ecosystem docs, WaveDrom docs, abcjs docs, smiles-drawer docs, GitHub and docs-site markdown behavior, 2025-2026 renderer ecosystem research.

Covers: Renderer families beyond plain markdown, what to implement first, what to defer, and how to choose the right adapter for the content instead of forcing everything into one engine.

## 1. Start with categories, not packages

Before picking libraries, classify the rendering need.

| Category | Example | Typical phase |
| --- | --- | --- |
| Native markdown / GFM | tables, footnotes, task lists | Compile |
| Deterministic diagram engine | DOT / Graphviz | Compile |
| Browser-oriented diagram engine | Mermaid | Execute |
| Niche notation | ABC music, SMILES chemistry | Depends on library |
| Heavy interactive embed | maps, code playgrounds | Execute |

This classification stops scope creep. Many requests that sound new are actually already covered by GFM.

## 2. Recommended first extra adapter: Graphviz

Graphviz is the best first expansion beyond Mermaid.

Why:

- strong text-to-diagram model
- deterministic SVG output
- no hosted service required when using WASM
- complements Mermaid instead of duplicating it

Use Graphviz when the author needs explicit graph layout control or already writes DOT.

## 3. Mermaid variants are still Mermaid, not new engines

Mermaid supports more than just flowcharts.

Treat these as syntax families inside the same engine:

- flowchart
- sequence
- class
- state
- ER
- timeline
- gantt
- git graph
- mindmap

If a user wants one of these, do not add a new adapter. Reuse the Mermaid path.

## 4. PlantUML tradeoff

PlantUML is powerful but comes with one of two costs:

1. a remote service dependency, or
2. a heavier local setup

That makes it a weaker v1 candidate than Graphviz.

Use PlantUML when:

- the team already speaks PlantUML
- UML expressiveness matters more than setup simplicity
- you are willing to document the operational dependency clearly

## 5. WaveDrom

WaveDrom is a good specialized adapter for timing diagrams.

Use it when the markdown documents hardware, protocols, clocks, or digital state transitions. Do not use Mermaid for this if the data is fundamentally timing-oriented.

WaveDrom should usually be a later adapter because:

- it serves a narrower audience
- it increases browser/runtime complexity
- its value only appears in certain domains

## 6. nomnoml

nomnoml is useful when the team wants lightweight UML-like diagrams without the full PlantUML ecosystem.

Good fit:

- quick class or relationship sketches
- small docs where simplicity matters more than UML completeness

Less ideal when:

- you need enterprise UML coverage
- diagrams are authored outside the docs team in a stricter UML format

## 7. ABC music notation

ABC notation is worth mentioning because it proves markdown can render domain-specific notation beyond software diagrams.

Use it when docs need:

- short melodic notation
- educational music content
- low-friction music examples inside markdown

This is a great “more ideas” example even if not implemented in v1.

## 8. SMILES chemistry diagrams

SMILES rendering is another strong example of notation-to-visual transformation.

Use it when docs cover:

- chemistry education
- molecule examples
- domain-specific scientific notes

Like ABC notation, it expands the skill’s advice surface even if the first prototype only teaches the extension pattern.

## 9. Maps and GeoJSON

Maps are tempting because GitHub and other tools treat GeoJSON specially. But they are usually not the right v1 renderer target.

Why to defer:

- interactive map libraries are heavier than diagram engines
- styling and basemap decisions add scope fast
- verification is harder than simple SVG assertions

Mention maps as a future branch, not a first extension.

## 10. Code playgrounds

Code playgrounds are not just renderers. They are mini execution environments.

That means:

- more sandboxing concerns
- larger bundle/runtime cost
- stronger safety requirements

They belong in a later phase unless the user explicitly wants executable code blocks as a primary product feature.

## 11. Selection matrix

Use this matrix when choosing the next adapter.

| Need | Best first choice | Why |
| --- | --- | --- |
| General software diagram | Mermaid | broad syntax coverage |
| Precise graph layout | Graphviz | deterministic DOT-to-SVG |
| Timing diagram | WaveDrom | domain fit |
| Lightweight UML sketch | nomnoml | simpler than PlantUML |
| Full UML ecosystem | PlantUML | feature depth |
| Music notation | ABC.js | strong niche value |
| Chemistry notation | smiles-drawer | strong niche value |

## 12. How to decide what belongs in v1

An adapter belongs in v1 when:

1. it serves a broad enough audience
2. it fits the compile/execute model cleanly
3. it can be verified with real tests without heroic setup

That is why Graphviz is a better early adapter than maps or playgrounds.

## 13. Good “more ideas” to suggest to users

When a user asks for more ideas beyond Mermaid, math, markdown, SVG, and HTML, suggest grouped options:

### Native markdown and presentation features

- tables
- task lists
- footnotes
- `diff`
- `kbd`
- alerts or callouts
- `<details>` blocks

### True renderer adapters

- Graphviz / DOT
- PlantUML
- WaveDrom
- nomnoml
- ABC music notation
- SMILES chemistry diagrams

### Later-phase interactive or embed systems

- GeoJSON maps
- code playgrounds
- interactive data tables
- org charts or network graphs
- whiteboard-style embeds

This grouping helps users ask better follow-up questions.

## 14. Don’t confuse “supports” with “implements”

The skill can be expert in more renderer families than the first prototype fully implements.

That is acceptable as long as the docs are honest:

- implemented now
- recommended next
- intentionally deferred

Users trust clear boundaries more than inflated feature claims.
