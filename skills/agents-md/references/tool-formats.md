# Tool-Specific Instruction Formats

Sources: Anthropic Claude Code docs (2026), Cursor documentation, GitHub Copilot docs, OpenAI Codex docs, OpenCode docs, Windsurf docs, Google Gemini CLI docs, Aider docs

Covers: native instruction file format for every major AI coding tool, including file locations, format requirements, scoping mechanisms, and unique features.

## Format Comparison Matrix

| Tool | Primary File | Format | Frontmatter | Multi-File | Path Scoping | Auto-Memory |
|------|-------------|--------|-------------|------------|--------------|-------------|
| Codex CLI | AGENTS.md | Plain MD | No | Yes (nested dirs) | Nearest-file | No |
| Claude Code | CLAUDE.md | Plain MD | No | Yes (nested dirs + .claude/rules/) | Glob patterns | Yes |
| Cursor | .cursor/rules/*.mdc | MD + YAML | Required | Yes (rules dir) | Glob patterns | Unknown |
| GitHub Copilot | .github/copilot-instructions.md | Plain MD | Optional | Yes (.instructions.md) | YAML applyTo | Yes (Copilot Memory) |
| Windsurf | .windsurfrules | Plain MD | No | Limited | Directory-based | Yes (Memories) |
| Gemini CLI | GEMINI.md | Plain MD | No | Yes (nested dirs) | Nearest-file | No |
| OpenCode | AGENTS.md | Plain MD | No | Yes (global + project) | No | No |
| Aider | .aider.conf.yml | YAML config | N/A | Via config | No | Yes (conventions) |

## OpenAI Codex CLI

### File Locations

| Scope | Path | Purpose |
|-------|------|---------|
| Global | `~/.codex/AGENTS.md` | Personal defaults across all repos |
| Global override | `~/.codex/AGENTS.override.md` | Temporary global override |
| Project root | `./AGENTS.md` | Team-shared project instructions |
| Subdirectory | `./services/api/AGENTS.md` | Package-specific overrides |
| Subdirectory override | `./services/api/AGENTS.override.md` | Overrides subdirectory AGENTS.md |

### Discovery Order (per directory)

1. `AGENTS.override.md` (if exists)
2. `AGENTS.md`
3. Fallback filenames from `project_doc_fallback_filenames`
4. At most one file per directory

### Configuration

```toml
# ~/.codex/config.toml
project_doc_fallback_filenames = ["TEAM_GUIDE.md", "CLAUDE.md"]
project_doc_max_bytes = 65536
```

### Unique Features

- Override files at every level for temporary changes
- Configurable fallback filenames (can include CLAUDE.md)
- Size-limited concatenation with configurable byte cap
- `CODEX_HOME` environment variable for profile switching

## Claude Code (CLAUDE.md)

### File Locations

| Scope | Path | Shared | Purpose |
|-------|------|--------|---------|
| Managed policy | `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS) | Org-wide | IT-managed, cannot be excluded |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Via git | Team standards |
| User | `~/.claude/CLAUDE.md` | Personal | Cross-project preferences |
| Local | `./CLAUDE.local.md` | No (gitignored) | Personal project prefs |

### Hierarchy Loading

1. Managed policy CLAUDE.md loads first (cannot be excluded)
2. Walk up directory tree from CWD, loading CLAUDE.md + CLAUDE.local.md at each level
3. Subdirectory CLAUDE.md files load on demand when Claude reads files in those dirs
4. Within each directory: CLAUDE.local.md appended after CLAUDE.md
5. All files concatenated (not overridden)

### Import Syntax

```markdown
# CLAUDE.md
@AGENTS.md
@README.md
@docs/development-guide.md

## Additional Claude-specific rules
Use plan mode for changes under src/billing/.
```

Imports resolve relative to the containing file. Max depth: 5 hops. First-time external imports show an approval dialog.

### Unique Features

- `@path` import syntax for file references
- `.claude/rules/` directory with path-specific glob scoping
- Auto memory that persists learnings across sessions
- `claudeMdExcludes` setting to skip irrelevant monorepo files
- HTML comments stripped before injection (use for human-only notes)
- `/init` command generates initial CLAUDE.md
- `/memory` command to browse loaded instruction files

For full CLAUDE.md details, see `references/claude-code-deep.md`.

## Cursor (.cursor/rules/)

### File Locations

| File | Status | Purpose |
|------|--------|---------|
| `.cursorrules` | Legacy (still works) | Single project-level rules file |
| `.cursor/rules/*.mdc` | Current | Per-concern rules with glob scoping |
| AGENTS.md | Also read | Cross-tool instructions |

### MDC Format (Cursor-specific)

Cursor rules use Markdown with required YAML frontmatter:

```yaml
---
description: "TypeScript conventions for all source files"
globs: "src/**/*.{ts,tsx}"
alwaysApply: false
---

Use strict TypeScript. No `any` types. Named exports only.
Prefer interface over type for object shapes.
```

### Frontmatter Fields

| Field | Type | Purpose |
|-------|------|---------|
| `description` | string | Agent reads this to decide if rule is relevant |
| `globs` | string/array | File patterns that trigger rule loading |
| `alwaysApply` | boolean | Load on every request regardless of file context |

### Loading Behavior

- `alwaysApply: true`: Loaded into every prompt
- `alwaysApply: false` + `globs`: Loaded when matching files are in context
- `alwaysApply: false` + no `globs`: Agent decides based on `description` field
- Rules are additive (not overriding)

### Migration from .cursorrules

```bash
mkdir -p .cursor/rules
# Split monolithic file into topic-specific rules
mv .cursorrules .cursor/rules/general.mdc
# Add YAML frontmatter to each .mdc file
```

## GitHub Copilot

### File Locations

| File | Purpose |
|------|---------|
| `.github/copilot-instructions.md` | Repository-wide defaults |
| `.github/instructions/*.instructions.md` | Path-scoped instruction files |
| `.github/agents/*.md` | Agent persona definitions |
| `AGENTS.md` | Cross-tool (also read by Copilot) |

### Path-Scoped Instructions

```yaml
---
applyTo: "src/**/*.ts"
---

Use strict TypeScript with no `any` types.
All functions must have explicit return types.
```

### Agent Persona Files

```yaml
---
name: test-agent
description: Writes unit tests for TypeScript functions
---

You are a QA engineer. Write comprehensive tests.

## Boundaries
- Write to tests/ only
- Never modify source code
```

Invoke with `@test-agent` in Copilot chat.

### Unique Features

- Copilot Memory for auto-learning
- Agent personas with `@name` invocation
- Path-scoped `.instructions.md` with YAML `applyTo`
- Integrates with VS Code settings (`github.copilot.chat.codeGeneration.instructions`)

## Windsurf

### File Locations

| File | Purpose |
|------|---------|
| `.windsurfrules` | Project-level rules (root) |
| `AGENTS.md` | Cross-tool (also read) |
| `.windsurf/rules/` | Directory-based rules |

### Behavior

- Root `.windsurfrules` and root `AGENTS.md` are always active
- Subdirectory AGENTS.md files load when Cascade works in that directory
- Windsurf supports "Memories" -- auto-saved learnings from corrections
- System-level rules for enterprise compliance

## Gemini CLI (GEMINI.md)

### File Locations

| Scope | Path |
|-------|------|
| Global | `~/.gemini/GEMINI.md` |
| Project | `./GEMINI.md` |
| Subdirectory | Any nested `GEMINI.md` |

### Unique Behavior

- Reads GEMINI.md files both UP and DOWN the directory tree
- Concatenates all discovered files with path separators
- Inspect combined context with `/memory show`
- Configure in `.gemini/settings.json`:

```json
{
  "context": {
    "fileName": "AGENTS.md"
  }
}
```

## Aider

### Configuration

Aider uses `.aider.conf.yml` to load instruction files:

```yaml
# .aider.conf.yml
read: AGENTS.md
conventions: true
```

The `conventions` setting auto-loads a `CONVENTIONS.md` file. Aider also supports `.aider/conventions.md` for project-specific coding standards.

### Unique Features

- Convention files auto-loaded when `conventions: true`
- Multiple files can be listed under `read:`
- Supports repository map for codebase understanding
- No built-in directory traversal for instruction files

## OpenCode

### File Locations

| Scope | Path |
|-------|------|
| Project | `./AGENTS.md` |
| Global | `~/.config/opencode/AGENTS.md` |
| Fallback | `./CLAUDE.md` (if no AGENTS.md) |
| Global fallback | `~/.claude/CLAUDE.md` (if no opencode AGENTS.md) |

### Configuration Extensions

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "CONTRIBUTING.md",
    "docs/guidelines.md",
    ".cursor/rules/*.md",
    "https://raw.githubusercontent.com/org/repo/main/style.md"
  ]
}
```

### Unique Features

- `/init` command generates AGENTS.md from codebase analysis
- `instructions` field in `opencode.json` for additional files (supports globs and URLs)
- Claude Code compatibility mode (disable with `OPENCODE_DISABLE_CLAUDE_CODE=1`)
- Skills integration for on-demand task workflows
