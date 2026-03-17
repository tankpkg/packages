---
name: "@tank/adversarial-agent-coach"
description: |
  Improve AI agents with adversarial coaching, contradiction checks, evidence
  demands, and verification loops. Covers review, ReAct and Reflexion
  retries, multi-agent critique, and prompt tuning.
  Sources: Anthropic prompting/evals, ReAct, Reflexion, DSPy, DeepEval.

  Trigger phrases: "gaslight ai", "gaslighting ai agents", "make ai work
  better", "challenge my agent", "adversarial critique", "pressure test
  prompt", "contradiction check", "prove it", "verify output",
  "agent self-critique"
---

# Adversarial Agent Coach

Push the model to earn confidence through evidence and contradiction handling.
Treat "gaslighting AI" as adversarial coaching for better outputs, never deception.

## Core Philosophy

1. **Attack the draft, not the user.** The goal is a stronger answer, not theatrical aggression.
2. **Pressure without deception.** Never invent evidence, fake tool results, or force certainty.
3. **Make claims pay rent.** Important claims need support, caveats, or a verification step.
4. **Critique is only useful if it changes the next draft.** Convert objections into targeted revisions.
5. **Stop when risk drops, not when tone feels tough enough.** Reliability beats performative harshness.

## Quick-Start: Pick the Right Pressure Level

| Situation | Default move |
|-----------|--------------|
| Draft is vague or padded | Run contradiction and specificity checks |
| Draft sounds confident but thin | Demand evidence tier and confidence label |
| Task uses tools or data | Switch to act-observe-verify loop |
| Task keeps failing the same way | Run Reflexion-style failure review |
| High-stakes answer | Split roles into builder, skeptic, verifier |

## The Operating Loop

### Phase 1: Diagnose the Failure Mode

Classify the current output before changing anything:

| Failure mode | Signal | First response |
|--------------|--------|----------------|
| Overconfidence | Strong claims, weak support | Ask for claim-evidence-confidence |
| Sycophancy | Agrees too easily | Force disagreement and counterexamples |
| Hallucination risk | Missing source or unverifiable detail | Require proof or explicit uncertainty |
| Incomplete reasoning | Jumps to answer | Break into subclaims and verify each |
| Tool blindness | Assumes actions worked | Inspect observations before next step |

Load `references/adversarial-review-playbook.md` when the failure mode is unclear.

### Phase 2: Apply Pressure

Use the lightest intervention that exposes the weakness:

1. Ask what would make the answer false.
2. Demand the strongest missing evidence.
3. Require one concrete counterexample or edge case.
4. Make the model state confidence and why it is limited.
5. If tools exist, verify instead of debating.

Load `references/verification-and-evidence.md` for evidence tiers.

### Phase 3: Revise, Do Not Rant

After critique, revise only the risky parts first:

1. Remove unsupported claims.
2. Add source, test, or tool-backed support.
3. Tighten caveats where certainty is unjustified.
4. Re-run the top two contradiction checks.

Load `references/react-reflexion-loops.md` for revision loops.

### Phase 4: Verify Release Readiness

Before accepting the result, confirm:

| Check | Pass condition |
|-------|----------------|
| Evidence | Important claims have support or explicit unknowns |
| Contradictions | No unresolved counterexample breaks the answer |
| Reproducibility | Steps, commands, or criteria are inspectable |
| Scope | Answer matches the actual task, not a nearby one |

Load `references/evals-and-metrics.md` when the task needs a repeatable quality bar.

## Decision Trees

### When to Use Single-Agent vs Multi-Agent Review

| Signal | Recommendation |
|--------|----------------|
| Quick draft cleanup | Single-agent contradiction pass |
| Complex reasoning | Builder + skeptic roles |
| High-stakes or repeated failures | Builder + skeptic + verifier |
| Retrieval-heavy workflow | Add retrieval verifier and citation check |

Load `references/multi-agent-review.md` for role splits.

### When to Stop Iterating

| Signal | Action |
|--------|--------|
| Top risks resolved | Stop |
| New critique only finds style nits | Stop |
| Same failure repeats twice | Change method, do not repeat prompt |
| Missing evidence cannot be obtained | Mark uncertainty clearly and stop |

## Pressure Patterns That Work

Use short, concrete prompts like:

- "What would make this answer false?"
- "List the two weakest claims and either prove or remove them."
- "Show the observation that justifies the next step."
- "State confidence for each key claim and why it is not higher."
- "Give one serious counterexample and resolve it before finalizing."

## Anti-Patterns

| Do not do this | Why it fails | Better move |
|----------------|-------------|-------------|
| Fake confidence pressure | Produces bluffing | Ask for evidence tier instead |
| Demand certainty everywhere | Forces hallucination | Allow explicit unknowns |
| Rewrite everything after every critique | Hides the real fix | Patch the risky claims first |
| Attack the user's framing | Creates friction | Attack the draft's weak points |
| Simulate tool success | Breaks trust | Verify with real observations |

## Reference Files

| File | Contents |
|------|----------|
| `references/adversarial-review-playbook.md` | Failure taxonomy, contradiction pressure, edge-case and falsification tactics |
| `references/verification-and-evidence.md` | Evidence hierarchy, claim-evidence-confidence format, uncertainty rules |
| `references/react-reflexion-loops.md` | ReAct, Reflexion, and revision loops for tool use and retry discipline |
| `references/multi-agent-review.md` | Builder, skeptic, verifier role splits and structured disagreement patterns |
| `references/evals-and-metrics.md` | Eval-first optimization, regression gates, and agent-quality measurement patterns |
