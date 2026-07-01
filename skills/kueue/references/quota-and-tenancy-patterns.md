# Quota and Tenancy Patterns

Sources: Kueue documentation (kueue.sigs.k8s.io/docs/concepts/cluster_queue/, /cohort/, /tasks/manage/administer_cluster_quotas/, /concepts/fair_sharing/), kubernetes-sigs/kueue v1beta1 + v1beta2 API spec, Kueue KEPs.

Covers: the quota math (nominalQuota / borrowingLimit / lendingLimit / effectiveQuota), single-tenant and multi-tenant topologies (equal-share with borrowing, tiered priority, reserved + shared pool, strict isolation), hierarchical cohorts, flavor patterns (spot+on-demand, GPU classes, cross-zone), preemption design, namespace selectors, RBAC, cost showback, anti-patterns, and a safe migration playbook.

## Quota Math

Three knobs per `(ClusterQueue, flavor, resource)`:

| Field | Meaning | Default |
|-------|---------|---------|
| `nominalQuota` | Guaranteed amount this CQ can always use | required |
| `borrowingLimit` | Max additional amount from cohort siblings | nil = unlimited within cohort |
| `lendingLimit` | Max amount this CQ exposes for siblings to borrow | nil = all unused nominal |

Effective ceiling at any moment: `nominalQuota + min(borrowingLimit, sum-of-siblings-lendable)`.

Reservation amount = sum of resource requests across admitted Workloads. Borrowed portion = `max(0, reservation - nominalQuota)`.

| Symptom | Likely misconfiguration |
|---------|------------------------|
| Workloads admit but consume way more than expected | `borrowingLimit` is nil → unbounded sibling consumption |
| Sibling CQs starved when this CQ is idle | `lendingLimit` is set too low (or 0) |
| Big workload never admits despite cohort having capacity | Cohort doesn't have a *single* sibling with enough lendable for the request — cohorts pool but each request needs a single donor's lendable to fit |
| Workload admits with mixed flavors that wreck NCCL | Resources spread across flavors when they should be in one resourceGroup |

### Resource groups and flavor fungibility

A `resourceGroup` ties resources together so they come from the same flavor. Most useful for GPU + paired CPU + memory:

```yaml
resourceGroups:
- coveredResources: [cpu, memory, "nvidia.com/gpu"]
  flavors:
  - { name: gpu-h100, resources: [...] }
  - { name: gpu-a100, resources: [...] }
```

When admission needs all three resources, they must come from the *same* flavor entry — Kueue won't pick CPU from h100 and GPU from a100. To allow that, put them in separate resourceGroups.

`flavorFungibility` controls fall-through. The defaults (`whenCanBorrow: Borrow`, `whenCanPreempt: TryNextFlavor`) mean: prefer borrowing over fallback, but try next flavor before resorting to preemption.

## Single-Tenant Pattern

Smallest viable setup. One namespace, one team, one CQ, no cohort.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: default }
spec: {}
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: only-cq }
spec:
  namespaceSelector: {}                            # any namespace
  resourceGroups:
  - coveredResources: [cpu, memory]
    flavors:
    - name: default
      resources:
      - { name: cpu,    nominalQuota: "96" }      # ≈ cluster capacity − system overhead
      - { name: memory, nominalQuota: "384Gi" }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata: { name: default, namespace: default }
spec: { clusterQueue: only-cq }
```

Use this on dev clusters or single-team production. No cohort means no borrowing complexity to reason about.

## Multi-Team Patterns

### Pattern A — Equal share with borrowing

Four teams, 100 GPUs total. Each gets 25 nominal, can borrow up to 25 more.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata: { name: teams }
---
# repeat for team-b, team-c, team-d with name + namespaceSelector changes
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: team-a-cq }
spec:
  cohort: teams
  namespaceSelector: { matchLabels: { team: a } }
  resourceGroups:
  - coveredResources: ["nvidia.com/gpu"]
    flavors:
    - name: gpu
      resources:
      - { name: "nvidia.com/gpu", nominalQuota: "25", borrowingLimit: "25" }
```

Net effect: each team is guaranteed 25, can burst to 50 when neighbors are idle. Add `WorkloadPriorityClass` on top if you want intra-team prioritization.

### Pattern B — Tiered priority (production preempts research)

Same cohort, different priorities + preemption policy.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata: { name: prod-research }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: prod-cq }
spec:
  cohort: prod-research
  namespaceSelector: { matchLabels: { tier: production } }
  resourceGroups:
  - coveredResources: [cpu]
    flavors:
    - { name: default, resources: [{ name: cpu, nominalQuota: "60" }] }
  preemption:
    reclaimWithinCohort: Any                # take back nominal from anyone
    withinClusterQueue: LowerPriority
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: research-cq }
spec:
  cohort: prod-research
  namespaceSelector: { matchLabels: { tier: research } }
  resourceGroups:
  - coveredResources: [cpu]
    flavors:
    - { name: default, resources: [{ name: cpu, nominalQuota: "40", borrowingLimit: "60" }] }
  preemption:
    withinClusterQueue: LowerPriority
    # no reclaimWithinCohort → research never preempts production
```

Combine with two `WorkloadPriorityClass` objects (`prod-high: 1000`, `research-low: 100`). Research can borrow up to 60 extra (using prod's idle capacity), but loses it the moment prod has a Workload that can't fit its nominal.

### Pattern C — Reserved + shared burst pool

Each team has a dedicated CQ with small nominal; a separate "shared pool" CQ holds most of the cluster, also in the cohort, that everyone borrows from.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata: { name: with-burst }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: team-a-reserved }
spec:
  cohort: with-burst
  namespaceSelector: { matchLabels: { team: a } }
  resourceGroups:
  - coveredResources: [cpu]
    flavors:
    - { name: default, resources: [{ name: cpu, nominalQuota: "20", borrowingLimit: "60" }] }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: shared-burst }
spec:
  cohort: with-burst
  namespaceSelector:
    matchExpressions:
    - { key: team, operator: DoesNotExist }      # no team can submit directly here
  resourceGroups:
  - coveredResources: [cpu]
    flavors:
    - { name: default, resources: [{ name: cpu, nominalQuota: "60", lendingLimit: "60" }] }
```

Why use a "ghost" shared-burst CQ instead of putting capacity directly into a Cohort? Compatibility with older Kueue versions and clearer accounting. With hierarchical cohorts (v0.12+), the same effect can be achieved by setting `Cohort.spec.resourceGroups`.

### Pattern D — Strict isolation (no sharing)

When teams must not affect each other (regulatory, billing isolation):

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: team-a-isolated }
spec:                                          # no cohort field
  namespaceSelector: { matchLabels: { team: a } }
  resourceGroups:
  - coveredResources: [cpu]
    flavors:
    - { name: default, resources: [{ name: cpu, nominalQuota: "25" }] }
```

Tradeoff: idle quota is wasted. Use only when necessary.

## Hierarchical Cohort Pattern

Org → Department → Team. The Cohort CRD with `parentName` enables capacity to flow down through weighted shares.

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata: { name: company-root }
spec:
  resourceGroups:                              # root holds the company-wide pool
  - coveredResources: [cpu, "nvidia.com/gpu"]
    flavors:
    - name: default
      resources:
      - { name: cpu, nominalQuota: "1000" }
      - { name: "nvidia.com/gpu", nominalQuota: "64" }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata: { name: ml-platform }
spec:
  parentName: company-root
  fairSharing: { weight: "0.6" }               # 60% of root's borrowable
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: Cohort
metadata: { name: data-platform }
spec:
  parentName: company-root
  fairSharing: { weight: "0.4" }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: team-llm }
spec:
  cohort: ml-platform                          # joins ML dept cohort
  namespaceSelector: { matchLabels: { team: llm } }
  resourceGroups:
  - coveredResources: [cpu, "nvidia.com/gpu"]
    flavors:
    - name: default
      resources:
      - { name: cpu, nominalQuota: "0" }       # zero nominal — fully borrowing
      - { name: "nvidia.com/gpu", nominalQuota: "0" }
```

Quota cascades top-down: company-root holds the pool, ML dept claims 60%, teams within ML dept share that 60% by their own weights. Useful for organizations where capacity is allocated by org chart.

## Flavor Patterns

### Spot + on-demand fallback

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: spot }
spec:
  nodeLabels: { capacity-type: spot }
  tolerations:
  - { key: spot, operator: Equal, value: "true", effect: NoSchedule }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: on-demand }
spec:
  nodeLabels: { capacity-type: on-demand }
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: cost-optimized }
spec:
  resourceGroups:
  - coveredResources: [cpu, memory]
    flavors:
    - name: spot
      resources: [{ name: cpu, nominalQuota: "200" }, { name: memory, nominalQuota: "800Gi" }]
    - name: on-demand
      resources: [{ name: cpu, nominalQuota: "50" },  { name: memory, nominalQuota: "200Gi" }]
  flavorFungibility:
    whenCanBorrow: TryNextFlavor                # don't borrow spot — go to on-demand instead
```

Workloads tolerating the `spot` taint admit on the spot flavor first. When spot is full, fall through to on-demand. Workloads without the toleration skip the spot flavor entirely and only consider on-demand.

### GPU classes with fallback

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: any-gpu }
spec:
  resourceGroups:
  - coveredResources: [cpu, memory, "nvidia.com/gpu"]
    flavors:
    - { name: h100, resources: [{ name: cpu, nominalQuota: "32" }, { name: memory, nominalQuota: "128Gi" }, { name: "nvidia.com/gpu", nominalQuota: "8" }] }
    - { name: a100, resources: [{ name: cpu, nominalQuota: "64" }, { name: memory, nominalQuota: "256Gi" }, { name: "nvidia.com/gpu", nominalQuota: "16" }] }
    - { name: t4,   resources: [{ name: cpu, nominalQuota: "32" }, { name: memory, nominalQuota: "128Gi" }, { name: "nvidia.com/gpu", nominalQuota: "32" }] }
  flavorFungibility:
    whenCanBorrow: TryNextFlavor
    whenCanPreempt: TryNextFlavor
```

Workloads requesting "any GPU" admit on h100 first. Workloads with `nodeSelector: nvidia.com/gpu-product: A100` skip h100 and t4 because of the nodeLabel mismatch. Order the flavors by preference (most expensive/scarce first if you want to use them when available).

### Cross-zone for locality

One flavor per zone enforces zone-locality at admission time:

```yaml
- { name: zone-a, nodeLabels: { topology.kubernetes.io/zone: us-east-1a } }
- { name: zone-b, nodeLabels: { topology.kubernetes.io/zone: us-east-1b } }
- { name: zone-c, nodeLabels: { topology.kubernetes.io/zone: us-east-1c } }
```

Each ClusterQueue gets quota per zone. Workloads admit into one zone (no cross-zone egress). For finer hardware locality (rack/host), use Topology-Aware Scheduling instead.

## Preemption Design

Two patterns dominate:

**Production preempts research** — `WorkloadPriorityClass(prod=1000) > research(100)`, `prod-cq.preemption.reclaimWithinCohort: Any`. Already covered above in Pattern B.

**Within-team priority** — set `withinClusterQueue: LowerPriority` on each CQ. A team's `prod-online` Workloads (priority 1000) can preempt its own `nightly-batch` Workloads (priority 100) if both submit to the same CQ.

Combine with `borrowWithinCohort: { policy: LowerPriority, maxPriorityThreshold: 999 }` to allow a high-priority Workload to *both* preempt within its CQ *and* borrow from cohort siblings — the threshold prevents borrowing from killing other production work.

## Namespace Selectors and Tenancy

The standard pattern: one ClusterQueue per team, gated by namespace label.

```yaml
# Namespace setup
apiVersion: v1
kind: Namespace
metadata: { name: team-a, labels: { team: a, kueue.x-k8s.io/managed: "true" } }
---
# CQ matches the label
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: team-a-cq }
spec:
  namespaceSelector: { matchLabels: { team: a } }
  ...
```

Enable `LocalQueueDefaulting` so users in `team-a` namespace get a `default` LocalQueue auto-created pointing at `team-a-cq`. They no longer need to specify a queue label on every Job (Kueue assigns one by default).

The `managedJobsNamespaceSelector` (in Kueue Configuration) is *separate* — it controls which namespaces Kueue's Pod-derived integrations (`pod`, `deployment`, `statefulset`) operate on. Both should typically include the same set of team namespaces.

## Queue Admin RBAC

Two-tier model:

```yaml
# Cluster admin — manages quota objects
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata: { name: kueue-cluster-admin }
rules:
- { apiGroups: [kueue.x-k8s.io], resources: [clusterqueues, resourceflavors, cohorts, workloadpriorityclasses, admissionchecks], verbs: ["*"] }
---
# Namespace admin — creates LocalQueues only
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: kueue-namespace-admin, namespace: team-a }
rules:
- { apiGroups: [kueue.x-k8s.io], resources: [localqueues], verbs: ["*"] }
- { apiGroups: [kueue.x-k8s.io], resources: [workloads], verbs: [get, list, watch] }
```

Regular users only need permission to create their workload kinds (Jobs, RayJobs, etc.). The `kueue.x-k8s.io/queue-name` label is just a label — no special RBAC needed to set it.

## Cost Allocation and Showback

Aggregate Prometheus metrics by namespace:

```promql
# CPU-hours per namespace
sum by (namespace) (
  rate(kueue_cluster_queue_resource_usage{resource="cpu"}[1h])
) * 3600

# GPU-hours per ClusterQueue
sum by (cluster_queue) (
  rate(kueue_cluster_queue_resource_usage{resource="nvidia.com/gpu"}[1h])
) * 3600
```

For team-level chargeback, label your ClusterQueues consistently (`team`, `cost-center`) and join with cloud billing data. OpenCost can already attribute Pod-level cost to namespace; layering Kueue's per-CQ usage gives a "what was reserved vs what was spent" view.

## Anti-Patterns

| Anti-pattern | What goes wrong | Fix |
|--------------|-----------------|-----|
| Single giant CQ for the whole cluster | Loses per-team accountability and fairness | Split per team; use cohort to keep sharing |
| No cohort at all | Idle capacity wasted; no bursting | Group team CQs into a cohort |
| `borrowingLimit: nil` | One CQ can monopolize the whole cohort | Set explicit borrowingLimit |
| Same flavor for spot + on-demand | Can't differentiate hardware cost | Two ResourceFlavors with `flavorFungibility.whenCanBorrow: TryNextFlavor` |
| Aggressive preemption everywhere | Production stability suffers | Use `reclaimWithinCohort: LowerPriority` (not `Any`) at minimum |
| StrictFIFO with one giant Workload | Head-of-line blocks everyone | BestEffortFIFO unless strict ordering is a hard requirement |
| ResourceFlavor `nodeLabels` don't match any node | Workloads stay Inadmissible forever | Run `kubectl get nodes --show-labels` to verify exact label keys/values |
| `nominalQuota` exceeds cluster physical capacity | Workloads admit but Pods stay Pending | Set quota to actual schedulable capacity; use ProvisioningRequest for bursting |
| Mixing `pod` integration with system namespaces in `managedJobsNamespaceSelector` | kube-system Pods get queued; cluster breaks | Tighten selector to opt-in namespaces only |
| Forgetting `lendingLimit` when one team has 90% nominal | Other teams can't borrow because primary team rarely has unused capacity | Set explicit lendingLimit; rebalance nominal |

## Migration / Rollout Playbook

Adopting Kueue on a running cluster, in stages:

**Phase 1 — Install + observe (week 1)**
- Install Kueue with `manageJobsWithoutQueueName: false`
- Create one ResourceFlavor matching your most common node type
- Create one ClusterQueue with quota = current peak Job usage × 1.2
- Don't label any Jobs yet — observe scheduler logs

**Phase 2 — Pilot one namespace (week 2)**
- Pick one team's namespace; add `kueue.x-k8s.io/managed: "true"` label
- Create LocalQueue in that namespace
- Add `kueue.x-k8s.io/queue-name` label to that team's Jobs
- Watch metrics: admission latency, eviction rate, quota utilization

**Phase 3 — Multi-tenant (weeks 3-4)**
- Add more teams: one ClusterQueue each, all in a cohort
- Set `borrowingLimit` and `lendingLimit` per CQ
- Add `WorkloadPriorityClass` for prod vs research

**Phase 4 — Advanced features (later)**
- Enable `fairSharing` once cohort behavior is understood
- Add ProvisioningRequest for autoscaler integration
- Consider TAS for GPU-heavy training
- Federate with MultiKueue if you have multiple clusters

**Quota change semantics:**

- **Increasing nominalQuota** — immediate; no Workload disruption; new Workloads can admit on next scheduling cycle.
- **Decreasing nominalQuota** — admitted Workloads keep running; new admissions blocked until usage drops below new quota.
- **Adding a namespaceSelector restriction** — already-admitted Workloads from now-excluded namespaces keep running; new ones can't submit.

These all-non-destructive operations are why Kueue is safe to adopt incrementally.

## Sources

- https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/
- https://kueue.sigs.k8s.io/docs/concepts/cohort/
- https://kueue.sigs.k8s.io/docs/concepts/fair_sharing/
- https://kueue.sigs.k8s.io/docs/tasks/manage/administer_cluster_quotas/
- https://kueue.sigs.k8s.io/docs/tasks/manage/setup_sequential_admission_with_priorities/
- https://kueue.sigs.k8s.io/docs/tasks/manage/setup_consumable_resources/
- https://github.com/kubernetes-sigs/kueue/tree/main/keps
