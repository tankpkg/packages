# Networking and Services

Sources: Kubernetes official documentation (v1.32), Luksa (Kubernetes in Action, 2nd ed.), Rice (Kubernetes Security and Observability), NGINX Ingress Controller docs, Istio documentation, CoreDNS documentation

Covers: Service types, Ingress controllers, DNS and service discovery, Endpoints, headless Services, service mesh overview, and network debugging.

## Kubernetes Networking Model

Every Pod gets its own IP address. Pods communicate directly without NAT. Three levels of networking:

| Level | Scope | Mechanism |
|-------|-------|-----------|
| Container-to-container | Same pod | localhost (shared network namespace) |
| Pod-to-pod | Same/different nodes | CNI plugin (Calico, Cilium, Flannel) |
| External-to-pod | Outside cluster | Service + Ingress |

## Service Types

A Service provides a stable endpoint (ClusterIP or DNS name) for a set of pods matched by label selectors.

### ClusterIP (Default)

Internal-only virtual IP. Accessible only from within the cluster.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  type: ClusterIP              # default, can omit
  selector:
    app: backend
  ports:
  - port: 80                   # service port (what clients connect to)
    targetPort: 8080            # container port (what the app listens on)
    protocol: TCP
```

Access from other pods: `http://backend.default.svc.cluster.local:80` or simply `http://backend:80` within the same namespace.

### NodePort

Exposes the service on a static port (30000-32767) on every node's IP.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080             # optional, auto-assigned if omitted
```

Access: `http://<any-node-ip>:30080`. Rarely used directly in production -- use LoadBalancer or Ingress instead.

### LoadBalancer

Provisions a cloud load balancer (AWS ALB/NLB, GCP LB, Azure LB) that routes external traffic to the service.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb    # cloud-specific
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 443
    targetPort: 8080
```

Each LoadBalancer service gets its own external IP and cloud LB. Use Ingress to consolidate multiple services behind a single LB.

### ExternalName

Maps a service to an external DNS name. No proxying -- returns a CNAME record.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: db.example.com
```

Use for referencing external services (RDS, Cloud SQL) by a cluster-internal DNS name.

### Headless Service

Returns pod IPs directly instead of a single ClusterIP. Required for StatefulSets.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  clusterIP: None              # headless
  selector:
    app: postgres
  ports:
  - port: 5432
```

DNS returns A records for each pod: `postgres-0.postgres.default.svc.cluster.local`.

### Service Type Selection

| Need | Type |
|------|------|
| Internal pod-to-pod communication | ClusterIP |
| Direct pod DNS (StatefulSets) | Headless (clusterIP: None) |
| External access with cloud LB | LoadBalancer |
| External access without cloud LB | NodePort + Ingress |
| Reference external service by DNS | ExternalName |
| Multiple services on single LB | Ingress (with one LB Service) |

## Ingress

Ingress manages external HTTP/HTTPS access to services, providing host-based and path-based routing, TLS termination, and a single entry point.

### Ingress Resource

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - app.example.com
    secretName: app-tls
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

### Ingress Controller Comparison

| Controller | Provider | Strengths |
|-----------|----------|-----------|
| NGINX Ingress | Community/NGINX Inc | Widely adopted, mature, extensive annotations |
| Traefik | Traefik Labs | Auto-discovery, middleware chain, dashboard |
| HAProxy Ingress | HAProxy | High performance, enterprise features |
| AWS ALB Ingress | AWS | Native ALB integration, IAM, WAF |
| GKE Ingress | Google | Native GCP LB integration |
| Istio Gateway | Istio | Service mesh integration, advanced traffic |
| Contour | VMware | Envoy-based, HTTPProxy CRD |
| Emissary | Ambassador | API gateway features, rate limiting |

### Gateway API (Ingress successor)

Gateway API is the evolution of Ingress, providing more expressive routing. Graduating to GA in recent Kubernetes versions.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: web-route
spec:
  parentRefs:
  - name: main-gateway
  hostnames:
  - app.example.com
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api
      port: 80
```

| Feature | Ingress | Gateway API |
|---------|---------|-------------|
| Role separation | Single resource | Gateway (infra) + Route (app team) |
| Header-based routing | Annotation-dependent | Native |
| Traffic splitting | Not built-in | Native (weight-based) |
| Cross-namespace | Limited | First-class support |
| Status | Stable | GA (v1.2+) |

## DNS and Service Discovery

CoreDNS resolves cluster-internal names. Every Service gets a DNS entry automatically.

### DNS Record Format

| Record Type | Format | Resolves To |
|-------------|--------|-------------|
| Service A record | `{svc}.{ns}.svc.cluster.local` | ClusterIP |
| Headless A record | `{svc}.{ns}.svc.cluster.local` | All pod IPs |
| Pod A record | `{pod-ip-dashed}.{ns}.pod.cluster.local` | Pod IP |
| StatefulSet pod | `{pod}.{svc}.{ns}.svc.cluster.local` | Specific pod IP |
| SRV record | `_{port}._{proto}.{svc}.{ns}.svc.cluster.local` | Port + IP |

### DNS Shorthand Rules

From within the same namespace, use short names:

```bash
# Same namespace
curl http://backend:80

# Different namespace
curl http://backend.other-namespace:80

# FQDN (always works)
curl http://backend.other-namespace.svc.cluster.local:80
```

### DNS Debugging

```bash
# Run a debug pod with DNS tools
kubectl run dns-test --rm -it --image=busybox:1.36 -- nslookup backend

# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns

# Verify DNS config in a pod
kubectl exec <pod> -- cat /etc/resolv.conf
```

## Endpoints and EndpointSlices

Services discover pods via Endpoints (or EndpointSlices in modern clusters). The endpoints controller watches pods matching the Service selector and updates the endpoint list.

### Manual Endpoints (No Selector)

Route traffic to external IPs by creating a Service without a selector and defining Endpoints manually:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  ports:
  - port: 5432
---
apiVersion: v1
kind: Endpoints
metadata:
  name: external-db          # must match Service name
subsets:
- addresses:
  - ip: 10.0.1.50
  ports:
  - port: 5432
```

Use this to integrate off-cluster databases or legacy services into Kubernetes DNS.

## Service Mesh Overview

A service mesh adds observability, traffic management, and security to service-to-service communication via sidecar proxies.

### When to Consider a Service Mesh

| Signal | Recommendation |
|--------|---------------|
| < 10 services, simple communication | Skip service mesh -- overhead not justified |
| Need mutual TLS between services | Service mesh or manual cert management |
| Need traffic splitting for canary | Service mesh or Argo Rollouts |
| Need per-request observability (traces) | Service mesh or application-level instrumentation |
| > 50 services, complex topology | Service mesh provides significant value |

### Service Mesh Options

| Mesh | Sidecar | Key Differentiator |
|------|---------|-------------------|
| Istio | Envoy | Most features, largest community, highest complexity |
| Linkerd | Rust micro-proxy | Lightweight, simple, low resource overhead |
| Cilium Service Mesh | eBPF (sidecar-free) | Kernel-level networking, no sidecar overhead |
| Consul Connect | Envoy | Multi-platform (K8s + VMs), HashiCorp ecosystem |

For most teams starting out: skip the service mesh. Add it when the problem it solves (mTLS, traffic splitting, distributed tracing) outweighs the operational complexity.

## Network Debugging Toolkit

```bash
# Check if service resolves
kubectl run tmp --rm -it --image=busybox:1.36 -- wget -qO- http://backend:80

# Check endpoints
kubectl get endpoints backend

# Check service
kubectl describe service backend

# Port forward for local testing
kubectl port-forward svc/backend 8080:80

# Check network policies affecting a pod
kubectl get networkpolicy -n <namespace>
```
