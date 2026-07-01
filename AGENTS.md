# Tank Skills — Contributing Standard

This repository contains reusable AI agent skills published under the
`@tank` namespace. Every skill follows the conventions below.

## Package Types

Tank supports two package formats. Use the simplest one that fits.

### Instruction-only (legacy, most skills)

A single `SKILL.md` instruction blob. No build step, no atoms.

```
skills/{kebab-name}/
├── SKILL.md              # Required — frontmatter + body (<200 lines)
├── tank.json             # Required — metadata + permissions (no atoms field)
├── references/           # Optional — context-loaded deep docs (250-450 lines each)
├── scripts/              # Optional — executable code
└── assets/               # Optional — templates, images (not loaded into context)
```

### Multi-atom (new format)

Packages with hooks, agents, rules, tools, resources, or prompts.
The `tank.json` has an `atoms` array that defines typed primitives.

```
skills/{kebab-name}/
├── SKILL.md              # Optional — instruction content (referenced by an atom)
├── tank.json             # Required — metadata + permissions + atoms array
├── hooks/                # Optional — JS/TS hook handlers (referenced by hook atoms)
├── references/           # Optional — context-loaded deep docs (250-450 lines each)
├── scripts/              # Optional — executable code
└── assets/               # Optional — templates, images (not loaded into context)
```

### When to use which

| Signal                                    | Format           |
| ----------------------------------------- | ---------------- |
| Skill is pure instructions/knowledge      | Instruction-only |
| Need hooks that intercept agent behavior  | Multi-atom       |
| Need a custom reviewer/auditor agent      | Multi-atom       |
| Need enforcement rules (block/allow/warn) | Multi-atom       |
| Need MCP tool registration                | Multi-atom       |
| Need prompt templates or slash commands   | Multi-atom       |

## Naming

- Directory: `skills/{kebab-name}/` — lowercase, digits, hyphens only
- Package name: `@tank/{kebab-name}` — used in both `SKILL.md` and `tank.json`
- Max 64 characters for the `{kebab-name}` portion

## SKILL.md

### Frontmatter (YAML)

```yaml
---
name: "@tank/{kebab-name}"
description: |
  What the skill does — 2-4 lines covering scope and capabilities.
  Source attribution — books, frameworks, specifications synthesized.

  Trigger phrases: "phrase 1", "phrase 2", ... (10-15 phrases minimum)
---
```

- `name`: Must match `@tank/{directory-name}` exactly
- `description`: The PRIMARY triggering mechanism. Body loads AFTER
  triggering, so everything needed to decide "should this skill activate?"
  must be in the description. Include:
  - What the skill covers (scope)
  - Source attribution (books, specs, docs)
  - 10-15 trigger phrases covering how users phrase requests

### Body Structure

```markdown
# {Title}

## Core Philosophy

{3-5 numbered principles, bold key phrase + explanation}

## Quick-Start: Common Problems

### "{Problem 1}"

1. Step...
   -> See `references/{file}.md`

## Decision Trees

| Signal | Recommendation |
| ------ | -------------- |

## Reference Index

| File                   | Contents             |
| ---------------------- | -------------------- |
| `references/{file}.md` | One-line description |
```

### Body Rules

- Under 200 lines (strict)
- Imperative form: "Run the script" not "You should run"
- Problem-solution framing: common tasks users bring
- Decision trees as tables, not prose
- Reference index table as the LAST section
- Every reference file listed in the index
- No "When to Use This Skill" sections (that belongs in `description`)

## tank.json

### Instruction-only packages

```json
{
  "name": "@tank/{kebab-name}",
  "version": "1.0.0",
  "description": "Concise description. Include key triggers.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/skills"
}
```

No `atoms` field — Tank auto-generates a single instruction atom from `SKILL.md`.

### Multi-atom packages

```json
{
  "name": "@tank/{kebab-name}",
  "version": "1.0.0",
  "description": "Concise description. Include key triggers.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/skills",
  "atoms": [
    { "kind": "instruction", "content": "./SKILL.md" },
    {
      "kind": "hook",
      "event": "pre-stop",
      "handler": { "type": "js", "entry": "./hooks/gate.ts" }
    },
    {
      "kind": "agent",
      "name": "reviewer",
      "role": "Code reviewer",
      "tools": ["read", "grep"],
      "readonly": true
    },
    {
      "kind": "rule",
      "event": "pre-stop",
      "policy": "block",
      "reason": "Issues found"
    }
  ]
}
```

### Atom kinds

| Kind          | Purpose                                | Required fields       |
| ------------- | -------------------------------------- | --------------------- |
| `instruction` | Behavioral context injected into agent | `content` (file path) |
| `hook`        | Code that runs at lifecycle points     | `event`, `handler`    |
| `agent`       | Named role with tools and permissions  | `name`, `role`        |
| `rule`        | Machine-enforced validation constraint | `event`, `policy`     |
| `tool`        | MCP server the agent can invoke        | `name`                |
| `resource`    | Data/context the agent can read        | `uri`                 |
| `prompt`      | Reusable invocable template            | `name`, `template`    |

### Hook events

Canonical events (adapters translate to platform-specific equivalents):

| Category      | Events                                                                                                        |
| ------------- | ------------------------------------------------------------------------------------------------------------- |
| Tool          | `pre-tool-use`, `post-tool-use`                                                                               |
| File          | `pre-file-read`, `post-file-read`, `pre-file-write`, `post-file-write`, `file-edited`, `file-watcher-updated` |
| Shell         | `pre-command`, `post-command`                                                                                 |
| MCP           | `pre-mcp-tool-use`, `post-mcp-tool-use`                                                                       |
| Session       | `session-created`, `session-updated`, `session-idle`, `session-error`, `session-deleted`                      |
| Stop          | `pre-stop` (blocking — can force agent to continue)                                                           |
| Task          | `task-start`, `task-resume`, `task-complete`, `task-cancel`                                                   |
| Conversation  | `pre-user-prompt`, `post-response`, `message-updated`, `message-removed`                                      |
| System prompt | `system-prompt-transform`                                                                                     |
| Context       | `pre-context-compact`, `post-context-compact`                                                                 |
| Permissions   | `permission-asked`, `permission-replied`                                                                      |
| IDE/LSP       | `lsp-diagnostics`, `lsp-updated`                                                                              |
| Subagent      | `subagent-start`, `subagent-complete`, `subagent-tool-use`                                                    |
| Environment   | `shell-env`                                                                                                   |
| Workflow      | `todo-updated`, `installation-updated`                                                                        |

### Hook handlers

Two types — use DSL for simple portable logic, JS for complex behavior:

```json
{ "type": "dsl", "actions": [{ "action": "block", "match": "rm -rf", "reason": "Destructive" }] }
{ "type": "js", "entry": "./hooks/my-hook.ts" }
```

DSL actions: `block`, `allow`, `rewrite`, `injectContext`.

### Canonical tool names

For `match` and agent `tools` fields: `bash`, `read`, `write`, `edit`,
`grep`, `glob`, `lsp`, `mcp`, `browser`, `fetch`, `git`, `task`, `notebook`.
Custom strings also accepted.

### Model tiers

For agent `model` field: `fast`, `balanced`, `powerful`, `custom`.
Custom strings also accepted.

### Extension bags

Any atom can include an `extensions` object with platform-specific overrides.
Extensions are passed through without validation — adapters own their shape.

```json
{
  "kind": "instruction",
  "content": "./SKILL.md",
  "extensions": {
    "cursor": { "alwaysApply": true },
    "opencode": { "scope": "global" }
  }
}
```

### Manifest rules

- `version`: Semver. Start at `1.0.0` for new skills.
- `description`: Shorter than SKILL.md description. One paragraph.
- `permissions`: Minimal by default. Only add when actually needed:
  - Network: specific hostnames for API calls
  - Filesystem write: specific paths
  - Subprocess: only when running scripts

## Reference Files

### Format

```markdown
# {Title}

Sources: Author1 (Book1), Author2 (Book2), {year} research

Covers: brief scope sentence.

## {Major Section}

{Content: tables, frameworks, procedures}

### {Subsection}

{More specific content}
```

### Rules

| Rule        | Requirement                                           |
| ----------- | ----------------------------------------------------- |
| First line  | `# Title` (H1)                                        |
| Third line  | `Sources: {attribution}`                              |
| Length      | 250-450 lines target                                  |
| Frontmatter | None (only SKILL.md has YAML)                         |
| Emoji       | None                                                  |
| Tone        | Professional, imperative                              |
| Tables      | Use for frameworks, comparisons, decision trees       |
| Code blocks | Include language annotation                           |
| Overlap     | Each file covers a distinct subtopic — no duplication |
| Cross-refs  | Link to other reference files when related            |

## Quality Checklist

### SKILL.md

- [ ] `name` field starts with `@tank/`
- [ ] `description` includes 10-15 trigger phrases
- [ ] `description` includes scope, capabilities, sources
- [ ] Body under 200 lines
- [ ] Core Philosophy section (3-5 principles)
- [ ] Quick-Start or problem-solution section
- [ ] Decision trees as tables
- [ ] Reference Index table at end

### tank.json

- [ ] `name` matches SKILL.md `name` exactly
- [ ] `version` is valid semver
- [ ] `description` is concise (1 paragraph)
- [ ] `permissions` uses minimal defaults
- [ ] `repository` points to `https://github.com/tankpkg/skills`

### Multi-atom packages (additional)

- [ ] Every atom has a valid `kind`
- [ ] Hook atoms reference existing handler files
- [ ] Agent atoms have `name` and `role`
- [ ] Rule atoms have `event` and `policy`
- [ ] Extension bags use platform names as keys

### Reference Files

- [ ] Each starts with `# Title` then `Sources:` line
- [ ] No YAML frontmatter
- [ ] No emoji
- [ ] No content overlap between files
- [ ] Professional tone, imperative form
- [ ] Tables for frameworks and comparisons

## Publishing

### Workflow

1. Create a feature branch for the new or updated skill
2. Commit all skill files to the branch
3. Open a PR and merge to `main` (the `main` branch is protected — direct
   pushes are rejected, so a PR is required)
4. Only after the merge is complete, pull `main` locally and publish from
   the skill directory:

```bash
git checkout main && git pull origin main
cd skills/<your-skill>/
tank publish --dry-run    # validate and pack without uploading
tank publish              # upload to the registry
```

Never publish from a feature branch — the source must exist on `main` first.

### Publish target

The publish target is inferred from the `name` field in `tank.json`. As long
as `name` starts with `@tank/`, the skill publishes under the `tank`
organization. There is no `--org` flag on `tank publish`.

### Available flags

```
tank publish [options]

  --dry-run            Validate and pack without uploading
  --private            Publish skill as private
  --visibility <mode>  Skill visibility (public|private)
```

Defaults to public visibility.

### Rules

- Every skill in this repo belongs to the `@tank` namespace
- The `name` field in `tank.json` MUST start with `@tank/` — this is what
  routes the publish to the `tank` org. Never use a personal namespace.
- Run `tank publish --dry-run` first to catch packing or auth issues before
  uploading
- Confirm you are on `main` and pulled latest before publishing — publishing
  packs the current working directory, not a git ref
- Confirm you are authenticated: `tank whoami` (use `tank login` if not)
