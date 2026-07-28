# Providers and Modules

Sources: HashiCorp provider requirements, dependency lockfile, provider configuration, standard module structure, composition, and module-development documentation

Covers: provider source/version declarations, lockfiles, aliases, authentication, module contracts, composition, and publishing boundaries.

## Provider Contract

Every module declares required provider source and compatible minimum version.
The root module also constrains operational compatibility and commits the lock
file so installations select reviewed provider builds.

```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}
```

Run `terraform init -upgrade` only in an isolated dependency-upgrade change.
Provider upgrades can alter defaults, schemas, import parsing, and replacement
behavior.

## Lockfile

Commit `.terraform.lock.hcl` for root configurations. Review version and checksum
changes. Reusable modules declare compatible constraints but do not own the
caller's selected build.

Do not commit `.terraform/`; it contains downloaded plugins and local metadata.

## Provider Configuration

Configure credentials and target account/project/region in root modules. Child
modules receive provider configurations from callers and declare aliases they
accept.

| Scenario | Pattern |
|---|---|
| One target | Default provider in root |
| Multiple GCP projects | Aliased provider per project |
| Reusable module | Declare requirement; caller passes provider |
| CI | Workload identity/OIDC, not static keys |

Do not hide target project selection in ambient CLI defaults. Plans and imports
must identify the intended provider configuration.

## Module Contract

A module should model one deployable capability with:

- typed, validated inputs
- sensible but non-surprising defaults
- minimal outputs
- no embedded provider credentials
- explicit provider requirements
- stable internal addresses
- tests for durable behavior

Prefer composition at the root over deep modules calling sibling modules.
Callers can wire outputs to inputs and retain control over architecture.

## Structure

```text
module/
  main.tf
  variables.tf
  outputs.tf
  versions.tf
  README.md
  tests/
  examples/
```

The root is the public module. Nested modules under `modules/` should remain
composable; document any intended public nested modules.

## Versioning

Pin published module versions in callers. Use semantic releases and explain
state/address migrations. A source ref such as a moving branch makes the same
configuration resolve to different infrastructure logic over time.

## Provider Aliases

Aliases are part of module wiring. Declare `configuration_aliases` in reusable
modules, then pass explicit mappings from the root. Import commands and blocks
must resolve the same alias that will manage the object afterward.

## Module Refactoring

Moving resources into or between modules changes addresses. Add `moved` blocks
from old to new addresses in the configuration version that performs the move.
Keep migration blocks until all states using the module have upgraded.

## Anti-Patterns

| Pattern | Failure |
|---|---|
| Provider block inside reusable child | Callers cannot safely alias/override targets |
| One module wrapping one resource without policy | Adds indirection without capability |
| Mega-module with dozens of switches | Huge state/blast radius and invalid combinations |
| Outputs exposing every attribute | Couples callers to implementation |
| Broad version ranges in root | Surprise upgrades |
| Credentials in variables/tfvars | Leak into files, logs, or state |

## Review Checklist

- Every provider has an explicit source and constraint.
- Root lockfile is committed.
- Provider upgrade is isolated.
- Root owns authentication and aliases.
- Modules expose capabilities and minimal outputs.
- Module sources are immutable/versioned.
- Address moves have migration blocks.
- Provider targets are explicit in plan and import workflows.

## Source Links

- https://developer.hashicorp.com/terraform/language/providers/requirements
- https://developer.hashicorp.com/terraform/language/files/dependency-lock
- https://developer.hashicorp.com/terraform/language/modules/develop/structure
- https://developer.hashicorp.com/terraform/language/modules/develop/composition
- https://developer.hashicorp.com/terraform/language/modules/develop/providers
