# Prompt Atom Anatomy

Sources: Tank Contributing Standard (AGENTS.md 2025-2026), Anthropic Prompt Engineering Guide, OpenAI Prompt Best Practices

Covers: The Tank prompt atom schema, required and optional fields, template variable syntax, how prompt atoms differ from instruction atoms, how adapters translate prompt atoms into platform-specific slash commands or invocable templates, and the lifecycle of a prompt invocation.

## What is a Prompt Atom

A prompt atom is a typed primitive in a Tank bundle's `tank.json` `atoms` array. It declares a reusable template that an agent can invoke by name, rather than absorbing automatically on session start. Think of it as a parameterized macro the user or agent triggers on demand.

Prompt atoms serve the same purpose as vendor-specific "commands" (Cursor's `.md` files in `commands/`, OpenCode's slash commands) but are declared portably in Tank's atom format. Adapters translate them to each platform's native mechanism.

### Atom Kind Table

| Kind          | Loaded When          | Purpose                            | Required Fields       |
| ------------- | -------------------- | ---------------------------------- | --------------------- |
| `instruction` | Every session start  | Behavioral context, always-on      | `content`             |
| `prompt`      | On invocation only   | Reusable template, on-demand       | `name`, `template`    |
| `hook`        | At lifecycle event   | Intercept and gate agent actions   | `event`, `handler`    |
| `agent`       | When delegated to    | Named sub-agent with tools         | `name`, `role`        |
| `rule`        | At lifecycle event   | Declarative policy enforcement     | `event`, `policy`     |
| `tool`        | When called          | MCP server registration            | `name`                |
| `resource`    | When read            | Data/context source                | `uri`                 |

## Schema Definition

### Required Fields

```json
{
  "kind": "prompt",
  "name": "pr-description",
  "template": "Write a pull request description for the following changes:\n\n{{diff_output}}\n\nInclude: summary, motivation, testing done."
}
```

**`name`** (string, required): The invocation identifier. Adapters translate
this into a slash command (`/pr-description`), a menu entry, or a callable
name depending on the platform.

Naming rules:
- Kebab-case: `commit-message`, `incident-report`, `code-review-checklist`
- Descriptive of the output, not the mechanism: `pr-description` not `run-template-3`
- Unique within the bundle: no two prompt atoms share a name
- Max 64 characters

**`template`** (string, required): The prompt text with optional variable
placeholders. This is the literal text sent to the model when the prompt is
invoked. It can be a single line or a multi-line string.

### Optional Fields

**`extensions`** (object, optional): Platform-specific overrides. Adapters
pass these through without validation.

```json
{
  "kind": "prompt",
  "name": "commit-message",
  "template": "...",
  "extensions": {
    "cursor": { "showInCommandPalette": true },
    "opencode": { "shortcut": "/cm" }
  }
}
```

Extensions are the escape hatch for platform behaviors that Tank's portable
schema does not model. Use sparingly -- every extension is a portability cost.

## Template Variable Syntax

### Double-Brace Placeholders

Variables use `{{variable_name}}` syntax. The adapter collects values from
the invoker (user input, tool output, or context) and substitutes them
before sending the rendered template to the model.

```
Generate a code review for:

Repository: {{repo_name}}
Files changed: {{changed_files}}
Diff:
{{diff_output}}

Focus areas: {{focus_areas}}
```

### Variable Naming Rules

| Rule                    | Good                     | Bad                      |
| ----------------------- | ------------------------ | ------------------------ |
| Descriptive noun        | `{{diff_output}}`        | `{{input1}}`             |
| Snake_case              | `{{ticket_url}}`         | `{{ticketUrl}}`          |
| No reserved words       | `{{file_content}}`       | `{{template}}`           |
| Specific over generic   | `{{error_stack_trace}}`  | `{{data}}`               |
| Indicate type if useful | `{{severity_level}}`     | `{{level}}`              |

### Optional Variables

Mark optional variables with a trailing question mark inside the braces.
Adapters omit the line or section if the value is not supplied.

```
{{changelog_entry?}}
```

This convention is adapter-dependent. Document which variables are required
vs optional in the template itself when possible.

### Multi-Line Templates

For complex templates, use JSON string escaping with `\n` for newlines,
or reference an external file. Inline is preferred for short templates
(under ~20 lines). For longer templates, consider splitting into multiple
prompt atoms that compose as a workflow.

```json
{
  "kind": "prompt",
  "name": "incident-report",
  "template": "## Incident Report\n\nSeverity: {{severity}}\nDate: {{date}}\n\n### Summary\n{{incident_summary}}\n\n### Timeline\n{{timeline}}\n\n### Root Cause\nAnalyze the above and determine root cause.\n\n### Action Items\nList 3-5 concrete action items to prevent recurrence."
}
```

## Prompt vs Instruction: The Loading Model

This is the critical distinction. Confusing the two wastes context tokens
or hides useful templates where users cannot find them.

### Loading Behavior

| Aspect          | Instruction Atom                  | Prompt Atom                        |
| --------------- | --------------------------------- | ---------------------------------- |
| When loaded     | Every session, automatically      | On invocation only                 |
| Token cost      | Always consumed                   | Zero until invoked                 |
| User triggers   | Never -- agent absorbs silently   | By name, slash command, or menu    |
| Parameterized   | No (static text)                  | Yes ({{variables}})                |
| Typical use     | Coding standards, project context | Generators, formatters, workflows  |
| Context budget  | Counts against session budget     | Counts only when rendered          |

### Decision Framework

Use an **instruction atom** when:
- The agent needs this information in every session
- The content defines behavioral rules or coding standards
- There are no variable slots -- the text is static
- Forgetting this context would cause incorrect behavior

Use a **prompt atom** when:
- A user or agent invokes the template by name
- The template has variable slots that change per invocation
- The workflow is occasional, not continuous
- The output is a generated artifact (PR description, commit message, report)

### Gray Areas

Some content could go either way. Apply this tiebreaker: if the agent
needs the information even when the user has not asked for it, use an
instruction. If the information is only relevant when explicitly requested,
use a prompt.

| Scenario                                  | Verdict           | Why                                  |
| ----------------------------------------- | ----------------- | ------------------------------------ |
| "Always use conventional commits"         | Instruction       | Behavioral rule, every session       |
| "Generate a conventional commit message"  | Prompt            | On-demand generator with variables   |
| "Our API uses REST conventions"           | Instruction       | Context needed for all API work      |
| "Generate an API endpoint scaffold"       | Prompt            | Template invoked when building new   |
| "Code review checklist"                   | Prompt            | Invoked per review, not always       |
| "Never commit secrets"                    | Instruction (rule) | Safety rule, always active           |

## Adapter Translation

Adapters translate prompt atoms into platform-native mechanisms. The
Tank runtime does not execute prompts directly -- it declares them, and
adapters bridge the gap.

### Translation Table

| Platform    | Prompt Atom Becomes                           |
| ----------- | --------------------------------------------- |
| Cursor      | `.md` file in `.cursor/commands/`             |
| OpenCode    | Slash command registered in config            |
| Claude Code | Callable prompt template                      |
| Windsurf    | Custom command                                |
| VS Code     | Command palette entry via extension           |

### Invocation Flow

1. User or agent triggers the prompt by name
2. Adapter collects variable values (from user input, context, or tools)
3. Adapter substitutes variables into the template string
4. Rendered template is sent to the model as a user message or injected prompt
5. Model generates the output
6. Output is returned to the user or passed to the next step

## Prompt Atom in tank.json

### Placement

Prompt atoms live in the `atoms` array alongside other atom kinds. A
bundle can have zero, one, or many prompt atoms.

```json
{
  "name": "@tank/git-workflows",
  "version": "1.0.0",
  "atoms": [
    { "kind": "instruction", "content": "./SKILL.md" },
    {
      "kind": "prompt",
      "name": "commit-message",
      "template": "Generate a conventional commit message for:\n\n{{diff_summary}}\n\nTicket: {{ticket_id}}"
    },
    {
      "kind": "prompt",
      "name": "pr-description",
      "template": "Write a PR description for:\n\n{{diff_output}}\n\nInclude summary, motivation, and testing notes."
    }
  ]
}
```

### Validation Checklist

- [ ] `kind` is exactly `"prompt"`
- [ ] `name` is present, kebab-case, unique within the bundle
- [ ] `template` is present and non-empty
- [ ] All `{{variables}}` use snake_case naming
- [ ] No `{{variable}}` shadows a reserved field name (`name`, `kind`, `template`)
- [ ] `extensions` (if present) uses platform names as keys
- [ ] Template renders correctly with sample variable values

## Prompt Atom Lifecycle

Understanding the full lifecycle of a prompt invocation helps debug
issues and design templates that work reliably across adapters.

### Stage 1: Registration

When a bundle with prompt atoms is installed, the adapter reads each
prompt atom and registers it in the platform's command system. The
`name` field becomes the invocation key. Registration happens once
at install time, not per session.

### Stage 2: Discovery

Users discover available prompts through the platform's command palette,
slash command autocomplete, or documentation. The `name` field is the
primary discovery mechanism. Descriptive names (`pr-description`) beat
cryptic abbreviations (`prd`).

### Stage 3: Invocation

The user triggers the prompt by name. The adapter determines which
variables the template requires by scanning for `{{variable_name}}`
patterns. It collects values from:
- User input (typed or selected)
- Agent context (current file, selection, session state)
- Tool output (git diff, file content, command results)

### Stage 4: Rendering

The adapter substitutes collected values into the template string,
replacing each `{{variable_name}}` with its value. Optional variables
(`{{variable?}}`) that have no value are either removed or replaced
with an empty string, depending on the adapter.

### Stage 5: Execution

The rendered template is sent to the model as a prompt. The model
generates the output according to the template's format instructions.

### Stage 6: Output

The generated output is returned to the user or passed to the next
step in a workflow (another prompt, a tool invocation, or a file write).

## Common Mistakes

| Mistake                                          | Fix                                         |
| ------------------------------------------------ | ------------------------------------------- |
| Using a prompt atom for always-on context        | Convert to instruction atom                 |
| Putting complex logic in the template            | Pair with a hook or agent atom              |
| Unnamed or generic variable names                | Use descriptive snake_case names            |
| Template longer than ~30 lines inline            | Split into multiple prompts or stages       |
| Duplicating template text across atoms           | Extract shared preamble to an instruction   |
| Using prompt atom where a rule atom fits         | Rules enforce; prompts generate             |

## Tank Prompt Atoms vs MCP Prompts

Tank prompt atoms and MCP prompt primitives share terminology but are
different mechanisms. Avoid confusing the two.

| Aspect             | Tank Prompt Atom                      | MCP Prompt                           |
| ------------------ | ------------------------------------- | ------------------------------------ |
| Declared in        | `tank.json` atoms array               | MCP server manifest                  |
| Schema             | `{ kind, name, template }`            | `{ name, description, arguments }`   |
| Execution          | Adapter renders and sends to model    | MCP client resolves from server      |
| Variable syntax    | `{{double_braces}}`                   | JSON Schema arguments                |
| Portability        | Across all Tank adapters              | Across MCP-compatible clients        |
| Purpose            | Reusable agent prompt template        | Server-provided prompt suggestions   |

When authoring Tank bundles, use Tank prompt atoms for templates the
bundle owns. Use MCP tool atoms to connect to external MCP servers
that may expose their own prompts.
