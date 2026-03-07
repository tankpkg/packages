---
name: "@tank/bulletproof"
description: |
  Build it right, prove it works, ship with confidence. Combines
  intent-driven development (@tank/idd) with real-system E2E testing
  (@tank/bdd-e2e-testing). Nothing ships without being defined first
  and verified against real dependencies. No mocks. No guessing.

  Trigger phrases: "bulletproof", "ship with confidence",
  "intent and testing", "define and verify", "intent to tests",
  "verified development", "build right ship fast", "no mocks",
  "real system testing", "full development workflow", "intent verified"
---

# Bulletproof

Define what the system must do. Prove it does it. Ship it.

## Hard Rules

These override your default instincts. They exist because without them
you will revert to "read code → debug → fix → hope" every single time.

1. **Behavior before code.** Your training biases you toward reading source
   code when something breaks. Resist this. Source code tells you what IS,
   not what SHOULD BE. Start from the other end: define expected behavior
   in INTENT.md and a Gherkin scenario FIRST. The failing test then tells
   you exactly where to look in the code and exactly when the fix is done.

   Every time you catch yourself opening a source file before writing a
   test, stop. You are doing it backwards.

2. **RED before GREEN.** Never fix code without a failing test that captures
   the correct behavior. The test is your proof the fix works AND your
   guarantee it never regresses. Without it, you are shipping hope.

3. **Intent drives tests. Tests verify code.** The arrow is one-directional:
   INTENT.md → Gherkin scenario → step definition → application code. When
   a test fails, fix the application — never weaken the test, never adjust
   the intent to match broken behavior.

4. **No mocking.** All tests run against real systems — real databases, real
   APIs, real services. A test suite that passes against mocks proves the
   code works with the mock, not with reality. If a dependency is unavailable,
   stop and tell the user. Do not silently introduce mocks to keep going.

## The Loop

Every task — bug fix, feature, refactor — follows this loop:

```
INTENT  →  RED  →  GREEN  →  REFACTOR
  │         │        │          │
  │         │        │          └─ Clean up. Tests still green.
  │         │        └─ Fix/build until test passes. Minimal change.
  │         └─ Write Gherkin scenario. Run it. Watch it FAIL.
  └─ Update INTENT.md with the behavior/constraint/example.
```

### Bug Fix Protocol

1. Read the bug report. Understand the symptom.
2. **Update INTENT.md** — add the correct behavior as an Example row.
   Bugs are edge cases that belong in the spec permanently.
3. **Write the Gherkin scenario** — describe what SHOULD happen.
4. **Run the test.** It fails (RED). This confirms the bug exists.
5. **NOW read the code.** Find the bug. Fix it. Minimal change.
6. **Run the test.** It passes (GREEN). Fix is proven.
7. **Document** — resolution in `.bdd/qa/resolutions/`.

Step 5 is where you read source code. Not step 1. The test written at
step 3 tells you exactly what to look for — the gap between "should
return 200 with active session" and "actually returns 500." The fix is
scoped to closing that gap. No guessing, no over-investigation.

### New Feature Protocol

1. **Interview** — extract requirements into INTENT.md Layer 3 examples.
2. **Critique** — is every line earning its place?
3. **Convert to Gherkin** — each Example row becomes a scenario.
4. **Run tests.** They fail (RED).
5. **Build.** Code until tests pass (GREEN).
6. **Sync** — does the code match the intent?

### Refactoring Protocol

1. Verify existing scenarios cover current behavior. Run them — all GREEN.
   These are your safety net.
2. Update INTENT.md if structure/constraints change.
3. Perform the refactoring.
4. Run ALL scenarios — still GREEN. The tests prove nothing broke.

## Wrong vs Right

| Your Instinct (WRONG) | Bulletproof (RIGHT) |
|---|---|
| Bug reported → read source code → find the problem → write fix | Bug reported → define expected behavior → write test → RED → fix → GREEN |
| Feature requested → start coding → test manually → ship | Feature requested → write intent → write scenarios → RED → code → GREEN |
| Test fails → debug the test → adjust assertions | Test fails → debug the application → fix the code |
| Dependency unavailable → mock it to unblock | Dependency unavailable → stop and tell the user |
| "Let me investigate the codebase first" | "Let me define what correct behavior looks like first" |
| "This is too simple for the full workflow" | The simpler the fix, the faster the workflow. Skip nothing. |

That last row is the most common trap. "Let me investigate" feels
productive. It feels like the responsible thing to do. But investigation
without a behavioral target is wandering. Define the target first,
then investigate with purpose.

See `references/behavioral-protocol.md` for detailed walkthroughs.

## Combining IDD + BDD

| Concern | IDD handles it | BDD handles it |
|---------|---------------|----------------|
| "Why does this module exist?" | INTENT.md anchor | — |
| "What are the constraints?" | Layer 2 constraint tables | — |
| "What should the user experience?" | — | Gherkin scenarios |
| "Does it actually work?" | — | E2E against real system |
| "Are acceptance criteria met?" | Layer 3 examples | Feature files |

IDD defines the contract. BDD verifies it.

## Directory Structure

```
project/
  .idd/                          # Intent (owned by IDD)
    project.intent.md
    modules/{module}/INTENT.md
  .bdd/                          # Verification (owned by BDD)
    features/{module}/*.feature  # Mirrors .idd/modules/
    steps/*.steps.ts
    qa/findings/                 # What happened
    qa/resolutions/              # What was fixed
```

Module names in `.bdd/features/` mirror `.idd/modules/`. The directory
name IS the traceability link.

## Quick-Start

### "I have IDD + want to add BDD verification"

1. Create `.bdd/` structure. Mirror each `.idd/modules/` in `.bdd/features/`
2. Convert Layer 3 examples to Gherkin scenarios
3. Convert Layer 2 runtime constraints to step assertions
4. Run against real system. Document findings.

### "Something is broken and I need to fix it"

Follow the Bug Fix Protocol above. Do NOT open source files first. The
test tells you what's broken. The fix is scoped to making that test pass.

See `references/orchestration-workflow.md` for bridge workflow details.

## Decision Tree

| If intent says... | Write this BDD artifact |
|---|---|
| Example: `f(valid_input) → expected_output` | Gherkin Scenario |
| Constraint: observable limit (rate, timeout) | Dedicated scenario |
| Constraint: runtime invariant ("always return 401") | Step assertion |
| Constraint: static/architectural ("A never imports B") | CI lint rule |
| Structure: directory tree | Test directory mirrors module directory |

## Reference Files

| File | Contents |
|------|----------|
| `references/orchestration-workflow.md` | Bridge model: Layer-to-Gherkin conversion, constraint-to-step mapping, sync checklist, combined lifecycle, anti-patterns |
| `references/behavioral-protocol.md` | Detailed wrong-vs-right walkthroughs, instinct traps with redirects, self-check checkpoints, recovery when you started wrong |
