---
name: "@tank/prompt-creator"
description: |
  Author Tank prompt atoms -- reusable invocable templates declared in
  bundle tank.json files. Covers the prompt atom schema (name, template),
  template variable syntax, structured output guidance, multi-step workflow
  templates, composing prompts with agent and hook atoms, and when to use
  a prompt atom vs an instruction atom. Synthesizes the Tank Contributing
  Standard (AGENTS.md), the ECC command-to-prompt migration pattern, and
  prompt engineering best practices from Anthropic and OpenAI documentation.

  Trigger phrases: "create prompt", "prompt template", "tank prompt atom",
  "slash command", "workflow template", "prompt atom", "write a prompt",
  "invocable template", "parameterized prompt", "reusable prompt",
  "prompt variable", "commit message template", "PR description template",
  "incident report template", "code review prompt"
---

# Tank Prompt Creator

Author prompt atoms that give agents on-demand templates triggered by
name or slash command, rather than always-loaded instruction context.

## Core Philosophy

1. **Prompts are invocable, not ambient.** A prompt atom loads only when
   triggered by name. An instruction atom loads every session. Put
   workflows the agent always needs in instructions; put templates the
   user sometimes invokes in prompts.
   -> See `references/prompt-atom-anatomy.md`

2. **Variables are contracts.** Every `{{variable}}` in a template is a
   parameter the invoker must supply. Name variables for what the value
   represents, not where it goes. `{{diff_output}}` beats `{{input1}}`.
   -> See `references/template-design.md`

3. **One prompt, one job.** A prompt that generates a PR description
   should not also run linting. Compose multiple prompts in a bundle
   if the workflow has stages, but keep each template focused.

4. **Structured output over prose.** Templates that produce structured
   formats (markdown sections, checklists, labeled fields) are more
   useful downstream than templates that produce free-form paragraphs.
   -> See `references/template-design.md`

5. **Compose with atoms, not with bloat.** A prompt atom can reference
   agents (for delegation), hooks (for triggering), and instructions
   (for shared context). Keep the template lean; let companion atoms
   handle orchestration.
   -> See `references/worked-examples.md`

## Quick-Start: Common Problems

### "Turn an ECC command into a Tank prompt"

1. Extract the command's template text and variable slots
2. Map each slot to a `{{variable_name}}` with a descriptive name
3. Add the atom to `tank.json`: `{ "kind": "prompt", "name": "...", "template": "..." }`
4. If the command had complex logic, pair with a hook or agent atom
   -> See `references/worked-examples.md` (PR Description Generator)

### "Create a slash command for commit messages"

1. Define the template with `{{diff_summary}}` and `{{ticket_id}}` variables
2. Add the prompt atom to a bundle's `tank.json`
3. Adapters translate the `name` field into a slash command
   -> See `references/worked-examples.md` (Commit Message Formatter)

### "Prompt vs instruction -- which do I use?"

1. Check the decision tree below
2. If the content applies every session, use an instruction atom
3. If the content is invoked on demand by name, use a prompt atom
   -> See `references/prompt-atom-anatomy.md` (Prompt vs Instruction)

### "Template has too many variables"

1. Split into multiple prompts, each handling one stage
2. Chain prompts in a workflow by composing with agent atoms
3. Provide sensible defaults or optional variables where possible
   -> See `references/template-design.md` (Multi-Step Workflows)

## Decision Trees

### Prompt Atom vs Instruction Atom

| Signal                                        | Use Prompt         | Use Instruction    |
| --------------------------------------------- | ------------------ | ------------------ |
| User triggers by name or slash command        | Yes                | No                 |
| Template with variable slots                  | Yes                | No                 |
| Always-needed behavioral context              | No                 | Yes                |
| Agent should know this every session          | No                 | Yes                |
| On-demand workflow or generator               | Yes                | No                 |

### Template Complexity

| Signal                                        | Recommendation                    |
| --------------------------------------------- | --------------------------------- |
| Single output, few variables                  | One prompt atom                   |
| Multi-stage workflow, sequential outputs      | Multiple prompts + agent atom     |
| Needs tool execution during generation        | Prompt + hook atom                |
| Needs enforcement or validation               | Prompt + rule atom                |
| Needs external data before rendering          | Prompt + resource atom            |

### Variable Design

| Variable Type     | Naming Convention        | Example                       |
| ----------------- | ------------------------ | ----------------------------- |
| Raw input data    | `{{noun_description}}`   | `{{diff_output}}`             |
| Configuration     | `{{setting_name}}`       | `{{severity_threshold}}`      |
| Context reference | `{{context_source}}`     | `{{ticket_url}}`              |
| Output constraint | `{{format_spec}}`        | `{{max_length}}`              |

### Manifest Wiring

| Component          | Location in tank.json                                     |
| ------------------ | --------------------------------------------------------- |
| Prompt atom        | `atoms[]` with `kind: "prompt"`                           |
| Name (slash cmd)   | `name` field on the prompt atom                           |
| Template body      | `template` field (inline string or file reference)        |
| Companion agent    | Separate atom with `kind: "agent"`                        |
| Companion hook     | Separate atom with `kind: "hook"` for triggering logic    |

## Atom Schema Quick Reference

```json
{
  "kind": "prompt",
  "name": "commit-message",
  "template": "Generate a commit message for these changes:\n\n{{diff_summary}}\n\nTicket: {{ticket_id}}\n\nFormat: conventional commits (type: description)"
}
```

Required fields: `name`, `template`. Optional: `extensions` for
platform-specific overrides.

## Reference Index

| File                                  | Contents                                              |
| ------------------------------------- | ----------------------------------------------------- |
| `references/prompt-atom-anatomy.md`   | Prompt atom schema, variable syntax, prompt vs instruction distinction |
| `references/template-design.md`       | Variable naming, structured output, multi-step workflows, composition |
| `references/worked-examples.md`       | 4+ worked prompt atoms with full bundle context        |
