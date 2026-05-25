---
name: "@tank/mermaid-charts"
description: |
  Author and validate Mermaid diagrams with confidence — flowcharts, sequence,
  class, state, ER, gantt, pie, mindmap, gitgraph, C4, journey, quadrant,
  timeline, sankey, xychart, block, packet, kanban, architecture, radar.
  Covers chart-type selection, exact syntax per diagram, common pitfalls
  (reserved keywords, quoting, arrow variants, subgraph scoping), and a
  bundled validator that runs the official `mermaid.parse()` grammar locally
  via Node + jsdom — the same parser GitHub, GitLab, and Notion use to render.
  Sources: Mermaid.js official docs (v11.x), mermaid-js/mermaid source,
  NVIDIA/OpenShell lint-mermaid, GitLab check_mermaid, real-world parse errors.

  Trigger phrases: "mermaid chart", "mermaid diagram", "validate mermaid",
  "check mermaid syntax", "mermaid syntax error", "flowchart syntax",
  "sequence diagram syntax", "class diagram mermaid", "state diagram mermaid",
  "ER diagram mermaid", "gantt chart mermaid", "mermaid parser",
  "fix mermaid diagram", "mermaid won't render", "lint mermaid",
  "verify mermaid", "mermaid quality gate", "which mermaid diagram",
  "mermaid best practices", "mermaid not rendering"
---

# Mermaid Charts

Write Mermaid diagrams that render on the first try — and prove it by running
the same parser the renderer uses.

## Core Philosophy

1. **The parser is the source of truth.** Mermaid syntax has many edge cases
   (reserved words, quoting, arrow variants). Do not guess whether a chart
   is valid — run `scripts/validate-mermaid.mjs` and let the official
   `mermaid.parse()` grammar answer.
2. **Pick the right diagram for the relationship.** A flowchart for a state
   machine is a smell. See `references/chart-selection.md` before authoring.
3. **Validate every chart before claiming the task is done.** "Looks right"
   is not done. The validator returning exit code 0 is done.
4. **Read the error, do not shotgun fixes.** Mermaid parse errors point at a
   line and a token. Fix the indicated token, re-run, repeat. See
   `references/common-syntax-errors.md` for the error → fix lookup table.
5. **Prefer minimal, scannable diagrams.** A 40-node flowchart is unreadable.
   If a diagram needs explanation, split it or restructure it.

## When to Validate

| Situation                                               | Action                            |
| ------------------------------------------------------- | --------------------------------- |
| You wrote a new mermaid block                           | Run validator before reporting    |
| User reports a chart "doesn't render"                   | Run validator first, then triage  |
| Editing a doc that contains mermaid blocks              | Re-validate after edits           |
| Generating mermaid in code (templates, RAG output)      | Validate in CI / pre-commit       |
| Reviewing a PR that touches `.md` / `.mdx` with mermaid | Run validator on changed files    |

## Quick-Start: Validate a Chart

### One-time setup (per project)

```bash
cd scripts/
npm install      # installs mermaid + jsdom (pinned in package.json)
```

### Validate

```bash
# Validate all .md / .mdx files in a directory tree:
node scripts/validate-mermaid.mjs path/to/docs/

# Validate a single file:
node scripts/validate-mermaid.mjs path/to/diagram.md

# Validate a raw .mmd file or piped chart text:
node scripts/validate-mermaid.mjs --stdin < diagram.mmd
echo 'flowchart TD\n A --> B' | node scripts/validate-mermaid.mjs --stdin
```

Exit code `0` = all diagrams valid. Exit code `1` = at least one parse error
(printed in `file:line: message` format for editor jump-to-line). Exit code
`2` = validator itself crashed.

→ See `references/validation-workflow.md` for CI integration, error
interpretation, and the "passes here = renders there" guarantee.

## Quick-Start: Common Problems

### "Parse error on line N — Lexical error, Unrecognized text"

The token before the caret is the problem. Most common causes:

1. Reserved keyword used as a node ID (`end`, `class`, `default`, `subgraph`,
   `direction`, `style`, `linkStyle`). Rename or quote: `Node1["end"]`.
2. Unbalanced brackets: `A[Label` missing `]`, `A((Circle)` missing `)`.
3. Wrong arrow for diagram type — flowchart uses `-->`, sequence uses `->>`,
   class uses `<|--`, ER uses `||--o{`. See `references/mermaid-syntax-cheatsheet.md`.
4. Special characters in unquoted labels — `()`, `:`, `;`, `#`. Wrap label in
   quotes: `A["label: with colon"]`.

→ Full catalog in `references/common-syntax-errors.md`.

### "No diagram type detected"

The first non-empty, non-comment line must be a diagram declaration:
`flowchart TD`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`,
`erDiagram`, `gantt`, `pie`, `mindmap`, `gitGraph`, `journey`,
`quadrantChart`, `timeline`, `sankey-beta`, `xychart-beta`, `block-beta`,
`packet-beta`, `kanban`, `architecture-beta`, `radar-beta`, `C4Context`.

Frontmatter (`---\n...\n---`) is the only allowed prefix.

### "Chart renders on Mermaid Live but not on GitHub"

Version skew. The bundled validator pins Mermaid to the same major version
as common renderers. Re-run the validator; if it passes here, it renders on
GitHub. If it fails, fix the indicated issue.

## Decision Trees

### Which Diagram Type?

| You are showing…                       | Use                  | Declaration         |
| -------------------------------------- | -------------------- | ------------------- |
| Process / decision flow                | Flowchart            | `flowchart TD`      |
| Interaction over time between actors   | Sequence diagram     | `sequenceDiagram`   |
| OO structure (classes, inheritance)    | Class diagram        | `classDiagram`      |
| State machine / lifecycle              | State diagram        | `stateDiagram-v2`   |
| Data model / table relationships       | ER diagram           | `erDiagram`         |
| Project schedule                       | Gantt                | `gantt`             |
| Proportional parts of a whole          | Pie                  | `pie`               |
| Concept hierarchy / brainstorm         | Mindmap              | `mindmap`           |
| Git branching / release history        | Git graph            | `gitGraph`          |
| User journey with emotion              | User journey         | `journey`           |
| 2x2 strategic matrix                   | Quadrant             | `quadrantChart`     |
| Events on a horizontal axis            | Timeline             | `timeline`          |
| Flow volumes between stages            | Sankey               | `sankey-beta`       |
| Trend over numeric axes                | XY chart             | `xychart-beta`      |
| System architecture (services, edges)  | Architecture         | `architecture-beta` |
| Software architecture (Context/Container/Component) | C4      | `C4Context`         |

If your chart needs 2+ of these at once, you picked the wrong type — split
the chart. See `references/chart-selection.md` for anti-patterns.

### Validate-or-not?

| Signal                                          | Validate? |
| ----------------------------------------------- | --------- |
| Hand-wrote a chart                              | Yes       |
| Edited an existing chart                        | Yes       |
| Copy-pasted from Mermaid Live Editor            | Yes (version skew) |
| Generated programmatically                      | Yes (always) |
| Chart was already in the repo and untouched     | No        |

## Authoring Workflow

1. **Pick the diagram type** using the table above.
2. **Write the chart** following the per-type syntax in
   `references/mermaid-syntax-cheatsheet.md`.
3. **Validate** with `node scripts/validate-mermaid.mjs <path>`.
4. **If errors:** open `references/common-syntax-errors.md`, find the error
   pattern, apply the fix, re-validate.
5. **If clean:** the chart will render anywhere the official Mermaid parser
   runs (GitHub, GitLab, Notion, Obsidian, VS Code preview, mermaid.live).
6. **Only then** mark the authoring task complete.

## Reference Files

| File                                       | Contents                                                                                                                |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `references/mermaid-syntax-cheatsheet.md`  | Per-diagram syntax: declarations, nodes, edges/arrows, labels, subgraphs, styling. One section per diagram type.        |
| `references/common-syntax-errors.md`       | Error message → fix lookup. Reserved keywords, quoting rules, arrow mismatches, indentation, frontmatter pitfalls.      |
| `references/chart-selection.md`            | When to use each diagram type. Anti-patterns (flowchart-as-state-machine, sequence-as-flowchart). Splitting heuristics. |
| `references/validation-workflow.md`        | Running the validator, interpreting output, CI integration, the parser-equivalence guarantee, troubleshooting.          |

## Scripts

| Script                          | Purpose                                                                                                                          |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `scripts/validate-mermaid.mjs`  | Validates all mermaid blocks in `.md`/`.mdx` files or a piped chart. Uses the official `mermaid.parse()` grammar via Node+jsdom. |
| `scripts/package.json`          | Pins `mermaid` and `jsdom` so behavior is reproducible. Run `npm install` in `scripts/` once.                                    |
