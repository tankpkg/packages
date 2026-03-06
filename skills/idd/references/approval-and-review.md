# Approval and Review

Sources: ArcBlock/idd section approval system (MIT), FORGE phase-gate model (MIT),
code review practices synthesized into section-level approval workflow.

Covers: three approval states, fenced div syntax, when to lock, change proposals,
review workflow, AI agent behavior, patterns and anti-patterns.

## Three Approval States

Every section in an intent file carries one of three approval states. Unmarked
sections default to DRAFT.

| State | Meaning | AI Behavior | Who Can Change |
|-------|---------|-------------|----------------|
| LOCKED | Core architecture. Stable contract. Not changing. | Stop. Ask human before any modification. | Human only, via change proposal |
| REVIEWED | Accepted. Minor edits allowed. | Proceed, then notify human of what changed. | AI with notification, human freely |
| DRAFT | Still evolving. Under active development. | Modify freely. No notification required. | Anyone |

The default matters: an unmarked section is DRAFT. AI agents treat silence as
permission to evolve. Explicit state is required to restrict that permission.

### State Transitions

```
DRAFT ──────────────────────────────► REVIEWED
  │                                       │
  │  (survives one build cycle unchanged) │  (stable, no more changes expected)
  │                                       │
  └──────────────────────────────────────► LOCKED
```

Move forward through states as confidence grows. Move backward only when
requirements change — and treat that as a signal to run a new interview.

## Fenced Div Syntax

Mark sections using fenced divs with the state as the class. The syntax follows
the Pandoc fenced div convention, extended with IDD attributes.

### Basic Syntax

```markdown
::: locked

## API Signatures

### authenticate(credentials): Promise<Session>
...

:::
```

```markdown
::: reviewed

## Constraints

| Rule | Rationale |
|------|-----------|
| Never import from payments/ | Auth must not know about billing |

:::
```

```markdown
::: draft

## Error Handling

Still deciding between error codes and typed exceptions.

:::
```

### Attribute Syntax

Add metadata to any state marker using attribute syntax:

```markdown
::: locked {reason="API contract signed with mobile team", by=alice, date=2026-03-01}

## API Signatures

:::
```

| Attribute | Required | Description |
|-----------|----------|-------------|
| `reason` | Recommended for locked | Why this section is locked |
| `by` | Recommended for locked | Who approved the lock |
| `date` | Recommended for locked | When the lock was applied |

Attributes are optional for REVIEWED and DRAFT. For LOCKED sections, include
all three — they become the audit trail for change proposals.

### Marking an Entire File

To lock an entire intent file, wrap the full body content:

```markdown
---
status: implemented
---

# Payment Module Intent

> Anchor: Process payments and manage subscription billing.

::: locked {reason="Shipped to production 2026-02-15", by=alice, date=2026-02-15}

## Responsibilities
...

## API
...

## Constraints
...

:::
```

Alternatively, set `status: implemented` in frontmatter — AI agents treat
`implemented` as an implicit file-level lock. Fenced divs take precedence
over frontmatter status for individual sections.

### Nesting Rules

Do not nest approval states. A section is either locked, reviewed, or draft —
not a mix. If part of a section needs different treatment, split it into
separate sections with separate markers.

## When to Lock

Locking too early kills evolution. Locking too late means AI rewrites stable
contracts. Use this decision tree:

| Question | Yes → | No → |
|----------|-------|------|
| Has this section survived one full build cycle unchanged? | Consider locking | Keep as DRAFT |
| Do other modules depend on this section's contracts? | Lock it | REVIEWED is sufficient |
| Would changing this section require coordinating with other teams? | Lock it | REVIEWED is sufficient |
| Is this section still under active discussion? | Keep as DRAFT | Proceed to next question |
| Has a human explicitly approved this section? | REVIEWED minimum | Keep as DRAFT |

### The One Build Cycle Rule

Lock a section after it survives one complete implementation cycle without
modification. If you wrote the API signatures, built against them, and shipped
without changing them — lock them. If you changed them during implementation,
they weren't ready to lock.

This rule prevents premature locking. A section that looks stable during
planning often needs adjustment once real code runs against it.

### What to Lock First

| Section Type | Lock Timing | Rationale |
|-------------|-------------|-----------|
| API signatures | After first successful integration | Other modules build against these |
| Data contracts (schemas, types) | After first consumer ships | Schema changes break consumers |
| Security constraints | After security review | Compliance requirement |
| Module boundaries | After dependency graph stabilizes | Circular dependency prevention |
| Implementation details | Rarely | These should stay flexible |
| Examples | Never lock | Examples evolve with the system |

## Change Proposals for Locked Sections

AI agents cannot modify locked sections. Humans initiate changes through a
formal proposal process.

### Process

```
1. Propose    → Write change proposal in records/
2. Review     → Human evaluates impact
3. Approve    → Human approves (never AI)
4. Unlock     → Remove ::: locked marker temporarily
5. Modify     → Make the approved change
6. Re-lock    → Restore ::: locked with updated attributes
7. Record     → Append outcome to records/INDEX.md
```

### Change Proposal Format

Create a file in `records/` named `change-YYYY-MM-DD-{section}.md`:

```markdown
# Change Proposal: API Signatures — 2026-03-06

**Section:** `## API Signatures` in `.idd/modules/auth/INTENT.md`
**Locked by:** alice on 2026-02-15
**Proposed by:** bob on 2026-03-06

## What

Add `refreshToken(token: string): Promise<Session>` to the auth API.

## Why

Mobile clients need token refresh without re-authentication. Current API
forces full re-login on expiry, causing user friction.

## Impact

- Mobile team must update their auth client (estimated 2 days)
- Session storage schema unchanged — no migration required
- Rate limiting rules apply to refresh endpoint (existing constraint satisfied)

## Alternatives Considered

1. Extend session TTL — rejected, security team requires short-lived tokens
2. Separate refresh service — rejected, adds deployment complexity

## Approval

- [ ] alice (original lock owner)
- [ ] security-team (constraint owner)
```

### Who Can Approve

Only humans approve change proposals. AI agents may draft proposals, analyze
impact, and suggest alternatives — but the approval checkbox requires a human.

This is non-negotiable. Locked sections exist precisely because they represent
decisions that should not change without human judgment.

### Emergency Unlock

For production incidents requiring immediate changes to locked sections:

1. Document the emergency in `records/emergency-YYYY-MM-DD.md`
2. Make the minimum change required to resolve the incident
3. Re-lock immediately after the incident resolves
4. File a retroactive change proposal within 24 hours
5. Schedule a review to determine if the lock criteria still apply

Emergency unlocks without documentation are treated as process violations.

## Review Workflow

### Step-by-Step Review

1. **Trigger** — Set `needs: [review]` in frontmatter, or request review explicitly
2. **Prepare** — Reviewer reads the intent file and the decisions.md for context
3. **Check** — Run through the review checklist below
4. **Decide** — Approve, request changes, or escalate
5. **Record** — Append review outcome to `records/`
6. **Update** — Remove `needs: review` from frontmatter, apply state markers

### Review Checklist

| Check | Pass Criteria |
|-------|---------------|
| Anchor alignment | Every section traces back to the anchor |
| Size budget | File under 300 lines (warn at 300-500, block at 500+) |
| Constraint quality | Each constraint is testable, has rationale |
| Example coverage | Happy path, error cases, and at least one edge case |
| Dependency accuracy | `Depends:` tag lists only direct dependencies |
| No planning content | Background analysis lives in `planning/`, not here |
| Approval state accuracy | Locked sections have reason, by, date attributes |

### Recording Review Decisions

Append to `records/INDEX.md` after every review:

```markdown
| 2026-03-06 | review | Locked API signatures. Flagged error handling as needs-work. |
```

Create a full review record in `records/review-YYYY-MM-DD.md` for any review
that results in locking sections or requesting significant changes.

### Escalation

When reviewers disagree on whether to lock a section:

1. Default to REVIEWED (not LOCKED) — less restrictive is safer when uncertain
2. Set a re-review date: add `needs: [review]` and a comment with the date
3. If disagreement persists after two review cycles, escalate to the team lead
4. Document the disagreement and resolution in `records/`

Never leave a section in limbo. Make a decision, record it, move forward.

## AI Agent Behavior

### Encountering Each State

| State | AI Action |
|-------|-----------|
| LOCKED | Stop. Report the locked section to the human. Do not modify. Offer to draft a change proposal. |
| REVIEWED | Proceed with modification. Append a summary of changes to the session output. |
| DRAFT | Modify freely. No notification required. |
| Unmarked | Treat as DRAFT. Modify freely. |

### Reporting Locked Section Encounters

When AI encounters a locked section it would otherwise modify:

```
LOCKED SECTION ENCOUNTERED

File: .idd/modules/auth/INTENT.md
Section: ## API Signatures
Locked by: alice on 2026-02-15
Reason: API contract signed with mobile team

Requested change: Add refreshToken() method

To proceed: Create a change proposal in records/ and get human approval.
I can draft the change proposal if you'd like.
```

Report the lock, explain what change was blocked, and offer to help with the
proposal process. Do not silently skip the modification.

### Reviewed Section Notification

When AI modifies a REVIEWED section, append to the session output:

```
REVIEWED SECTION MODIFIED

File: .idd/modules/auth/INTENT.md
Section: ## Constraints
Change: Added rate limiting constraint for refresh endpoint (5 req/min per IP)
Rationale: Consistent with existing authenticate() rate limiting rule

Human review recommended before next lock cycle.
```

### The Human-in-the-Loop Principle

Locked sections encode decisions that required human judgment to make. They
require human judgment to change. AI agents are powerful at generating and
modifying content — but they lack the organizational context to know when a
contract change will break a team's sprint, violate a compliance requirement,
or contradict a verbal agreement made in a meeting.

The lock is not a technical restriction. It's a signal: this decision was hard
to reach, and changing it has consequences beyond the file.

## Common Patterns and Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Lock everything on day one | Prevents evolution. AI can't help. Every change requires a proposal. | Lock only after one build cycle. Start with DRAFT. |
| Never lock anything | AI rewrites stable contracts. Mobile team's integration breaks. | Lock API surfaces and data contracts after first consumer ships. |
| Lock implementation details | Blocks AI from improving code structure. | Lock contracts, not implementations. |
| Lock without attributes | No audit trail. Can't find who locked it or why. | Always include reason, by, date on locked sections. |
| Forget to re-lock after emergency | Section stays unlocked. AI modifies it freely. | Re-lock immediately after incident resolves. |
| Lock after first draft | Section hasn't been tested. Lock is premature. | Apply the one build cycle rule. |
| Use REVIEWED as a rubber stamp | Sections accumulate REVIEWED state without real review. | REVIEWED means a human read it and accepted it. |

### Recommended Lock Targets

Lock these first, in this order:

1. API signatures (after first integration)
2. Data schemas and types (after first consumer)
3. Security and compliance constraints (after security review)
4. Module boundary rules (after dependency graph stabilizes)

Leave these as DRAFT or REVIEWED:

- Implementation details
- Internal structure diagrams
- Examples and test cases
- Performance targets (until measured)

---

For the full lifecycle context of when locking occurs, see `references/idd-lifecycle.md`
step 5 (Lock). The lifecycle file covers the sequence of phases; this file covers
the mechanics of the approval system within those phases.
