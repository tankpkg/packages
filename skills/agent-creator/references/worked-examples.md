# Worked Agent Examples

Sources: Tank Contributing Standard (AGENTS.md), quality-gate bundle (canonical example), multi-agent composition patterns

Covers: four complete agent atom examples with rationale — code-reviewer, security-auditor, doc-updater, and a multi-agent reviewer+fixer bundle. Each example includes the full JSON, field-by-field justification, and guidance on when to use the pattern.

## Example 1: Code Reviewer (Readonly, Fast)

This is the canonical agent atom from the quality-gate bundle. It
demonstrates the most common pattern — a readonly analysis agent paired
with a hook.

### The Atom

```json
{
  "kind": "agent",
  "name": "code-reviewer",
  "role": "Senior code reviewer. Review ONLY the modified files/hunks provided. Categorize every issue as critical, high, medium, or low. Focus on bugs, security, correctness, and maintainability. Do NOT review style/formatting — linters handle that. Be concise: one line per issue with file, line, severity, and what's wrong.",
  "tools": ["read", "grep", "glob", "lsp"],
  "model": "fast",
  "readonly": true
}
```

### Field-by-Field Rationale

| Field | Value | Why |
|-------|-------|-----|
| `name` | `code-reviewer` | Descriptive, kebab-case, clear function |
| `role` | (see above) | Identity-first, scoped to modified files, explicit exclusion of style checks, defined output format |
| `tools` | `read`, `grep`, `glob`, `lsp` | Minimum set to navigate and understand code. No `write`, `edit`, or `bash` — reviewer does not fix |
| `model` | `fast` | Code review is pattern matching, not deep reasoning. Fast model reduces latency and cost |
| `readonly` | `true` | Reviewer observes and reports. Must never modify files |

### Bundle Context

In the quality-gate bundle, this agent is triggered by a `pre-stop` hook.
The hook detects modified code files, delegates to the agent, and blocks
the session from stopping if critical or high issues are found.

```json
{
  "atoms": [
    {
      "kind": "hook",
      "name": "quality-gate",
      "event": "pre-stop",
      "handler": { "type": "js", "entry": "./hooks/quality-gate.ts" }
    },
    {
      "kind": "agent",
      "name": "code-reviewer",
      "role": "...",
      "tools": ["read", "grep", "glob", "lsp"],
      "model": "fast",
      "readonly": true
    },
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    }
  ]
}
```

### When to Use This Pattern

- Automatic code review on every agent stop
- CI-style quality gates within agent workflows
- Any scenario where analysis must happen before work is considered done

### Variations

| Variation | Change | Rationale |
|-----------|--------|-----------|
| Stricter review | Add `lsp` diagnostics focus to role | Catch type errors, unused imports |
| Language-specific | Narrow role to "Python reviewer" | Deeper expertise in one language |
| Severity threshold | Pair with rule that blocks on medium+ | Higher quality bar |

## Example 2: Security Auditor (Readonly, Powerful)

A security-focused agent that needs deeper reasoning than a code reviewer.
Scans for vulnerability patterns, insecure configurations, and supply chain
risks.

### The Atom

```json
{
  "kind": "agent",
  "name": "security-auditor",
  "role": "Application security auditor. Analyze code for OWASP Top 10 vulnerabilities, insecure cryptographic usage, hardcoded secrets, SQL injection, XSS, SSRF, path traversal, and insecure deserialization. Check dependency manifests for known CVEs. Report each finding with file, line, CWE ID, severity (critical/high/medium/low), and remediation suggestion. Do NOT fix issues — report only.",
  "tools": ["read", "grep", "glob"],
  "model": "powerful",
  "readonly": true
}
```

### Field-by-Field Rationale

| Field | Value | Why |
|-------|-------|-----|
| `name` | `security-auditor` | Clear security focus, distinct from generic reviewer |
| `role` | (see above) | Enumerates specific vulnerability classes to check. Includes CWE ID in output format. Explicit "report only" constraint |
| `tools` | `read`, `grep`, `glob` | No `lsp` needed — security patterns are string/regex based. No `fetch` — auditor works offline |
| `model` | `powerful` | Security analysis requires nuanced reasoning about data flow, trust boundaries, and attack vectors. Fast models miss subtle vulnerabilities |
| `readonly` | `true` | Auditor must never modify code. Modifications could mask findings |

### Bundle Context

Pair with an instruction atom containing security checklists:

```json
{
  "atoms": [
    {
      "kind": "agent",
      "name": "security-auditor",
      "role": "...",
      "tools": ["read", "grep", "glob"],
      "model": "powerful",
      "readonly": true
    },
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    }
  ]
}
```

The instruction atom can provide OWASP checklists, language-specific
vulnerability patterns, and severity classification criteria.

### When to Use This Pattern

- Pre-merge security review of pull requests
- Periodic security audit of entire codebases
- Compliance scanning for regulated industries
- Supply chain security checks on dependency updates

### Variations

| Variation | Change | Rationale |
|-----------|--------|-----------|
| Dependency-focused | Add `fetch` tool, narrow role to dependencies | Check CVE databases online |
| Infrastructure | Expand role to include IaC patterns | Terraform, CloudFormation security |
| Secrets-only | Narrow role to hardcoded secrets and API keys | Fast, focused scan |

## Example 3: Documentation Updater (Read-Write, Balanced)

A read-write agent that keeps documentation in sync with code changes.
This demonstrates the mutable agent pattern.

### The Atom

```json
{
  "kind": "agent",
  "name": "doc-updater",
  "role": "Documentation maintainer. When code changes are detected, update corresponding documentation files (README, API docs, inline comments, changelogs). Match the existing documentation style and tone. Update code examples to reflect the new API. Add entries to CHANGELOG.md for user-facing changes. Do NOT modify source code — only documentation files.",
  "tools": ["read", "write", "grep", "glob"],
  "model": "balanced"
}
```

### Field-by-Field Rationale

| Field | Value | Why |
|-------|-------|-----|
| `name` | `doc-updater` | Action-oriented name — this agent updates, not just reads |
| `role` | (see above) | Scoped to documentation files only. Explicit constraint against modifying source code. Specifies output artifacts (README, API docs, CHANGELOG) |
| `tools` | `read`, `write`, `grep`, `glob` | Needs `write` to create/update doc files. `read` and `grep` to understand code changes. No `edit` — prefers full file writes for docs. No `lsp` — documentation is prose, not code |
| `model` | `balanced` | Documentation writing needs decent language ability but not deep reasoning. Balanced is the right trade-off |
| `readonly` | (omitted) | Defaults to `false`. This agent must write files — readonly would break its purpose |

### Bundle Context

Pair with a hook that triggers after code files are modified:

```json
{
  "atoms": [
    {
      "kind": "hook",
      "name": "doc-sync",
      "event": "post-tool-use",
      "handler": { "type": "js", "entry": "./hooks/doc-sync.ts" }
    },
    {
      "kind": "agent",
      "name": "doc-updater",
      "role": "...",
      "tools": ["read", "write", "grep", "glob"],
      "model": "balanced"
    }
  ]
}
```

The hook detects when `write` or `edit` tools modify source code files
and triggers the doc-updater to check if documentation needs updating.

### When to Use This Pattern

- Keeping README and API docs in sync with code
- Automated changelog maintenance
- Updating code examples in documentation after API changes
- Maintaining inline documentation comments

### Variations

| Variation | Change | Rationale |
|-----------|--------|-----------|
| With `edit` | Add `edit` to tools | When docs need surgical updates, not rewrites |
| API-doc specialist | Narrow role to OpenAPI/JSDoc | Focused on structured API documentation |
| Changelog-only | Remove README scope from role | Minimal, focused on release notes |

## Example 4: Multi-Agent Bundle (Reviewer + Fixer)

The most powerful pattern — two agents with different capabilities
coordinated by a hook. The reviewer finds problems, the fixer resolves
them.

### The Full Bundle

```json
{
  "name": "@tank/review-and-fix",
  "version": "1.0.0",
  "description": "Automatic code review with self-healing. Reviewer finds issues, fixer resolves critical and high severity problems, reviewer re-checks until clean.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    },
    {
      "kind": "hook",
      "name": "review-gate",
      "event": "pre-stop",
      "handler": {
        "type": "js",
        "entry": "./hooks/review-gate.ts"
      }
    },
    {
      "kind": "agent",
      "name": "reviewer",
      "role": "Code reviewer. Analyze modified files for bugs, security issues, logic errors, and missing error handling. Categorize each issue as critical, high, medium, or low. Output one line per issue: file path, line number, severity, description. Do NOT suggest fixes — only identify problems.",
      "tools": ["read", "grep", "glob", "lsp"],
      "model": "fast",
      "readonly": true
    },
    {
      "kind": "agent",
      "name": "fixer",
      "role": "Code fixer. Receive a list of issues from the reviewer. Fix ONLY critical and high severity issues. Make minimal, targeted changes. Do NOT refactor unrelated code. After fixing, report what was changed and why.",
      "tools": ["read", "write", "edit", "grep", "glob", "lsp"],
      "model": "balanced"
    },
    {
      "kind": "rule",
      "event": "pre-stop",
      "policy": "block",
      "reason": "Unresolved critical or high severity issues remain"
    }
  ]
}
```

### Architecture Breakdown

```
Agent finishes work
        |
        v
  [pre-stop hook fires]
        |
        v
  Delegate to "reviewer" agent
        |
        v
  Reviewer reports issues
        |
        v
  Any critical/high issues?
   +-- No  -> agent stops (medium/low reported)
   +-- Yes -> delegate to "fixer" agent
                    |
                    v
              Fixer patches critical/high issues
                    |
                    v
              [pre-stop hook fires again]
              Reviewer re-checks
                    |
                    v
              (loop until clean)
```

### Agent Comparison

| Aspect | Reviewer | Fixer |
|--------|----------|-------|
| Purpose | Identify problems | Resolve problems |
| Tools | `read`, `grep`, `glob`, `lsp` | `read`, `write`, `edit`, `grep`, `glob`, `lsp` |
| Model | `fast` | `balanced` |
| Readonly | Yes | No |
| Output | Issue list (text) | File modifications |
| Scope | All issues | Critical and high only |

### Design Decisions

**Why two agents instead of one?**
A single agent that reviews and fixes conflates observation with action.
The reviewer might unconsciously ignore issues it cannot fix. Separation
ensures honest assessment.

**Why `fast` for reviewer and `balanced` for fixer?**
Review is pattern matching — fast models excel. Fixing requires
understanding context, generating correct code, and reasoning about side
effects — balanced models handle this better.

**Why the reviewer explicitly says "Do NOT suggest fixes"?**
Prevents the reviewer from spending tokens on fix suggestions that the
fixer will independently generate. Keeps reviewer output concise and
structured for machine parsing.

**Why a rule atom in addition to the hook?**
Defense in depth. The hook orchestrates the workflow. The rule provides
a hard constraint that the session cannot stop with unresolved issues,
even if the hook has a bug.

### When to Use This Pattern

- Self-healing code quality pipelines
- Automated bug fix workflows
- Any scenario requiring review-then-act cycles
- CI/CD quality gates with automatic remediation

### Platform Extensions Example

Add platform-specific configuration without changing the core atoms:

```json
{
  "kind": "agent",
  "name": "reviewer",
  "role": "...",
  "tools": ["read", "grep", "glob", "lsp"],
  "model": "fast",
  "readonly": true,
  "extensions": {
    "opencode": {
      "mode": "subagent",
      "temperature": 0.0,
      "color": "#FF9800"
    },
    "cursor": {
      "when": "always",
      "category": "quality"
    }
  }
}
```

The core atom remains portable. Each platform reads only the extensions
it understands.

## Choosing the Right Pattern

| Scenario | Pattern | Key Agent(s) |
|----------|---------|-------------|
| Passive quality check | Single readonly agent | Reviewer or auditor |
| Active maintenance | Single read-write agent | Updater or generator |
| Review then fix | Two-agent sequential | Reviewer + fixer |
| Multi-perspective analysis | Two-agent parallel | Auditor + reviewer |
| Conditional specialist dispatch | Two-agent gated | Triage + specialist |
| Full pipeline | Three+ agent orchestrated | Triage + specialist + reviewer |

## Checklist for New Agent Atoms

Before publishing an agent atom, verify:

- [ ] `name` is kebab-case, descriptive, unique within the bundle
- [ ] `role` follows the three-part pattern (identity, scope, output)
- [ ] `tools` grant only what the role requires (least-privilege)
- [ ] `model` matches the task complexity (see tier table)
- [ ] `readonly` is `true` for all non-mutating agents
- [ ] No platform-specific logic in `role` (use `extensions`)
- [ ] Role does not reference specific files or paths
- [ ] Role includes at least one "Do NOT" constraint
- [ ] Agent solves exactly one problem (single-responsibility)
- [ ] If multi-agent, each agent has distinct tools and model tier
