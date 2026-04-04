# Prompt Versioning and Feedback

Sources: Langfuse prompt management docs, LangSmith prompt/version docs, Braintrust practices, prompt ops community patterns

Covers: prompt registries, version promotion, human feedback capture, annotation workflows, A/B testing prompts, and operational prompt management.

## Prompts Are Production Artifacts

Treat prompts like versioned, reviewable assets rather than inline strings hidden in code.

| Good practice | Why |
|--------------|-----|
| version every meaningful prompt change | trace regressions |
| separate draft/staging/prod labels | safer promotion |
| attach prompt version to traces | observability and eval linkage |

## Feedback Capture Types

| Type | Example |
|-----|---------|
| explicit thumbs up/down | simple product feedback |
| annotation/rubric review | internal QA labeling |
| implicit outcome signals | user retry, abandonment, correction |

## Prompt Review Questions

1. What changed and why?
2. What eval or production signal justified the change?
3. Which prompt version is currently live?

## A/B Prompt Testing

| Need | Pattern |
|-----|---------|
| low-risk comparison | traffic split between prompt versions |
| subjective output quality | human or rubric review |
| production confidence | compare quality + cost + latency |

## Common Prompt Ops Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| editing prompts without version tags | no rollback clarity | version and label prompts |
| collecting feedback with no route to action | observability theater | tie to evaluation workflow |
| prompt drift hidden in app code | hard review | central registry or structured prompt management |

## Prompt Registry Questions

1. Where is the source of truth for each production prompt?
2. Can you tell which prompt version was active for a past trace?
3. Is there a promotion path from draft to production?

## Feedback Taxonomy

| Feedback source | Example |
|----------------|---------|
| explicit user rating | thumbs up/down |
| operator annotation | support or QA labels |
| downstream correction signal | user edits or retries |
| task completion metric | did the workflow succeed? |

## Version Promotion Workflow

1. create draft prompt version
2. test against eval set
3. run limited experiment or internal review
4. promote with label/environment change
5. monitor production trace quality and feedback

## Human Annotation Workflows

| Pattern | Benefit |
|--------|---------|
| rubric-based annotation | more consistent labels |
| sampled bad-case review | focused triage |
| route/feature-specific labeling | clearer ownership |

## A/B Testing Questions

1. Is traffic split deterministic enough to compare meaningfully?
2. Are both quality and cost/latency compared?
3. Is experiment scope narrow enough to interpret?

## Prompt Lifecycle Smells

| Smell | Why it matters |
|------|----------------|
| production prompt edited ad hoc | unsafe change management |
| no archived history | weak incident analysis |
| feedback stored but not tied to version | low actionability |

## Final Prompt Ops Checklist

- [ ] prompt source of truth is explicit
- [ ] version promotion path is documented
- [ ] feedback loops connect to evaluation and release decisions
- [ ] experiments compare quality, cost, and latency together

## Prompt Registry Metadata

| Field | Why |
|------|-----|
| prompt name | stable identity |
| version | rollback and comparison |
| labels/environment | promotion status |
| owner | operational accountability |
| notes/changelog | decision context |

## Feedback Triage Questions

1. Is this bad output traceable to one prompt version?
2. Is the issue prompt quality, retrieval quality, model behavior, or user expectation mismatch?
3. Should the response become an eval case, prompt edit, or product/UI change?

## Prompt Lifecycle Review

| Stage | Typical action |
|------|----------------|
| draft | design and offline testing |
| staging | limited eval/traffic review |
| production | monitored live use |
| deprecated | retained for trace history and rollback analysis |

## Annotation Workflow Notes

| Concern | Recommendation |
|--------|----------------|
| reviewer consistency | use a rubric |
| high volume | sample intelligently |
| low-quality clusters | label by failure mode, not only score |

## Prompt Ops Smells

| Smell | Why it matters |
|------|----------------|
| multiple codepaths defining “same” prompt | weak control |
| no owner for a prompt family | drift and stale logic |
| feedback collected without version linkage | low actionability |

## Final Prompt Governance Questions

1. Who can promote a prompt to production?
2. What evidence is required before promotion?
3. How fast can you roll back a bad prompt change?

## Prompt Changelog Discipline

| Field | Example |
|------|---------|
| why changed | hallucination reduction, format fix |
| expected effect | better grounding, lower verbosity |
| linked eval | dataset or experiment result |

Prompt changelogs make future debugging far less speculative.

## Promotion Criteria Ideas

| Criterion | Example |
|----------|---------|
| no critical regression on eval set | baseline guard |
| acceptable cost delta | budget control |
| latency within route SLO | UX guard |
| reviewer sign-off | human confidence |

## Feedback Taxonomy Questions

1. Is this a prompt problem, retrieval problem, model problem, or UX expectation problem?
2. Should this become a new eval case?
3. Does the feedback cluster around one prompt version or feature?

## Human Review Workflow

| Step | Why |
|-----|-----|
| sample failures or low scores | efficient triage |
| label by failure mode | actionable patterns |
| feed into prompt/eval backlog | closes the loop |

## Common Prompt Governance Smells

| Smell | Why it matters |
|------|----------------|
| no changelog or rationale | weak release memory |
| production prompt promotion by ad hoc manual edit | risky rollout |
| feedback not tied to prompt version | poor attribution |

## Final Prompt Ops Notes

Prompt governance is effective when a bad output can be traced to a version, evaluated against a baseline, and corrected without guesswork.

## Ownership Model

| Artifact | Typical owner |
|---------|---------------|
| prompt family | feature team or AI owner |
| production label promotion | release owner |
| feedback triage | product/QA/AI ops shared workflow |

## Rollback Questions

1. Can you revert to the prior prompt version instantly?
2. Is the previous prompt still evaluable and trace-linked?
3. Will rollback also require retrieval or UI/config changes?

## Prompt Review Smells

| Smell | Why it matters |
|------|----------------|
| prompt changes merged with no eval evidence | unsafe release |
| one prompt serving many unrelated tasks | poor ownership |
| no failure-mode taxonomy in feedback | weak iteration loop |

## Version Review Checklist

1. Is the prompt diff understandable to a reviewer?
2. Is there eval evidence for promotion?
3. Is rollback to previous version immediate and unambiguous?

## Feedback Loop Smells

| Smell | Why it matters |
|------|----------------|
| thumbs-only feedback with no triage process | low actionability |
| annotation but no version linkage | weak attribution |
| no owner for low-score clusters | slow improvement |

## Prompt Ops Review Questions

1. Can you explain why the current production prompt is live?
2. What evidence supported its promotion?
3. If feedback turns sharply negative, how quickly can you revert?

Prompt governance is a release discipline, not just a docs habit.

## Governance Review Note

If no one owns prompt promotion, rollback, and feedback triage, prompt quality will drift no matter which platform is installed.

Version history only matters when it changes release behavior.

That is the difference between prompt ops and prompt clutter.

It is also the difference between safe rollouts and guesswork.

## Release Readiness Checklist

- [ ] prompts are versioned and linked to traces
- [ ] promotion path from draft/staging to prod is explicit
- [ ] feedback capture has a review loop, not just storage
- [ ] A/B comparisons include quality, latency, and cost context
