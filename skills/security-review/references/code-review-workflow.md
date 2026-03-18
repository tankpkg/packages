# Security Code Review Workflow

Sources: OWASP Web Security Testing Guide (WSTG v5), Trail of Bits audit methodology, McGraw (Software Security), Howard/LeBlanc (Writing Secure Code)

Covers: Differential (PR/MR) review methodology, full audit workflow, attack surface mapping, confidence and severity classification, finding report format, and common review anti-patterns.

---

## Differential Review (PR/MR)

A differential review targets the changed lines in a pull request. The goal is to identify security regressions introduced by the change — not to audit the entire codebase.

### Step 1: Risk-Classify Changed Files

Before reading a single line of code, classify each changed file by risk tier. Spend review time proportional to risk.

| Risk Tier | File Categories | Review Depth |
|-----------|----------------|--------------|
| Critical | Authentication, authorization, session management, payment processing, cryptographic operations | Full manual review + SAST |
| High | Input handling, API endpoints, database queries, file upload/download, OAuth flows | Manual review of changed logic + SAST |
| Medium | Business logic, configuration files, third-party integrations, admin interfaces | Spot-check changed logic |
| Low | UI components, documentation, test files, static assets, build scripts | Skim for secrets only |

Apply this classification before opening any file. If a PR touches only Low-tier files, a secrets scan and a 5-minute skim is sufficient. If it touches Critical-tier files, allocate full review time.

### Step 2: Check New Dependencies

Every new dependency is a supply chain risk. For each new package added to a manifest file:

1. Verify the package name matches the intended library (typosquatting check).
2. Check the package's publish date and download count — newly published packages with few downloads warrant extra scrutiny.
3. Run the dependency against a known-vulnerability database (see `sast-and-scanning-tools.md` for SCA tooling).
4. Check whether the dependency is pinned to an exact version or a range. Ranges allow silent upgrades to malicious versions.
5. Flag any dependency that requests unusual permissions (native addons, network access in build scripts).

### Step 3: Scan the Diff for Secrets

Run a secrets scanner against the diff before any manual review. Do not rely on visual inspection alone — encoded secrets, split strings, and environment variable names that shadow real values are easy to miss.

Patterns that require manual verification even if the scanner passes:

- Strings matching `[A-Za-z0-9+/]{40,}` (base64-encoded blobs)
- Hex strings of length 32, 40, 64 (MD5, SHA1, SHA256 hashes used as keys)
- Any string assigned to a variable named `key`, `secret`, `token`, `password`, `credential`, `api_key`, or `private`
- Hardcoded IP addresses or internal hostnames in non-test code

### Step 4: Manual Review of High-Risk Files

For every Critical or High-tier file, apply the following checklist. Each item is a binary pass/fail.

#### PR Security Checklist

| # | Category | Check | Pass Criteria |
|---|----------|-------|---------------|
| 1 | Input Handling | All new endpoint parameters are validated before use | Validation present, not just type coercion |
| 2 | Input Handling | Validation rejects unexpected types, not just sanitizes | Allowlist or strict schema, not denylist |
| 3 | Input Handling | File upload handlers check MIME type server-side | Content-Type header alone is insufficient |
| 4 | Input Handling | Path parameters are not used in filesystem operations without normalization | `path.resolve` + prefix check or equivalent |
| 5 | Input Handling | SQL/NoSQL queries use parameterized statements or ORM | No string concatenation into queries |
| 6 | Input Handling | XML/HTML parsers have entity expansion disabled | XXE prevention configured |
| 7 | Auth | New endpoints have explicit authorization checks | Not relying on middleware that may be bypassed |
| 8 | Auth | Authorization checks verify the acting user owns the resource | IDOR prevention: check `resource.owner == current_user` |
| 9 | Auth | Privilege-escalation paths require re-authentication | Sensitive actions prompt for password/MFA |
| 10 | Auth | New tokens or session identifiers are generated with a CSPRNG | Not `Math.random()`, `rand()`, or timestamp-based |
| 11 | Auth | Password comparison uses constant-time equality | Not `==` or `===` on raw strings |
| 12 | Crypto | New cryptographic operations use approved algorithms | AES-GCM, ChaCha20-Poly1305, RSA-OAEP, Ed25519 |
| 13 | Crypto | Encryption keys are not derived from low-entropy sources | No `md5(password)` as key |
| 14 | Crypto | IVs and nonces are generated fresh per operation | Not reused, not hardcoded |
| 15 | Data Exposure | Error responses do not include stack traces, SQL errors, or internal paths | Generic error messages in production paths |
| 16 | Data Exposure | Logging statements do not record PII, credentials, or session tokens | Scrub before log |
| 17 | Data Exposure | API responses do not include fields the caller is not authorized to see | Explicit field allowlist, not object serialization |
| 18 | Data Exposure | Redirects use an allowlist of permitted destinations | Open redirect prevention |
| 19 | Config | New feature flags or config values have secure defaults | Default is deny, not allow |
| 20 | Config | CORS configuration is not set to `*` for credentialed requests | Explicit origin allowlist |
| 21 | Config | New HTTP endpoints set appropriate security headers | CSP, X-Frame-Options, HSTS where applicable |
| 22 | Config | Dependency versions are pinned in lockfiles | No floating ranges in production manifests |
| 23 | Output | User-controlled data rendered in HTML is escaped | Context-aware encoding, not just `htmlspecialchars` |
| 24 | Output | User-controlled data in JSON responses is not reflected into `<script>` blocks | JSON encoding is not HTML encoding |
| 25 | Output | Template engines have auto-escaping enabled | Not disabled for convenience |

### Step 5: Run Targeted SAST

Run static analysis scoped to the changed files only. Full-codebase scans during PR review produce noise from pre-existing issues. Pass the diff or the list of changed file paths to the scanner.

Prioritize rules covering: injection (SQL, command, LDAP, XPath), deserialization, path traversal, hardcoded credentials, insecure randomness, and weak cryptography.

Suppress findings that are not in the changed lines unless they are in a function directly called by the changed code.

### Step 6: Apply the Confidence Threshold

Report only findings where you are confident the issue is exploitable in the current context.

| Confidence | Action |
|------------|--------|
| > 80% | Report as a finding. Include proof of concept. |
| 50–80% | Add as a review comment requesting clarification. Do not block the PR. |
| < 50% | Do not report. Note internally for full audit if the file is revisited. |

A finding is high-confidence when: the vulnerable code path is reachable from an untrusted input, no compensating control exists elsewhere in the call chain, and you can describe the exploit steps without assuming additional preconditions.

---

## Full Audit Workflow

A full audit examines the entire codebase, not just recent changes. Use this workflow for pre-release security assessments, third-party audits, and post-incident reviews.

### Phase 1: Scope and Reconnaissance

Define what is in scope before writing a single note.

- Identify the application's primary function and the data it handles (PII, financial, health, credentials).
- Document the tech stack: language, framework, database, cache, message queue, cloud provider.
- Obtain architecture diagrams, API documentation, and threat model if they exist.
- Identify the trust boundaries: what is public-facing, what is internal, what is admin-only.
- Agree on out-of-scope items in writing (third-party SaaS, infrastructure not owned by the team).

Deliverable: a one-page scope document listing in-scope components, data classifications, and known threat actors.

### Phase 2: Attack Surface Mapping

Enumerate every point where untrusted data enters the system. Do not begin reviewing code until this map is complete.

See the Attack Surface Analysis section below for the full entry point taxonomy.

Deliverable: a table of entry points, their trust level, and the data they accept.

### Phase 3: Automated Scanning

Run all four scanner categories against the full codebase. Triage results before manual review to avoid duplicating effort.

| Scanner Type | What It Finds | When to Run |
|-------------|---------------|-------------|
| SAST | Code-level vulnerabilities: injection, path traversal, insecure APIs | Before manual review |
| SCA | Known CVEs in dependencies | Before manual review |
| Secrets | Hardcoded credentials, API keys, private keys | Before manual review |
| IaC | Misconfigured cloud resources, overly permissive IAM, open security groups | Before manual review |

Triage automated findings into: confirmed (will report), needs-manual-verification, and false-positive. Do not carry unverified automated findings into the report.

### Phase 4: Manual Review

Manual review covers what automated tools cannot: business logic flaws, authorization model correctness, and cryptographic protocol design.

Prioritize in this order:

1. **Authentication flows** — registration, login, password reset, MFA enrollment, session termination. Trace each flow end-to-end.
2. **Authorization model** — identify every permission check in the codebase. Verify that every sensitive operation has one. Look for checks that can be bypassed by manipulating object IDs, role parameters, or request headers.
3. **Business logic** — identify operations that have financial, legal, or safety consequences. Ask: can these be triggered out of order? Can they be triggered by an unauthorized user? Can they be triggered more times than intended?
4. **Cryptographic operations** — review every use of encryption, hashing, signing, and random number generation. Verify algorithm choice, key management, and IV/nonce handling.
5. **Session handling** — verify session tokens are invalidated on logout, privilege change, and password reset. Check for session fixation vectors.
6. **Data flows for sensitive data** — trace PII and credentials from entry to storage to deletion. Verify encryption at rest and in transit.

### Phase 5: Finding Validation

Before writing a finding, validate it.

1. Confirm the vulnerable code path is reachable from an untrusted input.
2. Identify any compensating controls in the call chain (WAF rules, middleware, framework defaults).
3. Reproduce the issue in a test environment or construct a proof of concept that demonstrates exploitability.
4. Rate severity using the criteria in the Confidence and Severity section below.
5. Discard findings that cannot be reproduced or where compensating controls fully mitigate the risk.

Do not report theoretical vulnerabilities without evidence of reachability.

### Phase 6: Reporting

Structure each finding using the format in the Report Format section below. Organize the report as:

1. Executive summary (1 page): overall risk posture, critical finding count, key themes.
2. Findings (one page per finding): full detail per the standard format.
3. Appendix: scope, methodology, tool versions, out-of-scope items.

Deliver a draft to the development team for factual corrections before finalizing. Do not accept requests to downgrade severity without a documented technical justification.

---

## Attack Surface Analysis

Map every entry point before reviewing code. An entry point is any location where data from an untrusted source enters the application.

| Entry Point Type | Trust Level | Key Checks |
|-----------------|-------------|------------|
| HTTP REST endpoints | Untrusted | Input validation, auth check, rate limiting, output encoding |
| GraphQL resolvers | Untrusted | Query depth/complexity limits, field-level auth, introspection disabled in prod |
| WebSocket handlers | Untrusted | Auth on connection upgrade, message validation, per-message auth if stateless |
| Message queue consumers | Semi-trusted | Schema validation, idempotency, poison message handling |
| Cron jobs / scheduled tasks | Internal | Verify no user-controlled input reaches the job; check for TOCTOU |
| CLI commands | Varies | Argument injection, shell metacharacter handling, privilege level |
| File upload handlers | Untrusted | MIME validation server-side, filename sanitization, storage outside webroot, virus scan |
| OAuth callbacks | Untrusted | State parameter validation, code-for-token exchange server-side, redirect URI allowlist |
| Webhook receivers | Semi-trusted | Signature verification before processing, replay protection |
| Admin interfaces | Privileged | Separate auth domain, IP allowlist, audit logging |
| Import/export features | Untrusted | CSV injection, XML/ZIP bomb, path traversal in archive extraction |
| Third-party SDK callbacks | Semi-trusted | Validate data from SDK before use; do not trust SDK-provided identity claims |

For each entry point, trace the data flow to: database queries, filesystem operations, subprocess calls, template rendering, and external API calls. These are the sinks where injection vulnerabilities manifest.

---

## Confidence and Severity

### Confidence Thresholds

| Confidence Level | Criteria | Action |
|-----------------|----------|--------|
| High (> 80%) | Reachable from untrusted input, no compensating control, exploit steps are clear | Report as finding |
| Medium (50–80%) | Reachable but compensating control may exist, or exploit requires specific conditions | Note for follow-up; request clarification |
| Low (< 50%) | Theoretical, not confirmed reachable, or fully mitigated | Do not report |

### Severity Ratings

| Severity | Examples | Business Impact |
|----------|----------|----------------|
| Critical | Remote code execution, authentication bypass, mass data breach, privilege escalation to admin without credentials | Immediate exploitation likely; system compromise or data loss |
| High | Privilege escalation requiring valid account, stored XSS in admin panel, SQL injection with limited data access, SSRF to internal network | Significant damage possible; exploitation requires some effort |
| Medium | Reflected XSS, CSRF on sensitive actions, insecure direct object reference, sensitive data in logs, missing rate limiting on auth endpoints | Moderate damage; exploitation requires user interaction or specific conditions |
| Low | Verbose error messages, missing security headers, weak password policy, information disclosure in non-sensitive endpoints | Limited direct impact; increases attack surface or aids reconnaissance |
| Informational | Best practice deviations, deprecated API usage, missing audit logging | No direct exploitability; improves security posture if addressed |

### Exploitability Factors

Adjust severity up or down based on these factors:

| Factor | Severity Adjustment |
|--------|-------------------|
| Network-accessible without authentication | +1 tier |
| Authentication required | -1 tier |
| User interaction required (e.g., victim must click a link) | -1 tier |
| Exploit is publicly known or tooled | +1 tier |
| Data affected is regulated (PII, PCI, PHI) | +1 tier |
| Compensating control partially mitigates | -1 tier |

Do not adjust below Informational or above Critical.

---

## Report Format

Use this structure for every finding. Consistency enables developers to triage and remediate efficiently.

### Finding Template

```
Title:       [Concise description of the vulnerability, e.g., "SQL Injection in User Search Endpoint"]
Severity:    [Critical | High | Medium | Low | Informational]
Confidence:  [High | Medium | Low]
CWE:         CWE-[ID]: [Name]
Location:    [file path]:[line number(s)]

Description:
[2–4 sentences explaining what the vulnerability is, where it exists, and why it is dangerous.
Do not describe how to fix it here.]

Proof of Concept:
[Step-by-step instructions to reproduce the issue, or a code snippet demonstrating exploitability.
Include the exact request, payload, or code path. If a test environment is required, note it.]

Remediation:
[Specific, actionable fix instructions. Reference the relevant pattern in remediation-patterns.md.
Include a corrected code snippet where the fix is non-obvious.]

References:
- OWASP WSTG: [section ID and URL]
- CWE: https://cwe.mitre.org/data/definitions/[ID].html
- [Additional references as needed]
```

### Sample Finding

```
Title:       SQL Injection in User Search Endpoint
Severity:    High
Confidence:  High
CWE:         CWE-89: Improper Neutralization of Special Elements used in an SQL Command
Location:    src/api/users/search.js:47

Description:
The user search endpoint constructs a SQL query by concatenating the `q` query parameter
directly into the query string without parameterization. An attacker can inject arbitrary
SQL to extract data from any table accessible to the database user, modify records, or
in some configurations execute operating system commands.

Proof of Concept:
  GET /api/users/search?q=' UNION SELECT username,password,null FROM admin_users--

  Expected response includes admin credentials from the admin_users table.
  Tested against staging environment on 2026-03-15.

Remediation:
Replace string concatenation with a parameterized query:

  // Vulnerable
  const query = `SELECT * FROM users WHERE name LIKE '%${req.query.q}%'`;

  // Fixed
  const query = 'SELECT * FROM users WHERE name LIKE ?';
  db.execute(query, [`%${req.query.q}%`]);

See remediation-patterns.md § SQL Injection for ORM-specific patterns.

References:
- OWASP WSTG: WSTG-INPV-05 — https://owasp.org/www-project-web-security-testing-guide/
- CWE: https://cwe.mitre.org/data/definitions/89.html
```

---

## Review Anti-Patterns

Avoid these failure modes. Each one produces reviews that miss real vulnerabilities or waste reviewer time.

| Anti-Pattern | Description | Consequence | Correction |
|-------------|-------------|-------------|------------|
| Rubber-stamping | Approving a PR without reading the diff, relying on CI passing | Security regressions ship undetected | Apply the risk classification step; never approve without reading Critical/High-tier files |
| Tool-only review | Running a scanner and reporting its output without manual verification | High false-positive rate; developers lose trust in security reviews | Validate every automated finding before reporting; manual review is mandatory for auth and business logic |
| Scope creep | Auditing the entire codebase during a PR review | Review takes too long; blocks development; reviewer fatigue | Scope PR reviews to changed files and their direct callers only |
| False positive fatigue | Reporting low-confidence findings to appear thorough | Developers ignore security comments; real findings are buried | Apply the 80% confidence threshold strictly; fewer, higher-quality findings |
| Diff-only blindness | Reviewing only the changed lines without understanding the surrounding context | Missing vulnerabilities where the change removes a compensating control | Read the full function and its callers for any Critical/High-tier change |
| Missing business logic | Focusing exclusively on injection and XSS; ignoring authorization and workflow flaws | Business logic bugs (IDOR, privilege escalation, race conditions) ship undetected | Explicitly review authorization checks and state machine transitions in every audit |
| Severity inflation | Rating every finding as Critical to ensure it gets fixed | Developers deprioritize security work; credibility erodes | Apply severity criteria strictly; reserve Critical for RCE, auth bypass, and mass data breach |
| No proof of concept | Reporting a finding without demonstrating exploitability | Developers dispute findings; remediation is deprioritized | Reproduce every High and Critical finding before reporting |
| Ignoring compensating controls | Reporting a vulnerability that is fully mitigated by a WAF rule or framework default | Wasted developer time; erodes trust | Trace the full call chain including middleware before reporting |
| Skipping the threat model | Reviewing code without understanding who the adversary is | Effort spent on low-risk paths; high-risk paths missed | Complete Phase 1 (scope and reconnaissance) before any code review |
