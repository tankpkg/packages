# Cost, Latency, and Ops

Sources: Langfuse metrics docs, Helicone usage tracking docs, LangSmith monitoring docs, provider billing/latency guidance, production LLM ops practices

Covers: token and spend tracking, latency budgets, model routing decisions, alerts, dashboards, and production operational review for LLM systems.

## Quality Is Not the Only SLO

An LLM system that is high quality but too slow or too expensive can still fail in production.

| Dimension | Why |
|----------|-----|
| quality | user trust and usefulness |
| latency | perceived responsiveness |
| cost | product viability |

## Cost Tracking Basics

| Field | Why capture it |
|------|----------------|
| input tokens | cost and prompt growth |
| output tokens | verbosity and spend |
| model/provider | route-level economics |
| feature/endpoint | hotspot analysis |

## Latency Review

| Layer | Example |
|------|---------|
| retrieval latency | vector/db lookup bottleneck |
| model latency | provider/model choice impact |
| tool latency | external API or function cost |
| total request latency | user-facing experience |

## Common Ops Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| no per-feature cost attribution | budget blind spots | tag traces by feature/use case |
| improving quality while ignoring latency | UX degradation | review all three dimensions together |
| no alerts on spend spikes | surprise bills | add budget thresholds |

## Latency Budget Questions

1. What total response time is acceptable to users?
2. Which stage dominates: retrieval, model, tool, or formatting?
3. Are slow paths rare edge cases or the mainline experience?

## Cost Attribution Patterns

| Attribution key | Why |
|----------------|-----|
| feature/route | identify expensive product areas |
| customer or tenant | enterprise billing/abuse insight |
| prompt/model version | regression attribution |

## Dashboard Design

| Panel | Why |
|------|-----|
| quality over time | detect drift |
| cost by feature/model | budget control |
| latency percentiles | UX and bottleneck visibility |
| failure/error categories | reliability review |

## Alerting Heuristics

| Alert | Trigger example |
|------|------------------|
| cost spike | daily spend above threshold |
| latency spike | p95 above budget |
| error spike | provider/tool failure surge |
| quality regression | eval score drop after rollout |

## Routing and Optimization Questions

1. Could a cheaper model serve this route?
2. Could retrieval or caching reduce total model usage?
3. Is prompt verbosity inflating token cost?

## Ops Smells

| Smell | Why it matters |
|------|----------------|
| one total spend number only | no actionability |
| no route-level latency visibility | hidden slow hotspots |
| quality dashboards detached from cost dashboards | bad release trade-offs |

## Final Ops Checklist

- [ ] costs are attributable by meaningful product dimension
- [ ] latency budgets exist and are monitored
- [ ] alerts cover cost, latency, reliability, and quality drift
- [ ] dashboards support release and routing decisions, not just vanity metrics

## Cost Review Questions

1. Which routes or tenants dominate spend?
2. Is token growth coming from prompt bloat, retrieval bloat, or model verbosity?
3. Could routing or caching cut spend without meaningful quality loss?

## Latency Review Questions

| Question | Why |
|---------|-----|
| where is p95 time spent? | prioritization |
| are slow traces clustered by prompt/model/tool? | root cause attribution |
| is latency acceptable for the product surface? | UX fit |

## Model Routing Trade-offs

| Strategy | Benefit | Risk |
|---------|---------|------|
| single premium model | simpler quality profile | high cost |
| tiered routing by task | cost control | more operational complexity |
| fallback models | resilience | behavior inconsistency |

## Dashboard Smells

| Smell | Why it matters |
|------|----------------|
| total spend only, no attribution | no actionability |
| average latency only, no percentile view | hidden UX pain |
| no correlation between quality and cost | bad release decisions |

## Operations Review Checklist

1. Can you identify the most expensive route quickly?
2. Can you explain a sudden latency spike with trace data?
3. Can you decide whether a prompt/model change was worth it operationally?

## Budget Guardrails

| Guardrail | Example |
|----------|---------|
| per-feature budget | support assistant capped monthly spend |
| per-tenant/customer budget | enterprise account usage monitoring |
| per-route max cost | expensive research route protection |

## Cost Drift Causes

| Cause | Example |
|------|---------|
| prompt growth | extra instructions inflate input tokens |
| retrieval bloat | too many chunks stuffed into context |
| model escalation | premium model used on too many requests |
| verbose outputs | output token growth |

## Latency Drift Causes

| Cause | Example |
|------|---------|
| slower provider/model | routing change or provider issue |
| retrieval expansion | more sources or slower DB/vector lookup |
| extra tool calls | chain growth |
| retry behavior | provider instability |

## Ops Response Patterns

| Problem | Response |
|--------|----------|
| cost spike | identify route/model/prompt source, add guardrails |
| latency spike | inspect span breakdown, not just total latency |
| quality-cost tension | run explicit trade-off review, don’t guess |

## Practical Dashboard Questions

1. What are the top 5 most expensive features?
2. Which routes have the worst p95 latency?
3. Which recent prompt/model rollout changed cost or latency materially?

## Final Ops Notes

Operations maturity means cost, latency, and quality are reviewed together as one release decision system.

## Alert Design Questions

| Question | Why |
|---------|-----|
| who receives spend spike alerts? | actionability |
| what latency spike is worth paging or rollback? | avoid alert fatigue |
| how are quality regressions surfaced next to ops metrics? | balanced decisions |

## Cost Governance Questions

1. Is there a maximum acceptable cost per request or feature?
2. Are expensive routes protected by auth/quota or caching?
3. Is model routing reviewed after major prompt changes?

## Ops Maturity Levels

| Level | Description |
|------|-------------|
| basic | token and latency totals only |
| intermediate | route-level attribution and alerts |
| mature | quality, cost, latency, and feedback all connected in dashboards and release review |

## Runbook Questions

1. If spend spikes tomorrow, who investigates first?
2. If latency spikes after a prompt release, what dashboard proves it?
3. If quality rises but cost doubles, who decides whether that is acceptable?

## Cost/Latency Smells

| Smell | Why it matters |
|------|----------------|
| no route or tenant attribution | low actionability |
| one average latency number only | hidden p95 pain |
| cost dashboards separated from prompt/model versions | poor release insight |

## Release Review Questions

1. Which change increased cost or latency?
2. Did that change also improve quality enough to justify it?
3. Is the issue global or isolated to one route/customer/model?

Without that clarity, operational review becomes guesswork.

## Budget Questions

1. What monthly spend is acceptable for this feature?
2. Which route or model dominates that spend?
3. What optimization would matter most if costs doubled?

## Final Cost/Ops Checklist

- [ ] cost is attributable by meaningful dimensions
- [ ] latency is monitored at percentile level
- [ ] quality changes are reviewed with cost and latency, not separately

That is what makes LLM ops operational rather than anecdotal.

Teams need that clarity to ship responsibly.

It is the foundation of sane model and prompt routing choices.

Without it, cost review becomes reactive instead of designed.

That makes budgets and latency harder to control under growth.

Predictability is the goal.

Good ops makes model changes safer.

That is why observability exists.

## Release Readiness Checklist

- [ ] cost, tokens, and latency are visible by route/feature
- [ ] dashboards highlight regressions, not just totals
- [ ] alerts exist for spend and severe latency spikes
- [ ] model/prompt changes are reviewed for cost trade-offs as well as quality
