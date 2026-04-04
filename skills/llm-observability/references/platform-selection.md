# Platform Selection

Sources: Langfuse docs, LangSmith docs, Arize Phoenix docs, Helicone docs, Braintrust docs, community comparison material from 2024-2026

Covers: platform trade-offs across Langfuse, LangSmith, Phoenix, Helicone, Braintrust, and practical selection criteria for teams building LLM systems.

## Pick the Platform That Matches the Real Problem

| Need | Best-fit direction |
|-----|--------------------|
| prompt/version management + traces | Langfuse |
| LangChain-heavy experiment workflow | LangSmith |
| open-source tracing/eval stack | Phoenix |
| gateway/lightweight usage monitoring | Helicone |
| evaluation-heavy workflow | Braintrust or equivalent eval-first stack |

## Selection Questions

1. Is the main pain prompt ops, tracing, evaluation, or gateway monitoring?
2. Does the team need hosted convenience or open-source control?
3. How tightly is the stack coupled to LangChain or another framework?

## Common Selection Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| picking platform by hype alone | weak fit to workflow | choose by primary pain |
| overbuying giant platform before signals exist | wasted complexity | start with core needs |
| no clear ownership of eval/tracing data | tooling confusion | define workflow and owners |

## Selection Dimensions

| Dimension | Questions |
|----------|-----------|
| tracing depth | do we need request/tool/retrieval spans? |
| prompt ops | is registry/version promotion central? |
| evaluation | do we need datasets, scoring, experiments? |
| deployment style | hosted convenience or self-hosted control? |

## Platform Review Questions

1. Is this platform strongest at the problem we actually have today?
2. How tied are we to one framework or SDK?
3. Can teams outside ML/AI engineering use it operationally?

## Comparative Heuristics

| Platform tendency | Best fit |
|------------------|----------|
| Langfuse | prompt ops + traces + OSS-friendly workflow |
| LangSmith | LangChain-heavy experimentation and debugging |
| Phoenix | open-source tracing/eval and observability depth |
| Helicone | gateway/usage/cost-first monitoring |
| Braintrust | eval-centric organizations |

## Migration and Lock-In Notes

| Concern | Why |
|--------|-----|
| proprietary prompt registry model | migration friction |
| framework-specific coupling | stack constraints |
| trace schema portability | future platform flexibility |

## Selection Smells

| Smell | Why it matters |
|------|----------------|
| buying platform before defining success criteria | weak adoption |
| too many tools overlapping | fragmented observability |
| no owner for eval/tracing data model | low trust |

## Final Platform Checklist

- [ ] platform choice aligns with primary observability problem
- [ ] hosted vs self-hosted trade-offs are understood
- [ ] framework coupling and migration risks are visible
- [ ] team ownership and workflows are defined before rollout

## Hosted vs Open-Source Questions

| Question | Why |
|---------|-----|
| do we need managed convenience now? | speed vs control |
| do we need data residency or deep control? | compliance/ops |
| can the team operate the open-source stack well? | realistic ownership |

## Workflow Fit Table

| Team situation | Likely preference |
|---------------|-------------------|
| prompt-heavy product iteration | Langfuse or LangSmith |
| framework-heavy LangChain stack | LangSmith |
| OSS and custom observability pipeline | Phoenix |
| gateway-first monitoring | Helicone |
| eval-first org | Braintrust-style workflow |

## Migration Questions

1. How portable are traces and prompt versions?
2. How expensive is migration if the framework stack changes?
3. Are dashboards and eval workflows encoded in platform-specific ways?

## Platform Ownership Questions

| Concern | Why |
|--------|-----|
| who owns prompt registry? | operational clarity |
| who owns evaluation datasets? | quality governance |
| who owns tracing schema/taxonomy? | observability consistency |

## Selection Smells

| Smell | Why it matters |
|------|----------------|
| buying several overlapping platforms | fragmented signal |
| no explicit success criteria for adoption | tool churn |
| platform chosen only because one engineer likes it | weak organizational fit |

## Langfuse Fit Notes

| Strength | Why teams choose it |
|---------|---------------------|
| prompt versioning + traces in one workflow | good prompt ops baseline |
| open-source friendliness | control and extensibility |
| useful for mixed custom stacks | not only one framework |

## LangSmith Fit Notes

| Strength | Why teams choose it |
|---------|---------------------|
| strong LangChain ecosystem fit | easier integration when already committed |
| experiments and traces together | useful for chain-heavy apps |

## Phoenix Fit Notes

| Strength | Why teams choose it |
|---------|---------------------|
| open-source tracing/eval orientation | good for teams wanting control |
| good observability-first posture | useful when debugging pipelines deeply |

## Helicone Fit Notes

| Strength | Why teams choose it |
|---------|---------------------|
| gateway/monitoring style simplicity | cost and request monitoring quickly |
| lighter starting point | lower adoption overhead for some teams |

## Braintrust / Eval-First Fit Notes

| Strength | Why teams choose it |
|---------|---------------------|
| evaluation-centered workflow | useful for teams treating eval as product governance |
| dataset/experiment emphasis | good for structured quality loops |

## Decision Questions by Maturity Stage

| Stage | Main question |
|------|---------------|
| early | do we mostly need traces and prompt history? |
| growth | do we need robust evaluation and regression gates? |
| mature | do we need cross-team ownership, dashboards, and cost governance? |

## Adoption Checklist

1. define success criteria before rollout
2. choose one primary platform, not five overlapping ones
3. decide who owns prompts, traces, and eval datasets
4. pilot on one high-value workflow first

## Final Selection Notes

The best platform is the one that makes your real failure modes and release decisions visible — not the one with the flashiest demo.

## Platform Fit Questions by Team Type

| Team type | Main question |
|----------|---------------|
| product-heavy startup | do we need fast prompt/version iteration more than deep OSS control? |
| infra/ML platform team | do we need extensible traces and custom eval pipelines? |
| framework-coupled app team | is stack-native tooling more valuable than portability? |

## Rollout Checklist

1. define the first workflow to instrument
2. define owner for prompt/eval/trace schema
3. define success metrics for adoption
4. avoid overlapping platform sprawl unless justified

## Final Platform Review Notes

Tool choice is only correct if it improves release confidence, debugging speed, and operational clarity in your actual stack.

## Platform Evaluation Checklist

1. Does it solve the top current pain?
2. Can the team actually operate it?
3. Are prompt, trace, and eval workflows cohesive enough to avoid tool sprawl?

## Selection Anti-Patterns

| Anti-pattern | Why it matters |
|-------------|----------------|
| picking a platform before defining workflow ownership | low adoption |
| duplicating the same telemetry in multiple tools with no strategy | confusion |
| underestimating migration and coupling cost | future lock-in pain |

## Fit Review Questions

1. Does this platform improve one painful workflow in the next month?
2. Can non-ML engineers actually use the dashboards and traces?
3. Are we buying a platform or a cohesive operating model?

Good platform fit is mostly about workflow fit.

It is also about whether the team will trust and actually use the system in release decisions.

## Adoption Questions

1. What is the first workflow to instrument?
2. What concrete decision should become easier after adoption?
3. What would failure to adopt look like in three months?

That framing keeps platform choice tied to outcomes instead of tool aesthetics.

## Final Adoption Checklist

- [ ] one initial workflow is chosen
- [ ] ownership is explicit
- [ ] platform success criteria are documented

Platform selection is successful only when it improves real release and debugging decisions.

Otherwise it is just another dashboard purchase.

The right tool should change team behavior, not just screenshots.

Choose the platform you can actually operate.

That usually beats the most feature-rich brochure.

Fit beats hype.

Usefulness beats novelty.

## Release Readiness Checklist

- [ ] platform choice matches the team’s actual observability gap
- [ ] prompt, trace, and eval data have clear ownership
- [ ] platform/framework coupling is understood before adoption
- [ ] migration/portability concerns are considered where relevant
