---
name: "@tank/agents-md"
description: |
  Write, audit, and manage AI coding agent instruction files across every major
  tool. Covers the AGENTS.md specification (Linux Foundation / Agentic AI
  Foundation), CLAUDE.md (Anthropic Claude Code), .cursor/rules/ MDC format
  (Cursor), .github/copilot-instructions.md (GitHub Copilot), .windsurfrules
  (Windsurf), GEMINI.md (Gemini CLI), Aider conventions, OpenCode rules, and
  Codex CLI discovery. Includes cross-tool compatibility strategies (symlinks,
  imports, canonical file patterns), monorepo multi-file instruction hierarchies,
  writing effective rules (ETH Zurich research on context file quality), anti-
  patterns (auto-generated file risks, bloat, staleness), and migration paths
  between formats.

  Synthesizes agents.md official specification, Anthropic Claude Code docs,
  OpenAI Codex docs, GitHub Blog (2500+ repo analysis), Augment Code guide,
  ETH Zurich context file study (2026), and tool vendor documentation.

  Trigger phrases: "AGENTS.md", "CLAUDE.md", "cursorrules", "cursor rules",
  ".cursor/rules", "AI agent instructions", "coding assistant rules",
  "AI coding rules", "copilot instructions", "windsurf rules", "cline rules",
  "aider conventions", "GEMINI.md", "OpenCode rules", "agent memory files",
  "coding agent config", "AGENTS.md vs CLAUDE.md", "AGENTS.md guide",
  "write agent instructions", "instruction file", "rules file"
---

# Agent Instruction Files

## Core Philosophy

1. **Write only what agents cannot discover** -- ETH Zurich research shows auto-generated context files reduce task success by ~3% and increase costs by 20%+. Include non-inferable details: custom build commands, counterintuitive patterns, tooling choices underrepresented in training data.
2. **One canonical file, tool-specific bridges** -- Maintain a single AGENTS.md as the source of truth. Use symlinks, imports, or `@AGENTS.md` references to feed the same content to Claude Code, Cursor, and Copilot.
3. **Scope rules to where they matter** -- Root-level instructions for project-wide standards. Subdirectory files for team-specific or language-specific conventions. Path-scoped rules (Cursor, Copilot, Claude Code) reduce token noise.
4. **Treat instructions as code** -- Version-control instruction files. Review changes in PRs. Remove stale rules. Stale structure references actively mislead agents.
5. **Concise beats comprehensive** -- Keep root AGENTS.md under 200 lines. Context windows are shared with conversation, code, and tool outputs. Every line of instruction competes with actual work.

## Quick-Start: Common Problems

### "Which instruction file should I create?"

| Your Tool(s) | Create | Notes |
|--------------|--------|-------|
| OpenAI Codex CLI | `AGENTS.md` | Primary file, walks directory tree |
| Claude Code | `CLAUDE.md` | Add `@AGENTS.md` import for cross-tool compat |
| Cursor | `.cursor/rules/*.mdc` + `AGENTS.md` | MDC for globs, AGENTS.md also read |
| GitHub Copilot | `AGENTS.md` + `.github/copilot-instructions.md` | Both read; path `.instructions.md` for scoping |
| Windsurf | `AGENTS.md` + `.windsurfrules` | Both active |
| Gemini CLI | `GEMINI.md` | Configure in `.gemini/settings.json` |
| OpenCode | `AGENTS.md` | Falls back to CLAUDE.md if absent |
| Multi-tool team | `AGENTS.md` (canonical) + tool symlinks | Single source of truth |
-> See `references/tool-formats.md` and `references/cross-tool-strategy.md`

### "My agent ignores my instruction file"

1. Verify the file is in the correct location for your tool's discovery path
2. Check for conflicting instructions across multiple files
3. Make rules more specific: "Use 2-space indentation" beats "format code properly"
4. Confirm the file is under the size limit (32 KiB for Codex, ~200 lines recommended)
5. Start a fresh session -- instructions load at session start, not mid-conversation
-> See `references/writing-rules.md` and `references/troubleshooting.md`

### "I need to set up a monorepo with different rules per package"

1. Place org-wide standards in root `AGENTS.md`
2. Add package-specific overrides in subdirectory `AGENTS.md` files
3. Nearest file wins (most tools use closest-to-edited-file precedence)
4. Use Cursor `.mdc` glob patterns or Copilot `.instructions.md` for path scoping
-> See `references/monorepo-patterns.md`

## Decision Trees

### Format Selection

| Signal | Recommended Format |
|--------|--------------------|
| Cross-tool team, open source | AGENTS.md (universal standard) |
| Claude Code only | CLAUDE.md with .claude/rules/ |
| Cursor-heavy team | .cursor/rules/*.mdc + AGENTS.md |
| Enterprise compliance | Managed policy CLAUDE.md + AGENTS.md |
| Existing .cursorrules | Migrate to .cursor/rules/ + AGENTS.md |

### What to Include vs Exclude

| Include | Exclude |
|---------|---------|
| Custom build/test commands | Architecture overviews agents find independently |
| Counterintuitive patterns | Content already in README or docs |
| Non-standard tooling choices | Generic best practices agents already know |
| "Never touch" boundaries | Lengthy style guides (link instead) |
| Stack with exact versions | Auto-generated summaries |

### Rule Specificity Level

| Rule Type | Example |
|-----------|---------|
| Boundary (critical) | "Never modify /db/migrations/ directly" |
| Command (executable) | "Run `npm test -- --coverage` before committing" |
| Convention (verifiable) | "Named exports only, no default exports" |
| Preference (flexible) | "Prefer functional components with hooks" |

## Reference Index

| File | Contents |
|------|----------|
| `references/agents-md-spec.md` | AGENTS.md specification, format, discovery, AAIF governance, FAQ, and 60k+ repo ecosystem |
| `references/tool-formats.md` | Every tool's native format: CLAUDE.md hierarchy, .cursor/rules/ MDC, copilot-instructions.md, .windsurfrules, GEMINI.md, Codex, OpenCode, Aider |
| `references/writing-rules.md` | How to write effective agent instructions: ETH Zurich findings, six core sections, anti-patterns, context cost tradeoffs |
| `references/cross-tool-strategy.md` | Multi-tool compatibility: canonical file patterns, symlink strategies, import syntax, migration paths between formats |
| `references/monorepo-patterns.md` | Directory-scoped instructions: nested file hierarchies, precedence rules, path-specific scoping, team isolation patterns |
| `references/claude-code-deep.md` | Claude Code memory system: CLAUDE.md locations, .claude/rules/ with path globs, auto memory, managed policy, @imports, claudeMdExcludes |
| `references/troubleshooting.md` | Diagnosing instruction failures: discovery verification, staleness detection, conflict resolution, size limits, session lifecycle |
