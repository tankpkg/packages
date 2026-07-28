# Testing, Security, and Delivery

Sources: HashiCorp Terraform validate, test framework, sensitive data, automation, HCP Terraform, policy, and dependency lockfile documentation; workload identity practices

Covers: formatting, validation, native tests, real integration tests, policy, secrets, CI authentication, plan review, serialized apply, and post-deploy evidence.

## Verification Layers

| Layer | Proves |
|---|---|
| `fmt -check` | Canonical formatting |
| `validate` | Internal syntax/schema consistency |
| `test` with plan | Module logic and assertions without apply |
| `test` with apply | Real provider lifecycle against test resources |
| Policy/static analysis | Organization rules and known misconfiguration |
| Full environment plan | Exact proposed operations |
| Post-apply checks | Runtime service behavior |

Mocks cannot prove cloud permissions, quotas, defaults, eventual consistency, or
real replacement behavior. Keep real, isolated lifecycle tests for reusable
modules and high-risk provider behavior.

## Native Tests

Terraform discovers `.tftest.hcl` and `.tftest.json`. Default run blocks apply
real infrastructure; set `command = plan` deliberately for non-creating tests.

Assert durable outcomes such as encryption, network exposure, labels, retention,
and output contracts. Avoid exact snapshots of every provider default.

Test cleanup failure is an incident: leaked resources create cost and exposure.

## Sensitive Data

Sensitive markings redact CLI/UI display but values may remain in state and plan
files. Secure backend, plan artifacts, logs, variable files, and CI caches.

Prefer short-lived workload identity and secret managers. Do not commit `.tfvars`
containing credentials or pass secrets on command lines that enter shell history.

## CI Pipeline

```text
pull request
  -> fmt and validate
  -> provider/module integrity
  -> tests and policy
  -> full plan
  -> review
trusted merge
  -> acquire short-lived identity
  -> apply reviewed plan, one state at a time
  -> health checks and evidence
```

Untrusted pull-request code must not receive cloud or state credentials.

## Plan Evidence

Record state/workspace, commit, Terraform/provider versions, plan operation
counts, policy results, approval, apply result, and health checks. Restrict saved
plan access because it can contain sensitive values.

## Concurrency

Serialize apply per state with backend locking and CI concurrency controls. Do
not run local emergency applies concurrently with automation.

Targeted plans/applies are diagnostic or recovery tools, not normal delivery;
follow them with a complete plan to restore graph-wide confidence.

## Provider Upgrades

Upgrade separately, review lockfile checksums, plan representative states, and
roll out gradually. Do not combine provider upgrades with imports or refactors.

## Production Gate

- Correct state/backend and cloud identity.
- Checks and tests pass.
- Full saved plan is current and reviewed.
- No unexplained replacement or destroy.
- Stateful changes have provider-native backup/recovery.
- Short-lived least-privilege credentials are active.
- Apply is serialized.
- Health checks and rollback ownership are defined.

## Review Checklist

- Tests match their real-vs-mocked scope.
- Secrets are protected beyond display redaction.
- Untrusted code has no deployment credentials.
- Plans are exact, reviewable, and access-controlled.
- Applies use reviewed saved plans.
- Provider upgrades are isolated.
- Production verification covers user-visible behavior.

## Source Links

- https://developer.hashicorp.com/terraform/language/validate
- https://developer.hashicorp.com/terraform/language/tests
- https://developer.hashicorp.com/terraform/language/manage-sensitive-data
- https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform
- https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement
