---
name: "@tank/kubernetes-mastery"
description: |
  Production Kubernetes operations and architecture for any cluster size.
  Covers workload controllers (Pods, Deployments, StatefulSets, DaemonSets,
  Jobs), networking (Services, Ingress, DNS, NetworkPolicies), Helm charts
  and Kustomize, RBAC and Pod Security Standards, storage (PV/PVC/StorageClass),
  ConfigMaps and Secrets, resource limits and QoS classes, HPA/VPA autoscaling,
  health probes (startup/readiness/liveness), rolling updates and canary
  deployments, kubectl debugging patterns, observability (Prometheus/Grafana),
  and GitOps workflows (ArgoCD/Flux).

  Synthesizes Kubernetes official documentation (v1.32+), Kubernetes in Action
  (Luksa), Kubernetes Patterns (Ibryam/Huss), Production Kubernetes (Rosso
  et al.), Google Zanzibar/BorgMaster papers, CNCF landscape, and Helm/
  Kustomize documentation.

  Trigger phrases: "kubernetes", "k8s", "kubectl", "helm", "helm chart",
  "kubernetes deployment", "kubernetes service", "kubernetes ingress",
  "kubernetes secrets", "kubernetes hpa", "kubernetes rbac", "kustomize",
  "kubectl cheat sheet", "pod not starting", "kubernetes networking",
  "kubernetes storage", "persistent volume", "kubernetes autoscaling",
  "kubernetes security", "argocd", "gitops", "kubernetes debug",
  "kubernetes best practices", "kubernetes production", "statefulset",
  "daemonset", "kubernetes monitoring", "kubernetes troubleshooting"
---

# Kubernetes Mastery

## Core Philosophy

1. **Declarative over imperative** -- Define desired state in YAML manifests. Let controllers reconcile actual state. Never rely on `kubectl run` in production; commit manifests to Git.
2. **Least privilege by default** -- Every workload gets its own ServiceAccount with minimal RBAC. Run as non-root. Drop all capabilities. Apply Pod Security Standards at namespace level.
3. **Resource-aware scheduling** -- Always set CPU/memory requests (scheduler guarantee) and memory limits (OOM protection). Omit CPU limits for latency-sensitive workloads to avoid throttling.
4. **Probes are self-healing** -- Configure startup probes for slow-init apps, readiness probes to gate traffic, and liveness probes to restart deadlocked processes. Aggressive liveness probes cause restart storms.
5. **GitOps is the deployment model** -- ArgoCD or Flux syncs cluster state from Git. Manual `kubectl apply` is for emergencies only. Every change is auditable and reversible.

## Quick-Start: Common Problems

### "My Pod is stuck in CrashLoopBackOff"

1. Check exit code: `kubectl describe pod <name>` -- look at `Last State` and `Exit Code`
2. Read logs: `kubectl logs <name> --previous` (shows last crashed container)
3. Exit code 137 = OOM killed -- increase memory limit
4. Exit code 1 = application error -- fix the app
5. Liveness probe failing? Check if probe path/port is correct and timeout is sufficient
-> See `references/observability-and-debugging.md`

### "Which Service type should I use?"

| Scenario | Service Type |
|----------|-------------|
| Pod-to-pod within cluster | ClusterIP (default) |
| External access via cloud LB | LoadBalancer |
| External access without cloud LB | NodePort + Ingress |
| Headless (direct pod DNS) | ClusterIP with `clusterIP: None` |
| External database/API | ExternalName or Endpoints |
-> See `references/networking-and-services.md`

### "Helm or Kustomize?"

| Signal | Use |
|--------|-----|
| Packaging for distribution (charts) | Helm |
| Environment-specific overlays (dev/staging/prod) | Kustomize |
| Need templating with conditionals/loops | Helm |
| Prefer pure YAML, no templating language | Kustomize |
| Both -- Helm for third-party, Kustomize for in-house | Common hybrid |
-> See `references/helm-and-kustomize.md`

### "How do I set up autoscaling?"

1. Set resource requests on all containers (HPA needs metrics to compare against)
2. Deploy Metrics Server (`kubectl apply -f metrics-server.yaml`)
3. Create HPA: `kubectl autoscale deployment <name> --min=2 --max=10 --cpu-percent=70`
4. For custom metrics (queue depth, RPS): use Prometheus Adapter + HPA v2
5. Add Cluster Autoscaler for node-level scaling
-> See `references/autoscaling-and-resources.md`

### "My Deployment rollout is stuck"

1. Check status: `kubectl rollout status deployment/<name>`
2. Check events: `kubectl describe deployment/<name>` -- look for `FailedCreate`
3. Insufficient resources? Scale down or add nodes
4. Image pull error? Verify image name, tag, and imagePullSecrets
5. Rollback: `kubectl rollout undo deployment/<name>`
-> See `references/gitops-and-deployment.md`

## Decision Trees

### Workload Controller Selection

| Workload Type | Controller |
|--------------|------------|
| Stateless web app, API | Deployment |
| Database, distributed store | StatefulSet |
| Per-node agent (logging, monitoring) | DaemonSet |
| One-off batch processing | Job |
| Scheduled batch processing | CronJob |

### Security Hardening Priority

| Priority | Action |
|----------|--------|
| 1 (Day 1) | Dedicated ServiceAccounts, no default SA |
| 2 (Day 1) | Pod Security Standards: `warn` then `enforce` `restricted` |
| 3 (Week 1) | Default-deny NetworkPolicies per namespace |
| 4 (Week 1) | RBAC audit -- remove wildcards and ClusterRoleBindings |
| 5 (Ongoing) | Secrets in external store (Vault, ESO), not plain manifests |

### Storage Selection

| Need | Solution |
|------|----------|
| Shared config files | ConfigMap (mounted as volume) |
| Credentials, API keys | Secret (+ External Secrets Operator) |
| Database storage | PVC with StorageClass (retain policy) |
| Shared filesystem (multi-pod) | ReadWriteMany PVC (NFS, EFS, CephFS) |
| Ephemeral scratch space | emptyDir |

## Reference Index

| File | Contents |
|------|----------|
| `references/workloads-and-controllers.md` | Pods, Deployments, StatefulSets, DaemonSets, Jobs, CronJobs, ReplicaSets, init containers, sidecar pattern, pod lifecycle |
| `references/networking-and-services.md` | Service types (ClusterIP/NodePort/LoadBalancer/ExternalName), Ingress controllers, DNS, service discovery, service mesh overview |
| `references/helm-and-kustomize.md` | Helm chart anatomy, values/templates, chart repositories, hooks, Kustomize bases/overlays, patches, strategic merge, Helm vs Kustomize selection |
| `references/security-and-rbac.md` | RBAC (Roles/ClusterRoles/Bindings), ServiceAccounts, Pod Security Standards/Admission, NetworkPolicies, SecurityContext, OPA/Gatekeeper |
| `references/storage-and-configuration.md` | PersistentVolumes, PersistentVolumeClaims, StorageClasses, volume types, ConfigMaps, Secrets, External Secrets Operator, projected volumes |
| `references/autoscaling-and-resources.md` | Resource requests/limits, QoS classes, LimitRanges, ResourceQuotas, HPA (v1/v2), VPA, Cluster Autoscaler, Karpenter, right-sizing |
| `references/observability-and-debugging.md` | kubectl debug/logs/exec/describe, events, Prometheus, Grafana, log aggregation, troubleshooting CrashLoopBackOff/ImagePull/Pending/OOM |
| `references/gitops-and-deployment.md` | ArgoCD, Flux, rolling updates, blue/green, canary (Argo Rollouts/Flagger), PodDisruptionBudgets, rollback, progressive delivery |
