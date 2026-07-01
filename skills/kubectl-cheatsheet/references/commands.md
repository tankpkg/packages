# Kubectl Commands

Sources: Kubernetes official kubectl documentation, kubectl command reference, Kubernetes task documentation, common operator workflows from production Kubernetes usage

Covers: high-frequency kubectl commands organized by inspect, debug, mutate, rollout, namespace management, selectors, output shaping, and common resource types.

## Core Read Commands

| Task | Command |
|-----|---------|
| list pods in current namespace | `kubectl get pods` |
| list pods in all namespaces | `kubectl get pods -A` |
| wide pod output | `kubectl get pods -o wide` |
| get deployments | `kubectl get deploy` |
| get services | `kubectl get svc` |
| get nodes | `kubectl get nodes` |
| get namespaces | `kubectl get ns` |

## Describe and Inspect

| Task | Command |
|-----|---------|
| inspect pod details | `kubectl describe pod <pod> -n <ns>` |
| inspect deployment | `kubectl describe deploy <name> -n <ns>` |
| inspect node | `kubectl describe node <node>` |
| inspect service | `kubectl describe svc <name> -n <ns>` |

Use `describe` when `get` is too shallow and you need events, conditions, or container state.

## Logs

| Task | Command |
|-----|---------|
| logs from one pod | `kubectl logs <pod> -n <ns>` |
| follow logs | `kubectl logs -f <pod> -n <ns>` |
| previous crashed container logs | `kubectl logs --previous <pod> -n <ns>` |
| specific container in multi-container pod | `kubectl logs <pod> -c <container> -n <ns>` |
| logs by label selector | `kubectl logs -l app=myapp -n <ns>` |

## Exec and Port Forward

| Task | Command |
|-----|---------|
| shell into pod | `kubectl exec -it <pod> -n <ns> -- sh` |
| bash into pod | `kubectl exec -it <pod> -n <ns> -- bash` |
| run one command | `kubectl exec <pod> -n <ns> -- env` |
| port-forward pod | `kubectl port-forward pod/<pod> 8080:80 -n <ns>` |
| port-forward service | `kubectl port-forward svc/<svc> 8080:80 -n <ns>` |

## Apply, Delete, Diff

| Task | Command |
|-----|---------|
| apply manifest | `kubectl apply -f file.yaml` |
| apply directory | `kubectl apply -f k8s/` |
| dry-run client | `kubectl apply -f file.yaml --dry-run=client` |
| diff before apply | `kubectl diff -f file.yaml` |
| delete manifest | `kubectl delete -f file.yaml` |
| delete pod | `kubectl delete pod <pod> -n <ns>` |

Prefer `diff` and dry-run before large changes in live clusters.

## Rollouts and Scale

| Task | Command |
|-----|---------|
| check rollout status | `kubectl rollout status deploy/<name> -n <ns>` |
| rollout history | `kubectl rollout history deploy/<name> -n <ns>` |
| restart deployment | `kubectl rollout restart deploy/<name> -n <ns>` |
| undo rollout | `kubectl rollout undo deploy/<name> -n <ns>` |
| scale deployment | `kubectl scale deploy/<name> --replicas=3 -n <ns>` |

## Resource Metrics

| Task | Command |
|-----|---------|
| pod CPU/memory | `kubectl top pods -n <ns>` |
| node CPU/memory | `kubectl top nodes` |

Requires metrics server or equivalent metrics pipeline.

## Namespace Handling

| Task | Command |
|-----|---------|
| list namespaces | `kubectl get ns` |
| create namespace | `kubectl create ns <name>` |
| target namespace in command | `-n <ns>` |
| set default namespace in context | `kubectl config set-context --current --namespace=<ns>` |

Namespace mistakes are one of the most common kubectl operator mistakes.

## ConfigMaps and Secrets

| Task | Command |
|-----|---------|
| get configmaps | `kubectl get configmap -n <ns>` |
| describe configmap | `kubectl describe configmap <name> -n <ns>` |
| get secrets | `kubectl get secret -n <ns>` |
| describe secret metadata | `kubectl describe secret <name> -n <ns>` |
| decode secret key | `kubectl get secret <name> -n <ns> -o jsonpath='{.data.key}' | base64 -d` |

Be cautious with decoded secrets in shell history and logs.

## Selectors and Filtering

| Need | Pattern |
|-----|---------|
| label selector | `-l app=myapp` |
| multiple label filters | `-l app=myapp,env=prod` |
| field selector | `--field-selector status.phase=Running` |
| specific output columns | `-o custom-columns=...` |

## Output Shaping

| Task | Command |
|-----|---------|
| YAML output | `kubectl get pod <pod> -o yaml` |
| JSON output | `kubectl get pod <pod> -o json` |
| JSONPath | `kubectl get pod <pod> -o jsonpath='{.status.phase}'` |
| name only | `kubectl get pods -o name` |

## Debugging Flow

1. `kubectl get` to see status quickly
2. `kubectl describe` to inspect conditions/events
3. `kubectl logs` and `--previous` for runtime failures
4. `kubectl exec` if deeper inspection is safe/needed

## Common Operator Tasks

| Problem | Command path |
|--------|--------------|
| pod crash loop | `get pods` → `describe pod` → `logs --previous` |
| deployment not updating | `rollout status` → `describe deploy` |
| service not reachable | `get svc` → `describe svc` → `get endpoints` |
| node pressure | `top nodes` → `describe node` |

## Safety Heuristics

| Rule | Why |
|-----|-----|
| prefer read commands first | avoid accidental mutation |
| include namespace explicitly | reduce targeting mistakes |
| use selectors carefully | avoid broad accidental matches |
| diff and dry-run before apply when risk is non-trivial | safer rollout |

## Output and Selector Questions

1. Do I need one object, many objects, or just one field?
2. Am I in the right namespace/context?
3. Would `-o wide`, `yaml`, or `jsonpath` answer this faster than another command?

## Common Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| forgetting namespace | wrong target set | add `-n` or set context |
| deleting by broad selector carelessly | accidental blast radius | inspect with `get` first |
| only looking at `get` output | misses events/details | use `describe` |
| ignoring `--previous` logs | hides crash-loop root cause | check prior container logs |

## Quick Reference by Resource

| Resource | Read | Debug | Mutate |
|---------|------|-------|--------|
| pods | `get pods` | `describe`, `logs`, `exec` | `delete pod` |
| deployments | `get deploy` | `describe`, `rollout status` | `apply`, `scale`, `rollout restart` |
| services | `get svc` | `describe svc`, endpoints | `apply` |
| nodes | `get nodes` | `describe node`, `top nodes` | cordon/drain workflows |
| configmaps/secrets | `get`, `describe` | inspect keys/data carefully | `apply` |

## Final Operator Checklist

- [ ] namespace/context is correct before mutating
- [ ] read and debug commands precede write commands during incidents
- [ ] selectors and output shaping are used intentionally
- [ ] rollout and scale commands are followed by status checks
- [ ] secret inspection is handled carefully

## Context and Cluster Safety

| Task | Command |
|-----|---------|
| show current context | `kubectl config current-context` |
| list contexts | `kubectl config get-contexts` |
| switch context | `kubectl config use-context <name>` |

Wrong-cluster mistakes are often more dangerous than wrong-command mistakes.

## Deployment and ReplicaSet Inspection

| Task | Command |
|-----|---------|
| list replica sets | `kubectl get rs -n <ns>` |
| describe replica set | `kubectl describe rs <name> -n <ns>` |
| list deployments wide | `kubectl get deploy -o wide -n <ns>` |

## Stateful and Batch Workloads

| Resource | Command |
|---------|---------|
| statefulsets | `kubectl get sts -n <ns>` |
| jobs | `kubectl get jobs -n <ns>` |
| cronjobs | `kubectl get cronjobs -n <ns>` |

Even if your day job is mostly deployments and pods, these resources show up in real incidents.

## Events and Endpoint Checks

| Task | Command |
|-----|---------|
| recent events in namespace | `kubectl get events -n <ns> --sort-by=.metadata.creationTimestamp` |
| get endpoints | `kubectl get endpoints -n <ns>` |
| describe endpoints | `kubectl describe endpoints <name> -n <ns>` |

Events often explain failures faster than reading YAML first.

## Node Operations

| Task | Command |
|-----|---------|
| cordon node | `kubectl cordon <node>` |
| drain node | `kubectl drain <node> --ignore-daemonsets --delete-emptydir-data` |
| uncordon node | `kubectl uncordon <node>` |

Use node mutation commands cautiously and deliberately.

## Resource Edit and Patch

| Task | Command |
|-----|---------|
| edit live resource | `kubectl edit deploy/<name> -n <ns>` |
| patch resource | `kubectl patch deploy/<name> -p '{...}' -n <ns>` |

Prefer declarative source-of-truth changes where possible; live edits are powerful but easy to forget in GitOps-style environments.

## Label and Annotation Operations

| Task | Command |
|-----|---------|
| add label | `kubectl label pod <pod> key=value -n <ns>` |
| add annotation | `kubectl annotate pod <pod> key=value -n <ns>` |
| overwrite label | add `--overwrite` |

## Output Recipes

| Need | Example |
|-----|---------|
| pod names only | `kubectl get pods -o name` |
| pod IPs via jsonpath | `kubectl get pods -o jsonpath='{.items[*].status.podIP}'` |
| custom columns | `kubectl get pods -o custom-columns=NAME:.metadata.name,PHASE:.status.phase` |

## Namespace Debugging Questions

1. Am I looking in the correct namespace?
2. Is the object cluster-scoped or namespaced?
3. Is my context targeting the intended cluster?

These three questions prevent a huge amount of wasted kubectl time.

## Mutation Review Heuristics

| Before mutating | Why |
|----------------|-----|
| run `get` first | confirm target scope |
| use selectors carefully | avoid wide blast radius |
| inspect rollout/status after change | validate effect |

## Practical Incident Flow

1. confirm context/namespace
2. `get` object list and status
3. `describe` the failing object
4. inspect logs or events
5. only then mutate if needed

## Common kubectl Smells

| Smell | Why it matters |
|------|----------------|
| using `delete` before understanding state | hides root cause |
| overusing live edits | config drift from source control |
| no selectors or namespace flags | dangerous ambiguity |

## Final Review Questions

1. Is this a read/debug task or a desired-state change?
2. Do I know exactly which resources I’m targeting?
3. Am I using output shaping to avoid extra commands?

## Operator Smells

| Smell | Why it matters |
|------|----------------|
| context/namespace not checked before mutation | cluster blast radius risk |
| relying on delete/restart before understanding state | hides root cause |
| skipping `describe` and events | misses the fastest diagnosis path |
