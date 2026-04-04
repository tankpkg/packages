# Security and RBAC

Sources: Kubernetes official documentation (v1.32), Rice (Kubernetes Security and Observability), NIST SP 800-190 (Container Security), CIS Kubernetes Benchmark v1.9, NSA/CISA Kubernetes Hardening Guide (2024), Pod Security Standards documentation

Covers: RBAC (Roles, ClusterRoles, Bindings), ServiceAccounts, Pod Security Standards and Admission, NetworkPolicies, SecurityContext, secrets management, OPA/Gatekeeper, and security hardening checklist.

## RBAC Fundamentals

RBAC controls who can perform what actions on which resources in the Kubernetes API.

### RBAC Building Blocks

| Resource | Scope | Purpose |
|----------|-------|---------|
| Role | Namespace | Grants permissions within a namespace |
| ClusterRole | Cluster-wide | Grants permissions cluster-wide or on non-namespaced resources |
| RoleBinding | Namespace | Binds a Role or ClusterRole to subjects within a namespace |
| ClusterRoleBinding | Cluster-wide | Binds a ClusterRole to subjects cluster-wide |

### Role Example

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: pod-reader
rules:
- apiGroups: [""]              # core API group
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list"]
```

### RoleBinding Example

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: production
subjects:
- kind: User
  name: alice
  apiGroup: rbac.authorization.k8s.io
- kind: ServiceAccount
  name: monitoring-sa
  namespace: monitoring
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### Available Verbs

| Verb | Action |
|------|--------|
| get | Read a single resource |
| list | List resources |
| watch | Stream changes |
| create | Create new resources |
| update | Modify existing resources |
| patch | Partially modify resources |
| delete | Delete resources |
| deletecollection | Delete multiple resources |
| impersonate | Act as another user/group |
| bind | Bind roles (escalation control) |
| escalate | Modify roles beyond own permissions |

### RBAC Best Practices

| Practice | Rationale |
|----------|-----------|
| Prefer Role over ClusterRole | Limits blast radius to namespace |
| Never use wildcards (`*`) in production | Grants everything, including future resources |
| One ServiceAccount per workload | Compromised SA only affects that workload |
| Never use the `default` ServiceAccount | It exists in every namespace, easy target |
| Disable automounting when not needed | `automountServiceAccountToken: false` |
| Regular RBAC audits | `kubectl auth can-i --list --as=system:serviceaccount:ns:sa` |

### RBAC Debugging

```bash
# Check what a user/SA can do
kubectl auth can-i --list --as=alice
kubectl auth can-i --list --as=system:serviceaccount:production:app-sa

# Check specific permission
kubectl auth can-i create deployments --as=alice -n production

# Find all ClusterRoleBindings (high-risk)
kubectl get clusterrolebindings -o wide

# Find bindings granting cluster-admin
kubectl get clusterrolebindings -o json | \
  jq '.items[] | select(.roleRef.name=="cluster-admin") | .subjects'
```

### RBAC Review Questions

1. Could this permission be namespaced instead of cluster-wide?
2. Does this Role or ClusterRole grant only the verbs and resources actually needed?
3. Is each ServiceAccount scoped to one workload or reused too broadly?

## ServiceAccounts

Every pod runs as a ServiceAccount. Tokens are projected into the pod as volume mounts.

### Dedicated ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: production
  annotations:
    # AWS IAM Roles for Service Accounts (IRSA)
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/app-role
automountServiceAccountToken: false    # disable unless needed
```

### Token Projection (Bound Tokens)

Modern Kubernetes projects short-lived, audience-bound tokens:

```yaml
spec:
  serviceAccountName: app-sa
  automountServiceAccountToken: false
  containers:
  - name: app
    volumeMounts:
    - name: token
      mountPath: /var/run/secrets/tokens
  volumes:
  - name: token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600
          audience: my-api
```

## Pod Security Standards (PSS)

Three profiles define security constraints for pods. Enforced via Pod Security Admission (PSA), the built-in admission controller.

### Security Profiles

| Profile | Description | Use Case |
|---------|-------------|----------|
| Privileged | No restrictions | System-level workloads (CNI, storage drivers) |
| Baseline | Prevents known privilege escalations | General-purpose workloads |
| Restricted | Current hardening best practices | Production application workloads |

### Restricted Profile Requirements

| Requirement | What It Enforces |
|-------------|-----------------|
| runAsNonRoot: true | No root containers |
| allowPrivilegeEscalation: false | No setuid/setgid |
| Drop ALL capabilities | Only add back specific ones needed |
| seccompProfile: RuntimeDefault | Restrict system calls |
| readOnlyRootFilesystem | Prevent filesystem writes (except volumes) |
| No hostNetwork, hostPID, hostIPC | No host namespace sharing |
| No privileged containers | No elevated privileges |
| No hostPath volumes | No direct host filesystem access |

### Applying PSA Per Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
```

### PSA Adoption Strategy

| Phase | Mode | Profile | Purpose |
|-------|------|---------|---------|
| 1 (Assessment) | audit + warn | restricted | Identify non-compliant workloads |
| 2 (Remediation) | audit + warn | restricted | Fix violations |
| 3 (Enforcement) | enforce | restricted | Block non-compliant pods |

Start with `warn` mode to see violations in kubectl output without breaking workloads. Move to `enforce` after remediating all violations.

### PSA Review Questions

1. Is this namespace ready for `restricted`, or does it still depend on privileged behavior?
2. Are warnings being reviewed before enforcement is flipped on?
3. Is there an intentional exception path for system-level workloads?

## SecurityContext

Applied at pod or container level to restrict runtime behavior.

```yaml
spec:
  securityContext:                    # pod-level
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    securityContext:                  # container-level
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
        add: ["NET_BIND_SERVICE"]    # only if binding < 1024
```

### Capability Reference

| Capability | When Needed |
|-----------|-------------|
| NET_BIND_SERVICE | Bind ports below 1024 |
| SYS_PTRACE | Debugging tools (ephemeral containers) |
| NET_RAW | Network tools (ping, tcpdump) |
| All others | Drop unless specifically required |

### SecurityContext Review Questions

1. Does this workload truly need root, writable root filesystem, or added capabilities?
2. Are pod-level and container-level security settings aligned, or contradictory?
3. Is the hardened posture enforced by policy or only by convention?

## NetworkPolicies

Control pod-to-pod and pod-to-external traffic. Requires a CNI that supports NetworkPolicies (Calico, Cilium, Weave).

### NetworkPolicy Review Questions

1. Is default deny actually in place for namespaces that need isolation?
2. Have required DNS and control-plane egress paths been explicitly restored?
3. Does this policy model the real service graph, or just an assumed one?

### Default Deny All

Apply to every namespace as a baseline:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}              # applies to all pods in namespace
  policyTypes:
  - Ingress
  - Egress
```

### Allow Specific Traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

### Allow DNS Egress (Required)

After default-deny egress, pods cannot resolve DNS. Allow it:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
```

## Secrets Management

Kubernetes Secrets are base64-encoded, not encrypted at rest by default.

### Hardening Secrets

| Measure | How |
|---------|-----|
| Enable encryption at rest | EncryptionConfiguration with AES-CBC or KMS provider |
| External secrets manager | HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager |
| External Secrets Operator | Syncs external secrets into Kubernetes Secrets |
| Sealed Secrets | Encrypt secrets for Git storage (Bitnami Sealed Secrets) |
| RBAC on secrets | Restrict `get` and `list` on Secrets to specific SAs |
| Avoid env vars for secrets | Mount as files -- env vars leak into crash dumps and logs |

### External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: app-secrets
  data:
  - secretKey: db-password
    remoteRef:
      key: secret/data/production/db
      property: password
```

## Policy Engines

For policies beyond PSA (custom validation, mutation, audit):

| Engine | Approach | Language |
|--------|----------|----------|
| OPA/Gatekeeper | Constraint templates + constraints | Rego |
| Kyverno | Kubernetes-native policies | YAML |
| Kubewarden | WebAssembly policies | Any (Rust, Go, JS) |
| Cedar (AWS) | Attribute-based policies | Cedar |

Kyverno is easiest to adopt (pure YAML). OPA/Gatekeeper is more powerful for complex logic.

## Security Hardening Checklist

| Area | Action | Priority |
|------|--------|----------|
| RBAC | Dedicated SAs, no wildcards, regular audits | Day 1 |
| Pods | PSA enforce `restricted`, non-root, drop capabilities | Day 1 |
| Network | Default-deny NetworkPolicies per namespace | Week 1 |
| Secrets | External Secrets Operator, encryption at rest | Week 1 |
| Images | Private registry, image scanning, no :latest | Week 1 |
| API server | Restrict network access, enable audit logging | Week 1 |
| Nodes | Auto-updates, minimal OS, CIS benchmarks | Ongoing |
| Runtime | Falco or equivalent for anomaly detection | Month 1 |
