# Wrangler and Deployment

Sources: Wrangler documentation, Cloudflare Workers deployment documentation, Cloudflare Pages documentation, CI/CD examples, community production practices

Covers: Wrangler config, environments, secrets, preview and production rollout, deployment workflows, CI/CD, and operational deployment patterns for Workers and Pages Functions.

## Wrangler Is the Operational Control Plane

Wrangler defines your app name, entrypoint, bindings, compatibility date, environments, and deploy workflow.

| Concern | Wrangler role |
|--------|----------------|
| local dev | `wrangler dev` |
| deploy | `wrangler deploy` |
| env-specific bindings | `[env.staging]`, `[env.production]` |
| secrets | `wrangler secret put` |

Keep Wrangler config readable and close to the actual runtime shape.

## Environment Strategy

| Environment | Use |
|------------|-----|
| preview/dev | local iteration or branch preview |
| staging | integration verification |
| production | live traffic |

Separate bindings and secrets by environment. Do not reuse production bindings casually in staging.

## Basic Wrangler Practices

1. Pin a compatibility date intentionally
2. Type your bindings in code
3. Keep environment-specific config explicit
4. Treat secrets as runtime config, not repo content

## Secrets Handling

| Rule | Why |
|-----|-----|
| use `wrangler secret put` | avoid committing secrets |
| scope secrets per environment | reduce blast radius |
| document required secret names | deployment repeatability |

## Deployment Patterns

| Pattern | Best for |
|--------|----------|
| manual CLI deploy | small team / low frequency |
| CI deploy on main/tag | repeatable production workflow |
| preview deploys by branch | app review and testing |

Make promotion predictable rather than relying on ad hoc local deploys forever.

## CI/CD Checklist

| Step | Purpose |
|-----|---------|
| test/build | correctness |
| verify Wrangler config | runtime validity |
| deploy to staging | integration check |
| promote to production | controlled release |

## Pages Functions Notes

Pages Functions share much of the same deployment thinking but live inside a Pages project model.

| Concern | Note |
|--------|------|
| static assets + functions | good Pages fit |
| fully API-centric worker | plain Workers may be clearer |

## Common Deployment Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| no staging environment | production becomes test surface | add staging |
| secrets managed manually with poor docs | broken releases | document and script |
| compatibility date never reviewed | surprise runtime drift | intentional bumps |

## CI Promotion Pattern

| Stage | Goal |
|------|------|
| test | validate code and config |
| deploy preview/staging | runtime verification |
| promote production | controlled rollout |

Prefer promotion over rebuilding different artifacts for each environment when your process supports it.

## Environment Drift Checks

1. compare bindings between staging and production
2. verify secret names exist in both where required
3. confirm compatibility date and vars are aligned intentionally

Most deployment pain is configuration drift, not deploy command syntax.

## Preview Environment Strategy

| Strategy | Benefit |
|---------|---------|
| per-branch preview | safer review of route/runtime changes |
| shared staging | integration with real services/bindings |
| production-gated promotion | lower blast radius |

Preview environments are especially valuable when bindings, routes, and edge behavior evolve together.

## Deployment Review Checklist

1. confirm Wrangler config and bindings for target env
2. verify secrets exist before deploy step
3. validate route ownership and custom domain impact
4. smoke-test a binding-backed endpoint after deploy

## Rollback Thinking

| Concern | Recommendation |
|--------|----------------|
| bad code deploy | keep prior release/version path documented |
| config mistake | compare env config before code rollback |
| binding mismatch | fix configuration first if code is correct |

Rollback is not always "deploy old code". Sometimes the broken thing is the environment wiring.

## Binding Documentation Pattern

Document bindings in a table near the deploy workflow.

| Binding | Type | Env(s) | Purpose |
|--------|------|--------|---------|
| `DB` | D1 | staging, prod | relational metadata |
| `CACHE` | KV | all | low-latency cached reads |
| `BUCKET` | R2 | prod | object storage |

Binding documentation prevents mystery config and reduces onboarding friction.

## Secret Rotation Notes

| Step | Why |
|-----|-----|
| create new secret | stage rotation safely |
| deploy with dual-read or updated config | avoid service breakage |
| verify traffic path | ensure new secret works |
| remove old secret | finish cleanup |

Rotating secrets operationally matters more than just storing them correctly once.

## CI Authentication Patterns

| Pattern | Use |
|--------|-----|
| API token in CI secret store | common baseline |
| scoped deployment credentials | safer than wide account access |
| separate staging/prod credentials | reduce blast radius |

Do not let CI use over-broad credentials if environments can be separated.

## Post-Deploy Operational Checks

1. hit health or sanity endpoint
2. verify binding-backed route behavior
3. inspect logs for runtime/config regressions
4. confirm preview/staging parity before prod if using promotion flow

The deploy is not complete when the command returns; it is complete when the runtime behaves correctly.

## Multi-Environment Naming Strategy

| Concern | Recommendation |
|--------|----------------|
| worker names | keep predictable suffixes or env mapping |
| binding names | keep stable across envs when possible |
| custom domains/routes | document ownership per env |

Consistency reduces deployment mistakes more than clever naming schemes.

## Release Runbook Outline

1. verify config and secrets
2. run tests/build checks
3. deploy to non-prod target
4. smoke-test critical route + binding path
5. promote or deploy prod
6. inspect logs and rollback conditions

This runbook should be lightweight enough to follow every time.

## Documentation Checklist

| Item | Why |
|-----|-----|
| required bindings table | easier onboarding and review |
| required secrets list | avoids broken deploys |
| deploy command/pipeline reference | repeatability |
| rollback notes | faster incident response |

## Release Approval Questions

1. Are bindings and secrets present in the target environment?
2. Has at least one binding-backed path been smoke-tested outside local dev?
3. Is the compatibility date change, if any, intentional and reviewed?
4. Are route/domain changes understood before production rollout?

These questions catch many edge deployment failures before they reach users.

## Common Deployment Smells

| Smell | Why it matters |
|------|----------------|
| staging and production configs differ without documentation | hidden drift |
| no one knows which secret names are required | fragile deploy process |
| preview environments are skipped for risky runtime changes | production becomes test surface |

Operational clarity is a real engineering feature for Workers deployments.

## Deployment Ownership Questions

1. Who can deploy to staging?
2. Who can deploy to production?
3. How are secret changes reviewed and recorded?

Answers to these reduce operational ambiguity as much as technical config does.

## Minimal Runbook Metadata

| Item | Why |
|-----|-----|
| deploy command or CI job name | avoid guesswork |
| required bindings/secrets | preflight checklist |
| smoke-test endpoint list | post-deploy validation |

Even a short runbook is better than tribal knowledge.

## Pre-Deploy Checklist

1. confirm environment target
2. confirm bindings and secret names
3. confirm compatibility date expectations
4. run at least one binding-aware test or smoke check

This checklist prevents configuration mistakes from masquerading as code problems.

## Release Readiness Checklist

- [ ] Environments are explicit and documented
- [ ] Secrets are environment-scoped and not committed
- [ ] Deploy workflow is repeatable via CLI or CI
- [ ] Compatibility date is pinned intentionally
- [ ] Staging exists for meaningful validation when risk justifies it
