# Threat Modeling

Sources: Shostack (Threat Modeling: Designing for Security), OWASP Threat Modeling documentation, UcedaVelez/Morana (Risk Centric Threat Modeling), PASTA methodology documentation

Covers: When to threat model, STRIDE framework (per-element application), PASTA 7-stage methodology, attack trees, trust boundaries, data flow diagrams, and lightweight 4-question sessions.

---

## When to Threat Model

Match the depth of analysis to the scope of change. Over-investing in lightweight changes wastes time; under-investing in architectural changes creates blind spots.

| Trigger | Depth |
|---------|-------|
| New feature with external input | Lightweight (30 min) |
| New service or microservice | Standard STRIDE (2-4 hours) |
| Architecture redesign | Full PASTA (1-2 days) |
| Pre-release compliance audit | Full PASTA + documentation |
| Simple UI change, no new data flows | Skip |

Treat threat modeling as a design activity, not a gate. Run it during design, not after implementation. Findings discovered post-implementation cost 10-100x more to remediate.

---

## STRIDE Framework

STRIDE is the most widely used threat modeling framework. Apply it systematically to each element in a data flow diagram. Each letter names a threat category and maps to a violated security property.

| Threat | Definition | Security Property Violated | Example |
|--------|-----------|---------------------------|---------|
| Spoofing | Pretending to be something or someone else | Authentication | Forged JWT, stolen session cookie |
| Tampering | Modifying data or code without authorization | Integrity | SQL injection, parameter tampering, log manipulation |
| Repudiation | Denying that an action occurred | Non-repudiation | Missing audit logs, unsigned transactions |
| Information Disclosure | Exposing information to unauthorized parties | Confidentiality | Error stack traces, directory listing, verbose headers |
| Denial of Service | Making a service unavailable to legitimate users | Availability | ReDoS, resource exhaustion, amplification attacks |
| Elevation of Privilege | Gaining capabilities beyond what is authorized | Authorization | IDOR, privilege escalation, JWT algorithm confusion |

### STRIDE Per Element

Not every threat applies to every element type. Applying STRIDE per element focuses analysis and avoids wasted effort.

| Element | Applicable Threats | Rationale |
|---------|-------------------|-----------|
| External entity | S, R | External entities can impersonate others and deny actions; they do not process or store data directly |
| Process | S, T, R, I, D, E | Processes execute logic and are exposed to the full threat surface |
| Data store | T, R, I, D | Stores hold data at rest; they can be tampered with, read, or made unavailable |
| Data flow | T, I, D | Data in transit can be intercepted, modified, or disrupted |
| Trust boundary | All | Crossing a trust boundary is the highest-risk event; apply all six categories |

### Conducting a STRIDE Analysis

Follow these steps in order. Do not skip the data flow diagram — it is the foundation of the analysis.

1. **Draw the data flow diagram.** Include all processes, data stores, external entities, data flows, and trust boundaries. Every element that handles, transforms, or transmits data must appear.
2. **Enumerate elements.** List each process, store, external entity, and flow as a row in a working document.
3. **Walk STRIDE per element.** For each element, apply the applicable threat categories from the table above. Ask: "How could an attacker exploit this element under this threat category?"
4. **Assess each identified threat.** For each threat, determine: likelihood (low/medium/high), impact (low/medium/high), and existing mitigations (none/partial/full).
5. **Prioritize.** Unmitigated threats that cross trust boundaries take priority. High-impact, low-mitigation threats come next.
6. **Document findings.** Record each threat with its element, category, likelihood, impact, current mitigation, and recommended remediation.
7. **Assign ownership.** Each finding must have an owner and a target resolution date before the session closes.

### STRIDE Mitigation Patterns

| Threat | Standard Mitigations |
|--------|---------------------|
| Spoofing | Strong authentication (MFA, certificate pinning), session binding, short-lived tokens |
| Tampering | Input validation, parameterized queries, HMAC signatures, integrity checks |
| Repudiation | Append-only audit logs, signed log entries, centralized log aggregation |
| Information Disclosure | Least-privilege access, encryption at rest and in transit, sanitized error messages |
| Denial of Service | Rate limiting, resource quotas, circuit breakers, input size limits |
| Elevation of Privilege | Least-privilege roles, RBAC enforcement, server-side authorization checks |

---

## PASTA (Process for Attack Simulation and Threat Analysis)

PASTA is a risk-centric, 7-stage methodology. It produces a full risk assessment rather than a threat list, making it suitable for compliance requirements and business stakeholder communication.

| Stage | Name | Activity | Output |
|-------|------|----------|--------|
| 1 | Business Objectives | Identify business-critical assets, data classifications, and regulatory constraints | Asset inventory, data classification matrix |
| 2 | Technical Scope | Map the technology stack, infrastructure components, and data flows | Architecture diagram, technology inventory |
| 3 | Application Decomposition | Identify entry points, trust boundaries, data stores, and privilege levels | Data flow diagrams, trust zone map |
| 4 | Threat Analysis | Identify threat agents, attack motivations, and threat intelligence relevant to the system | Threat actor profiles, threat scenarios |
| 5 | Vulnerability Analysis | Map known vulnerabilities (CVE, CWE) to identified assets and components | Vulnerability inventory with asset mapping |
| 6 | Attack Modeling | Build attack trees and kill chain scenarios for the highest-priority threats | Attack trees, exploit scenario narratives |
| 7 | Risk Analysis | Score residual risk, prioritize remediation, and produce a roadmap | Risk matrix, remediation roadmap with business justification |

### When PASTA vs STRIDE

| Factor | STRIDE | PASTA |
|--------|--------|-------|
| Time available | 2-4 hours | 1-2 days |
| Compliance requirement | No | Yes |
| Stakeholder audience | Engineering team | Engineering + business + compliance |
| Focus | Technical threats | Business risk |
| Output | Threat list with mitigations | Full risk assessment with roadmap |
| Suitable for | Feature-level and service-level analysis | System-level and pre-release audits |

Use STRIDE as the default. Escalate to PASTA when a compliance artifact is required, when business stakeholders need to participate, or when the system handles regulated data (PII, PHI, PCI).

---

## Attack Trees

An attack tree is a visual representation of how an attacker might achieve a goal. Use attack trees during PASTA Stage 6 or as a standalone tool when analyzing a specific high-risk threat.

### Structure

- **Root node:** The attacker's goal (e.g., "Steal user data", "Disrupt payment processing").
- **OR nodes:** Alternative methods to achieve the parent goal. Any one child succeeding achieves the parent.
- **AND nodes:** Prerequisites that must all be satisfied to achieve the parent goal.
- **Leaf nodes:** Atomic attack steps that require no further decomposition.

Label each leaf with an estimated difficulty (low/medium/high) and whether a known exploit exists. This enables prioritization without full risk scoring.

### Example: Access Admin Panel

```
Access admin panel (OR)
├── Exploit authentication bypass (AND)
│   ├── Discover login endpoint
│   └── Inject SQL into username field
├── Steal admin credentials (AND)
│   ├── Phish admin user via spear-phishing email
│   └── Replay stolen session token before expiry
└── Exploit authorization flaw (AND)
    ├── Authenticate as regular user
    └── Modify role parameter in API request (IDOR)
```

### Reading Attack Trees for Prioritization

- Paths with all low-difficulty leaves represent the highest-priority remediation targets.
- AND nodes increase attacker cost — adding a prerequisite raises the bar.
- OR nodes decrease attacker cost — each alternative path is an independent risk.
- Removing a single AND-node prerequisite can block an entire attack path.
- Removing an OR-node alternative reduces the attack surface but does not eliminate the threat.

---

## Trust Boundaries

A trust boundary exists wherever data crosses between components operating at different privilege or trust levels. Every trust boundary crossing is a potential attack surface. Enumerate all boundaries before conducting STRIDE analysis.

| Boundary | Example | What to Verify |
|----------|---------|----------------|
| Internet to web server | Inbound HTTP/S requests | Input validation, rate limiting, WAF rules, TLS configuration |
| Web server to database | SQL queries over internal network | Parameterized queries, least-privilege database user, network segmentation |
| Frontend to backend API | AJAX calls, form submissions | Authentication header, authorization check, schema validation |
| Microservice to microservice | Internal REST or gRPC calls | mTLS, service mesh authorization policy, input validation |
| User upload to file system | Multipart form file writes | File type validation, path traversal prevention, antivirus scanning |
| Third-party API to your service | Webhooks, OAuth callbacks | Signature verification, replay protection, input validation |
| Admin interface to production | Privileged management operations | MFA enforcement, IP allowlisting, audit logging |
| CI/CD pipeline to production | Deployment automation | Secret management, artifact signing, least-privilege deploy credentials |

### Trust Boundary Rules

- Validate all data crossing a trust boundary, regardless of the source's apparent trustworthiness.
- Never trust data from a lower-trust zone without explicit validation, even if it originated in a higher-trust zone.
- Authenticate and authorize at every boundary, not just at the perimeter.
- Log all trust boundary crossings for audit purposes.

---

## Data Flow Diagrams

A data flow diagram (DFD) is the primary artifact for threat modeling. Draw one before conducting any STRIDE or PASTA analysis.

### DFD Element Notation

| Element | Notation | Description |
|---------|----------|-------------|
| Process | Circle or rounded rectangle | A component that transforms or acts on data |
| Data store | Two parallel horizontal lines | Persistent storage: database, file system, cache |
| External entity | Rectangle | An actor or system outside the trust boundary of the application |
| Data flow | Labeled arrow | Data moving between elements; label with protocol and data type |
| Trust boundary | Dashed line | Separates zones of different trust levels |

### DFD Construction Rules

1. Start with external entities (users, third-party services, partner systems).
2. Trace each data flow from entry to storage to response.
3. Draw trust boundaries around logical trust zones, not physical infrastructure.
4. Label every data flow with the protocol (HTTPS, SQL, gRPC) and the data classification (PII, session token, public).
5. Include all data stores, even internal caches and message queues.
6. Keep the diagram at one level of abstraction. Use child diagrams to decompose complex processes.

### Example: Web Application DFD (Textual)

```
[User Browser] --HTTPS (credentials, form data)--> |Trust Boundary: Internet/DMZ|
    --> (Web Server / App Process)
            |
            +--SQL (parameterized queries)--> [[Primary Database]]
            |
            +--HTTPS (API request)--> |Trust Boundary: DMZ/External|
                    --> [Third-Party Payment API]
            |
            +--Redis protocol--> [[Session Cache]]

[Admin User] --HTTPS (admin credentials)--> |Trust Boundary: Admin/App|
    --> (Admin Process)
            |
            +--SQL (privileged queries)--> [[Primary Database]]
```

Each arrow in this diagram is a candidate data flow for STRIDE analysis. Each dashed boundary is a candidate trust boundary for full STRIDE coverage.

---

## Lightweight Threat Modeling

Use the 4-question framework (Shostack) for feature-level changes, pull request reviews, and time-constrained sessions. Target 30 minutes. Do not skip this for any change that introduces new external input, new data storage, or new trust boundary crossings.

### The 4 Questions

**1. What are we building?**
Write one paragraph describing the feature or change: what data it handles, what systems it touches, and what users interact with it. This scopes the analysis and surfaces assumptions.

**2. What can go wrong?**
Brainstorm 5-10 threats in 15 minutes. Use STRIDE categories as prompts if the team is stuck. Do not filter during brainstorming — capture everything, then triage.

**3. What are we doing about it?**
For each identified threat, map it to an existing control (authentication, validation, rate limiting) or identify a new control that must be added before shipping.

**4. Did we do a good job?**
Review the output with at least one other team member. Ask: "Is there a threat we missed? Is there a control we assumed exists but have not verified?"

### Lightweight Session Output

Capture the output in a short document or pull request comment:

```
Feature: [name]
Date: [date]
Participants: [names]

Threats identified:
1. [Threat] — [Mitigation / Owner]
2. [Threat] — [Mitigation / Owner]
...

Open items:
- [Any unresolved threat or control gap]
```

Attach this output to the pull request or design document. It serves as a lightweight audit trail and prompts reviewers to verify that identified mitigations were implemented.

---

## Threat Modeling Anti-Patterns

Avoid these failure modes that reduce the value of threat modeling sessions.

| Anti-Pattern | Consequence | Correction |
|-------------|-------------|------------|
| Modeling after implementation | Findings are expensive to fix; teams resist changes | Run threat modeling during design, before code is written |
| No data flow diagram | Analysis is vague and misses data stores and flows | Always draw the DFD first, even a rough sketch |
| Treating all threats as equal | High-risk items are buried in low-risk noise | Score likelihood and impact; prioritize unmitigated trust boundary crossings |
| No ownership assigned | Findings are documented but never remediated | Every finding must have a named owner and a target date |
| One-time activity | System evolves but threat model does not | Re-run threat modeling on every significant architectural change |
| Security team only | Engineers lack context; findings are disconnected from implementation | Include the engineers who will implement the mitigations |
