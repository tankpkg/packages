# Projects, Stacks, Configuration, and Secrets

Sources: Pulumi documentation on projects, stacks, configuration, secrets, stack settings, environments, and project organization; Twelve-Factor App configuration principles

Covers: boundary design, `Pulumi.yaml`, stack settings, configuration namespaces, secret handling, stack outputs, and cross-stack contracts.

## Mental Model

| Object | Purpose | Identity |
|---|---|---|
| Project | One Pulumi program and its metadata | `name` in `Pulumi.yaml` |
| Stack | Isolated instance of a project | organization/project/stack |
| Configuration | Stack-specific program inputs | namespaced key/value entries |
| Output | Published deployment result | exported by the stack program |
| Environment | Reusable config/secrets context | imported into stack settings |

A stack is not merely a label. It owns an independent resource graph and state
checkpoint. An update targets exactly one stack, so stack boundaries are blast
radius boundaries.

## Design Project Boundaries

Score each candidate boundary against four forces:

| Force | Split when | Keep together when |
|---|---|---|
| Ownership | Different teams approve changes | One team owns the lifecycle |
| Lifecycle | Resources deploy at different rates | Resources change atomically |
| Privilege | Different deployment identities are required | Permissions are identical |
| Failure domain | One update must not affect the other | Partial deployment is harmful |

Prefer a small number of coherent projects over either extreme. A monolithic
organization stack creates a huge blast radius; a project per resource creates
dependency and coordination overhead.

## Map Environments to Stacks

Use stacks for repeated instances of the same program such as `dev`, `staging`,
and `production`. Use separate projects when the program shape, owner, or
deployment permissions differ materially.

Naming checklist:

1. Choose a stable project name before importing resources.
2. Use organization-qualified stack names in automation.
3. Avoid ambiguous environment aliases such as `prod2`.
4. Record cloud account/project and region in stack configuration.
5. Verify the selected stack before preview and update.

## Project File

`Pulumi.yaml` declares project metadata and runtime. Keep it deterministic and
reviewable. Use the runtime options supported by the chosen language rather
than shell wrappers that obscure program execution.

```yaml
name: payments-platform
runtime:
  name: nodejs
  options:
    typescript: true
description: Shared payments infrastructure
```

Keep provider versions in the language package manager, lock them, and review
upgrades. The CLI, language SDK, and provider plugin participate in one update;
unexpected version drift can change schemas or diffs.

## Configuration Contract

Treat config as a typed public interface for the program.

| Value | Store as | Reason |
|---|---|---|
| Region, feature flag, resource size | Plain stack config | Non-sensitive deployment input |
| Password, token, private key | Secret config | Encrypt in state and propagate secrecy |
| Resource-derived endpoint | Stack output | Produced by deployment, not operator input |
| Shared organization defaults | Environment or component default | Reuse without duplicating stack files |
| Cloud identity | Workload identity / environment | Avoid long-lived credential config |

Use namespaced configuration so package and project keys do not collide. Read
required values with required getters so missing configuration fails early.

```bash
pulumi config set app:region europe-west1
pulumi config set --secret app:databasePassword "$VALUE"
pulumi config set --path app:network.subnetCount 3
```

Do not place secret plaintext in `Pulumi.<stack>.yaml`, command history, logs,
preview comments, test fixtures, or exported stack files.

## Secret Semantics

Pulumi records resource inputs and outputs in state. Marking a config value as
secret encrypts it and normally causes derived Outputs to remain secret. This
is protection in state and display, not permission to expose the value to an
unsafe command or third-party process.

Secret review checklist:

1. Obtain credentials through short-lived workload identity where possible.
2. Use `pulumi config set --secret` for unavoidable static values.
3. Confirm the stack has the intended secrets provider.
4. Avoid `apply` callbacks that log values.
5. Mark derived sensitive values as secret if secrecy is not preserved.
6. Review exported checkpoints as sensitive material even when encrypted.

Changing secrets providers is a state operation. Back up and follow the
documented migration command rather than editing ciphertext in YAML.

## Stack Outputs as Contracts

Export stable, consumer-oriented values instead of entire resource objects.

Good outputs:

- Service URL
- Network or subnet ID
- Service account email
- Database instance connection name
- Artifact repository name

Poor outputs:

- Full provider response objects
- Secrets a consumer does not need
- Internal logical names
- Values that can be derived locally

When one stack consumes another, use a stack reference and version the contract
operationally. A producer rename can break consumers even if no cloud resource
changes.

## Cross-Stack Decision

| Relationship | Pattern |
|---|---|
| Same lifecycle and owner | Keep resources in one stack |
| Stable provider/consumer boundary | Export minimal outputs and use stack reference |
| Runtime application lookup | Publish to service discovery or secret manager |
| Circular dependency | Redesign ownership; do not create reciprocal stack references |

## Repository Layout

Choose discoverability over ceremony:

```text
infra/
  Pulumi.yaml
  Pulumi.dev.yaml
  Pulumi.production.yaml
  src/
    index.ts
    network.ts
    service.ts
  test/
```

For multiple projects, give each project its own `Pulumi.yaml` and dependency
lockfile boundary. Share components through a normal package when multiple
projects need the same architecture.

## Review Checklist

- Project boundary matches owner and blast radius.
- Stack name and cloud target are explicit.
- Required config fails fast.
- Secrets are encrypted and not logged.
- Provider and language dependencies are locked.
- Outputs are minimal and documented.
- Cross-stack references are acyclic.
- Stack settings contain no generated resource state.

## Source Links

- https://www.pulumi.com/docs/iac/concepts/projects/
- https://www.pulumi.com/docs/iac/concepts/stacks/
- https://www.pulumi.com/docs/iac/concepts/config/
- https://www.pulumi.com/docs/iac/concepts/secrets/
- https://www.pulumi.com/docs/iac/concepts/projects/stack-settings-file/
- https://www.pulumi.com/docs/iac/guides/basics/organizing-projects-stacks/
