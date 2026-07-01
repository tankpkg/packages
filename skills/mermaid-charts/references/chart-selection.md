# Chart Type Selection

Sources: Mermaid.js official diagram catalog, Tufte (The Visual Display of
Quantitative Information, 2001), Few (Show Me the Numbers, 2012), Mermaid
Chart usage research (2024), C4 model documentation (Brown, 2018).

Covers: matching diagram type to the relationship being shown, anti-patterns
(using the wrong type), and heuristics for splitting overgrown diagrams.

## The selection question

Before writing any chart, answer: **what kind of relationship am I
showing?** The relationship determines the diagram type.

| Relationship                          | Diagram type     | Declaration         |
| ------------------------------------- | ---------------- | ------------------- |
| Decision / branching control flow     | Flowchart        | `flowchart TD`      |
| Time-ordered message exchange         | Sequence         | `sequenceDiagram`   |
| Static structure (classes, types)     | Class            | `classDiagram`      |
| Transitions between discrete states   | State            | `stateDiagram-v2`   |
| Entities with cardinality / relations | ER               | `erDiagram`         |
| Tasks scheduled across time           | Gantt            | `gantt`             |
| Parts of a whole (proportion)         | Pie              | `pie`               |
| Idea / topic hierarchy                | Mindmap          | `mindmap`           |
| Commit / branch history               | Git graph        | `gitGraph`          |
| Step-by-step user experience          | User journey     | `journey`           |
| 2D strategic positioning              | Quadrant         | `quadrantChart`     |
| Events along a time axis              | Timeline         | `timeline`          |
| Flow magnitudes between stages        | Sankey           | `sankey-beta`       |
| Trend across continuous axes          | XY chart         | `xychart-beta`      |
| Layout-first composition              | Block            | `block-beta`        |
| Services + connections + groups       | Architecture     | `architecture-beta` |
| Software system (C/C/C/D abstractions)| C4               | `C4Context`         |
| Network packet structure              | Packet           | `packet-beta`       |
| Multi-axis comparison (spider)        | Radar            | `radar-beta`        |

## Decision flow

```
Is order / time significant?
├── Yes — between actors        → sequenceDiagram
├── Yes — for one entity        → stateDiagram-v2 or timeline
├── Yes — for projects / tasks  → gantt
└── No
    │
    Is it a structure (types, entities)?
    ├── Classes + inheritance    → classDiagram
    ├── Entities + cardinality   → erDiagram
    ├── Services + groups        → architecture-beta or C4*
    └── No
        │
        Is it a flow / decision?
        ├── Yes (decisions, branches)  → flowchart
        ├── Magnitudes between stages  → sankey-beta
        └── No
            │
            Is it a quantity?
            ├── Parts of a whole       → pie
            ├── Trend / continuous     → xychart-beta
            ├── Positioning in 2 dims  → quadrantChart
            └── Hierarchy of ideas     → mindmap
```

## Anti-patterns

### Anti-pattern 1: Flowchart as state machine

**Smell:** flowchart nodes are named after states ("Idle", "Loading",
"Error"), edges are events ("click", "fetch").

**Why bad:** loses semantics that state diagrams give for free:
initial/final states (`[*]`), composite states, concurrent regions,
choices, history.

**Fix:** convert to `stateDiagram-v2`. Each flowchart node becomes a state,
each edge becomes a transition with an event label.

### Anti-pattern 2: Flowchart as sequence

**Smell:** vertical chain of nodes, each labeled "A calls B" or "B replies
to A".

**Why bad:** does not show actors, parallel lifelines, activation periods,
or async messages. Reviewers cannot tell who initiates what.

**Fix:** convert to `sequenceDiagram`. Extract actors as `participant`s,
edges become arrows between participants.

### Anti-pattern 3: Sequence as flowchart

**Smell:** a `sequenceDiagram` with one participant and a chain of messages
to itself — modeling internal logic, not a conversation.

**Why bad:** sequence diagrams are for **inter-actor** communication. A
single-actor sequence is just a flowchart drawn sideways.

**Fix:** use `flowchart TD` instead.

### Anti-pattern 4: Class diagram as ER diagram

**Smell:** "classes" are database tables, "methods" are absent,
"associations" carry cardinality like `1..*`.

**Why bad:** ER diagrams give you native cardinality syntax (`||--o{`),
attribute keys (`PK`, `FK`, `UK`), and identifying vs non-identifying
relationships. Class diagrams force you to fake all of this.

**Fix:** use `erDiagram`. Attributes go inside the entity block, not as
"members".

### Anti-pattern 5: Pie chart with > 6 slices

**Smell:** pie chart of "browser market share" with 11 slices, three
slivers labeled "Other Edge variant".

**Why bad:** humans cannot compare angles below ~5%. Slivers are noise.

**Fix:** group small slices into "Other", or switch to a bar chart
(`xychart-beta` with `bar` series). Pie is for ≤ 6 well-separated parts.

### Anti-pattern 6: Gantt without a critical path

**Smell:** Gantt chart with tasks but no `crit` markers and no dependencies
(`after`).

**Why bad:** a Gantt without dependencies is just a stacked-bar timeline.
The whole point of Gantt is showing critical paths and slack.

**Fix:** add `after task-id` to express dependencies; mark blocking tasks
`crit`.

### Anti-pattern 7: Architecture diagram with no groups

**Smell:** `architecture-beta` with 20 services, no `group` definitions.

**Why bad:** architecture diagrams scale by **encapsulation**. Without
groups, a viewer cannot tell which services belong together.

**Fix:** add `group <id>(cloud)[Label]` blocks and place services `in <id>`.
Aim for 3–7 groups; nest if needed.

## Splitting overgrown diagrams

A diagram that does not fit on one screen is two diagrams. Heuristics:

1. **Count edges.** > 20 edges → split. Most readers track ~7 at once.
2. **Count nodes.** > 15 nodes → split by subsystem or by phase.
3. **Multiple diagram types implied.** If you keep wanting to add
   "happy path" arrows, "error path" arrows, and "state on failure", you
   have a flowchart, a sequence, and a state diagram tangled together.
4. **Audience differs by region.** If the left half is for engineers and
   the right half is for executives, split by audience.

### Splitting strategies

| Strategy            | When to use                                  |
| ------------------- | -------------------------------------------- |
| By **subsystem**    | Architecture / class / ER diagrams           |
| By **phase**        | Sequence / flowchart (login phase, work phase) |
| By **abstraction**  | C4 (context → container → component)         |
| By **happy/error**  | Sequence (separate happy-path and error)     |
| By **state group**  | State diagram (composite state → its own diagram) |

## Choosing direction (flowcharts, state)

| Direction     | Use when…                                    |
| ------------- | -------------------------------------------- |
| `TD` (top→down) | Linear pipelines, decisions, default        |
| `LR` (left→right) | Wide diagrams, narrow vertical space       |
| `BT` (bottom→up) | Build / dependency graphs ("X depends on Y") |
| `RL` (right→left) | Right-to-left reading or reverse data flow |

Default to `TD`. Switch to `LR` only when the diagram is wider than tall.

## C4 vs Architecture-beta

Both model systems-of-services. Choose:

- **C4** when your audience knows the C4 model (Context, Container,
  Component, Code). Best for software architecture documents.
- **Architecture-beta** when you want native cloud-icon support
  (`cloud`, `database`, `server`, `disk`, `internet`) and lightweight
  grouping. Best for infra diagrams.

For deeper coverage of architecture documentation patterns, see the
`@tank/crystal-clear-docs` skill (SVG diagrams reference).

## Style minimalism

Across all diagram types: **do not style your way out of a wrong type**.
If a chart needs custom colors and icons to be readable, it is the wrong
chart type. Refactor first, style second.

Default theme (`config: theme: default` or omit) usually beats custom
themes on hosted renderers — they often override your styles to match the
surrounding doc.

## Selection examples

| Scenario                                                | Diagram        |
| ------------------------------------------------------- | -------------- |
| "How does the login API process a request?"             | sequenceDiagram |
| "What states can an Order be in?"                       | stateDiagram-v2 |
| "How are Customers, Orders, and LineItems related?"     | erDiagram      |
| "What's the deployment topology of our services?"       | architecture-beta |
| "What does our roadmap look like over the next quarter?"| gantt          |
| "How does the homepage funnel users to signup?"         | flowchart TD   |
| "Where does our energy budget go?"                      | sankey-beta    |
| "How do features compare on impact vs effort?"          | quadrantChart  |
| "Show the history of major releases"                    | timeline OR gitGraph |
| "Explain the class hierarchy of our auth library"       | classDiagram   |
| "Brainstorm topics for the team offsite"                | mindmap        |
| "Visualize monthly revenue trend"                       | xychart-beta   |
