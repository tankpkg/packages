# IDD Lifecycle

Sources: ArcBlock/idd workflow (MIT), FORGE 5-phase cycle (MIT),
Praxis intent-spec pipeline (MIT), synthesized into one workflow.

Covers: Full lifecycle from project assessment through build and sync.
Each step's inputs, outputs, gates, and common failure modes.

## The Loop

IDD is not waterfall. It's a tightening spiral — each pass through the
loop sharpens the intent and validates the implementation.

```
  Assess → Init → Interview → Critique → Lock
                                            │
     Audit ← Sync ← Build ← Plan ──────────┘
       │
       └──→ (next iteration)
```

Steps 3–9 repeat per module and across releases.

---

## Step 1: Assess

**Question:** Is IDD the right tool for this project?

**How to assess:**

| Dimension | IDD-favorable | Skip IDD |
|-----------|--------------|----------|
| Codebase size | >5k LOC, multi-module | Single file script |
| AI involvement | Claude/Copilot writes code | Pure manual coding |
| Lifespan | Maintained over months/years | One-time throwaway |
| Team | Multiple contributors + AI | Solo, well-understood domain |
| Architecture | Needs boundary enforcement | Flat, no module separation |
| Stakeholders | Need to review design, not code | Dev reviews own work |

**Output:** Go/no-go decision. If no-go, skip IDD — the overhead isn't
worth it. Write your code directly.

**Gate:** Honest assessment that IDD adds more value than ceremony.

---

## Step 2: Init

**Action:** Scaffold the `.idd/` directory structure.

**Process:**
1. Scan for existing intent-like files (specs/, design/, INTENT.md, etc.)
2. Create the mandatory structure (see SKILL.md)
3. Generate template files for project-level intent and first module

**First file to write:** `.idd/project.intent.md` — project vision,
module index, explicit non-goals.

**Gate:** `.idd/` directory exists with `project.intent.md`.

---

## Step 3: Interview

The interview is where vague ideas become concrete decisions. It runs
in two distinct phases to prevent intent bloat.

### Phase A: Question (produces decisions.md)

Ask yourself (or have the AI ask you) structured questions about the
module. Work through these domains in order:

1. **Problem space** — What problem? For whom? What happens if unsolved?
2. **Data** — What data structures? What's the shape? Where stored?
3. **API** — What does the public surface look like? What goes in, what
   comes out?
4. **Architecture** — How does this module relate to others? What are
   the boundaries?
5. **Edge cases** — What breaks? What's the error story?
6. **Scope** — What are we explicitly NOT building?
7. **Constraints** — Performance? Security? Consistency?

Record every Q&A in `decisions.md`. Include the rationale — not just
"we chose Redis" but "we chose Redis because we need shared sessions
across instances and sub-millisecond lookup."

**Output:** `.idd/modules/<name>/decisions.md`

**Scope guard:** After establishing the anchor, every subsequent question
gets checked against it. If an answer drifts beyond the anchor's scope,
flag it and either defer to a different module's intent or explicitly
expand the anchor.

### Phase B: Compose (produces INTENT.md)

Only start composing after Phase A is complete. Transform decisions into
the three-layer intent format:

1. Extract structure decisions → Layer 1 (diagrams)
2. Extract rule decisions → Layer 2 (constraints table)
3. Extract behavior decisions → Layer 3 (examples table)
4. Write the anchor statement
5. Budget check: is it under 300 lines? Under 500?

**Output:** `.idd/modules/<name>/INTENT.md`

**Gate:** Anchor exists. Budget within limits. All three layers present.

**Save the raw transcript** to `records/interview-YYYY-MM-DD.md` and
update `records/INDEX.md`.

---

## Step 4: Critique

The critique exists to fight natural bloat. Every conversation, every
brainstorm, every "what about..." adds lines. Critique removes them.

### The Net-Reduce Rule

After critique, the file must be shorter or equal. Not "shorter on
average across sessions" — shorter right now, this critique, measured
by `wc -l`. If the line count went up, the critique failed. Revert and
try again.

### Critique Process

1. **Record starting line count** (`wc -l INTENT.md`)
2. **Anchor trace** — Can every section justify its existence relative
   to the anchor? If not, cut it.
3. **Over-engineering scan:**
   - More than 3 configurable things? Probably too many.
   - Plugin/extension mechanisms? Do you actually need them today?
   - Multiple abstraction layers? Start with one.
   - "Supports multiple X"? Pick one X and ship it.
4. **YAGNI scan:**
   - "Might need in future"? Remove. Add it when the future arrives.
   - "Reserved for extension"? Unreserve it.
   - "For convenience"? Convenience for whom? Cut if speculative.
5. **Constraint vs analysis check:**
   - Is this section a testable rule ("latency < 200ms") or background
     analysis ("there are several approaches to caching")?
   - Move analysis to `planning/`. Only constraints belong in intent.
6. **Record ending line count.** Verify `after <= before`.

### Allowed Critique Operations

Only four operations are permitted during critique:

| Operation | What it means |
|-----------|---------------|
| **Delete** | Remove a section entirely |
| **Merge** | Combine two overlapping sections into one |
| **Split** | Move content to a separate module intent |
| **Simplify** | Rewrite a section in fewer lines |

Adding new concepts, new sections, or new ideas is forbidden during
critique. That's what interview is for.

**Output:** Updated INTENT.md with fewer lines. Critique saved to
`records/critique-YYYY-MM-DD.md`.

**Gate:** `after_lines <= before_lines`

See `references/quality-enforcement.md` for advanced patterns.

---

## Step 5: Lock

Once critical sections stabilize, lock them to prevent accidental
modification by AI agents or careless edits.

### Three Approval States

| State | Meaning | AI behavior |
|-------|---------|-------------|
| **LOCKED** | Core architecture, not changing | Stop and ask human permission |
| **REVIEWED** | Accepted, minor changes OK | Proceed but notify human |
| **DRAFT** | Still evolving | Modify freely |

### Marking Sections

Use fenced div syntax in the INTENT.md:

```markdown
::: locked {reason="Core API contract"}
## API Signatures
...
:::

::: reviewed {by=alice date=2026-03-06}
## Data Structures
...
:::
```

Unmarked sections are treated as draft.

See `references/approval-and-review.md` for the full review workflow.

---

## Step 6: Plan

Transform the approved intent into a phased execution plan suitable
for TDD.

### Pre-Plan Gates

All three must pass before planning begins:

1. **Intent gate** — INTENT.md exists, has anchor, within budget, has
   all three layers (structure, constraints, examples)
2. **Critique gate** — At least one critique has been run. If INTENT.md
   was modified after the last critique, re-critique first.
3. **Dependency gate** — All intents referenced in `Depends:` are in
   `status: implemented` or `status: active` with their own plan.

### Plan Output

Generate `plan.md` with phases. Each phase is sized for one focused
work session.

```markdown
# Execution Plan: Auth Module

## Phase 0: Session Storage Layer

### Description
Implement Redis-backed session store with TTL management.

### Tests
#### Happy Path
- Create session → returns session ID
- Lookup valid session → returns session data

#### Error Path
- Lookup expired session → returns null
- Lookup nonexistent session → returns null

#### Edge Cases
- Concurrent session creation for same user
- Redis connection failure during lookup

#### Security
- Session ID is not guessable (UUID v4 or better)
- Session data is not accessible without valid ID

#### Data Integrity
- Session TTL is enforced (not just advisory)
- Expired sessions are actually cleaned up

#### Destructive Operations
- Session revocation actually prevents future lookups
- Bulk revocation (logout everywhere) is atomic

### E2E Gate
` ` `bash
npm test -- --grep "session"
` ` `

### Acceptance Criteria
- [ ] All tests passing
- [ ] Coverage > 80%
- [ ] No hardcoded session secrets
```

### Commit Convention

Prefix commits with the phase:

```
plan: add execution plan for auth module
build: implement session storage (phase 0)
build: add auth middleware (phase 1)
sync: update auth intent with finalized API signatures
```

See `references/tdd-from-intent.md` for the full TDD execution model.

---

## Step 7: Build

Execute the plan using strict TDD. For each phase:

1. Write the failing tests (RED) — derived from the plan's test matrix
2. Write minimal code to pass (GREEN) — no more than what tests require
3. Refactor — improve quality while keeping tests green
4. Run E2E gate script
5. Commit with phase prefix

**One phase per focused session.** Don't mix phases. Context pollution
leads to boundary violations.

**Gate:** All tests pass. E2E gate script exits 0. Coverage meets threshold.

---

## Step 8: Sync

After implementation stabilizes (not during active development), reconcile
what actually shipped with what the intent described.

**Process:**
1. Scan codebase: public APIs, data structures, module boundaries
2. Compare against INTENT.md
3. Categorize diffs: New (in code, not in intent) / Changed (differs
   from intent) / Confirmed (matches) / Removed (in intent, not in code)
4. Present diffs to human for approval
5. Update INTENT.md with confirmed actuals
6. Add sync marker: `> Synced: 2026-03-06 from commit abc123`

**What gets synced:** API signatures, data structures, module boundaries,
error codes, configuration. NOT implementation details — intent stays at
the "what" level.

**Gate:** Human approved all diffs. Sync marker added.

See `references/drift-detection.md`.

---

## Step 9: Audit

Periodic health check across all intent files in the project.

**Dimensions checked:**
1. Coverage — which modules have intents, which don't
2. Freshness — intent last modified vs code last modified
3. Budget — per-intent line counts vs thresholds
4. Approval — locked/reviewed/draft percentages
5. Dependencies — declared deps vs actual imports
6. Boundary violations — forbidden patterns found in code
7. Orphans — intents with no connections to other intents
8. Stale references — Depends/See-also pointing to deleted files

**Output:** Health score (0–100) and prioritized action items.

**Gate:** Score > 80 for healthy projects. Below 60 means intent has
rotted and needs serious attention.

---

## Failure Modes

| What goes wrong | Why | Fix |
|----------------|-----|-----|
| Intent written after code | Defeats the purpose. Intent drives, code follows. | Discipline. Write intent first, even rough. |
| Intent never updated after build | Intent rots. New contributors get stale info. | Run sync after each release. |
| Critique skipped "because we're busy" | File bloats to 800 lines. AI gets confused. | Budget enforcement is automated. No workaround. |
| Everything locked on day one | Nothing can evolve. Teams route around locks. | Lock only after sections prove stable through a build cycle. |
| Interview produces 50 questions | Analysis paralysis. Decisions never made. | Cap at 15 questions per interview. Defer the rest. |
