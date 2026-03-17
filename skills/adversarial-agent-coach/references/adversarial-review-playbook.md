# Adversarial Review Playbook

Sources: Anthropic prompt engineering and eval guidance, ReAct, Chain-of-Thought prompting, Reflexion, MAR, Six Sigma Agent patterns, industrial hallucination reduction practice

Covers: failure taxonomy, contradiction pressure, falsification prompts, edge-case search, and how to convert critique into a better next draft.

## Purpose

Use this file when a draft feels polished but suspicious, when an answer agrees too quickly, or when you need a reliable way to find the weak joints in an agent's output.

Adversarial coaching is not deception. It is structured skepticism. The point is to make the answer survive contact with reality.

## What to Attack First

Attack the smallest unit that can break correctness.

| Priority | What to inspect | Why it fails often |
|----------|-----------------|--------------------|
| 1 | Core claim | If false, the whole answer collapses |
| 2 | Hidden assumption | The agent often imports unstated premises |
| 3 | Missing observation | Tool-driven work fails when a step is assumed, not observed |
| 4 | Edge case | Drafts are often optimized for the happy path only |
| 5 | Scope match | The answer may be good, but for the wrong task |

## Failure Taxonomy

| Failure mode | Detection signal | Typical root cause | First intervention |
|--------------|------------------|--------------------|--------------------|
| Sycophancy | Mirrors user language without challenge | Rewarding agreement over truth | Ask for strongest disagreement |
| Bluffing | Sounds precise, lacks support | Pressure to be complete | Require evidence tier per claim |
| Vague abstraction | Generic principles, no operational detail | Insufficient grounding | Demand one concrete example or step |
| Missing edge cases | Only ideal path described | Shallow review pass | Force boundary-condition search |
| Tool optimism | "Done" without proof | No act-observe separation | Require explicit observation log |
| Incomplete decomposition | Jumps from question to answer | Unbroken reasoning chain | Split into subclaims or subtasks |
| False certainty | No uncertainty markers despite risk | Style over calibration | Add confidence statements with reasons |
| Goal drift | Helpful content that misses the request | Nearby-task substitution | Restate target and trim extras |

## Contradiction Pressure

The most reliable first move is to ask how the answer could fail.

Use pressure prompts like these:

| Prompt | Best use |
|--------|----------|
| "What would make this false?" | Expose brittle claims |
| "Which assumption is doing the most work here?" | Surface hidden premises |
| "Give the strongest counterexample." | Stress-test logic |
| "What observation would disprove your next step?" | Tool-driven workflows |
| "Which sentence sounds strongest but is least supported?" | Tone vs evidence mismatch |

### Practical Sequence

1. Isolate the answer's most important claim.
2. Ask for the strongest plausible contradiction.
3. Decide whether the contradiction is real, resolved, or requires a caveat.
4. Patch only the affected claim first.
5. Re-run one more contradiction pass.

## Edge-Case Search

Most model drafts are optimized for the center of the distribution. Push them to the boundary.

| Edge-case type | Questions to ask |
|----------------|------------------|
| Empty input | What if required data is missing? |
| Maximal input | What breaks under very large scale or long context? |
| Wrong type | What if the input shape or format is invalid? |
| Ambiguous intent | What if the task can be interpreted two ways? |
| Partial success | What if step 1 works but step 2 fails? |
| Adversarial environment | What if assumptions about tools or network are wrong? |

### Edge-Case Drill

Use this pattern:

1. Identify the happy-path assumption.
2. Flip it.
3. Ask whether the answer still holds.
4. If not, add a branch, guard, or caveat.

## Falsification Before Expansion

Do not ask the model to elaborate until it survives contradiction pressure.

Weak order:

1. Draft answer
2. Expand details
3. Discover contradiction late

Better order:

1. Draft answer
2. Falsify it
3. Repair it
4. Expand only the repaired version

This preserves signal and reduces confident nonsense.

## Good Adversarial Tone

Be sharp about the work, calm about the process.

| Bad move | Better move |
|----------|-------------|
| "This is wrong." | "This claim is under-supported. Prove or soften it." |
| "Try harder." | "Find the weakest claim and repair that one first." |
| "You missed stuff." | "List two likely edge cases you have not covered." |
| "That sounds fake." | "What evidence tier supports this sentence?" |

## Claim Surgery

When a sentence fails review, do not nuke the whole answer. Repair the claim.

### Claim Repair Options

| Problem | Repair |
|---------|--------|
| No support | Add source, observation, test, or remove |
| Too broad | Narrow the scope |
| Too certain | Add calibrated uncertainty |
| Missing condition | Add the dependency or precondition |
| Easily broken by counterexample | Split into branches |

### Example

Weak claim:

"This approach always improves retrieval accuracy."

Pressure result:

- Unsupported absolute
- No conditions specified
- No evaluation setup mentioned

Repaired claim:

"This approach often improves retrieval accuracy when chunking and ranking are the main bottlenecks, but it should be verified against a labeled eval set before adoption."

## Sycophancy Countermeasures

If the model is aligning to the user's confidence instead of the task, force dissent.

Use one of these patterns:

- "Assume the user's framing is partly wrong. What is the strongest objection?"
- "If you had to disagree with the current plan, what would you say?"
- "Which part of the request is likely to cause downstream problems?"

### Dissent Protocol

1. Restate the goal neutrally.
2. Identify the assumption to challenge.
3. Provide one concrete consequence if it stays unchallenged.
4. Offer a safer or more reliable alternative.

This keeps pushback useful instead of performative.

## Red-Team Checklist

Run this checklist before accepting a high-stakes answer:

- Does the answer claim more than the evidence supports?
- Is there a strong counterexample that has not been handled?
- Did any tool step skip direct observation?
- Is the answer solving the exact task, not a nearby one?
- Are limitations explicit where proof is missing?
- Would a skeptical reviewer know what to verify next?

## Stop Conditions

Adversarial review should stop when it stops paying for itself.

Stop when:

- The top claims have support or explicit unknowns.
- Remaining objections are stylistic, not correctness-related.
- A second contradiction pass finds no new substantive risk.

Escalate when:

- The same failure keeps returning after revision.
- The answer depends on unverified external facts.
- The task is high stakes and needs multi-agent review.

## Hand-off to Other References

Use other files based on the failure you uncovered:

| Need | File |
|------|------|
| Evidence rules | `verification-and-evidence.md` |
| Iterative retry loop | `react-reflexion-loops.md` |
| Multi-role review | `multi-agent-review.md` |
| Measurable quality bar | `evals-and-metrics.md` |

## Minimal Review Template

Use this compact pattern during live work:

1. **Claim at risk** — quote the sentence or step.
2. **Why it may fail** — contradiction, missing evidence, or edge case.
3. **Best next move** — prove, soften, branch, or remove.
4. **Repaired output** — targeted revision only.

This is usually enough to turn a shaky answer into a robust one.
