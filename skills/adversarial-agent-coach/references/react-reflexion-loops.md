# ReAct and Reflexion Loops

Sources: ReAct, Reflexion, MAR, Anthropic agentic workflow guidance, verification-first debugging patterns

Covers: act-observe discipline, self-critique loops, retry boundaries, and how to revise without thrashing.

## Purpose

Use this file when the task requires more than one shot, especially when tools are involved or the same type of error keeps returning.

The core rule is simple: do not repeat the same failing move with slightly different wording.

## ReAct in Practice

ReAct means the model alternates between reasoning and action, but the important operational detail is the observation boundary.

| Stage | Question |
|-------|----------|
| Plan | What am I trying next and why? |
| Act | What concrete step will I take? |
| Observe | What actually happened? |
| Update | What changed in my model of the task? |

### Minimal ReAct Loop

1. State the next hypothesis.
2. Perform the smallest useful action.
3. Capture the result exactly.
4. Update the plan from the result, not from hope.

## Common ReAct Failures

| Failure | Signal | Fix |
|---------|--------|-----|
| Action without plan | Random tool flailing | Write one-step hypothesis first |
| Observation skipped | Claims success too early | Require explicit output check |
| Update skipped | Repeats same mistake | Write what changed after result |
| Overplanning | Endless reasoning, no action | Take the cheapest discriminating step |

## Reflexion in Practice

Reflexion adds a deliberate review pass after failure.

Use it when:

- the answer failed a quality gate
- the same bug or gap reappeared
- first-pass reasoning looked plausible but wrong

### Reflexion Loop

1. Produce the draft or attempt.
2. Evaluate it against explicit criteria.
3. Write the failure hypothesis in plain language.
4. Revise only the part implicated by that hypothesis.
5. Re-test.

This is stronger than asking the model to "think harder" because it binds the next attempt to a diagnosed failure.

## Failure Hypothesis Format

Use a compact reflection note:

| Field | Example |
|-------|---------|
| What failed | `Answer claimed tests pass, but build output showed one failure.` |
| Why it failed | `I inferred completion from partial output.` |
| Next change | `Inspect final exit code and summary line before claiming success.` |

## When Reflexion Beats ReAct

| Situation | Better loop |
|-----------|-------------|
| Need new external information | ReAct |
| Need better reasoning on same information | Reflexion |
| Tool workflow is brittle | ReAct + verification |
| Quality bar is conceptual or stylistic | Reflexion |

## Retry Boundaries

Retries help only when they change the decision basis.

Allowed reasons to retry:

- new evidence arrived
- failure hypothesis changed
- verification exposed a specific weakness
- role split changed the perspective

Bad reasons to retry:

- the first answer felt wrong
- the user is impatient
- the draft looked too short
- confidence is low but no new step is proposed

## The Two-Retry Rule

If the same failure mode survives two revisions, change the method.

Possible method changes:

- switch from single-agent to skeptic/verifier split
- replace reasoning with direct verification
- decompose the task further
- reduce scope and answer only what can be supported

## Builder vs Critic Separation

One model can simulate multiple roles, but the prompts must stay distinct.

| Role | Job |
|------|-----|
| Builder | Produce the best current answer |
| Critic | Find the weakest assumptions and unsupported claims |
| Verifier | Decide whether evidence is sufficient |

Keep the critic from rewriting the whole answer. Its job is to pressure-test, not take over.

## Practical Single-Agent Emulation

When only one agent is available, run roles in sequence:

1. Builder draft
2. Critic pass: list top 3 risks
3. Verifier pass: check whether each risk is resolved
4. Builder patch pass only

This sequence reduces self-confirmation bias better than free-form self-critique.

## Revision Discipline

Patch the minimum necessary surface area.

| Problem | Revision style |
|---------|----------------|
| One weak claim | Edit that sentence or paragraph |
| Missing evidence | Add citation, test result, or uncertainty note |
| Scope drift | Cut unrelated sections |
| Tool optimism | Add explicit observation and re-interpret |

Large rewrites often hide whether the real issue was solved.

## Loop Exit Signals

Exit the loop when:

- the original failure hypothesis is resolved
- verification passes at the required evidence tier
- a new loop would only polish wording

Escalate when:

- each loop creates different answers with the same unresolved weakness
- the task remains blocked by missing external evidence
- the stakes justify multi-agent review or human escalation

## Example: Tool-Backed ReAct

1. Hypothesis: `The test suite fails because the config file is malformed.`
2. Action: run config parse or diagnostics.
3. Observation: `No parse error; failure occurs in unrelated test.`
4. Update: reject config hypothesis, inspect failing test path.

## Example: Reflexion on Research Draft

1. Draft claims a framework is official guidance.
2. Critic notes no official source was cited.
3. Failure hypothesis: pattern was inferred from blogs.
4. Revision: either find official doc or downgrade claim to practitioner pattern.

## Relationship to Other References

Use this file with:

- `verification-and-evidence.md` when the loop needs stronger proof
- `adversarial-review-playbook.md` when you need better critique prompts
- `multi-agent-review.md` when single-agent loops are not enough

The best loop is the lightest one that resolves the actual failure.
