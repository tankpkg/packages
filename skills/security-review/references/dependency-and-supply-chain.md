# Dependency and Supply Chain Security

Sources: OWASP Dependency-Check documentation, Trivy documentation, npm audit documentation, SLSA specification, Sonatype State of the Software Supply Chain (2024)

Covers: Software Composition Analysis (SCA) by ecosystem, SBOM generation, supply chain attack patterns and detection, lock file hygiene, and a structured triage workflow for dependency vulnerabilities.

---

## Dependency Scanning by Ecosystem

Run SCA scans on every pull request and in CI. Treat HIGH and CRITICAL findings as blocking by default; establish a documented exception process for accepted risks.

| Ecosystem | Primary Tool | Command | Alternative |
|-----------|-------------|---------|-------------|
| Node.js | npm audit | `npm audit --audit-level=high` | Snyk, Trivy |
| Python | pip-audit | `pip-audit --strict` | Safety, Trivy |
| Go | govulncheck | `govulncheck ./...` | Trivy |
| Rust | cargo-audit | `cargo audit` | Trivy |
| Java/Kotlin | OWASP Dependency-Check | `dependency-check --scan .` | Trivy, Snyk |
| .NET | dotnet list package | `dotnet list package --vulnerable` | Snyk |
| Multi-ecosystem | Trivy | `trivy fs --scanners vuln .` | Grype, Snyk |

### Trivy (Universal Scanner)

Trivy is the recommended default for multi-ecosystem and container scanning. It covers OS packages, language dependencies, IaC misconfigurations, and secrets in a single binary.

**Installation:**

```bash
# macOS
brew install trivy

# Linux (script)
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Docker (no install required)
docker run --rm -v "$(pwd)":/workspace aquasec/trivy fs /workspace
```

**Core scanning modes:**

```bash
# Filesystem scan — all supported ecosystems under current directory
trivy fs .

# Container image scan
trivy image myapp:latest

# Remote git repository
trivy repo https://github.com/org/repo

# IaC configuration scan (Terraform, Kubernetes, Dockerfile)
trivy config .
```

**Severity filtering — only report HIGH and CRITICAL:**

```bash
trivy fs --severity HIGH,CRITICAL .
trivy image --severity HIGH,CRITICAL myapp:latest
```

**Ignoring accepted risks with `.trivyignore`:**

Create `.trivyignore` at the repository root. Each line is a CVE ID or Trivy finding ID to suppress. Document the reason in a comment.

```
# CVE-2023-12345: affects only the CLI entrypoint, not reachable in production
CVE-2023-12345

# Accepted risk: no fix available, mitigated by WAF rule WR-42
CVE-2024-67890
```

**CI integration (GitHub Actions):**

```yaml
- name: Run Trivy vulnerability scan
  uses: aquasecurity/trivy-action@0.28.0
  with:
    scan-type: fs
    scan-ref: .
    severity: HIGH,CRITICAL
    exit-code: 1
    ignore-unfixed: true
    format: sarif
    output: trivy-results.sarif

- name: Upload Trivy results to GitHub Security tab
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: trivy-results.sarif
```

### npm audit Specifics

**Understand the three invocation modes:**

```bash
# Report only — exits non-zero if vulnerabilities at or above threshold
npm audit --audit-level=high

# Apply safe, non-breaking upgrades automatically
npm audit fix

# Apply breaking upgrades (semver major bumps) — review diff carefully
npm audit fix --force
```

`npm audit fix --force` can introduce breaking API changes. Always review the resulting diff and run the full test suite before merging.

**Advisory severity levels:** `critical`, `high`, `moderate`, `low`. Set CI gates at `high` minimum. Treat `critical` as P0.

**Patching transitive dependencies with `overrides`:**

When a transitive dependency has a vulnerability and the direct dependency has not yet released a fix, use the `overrides` field in `package.json` to force a patched version:

```json
{
  "overrides": {
    "vulnerable-transitive-package": ">=2.3.1"
  }
}
```

Verify the override does not break the dependent package's behavior. Remove the override once the direct dependency ships a fix.

**Verifying package provenance:**

```bash
# Verify registry signatures for all installed packages
npm audit signatures
```

This checks that packages were signed by the npm registry and have not been tampered with post-publish. Run this in CI alongside `npm audit`.

### pip-audit

```bash
# Install
pip install pip-audit

# Scan current environment
pip-audit

# Strict mode — exit non-zero on any vulnerability
pip-audit --strict

# Scan a requirements file without installing
pip-audit -r requirements.txt

# Output JSON for downstream processing
pip-audit --format json --output audit.json
```

### govulncheck (Go)

`govulncheck` uses the Go vulnerability database and performs call-graph analysis to report only vulnerabilities in code paths that are actually reachable.

```bash
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```

Unreachable vulnerabilities are reported at a lower severity. Prioritize findings where `govulncheck` confirms the vulnerable symbol is called.

### OWASP Dependency-Check (Java/Kotlin)

```bash
# CLI scan
dependency-check --scan . --format HTML --out reports/

# Maven plugin
mvn org.owasp:dependency-check-maven:check

# Gradle plugin (build.gradle)
# apply plugin: 'org.owasp.dependencycheck'
# dependencyCheck { failBuildOnCVSS = 7 }
```

The NVD data feed requires an API key for reliable updates. Set `NVD_API_KEY` in CI and pass `--nvdApiKey $NVD_API_KEY`.

---

## SBOM Generation

An SBOM (Software Bill of Materials) is a complete, machine-readable inventory of all components in a software artifact, including direct and transitive dependencies, their versions, and their licenses.

**Why generate SBOMs:** Rapid CVE impact assessment (query the SBOM when a new CVE is published); license compliance (identify GPL/AGPL before production); regulatory compliance (US EO 14028, EU CRA); incident response evidence.

**SBOM formats:**

| Format | Standard Body | Best For |
|--------|---------------|----------|
| CycloneDX | OWASP | Security analysis, CVE correlation, VEX |
| SPDX | Linux Foundation | License compliance, legal review |

Prefer CycloneDX for security workflows; use SPDX when legal or procurement teams require it.

**Generation commands:**

```bash
# CycloneDX for Node.js
npx @cyclonedx/cyclonedx-npm --output-file sbom.json

# CycloneDX for Python
pip install cyclonedx-bom
cyclonedx-py environment --output-format json > sbom.json

# Trivy SBOM output (multi-ecosystem)
trivy fs --format cyclonedx --output sbom.json .

# Syft (universal, supports 50+ ecosystems)
# Install: brew install syft
syft . -o cyclonedx-json > sbom.json
syft . -o spdx-json > sbom-spdx.json

# Attach SBOM to container image as OCI attestation
syft myapp:latest -o cyclonedx-json | \
  cosign attest --predicate - --type cyclonedx myapp:latest
```

**Querying an SBOM for a specific CVE:**

```bash
# Using grype against a CycloneDX SBOM
grype sbom:./sbom.json

# Using OSV-Scanner against a CycloneDX SBOM
osv-scanner --sbom sbom.json
```

Store SBOMs as CI artifacts, regenerate on every release, and version-control them alongside the release tag.

---

## Supply Chain Attack Patterns

Supply chain attacks target the build pipeline, package registry, or dependency graph rather than the application directly. A single compromised package can affect thousands of downstream consumers.

| Attack Type | Mechanism | Real-World Example |
|-------------|-----------|-------------------|
| Typosquatting | Publish a package with a name similar to a popular package | `ua-parser-js` (2021), `colors.js` protest injection |
| Dependency confusion | Register a public package matching a private internal package name | Alex Birsan research (2021), affected Microsoft, Apple, PayPal |
| Compromised maintainer | Attacker gains control of a legitimate maintainer account | `event-stream` (2018) — malicious code injected via new maintainer |
| Malicious CI action | Compromise a GitHub Action used in thousands of pipelines | `tj-actions/changed-files` CVE-2025-30066 — secrets exfiltrated |
| Build system poisoning | Compromise the build infrastructure itself | SolarWinds SUNBURST (2020) — trojanized build output |
| Protestware | Maintainer intentionally injects malicious or disruptive code | `node-ipc` (2022) — deleted files on Russian/Belarusian IPs |

### Lock File Analysis

Lock files (`package-lock.json`, `yarn.lock`, `Pipfile.lock`, `go.sum`, `Cargo.lock`) pin exact resolved versions and integrity hashes. They are the primary defense against version-range attacks.

**Rules:**

- Always commit lock files. Never add them to `.gitignore`.
- Use `npm ci` in CI, not `npm install`. `npm ci` installs exactly what the lock file specifies and fails if `package.json` and the lock file are out of sync.
- Review lock file diffs in every pull request. An unexpected new dependency or a version change in a transitive package is a signal worth investigating.
- Verify `integrity` fields in `package-lock.json` are present and use `sha512`. A missing or `sha1`-only integrity hash is a red flag.

```bash
# Reproducible install in CI
npm ci

# Detect lock file drift (fails if lock file would change)
npm install --frozen-lockfile   # yarn
pip install --require-hashes -r requirements.txt  # pip
```

**Reviewing lock file diffs:** When a PR modifies `package-lock.json`, verify: (1) the change was intentional; (2) no new packages appear that are absent from `package.json`; (3) no existing package changed its resolved URL or integrity hash without a version bump.

### Detection and Prevention

**Pin GitHub Actions by commit SHA:**

```yaml
# Vulnerable — tag can be moved to a different commit
- uses: actions/checkout@v4

# Safe — SHA is immutable
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
```

Use a tool such as `pin-github-action` or Dependabot's `github-actions` ecosystem support to automate SHA pinning and updates.

**Verify npm package provenance:**

```bash
npm audit signatures
```

Packages published with provenance attestations (npm 9.5+) include a link to the source repository and CI run that produced them. Verify provenance for critical dependencies.

**SLSA provenance verification:**

SLSA (Supply-chain Levels for Software Artifacts) defines four levels of build integrity. Level 3 requires a hermetic, reproducible build with signed provenance.

```bash
# Verify SLSA provenance for a GitHub release artifact
gh attestation verify artifact.tar.gz --owner org-name

# Verify using slsa-verifier
slsa-verifier verify-artifact artifact.tar.gz \
  --provenance-path artifact.tar.gz.intoto.jsonl \
  --source-uri github.com/org/repo
```

**OSV-Scanner — open-source vulnerability database:**

```bash
# Install
go install github.com/google/osv-scanner/cmd/osv-scanner@latest

# Scan lock files
osv-scanner --lockfile=package-lock.json
osv-scanner --lockfile=requirements.txt
osv-scanner --lockfile=go.sum

# Recursive scan of a directory
osv-scanner -r .
```

OSV-Scanner queries the Open Source Vulnerabilities database, aggregating CVEs, GitHub Security Advisories, and ecosystem-specific advisories.

**Socket.dev — supply chain attack detection in PRs:** Analyzes package behavior (network access, filesystem access, obfuscated code, install scripts) rather than CVE databases alone. Install the GitHub App to receive PR comments when a dependency change introduces suspicious behavior.

---

## Triage Workflow

Not every vulnerability requires immediate remediation. Apply a consistent triage process to prioritize effort and document accepted risks.

**Step 1: Determine dependency type.** Direct dependencies are under your control; update them. Transitive dependencies require updating the direct dependency that pulls them in, using an `overrides`/`resolutions` field, or accepting the risk.

**Step 2: Assess reachability.** Is the vulnerable code path actually invoked? Use `govulncheck` (Go) or manual code review to confirm. A vulnerability in a JSON parser is not exploitable if your application never passes untrusted input to it.

**Step 3: Check fix availability.**

```bash
# npm — show available fix
npm audit --json | jq '.vulnerabilities | to_entries[] | {name: .key, fixAvailable: .value.fixAvailable}'

# pip-audit — show fix version
pip-audit --format json | jq '.[] | {name: .name, fix: .fix_versions}'
```

**Step 4: Apply the fix or mitigate.**

| Situation | Action |
|-----------|--------|
| Fix available, no breaking change | Upgrade immediately |
| Fix available, breaking change | Schedule upgrade, add regression tests |
| No fix, vulnerability reachable | Apply WAF rule, input validation, or disable feature |
| No fix, vulnerability unreachable | Document and accept; set a review date |

**Step 5: Document accepted risks.**

Every suppressed finding must have a documented rationale, owner, and review date.

```
# .trivyignore
# CVE-2024-12345
# Reason: vulnerable function is not called; confirmed by govulncheck
# Owner: security@example.com
# Review date: 2025-06-01
CVE-2024-12345
```

**Triage decision matrix:**

| Reachability | Fix Available | Action |
|-------------|---------------|--------|
| Reachable | Yes | Upgrade immediately (P1 for CRITICAL, P2 for HIGH) |
| Reachable | No | Mitigate via WAF/config; escalate to vendor; set SLA |
| Unreachable | Yes | Upgrade in next sprint to reduce noise |
| Unreachable | No | Document and accept; suppress with expiry comment |

**Recommended SLA defaults:** Critical/reachable — 24 hours. High/reachable — 7 days. Medium/reachable — 30 days. Low — 90 days or next major release. Tighten for internet-facing services handling sensitive data.
