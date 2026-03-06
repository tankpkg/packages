# Quality Enforcement

Sources: ArcBlock/idd anti-accretion system (MIT), FORGE phase validation
gates (MIT), production bloat analysis.

Covers: Anti-accretion rules, budget enforcement mechanics, net-reduce
critique protocol, convergence checkpoints, scope guard, and the devil's
advocate pattern.

## Why Intent Files Bloat

Every conversation adds content. Every brainstorm adds "just one more
thing." Every review adds a clarification. Left unchecked, a 150-line
intent becomes 800 lines of mixed analysis, decisions, research, and
actual constraints. At that point the AI can't separate signal from
noise, and the intent fails its primary job.

IDD has five anti-accretion mechanisms. Each one fights a different
bloat vector.

---

## Mechanism 1: The Size Budget

Hard line counts. No negotiation.

| Lines | Status | Consequence |
|-------|--------|-------------|
| ≤ 300 | Healthy | All clear |
| 301–500 | Warning | Flag for review. Consider splitting or trimming. |
| > 500 | Blocked | All work on this module stops. Critique must reduce. |

**Count method:** `wc -l INTENT.md`, excluding YAML frontmatter lines.

**When you hit the ceiling:**

1. **Anchor trace** — Read every section. Ask: "does this serve the
   anchor?" Cut anything that doesn't.
2. **Analysis purge** — Move background research, exploration, and
   comparisons to `planning/`. Only constraints stay.
3. **Module split** — If the intent covers two distinct responsibilities,
   split into two INTENT.md files with their own anchors.
4. **Dedup** — Check for the same constraint stated in different words.
   Check for overlap with project-level intent.
5. **Simplify** — Replace 10-line prose explanations with 3-line
   constraint tables.

---

## Mechanism 2: The Net-Reduce Critique

The critique step has one iron rule: the file must end up shorter.

**Protocol:**

```
1. Record before: wc -l INTENT.md → before_lines
2. Run critique (see lifecycle for full process)
3. Record after: wc -l INTENT.md → after_lines
4. Verify: after_lines <= before_lines
5. If violated: git checkout INTENT.md (revert everything)
```

This is not "try to make it shorter." This is "it MUST be shorter or
equal, or the critique is rejected and reverted."

**Why so strict?** Without this rule, "critique" becomes "review and
add clarifications," which is the opposite of what it's supposed to do.
The constraint forces the critiquer to make hard choices: what stays,
what goes, what merges.

### Allowed Operations During Critique

| Operation | Effect on line count |
|-----------|---------------------|
| Delete section | Decreases |
| Merge two sections into one | Decreases |
| Simplify (rewrite shorter) | Decreases |
| Split to separate intent file | Decreases (in this file) |
| Add new section | **FORBIDDEN** |
| Add clarification | **FORBIDDEN** |
| Expand existing section | **FORBIDDEN** |

If you discover something new during critique that should be added,
note it in `records/critique-YYYY-MM-DD.md` under "Deferred additions."
Then run a separate interview to incorporate it — interview is where
content enters; critique is where content exits.

---

## Mechanism 3: The Scope Guard

After the anchor is established, every new piece of content gets
checked against it. This happens during interviews and during critique.

**How it works:**

Given anchor: `> Anchor: Handle user authentication and session management.`

For each new section, constraint, or example, ask:

1. Does this directly support "user authentication"?
2. Does this directly support "session management"?
3. If neither — it doesn't belong here.

**Example drift detection:**

| Content | Serves anchor? | Verdict |
|---------|---------------|---------|
| "Rate limit login attempts" | Yes (auth security) | Keep |
| "Password hashing with bcrypt" | Yes (authentication) | Keep |
| "User profile editing" | No (that's user management, not auth) | Move to separate intent |
| "Email notification on login from new device" | Borderline | Defer to notification module |
| "OAuth2 grant type comparison" | No (that's research, not intent) | Move to planning/ |

**When content is borderline:**
- Record the decision in `decisions.md` with rationale
- If included: add a note explaining why it serves the anchor
- If excluded: note where it should go instead

---

## Mechanism 4: Convergence Checkpoints

After an intent accumulates 3 or more modifications (commits touching
the INTENT.md), run a convergence check before any further work.

**The 4-point convergence check:**

### 1. Anchor Trace
Go through every section. Can it trace a straight line back to the
anchor? If a section requires two hops of reasoning to connect ("well,
this supports X, which enables Y, which serves the anchor..."), it's
too far removed. Cut or split.

### 2. Implementation Match
For intents that already have code: does each section have corresponding
implementation? If a section describes something that was never built
and isn't planned, it's dead weight.

### 3. Constraint vs Analysis Ratio
Count sections that are testable constraints (tables with rules,
input-output examples) vs sections that are analysis (explanations,
comparisons, background). If analysis sections outnumber constraint
sections, the intent has drifted from its purpose.

| Ratio | Status |
|-------|--------|
| > 70% constraints | Healthy |
| 50–70% constraints | Trim analysis |
| < 50% constraints | Major refactor — move analysis to planning/ |

### 4. Cross-Module Dedup
Check for content that duplicates what's in the project-level intent
or in sibling module intents. Shared constraints belong at the project
level. Module intents should only contain module-specific content.

---

## Mechanism 5: The Devil's Advocate

An advanced technique for when you suspect an intent has drifted but
can't see it because you're too close to the content.

**Process:**
1. Take only the INTENT.md and its anchor — no other context
2. Ask three questions from a hostile, skeptical perspective:
   - "What's the single biggest design risk in this intent?"
   - "Which sections are analysis pretending to be constraints?"
   - "If you could only keep 3 sections, which would you cut?"
3. Compare answers against your full-context perspective
4. Any disagreement reveals blind spots worth investigating

**When to use:**
- Before locking critical sections
- When an intent has been through 5+ modification cycles
- When two team members disagree about scope
- When the health score drops below 70

---

## Budget Enforcement in Practice

### Example: Auth Module Intent Lifecycle

```
Day 1: Initial interview
  → INTENT.md: 120 lines (healthy)

Day 3: Added OAuth2 support details
  → INTENT.md: 250 lines (healthy)

Day 7: Added error handling, retry logic, MFA considerations
  → INTENT.md: 380 lines (WARNING)

Day 10: Added session migration plan, backward compatibility
  → INTENT.md: 520 lines (BLOCKED)

Day 10: Critique required
  → Moved OAuth2 research to planning/
  → Moved MFA to separate module intent
  → Simplified error handling to constraint table
  → INTENT.md: 280 lines (healthy)
```

### The "Just One More Section" Trap

The most common bloat pattern. Each section seems reasonable in isolation:
"We should document the error codes." "Let's add the migration plan."
"Better note the backward compatibility requirements." Each one is 20-40
lines. After 10 additions, you've doubled the file.

**Prevention:** Before adding content, check current line count. If
adding would push past 300, ask: "Is this more important than everything
already here? What can I cut to make room?"

---

## Quality Scoring

For audit purposes, each intent gets a quality score:

| Dimension | Weight | Scoring |
|-----------|--------|---------|
| Budget status | 25% | Healthy=100, Warning=50, Blocked=0 |
| Anchor quality | 20% | Present+specific=100, Present+vague=50, Missing=0 |
| Layer completeness | 20% | All 3 layers=100, 2 layers=66, 1 layer=33 |
| Constraint ratio | 15% | >70%=100, 50-70%=60, <50%=20 |
| Freshness | 10% | Modified within 30 days=100, 90 days=50, older=10 |
| Approval coverage | 10% | >50% locked/reviewed=100, 25-50%=50, <25%=20 |

**Score interpretation:**

| Score | Status | Action |
|-------|--------|--------|
| 90-100 | Excellent | Maintain |
| 70-89 | Good | Minor improvements |
| 50-69 | Needs attention | Schedule critique + review |
| < 50 | Unhealthy | Stop feature work, fix intent first |

---

## Common Quality Anti-Patterns

Teams often undermine quality enforcement with good intentions. Recognize
these patterns and apply the fix:

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Lowering the budget when files exceed it | Removes the constraint that forces hard choices. Bloat returns. | Never lower the budget. Run critique instead. |
| Running critique without the net-reduce check | Critique becomes "review and clarify," the opposite of its purpose. | Enforce the rule: after_lines ≤ before_lines, always. Revert if violated. |
| Skipping convergence checks to ship faster | Drift accumulates silently. Intent becomes analysis, not constraints. | Run convergence after 3+ modifications. Non-negotiable. |
| Deferring scope guard decisions | Borderline content stays in the intent, slowly poisoning it. | Decide immediately: keep with rationale, or move to planning/. Record in decisions.md. |
| Treating quality score as advisory | Scores below 50 are ignored; work continues. | Treat < 50 as a blocker. No feature work until intent is fixed. |
| Adding "just one more section" without cutting | Each addition seems small. Bloat is death by a thousand cuts. | Before adding, check line count. If it pushes past 300, cut something first. |

---

## Related References

- `function-design.md` — Applies the same constraint discipline to function
  signatures and complexity.
- `modularity-and-design.md` — Covers module-level scope guards and
  responsibility boundaries.
- `readability-patterns.md` — Explains cognitive load scoring, which
  complements quality scoring for intent files.
