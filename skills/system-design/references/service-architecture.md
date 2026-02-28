# Service Architecture Patterns

Sources: Synthesized from Newman (Building Microservices), Ford et al. (Software Architecture: The Hard Parts), Richards & Ford (Fundamentals of Software Architecture)

Covers: architecture style selection, service decomposition, API gateway, communication patterns, service discovery, distributed transactions, API design, service mesh.

## Architecture Style Selection

### Monolith to Microservices Spectrum

| Style | Description | Team Size | Deploy Independence | Operational Complexity |
|---|---|---|---|---|
| Single-process monolith | One deployable unit, one database | 1-15 | None | Lowest |
| Modular monolith | Single deploy, but internally separated modules with clear boundaries | 5-30 | None (but modular internals) | Low |
| Service-based | Few coarse-grained services (3-12), each owning a domain | 10-50 | Moderate | Moderate |
| Microservices | Many fine-grained services, each independently deployable | 30-500+ | High | High |
| Serverless functions | Individual functions triggered by events | Any | Per-function | Variable (platform-managed) |

### Decision Framework

Ask these questions in order. Stop when you have enough information to decide.

1. **Do separate teams need to deploy independently?** If no → monolith or modular monolith is sufficient.
2. **Do components have fundamentally different scaling needs?** If yes → separate the components that need different scaling.
3. **Is the domain well-understood with stable boundaries?** If no → monolith first. Wrong service boundaries in microservices are expensive to fix.
4. **Can you afford the operational complexity?** Microservices require: service discovery, distributed tracing, independent CI/CD, contract testing, and on-call per service.
5. **Is your team large enough that a monolith is a coordination bottleneck?** If yes (typically 30+ engineers) → decompose.

### The Monolith-First Principle

Start with a monolith. It is easier to decompose a well-structured monolith into services than to merge poorly-designed services back into a coherent system. A modular monolith with clear internal boundaries gives most benefits of microservices without the operational cost.

**Decompose when you observe**:
- Deploy conflicts: Teams blocking each other on releases
- Scaling mismatch: One module needs 10x resources but everything scales together
- Technology mismatch: One component needs a different language or runtime
- Blast radius: A bug in one area crashes the entire application

## Service Decomposition

### Identifying Service Boundaries

| Approach | How | Strength | Risk |
|---|---|---|---|
| By business capability | Map to what the business does (billing, shipping, inventory) | Stable boundaries, aligned with org structure | May not match technical reality |
| By subdomain (DDD) | Core, supporting, and generic subdomains | Explicit investment priority | Requires deep domain understanding |
| By data ownership | Each service owns the data it writes | Clear consistency boundaries | May create chatty inter-service communication |
| By team | Conway's Law — structure mirrors communication | Natural ownership, clear accountability | Teams may not align with optimal technical boundaries |

### Data Ownership as Hard Constraint

The most important boundary decision: which service owns which data.

| Principle | Implication |
|---|---|
| A service owns its data exclusively | Other services cannot write to its database directly |
| Data access is through the owning service's API | No shared databases between services |
| If two services need the same data | One owns it, the other gets a copy via events or API |
| Joins across services | Not possible at database level — join at application level or denormalize |

### The Distributed Monolith Anti-Pattern

Microservices that must be deployed together, share databases, or have tight synchronous coupling. All the complexity of distribution with none of the benefits.

**Symptoms**:
- Deploying service A requires simultaneously deploying service B
- Multiple services read from or write to the same database tables
- A change in one service's data schema requires changes in other services
- Service A cannot function at all when service B is down

**Fix**: Enforce data ownership, introduce async communication for non-critical coupling, accept eventual consistency where appropriate.

## API Gateway Pattern

A single entry point for external clients that routes requests to appropriate backend services.

### Core Responsibilities

| Responsibility | What It Does | Example |
|---|---|---|
| Request routing | Routes to correct backend service based on path/header | `/api/orders/*` → orders service |
| Authentication | Verifies identity (JWT validation, API key check) | Reject unauthenticated requests |
| Rate limiting | Throttles requests per client/API key | 1000 requests per minute per API key |
| Protocol translation | Convert between protocols | External REST ↔ internal gRPC |
| Response aggregation | Combine responses from multiple services | Product page = product + reviews + recommendations |
| TLS termination | Handle HTTPS at the gateway | Backend services communicate over plain HTTP internally |

### Gateway vs Backend for Frontend (BFF)

| Pattern | Structure | Best For |
|---|---|---|
| Single gateway | One gateway for all clients (web, mobile, third-party) | Simple APIs, uniform client needs |
| BFF per client type | Separate gateway for web, mobile, third-party | Different clients need different data shapes and aggregations |
| BFF per team | Each team owns their BFF | Maximum team autonomy |

### Gateway Anti-Patterns

| Anti-Pattern | Why It Is Harmful | Alternative |
|---|---|---|
| Business logic in gateway | Gateway becomes a monolith, coupling point | Keep business logic in domain services |
| Excessive aggregation | Gateway becomes slow and fragile | Client makes parallel requests or use BFF |
| Single gateway for all traffic | Single point of failure, performance bottleneck | Deploy multiple gateway instances, separate external/internal |
| No timeouts on upstream calls | Gateway hangs when backend is slow | Set aggressive timeouts, circuit breakers |

## Service Communication Patterns

### Protocol Selection

| Protocol | Format | Strengths | Weaknesses | Best For |
|---|---|---|---|---|
| REST (HTTP/JSON) | Text-based, human-readable | Universal, tooling-rich, cache-friendly | Verbose, no streaming (HTTP/1.1), no schema enforcement | Public APIs, web/mobile clients, simple CRUD |
| gRPC (HTTP/2 + Protobuf) | Binary, schema-defined | Low latency, streaming, strong typing, code generation | Not browser-friendly (needs proxy), harder to debug | Internal service-to-service, high-throughput, polyglot |
| GraphQL | Query language over HTTP | Client specifies exact data needed, single endpoint | Complexity, N+1 query risk, caching harder | APIs with diverse client data needs, mobile apps |
| WebSocket | Bidirectional TCP | Real-time, low overhead per message | Stateful connection, harder to scale | Chat, live updates, collaborative editing |

### Synchronous vs Asynchronous Selection

| Use Synchronous When | Use Asynchronous When |
|---|---|
| Response needed to complete the operation | Work can be done in the background |
| Low-latency, user-facing request | Decoupling sender and receiver is valuable |
| Simple request-response flow | Broadcasting to multiple consumers |
| Query/read operations | Long-running workflows |
| Authentication/authorization checks | Eventual consistency is acceptable |

Detailed async patterns are in `references/messaging-and-async.md`.

### API Versioning Strategies

| Strategy | How | Pros | Cons |
|---|---|---|---|
| URL path versioning | `/v1/users`, `/v2/users` | Explicit, easy to route | URL pollution, hard to deprecate |
| Header versioning | `Accept: application/vnd.api.v2+json` | Clean URLs | Less visible, harder to test in browser |
| Query parameter | `/users?version=2` | Simple to implement | Easily forgotten, caching complications |
| No versioning (additive only) | Only add fields, never remove or change | Simplest | Eventually accumulates cruft |

**Recommendation**: URL path versioning for public APIs (explicit and discoverable). Additive-only changes for internal APIs (minimize coordination cost).

### Contract Testing

Verify that a service produces responses matching what its consumers expect, without end-to-end tests.

| Component | Role |
|---|---|
| Consumer contract | Consumer defines what it expects from the provider |
| Provider verification | Provider runs consumer contracts as tests |
| Pact/Spring Cloud Contract | Tools that automate this workflow |

## Service Discovery

### Approaches

| Pattern | How | Example |
|---|---|---|
| Client-side discovery | Client queries a registry, selects an instance, connects directly | Eureka + client-side load balancer |
| Server-side discovery | Client sends to a load balancer, which queries registry and routes | AWS ALB + ECS service discovery |
| DNS-based | Services register as DNS entries, client resolves hostname | Kubernetes Services (kube-dns), Consul DNS |
| Service mesh sidecar | Sidecar proxy handles discovery and routing transparently | Envoy (Istio), Linkerd proxy |

### Selection Criteria

| Factor | Client-Side | Server-Side | DNS-Based | Service Mesh |
|---|---|---|---|---|
| Client complexity | High (discovery + LB logic) | Low (just an endpoint) | Low (hostname) | Lowest (transparent) |
| Infrastructure cost | Low | Medium (load balancer) | Low | High (sidecar per pod) |
| Latency | Lowest (direct connection) | Slight hop through LB | DNS TTL caching delay | Slight sidecar overhead |
| Best for | Internal services in homogeneous stack | Heterogeneous clients | Kubernetes environments | Large microservice deployments |

## Distributed Transactions

Two-phase commit (2PC) requires all participants to be available and locks resources during prepare phase. This is impractical in microservices due to latency, availability impact, and tight coupling.

### Alternatives to 2PC

| Pattern | How | Consistency | Complexity |
|---|---|---|---|
| Saga (choreography or orchestration) | Sequence of local transactions with compensations | Eventual | Medium-High |
| Transactional outbox | Write business data and outbound message in same local transaction | Eventual (guaranteed delivery) | Medium |
| Change data capture (CDC) | Capture database changes and publish as events (Debezium) | Eventual | Medium (infrastructure) |
| Best effort + reconciliation | Attempt all operations, reconcile failures with batch job | Eventual (with manual intervention) | Low-Medium |

Detailed saga patterns are in `references/messaging-and-async.md`.

### Transactional Outbox Pattern

1. In a single database transaction: write the business data AND an outbox record (message to be sent)
2. A separate publisher process reads the outbox table and publishes messages to the broker
3. After successful publish, mark outbox record as sent

This guarantees that if the business transaction commits, the message will eventually be published. No distributed transaction needed.

## API Design for Services

### Idempotency

Make operations safe to retry by including an idempotency key.

| HTTP Method | Naturally Idempotent | Idempotency Key Needed |
|---|---|---|
| GET | Yes | No |
| PUT | Yes (full replacement) | No |
| DELETE | Yes (deleting twice = same result) | No |
| POST | No | Yes — client generates unique key, server deduplicates |
| PATCH | Depends on implementation | Recommended |

### Pagination Patterns

| Pattern | How | Pros | Cons |
|---|---|---|---|
| Offset-based | `?offset=20&limit=10` | Simple, supports random access | Slow for large offsets, inconsistent with concurrent writes |
| Cursor-based (keyset) | `?after=eyJpZCI6MTIzfQ&limit=10` | Consistent, performant at any depth | No random access, opaque cursor |
| Page token | `?pageToken=abc123&pageSize=10` | Server controls implementation, opaque to client | Requires server-side state or encoding |

**Recommendation**: Cursor-based for large datasets (API responses, feeds). Offset-based for small datasets or when random page access is needed (admin dashboards).

### Error Response Standard

Consistent error format across all services:

```json
{
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Account balance is insufficient for this transaction",
    "details": [
      { "field": "amount", "reason": "Exceeds available balance of 150.00" }
    ],
    "request_id": "req_abc123"
  }
}
```

Include `request_id` for distributed tracing correlation.

## Service Mesh

### What a Service Mesh Solves

| Concern | Without Mesh | With Mesh |
|---|---|---|
| mTLS between services | Each service implements TLS | Sidecar handles encryption transparently |
| Observability | Each service instruments metrics/traces | Sidecar collects automatically |
| Traffic management | Application-level routing logic | Sidecar handles retries, canary, routing rules |
| Access control | Application-level auth between services | Policy-based control at mesh level |

### When a Service Mesh Is Justified

| Signal | Mesh Helps |
|---|---|
| 20+ microservices | Consistent cross-cutting concerns without per-service work |
| Strict security requirements (mTLS everywhere) | Transparent encryption without application changes |
| Complex traffic management (canary, A/B, traffic splitting) | Declarative routing rules |
| Multiple programming languages | Language-agnostic sidecar handles networking |

### When a Service Mesh Is Overkill

| Signal | Skip the Mesh |
|---|---|
| Fewer than 10 services | Overhead exceeds benefit |
| Single language/framework | Framework-level solutions (middleware) suffice |
| Simple traffic patterns | Load balancer handles routing |
| Small team | Operational complexity of mesh is a burden |

**Incremental adoption**: Start without a mesh. Add it when you observe pain in mTLS management, cross-service observability, or traffic control across many services.
