# Performance and Security

Sources: Cloudflare Workers official documentation, Cloudflare cache and security docs, Hono docs, community edge security and performance guidance

Covers: latency reduction, caching, background work, auth/secrets handling, edge-safe dependencies, and common performance/security pitfalls in Workers applications.

## Edge Performance Starts with Simplicity

| Pattern | Benefit |
|--------|---------|
| short request path | lower latency |
| explicit caching | fewer origin trips |
| async side work in `waitUntil` | faster user response |

## Security Rules

| Rule | Why |
|-----|-----|
| keep secrets in Wrangler secrets/env bindings | avoid source leaks |
| validate all request input | edge exposure is public exposure |
| authenticate before expensive work | reduce abuse cost |
| avoid Node-only deps with unknown behavior | runtime and supply-chain risk |

## Caching Strategy

| Need | Pattern |
|-----|---------|
| repeated GET responses | Cache API / platform cache headers |
| static/generated artifacts | store in R2 + cache aggressively |
| computed reads | KV or cache with invalidation path |

## Common Pitfalls

| Pitfall | Fix |
|--------|-----|
| doing all work synchronously in fetch | move non-critical work to queue or `waitUntil` |
| overusing Durable Objects for simple reads | use KV/cache |
| mixing secret and public env carelessly | keep private env server-only |

## Cache Review Questions

1. What is the invalidation path?
2. Is stale data acceptable here?
3. Could this read be served from the platform cache instead of recomputation?

## Abuse and Cost Controls

| Risk | Mitigation |
|-----|------------|
| unauthenticated expensive AI route | auth + quota + rate limiting |
| hot key coordination path | redesign ownership or shard workload |
| origin amplification | cache, validate, and short-circuit aggressively |

## Secret Handling Rules

| Rule | Why |
|-----|-----|
| keep secrets in runtime bindings | avoid source leakage |
| separate public config from secrets | reduce accidental exposure |
| rotate and scope secrets by environment | blast radius control |

## Edge Security Questions

1. What routes are publicly callable without auth?
2. Which routes can trigger expensive downstream work?
3. Are rate limits and quotas appropriate for cost exposure?
4. Could a malformed request fan out into expensive origin calls?

## Performance Checklist

| Check | Why |
|------|-----|
| cache obvious repeatable reads | reduce latency and origin load |
| short-circuit invalid/auth-failed requests early | reduce wasted work |
| keep edge path small | predictable tail latency |

## Origin Protection Patterns

| Pattern | Benefit |
|--------|---------|
| validate before origin fetch | avoid amplification |
| cache successful reads | reduce repeated backend work |
| queue non-critical follow-up tasks | faster response path |

## Dependency Review Checklist

1. confirm package does not require Node built-ins
2. confirm runtime size/cost impact is acceptable
3. confirm package behavior under edge constraints is documented or tested

Packages that are fine in Node servers can still be a bad fit at the edge.

## Route Cost Review

| Question | Why |
|---------|-----|
| does this route hit origin on every request? | latency and cost |
| could cached or static data satisfy most requests? | reduce backend pressure |
| does unauthenticated traffic reach expensive code paths? | abuse exposure |

## Secure Defaults

| Concern | Default |
|--------|---------|
| unauthenticated expensive route | deny or throttle |
| sensitive env vars | private bindings only |
| malformed input | reject early |

## Review Checklist for Hot Paths

1. Is there any unnecessary origin fetch in the critical path?
2. Can the route be cached safely?
3. Does authentication happen before expensive work?
4. Is asynchronous follow-up work leaving the response path?

## Practical Edge Hardening

| Practice | Benefit |
|---------|---------|
| explicit request validation | lower abuse and bug surface |
| auth before downstream fanout | reduced cost exposure |
| small dependency set | smaller runtime and attack surface |

Performance and security often improve together when request paths are simpler.

## Cost-Sensitive Route Review

| Question | Why |
|---------|-----|
| does this route call AI or origin every time? | runaway cost risk |
| can invalid requests be rejected before expensive work? | protect platform spend |
| can a queue decouple slow side effects? | lower p95 latency |

Expensive edge routes need explicit cost design, not just correct code.

## Basic Security Review Questions

1. Are secret and public config clearly separated?
2. Could anonymous traffic trigger expensive or privileged behavior?
3. Are validation failures rejected before backend fanout?

Simple review questions catch many edge-specific mistakes early.

## Edge Runtime Performance Notes

| Concern | Recommendation |
|--------|----------------|
| repeated identical reads | cache or KV where consistency allows |
| serialized coordination | reserve Durable Objects for true coordination |
| AI or origin-heavy routes | add strict auth, quota, and caching review |

Good edge performance comes from architecture discipline more than micro-optimizing syntax.

## Latency Reduction Checklist

1. avoid unnecessary origin round-trips
2. reject bad requests before expensive work
3. move non-critical side effects off the response path
4. choose the cheapest state primitive that still matches consistency needs

This checklist is often enough to fix the worst p95 problems.

## Security Review Heuristics

| Heuristic | Why |
|----------|-----|
| privileged routes must be explicit | easier auditability |
| expensive routes need auth/quota review | cost-abuse protection |
| secret usage should be obvious in code and config | lower leak risk |

## Fast Review Questions

1. Can an anonymous caller trigger expensive origin or AI work?
2. Is any secret-like value accidentally treated as public config?
3. Could caching return the wrong data to the wrong caller?

Short review questions keep edge security and cost discipline in daily development conversations.

## Caching Safety Questions

| Question | Why |
|---------|-----|
| is response user-specific? | avoid cache leakage |
| is stale data acceptable? | choose cache strategy correctly |
| is invalidation path defined? | prevent silent data drift |

Caching is a security concern whenever data visibility varies by caller.

## Authentication Cost Review

| Route type | Review focus |
|-----------|--------------|
| public informational | cacheability and abuse limits |
| authenticated data route | per-user correctness and cache isolation |
| AI or heavy compute route | auth, quota, and budget exposure |

The most expensive edge routes deserve the strictest auth and quota review.

## Edge Response Path Checklist

1. validate request early
2. authenticate before expensive work
3. serve cacheable data from the cheapest safe source
4. push non-critical side effects off the request path

This is the practical path to safer and faster Workers services.

## Practical Hardening Defaults

| Default | Why |
|--------|-----|
| explicit validation at edge boundary | rejects malformed input early |
| narrow dependency set | lowers runtime and supply-chain risk |
| documented auth/quota for expensive routes | protects cost and uptime |

Defaults matter because edge services tend to sprawl quickly when routes and bindings multiply.

## Cheap Review Win

Review one representative hot route from request entry to final response. The end-to-end path often reveals both latency and security waste.

## Baseline Edge Safety Rules

1. reject invalid requests before origin or AI calls
2. keep secret-bearing logic server-side and explicit
3. choose the least powerful state primitive that still satisfies correctness
4. prefer cache hits over repeated expensive computation when safe

These are small rules, but they compound into lower latency, lower cost, and lower risk.

## Final Review Prompts

Ask these before shipping a hot route:

1. What is the cheapest safe way to answer this request?
2. What is the earliest point we can reject abuse or invalid input?
3. Are we paying origin, AI, or coordination cost unnecessarily?

These prompts help catch both performance waste and security exposure in one pass.

Short review loops at the edge are valuable because mistakes scale globally and quickly.

Keep the critical path small.

## Release Readiness Checklist

- [ ] Caching strategy matches actual read/write patterns
- [ ] Request path avoids unnecessary origin or coordination work
- [ ] Secrets and auth checks are explicit
- [ ] Dependencies are edge-safe and intentionally chosen
