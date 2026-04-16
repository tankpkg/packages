# Universal Pre-Publish Quality Checklist

Sources: Tank Contributing Standard (AGENTS.md), production publishing workflow, Tank registry conventions

Covers: every validation check for Tank packages before running `tank publish`.
Applicable to both instruction-only skills and multi-atom bundles. Organized
by file, then by concern. Run this checklist top-to-bottom before every publish.

## How to Use This Checklist

Run through each section sequentially. A single failure in a Critical gate
blocks publishing. Warnings indicate quality issues that degrade the package
but do not prevent publishing.

Severity levels:

| Level    | Meaning                                      |
| -------- | -------------------------------------------- |
| Critical | Blocks publishing. Must fix before `tank publish`. |
| High     | Causes user confusion or activation failure. Fix strongly recommended. |
| Medium   | Quality degradation. Fix when practical.     |
| Low      | Polish item. Fix if time allows.             |

## 1. Package Structure

### Critical

- [ ] Directory follows naming convention:
  - Instruction-only: `skills/{kebab-name}/`
  - Multi-atom: `bundles/{kebab-name}/`
- [ ] `{kebab-name}` uses only lowercase letters, digits, and hyphens
- [ ] `{kebab-name}` is 64 characters or fewer
- [ ] `SKILL.md` exists (required for instruction-only; optional for bundles but strongly recommended)
- [ ] `tank.json` exists at the package root

### High

- [ ] Reference files live in `references/` directory
- [ ] Scripts live in `scripts/` directory
- [ ] Assets live in `assets/` directory
- [ ] No unexpected files at the package root

### Medium

- [ ] No empty directories
- [ ] No backup files (.bak, .swp, .orig, ~files)
- [ ] No OS artifacts (.DS_Store, Thumbs.db)

## 2. SKILL.md Frontmatter

### Critical

- [ ] Frontmatter exists (YAML between `---` delimiters)
- [ ] `name` field is present
- [ ] `name` starts with `@tank/`
- [ ] `name` matches the directory: `@tank/{directory-name}`
- [ ] `name` matches `tank.json` `name` field exactly
- [ ] `description` field is present

### High

- [ ] `description` includes 10-15 trigger phrases
- [ ] `description` covers scope and capabilities (what the skill does)
- [ ] `description` includes source attribution (books, specs, docs synthesized)
- [ ] Trigger phrases cover how users actually phrase requests, not just formal names

### Medium

- [ ] Trigger phrases are comma-separated in quotes
- [ ] Description is 2-8 lines (not a single line, not a wall of text)
- [ ] No markdown formatting in frontmatter (no bold, no links, no code blocks)

## 3. SKILL.md Body

### Critical

- [ ] Body is under 200 lines (strict limit)
- [ ] First line of body is a level-1 heading (`# Title`)

### High

- [ ] Contains a Core Philosophy section with 3-5 numbered principles
- [ ] Each principle uses bold key phrase + explanation format
- [ ] Contains a Quick-Start or problem-solution section
- [ ] Decision trees rendered as tables, not prose
- [ ] Reference Index table is the LAST section of the body
- [ ] Every reference file is listed in the Reference Index

### Medium

- [ ] Uses imperative form ("Run the script" not "You should run")
- [ ] No "When to Use This Skill" section (belongs in description)
- [ ] No vendor-specific naming (claude-*, cc-*)
- [ ] No emoji anywhere in the body

### Low

- [ ] Consistent heading hierarchy (no skipped levels)
- [ ] Code blocks include language annotation
- [ ] Tables are properly aligned
- [ ] No trailing whitespace on lines

## 4. tank.json Manifest

### Critical

- [ ] Valid JSON (parseable without errors)
- [ ] `name` field is present and starts with `@tank/`
- [ ] `name` matches SKILL.md `name` exactly
- [ ] `version` field is present and valid semver (e.g., `1.0.0`)
- [ ] `permissions` object is present

### High

- [ ] `description` field is present and concise (1 paragraph max)
- [ ] `repository` field is `"https://github.com/tankpkg/packages"`
- [ ] `permissions.network.outbound` is an empty array unless the package makes HTTP calls
- [ ] `permissions.filesystem.read` is `["**/*"]` (standard default)
- [ ] `permissions.filesystem.write` is an empty array unless the package writes files
- [ ] `permissions.subprocess` is `false` unless the package runs shell commands

### Medium

- [ ] `description` includes key trigger terms (shorter than SKILL.md description)
- [ ] No unnecessary fields beyond the standard schema
- [ ] JSON is formatted with 2-space indentation

### Permission Audit

For each declared permission beyond the defaults, verify:

- [ ] `network.outbound` entries: each hostname is actually called by the package
- [ ] `filesystem.write` entries: each path is actually written to
- [ ] `subprocess: true`: the package actually executes shell commands
- [ ] No wildcard patterns in write paths (specific paths only)
- [ ] No unnecessary `subprocess: true` (instruction-only skills never need it)

## 5. Multi-Atom Bundle Validation

Skip this section entirely for instruction-only skills.

### Critical

- [ ] `atoms` array exists in `tank.json`
- [ ] Every atom has a valid `kind` field (one of: instruction, hook, agent, rule, tool, resource, prompt)
- [ ] Every `instruction` atom has a `content` field pointing to an existing file
- [ ] Every `hook` atom has an `event` field and a `handler` field
- [ ] Every `agent` atom has a `name` field and a `role` field
- [ ] Every `rule` atom has an `event` field and a `policy` field
- [ ] Every `tool` atom has a `name` field
- [ ] Every `resource` atom has a `uri` field
- [ ] Every `prompt` atom has a `name` field and a `template` field

### High

- [ ] Hook atoms: `handler.type` is either `"dsl"` or `"js"`
- [ ] Hook atoms with JS handlers: the entry file exists at the declared path
- [ ] Hook atoms: `event` is a canonical event name from the Tank specification
- [ ] Agent atoms: `tools` array uses canonical tool names (bash, read, write, edit, grep, glob, lsp, mcp, browser, fetch, git, task, notebook)
- [ ] Agent atoms: `model` is a valid tier (fast, balanced, powerful, custom) or a specific model ID string
- [ ] Rule atoms: `policy` is one of `block`, `warn`, `allow`
- [ ] Rule atoms: `reason` field is present (strongly recommended)
- [ ] Permissions cover what ALL atoms need combined

### Medium

- [ ] Extension bags use platform names as keys (claude-code, opencode, cursor, windsurf, default)
- [ ] Agent atoms with `readonly: true` do not have `write`, `edit`, or `bash` in their tools array
- [ ] No duplicate atom names within the same bundle
- [ ] Hook handler files use TypeScript (.ts) extension

## 6. Reference Files

### Critical

- [ ] Each reference file starts with a level-1 heading (`# Title`)
- [ ] Each reference file has a `Sources:` line (third line or immediately after title)

### High

- [ ] Each file is 250-450 lines (target range)
- [ ] No YAML frontmatter in any reference file
- [ ] No emoji in any reference file
- [ ] No content overlap between reference files
- [ ] Professional tone, imperative form throughout

### Medium

- [ ] Tables used for frameworks, comparisons, and decision trees
- [ ] Code blocks include language annotation
- [ ] Cross-references to other reference files where related
- [ ] Each file covers a distinct subtopic

### Low

- [ ] Consistent formatting across all reference files
- [ ] No broken internal references (e.g., "See section X" where X does not exist)
- [ ] Headers follow a logical hierarchy

## 7. Scripts and Assets

### High

- [ ] Scripts in `scripts/` are executable (correct shebang, permissions)
- [ ] Scripts have inline documentation explaining purpose and usage
- [ ] Assets in `assets/` are referenced somewhere in the package

### Medium

- [ ] Scripts do not hardcode paths or credentials
- [ ] Scripts use environment variables for configuration
- [ ] Asset file sizes are reasonable (no multi-MB files in context)

## 8. Content Quality

### High

- [ ] Package provides actionable value (decision trees, procedures, worked examples)
- [ ] Content synthesizes knowledge rather than summarizing or copying sources
- [ ] No placeholder content ("TODO", "TBD", "add later")
- [ ] No duplicate information between SKILL.md body and reference files

### Medium

- [ ] Consistent terminology throughout the package
- [ ] Acronyms defined on first use
- [ ] Examples use realistic, non-trivial scenarios
- [ ] Anti-patterns section included where appropriate

### Low

- [ ] Cross-references between reference files are bidirectional
- [ ] Examples are tested and functional
- [ ] Code snippets follow current best practices for their language

## 9. Pre-Publish Commands

Run these commands before publishing:

### Validate JSON

```bash
# Verify tank.json is valid JSON
python3 -c "import json; json.load(open('tank.json'))"
```

### Check Line Counts

```bash
# SKILL.md body should be under 200 lines (excluding frontmatter)
awk '/^---$/{n++; next} n>=2{print}' SKILL.md | wc -l

# Reference files should be 250-450 lines
wc -l references/*.md
```

### Dry Run

```bash
# Always dry-run first
tank publish --dry-run --org tank
```

### Verify Name Consistency

```bash
# Extract names and compare
grep '^name:' SKILL.md
python3 -c "import json; print(json.load(open('tank.json'))['name'])"
# These must match exactly
```

### Check for Secrets

```bash
# Scan for common secret patterns
grep -rn 'sk-\|api_key\|password\|secret\|token' . --include='*.md' --include='*.json' --include='*.ts'
# Should return nothing
```

## 10. Publishing Workflow

After all checks pass:

1. Create a feature branch for the new or updated package.
2. Commit all package files to the branch.
3. Open a PR and merge to `main`.
4. Only after the merge is complete, publish from `main`:

```bash
tank publish --org tank
```

Rules:
- Never publish from a feature branch.
- Always publish under the `tank` organization.
- Verify the `name` field starts with `@tank/` before publishing.
- Use `tank publish --dry-run` first to catch issues.

## Quick Reference: Minimum Viable Package

### Instruction-Only Skill

```
skills/{name}/
  SKILL.md       # Frontmatter (name, description) + body (<200 lines)
  tank.json      # name, version, description, permissions, repository
```

Minimum tank.json:

```json
{
  "name": "@tank/{name}",
  "version": "1.0.0",
  "description": "...",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages"
}
```

### Multi-Atom Bundle

```
bundles/{name}/
  tank.json      # name, version, description, permissions, repository, atoms
  SKILL.md       # Optional but recommended for instruction atom
```

Minimum tank.json with one atom:

```json
{
  "name": "@tank/{name}",
  "version": "1.0.0",
  "description": "...",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    { "kind": "instruction", "content": "./SKILL.md" }
  ]
}
```
