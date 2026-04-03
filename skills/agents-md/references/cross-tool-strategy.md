# Cross-Tool Compatibility Strategy

Sources: agents.md official site, Anthropic Claude Code docs, Augment Code guide (2026), vibecoding.app AGENTS.md guide (2026), OpenCode docs

Covers: canonical file patterns for multi-tool teams, symlink strategies, import syntax per tool, migration paths between formats, and the "write once, read everywhere" workflow.

## The Multi-Tool Problem

Most teams use multiple AI coding tools. A developer might use Cursor daily, run Claude Code for complex refactors, and have GitHub Copilot active in VS Code. Without a strategy, this produces:

```
project/
  AGENTS.md              # For Codex, Copilot, Cursor, Windsurf
  CLAUDE.md              # For Claude Code
  .cursorrules           # Legacy Cursor
  .cursor/rules/         # Current Cursor
  .windsurfrules         # Windsurf
  GEMINI.md              # Gemini CLI
  .github/copilot-instructions.md  # Copilot
```

The same content in each file. Slowly drifting apart. Every update requires editing 5+ files. This is the canonical failure mode.

## The Canonical File Pattern

Maintain one source of truth in AGENTS.md. Connect other tools to it.

### Recommended Layout

```
project/
  AGENTS.md                              # Canonical: shared rules
  CLAUDE.md                              # Imports AGENTS.md + Claude-specific
  .cursor/rules/shared.mdc              # References AGENTS.md content
  .github/copilot-instructions.md       # Copilot-specific only
```

### Strategy Per Tool

| Tool | Strategy | Implementation |
|------|----------|---------------|
| Codex CLI | Direct read | Already reads AGENTS.md natively |
| Claude Code | Import | `@AGENTS.md` in CLAUDE.md |
| Cursor | Dual read | Reads AGENTS.md + .cursor/rules/ |
| GitHub Copilot | Dual read | Reads AGENTS.md + .github/ files |
| Windsurf | Dual read | Reads AGENTS.md + .windsurfrules |
| OpenCode | Direct read | AGENTS.md primary, CLAUDE.md fallback |
| Gemini CLI | Config redirect | Point settings.json at AGENTS.md |
| Aider | Config | `read: AGENTS.md` in .aider.conf.yml |
| Amp | Direct + fallback | Reads AGENTS.md, falls back to CLAUDE.md |

## Implementation: CLAUDE.md Bridge

Claude Code does not natively read AGENTS.md. Create a CLAUDE.md that imports it:

```markdown
# CLAUDE.md

@AGENTS.md

## Claude Code Specific

Use plan mode for changes under src/billing/.
Prefer the Read tool over grep for files under 500 lines.
```

Claude loads the imported AGENTS.md at session start, then appends the Claude-specific instructions. This gives Claude Code all the shared context plus tool-specific guidance.

### What Goes in CLAUDE.md Only

- Claude Code permission boundaries (plan mode triggers)
- Claude-specific tool preferences
- MCP server configuration references
- Auto memory adjustments

### What Stays in AGENTS.md

Everything that applies regardless of which tool is being used: stack, commands, conventions, boundaries, testing rules.

## Implementation: Cursor Bridge

Cursor reads AGENTS.md natively as of 2026. Use `.cursor/rules/*.mdc` files for Cursor-specific features that AGENTS.md cannot express:

### Glob-Scoped Rules (Cursor only)

```yaml
---
description: "API development standards"
globs: "src/api/**/*.ts"
alwaysApply: false
---

All API endpoints must include input validation using Zod.
Use the standard error response format from src/api/errors.ts.
Include OpenAPI documentation comments.
```

This rule loads only when Cursor works on API files. AGENTS.md has no glob-scoping mechanism, so this is a legitimate Cursor-only concern.

### Migration from .cursorrules

1. Copy shared content from `.cursorrules` to `AGENTS.md`
2. Split Cursor-specific rules into `.cursor/rules/*.mdc` with appropriate globs
3. Add YAML frontmatter to each `.mdc` file
4. Remove `.cursorrules` or leave as legacy fallback

```bash
# Step-by-step
cp .cursorrules AGENTS.md
mkdir -p .cursor/rules
# Extract glob-specific rules into .mdc files
# Delete .cursorrules when confident
```

## Implementation: Copilot Bridge

GitHub Copilot reads AGENTS.md natively. Use `.github/copilot-instructions.md` for Copilot-specific defaults and `.github/instructions/*.instructions.md` for path-scoped rules:

```yaml
---
applyTo: "src/components/**/*.tsx"
---

Use functional components with hooks.
All components must accept a className prop for style composition.
```

### Copilot Agent Personas

Copilot's `.github/agents/*.md` system is a unique feature. Define specialized agents that can be invoked by name:

```markdown
---
name: security-agent
description: Reviews code for security vulnerabilities
---

You are a security engineer reviewing this codebase.

## Focus Areas
- Input validation and sanitization
- Authentication and authorization checks
- Secret exposure in code or config
```

This has no equivalent in AGENTS.md -- keep it in the Copilot-specific directory.

## Implementation: Gemini CLI Bridge

Gemini CLI uses GEMINI.md by default. Redirect it to read AGENTS.md:

```json
{
  "context": {
    "fileName": "AGENTS.md"
  }
}
```

Place in `.gemini/settings.json`. Gemini CLI then reads AGENTS.md instead of looking for GEMINI.md. Create a minimal GEMINI.md only if Gemini-specific instructions are needed.

## Implementation: Aider Bridge

Configure Aider to load AGENTS.md:

```yaml
# .aider.conf.yml
read: AGENTS.md
conventions: true
```

The `conventions: true` setting enables Aider's convention system. The `read` directive loads AGENTS.md into context at the start of every session.

## Implementation: OpenCode Bridge

OpenCode reads AGENTS.md natively. For additional instruction files:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "docs/development-guide.md",
    ".cursor/rules/*.md"
  ]
}
```

OpenCode can load Cursor rules, remote URLs, and arbitrary Markdown files alongside AGENTS.md.

## The Symlink Pattern

For tools that read their own filename but not AGENTS.md:

```bash
# AGENTS.md is the canonical file
# Create symlinks for tools that need specific filenames
ln -s AGENTS.md CLAUDE.md       # If Claude-specific rules not needed
ln -s AGENTS.md .windsurfrules  # If Windsurf-specific rules not needed
ln -s AGENTS.md GEMINI.md       # If Gemini-specific rules not needed
```

### Symlink Caveats

- Git tracks symlinks as symlinks -- team members on Windows may need `git config core.symlinks true`
- If any tool-specific instructions are needed, use import/reference instead of symlink
- Test that each tool correctly resolves the symlink

## Migration Decision Tree

| Current State | Target | Steps |
|---------------|--------|-------|
| Only .cursorrules | AGENTS.md + Cursor rules | Copy shared to AGENTS.md, split Cursor-specific into .mdc |
| Only CLAUDE.md | AGENTS.md + CLAUDE.md bridge | Move shared content to AGENTS.md, add `@AGENTS.md` import |
| Multiple duplicate files | Single canonical AGENTS.md | Diff all files, merge into AGENTS.md, create tool bridges |
| No instruction files | AGENTS.md from scratch | Use template from `references/writing-rules.md` |
| AGENTS.md already canonical | Add new tool | Create tool-specific bridge (symlink or import) |

## Migration Checklist

1. Inventory all existing instruction files across the project
2. Diff them to identify shared vs tool-specific content
3. Create AGENTS.md with all shared content
4. Create minimal tool-specific files that import or reference AGENTS.md
5. Remove or archive old files (.cursorrules, duplicate CLAUDE.md)
6. Document the strategy in AGENTS.md itself or CONTRIBUTING.md
7. Update CI/CD to lint for instruction file drift (optional)

## Content Routing Guide

| Content Type | Where to Put It |
|-------------|-----------------|
| Build/test commands | AGENTS.md |
| Coding conventions | AGENTS.md |
| Boundaries (never touch) | AGENTS.md |
| Stack and versions | AGENTS.md |
| Claude Code plan mode triggers | CLAUDE.md only |
| Cursor glob-scoped rules | .cursor/rules/*.mdc only |
| Copilot agent personas | .github/agents/*.md only |
| Auto-memory preferences | Tool-specific config |
| MCP server references | Tool-specific config |
| Enterprise compliance | Managed policy (per tool) |

## Anti-Drift Practices

### Version Control

- Track all instruction files in git
- Require PR review for changes to AGENTS.md (like code changes)
- Add `.cursorrules` to `.gitignore` if migrated to `.cursor/rules/`

### Quarterly Audit

1. List all instruction files: `find . -name "AGENTS.md" -o -name "CLAUDE.md" -o -name ".cursorrules" -o -name "*.mdc" -o -name "copilot-instructions.md"`
2. Compare content across files for drift
3. Remove stale rules (reference moved files, deprecated tools)
4. Verify tool-specific bridges still import correctly

### CI Check (Optional)

```bash
# Verify CLAUDE.md imports AGENTS.md
grep -q "@AGENTS.md" CLAUDE.md || echo "WARN: CLAUDE.md not importing AGENTS.md"
```
