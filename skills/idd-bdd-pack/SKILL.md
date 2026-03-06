---
name: "@tank/idd-bdd-pack"
description: |
  Orchestrator pack combining Intent-Driven Development (IDD) with BDD
  end-to-end testing. Installs both @tank/idd and @tank/bdd-e2e-testing,
  then provides the bridge workflow for using .idd/ and .bdd/ folders
  together. Does not stand alone — requires both dependencies.

  Trigger phrases: "IDD BDD", "intent and behavior", "intent to BDD",
  "BDD from intent", "intent verified testing", "intent behavior pack",
  "combine IDD BDD", "IDD BDD orchestrator", "intent driven BDD",
  "intent plus BDD", "full testing workflow", ".idd .bdd together"
---

# IDD + BDD Orchestration

This pack does not teach IDD or BDD. It teaches how to use them together.

For IDD methodology, load `@tank/idd`.
For BDD testing, load `@tank/bdd-e2e-testing`.
This pack installs both and adds the bridge.

## Why Combine Them

IDD and BDD solve different halves of the same problem.

| Concern | IDD handles it | BDD handles it |
|---------|---------------|----------------|
| "Why does this module exist?" | Anchor in INTENT.md | — |
| "What are the architectural constraints?" | Layer 2 constraint tables | — |
| "What should the user experience?" | — | Gherkin scenarios |
| "Does it actually work against real systems?" | — | E2E verification |
| "Are the acceptance criteria met?" | Layer 3 examples | Feature files |

IDD defines the contract. BDD verifies it. Without IDD, BDD scenarios
lack architectural grounding. Without BDD, intent files are untested
promises.

**No mocking in either layer. This is non-negotiable.** All tests — IDD
functional tests and BDD E2E tests — run against real systems. Not stubs.
Not fakes. Not in-memory replacements. The real dependency. If it's
unavailable, stop and tell the user. Do not silently introduce mocks to
keep going. The only exception is the user explicitly saying "mock X."

## When to Install This Pack

| Situation | Install this pack? |
|-----------|--------------------|
| Multi-module system with AI-assisted development + E2E testing | **Yes** |
| IDD only (no E2E tests yet) | **No** — install `@tank/idd` alone |
| BDD only (no intent files) | **No** — install `@tank/bdd-e2e-testing` alone |
| Small script, single file | **No** — neither tool is needed |
| Existing BDD tests, adding intent discipline | **Yes** — the bridge maps existing features to intent layers |

## The Bridge: Intent Layers to BDD Artifacts

Each intent layer maps to a specific BDD artifact type:

| Intent Layer | Content | BDD Artifact | Location |
|-------------|---------|--------------|----------|
| Layer 3: Examples | Input/output pairs | Gherkin scenarios | `.bdd/features/` |
| Layer 2: Constraints | Architectural rules | Step assertions + lint rules | `.bdd/steps/` + CI |
| Layer 1: Structure | Module boundaries | Test organization | `.bdd/features/{module}/` |

The handoff is one-directional: intent drives tests. Tests never modify
intent — that flows through the IDD sync process.

See `references/orchestration-workflow.md` for the full bridge workflow.

## Combined Directory Structure

```
project/
  .idd/                          # Intent (owned by IDD)
    project.intent.md
    modules/
      auth/
        INTENT.md                # Anchor + layers
        decisions.md
      payments/
        INTENT.md
    records/
    _data/

  .bdd/                          # Verification (owned by BDD)
    features/
      auth/                      # Mirrors .idd/modules/auth/
        login.feature            # Derived from auth INTENT.md Layer 3
        rate-limiting.feature    # Derived from auth INTENT.md Layer 2
      payments/
        checkout.feature
    steps/
      auth.steps.ts
      payments.steps.ts
    interactions/
    support/
    qa/
      findings/
      resolutions/
```

Module names in `.bdd/features/` mirror module names in `.idd/modules/`.
This is not optional — the mapping must be traceable by directory name.

## Quick-Start

### "I have IDD intent files and want to add BDD verification"

1. Create `.bdd/` with the mandatory BDD structure
2. For each module in `.idd/modules/`, create a matching directory in `.bdd/features/`
3. Convert Layer 3 examples to Gherkin scenarios
4. Convert Layer 2 constraints to assertion patterns in step definitions
5. Run against the real system. Document findings.

See `references/orchestration-workflow.md` for step-by-step conversion.

### "I have BDD tests and want to add IDD discipline"

1. Create `.idd/` with the mandatory IDD structure
2. For each feature directory in `.bdd/features/`, create a module in `.idd/modules/`
3. Write INTENT.md for each module — the existing features tell you what the system does
4. Map existing scenarios back to Layer 3 examples
5. Add Layer 2 constraints for rules not yet captured in tests

### "How do I keep them in sync?"

Run the IDD sync process (Step 8). During sync, also check:
- Every Layer 3 example has a corresponding Gherkin scenario
- Every Layer 2 constraint with a test-form has a corresponding step assertion
- No orphan features exist without a backing intent module

See `references/orchestration-workflow.md` for the sync checklist.

## Decision Tree

### Which layer drives which test type?

| If the intent says... | Write this BDD artifact |
|-----------------------|------------------------|
| Example: `authenticate(valid) → Session` | Scenario in `.bdd/features/auth/login.feature` |
| Constraint: "Auth never imports payments" | CI lint rule (not a BDD scenario) |
| Constraint: "Rate limit 5/min per IP" | Scenario in `.bdd/features/auth/rate-limiting.feature` |
| Constraint: "All errors return 401" | Assertion pattern in step definitions |
| Structure: directory tree diagram | Test directory organization — no scenario needed |

Not every intent line becomes a Gherkin scenario. Constraints that are
better enforced by lint rules or CI checks stay outside `.bdd/`.

## Reference Files

| File | Contents |
|------|----------|
| `references/orchestration-workflow.md` | Full bridge workflow: Layer-to-Gherkin conversion, constraint-to-step mapping, sync checklist, combined lifecycle |
