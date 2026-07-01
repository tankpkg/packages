# Worked Prompt Atom Examples

Sources: Tank Contributing Standard (AGENTS.md 2025-2026), ECC command migration patterns, production bundle analysis (@tank/quality-gate)

Covers: Four complete prompt atom examples with full bundle context, showing how each prompt composes with companion atoms. Each example includes the problem statement, the tank.json atoms array, the template text with variable annotations, and adapter behavior notes.

## Example 1: PR Description Generator

### Problem

Developers need consistent, well-structured pull request descriptions.
The template should accept a diff and optional ticket reference, then
produce a description with summary, motivation, changes, and testing
sections.

### tank.json

```json
{
  "name": "@tank/pr-workflows",
  "version": "1.0.0",
  "description": "PR description and review workflow templates.",
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
      "kind": "prompt",
      "name": "pr-description",
      "template": "Variables:\n- diff_output (required): Full git diff of the PR\n- ticket_id (optional): Issue or ticket reference\n- base_branch (optional): Target branch name\n\n---\n\nGenerate a pull request description for the following changes.\n\nDiff:\n{{diff_output}}\n\nTicket: {{ticket_id?}}\nBase branch: {{base_branch?}}\n\nProduce the description in this format:\n\n## Summary\nOne paragraph explaining what this PR does and why.\n\n## Motivation\nWhat problem does this solve? Link to the ticket if provided.\n\n## Changes\nBullet list of the key changes, grouped by area.\n\n## Testing\nHow were these changes tested? List manual and automated steps.\n\n## Checklist\n- [ ] Tests added/updated\n- [ ] Documentation updated if needed\n- [ ] No breaking changes (or migration notes added)"
    }
  ]
}
```

### Template Anatomy

The template has three zones:

1. **Variable documentation block** (lines 1-5): Lists variables with
   required/optional status and descriptions. This is read by the model
   as context, not parsed by the adapter.

2. **Separator** (`---`): Visual break between documentation and template.

3. **Template body** (remaining lines): The actual prompt with variable
   placeholders and explicit output format specification.

### Composition Notes

- The `instruction` atom (`./SKILL.md`) provides project-specific PR
  conventions. The prompt atom references these implicitly ("our format").
- No hook or agent atom needed -- this is a standalone on-demand template.
- A future enhancement could add a `hook` atom on `pre-stop` that
  auto-generates the PR description when the agent completes work.

### Adapter Behavior

| Platform    | Invocation                              |
| ----------- | --------------------------------------- |
| Cursor      | `/pr-description` in command palette    |
| OpenCode    | `/pr-description` slash command         |
| Claude Code | `pr-description` callable template      |

## Example 2: Commit Message Formatter

### Problem

Enforce conventional commit format across a team. The template accepts
a diff summary and optional ticket ID, producing a properly formatted
conventional commit message.

### tank.json

```json
{
  "name": "@tank/git-conventions",
  "version": "1.0.0",
  "description": "Git workflow templates: commit messages, branch naming, changelog entries.",
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
      "kind": "prompt",
      "name": "commit-message",
      "template": "Variables:\n- diff_summary (required): Summary of staged changes\n- ticket_id (optional): Issue tracker reference\n\n---\n\nGenerate a conventional commit message for these staged changes:\n\n{{diff_summary}}\n\nTicket: {{ticket_id?}}\n\nRules:\n1. Type must be one of: feat, fix, refactor, docs, test, chore, ci, perf, build\n2. Scope is the module or area affected (optional, in parentheses)\n3. Subject line is imperative, lowercase, no period, under 72 characters\n4. Body explains what and why (not how), wrapped at 72 characters\n5. Footer references the ticket if provided\n\nOutput format:\n```\ntype(scope): subject\n\nbody\n\nRefs: #ticket\n```"
    },
    {
      "kind": "prompt",
      "name": "changelog-entry",
      "template": "Variables:\n- commits (required): List of commits since last release\n- version (required): New version number\n\n---\n\nGenerate a changelog entry for version {{version}}.\n\nCommits:\n{{commits}}\n\nGroup entries under:\n## Added\n## Changed\n## Fixed\n## Removed\n\nOmit empty groups. Use past tense. One line per entry."
    }
  ]
}
```

### Template Anatomy

The `commit-message` prompt encodes formatting rules directly in the
template rather than relying on ambient instruction context. This makes
the prompt self-contained -- it works correctly even if the instruction
atom is not loaded.

The `changelog-entry` prompt demonstrates a second prompt atom in the
same bundle. Both serve the "git conventions" capability but are
invoked independently.

### Composition Notes

- Two prompts in one bundle, each independently invocable.
- The instruction atom provides broader git workflow context (branch
  naming, merge strategy) that both prompts can reference.
- These prompts could be chained: generate commit messages during
  development, then generate changelog from accumulated commits at
  release time.

### Why Two Prompt Atoms, Not One

A single prompt that both formats commits and generates changelogs would
violate the "one prompt, one job" principle. Users invoke these at
different times (per-commit vs per-release) with different inputs.

## Example 3: Incident Report Template

### Problem

Standardize incident reporting across a team. The template captures
severity, timeline, summary, and analysis, producing a structured
report that can be pasted into a wiki or ticketing system.

### tank.json

```json
{
  "name": "@tank/incident-response",
  "version": "1.0.0",
  "description": "Incident report generation and post-mortem workflow templates.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "prompt",
      "name": "incident-report",
      "template": "Variables:\n- severity (required): P0-P4 severity level\n- incident_summary (required): Brief description of what happened\n- timeline (required): Chronological events with timestamps\n- affected_services (required): List of impacted services/systems\n- detection_method (optional): How the incident was discovered\n- resolution_steps (optional): Steps taken to resolve\n\n---\n\nGenerate a structured incident report.\n\nSeverity: {{severity}}\nSummary: {{incident_summary}}\nAffected services: {{affected_services}}\nDetection: {{detection_method?}}\n\nTimeline:\n{{timeline}}\n\nResolution steps:\n{{resolution_steps?}}\n\nProduce the report in this format:\n\n# Incident Report\n\n**Severity**: <severity>\n**Status**: <resolved / investigating / monitoring>\n**Date**: <date from timeline>\n**Duration**: <calculated from timeline>\n\n## Summary\nOne paragraph describing the incident and its impact.\n\n## Timeline\n| Time | Event |\n|------|-------|\n| ...  | ...   |\n\n## Root Cause\nAnalyze the timeline and determine the most likely root cause.\n\n## Impact\n- Users affected: <estimate from affected services>\n- Services degraded: <list>\n- Data loss: <yes/no with details>\n\n## Resolution\nSteps taken to resolve, in chronological order.\n\n## Action Items\n| Priority | Action | Owner | Due Date |\n|----------|--------|-------|----------|\n| P0       | ...    | TBD   | TBD      |\n\n## Lessons Learned\n3-5 bullet points on what went well and what to improve."
    },
    {
      "kind": "agent",
      "name": "incident-analyzer",
      "role": "Analyze incident timelines and logs to identify root causes. When the incident-report prompt is invoked, assist by reading log files and correlating events. Focus on causation chains, not symptoms.",
      "tools": ["read", "grep", "glob"],
      "model": "balanced",
      "readonly": true
    }
  ]
}
```

### Template Anatomy

This is the most complex single-prompt example. It has six variables
(four required, two optional) and a detailed output format with tables.
This is near the upper limit of single-prompt complexity -- adding
more variables would warrant splitting into gather and draft stages.

### Composition Notes

- The `agent` atom (`incident-analyzer`) provides analytical capability
  the prompt alone cannot. When the user invokes `incident-report`,
  the agent can be delegated to read log files and build the timeline
  before the prompt renders the final report.
- No instruction atom -- the prompt is self-contained with formatting
  rules embedded in the template.
- No hook atom -- incident reports are always user-initiated, never
  auto-triggered.

### Why an Agent Companion

The incident report prompt produces structured output from provided
inputs. But gathering those inputs (reading logs, correlating timestamps,
identifying affected services) requires tool access. The agent atom
provides that capability. The prompt defines the output format; the
agent gathers the input data.

## Example 4: Code Review Checklist

### Problem

Provide a consistent code review framework that adapts to the type
of change (feature, bugfix, refactor, dependency update). The reviewer
invokes the prompt, supplies the diff, and gets a structured checklist
tailored to the change type.

### tank.json

```json
{
  "name": "@tank/code-review-toolkit",
  "version": "1.0.0",
  "description": "Code review checklist and feedback templates.",
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
      "kind": "prompt",
      "name": "review-checklist",
      "template": "Variables:\n- diff_output (required): Git diff of the changes to review\n- change_type (required): One of: feature, bugfix, refactor, dependency, config\n- focus_areas (optional): Specific areas to pay attention to\n\n---\n\nPerform a code review of the following changes.\n\nChange type: {{change_type}}\nFocus areas: {{focus_areas?}}\n\nDiff:\n{{diff_output}}\n\nProduce the review as a checklist tailored to the change type.\n\n## Review: {{change_type}}\n\n### Correctness\n- [ ] Logic is correct and handles edge cases\n- [ ] Error handling is appropriate\n- [ ] ... (add items specific to the change type)\n\n### Security\n- [ ] No secrets or credentials in code\n- [ ] Input validation present where needed\n- [ ] ... (add items specific to the change type)\n\n### Testing\n- [ ] Tests cover the changed behavior\n- [ ] Edge cases have test coverage\n- [ ] ... (add items specific to the change type)\n\n### Maintainability\n- [ ] Naming is clear and consistent\n- [ ] No unnecessary complexity\n- [ ] ... (add items specific to the change type)\n\n### Issues Found\nFor each issue:\n- **File**: filename:line\n- **Severity**: critical / high / medium / low\n- **Issue**: description\n- **Suggestion**: how to fix\n\n### Verdict\nAPPROVE, REQUEST_CHANGES, or COMMENT."
    },
    {
      "kind": "prompt",
      "name": "review-response",
      "template": "Variables:\n- review_feedback (required): Code review feedback received\n- original_diff (required): The original diff that was reviewed\n\n---\n\nAddress this code review feedback.\n\nFeedback:\n{{review_feedback}}\n\nOriginal diff:\n{{original_diff}}\n\nFor each item:\n1. State whether you agree or disagree (with reasoning)\n2. If agree, describe the fix\n3. If disagree, provide justification\n\nOutput format:\n| # | Feedback Item | Response | Action |\n|---|--------------|----------|--------|\n| 1 | ...          | Agree/Disagree + reasoning | Fix description or justification |"
    },
    {
      "kind": "rule",
      "event": "post-tool-use",
      "policy": "block",
      "reason": "Review checklist must include a verdict (APPROVE, REQUEST_CHANGES, or COMMENT)"
    }
  ]
}
```

### Template Anatomy

Two complementary prompts form a review workflow:

1. `review-checklist`: The reviewer runs this against a diff. The
   `change_type` variable adapts the checklist categories.
2. `review-response`: The author runs this to systematically address
   received feedback.

### Composition Notes

- **Instruction atom**: Provides project-specific code standards that
  inform what "correct" and "maintainable" mean in context.
- **Rule atom**: Validates that review output includes a verdict.
  This demonstrates prompt + rule composition -- the rule gates the
  output quality of the prompt.
- **Two prompts, one workflow**: The review and response prompts
  form a natural cycle. The output of `review-checklist` becomes
  the `review_feedback` input of `review-response`.

### ECC Migration Notes

This example maps directly to ECC's "code review" command pattern.
The ECC command was a single monolithic `.md` file with hardcoded
instructions. The Tank version:

| ECC Command                | Tank Equivalent                          |
| -------------------------- | ---------------------------------------- |
| `commands/code-review.md`  | Prompt atom `review-checklist`           |
| Hardcoded review criteria  | Instruction atom with project standards  |
| No response workflow       | Second prompt atom `review-response`     |
| No output validation       | Rule atom enforcing verdict requirement  |

This decomposition improves on the ECC pattern: each concern lives
in a dedicated atom, independently testable and composable.

## Composition Summary

| Example               | Prompt | Instruction | Agent | Hook | Rule | Total Atoms |
| --------------------- | ------ | ----------- | ----- | ---- | ---- | ----------- |
| PR Description        | 1      | 1           | 0     | 0    | 0    | 2           |
| Git Conventions       | 2      | 1           | 0     | 0    | 0    | 3           |
| Incident Report       | 1      | 0           | 1     | 0    | 0    | 2           |
| Code Review Toolkit   | 2      | 1           | 0     | 0    | 1    | 4           |

### Patterns Observed

1. **Prompt + Instruction** is the most common pair. The instruction
   provides ambient context; the prompt provides the on-demand template.

2. **Multiple prompts per bundle** serve related workflows. Name them
   with a shared prefix or domain to signal cohesion.

3. **Prompt + Agent** pairs appear when the prompt needs data that
   requires tool access to gather.

4. **Prompt + Rule** pairs appear when output quality needs machine
   enforcement beyond what the template text alone can guarantee.

5. **Prompt + Hook** pairs appear when prompts should fire automatically
   at lifecycle events rather than on manual invocation.
