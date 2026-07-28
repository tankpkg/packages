---
name: @tank/pulumi
description: |
  Build, review, operate, and troubleshoot production Pulumi infrastructure as
  code in TypeScript, Python, Go, .NET, Java, or YAML. Covers projects and
  stacks, configuration and secrets, Inputs and Outputs, components, providers,
  state and backends, imports, safe refactoring, testing, policy, CI/CD, drift,
   and Automation API. Synthesizes current Pulumi documentation, engine and
   provider source, 2026 release notes, maintainer issue investigations, and
   production incident reports.

  Trigger phrases: "pulumi", "pulumi up", "pulumi preview", "Pulumi.yaml",
  "Pulumi stack", "pulumi config", "Pulumi secrets", "Input Output apply",
  "Pulumi component", "Pulumi provider", "Pulumi state", "pulumi import",
  "Pulumi drift", "Pulumi Automation API", "CrossGuard", "Pulumi CI/CD",
  "infrastructure as code with TypeScript", "infrastructure as code with Python"
---

# Pulumi

## Core Philosophy

1. **Preview is a review artifact** -- inspect creates, updates, replacements,
   and deletes before every update; a syntactically valid program can still
   propose destructive infrastructure changes.
2. **Resource identity is durable** -- URNs combine stack, project, type,
   parent, and logical name. Preserve identity with aliases when reorganizing
   code so refactors do not become replacements.
3. **Outputs are deferred values** -- pass `Output` values directly as inputs
   and transform them with the language SDK. Do not block, stringify, or read
   them as ordinary values during program evaluation.
4. **State is sensitive coordination data** -- use a durable backend, protect
   secrets, avoid manual edits, and use supported stack/state commands only
   with an export available for recovery.
5. **Blast radius defines boundaries** -- split projects and stacks by
   ownership, lifecycle, permissions, and failure domain rather than creating
   one stack per resource or one stack for an entire organization.

## Default Workflow

1. Inspect `Pulumi.yaml`, stack settings, language dependencies, backend, and
   selected stack before changing code.
2. Confirm cloud identity, provider configuration, target account/project,
   region, and stack configuration without printing secret values.
3. Make the smallest typed program change that preserves resource identity.
4. Run language checks and tests, then `pulumi preview --diff` for the exact
   target stack.
5. Treat every replacement or delete as a blocker until its cause and blast
   radius are understood.
6. Apply through the repository's approval path; verify outputs and provider
   health after deployment.

## Quick-Start: Common Problems

### "How should I organize this Pulumi estate?"

Choose boundaries from ownership and lifecycle first, then map environments to
stacks. Connect stacks with explicit outputs or references rather than hidden
global lookups.

-> See `references/projects-stacks-config.md`.

### "Why can I not use this resource property like a normal string?"

It is probably an `Output`. Pass it directly to another resource input, use
`apply` only for a derived value, and export only values consumers need.

-> See `references/programming-model.md`.

### "Why does this refactor want to replace infrastructure?"

Compare old and new URNs. A changed logical name, parent, type, project, or
stack changes identity. Add the appropriate alias before moving code.

-> See `references/resources-components-providers.md`.

### "The cloud and Pulumi disagree"

Run `pulumi refresh --preview-only` to observe drift without changing state.
Decide whether code or live infrastructure is authoritative before refreshing
state or reconciling with an update.

-> See `references/state-and-operations.md`.

### "How do I ship Pulumi safely?"

Run static checks and tests, publish the preview for review, authenticate with
short-lived credentials, serialize updates per stack, and apply only from a
trusted branch with an approval gate for production.

-> See `references/testing-policy-delivery.md`.

### "What are the sharp edges that ordinary docs do not teach?"

Check the current CLI/provider versions before importing or repairing state,
distinguish bridged-provider behavior from Pulumi engine behavior, and consult
the failure-mode ledger before using refresh, ignoreChanges, deletedWith,
generated import code, or a DIY backend in production.

-> See `references/field-guide-2026.md`.

## Decision Trees

### Choose a Language

| Signal | Default |
|---|---|
| Existing application team owns infrastructure | Use its primary supported language |
| TypeScript-heavy platform team | TypeScript for mature package ergonomics |
| Python-heavy data or backend team | Python with strict type checking |
| Go platform tooling | Go for explicit control flow and compiled tooling |
| .NET or Java organization | Use the native ecosystem language |
| Small declarative composition with little logic | YAML |

### Choose a State Backend

| Need | Direction |
|---|---|
| Managed locking, history, RBAC, deployments, drift, policy | Pulumi Cloud |
| Existing object-storage control requirement | DIY backend with encryption, versioning, and access controls |
| Disposable local experiment only | Local backend; migrate before collaboration |

### Choose a Resource Abstraction

| Reuse scope | Construct |
|---|---|
| One stack, one resource | Custom resource |
| Repeated architecture inside programs | `ComponentResource` |
| Versioned multi-language reusable package | Pulumi Package / provider package |
| Orchestrating Pulumi from an application | Automation API |

## Safety Gates

Pause before applying when a preview contains an unexplained replacement,
delete, provider change, parent change, secret plaintext, or a target stack that
does not match the intended environment. Do not use `--yes`, targeted updates,
state deletion, or manual checkpoint editing to bypass uncertainty.

## Reference Index

| File | Contents |
|---|---|
| `references/projects-stacks-config.md` | Project and stack boundaries, config, secrets, environments, and references |
| `references/programming-model.md` | Inputs, Outputs, dependencies, language choices, and asynchronous value handling |
| `references/resources-components-providers.md` | Resource identity, options, components, providers, imports, and safe refactoring |
| `references/state-and-operations.md` | Backends, previews, updates, refresh, drift, recovery, and state safety |
| `references/testing-policy-delivery.md` | Tests, policy packs, CI/CD, Automation API, and production controls |
| `references/field-guide-2026.md` | 2026 version floors, engine/provider internals, import incidents, state traps, and operational heuristics |
