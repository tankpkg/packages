# Evals and Metrics

Sources: Anthropic define-success guidance, Anthropic prompt engineering best practices, DSPy optimization patterns, DeepEval metrics, RAGAS metrics, reliability and regression-testing practice

Covers: eval-first workflow, regression gates, task-specific metrics, and how to measure whether adversarial coaching is actually improving the agent.

## Purpose

Use this file when you want the coaching style to become a repeatable quality system instead of a vibe.

If you cannot measure whether the agent got better, you are only changing its tone.

## Eval-First Rule

Before rewriting prompts or adding harsher critique, define success.

| Step | Question |
|------|----------|
| Define | What does good output look like? |
| Measure | How will we detect better vs worse? |
| Analyze | Which failure mode is most common? |
| Improve | What one change targets that failure mode? |
| Control | How will we prevent regression? |

This is the smallest useful version of a reliability loop.

## Success Criteria

Good criteria are concrete enough to score.

| Weak criterion | Better criterion |
|----------------|------------------|
| "Be more accurate" | "Core claim is supported by an official source or direct observation" |
| "Be less hallucinated" | "Unsupported factual claims drop below 1 per response" |
| "Use tools better" | "Every tool action is followed by an explicit observation" |
| "Push back more" | "The agent raises at least one concrete objection when assumptions are weak" |

## Metric Layers

Measure the layer you are trying to improve.

| Layer | Example metric |
|-------|----------------|
| Planning | Plan completeness, subtask quality, dependency accuracy |
| Execution | Tool-call accuracy, observation discipline |
| Output | Correctness, completeness, evidence quality |
| Behavior | Confidence calibration, useful pushback, contradiction handling |

Do not use output metrics alone when the failure is clearly process-driven.

## Minimal Eval Harness

Start with a small set:

1. 5-10 representative prompts
2. 2-3 adversarial prompts that previously caused failures
3. One rubric per prompt or prompt class
4. A baseline score before changes
5. One change at a time

This is usually enough to tell if the skill is helping.

## Rubric Design

Each rubric dimension should correspond to a real failure mode.

| Dimension | Pass question |
|-----------|---------------|
| Correctness | Are key claims supported or clearly bounded? |
| Scope fit | Did the answer solve the actual request? |
| Evidence quality | Are high-risk claims backed by strong evidence tiers? |
| Contradiction handling | Were plausible counterexamples addressed? |
| Calibration | Is confidence aligned with the evidence? |

Use 0-2 or pass/fail scales unless finer granularity is genuinely useful.

## Adversarial Prompt Set

Build prompts that trigger common failure modes:

| Failure mode | Eval example |
|--------------|--------------|
| Sycophancy | User confidently asks for a bad or incomplete approach |
| Bluffing | User requests a conclusion with missing data |
| Scope drift | User asks a narrow question inside a broad domain |
| Tool optimism | Task requires confirmation after a command |
| Hallucination | Research question where only some facts are verifiable |

The skill is working if these prompts improve, not just easy ones.

## LLM Judge vs Deterministic Checks

| Check type | Best for | Limitation |
|------------|----------|------------|
| Deterministic | Commands, tests, exact formats, citations present | Cannot judge nuanced helpfulness |
| LLM judge | Reasoning quality, usefulness, contradiction handling | Needs calibration |
| Human review | High-stakes final quality | Slow and expensive |

Prefer deterministic checks where possible. Use LLM judging for the parts humans care about but scripts cannot score directly.

## DSPy-Style Optimization Mindset

DSPy is useful when you have:

- a stable task shape
- a metric or scorer
- enough examples to optimize against

The big lesson to borrow even without DSPy is this: optimize programs and prompts against an eval, not against intuition.

## DeepEval and RAGAS Mindset

You do not need the libraries to use the underlying principles.

Borrow these ideas:

- score retrieval separately from answer quality
- score process quality separately from final correctness
- inspect traces, not just end outputs

This matters because adversarial coaching may improve one layer while hurting another.

## Regression Gates

Any change to prompting or coaching should be blocked if it causes regressions on core prompts.

Basic gate:

- no drop on baseline-correct prompts
- measurable gain on at least one known failure cluster
- no new unsupported certainty introduced

## Scorecard Template

Use a compact sheet:

| Prompt | Baseline | New score | Delta | Failure cluster |
|--------|----------|-----------|-------|-----------------|
| Prompt A | 5/10 | 8/10 | +3 | Sycophancy |
| Prompt B | Pass | Pass | 0 | Stable |
| Prompt C | 2/10 | 2/10 | 0 | Tool optimism |

This helps target the next iteration instead of rewriting everything.

## Stop Rules for Optimization

Stop tuning when:

- the main failure cluster is materially improved
- remaining issues require new tools or external data, not prompt changes
- additional pressure only increases verbosity or hedging

Keep going when:

- the gain is inconsistent across similar prompts
- a new failure cluster appears after the change
- the skill improved tone but not correctness

## Example Quality Gates

### Research Tasks

- At least one primary source for major claims
- Explicit uncertainty where verification is incomplete
- No unsupported absolute statements

### Coding Tasks

- Diagnostics clean on changed files
- Required tests/build run or limitation stated
- Claimed fix matches actual evidence

### Agent Review Tasks

- At least one concrete objection raised when assumptions are weak
- Top claims include evidence or explicit limits
- Final answer reflects the critique, not just the same draft repeated

## Continuous Control

Once the skill is useful, keep a small regression set.

Good candidates:

- prompts that previously caused the worst bluffing
- tasks where the model skipped verification
- prompts where users gave flawed assumptions confidently

Re-run them whenever the coaching instructions change.

## Hand-off Guidance

Use this file with:

- `adversarial-review-playbook.md` to define failure clusters
- `verification-and-evidence.md` to choose proof standards
- `multi-agent-review.md` when one pass cannot settle the result

Measurement is what turns aggressive prompting into disciplined reliability work.
