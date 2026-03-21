# Tank Skills — Contributing Standard

This repository contains reusable AI agent skills published under the
`@tank` namespace. Every skill follows the conventions below.

## Directory Structure

```
skills/{kebab-name}/
├── SKILL.md              # Required — frontmatter + body (<200 lines)
├── skills.json           # Required — metadata + permissions
├── references/           # Optional — context-loaded deep docs (250-450 lines each)
├── scripts/              # Optional — executable code
└── assets/               # Optional — templates, images (not loaded into context)
```

## Naming

- Directory: `skills/{kebab-name}/` — lowercase, digits, hyphens only
- Package name: `@tank/{kebab-name}` — used in both `SKILL.md` and `skills.json`
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
|--------|---------------|

## Reference Index
| File | Contents |
|------|----------|
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

## skills.json

```json
{
  "name": "@tank/{kebab-name}",
  "version": "1.0.0",
  "description": "Concise description matching SKILL.md description scope. Include key triggers.",
  "permissions": {
    "network": {
      "outbound": []
    },
    "filesystem": {
      "read": ["**/*"],
      "write": []
    },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/skills"
}
```

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

| Rule | Requirement |
|------|-------------|
| First line | `# Title` (H1) |
| Third line | `Sources: {attribution}` |
| Length | 250-450 lines target |
| Frontmatter | None (only SKILL.md has YAML) |
| Emoji | None |
| Tone | Professional, imperative |
| Tables | Use for frameworks, comparisons, decision trees |
| Code blocks | Include language annotation |
| Overlap | Each file covers a distinct subtopic — no duplication |
| Cross-refs | Link to other reference files when related |

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

### skills.json
- [ ] `name` matches SKILL.md `name` exactly
- [ ] `version` is valid semver
- [ ] `description` is concise (1 paragraph)
- [ ] `permissions` uses minimal defaults
- [ ] `repository` points to `https://github.com/tankpkg/skills`

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
3. Open a PR and merge to `main`
4. Only after the merge is complete, publish from `main`:

```bash
tank publish --org tank
```

Never publish from a feature branch — the source must exist on `main` first.

### Rules

- Every skill in this repo belongs to the `@tank` namespace
- Always publish under the `tank` organization — never a personal account or other org
- Verify the `name` field in `skills.json` starts with `@tank/` before publishing
- Use `tank publish --dry-run` first to catch issues
