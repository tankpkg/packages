# Collaboration and Process

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Gregory on programmer/tester collaboration; Rising on future maintainers; Tank github-issues, bdd-e2e-testing, and clean-code skills

Covers: code review, pairing, testers, customer ambiguity, documentation, estimation, humility, and team learning.

## Collaboration Standard

Professional programming is social work performed through technical artifacts. Code must satisfy machines and humans.

Default to clarity, respect, and evidence. Do not use seniority, taste, or slogans as substitutes for reasoning.

## Code Reviews

Review for correctness, risk, maintainability, test coverage, security, and user behavior. Avoid spending human attention on issues a formatter or linter can fix.

Good review comments include evidence and a concrete alternative.

| Weak Comment | Professional Comment |
| ------------ | -------------------- |
| "This is bad" | "This hides a payment failure; return a typed result so callers can retry or show decline." |
| "Use best practices" | "This abstraction has one implementation and couples billing to UI wording; keep it concrete for now." |
| "Needs tests" | "Add a regression test for expired authorization before capture." |

## Pairing and Two Heads

Use pairing or second review for risky work: concurrency, security, migrations, production incidents, ambiguous requirements, and unfamiliar domains.

Two heads help when they bring different failure models. Pairing is not useful if both people silently accept the same assumptions.

## Testers Are Allies

Treat testers as collaborators in risk discovery. They are not a phase after coding; they help define what correctness means.

When programmers and testers collaborate early, tests become sharper and rework decreases.

## Customers and Requirements

Customers often describe what they think the solution is. Ask what they are trying to accomplish, what currently hurts, and what they will do if the system behaves differently.

Start from yes when possible, then shape scope responsibly. "Yes, if we limit the first release to X" is more useful than reflexive refusal.

## Documentation and Project Speech

Let the project speak for itself. A newcomer should find how to install, run, test, configure, deploy, and troubleshoot without oral tradition.

Write documentation at decision boundaries: setup, architecture, external contracts, tradeoffs, and runbooks.

## Blameless Diagnosis

Check your code first before blaming others. After incidents, ask how the system allowed the failure and what guard would prevent recurrence.

Avoid hero culture and guru myths. A healthy system does not depend on one person remembering everything.

## Learning Culture

Read code, not only articles. Study how mature systems handle errors, compatibility, testing, and operations.

Read outside programming when communication, ethics, product judgment, and user understanding matter.

Know limits. Escalate early when risk exceeds your evidence.

## Routing

Use `@tank/bdd-e2e-testing` for shared examples and behavior alignment.

Use `@tank/github-issues` when issue structure, triage, labels, or workflow automation are the main need.

Use `@tank/clean-code` when review feedback focuses on readability and maintainability.

## Collaboration Decision Catalog

| Signal | Recommended Move | Why |
| ------ | ---------------- | --- |
| Vague review | Evidence-based comment | Makes feedback actionable |
| Risky change | Second reviewer/pair | Improves failure discovery |
| Ambiguous request | Clarify outcome | Avoids wrong solution |
| Tester late involvement | Example mapping early | Finds risk sooner |
| Incident blame | System postmortem | Prevents recurrence |
| Guru bottleneck | Document decision | Spreads knowledge |
| Poor issue | Repro template | Improves triage |
| Large estimate | Slice work | Exposes unknowns |
| Setup confusion | README/runbook | Helps maintainers |
| Release surprise | Communicate tradeoffs | Aligns team |

## Collaboration Failure Patterns

### Review Without Evidence

A review comment that says only "this is ugly" creates defensiveness and no path forward. Convert it to evidence: name the risk, cite the code, and propose one change. If the point is taste, label it as non-blocking.

### Late Tester Involvement

If testers see the feature only after implementation, they can find bugs but cannot shape the risk model. Involve them when examples are still cheap to change, especially for state machines, payments, migrations, and user journeys.

### Customer Solution Bias

A customer asking for a button may need an export, a schedule, an alert, or a permission change. Capture the desired outcome and acceptance example before treating the requested UI as the requirement.

### Guru Bottleneck

If only one engineer understands a subsystem, code review becomes permission seeking. Convert repeated explanations into docs, tests, names, or diagrams near the code.

## Team Case Patterns

| Case | Professional Move |
| ---- | ----------------- |
| Vague review | Convert taste into concrete risk and alternative. |
| Tester handoff late | Bring testers into example discovery before code freezes. |
| Customer asks for button | Clarify workflow and consumer of the output. |
| Incident review | Ask how the system allowed failure and what guard changes. |
| Guru bottleneck | Turn repeated explanations into docs, names, or tests. |
| Missing reproduction | Do not start implementation until the issue can be reproduced or bounded. |
| Large estimate | Slice into verifiable increments and expose assumptions. |
| Risky migration | Require second reviewer and rollback plan. |
| Setup confusion | Update README/runbook where the next user will look. |
| Post-release feedback | Close loop with issue, test, or documentation update. |

