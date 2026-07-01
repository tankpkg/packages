# Policy Design

Sources: Tank specification (AGENTS.md), OPA best practices (Styra), HashiCorp Sentinel
policy-as-code patterns, AWS Service Control Policies, Zero Trust architecture principles

Covers: designing effective rule policies -- when to block vs warn vs allow, composing
multiple rules into policy sets, ordering and precedence, false positive mitigation,
user escape hatches, and the relationship between rules and instructions.

## The Policy Spectrum

Every rule enforces a position on the restriction spectrum:

```
PERMISSIVE                                                    RESTRICTIVE
   |                                                               |
   allow-list     warn on smell     warn on risk     block danger  block all
   (explicit      (advisory,        (strong          (hard stop,   (lockdown,
    green-light)   proceed ok)       nudge)           must reroute) deny-by-default)
```

Position rules according to the severity of the consequence if the agent proceeds.

## When to Block

Block when the operation causes irreversible harm or violates a hard security boundary.

| Signal                                       | Example                            |
| -------------------------------------------- | ---------------------------------- |
| Data destruction without backup              | `rm -rf`, `DROP TABLE`, `--force`  |
| Credential or secret exposure                | Writing `.env` to stdout, logs     |
| Production system mutation from dev context  | `kubectl delete` in prod namespace |
| Compliance violation (legal, regulatory)     | PII in logs, unencrypted storage   |
| Dependency on external irreversible action   | Sending emails, publishing packages|

### Block rules: design principles

1. **Narrow the match** -- Block `rm -rf /` not `rm`. Block `git push --force origin main`
   not `git push`. Over-broad matches create false positives that erode trust.
2. **Offer an alternative in the reason** -- "Use `trash-cli` instead of `rm -rf`" gives
   the agent a path forward. A block without an alternative is a dead end.
3. **Pair with an instruction atom** -- The instruction explains *why* the rule exists
   and describes the approved workflow. The rule enforces; the instruction educates.

## When to Warn

Warn when the operation is suboptimal but not dangerous. The agent should know
about the concern and may choose to proceed.

| Signal                                       | Example                            |
| -------------------------------------------- | ---------------------------------- |
| Code quality issue                           | `as any`, `eslint-disable`, `TODO` |
| Deprecated API usage                         | Old library imports, legacy syntax |
| Performance concern                          | N+1 queries, unbounded loops       |
| Style deviation from project standards       | Wrong naming convention            |
| Potential security weakness (not critical)   | Missing input validation           |

### Warn rules: design principles

1. **Be specific about the problem** -- "Using `as any` bypasses TypeScript safety --
   prefer a proper type assertion or generic" teaches more than "Bad practice."
2. **Accept that warnings get overridden** -- Warnings are advisory. If the agent
   proceeds, that is by design. If the constraint must be enforced, escalate to block.
3. **Batch related warnings** -- Five warnings for the same pattern in one file
   overwhelm the agent. Consider one rule with a broader match over many narrow ones.

## When to Allow

Allow when operating inside a restricted policy set and specific operations need
explicit permission. Allow-list patterns require a default-deny (block) rule.

| Signal                                       | Example                            |
| -------------------------------------------- | ---------------------------------- |
| Known-safe tool in a restricted environment  | `read`, `grep` in audit-only mode |
| Approved command in a locked-down shell      | `ls`, `cat` when shell is limited  |
| Exemption from a broader block               | Allow `rm` for temp files only     |

### Allow rules: design principles

1. **Always pair with a catch-all block** -- An allow rule without a default deny
   is meaningless. The pattern is: specific allows + one broad block.
2. **Document what is allowed, not just what is blocked** -- Users reading the
   policy should understand the positive intent, not just the restrictions.
3. **Keep the allow-list minimal** -- Every allowed operation is an attack surface.
   Start with zero and add permissions as justified.

## Composing Rule Sets

### Multiple rules in one bundle

A bundle's `atoms` array can contain any number of rule atoms. Each rule is
independent -- the runtime evaluates all rules bound to the triggering event.

```json
{
  "atoms": [
    { "kind": "rule", "event": "pre-command", "policy": "block", "match": "rm -rf", "reason": "..." },
    { "kind": "rule", "event": "pre-command", "policy": "block", "match": "chmod 777", "reason": "..." },
    { "kind": "rule", "event": "pre-command", "policy": "warn", "match": "sudo", "reason": "..." },
    { "kind": "rule", "event": "pre-tool-use", "policy": "block", "match": "browser", "reason": "..." },
    { "kind": "instruction", "content": "./SKILL.md" }
  ]
}
```

### Policy set design patterns

#### Pattern 1: Safety net

Block a handful of known-dangerous operations. Everything else is allowed.

```
Rules: 3-5 block rules on pre-command
Instruction: explains what is blocked and why
Default: permissive (agent can do anything not blocked)
```

Best for: general-purpose safety in any project.

#### Pattern 2: Allow-list (zero trust)

Block everything by default. Allow only approved operations.

```
Rules: N allow rules for specific tools/commands + 1 catch-all block
Instruction: explains the approved workflow
Default: restrictive (agent can only do what is explicitly allowed)
```

Best for: sensitive environments, compliance-heavy projects.

#### Pattern 3: Style guide enforcement

Warn on patterns that violate project standards. No blocking.

```
Rules: 5-15 warn rules on post-file-write
Instruction: explains the style guide and preferred patterns
Default: permissive with guidance
```

Best for: code quality, consistency, onboarding new agents to a codebase.

#### Pattern 4: Layered defense

Combine block rules for safety, warn rules for quality, and an instruction
for education.

```
Rules: 2-3 block rules (safety) + 5-10 warn rules (quality)
Instruction: comprehensive policy explanation
Default: mixed -- hard limits on danger, soft guidance on quality
```

Best for: mature projects with established standards.

## Precedence and Ordering

### Evaluation model

When an event fires, the runtime collects all rules bound to that event and
evaluates them. The evaluation follows this precedence:

1. **Block wins over warn** -- If any rule blocks, the operation is blocked
   regardless of other rules that warn or allow.
2. **Allow exempts from block** -- An allow rule with a more specific match
   can exempt an operation from a broader block rule.
3. **Warn accumulates** -- Multiple warn rules can all fire. The agent sees
   all warnings.

### Specificity determines exemption

When an allow rule and a block rule both match:

```json
{ "kind": "rule", "event": "pre-tool-use", "policy": "block", "reason": "No tools by default" },
{ "kind": "rule", "event": "pre-tool-use", "policy": "allow", "match": "read", "reason": "Read is safe" }
```

The runtime treats the allow with a `match` as more specific than the block
without one. The `read` tool is permitted; all others are blocked.

### Array order is not precedence

Rule evaluation order is determined by specificity and policy weight, not by
position in the `atoms` array. Place rules in logical reading order for humans
but do not rely on array index for enforcement behavior.

## False Positive Mitigation

False positives -- rules that fire incorrectly -- are the primary risk of
rule-based policies. They erode agent trust and developer patience.

### Prevention strategies

| Strategy                          | Implementation                              |
| --------------------------------- | ------------------------------------------- |
| Narrow match patterns             | `rm -rf /` not `rm`                         |
| Test before shipping              | Trigger the rule deliberately                |
| Use warn before block             | Deploy as warn, observe, escalate to block   |
| Combine with instruction context  | Agent understands the rule's intent          |
| Provide escape in reason          | "If this is intentional, use --force flag"   |

### Progressive enforcement

Start all new rules as `warn`. Observe how often they fire and whether the
triggers are correct. After validation, escalate critical rules to `block`.

```
Week 1: Deploy as warn, monitor triggers
Week 2: Review false positive rate
Week 3: Escalate validated rules to block
Week 4: Remove or adjust rules with high false positive rates
```

## Escape Hatches

Sometimes the agent legitimately needs to do something a rule blocks. Design
for this:

1. **Reason field as guidance** -- Include the approved alternative in the reason.
   "Blocked: use `trash` instead of `rm -rf`" gives a path forward.
2. **Allow-list exemptions** -- Add a specific allow rule for the justified case.
3. **Instruction context** -- The paired instruction atom can describe conditions
   under which the rule can be reconsidered.
4. **Extension overrides** -- Platform-specific extensions can soften enforcement
   for certain environments (e.g., CI vs local).

Do NOT design rules that can be bypassed by the agent rephrasing its request.
If a block can be circumvented by rewording, the match pattern is too narrow.

## Rules + Instructions: The Complete Pattern

Rules enforce. Instructions educate. Ship both.

A rule alone tells the agent "no" but not "why" or "what instead." An instruction
alone hopes the agent follows guidance but cannot enforce it. Together they form
a complete policy.

```json
{
  "atoms": [
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    },
    {
      "kind": "rule",
      "event": "pre-command",
      "policy": "block",
      "match": "rm -rf",
      "reason": "Use trash-cli for safe deletion. See SKILL.md for approved file operations."
    }
  ]
}
```

The instruction (`SKILL.md`) explains the project's file operation policy, lists
approved tools, and describes the rationale. The rule enforces the hard limit.

## Anti-Patterns

| Anti-pattern                  | Problem                                    | Fix                          |
| ----------------------------- | ------------------------------------------ | ---------------------------- |
| Block without reason          | Agent has no path forward                  | Add actionable reason        |
| Over-broad match              | Blocks legitimate operations               | Narrow the pattern           |
| All-block, no-allow           | Agent is paralyzed                         | Add explicit allow rules     |
| Warn for critical safety      | Agent ignores and proceeds                 | Escalate to block            |
| Rule without instruction      | Agent cannot learn the policy              | Add instruction atom         |
| Duplicate rules               | Confusing, hard to maintain                | Consolidate into one         |
| Regex in match                | Portability risk across adapters           | Use simple substring matches |

## Checklist: Designing a Policy Set

- [ ] Identified all dangerous operations (block candidates)
- [ ] Identified all suboptimal patterns (warn candidates)
- [ ] Determined default posture (permissive or restrictive)
- [ ] Each rule has a clear, actionable `reason`
- [ ] Block rules offer alternatives
- [ ] Match patterns are narrow enough to avoid false positives
- [ ] Rules are paired with an instruction atom
- [ ] Tested each rule by deliberately triggering its condition
- [ ] Reviewed for over-restriction (agent must remain useful)
- [ ] Rules live in a `bundles/` directory (multi-atom format)
