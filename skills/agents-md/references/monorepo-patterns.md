# Monorepo Instruction Patterns

Sources: OpenAI Codex AGENTS.md documentation, Anthropic Claude Code docs, GitHub Copilot docs, Augment Code guide (2026), vibecoding.app multi-agent guide

Covers: directory-scoped instruction hierarchies, precedence rules per tool, path-specific scoping mechanisms, team isolation patterns, and multi-agent monorepo workflows.

## Why Monorepos Need Special Handling

A monolith has one AGENTS.md. A monorepo has different teams, languages, frameworks, and conventions sharing one repository. A root AGENTS.md that covers everything becomes hundreds of lines -- too large for context efficiency. Different packages need different rules.

The solution: nested instruction files that scope rules to where they apply.

## Directory Hierarchy Pattern

```
monorepo/
  AGENTS.md                      # Org-wide: git conventions, CI checks, security
  apps/
    web/
      AGENTS.md                  # Frontend: React, Tailwind, component patterns
    api/
      AGENTS.md                  # Backend: FastAPI, SQLAlchemy, endpoint patterns
    mobile/
      AGENTS.md                  # React Native, Expo, platform specifics
  packages/
    shared/
      AGENTS.md                  # Shared library: TypeScript strict, no side effects
    design-system/
      AGENTS.md                  # Component library: Storybook, accessibility
  infra/
    AGENTS.md                    # Terraform, Docker, deployment rules
```

### What Goes Where

| Level | Content | Example |
|-------|---------|---------|
| Root | Org-wide standards | Git workflow, security boundaries, CI commands |
| App directory | App-specific stack and conventions | "React 19 with Vite", "FastAPI with async" |
| Package directory | Package-specific constraints | "No side effects in shared/", "a11y required" |
| Infra directory | Deployment and infrastructure rules | "Terraform only, never manual cloud changes" |

### Root File Template (Monorepo)

```markdown
# AGENTS.md

## Organization Standards
- All commits follow conventional commits format
- Run CI checks before pushing: `pnpm turbo run check`
- Never commit secrets or .env files
- Never force push to main or release branches

## Monorepo Commands
- Install all: `pnpm install`
- Build all: `pnpm turbo run build`
- Test all: `pnpm turbo run test`
- Lint all: `pnpm turbo run lint`
- Build specific: `pnpm turbo run build --filter=@org/web`
- Test specific: `pnpm turbo run test --filter=@org/api`

## Package Naming
- All packages use @org/ prefix
- Check package.json name field to confirm the right package name
```

### Subdirectory File Template

```markdown
# AGENTS.md - Web Application

## Stack
- Next.js 15 (App Router), TypeScript strict, Tailwind CSS v4
- State: Zustand, Server state: TanStack Query
- Testing: Vitest + React Testing Library

## Commands
- Dev: `pnpm dev` (from this directory)
- Test: `pnpm test`
- Typecheck: `pnpm typecheck`

## Conventions
- Named exports only
- Components in src/components/, pages in src/app/
- Server Components by default, 'use client' only when needed

## Boundaries
- Don't modify ../api/ or ../mobile/ directories
- Don't add dependencies to root package.json from here
```

## Precedence Rules by Tool

### Common Pattern (Most Tools)

Most tools follow "nearest file wins" -- the AGENTS.md closest to the file being edited takes priority. Files are concatenated, not replaced.

| Tool | Merge Behavior | Precedence |
|------|---------------|------------|
| Codex CLI | Concatenate root-to-CWD | Later files override earlier |
| Claude Code | Concatenate + on-demand subdirs | Subdirectory loaded when entering that path |
| GitHub Copilot | Nearest file | Closest to edited file |
| Windsurf | Root always + subdirectory when active | Subdirectory adds to root |
| OpenCode | First match per scope | AGENTS.md > CLAUDE.md at each level |

### Codex CLI Monorepo Specifics

Codex walks from Git root to CWD, loading one file per directory. Override files (`AGENTS.override.md`) at any level take precedence over `AGENTS.md` at that level.

```
monorepo/
  AGENTS.md                  # Loaded first (root)
  services/
    AGENTS.md                # Loaded second (intermediate)
    payments/
      AGENTS.override.md     # Loaded third (overrides payments/AGENTS.md)
      AGENTS.md              # Skipped (override exists)
```

Size limit: 32 KiB combined. Raise with `project_doc_max_bytes` in config.

### Claude Code Monorepo Specifics

Claude Code loads root `CLAUDE.md` and `CLAUDE.local.md` at launch. Subdirectory `CLAUDE.md` files load on demand when Claude reads files in those directories.

Use `claudeMdExcludes` to skip irrelevant team files:

```json
{
  "claudeMdExcludes": [
    "**/mobile/CLAUDE.md",
    "**/infra/.claude/rules/**"
  ]
}
```

This prevents the frontend developer from having mobile or infra rules loaded when working on web/ files.

## Path-Specific Scoping

### Cursor .mdc Rules (Glob-based)

Cursor's `.cursor/rules/*.mdc` files support glob patterns for precise scoping:

```yaml
---
description: "React component conventions"
globs: "apps/web/src/components/**/*.tsx"
alwaysApply: false
---

All components must:
- Accept a className prop
- Use forwardRef for DOM-wrapping components
- Have a corresponding .test.tsx file
```

```yaml
---
description: "API endpoint patterns"
globs: "apps/api/src/routes/**/*.ts"
alwaysApply: false
---

All routes must:
- Validate input with Zod schemas
- Return standardized error responses
- Log request/response at info level
```

Place `.cursor/rules/` at the monorepo root. Glob patterns scope each rule to the relevant package.

### Copilot Path-Scoped Instructions

```yaml
---
applyTo: "apps/web/**/*.{ts,tsx}"
---
Use React 19 patterns. Prefer Server Components.
Never use class components or string refs.
```

```yaml
---
applyTo: "apps/api/**/*.py"
---
Use FastAPI with async handlers.
All endpoints must have type hints.
Use Pydantic v2 models for request/response.
```

Place in `.github/instructions/` directory at the repo root.

### Claude Code Path-Scoped Rules

```markdown
---
paths:
  - "apps/web/src/**/*.{ts,tsx}"
---

# Frontend Development Rules

Use React 19 with TypeScript strict mode.
All components must have prop type definitions.
```

Place in `.claude/rules/` directory.

## Team Isolation Patterns

### Pattern 1: Directory Ownership

Each team owns a directory and its AGENTS.md:

| Team | Directory | Owns |
|------|-----------|------|
| Frontend | apps/web/ | AGENTS.md, .cursor/rules/frontend.mdc |
| Backend | apps/api/ | AGENTS.md, .cursor/rules/backend.mdc |
| Platform | infra/ | AGENTS.md |
| Shared | packages/ | AGENTS.md |

Teams can modify their own instruction files without PR review from other teams (use CODEOWNERS for enforcement).

### Pattern 2: CODEOWNERS for Instruction Files

```
# .github/CODEOWNERS
AGENTS.md                              @org/platform-team
apps/web/AGENTS.md                     @org/frontend-team
apps/api/AGENTS.md                     @org/backend-team
.claude/rules/security.md              @org/security-team
.github/copilot-instructions.md        @org/platform-team
```

Root-level instruction files require platform team review. Team-specific files require only that team's approval.

### Pattern 3: Shared + Local

Split instructions into committed shared files and gitignored local files:

```
apps/web/
  AGENTS.md              # Team-shared conventions (committed)
  CLAUDE.local.md        # Personal preferences (gitignored)
```

This prevents personal tooling preferences from affecting the team while allowing individual customization.

## Multi-Agent Workflow Pattern

When running multiple agents in parallel (one per package), scope instructions to prevent cross-contamination:

```markdown
# apps/web/AGENTS.md

## Scope
You handle UI work only. Your workspace is apps/web/.

## Off-limits
- Never modify apps/api/ or apps/mobile/
- Never modify packages/ without explicit instruction
- Never modify root configuration files
```

```markdown
# apps/api/AGENTS.md

## Scope
You handle API work only. Your workspace is apps/api/.

## Off-limits
- Never modify apps/web/ or apps/mobile/
- Never modify infrastructure in infra/
```

Each agent gets root-level shared context plus its scoped instructions. Boundaries prevent agents from stepping on each other.

## When to Split

| Condition | Action |
|-----------|--------|
| Root AGENTS.md under 100 lines | Keep monolithic |
| Root AGENTS.md 100-200 lines | Consider splitting if teams diverge |
| Root AGENTS.md over 200 lines | Split into subdirectory files |
| 3+ teams with different stacks | Mandatory subdirectory files |
| Cross-cutting concerns (security, testing) | Path-scoped rules (.mdc, .instructions.md) |
| Multiple AI tools | Canonical AGENTS.md + tool bridges per package |

## Common Monorepo Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Single massive root file | Token bloat, lost-in-middle | Split by package |
| No root file at all | Teams duplicate org standards | Root file for shared rules |
| Conflicting package rules | Agent behavior unpredictable | Audit for contradictions |
| Stale subdirectory files | Agent follows wrong conventions | CODEOWNERS + review |
| Path rules too broad | Wrong rules load for wrong files | Narrow glob patterns |
| Missing scope boundaries | Agent modifies other team's code | Explicit off-limits section |

## OpenAI Scale Example

At time of writing, the OpenAI Codex repository contains 88 AGENTS.md files -- one per significant directory. This represents the upper bound of modular instruction architecture, suitable for very large projects with dozens of sub-systems.
