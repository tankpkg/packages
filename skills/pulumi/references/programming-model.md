# Pulumi Programming Model

Sources: Pulumi documentation on Inputs and Outputs, resource dependencies, functions, language runtimes, and programming model; official language SDK references

Covers: program evaluation, `Input` and `Output`, dependency inference, transformations, invoke functions, language selection, and common asynchronous-value failures.

## Two-Phase Reasoning

A Pulumi program runs as ordinary language code while registering a desired
resource graph with the deployment engine. Providers then create, read, update,
or delete resources according to the engine's plan.

Distinguish:

| Time | What is available |
|---|---|
| Program evaluation | Config, ordinary values, resource declarations |
| Deployment | Provider-computed IDs, endpoints, status, and outputs |

Values computed by providers cannot be treated as synchronous values during
program evaluation. Pulumi represents them as `Output<T>`.

## Input and Output Contract

An input accepts either a known value or an output that will resolve later.
An output carries a future value plus dependency and secret metadata.

Default rules:

1. Pass an output directly when a resource input accepts it.
2. Use interpolation helpers for string composition.
3. Use `apply` only when computation cannot be expressed directly.
4. Keep resource construction outside `apply` unless the resource truly exists
   only conditionally on a resolved value.
5. Never block waiting for an output.

TypeScript example:

```typescript
const bucket = new gcp.storage.Bucket("assets");
const url = pulumi.interpolate`gs://${bucket.name}`;
export const bucketUrl = url;
```

Python example:

```python
bucket = gcp.storage.Bucket("assets")
bucket_url = bucket.name.apply(lambda name: f"gs://{name}")
pulumi.export("bucket_url", bucket_url)
```

## Dependency Inference

Passing one resource's output into another resource's input creates an implicit
dependency. Prefer this dataflow because it is precise and refactor-friendly.

Use `dependsOn` only for a real ordering constraint with no data edge, such as
an API enablement resource that must complete before another provider call.
Overusing explicit dependencies serializes updates and hides the actual model.

| Situation | Mechanism |
|---|---|
| Consumer needs producer ID | Pass the producer output |
| Provider lacks a usable data property but order matters | `dependsOn` |
| Parent should own child lifecycle and URN | `parent` |
| Separate stack provides value | Stack reference output |

## Known and Unknown Values

During preview, outputs may be unknown because no provider call has created the
resource. Code inside `apply` may not run during preview. Do not put essential
registration side effects, file writes, network calls, or validation solely in
an `apply` callback.

An `apply` callback should be:

- deterministic
- side-effect free
- small
- safe when skipped during preview
- free of secret logging

## Invoke Functions

Provider functions read data without creating a managed custom resource.
Choose the output-aware form when arguments contain outputs. Use invokes for
lookups, not as a substitute for managing infrastructure that Pulumi should own.

| Need | Choice |
|---|---|
| Read an existing value only | Provider invoke/get function |
| Adopt lifecycle ownership | Resource import |
| Reference another Pulumi resource | Resource output |
| Read another stack contract | Stack reference |

Provider reads can make preview depend on live API availability and credentials.
Keep them explicit and avoid repeating the same lookup in loops.

## Language Selection

The infrastructure model is shared, but ergonomics differ.

| Language | Strength | Watch for |
|---|---|---|
| TypeScript | Rich package ecosystem, concise output composition | Promise and `Output` confusion |
| Python | Familiar automation syntax | Runtime type errors without strict checks |
| Go | Explicit errors and data flow | Verbose output helpers and pointer types |
| C# | Strong typing and enterprise integration | Async and `Output<T>` distinction |
| Java | JVM integration | Generated builder conventions |
| YAML | Small declarative programs | Limited abstraction and complex logic |

Use the team's strongest maintained language. Do not choose a language because
one migration generator emits it if the owning team cannot operate it.

## Program Purity

Pulumi evaluates the program during preview and update. Uncontrolled side
effects make those operations diverge.

Avoid:

- current-time resource names
- random values outside managed random resources
- unversioned network downloads
- shell commands that mutate cloud resources
- filesystem state used as hidden configuration
- environment variables that are not documented deployment inputs

If external data must affect infrastructure, model and version it as config,
a provider data source, a dynamic provider with a clear lifecycle, or a separate
build artifact.

## Conditional Resources and Loops

Use ordinary language control flow only with values known during evaluation,
usually config. Give loop-created resources stable logical names from durable
keys rather than list indexes.

```typescript
for (const [name, spec] of Object.entries(services)) {
  new ServiceComponent(name, spec);
}
```

Changing map keys changes resource identity. If a key must change, add aliases.

## Errors and Diagnostics

Fail early for invalid program inputs. Include the config key or resource role
in errors without exposing secrets. Provider errors often identify a resource
URN; trace it to the declaration and inspect the provider inputs shown in the
detailed preview.

Debug in layers:

1. Language compile/type/lint errors.
2. Pulumi program registration errors.
3. Preview diff and unknown values.
4. Provider schema or authentication errors.
5. Cloud API operation errors.

## Review Checklist

- Outputs are passed as inputs instead of synchronously unwrapped.
- `apply` callbacks are pure and preview-safe.
- Resource names use stable keys.
- Dataflow expresses dependencies where possible.
- Explicit dependencies have a documented provider/order reason.
- Invokes are reads, not accidental unmanaged ownership.
- Program evaluation has no hidden mutation.
- Exports form a small consumer contract.

## Source Links

- https://www.pulumi.com/docs/iac/concepts/inputs-outputs/
- https://www.pulumi.com/docs/iac/concepts/resources/
- https://www.pulumi.com/docs/iac/concepts/resources/options/dependson/
- https://www.pulumi.com/docs/iac/concepts/functions/
- https://www.pulumi.com/docs/iac/languages-sdks/
