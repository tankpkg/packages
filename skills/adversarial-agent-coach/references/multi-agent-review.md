# Multi-Agent Review

Sources: MAR, debate-style review patterns, Anthropic agentic workflow guidance, reliability engineering and consensus patterns

Covers: role splitting, structured disagreement, verifier sign-off, and when multiple reviewers outperform one harsh prompt.

## Purpose

Use this file when the task is high stakes, the draft has repeated the same failure, or you want to separate creation from criticism so the same mind does not defend its own mistake.

Multi-agent review is not about adding noise. It is about adding independent pressure.

## Default Roles

| Role | Mission | What it must not do |
|------|---------|---------------------|
| Builder | Produce the best draft within scope | Defend unsupported claims |
| Skeptic | Find contradictions, edge cases, and weak support | Rewrite the whole answer |
| Verifier | Decide whether evidence and scope are good enough | Invent proof or average opinions |

Optional roles:

| Role | Use when |
|------|----------|
| Retrieval verifier | Facts depend on external sources |
| Test executor | Code or commands can prove correctness |
| Editor | Final polish after correctness is settled |

## Why Role Split Helps

Single-agent self-critique often reuses the same assumptions that created the error.

Role split helps by:

- forcing distinct goals
- making disagreement explicit
- preventing the first draft from anchoring the whole process

## Review Order

Use a stable order:

1. Builder drafts.
2. Skeptic lists top risks.
3. Builder patches only the flagged risks.
4. Verifier signs off or blocks release.

Do not let the skeptic and builder argue indefinitely. The verifier decides whether evidence is sufficient.

## Structured Disagreement Format

Each skeptic comment should include:

| Field | Meaning |
|-------|---------|
| Claim at risk | The exact sentence, assumption, or step |
| Objection | Why it may fail |
| Severity | High, medium, low |
| Required fix | Proof, caveat, branch, or removal |

Example:

- Claim at risk: `This migration is backwards compatible.`
- Objection: `No compatibility evidence was shown for existing clients.`
- Severity: `High`
- Required fix: `Show versioning strategy or soften the claim.`

## Verifier Sign-Off Rules

The verifier should approve only when:

- high-severity objections are resolved
- key claims have sufficient evidence
- the answer still matches the user's actual task

The verifier should block when:

- disagreement remains unresolved on a core claim
- proof is missing for a high-risk recommendation
- the process drifted into style edits before correctness was settled

## Consensus Is Not Averaging

Do not merge outputs by smoothing them together.

Better rule:

- keep the strongest supported claim
- discard unsupported flourish
- preserve explicit uncertainty where proof is incomplete

Consensus means the surviving answer passed pressure, not that every role liked it equally.

## When to Add More Agents

| Signal | Add role? |
|--------|-----------|
| Facts are disputed | Yes, retrieval verifier |
| Code behavior is disputed | Yes, test executor |
| Builder and skeptic keep looping | Yes, separate verifier |
| Task is simple and local | No, stay single-agent |

More agents help only when they add a genuinely different check.

## Lightweight Debate Pattern

For high-risk answers, run a short debate:

1. Builder makes the strongest case for the answer.
2. Skeptic makes the strongest case against it.
3. Builder patches only what the skeptic exposed.
4. Verifier decides whether the patched answer is ready.

Keep debate bounded to one round unless new evidence appears.

## Common Multi-Agent Failures

| Failure | Why it happens | Fix |
|---------|----------------|-----|
| Everyone agrees too fast | Roles were not differentiated | Sharpen role prompts |
| Skeptic rewrites the answer | Scope creep | Restrict to objections only |
| Builder ignores criticism | No verifier gate | Require sign-off |
| Verifier becomes another editor | Blurry mission | Limit to pass, block, or request proof |
| Too many opinions | Role explosion | Add only one new independent check at a time |

## Review Rubric

Use this small rubric at the end:

| Dimension | Question |
|-----------|----------|
| Correctness | Is the core claim still standing? |
| Evidence | Is support strong enough for the stated confidence? |
| Scope | Is the answer solving the actual request? |
| Reproducibility | Can another reviewer inspect the same proof path? |

If any answer is no, the verifier should block or request one explicit next fix.

## Hand-off Guidance

After multi-agent review:

- if correctness is settled, let an editor polish
- if evidence is weak, go to `verification-and-evidence.md`
- if the same type of failure persists, go to `react-reflexion-loops.md`

Multi-agent review is a tool for reducing self-confirmation bias. Use it when that bias is likely to matter.
