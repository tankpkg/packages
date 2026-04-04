# Evaluation and Regressions

Sources: RAGAS documentation, DeepEval documentation, Langfuse evaluation docs, LangSmith experiments/evals docs, community LLM evaluation practices from 2024-2026

Covers: evaluation datasets, prompt and model regression checks, rubric/model-graded scoring, retrieval evaluation, RAGAS-style thinking, DeepEval-style assertions, and release gating for LLM systems.

## Evaluation Is a Product Safety Net

LLM quality drifts from prompt edits, retrieval changes, model changes, and data shifts. Evaluation catches this before users do.

| Change type | Risk |
|------------|------|
| prompt wording | output drift |
| model swap | quality/cost/latency change |
| retrieval change | grounding and relevance shift |
| post-processing tweak | formatting or safety regressions |

## Dataset Design

| Dataset type | Use |
|-------------|-----|
| golden production examples | regression guardrails |
| hand-authored edge cases | failure-focused coverage |
| user feedback derived set | real-world drift detection |

### Dataset questions

1. Does this set reflect real user tasks?
2. Are edge/failure cases represented explicitly?
3. Is the dataset small enough for fast iteration and large enough for signal?

## Metric Families

| Metric | Best for |
|-------|----------|
| exact/assertive checks | deterministic tasks |
| rubric/model-graded scores | subjective generation quality |
| retrieval precision/recall proxies | RAG retrieval health |
| latency/cost attached to quality | release trade-off review |

## RAG Evaluation Notes

RAG systems need both retrieval and answer evaluation.

| Layer | Example concern |
|------|------------------|
| retrieval | are the right chunks found? |
| generation | does the answer use evidence well? |
| end-to-end | is the user answer correct and grounded? |

## Regression Gates

| Gate | Example |
|-----|---------|
| score threshold | average score must not drop below X |
| no critical-case failure | key test set must all pass |
| cost/latency bound | quality gain cannot blow budget/SLO |

## Common Evaluation Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| evaluating only happy paths | blind to user pain | add edge cases |
| no prompt/model version linkage | impossible attribution | capture versions |
| pure subjective grading with no consistency | noisy decisions | define rubric and thresholds |

## Evaluation Layer Model

| Layer | Question |
|------|----------|
| prompt-only | does this wording improve output quality? |
| model-only | does this provider/model route change behavior materially? |
| retrieval | are relevant contexts found? |
| end-to-end | does the user receive a better answer? |

The right evaluation layer depends on what changed.

## Dataset Composition Rules

| Rule | Why |
|-----|-----|
| include representative production cases | avoid toy evals |
| include edge/failure cases | catch regressions that hurt users |
| keep a stable core regression set | comparable history |
| allow an exploratory set for new behavior | innovation without losing guardrails |

## Human vs Model-Graded Evaluation

| Approach | Strength | Weakness |
|---------|----------|----------|
| human review | nuanced judgment | slow and expensive |
| model-graded rubric | scalable | evaluator drift/noise |
| exact assertions | deterministic | narrow applicability |

Most mature systems need a mix.

## Prompt Regression Workflow

1. create or update prompt draft version
2. run eval set against old and new prompt
3. compare quality, latency, and cost
4. inspect worst regressions manually
5. promote only if trade-off is acceptable

This workflow should be routine, not heroic.

## RAG Evaluation Questions

1. Was the right evidence retrieved?
2. Did the answer actually use that evidence?
3. Was the answer correct even if retrieval looked good?

RAG failures often hide in the gap between retrieval success and answer quality.

## Regression Gate Design

| Gate type | Example |
|----------|---------|
| hard failure gate | no critical examples may regress |
| threshold gate | average quality must remain above X |
| trade-off gate | quality gain must not exceed latency/cost budget |

## Common Eval Smells

| Smell | Why it matters |
|------|----------------|
| one giant average score only | hides catastrophic edge failures |
| no manual review of worst cases | evaluator blind spots persist |
| no saved baseline | impossible trend analysis |

## Evaluation Review Checklist

1. Do metrics reflect what users actually care about?
2. Are failure cases prominent, not averaged away?
3. Are prompt/model/retrieval versions recorded alongside results?
4. Is there a clear decision rule for promotion or rollback?

## Final Evaluation Notes

Evaluation is not just measurement. It is the release governance mechanism for non-deterministic systems.

## Baseline Dataset Strategy

| Dataset | Role |
|--------|------|
| stable regression set | release gate and trend tracking |
| exploratory set | prompt/model experimentation |
| failure-focused set | protect against known incidents |

## Human Review Integration

| Pattern | Benefit |
|--------|---------|
| review worst regressions only | efficient use of human time |
| rubric calibration sessions | improves score consistency |
| periodic spot-check of “passing” examples | catches evaluator blind spots |

## Threshold Design Questions

1. What score drop is unacceptable?
2. Which examples are so critical they must never regress?
3. When does a quality gain justify a latency or cost increase?

## Example RAG Evaluation Split

| Component | Example metric |
|----------|----------------|
| retrieval relevance | chunk recall / relevance score |
| answer grounding | citation faithfulness / evidence usage |
| final utility | task success or rubric score |

## Evaluation Anti-Patterns

| Anti-pattern | Problem |
|-------------|---------|
| one monolithic metric for every task | low diagnostic value |
| no saved examples for regressions | poor repeatability |
| evaluating prompt quality without tracking prompt version | weak attribution |

## Operational Evaluation Checklist

1. store dataset version
2. store prompt/model version
3. store evaluator version or rubric definition
4. compare against explicit baseline

Without evaluator versioning, score drift can masquerade as product improvement.

## Dataset Maintenance Questions

| Question | Why |
|---------|-----|
| which examples are now stale? | avoid overfitting to old behavior |
| which new incidents should become eval cases? | production learning loop |
| is the dataset still balanced across task types? | useful signal |

## Eval Review Heuristics

| Heuristic | Why |
|----------|-----|
| inspect worst failures, not just average scores | catch catastrophic regressions |
| compare cost and latency with quality | release realism |
| keep critical examples visible in dashboards | governance clarity |

## Regression Triage Questions

1. Did quality drop because of prompt, retrieval, model, or formatting changes?
2. Is the regression broad or isolated to a scenario cluster?
3. Should rollback happen before deeper experimentation?

## Evaluation Ownership

| Artifact | Owner |
|---------|-------|
| eval dataset | feature/AI owner |
| scoring rubric | quality owner or team consensus |
| release gate threshold | product + engineering decision |

## Eval Smells

| Smell | Why it matters |
|------|----------------|
| thresholds chosen with no user or product meaning | weak governance |
| no stable critical-case dataset | major regressions sneak through |
| eval scores detached from release process | observability theater |

## Release Gate Questions

1. What score drop forces rollback?
2. Which failures are unacceptable regardless of average score?
3. Who approves exceptions when quality and latency/cost disagree?

Release gates matter only if they are used consistently.

## Promotion Review Notes

Good eval systems make promotion conversations concrete: which cases improved, which regressed, and whether the trade-off is acceptable.

They also make rollback decisions faster because the baseline is explicit.

Baseline clarity is one of the highest-value properties of a good eval system.

It turns debates into decisions.

## Release Readiness Checklist

- [ ] dataset covers real tasks and known failure cases
- [ ] regression gates are explicit for quality, cost, and latency
- [ ] RAG systems evaluate retrieval and generation separately where useful
- [ ] prompt/model changes are compared against previous baselines
