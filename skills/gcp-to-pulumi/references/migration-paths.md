# Migration Path Selection

Sources: Pulumi documentation on importing existing infrastructure, CLI import, import resource option, program-first import, migration converters, and Terraform migration

Covers: migration-path decisions, direct and bulk import, Terraform-aware adoption, read-only references, unsupported resources, and generated-code review.

## Separate Code Conversion from Ownership Transfer

Code conversion creates a draft Pulumi program. Import associates existing
provider objects with Pulumi state. A migration may need either or both.

| Existing situation | Code needed | State action |
|---|---|---|
| Manual GCP resources | Write/generate Pulumi declarations | Import provider IDs |
| Terraform code and reliable state | Convert/rewrite declarations | Adopt from tfstate |
| Terraform code without reliable state | Use conversion as reference | Directly import live IDs |
| Deployment Manager or scripts | Translate intent manually | Directly import live IDs |
| Shared resource owned elsewhere | No managed declaration | Read/invoke or stack contract |

Do not run converted code against an empty Pulumi stack and assume Pulumi will
discover existing resources. It will plan creates unless resources are imported.

## CLI Import

Use for a small number of resources or for learning the provider's generated
declaration.

```bash
pulumi import gcp:storage/bucket:Bucket assets BUCKET_NAME \
  --stack org/project/production \
  --preview-only
```

Then run the actual reviewed import and capture generated code with the CLI's
output option where appropriate. Check the current CLI help for exact flags.

CLI import normally protects imported resources by default. Preserve protection
for critical resources until the ownership transfer is proven.

## Resource Import Option

Use program-first import when code structure, logical names, parents, explicit
providers, and components must be designed before adoption.

TypeScript shape:

```typescript
const bucket = new gcp.storage.Bucket("assets", {
  name: "existing-assets",
  location: "EU",
}, {
  import: "existing-assets",
  protect: true,
});
```

Match live immutable and defaulted inputs. An import error often means the code
does not describe the object the provider read, not that the object is absent.

## Program-First Bulk Import

For a graph, write the target program first and ask preview to generate an
import file for resources it would otherwise create.

```bash
pulumi preview --import-file import.json
```

Review the generated entries, add canonical provider IDs, and import with the
documented CLI flow. This retains parent and provider relationships from the
program and reduces flat-import reparenting later.

Bulk import checklist:

1. Program uses final logical names and parents.
2. Explicit providers target correct GCP projects.
3. Every import ID comes from the Registry and live API evidence.
4. Parent/dependency resources appear in a safe wave.
5. Import file is reviewed as migration data.
6. Generated code is reconciled into the maintained program.
7. Full preview reaches steady state.

## Terraform-Aware Adoption

When reliable `.tfstate` exists, use Pulumi's Terraform migration commands to
preserve the mapping between Terraform addresses and provider IDs. Current
Pulumi guidance supports `pulumi convert --from terraform` for HCL and
`pulumi import --from terraform` for state adoption.

Treat converter output as a draft:

- run language formatter and type checks
- resolve unsupported constructs and diagnostics
- verify provider versions and aliases
- compare every state address to a Pulumi resource
- preserve explicit physical names
- preview without replacements

See `terraform-to-pulumi.md` for the full sequence.

## Read Instead of Import

Use provider lookup functions when this stack needs metadata but another system
owns lifecycle. Document the owner and contract.

Reads are appropriate for:

- organization-owned shared VPC
- centrally managed DNS zone
- pre-existing project owned by a landing-zone platform
- externally managed secret version
- service-generated resource

A read does not protect or control the resource. Runtime dependencies still
need monitoring and an ownership agreement.

## Unsupported Resources

Do not force an unsupported Google API object into a vaguely similar resource
type. Options, in order:

1. Keep the existing owner and read outputs.
2. Check the other official Pulumi Google provider family.
3. Use a reviewed provider package that accurately models lifecycle.
4. Build a dynamic/provider bridge only with a clear CRUD and import contract.
5. Defer the resource from migration.

Using command resources or shell scripts to mutate cloud APIs hides diffs and
usually cannot provide safe import/update/delete semantics.

## Generated Code Review

Generated declarations capture provider-read properties, not architectural
intent. Normalize only after import is stable.

Review for:

- plaintext secrets
- computed/output-only fields copied as inputs
- provider defaults that should stay explicit during migration
- obsolete fields
- unstable generated names
- missing parent or provider options
- IAM resources with authoritative semantics
- references represented as raw strings instead of resource outputs

## Path Gate

Before execution, every resource has one chosen path, one intended Pulumi URN,
one provider ID, and one current/target owner. Mixed or undecided rows remain
blocked.

## Source Links

- https://www.pulumi.com/docs/iac/guides/migration/import/
- https://www.pulumi.com/docs/iac/cli/commands/pulumi_import/
- https://www.pulumi.com/docs/iac/concepts/resources/options/import/
- https://www.pulumi.com/docs/iac/guides/migration/migrating-to-pulumi/from-terraform/
- https://www.pulumi.com/docs/iac/cli/commands/pulumi_convert/
