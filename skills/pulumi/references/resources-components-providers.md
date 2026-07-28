# Resources, Components, Providers, and Identity

Sources: Pulumi documentation on resources, names, URNs, components, providers, resource options, import, aliases, protect, retainOnDelete, and transformations

Covers: identity, physical naming, components, explicit providers, lifecycle options, imports, and no-replacement refactoring.

## Resource Identity

Pulumi tracks resources by URN, not by source file or variable name. URN inputs
include stack, project, type, parent path, and logical name.

| Change | Identity impact |
|---|---|
| Rename source variable only | None |
| Move declaration to another file | None |
| Change logical resource name | New URN unless aliased |
| Change parent component | New URN unless aliased |
| Change resource type/provider package | Usually replacement or migration |
| Move to another project or stack | New state ownership |

Separate the Pulumi logical name from the cloud provider's physical name.
Auto-naming often prevents collisions and permits create-before-delete. Existing
resources imported with fixed physical names need extra care around replacement.

## Read Every Preview by Operation

| Symbol/operation | Meaning | Review question |
|---|---|---|
| Create | New managed object | Is this intentionally new? |
| Update | In-place provider change | Is downtime or policy impact acceptable? |
| Replace | Delete/create or create/delete | Why can this not update in place? |
| Delete | Remove from provider | Is deletion intended and recoverable? |
| Same | No desired change | Does drift still need checking? |

An alias solves Pulumi identity movement; it does not make an immutable cloud
property mutable. After preserving the URN, the provider may still require a
replacement for a changed physical property.

## Safe Refactoring with Aliases

Add aliases in the same change that renames or reparents a resource. Preview
must show the existing resource adopting the new identity without create/delete.

Common alias dimensions:

- old logical name
- old parent
- old type
- old project or stack where supported by the migration design
- prior full URN for exact control

Keep aliases long enough for all active stacks to pass through the migration.
Removing an alias before a dormant stack updates can cause replacement later.

## Components

Use `ComponentResource` to create a semantic architecture boundary, not merely
to shorten a file. A component should:

1. Accept a typed, minimal input contract.
2. Register itself before children.
3. Parent all child resources to itself.
4. Propagate relevant resource options.
5. Register stable outputs.
6. Hide incidental child implementation details.

Changing an existing resource's parent to a new component changes its URN.
Supply aliases for the old parent relationship during component extraction.

## Provider Selection

Default providers are convenient for one target account and region. Use an
explicit provider when the program manages multiple accounts/projects/regions,
requires distinct credentials, or needs deterministic provider configuration.

| Scenario | Pattern |
|---|---|
| One cloud target per stack | Stack config plus default provider |
| Multiple GCP projects | Explicit provider per project |
| Component deploys to a supplied target | Accept provider through options |
| Child package needs provider inheritance | Use provider/provider-map options |

Provider changes can alter defaults, API behavior, and resource identity.
Preview provider upgrades and provider reassignment as infrastructure changes,
not package-maintenance noise.

## Lifecycle Options

| Option | Use | Risk |
|---|---|---|
| `protect` | Block deletion of critical resources | Must be intentionally removed before legitimate delete |
| `retainOnDelete` | Remove from Pulumi without deleting provider object | Leaves unmanaged infrastructure and cost |
| `deleteBeforeReplace` | Force old deletion before replacement | Creates downtime; use only for naming/API constraint |
| `ignoreChanges` | Delegate selected property ownership externally | Can hide drift and stale desired values |
| `replaceOnChanges` | Force replacement for selected changes | Expands blast radius |
| `dependsOn` | Add non-data ordering edge | Can over-serialize graph |
| `parent` | Establish hierarchy and inherited identity | Reparenting needs aliases |
| `provider` | Select explicit provider instance | Provider mismatch may propose replacement |

`protect` and `retainOnDelete` solve different problems. Protection blocks a
Pulumi delete. Retention allows the state entry to be deleted while preserving
the cloud object.

## Import Existing Resources

Import associates a real provider ID with a Pulumi resource identity. Use the
CLI for generated code or the resource `import` option for program-first work.

Import invariants:

1. Find the provider-specific canonical import ID in the Registry resource page.
2. Use the exact provider package and resource type intended for long-term use.
3. Match immutable and provider-defaulted inputs to the live resource.
4. Import into the final project, stack, logical name, and parent where possible.
5. Preview after removing one-time import options from committed code if the
   selected workflow requires that cleanup.
6. Require a no-create/no-delete steady-state preview.

Do not import one cloud object into two Pulumi stacks. State ownership must be
singular even if multiple stacks read the object through data sources.

## Bulk Import

For complex programs, declare the desired graph and run
`pulumi preview --import-file import.json`. Pulumi fills type, logical name,
parent, and provider data; supply the real IDs, then execute import using the
reviewed file.

This program-first path preserves intended hierarchy better than a flat series
of CLI imports. Import dependencies in provider-valid order when the provider
requires parent resources or enabled APIs to exist.

## Ignore Changes Carefully

Use `ignoreChanges` only after naming the external controller and authority for
the property. Pulumi uses prior state for ignored properties; refresh may be
needed to observe external values before the next update.

Good candidates include controller-managed replica counts. Poor candidates
include security policy, IAM membership, encryption, or broad resource objects.

## Review Checklist

- Logical names and parent paths are stable.
- Every rename or reparent includes aliases.
- Physical names are explicit only when required.
- Components own and parent their children.
- Explicit providers match target accounts and regions.
- Critical resources use deliberate protection.
- Imports use Registry-documented IDs.
- Ignore rules identify an external owner.
- Preview contains no unexplained replacement or delete.

## Source Links

- https://www.pulumi.com/docs/iac/concepts/resources/names/
- https://www.pulumi.com/docs/iac/concepts/components/
- https://www.pulumi.com/docs/iac/concepts/resources/providers/
- https://www.pulumi.com/docs/iac/concepts/resources/options/
- https://www.pulumi.com/docs/iac/concepts/resources/options/aliases/
- https://www.pulumi.com/docs/iac/concepts/resources/options/import/
- https://www.pulumi.com/docs/iac/concepts/resources/options/protect/
- https://www.pulumi.com/docs/iac/concepts/resources/options/retainondelete/
