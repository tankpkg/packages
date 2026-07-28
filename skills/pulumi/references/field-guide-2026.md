# Pulumi Field Guide 2026

Sources: Pulumi CLI v3.244-v3.254 release notes, pulumi/pulumi and pulumi/pulumi-gcp issue investigations, Pulumi engine and Terraform Bridge documentation, and current state, import, refresh, aliases, and ignoreChanges documentation

Covers: version floors, engine/provider boundaries, imports, refresh semantics, state durability, lifecycle traps, provider upgrades, and incident-driven operating rules.

## Start With a Version Ledger

Record four independent versions for every production stack:

| Layer | Why it matters |
|---|---|
| Pulumi CLI | Engine planning, checkpoint, import, refresh, and code generation |
| Language SDK | Input/Output serialization and resource option behavior |
| Provider plugin/package | Cloud schema, defaults, CRUD, diffs, and import parsing |
| Cloud API | Server defaults, immutability, eventual consistency, and async behavior |

Do not write "Pulumi version" when diagnosing a failure. Capture all four.
The package version used by source code and the plugin loaded by the engine can
also diverge; include `pulumi about` and `pulumi plugin ls` in evidence.

### Current Safety Floors

As of July 2026, use a current v3.254-series CLI for migration work. At minimum:

| Capability or fix | Minimum CLI | Operational consequence |
|---|---:|---|
| Snapshot-integrity fix for `up --refresh` | 3.244.0 | Older refresh/update combinations carry a known integrity defect |
| Read timeout in `customTimeouts` | 3.246.0 | Long provider reads can be bounded separately |
| Canonical import-ID deletion fix | 3.252.0 | Older CLIs can re-import then delete the same live object |
| Automation API import | 3.252.0 | Import can be orchestrated without shell-only glue |
| Explicit providers and state in import files | 3.254.0 | Bulk/state conversion can preserve provider and hierarchy context |
| `pulumi stack migrate` with secret re-encryption | 3.254.0 | Prefer this over manual backend export/import |

The v3.252 import defect was not cosmetic. A reported GCP Secret Manager import
deleted production secrets on the next update and caused a SEV0. The engine lost
the original import ID when it differed from the provider's canonical ID,
planned an import replacement, then deleted the same physical object. The fix
shipped in v3.252.0. Do not conduct brownfield imports on an older CLI.

## Separate Engine Behavior From Provider Behavior

Pulumi has at least three decision layers:

1. The language program registers goals and dependencies.
2. The Pulumi engine compares goals with checkpoint state and schedules steps.
3. The provider validates, diffs, reads, creates, updates, and deletes cloud objects.

A replacement can originate in the engine because identity changed, or in the
provider because a schema field is force-new. A perpetual diff can originate in
the cloud API normalizing a value, the provider flattening it differently, the
Terraform Bridge mapping it, or the language SDK serializing it.

### Bridged Providers

Many Pulumi providers adapt Terraform providers through
`pulumi-terraform-bridge`. At build time the bridge inspects Terraform schemas
and generates Pulumi packages. At runtime it uses that schema for validation and
diffs while connecting the Pulumi engine to the Terraform provider.

This has practical consequences:

- Read the upstream Terraform provider changelog as well as the Pulumi provider
  changelog before upgrades.
- Search both issue trackers when a diff, import, timeout, or default is wrong.
- Expect a lag between an upstream fix and the Pulumi provider release that
  consumes it.
- Do not assume Pulumi property naming means the underlying lifecycle semantics
  differ from Terraform.
- Pin the Pulumi provider version; "upstream fixed" is not evidence that the
  installed bridge contains the fix.

## Preview Is Not a Live Read

Normal `pulumi preview` and `pulumi up` compare the program against recorded
checkpoint state. They do not read every cloud resource first. Therefore:

- A no-change preview proves code agrees with state, not that state agrees with
  the cloud.
- Out-of-band deletion can remain invisible until refresh.
- Out-of-band mutation can be overwritten by the next update.
- An ownership-transfer gate must include a refresh-aware observation.

Use two distinct operations during risky work:

```bash
pulumi refresh --preview-only --diff
pulumi preview --refresh --diff
```

The first shows what live reads would write into state. The second evaluates the
program after live state is considered. Do not treat them as interchangeable.

### `ignoreChanges` Is State Substitution

`ignoreChanges` does not dynamically preserve the live property. Pulumi reuses
the old serialized state value for that input. If an external controller changes
the live value and no refresh runs, a later update can resend the stale state and
undo the controller's change.

Operating rule:

1. Name the external owner and exact property path.
2. Refresh before every update that might send the surrounding object.
3. Inspect whether the provider performs partial patches or sends the whole
   nested object.
4. Prefer a narrower resource boundary over broad ignore paths.

`ignoreChanges` affects custom-resource inputs, not outputs. Passing it to a
component has no automatic effect on its children.

## Import Is a State Transition, Not Code Generation

The CLI import path performs three logically separate jobs:

1. Read a provider ID and bind it to a Pulumi identity.
2. Store provider inputs and outputs in checkpoint state.
3. Attempt to generate a source declaration.

Job 3 can fail or produce poor code while jobs 1-2 succeed. Confirm stack state
and cloud health before retrying a failed generation command. Blind retries can
turn an already-imported object into a replacement path.

Generated code is a forensic starting point, not a maintained contract. Known
failure classes include string constants instead of strong enum types, missing
explicit physical names, incomplete nested values, language codegen defects,
and inability to express provider-specific names. Compile/typecheck generated
code before using it, then reconcile one field at a time.

### Safe Import Procedure

1. Pin current CLI, SDK, and provider versions.
2. Export the stack and preserve the prior owner's state.
3. Use the final logical name, parent, provider, and physical name.
4. Copy the import format from the exact provider version's Registry page.
5. Run import preview first and retain default protection.
6. Verify the stored provider ID is canonical after import.
7. Remove the import option only after code and state converge.
8. Run refresh-aware full preview and service health checks.
9. Keep the previous writer frozen until the next ordinary update also passes.

The CLI protects imported resources by default. Keep protection through
adoption; remove it later only through a separately reviewed change.

## State Backends Are Not Equivalent

Pulumi Cloud checkpoints through a transactional API and journals operations.
DIY object-store backends maintain history, but blob protocols cannot provide
the same transparent recovery from every partial failure. Skipping checkpoints
to speed up large DIY stacks explicitly trades durability for performance.

For DIY backends, document and test:

- object versioning and retention
- concurrent writer exclusion
- secrets-provider recovery and key rotation
- recovery from an interrupted write
- restore of a previous checkpoint
- backend URL pinning in CI
- access audit evidence

Use `pulumi stack migrate` on CLI 3.254+ for backend moves. It migrates the
latest checkpoint and configuration, re-encrypts config and state secrets for
the target secrets provider, leaves source state intact, and may replace a
target stack settings file. Back up local stack settings first.

## Pending Operations Mean Unknown Reality

An interrupted provider call can leave a pending create/update/delete. The
cloud request may have completed even if the CLI never recorded completion.

| Pending operation | Establish before repair |
|---|---|
| Create | Whether exactly one object exists and its provider ID |
| Update | Which fields changed and whether the operation is still running |
| Delete | Whether the object exists, is recoverable, or is already gone |
| Replacement | Which old/new physical objects exist and receive traffic |

Do not choose `--clear-pending-creates` merely to unblock the stack. Use
`--import-pending-creates URN ID` when the cloud object exists. Clearing a real
create or retrying an unknown create can orphan or duplicate infrastructure.

## Lifecycle Options Have Different Failure Domains

| Option | What it actually protects or controls |
|---|---|
| `protect` | Blocks engine-planned deletion of that resource |
| `retainOnDelete` | Removes ownership while intentionally retaining the object |
| `deleteBeforeReplace` | Orders destructive replacement; can cause downtime |
| `replaceOnChanges` | Reclassifies a detected diff as replacement |
| `deletedWith` | Skips a redundant delete when another resource removes it |
| `aliases` | Maps previous Pulumi identities to the current identity |

Do not treat these as cloud-native safety controls. Provider/API deletion
protection, backups, retention locks, and traffic failover remain separate.

### Open `deletedWith` Replacement Hazard

As of July 2026, pulumi/pulumi#23817 reports that a resource marked
`deletedWith` can become a ghost in state when its target is replaced. If the
dependent's inputs are byte-identical, the engine may not replace it; the cloud
deletes it as a cascade, but Pulumi reports success and retains its state entry.
A refresh followed by another update is required to recover.

Until the issue is fixed in the deployed CLI:

- Do not rely on `deletedWith` alone for critical cascade-deleted dependents.
- Refresh and health-check dependents after replacing the target.
- Model explicit replacement when the dependent must be recreated.

## Aliases Are Combinatorial

Parent aliases are inherited by children. If both parent and child have aliases,
the engine computes combinations through the hierarchy. This is powerful but can
make broad component refactors difficult to reason about.

Safe refactor sequence:

1. Export the pre-refactor URNs.
2. Add one structural move at a time.
3. Use explicit old URNs for ambiguous multi-axis moves.
4. Preview every deployed stack, not only a new test stack.
5. Keep aliases until every stack has rolled forward.

Changing provider family is not proven safe merely by a type alias. Providers
can use different IDs, schemas, and CRUD semantics; treat it as ownership
migration unless provider documentation proves compatible state.

## Provider Upgrades Need Diff Canaries

Provider upgrades can introduce broad change without any source edit: new
defaults, corrected force-new markers, new flattening, new import ID parsing,
or upstream API-client changes.

Run upgrades as their own change:

1. Read Pulumi provider and upstream provider release notes.
2. Identify force-new/default/import changes for used resource types.
3. Preview a representative stack with a live refresh.
4. Compare normalized state before and after.
5. Canary one low-blast-radius stack.
6. Hold the version if unexplained replacements or permadiffs appear.

Do not solve an upgrade permadiff with `ignoreChanges` until the upstream schema,
bridge mapping, provider state upgrader, and cloud response have been checked.

## Incident Triage Search Order

For an unexplained Pulumi behavior, search in this order:

1. Current Pulumi CLI release notes.
2. `pulumi/pulumi` issues for engine/checkpoint/codegen behavior.
3. The Pulumi provider issues and releases.
4. `pulumi-terraform-bridge` if the provider is bridged.
5. The upstream Terraform provider and generator repository.
6. The cloud API release notes and known issues.

Issue reports are leads, not universal truth. Match version, resource type,
provider generation, platform, and reproduction before applying a workaround.

## Source Links

- https://github.com/pulumi/pulumi/releases/tag/v3.254.0
- https://github.com/pulumi/pulumi/releases/tag/v3.252.0
- https://github.com/pulumi/pulumi/issues/14836
- https://github.com/pulumi/pulumi/issues/23817
- https://github.com/pulumi/pulumi/issues/17131
- https://github.com/pulumi/pulumi-terraform-bridge
- https://www.pulumi.com/docs/iac/concepts/state-and-backends/
- https://www.pulumi.com/docs/iac/concepts/resources/options/ignorechanges/
- https://www.pulumi.com/docs/iac/concepts/resources/options/aliases/
- https://www.pulumi.com/docs/iac/cli/commands/pulumi_import/
- https://www.pulumi.com/docs/iac/cli/commands/pulumi_refresh/
