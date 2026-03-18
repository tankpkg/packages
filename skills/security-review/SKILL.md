---
name: "@tank/security-review"
description: |
  Comprehensive security review for any codebase, PR, or architecture.
  Covers OWASP Top 10 (2021) and API Security Top 10 (2023), CWE Top 25,
  code review methodology (differential and full audit), SAST tools
  (Semgrep, CodeQL, Bandit, ESLint security), dependency and supply chain
  scanning (npm audit, Trivy, Snyk, OSV-Scanner, SBOM), secret detection
  (Gitleaks, TruffleHog), IaC scanning (Checkov, tfsec), threat modeling
  (STRIDE, PASTA), language-specific vulnerability patterns (JS/TS, Python,
  Go, Rust, Java), and remediation patterns for every vulnerability class.
  Synthesizes OWASP Foundation standards, MITRE CWE, NIST NVD, Trail of
  Bits audit methodology, Shostack (Threat Modeling), and OWASP Testing
  Guide (WSTG v5).

  Trigger phrases: "security review", "security audit", "OWASP",
  "vulnerability", "CVE", "CWE", "code audit", "penetration test",
  "threat model", "STRIDE", "PASTA", "Semgrep", "CodeQL", "SAST",
  "DAST", "dependency scan", "npm audit", "Trivy", "Snyk", "Gitleaks",
  "TruffleHog", "secret scanning", "supply chain", "XSS", "SQL injection",
  "SSRF", "CSRF", "IDOR", "injection", "deserialization", "Checkov",
  "tfsec", "IaC security", "security scanning", "secure code review",
  "attack surface", "SBOM", "ASVS", "security checklist"
---

# Security Review

## Core Philosophy

1. **High confidence only** — Flag findings where you are >80% confident of real exploitability. Theoretical issues, style concerns, and low-impact findings waste reviewer trust. One confirmed RCE matters more than twenty speculative XSS.
2. **Static tools first, human judgment second** — Run Semgrep/CodeQL/Gitleaks before manual review. Tools catch the mechanical bugs; the reviewer's time is for logic flaws, auth bypasses, and design-level issues that tools miss.
3. **Fix patterns, not instances** — When you find one SQL injection, search for the pattern across the codebase. A vulnerability is a symptom; the missing input validation framework is the disease.
4. **Defense in depth** — No single control is sufficient. Validate inputs AND encode outputs AND use parameterized queries AND enforce least privilege. Each layer catches what the previous one misses.
5. **Shift left, but verify right** — Integrate scanning into CI/CD, but run a full audit before major releases. Pre-commit hooks catch secrets; production monitoring catches what pre-commit missed.

## Quick-Start: Common Problems

### "Review this PR for security"

1. Get the diff: `git diff main...HEAD` or the PR diff
2. Classify changed files by risk (auth, payments, user input, config > UI, docs, tests)
3. For each high-risk file, check against → `references/code-review-workflow.md`
4. Run targeted SAST: `semgrep scan --config p/security-audit --diff-depth 0`
5. Check for new dependencies → `references/dependency-and-supply-chain.md`
6. Report only >80% confidence findings with severity, location, and fix suggestion

### "Run a full security audit"

1. Map the attack surface: entry points, trust boundaries, data flows
2. Run automated scans: SAST + dependency + secrets + IaC
3. Manual review: auth flows, business logic, crypto usage, session handling
4. Threat model critical components → `references/threat-modeling.md`
5. Prioritize findings by exploitability × impact
6. Write report → `references/code-review-workflow.md` (report format section)

### "Check for OWASP issues"

1. Identify the target type (web app, API, mobile backend)
2. Select the relevant list: OWASP Top 10 (web) or API Security Top 10
3. Walk through each category against the codebase
→ See `references/owasp-vulnerability-taxonomy.md`

### "Scan dependencies for vulnerabilities"

1. Detect package manager (package.json, requirements.txt, go.mod, Cargo.toml)
2. Run the appropriate scanner: `npm audit`, `pip-audit`, `trivy fs .`
3. Triage: fixable vs unfixable, exploitable vs theoretical, direct vs transitive
→ See `references/dependency-and-supply-chain.md`

### "Set up security scanning in CI"

1. Add SAST (Semgrep) → non-blocking initially, blocking after baseline
2. Add dependency scanning (Trivy or npm audit) → block on critical/high
3. Add secret scanning (Gitleaks) → always blocking
4. Add IaC scanning if applicable (Checkov) → block on high
→ See `references/sast-and-scanning-tools.md` and `references/secrets-and-iac-scanning.md`

### "Find secrets in the codebase"

1. Run `gitleaks detect --source . --verbose` (includes git history)
2. Run `trufflehog filesystem . --only-verified` (verifies credentials are live)
3. For pre-commit prevention: `pre-commit install` with gitleaks hook
→ See `references/secrets-and-iac-scanning.md`

## Decision Trees

### Which Review Depth?

| Signal | Depth | Time |
|--------|-------|------|
| Small PR, no auth/payment/input changes | Quick scan — SAST + dependency check | 10 min |
| PR touches auth, sessions, payments, crypto | Targeted review — manual + automated | 1 hour |
| New feature with external input | Full feature review — threat model + manual | 2-4 hours |
| Pre-release audit, compliance requirement | Full audit — all tools + manual + report | 1-3 days |

### Which SAST Tool?

| Need | Tool | Why |
|------|------|-----|
| Fast, broad coverage, custom rules | Semgrep | Pattern-based, 30+ languages, free tier |
| Deep data flow / taint tracking | CodeQL | Interprocedural analysis, 166 CWEs, GitHub-native |
| Python-specific | Bandit | AST-based, Python-only, fast |
| JavaScript/TypeScript linting | eslint-plugin-security + no-unsanitized | Integrates with existing ESLint |
| Quick pattern matching | ast-grep | YAML rules, fast, multi-language |

### Which Dependency Scanner?

| Ecosystem | Tool | Command |
|-----------|------|---------|
| Node.js | npm audit / Trivy | `npm audit --audit-level=high` |
| Python | pip-audit / Trivy | `pip-audit --strict` |
| Go | govulncheck / Trivy | `govulncheck ./...` |
| Rust | cargo-audit | `cargo audit` |
| Multi-ecosystem | Trivy | `trivy fs --scanners vuln .` |
| Enterprise / paid | Snyk | `snyk test` |

## Exclusions

These are handled by other skills or processes — do not duplicate:
- **Auth patterns** (JWT, OAuth2, session design) → `@tank/auth-patterns`
- **Container security** (image scanning, cosign, SBOM signing) → `@solaraai/devops-mastery`
- **macOS system security** (SIP, Gatekeeper, FileVault) → `@tank/macos-maintenance`
- **DOS/rate limiting** — typically operational, not code review scope
- **Secrets already on disk** — handled by secret managers, not review

## Reference Files

| File | Contents |
|------|----------|
| `references/owasp-vulnerability-taxonomy.md` | OWASP Top 10 (2021), API Security Top 10 (2023), CWE Top 25 (2024), ASVS verification levels, vulnerability classification with code examples |
| `references/code-review-workflow.md` | Differential (PR) review methodology, full audit workflow, attack surface mapping, >80% confidence threshold, finding classification (severity/exploitability), report format, review anti-patterns |
| `references/sast-and-scanning-tools.md` | Semgrep (configs, custom rules, CI), CodeQL (query suites, MRVA), Bandit, ESLint security, ast-grep rules. Tool selection, result interpretation, false positive triage, CI pipeline setup |
| `references/dependency-and-supply-chain.md` | npm audit, pip-audit, cargo-audit, govulncheck, Trivy, Snyk, OSV-Scanner. SBOM generation (CycloneDX/SPDX). Lock file analysis, typosquatting, supply chain attack patterns |
| `references/secrets-and-iac-scanning.md` | Gitleaks, TruffleHog, detect-secrets for secret detection. Checkov, tfsec, KICS for IaC. Pre-commit hooks, CI integration, incident response for leaked secrets |
| `references/language-vulnerability-patterns.md` | Common vulns per language: JS/TS (XSS, prototype pollution, ReDoS), Python (SSTI, pickle, command injection), Go (race conditions, integer overflow), Rust (unsafe, FFI), Java (deserialization, JNDI injection) |
| `references/threat-modeling.md` | STRIDE framework, PASTA methodology (7 stages), attack trees, trust boundaries, data flow diagrams, when to threat model, lightweight vs formal approaches |
| `references/remediation-patterns.md` | Fix patterns per vulnerability class: input validation, output encoding, parameterized queries, CSP/CORS headers, secure defaults, crypto best practices, safe deserialization, secure file handling |
