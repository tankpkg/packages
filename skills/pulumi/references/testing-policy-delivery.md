# Testing, Policy, and Delivery

Sources: Pulumi documentation on testing, integration testing, Automation API, policy as code, Pulumi Deployments, CI/CD, and ESC; supply-chain and least-privilege deployment practices

Covers: layered verification, policy packs, preview review, CI authentication, serialized updates, Automation API, and production gates.

## Verification Pyramid

Infrastructure correctness includes program behavior, engine planning, provider
behavior, and service behavior. No single test layer covers all four.

| Layer | Proves | Does not prove |
|---|---|---|
| Language checks | Syntax, types, lint, deterministic tests | Provider acceptance |
| Program/unit tests | Registered resource shape and invariants | Real cloud behavior |
| Preview | Planned operations for one stack | Successful provider execution |
| Policy | Organizational rules on resource inputs | Application health |
| Integration deployment | Provider creates and updates real resources | Production scale by itself |
| Post-deploy checks | User-visible behavior | Future drift |

Use the cheapest layer that can catch a failure, but retain real integration
coverage for provider and lifecycle behavior.

## Program Tests

Test durable invariants rather than generated implementation details.

Good assertions:

- storage is encrypted
- public access is disabled
- required labels are present
- production database deletion protection is enabled
- component exports the documented contract
- provider targets the expected project

Brittle assertions:

- exact child registration order
- every provider default
- generated auto-name suffix
- full serialized resource object

Mocks help exercise program registration but cannot prove permissions, quotas,
eventual consistency, API defaults, or replacement behavior. Label their scope
honestly and complement them with preview/integration checks.

## Preview as Required Evidence

In pull requests, generate a preview for affected stacks and make these fields
easy to review:

- stack identity
- create/update/replace/delete counts
- detailed changes for IAM, networking, data, and public exposure
- policy violations
- provider/version changes
- unknown values that defer decisions until update

Do not expose secret config or output values in logs. Restrict preview comments
to trusted repositories and actors.

## Policy as Code

Use policy packs for rules that should apply across projects. Keep local
program validation for project-specific contracts.

| Rule type | Best home |
|---|---|
| Organization forbids public buckets | Mandatory policy pack |
| All resources require cost-center tag | Policy pack with clear exception path |
| One component requires exactly two subnets | Component/program validation |
| Team naming preference | Advisory policy or lint |

Policies evaluate resource inputs during preview/update. They do not replace
cloud organization policies, IAM boundaries, or runtime security monitoring.

Policy design:

1. Give the violation a remediation-oriented message.
2. Handle unknown values without silently passing unsafe cases.
3. Test both compliant and violating resources.
4. Version policy packs.
5. Roll new mandatory rules through advisory mode when existing estates need
   remediation.

## CI Authentication

Prefer workload identity federation or OIDC for Pulumi and cloud access.
Avoid long-lived service account keys and personal access tokens.

Deployment identity should have:

- read access for preview
- narrowly scoped mutation access for update
- backend access only to intended stacks
- secrets-provider decrypt access only when required
- no broad organization owner role

Separate preview and update permissions when the platform supports it.

## Pipeline Shape

```text
pull request
  -> dependency integrity
  -> language checks
  -> program tests
  -> policy checks
  -> preview affected stacks
  -> human review
trusted merge
  -> acquire short-lived identity
  -> update one stack at a time
  -> post-deploy verification
  -> record deployment evidence
```

Serialize updates per stack. Use concurrency groups or the managed deployment
system so a second merge cannot race the first update.

## Environment Promotion

Promote the same reviewed source and locked dependencies through environments.
Change stack config, not program branches, for environment-specific values.

Production gate checklist:

1. Non-production update passed.
2. Detailed production preview is current.
3. Replacement/delete decisions are approved.
4. Data backup and rollback controls exist for stateful changes.
5. Policy checks pass.
6. Deployment identity and target stack are verified.
7. Post-deploy health checks are defined.

## Automation API

Use Automation API when a service or tool must orchestrate Pulumi operations
programmatically. Do not adopt it merely to wrap a CLI call in custom code.

Good fits:

- self-service infrastructure portals
- per-tenant stack orchestration
- integration test environments
- multi-stage application deployments
- custom workflows requiring structured events and outputs

Automation requirements:

- explicit stack naming and ownership
- serialized operations
- durable logs and update events
- cancellation and timeout handling
- secret-safe output handling
- idempotent retry strategy based on observed stack state
- lifecycle cleanup and retention policy

## Integration Tests

Use ephemeral, isolated stacks with unique cloud naming and budget controls.
Test create, read/health, update, and destroy for reusable components. If the
resource is intentionally retained or protected, test the documented cleanup
path rather than weakening production safeguards.

Record failed cleanup as an operational incident because leaked cloud resources
cost money and can create security exposure.

## Supply Chain

- Pin provider and SDK versions through lockfiles.
- Review provider upgrades separately.
- Verify third-party component/package provenance.
- Restrict CI actions and images to reviewed versions.
- Avoid executing untrusted pull-request code with deployment credentials.
- Keep policy and deployment logs according to audit requirements.

## Review Checklist

- Tests assert infrastructure outcomes, not generated internals.
- Preview is attached to the exact stack and commit.
- Policies have actionable messages and tests.
- CI uses short-lived credentials.
- Untrusted code cannot access deployment secrets.
- Updates are serialized per stack.
- Production has an approval and post-deploy gate.
- Automation API services handle concurrency and failure explicitly.

## Source Links

- https://www.pulumi.com/docs/iac/guides/testing/
- https://www.pulumi.com/docs/iac/guides/testing/integration/automation-api/
- https://www.pulumi.com/docs/iac/concepts/automation-api/
- https://www.pulumi.com/docs/iac/concepts/policy/
- https://www.pulumi.com/docs/pulumi-cloud/deployments/
- https://www.pulumi.com/docs/iac/guides/continuous-delivery/
