# The RED-GREEN Fix Cycle

Sources: Beck (TDD By Example), Smart/Molak (BDD in Action), SWE-bench (Princeton NLP), REFINE pattern (Microsoft Research), Sweep.dev iteration patterns

Covers: confirming the bug (RED), implementing fixes with escalating strategies, analyzing failures between iterations, the never-weaken rule, escalation protocol.

This is the core of the skill. The Gherkin scenario is written. Now make it pass.
Do not give up. Do not weaken the test. Iterate until GREEN or escalate after
5 genuine attempts.

## The Cycle

```
Gherkin scenario exists (from issue-to-gherkin step)
         |
         v
   Run scenario against current code
         |
    PASS? ---YES---> Issue already fixed. Close it. Done.
         |
        NO (RED confirmed)
         |
         v
   Read test output. Understand WHY it fails.
         |
         v
   Implement minimal fix (iteration N)
         |
         v
   Run scenario again
         |
    PASS? ---YES---> Proceed to verification (fix-verification.md)
         |
        NO
         |
         v
   Analyze new failure. Is it DIFFERENT from before?
         |
         v
   Adjust approach. Go to "Implement minimal fix" (iteration N+1)
         |
   N >= 5? ---YES---> Escalate (do NOT abandon)
```

Maximum 5 iterations. Each iteration uses a progressively broader strategy.

## RED Phase: Confirming the Bug

Before writing ANY fix, run the Gherkin scenario and confirm it fails. This is
non-negotiable.

```bash
# Run the specific scenario tagged with the issue number
[test-runner] --grep "@issue-42"
```

### Interpreting RED Results

| Test output | Meaning | Action |
|-------------|---------|--------|
| Assertion failure (expected X, got Y) | Bug confirmed. The code produces wrong behavior. | Proceed to fix. |
| Timeout (scenario hangs) | Feature is broken OR test infrastructure is wrong. | Check if the feature works at all. If feature works but test hangs, fix the step definition. |
| Runtime error in step code (import error, undefined function) | Step implementation has a bug. | Fix the step code, NOT the application. Then re-run. |
| Setup/infrastructure error (DB not running, server not started) | Test environment issue. | Fix infrastructure. Start required services. Then re-run. |
| Scenario PASSES | Bug does not exist, or was already fixed. | Verify manually. If truly fixed, close the issue. If not, the test is wrong — revisit the Gherkin. |

If the scenario passes when the bug clearly exists, the Gherkin does not
capture the actual broken behavior. Go back to `issue-to-gherkin.md` and
rewrite the scenario with more precision.

## Implementing the Fix

### The Five Rules of Fixing

1. **Read the failing test output FIRST.** Understand exactly which assertion
   failed, what the expected value was, and what the actual value was.

2. **Trace from test to code.** Use the Given/When/Then steps to find the
   relevant source code. The When step tells you what function is being
   exercised. The Then step tells you what output is wrong.

3. **Make the MINIMAL change.** The smallest edit that makes the test pass.
   Do not improve code style, rename variables, or restructure while fixing.

4. **Fix one thing at a time.** Do not fix adjacent issues you notice. One
   issue per fix cycle. File new issues for other problems.

5. **Do not refactor while fixing.** Fix the bug. Commit. Refactor later if
   needed. Mixing fix and refactor makes it impossible to verify which change
   fixed the bug.

### Iteration Strategies

Each iteration uses a progressively broader approach. Do not skip to iteration
3 on the first try. The simplest fix is often the correct one.

| Iteration | Strategy | Description |
|-----------|----------|-------------|
| 1 | **Direct fix** | The most obvious change. If the error says "expected UTF-8 but got Latin-1", add the encoding parameter. |
| 2 | **Root cause analysis** | The direct fix did not work. Read the stack trace more carefully. Find the ACTUAL function where the bug originates, not just where it manifests. |
| 3 | **Broader context** | Read surrounding code. Understand the data flow. Maybe the bug is in a function upstream that passes bad data to the function you fixed. |
| 4 | **Alternative approach** | The code path you have been fixing might be fundamentally wrong. Try a different algorithm, a different library function, or a different code path entirely. |
| 5 | **Minimal viable fix** | All elegant solutions have failed. Write the simplest, most brute-force code that makes the test pass. Correctness over elegance. |

### What to Do Between Iterations

After each failed fix attempt:

1. Read the ENTIRE test output, not just the first error line.
2. Compare the new failure to the previous failure.
3. Check: is the error DIFFERENT from before? If yes, that is progress.
4. Check: did the fix actually get loaded? (Did you save the file? Is the
   test hitting the right code path?)
5. Revert the failed fix if it made things worse. Keep it if the error changed
   in a promising direction.

## Analyzing Test Failures

After each iteration, the test either passes (done) or fails (continue). When
it fails, use this table to diagnose:

| Failure pattern | Diagnosis | Next action |
|-----------------|-----------|-------------|
| Same assertion, same expected/actual values | Fix had zero effect. | Verify fix was saved. Check if the test is hitting the right code path. The fix may be in the wrong file or function. |
| Same assertion, different actual value | Fix partially worked. The logic is moving in the right direction. | Adjust the fix. You are close. |
| Different assertion entirely | Fix changed the behavior in an unexpected way. | Analyze which behavior changed. The fix may need to be more targeted. |
| New runtime error (TypeError, null reference) | Fix introduced a new bug. | Make the fix more defensive. Handle the edge case that caused the new error. |
| Timeout where assertion used to fail | Fix changed the code path and now it hangs. | The fix may have created an infinite loop or deadlock. Investigate the new code path. |
| Different scenario fails (regression) | Fix broke adjacent functionality. | The fix needs to handle BOTH the target behavior and the adjacent one. See `fix-verification.md`. |

### Execution-Level Feedback

Between iterations, pass FULL context forward. Do not strip or summarize.

**Required context for each iteration:**
- Complete test output (stdout and stderr)
- The exact diff of what was changed
- Stack traces, if any
- The assertion: expected value vs actual value
- Any console output or log messages from the application
- The iteration number and what strategy was used

Do not pass "the test failed" as context. Pass "the test asserted
expected='Jose Garcia' but got='JosÃ© GarcÃ­a', suggesting the encoding
conversion is happening after the export function returns, not before."

## The Never-Weaken Rule

This is the cardinal rule. Violation means the work is invalid.

| Action | Verdict |
|--------|---------|
| Change Gherkin scenario to match code behavior | **FORBIDDEN** |
| Add `@skip` or `.skip()` to the failing scenario | **FORBIDDEN** |
| Mock a dependency to avoid a real failure | **FORBIDDEN** |
| Change expected values to match actual values | **FORBIDDEN** |
| Replace exact assertion with approximate ("close to") | **FORBIDDEN** |
| Add retry/polling logic to hide flaky behavior | **FORBIDDEN** |
| Wrap assertion in try-catch and swallow the error | **FORBIDDEN** |
| Comment out failing assertions | **FORBIDDEN** |
| Reduce the number of scenarios to "simplify" | **FORBIDDEN** |

If the scenario seems wrong after reading the code, re-read the issue. The
issue defines the behavior. The code must conform to the issue.

If you genuinely believe the scenario is incorrect (the issue was misunderstood),
go back to the issue and re-read it from scratch. If the Gherkin truly
misrepresents the issue, fix the Gherkin — but document WHY in the PR with a
reference to the specific part of the issue that was re-interpreted.

This is the ONLY exception, and it requires explicit justification.

## When to Escalate

After 5 iterations without GREEN, escalate. Do not abandon.

### Escalation Protocol

1. **Document all 5 attempts.** For each iteration, record:
   - What strategy was used
   - What change was made (diff)
   - What the test output was
   - Why it did not work

2. **Write a detailed comment on the issue:**

```markdown
## Automated Fix Attempted

I attempted 5 fix iterations for this issue but could not achieve a passing test.

### Attempts
1. **Direct fix:** Added UTF-8 encoding parameter to export function.
   Result: Same garbled output. The encoding happens downstream.
2. **Root cause:** Found encoding happens in the serializer, not the exporter.
   Fixed serializer. Result: Different garbled output (progress).
3. **Broader context:** Traced data flow from DB to export. Found the DB
   driver strips encoding metadata. Result: Correct encoding but wrong
   line breaks.
4. **Alternative approach:** Used Buffer-based encoding instead of stream.
   Result: Correct encoding, correct line breaks, but headers are duplicated.
5. **Minimal viable:** Hard-coded BOM + manual header write.
   Result: Test still fails on the "parseable without errors" assertion.

### Root Cause Hypothesis
The CSV serialization pipeline has multiple encoding conversion points that
conflict. A proper fix likely requires refactoring the serializer to use a
single encoding pass.

### Suggested Next Steps
- Review the serializer pipeline in `src/export/serializer.ts`
- Consider replacing the custom serializer with a well-tested CSV library
```

3. **Label the issue** as `needs-human-review`:
```bash
gh issue edit 42 --add-label "needs-human-review"
```

4. **Do NOT close the issue.** It is still a real bug.

5. **Do NOT merge a partial fix.** If the test does not pass, the fix is
   not complete. Do not merge code that "mostly works."

## Anti-Patterns

| Anti-pattern | Why it fails | What to do instead |
|-------------|-------------|-------------------|
| Giving up after 1 attempt | Most bugs require 2-3 iterations. SWE-bench average is 2.3. | Try all 5 strategies before escalating. |
| Fixing without reading test output | You are guessing, not debugging. | Read the FULL output before writing code. |
| Changing test and code simultaneously | You cannot tell which change fixed the bug. | Change code only. The test is immutable. |
| Making large changes per iteration | Large diffs make it impossible to isolate the fix. | Small, targeted edits. One logical change per iteration. |
| Ignoring "progress" signals | A DIFFERENT failure is progress, not a new problem. | Track how the failure changes across iterations. |
| Skipping directly to iteration 5 | Brute-force should be the last resort, not the first. | Follow the iteration ladder in order. |
