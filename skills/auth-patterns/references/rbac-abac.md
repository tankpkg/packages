# RBAC, ABAC, and Authorization Models

Sources: NIST RBAC Standard (ANSI/INCITS 359-2004), Ferraiolo & Kuhn (Role-Based Access Controls, 1992), Google Zanzibar paper (Warrick et al., 2019), LoginRadius engineering blog, Permit.io engineering blog, Permify ABAC guide

Covers: RBAC levels, ABAC vs RBAC selection, ReBAC/Zanzibar model, role explosion prevention, multi-tenant authorization, permission modeling, and policy enforcement patterns.

## Authorization vs Authentication

Authentication answers "who are you?" Authorization answers "what are you allowed to do?" These are separate concerns, solved separately.

Design authorization as a service boundary: centralize policy definitions, enforce at each resource boundary, log every access decision.

## Role-Based Access Control (RBAC)

RBAC assigns permissions to roles, then assigns roles to users. Users gain permissions transitively through their roles.

```
Users → Roles → Permissions
Alice → [admin, editor] → [read, write, delete, publish]
Bob   → [viewer]        → [read]
```

### NIST RBAC Levels

| Level | Name | What It Adds |
|-------|------|-------------|
| RBAC0 | Core RBAC | Users, roles, permissions, sessions. Basic assignment |
| RBAC1 | Hierarchical RBAC | Role inheritance — senior roles inherit junior role permissions |
| RBAC2 | Constrained RBAC | Separation of duty (SoD) constraints — mutually exclusive roles |
| RBAC3 | Consolidated RBAC | RBAC1 + RBAC2 combined |

### RBAC0: Flat Roles

All roles are equal peers. Assign each user a set of roles explicitly.

```
admin     → create, read, update, delete, manage_users
editor    → create, read, update
viewer    → read
billing   → read, manage_subscription
```

Simple to implement, simple to audit. Sufficient for most applications up to ~20 roles and ~100 permissions.

### RBAC1: Role Hierarchy

Child roles inherit permissions from parent roles. Reduces duplication.

```
super_admin
  └── admin
        └── manager
              └── employee
                    └── intern
```

`admin` implicitly has all permissions of `manager`, `employee`, and `intern`. Assign the user to the highest applicable role only.

**Caution**: Deep hierarchies become hard to audit. Limit depth to 3-4 levels.

### RBAC2: Separation of Duty

Mutually exclusive role constraints prevent conflicts of interest.

| Constraint Type | Example |
|----------------|---------|
| Static SoD | User cannot hold both `initiator` and `approver` roles simultaneously |
| Dynamic SoD | User cannot activate both roles in the same session |
| Cardinality | A maximum of 3 users can hold the `key_custodian` role |

Enforce SoD at role assignment time (static) or session activation time (dynamic).

### When RBAC Works Well

- Permissions align with organizational job functions
- Role count stays manageable (< 50 roles for most teams)
- Users fit cleanly into defined role categories
- Compliance and audit are priorities (auditors understand RBAC)
- User count >> role count (scales well)

### Role Explosion Problem

RBAC breaks down when role count grows uncontrollably.

**Causes**:
- Creating per-user roles ("Alice's custom permissions")
- Creating per-resource roles ("read_project_123")
- Over-granular permission modeling
- Business requirements that depend on attributes

**Warning signs**:
- Role count > user count
- Roles that only one user holds
- Role names containing IDs or usernames
- Role assignment automation required due to volume

**Solutions**:
1. Introduce role hierarchy to collapse similar roles
2. Use parameterized roles with ABAC for resource-specific access
3. Audit and merge overlapping roles quarterly
4. Move resource-instance permissions to ABAC
5. Define maximum number of roles; require approval to exceed it
6. Use attribute-based refinement within RBAC structure (hybrid)

## Attribute-Based Access Control (ABAC)

ABAC makes access decisions based on attributes of the subject, resource, action, and environment — not static role assignments.

```
ALLOW IF:
  subject.department == resource.department
  AND action == "read"
  AND environment.time >= 09:00
  AND environment.time <= 17:00
```

### ABAC Attribute Categories

| Category | Examples |
|----------|---------|
| Subject attributes | `user.department`, `user.clearance_level`, `user.location`, `user.employment_type` |
| Resource attributes | `document.classification`, `document.owner_id`, `document.department` |
| Action attributes | `action.type` (read/write/delete), `action.sensitivity` |
| Environment attributes | `env.time_of_day`, `env.ip_address`, `env.risk_score` |

### ABAC vs RBAC Selection

| Factor | Choose RBAC | Choose ABAC |
|--------|-------------|-------------|
| Permission model complexity | Permissions align to roles | Permissions depend on data attributes |
| Role count trajectory | Stable and bounded | Growing rapidly |
| Access granularity | Coarse (role-level) | Fine (per-record, per-field) |
| Dynamic conditions | Not needed | Time-based, location-based, risk-based |
| Multi-tenancy | Separate role sets per tenant | Tenant as an attribute in policy |
| Regulatory audit | Simple to explain | More complex to audit |
| Team size | Small — easy RBAC governance | Large — RBAC governance overhead too high |
| Speed of change | Roles change infrequently | Access rules change frequently |

**Practical recommendation**: Start with RBAC. Add ABAC for specific use cases where role explosion would otherwise occur. Hybrid is common in production.

### ABAC Implementation Approaches

| Approach | Mechanism | When to Use |
|----------|-----------|-------------|
| Inline code | `if user.dept == doc.dept: allow` | Small teams, stable policies |
| Policy engine | OPA, Cedar, Casbin — externalized policies | Multiple services needing consistent authorization |
| XACML | XML-based policy language, industry standard | Enterprise/government compliance |
| Permission service | Dedicated authorization microservice (Permit.io, Oso, Authzed) | Large teams, complex multi-tenant |

### XACML Concepts (Without Full Spec)

XACML defines four combining algorithms for policy evaluation:

| Algorithm | Behavior |
|-----------|----------|
| `permit-overrides` | One permit is sufficient to allow |
| `deny-overrides` | One deny is sufficient to block |
| `first-applicable` | First matching policy wins |
| `only-one-applicable` | Only one policy may match; error if multiple match |

Use `deny-overrides` for safety-critical resources (a denial anywhere blocks). Use `permit-overrides` for additive permissions (any permission grants access).

## Relationship-Based Access Control (ReBAC)

ReBAC defines permissions through relationships between entities. Popularized by Google Zanzibar (2019) — the authorization system backing Google Drive, Docs, YouTube, and Maps.

### Zanzibar Core Model

```
// Tuples: (object, relation, subject)
doc:readme#owner@alice         // Alice is owner of readme
doc:readme#editor@bob          // Bob is editor of readme
doc:readme#viewer@charlie      // Charlie is viewer of readme
org:acme#member@alice          // Alice is member of acme org
doc:readme#viewer@org:acme#member  // All acme members are viewers of readme
```

Permission = tuple lookup + transitive closure. "Can Charlie view readme?" → check viewer tuples, traverse group memberships.

### ReBAC vs RBAC vs ABAC

| Model | State Location | Access Definition | Scales For |
|-------|--------------|-------------------|-----------|
| RBAC | Roles on users | Role → Permission table | Organizational hierarchy |
| ABAC | Attributes on subjects/resources | Policy expressions | Attribute-rich decisions |
| ReBAC | Relationships between entities | Relationship graph traversal | Sharing, collaboration, social |

ReBAC excels when: user-to-resource relationships are the permission mechanism (file sharing, team membership, ownership), permissions cascade through relationships, and the relationship graph is queried frequently.

### Open-Source Zanzibar Implementations

| Project | Language | Notes |
|---------|----------|-------|
| SpiceDB (Authzed) | Go | Direct Zanzibar descendant |
| OpenFGA | Go | CNCF project, Auth0 backed |
| Permify | Go | Zanzibar-inspired |
| Ory Keto | Go | Relationship-based |

## Multi-Tenant Authorization Patterns

In multi-tenant SaaS, authorization must be scoped to the tenant. Three approaches:

### Pattern 1: Tenant as Role Namespace

```
tenant_id:123:admin
tenant_id:123:viewer
tenant_id:456:admin
```

Roles are namespaced by tenant ID. Prevents cross-tenant permission leakage. Simple to implement. Scales to thousands of tenants.

### Pattern 2: Tenant as Attribute in ABAC Policy

```
ALLOW IF:
  subject.tenant_id == resource.tenant_id
  AND subject.roles contains "editor"
```

The tenant attribute is always included in every authorization decision. Enforced in policy, not data model.

### Pattern 3: Per-Tenant Policy Configuration

Tenants can define their own roles and permissions within boundaries set by the platform. Enterprise "bring your own roles" pattern.

Implementation: Store tenant-specific policy overrides. Load base platform policy + tenant overrides at decision time. Never let tenant policies escape their namespace.

## Permission Modeling Best Practices

### Granularity Decision

| Granularity | Examples | Trade-offs |
|-------------|---------|------------|
| Coarse | `read`, `write`, `admin` | Simple but inflexible |
| Medium | `posts:read`, `posts:write`, `users:manage` | Balanced — recommended starting point |
| Fine | `posts:123:read`, `posts:123:write` | Maximum control; use ABAC not RBAC for this |

Avoid mixing granularity levels. Audit UIs for resource-instance permissions become unmanageable.

### Naming Conventions

```
{resource}:{action}        → posts:read, posts:write, users:delete
{resource}:{sub-resource}:{action} → invoices:line-items:edit
admin:{resource}           → admin:users, admin:billing
```

Document every permission in code comments or a permissions manifest. Undocumented permissions become security debt.

### Principle of Least Privilege

Assign users the minimum permissions required to do their job. Enforce at design time (default deny) and audit at runtime (access logs).

- Default all new users to the lowest-privilege role
- Require explicit justification to grant elevated roles
- Set expiry on elevated role assignments (time-boxed access)
- Alert on unused permissions (user has permission but never used it in 90 days)

## Policy Enforcement Patterns

### Enforcement Points

| Layer | Where to Enforce | What to Check |
|-------|-----------------|---------------|
| API gateway | Before routing | Coarse authentication, rate limits |
| API handler | At request entry | Role/permission checks for endpoint |
| Service layer | Business logic | Resource-specific ownership |
| Database | Row-level security | Data-layer isolation |

Enforce authorization at every layer. Defense in depth — a bug in one layer should not expose all data.

### Never Enforce Only at UI

Frontend authorization (hiding buttons) is UX, not security. Always enforce server-side. Assume all API endpoints are directly callable.

### Centralize Authorization Logic

Avoid sprinkling permission checks throughout the codebase. Create a single authorization function:

```
isAllowed(subject, action, resource) → bool
```

Centralization enables: consistent enforcement, centralized auditing, easier testing, policy changes without code changes.

## Authorization Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Check roles in middleware only | Skipped by direct service calls | Check in service layer too |
| Boolean `is_admin` column | Binary — no gradation | Role assignment table |
| Role stored only in JWT | Stale if role changes | Short expiry or introspection |
| Per-user permission rows | Infinite role explosion | Group users into roles |
| Resource IDs in role names | Role explosion, DB joins | Use ABAC for resource-specific access |
| Frontend-only permission checks | Bypassable via curl | Always enforce server-side |
| God role with all permissions | No least privilege | Break into specific roles |
| No permission documentation | Audit failure | Maintain permissions manifest |
