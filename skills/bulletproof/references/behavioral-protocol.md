# Behavioral Protocol

Sources: Agent failure analysis (Bulletproof deployment runs), Beck
(TDD By Example), Smart/Molak (BDD in Action), ArcBlock/idd standard.

Covers: Agent behavioral overrides, detailed wrong-vs-right walkthroughs
for bugs/features/refactors, instinct traps with redirects, self-check
checkpoints, recovery protocol when you already started wrong.

## Why Your Default Instinct Is Wrong

AI agents are trained on millions of debugging sessions that follow this
pattern: read error → read code → understand code → fix code. This pattern
is deeply ingrained and feels productive. You feel like you are making
progress when you read source files.

Bulletproof requires a different pattern: read error → define correct
behavior → prove the behavior is unmet → fix to meet the behavior.

The difference seems subtle but changes everything:

| Code-first debugging | Behavior-first debugging |
|---|---|
| Starts from "what IS" | Starts from "what SHOULD BE" |
| Produces a code change and hope | Produces a test, a spec update, and a proven fix |
| Scoped by what you understand about the code | Scoped by the behavioral gap (always precise) |
| Bug can resurface — nothing guards against it | Test prevents regression permanently |
| "Fixed" means "I think it works now" | "Fixed" means "the test passes" |

When you start from code, you are building a mental model of the system
and trying to reach "what should be." When you start from behavior, you
already know "what should be" and you measure the gap. The second approach
is faster, produces better artifacts, and the fix is always correctly scoped.

## Self-Check Checkpoint

Run this check before every significant action. If any answer is "no,"
stop and correct course.

| # | Checkpoint | Question to ask yourself |
|---|---|---|
| 1 | Intent updated | Have I added the expected behavior to INTENT.md? |
| 2 | Scenario written | Have I written a Gherkin scenario that captures it? |
| 3 | RED confirmed | Have I run the test and confirmed it fails? |
| 4 | Fix scoped | Am I changing only what the failing test demands? |
| 5 | GREEN confirmed | Does the test pass after my change? |
| 6 | No mocks | Am I running against real dependencies? |
| 7 | Documented | Is the finding/resolution recorded in `.bdd/qa/`? |

If you find yourself reading source code and checkpoints 1-3 are unchecked,
you have reverted to instinct. Stop. Go back to checkpoint 1.

## Walkthrough 1: Bug Fix

**Scenario:** User reports "Login returns 500 for valid users."

### Wrong Approach (instinct-driven)

```
1. Read the bug report: "Login returns 500 for valid users"
2. Open auth/login.ts
3. Read the login handler line by line
4. Read the database query
5. Notice a missing null check on line 47
6. Add the null check
7. Test manually in browser
8. Declare it fixed
```

What went wrong here:

- No test proves the fix works. You tested manually once. Manual tests
  do not run again tomorrow.
- No spec captures what "login for valid users" should return. The expected
  behavior lives only in your head during this debugging session.
- If someone removes the null check later, nothing catches it.
- The bug's correct behavior is not documented anywhere permanent.
- You spent time reading code top-to-bottom instead of letting a test
  point you to the problem.

### Right Approach (Bulletproof)

```
1. Read the bug report: "Login returns 500 for valid users"

2. Update INTENT.md — add to Examples table:
   | authenticate("valid@test.com", "correct") | Session { status: "active" } |
   (This row may already exist. If so, the intent is correct and the
   code violates it — which is useful information.)

3. Write Gherkin scenario:
   Scenario: Successful login with valid credentials
     Given a registered user "valid@test.com" with password "correct"
     When the user authenticates with email "valid@test.com" and password "correct"
     Then the response status is 200
     And the response contains a session with status "active"

4. Run the test → FAILS with status 500 instead of 200. RED confirmed.
   The test now documents exactly what is broken and what "fixed" means.

5. NOW read the code. The test failure tells you: the login endpoint
   returns 500 when it should return 200 with a session. You know exactly
   what to look for — something that throws/crashes instead of returning
   a session. Open auth/login.ts. Find the null check issue on line 47.
   Fix it. Minimal change.

6. Run the test → PASSES. GREEN confirmed. The fix is proven.

7. Document in .bdd/qa/resolutions/:
   Bug: Login 500 for valid users
   Root cause: Missing null check on user.profile (line 47)
   Fix: Added null coalescing for profile field
   Verified: login.feature scenario passes
```

The code investigation happens at step 5, not step 1. The test written
at step 3 told you exactly what to look for — the gap between "should
return 200 with active session" and "actually returns 500." You did not
wander through source files building a mental model. You went straight
to the gap.

## Walkthrough 2: New Feature

**Scenario:** Product request "Add rate limiting to login endpoint."

### Wrong Approach (instinct-driven)

```
1. Read request: "Add rate limiting to login"
2. Research rate limiting libraries/approaches
3. Pick an approach
4. Implement rate limiting middleware
5. Wire it into the login route
6. Test manually by hitting the endpoint a few times
7. Ship it
```

No spec. No test. No proof it actually limits at the right threshold.
No proof it returns the right status code. No proof it resets correctly.

### Right Approach (Bulletproof)

```
1. Read request: "Add rate limiting to login"

2. Update INTENT.md — add to Constraints table:
   | Rule | Rationale | Verified by |
   | Rate limit: 5 attempts per minute per IP | Brute force prevention | BDD scenario |

   Add to Examples table:
   | authenticate(6th attempt in 60s) | RateLimitError { code: "RATE_LIMITED", retryAfter: 60 } |

3. Write Gherkin:
   Feature: Authentication Rate Limiting

   Scenario: Sixth login attempt within one minute is rate limited
     Given a registered user "user@test.com"
     When the user fails authentication 5 times within 60 seconds
     And the user attempts authentication a 6th time
     Then the response status is 429
     And the response contains an error with code "RATE_LIMITED"

   Scenario: Rate limit resets after one minute
     Given a registered user "user@test.com"
     And the user has been rate limited
     When 60 seconds have passed
     And the user attempts authentication
     Then the response status is not 429

4. Run → FAILS (no rate limiting exists). RED confirmed.

5. Implement rate limiting. Run → PASSES. GREEN confirmed.

6. Refactor if needed. Tests still green.
```

The scenarios captured two behaviors you might have missed with
instinct-driven development: the rate limit trigger AND the reset.
Defining behavior first forces you to think about the full contract.

## Walkthrough 3: Refactoring

**Scenario:** Tech debt cleanup "Extract auth logic into separate service."

### Wrong Approach (instinct-driven)

```
1. Read request: "Extract auth into separate service"
2. Create new service directory
3. Move auth files
4. Update imports across the codebase
5. Run the app, click around
6. Looks OK, ship it
```

### Right Approach (Bulletproof)

```
1. Run existing .bdd/features/auth/*.feature scenarios.
   All GREEN. These are your safety net — they define what "auth works"
   means, independent of where the code lives.

2. Update INTENT.md Layer 1 structure diagram to reflect the new
   service boundary. Update Layer 2 constraints if architectural
   rules change.

3. Perform the refactoring. Move files, update imports, restructure.

4. Run ALL auth scenarios. Still GREEN.
   The tests prove the refactoring preserved behavior.

5. If any test FAILS, the refactoring introduced a bug. Fix the
   code, not the test. The test defines correct behavior; the
   refactoring must preserve it.
```

Refactoring is the scenario where existing tests shine. They guard
behavior while you restructure code. Without them, you are relying
on manual testing and hope — which is how refactoring introduces bugs.

## Walkthrough 4: Investigating an Unfamiliar Codebase

**Scenario:** You are new to the codebase. Something needs fixing.

### Wrong Approach (instinct-driven)

```
1. Read directory structure
2. Open main entry point
3. Follow the call chain
4. Read related modules
5. Build mental model
6. Start fixing
```

This approach burns enormous context on code that may be irrelevant
to the actual problem. You read 20 files when 2 were relevant.

### Right Approach (Bulletproof)

```
1. Read the bug/task description.

2. Check if .idd/ exists with relevant INTENT.md files. If yes,
   read the intent — it tells you what the module SHOULD do, its
   constraints, and its examples. This is faster than reading code
   because intent describes behavior at a higher level.

3. Check if .bdd/features/ has relevant scenarios. If yes, run them.
   Passing tests tell you what works. Failing tests tell you what
   is broken. This is faster than reading code because tests show
   you behavior, not implementation.

4. Update INTENT.md with the expected behavior for your task.

5. Write a Gherkin scenario. Run it. RED or GREEN tells you the
   current state of the system with certainty — no guessing.

6. Now you have a precise behavioral target. Read only the code
   relevant to making the test pass.
```

The key difference: instead of reading code to understand the system,
you read intent and tests to understand the system. Then you read only
the code you need. This is dramatically more efficient.

## Instinct Traps

These are the moments where agents most commonly revert to instinct.
Learn to recognize the trigger and redirect.

### Trap 1: "Let me investigate first"

**Trigger:** Receiving a bug report or unclear task.

**What happens:** You open source files, read code, build a mental model
of how things work. This feels productive. You are learning. But you are
learning what IS, not defining what SHOULD BE. Two hours later, you have
read 15 files and still have not written a test.

**Redirect:** Ask "what should the system do in this case?" Write it in
INTENT.md and a Gherkin scenario. Run the scenario. The result (PASS or
FAIL) tells you more about the system state than 15 files of source code.

### Trap 2: "The test is wrong"

**Trigger:** A test you wrote fails in an unexpected way.

**What happens:** You look at the assertion, look at the actual value,
and think "maybe I wrote the wrong expected value." You adjust the test
to match actual behavior.

**Redirect:** The test describes what SHOULD happen. If reality differs,
reality is wrong — not the test. Fix the application. The only exception:
you made a genuine mistake in test setup (wrong test data, wrong endpoint
URL). Even then, fix the setup. Never weaken the assertion.

### Trap 3: "I'll add a test later"

**Trigger:** Time pressure, "simple" fix, high confidence in the change.

**What happens:** You make the code change directly. You plan to add a
test afterward. You never do, or the test you add is an afterthought
that tests the implementation rather than the behavior.

**Redirect:** The test comes FIRST because it defines what "fixed" means.
Without the failing test, you do not have a definition of done. The test
takes 2 minutes. The debugging session when the bug resurfaces without
a test to catch it takes hours.

### Trap 4: "Let me mock this to unblock myself"

**Trigger:** A dependency (database, API, service) is unavailable or
slow to set up.

**What happens:** You create a mock/stub/fake so you can keep making
progress. The tests pass. You feel productive.

**Redirect:** Stop. Tell the user the dependency is unavailable. A test
that passes against a mock proves the code works with the mock — it says
nothing about whether the code works with reality. If the user explicitly
says "mock it for now," add `TODO: remove mock` and document it in the
resolution. But never introduce mocks on your own initiative.

### Trap 5: "This is too simple for the full workflow"

**Trigger:** Trivial-looking bug, one-line fix, "obvious" change.

**What happens:** You skip the intent update and Gherkin scenario because
"it's just a null check" or "it's just a typo in a query." You fix the
code directly.

**Redirect:** The simpler the fix, the faster the workflow goes. Updating
INTENT.md is one line. Writing the scenario is 5 lines. Running it takes
seconds. The total overhead is under 2 minutes. Skipping the workflow
saves 2 minutes now and risks the bug returning in a week with no test
to catch it. Two minutes of discipline versus hours of future debugging.

### Trap 6: "I need to understand the architecture first"

**Trigger:** Working on a system you have not seen before.

**What happens:** You start reading README, docs, source files, config
files, trying to build a complete mental model before doing anything.

**Redirect:** You do not need a complete mental model. You need to know
what the system SHOULD DO for your specific task. Read the INTENT.md for
the relevant module. Read the existing Gherkin scenarios. These tell you
the system's contract without requiring you to understand every line of
implementation. Then write your test and let the failure guide you to
exactly the code you need to read.

## Recovery Protocol

If you realize you have already started wrong — you have been reading
source code, you have been debugging without a test, you have been
investigating without defining behavior — here is how to recover:

### Step 1: Stop

Do not continue the investigation. Whatever mental model you have built
from reading code is useful context, but it is not a substitute for the
workflow.

### Step 2: Capture What You Learned

Write down what you discovered so far. "The login handler calls
getUserProfile() which can return null, and line 47 does not handle
that." This knowledge is not wasted — it will speed up step 5 of the
correct workflow.

### Step 3: Restart the Loop

Go to the beginning: update INTENT.md, write the Gherkin scenario, run
it to confirm RED, then apply your fix, confirm GREEN. You already know
where the bug is from your investigation — the workflow will go fast.
But the test and intent update are not optional. They must exist.

### Step 4: Do Not Skip Steps Because "I Already Know the Answer"

The most dangerous moment is when you have already found the bug through
code investigation and you think "I already know the fix, let me just
apply it." The test and intent update serve purposes beyond finding the
bug: they prevent regression, document behavior, and prove the fix. They
are not debugging tools — they are engineering artifacts. You need them
regardless of whether you already know the answer.

## Intent-to-Test Conversion

Quick reference for converting INTENT.md content to BDD artifacts:

| INTENT.md content | BDD artifact |
|---|---|
| Examples table: `f(x) → y` | Gherkin Scenario: Given/When/Then |
| 3+ examples with same structure, different values | Scenario Outline with Examples table |
| Constraint: runtime invariant ("all errors return 401") | Step assertion — invariant inside the step definition |
| Constraint: observable limit (rate, timeout, concurrency) | Dedicated Gherkin scenario |
| Constraint: static/architectural ("A never imports B") | CI lint rule, not a BDD scenario |
| Structure: directory tree, module boundary | Test directory mirrors module directory |

When converting, map one Example row to one Scenario. If the Example row
has multiple assertions (function returns X AND creates record Y), the
Scenario has multiple Then steps. Do not split into separate scenarios
unless the behaviors are genuinely independent.

## Post-Fix Checklist

After every fix, before declaring "done":

- [ ] INTENT.md updated with the behavior/constraint/example
- [ ] Gherkin scenario exists capturing the expected behavior
- [ ] Scenario was RED before the fix (confirming the bug/gap)
- [ ] Scenario is GREEN after the fix (proving the fix works)
- [ ] No mocks introduced (running against real dependencies)
- [ ] Resolution documented in `.bdd/qa/resolutions/`
- [ ] All pre-existing scenarios still pass (no regressions introduced)
- [ ] Code change is minimal — scoped to what the test demands

If any checkbox is unchecked, the task is not complete.
