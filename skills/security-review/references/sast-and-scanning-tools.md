# SAST and Scanning Tools

Sources: Semgrep documentation (2025-2026), GitHub CodeQL documentation, Bandit documentation, OWASP Source Code Analysis Tools

Covers: Tool selection by language and use case, Semgrep usage and custom rule authoring, CodeQL query suites and CLI, Bandit for Python, ESLint security plugins for JavaScript/TypeScript, ast-grep YAML rules, CI/CD pipeline integration, and false positive management workflows.

---

## Tool Selection

| Tool | Best For | Languages | Strength | Limitation |
|---|---|---|---|---|
| Semgrep | Fast pattern matching, custom rules, shift-left | 30+ | Speed, custom rules, low setup | No cross-file data flow in OSS tier |
| CodeQL | Deep taint tracking, CWE coverage, GitHub-native | JS/TS, Python, Java, C/C++, Go, Ruby, Swift, C# | 166 CWEs, full data flow, MRVA | Slow build step, requires GitHub Advanced Security |
| Bandit | Python AST checks | Python only | Zero config, fast, CI-friendly | Python only, no data flow |
| eslint-plugin-security | JS/TS inline with existing lint | JavaScript, TypeScript | Integrates with existing ESLint config | Pattern-based only |
| ast-grep | YAML-driven multi-language patterns | 20+ | Portable rules, fast, no runtime | No semantic analysis |

**Decision guide:**

- New project: run Semgrep with `p/security-audit` and `p/owasp-top-ten` on every PR.
- Python codebase: add Bandit alongside Semgrep; they cover different checks.
- GitHub-hosted repo with Advanced Security: enable CodeQL for deep taint analysis.
- JS/TS monorepo with existing ESLint: add `eslint-plugin-security` to the existing config.
- Polyglot repo needing portable rules without a runtime dependency: use ast-grep.

---

## Semgrep

Semgrep performs AST-level pattern matching across 30+ languages. It is fast enough to run on every pull request and supports custom rules without compilation.

### Running Semgrep

```bash
# Basic scan
semgrep scan --config auto .

# Security-focused scan
semgrep scan --config p/security-audit --config p/owasp-top-ten .

# CI mode (reports to Semgrep Cloud via SEMGREP_APP_TOKEN)
semgrep ci

# Diff-only scan — only findings introduced in the current diff
semgrep scan --config p/security-audit --diff-depth 0 .

# JSON output for downstream processing
semgrep scan --config p/security-audit --json -o results.json .
```

**Key rule presets:** `p/security-audit` (broad security checks), `p/owasp-top-ten` (OWASP Top Ten 2021), `p/secrets` (hardcoded credentials), `p/default` (high-confidence rules), `p/sql-injection`, `p/jwt`.

### Writing Custom Semgrep Rules

Place custom rules in `.semgrep/` and reference with `--config .semgrep/`.

```yaml
rules:
  - id: dangerous-eval
    patterns:
      - pattern: eval($X)
      - pattern-not: eval("...")
    message: "eval() with dynamic input enables code injection. Use a safe alternative."
    severity: ERROR
    languages: [javascript, typescript]
    metadata:
      cwe: ["CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code"]
      owasp: ["A03:2021 - Injection"]
      confidence: HIGH
```

**Pattern operators:** `pattern` (must match), `pattern-not` (exclusion), `pattern-either` (OR), `pattern-inside` / `pattern-not-inside` (scope), `metavariable-regex` (constrain with regex), `focus-metavariable` (report specific variable location).

**Example: SQL string concatenation in Python:**

```yaml
rules:
  - id: sql-string-concat
    patterns:
      - pattern: |
          $QUERY = "..." + $INPUT
          $CURSOR.execute($QUERY)
      - pattern-not: |
          $CURSOR.execute($QUERY, $PARAMS)
    message: "SQL query built by string concatenation. Use parameterized queries."
    severity: ERROR
    languages: [python]
    metadata:
      cwe: ["CWE-89"]
      owasp: ["A03:2021"]
```

### Interpreting Results

Semgrep output includes: rule ID, file path, line number, matched code, severity, and message.

**Triage:** Open the file at the reported line. Determine whether attacker-controlled input reaches the sink. True positive: fix it. False positive: suppress with rule ID and reason.

**Suppressing a false positive:**

```javascript
// nosemgrep: dangerous-eval -- input is validated against an allowlist before this call
eval(sanitizedExpression);
```

Always include the rule ID and a brief justification. Bare `# nosemgrep` without a rule ID suppresses all rules and should be avoided.

Semgrep Pro adds cross-file taint tracking and cross-function analysis, which follow data from source to sink across module boundaries.

---

## CodeQL

CodeQL compiles source code into a relational database and runs declarative QL queries against it. It performs full data flow and taint tracking, making it the most thorough SAST option for supported languages.

### Running CodeQL

**GitHub Actions (recommended):**

```yaml
# .github/workflows/codeql.yml
name: CodeQL
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      actions: read
      contents: read
    strategy:
      matrix:
        language: [javascript, python]
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: security-and-quality
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3
```

**CLI: create a database and analyze locally:**

```bash
codeql database create codeql-db --language=javascript --source-root=.

codeql database analyze codeql-db \
  javascript-security-and-quality.qls \
  --format=sarif-latest \
  --output=results.sarif
```

**Query suites:**

| Suite | Queries | Use |
|---|---|---|
| `security-and-quality` | ~491 | Default; covers security and code quality |
| `security-extended` | ~626 | Adds lower-confidence security queries |
| `security-experimental` | Varies | Experimental; higher false positive rate |

Use `security-and-quality` as the baseline. Add `security-extended` for high-value targets or pre-release audits. MRVA (Multi-Repository Variant Analysis) runs a query across all repositories in a GitHub organization simultaneously — use it to find a newly discovered vulnerability pattern fleet-wide.

### Key CodeQL Queries

| Language | Query ID | CWE | What It Finds |
|---|---|---|---|
| JavaScript/TypeScript | `js/sql-injection` | CWE-89 | SQL built from user-controlled input |
| JavaScript/TypeScript | `js/xss` | CWE-79 | DOM or reflected XSS via taint flow |
| JavaScript/TypeScript | `js/path-injection` | CWE-22 | File path constructed from user input |
| JavaScript/TypeScript | `js/prototype-pollution` | CWE-1321 | Prototype pollution via object merge |
| Python | `py/sql-injection` | CWE-89 | SQL string formatting with user input |
| Python | `py/command-line-injection` | CWE-78 | `subprocess` with `shell=True` and user input |
| Python | `py/code-injection` | CWE-94 | `eval`/`exec` with user input |
| Java | `java/sql-injection` | CWE-89 | JDBC query built from user input |
| Java | `java/unsafe-deserialization` | CWE-502 | `ObjectInputStream` with untrusted data |
| Go | `go/sql-injection` | CWE-89 | SQL via `fmt.Sprintf` into query |
| Go | `go/path-injection` | CWE-22 | `os.Open` with user-controlled path |
| C/C++ | `cpp/buffer-overflow` | CWE-120 | Classic buffer overflow patterns |

---

## Bandit (Python)

Bandit performs AST-based security analysis on Python source code. It is fast, requires no configuration to start, and covers Python-specific risks that generic tools miss.

### Running Bandit

```bash
# Recursive scan with JSON output
bandit -r . -f json -o bandit-results.json

# Medium and high severity/confidence only
bandit -r . -l -i

# Exclude test directories
bandit -r . --exclude ./tests,./venv -f json

# Target specific checks
bandit -r . -t B301,B302
```

### Key Bandit Checks

| Check ID | Name | What It Flags |
|---|---|---|
| B101 | assert_used | `assert` statements (stripped in optimized bytecode) |
| B105 | hardcoded_password_string | String literals assigned to password-like variables |
| B301 | pickle | `pickle.loads` with untrusted data |
| B303 | md5 | MD5 used for cryptographic purposes |
| B311 | random | `random` module for security-sensitive values |
| B324 | hashlib | MD5 or SHA1 in `hashlib` |
| B501 | request_with_no_cert_validation | `verify=False` in requests |
| B602 | subprocess_popen_with_shell_equals_true | `subprocess` with `shell=True` |
| B608 | hardcoded_sql_expressions | SQL string with `SELECT`, `INSERT`, etc. |
| B701 | jinja2_autoescape_false | Jinja2 with `autoescape=False` |
| B703 | django_mark_safe | Django `mark_safe()` with variable input |

### Bandit Configuration

Configure via `.bandit` or `pyproject.toml`:

```toml
[tool.bandit]
exclude_dirs = ["tests", "migrations"]
skips = ["B101"]
```

---

## ESLint Security (JavaScript/TypeScript)

### Setup

```bash
npm install --save-dev eslint-plugin-security eslint-plugin-no-unsanitized
```

```javascript
// eslint.config.js (flat config)
import security from 'eslint-plugin-security';
import noUnsanitized from 'eslint-plugin-no-unsanitized';

export default [
  security.configs.recommended,
  {
    plugins: { 'no-unsanitized': noUnsanitized },
    rules: {
      'no-unsanitized/method': 'error',
      'no-unsanitized/property': 'error',
    },
  },
];
```

### Key Rules

| Rule | Plugin | What It Flags |
|---|---|---|
| `security/detect-eval-with-expression` | security | `eval()` with a non-literal argument |
| `security/detect-non-literal-fs-filename` | security | `fs` methods with variable filenames |
| `security/detect-non-literal-regexp` | security | `RegExp` constructor with variable pattern |
| `security/detect-unsafe-regex` | security | Regexes vulnerable to ReDoS |
| `security/detect-child-process` | security | `child_process` usage |
| `security/detect-object-injection` | security | Bracket notation with variable key (prototype pollution risk) |
| `no-unsanitized/method` | no-unsanitized | `insertAdjacentHTML`, `write`, `writeln` with dynamic input |
| `no-unsanitized/property` | no-unsanitized | `innerHTML`, `outerHTML` assignment with dynamic input |

Note: `detect-object-injection` produces a high false positive rate on normal array/object access. Tune it with `allowedPatterns` or disable it if noise outweighs signal.

---

## ast-grep Security Rules

ast-grep uses YAML rule files to match AST patterns across 20+ languages. It requires no language runtime and integrates into any CI pipeline.

```yaml
# rules/detect-innerhtml.yml
id: detect-innerhtml-assignment
language: JavaScript
rule:
  pattern: $EL.innerHTML = $INPUT
  not:
    pattern: $EL.innerHTML = "..."
message: "Direct innerHTML assignment with dynamic input enables XSS. Use textContent or a sanitizer."
severity: warning
metadata:
  cwe: CWE-79
```

```bash
# Run a single rule
ast-grep scan --rule rules/detect-innerhtml.yml src/

# Run all rules in a directory
ast-grep scan --rule rules/ src/

# JSON output
ast-grep scan --rule rules/ --json src/
```

ast-grep rules can be committed to the repository and run as a pre-commit hook or CI step without installing a language-specific runtime, making it suitable for polyglot repositories.

---

## CI/CD Pipeline Setup

### Semgrep in GitHub Actions

```yaml
name: Semgrep
on:
  push:
    branches: [main]
  pull_request: {}

jobs:
  semgrep:
    runs-on: ubuntu-latest
    container:
      image: semgrep/semgrep
    steps:
      - uses: actions/checkout@v4
      - name: Run Semgrep
        run: semgrep scan --config p/security-audit --config p/owasp-top-ten --config .semgrep/ --sarif --output semgrep.sarif .
        env:
          SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: semgrep.sarif
```

### Blocking vs Non-Blocking Strategy

Do not block the pipeline on day one:

1. **Weeks 1-2:** Run in report-only mode. Collect baseline findings and understand noise level.
2. **Weeks 3-4:** Triage existing findings. Suppress acknowledged false positives with documented reasons.
3. **Month 2+:** Fail only on findings introduced in the current diff (`--diff-depth 0` for Semgrep, `--baseline-commit` against the target branch). Pre-existing findings do not block.
4. **Ongoing:** Reduce the backlog incrementally. Tighten blocking criteria as it shrinks.

---

## False Positive Management

### Triage Workflow

For each finding: read the matched code in context, trace whether attacker-controlled input reaches the sink, check whether existing sanitization mitigates the risk, then classify as **true positive** (fix it), **false positive** (suppress with reason), or **accepted risk** (document and suppress).

### Suppression Syntax by Tool

**Semgrep:**

```python
# nosemgrep: sql-string-concat -- query is built from an allowlist of column names, not user input
query = "SELECT " + column_name + " FROM users"
```

**Bandit:**

```python
result = subprocess.run(cmd, shell=True)  # nosec B602 -- cmd is constructed from a hardcoded allowlist
```

**ESLint:**

```javascript
element.innerHTML = sanitizedHtml; // eslint-disable-line no-unsanitized/property -- sanitized with DOMPurify
```

**CodeQL:** Dismiss alerts directly in the GitHub Security tab. Select a reason (false positive, used in tests, won't fix) and add a comment. Dismissed alerts are excluded from future runs and tracked in the audit log.

### Baseline Approach

Use Semgrep's `--baseline-commit` flag to report only findings introduced since a specific commit:

```bash
semgrep scan --config p/security-audit --baseline-commit $(git rev-parse origin/main) .
```

For CodeQL, configure the workflow to annotate pull requests with new alerts only. This prevents pre-existing technical debt from blocking new work while still surfacing regressions.

### Suppression Hygiene

- Never suppress without a rule ID. Bare `# nosemgrep` or `# nosec` without specifics hides future regressions.
- Review suppressions quarterly. Remove suppressions where the underlying code has changed.
- Track suppression counts in dashboards. A rising suppression count without a corresponding fix count signals a process problem, not a tooling problem.
