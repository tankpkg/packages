# Verification and Evidence

Sources: Anthropic prompt engineering and eval guidance, DeepEval documentation, RAGAS evaluation patterns, process-verification research, reliability engineering practices

Covers: evidence hierarchy, claim-evidence-confidence formatting, uncertainty rules, and how to verify without pretending.

## Purpose

Use this file when the model sounds convincing but you need to know whether it has earned that tone.

Verification is the bridge between a good draft and a trustworthy answer.

## Evidence Hierarchy

Not all support is equal. Use the strongest affordable evidence.

| Tier | Evidence type | Examples | Default trust |
|------|---------------|----------|---------------|
| 1 | Direct observation | Command output, test result, fetched document, screenshot, query result | Highest |
| 2 | Primary source quote | Official docs, source code, spec text | High |
| 3 | Reputable secondary source | Strong blog post, paper summary, maintainer guide | Medium |
| 4 | Pattern-based inference | Existing repo convention, common architecture pattern | Medium-low |
| 5 | Intuition | "This is probably true" | Lowest |

Default rule: do not present Tier 4 or Tier 5 as if they were Tier 1.

## Claim-Evidence-Confidence Format

For important claims, use a compact inspection-friendly structure:

| Field | Question |
|-------|----------|
| Claim | What am I asserting? |
| Evidence | What supports it? |
| Confidence | How sure am I and why not more? |

### Example

Claim: `This prompt fails because the model is never asked to verify tool output.`

Evidence: `The workflow jumps from action to conclusion and includes no observation or check step.`

Confidence: `High. The failure pattern matches repeated tool-optimism errors and is visible in the prompt sequence.`

## Verification Ladder

Use the cheapest sufficient check first.

| Step | Use when | Example |
|------|----------|---------|
| Internal consistency check | Draft may contradict itself | Compare key claims |
| Cheap calculation or schema check | Error is deterministic | Count, parse, type-check |
| Direct tool verification | Environment can confirm | Run test, fetch file, inspect output |
| Source lookup | Facts depend on docs or web | Check official docs |
| Independent review | Stakes are high or ambiguity persists | Multi-agent or human review |

### Ladder Rule

Climb only as far as needed. Do not spend a web search when a local test can settle it.

## Uncertainty Rules

Good adversarial coaching leaves room for explicit unknowns.

| Situation | Required move |
|-----------|---------------|
| Evidence missing | Say what is unknown |
| Evidence contradictory | Present conflict and recommended next check |
| Verification impossible right now | State limitation and best follow-up |
| Answer is pattern-based only | Mark it as inference, not proof |

### Useful Phrases

- "I do not have direct evidence for this part."
- "This appears likely from the repo pattern, but I have not verified it."
- "The next reliable check would be..."
- "This claim should be softened unless we can confirm X."

## Tool-Backed Verification

When tools are available, separate action from observation.

Bad:

1. Run command
2. Assume it worked
3. Claim success

Good:

1. Run command
2. Record observable result
3. Interpret result carefully
4. Claim only what the result supports

### Observation Log Pattern

| Action | Observation | Interpretation |
|--------|-------------|----------------|
| `npm test` | `23 passed, 1 failed` | Not fixed yet |
| `grep` search | Symbol found in 4 files | Refactor needs 4 touchpoints |
| API request | 403 response | Auth or permissions issue, not network success |

## Retrieval and Citation Rules

For retrieval-heavy tasks, support every major fact with one of:

- a quoted source snippet
- a file path and line reference
- an official documentation URL
- a tested result from the environment

If none exist, do not behave as though they do.

## What Counts as a Passed Check

| Question | Pass condition |
|----------|----------------|
| Is the claim true enough to state strongly? | Evidence is Tier 1-2, or uncertainty is explicit |
| Is the result reproducible? | Another reviewer can follow the same proof path |
| Is the reasoning inspectable? | Major steps are visible and tied to evidence |
| Is the answer honest? | No invented facts, no hidden leap presented as proof |

## Common Verification Mistakes

| Mistake | Why it happens | Fix |
|---------|----------------|-----|
| Confusing pattern with proof | Familiarity bias | Label it inference |
| Quoting stale docs from memory | Convenience | Re-open the source |
| Claiming success from partial output | Wishful interpretation | State exact observed scope |
| Hiding uncertainty | Tone pressure | Add calibrated caveat |
| Over-verifying everything | Fear of being wrong | Focus on high-leverage claims |

## Verification by Task Type

### Code Changes

Strong evidence includes:

- diagnostics are clean on changed files
- tests/build pass
- diff matches requested scope

### Research Answers

Strong evidence includes:

- official docs
- reputable papers or source repos
- agreement across multiple credible sources

### Operational Guidance

Strong evidence includes:

- commands that were actually run
- configuration files inspected directly
- failure or success outputs captured precisely

## Evidence Compression

Do not dump raw logs when one sentence plus one key line proves the point.

Compress evidence like this:

| Raw form | Better form |
|----------|-------------|
| Full 200-line test run | `Tests passed: 24/24` plus one meaningful note |
| Entire doc page | Link + one relevant quote |
| Huge diff description | File path + one-line summary |

The goal is inspectability with minimal noise.

## Escalation Rules

Escalate to deeper verification when:

- the answer affects production, billing, security, or data safety
- the same claim has already failed once
- the evidence tier is below what the risk level demands

Do not escalate just because the tone feels uncertain.

## Lightweight Verification Template

Use this in practice:

1. **Claim** — the statement under review
2. **Best evidence available** — tier and source
3. **Confidence** — high, medium, low, plus reason
4. **Next check** — only if confidence is below required level

Example:

1. Claim: `The issue comes from missing branch protection.`
2. Evidence: `Low-tier inference from workflow config only.`
3. Confidence: `Low, because no repo settings were inspected.`
4. Next check: `Verify branch rules with gh or repository settings.`

## Relationship to Adversarial Coaching

Adversarial review finds the weak points.
Verification decides which weak points are real.

Use `adversarial-review-playbook.md` to discover the risk.
Use this file to decide whether the risk has been resolved enough to ship.
