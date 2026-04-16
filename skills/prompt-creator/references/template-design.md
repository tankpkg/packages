# Template Design Patterns

Sources: Anthropic Prompt Engineering Guide (2025), OpenAI Prompt Best Practices (2025), Tank Contributing Standard (AGENTS.md), ECC command migration patterns (2025-2026)

Covers: Designing effective prompt templates for Tank prompt atoms -- variable naming conventions, structured output guidance, multi-step workflow templates, composing prompts with other atoms, and the distinction between template design and prompt engineering.

## Template Design vs Prompt Engineering

Template design is a subset of prompt engineering focused on creating
reusable, parameterized prompts rather than one-off queries. The
constraints are different:

| Concern                | One-Off Prompt           | Prompt Template                   |
| ---------------------- | ------------------------ | --------------------------------- |
| Variable inputs        | Hardcoded                | Parameterized with `{{slots}}`    |
| Audience               | You, right now           | Any user, any time                |
| Stability              | Adjust on the fly        | Must work across invocations      |
| Context assumptions    | Full session context     | Minimal -- only what's injected   |
| Output format          | Whatever works           | Consistent, structured            |

## Variable Design

### Naming Convention Reference

All variables use `{{snake_case}}` inside double braces.

| Category        | Pattern                  | Examples                                  |
| --------------- | ------------------------ | ----------------------------------------- |
| Raw data        | `{{noun_descriptor}}`    | `{{diff_output}}`, `{{error_log}}`        |
| Identifiers     | `{{entity_id}}`          | `{{ticket_id}}`, `{{pr_number}}`          |
| Configuration   | `{{setting_name}}`       | `{{severity_threshold}}`, `{{max_items}}` |
| Context refs    | `{{context_source}}`     | `{{repo_url}}`, `{{branch_name}}`         |
| Content blocks  | `{{content_type}}`       | `{{test_output}}`, `{{stack_trace}}`      |
| Constraints     | `{{format_constraint}}`  | `{{max_length}}`, `{{output_format}}`     |

### Variable Density Guidelines

Templates with too many variables become difficult to invoke and maintain.
Templates with too few become inflexible.

| Variable Count | Template Type                 | Guidance                          |
| -------------- | ----------------------------- | --------------------------------- |
| 1-2            | Simple generator              | Ideal for focused tasks           |
| 3-5            | Standard workflow template    | Sweet spot for most prompts       |
| 6-8            | Complex report template       | Consider splitting into stages    |
| 9+             | Over-parameterized            | Split into multiple prompt atoms  |

### Required vs Optional Variables

Distinguish required variables (template breaks without them) from optional
variables (template works with a default or omission).

Inline documentation approach -- add a comment block at the top of the template:

```
Variables:
- diff_output (required): Git diff of changes to describe
- ticket_id (optional): Jira/GitHub issue reference
- breaking_changes (optional): List of breaking changes if any

---

Write a pull request description for the following changes:

{{diff_output}}

Ticket: {{ticket_id}}
Breaking changes: {{breaking_changes?}}
```

The `---` separator between the variable documentation and the template body
is a convention, not a parsed syntax. Adapters pass the entire template
string; the model reads the documentation block as context.

## Structured Output Patterns

Templates that produce structured output are more useful than templates
that produce free-form text. Structure makes output parseable, consistent,
and composable.

### Section Headers Pattern

Define the output format explicitly with markdown headers:

```
Generate a code review report.

## Files Reviewed
{{changed_files}}

## Diff
{{diff_output}}

---

Produce the review in this format:

## Summary
One paragraph overview of the changes.

## Issues Found
For each issue:
- **File**: filename
- **Line**: line number
- **Severity**: critical / high / medium / low
- **Description**: what is wrong and why

## Recommendations
Numbered list of improvement suggestions.

## Verdict
APPROVE, REQUEST_CHANGES, or COMMENT with one-sentence justification.
```

### Checklist Pattern

For templates that produce actionable checklists:

```
Generate a pre-deploy checklist for this release.

Changes: {{release_notes}}
Environment: {{target_environment}}

Produce a markdown checklist:

## Pre-Deploy Checklist

### Code Quality
- [ ] All tests pass
- [ ] No critical or high lint issues
- [ ] ...add items based on the changes

### Infrastructure
- [ ] Database migrations reviewed
- [ ] ...add items based on the changes

### Communication
- [ ] Stakeholders notified
- [ ] ...add items based on the changes
```

### Labeled Fields Pattern

For templates that produce key-value structured data:

```
Generate a commit message for these changes.

Diff: {{diff_summary}}
Ticket: {{ticket_id}}

Output format:
Type: <conventional commit type>
Scope: <affected module>
Subject: <imperative description under 72 chars>
Body: <detailed explanation if needed>
Breaking: <yes/no, with migration note if yes>
```

### Table Pattern

For templates that produce comparison or analysis tables:

```
Compare these two implementation approaches.

Approach A: {{approach_a}}
Approach B: {{approach_b}}
Criteria: {{evaluation_criteria}}

Output as a markdown table:

| Criterion | Approach A | Approach B | Winner |
|-----------|-----------|-----------|--------|
| ...       | ...       | ...       | ...    |

## Recommendation
State which approach to use and why.
```

## Multi-Step Workflow Templates

Complex workflows that exceed a single prompt atom's scope should be
decomposed into multiple prompt atoms, each handling one stage.

### Decomposition Strategy

Split a workflow when:
- The output of one stage feeds as input to the next
- Different stages need different variable sets
- Users may want to invoke individual stages independently
- The combined template exceeds ~25 lines

### Workflow Composition Pattern

Define multiple prompt atoms in the same bundle. Name them with a shared
prefix to signal they belong to a workflow.

```json
{
  "atoms": [
    {
      "kind": "prompt",
      "name": "release-notes-gather",
      "template": "List all commits between {{base_tag}} and {{head_ref}}.\n\nGroup by: feature, fix, chore, breaking.\nFormat as bullet points under each group."
    },
    {
      "kind": "prompt",
      "name": "release-notes-draft",
      "template": "Draft release notes from these grouped commits:\n\n{{grouped_commits}}\n\nVersion: {{version}}\n\nInclude: highlights section, full changelog, migration notes for breaking changes."
    },
    {
      "kind": "prompt",
      "name": "release-notes-review",
      "template": "Review these draft release notes for:\n\n{{draft_notes}}\n\nCheck: accuracy vs commits, tone consistency, missing breaking change warnings.\nOutput: corrected release notes or LGTM."
    }
  ]
}
```

### Chaining with Agent Atoms

For automated multi-step execution, pair workflow prompts with an agent
atom that orchestrates the chain:

```json
{
  "kind": "agent",
  "name": "release-manager",
  "role": "Orchestrate release note generation by invoking release-notes-gather, then release-notes-draft, then release-notes-review in sequence. Pass output of each stage as input to the next.",
  "tools": ["git", "read"],
  "model": "balanced"
}
```

The agent invokes each prompt in sequence, feeding outputs forward.
This pattern separates the template content (prompts) from the
orchestration logic (agent).

## Composing Prompts with Other Atoms

Prompt atoms gain power when composed with companion atoms in a bundle.

### Prompt + Instruction

Add an instruction atom to provide the prompt with persistent context
that every invocation needs:

```json
{
  "atoms": [
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    },
    {
      "kind": "prompt",
      "name": "api-endpoint",
      "template": "Generate an API endpoint following our conventions.\n\nResource: {{resource_name}}\nOperations: {{crud_operations}}\nAuth: {{auth_method}}"
    }
  ]
}
```

The instruction provides "our conventions" context; the prompt provides
the parameterized generator. The instruction loads every session; the
prompt loads only when invoked.

### Prompt + Hook

A hook can trigger a prompt automatically at a lifecycle event:

```json
{
  "atoms": [
    {
      "kind": "hook",
      "event": "pre-stop",
      "handler": {
        "type": "js",
        "entry": "./hooks/auto-commit-message.ts"
      }
    },
    {
      "kind": "prompt",
      "name": "commit-message",
      "template": "Generate a conventional commit message for:\n\n{{diff_summary}}"
    }
  ]
}
```

The hook fires on `pre-stop`, collects the diff, and invokes the prompt
atom to generate a commit message before the session ends.

### Prompt + Rule

A rule atom can validate the output of a prompt invocation:

```json
{
  "atoms": [
    {
      "kind": "prompt",
      "name": "migration-script",
      "template": "Generate a database migration for:\n\n{{schema_change}}\n\nTarget: {{db_engine}}"
    },
    {
      "kind": "rule",
      "event": "post-tool-use",
      "policy": "block",
      "reason": "Migration scripts must not contain DROP TABLE without explicit user confirmation"
    }
  ]
}
```

### Prompt + Resource

A resource atom provides data the prompt template references:

```json
{
  "atoms": [
    {
      "kind": "resource",
      "uri": "./assets/commit-conventions.md"
    },
    {
      "kind": "prompt",
      "name": "commit-message",
      "template": "Using the commit conventions from the project resource, generate a message for:\n\n{{diff_summary}}"
    }
  ]
}
```

## Template Anti-Patterns

| Anti-Pattern                              | Problem                                | Fix                                      |
| ----------------------------------------- | -------------------------------------- | ---------------------------------------- |
| God template (does everything)            | Fragile, hard to maintain              | Split into focused prompt atoms          |
| Instruction masquerading as prompt        | Wastes the invocation mechanism        | Convert to instruction atom              |
| Hardcoded values that should be variables | Inflexible across projects             | Extract to `{{variable}}`                |
| Vague output instructions                 | Inconsistent results                   | Add explicit format specification        |
| No variable documentation                 | Users do not know what to supply       | Add variable block at template top       |
| Template assumes session context          | Breaks when invoked in isolation       | Make all needed context explicit as vars  |
| Prompt doing tool work                    | Models cannot execute tools in prompts | Pair with hook or agent atom             |

## Template Quality Checklist

- [ ] Every `{{variable}}` has a descriptive snake_case name
- [ ] Required vs optional variables are documented or obvious
- [ ] Output format is explicitly specified (sections, checklist, table, fields)
- [ ] Template works with only the declared variables (no hidden dependencies)
- [ ] Template is under ~25 lines; longer workflows are split into stages
- [ ] No duplicated text across prompt atoms in the same bundle
- [ ] Template tested with sample values to verify coherent output
