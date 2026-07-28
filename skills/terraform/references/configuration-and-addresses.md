# Configuration and Resource Addresses

Sources: HashiCorp Terraform language, expressions, resource addressing, style, variables, outputs, and meta-argument documentation

Covers: HCL data flow, types, variables, locals, outputs, dependencies, `for_each`, `count`, lifecycle, and stable addresses.

## Configuration Model

Terraform evaluates configuration into a dependency graph. References between
resources create edges; file order does not. Split files for readability, not
execution order.

| Construct | Use |
|---|---|
| Variable | Typed caller input with description and validation |
| Local | Named deterministic derivation |
| Data source | Read an externally owned object |
| Resource | Declare lifecycle ownership |
| Output | Publish a minimal root/module contract |
| Check/precondition | Assert an operational invariant |

## Variables

Declare precise object, map, set, tuple, number, bool, or string types. Add
nullable/default semantics intentionally and validate domain constraints near
the input boundary.

```hcl
variable "environment" {
  type        = string
  description = "Deployment environment name."
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production"
  }
}
```

Avoid `type = any` unless the module truly passes opaque data through. Loose
types move errors into provider execution and make module contracts unclear.

## Dependencies

Prefer expression references:

```hcl
network = google_compute_network.main.id
```

Use `depends_on` only when a hidden behavior dependency has no value edge, such
as API enablement that must precede a provider call. Broad module dependencies
serialize graphs and produce more unknown values.

## Stable Collection Identity

`for_each` addresses instances by key; `count` addresses by index.

```hcl
resource "google_service_account" "workload" {
  for_each   = var.workloads
  account_id = each.key
}
```

Use keys that survive display-name and ordering changes. Renaming a key changes
the address; add a `moved` block when identity should remain.

| Data shape | Pattern |
|---|---|
| Named workloads | `for_each = map` |
| Unique unordered names | `for_each = toset(...)` |
| Truly indexed replicas | `count` |
| Optional singleton | Conditional `for_each` or count with known address tradeoff |

## Outputs

Export consumer capabilities such as IDs, endpoints, and names. Do not expose
whole resources or sensitive values without a real consumer need.

Mark sensitive outputs, but remember sensitivity hides display; state can still
contain the value. Protect the backend accordingly.

## Lifecycle

| Setting | Use | Risk |
|---|---|---|
| `prevent_destroy` | Block accidental destroy of critical resources | Requires explicit removal for legitimate deletion |
| `create_before_destroy` | Reduce replacement downtime | Needs parallel-name/quota capacity |
| `ignore_changes` | External controller owns named fields | Can hide security or configuration drift |
| `replace_triggered_by` | Couple replacement to explicit dependency | Expands blast radius |

Use `ignore_changes` only with a named external owner and narrow attributes.
Refreshing state does not make ignored drift harmless.

## Address Changes

These change a resource address:

- resource block label
- module path
- `for_each` key
- `count` index
- resource type

Moving source between `.tf` files does not. Preserve deliberate identity changes
with `moved` blocks and review the plan for move rather than destroy/create.

## Determinism

Avoid timestamps, unstable set/list conversions, mutable remote files, and shell
side effects in configuration. Pin external module/provider versions and make
environment inputs explicit.

## Review Checklist

- Variables are typed, described, and validated.
- References express dependencies.
- Collection keys are durable.
- Outputs are minimal.
- Lifecycle rules name the operational reason.
- Address changes have `moved` blocks.
- Sensitive values are not printed or committed.
- Full plan has no unexplained replacement or destroy.

## Source Links

- https://developer.hashicorp.com/terraform/language
- https://developer.hashicorp.com/terraform/language/values/variables
- https://developer.hashicorp.com/terraform/language/values/outputs
- https://developer.hashicorp.com/terraform/language/meta-arguments/for_each
- https://developer.hashicorp.com/terraform/cli/state/resource-addressing
