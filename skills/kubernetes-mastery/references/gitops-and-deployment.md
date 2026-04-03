# GitOps and Deployment Strategies

Sources: Kubernetes official documentation (v1.32), Argo CD documentation (v2.13), Flux documentation (v2), Argo Rollouts documentation, Flagger documentation, Ibryam/Huss (Kubernetes Patterns, 2nd ed.), Limoncelli et al. (The Practice of Cloud System Administration)

Covers: GitOps principles, ArgoCD and Flux setup, rolling updates, blue/green deployments, canary releases, progressive delivery, PodDisruptionBudgets, rollback strategies, and deployment best practices.

## GitOps Principles

GitOps is a deployment methodology where Git repositories are the single source of truth for cluster state.

### Core Tenets

| Principle | Description |
|-----------|-------------|
| Declarative | Entire system described declaratively in Git |
| Versioned and immutable | Git history is the audit log; every change tracked |
| Pulled automatically | Agents pull desired state from Git (not push via CI) |
| Continuously reconciled | Agents detect and correct drift from desired state |

### GitOps vs Traditional CI/CD

| Aspect | Traditional CI/CD | GitOps |
|--------|-------------------|--------|
| Deployment trigger | CI pipeline pushes to cluster | Agent pulls from Git |
| Source of truth | Pipeline configuration | Git repository |
| Drift detection | None | Continuous reconciliation |
| Rollback | Re-run old pipeline | Git revert |
| Audit trail | CI logs | Git history |
| Access model | CI needs cluster credentials | Agent runs inside cluster |

## ArgoCD

ArgoCD is a declarative, GitOps continuous delivery tool for Kubernetes. Most popular GitOps controller.

### Installation

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Get initial admin password
argocd admin initial-password -n argocd

# Access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### Application Manifest

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/k8s-manifests.git
    targetRevision: main
    path: apps/web/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true              # delete resources removed from Git
      selfHeal: true           # revert manual changes (drift correction)
    syncOptions:
    - CreateNamespace=true
    - ApplyOutOfSyncOnly=true  # only sync changed resources
    retry:
      limit: 3
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### ApplicationSet (Multi-Cluster/Multi-Env)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: web-app
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - cluster: dev
        url: https://dev-cluster.example.com
        path: overlays/dev
      - cluster: staging
        url: https://staging-cluster.example.com
        path: overlays/staging
      - cluster: production
        url: https://prod-cluster.example.com
        path: overlays/production
  template:
    metadata:
      name: 'web-app-{{cluster}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/org/k8s-manifests.git
        targetRevision: main
        path: 'apps/web/{{path}}'
      destination:
        server: '{{url}}'
        namespace: production
```

### ArgoCD with Helm

```yaml
spec:
  source:
    repoURL: https://charts.bitnami.com/bitnami
    chart: postgresql
    targetRevision: "13.4.0"
    helm:
      releaseName: postgres
      valueFiles:
      - values-production.yaml
```

### ArgoCD CLI Essentials

```bash
argocd app list
argocd app get web-app
argocd app sync web-app
argocd app sync web-app --force              # force sync
argocd app rollback web-app <revision>
argocd app diff web-app
argocd app history web-app
```

## Flux

Flux is a CNCF graduated GitOps toolkit. Modular architecture with separate controllers.

### Installation

```bash
flux bootstrap github \
  --owner=org \
  --repository=fleet-infra \
  --branch=main \
  --path=clusters/production \
  --personal
```

### Flux Components

| Component | Purpose |
|-----------|---------|
| source-controller | Fetches manifests from Git, Helm, OCI, S3 |
| kustomize-controller | Reconciles Kustomize overlays |
| helm-controller | Reconciles Helm releases |
| notification-controller | Handles alerts and webhooks |
| image-automation | Detects new container images and updates Git |

### GitRepository + Kustomization

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: app-repo
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/org/k8s-manifests.git
  ref:
    branch: main
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: web-app
  namespace: flux-system
spec:
  interval: 5m
  path: ./apps/web/overlays/production
  prune: true
  sourceRef:
    kind: GitRepository
    name: app-repo
  healthChecks:
  - apiVersion: apps/v1
    kind: Deployment
    name: web
    namespace: production
```

### ArgoCD vs Flux

| Factor | ArgoCD | Flux |
|--------|--------|------|
| UI | Built-in web UI | No built-in UI (use Weave GitOps) |
| Multi-cluster | ApplicationSet | Kustomization per cluster |
| Helm support | Native | HelmRelease CRD |
| Image automation | Not built-in (use Argo Image Updater) | Built-in image-automation |
| CNCF status | Graduated | Graduated |
| Complexity | Moderate (single binary) | Higher (multiple controllers) |
| RBAC | Built-in RBAC + SSO | Kubernetes RBAC |

## Deployment Strategies

### Rolling Update (Default)

Incrementally replaces pods. Zero downtime when configured correctly.

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

Requirements for zero-downtime rolling updates:
1. Readiness probe configured (traffic only sent to ready pods)
2. `maxUnavailable: 0` (never drop below desired count)
3. Graceful shutdown handling (`SIGTERM` → drain connections → exit)
4. `terminationGracePeriodSeconds` long enough for in-flight requests
5. PreStop hook if needed: `lifecycle.preStop.exec.command: ["sleep", "5"]`

### Blue/Green Deployment

Run two identical environments. Switch traffic by updating Service selector.

```bash
# Deploy green version alongside blue
kubectl apply -f deployment-green.yaml

# Verify green is healthy
kubectl rollout status deployment/web-green

# Switch traffic (update Service selector)
kubectl patch service web -p '{"spec":{"selector":{"version":"green"}}}'

# Rollback: switch selector back to blue
kubectl patch service web -p '{"spec":{"selector":{"version":"blue"}}}'
```

For production, use Argo Rollouts or Flagger to automate this.

### Canary Deployment

Route a percentage of traffic to the new version. Monitor metrics. Gradually increase or rollback.

### Argo Rollouts (Progressive Delivery)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: web
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: web-canary
      stableService: web-stable
      trafficRouting:
        nginx:
          stableIngress: web-ingress
      steps:
      - setWeight: 10
      - pause: {duration: 5m}
      - setWeight: 30
      - pause: {duration: 5m}
      - setWeight: 60
      - pause: {duration: 5m}
      analysis:
        templates:
        - templateName: success-rate
        startingStep: 1
        args:
        - name: service-name
          value: web-canary
  selector:
    matchLabels:
      app: web
  template:
    # ... pod template
```

### AnalysisTemplate (Automated Rollback)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
  - name: service-name
  metrics:
  - name: success-rate
    interval: 60s
    successCondition: result[0] >= 0.95
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          sum(rate(http_requests_total{service="{{args.service-name}}",status!~"5.."}[5m])) /
          sum(rate(http_requests_total{service="{{args.service-name}}"}[5m]))
```

## PodDisruptionBudgets (PDB)

Protect application availability during voluntary disruptions (node drain, cluster upgrades, spot instance reclamation).

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-pdb
spec:
  minAvailable: 2              # at least 2 pods must remain
  # OR
  # maxUnavailable: 1          # at most 1 pod can be unavailable
  selector:
    matchLabels:
      app: web
```

### PDB Guidelines

| Replicas | Recommended PDB |
|----------|----------------|
| 1 | No PDB (blocks all drains) or `maxUnavailable: 1` |
| 2-3 | `maxUnavailable: 1` |
| 4+ | `minAvailable: 50%` or `maxUnavailable: 25%` |

Always create PDBs for production workloads with 2+ replicas.

## Deployment Best Practices

| Practice | Rationale |
|----------|-----------|
| Use specific image tags (never :latest) | Reproducible deployments; :latest breaks caching and rollback |
| Set `revisionHistoryLimit: 5` | Keep rollback history without wasting etcd storage |
| Configure PDBs for all production services | Prevent disruptions during maintenance |
| Use readiness gates for complex dependencies | Block traffic until all requirements met |
| Set `terminationGracePeriodSeconds` appropriately | Allow in-flight requests to complete |
| Add preStop hook for graceful shutdown | `sleep 5` gives load balancers time to deregister |
| Pin chart versions in GitOps | `targetRevision: "13.4.0"` not `latest` |
| Separate config repos from app repos | Decouple deployment cadence from release cadence |
| Use namespaces for environment isolation | dev/staging/production in separate namespaces |
| Implement progressive delivery for critical services | Canary with automated analysis catches regressions |
