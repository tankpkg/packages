---
name: "@tank/idd"
description: |
  Intent-Driven Development: define what and why before writing how.
  AI writes code; humans write intent. Covers the full IDD lifecycle —
  structured interviewing, design critique, section locking, phased TDD
  execution, and code-intent drift detection. Opinionated synthesis of
  ArcBlock/idd, Praxis, and FORGE (all MIT).

  Trigger phrases: "IDD", "intent driven development", "intent file",
  "INTENT.md", "intent interview", "intent critique", "intent review",
  "intent plan", "intent build", "intent sync", "intent check",
  "intent audit", "intent init", "intent driven", "implementation last",
  "AI native development", "intent standard", "intent approval",
  "drift detection", "convergence check", ".idd folder"
---

# Intent-Driven Development

> Vague instructions produce vague code. If you can't write down what
> the module must do, must not do, and how you'll know it works — you're
> not ready to build it.

## Hard Rules

These are non-negotiable. Violating any of them means the work is wrong.

1. **ALL intent artifacts go in `.idd/` at project root.** Not `specs/`,
   `design/`, `docs/requirements/`, or scattered markdown files. One folder,
   one source of truth — same discipline as `.bdd/` for tests.

2. **Every INTENT.md opens with an anchor** — one sentence declaring why
   this module exists. Every section must justify itself against that anchor.
   If it can't, cut it.

3. **Budget is enforced, not suggested.** 300 lines is healthy. 500 is the
   ceiling. Over 500? All work stops until critique brings it down. No
   exceptions.

4. **Tests trace to intent.** Constraints become assertions. Examples become
   test cases. No test exists without an intent line it verifies.

5. **No mocking. Period.** Every test runs against the real system — real
   databases, real APIs, real services. Not in-memory fakes. Not stubs. Not
   "lightweight replacements." The real thing. If a dependency is unavailable,
   stop and tell the user. Do not silently substitute a mock to keep going.
   The only exception is the user explicitly saying "mock X for now" — and
   even then, mark it `TODO: remove mock` so it doesn't rot. This rule is
   not a suggestion. It is a hard blocker. Violating it invalidates the
   entire test suite.

6. **Bugs are edge cases, not regressions.** When a bug is found, do not
   write a "regression test." Add the bug's scenario to the intent Examples
   table as an edge case, then write a functional test for that edge case.
   The bug becomes part of the specification — permanently. The intent file
   is the source of truth, not the bug tracker.

## Core Philosophy

1. **You own the problem. AI owns the solution.** Traditional development
   spends 80% writing code and 20% verifying it. Invert that. Nail the
   constraints and acceptance criteria first. Let AI fill the implementation
   gap.

2. **Draw it, don't describe it.** ASCII diagrams beat prose. An LLM reads
   a directory tree or dependency graph in one pass. Three paragraphs
   describing the same structure cost tokens and introduce ambiguity.

3. **One module, one file, complete context.** Scattering a module's intent
   across functional-reqs.md, ux-reqs.md, and tech-reqs.md forces the AI to
   reassemble a picture you already had. Keep the full picture in one
   INTENT.md.

4. **Intent files are living documents.** They start rough, sharpen through
   interview and critique, lock when stable, and sync back after implementation
   reveals what reality actually demanded. Ignore them and they rot — so
   detect drift.

5. **Brevity is a feature.** Every line costs tokens and attention. If
   critique doesn't make the file shorter, the critique failed.

## What Goes in an Intent File

Three layers, each more concrete than the last:

| Layer | What you write | What it becomes |
|-------|----------------|-----------------|
| **Structure** | ASCII directory trees, data models, module boundaries | Architecture guardrails for the AI |
| **Constraints** | Rules as tables: "X must never import Y", "latency < 200ms" | Lint rules and test assertions |
| **Examples** | `connect("valid-uuid") → Session { status: "connected" }` | Actual test cases |

See `references/intent-standard.md` for the full format specification.

## Mandatory Directory Structure

```
.idd/
  project.intent.md        # Project vision, module index, non-goals
  architecture/
    dependencies.md         # Module dependency graph (ASCII + matrix)
    boundaries.md           # Forbidden patterns, boundary rules
  modules/                  # One INTENT.md per module
    auth/
      INTENT.md             # Anchor + structure + constraints + examples
      decisions.md          # Interview Q&A log
    payments/
      INTENT.md
  records/                  # Append-only audit trail
    INDEX.md
  plans/                    # Phased execution plans (generated)
  _archive/                 # Retired intents (git mv, never delete)
  _data/                    # Computed health data (generated, don't touch)
```

Create this structure before writing any intent.

## The Lifecycle

IDD is a loop, not a one-shot process.

| Step | What happens | Artifact produced |
|------|-------------|-------------------|
| 1. Assess | Is IDD right for this project? | Go/no-go decision |
| 2. Init | Scaffold `.idd/` structure | Directory tree + templates |
| 3. Interview | Structured Q&A to extract decisions | `decisions.md` → `INTENT.md` |
| 4. Critique | Attack over-engineering, enforce brevity | Shorter INTENT.md (net-reduce) |
| 5. Lock | Mark stable sections as locked | `LOCKED` / `REVIEWED` / `DRAFT` |
| 6. Plan | Break intent into phased TDD plan | `plan.md` with test matrix |
| 7. Build | Execute TDD per phase | Code + tests + phase commits |
| 8. Sync | Reconcile what shipped vs what was intended | Updated INTENT.md |
| 9. Audit | Measure drift, coverage, health | Health score + action items |

Steps 3–9 repeat. Intent is never "done" — it evolves with the codebase.

See `references/idd-lifecycle.md` for the detailed workflow.

## Quick-Start

### "I want to adopt IDD on my project"

1. Create `.idd/` with the structure above
2. Write `project.intent.md` — vision, module index, what you're NOT building
3. Pick the first module. Run an interview: ask the hard questions
4. Write `INTENT.md` with anchor, structure diagram, constraints, examples
5. Critique it — is every section earning its lines?
6. Generate a phased plan and build with TDD

### "My intent files keep growing"

| Problem | Fix |
|---------|-----|
| Over 500 lines | Critique must net-reduce. No exceptions. |
| Sections that don't serve the anchor | Cut them or split into a separate module intent |
| Background research mixed in with rules | Move exploration to `planning/` — it's not intent |
| Same content in project + module intent | Pick one home. Cross-reference the other. |

### "Code and intent diverged"

Run a sync check. Compare what INTENT.md says against what the code actually
does. Categorize every diff: New / Changed / Confirmed / Removed. Update
intent with what actually shipped. See `references/drift-detection.md`.

## Decision Trees

### When is IDD worth the overhead?

| Signal | Verdict |
|--------|---------|
| Multi-module system (>5k LOC) | **Yes** — constraints prevent AI from drifting across boundaries |
| AI-heavy workflow (Claude, Copilot) | **Yes** — intent files are the guardrails that prevent hallucination |
| Library or framework (consumers depend on your API) | **Yes** — intent locks the contract |
| Long-lived project with team turnover | **Yes** — intent survives people leaving |
| Small script, single file | **No** — just write the code |
| Throwaway prototype | **No** — intent outlives the thing it describes |
| Regulated industry needing formal docs | **Supplement** — intent helps but doesn't replace compliance artifacts |

## Reference Files

| File | Contents |
|------|----------|
| `references/intent-standard.md` | INTENT.md format, frontmatter, anchor rules, three-layer model, size budget, supporting file formats |
| `references/idd-lifecycle.md` | Full lifecycle: assess → init → interview → critique → lock → plan → build → sync → audit |
| `references/intent-authoring.md` | How to write good intent: diagrams-first, constraint tables, example pairs, common anti-patterns |
| `references/quality-enforcement.md` | Anti-accretion rules, budget thresholds, net-reduce critique, convergence checks, scope guard |
| `references/tdd-from-intent.md` | Deriving tests from intent layers, 6 test categories, phased execution, E2E gates, commit conventions |
| `references/approval-and-review.md` | Section locking (LOCKED/REVIEWED/DRAFT), change proposals, review workflow |
| `references/drift-detection.md` | Code-intent sync, drift modes, audit dimensions, health scoring, CI integration |
